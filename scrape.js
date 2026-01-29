const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
    console.log("🚀 Uruchamiam pancerny skaner PEŁNEJ LISTY dla pelna-kulturka.pl...");
    const browser = await puppeteer.launch({ 
        headless: "shell",
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-http2', '--disable-blink-features=AutomationControlled']
    });
    
    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36');

    try {
        const url = 'https://scarletsrealm.com/the-mod-list-sfw-nsfw-edition/';
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 90000 });

        console.log("⏳ Czekam, aż tabela wczyta dane (może to zająć do 30s)...");
        
        // POPRAWKA: Czekamy, aż w tabeli pojawi się WIĘCEJ niż 5 wierszy (to eliminuje błąd "1 moda")
        await page.waitForFunction(() => {
            const rows = document.querySelectorAll('.ninja_table_pro tbody tr');
            return rows.length > 5; 
        }, { timeout: 60000 });

        let allData = [];
        let pageCounter = 1;
        let hasNextPage = true;

        while (hasNextPage && pageCounter <= 500) {
            console.log(`📥 Przetwarzanie strony ${pageCounter}...`);

            const data = await page.evaluate(() => {
                const rows = document.querySelectorAll('.ninja_table_pro tbody tr');
                return Array.from(rows).map(row => {
                    const cols = row.querySelectorAll('td');
                    return {
                        name: cols[0]?.innerText.trim() || "",
                        author: cols[1]?.innerText.trim() || "",
                        category: cols[2]?.innerText.trim() || "", // DODANO: Gatunek
                        status: cols[3]?.innerText.trim() || "",
                        update: cols[4]?.innerText.trim() || ""
                    };
                }).filter(item => item.name.length > 2);
            });

            if (data.length > 0) {
                allData.push(...data);
                if (pageCounter % 10 === 0) console.log(`📊 Suma pobranych rekordów: ${allData.length}`);
            }

            const nextButton = await page.$('li.footable-page-nav[data-page="next"] a');
            if (nextButton) {
                await page.evaluate(el => {
                    el.scrollIntoView();
                    el.click();
                }, nextButton);
                
                // Czekamy, aż wiersze się zmienią po kliknięciu
                await new Promise(r => setTimeout(r, 5000));
                pageCounter++;
            } else {
                console.log("🏁 Brak przycisku 'Dalej'. Kończę pobieranie.");
                hasNextPage = false;
            }
        }

        if (allData.length > 0) {
            fs.writeFileSync('scarlet_db_full.json', JSON.stringify(allData, null, 2));
            console.log(`\n🎉 SUKCES! Pobrano całą bazę: ${allData.length} modów (w tym gatunki).`);
        }

    } catch (error) {
        console.error("❌ BŁĄD:", error.message);
        process.exit(1);
    } finally {
        await browser.close();
    }
})();
