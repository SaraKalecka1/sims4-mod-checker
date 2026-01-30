import json
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape_with_interaction():
    url = "https://scarletsrealm.com/the-mod-list-sfw-nsfw-edition/"
    output_file = "scarlet_mods.json"
    
    print(f"🚀 Uruchamiam bota...")

    with sync_playwright() as p:
        # Uruchamiamy przeglądarkę
        browser = p.chromium.launch(headless=True) # Zmień na False jeśli testujesz lokalnie i chcesz widzieć okno
        # Ustawiamy duży viewport, żeby przyciski nie były schowane
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        # Zmienna na dane
        captured_data = []

        # 1. Konfiguracja nasłuchiwania sieci (tak jak wcześniej)
        def handle_response(response):
            if "admin-ajax.php" in response.url and response.status == 200:
                try:
                    json_body = response.json()
                    # Logika wyciągania danych z JSON
                    data_chunk = []
                    if isinstance(json_body, dict) and 'data' in json_body:
                        data_chunk = json_body['data']
                    elif isinstance(json_body, list):
                        data_chunk = json_body
                    
                    if data_chunk and len(data_chunk) > 0:
                        print(f"🎯 Przechwycono pakiet danych: {len(data_chunk)} rekordów!")
                        captured_data.extend(data_chunk)
                except:
                    pass

        page.on("response", handle_response)

        # 2. Wejście na stronę
        print(f"🌍 Wchodzę na: {url}")
        page.goto(url, timeout=60000)
        
        # --- SEKCJA: HANDLE POPUPS (KLIKANIE OKIENEK) ---
        print("🛡️ Sprawdzam obecność popupów (Age Gate / Cookies)...")
        time.sleep(5) # Dajemy chwilę, żeby okienka wyskoczyły

        # Próba 1: Bramka wiekowa (Szukamy przycisków typu "Enter", "I am 18+", "Yes")
        try:
            # Szukamy przycisku, który zawiera słowo "Enter" lub "18"
            # (dostosowane do Scarlet - zazwyczaj jest to przycisk "Enter")
            age_btn = page.locator("button:has-text('Enter'), a:has-text('Enter'), button:has-text('18'), button:has-text('Yes')").first
            
            if age_btn.is_visible():
                print("Found Age Gate button. Clicking...")
                age_btn.click()
                time.sleep(2) # Czekamy na przeładowanie
            else:
                print("ℹ️ Nie znaleziono bramki wiekowej (lub już zniknęła).")
        except Exception as e:
            print(f"⚠️ Błąd przy klikaniu Age Gate: {e}")

        # Próba 2: Cookies (Szukamy "Accept", "Agree", "Got it")
        try:
            cookie_btn = page.locator("button:has-text('Accept'), button:has-text('Agree'), a:has-text('Accept')").first
            if cookie_btn.is_visible():
                print("Found Cookie button. Clicking...")
                cookie_btn.click()
                time.sleep(1)
        except:
            pass
        
        # --- KONIEC SEKCJI POPUPÓW ---

        # 3. Wymuszenie ładowania tabeli
        # Czasami tabela ładuje się dopiero jak się trochę zjedzie w dół
        print("📜 Przewijanie strony, aby wymusić ładowanie danych...")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
        page.evaluate("window.scrollTo(0, 500)") # Powrót trochę wyżej
        
        # Czekamy chwilę na ruch w sieci (captured_data powinno się napełniać)
        print("⏳ Czekam na dane (max 15s)...")
        # Pętla czekająca aktywnie na dane
        for _ in range(15):
            if len(captured_data) > 0:
                break
            time.sleep(1)

        # DEBUG: Zrób zrzut ekranu, żebyśmy widzieli co widzi bot
        page.screenshot(path="debug_screenshot.png")
        print("📸 Zrobiono zrzut ekranu (debug_screenshot.png) - sprawdź Artifacts w GitHub Actions jeśli pusto.")

        browser.close()

        if not captured_data:
            print("❌ Nadal brak danych. Sprawdź zrzut ekranu debug_screenshot.png")
            return

        # 4. Obróbka danych (tak jak w poprzednich wersjach)
        print(f"📦 Przetwarzanie {len(captured_data)} rekordów...")
        clean_mods = []
        
        for item in captured_data:
            # NAME
            raw_name = item.get('name') or item.get('modname') or item.get('title') or ""
            soup_name = BeautifulSoup(raw_name, 'html.parser')
            clean_name = soup_name.get_text(strip=True)
            
            # LINK
            link_tag = soup_name.find('a', href=True)
            mod_url = link_tag['href'] if link_tag else item.get('modlink', '')
            if mod_url and mod_url.startswith('/'): mod_url = "https://scarletsrealm.com" + mod_url

            # AUTHOR
            raw_author = item.get('creators') or item.get('author') or item.get('creatorsname') or "Unknown"
            clean_author = BeautifulSoup(raw_author, 'html.parser').get_text(strip=True)

            # STATUS
            raw_status = item.get('status') or "Unknown"
            clean_status = BeautifulSoup(raw_status, 'html.parser').get_text(strip=True)

            # UPDATE
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

        print(f"✅ Sukces! Zapisano {len(clean_mods)} modów.")

if __name__ == "__main__":
    scrape_with_interaction()
