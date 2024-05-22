from flask import Flask, jsonify, render_template, request
from apscheduler.schedulers.background import BackgroundScheduler
from scraper import main_scraper
import requests, pytz

app = Flask(__name__)
scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Jakarta'))

@app.route('/')
def index():
    resp = requests.get('http://localhost:5001/api', params={"offset": 0})
    params=dict(
        offset=0,
        jenis_pekerjaan='',
        dari_tanggal='',
        sampai_tanggal='',
        lokasi='',
        perusahaan=''
    )
    return render_template('page.html', jobs=resp.json(), params=params, scroll=0)

@app.route('/filter')
def search():
    jenis_pekerjaan = request.args.get('jenis_pekerjaan')
    dari_tanggal = request.args.get('dari_tanggal')
    sampai_tanggal = request.args.get('sampai_tanggal')
    lokasi = request.args.get('lokasi')
    perusahaan = request.args.get('perusahaan')

    params=dict(
        offset=0,
        jenis_pekerjaan=jenis_pekerjaan,
        dari_tanggal=dari_tanggal,
        sampai_tanggal=sampai_tanggal,
        lokasi=lokasi,
        perusahaan=perusahaan
    )

    resp = requests.get('http://localhost:5001/api', params=params)
    return render_template('page.html', jobs=resp.json(), params=params, scroll=1)

@app.route('/more_jobs')
def more_jobs():
    jenis_pekerjaan = request.args.get('jenis_pekerjaan')
    dari_tanggal = request.args.get('dari_tanggal')
    sampai_tanggal = request.args.get('sampai_tanggal')
    lokasi = request.args.get('lokasi')
    perusahaan = request.args.get('perusahaan')
    offset = int(request.args.get('offset', 0))

    params=dict(
        offset=offset,
        jenis_pekerjaan=jenis_pekerjaan,
        dari_tanggal=dari_tanggal,
        sampai_tanggal=sampai_tanggal,
        lokasi=lokasi,
        perusahaan=perusahaan
    )

    additional_jobs =requests.get('http://localhost:5001/api', params=params)
    return jsonify(additional_jobs.json())

if __name__ == '__main__':
    scheduler.add_job(main_scraper.scrape, 'cron', hour=1)
    scheduler.start()
    app.run(debug=True, port=5002, host='0.0.0.0')
