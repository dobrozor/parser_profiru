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

    def __init__(self):
        super().__init__()
        self.title("Profi.ru Monitor")
        self.geometry("500x780")  # Увеличили высоту для новых элементов
        self.minsize(500, 780)

        # Устанавливаем белую тему и светлый режим
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Инициализация переменных
        self.driver = None
        self.sent_links = set()
        self.is_running = False
        self.debug_mode = ctk.BooleanVar(value=False)  # Для чекбокса отладки

        self.create_widgets()
        self.setup_threads()
        self.load_config()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

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
        self.log_area.insert("end", f"{message}\n")
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
                    # Загружаем состояние чекбокса отладки
                    self.debug_mode.set(config.get("DEBUG_MODE", False))
                self.log_message("Настройки загружены из файла")
            except Exception as e:
                self.log_message(f"Ошибка загрузки настроек: {str(e)}")

    def save_config(self):
        try:
            config = {
                "TELEGRAM_TOKEN": self.entries["TELEGRAM_TOKEN"].get(),
                "TELEGRAM_CHAT_ID": self.entries["TELEGRAM_CHAT_ID"].get(),
                "PROFI_LOGIN": self.entries["PROFI_LOGIN"].get(),
                "PROFI_PASSWORD": self.entries["PROFI_PASSWORD"].get(),
                "CUSTOM_BAD_WORDS": self.entries["CUSTOM_BAD_WORDS"].get(),
                "DEBUG_MODE": self.debug_mode.get()
            }

            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            self.log_message("Настройки успешно сохранены")
        except Exception as e:
            self.log_message(f"Ошибка сохранения настроек: {str(e)}")

    def setup_threads(self):
        self.monitor_thread = None
        self.clear_thread = None
        self.is_running = False

    def start_monitoring(self):
        self.save_config()
        if not all(self.entries[e].get() for e in self.entries if e != "CUSTOM_BAD_WORDS"):
            self.log_message("Ошибка: Заполните все обязательные поля конфигурации!")
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

        # Обрабатываем дополнительные стоп-слова
        custom_bad_words = []
        if self.entries["CUSTOM_BAD_WORDS"].get().strip():
            custom_bad_words = [word.strip().lower() for word in self.entries["CUSTOM_BAD_WORDS"].get().split(',')]

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
                "TIME_KEYWORDS": ["часов", "час", "Вчера", "января", "февраля", "марта",
                                  "апреля", "мая", "июня", "июля", "августа", "сентября",
                                  "ноября", "октября", "декабря"],
                "BAD_WORDS": ["Опрос", "Опросы"],
                "CUSTOM_BAD_WORDS": custom_bad_words  # Добавляем пользовательские стоп-слова
            },
            "SLEEP": {
                "CLEAR_HISTORY": 3600,
                "PAGE_REFRESH": (60, 120)
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

    def stop_monitoring(self):
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
        self.log_message("Мониторинг остановлен")

        if self.driver:
            self.driver.quit()
            self.driver = None

    def init_driver(self, debug_mode=False):
        chrome_options = Options()
        if not debug_mode:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        return webdriver.Chrome(options=chrome_options)

    def login(self, driver, config):
        try:
            self.log_message("Начинаю авторизацию")
            driver.get("https://profi.ru/backoffice/n.php")
            time.sleep(5)

            driver.find_element(By.CSS_SELECTOR, '.login-form__input-login') \
                .send_keys(config["PROFI"]["LOGIN"])

            driver.find_element(By.CSS_SELECTOR, '.login-form__input-password') \
                .send_keys(config["PROFI"]["PASSWORD"])

            driver.find_element(By.CSS_SELECTOR, '.ui-button').click()
            time.sleep(5)
            return True
        except Exception as e:
            self.log_message(f"Ошибка авторизации: {str(e)}")
            return False

    def send_telegram_message(self, config, order):
        try:
            bot = telebot.TeleBot(config["TELEGRAM"]["TOKEN"])

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
                chat_id=config["TELEGRAM"]["CHAT_ID"],
                text=message,
                reply_markup=markup,
                parse_mode='HTML'
            )
            self.log_message(f"Отправлен заказ: {order['subject']}")
        except Exception as e:
            self.log_message(f"Ошибка отправки: {str(e)}")

    def clear_history(self):
        while self.is_running:
            time.sleep(3600)
            if self.is_running:  # Дополнительная проверка
                self.sent_links.clear()
                self.log_message("История отправленных ссылок очищена")

    def main_loop(self, config):
        self.driver = self.init_driver(config["DEBUG_MODE"])

        if not self.login(self.driver, config):
            self.log_message("❌ Ошибка авторизации на Profi.ru!")
            self.stop_monitoring()
            return

        self.log_message("Авторизация успешна! Начало мониторинга...")

        while self.is_running:
            try:
                self.driver.refresh()
                time.sleep(10)

                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                containers = soup.find_all(
                    class_="OrderSnippetContainerStyles__Container-sc-1qf4h1o-0"
                )

                if not containers:
                    self.log_message("Заказы не найдены. Проверьте авторизацию или перезапустите программу")
                    time.sleep(random.randint(*config["SLEEP"]["PAGE_REFRESH"]))
                    continue

                for container in containers:
                    if not self.is_running:
                        break

                    order = self.parse_order(container)
                    if order and self.is_valid_order(config, order):
                        self.send_telegram_message(config, order)
                        self.sent_links.add(order["link"])

                time.sleep(random.randint(*config["SLEEP"]["PAGE_REFRESH"]))

            except Exception as e:
                self.log_message(f"Ошибка: {str(e)}")
                time.sleep(60)

        if self.driver:
            self.driver.quit()
            self.driver = None

    def parse_order(self, container):
        """Парсинг данных из контейнера заказа"""
        try:
            link_tag = container.find('a')
            link = link_tag['id'] if link_tag else None

            subject_tag = container.find(class_="SubjectAndPriceStyles__SubjectsText-sc-18v5hu8-1")
            subject = subject_tag.text.strip() if subject_tag else None

            desc_tag = container.find(class_="SnippetBodyStyles__MainInfo-sc-tnih0-6")
            description = desc_tag.text.strip() if desc_tag else None

            price_tag = container.find(class_="SubjectAndPriceStyles__PriceValue-sc-18v5hu8-5")
            price = price_tag.text.strip() if price_tag else None

            time_tag = container.find(class_="Date__DateText-sc-e1f8oi-1")
            time_info = time_tag.text.strip() if time_tag else None

            # Проверяем, что все поля заполнены
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
            self.log_message(f"Ошибка парсинга: {str(e)}")
            return None

    def is_valid_order(self, config, order):
        if not order:
            return False

        time_checks = [
            any(word in order["time_info"] for word in config["FILTERS"]["TIME_KEYWORDS"]),
            #order["time_info"] == '1 минуту назад'
        ]

        if any(time_checks):
            return False

        # Объединяем стандартные и пользовательские стоп-слова
        all_bad_words = config["FILTERS"]["BAD_WORDS"] + config["FILTERS"]["CUSTOM_BAD_WORDS"]

        if any(bad_word.lower() in order["subject"].lower()
               for bad_word in all_bad_words):
            return False

        if order["link"] in self.sent_links:
            return False

        return True


if __name__ == "__main__":
    app = ProfiMonitorApp()
    app.mainloop()
