import requests
import csv
import json
import io
from bs4 import BeautifulSoup

def scrape_smart_headers():
    # Link bezpośredni do CSV
    csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTdw9ZyYV2ez4z1WAmH1CnYi_90ISRKAeZQ4fdi6kGgnFe2XjOJDFNErvuYxS87vh2pNstDVUYi7oGf/pub?gid=119778444&single=true&range=A:I&output=csv"
    output_file = "scarlet_mods.json"

    print(f"🚀 Pobieranie danych z Google Sheets...")
    
    try:
        response = requests.get(csv_url)
        response.raise_for_status()
        
        # Dekodujemy treść
        content = response.content.decode('utf-8')
        
        # Używamy StringIO, żeby traktować string jak plik
        f = io.StringIO(content)
        lines = f.readlines()
        
        # --- KROK 1: Szukanie wiersza z nagłówkami ---
        header_row_index = 0
        found_header = False
        
        # Sprawdzamy pierwsze 10 linii, żeby znaleźć, gdzie zaczyna się tabela
        for i, line in enumerate(lines[:10]):
            # Szukamy słów kluczowych, które na pewno są w nagłówku
            if "Status" in line and ("Creator" in line or "Author" in line):
                header_row_index = i
                found_header = True
                print(f"✅ Znaleziono nagłówki w wierszu nr {i+1}: {line.strip()}")
                break
        
        if not found_header:
            print("⚠️ Nie znaleziono typowych nagłówków. Próbuję czytać od początku.")

        # --- KROK 2: Czytanie danych od właściwego miejsca ---
        # Przewijamy do linii z nagłówkami
        f.seek(0)
        # Pomijamy linie "śmieciowe" na górze
        for _ in range(header_row_index):
            next(f)
            
        reader = csv.DictReader(f)
        
        # Normalizacja nagłówków (usuwamy spacje i robimy małe litery dla łatwiejszego szukania)
        # Np. " Mod Name " zamieni się na "mod name"
        normalized_fieldnames = [h.strip().lower() for h in reader.fieldnames] if reader.fieldnames else []
        
        # Mapowanie oryginalnych nazw kolumn na nasze znormalizowane klucze
        # Tworzymy mapę: { 'mod name': 'Mod Name', 'status': 'Status' ... }
        key_map = {}
        if reader.fieldnames:
            for orig in reader.fieldnames:
                key_map[orig.strip().lower()] = orig

        mods_list = []
        
        for row in reader:
            # Funkcja pomocnicza do wyciągania wartości po znormalizowanej nazwie
            def get_col(candidates):
                for cand in candidates:
                    # Szukamy klucza w mapie (np. 'creator(s)'), a potem wartości w wierszu
                    real_key = key_map.get(cand.lower())
                    if real_key and row.get(real_key):
                        return row.get(real_key)
                return ""

            # 1. NAME
            raw_name = get_col(['Mod Name', 'Name', 'Mod', 'Title'])
            if not raw_name: continue # Pomiń puste

            # Czyścimy HTML
            clean_name = BeautifulSoup(raw_name, 'html.parser').get_text(strip=True)

            # 2. AUTHOR
            raw_author = get_col(['Creator(s)', 'Creators', 'Author', 'Mod Creator'])
            clean_author = BeautifulSoup(raw_author, 'html.parser').get_text(strip=True)
            if not clean_author: clean_author = "Unknown"

            # 3. STATUS
            raw_status = get_col(['Status', 'Mod Status', 'Compatibility'])
            clean_status = BeautifulSoup(raw_status, 'html.parser').get_text(strip=True)
            if not clean_status: clean_status = "Unknown"

            # 4. UPDATE
            raw_update = get_col(['Last Updated', 'Updated', 'Date'])
            clean_update = BeautifulSoup(raw_update, 'html.parser').get_text(strip=True)

            # Tworzymy obiekt (bez kategorii)
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
        print(f"❌ Błąd krytyczny: {e}")

if __name__ == "__main__":
    scrape_smart_headers()
