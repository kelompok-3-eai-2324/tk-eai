from flask import Flask, request
from utils.db import get_lowongan_by

app = Flask(__name__)

@app.get('/api')
def api():
    # Retrieve query parameters
    offset = request.args.get("offset")
    jenis_pekerjaan = request.args.get('jenis_pekerjaan')
    dari_tanggal = request.args.get('dari_tanggal')
    sampai_tanggal = request.args.get('sampai_tanggal')
    lokasi = request.args.get('lokasi')
    perusahaan = request.args.get('perusahaan')

    res = []
    for row in get_lowongan_by(offset, jenis_pekerjaan, dari_tanggal, sampai_tanggal, lokasi, perusahaan):
        res.append(dict(
            judul_lowongan=row[0],
            tanggal_publikasi=row[1],
            lokasi_pekerjaan=row[2],
            perusahaan=row[3],
            sumber_situs=row[4],
            link_lowongan=row[5],
            jenis_pekerjaan=row[6]
            ))
    return res

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)