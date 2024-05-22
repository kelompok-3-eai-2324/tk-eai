import asyncio
import random
import re
from pyppeteer import launch, errors
from datetime import datetime, timedelta
import time, os, psycopg2, pytz
import random
from utils.db import insert_to_db

def convert_relative_time_to_date(number, unit):
    now = datetime.now(pytz.timezone('Asia/Jakarta'))
    if re.search(r'week[s]?', unit):
        return now - timedelta(weeks=number)
    elif re.search(r'day[s]?', unit):
        return now - timedelta(days=number)
    elif re.search(r'month[s]?', unit):
        return now - timedelta(days=number * 30)
    elif re.search(r'hour[s]?', unit):
        return now - timedelta(hours=number)
    elif re.search(r'minute[s]?', unit):
        return now - timedelta(minutes=number)
    else:
        return now

async def random_delay(min_delay, max_delay):
    delay = random.uniform(min_delay, max_delay)
    await asyncio.sleep(delay)
    
async def scrape():
    print("Scraping job from Karir ...")

    
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
        "--ignore-certificate-errors",
        "--disable-infobars",
        "--disable-notifications",
        "--disable-popup-blocking",
        "--disable-background-networking",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        ],
    )

    context = await browser.createIncognitoBrowserContext()
    page = await context.newPage()
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')

    jenis_urls = {
        'programmer' : 'https://karir.com/search-lowongan?keyword=programmer',
        'data' : 'https://karir.com/search-lowongan?keyword=data',
        'network': 'https://karir.com/search-lowongan?keyword=network',
        'cyber security' : 'https://karir.com/search-lowongan?keyword=cyber%20security',
        
    }
    
    for jenis in jenis_urls:
        context = await browser.createIncognitoBrowserContext()
        page = await context.newPage()
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')
        await page.goto(jenis_urls[jenis])
        
        all_loaded = False
        i = 0
        current_page = 1
        
        print (f'Currently scraping for this url : {jenis}')
        
        while not all_loaded:
            try:
                await random_delay(1,3)
                print (f'Page {current_page} for {jenis} has been finished rendered')
                
                await page.waitForSelector('.jsx-4093401097.container')
                job_elements = await page.querySelectorAll('.jsx-4093401097.container')
                
                print(f'Page {current_page} - Total links found : {len(job_elements)}')
                
                current_index = 0
                
                for job_element in job_elements:
                    
                    await job_elements[current_index].click()
                    
                    current_index += 1
                    await page.waitForNavigation()
                    await random_delay(1,3)
                    
                    judul_lowongan_element = await page.querySelector('.MuiTypography-root.MuiTypography-body1.css-f6lc1t')
                    judul_lowongan = await page.evaluate('(element) => element.textContent', judul_lowongan_element)
                    
                    
                    tanggal_publikasi_element = await page.querySelectorAll('.MuiTypography-root.MuiTypography-body1.css-1l6lhfq')
                    tanggal_publikasi = await page.evaluate('(element) => element.textContent', tanggal_publikasi_element[1])

                    tanggal_publikasi = tanggal_publikasi.split(" ")
                    
                    if tanggal_publikasi[2] == "bulan" and int(tanggal_publikasi[1]) > 2:
                        continue
                    else:
                        if len(tanggal_publikasi) == 3:
                            number = int(tanggal_publikasi[0])
                            unit = tanggal_publikasi[1]
                        else:
                            number = int(tanggal_publikasi[1])
                            unit = tanggal_publikasi[2]

                    tanggal_publikasi = convert_relative_time_to_date(number, unit)
                    
                    
                    lokasi_pekerjaan = None
                    
                    lokasi_and_perusahaan_element = await page.querySelectorAll('.MuiTypography-root.MuiTypography-body1.css-6uefso')
                    if (len(lokasi_and_perusahaan_element) == 4):
                        lokasi_pekerjaan = await page.evaluate('(element) => element.textContent', lokasi_and_perusahaan_element[2])
                    elif (len(lokasi_and_perusahaan_element) == 3):
                        lokasi_pekerjaan = await page.evaluate('(element) => element.textContent', lokasi_and_perusahaan_element[1])
                    
                    
                    perusahaan = None
                    
                    perusahaan_element = await page.querySelector('.MuiTypography-root.MuiTypography-body1.css-wqnft9')
                    if (perusahaan_element):
                        perusahaan = await page.evaluate('(element) => element.textContent', perusahaan_element)
                    else:
                        perusahaan_element = await page.querySelectorAll('.MuiTypography-root.MuiTypography-body1.css-6uefso')
                        perusahaan = await page.evaluate('(element) => element.textContent', lokasi_and_perusahaan_element[0])
                    
                    
                    sumber_situs = "karir.com"
                    
                    link_lowongan = page.url
                    
                    d = dict(
                        no=i,
                        judul_lowongan=judul_lowongan,
                        tanggal_publikasi=tanggal_publikasi,
                        lokasi_pekerjaan=lokasi_pekerjaan,
                        perusahaan=perusahaan,
                        sumber_situs=sumber_situs,
                        link_lowongan=link_lowongan,
                        jenis_pekerjaan=jenis,
                        )
                    print(d, flush=True)
                    insert_to_db(d)
                    
                    i += 1
                    
                    await page.goBack()
                    await page.reload()
                    await random_delay(2,4)
                    await page.waitForSelector('.jsx-4093401097.container')
                    job_elements = await page.querySelectorAll('.jsx-4093401097.container')
                
                current_page += 1
                
                next_page_button = await page.xpath(f"//div[contains(@class, 'jsx-2806892642') and text()='{current_page}']")
                
                if next_page_button:
                    await next_page_button[0].click()
                    await random_delay(1,3)
                else :
                    all_loaded = True
            
            except (errors.TimeoutError, errors.ElementHandleError, AttributeError) as e :
                print(f"Error on page {current_page}: {e}")
                all_loaded = True
    
    await browser.close()