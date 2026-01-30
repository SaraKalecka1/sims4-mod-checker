import requests
import csv
import json
import io
from bs4 import BeautifulSoup

def scrape_google_csv_clean():
    # Twój link do CSV
    csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTdw9ZyYV2ez4z1WAmH1CnYi_90ISRKAeZQ4fdi6kGgnFe2XjOJDFNErvuYxS87vh2pNstDVUYi7oGf/pub?gid=119778444&single=true&range=A:I&output=csv"
    output_file = "scarlet_mods.json"

    print(f"🚀 Pobieranie danych z Google Sheets...")
    
    try:
        response = requests.get(csv_url)
        response.raise_for_status()
        csv_content = response.content.decode('utf-8')
        
        # Czytanie CSV
        reader = csv.DictReader(io.StringIO(csv_content))
        
        # --- DIAGNOSTYKA ---
        # To pokaże w logach GitHuba, jak DOKŁADNIE nazywają się kolumny
        headers = [h.strip() for h in reader.fieldnames]
        print(f"📋 WYKRYTE KOLUMNY: {headers}") 
        # -------------------

        mods_list = []
        
        # Funkcja pomocnicza: szuka wartości w kilku wariantach nazwy kolumny
        def get_val(row, candidates):
            # Normalizujemy klucze wiersza do małych liter
            row_lower = {k.strip().lower(): v for k, v in row.items() if k}
            
            for candidate in candidates:
                val = row_lower.get(candidate.lower())
                if val and val.strip(): # Jeśli znaleziono i nie jest puste
                    return val.strip()
            return "" # Jak nic nie znajdzie

        # Reset readera
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        for row in csv_reader:
            # 1. NAME (Nazwa moda)
            # Szukamy pod: 'Mod Name', 'Name', 'Mod'
            raw_name = get_val(row, ['Mod Name', 'Name', 'Mod', 'Title'])
            
            if not raw_name: continue # Jeśli nie ma nazwy, pomiń wiersz

            # Czyścimy HTML z nazwy (usuwamy linki <a>)
            soup = BeautifulSoup(raw_name, 'html.parser')
            clean_name = soup.get_text(strip=True)

            # 2. AUTHOR
            # Szukamy pod: 'Creator(s)', 'Creators', 'Author', 'Made By'
            raw_author = get_val(row, ['Creator(s)', 'Creators', 'Author', 'Mod Creator'])
            clean_author = BeautifulSoup(raw_author, 'html.parser').get_text(strip=True)
            if not clean_author: 
                clean_author = "Unknown"

            # 3. STATUS
            # Szukamy pod: 'Status', 'Mod Status', 'Compatibility'
            raw_status = get_val(row, ['Status', 'Mod Status', 'State'])
            clean_status = BeautifulSoup(raw_status, 'html.parser').get_text(strip=True)
            if not clean_status:
                clean_status = "Unknown"
            
            # 4. UPDATE (Ostatnia zmiana)
            # Szukamy pod: 'Last Updated', 'Updated', 'Date'
            raw_update = get_val(row, ['Last Updated', 'Updated', 'Date', 'Update Date'])
            clean_update = BeautifulSoup(raw_update, 'html.parser').get_text(strip=True)

            # Budujemy obiekt (bez kategorii, zgodnie z życzeniem)
            mods_list.append({
                "name": clean_name,
                "author": clean_author,
                "status": clean_status,
                "update": clean_update
            })

        # Zapis do pliku
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mods_list, f, ensure_ascii=False, indent=2)

        print(f"✅ Sukces! Zapisano {len(mods_list)} modów.")

    except Exception as e:
        print(f"❌ Błąd: {e}")

if __name__ == "__main__":
    scrape_google_csv_clean()
