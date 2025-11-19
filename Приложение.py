import tkinter as tk
from tkinter import ttk
import time
import random
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import telebot
from telebot import types
import json
import os
import customtkinter as ctk
import webbrowser
import re  # Импорт для обработки времени


class ProfiMonitorApp(ctk.CTk):
    CONFIG_FILE = "profi_config.json"

    # Обновленная цветовая палитра с белым фоном
    COLORS = {
        "primary": "#2B2B2B",
        "secondary": "#FFFFFF",  # Белый фон
        "accent": "#FF6D00",
        "success": "#4CAF50",
        "danger": "#F44336",
        "text": "#333333",
        "widget_bg": "#F5F5F5",  # Светлый фон для виджетов
        "border": "#E0E0E0"  # Цвет границ
    }

    # Константы для выбора порога времени
    TIME_THRESHOLD_OPTIONS = {
        "Меньше 1 часа": 1,
        "Меньше 3 часов": 3,
        "Меньше 6 часов": 6,
        "Меньше 12 часов": 12,
        "Меньше 24 часов (сутки)": 24,
        "Все (без фильтра по времени)": 99999
    }
    DEFAULT_TIME_THRESHOLD_KEY = "Меньше 6 часов"

    def __init__(self):
        super().__init__()
        self.title("Profi.ru Monitor")
        self.geometry("500x780")
        self.minsize(780, 780)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.driver = None
        self.sent_links = set()
        self.is_running = False
        self.debug_mode = ctk.BooleanVar(value=False)
        self.time_threshold_var = ctk.StringVar(
            value=self.DEFAULT_TIME_THRESHOLD_KEY)  # Новая переменная для порога времени

        self.create_widgets()
        self.setup_threads()
        self.load_config()

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.log_message("✅ Приложение инициализировано.")

    def create_widgets(self):
        # Настройка сетки
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Основной фон приложения - белый
        self.configure(fg_color=self.COLORS["secondary"])

        # Заголовок
        self.header = ctk.CTkLabel(
            self,
            text="Profi Monitor",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.COLORS["primary"]
        )
        self.header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nw")

        # Основной фрейм
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)

        # Настройки
        config_frame = ctk.CTkFrame(
            main_frame,
            corner_radius=12,
            fg_color=self.COLORS["widget_bg"],
            border_width=1,
            border_color=self.COLORS["border"]
        )
        config_frame.grid(row=0, column=0, padx=0, pady=(0, 15), sticky="nsew")

        fields = [
            ("Telegram Token", "TELEGRAM_TOKEN", False),
            ("Chat ID", "TELEGRAM_CHAT_ID", False),
            ("Логин Profi.ru", "PROFI_LOGIN", False),
            ("Пароль Profi.ru", "PROFI_PASSWORD", True)  # Добавлен флаг для пароля
        ]

        self.entries = {}
        for i, (text, name, is_password) in enumerate(fields):
            label = ctk.CTkLabel(
                config_frame,
                text=text,
                text_color=self.COLORS["text"]
            )
            label.grid(row=i, column=0, padx=10, pady=5, sticky="e")

            # Создаем поле ввода с учетом типа
            entry = ctk.CTkEntry(
                config_frame,
                width=400,
                corner_radius=8,
                fg_color="white",
                border_color=self.COLORS["border"],
                text_color=self.COLORS["text"],
                show="•" if is_password else "",
                font=ctk.CTkFont(size=14)
            )
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            self.entries[name] = entry

        # Дополнительные стоп-слова
        row_idx = len(fields)
        label = ctk.CTkLabel(
            config_frame,
            text="Дополнительные стоп-слова",
            text_color=self.COLORS["text"]
        )
        label.grid(row=row_idx, column=0, padx=10, pady=5, sticky="e")

        custom_bad_words_entry = ctk.CTkEntry(
            config_frame,
            width=400,
            corner_radius=8,
            fg_color="white",
            border_color=self.COLORS["border"],
            text_color=self.COLORS["text"],
            font=ctk.CTkFont(size=14),
            placeholder_text="Введите слова через запятую"
        )
        custom_bad_words_entry.grid(row=row_idx, column=1, padx=10, pady=5, sticky="ew")
        self.entries["CUSTOM_BAD_WORDS"] = custom_bad_words_entry

        # --- НОВЫЙ ЭЛЕМЕНТ: Порог времени ---
        row_idx += 1
        time_label = ctk.CTkLabel(
            config_frame,
            text="Максимальный возраст заказа (часов)",
            text_color=self.COLORS["text"]
        )
        time_label.grid(row=row_idx, column=0, padx=10, pady=5, sticky="e")

        time_options = list(self.TIME_THRESHOLD_OPTIONS.keys())
        self.time_threshold_menu = ctk.CTkOptionMenu(
            config_frame,
            variable=self.time_threshold_var,
            values=time_options,
            corner_radius=8,
            fg_color="white",
            button_color=self.COLORS["border"],
            button_hover_color="#EFEFEF",
            text_color=self.COLORS["text"],
            font=ctk.CTkFont(size=14)
        )
        self.time_threshold_menu.grid(row=row_idx, column=1, padx=10, pady=5, sticky="ew")
        # -----------------------------------

        # Чекбокс для отладки
        row_idx += 1
        debug_checkbox = ctk.CTkCheckBox(
            config_frame,
            text="Отладка (показывать браузер)",
            variable=self.debug_mode,
            onvalue=True,
            offvalue=False,
            checkbox_width=18,
            checkbox_height=18,
            corner_radius=4,
            border_width=1,
            border_color=self.COLORS["border"],
            fg_color=self.COLORS["accent"],
            hover_color="#FF8000",
            text_color=self.COLORS["text"]
        )
        debug_checkbox.grid(row=row_idx, column=1, padx=10, pady=(5, 10), sticky="w")

        # Кнопки управления
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=1, column=0, padx=0, pady=(0, 15), sticky="ew")

        self.start_btn = ctk.CTkButton(
            button_frame,
            text="Запустить мониторинг",
            command=self.start_monitoring,
            corner_radius=8,
            height=40,
            fg_color=self.COLORS["accent"],
            hover_color="#FF8000",
            text_color="white",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.start_btn.pack(side="left", padx=(0, 10), fill="x", expand=True)

        self.stop_btn = ctk.CTkButton(
            button_frame,
            text="Остановить",
            command=self.stop_monitoring,
            state="disabled",
            corner_radius=8,
            height=40,
            fg_color=self.COLORS["danger"],
            hover_color="#D32F2F",
            text_color="white",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.stop_btn.pack(side="right", fill="x", expand=True)

        # Логгер
        log_frame = ctk.CTkFrame(
            main_frame,
            corner_radius=12,
            fg_color=self.COLORS["widget_bg"],
            border_width=1,
            border_color=self.COLORS["border"]
        )
        log_frame.grid(row=2, column=0, padx=0, pady=0, sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)

        self.log_area = ctk.CTkTextbox(
            log_frame,
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=12),
            activate_scrollbars=True,
            corner_radius=8,
            fg_color="white",
            text_color=self.COLORS["text"],
            border_width=1,
            border_color=self.COLORS["border"]
        )
        self.log_area.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # Нижняя панель
        footer_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            height=40
        )
        footer_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="sew")
        footer_frame.grid_columnconfigure(0, weight=1)

        # Текст разработчика
        dev_label = ctk.CTkLabel(
            footer_frame,
            text="Разработка от dobrozor",
            text_color=self.COLORS["text"],
            font=ctk.CTkFont(size=12, slant="italic")
        )
        dev_label.grid(row=0, column=0, padx=10, sticky="w")

        # Социальные ссылки
        social_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        social_frame.grid(row=0, column=1, padx=10, sticky="e")

        # Стиль для ссылок
        link_style = {
            "font": ctk.CTkFont(size=12, underline=True),
            "cursor": "hand2",
            "text_color": "#1976D2"
        }

        # GitHub ссылка
        github_link = ctk.CTkLabel(
            social_frame,
            text="GitHub",
            **link_style
        )
        github_link.grid(row=0, column=0, padx=(0, 15))
        github_link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/dobrozor"))

        # Telegram ссылка
        telegram_link = ctk.CTkLabel(
            social_frame,
            text="Telegram",
            **link_style
        )
        telegram_link.grid(row=0, column=1, padx=(0, 10))
        telegram_link.bind("<Button-1>", lambda e: webbrowser.open("https://t.me/pro_parser_profi"))

        # Эффекты при наведении
        for link in [github_link, telegram_link]:
            link.bind("<Enter>", lambda e, l=link: l.configure(text_color="#1565C0"))
            link.bind("<Leave>", lambda e, l=link: l.configure(text_color="#1976D2"))

    def on_close(self):
        self.stop_monitoring()
        self.destroy()

    def log_message(self, message):
        self.log_area.configure(state="normal")
        self.log_area.insert("end", f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.log_area.see("end")
        self.log_area.configure(state="disabled")

    def load_config(self):
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    for key, entry in self.entries.items():
                        entry.delete(0, tk.END)
                        entry.insert(0, config.get(key, ''))

                    self.debug_mode.set(config.get("DEBUG_MODE", False))

                    # --- Загрузка нового параметра ---
                    saved_threshold = config.get("TIME_THRESHOLD", self.DEFAULT_TIME_THRESHOLD_KEY)
                    if saved_threshold in self.TIME_THRESHOLD_OPTIONS:
                        self.time_threshold_var.set(saved_threshold)
                    # --------------------------------

                self.log_message("📁 Настройки загружены из файла")
            except Exception as e:
                self.log_message(f"❌ Ошибка загрузки настроек: {str(e)}")
        else:
            self.log_message("ℹ️ Файл настроек не найден. Используются значения по умолчанию.")

    def save_config(self):
        try:
            config = {
                "TELEGRAM_TOKEN": self.entries["TELEGRAM_TOKEN"].get(),
                "TELEGRAM_CHAT_ID": self.entries["TELEGRAM_CHAT_ID"].get(),
                "PROFI_LOGIN": self.entries["PROFI_LOGIN"].get(),
                "PROFI_PASSWORD": self.entries["PROFI_PASSWORD"].get(),
                "CUSTOM_BAD_WORDS": self.entries["CUSTOM_BAD_WORDS"].get(),
                "DEBUG_MODE": self.debug_mode.get(),
                "TIME_THRESHOLD": self.time_threshold_var.get()  # Сохраняем выбранный порог
            }

            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            self.log_message("💾 Настройки успешно сохранены")
        except Exception as e:
            self.log_message(f"❌ Ошибка сохранения настроек: {str(e)}")

    def setup_threads(self):
        self.monitor_thread = None
        self.clear_thread = None
        self.is_running = False
        self.log_message("⚙️ Потоки инициализированы.")

    def start_monitoring(self):
        self.save_config()
        if not all(self.entries[e].get() for e in self.entries if e != "CUSTOM_BAD_WORDS"):
            self.log_message("❌ Ошибка: Заполните все обязательные поля конфигурации!")
            return

        self.is_running = True
        self.start_btn.configure(
            state="disabled",
            fg_color=self.COLORS["success"],
            hover_color="#45A049"
        )
        self.stop_btn.configure(
            state="normal",
            fg_color=self.COLORS["danger"],
            hover_color="#D32F2F"
        )
        self.log_message("⏳ Запуск мониторинга...")

        # Обрабатываем дополнительные стоп-слова
        custom_bad_words = []
        if self.entries["CUSTOM_BAD_WORDS"].get().strip():
            custom_bad_words = [word.strip().lower() for word in self.entries["CUSTOM_BAD_WORDS"].get().split(',')]
            self.log_message(f"🚫 Добавлены пользовательские стоп-слова: {', '.join(custom_bad_words)}")

        # Получаем значение порога в часах
        selected_threshold_key = self.time_threshold_var.get()
        time_threshold_hours = self.TIME_THRESHOLD_OPTIONS.get(selected_threshold_key, self.TIME_THRESHOLD_OPTIONS[
            self.DEFAULT_TIME_THRESHOLD_KEY])
        self.log_message(
            f"⏰ Установлен максимальный возраст заказа: {selected_threshold_key} ({time_threshold_hours} ч)")

        config = {
            "TELEGRAM": {
                "TOKEN": self.entries["TELEGRAM_TOKEN"].get(),
                "CHAT_ID": self.entries["TELEGRAM_CHAT_ID"].get()
            },
            "PROFI": {
                "LOGIN": self.entries["PROFI_LOGIN"].get(),
                "PASSWORD": self.entries["PROFI_PASSWORD"].get()
            },
            "FILTERS": {
                "TIME_THRESHOLD_HOURS": time_threshold_hours,  # Новый параметр
                "BAD_WORDS": ["Опрос", "Опросы"],
                "CUSTOM_BAD_WORDS": custom_bad_words
            },
            "SLEEP": {
                "CLEAR_HISTORY": 3600,
                "PAGE_REFRESH": (45, 119)
            },
            "DEBUG_MODE": self.debug_mode.get()
        }

        self.monitor_thread = threading.Thread(
            target=self.main_loop,
            args=(config,),
            daemon=True
        )
        self.monitor_thread.start()

        self.clear_thread = threading.Thread(
            target=self.clear_history,
            daemon=True
        )
        self.clear_thread.start()
        self.log_message("✅ Мониторинг запущен в фоновом режиме")

    def stop_monitoring(self):
        if not self.is_running:
            return

        self.is_running = False
        self.start_btn.configure(
            state="normal",
            fg_color=self.COLORS["accent"],
            hover_color="#FF8000"
        )
        self.stop_btn.configure(
            state="disabled",
            fg_color="#BDBDBD",
            hover_color="#9E9E9E"
        )
        self.log_message("🛑 Мониторинг остановлен. Закрываю браузер...")

        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.log_message("🌐 Браузер успешно закрыт.")
            except Exception as e:
                self.log_message(f"❌ Ошибка при закрытии браузера: {str(e)}")

    def init_driver(self, debug_mode=False):
        self.log_message(f"🌐 Инициализация браузера. Режим отладки: {'ВКЛ' if debug_mode else 'ВЫКЛ'}")
        chrome_options = Options()
        if not debug_mode:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

        try:
            driver = webdriver.Chrome(options=chrome_options)
            self.log_message("✅ WebDriver запущен.")
            return driver
        except Exception as e:
            self.log_message(f"❌ Ошибка запуска WebDriver: {str(e)}")
            self.stop_monitoring()
            return None

    def login(self, driver, config):
        if not driver:
            return False

        try:
            self.log_message("🔑 Начинаю авторизацию: переход на страницу входа.")
            driver.get("https://profi.ru/backoffice/n.php")
            time.sleep(1)

            driver.find_element(By.CSS_SELECTOR, '.login-form__input-login') \
                .send_keys(config["PROFI"]["LOGIN"])
            self.log_message("➡️ Введен логин.")

            driver.find_element(By.CSS_SELECTOR, '.login-form__input-password') \
                .send_keys(config["PROFI"]["PASSWORD"])
            self.log_message("➡️ Введен пароль.")

            driver.find_element(By.CSS_SELECTOR, '.ui-button').click()
            self.log_message("➡️ Нажата кнопка 'Войти'.")
            time.sleep(2)

            if "login-form" in driver.current_url:
                self.log_message("❌ Авторизация не удалась. Проверьте логин/пароль.")
                return False

            self.log_message("✅ Авторизация успешна!")
            return True
        except Exception as e:
            self.log_message(f"❌ Ошибка авторизации (Selenium): {str(e)}")
            return False

    def send_telegram_message(self, config, order):
        try:
            bot = telebot.TeleBot(config["TELEGRAM"]["TOKEN"])

            message = f"<b>{order['subject']}</b>\n"
            if order['price'] and order['price'] != "Цена не указана":
                message += f"<b>{order['price']}</b>\n"
            message += f"\n{order['description']}\n\n<i>{order['time_info']}</i>"

            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                text="Откликнуться",
                url=f"https://profi.ru/backoffice/n.php?o={order['link']}"
            ))

            bot.send_message(
                chat_id=config["TELEGRAM"]["CHAT_ID"],
                text=message,
                reply_markup=markup,
                parse_mode='HTML'
            )
            self.log_message(f"➡️ Telegram: Отправлен заказ {order['link']} ({order['subject']})")
        except Exception as e:
            self.log_message(f"❌ Ошибка отправки в Telegram: {str(e)}")

    def clear_history(self):
        self.log_message(f"⏳ Поток очистки истории запущен. Интервал: 3600 сек.")
        while self.is_running:
            time.sleep(3600)
            if self.is_running:
                self.sent_links.clear()
                self.log_message("🧹 История отправленных ссылок очищена (плановая очистка)")

    def main_loop(self, config):
        self.driver = self.init_driver(config["DEBUG_MODE"])
        if not self.driver:
            return

        if not self.login(self.driver, config):
            self.stop_monitoring()
            return

        self.log_message("✅ Авторизация успешна! Начало мониторинга...")

        while self.is_running:
            try:
                refresh_time = random.randint(*config["SLEEP"]["PAGE_REFRESH"])
                self.log_message(f"🔄 Обновляю страницу. Следующее обновление через {refresh_time} сек.")
                self.driver.refresh()
                time.sleep(3)

                # Получаем HTML
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')

                containers = soup.find_all(
                    'a', attrs={'data-testid': lambda x: x and x.endswith('_order-snippet')}
                )
                self.log_message(f"🔍 Найдено {len(containers)} контейнеров заказов на странице.")

                if not containers:
                    self.log_message("ℹ️ Заказы не найдены. Проверьте авторизацию или наличие новых заказов.")
                    time.sleep(refresh_time)
                    continue

                new_orders_count = 0
                for container in containers:
                    if not self.is_running:
                        break

                    order = self.parse_order(container)

                    if order:
                        if self.is_valid_order(config, order):
                            self.send_telegram_message(config, order)
                            self.sent_links.add(order["link"])
                            new_orders_count += 1
                        else:
                            pass  # Логирование причины пропуска происходит внутри is_valid_order
                    else:
                        self.log_message(f"⚠️ Парсинг контейнера не удался. Пропускаю.")

                self.log_message(f"✨ За цикл обработано новых заказов: {new_orders_count}")
                time.sleep(refresh_time)

            except Exception as e:
                self.log_message(f"❌ Критическая ошибка в цикле мониторинга: {str(e)}")
                time.sleep(60)

        # Выход из цикла - остановка мониторинга
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
            except:
                pass

    def parse_order(self, container):
        """Парсинг данных из контейнера заказа (тега <a>)"""
        try:
            # 1. ID Заказа (Link)
            link = container.get('data-testid', '').split('_')[0]

            # 2. Тема (Subject)
            subject_tag = container.find('h3')
            subject = subject_tag.text.strip() if subject_tag else None

            # 3. Описание (Description)
            description_tag = container.find('div', class_=lambda c: c and 'sc-tnih0-' in c)
            if not description_tag:
                description_tag = container.find('p')
            description = description_tag.text.strip() if description_tag else None

            # 4. Цена (Price)
            price_tag = container.find('span', class_='sc-eOWKyy')
            if not price_tag:
                price_tag = container.find('span', class_=lambda c: c and ('PriceValue' in c or 'sc-kCkVJn' in c))

            price = None
            if price_tag:
                full_price_text = price_tag.get_text(strip=True, separator=' ')
                price = ' '.join(full_price_text.split()).replace(' false', '').replace('false', '').strip()

                if not price:
                    price = None

            # 5. Время (Time Info)
            time_tag = container.find('span', class_=lambda c: c and 'Date__' in c)
            if not time_tag:
                time_tag = container.find('span', class_=lambda c: c and 'sc-iaHkcm' in c)
            time_info = time_tag.text.strip() if time_tag else None

            if not all([link, subject]):
                self.log_message(f"⚠️ Пропущен заказ: не найден Link ({link}) или Subject ({subject}).")
                return None

            # Устанавливаем значения по умолчанию
            if not description: description = "Описание не найдено."
            if not price: price = "Цена не указана"
            if not time_info: time_info = "Время не указано"

            return {
                "link": link,
                "subject": subject,
                "description": description,
                "price": price,
                "time_info": time_info
            }
        except Exception as e:
            self.log_message(f"❌ Ошибка парсинга контейнера {container.get('data-testid', 'N/A')}: {str(e)}")
            return None

    def is_recent_order(self, time_info, max_hours):
        """
        Проверяет, является ли заказ "свежим" на основании его time_info и максимального порога в часах.

        :param time_info: Строка времени из парсинга (например, "8 часов назад", "Вчера", "14:30")
        :param max_hours: Максимально допустимый возраст заказа в часах (int)
        :return: True, если заказ свежее порога, False в противном случае.
        """
        if max_hours >= self.TIME_THRESHOLD_OPTIONS["Все (без фильтра по времени)"]:
            return True  # Фильтр отключен

        lower_time_info = time_info.lower()

        # 1. Фильтрация по дням, месяцам, датам
        # Если присутствуют слова "Вчера", "день" (или части) или название месяца, считаем заказ слишком старым
        if any(word in lower_time_info for word in ["вчера", "дней", "день", "января", "февраля", "марта",
                                                    "апреля", "мая", "июня", "июля", "августа", "сентября",
                                                    "ноября", "октября", "декабря"]):
            return False

        # 2. Фильтрация по часам/минутам

        # Регулярное выражение для поиска "N минут/часов назад"
        # Пример: 15 минут назад, 8 часов назад
        match = re.search(r'(\d+)\s+(минут|мин|часов|час)', lower_time_info)

        if match:
            value = int(match.group(1))
            unit = match.group(2)

            if "час" in unit:
                age_in_hours = value
            elif "мин" in unit:
                age_in_hours = value / 60.0
            else:
                return True  # Неопознанный, но содержит числовой/временной формат, пропускаем через фильтр

            return age_in_hours <= max_hours

        # 3. Если формат "HH:MM" (например, "14:30") - это, вероятно, сегодняшний заказ (несколько часов назад).
        # Профи.ру обычно использует "N часов/минут назад" для свежих.
        # Если не смогли определить возраст, но нет явных признаков старости (как в п.1), пропускаем.
        if re.match(r'\d{1,2}:\d{2}', lower_time_info):
            # Считаем, что это свежий заказ, если явно не сказано обратное.
            # Это безопасно, так как старые заказы будут помечены "Вчера", "5 дней назад" и т.д.
            return True

            # 4. Прочие случаи. Если не смогли определить время, пропускаем (лучше пропустить, чем потерять).
        return True

    def is_valid_order(self, config, order):
        if not order:
            return False

        if order["link"] in self.sent_links:
            self.log_message(f"🚫 Пропущен заказ {order['link']}: уже был отправлен.")
            return False

        # --- НОВАЯ ПРОВЕРКА НА СВЕЖЕСТЬ ---
        if not self.is_recent_order(order["time_info"], config["FILTERS"]["TIME_THRESHOLD_HOURS"]):
            self.log_message(
                f"🚫 Пропущен заказ {order['link']}: не соответствует порогу по времени ({order['time_info']}).")
            return False
        # -----------------------------------

        # Проверка на стоп-слова
        all_bad_words = config["FILTERS"]["BAD_WORDS"] + config["FILTERS"]["CUSTOM_BAD_WORDS"]
        subject_lower = order["subject"].lower()

        for bad_word in all_bad_words:
            if bad_word.lower() in subject_lower:
                self.log_message(f"🚫 Пропущен заказ {order['link']}: стоп-слово '{bad_word}' в теме.")
                return False

        return True


if __name__ == "__main__":
    app = ProfiMonitorApp()
    app.mainloop()
