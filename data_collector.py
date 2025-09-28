# data_collector.py
import requests
import pandas as pd
import logging
import time
from config import TWELVE_DATA_API_KEY, FEAR_GREED_API_URL

def get_historical_data(symbol, interval='1h', outputsize=500):
    """
    Mengambil data harga historis dari Twelve Data API.
    Fungsi ini sekarang menambahkan kolom 'volume' default untuk stabilitas.
    """
    api_url = f"https://api.twelvedata.com/time_series"
    params = {
        "symbol": symbol,
        "interval": interval,
        "apikey": TWELVE_DATA_API_KEY,
        "outputsize": outputsize,
        "timezone": "UTC"
    }
    for attempt in range(1, 4):
        try:
            response = requests.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get('status') != 'ok' or 'values' not in data:
                raise ValueError(f"API response tidak valid: {data.get('message', 'No message')}")

            df = pd.DataFrame(data['values'])
            
            # --- [PERBAIKAN] Penanganan Volume untuk Forex ---
            # Twelve Data tidak menyediakan volume untuk FX spot, jadi kita buat kolom default.
            # Ini memastikan konsistensi fitur dengan model yang sudah dilatih.
            if 'volume' not in df.columns:
                df['volume'] = 0.0
            # --- AKHIR PERBAIKAN ---

            # Ganti nama dan atur tipe data
            df.rename(columns={'datetime': 'timestamp'}, inplace=True)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col])

            df = df.iloc[::-1] # API mengembalikan data dari terbaru ke terlama, kita balik urutannya
            
            logging.info(f"Berhasil mengambil {len(df)} baris data untuk {symbol} dari Twelve Data.")
            return df

        except Exception as e:
            logging.warning(f"Gagal mengambil data untuk {symbol} (percobaan {attempt}/3): {e}")
            if attempt < 3:
                time.sleep(5)
            else:
                logging.error(f"Gagal total mengambil data untuk {symbol} setelah 3 percobaan.")
                return pd.DataFrame()

def get_sentiment_data():
    """Mengambil data Fear & Greed Index."""
    try:
        response = requests.get(FEAR_GREED_API_URL)
        response.raise_for_status()
        data = response.json().get('data', [])
        df = pd.DataFrame(data)
        if df.empty:
            raise ValueError("Data sentimen kosong.")
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s').dt.date
        df.set_index('timestamp', inplace=True)
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df = df[['value']].dropna()
        logging.info(f"Berhasil mengambil {len(df)} data sentimen historis.")
        return df
    except Exception as e:
        logging.error(f"Gagal mengambil data sentimen: {e}")
        return pd.DataFrame()

