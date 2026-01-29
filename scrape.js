const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
    console.log("🚀 Uruchamiam zaawansowany skaner dla pelna-kulturka.pl...");
    
    const browser = await puppeteer.launch({ 
        headless: "shell",
        args: [
            '--no-sandbox', 
            '--disable-setuid-sandbox', 
            '--disable-dev-shm-usage',
            '--disable-http2', // Naprawia ERR_HTTP2_PROTOCOL_ERROR
            '--disable-blink-features=AutomationControlled', // Ukrywa fakt, że to bot
            '--lang=pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7'
        ]
    });
    
    const page = await browser.newPage();

    // Udajemy prawdziwego użytkownika na Windowsie
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36');
    await page.setViewport({ width: 1920, height: 1080 });

    try {
        const url = 'https://scarletsrealm.com/the-mod-list-sfw-nsfw-edition/';
        console.log(`🔗 Próba połączenia z: ${url}`);
        
        // Używamy 'domcontentloaded' zamiast 'networkidle2', aby uniknąć blokad na skryptach śledzących
        await page.goto(url, { 
            waitUntil: 'domcontentloaded', 
            timeout: 60000 
        });

        console.log("⏳ Strona załadowana. Czekam 15s na inicjalizację tabeli Ninja...");
        // Ninja Tables potrzebują chwili, by pobrać dane przez AJAX
        await new Promise(r => setTimeout(r, 15000));

        // Sprawdzamy czy tabela w ogóle istnieje
        const tableExists = await page.$('.ninja_table_pro');
        if (!tableExists) {
            console.log("❌ Nie znaleziono tabeli! Robię zrzut ekranu dla diagnostyki...");
            await page.screenshot({ path: 'error_screenshot.png' });
            throw new Error("Tabela .ninja_table_pro nie pojawiła się na stronie.");
        }

        let allData = [];
        let pageCounter = 1;
        let hasNextPage = true;

        while (hasNextPage && pageCounter <= 30) {
            console.log(`📥 Scrapowanie strony ${pageCounter}...`);

            const data = await page.evaluate(() => {
                const rows = document.querySelectorAll('.ninja_table_pro tbody tr');
                return Array.from(rows).map(row => {
                    const cols = row.querySelectorAll('td');
                    // Pobieramy dane na podstawie pozycji kolumn (0: Nazwa, 1: Autor, 3: Status, 4: Data)
                    return {
                        name: cols[0]?.innerText.trim() || "",
                        author: cols[1]?.innerText.trim() || "",
                        status: cols[3]?.innerText.trim() || "",
                        update: cols[4]?.innerText.trim() || ""
                    };
                }).filter(item => item.name.length > 1);
            });

            if (data.length > 0) {
                allData.push(...data);
                console.log(`✅ Pobrano ${data.length} wierszy.`);
            }

            // Szukamy przycisku "Next"
            const nextButton = await page.$('.footable-page-nav[data-page="next"]:not(.disabled)');
            if (nextButton && pageCounter < 30) { 
                await nextButton.click();
                await new Promise(r => setTimeout(r, 5000));
                pageCounter++;
            } else {
                hasNextPage = false;
            }
        }

        if (allData.length > 0) {
            fs.writeFileSync('scarlet_db_full.json', JSON.stringify(allData, null, 2));
            console.log(`\n🎉 SUKCES! Zapisano: ${allData.length} modów.`);
        } else {
            console.log("\n⚠️ Tabela pusta. Serwer mógł zablokować dostęp do danych.");
        }

    } catch (error) {
        console.error("❌ BŁĄD:", error.message);
        process.exit(1);
    } finally {
        await browser.close();
    }
})();
