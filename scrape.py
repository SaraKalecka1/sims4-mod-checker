import requests
import csv
import json
import io
from bs4 import BeautifulSoup

def scrape_shifted():
    # Link do CSV
    csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTdw9ZyYV2ez4z1WAmH1CnYi_90ISRKAeZQ4fdi6kGgnFe2XjOJDFNErvuYxS87vh2pNstDVUYi7oGf/pub?gid=119778444&single=true&range=A:I&output=csv"
    output_file = "scarlet_mods.json"

    print(f"🚀 Pobieranie danych z przesunięciem (1, 2, 4, 5)...")
    
    try:
        response = requests.get(csv_url)
        response.raise_for_status()
        content = response.content.decode('utf-8')
        
        f = io.StringIO(content)
        reader = csv.reader(f)
        all_rows = list(reader)
        
        mods_list = []
        
        # Pomijamy pierwsze 2 wiersze (Tytuł + Nagłówki)
        data_rows = all_rows[2:]
        
        # --- DEBUGGER: Pokaż pierwszy wiersz z numerami ---
        if len(data_rows) > 0:
            print("\n🔍 ANALIZA PIERWSZEGO WIERSZA DANYCH:")
            first = data_rows[0]
            for i, cell in enumerate(first):
                print(f"   Kolumna [{i}]: {cell}")
            print("--------------------------------------\n")
        # --------------------------------------------------

        for row in data_rows:
            # Musi mieć minimum 6 kolumn, żeby pobrać datę (indeks 5)
            if not row or len(row) < 6:
                continue

            # --- MAPOWANIE (PRZESUNIĘTE) ---
            # [0] = Liczba porządkowa (ignorujemy)
            # [1] = Mod Name
            # [2] = Creator
            # [3] = Link (ignorujemy)
            # [4] = Status
            # [5] = Date
            
            raw_name = row[1].strip()
            
            # Pomiń jeśli nazwa jest pusta
            if not raw_name: continue

            raw_author = row[2].strip()
            raw_status = row[4].strip()
            raw_update = row[5].strip()

            # Czyszczenie
            clean_name = BeautifulSoup(raw_name, 'html.parser').get_text(strip=True)
            clean_author = BeautifulSoup(raw_author, 'html.parser').get_text(strip=True)
            clean_status = BeautifulSoup(raw_status, 'html.parser').get_text(strip=True)
            clean_update = BeautifulSoup(raw_update, 'html.parser').get_text(strip=True)

            if not clean_author: clean_author = "Unknown"
            if not clean_status: clean_status = "Unknown"

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

    except Exception as e:
        print(f"❌ Błąd: {e}")

if __name__ == "__main__":
    scrape_shifted()
