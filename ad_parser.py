import requests
from bs4 import BeautifulSoup
import telegram
import time
import json
import os
from urllib.parse import urljoin
import asyncio

# Настройки
SITE_URL = "https://goszakup.gov.kz/ru/search/lots?filter%5Bname%5D=&filter%5Bnumber%5D=&filter%5Bnumber_anno%5D=&filter%5Benstru%5D=&filter%5Bstatus%5D%5B%5D=360&filter%5Bcustomer%5D=&filter%5Bamount_from%5D=100000000&filter%5Bamount_to%5D=&filter%5Btrade_type%5D=&filter%5Bmonth%5D=&filter%5Bplan_number%5D=&filter%5Bend_date_from%5D=&filter%5Bend_date_to%5D=&filter%5Bstart_date_to%5D=&filter%5Byear%5D=&filter%5Bitogi_date_from%5D=&filter%5Bitogi_date_to%5D=&filter%5Bstart_date_from%5D=&filter%5Bmore%5D=&smb="
SELECTOR = 'a[href^="/ru/announce/index/"]'
BOT_TOKEN = os.getenv("BOT_TOKEN", "7284910740:AAHutbJFnGCdL9xMfySjikQFhNPKVavb_8I")
CHAT_ID = os.getenv("CHAT_ID", "-4955461543")  # Замени на CHAT_ID группы
DATA_FILE = "seen_ads.json"
LOG_FILE = "parser_log.txt"

# Функция логирования
def log_message(message):
    timestamp = time.ctime()
    with open(LOG_FILE, 'a') as log:
        log.write(f"{timestamp}: {message}\n")
    print(f"{timestamp}: {message}")

# Инициализация Telegram-бота
log_message("Инициализация бота...")
try:
    bot = telegram.Bot(token=BOT_TOKEN)
    log_message("Бот успешно инициализирован")
except Exception as e:
    log_message(f"Ошибка инициализации бота: {e}")

# Функции для работы с файлом
def load_seen_ads():
    log_message(f"Проверка наличия {DATA_FILE}")
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                ads = set(json.load(f))
                log_message(f"Загружено {len(ads)} объявлений из {DATA_FILE}")
                return ads
        except json.JSONDecodeError as e:
            log_message(f"Ошибка чтения {DATA_FILE}: {e}. Начинаем с пустого списка")
            return set()
    log_message(f"Файл {DATA_FILE} не найден, начинаем с пустого списка")
    return set()

def save_seen_ads(seen_ads):
    log_message(f"Попытка сохранить {len(seen_ads)} объявлений в {DATA_FILE}")
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(list(seen_ads), f, indent=2)
        log_message(f"Успешно сохранено {len(seen_ads)} объявлений в {DATA_FILE}")
        with open(DATA_FILE, 'r') as f:
            log_message(f"Содержимое {DATA_FILE}: {f.read()}")
        if os.path.exists(DATA_FILE):
            log_message(f"Файл {DATA_FILE} подтверждён в директории")
        else:
            log_message(f"Файл {DATA_FILE} НЕ найден после сохранения")
    except Exception as e:
        log_message(f"Ошибка при сохранении {DATA_FILE}: {e}")

# Функция парсинга объявлений
def parse_ads():
    log_message(f"Проверка SELECTOR: {SELECTOR}")
    try:
        log_message(f"Выполняется запрос к {SITE_URL}")
        response = requests.get(SITE_URL, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        ad_links = [urljoin(SITE_URL, a['href']) for a in soup.select(SELECTOR)]
        log_message(f"Найдено {len(ad_links)} ссылок: {ad_links[:5]}")
        return set(ad_links)
    except Exception as e:
        log_message(f"Ошибка при парсинге: {e}")
        return set()

# Асинхронная функция отправки уведомления в Telegram
async def send_telegram_notification(link):
    log_message(f"Отправка уведомления в Telegram группу (CHAT_ID: {CHAT_ID}): {link}")
    try:
        await bot.send_message(chat_id=CHAT_ID, text=f"Новое объявление: {link}")
        log_message(f"Успешно отправлено уведомление в Telegram группу (CHAT_ID: {CHAT_ID}): {link}")
    except Exception as e:
        log_message(f"Ошибка при отправке уведомления в Telegram группу (CHAT_ID: {CHAT_ID}): {e}")

# Проверка новых объявлений
async def check_new_ads():
    log_message("Проверка новых объявлений...")
    seen_ads = load_seen_ads()
    log_message(f"Текущее количество seen_ads: {len(seen_ads)}")
    current_ads = parse_ads()
    log_message(f"Текущее количество current_ads: {len(current_ads)}")
    new_ads = current_ads - seen_ads
    if new_ads:
        log_message(f"Найдено {len(new_ads)} новых объявлений")
        for ad in new_ads:
            await send_telegram_notification(ad)
            seen_ads.add(ad)
    else:
        log_message("Новых объявлений нет")
    log_message(f"Перед сохранением seen_ads: {len(seen_ads)} объявлений")
    save_seen_ads(seen_ads)
    return seen_ads

# Главная функция
if __name__ == "__main__":
    log_message("Парсер запущен...")
    try:
        asyncio.run(check_new_ads())
        log_message("Парсер завершил работу")
    except Exception as e:
        log_message(f"Ошибка выполнения парсера: {e}")
