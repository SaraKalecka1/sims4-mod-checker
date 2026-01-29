const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
    console.log("🚀 Uruchamiam skaner w trybie STEALTH dla pelna-kulturka.pl...");
    
    const browser = await puppeteer.launch({ 
        headless: "shell",
        args: [
            '--no-sandbox', 
            '--disable-setuid-sandbox', 
            '--disable-http2', // Rozwiązuje ERR_HTTP2_PROTOCOL_ERROR
            '--disable-blink-features=AutomationControlled', // Ukrywa tryb automatyzacji
            '--disable-web-security'
        ]
    });
    
    const page = await browser.newPage();

    // Maskowanie parametrów przeglądarki
    await page.evaluateOnNewDocument(() => {
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    });

    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36');
    await page.setViewport({ width: 1366, height: 768 });

    try {
        const url = 'https://scarletsrealm.com/the-mod-list-sfw-nsfw-edition/';
        console.log(`🔗 Próba połączenia (Stealth Mode): ${url}`);
        
        // Używamy domcontentloaded - jest trudniejsze do zablokowania
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 90000 });

        console.log("⏳ Stabilizacja strony (15s)...");
        await new Promise(r => setTimeout(r, 15000));

        let allData = [];
        let pageCounter = 1;
        let hasNextPage = true;

        while (hasNextPage && pageCounter <= 30) {
            console.log(`📥 Przetwarzanie strony ${pageCounter}...`);

            // Czekamy na dane w tabeli
            await page.waitForSelector('.ninja_table_pro tbody tr', { timeout: 30000 }).catch(() => null);

            const data = await page.evaluate(() => {
                const rows = document.querySelectorAll('.ninja_table_pro tbody tr');
                return Array.from(rows).map(row => {
                    const cols = row.querySelectorAll('td');
                    return {
                        name: cols[0]?.innerText.trim() || "",
                        author: cols[1]?.innerText.trim() || "",
                        status: cols[3]?.innerText.trim() || "",
                        update: cols[4]?.innerText.trim() || ""
                    };
                }).filter(item => item.name.length > 2);
            });

            if (data.length > 0) {
                allData.push(...data);
                console.log(`✅ Pobrano ${data.length} wierszy.`);
            }

            // Obsługa przycisku "Next" - Metoda bezpieczna (Force Click)
            const nextButton = await page.$('li.footable-page-nav[data-page="next"] a');
            
            if (nextButton && pageCounter < 30) {
                console.log("🖱️ Klikam 'Dalej'...");
                await page.evaluate(el => {
                    el.scrollIntoView();
                    el.click();
                }, nextButton);
                
                // Losowe czekanie, by udawać człowieka (6-10 sekund)
                const delay = Math.floor(Math.random() * 4000) + 6000;
                await new Promise(r => setTimeout(r, delay));
                pageCounter++;
            } else {
                hasNextPage = false;
            }
        }

        if (allData.length > 0) {
            fs.writeFileSync('scarlet_db_full.json', JSON.stringify(allData, null, 2));
            console.log(`\n🎉 SUKCES! Baza pelna-kulturka.pl zaktualizowana: ${allData.length} modów.`);
        } else {
            console.log("⚠️ Pobrano 0 rekordów. Serwer może blokować treść tabeli.");
        }

    } catch (error) {
        console.error("❌ BŁĄD:", error.message);
        process.exit(1);
    } finally {
        await browser.close();
    }
})();
