from . import jobstreet_scraper, kalibrr_scraper, karir_scraper, linkedin_scraper
from datetime import datetime, timedelta
from dotenv import load_dotenv
import asyncio, os, psycopg2, pytz

load_dotenv()

def filter_outdated_lowongan():
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
            two_months_ago = datetime.now(pytz.timezone('Asia/Jakarta')) - timedelta(days=60)
            cur.execute("DELETE FROM lowongan_table WHERE tanggal_publikasi < %s", (two_months_ago,))
            conn.commit()


def scrape():
    # asyncio.get_event_loop().run_until_complete(kalibrr_scraper.scrape())
    filter_outdated_lowongan()
    asyncio.run(kalibrr_scraper.scrape())
    asyncio.run(jobstreet_scraper.scrape())