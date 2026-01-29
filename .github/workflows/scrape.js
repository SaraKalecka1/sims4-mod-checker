const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
    console.log("🚀 Starting the bot for pelna-kulturka.pl...");
    const browser = await puppeteer.launch({ 
        headless: true,
        args: [
            '--no-sandbox', 
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
    });
    
    const page = await browser.newPage();
    await page.setDefaultNavigationTimeout(120000);

    try {
        console.log("🔗 Navigating to the mod list...");
        await page.goto('https://scarletsrealm.com/the-sims-4/mods/mod-list/', { 
            waitUntil: 'networkidle2' 
        });

        let allData = [];
        let hasNextPage = true;
        let pageCounter = 1;

        while (hasNextPage) {
            console.log(`Scraping page ${pageCounter}...`);
            
            // Czekamy na załadowanie tabeli
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

            if (data.length > 0) {
                allData.push(...data);
                console.log(`✅ Collected ${data.length} records.`);
            }
            
            const nextButton = await page.$('.footable-page-nav[data-page="next"]:not(.disabled)');
            if (nextButton && pageCounter < 25) { 
                await nextButton.click();
                await new Promise(r => setTimeout(r, 5000));
                pageCounter++;
            } else {
                hasNextPage = false;
            }
        }

        fs.writeFileSync('scarlet_db_full.json', JSON.stringify(allData, null, 2));
        console.log(`✅ Success! Total records saved: ${allData.length}`);

    } catch (error) {
        console.error("❌ Critical Error:", error.message);
        process.exit(1);
    } finally {
        await browser.close();
    }
})();
