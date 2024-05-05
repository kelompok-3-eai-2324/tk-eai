import jobstreet_scraper, kalibrr_scraper, karir_scraper, linkedin_scraper
import asyncio

def main():
    asyncio.run(kalibrr_scraper.scrape())

if __name__ == '__main__':
    exit(main())