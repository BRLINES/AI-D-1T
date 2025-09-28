# predictor.py
import logging
import pandas as pd
import numpy as np
from tensorflow.keras.models import load_model
import joblib
from config import (MODEL_PATH, SCALER_X_PATH, SCALER_Y_PATH, 
                    SEQUENCE_LENGTH, PREDICTION_HORIZON, FEATURES, FRIENDLY_NAMES)
from data_collector import get_historical_data, get_sentiment_data
from feature_engine import create_lstm_features

def generate_reasoning(latest_data, trend):
    """
    Membangkitkan alasan singkat berdasarkan analisis indikator teknikal dan sentimen.
    Ini adalah lapisan interpretasi untuk memberikan konteks "mengapa".
    """
    reasons = []
    
    # 1. Analisis Momentum (RSI)
    rsi = latest_data.get('rsi_14', 50)
    if trend == "Naik":
        if rsi > 60:
            reasons.append("momentum bullish kuat (RSI > 60)")
        elif rsi > 50:
            reasons.append("momentum cenderung positif (RSI > 50)")
    elif trend == "Turun":
        if rsi < 40:
            reasons.append("momentum bearish kuat (RSI < 40)")
        elif rsi < 50:
            reasons.append("momentum cenderung negatif (RSI < 50)")

    # 2. Analisis Tren (EMA Cross)
    ema_10 = latest_data.get('ema_10', 0)
    ema_50 = latest_data.get('ema_50', 0)
    if ema_10 > ema_50:
        reasons.append("tren jangka pendek menguat (EMA Cross)")
    elif ema_10 < ema_50:
        reasons.append("tren jangka pendek melemah (EMA Cross)")

    # 3. Analisis Sentimen Pasar
    sentiment = latest_data.get('sentiment_value', 50)
    if sentiment > 65:
        reasons.append("sentimen pasar sangat optimis (Extreme Greed)")
    elif sentiment < 35:
        reasons.append("sentimen pasar pesimis (Fear)")
        
    if not reasons:
        return "Kondisi pasar campuran berdasarkan indikator utama."
        
    return "Didukung oleh " + ", ".join(reasons) + "."

def get_prediction(symbol):
    """
    Menghasilkan prediksi tren untuk satu simbol, kini dilengkapi dengan alasan.
    """
    logging.info(f"Memproses prediksi untuk {symbol}...")

    try:
        model = load_model(MODEL_PATH)
        scaler_x = joblib.load(SCALER_X_PATH)
        scaler_y = joblib.load(SCALER_Y_PATH)
    except Exception as e:
        logging.error(f"Gagal memuat model atau scaler: {e}")
        return None

    try:
        historical_data = get_historical_data(symbol, interval="1h", outputsize=500)
        if not isinstance(historical_data, pd.DataFrame) or historical_data.empty:
            logging.warning(f"Data historis untuk {symbol} tidak valid. Skip prediksi.")
            return None

        sentiment_data = get_sentiment_data()
        if not isinstance(sentiment_data, pd.DataFrame):
            sentiment_data = pd.DataFrame()

    except Exception as e:
        logging.error(f"Gagal mengambil data untuk {symbol}: {e}")
        return None

    # Buat fitur LSTM
    featured_data = create_lstm_features(historical_data, sentiment_data)
    
    # Ambil baris data terakhir untuk dianalisis alasannya
    latest_data_for_reasoning = featured_data.iloc[-1]
    
    last_sequence_data = featured_data.tail(SEQUENCE_LENGTH).copy()

    if len(last_sequence_data) < SEQUENCE_LENGTH:
        logging.warning(f"Tidak cukup data setelah pembuatan fitur untuk {symbol}.")
        return None

    # Scaling input
    available_features = [f for f in FEATURES if f in last_sequence_data.columns]
    X_input = last_sequence_data[available_features]
    X_scaled = scaler_x.transform(X_input)
    X_seq = np.array([X_scaled])

    # Prediksi
    predicted_scaled_price = model.predict(X_seq, verbose=0)[0][0]
    predicted_price = scaler_y.inverse_transform([[predicted_scaled_price]])[0][0]

    # Interpretasi hasil
    current_price = featured_data['close'].iloc[-1]
    price_change = predicted_price - current_price
    percent_change = (price_change / current_price) * 100

    trend = "Netral"
    if percent_change > 0.1:
        trend = "Naik"
    elif percent_change < -0.1:
        trend = "Turun"

    atr = featured_data['atr_14'].iloc[-1]
    if atr > 0:
        confidence = min(99.0, 50 + (abs(percent_change) / (atr / current_price * 100)) * 25)
    else:
        confidence = 50.0

    # Panggil fungsi untuk menghasilkan alasan
    reason = generate_reasoning(latest_data_for_reasoning, trend)

    result = {
        'symbol': symbol,
        'friendly_name': FRIENDLY_NAMES.get(symbol, symbol),
        'current_price': current_price,
        'predicted_price': predicted_price,
        'trend': trend,
        'confidence': round(confidence, 2),
        'atr': atr,
        'reason': reason  # <-- Alasan ditambahkan di sini
    }

    logging.info(f"Prediksi untuk {symbol}: Tren {trend} dengan confidence {result['confidence']}%")
    return result

