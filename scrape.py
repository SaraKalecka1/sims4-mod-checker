import requests
import json
import re
from bs4 import BeautifulSoup

def scrape_scarlet_precision():
    # URL głównej strony (do znalezienia ID tabeli)
    base_url = "https://scarletsrealm.com/the-mod-list-sfw-nsfw-edition/"
    # URL API (tzw. backend WordPressa)
    ajax_url = "https://scarletsrealm.com/wp-admin/admin-ajax.php"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': base_url
    }

    print(f"🕵️  Szukanie ID tabeli na stronie: {base_url}")
    
    try:
        # KROK 1: Pobieramy stronę, by znaleźć aktualne ID tabeli
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        
        # Szukamy ciągu: ninja_table_table_XXXX
        match = re.search(r'ninja_table_table_(\d+)', response.text)
        
        if not match:
            print("❌ Nie znaleziono ID tabeli. Strona mogła zmienić strukturę.")
            return

        table_id = match.group(1)
        print(f"✅ Znaleziono Table ID: {table_id}")

        # KROK 2: Pobieramy CAŁĄ bazę danych jednym strzałem
        print(f"🚀 Pobieranie danych z API (limit 10000)...")
        
        payload = {
            'action': 'ninja_tables_data',
            'table_id': table_id,
            'id': table_id,
            'ninja_table_public_request': 1,
            'limit': 10000, # Pobieramy wszystko naraz, omijając paginację
            'skip_rows': 0,
            'chunk_size': 10000
        }

        api_response = requests.post(ajax_url, data=payload, headers=headers)
        api_response.raise_for_status()
        json_response = api_response.json()

        # Czasem dane są bezpośrednio listą, a czasem w kluczu 'data' (zależy od wersji wtyczki)
        if isinstance(json_response, list):
            raw_data = json_response
        elif isinstance(json_response, dict) and 'data' in json_response:
            raw_data = json_response['data']
        else:
            raw_data = []

        print(f"📦 Pbrano {len(raw_data)} surowych rekordów. Przetwarzanie...")

        # KROK 3: Czyszczenie i mapowanie (na podstawie Twojego pliku txt)
        clean_mods = []
        
        for item in raw_data:
            # 1. NAME i LINK
            # Scarlet trzyma link w polu 'name' jako HTML (<a href="...">Nazwa</a>)
            raw_name_html = item.get('name', '')
            
            # Używamy BeautifulSoup do wyjęcia czystego tekstu i linku
            soup = BeautifulSoup(raw_name_html, 'html.parser')
            
            clean_name = soup.get_text(strip=True) # Sama nazwa moda
            
            # Wyciągamy link (href) z tagu <a>, jeśli istnieje
            link_tag = soup.find('a', href=True)
            mod_url = link_tag['href'] if link_tag else ""
            
            # Jeśli w polu name nie było linku, sprawdzamy pole 'modlink' (czasem tam jest)
            if not mod_url:
                mod_url = item.get('modlink', '')

            # 2. STATUS
            # Klucz z pliku: ninja_column_status -> 'status'
            status = item.get('status', 'Unknown')
            # Czyścimy HTML ze statusu (czasem są tam kolory/boldy)
            status = BeautifulSoup(status, 'html.parser').get_text(strip=True)

            # 3. AUTHOR
            # Klucz z pliku: ninja_column_creators -> 'creators'
            author = item.get('creators', 'Unknown Author')
            author = BeautifulSoup(author, 'html.parser').get_text(strip=True)

            # 4. UPDATE
            # Klucz z pliku: ninja_column_date -> 'date'
            update = item.get('date', '')

            # Budowanie obiektu wynikowego
            entry = {
                "name": clean_name,
                "author": author,
                # Zgodnie z Twoim życzeniem w polu 'category' dajemy URL
                "category": mod_url, 
                "status": status,
                "update": update
            }
            
            # Opcjonalnie: pomijamy puste wiersze (bez nazwy)
            if clean_name:
                clean_mods.append(entry)

        # KROK 4: Zapis do pliku
        output_file = "scarlet_mods.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(clean_mods, f, ensure_ascii=False, indent=2)

        print(f"✅ Sukces! Zapisano {len(clean_mods)} modów do '{output_file}'.")

    except Exception as e:
        print(f"❌ Błąd: {e}")

if __name__ == "__main__":
    scrape_scarlet_precision()
