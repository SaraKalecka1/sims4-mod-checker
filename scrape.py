import requests
import json
import re

def scrape_scarlet_api():
    # URL strony głównej (tylko po to, by znaleźć ID tabeli)
    base_url = "https://scarletsrealm.com/the-mod-list-sfw-nsfw-edition/"
    # Endpoint AJAX WordPressa (to tu są faktyczne dane)
    ajax_url = "https://scarletsrealm.com/wp-admin/admin-ajax.php"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': base_url
    }

    print(f"🕵️  Szukanie ID tabeli na stronie: {base_url}")
    
    try:
        # KROK 1: Pobierz HTML, żeby znaleźć ID tabeli
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        html_content = response.text
        
        # Szukamy ciągu znaków typu: id="ninja_table_table_1234" lub data-id="1234"
        # Najczęstszy wzorzec dla Ninja Tables:
        match = re.search(r'ninja_table_table_(\d+)', html_content)
        
        if not match:
            print("❌ Nie znaleziono ID tabeli w kodzie strony.")
            return

        table_id = match.group(1)
        print(f"✅ Znaleziono Table ID: {table_id}")

        # KROK 2: Pobierz dane bezpośrednio z API (pomijamy HTML!)
        print(f"🚀 Pobieranie danych JSON z API (to może chwilę potrwać)...")
        
        payload = {
            'action': 'ninja_tables_data',
            'table_id': table_id,
            'id': table_id,
            'ninja_table_public_request': 1,
            'limit': 10000,  # Prosimy o 10000 rekordów na raz (żeby ominąć paginację)
            'skip_rows': 0,
            'chunk_size': 10000
        }

        api_response = requests.post(ajax_url, data=payload, headers=headers)
        api_response.raise_for_status()
        
        # Ninja Tables zwraca dane w formacie JSON
        json_response = api_response.json()
        
        # Dane zwykle siedzą w jednym z tych kluczy
        raw_data = []
        if isinstance(json_response, list):
            raw_data = json_response
        elif 'data' in json_response:
            raw_data = json_response['data']
        else:
            print(f"❌ Nieznana struktura odpowiedzi API: {json_response.keys()}")
            return

        print(f"📦 Pbrano surowe dane: {len(raw_data)} rekordów.")

        # KROK 3: Czyszczenie i mapowanie danych
        clean_mods = []
        
        for item in raw_data:
            # Ninja Tables zwraca dane gdzie klucze to np. "scatmodname", "scatauthor" albo generyczne
            # Poniższa logika próbuje wyłapać odpowiednie pola niezależnie od nazewnictwa
            
            # Pobieranie wartości, radzenie sobie z brakującymi polami
            # Uwaga: Klucze poniżej (np. 'creatorsname') są zgadywane na podstawie typowych nazw w Scarlet.
            # Jeśli API zwróci inne klucze, zobaczymy to w pliku wyjściowym.
            
            # Szukamy kluczy w obiekcie item (elastyczne podejście)
            # Zazwyczaj klucze to kolumny z bazy danych
            
            name = item.get('modname') or item.get('name') or item.get('title') or "Unknown Name"
            author = item.get('creatorsname') or item.get('author') or "Unknown Author"
            status = item.get('status') or "Unknown"
            
            # Data aktualizacji
            update = item.get('lastupdated') or item.get('date') or item.get('update') or ""
            
            # Link (często jest ukryty w polu 'modlink' lub 'download')
            link = item.get('modlink') or item.get('link') or item.get('url') or ""
            
            # Czasami link jest HTML-em w środku JSONa, trzeba by go wyczyścić, 
            # ale na razie bierzemy surowy tekst, żeby zobaczyć co przychodzi.

            entry = {
                "name": name,
                "author": author,
                "category": link, # Używamy linku jako kategorii/źródła zgodnie z Twoim wymogiem
                "status": status,
                "update": update
            }
            clean_mods.append(entry)

        # KROK 4: Zapis
        output_file = "scarlet_mods.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(clean_mods, f, ensure_ascii=False, indent=2)

        print(f"✅ Sukces! Zapisano {len(clean_mods)} modów do '{output_file}'.")

    except Exception as e:
        print(f"❌ Wystąpił błąd krytyczny: {e}")

if __name__ == "__main__":
    scrape_scarlet_api()
