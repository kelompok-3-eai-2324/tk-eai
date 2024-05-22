from datetime import datetime, timedelta
from dotenv import load_dotenv
import os, psycopg2, pytz

load_dotenv()

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')

def insert_to_db(data):
    with psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
        ) as conn:

        with conn.cursor() as cur:
            cur.execute("""
                        SELECT tanggal_publikasi, jenis_pekerjaan FROM lowongan_table WHERE perusahaan = %s AND judul_lowongan = %s;
                        """, (data["perusahaan"], data["judul_lowongan"]))
            existing_row = cur.fetchone()

            if existing_row:
                existing_tanggal_publikasi = existing_row[0]
                existing_jenis_pekerjaan = existing_row[1]
                if data["jenis_pekerjaan"] in existing_jenis_pekerjaan:
                    data["jenis_pekerjaan"] = existing_jenis_pekerjaan
                else:
                    data["jenis_pekerjaan"] = existing_jenis_pekerjaan + "," + data["jenis_pekerjaan"]

                if existing_tanggal_publikasi.replace(tzinfo=pytz.timezone('Asia/Jakarta')) < data["tanggal_publikasi"]:
                    cur.execute("""
                                UPDATE lowongan_table
                                SET judul_lowongan = %s, 
                                    tanggal_publikasi = %s, 
                                    lokasi_pekerjaan = %s, 
                                    perusahaan = %s, 
                                    sumber_situs = %s, 
                                    link_lowongan = %s, 
                                    jenis_pekerjaan = %s
                                WHERE perusahaan = %s AND judul_lowongan = %s;
                                """, (data["judul_lowongan"], 
                                    data["tanggal_publikasi"], 
                                    data["lokasi_pekerjaan"], 
                                    data["perusahaan"], 
                                    data["sumber_situs"], 
                                    data["link_lowongan"], 
                                    data["jenis_pekerjaan"], 
                                    data["perusahaan"], 
                                    data["judul_lowongan"]))
                else:
                    cur.execute("""
                                UPDATE lowongan_table
                                SET jenis_pekerjaan = %s
                                WHERE perusahaan = %s AND judul_lowongan = %s;
                                """, (
                                    data["jenis_pekerjaan"], 
                                    data["perusahaan"], 
                                    data["judul_lowongan"]))

            else:
                cur.execute("""
                            INSERT INTO lowongan_table (
                                    judul_lowongan, 
                                    tanggal_publikasi, 
                                    lokasi_pekerjaan, 
                                    perusahaan, 
                                    sumber_situs, 
                                    link_lowongan, 
                                    jenis_pekerjaan)
                            VALUES (%s, %s, %s, %s, %s, %s, %s);
                            """, (data["judul_lowongan"], 
                                  data["tanggal_publikasi"], 
                                  data["lokasi_pekerjaan"], 
                                  data["perusahaan"],
                                  data["sumber_situs"],
                                  data["link_lowongan"],
                                  data["jenis_pekerjaan"]))

        conn.commit()


def filter_outdated_lowongan():
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

def get_all_lowongan():
    with psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
        ) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM lowongan_table")
            rows = cur.fetchall()   
            return rows
        
def get_lowongan_by(
        offset=None,
        jenis_pekerjaan=None,
        dari_tanggal=None,
        sampai_tanggal=None,
        lokasi=None,
        perusahaan=None
        ):
    
    if not any([offset, jenis_pekerjaan, dari_tanggal, sampai_tanggal, lokasi, perusahaan]):
        return get_all_lowongan()
    
    query = "SELECT * FROM lowongan_table "

    if any([jenis_pekerjaan, dari_tanggal, sampai_tanggal, lokasi, perusahaan]):
        query += "WHERE "

    if jenis_pekerjaan:
        query += f"jenis_pekerjaan LIKE '%{jenis_pekerjaan}%' AND "
    if dari_tanggal:
        query += f"tanggal_publikasi::date >='{dari_tanggal}' AND "
    if sampai_tanggal:
        query += f"tanggal_publikasi::date <='{sampai_tanggal}' AND "
    if lokasi:
        query += f"lokasi ILIKE '%{lokasi}%' AND "
    if perusahaan:
        query += f"perusahaan ILIKE '%{perusahaan}%' "

    query = query.rstrip("AND")

    if offset:
        query += f"LIMIT 30 OFFSET {offset}"

    query += ";"

    with psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
        ) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()   
            return rows