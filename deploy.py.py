# deploy.py
# Skrip ini berfungsi sebagai pembungkus (wrapper) untuk menjalankan siklus prediksi
# secara terus-menerus dengan jeda waktu, cocok untuk platform seperti Railway.

import time
import logging
import os
import main
from config import DEPLOY_SLEEP_SECONDS, LOGS_DIR

# Konfigurasi logging khusus untuk skrip deployment
os.makedirs(LOGS_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "deploy.log")),
        logging.StreamHandler()
    ]
)

if __name__ == "__main__":
    """
    Loop utama yang akan berjalan selamanya di server.
    """
    logging.info(f"Memulai skrip deployment... Siklus akan berjalan setiap {DEPLOY_SLEEP_SECONDS} detik.")
    
    while True:
        try:
            # Panggil fungsi utama dari main.py untuk menjalankan satu siklus prediksi
            main.main()
        except Exception as e:
            # Jika terjadi error di siklus utama, catat error tersebut
            # dan loop akan tetap berlanjut agar layanan tidak mati.
            logging.error(f"Terjadi error pada siklus utama: {e}", exc_info=True)
        
        logging.info(f"Siklus selesai. Skrip akan tidur selama {DEPLOY_SLEEP_SECONDS} detik sebelum berjalan lagi.")
        time.sleep(DEPLOY_SLEEP_SECONDS)
