const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
    console.log("🚀 Startujemy!");
    const browser = await puppeteer.launch({ 
        headless: "shell",
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const page = await browser.newPage();
    await page.setDefaultNavigationTimeout(90000);

    try {
        console.log("🔗 Otwieranie strony...");
        await page.goto('https://scarletsrealm.com/the-sims-4/mods/mod-list/', { 
            waitUntil: 'networkidle2' 
        });

        let allData = [];
        let hasNextPage = true;
        let pageCounter = 1;

        while (hasNextPage && pageCounter <= 25) {
            console.log(`Pobieranie strony ${pageCounter}...`);
            await page.waitForSelector('.ninja_table_pro', { timeout: 10000 }).catch(() => null);

            const data = await page.evaluate(() => {
                const rows = document.querySelectorAll('.ninja_table_pro tbody tr');
                return Array.from(rows).map(row => ({
                    name: row.querySelector('.ninja_column_0')?.innerText.trim(),
                    author: row.querySelector('.ninja_column_1')?.innerText.trim(),
                    status: row.querySelector('.ninja_column_3')?.innerText.trim(),
                    update: row.querySelector('.ninja_column_4')?.innerText.trim()
                }));
            });

            if (data.length > 0) allData.push(...data);
            
            const nextButton = await page.$('.footable-page-nav[data-page="next"]:not(.disabled)');
            if (nextButton) { 
                await nextButton.click();
                await new Promise(r => setTimeout(r, 4000));
                pageCounter++;
            } else {
                hasNextPage = false;
            }
        }

        fs.writeFileSync('scarlet_db_full.json', JSON.stringify(allData, null, 2));
        console.log(`✅ Gotowe! Zapisano rekordów: ${allData.length}`);

    } catch (error) {
        console.error("❌ Błąd:", error.message);
        process.exit(1);
    } finally {
        await browser.close();
    }
})();
