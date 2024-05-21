from . import jobstreet_scraper, kalibrr_scraper, karir_scraper, linkedin_scraper
from utils.db import filter_outdated_lowongan
import asyncio
from dotenv import load_dotenv
import os

LINKEDIN_EMAIL=os.getenv('LINKEDIN_EMAIL')
LINKEDIN_PASSWORD=os.getenv('LINKEDIN_PASSWORD')


def scrape():
    # asyncio.get_event_loop().run_until_complete(kalibrr_scraper.scrape())
    filter_outdated_lowongan()
    asyncio.run(kalibrr_scraper.scrape())
    asyncio.run(jobstreet_scraper.scrape())
    asyncio.run(linkedin_scraper.linkedin_scrape(LINKEDIN_EMAIL, LINKEDIN_PASSWORD))