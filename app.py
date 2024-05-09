from flask import Flask, render_template, request
from apscheduler.schedulers.background import BackgroundScheduler
from scraper import main_scraper
import requests, pytz

app = Flask(__name__)
scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Jakarta'))

@app.route('/')
def index():
    return 'halo'

if __name__ == '__main__':
    scheduler.add_job(main_scraper.scrape, 'cron', hour=1)
    scheduler.start()
    app.run()
