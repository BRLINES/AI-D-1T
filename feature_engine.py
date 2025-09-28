# feature_engine.py
import pandas as pd
import pandas_ta as ta
import numpy as np
import logging
from config import PREDICTION_HORIZON, FEATURES

def create_lstm_features(historical_data, sentiment_data):
    """
    Menciptakan fitur teknikal dan sentimen untuk model LSTM.
    Fungsi ini dirancang agar kuat (robust) dengan menangani nama kolom yang tidak konsisten,
    nilai NaN, dan memastikan struktur data output selalu sesuai dengan yang diharapkan model.
    """
    if not isinstance(historical_data, pd.DataFrame) or historical_data.empty:
        logging.warning("Menerima data historis kosong atau tidak valid. Melewati pembuatan fitur.")
        return pd.DataFrame()

    df = historical_data.copy()

    # --- TAHAP 1: Standardisasi & Penggabungan Data ---

    # Standarkan nama kolom input ke huruf kecil untuk konsistensi universal.
    df.columns = [col.lower() for col in df.columns]

    # Gabungkan data sentimen dengan aman.
    if sentiment_data is not None and not sentiment_data.empty:
        if 'value' in sentiment_data.columns:
            df.index = pd.to_datetime(df.index)
            sentiment_data.index = pd.to_datetime(sentiment_data.index)
            df = pd.merge(df, sentiment_data[['value']], left_index=True, right_index=True, how='left')
            df.rename(columns={'value': 'sentiment_value'}, inplace=True)
    
    if 'sentiment_value' not in df.columns:
        df['sentiment_value'] = 50.0  # Nilai netral

    # --- TAHAP 2: Perhitungan Indikator Teknikal ---
    
    df.ta.ema(length=10, append=True)
    df.ta.ema(length=50, append=True)
    df.ta.sma(length=20, append=True)
    df.ta.rsi(length=14, append=True)
    df.ta.macd(fast=12, slow=26, signal=9, append=True)
    df.ta.atr(length=14, append=True)
    df.ta.bbands(length=20, std=2.0, append=True)

    # --- TAHAP 3: Pembuatan Target & Pembersihan Akhir ---

    # Buat target harga di masa depan.
    if 'close' in df.columns:
        df['future_price'] = df['close'].shift(-PREDICTION_HORIZON)
    else:
        logging.error("Kolom 'close' tidak ditemukan. Tidak dapat membuat target.")
        return pd.DataFrame() 

    # Standarkan SEMUA nama kolom (termasuk yang baru dibuat) ke huruf kecil.
    df.columns = [col.lower() for col in df.columns]
    
    # Perbaiki nama kolom ATR yang tidak konsisten ('atrr_14' -> 'atr_14').
    if 'atrr_14' in df.columns:
        df.rename(columns={'atrr_14': 'atr_14'}, inplace=True)
        
    # --- [PERBAIKAN] Penanganan Nama Kolom Bollinger Bands yang Dinamis ---
    # Logika ini secara otomatis mencari dan menstandarkan nama kolom Bollinger Bands.
    for col in df.columns:
        if col.startswith('bbl'):
            df.rename(columns={col: 'bbl_20_2.0'}, inplace=True)
        elif col.startswith('bbm'):
            df.rename(columns={col: 'bbm_20_2.0'}, inplace=True)
        elif col.startswith('bbu'):
            df.rename(columns={col: 'bbu_20_2.0'}, inplace=True)
    # --- AKHIR PERBAIKAN ---

    # Tangani nilai NaN yang muncul di awal data akibat perhitungan indikator.
    df = df.bfill().ffill()

    # --- TAHAP 4: Finalisasi Struktur DataFrame ---

    # Pastikan urutan kolom selalu konsisten sesuai dengan daftar di config.py.
    available_features = [f for f in FEATURES if f in df.columns]
    
    if len(available_features) != len(FEATURES):
        missing = set(FEATURES) - set(available_features)
        logging.warning(f"Fitur berikut hilang setelah diproses: {missing}. Periksa daftar FITUR di config.")
    
    final_cols = available_features + ['future_price']
    if all(col in df.columns for col in final_cols):
        df.dropna(inplace=True)
        return df[final_cols]
    else:
        logging.error("Gagal membuat DataFrame final karena kolom penting hilang.")
        return pd.DataFrame()


def prepare_sequences(features, targets, sequence_length):
    """Mengubah data tabular menjadi sekuens untuk input LSTM."""
    X, y = [], []
    if len(features) < sequence_length:
        logging.warning("Data tidak cukup panjang untuk membuat sekuens.")
        return np.array(X), np.array(y)
        
    for i in range(len(features) - sequence_length):
        X.append(features[i:(i + sequence_length)])
        y.append(targets[i + sequence_length - 1])
    
    return np.array(X), np.array(y)

