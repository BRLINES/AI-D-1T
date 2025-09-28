# train_model.py
import os
import logging
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
# --- [PERBAIKAN SARAN ANDA] ---
# Impor 'Input' untuk menghilangkan UserWarning
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input 
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import joblib
# --- AKHIR PERBAIKAN ---

from config import (SYMBOLS, MODEL_PATH, SCALER_X_PATH, SCALER_Y_PATH, LOGS_DIR, 
                    SEQUENCE_LENGTH, PREDICTION_HORIZON, FEATURES)
from data_collector import get_historical_data, get_sentiment_data
from feature_engine import create_lstm_features, prepare_sequences

# Konfigurasi logging... (tetap sama)
os.makedirs(LOGS_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "training.log")),
        logging.StreamHandler()
    ]
)

def train_lstm_model():
    logging.info("Memulai proses training model LSTM...")
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

    try:
        sentiment_data = get_sentiment_data()
        if sentiment_data.empty: sentiment_data = None
    except Exception:
        sentiment_data = None

    all_features = []
    for symbol in SYMBOLS:
        logging.info(f"Memproses {symbol}...")
        data = get_historical_data(symbol)
        if data.empty or len(data) < PREDICTION_HORIZON + SEQUENCE_LENGTH:
            logging.warning(f"Data untuk {symbol} tidak cukup. Dilewati.")
            continue
        
        featured = create_lstm_features(data, sentiment_data)
        featured.dropna(subset=['future_price'], inplace=True)
        if not featured.empty:
            all_features.append(featured)

    if not all_features:
        logging.error("Tidak ada data valid untuk dilatih. Proses dihentikan.")
        return

    df_all = pd.concat(all_features, ignore_index=True)
    
    # --- [PERBAIKAN SARAN ANDA] ---
    # Menggunakan bfill().ffill() untuk membersihkan sisa NaN
    df_all.bfill(inplace=True)
    df_all.ffill(inplace=True)
    # --- AKHIR PERBAIKAN ---

    available_features = [f for f in FEATURES if f in df_all.columns]
    X_data = df_all[available_features]
    y_data = df_all[['future_price']]

    scaler_x = MinMaxScaler()
    X_scaled = scaler_x.fit_transform(X_data)
    
    scaler_y = MinMaxScaler()
    y_scaled = scaler_y.fit_transform(y_data)

    X_seq, y_seq = prepare_sequences(X_scaled, y_scaled, SEQUENCE_LENGTH)

    if len(X_seq) == 0:
        logging.error("Data tidak cukup untuk membuat sekuens LSTM.")
        return

    # --- [PERBAIKAN SARAN ANDA] ---
    # Menggunakan Input layer untuk menghilangkan UserWarning
    model = Sequential([
        Input(shape=(X_seq.shape[1], X_seq.shape[2])),
        LSTM(100, return_sequences=True),
        Dropout(0.2),
        LSTM(50, return_sequences=False),
        Dropout(0.2),
        Dense(25),
        Dense(1)
    ])
    # --- AKHIR PERBAIKAN ---

    model.compile(optimizer='adam', loss='mean_squared_error')
    model.summary()

    early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
    model_checkpoint = ModelCheckpoint(MODEL_PATH, save_best_only=True, monitor='val_loss')
    
    model.fit(X_seq, y_seq, epochs=50, batch_size=32, validation_split=0.1, callbacks=[early_stopping, model_checkpoint], verbose=1)

    joblib.dump(scaler_x, SCALER_X_PATH)
    joblib.dump(scaler_y, SCALER_Y_PATH)
    logging.info(f"Training selesai. Model disimpan di {MODEL_PATH} dan scaler telah disimpan.")

if __name__ == "__main__":
    train_lstm_model()

