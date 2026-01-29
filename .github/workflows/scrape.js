const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
    console.log("🚀 Uruchamiam bota skanującego...");
   const browser = await puppeteer.launch({ 
        headless: "shell", // Zmiana z "new" na "shell"
        args: [
            '--no-sandbox', 
            '--disable-setuid-sandbox',
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
    });
    
    const page = await browser.newPage();
    await page.setDefaultNavigationTimeout(60000);

    try {
        // Czysty adres URL (bez nawiasów kwadratowych i okrągłych)
       await page.goto('https://scarletsrealm.com/the-sims-4/mods/mod-list/', { 
    waitUntil: 'networkidle2' 
});

        let allData = [];
        let hasNextPage = true;
        let pageCounter = 1;

        while (hasNextPage) {
            console.log(`Pobieranie strony ${pageCounter}...`);
            
            const data = await page.evaluate(() => {
                const rows = document.querySelectorAll('.ninja_table_pro tbody tr');
                return Array.from(rows).map(row => ({
                    name: row.querySelector('.ninja_column_0')?.innerText.trim(),
                    author: row.querySelector('.ninja_column_1')?.innerText.trim(),
                    status: row.querySelector('.ninja_column_3')?.innerText.trim(),
                    update: row.querySelector('.ninja_column_4')?.innerText.trim()
                }));
            });

            allData.push(...data);
            
            const nextButton = await page.$('.footable-page-nav[data-page="next"]:not(.disabled)');
            if (nextButton && pageCounter < 25) { 
                await nextButton.click();
                await new Promise(r => setTimeout(r, 3000));
                pageCounter++;
            } else {
                hasNextPage = false;
            }
        }

        fs.writeFileSync('scarlet_db_full.json', JSON.stringify(allData, null, 2));
        console.log(`✅ Sukces! Zebrano ${allData.length} rekordów.`);

    } catch (error) {
        console.error("❌ Błąd:", error);
        process.exit(1);
    } finally {
        await browser.close();
    }
})();
