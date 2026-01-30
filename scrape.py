import json
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape_yes_clicker():
    url = "https://scarletsrealm.com/the-mod-list-sfw-nsfw-edition/"
    output_file = "scarlet_mods.json"
    
    print(f"🚀 Uruchamiam bota (Target: 'Yes')...")

    with sync_playwright() as p:
        # Uruchamiamy przeglądarkę
        browser = p.chromium.launch(headless=True)
        # Ustawiamy duże okno i język angielski (żeby przyciski były po angielsku)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='en-US' 
        )
        page = context.new_page()

        captured_data = []

        # 1. Nasłuchiwanie sieci (Kradzież danych)
        def handle_response(response):
            if "admin-ajax.php" in response.url and response.status == 200:
                try:
                    json_body = response.json()
                    chunk = []
                    # Wyciąganie danych z różnych formatów
                    if isinstance(json_body, dict) and 'data' in json_body:
                        chunk = json_body['data']
                    elif isinstance(json_body, list):
                        chunk = json_body
                    
                    if chunk:
                        print(f"🎯 Przechwycono {len(chunk)} rekordów!")
                        captured_data.extend(chunk)
                except:
                    pass

        page.on("response", handle_response)

        print(f"🌍 Wchodzę na: {url}")
        page.goto(url, timeout=60000, wait_until="domcontentloaded")
        
        # Czekamy chwilę, aż modal (okienko) się załaduje
        time.sleep(6)
        
        # Zrób zdjęcie PRZED kliknięciem (zobaczymy czy widzi Yes)
        page.screenshot(path="debug_1_before_click.png")

        # --- SEKCJA: KLIKANIE "YES" ---
        print("🔨 Szukam przycisku 'Yes'...")
        
        try:
            # Strategia 1: Szukamy dokładnego tekstu "Yes" (duże/małe litery ignorowane)
            # To kliknie w przycisk, który ma napisane po prostu "Yes"
            yes_btn = page.get_by_text("Yes", exact=True)
            
            if yes_btn.count() > 0 and yes_btn.first.is_visible():
                print("✅ Znaleziono idealne 'Yes'. Klikam!")
                yes_btn.first.click()
            else:
                print("⚠️ Nie znaleziono idealnego 'Yes', szukam wariantów...")
                
                # Strategia 2: Szukamy przycisku zawierającego "Yes" (np. "Yes, I am 18")
                # Ale uważamy, żeby nie kliknąć w coś innego
                alt_btn = page.locator("button:has-text('Yes'), a:has-text('Yes'), div[role='button']:has-text('Yes')").first
                if alt_btn.is_visible():
                    print("✅ Znaleziono przycisk zawierający 'Yes'. Klikam!")
                    alt_btn.click()
                else:
                    print("❌ Nie widzę przycisku Yes.")
            
            time.sleep(3) # Czekamy na zniknięcie modala
            
        except Exception as e:
            print(f"⚠️ Błąd podczas klikania: {e}")

        # Klikamy też Cookies dla pewności (czasem "Yes" jest od cookies)
        try:
            page.get_by_text("Accept", exact=False).first.click()
        except: pass
        
        # --- KONIEC KLIKANIA ---

        # 3. Wymuszenie ładowania tabeli (przewijanie)
        print("📜 Przewijanie strony...")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
        page.evaluate("window.scrollTo(0, 500)")
        
        print("⏳ Czekam na dane z sieci (max 20s)...")
        for i in range(20):
            if len(captured_data) > 0:
                break
            time.sleep(1)

        # Zdjęcie po wszystkim
        page.screenshot(path="debug_2_after_click.png")
        browser.close()

        if not captured_data:
            print("❌ Brak danych. Sprawdź 'debug_1_before_click.png' w Artifacts.")
            return

        # 4. Obróbka danych
        print(f"📦 Zapisywanie {len(captured_data)} rekordów...")
        clean_mods = []
        
        for item in captured_data:
            # Name
            raw_name = item.get('name') or item.get('modname') or item.get('title') or ""
            soup_name = BeautifulSoup(raw_name, 'html.parser')
            clean_name = soup_name.get_text(strip=True)
            
            # Link
            link_tag = soup_name.find('a', href=True)
            mod_url = link_tag['href'] if link_tag else item.get('modlink', '')
            if mod_url and mod_url.startswith('/'): mod_url = "https://scarletsrealm.com" + mod_url

            # Author
            raw_author = item.get('creators') or item.get('author') or "Unknown"
            clean_author = BeautifulSoup(raw_author, 'html.parser').get_text(strip=True)

            # Status
            raw_status = item.get('status') or "Unknown"
            clean_status = BeautifulSoup(raw_status, 'html.parser').get_text(strip=True)

            # Update
            clean_date = item.get('date') or item.get('last_updated') or ""

            if clean_name:
                clean_mods.append({
                    "name": clean_name,
                    "author": clean_author,
                    "category": mod_url,
                    "status": clean_status,
                    "update": clean_date
                })

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(clean_mods, f, ensure_ascii=False, indent=2)
            
        print("✅ Sukces! Plik zapisany.")

if __name__ == "__main__":
    scrape_yes_clicker()
