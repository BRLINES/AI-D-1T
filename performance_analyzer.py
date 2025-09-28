# performance_analyzer.py
import pandas as pd
import os
import logging
from datetime import datetime # <-- [PERBAIKAN] Menambahkan import yang hilang

from config import (HISTORY_FILE, ACCURACY_LOOKBACK, PERFORMANCE_THRESHOLD, 
                    CONFIDENCE_THRESHOLD, MIN_CONFIDENCE, MAX_CONFIDENCE, PREDICTION_HORIZON)
from data_collector import get_historical_data

def analyze_performance():
    """
    Menganalisis histori prediksi, menghitung akurasi, dan menyesuaikan
    confidence threshold secara dinamis.
    """
    if not os.path.exists(HISTORY_FILE):
        logging.info("File histori tidak ditemukan. Menggunakan confidence threshold default.")
        return CONFIDENCE_THRESHOLD

    try:
        history_df = pd.read_csv(HISTORY_FILE)
        if len(history_df) < 10: # Butuh minimal 10 data untuk analisis
            logging.info("Data histori tidak cukup untuk analisis. Menggunakan threshold default.")
            return CONFIDENCE_THRESHOLD

        # Ambil N prediksi terakhir yang belum dievaluasi
        untested_preds = history_df[history_df['actual_trend'].isna()].tail(ACCURACY_LOOKBACK)
        if untested_preds.empty:
            logging.info("Tidak ada prediksi baru untuk dievaluasi.")
            # Ambil threshold terakhir yang digunakan jika ada
            if 'adjusted_threshold' in history_df.columns:
                 last_threshold = history_df.dropna(subset=['adjusted_threshold'])['adjusted_threshold'].iloc[-1]
                 if last_threshold:
                     return last_threshold
            return CONFIDENCE_THRESHOLD

        # Evaluasi prediksi
        for index, row in untested_preds.iterrows():
            try:
                # Ambil data harga riil setelah prediksi dibuat
                real_data = get_historical_data(row['symbol'], interval="1h", outputsize=100) # Cukup ambil 100 bar terakhir
                
                if real_data.empty:
                    continue

                pred_timestamp = pd.to_datetime(row['timestamp'])
                target_timestamp = pred_timestamp + pd.Timedelta(hours=row['horizon'])
                
                # Cari baris data yang paling dekat dengan target waktu kita
                time_diffs = (real_data.index - target_timestamp).total_seconds().abs()
                closest_index = time_diffs.idxmin()
                real_price_at_horizon = real_data.loc[closest_index]['close']

                price_change = real_price_at_horizon - row['current_price']
                percent_change = (price_change / row['current_price']) * 100
                
                actual_trend = "Netral"
                if percent_change > 0.1: actual_trend = "Naik"
                elif percent_change < -0.1: actual_trend = "Turun"

                # Update histori
                history_df.loc[index, 'actual_price'] = real_price_at_horizon
                history_df.loc[index, 'actual_trend'] = actual_trend
                history_df.loc[index, 'is_correct'] = (row['predicted_trend'] == actual_trend)
            
            except Exception as e:
                logging.warning(f"Gagal mengevaluasi prediksi lama untuk {row['symbol']}: {e}")
                continue
        
        # Hitung akurasi dari N prediksi terakhir yang sudah dievaluasi
        evaluated_preds = history_df.dropna(subset=['is_correct']).tail(ACCURACY_LOOKBACK)
        new_threshold = CONFIDENCE_THRESHOLD # Default

        if len(evaluated_preds) > 10:
            accuracy = evaluated_preds['is_correct'].mean()
            logging.info(f"Akurasi historis ({len(evaluated_preds)} data terakhir): {accuracy:.2%}")
            
            if accuracy < PERFORMANCE_THRESHOLD:
                new_threshold = min(MAX_CONFIDENCE, CONFIDENCE_THRESHOLD + 5)
                logging.warning(f"Akurasi rendah. Menaikkan confidence threshold ke {new_threshold}%")
            else:
                new_threshold = max(MIN_CONFIDENCE, CONFIDENCE_THRESHOLD - 2)
                logging.info(f"Akurasi baik. Menyesuaikan confidence threshold ke {new_threshold}%")
        
        history_df['adjusted_threshold'] = new_threshold
        history_df.to_csv(HISTORY_FILE, index=False)
        return new_threshold

    except Exception as e:
        logging.error(f"Error saat menganalisis performa: {e}")
    
    return CONFIDENCE_THRESHOLD

def update_history(predictions):
    """Menyimpan prediksi baru ke file CSV."""
    if not predictions:
        return

    new_records = []
    for p in predictions:
        new_records.append({
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'symbol': p['symbol'],
            'current_price': p['current_price'],
            'predicted_price': p['predicted_price'],
            'predicted_trend': p['trend'],
            'confidence': p['confidence'],
            'horizon': PREDICTION_HORIZON,
            'actual_price': None,
            'actual_trend': None,
            'is_correct': None,
            'adjusted_threshold': None, # Kolom baru untuk menyimpan threshold saat itu
        })
    
    new_df = pd.DataFrame(new_records)
    
    if os.path.exists(HISTORY_FILE):
        new_df.to_csv(HISTORY_FILE, mode='a', header=False, index=False)
    else:
        new_df.to_csv(HISTORY_FILE, index=False)
    
    logging.info(f"Histori prediksi berhasil diperbarui dengan {len(new_records)} data baru.")

