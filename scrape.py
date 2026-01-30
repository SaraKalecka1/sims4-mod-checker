import requests
import csv
import json
import io
from bs4 import BeautifulSoup

def scrape_google_csv():
    # Twój link bezpośredni (oczyszczony ze znaków specjalnych HTML)
    csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTdw9ZyYV2ez4z1WAmH1CnYi_90ISRKAeZQ4fdi6kGgnFe2XjOJDFNErvuYxS87vh2pNstDVUYi7oGf/pub?gid=119778444&single=true&range=A:I&output=csv"
    output_file = "scarlet_mods.json"

    print(f"🚀 Pobieranie danych bezpośrednio z Google Sheets...")
    
    try:
        response = requests.get(csv_url)
        response.raise_for_status()
        
        # Dekodowanie treści CSV
        csv_content = response.content.decode('utf-8')
        
        # Czytanie CSV
        reader = csv.DictReader(io.StringIO(csv_content))
        
        # Normalizacja nazw kolumn (zmieniamy na małe litery, usuwamy spacje)
        # To zabezpiecza nas, gdyby Scarlet zmieniła "Mod Name" na "ModName"
        headers = [h.strip().lower() for h in reader.fieldnames]
        print(f"ℹ️ Znalezione kolumny: {headers}")
        
        mods_list = []
        
        # Resetujemy reader, żeby czytać dane
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        for row in csv_reader:
            # Tworzymy słownik z "czystymi" kluczami (lowercase)
            clean_row = {k.strip().lower(): v for k, v in row.items() if k}
            
            # --- MAPOWANIE DANYCH ---
            # Tutaj dopasowujemy kolumny z Google Sheet do Twojego JSONa
            
            # 1. NAME
            raw_name = clean_row.get('mod name') or clean_row.get('name') or ""
            if not raw_name: continue # Pomiń puste wiersze

            # Czyścimy HTML w nazwie (często Scarlet daje tam link <a href...>)
            soup = BeautifulSoup(raw_name, 'html.parser')
            clean_name = soup.get_text(strip=True)

            # 2. LINK (CATEGORY)
            # Link jest albo w kolumnie 'download link', albo ukryty w nazwie
            link = clean_row.get('download link') or clean_row.get('link') or clean_row.get('url') or ""
            if not link:
                a_tag = soup.find('a', href=True)
                if a_tag: link = a_tag['href']

            # 3. AUTHOR
            author = clean_row.get('creator(s)') or clean_row.get('author') or clean_row.get('creators') or "Unknown"
            
            # 4. STATUS
            status = clean_row.get('status') or "Unknown"
            
            # 5. UPDATE
            update = clean_row.get('last updated') or clean_row.get('date') or ""

            # Dodajemy do listy
            mods_list.append({
                "name": clean_name,
                "author": author,
                "category": link,
                "status": status,
                "update": update
            })

        # Zapis do pliku
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mods_list, f, ensure_ascii=False, indent=2)

        print(f"✅ Sukces! Pbrano {len(mods_list)} rekordów prosto ze źródła.")

    except Exception as e:
        print(f"❌ Błąd: {e}")

if __name__ == "__main__":
    scrape_google_csv()
