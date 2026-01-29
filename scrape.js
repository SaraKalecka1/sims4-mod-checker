const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
    console.log("🚀 Uruchamiam skaner dla pelna-kulturka.pl...");
    const browser = await puppeteer.launch({ 
        headless: "shell",
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });
    
    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36');

    try {
        console.log("🔗 Łączenie z: https://scarletsrealm.com/the-mod-list-sfw-nsfw-edition/");
        
        // Używamy adresu podanego przez Ciebie
        await page.goto('https://scarletsrealm.com/the-mod-list-sfw-nsfw-edition/', { 
            waitUntil: 'networkidle2',
            timeout: 90000 
        });

        console.log("⏳ Czekam na tabelę Ninja Tables...");
        // Czekamy konkretnie na wiersze danych, nie tylko na samą tabelę
        await page.waitForSelector('.ninja_table_pro tbody tr', { timeout: 60000 });

        let allData = [];
        let pageCounter = 1;
        let hasNextPage = true;

        while (hasNextPage && pageCounter <= 25) {
            console.log(`Pobieranie strony ${pageCounter}...`);

            const data = await page.evaluate(() => {
                const rows = document.querySelectorAll('.ninja_table_pro tbody tr');
                return Array.from(rows).map(row => ({
                    name: row.querySelector('.ninja_column_0')?.innerText.trim() || "Brak",
                    author: row.querySelector('.ninja_column_1')?.innerText.trim() || "Brak",
                    status: row.querySelector('.ninja_column_3')?.innerText.trim() || "Brak",
                    update: row.querySelector('.ninja_column_4')?.innerText.trim() || "Brak"
                })).filter(item => item.name !== "Brak");
            });

            if (data.length > 0) {
                allData.push(...data);
                console.log(`✅ Pobrano ${data.length} pozycji.`);
            }

            // Przycisk "Next" w tabelach Ninja / FooTable
            const nextButton = await page.$('.footable-page-nav[data-page="next"]:not(.disabled)');
            if (nextButton) { 
                await nextButton.click();
                // Ważne: dajemy stronie czas na odświeżenie wierszy
                await new Promise(r => setTimeout(r, 5000));
                pageCounter++;
            } else {
                hasNextPage = false;
            }
        }

        if (allData.length > 0) {
            fs.writeFileSync('scarlet_db_full.json', JSON.stringify(allData, null, 2));
            console.log(`\n🎉 Sukces! Zapisano łącznie: ${allData.length} rekordów.`);
        } else {
            console.log("\n⚠️ Tabela została znaleziona, ale wiersze są puste. Sprawdź selektory.");
        }

    } catch (error) {
        console.error("❌ Błąd krytyczny:", error.message);
        process.exit(1);
    } finally {
        await browser.close();
    }
})();
