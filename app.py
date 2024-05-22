from flask import Flask, jsonify, render_template, request
from apscheduler.schedulers.background import BackgroundScheduler
from scraper import main_scraper
import requests, pytz

app = Flask(__name__)
scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Jakarta'))

@app.route('/')
def index():
    response = requests.get('http://localhost:5001/api')
    
    if response.status_code == 200:
        data = response.json()
        return render_template('page.html', data=data)
    else:
        return jsonify({'message': 'Failed to fetch data from API'}), 500

if __name__ == '__main__':
    app.run()
    scheduler.add_job(main_scraper.scrape, 'cron', hour=1)
    scheduler.start()
