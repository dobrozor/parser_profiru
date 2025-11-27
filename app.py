import tkinter as tk
from tkinter import ttk
import time
import random
import threading
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import requests
from datetime import datetime, timedelta
import telebot
from telebot import types
import json
import os
import customtkinter as ctk
import webbrowser
import re


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

    # --- НОВЫЕ КОНСТАНТЫ ---
    MIN_ORDER_AGE_SECONDS = 70  # Минимальный возраст заказа в секундах (1 минута)

    GRAPHQL_URL = 'https://rnd.profi.ru/graphql'
    API_HEADERS = {
        'origin': 'https://rnd.profi.ru',
        'referer': 'https://rnd.profi.ru/backoffice/n.php',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 YaBrowser/25.10.0.0 Safari/537.36',
        'x-app-id': 'BO',
        'x-new-auth-compatible': '1',
    }
    API_JSON_DATA = {
        'query': '#prfrtkn:webbo:36bb338fde61287ba8723d0687db52f33ab381d8:9b53a063284429f629f81506c40339c13822dd22\n\n      query BoSearchBoardItems($filter: BoSearchFrontFiltersInput!, $useSavedFilter: Boolean, $allVerticals: Boolean, $searchQuery: String, $searchEntities: [BoSearchEntityInput!], $searchId: ID, $nextCursor: String, $pageSize: Int, $boSortUp: Int, $minScore: Float, $coordinates: BoSearchAreaInput, $clusterId: ID, $sort: BoSearchSortEnum) @domain(domains: [BO_BOARD, BO_BOARD_LIST]) {\n  boSearchBoardItems(\n    filter: $filter\n    useSavedFilter: $useSavedFilter\n    allVerticals: $allVerticals\n    searchQuery: $searchQuery\n    searchEntities: $searchEntities\n    searchId: $searchId\n    nextCursor: $nextCursor\n    pageSize: $pageSize\n    boSortUp: $boSortUp\n    minScore: $minScore\n    coordinates: $coordinates\n    clusterId: $clusterId\n    sort: $sort\n  ) {\n    nextCursor\n    serverTs\n    totalCount\n    analytics {\n      boardSearchQuery\n      boardSearchUsed\n    }\n    items {\n      id\n      type\n      ... on BoSearchPremiumBlock {\n        title\n        description\n        buttonLabel\n      }\n      ... on BoSearchPremiumRepeatBlock {\n        title\n      }\n      ... on BoSearchSnippet {\n        ...snippetFieldsCommon\n        isFresh\n        coordinates {\n          lat\n          lon\n        }\n        clientInfo {\n          name\n        }\n        clientTags {\n          value\n        }\n        badges {\n          id\n          imageKey\n          label\n        }\n        status {\n          text\n          color\n        }\n        schedule\n        images {\n          host\n          width\n          height\n          original\n        }\n      }\n      ... on BoSearchEmptyState {\n        view {\n          title\n          description\n          imageKey\n          button {\n            label\n            actionType\n          }\n        }\n      }\n      ... on BoSearchStories {\n        id\n        type\n      }\n      ... on BoSearchDivider {\n        title\n        button {\n          label\n          actionType\n        }\n      }\n      ... on BoSearchCarousel {\n        snippets {\n          id\n          isFresh\n          ...snippetFieldsCommon\n        }\n      }\n      ... on BoSearchSurvey {\n        id\n        type\n        title\n        surveyKey\n        options {\n          type\n          title\n          formId\n        }\n      }\n      ... on BoSearchAdFoxBanner {\n        adUnitId\n      }\n    }\n  }\n}\n      fragment snippetFieldsCommon on BoSearchSnippet {\n  score\n  title\n  description\n  isReposted\n  lastUpdateDate\n  analyticsData {\n    caseId\n    score\n  }\n  geo {\n    clientMayCome {\n      address\n      geoplaces {\n        code\n        color\n        distance\n        name\n      }\n      prefix\n      suffix\n    }\n    orderLocation {\n      address\n      geoplaces {\n        code\n        color\n        distance\n        name\n        prepDistance\n      }\n      prefix\n      suffix\n    }\n    remote {\n      address\n      geoplaces {\n        code\n        color\n        distance\n        name\n        prepDistance\n      }\n      prefix\n      suffix\n    }\n  }\n  price {\n    prefix\n    suffix\n    value\n  }\n  secondPrice {\n    prefix\n    suffix\n    value\n  }\n  headerIcon\n  isViewed\n  shouldRequestRefuseReasons\n}',
        'variables': {
            'allVerticals': True,
            'searchQuery': '',
            'searchEntities': [],
            'pageSize': 20,
            'useSavedFilter': True,
            'sort': 'DEFAULT',
            'filter': {},
        },
    }

    # ---------------------------

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
            value=self.DEFAULT_TIME_THRESHOLD_KEY)
        # --- НОВАЯ ПЕРЕМЕННАЯ ---
        self.min_age_filter_var = ctk.BooleanVar(value=False)
        # ------------------------

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
            ("Пароль Profi.ru", "PROFI_PASSWORD", True)
        ]

        self.entries = {}
        for i, (text, name, is_password) in enumerate(fields):
            label = ctk.CTkLabel(
                config_frame,
                text=text,
                text_color=self.COLORS["text"]
            )
            label.grid(row=i, column=0, padx=10, pady=5, sticky="e")

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

        # Порог времени (Максимальный возраст)
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
        debug_checkbox.grid(row=row_idx, column=1, padx=10, pady=(5, 5), sticky="w")

        # --- НОВЫЙ ЧЕКБОКС: Минимальный возраст ---
        row_idx += 1
        min_age_checkbox = ctk.CTkCheckBox(
            config_frame,
            text=f"Не показывать заказы менее 1 минуты (профи их блокирует(иногда))",
            variable=self.min_age_filter_var,
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
        min_age_checkbox.grid(row=row_idx, column=1, padx=10, pady=(5, 10), sticky="w")
        # -----------------------------------

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
        telegram_link.bind("<Button-1>", lambda e: webbrowser.open("https://t.me/talk_dobrozor"))

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
                    self.min_age_filter_var.set(config.get("MIN_AGE_FILTER", False))  # Загрузка нового параметра

                    saved_threshold = config.get("TIME_THRESHOLD", self.DEFAULT_TIME_THRESHOLD_KEY)
                    if saved_threshold in self.TIME_THRESHOLD_OPTIONS:
                        self.time_threshold_var.set(saved_threshold)

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
                "TIME_THRESHOLD": self.time_threshold_var.get(),
                "MIN_AGE_FILTER": self.min_age_filter_var.get()  # Сохранение нового параметра
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

        if self.min_age_filter_var.get():
            self.log_message(f"🕒 Включен фильтр: не показывать заказы моложе 1 минуты.")

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
                "TIME_THRESHOLD_HOURS": time_threshold_hours,
                "BAD_WORDS": ["Опрос", "Опросы"],
                "CUSTOM_BAD_WORDS": custom_bad_words,
                "MIN_AGE_FILTER": self.min_age_filter_var.get()  # Передаем новый параметр
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

        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--mute-audio")
        chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        if not debug_mode:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-dev-shm-usage")

        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.implicitly_wait(5)
            self.log_message("✅ WebDriver запущен.")
            return driver
        except Exception as e:
            self.log_message(f"❌ Ошибка запуска WebDriver: {str(e)}")
            self.stop_monitoring()
            return None

    def _extract_token_value(self):
        """Извлекает и возвращает значение куки prfr_bo_tkn."""
        if not self.driver:
            return None
        try:
            cookies = self.driver.get_cookies()
            for cookie in cookies:
                if cookie.get('name') == 'prfr_bo_tkn':
                    token = cookie.get('value')
                    self.log_message(f"✅ Токен 'prfr_bo_tkn' успешно найден. Длина: {len(token)}.")
                    return token
            self.log_message("⚠️ Куки 'prfr_bo_tkn' не найдены.")
            return None
        except Exception as e:
            self.log_message(f"❌ Ошибка при извлечении куки: {str(e)}")
            return None

    def login(self, driver, config):
        """
        Авторизация на Profi.ru с ожиданием элемента на странице заказов.
        Возвращает токен или None.
        """
        if not driver:
            return None

        WAIT_TIMEOUT = 10
        PAGE_LOAD_TIMEOUT = 5

        try:
            self.log_message("🔑 Начинаю авторизацию: переход на страницу входа.")
            driver.get("https://profi.ru/backoffice/n.php")

            # 1. Ввод логина
            login_input = WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="auth_login_input"]'))
            )
            login_input.send_keys(config["PROFI"]["LOGIN"])
            self.log_message("➡️ Введен логин.")

            # 2. Ввод пароля
            password_input = WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"]'))
            )
            password_input.send_keys(config["PROFI"]["PASSWORD"])
            self.log_message("➡️ Введен пароль.")

            # 3. Клик по кнопке
            login_button = WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="enter_with_sms_btn"]'))
            )
            login_button.click()
            self.log_message("➡️ Нажата кнопка 'Продолжить'.")

            # --- ЛОГИКА ОЖИДАНИЯ И ИЗВЛЕЧЕНИЯ ТОКЕНА ---

            driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
            self.log_message(
                f"⏳ Установлен таймаут загрузки страницы: {PAGE_LOAD_TIMEOUT} сек. (Для обхода вечной загрузки).")

            try:
                # Ожидаем появления элемента на странице заказов
                self.log_message("➡️ Ожидаю появления элемента на странице заказов...")
                WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'a[data-testid$="_order-snippet"]'))
                )
            except TimeoutException:
                self.log_message("⚠️ Таймаут загрузки страницы (ожидаемо, чтобы избежать зависания).")
            finally:
                driver.set_page_load_timeout(300)  # Сбрасываем таймаут

            # Проверяем, не остались ли мы на странице логина
            if "login-form" in driver.current_url:
                self.log_message("❌ Авторизация не удалась. Проверьте логин/пароль.")
                return None

            # Извлекаем токен
            token = self._extract_token_value()
            return token

        except Exception as e:
            try:
                driver.set_page_load_timeout(300)
            except:
                pass
            self.log_message(f"❌ Критическая ошибка авторизации (Timeout или элемент не найден): {str(e)}")
            return None

    def send_telegram_message(self, config, order):
        try:
            bot = telebot.TeleBot(config["TELEGRAM"]["TOKEN"])

            # Обновленный формат сообщения
            message = f"<b>🆕 Новый заказ (ID: {order['id']})</b>\n\n"
            message += f"<b>{order['subject']}</b>\n"

            if order['price'] and order['price'] != "Цена не указана":
                message += f"<b>{order['price']}</b>\n"

            message += f"\n{order['description']}\n\n<i>{order['time_info']}</i>"

            markup = types.InlineKeyboardMarkup()

            # Кнопка для быстрого отклика
            markup.add(types.InlineKeyboardButton(
                text="Откликнуться",
                # Используем ID как ссылку
                url=f"https://profi.ru/backoffice/n.php?o={order['id']}"
            ))

            bot.send_message(
                chat_id=config["TELEGRAM"]["CHAT_ID"],
                text=message,
                reply_markup=markup,
                parse_mode='HTML'
            )
            self.log_message(f"➡️ Telegram: Отправлен заказ {order['id']} ({order['subject']})")
        except Exception as e:
            self.log_message(f"❌ Ошибка отправки в Telegram: {str(e)}")

    def clear_history(self):
        self.log_message(f"⏳ Поток очистки истории запущен. Интервал: 3600 сек.")
        while self.is_running:
            time.sleep(3600)
            if self.is_running:
                self.sent_links.clear()
                self.log_message("🧹 История отправленных ссылок очищена (плановая очистка)")

    def _format_price(self, price_data):
        """Форматирует данные о цене в строку."""
        prefix = price_data.get('prefix', '') or ''
        suffix = price_data.get('suffix', '') or ''
        value = price_data.get('value', 'Не указана') or 'Не указана'
        price_str = f"{prefix} {value} {suffix}".strip().replace('  ', ' ')
        return price_str if price_str.replace(' ', '') and price_str != 'Не указана' else "Цена не указана"

    def _get_relative_time(self, timestamp):
        """
        Преобразует UNIX timestamp (в секундах) в относительное время
        (например, "24 минуты назад").
        """
        if not timestamp:
            return "Время неизвестно"

        try:
            # UNIX timestamp из Profi приходит в секундах
            last_update = datetime.fromtimestamp(timestamp)
            now = datetime.now()
            delta = now - last_update

            if delta.total_seconds() < 60:
                seconds = int(delta.total_seconds())
                return f"{seconds} секунд назад"
            elif delta.total_seconds() < 3600:
                minutes = int(delta.total_seconds() // 60)
                return f"{minutes} минут назад"
            elif delta.total_seconds() < 86400:
                hours = int(delta.total_seconds() // 3600)
                hour_str = f"{hours} час"
                if hours == 1:
                    hour_str += " назад"
                elif 2 <= hours <= 4:
                    hour_str += "а назад"
                else:
                    hour_str += "ов назад"
                return hour_str
            else:
                return last_update.strftime("%d.%m.%Y %H:%M")
        except Exception:
            return "Время неизвестно"

    def is_recent_order(self, last_update_ts, max_hours):
        """
        Проверяет, является ли заказ "свежим" на основании UNIX-timestamp и максимального порога в часах.
        """
        # 99999 - это "Все"
        if max_hours >= self.TIME_THRESHOLD_OPTIONS["Все (без фильтра по времени)"]:
            return True  # Фильтр отключен

        if not last_update_ts:
            return True

        try:
            # Преобразование порога в timedelta
            max_delta = timedelta(hours=max_hours)

            # Текущее время минус возраст заказа
            order_datetime = datetime.fromtimestamp(last_update_ts)
            time_ago = datetime.now() - order_datetime

            return time_ago <= max_delta
        except Exception:
            self.log_message("⚠️ Ошибка при проверке максимального времени заказа (timestamp). Считаем свежим.")
            return True

    def is_valid_order(self, config, order):
        if not order or order["id"] == 'N/A':
            return False

        if order["id"] in self.sent_links:
            self.log_message(f"🚫 Пропущен заказ {order['id']}: уже был отправлен.")
            return False

        # --- ПРОВЕРКА НА МИНИМАЛЬНЫЙ ВОЗРАСТ (НОВЫЙ ФИЛЬТР) ---
        if config["FILTERS"]["MIN_AGE_FILTER"]:
            last_update_ts = order.get("lastUpdateDate")
            if last_update_ts:
                # Время в секундах, прошедшее с обновления заказа
                age_seconds = datetime.now().timestamp() - last_update_ts
                if age_seconds < self.MIN_ORDER_AGE_SECONDS:
                    self.log_message(
                        f"🚫 Пропущен заказ {order['id']}: слишком 'молодой' ({age_seconds:.1f} сек).")
                    return False
        # -----------------------------------------------------

        # --- ПРОВЕРКА НА СВЕЖЕСТЬ (МАКСИМАЛЬНЫЙ ВОЗРАСТ) ---
        if not self.is_recent_order(order["lastUpdateDate"], config["FILTERS"]["TIME_THRESHOLD_HOURS"]):
            time_info_for_log = self._get_relative_time(order["lastUpdateDate"]) if order[
                "lastUpdateDate"] else "Время неизвестно"
            self.log_message(
                f"🚫 Пропущен заказ {order['id']}: не соответствует порогу по времени ({time_info_for_log}).")
            return False
        # -----------------------------

        # Проверка на стоп-слова
        all_bad_words = config["FILTERS"]["BAD_WORDS"] + config["FILTERS"]["CUSTOM_BAD_WORDS"]
        subject_lower = order["subject"].lower()
        description_lower = order["description"].lower()

        for bad_word in all_bad_words:
            if bad_word.lower() in subject_lower or bad_word.lower() in description_lower:
                self.log_message(f"🚫 Пропущен заказ {order['id']}: стоп-слово '{bad_word}' в теме/описании.")
                return False

        return True

    def _fetch_and_process_orders(self, token, config):
        """Выполняет GraphQL запрос, парсит, фильтрует и отправляет заказы."""
        self.log_message("🔄 Запрос заказов через GraphQL API...")

        cookies = {
            'prfr_bo_tkn': token,
        }

        try:
            response = requests.post(
                self.GRAPHQL_URL,
                cookies=cookies,
                headers=self.API_HEADERS,
                json=self.API_JSON_DATA,
                timeout=30
            )

            # Если токен невалиден, API вернет 401 Unauthorized
            if response.status_code == 401:
                self.log_message("❌ Ошибка 401: Токен невалиден или просрочен.")
                return False  # Флаг для повторной авторизации

            response.raise_for_status()

            data = response.json()
            items = data.get('data', {}).get('boSearchBoardItems', {}).get('items', [])

            # Получаем только сниппеты заказов
            snippets = [item for item in items if item.get('type') == 'SNIPPET']

            if not snippets:
                self.log_message("⚠️ API вернул 0 заказов-сниппетов.")
                return True

            self.log_message(f"✅ Успешно получено {len(snippets)} заказов. Начинаю обработку.")

            new_orders_count = 0
            for item in snippets:
                # 1. Сбор данных
                order_data = {
                    "id": item.get('id', 'N/A'),
                    "subject": item.get('title', 'N/A'),
                    "description": item.get('description', 'Нет описания') or 'Нет описания',
                    "lastUpdateDate": item.get('lastUpdateDate'),
                    "link": item.get('id', 'N/A'),
                    "price": self._format_price(item.get('price', {})),
                }

                # 2. Фильтрация и отправка
                if self.is_valid_order(config, order_data):
                    # Отправка требует форматированного времени
                    order_data["time_info"] = self._get_relative_time(order_data["lastUpdateDate"])
                    self.send_telegram_message(config, order_data)
                    self.sent_links.add(order_data["id"])
                    new_orders_count += 1

            self.log_message(f"✨ За цикл отправлено новых заказов: {new_orders_count}")
            return True

        except requests.exceptions.RequestException as err:
            self.log_message(f"❌ Ошибка запроса к API: {err}")
            return True

        except Exception as e:
            self.log_message(f"❌ Критическая ошибка при обработке API ответа: {e}")
            return True

    def main_loop(self, config):
        # 1. Первая авторизация
        self.driver = self.init_driver(config["DEBUG_MODE"])
        if not self.driver:
            return

        token = self.login(self.driver, config)
        if not token:
            self.stop_monitoring()
            return

        # 2. Закрываем браузер для экономии ресурсов
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.log_message("🌐 Браузер закрыт. Переход на API-парсинг.")
            except:
                pass

        self.log_message("✅ Токен получен. Начало API-мониторинга...")

        while self.is_running:
            refresh_time = random.randint(*config["SLEEP"]["PAGE_REFRESH"])

            # 3. API ПАРСИНГ
            parsing_successful = self._fetch_and_process_orders(token, config)

            if not parsing_successful:
                # 4. Если токен невалиден (ошибка 401), пробуем получить новый токен.
                self.log_message("🚨 Токен невалиден или просрочен. Попытка переавторизации...")
                self.driver = self.init_driver(config["DEBUG_MODE"])
                if not self.driver:
                    self.stop_monitoring()
                    return

                new_token = self.login(self.driver, config)

                if new_token:
                    token = new_token
                    self.log_message("✅ Повторная авторизация успешна. Продолжаю мониторинг.")
                    try:
                        self.driver.quit()
                        self.driver = None
                    except:
                        pass
                else:
                    self.log_message("❌ Повторная авторизация не удалась. Останавливаю мониторинг.")
                    self.stop_monitoring()
                    return
            # --------------------

            if self.is_running:
                self.log_message(f"⏳ Следующий цикл через {refresh_time} сек.")
                time.sleep(refresh_time)

        # Выход из цикла - остановка мониторинга
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
            except:
                pass


if __name__ == "__main__":
    app = ProfiMonitorApp()
    app.mainloop()
