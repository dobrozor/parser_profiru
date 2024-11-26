from bs4 import BeautifulSoup as bs
import time
from selenium import webdriver
import telebot
from telebot import types

# Settings
myLogin = ''  # логин (телефон не катит)
myPassword = ''  # пароль от профи.ру

token = '' #токен бота
chat_id = '' #сюда айди группы с ботом (создаёте беседу, в неё добавляете бота и вот йади беседы нужен, он всегда начинается с -100)

time_key = {'часов', 'час', 'Вчера', 'января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентрября', 'ноября', 'октября', 'декабря'}# Простейшее ограничение по времени
bad_words = {'Опрос', '3D', 'копирайтер', 'копирайт', 'моушн', 'видео', 'анимация', '3d', 'Опросы'}

#=========== ОСТАЛЬНОЕ ЛУЧШЕ НЕ МЕНЯТЬ ЕСЛИ НЕ ШАРИШ В ПИТОНЕ ============
url = 'https://profi.ru/backoffice/n.php'
sent_links = set()  # Set to keep track of sent messages

bot = telebot.TeleBot(token)
options = webdriver.ChromeOptions()
options.add_argument(
    "user-agent=Mozilla/5.0 (compatible; U; ABrowse 0.6; Syllable) AppleWebKit/420+ (KHTML, like Gecko)")
driver = webdriver.Chrome(options=options)

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

# Ввод логина и пароля
namesLogin = driver.execute_script(
    "return document.getElementsByClassName('ui-input ui-input-bo login-form__input-login ui-input_desktop ui-input_with-placeholder_empty');")
namesLogin[0].clear()
namesLogin[0].send_keys(myLogin)
namesPassword = driver.execute_script(
    "return document.getElementsByClassName('ui-input ui-input-bo login-form__input-password ui-input_desktop ui-input_with-placeholder_empty');")
namesPassword[0].clear()
namesPassword[0].send_keys(myPassword)
namesButton = driver.execute_script("return document.getElementsByClassName('ui-button');")
namesButton[0].click()

# Пауза для ввода капчи
print("Пожалуйста, введите капчу...")
time.sleep(30)

while True:
    print("Обновление страницы для получения данных...")
    # Обновляем страницу и получаем новые данные
    refresh_page()
    page = driver.page_source
    soup = bs(page, "html.parser")
    containers = soup.find_all(class_="OrderSnippetContainerStyles__Container-sc-1qf4h1o-0")  # Измените класс здесь

    if not containers:
        print("Ошибка в HTML, напиши в тг: @dobrozor")
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
    time.sleep(60)
