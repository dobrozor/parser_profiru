import bs4
import selenium
from bs4 import BeautifulSoup as bs
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import telebot
from telebot import types
import threading
import pickle


# Функция для загрузки настроек из файла
def load_settings(file_path):
    settings = {}
    with open(file_path, 'r', encoding='utf-8') as f:  # Использование кодировки UTF-8
        for line in f:
            line = line.strip()
            if not line:  # Пропускаем пустые строки
                continue
            key, value = line.split(': ', 1)  # Разбиение на ключ и значение
            # Обрабатываем параметры, разделенные запятыми
            if key in ['time_key', 'bad_words']:
                settings[key] = set(value.split(','))
            else:
                settings[key] = value
    return settings

# Загружаем настройки
settings = load_settings('settings.txt')

# Присваиваем значения переменным
token = settings['token']
chat_id = settings['chat_id']
time_key = settings['time_key']  # теперь это множество
bad_words = settings['bad_words']


#=========== ОСТАЛЬНОЕ ЛУЧШЕ НЕ МЕНЯТЬ ЕСЛИ НЕ ШАРИШ В ПИТОНЕ ============
url = 'https://profi.ru/backoffice/n.php'
sent_links = set()  # Set to keep track of sent messages

def clear_sent_links():
    global sent_links
    while True:
        time.sleep(1800)  # Задержка на 30 мин
        sent_links.clear()  # Очистка множества

# Запуск фонового потока для очистки
clear_thread = threading.Thread(target=clear_sent_links)
clear_thread.daemon = True  # Устанавливаем поток как демон, чтобы он завершался при закрытии программы
clear_thread.start()

bot = telebot.TeleBot(token)
chrome_options = Options()
#chrome_options.add_argument("--headless")  # Запуск в фоновом режиме
#chrome_options.add_argument("--no-sandbox")  # Для Linux
#chrome_options.add_argument("--disable-dev-shm-usage")  # Для Linux

# Создание драйвера с указанными опциями
driver = webdriver.Chrome(options=chrome_options)

def refresh_page():
    driver.refresh()
    time.sleep(10)

def send_message(subject, description, price, time_info, link):
    message = f"<b>{subject}</b>\n"
    if price:
        message += f"<b>{price}</b>\n"
    message += f"\n{description}\n\n<i>{time_info}</i>"
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton("Откликнуться", url=f"https://rnd.profi.ru{link}")
    markup.add(button)
    bot.send_message(chat_id, message, reply_markup=markup, parse_mode='HTML')

def check_conditions(subject):
    if any(bad_word in subject for bad_word in bad_words):
        return False
    return True

# Авторизация на сайте
driver.get(url)
time.sleep(5)

for cookie in pickle.load(open('session', 'rb')):
    driver.add_cookie(cookie)

bot.send_message(chat_id, 'Я вошел в браузер используя печеньки...')
driver.get(url)
time.sleep(10)

while True:
    print("Обновление страницы для получения данных...")
    # Обновляем страницу и получаем новые данные
    refresh_page()
    page = driver.page_source
    soup = bs(page, "html.parser")
    containers = soup.find_all(class_="OrderSnippetContainerStyles__Container-sc-1qf4h1o-0")  # Измените класс здесь

    if not containers:
        bot.send_message(chat_id, "Ошибка в HTML, напиши в тг: @dobrozor")
        continue

    for container in containers:
        link_element = container.find('a', class_="SnippetBodyStyles__Container-sc-tnih0-2")
        subject_element = container.find(class_="SubjectAndPriceStyles__SubjectsText-sc-18v5hu8-1")
        description_element = container.find(class_="SnippetBodyStyles__MainInfo-sc-tnih0-6")
        price_element = container.find(class_="SubjectAndPriceStyles__PriceValue-sc-18v5hu8-5")
        time_element = container.find(class_="Date__DateText-sc-e1f8oi-1")

        if link_element and subject_element and description_element:
            subject = subject_element.text.strip()
            description = description_element.text.strip()
            price = price_element.text.strip() if price_element else None
            time_info = time_element.text.strip()
            link = link_element['href']

            print(f"Получены данные: '{subject}'")
            # Проверка на совпадение времени
            if any(time_word in time_info for time_word in time_key):
                print(f"Сообщение не отправлено: '{time_info}' содержит фильтр.")
                continue

            if time_info == '1 минуту назад':
                print(f"Сообщение не отправлено: '{time_info}' может быть спамом")
                continue

            # Проверка на наличие 'плохих' слов
            if any(bad_word in subject for bad_word in bad_words):
                print(f"Сообщение не отправлено: '{subject}' содержит фильтр.")
                continue

            if description not in sent_links and check_conditions(subject):
                print(f"Проходит проверку: '{subject}'")
                send_message(subject, description, price, time_info, link)
                sent_links.add(description)  # Добавляем ссылку в список отправленных сообщений
                print(f"Сообщение отправлено.")
            else:
                print(
                    f"Данные не прошли проверку: '{subject}'")

    print("Ожидание перед следующим обновлением...")
    time.sleep(120)
