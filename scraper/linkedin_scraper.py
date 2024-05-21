import asyncio
import random
import re
from pyppeteer import launch, errors
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time, os, psycopg2, pytz
import random
from utils.db import insert_to_db

LINKEDIN_LOGIN_PAGE = 'https://linkedin.com/login'
LINKEDIN_LOGIN_BUTTON = '.btn__primary--large.from__button--floating'

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

async def scrape(linkedInEmail, linkedInPassword):
    print("Scraping job from LinkedIn ...")
    
    possible_args = [
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
    ]
    
    random.shuffle(possible_args)
    
    selected_args = random.sample(possible_args, 3)
    
    browser = await launch(
    headless=True,
    handleSIGINT=False,
    handleSIGTERM=False,
    handleSIGHUP=False,
    args=[
        *selected_args,
    ],
)

    context = await browser.createIncognitoBrowserContext()
    page = await context.newPage()
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')

    try: 
        await page.goto(LINKEDIN_LOGIN_PAGE)
        await page.type('#username', linkedInEmail)
        await page.type('#password', linkedInPassword)
        await page.click('button[data-litms-control-urn="login-submit"]')
        await page.waitForNavigation()
        print("Logged in to LinkedIn")
    except (errors.TimeoutError, errors.ElementHandleError, AttributeError) as e:
        print(f"Login failed: {e}")
        await browser.close()

    jenis_urls =  {
        'programmer' : 'https://www.linkedin.com/jobs/search/?keywords=programmer&location=Indonesia',
        'data' : 'https://www.linkedin.com/jobs/search/?keywords=data&location=Indonesia',
        'network' : 'https://www.linkedin.com/jobs/search/?keywords=network&location=Indonesia',
        'cyber security' : 'https://www.linkedin.com/jobs/search/?keywords=cyber%20security&location=Indonesia',
    }
    
    job_ids = []

    for jenis in jenis_urls:
        i=0;
        current_page = 1
        all_loaded = False
        
        print(f'Currently scraping for this URL: {jenis_urls[jenis]}')
        
        await page.goto(jenis_urls[jenis])
        
        await page.waitFor(3000)
        print("Page has been finished rendering")
        
        
        await page.waitForSelector('.artdeco-pagination__indicator--number:last-child')

        # Mendapatkan elemen terakhir dari halaman
        last_page_element = await page.querySelector('.artdeco-pagination__indicator--number:last-child')

        # Mendapatkan teks dari elemen terakhir untuk mendapatkan nomor halaman terakhir
        last_page_number = await page.evaluate('(element) => element.textContent', last_page_element)

        print(f'Last page for this url is : {int(last_page_number)}')
        
        while not all_loaded:
            try:
                await page.waitForSelector('.ember-view.jobs-search-results__list-item.occludable-update.p0.relative.scaffold-layout__list-item', timeout=10000)
                job_elements = await page.querySelectorAll('.ember-view.jobs-search-results__list-item.occludable-update.p0.relative.scaffold-layout__list-item')
                
                print(f"Page {current_page} - Total links found: {len(job_elements)}")
                
                for job_element in job_elements:
                    job_id = await page.evaluate('(element) => element.getAttribute("data-occludable-job-id")', job_element)
                    if (job_id in job_ids):
                        continue
                    else:
                        job_ids.append(job_id)
                        job_url = f'https://www.linkedin.com/jobs/view/{job_id}'
                        print(job_url)
                    
                        page_job = await context.newPage()
                        await page_job.goto(job_url)
                    
                        await page_job.waitFor(2500)
                        
                        date_element = await page_job.querySelectorAll('span.tvm__text.tvm__text--low-emphasis, span.tvm__text.tvm__text--positive')
                        date_text = await page_job.evaluate('(element) => element.textContent', date_element[2])
                        date_text = date_text.lower()
                        date_text = date_text.strip()
                        print(date_text)
                        
                        if "months" in date_text:
                            words = date_text.split()
                            index = words.index("months")
                            months = int(words[index - 1])
                            
                            if months > 2:
                                continue
                        
                        judul_lowongan_element =  await page_job.querySelector('.t-24.job-details-jobs-unified-top-card__job-title')
                        h1_element = await judul_lowongan_element.querySelector('h1.t-24.t-bold.inline')
                        judul_lowongan = await page_job.evaluate('(element) => element.textContent', h1_element)
                        print(judul_lowongan)     
                        tanggal_publikasi = None
                        
                        if date_text.startswith('reposted'):
                            date_text = date_text.split()
                            numb = int(date_text[1])
                            unit = date_text[2]
                            tanggal_publikasi = convert_relative_time_to_date(numb, unit)
                        else:
                            date_text = date_text.split()
                            numb = int(date_text[0])
                            unit = date_text[1]
                            tanggal_publikasi = convert_relative_time_to_date(numb, unit)
                        
                        print(tanggal_publikasi)
                        
                        location_element = await page_job.querySelectorAll('span.tvm__text')
                        lokasi_pekerjaan = await page_job.evaluate('(element) => element.textContent', location_element[0])
                        
                        print(lokasi_pekerjaan)
                        
                        perusahaan = None
                        
                        company_element = await page_job.querySelector('.job-details-jobs-unified-top-card__company-name')
                        link_company = await company_element.querySelector('a')
                        
                        if (link_company):
                            perusahaan = await page_job.evaluate('(element) => element.querySelector("a").textContent.trim()', company_element)
                        else:
                            perusahaan = await page_job.evaluate('(element) => element.textContent.trim()', company_element)
                         
                        print(perusahaan)
                        
                        sumber_situs = "linkedin.com"
                        
                        button_apply = '.jobs-apply-button.artdeco-button.artdeco-button--3.artdeco-button--primary.ember-view'
                        link_lowongan = None

                        is_external_link = await page_job.evaluate('(element) => element.querySelector("span").textContent.trim()', button_apply)
                        
                        if is_external_link.startswith('Apply'):
                            await page_job.click(button_apply)
                            await page_job.waitFor(2500)
                            await page.waitForSelector('.jobs-apply-button.artdeco-button.artdeco-button--icon-right.artdeco-button--3.artdeco-button--primary');
                            await page_job.click('.jobs-apply-button.artdeco-button.artdeco-button--icon-right.artdeco-button--3.artdeco-button--primary')
                            link_lowongan = page_job.url
                        else:
                            link_lowongan = page_job.url
                            
                        print(link_lowongan)
                        
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
                        
                        await page_job.close()
                        await page.waitFor(1000)

                current_page += 1
                
                if await page.querySelector(f'[aria-label="Page {current_page}"]'):
                    page_button = await page.querySelector(f'[aria-label="Page {current_page}"]')
                    await page_button.click()
                    await page.waitFor(5000)
                else:
                    all_loaded=True
                
                all_loaded = True
                
            except (errors.TimeoutError, errors.ElementHandleError, AttributeError) as e:
                print(f"Error on page {current_page}: {e}")
                all_loaded = True
            
    try:
        await page.goto('https://www.linkedin.com/m/logout/')
        print('Logged out from LinkedIn')
    except (errors.TimeoutError, errors.ElementHandleError, AttributeError) as e:
        print(f"Logout failed: {e}")
    finally: 
        await browser.close()