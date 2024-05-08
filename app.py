from flask import Flask, render_template, request
from apscheduler.schedulers.background import BackgroundScheduler
from scraper import main_scraper
import requests

app = Flask(__name__)

scheduler = BackgroundScheduler()
scheduler.add_job(main_scraper.scrape, 'cron', hour=1)

@app.before_first_request
def start_scheduler():
    scheduler.start()


@app.teardown_appcontext
def stop_scheduler(exception=None):
    scheduler.shutdown()

@app.route('/')
def index():
    return 'halo'
