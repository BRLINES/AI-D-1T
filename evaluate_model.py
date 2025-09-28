# evaluate_model.py
import pandas as pd
import logging
from config import HISTORY_FILE

def evaluate_performance():
    """
    Menganalisis file histori prediksi untuk menghitung metrik performa.
    Fungsi ini perlu dijalankan setelah hasil aktual diisi.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        df = pd.read_csv(HISTORY_FILE)
    except FileNotFoundError:
        logging.error(f"File histori '{HISTORY_FILE}' tidak ditemukan.")
        return

    # Filter hanya baris yang sudah punya hasil aktual
    df.dropna(subset=['actual_close'], inplace=True)

    if df.empty:
        logging.info("Tidak ada data prediksi dengan hasil aktual untuk dievaluasi.")
        return

    # Tentukan apakah prediksi benar
    conditions = [
        (df['trend_prediction'] == 'Naik') & (df['actual_close'] > df['last_price']),
        (df['trend_prediction'] == 'Turun') & (df['actual_close'] < df['last_price'])
    ]
    df['is_correct'] = pd.np.select(conditions, [True, True], default=False)

    accuracy = (df['is_correct'].sum() / len(df)) * 100
    
    logging.info("--- Laporan Performa Model ---")
    logging.info(f"Total Prediksi Dievaluasi: {len(df)}")
    logging.info(f"Akurasi Arah (Directional Accuracy): {accuracy:.2f}%")

    for symbol in df['symbol'].unique():
        symbol_df = df[df['symbol'] == symbol]
        symbol_accuracy = (symbol_df['is_correct'].sum() / len(symbol_df)) * 100
        logging.info(f"  - Akurasi untuk {symbol}: {symbol_accuracy:.2f}% ({len(symbol_df)} prediksi)")
        
if __name__ == "__main__":
    evaluate_performance()
