import re

from bs4 import BeautifulSoup as bs
import time
from selenium import webdriver
import telebot
import datetime

# Настройки
myLogin = ''  # логин от профи.ру
myPassword = ''  # парль
main_key = {'Дизайнеры',
            'Дизайн', 'Разработка логотипа', 'Графический дизайн', 'инфографика', 'инфографики', 'нарисовать', 'создать', 'дизайнер', 'создание', 'редизайн', 'разработка', 'обработка', 'макет', ''} #
time_key = {'часов',
            'час', 'Вчера', 'января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентрября', 'ноября', 'октября', 'декабря'}# Простейшее ограничение по времени
bad_words = {'Опрос', '3D', 'копирайтер', 'копирайт', 'моушн', 'видео', 'анимация'}

token = '' #токен бота
chat_id = '' #айди группы кудда бот отправит сообщение начинается с -100.....

url = 'https://profi.ru/backoffice/n.php'
url_site = 'https://rnd.profi.ru'


def refreshPage():
    driver.refresh()
    time.sleep(5)
    return


bot = telebot.TeleBot(token)
options = webdriver.ChromeOptions()
options.add_argument(
    "user-agent=Mozilla/5.0 (compatible; U; ABrowse 0.6; Syllable) AppleWebKit/420+ (KHTML, like Gecko)")

driver = webdriver.Chrome(
    options=options
)

# Логинемся
driver.get(url)
namesLogin = driver.execute_script(
    "return document.getElementsByClassName('ui-input ui-input-bo login-form__input-login ui-input_desktop ui-input_with-placeholder_empty');")
namesLogin[0].clear()
email_input = namesLogin[0].send_keys(myLogin)

time.sleep(0.5)
namesPassword = driver.execute_script(
    "return document.getElementsByClassName('ui-input ui-input-bo login-form__input-password ui-input_desktop ui-input_with-placeholder_empty');")
namesPassword[0].clear()
password_input = namesPassword[0].send_keys(myPassword)
time.sleep(0.5)

namesButton = driver.execute_script(
    "return document.getElementsByClassName('ui-button');")
button_input = namesButton[0].click()

# Время для ввода капчи
time.sleep(60)

page = driver.page_source

soup = bs(page, 'html.parser')
known_tasks = [] #В целом уже не нужно, требовалось для старой проверки

try:
    sent_links = []  # Список для отслеживания отправленных ссылок

    while True:
        refreshPage()
        print('обновил страницу')

        arr = driver.execute_script(
            "return document.getElementsByClassName('SnippetBodyStyles__Container-sc-br3c4b-0');")
        print('получил данные')

        for block in soup.find_all(class_=re.compile('SnippetBodyStyles__Container-')):
            name = block.find(class_=re.compile('SubjectAndPriceStyles__SubjectsText-'))
            about = block.find(class_=re.compile('SnippetBodyStyles__MainInfo-'))
            price = block.find(class_=re.compile('SubjectAndPriceStyles__PriceLine-'))
            date = block.find(class_=re.compile('Date__DateText-'))
            my_url = url_site + str(block.attrs['href'])

            # Создаем задачу для проверки
            task_stack = (str(about.get_text()), str(date.get_text()), my_url)

            tg_name = str(name.get_text())
            tg_about = str(about.get_text())
            tg_price = str(price.get_text())
            tg_date = str(date.get_text())

            # Проверка на наличие хотя бы одного слова из main_key в task_stack
            contains_keyword = any(key.lower() in i.lower() for key in main_key for i in task_stack)

            # Проверка, что нет слов из time_key
            not_in_time_key = all(key2.lower() not in str(task_stack) for key2 in time_key)

            # Проверка на отсутствие bad_words
            not_contains_bad_word = all(bad_word.lower() not in str(task_stack) for bad_word in bad_words)

            # Основная проверка на выполнение условий
            if contains_keyword and not_in_time_key and not_contains_bad_word:
                print('Нашел подходящее')

                # Проверяем, отправлял ли бот нам новый заказ или нет
                if my_url not in sent_links:
                    sent_links.append(my_url)  # если не отправлял то добавляем в отправленные и отправляем заказ в тг


                    message_text = f"*{tg_name}*\n{tg_price}\n\n{tg_about}\n\n_{tg_date}_"

                    # Создаем клавиатуру и кнопку
                    keyboard = telebot.types.InlineKeyboardMarkup()
                    callback_button = telebot.types.InlineKeyboardButton("Написать", url=my_url)
                    keyboard.add(callback_button)

                    # Отправляем сообщение с кнопкой
                    bot.send_message(chat_id, message_text, reply_markup=keyboard, parse_mode='Markdown')
                    current_time = datetime.datetime.now().time()
                    print(f'Отправил в тг в {current_time}')
                else:
                    print('А нет, уже такое отправлял')
            else:
                print('Ничего нового :(')

        time.sleep(90)
        driver.get(url)
        page = driver.page_source
        soup = bs(page, 'html.parser')

except Exception as ex:
    print(ex)

finally:
    driver.close()
    driver.quit()
