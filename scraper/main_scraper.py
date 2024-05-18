from . import jobstreet_scraper, kalibrr_scraper, karir_scraper, linkedin_scraper
from utils.db import filter_outdated_lowongan
import asyncio


def scrape():
    # asyncio.get_event_loop().run_until_complete(kalibrr_scraper.scrape())
    filter_outdated_lowongan()
    asyncio.run(kalibrr_scraper.scrape())
    asyncio.run(jobstreet_scraper.scrape())