const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
    console.log("🚀 Uruchamiam skaner dla pelna-kulturka.pl...");
    const browser = await puppeteer.launch({ 
        headless: "shell",
        args: [
            '--no-sandbox', 
            '--disable-setuid-sandbox', 
            '--disable-dev-shm-usage',
            '--disable-http2' // KLUCZOWA POPRAWKA: Wyłącza HTTP/2, aby uniknąć ERR_HTTP2_PROTOCOL_ERROR
        ]
    });
    
    const page = await browser.newPage();
    
    // Ustawiamy User-Agent, aby bot nie wyglądał jak automat
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36');
    await page.setDefaultNavigationTimeout(90000);

    try {
        const targetUrl = 'https://scarletsrealm.com/the-mod-list-sfw-nsfw-edition/';
        console.log(`🔗 Łączenie z: ${targetUrl}`);
        
        // Przechodzimy na stronę. Jeśli networkidle2 zawiedzie, spróbujemy domcontentloaded
        await page.goto(targetUrl, { 
            waitUntil: 'domcontentloaded', 
            timeout: 60000 
        });

        console.log("⏳ Czekam na załadowanie tabeli modów...");
        // Czekamy 10 sekund na wszelki wypadek, aby skrypty tabeli zdążyły ruszyć
        await new Promise(r => setTimeout(r, 10000));
        await page.waitForSelector('.ninja_table_pro tbody tr', { timeout: 60000 });

        let allData = [];
        let pageCounter = 1;
        let hasNextPage = true;

        while (hasNextPage && pageCounter <= 25) {
            console.log(`Pobieranie danych ze strony ${pageCounter}...`);

            const data = await page.evaluate(() => {
                const rows = document.querySelectorAll('.ninja_table_pro tbody tr');
                return Array.from(rows).map(row => ({
                    name: row.querySelector('.ninja_column_0')?.innerText.trim() || "Brak",
                    author: row.querySelector('.ninja_column_1')?.innerText.trim() || "Brak",
                    status: row.querySelector('.ninja_column_3')?.innerText.trim() || "Brak",
                    update: row.querySelector('.ninja_column_4')?.innerText.trim() || "Brak"
                })).filter(item => item.name !== "Brak" && item.name !== "");
            });

            if (data.length > 0) {
                allData.push(...data);
                console.log(`✅ Pobrano ${data.length} pozycji.`);
            }

            // Przycisk "Next"
            const nextButton = await page.$('.footable-page-nav[data-page="next"]:not(.disabled)');
            if (nextButton) { 
                await nextButton.click();
                await new Promise(r => setTimeout(r, 6000));
                pageCounter++;
            } else {
                hasNextPage = false;
            }
        }

        if (allData.length > 0) {
            fs.writeFileSync('scarlet_db_full.json', JSON.stringify(allData, null, 2));
            console.log(`\n🎉 Sukces! Zapisano łącznie: ${allData.length} rekordów.`);
        } else {
            console.log("\n⚠️ Tabela znaleziona, ale nadal nie pobrano danych. Sprawdzam strukturę...");
        }

    } catch (error) {
        console.error("❌ Błąd krytyczny:", error.message);
        // Jeśli błąd to timeout, spróbujemy zrobić zrzut ekranu do logów w przyszłości
        process.exit(1);
    } finally {
        await browser.close();
    }
})();
