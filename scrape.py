import json
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape_slow_scroll():
    url = "https://scarletsrealm.com/the-mod-list-sfw-nsfw-edition/"
    output_file = "scarlet_mods.json"
    
    print(f"🚀 Uruchamiam bota (Tryb: Slow Scroll)...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Ustawiamy wysoki ekran, żeby widzieć więcej na raz
        context = browser.new_context(viewport={'width': 1920, 'height': 1280})
        page = context.new_page()

        captured_data = []

        # 1. Nasłuchiwanie sieci
        def handle_response(response):
            if "admin-ajax.php" in response.url and response.status == 200:
                try:
                    json_body = response.json()
                    chunk = []
                    if isinstance(json_body, dict) and 'data' in json_body:
                        chunk = json_body['data']
                    elif isinstance(json_body, list):
                        chunk = json_body
                    
                    if chunk:
                        print(f"🎯 DANE ZŁAPANE W LOCIE: {len(chunk)} rekordów!")
                        captured_data.extend(chunk)
                except:
                    pass

        page.on("response", handle_response)

        print(f"🌍 Wchodzę na: {url}")
        page.goto(url, timeout=90000, wait_until="domcontentloaded")
        
        # Czekamy chwilę na inicjalizację
        time.sleep(5)

        # 2. Obsługa Pop-upów (Zostawiamy na wszelki wypadek)
        try:
            # Cookies
            page.get_by_text("Accept", exact=False).first.click(timeout=2000)
            print("🍪 Kliknięto Cookies.")
        except: pass

        try:
            # Age Gate (Yes/Enter)
            yes_btn = page.locator("text=Yes").or_(page.locator("text=Enter")).first
            if yes_btn.is_visible():
                yes_btn.click()
                print("✅ Kliknięto Yes/Enter.")
                time.sleep(3)
        except: pass

        # Zrzut przed przewijaniem
        page.screenshot(path="debug_1_start_scroll.png")

        # --- SEKCJA: POWOLNE PRZEWIJANIE (SLOW SCROLL) ---
        print("📜 Rozpoczynam powolne przewijanie w poszukiwaniu tabeli...")
        
        # Próbujemy znaleźć nagłówek tabeli, żeby wiedzieć gdzie celować
        # Ninja tables często ma klasę .ninja_table_wrapper
        try:
            table_wrapper = page.locator(".ninja_table_wrapper").first
            if table_wrapper.is_visible():
                print("👀 Widzę kontener tabeli. Przewijam do niego.")
                table_wrapper.scroll_into_view_if_needed()
                time.sleep(2)
        except:
            print("⚠️ Nie widzę konkretnego kontenera, jadę na ślepo.")

        # Pętla przewijania "na kółku myszy"
        # Przewijamy 20 razy po kawałku, sprawdzając czy dane spłynęły
        for i in range(25):
            if len(captured_data) > 0:
                print("✅ Mamy już dane! Przerywam przewijanie.")
                break
            
            print(f"⬇️ Przewijam w dół... (Krok {i+1}/25)")
            page.mouse.wheel(0, 500) # Symulacja ruchu kółkiem o 500px
            time.sleep(1.5) # Czekamy aż skrypty strony "załapią"
            
            # Co 5 kroków robimy mały ruch myszką, żeby "obudzić" stronę
            if i % 5 == 0:
                page.mouse.move(500, 500)

        # Na koniec zjazd na sam dół (dobicie)
        page.keyboard.press("End")
        time.sleep(3)

        # --- KONIEC PRZEWIJANIA ---

        # Zdjęcie końcowe
        page.screenshot(path="debug_2_end_scroll.png")
        browser.close()

        if not captured_data:
            print("❌ Brak danych. Sprawdź 'debug_2_end_scroll.png' - czy widać tam tabelę?")
            return

        # 3. Obróbka i zapis
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
    scrape_slow_scroll()
