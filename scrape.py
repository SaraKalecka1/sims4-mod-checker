import json
import re
from playwright.sync_api import sync_playwright

def scrape_with_browser():
    url = "https://scarletsrealm.com/the-mod-list-sfw-nsfw-edition/"
    output_file = "scarlet_mods.json"
    
    print(f"🚀 Uruchamiam przeglądarkę i wchodzę na: {url}")

    with sync_playwright() as p:
        # Uruchamiamy przeglądarkę (headless = bez okna graficznego)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Zmienna do przechowywania przechwyconych danych
        captured_data = []

        # Funkcja, która "podsluchuje" odpowiedzi serwera
        def handle_response(response):
            # Szukamy odpowiedzi z admin-ajax.php (tam są dane tabeli)
            if "admin-ajax.php" in response.url and response.status == 200:
                try:
                    # Próbujemy odczytać JSON
                    json_body = response.json()
                    
                    # Sprawdzamy czy to ten duży JSON z danymi (ma klucz 'data' lub jest listą)
                    data_chunk = []
                    if isinstance(json_body, dict) and 'data' in json_body:
                        data_chunk = json_body['data']
                    elif isinstance(json_body, list):
                        data_chunk = json_body
                    
                    if data_chunk and len(data_chunk) > 0:
                        print(f"🎯 Przechwycono pakiet danych: {len(data_chunk)} rekordów!")
                        captured_data.extend(data_chunk)
                except:
                    pass # Ignorujemy odpowiedzi, które nie są JSONem

        # Włączamy nasłuchiwanie
        page.on("response", handle_response)

        # Wchodzimy na stronę
        # waitUntil='networkidle' oznacza "czekaj aż strona przestanie pobierać dane"
        page.goto(url, wait_until="networkidle", timeout=60000)
        
        # Opcjonalnie: Jeśli dane ładują się dopiero po przewinięciu lub kliknięciu, 
        # Playwright tutaj "czekał" i zbierał pakiety w tle.

        browser.close()

        if not captured_data:
            print("❌ Nie udało się przechwycić danych z sieci. Strona mogła zmienić metodę ładowania.")
            return

        # --- OBRÓBKA DANYCH (To samo co wcześniej) ---
        print(f"📦 Łącznie zebrano {len(captured_data)} surowych rekordów. Czyszczenie...")
        
        clean_mods = []
        from bs4 import BeautifulSoup # Używamy bs4 do czyszczenia HTML wewnątrz JSONa

        for item in captured_data:
            # Pobieranie pól (zabezpieczone .get)
            # NAME
            raw_name = item.get('name') or item.get('modname') or item.get('title') or ""
            soup_name = BeautifulSoup(raw_name, 'html.parser')
            clean_name = soup_name.get_text(strip=True)
            
            # LINK (Category)
            link_tag = soup_name.find('a', href=True)
            mod_url = link_tag['href'] if link_tag else item.get('modlink', '')
            if mod_url and mod_url.startswith('/'): mod_url = "https://scarletsrealm.com" + mod_url

            # AUTHOR
            raw_author = item.get('creators') or item.get('author') or item.get('creatorsname') or "Unknown"
            clean_author = BeautifulSoup(raw_author, 'html.parser').get_text(strip=True)

            # STATUS
            raw_status = item.get('status') or "Unknown"
            clean_status = BeautifulSoup(raw_status, 'html.parser').get_text(strip=True)

            # UPDATE
            clean_date = item.get('date') or item.get('last_updated') or ""

            if clean_name:
                clean_mods.append({
                    "name": clean_name,
                    "author": clean_author,
                    "category": mod_url,
                    "status": clean_status,
                    "update": clean_date
                })

        # Zapis do pliku
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(clean_mods, f, ensure_ascii=False, indent=2)

        print(f"✅ Sukces! Zapisano {len(clean_mods)} modów do '{output_file}'.")

if __name__ == "__main__":
    scrape_with_browser()
