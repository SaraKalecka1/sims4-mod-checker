import requests
import json
import re
from bs4 import BeautifulSoup

def scrape_scarlet_final():
    base_url = "https://scarletsrealm.com/the-mod-list-sfw-nsfw-edition/"
    ajax_url = "https://scarletsrealm.com/wp-admin/admin-ajax.php"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': base_url
    }

    print(f"🕵️  Szukanie ID tabeli na stronie: {base_url}")
    
    try:
        # KROK 1: Znajdź ID tabeli
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        match = re.search(r'ninja_table_table_(\d+)', response.text)
        
        if not match:
            print("❌ Nie znaleziono ID tabeli. Spróbuję domyślnego ID (często 105 lub 42).")
            # Jeśli automat zawiedzie, skrypt spróbuje zgadnąć ID, ale lepiej żeby znalazł
            return

        table_id = match.group(1)
        print(f"✅ Znaleziono Table ID: {table_id}")

        # KROK 2: Pobierz dane z API
        print(f"🚀 Pobieranie bazy danych...")
        payload = {
            'action': 'ninja_tables_data',
            'table_id': table_id,
            'id': table_id,
            'ninja_table_public_request': 1,
            'limit': 10000,
            'skip_rows': 0,
            'chunk_size': 10000
        }

        api_response = requests.post(ajax_url, data=payload, headers=headers)
        api_response.raise_for_status()
        json_response = api_response.json()

        # Obsługa różnych struktur odpowiedzi
        if isinstance(json_response, list):
            raw_data = json_response
        elif isinstance(json_response, dict) and 'data' in json_response:
            raw_data = json_response['data']
        else:
            raw_data = []

        print(f"📦 Pbrano {len(raw_data)} rekordów. Rozpoczynam czyszczenie...")

        clean_mods = []
        
        for item in raw_data:
            # --- SEKCJA PANCERNA: Próba pobrania danych z różnych możliwych nazw kluczy ---
            
            # 1. NAZWA i LINK
            # Sprawdzamy klucze: 'name', 'modname', 'title'
            raw_name_html = item.get('name') or item.get('modname') or item.get('title') or ""
            
            # Czyścimy HTML (wyciągamy tekst i link)
            soup = BeautifulSoup(raw_name_html, 'html.parser')
            clean_name = soup.get_text(strip=True)
            
            # Link wyciągamy z tagu <a> w nazwie LUB z dedykowanego pola 'modlink'
            link_tag = soup.find('a', href=True)
            mod_url = link_tag['href'] if link_tag else item.get('modlink', '')
            
            # Jeśli link jest względny (zaczyna się od /), dodaj domenę (rzadkie, ale możliwe)
            if mod_url and mod_url.startswith('/'):
                mod_url = "https://scarletsrealm.com" + mod_url

            # 2. AUTOR
            # Sprawdzamy klucze: 'creators', 'author', 'creatorsname'
            raw_author = item.get('creators') or item.get('author') or item.get('creatorsname') or "Unknown"
            clean_author = BeautifulSoup(raw_author, 'html.parser').get_text(strip=True)

            # 3. STATUS
            raw_status = item.get('status') or "Unknown"
            clean_status = BeautifulSoup(raw_status, 'html.parser').get_text(strip=True)

            # 4. DATA
            clean_date = item.get('date') or item.get('last_updated') or ""

            # Pomijamy puste rekordy (bez nazwy)
            if not clean_name:
                continue

            entry = {
                "name": clean_name,
                "author": clean_author,
                "category": mod_url, # URL w polu category
                "status": clean_status,
                "update": clean_date
            }
            
            clean_mods.append(entry)

        # KROK 3: Zapis
        output_file = "scarlet_mods.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(clean_mods, f, ensure_ascii=False, indent=2)

        print(f"✅ Sukces! Zapisano {len(clean_mods)} modów do '{output_file}'.")

    except Exception as e:
        print(f"❌ Błąd: {e}")

if __name__ == "__main__":
    scrape_scarlet_final()
