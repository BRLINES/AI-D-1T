# config.py

# -- Konfigurasi API --
TWELVE_DATA_API_KEY = "MASUKKAN_API_KEY_ANDA_DISINI"
FEAR_GREED_API_URL = 'https://api.alternative.me/fng/?limit=90'

# -- Konfigurasi Aset & Simbol --
# Gunakan simbol yang dikenali oleh Twelve Data
SYMBOLS = [
    "XAU/USD",
    "EUR/USD",
    "USD/JPY",
    "GBP/USD",
    "GBP/JPY",
    "AUD/USD",
    "USD/CHF",
]

# Nama yang mudah dibaca untuk notifikasi Telegram
FRIENDLY_NAMES = {
    "XAU/USD": "Emas (XAU/USD)",
    "EUR/USD": "EUR/USD",
    "USD/JPY": "USD/JPY",
    "GBP/USD": "GBP/USD",
    "GBP/JPY": "GBP/JPY",
    "AUD/USD": "AUD/USD",
    "USD/CHF": "USD/CHF",
}

# -- Konfigurasi Model AI (LSTM) --
# Daftar fitur yang akan digunakan untuk training.
# NAMA HARUS SESUAI DENGAN OUTPUT DARI feature_engine.py (SEMUA HURUF KECIL).
FEATURES = [
    'open', 'high', 'low', 'close', 'volume', 
    'ema_10', 'ema_50', 'sma_20', 'rsi_14', 
    'macd_12_26_9', 'macdh_12_26_9', 'macds_12_26_9',
    'atr_14', 
    # --- [PERBAIKAN] Nama kolom Bollinger Bands disesuaikan ---
    'bbl_20_2.0',
    'bbm_20_2.0',
    'bbu_20_2.0',
    # ----------------------------------------------------
    'sentiment_value'
]
SEQUENCE_LENGTH = 24
PREDICTION_HORIZON = 4

# -- Konfigurasi Path File --
MODELS_DIR = "models"
LOGS_DIR = "logs"
MODEL_PATH = f"{MODELS_DIR}/lstm_forex_model.keras"
SCALER_X_PATH = f"{MODELS_DIR}/scaler_x.pkl"
SCALER_Y_PATH = f"{MODELS_DIR}/scaler_y.pkl"
# Lingkungan serverless Vercel hanya bisa menulis ke direktori /tmp
HISTORY_FILE = "/tmp/prediction_history.csv"

# -- Konfigurasi API Sentimen --
FEAR_GREED_API_URL = 'https://api.alternative.me/fng/?limit=90'

# -- Konfigurasi Notifikasi Telegram --
TELEGRAM_BOT_TOKEN = "ISI_TOKEN_ANDA_DISINI"
TELEGRAM_CHAT_ID = "ISI_CHAT_ID_ANDA_DISINI"
AI_NAME = "D-1T"

# -- Konfigurasi Logika Adaptif & Manajemen Risiko --
CONFIDENCE_THRESHOLD = 75.0
MIN_CONFIDENCE = 60.0
MAX_CONFIDENCE = 90.0
ACCURACY_LOOKBACK = 50
PERFORMANCE_THRESHOLD = 0.5


