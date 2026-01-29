const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
    console.log("🚀 Uruchamiam zaawansowany skaner dla pelna-kulturka.pl...");
    const browser = await puppeteer.launch({ 
        headless: "shell",
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-http2']
    });
    
    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36');
    await page.setViewport({ width: 1280, height: 800 });

    try {
        const url = 'https://scarletsrealm.com/the-mod-list-sfw-nsfw-edition/';
        console.log(`🔗 Próba połączenia z: ${url}`);
        
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });

        console.log("⏳ Czekam na tabelę Ninja (15s)...");
        await new Promise(r => setTimeout(r, 15000));

        let allData = [];
        let pageCounter = 1;
        let hasNextPage = true;

        while (hasNextPage && pageCounter <= 30) {
            console.log(`📥 Scrapowanie strony ${pageCounter}...`);

            // Pobieranie danych
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
                }).filter(item => item.name.length > 1);
            });

            if (data.length > 0) {
                allData.push(...data);
                console.log(`✅ Pobrano ${data.length} wierszy.`);
            }

            // --- POPRAWKA KLIKANIA (Next Button) ---
            const nextButton = await page.$('li.footable-page-nav[data-page="next"] a');
            
            if (nextButton) {
                console.log("🖱️ Przechodzę do następnej strony...");
                // Przewijamy do przycisku, żeby był widoczny
                await page.evaluate(el => el.scrollIntoView({ behavior: 'smooth', block: 'center' }), nextButton);
                await new Promise(r => setTimeout(r, 2000));
                
                // Klikamy przez evaluate (bardziej odporne na przeszkody)
                await page.evaluate(el => el.click(), nextButton);
                
                // Czekamy aż tabela się przeładuje
                await new Promise(r => setTimeout(r, 8000));
                pageCounter++;
            } else {
                console.log("🏁 Koniec stron lub przycisk nieaktywny.");
                hasNextPage = false;
            }
        }

        if (allData.length > 0) {
            fs.writeFileSync('scarlet_db_full.json', JSON.stringify(allData, null, 2));
            console.log(`\n🎉 SUKCES! Zapisano łącznie: ${allData.length} modów.`);
        }

    } catch (error) {
        console.error("❌ BŁĄD:", error.message);
        process.exit(1);
    } finally {
        await browser.close();
    }
})();
