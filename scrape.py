import json
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape_stealth():
    url = "https://scarletsrealm.com/the-mod-list-sfw-nsfw-edition/"
    output_file = "scarlet_mods.json"
    
    # Udajemy prawdziwą przeglądarkę
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

    print(f"🚀 Uruchamiam bota w trybie STEALTH...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # Konfigurujemy kontekst tak, by wyglądał jak zwykły użytkownik
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=user_agent,
            locale='en-US',
            timezone_id='America/New_York' # Czasem pomaga udawanie US
        )
        
        # Dodatkowa magia: ukrywamy fakt, że to webdriver
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page = context.new_page()
        captured_data = []

        # Nasłuchiwanie sieci
        def handle_response(response):
            if "admin-ajax.php" in response.url and response.status == 200:
                try:
                    json_body = response.json()
                    data_chunk = []
                    # Logika wyciągania danych (uniwersalna)
                    if isinstance(json_body, dict) and 'data' in json_body:
                        data_chunk = json_body['data']
                    elif isinstance(json_body, list):
                        data_chunk = json_body
                    
                    if data_chunk:
                        print(f"🎯 Przechwycono {len(data_chunk)} rekordów!")
                        captured_data.extend(data_chunk)
                except:
                    pass

        page.on("response", handle_response)

        print(f"🌍 Wchodzę na: {url}")
        page.goto(url, timeout=90000, wait_until="domcontentloaded")
        
        # --- INTERAKCJA (Klikanie) ---
        print("🛡️ Czekam na załadowanie (10s)...")
        time.sleep(10) 
        
        # Zrzut ekranu PRZED klikaniem (zobaczysz co widzi bot)
        page.screenshot(path="debug_1_entry.png")

        # 1. Cookies
        try:
            cookie_btn = page.locator("text=Accept").or_(page.locator("text=Agree")).first
            if cookie_btn.is_visible():
                cookie_btn.click()
                print("✅ Kliknięto Cookies.")
                time.sleep(2)
        except: pass

        # 2. Age Gate (Enter)
        try:
            enter_btn = page.locator("text=Enter").or_(page.locator("text=I am 18")).first
            if enter_btn.is_visible():
                enter_btn.click()
                print("✅ Kliknięto Enter.")
                time.sleep(5)
        except: pass

        # 3. Przewijanie (aby wymusić requesty)
        print("📜 Przewijanie strony...")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(3)
        page.evaluate("window.scrollTo(0, 1000)")
        
        # Czekanie na dane
        print("⏳ Czekam na dane z sieci...")
        for i in range(20):
            if len(captured_data) > 0:
                break
            time.sleep(1)

        # Zrzut ekranu PO wszystkim
        page.screenshot(path="debug_2_final.png")
        
        browser.close()

        if not captured_data:
            print("❌ Brak danych. Sprawdź pliki PNG w Artifacts na GitHubie.")
            return

        # --- OBRÓBKA DANYCH ---
        print(f"📦 Przetwarzanie {len(captured_data)} rekordów...")
        clean_mods = []
        
        for item in captured_data:
            raw_name = item.get('name') or item.get('modname') or item.get('title') or ""
            soup_name = BeautifulSoup(raw_name, 'html.parser')
            clean_name = soup_name.get_text(strip=True)
            
            link_tag = soup_name.find('a', href=True)
            mod_url = link_tag['href'] if link_tag else item.get('modlink', '')
            if mod_url and mod_url.startswith('/'): mod_url = "https://scarletsrealm.com" + mod_url

            raw_author = item.get('creators') or item.get('author') or "Unknown"
            clean_author = BeautifulSoup(raw_author, 'html.parser').get_text(strip=True)

            raw_status = item.get('status') or "Unknown"
            clean_status = BeautifulSoup(raw_status, 'html.parser').get_text(strip=True)

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
            
        print("✅ Gotowe! Plik zapisany.")

if __name__ == "__main__":
    scrape_stealth()
