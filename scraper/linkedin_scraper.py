import asyncio
import random
import re
from pyppeteer import launch, errors
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time, os, psycopg2, pytz

load_dotenv()

LINKEDIN_EMAIL=os.getenv('LINKEDIN_EMAIL')
LINKEDIN_PASSWORD=os.getenv('LINKEDIN_PASSWORD')

LINKEDIN_LOGIN_PAGE = 'https://linkedin.com/login'
LINKEDIN_LOGIN_BUTTON = '.btn__primary--large.from__button--floating'

async def scrape(linkedInEmail, linkedInPassword):
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

    urls = [
        'https://www.linkedin.com/jobs/search/?keywords=programmer&location=Indonesia',
        'https://www.linkedin.com/jobs/search/?keywords=data&location=Indonesia',
        'https://www.linkedin.com/jobs/search/?keywords=network&location=Indonesia',
        'https://www.linkedin.com/jobs/search/?keywords=cyber%20security&location=Indonesia',
    ]
    
    job_links = []

    for url in urls:
        current_page = 1
        all_loaded = False
        
        print(f'Currently scraping for this URL: {url}')
        
        await page.goto(url)
        
        await page.waitFor(3000)
        print("Page has been finished rendering")
        
        while not all_loaded:
            try:
                await page.waitForSelector('.ember-view.jobs-search-results__list-item.occludable-update.p0.relative.scaffold-layout__list-item', timeout=10000)
                job_elements = await page.querySelectorAll('.ember-view.jobs-search-results__list-item.occludable-update.p0.relative.scaffold-layout__list-item')
                
                print(f"Page {current_page} - Total links found: {len(job_elements)}")
                
                links_added = 0
                
                for job_element in job_elements:
                    await job_element.click()
                    await page.waitForSelector('.jobs-search__job-details--wrapper', timeout=10000)
                    
                    date_element = await page.querySelector('.jobs-search__job-details--wrapper span.tvm__text--neutral')
                    date_text = await page.evaluate('(element) => element.textContent', date_element)
                    print(f"Current job post date: {date_text}")
                    
                    match = re.search(r'(?:Reposted\s+)?(\d+)\s+(day|week|month)s?\s+ago\b', date_text)
                    if match:
                        time_ago, unit = match.groups()
                        if unit == 'month' and int(time_ago) > 2:
                            continue
                        
                        job_id = await job_element.getProperty('data-occludable-job-id')
                        job_id = await job_id.jsonValue()
                        job_url = f'https://www.linkedin.com/jobs/view/{job_id}'
                        job_links.append(job_url)
                        links_added += 1
                
                print(f"Page {current_page} links scraped: {links_added}/{len(job_elements)}")
                
                current_page += 1
                
                if await page.querySelector(f'[aria-label="Page {current_page}"]'):
                    page_button = await page.querySelector(f'[aria-label="Page {current_page}"]')
                    await page_button.click()
                    await page.waitFor(5000)
                else:
                    all_loaded=True
                
            except (errors.TimeoutError, errors.ElementHandleError, AttributeError) as e:
                print(f"Error on page {current_page}: {e}")
                await browser.close()
                all_loaded = True
            
    try:
        await page.goto('https://www.linkedin.com/m/logout/')
        print('Logged out from LinkedIn')
    except (errors.TimeoutError, errors.ElementHandleError, AttributeError) as e:
        print(f"Logout failed: {e}")
        await browser.close()

    print(f"Total job links found after filter by date: {len(job_links)}")
    await browser.close()

    return job_links

# Run the scrape function asynchronously
async def main():
    start = time.time()
    job_links = await scrape(LINKEDIN_EMAIL, LINKEDIN_PASSWORD)
    # for job_link in job_links:
    #     print(job_link)
    print(f'Scraping done in: {round(time.time() - start, 2)} seconds')

asyncio.run(main())