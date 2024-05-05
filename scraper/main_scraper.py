import jobstreet_scraper, kalibrr_scraper, karir_scraper, linkedin_scraper
import asyncio

def scrape():
    asyncio.get_event_loop().run_until_complete(kalibrr_scraper.scrape())

scrape()