import requests
import pandas as pd
import os
import time
from datetime import datetime, timedelta
from urllib.parse import urlparse

# --- НАСТРОЙКИ ---
TEST_MODE = False  # Поставь False для реального запуска на 30 минут

FEED_URL = "https://openphish.com/feed.txt"
CSV_FILE = "openphish_data.csv"  # Сохраняется в текущей директории запуска

if TEST_MODE:
    DURATION_MINUTES = 1
    INTERVAL_SECONDS = 10
    print("⚠️ ВКЛЮЧЕН ТЕСТОВЫЙ РЕЖИМ (1 минута, интервал 10 сек)")
else:
    DURATION_MINUTES = 30
    INTERVAL_SECONDS = 300  # 5 минут

def extract_brand(url: str) -> str:
    """
    Извлекает домен второго уровня как название бренда.
    Примеры: 
    - www.microsoft.com -> microsoft
    - login.microsoft.com -> microsoft
    - sberbank.ru -> sberbank
    """
    try:
        netloc = urlparse(url).netloc.lower()
        # Убираем www. если есть
        if netloc.startswith('www.'):
            netloc = netloc[4:]
        
        parts = netloc.split('.')
        parts = [p for p in parts if p] # Убираем пустые строки
        
        if len(parts) >= 2:
            # Предпоследний элемент обычно и есть домен второго уровня
            return parts[-2]
        return netloc # Если домен странный (например, просто 'localhost')
    except Exception:
        return "Unknown"

def fetch_and_process() -> list:
    """Запрашивает фид и преобразует его в список словарей."""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{current_time}] Запрос данных...")
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NetologyIBParser/1.0"}
        response = requests.get(FEED_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        urls = response.text.strip().split('\n')
        print(f"  → Получено строк: {len(urls)}")
        
        new_data = []
        for url in urls:
            url = url.strip()
            if not url or not url.startswith("http"):
                continue
            
            new_data.append({
                "URL": url,
                "Brand": extract_brand(url),
                "Detection_Time": current_time
            })
        return new_data
        
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Ошибка при запросе: {e}")
        return []

def save_to_csv(data: list):
    """Сохраняет данные в CSV с разделителем ';', удаляя дубликаты по URL."""
    if not data:
        print("  ⚠️ Нет данных для сохранения.")
        return
    
    df_new = pd.DataFrame(data)
    
    # Проверяем, существует ли файл и не пустой ли он
    if os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 0:
        try:
            df_existing = pd.read_csv(CSV_FILE, sep=";")
            # Объединяем и удаляем дубликаты по столбцу "URL", оставляя самую свежую запись
            df_combined = pd.concat([df_existing, df_new], ignore_index=True).drop_duplicates(subset=["URL"], keep="last")
        except Exception as e:
            print(f"  ⚠️ Ошибка чтения существующего CSV, создаем новый: {e}")
            df_combined = df_new
    else:
        df_combined = df_new
        
    # Сохраняем с разделителем ';'
    df_combined.to_csv(CSV_FILE, index=False, encoding="utf-8", sep=";")
    print(f"  ✅ Сохранено. Всего уникальных записей в файле: {len(df_combined)}")

def main():
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=DURATION_MINUTES)
    
    print("="*50)
    print(f"🚀 Запуск парсера OpenPhish")
    print(f"🕒 Начало: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🏁 Окончание: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    iteration = 1
    while datetime.now() < end_time:
        print(f"\n--- Итерация {iteration} ({datetime.now().strftime('%H:%M:%S')}) ---")
        
        data = fetch_and_process()
        save_to_csv(data)
        
        # Вычисляем оставшееся время для сна, чтобы не выйти за рамки DURATION_MINUTES
        time_left = (end_time - datetime.now()).total_seconds()
        if time_left > INTERVAL_SECONDS:
            sleep_time = INTERVAL_SECONDS
        elif time_left > 0:
            sleep_time = time_left
        else:
            break
            
        print(f"  💤 Ожидание {int(sleep_time)} сек. до следующей итерации...")
        time.sleep(sleep_time)
        iteration += 1
        
    print("\n" + "="*50)
    print("🏁 Парсинг успешно завершен!")
    print(f"📁 Результаты сохранены в: {os.path.abspath(CSV_FILE)}")
    print("="*50)
    
    # Бонус: сразу покажем предварительную статистику
    if os.path.exists(CSV_FILE):
        df_final = pd.read_csv(CSV_FILE, sep=";")
        print(f"\n📊 Предварительная статистика:")
        print(f"   Всего уникальных URL: {len(df_final)}")
        print(f"   Топ-3 атакуемых бренда:")
        top_brands = df_final['Brand'].value_counts().head(3)
        for brand, count in top_brands.items():
            print(f"   - {brand}: {count}")

if __name__ == "__main__":
    main()