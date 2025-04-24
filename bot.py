import time
import random
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import telebot
from telebot import types

# Конфигурация приложения
CONFIG = {
    "TELEGRAM": {
        "TOKEN": "TG_TOKEN_BOT",
        "CHAT_ID": "CHAT_ID"
    },
    "PROFI": {
        "URL": "https://profi.ru/backoffice/n.php",
        "LOGIN": "LOGIN_PROFI_RU",
        "PASSWORD": "PASS_PROFI_RU"
    },
    "FILTERS": {
        "TIME_KEYWORDS": ["часов", "час", "Вчера", "января", "февраля", "марта",
                          "апреля", "мая", "июня", "июля", "августа", "сентября",
                          "ноября", "октября", "декабря"], #фильтр дат
        "BAD_WORDS": ["Опрос", "3D", "копирайтер", "копирайт", "моушн",
                      "видео", "анимация", "3d", "Опросы", "инфографика", "3Д"] #фильтр запросов
    },
    "SLEEP": {
        "CLEAR_HISTORY": 3600, #очистка истории раз в час
        "PAGE_REFRESH": (60, 120) 
    }
}

# Глобальные состояния
sent_links = set()
bot = telebot.TeleBot(CONFIG["TELEGRAM"]["TOKEN"])
is_running = False
driver = None
main_thread = None
clear_thread = None


def init_driver():
    """Инициализация веб-драйвера"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=chrome_options)


def login(driver):
    """Авторизация на сайте Profi.ru"""
    try:
        driver.get(CONFIG["PROFI"]["URL"])
        time.sleep(5)

        # Ввод логина
        login_field = driver.find_element(By.CSS_SELECTOR, '.login-form__input-login')
        login_field.send_keys(CONFIG["PROFI"]["LOGIN"])

        # Ввод пароля
        password_field = driver.find_element(By.CSS_SELECTOR, '.login-form__input-password')
        password_field.send_keys(CONFIG["PROFI"]["PASSWORD"])

        # Клик по кнопке входа
        driver.find_element(By.CSS_SELECTOR, '.ui-button').click()
        time.sleep(5)
        return True
    except Exception as e:
        print(f"Ошибка авторизации: {str(e)}")
        return False


def parse_order(container):
    """Парсинг данных из контейнера заказа"""
    try:
        link = container.find('a', class_="SnippetBodyStyles__Container-sc-tnih0-2")['id'] if container.find('a',
                                                                                                             class_="SnippetBodyStyles__Container-sc-tnih0-2") else None
        subject = container.find(
            class_="SubjectAndPriceStyles__SubjectsText-sc-18v5hu8-1").text.strip() if container.find(
            class_="SubjectAndPriceStyles__SubjectsText-sc-18v5hu8-1") else None
        description = container.find(class_="SnippetBodyStyles__MainInfo-sc-tnih0-6").text.strip() if container.find(
            class_="SnippetBodyStyles__MainInfo-sc-tnih0-6") else None
        price = container.find(class_="SubjectAndPriceStyles__PriceValue-sc-18v5hu8-5").text.strip() if container.find(
            class_="SubjectAndPriceStyles__PriceValue-sc-18v5hu8-5") else None
        time_info = container.find(class_="Date__DateText-sc-e1f8oi-1").text.strip() if container.find(
            class_="Date__DateText-sc-e1f8oi-1") else None

        if not all([link, subject, description, price, time_info]):
            return None

        return {
            "link": link,
            "subject": subject,
            "description": description,
            "price": price,
            "time_info": time_info
        }
    except Exception as e:
        print(f"Ошибка парсинга: {str(e)}")
        return None


def is_valid_order(order):
    """Проверка заказа на соответствие фильтрам"""
    if not order:
        return False

    # Фильтр по времени
    if any(word in order["time_info"] for word in CONFIG["FILTERS"]["TIME_KEYWORDS"]):
        return False

    # Фильтр по времени публикации
    if order["time_info"] == '1 минуту назад':
        return False

    # Фильтр по ключевым словам
    if any(bad_word.lower() in order["subject"].lower() for bad_word in CONFIG["FILTERS"]["BAD_WORDS"]):
        return False

    return True


def send_telegram_message(order):
    """Отправка сообщения в Telegram"""
    try:
        message = f"<b>{order['subject']}</b>\n"
        if order['price']:
            message += f"<b>{order['price']}</b>\n"
        message += f"\n{order['description']}\n\n<i>{order['time_info']}</i>"

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(
            text="Откликнуться",
            url=f"https://profi.ru/backoffice/n.php?o={order['link']}"
        ))

        bot.send_message(
            chat_id=CONFIG["TELEGRAM"]["CHAT_ID"],
            text=message,
            reply_markup=markup,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Ошибка отправки сообщения: {str(e)}")


def clear_history():
    """Очистка истории отправленных ссылок"""
    global sent_links
    while is_running:
        time.sleep(CONFIG["SLEEP"]["CLEAR_HISTORY"])
        sent_links.clear()
        print("История отправленных ссылок очищена")


def main_loop():
    """Основной цикл обработки заказов"""
    global driver, is_running
    driver = init_driver()

    if not login(driver):
        bot.send_message(
            CONFIG["TELEGRAM"]["CHAT_ID"],
            "❌ Ошибка авторизации на Profi.ru!"
        )
        is_running = False
        return

    while is_running:
        try:
            # Обновление страницы
            driver.refresh()
            time.sleep(10)

            # Парсинг страницы
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            containers = soup.find_all(class_="OrderSnippetContainerStyles__Container-sc-1qf4h1o-0")

            if not containers:
                print("Заказы не найдены")
                time.sleep(random.randint(*CONFIG["SLEEP"]["PAGE_REFRESH"]))
                continue

            # Обработка заказов
            for container in containers:
                if not is_running:
                    break

                order = parse_order(container)
                if order and is_valid_order(order) and order["link"] not in sent_links:
                    try:
                        send_telegram_message(order)
                        sent_links.add(order["link"])
                        print(f"Отправлен: {order['subject']}")
                    except Exception as e:
                        print(f"Ошибка обработки заказа: {str(e)}")

            # Случайная задержка
            time.sleep(random.randint(*CONFIG["SLEEP"]["PAGE_REFRESH"]))

        except Exception as e:
            print(f"Критическая ошибка: {str(e)}")
            time.sleep(60)

    if driver:
        driver.quit()
        driver = None


@bot.message_handler(commands=['start'])
def start_command(message):
    global is_running, main_thread, clear_thread

    if is_running:
        bot.send_message(message.chat.id, "Бот уже запущен!")
        return

    is_running = True
    main_thread = threading.Thread(target=main_loop)
    clear_thread = threading.Thread(target=clear_history)

    main_thread.start()
    clear_thread.start()

    bot.send_message(message.chat.id, "Бот запущен и начал мониторинг заказов!")


@bot.message_handler(commands=['stop'])
def stop_command(message):
    global is_running, main_thread, clear_thread, driver

    if not is_running:
        bot.send_message(message.chat.id, "Бот уже остановлен!")
        return

    is_running = False

    if main_thread:
        main_thread.join()
    if clear_thread:
        clear_thread.join()

    if driver:
        driver.quit()
        driver = None

    bot.send_message(message.chat.id, "Бот остановлен!")


@bot.message_handler(commands=['clear'])
def clear_command(message):
    global sent_links
    sent_links.clear()
    bot.send_message(message.chat.id, "Список отправленных ссылок очищен!")


@bot.message_handler(commands=['get'])
def get_command(message):
    global sent_links
    if not sent_links:
        bot.send_message(message.chat.id, "Список отправленных ссылок пуст!")
    else:
        links_text = "\n".join(sent_links)
        bot.send_message(message.chat.id, f"Отправленные ссылки:\n{links_text}")


if __name__ == "__main__":
    print("Бот запущен. Ожидание команд...")
    bot.infinity_polling()
