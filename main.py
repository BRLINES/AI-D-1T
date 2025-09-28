# main.py
import logging
import os
from datetime import datetime

# Impor dari modul-modul lain dalam proyek
from config import SYMBOLS, LOGS_DIR, AI_NAME
from predictor import get_prediction
from notifier import send_telegram_notification
from performance_analyzer import analyze_performance, update_history

# Konfigurasi logging
os.makedirs(LOGS_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "main.log")),
        logging.StreamHandler()
    ]
)

def main():
    """Fungsi utama untuk menjalankan siklus prediksi."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"===== Memulai Siklus Prediksi pada {timestamp} =====")

    # 1. Analisis performa dari histori dan dapatkan threshold adaptif
    current_confidence_threshold = analyze_performance()

    all_predictions = []
    # 2. Dapatkan prediksi untuk setiap simbol
    for symbol in SYMBOLS:
        try:
            prediction_result = get_prediction(symbol)
            if prediction_result:
                all_predictions.append(prediction_result)
        except Exception as e:
            logging.error(f"Gagal total mendapatkan prediksi untuk {symbol}: {e}", exc_info=True)

    # 3. Filter prediksi berdasarkan confidence threshold yang sudah disesuaikan
    high_confidence_predictions = [
        p for p in all_predictions if p and p['confidence'] >= current_confidence_threshold
    ]

    # 4. Kirim notifikasi jika ada sinyal dengan confidence tinggi
    if high_confidence_predictions:
        try:
            send_telegram_notification(high_confidence_predictions, current_confidence_threshold, AI_NAME)
            logging.info(f"Notifikasi berhasil dikirim untuk {len(high_confidence_predictions)} sinyal.")
        except Exception as e:
            logging.error(f"Gagal mengirim notifikasi Telegram: {e}")
    else:
        logging.info("Tidak ada sinyal dengan confidence tinggi untuk dilaporkan saat ini.")

    # 5. Perbarui file histori dengan semua prediksi (baik yang dikirim maupun tidak)
    if all_predictions:
        update_history(all_predictions)

    logging.info("===== Siklus Prediksi Selesai =====")

if __name__ == "__main__":
    main()

