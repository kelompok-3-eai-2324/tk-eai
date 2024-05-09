from pyppeteer import launch, errors
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time, os, psycopg2, pytz, json

load_dotenv()

def convert_relative_time_to_date(number, unit):
    now = datetime.now(pytz.timezone('Asia/Jakarta'))
    if unit.startswith("hour"):
        return (now - timedelta(hours=number)).strftime("%Y-%m-%d")
    elif unit.startswith("day"):
        return (now - timedelta(days=number)).strftime("%Y-%m-%d")
    elif unit.startswith("month"):
        return (now - timedelta(days=number*30)).strftime("%Y-%m-%d")
    else:
        return now.strftime("%Y-%m-%d")
    
def insert_to_db(data):
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')
    DB_NAME = os.getenv('DB_NAME')

    with psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
        ) as conn:

        with conn.cursor() as cur:
            cur.execute("""
                        SELECT tanggal_publikasi FROM lowongan_table WHERE perusahaan = %s AND judul_lowongan = %s;
                        """, (data["perusahaan"], data["judul_lowongan"]))
            existing_row = cur.fetchone()

            if existing_row:
                existing_tanggal_publikasi = existing_row[0]
                if existing_tanggal_publikasi < data["tanggal_publikasi"]:
                    cur.execute("""
                                DELETE FROM lowongan_table WHERE perusahaan = %s AND judul_lowongan = %s;
                                """, (data["perusahaan"], data["judul_lowongan"]))

                    cur.execute("""
                                INSERT INTO lowongan_table (judul_lowongan, tanggal_publikasi, lokasi_pekerjaan, perusahaan, sumber_situs, link_lowongan)
                                VALUES (%s, %s, %s, %s, %s, %s);
                                """, (data["judul_lowongan"], data["tanggal_publikasi"], data["lokasi_pekerjaan"], data["perusahaan"], data["sumber_situs"], data["link_lowongan"]))
            else:
                cur.execute("""
                            INSERT INTO lowongan_table (judul_lowongan, tanggal_publikasi, lokasi_pekerjaan, perusahaan, sumber_situs, link_lowongan)
                            VALUES (%s, %s, %s, %s, %s, %s);
                            """, (data["judul_lowongan"], data["tanggal_publikasi"], data["lokasi_pekerjaan"], data["perusahaan"], data["sumber_situs"], data["link_lowongan"]))

        conn.commit()
    
async def scrape():
    start = time.time()
    browser = await launch(
        headless=True,
        handleSIGINT=False,
        handleSIGTERM=False,
        handleSIGHUP=False,
        args= [
            "--no-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--start-maximized",
            ],
    )

    urls = [
        'https://www.kalibrr.com/id-ID/home/te/programmer/co/Indonesia?sort=Freshness',
        'https://www.kalibrr.com/id-ID/home/te/data/co/Indonesia?sort=Freshness',
        'https://www.kalibrr.com/id-ID/home/te/network/co/Indonesia?sort=Freshness',
        'https://www.kalibrr.com/id-ID/home/te/cyber-security/co/Indonesia?sort=Freshness',
    ]

    for url in urls:
        context = await browser.createIncognitoBrowserContext()
        page = await context.newPage()
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')
        await page.goto(url)

        all_loaded = False
        i = 0
        while not all_loaded:
            try:
                await page.waitForSelector('.k-font-dm-sans.k-w-full.k-flex.k-justify-center.k-mb-10')
                load_more_div = await page.querySelector('.k-font-dm-sans.k-w-full.k-flex.k-justify-center.k-mb-10')
                load_more_btn = await load_more_div.querySelector('.k-btn-primary')
                await load_more_btn.click()
            except (errors.TimeoutError, errors.ElementHandleError, AttributeError) as e:
                print(e)
                all_loaded = True

        await page.waitForSelector(".k-w-36.k-text-center.k-btn-primary.k-bg-white.k-text-primary-color")
        job_links = await page.querySelectorAll(".k-w-36.k-text-center.k-btn-primary.k-bg-white.k-text-primary-color")
        
        arr = []
        for i, job_link in enumerate(job_links):
            try:
                job_href = await job_link.getProperty('href')
                job_url = await job_href.jsonValue()

                context = await browser.createIncognitoBrowserContext()
                page = await context.newPage()
                await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')
                await page.goto(job_url)

                
                await page.waitForSelector('.md\\:k-flex.md\\:k-justify-between')
                containers = await page.querySelectorAll('.md\\:k-flex.md\\:k-justify-between')
                container = containers[0]

                post_date_div = await container.querySelector('.k-text-subdued.k-text-caption')
                post_date_p = await post_date_div.querySelector('p')
                post_date_text = await page.evaluate('(element) => element.textContent', post_date_p)
                date_num, date_unit = post_date_text.split()[2:4]
                date_num = 1 if date_num == 'a' else int(date_num)

                if (date_unit == 'year' or date_unit == 'years' or (date_unit == 'months' and date_num > 2)):
                    break

                judul_lowongan_h1 = await container.querySelector('.k-text-title.k-inline-flex.k-items-center')
                judul_lowongan = await page.evaluate('(element) => element.textContent', judul_lowongan_h1)
                judul_lowongan = judul_lowongan.strip(' \xa0')

                tanggal_publikasi = convert_relative_time_to_date(date_num, date_unit)

                lokasi_pekerjaan_div = await container.querySelector('div[itemprop="streetAddress"]')
                lokasi_pekerjaan = await page.evaluate('(element) => element.textContent', lokasi_pekerjaan_div)

                spans = await container.querySelectorAll('.k-flex.k-items-center')
                perusahaan_span = spans[1]
                perusahaan_h2 = await perusahaan_span.querySelector('h2')
                perusahaan = await page.evaluate('(element) => element.textContent', perusahaan_h2)

                sumber_situs = 'kalibrr.com'

                link_lowongan = job_url

                d = dict(
                    no=i,
                    judul_lowongan=judul_lowongan,
                    tanggal_publikasi=tanggal_publikasi,
                    lokasi_pekerjaan=lokasi_pekerjaan,
                    perusahaan=perusahaan,
                    sumber_situs=sumber_situs,
                    link_lowongan=link_lowongan
                )
                print(json.dumps(d, indent=2))
                arr.append(d)
                insert_to_db(d)

            except Exception as e:
                print(e)
                pass

            await context.close()        

    print('Scraping done in:',round(time.time() - start,2),'seconds')