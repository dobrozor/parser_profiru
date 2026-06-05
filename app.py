import tkinter as tk
import time
import random
import threading
import requests
from datetime import datetime, timedelta
import telebot
from telebot import types
import json
import os
import customtkinter as ctk
import webbrowser
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


class ProfiMonitorApp(ctk.CTk):
    CONFIG_FILE = "profi_config.json"

    COLORS = {
        "primary": "#2B2B2B",
        "secondary": "#FFFFFF",
        "accent": "#FF6D00",
        "success": "#4CAF50",
        "danger": "#F44336",
        "text": "#333333",
        "widget_bg": "#F5F5F5",
        "border": "#E0E0E0"
    }

    TIME_THRESHOLD_OPTIONS = {
        "Меньше 1 часа": 1,
        "Меньше 3 часов": 3,
        "Меньше 6 часов": 6,
        "Меньше 12 часов": 12,
        "Меньше 24 часов (сутки)": 24,
        "Все (без фильтра по времени)": 99999
    }
    DEFAULT_TIME_THRESHOLD_KEY = "Меньше 6 часов"
    MIN_ORDER_AGE_SECONDS = 70

    GRAPHQL_URL = "https://rnd.profi.ru/graphql"

    # Обновленные заголовки с актуальным User-Agent
    API_HEADERS = {
        "origin": "https://rnd.profi.ru",
        "referer": "https://rnd.profi.ru/backoffice/n.php",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 YaBrowser/25.10.0.0 Safari/537.36",
        "x-app-id": "BO",
        "x-new-auth-compatible": "1",
    }

    # Рабочий GraphQL запрос со специальной сигнатурой и доменами
    GRAPHQL_QUERY = (
        "#prfrtkn:webbo:36bb338fde61287ba8723d0687db52f33ab381d8:9b53a063284429f629f81506c40339c13822dd22\n\n"
        "      query BoSearchBoardItems($filter: BoSearchFrontFiltersInput!, $useSavedFilter: Boolean, $allVerticals: Boolean, $searchQuery: String, $searchEntities: [BoSearchEntityInput!], $searchId: ID, $nextCursor: String, $pageSize: Int, $boSortUp: Int, $minScore: Float, $coordinates: BoSearchAreaInput, $clusterId: ID, $sort: BoSearchSortEnum) @domain(domains: [BO_BOARD, BO_BOARD_LIST]) {\n"
        "  boSearchBoardItems(\n"
        "    filter: $filter\n"
        "    useSavedFilter: $useSavedFilter\n"
        "    allVerticals: $allVerticals\n"
        "    searchQuery: $searchQuery\n"
        "    searchEntities: $searchEntities\n"
        "    searchId: $searchId\n"
        "    nextCursor: $nextCursor\n"
        "    pageSize: $pageSize\n"
        "    boSortUp: $boSortUp\n"
        "    minScore: $minScore\n"
        "    coordinates: $coordinates\n"
        "    clusterId: $clusterId\n"
        "    sort: $sort\n"
        "  ) {\n"
        "    nextCursor\n"
        "    serverTs\n"
        "    totalCount\n"
        "    analytics {\n"
        "      boardSearchQuery\n"
        "      boardSearchUsed\n"
        "    }\n"
        "    items {\n"
        "      id\n"
        "      type\n"
        "      ... on BoSearchPremiumBlock {\n"
        "        title\n"
        "        description\n"
        "        buttonLabel\n"
        "      }\n"
        "      ... on BoSearchPremiumRepeatBlock {\n"
        "        title\n"
        "      }\n"
        "      ... on BoSearchSnippet {\n"
        "        ...snippetFieldsCommon\n"
        "        isFresh\n"
        "        coordinates {\n"
        "          lat\n"
        "          lon\n"
        "        }\n"
        "        clientInfo {\n"
        "          name\n"
        "        }\n"
        "        clientTags {\n"
        "          value\n"
        "        }\n"
        "        badges {\n"
        "          id\n"
        "          imageKey\n"
        "          label\n"
        "        }\n"
        "        status {\n"
        "          text\n"
        "          color\n"
        "        }\n"
        "        schedule\n"
        "        images {\n"
        "          host\n"
        "          width\n"
        "          height\n"
        "          original\n"
        "        }\n"
        "      }\n"
        "      ... on BoSearchEmptyState {\n"
        "        view {\n"
        "          title\n"
        "          description\n"
        "          imageKey\n"
        "          button {\n"
        "            label\n"
        "            actionType\n"
        "          }\n"
        "        }\n"
        "      }\n"
        "      ... on BoSearchStories {\n"
        "        id\n"
        "        type\n"
        "      }\n"
        "      ... on BoSearchDivider {\n"
        "        title\n"
        "        button {\n"
        "          label\n"
        "          actionType\n"
        "        }\n"
        "      }\n"
        "      ... on BoSearchCarousel {\n"
        "        snippets {\n"
        "          id\n"
        "          isFresh\n"
        "          ...snippetFieldsCommon\n"
        "        }\n"
        "      }\n"
        "      ... on BoSearchSurvey {\n"
        "        id\n"
        "        type\n"
        "        title\n"
        "        surveyKey\n"
        "        options {\n"
        "          type\n"
        "          title\n"
        "          formId\n"
        "        }\n"
        "      }\n"
        "      ... on BoSearchAdFoxBanner {\n"
        "        adUnitId\n"
        "      }\n"
        "    }\n"
        "  }\n"
        "}\n"
        "      fragment snippetFieldsCommon on BoSearchSnippet {\n"
        "  score\n"
        "  title\n"
        "  description\n"
        "  isReposted\n"
        "  lastUpdateDate\n"
        "  analyticsData {\n"
        "    caseId\n"
        "    score\n"
        "  }\n"
        "  geo {\n"
        "    clientMayCome {\n"
        "      address\n"
        "      geoplaces {\n"
        "        code\n"
        "        color\n"
        "        distance\n"
        "        name\n"
        "      }\n"
        "      prefix\n"
        "      suffix\n"
        "    }\n"
        "    orderLocation {\n"
        "      address\n"
        "      geoplaces {\n"
        "        code\n"
        "        color\n"
        "        distance\n"
        "        name\n"
        "        prepDistance\n"
        "      }\n"
        "      prefix\n"
        "      suffix\n"
        "    }\n"
        "    remote {\n"
        "      address\n"
        "      geoplaces {\n"
        "        code\n"
        "        color\n"
        "        distance\n"
        "        name\n"
        "        prepDistance\n"
        "      }\n"
        "      prefix\n"
        "      suffix\n"
        "    }\n"
        "  }\n"
        "  price {\n"
        "    prefix\n"
        "    suffix\n"
        "    value\n"
        "  }\n"
        "  secondPrice {\n"
        "    prefix\n"
        "    suffix\n"
        "    value\n"
        "  }\n"
        "  headerIcon\n"
        "  isViewed\n"
        "  shouldRequestRefuseReasons\n"
        "}"
    )

    API_VARIABLES = {
        "allVerticals": True,
        "searchQuery": "",
        "searchEntities": [],
        "pageSize": 20,
        "useSavedFilter": True,
        "sort": "DEFAULT",
        "filter": {},
    }

    def __init__(self):
        super().__init__()
        self.title("Profi.ru Monitor")
        self.geometry("500x780")
        self.minsize(780, 780)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.pw_instance = None
        self.browser = None
        self.context = None

        self.sent_links: set = set()
        self.is_running = False
        self._stop_event = threading.Event()

        self.debug_mode = ctk.BooleanVar(value=False)
        self.time_threshold_var = ctk.StringVar(value=self.DEFAULT_TIME_THRESHOLD_KEY)
        self.min_age_filter_var = ctk.BooleanVar(value=False)

        self.entries: dict = {}
        self.create_widgets()
        self.load_config()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.log_message("✅ Приложение инициализировано.")

    # ──────────────────────────── UI ────────────────────────────

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.configure(fg_color=self.COLORS["secondary"])

        ctk.CTkLabel(
            self, text="Profi Monitor",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.COLORS["primary"]
        ).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nw")

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)

        config_frame = ctk.CTkFrame(
            main_frame, corner_radius=12,
            fg_color=self.COLORS["widget_bg"],
            border_width=1, border_color=self.COLORS["border"]
        )
        config_frame.grid(row=0, column=0, padx=0, pady=(0, 15), sticky="nsew")

        fields = [
            ("Telegram Token", "TELEGRAM_TOKEN", False),
            ("Chat ID", "TELEGRAM_CHAT_ID", False),
            ("Логин Profi.ru", "PROFI_LOGIN", False),
            ("Пароль Profi.ru", "PROFI_PASSWORD", True),
        ]
        for i, (label_text, name, is_pw) in enumerate(fields):
            ctk.CTkLabel(config_frame, text=label_text, text_color=self.COLORS["text"]).grid(
                row=i, column=0, padx=10, pady=5, sticky="e"
            )
            entry = ctk.CTkEntry(
                config_frame, width=400, corner_radius=8,
                fg_color="white", border_color=self.COLORS["border"],
                text_color=self.COLORS["text"],
                show="•" if is_pw else "",
                font=ctk.CTkFont(size=14)
            )
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            self.entries[name] = entry

        row = len(fields)
        ctk.CTkLabel(config_frame, text="Доп. стоп-слова", text_color=self.COLORS["text"]).grid(
            row=row, column=0, padx=10, pady=5, sticky="e"
        )
        bad_words_entry = ctk.CTkEntry(
            config_frame, width=400, corner_radius=8,
            fg_color="white", border_color=self.COLORS["border"],
            text_color=self.COLORS["text"], font=ctk.CTkFont(size=14),
            placeholder_text="Введите слова через запятую"
        )
        bad_words_entry.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        self.entries["CUSTOM_BAD_WORDS"] = bad_words_entry
        row += 1

        ctk.CTkLabel(config_frame, text="Макс. возраст заказа", text_color=self.COLORS["text"]).grid(
            row=row, column=0, padx=10, pady=5, sticky="e")
        ctk.CTkOptionMenu(
            config_frame, variable=self.time_threshold_var,
            values=list(self.TIME_THRESHOLD_OPTIONS.keys()),
            corner_radius=8, fg_color="white",
            button_color=self.COLORS["border"], button_hover_color="#EFEFEF",
            text_color=self.COLORS["text"], font=ctk.CTkFont(size=14)
        ).grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        row += 1

        checkbox_cfg = dict(checkbox_width=18, checkbox_height=18, corner_radius=4,
                            border_width=1, border_color=self.COLORS["border"],
                            fg_color=self.COLORS["accent"], hover_color="#FF8000", text_color=self.COLORS["text"])
        ctk.CTkCheckBox(config_frame, text="Отладка (показывать браузер)",
                        variable=self.debug_mode, **checkbox_cfg).grid(row=row, column=1, padx=10, pady=5, sticky="w")
        row += 1
        ctk.CTkCheckBox(config_frame, text="Не показывать заказы менее 1 минуты",
                        variable=self.min_age_filter_var, **checkbox_cfg).grid(row=row, column=1, padx=10, pady=(0, 10),
                                                                               sticky="w")

        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.grid(row=1, column=0, pady=(0, 15), sticky="ew")

        self.start_btn = ctk.CTkButton(btn_frame, text="Запустить мониторинг", command=self.start_monitoring,
                                       corner_radius=8, height=40, fg_color=self.COLORS["accent"])
        self.start_btn.pack(side="left", padx=(0, 10), fill="x", expand=True)
        self.stop_btn = ctk.CTkButton(btn_frame, text="Остановить", command=self.stop_monitoring, state="disabled",
                                      corner_radius=8, height=40, fg_color=self.COLORS["danger"])
        self.stop_btn.pack(side="right", fill="x", expand=True)

        log_frame = ctk.CTkFrame(main_frame, corner_radius=12, fg_color=self.COLORS["widget_bg"], border_width=1,
                                 border_color=self.COLORS["border"])
        log_frame.grid(row=2, column=0, sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        self.log_area = ctk.CTkTextbox(log_frame, wrap="word", font=ctk.CTkFont(family="Consolas", size=12),
                                       fg_color="white", text_color=self.COLORS["text"])
        self.log_area.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        footer = ctk.CTkFrame(self, fg_color="transparent", height=40)
        footer.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="sew")
        lbl = ctk.CTkLabel(footer, text="Разработка от dobrozor", text_color=self.COLORS["text"],
                           font=ctk.CTkFont(size=12, slant="italic"))
        lbl.pack(side="left")

    def on_close(self):
        self.stop_monitoring()
        self.destroy()

    def log_message(self, message: str):
        self.log_area.configure(state="normal")
        self.log_area.insert("end", f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.log_area.see("end")
        self.log_area.configure(state="disabled")

    # ──────────────────────────── Config ────────────────────────────

    def load_config(self):
        if not os.path.exists(self.CONFIG_FILE): return
        try:
            with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            for key, entry in self.entries.items():
                entry.insert(0, cfg.get(key, ""))
            self.debug_mode.set(cfg.get("DEBUG_MODE", False))
            self.min_age_filter_var.set(cfg.get("MIN_AGE_FILTER", False))
            self.time_threshold_var.set(cfg.get("TIME_THRESHOLD", self.DEFAULT_TIME_THRESHOLD_KEY))
        except:
            pass

    def save_config(self):
        try:
            cfg = {**{k: v.get() for k, v in self.entries.items()}, "DEBUG_MODE": self.debug_mode.get(),
                   "TIME_THRESHOLD": self.time_threshold_var.get(), "MIN_AGE_FILTER": self.min_age_filter_var.get()}
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except:
            pass

    # ──────────────────────────── Monitoring control ────────────────────────────

    def _build_config(self) -> dict:
        threshold_key = self.time_threshold_var.get()
        threshold_hours = self.TIME_THRESHOLD_OPTIONS.get(threshold_key, 6)
        raw_bad = self.entries["CUSTOM_BAD_WORDS"].get().strip()
        custom_bad = [w.strip().lower() for w in raw_bad.split(",") if w.strip()] if raw_bad else []
        return {
            "TELEGRAM": {"TOKEN": self.entries["TELEGRAM_TOKEN"].get(),
                         "CHAT_ID": self.entries["TELEGRAM_CHAT_ID"].get()},
            "PROFI": {"LOGIN": self.entries["PROFI_LOGIN"].get(), "PASSWORD": self.entries["PROFI_PASSWORD"].get()},
            "FILTERS": {"TIME_THRESHOLD_HOURS": threshold_hours, "BAD_WORDS": ["Опрос"], "CUSTOM_BAD_WORDS": custom_bad,
                        "MIN_AGE_FILTER": self.min_age_filter_var.get()},
            "SLEEP": {"PAGE_REFRESH": (45, 110)}, "DEBUG_MODE": self.debug_mode.get(), "_threshold_key": threshold_key,
        }

    def start_monitoring(self):
        self.save_config()
        required = [k for k in self.entries if k != "CUSTOM_BAD_WORDS"]
        if not all(self.entries[k].get() for k in required):
            self.log_message("❌ Заполните все поля!")
            return

        config = self._build_config()
        self.is_running = True
        self._stop_event.clear()

        self.start_btn.configure(state="disabled", fg_color=self.COLORS["success"])
        self.stop_btn.configure(state="normal")

        threading.Thread(target=self.main_loop, args=(config,), daemon=True).start()
        threading.Thread(target=self._clear_history_loop, daemon=True).start()
        self.log_message("🚀 Мониторинг запущен.")

    def stop_monitoring(self):
        self.is_running = False
        self._stop_event.set()
        self.start_btn.configure(state="normal", fg_color=self.COLORS["accent"])
        self.stop_btn.configure(state="disabled")
        self._stop_pw()
        self.log_message("🛑 Остановлено.")

    def _start_pw(self, debug_mode: bool):
        self.log_message(f"🌐 Инициализация Playwright (отладка: {'ВКЛ' if debug_mode else 'ВЫКЛ'})...")
        try:
            self.pw_instance = sync_playwright().start()
            self.browser = self.pw_instance.chromium.launch(
                channel="msedge",
                headless=not debug_mode,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
            )
            self.context = self.browser.new_context(viewport={'width': 1920, 'height': 1080})
            self.log_message("✅ Браузер запущен.")
            return True
        except Exception as e:
            self.log_message(f"❌ Ошибка запуска браузера: {e}")
            return False

    def _stop_pw(self):
        try:
            if self.context: self.context.close()
            if self.browser: self.browser.close()
            if self.pw_instance: self.pw_instance.stop()
        except:
            pass
        self.pw_instance = None
        self.log_message("🌐 Браузер закрыт.")

    def login(self, config) -> str | None:
        if not self.context: return None
        page = self.context.new_page()
        try:
            self.log_message("🔑 Переход на страницу авторизации...")
            page.goto("https://profi.ru/backoffice/n.php", timeout=30000)

            page.wait_for_selector('[data-testid="auth_login_input"]', timeout=10000)
            page.fill('[data-testid="auth_login_input"]', config["PROFI"]["LOGIN"])

            page.fill('input[type="password"]', config["PROFI"]["PASSWORD"])

            page.click('[data-testid="enter_with_sms_btn"]')
            self.log_message("➡️ Данные отправлены. Ожидаю авторизации...")

            try:
                page.wait_for_selector('a[data-testid$="_order-snippet"]', timeout=15000)
            except:
                pass

            if "login-form" in page.url:
                self.log_message("❌ Ошибка: все еще на странице логина.")
                return None

            cookies = self.context.cookies()
            for cookie in cookies:
                if cookie['name'] == "prfr_bo_tkn":
                    token = cookie['value']
                    self.log_message(f"✅ Токен получен (длина {len(token)}).")
                    return token

            self.log_message("⚠️ Кука 'prfr_bo_tkn' не найдена.")
            return None

        except PlaywrightTimeoutError:
            self.log_message("❌ Тайм-аут ожидания элементов страницы.")
            return None
        except Exception as e:
            self.log_message(f"❌ Ошибка в процессе входа: {e}")
            return None
        finally:
            page.close()

    # ──────────────────────────── API / Orders ────────────────────────────

    def _fetch_and_process_orders(self, token, config):
        try:
            resp = requests.post(
                self.GRAPHQL_URL,
                cookies={"prfr_bo_tkn": token},
                headers=self.API_HEADERS,
                json={"query": self.GRAPHQL_QUERY, "variables": self.API_VARIABLES},
                timeout=20
            )

            if resp.status_code == 401:
                return False

            data = resp.json()
            items = data.get("data", {}).get("boSearchBoardItems", {}).get("items", [])

            self.log_message(f"🔍 Проверка API: получено {len(items)} объектов.")

            sent = 0
            for item in [i for i in items if i.get("type") == "SNIPPET"]:
                order = {
                    "id": item.get("id"),
                    "subject": item.get("title"),
                    "description": item.get("description") or "...",
                    "lastUpdateDate": item.get("lastUpdateDate"),
                    "price": self._format_price(item.get("price") or {})
                }

                if self.is_valid_order(config, order):
                    order["time_info"] = self._get_relative_time(order["lastUpdateDate"])
                    self.send_telegram_message(config, order)
                    self.sent_links.add(order["id"])
                    sent += 1

            if sent > 0:
                self.log_message(f"✨ Отправлено в Telegram: {sent}")
            elif len(items) > 0:
                self.log_message("ℹ️ Новых заказов по вашим фильтрам пока нет.")

            return True
        except Exception as e:
            self.log_message(f"⚠️ Ошибка запроса: {e}")
            return True

    @staticmethod
    def _format_price(p):
        res = " ".join(filter(None, [p.get("prefix"), p.get("value"), p.get("suffix")]))
        return res if res else "Цена не указана"

    @staticmethod
    def _get_relative_time(ts):
        if not ts: return "Неизвестно"
        d = (datetime.now() - datetime.fromtimestamp(ts)).total_seconds()
        if d < 60: return f"{int(d)} сек. назад"
        if d < 3600: return f"{int(d // 60)} мин. назад"
        return f"{int(d // 3600)} час. назад"

    def is_recent_order(self, ts, max_hours: int) -> bool:
        if max_hours >= self.TIME_THRESHOLD_OPTIONS["Все (без фильтра по времени)"]:
            return True
        if not ts:
            return True
        try:
            return (datetime.now() - datetime.fromtimestamp(ts)) <= timedelta(hours=max_hours)
        except Exception:
            return True

    def is_valid_order(self, config, order):
        if not order.get("id") or order["id"] in self.sent_links: return False
        ts = order.get("lastUpdateDate")
        if config["FILTERS"]["MIN_AGE_FILTER"] and ts:
            if (time.time() - ts) < self.MIN_ORDER_AGE_SECONDS: return False
        if ts and (datetime.now() - datetime.fromtimestamp(ts)) > timedelta(
            hours=config["FILTERS"]["TIME_THRESHOLD_HOURS"]): return False
        text = f"{order['subject']} {order['description']}".lower()
        for w in (config["FILTERS"]["BAD_WORDS"] + config["FILTERS"]["CUSTOM_BAD_WORDS"]):
            if w in text: return False
        return True

    def send_telegram_message(self, config, order):
        try:
            bot = telebot.TeleBot(config["TELEGRAM"]["TOKEN"])
            msg = f"<b>{order['subject']}</b>\n<b>{order['price']}</b>\n\n{order['description']}\n\n<i>{order['time_info']}</i>"
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("Откликнуться", url=f"https://profi.ru/backoffice/n.php?o={order['id']}"))
            bot.send_message(config["TELEGRAM"]["CHAT_ID"], msg, reply_markup=kb, parse_mode="HTML")
        except:
            pass

    # ──────────────────────────── Background threads ────────────────────────────

    def _clear_history_loop(self):
        while self.is_running:
            if self._stop_event.wait(timeout=3600): break
            self.sent_links.clear()
            self.log_message("🧹 История ссылок очищена.")

    def main_loop(self, config: dict):
        if not self._start_pw(config["DEBUG_MODE"]):
            self.stop_monitoring()
            return

        token = self.login(config)
        self._stop_pw()

        if not token:
            self.log_message("❌ Не удалось получить токен. Проверьте логин/пароль.")
            self.stop_monitoring()
            return

        self.log_message("✅ Начинаю API-мониторинг.")
        while self.is_running:
            ok = self._fetch_and_process_orders(token, config)

            if not ok:
                self.log_message("🚨 Сессия isteklа. Переавторизация...")
                if self._start_pw(config["DEBUG_MODE"]):
                    new_token = self.login(config)
                    self._stop_pw()
                    if new_token:
                        token = new_token
                        continue
                self.stop_monitoring()
                return

            delay = random.randint(*config["SLEEP"]["PAGE_REFRESH"])
            self.log_message(f"⏳ Ожидание {delay} сек. до следующей проверки...")
            if self._stop_event.wait(timeout=delay):
                break


if __name__ == "__main__":
    app = ProfiMonitorApp()
    app.mainloop()
