import requests
import csv
import json
import io
from bs4 import BeautifulSoup

def scrape_exact_columns():
    # Link do CSV
    csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTdw9ZyYV2ez4z1WAmH1CnYi_90ISRKAeZQ4fdi6kGgnFe2XjOJDFNErvuYxS87vh2pNstDVUYi7oGf/pub?gid=119778444&single=true&range=A:I&output=csv"
    output_file = "scarlet_mods.json"

    print(f"🚀 Pobieranie danych (Mapowanie sztywne: 0, 1, 3, 4)...")
    
    try:
        response = requests.get(csv_url)
        response.raise_for_status()
        content = response.content.decode('utf-8')
        
        # Czytamy jako zwykłą listę list (nie słowniki)
        f = io.StringIO(content)
        reader = csv.reader(f)
        all_rows = list(reader)
        
        mods_list = []
        
        # Pętla po wierszach.
        # all_rows[0] -> Tytuł (pomijamy)
        # all_rows[1] -> Nagłówki (pomijamy)
        # Dane zaczynają się od indeksu 2
        
        data_rows = all_rows[2:] 
        
        print(f"ℹ️ Znaleziono {len(data_rows)} wierszy z danymi.")

        for row in data_rows:
            # Zabezpieczenie przed pustymi wierszami
            if not row or len(row) < 5:
                continue

            # --- MAPOWANIE POZYCYJNE ---
            # 0: Mod Name
            # 1: Creator
            # 2: Link (Pomijamy)
            # 3: Patch Status
            # 4: Last Status Change
            
            raw_name = row[0].strip()
            raw_author = row[1].strip()
            raw_status = row[3].strip()
            raw_update = row[4].strip()

            # Jeśli nie ma nazwy moda, to śmieć -> pomijamy
            if not raw_name:
                continue

            # Czyszczenie HTML (usuwanie ewentualnych linków z tekstu)
            clean_name = BeautifulSoup(raw_name, 'html.parser').get_text(strip=True)
            clean_author = BeautifulSoup(raw_author, 'html.parser').get_text(strip=True)
            clean_status = BeautifulSoup(raw_status, 'html.parser').get_text(strip=True)
            clean_update = BeautifulSoup(raw_update, 'html.parser').get_text(strip=True)

            # Uzupełnianie braków
            if not clean_author: clean_author = "Unknown"
            if not clean_status: clean_status = "Unknown"

            # Budowa obiektu
            mods_list.append({
                "name": clean_name,
                "author": clean_author,
                "status": clean_status,
                "update": clean_update
            })

        # Zapis
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mods_list, f, ensure_ascii=False, indent=2)

        print(f"✅ Sukces! Zapisano {len(mods_list)} modów.")
        
        # Podgląd dla pewności
        if len(mods_list) > 0:
            print(f"👀 Pierwszy rekord: {mods_list[0]}")

    except Exception as e:
        print(f"❌ Błąd: {e}")

if __name__ == "__main__":
    scrape_exact_columns()
