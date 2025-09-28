# api/run_prediction.py
# File ini berfungsi sebagai entry point untuk Vercel Cron Job.
# Vercel akan menjalankan file ini sesuai jadwal yang ditentukan di vercel.json.

import sys
import os
import logging

# Tambahkan direktori root proyek ke path agar bisa mengimpor modul lain
# seperti 'main', 'config', dll.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import main
from config import LOGS_DIR

# Konfigurasi logging dasar untuk file ini
os.makedirs(LOGS_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - VERCEL CRON - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler() # Output akan langsung terlihat di log Vercel
    ]
)

def handler(request, response):
    """
    Fungsi handler yang dipanggil oleh Vercel.
    Untuk Cron Job, kita hanya perlu menjalankan logika utama kita di sini.
    """
    try:
        logging.info("Memulai eksekusi Vercel Cron Job...")
        # Panggil fungsi utama dari main.py untuk menjalankan satu siklus prediksi
        main.main()
        logging.info("Eksekusi Vercel Cron Job selesai dengan sukses.")
        
        # Kirim respons sukses
        response.status_code = 200
        response.send("Siklus prediksi berhasil dijalankan.")

    except Exception as e:
        logging.error(f"Terjadi error pada Vercel Cron Job: {e}", exc_info=True)
        # Kirim respons error
        response.status_code = 500
        response.send(f"Terjadi error: {e}")

# Baris ini memungkinkan kita untuk menjalankan skrip secara lokal untuk testing
# dengan perintah `python api/run_prediction.py`
if __name__ == "__main__":
    # Simulasi objek request dan response untuk testing lokal
    class MockResponse:
        def __init__(self):
            self.status_code = 200
        def send(self, body):
            print(f"Response Body: {body}")
            print(f"Status Code: {self.status_code}")

    handler(None, MockResponse())
