import asyncio
import random
import re
from pyppeteer import launch, errors
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time, os, psycopg2, pytz

LINKEDIN_LOGIN_PAGE = 'https://linkedin.com/login'
LINKEDIN_LOGIN_BUTTON = '.btn__primary--large.from__button--floating'

async def scrape(linkedInEmail, linkedInPassword):
    
    start = time.time()
    print("Scraping job from LinkedIn ...")
    browser = await launch(
        headless=True,
        handleSIGINT=False,
        handleSIGTERM=False,
        handleSIGHUP=False,
        args=[
            "--no-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--start-maximized",
        ],
    )
    
    context = await browser.createIncognitoBrowserContext()
    page = await context.newPage()
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')
    
    
    try : 
        await page.goto(LINKEDIN_LOGIN_PAGE)
        
        await page.type('#username', linkedInEmail)
        
        await page.type('#password', linkedInPassword)
        
        await page.click('button[data-litms-control-urn="login-submit"]')
        
        await page.waitForNavigation()
        await page.waitFor(2500)
        
        print("Logged in to LinkedIn")
    except (errors.TimeoutError, errors.ElementHandleError, AttributeError) as e :
        print(e)
        
    urls = ['https://www.linkedin.com/jobs/search?keywords=programmer&location=Indonesia&position=1&pageNum=0',
            'https://www.linkedin.com/jobs/search?keywords=data&location=Indonesia&position=1&pageNum=0',
            'https://www.linkedin.com/jobs/search?keywords=network&location=Indonesia&position=1&pageNum=0',
            'https://www.linkedin.com/jobs/search?keywords=cyber%20security&location=Indonesia&position=1&pageNum=0',
            ]
    
    job_links = []

    for url in urls:
        current_page = 1
        all_loaded = False
        
        print(f'Currently scraping for this url : {url}')
        
        await page.goto(url)
        
        await page.waitFor(3000)
        
        await page.waitForSelector('.artdeco-pagination__indicator--number:last-child')
                
        # Mendapatkan elemen terakhir dari halaman
        last_page_element = await page.querySelector('.artdeco-pagination__indicator--number:last-child')

        # Mendapatkan teks dari elemen terakhir untuk mendapatkan nomor halaman terakhir
        last_page_number = await page.evaluate('(element) => element.textContent', last_page_element)
        
        print(int(last_page_number))
        
        while not all_loaded:
            try:
                await page.waitForSelector('.ember-view.jobs-search-results__list-item.occludable-update.p0.relative.scaffold-layout__list-item')
                
                job_elements = await page.querySelectorAll('.ember-view.jobs-search-results__list-item.occludable-update.p0.relative.scaffold-layout__list-item')
                
                print(f"Page {current_page} - Total links found: {len(job_elements)}")
                
                links_added = 0
                
                for job_element in job_elements:
                    await job_element.click()
                    
                    await page.waitFor(3000)
                    
                    await page.waitForSelector('.jobs-search__job-details--wrapper')
                    
                     # Dapatkan tanggal posting
                    date_element = await page.querySelector('.jobs-search__job-details--wrapper span.tvm__text--neutral')
                    date_text = await page.evaluate('(element) => element.textContent', date_element)
                    print(f"Current job post date : {date_text}")
                    
                    match = re.search(r'(?:Reposted\s+)?(\d+)\s+(day|week|month)s?\s+ago\b', date_text)
                    if match:
                        time_ago, unit = match.groups()
                        if unit == 'month':
                            if int(time_ago) <= 2:
                                next
                        else:
                            job_id = await job_element.getProperty('data-occludable-job-id')
                            job_id = await job_id.jsonValue()
                            url = f'https://www.linkedin.com/jobs/view/{job_id}'
                            job_links.append(url)
                            links_added += 1
                    
                
                print(f"Page {current_page} link finished scraped ...")
                print(f"Links added to from {current_page} is : {links_added} / {len(job_elements)}")
                # print('Scraped in : ', round(time.time() - start, 2), 'seconds')
                
                current_page += 1
                
                if (current_page > int(last_page_number)):
                    all_loaded = True
                else:
                    page_button = await page.querySelector(f'[aria-label="Page {current_page}"]')
                        
                    await page_button.click()
                    
                    await page.waitFor(5000)
                
            except (errors.TimeoutError, errors.ElementHandleError, AttributeError) as e:
                print(e)
                all_loaded = True
            
    
    try:
        await page.goto('https://www.linkedin.com/m/logout/')

        print('Log out from LinkedIn')
    except (errors.TimeoutError, errors.ElementHandleError, AttributeError) as e :
        print(e)
    
    print(len(job_links))
    
    # for items in job_links:
    #     print(items)
    
    await browser.close()

    print('Scraping done in:', round(time.time() - start, 2), 'seconds')
    
    # return urls


load_dotenv()

def convert_relative_time_to_date(number, unit):
    now = datetime.now(pytz.timezone('Asia/Jakarta'))
    if unit.startswith("hour"):
        return now - timedelta(hours=number)
    elif unit.startswith("day"):
        return now - timedelta(days=number)
    elif unit.startswith("month"):
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

async def scroll_page(page):
    # Tentukan tinggi dari viewport
    viewport_height = page.viewport['height']
    # Hitung tinggi dari konten pada halaman saat ini
    page_height = await page.evaluate("document.body.scrollHeight")

    # Lakukan scroll sampai ke bawah halaman penuh
    while True:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(1)  # Tunggu sebentar untuk memuat konten baru
        # Hitung kembali tinggi konten setelah scrolling
        new_page_height = await page.evaluate("document.body.scrollHeight")
        # Jika tinggi konten tidak bertambah, berarti sudah mencapai akhir halaman
        if new_page_height == page_height:
            break
        page_height = new_page_height



# Jalankan fungsi scrape secara asynchronous
async def main():
    urls_with_hrefs = await scrape("", "")
    # for url, hrefs in urls_with_hrefs.items():
    #     print("URL:", url)
    #     print("Hrefs:", hrefs)

asyncio.run(main())