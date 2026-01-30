import requests
from bs4 import BeautifulSoup
import json

def scrape_scarlet_v2():
    # 1. Zaktualizowany URL
    url = "https://scarletsrealm.com/the-mod-list-sfw-nsfw-edition/"
    output_file = "scarlet_mods.json"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Referer': 'https://google.com'
    }

    print(f"🔄 Pobieranie danych z: {url}...")
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Błąd połączenia: {e}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Szukamy tabeli Ninja Tables
    table = soup.find('table', {'id': lambda x: x and x.startswith('ninja_table_table_')})
    
    if not table:
        table = soup.find('table') # Fallback
        
    if not table:
        print("❌ Nie znaleziono tabeli w kodzie HTML. Tabela może być ładowana dynamicznie przez JS.")
        return

    mods_data = []
    # Pobieramy wszystkie wiersze z ciała tabeli
    rows = table.find('tbody').find_all('tr') if table.find('tbody') else table.find_all('tr')

    print(f"🔍 Przetwarzanie {len(rows)} wierszy...")

    for row in rows:
        cells = row.find_all('td')
        if not cells or len(cells) < 5:
            continue

        try:
            # 4. Mapowanie (Sprawdź czy kolejność na stronie to: Name | Author | Category | Status | Update)
            name_text = cells[0].get_text(strip=True)
            author_text = cells[1].get_text(strip=True)
            
            # Pobieranie linku z kolumny Category (zwykle indeks 2)
            # Jeśli w tej kolumnie jest link (<a>), pobieramy href. Jeśli nie, sam tekst.
            cat_cell = cells[2]
            link_tag = cat_cell.find('a', href=True)
            category_val = link_tag['href'] if link_tag else cat_cell.get_text(strip=True)

            status_text = cells[3].get_text(strip=True)
            update_text = cells[4].get_text(strip=True)

            mod_entry = {
                "name": name_text,
                "author": author_text,
                "category": category_val,
                "status": status_text,
                "update": update_text
            }
            
            mods_data.append(mod_entry)

        except Exception as e:
            continue

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(mods_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Gotowe. Zapisano {len(mods_data)} rekordów w '{output_file}'.")

if __name__ == "__main__":
    scrape_scarlet_v2()
