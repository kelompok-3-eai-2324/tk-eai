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
        'programmer' : 'https://www.jobstreet.co.id/id/programmer-jobs?page=%d&sortmode=ListedDate',
        'data' : 'https://www.jobstreet.co.id/id/data-jobs?page=%d&sortmode=ListedDate',
        'network': 'https://www.jobstreet.co.id/id/network-jobs?page=%d&sortmode=ListedDate',
        'cyber security' : 'https://www.jobstreet.co.id/id/cyber-security-jobs?page=%d&sortmode=ListedDate'
    }

    for jenis in jenis_urls:
        i = 1
        while 1:
            print('Currently scraping page:',i)
            try:
                context = await browser.createIncognitoBrowserContext()
                page = await context.newPage()
                await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')
                await page.goto(jenis_urls[jenis] % i)

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
                        link_lowongan=link_lowongan,
                        jenis_pekerjaan=jenis
                    )
                    print(d, flush=True)
                    insert_to_db(d)
            except Exception as e:
                print(e)
                pass

            await context.close()

            i += 1

    print('Scraping done in:',round(time.time() - start,2),'seconds')