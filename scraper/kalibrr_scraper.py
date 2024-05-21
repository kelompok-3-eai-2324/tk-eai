from pyppeteer import launch, errors
from utils.db import insert_to_db
from utils.date import convert_relative_time_to_date
import time

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

    jenis_urls = {
        'programmer' : 'https://www.kalibrr.com/id-ID/home/te/programmer/co/Indonesia?sort=Freshness',
        'data' : 'https://www.kalibrr.com/id-ID/home/te/data/co/Indonesia?sort=Freshness',
        'network': 'https://www.kalibrr.com/id-ID/home/te/network/co/Indonesia?sort=Freshness',
        'cyber security' : 'https://www.kalibrr.com/id-ID/home/te/cyber-security/co/Indonesia?sort=Freshness',
    }

    for jenis in jenis_urls:
        context = await browser.createIncognitoBrowserContext()
        page = await context.newPage()
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')
        await page.goto(jenis_urls[jenis])

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
                    link_lowongan=link_lowongan,
                    jenis_pekerjaan=jenis,
                )
                print(d, flush=True)
                insert_to_db(d)

            except Exception as e:
                print('Error:',e)
                pass

            await context.close()        

    print('Scraping done in:',round(time.time() - start,2),'seconds')