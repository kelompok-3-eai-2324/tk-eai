from pyppeteer import launch, errors
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time, os, psycopg2, asyncio, pytz, json

load_dotenv()

def convert_relative_time_to_date(number, unit):
    now = datetime.now(pytz.timezone('Asia/Jakarta'))
    if unit.startswith("jam"):
        return now - timedelta(hours=number)
    elif unit.startswith("hari"):
        return now - timedelta(days=number)
    elif unit.startswith("bulan"):
        return now - timedelta(days=number*30)
    else:
        return now
    
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
        'https://www.jobstreet.co.id/id/programmer-jobs?page=%d&sortmode=ListedDate',
        'https://www.jobstreet.co.id/id/data-jobs?page=%d&sortmode=ListedDate',
        'https://www.jobstreet.co.id/id/network-jobs?page=%d&sortmode=ListedDate',
        'https://www.jobstreet.co.id/id/cyber-security-jobs?page=%d&sortmode=ListedDate'
    ]

    for url in urls:
        i = 1
        while 1:
            print('Currently scraping page:',i)
            try:
                context = await browser.createIncognitoBrowserContext()
                page = await context.newPage()
                await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')
                await page.goto(url % i)

                try:
                    await page.waitForSelector('article[data-card-type="JobCard"]')
                except errors.TimeoutError:
                    break

                cards = await page.querySelectorAll('article[data-card-type="JobCard"]')
                for card in cards:
                    as_tag = await card.querySelectorAll('a')
                    judul_lowongan = await page.evaluate("(element) => element.textContent", as_tag[2])
                    perusahaan = await page.evaluate("(element) => element.textContent", as_tag[3])

                    lokasi_a = await card.querySelectorAll('a[data-automation="jobLocation"]')
                    if len(lokasi_a) == 1:
                        lokasi_pekerjaan = await page.evaluate("(element) => element.textContent", lokasi_a[0])
                    else:
                        lokasi_pekerjaan = ', '.join([await page.evaluate("(element) => element.textContent", elem) for elem in lokasi_a])
                    kota = await page.evaluate("(element) => element.textContent", as_tag[4])
                    provinsi = await page.evaluate("(element) => element.textContent", as_tag[5])
                    lokasi_pekerjaan = f'{kota}, {provinsi}'

                    sumber_situs = "jobstreet.co.id"
                    link_lowongan = await (await as_tag[0].getProperty('href')).jsonValue()

                    post_date_span = await card.querySelector('span[data-automation="jobListingDate"]')
                    post_date = await page.evaluate('(element) => element.textContent', post_date_span)
                    num = int(post_date.split()[0].strip('+'))
                    unit = post_date.split()[1]
                    tanggal_publikasi = convert_relative_time_to_date(num, unit)

                    d = dict(
                        judul_lowongan=judul_lowongan,
                        tanggal_publikasi=tanggal_publikasi,
                        lokasi_pekerjaan=lokasi_pekerjaan,
                        perusahaan=perusahaan,
                        sumber_situs=sumber_situs,
                        link_lowongan=link_lowongan
                    )
                    print(json.dumps(d, indent=2), flush=True)
                    insert_to_db(d)
            except Exception as e:
                print(e)
                pass

            await context.close()

            i += 1

    print('Scraping done in:',round(time.time() - start,2),'seconds')