import re
from bs4 import BeautifulSoup as bs
import time
from selenium import webdriver
import telebot
import datetime#нужен только чтоб отправлять в консоль время отправления данных в телеграм

import cfg

current_time = datetime.datetime.now().time()#нужен только чтоб отправлять в консоль время отправления данных в телеграм

# Settings
myLogin = cfg.myLogin
myPassword = cfg.myPassword
main_key = cfg.main_key
time_key = cfg.time_key

token = cfg.token
chat_id = cfg.chat_id

url = 'https://profi.ru/backoffice/n.php'
url_site = 'https://profi.ru'

def refreshPage():
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    return


bot = telebot.TeleBot(token)
options = webdriver.ChromeOptions()
options.add_argument(
    "user-agent=Mozilla/5.0 (compatible; U; ABrowse 0.6; Syllable) AppleWebKit/420+ (KHTML, like Gecko)")

driver = webdriver.Chrome(
    options=options
)

# логин
driver.get(url)
namesLogin = driver.execute_script(
    "return document.getElementsByClassName('ui-input ui-input-bo login-form__input-login ui-input_desktop ui-input_with-placeholder_empty');")
namesLogin[0].clear()
email_input = namesLogin[0].send_keys(myLogin)

time.sleep(1)
namesPassword = driver.execute_script(
    "return document.getElementsByClassName('ui-input ui-input-bo login-form__input-password ui-input_desktop ui-input_with-placeholder_empty');")
namesPassword[0].clear()
password_input = namesPassword[0].send_keys(myPassword)
time.sleep(1)

namesButton = driver.execute_script(
    "return document.getElementsByClassName('ui-button');")
button_input = namesButton[0].click()

# пауза для ввода капчи
time.sleep(30)

page = driver.page_source

soup = bs(page, 'html.parser')
known_tasks = []

try:
    while True:
        refreshPage()

        arr = driver.execute_script(
            "return document.getElementsByClassName('SnippetBodyStyles__Container-sc-br3c4b-0 dNCmqL');")

        for block in soup.find_all(class_=re.compile('SnippetBodyStyles__Container-')):

            #================Классы которые хотим парсить=================
            name = block.find(class_=re.compile('SubjectAndPriceStyles__SubjectsText-'))
            about = block.find(class_=re.compile('SnippetBodyStyles__MainInfo-'))
            price = block.find(class_=re.compile('SubjectAndPriceStyles__PriceLine-'))
            date = block.find(class_=re.compile('Date__DateText-'))
            my_url = url_site + str(block.attrs['href'])

            task_stack = (str(name.get_text()), str(about.get_text()), str(date.get_text()), my_url) #Делаем тоже самое что ниже, но объединяем в одну переменную для будущей проверки
            #Убираем из парсинга всё лишнее, выводим только текст, нужно для корректной отправки в телеграм
            tg_name = str(name.get_text())
            tg_about = str(about.get_text())
            tg_price = str(price.get_text())
            tg_date = str(date.get_text())

            if task_stack not in known_tasks:#проверка, новый заказ или старый
                # Проверка на наличие ключевых слов в cfg.task_stack
                contains_keyword = any(key.lower() in i.lower() for key in main_key for i in task_stack)
                # Проверка что заказ создан менее часа назад
                not_in_time_key = all(key2.lower() not in str(task_stack) for key2 in time_key)

                if contains_keyword and not_in_time_key:
                    known_tasks.append(task_stack)


                    message_text = f"*{tg_name}*\n{tg_price}\n\n{tg_about}\n{tg_date}_"#Формируем текст для отправки в тг

                    # Создаем клавиатуру и кнопку
                    keyboard = telebot.types.InlineKeyboardMarkup()
                    callback_button = telebot.types.InlineKeyboardButton("Написать", url=my_url)
                    keyboard.add(callback_button)

                    # Отправляем сообщение с кнопкой
                    bot.send_message(chat_id, message_text, reply_markup=keyboard, parse_mode='Markdown')
                    print(f'Отправил в тг в {current_time}')#выводим в консоль (сделал для собственного удобства)



        time.sleep(30)
        driver.get(url)
        page = driver.page_source
        soup = bs(page, 'html.parser')

except Exception as ex:
    print(ex)

finally:
    driver.close()
    driver.quit()
