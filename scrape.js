const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
    console.log("🚀 Uruchamiam skaner PEŁNEJ LISTY dla pelna-kulturka.pl...");
    
    const browser = await puppeteer.launch({ 
        headless: "shell",
        args: [
            '--no-sandbox', 
            '--disable-setuid-sandbox', 
            '--disable-http2',
            '--disable-blink-features=AutomationControlled'
        ]
    });
    
    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36');
    await page.setViewport({ width: 1366, height: 768 });

    try {
        const url = 'https://scarletsrealm.com/the-mod-list-sfw-nsfw-edition/';
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 90000 });

        console.log("⏳ Stabilizacja strony (15s)...");
        await new Promise(r => setTimeout(r, 15000));

        let allData = [];
        let pageCounter = 1;
        let hasNextPage = true;

        // ZWIĘKSZONY LIMIT: 500 stron pozwoli pobrać do 10 000 modów
        while (hasNextPage && pageCounter <= 500) {
            console.log(`📥 Przetwarzanie strony ${pageCounter}...`);

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
                if (pageCounter % 10 === 0) console.log(`📊 Suma pobranych: ${allData.length}`);
            }

            const nextButton = await page.$('li.footable-page-nav[data-page="next"] a');
            
            if (nextButton) {
                await page.evaluate(el => {
                    el.scrollIntoView();
                    el.click();
                }, nextButton);
                
                // Krótsze czekanie (4s), by przyspieszyć proces przy 400 stronach
                await new Promise(r => setTimeout(r, 4000));
                pageCounter++;
            } else {
                hasNextPage = false;
            }
        }

        if (allData.length > 0) {
            fs.writeFileSync('scarlet_db_full.json', JSON.stringify(allData, null, 2));
            console.log(`\n🎉 SUKCES! Pobrano całą bazę: ${allData.length} modów.`);
        }

    } catch (error) {
        console.error("❌ BŁĄD:", error.message);
        process.exit(1);
    } finally {
        await browser.close();
    }
})();
