# notifier.py
import requests
import logging
from datetime import datetime
import pytz

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_notification(predictions, confidence_threshold, ai_name):
    """
    Mengirim notifikasi yang sudah diformat ke channel/grup Telegram,
    dengan layout baru yang lebih profesional dan ringkas.
    """
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "ISI_TOKEN_ANDA_DISINI":
        logging.error("Token Telegram belum diatur di config.py.")
        return

    # --- [PERUBAHAN] Mulai membangun pesan dengan format baru ---

    # 1. Header Pesan
    wib = pytz.timezone('Asia/Jakarta')
    now_wib = datetime.now(wib).strftime('%d-%m-%Y %H:%M WIB')
    
    header = (
        f"🔔 **PREDIKSI PASAR | {now_wib}**\n"
        f"_(Dianalisis oleh AI {ai_name} | Min Confidence: {int(confidence_threshold)}%)_\n\n"
    )

    # 2. Ringkasan Pasar (Market Summary)
    total_pairs = len(predictions)
    count_naik = sum(1 for p in predictions if p['trend'] == 'Naik')
    count_turun = sum(1 for p in predictions if p['trend'] == 'Turun')
    count_netral = sum(1 for p in predictions if p['trend'] == 'Netral')

    summary = (
        f"📊 **Ringkasan Pasar:**\n"
        f"{count_naik}/{total_pairs} Pair Naik 🟢 | {count_turun}/{total_pairs} Pair Turun 🔴 | Sideways {count_netral} ➡️\n"
    )

    separator = "─────────────────────────────\n"

    # 3. Detail untuk Setiap Prediksi
    details = []
    for p in predictions:
        # Tentukan emoji dan teks kekuatan sinyal
        trend_emoji = "📈" if p['trend'] == "Naik" else "📉" if p['trend'] == "Turun" else "➡️"
        color_emoji = "🟢" if p['trend'] == "Naik" else "🔴" if p['trend'] == "Turun" else ""
        strength = "Strong" if p['confidence'] >= 90 else "Medium" if p['confidence'] >= 80 else ""

        # Format harga dan ATR
        price_format = "{:,.4f}" if "USD" in p['friendly_name'] and "XAU" not in p['friendly_name'] else "{:,.2f}"
        atr_format = "{:,.4f}" if "JPY" not in p['friendly_name'] else "{:,.3f}"
        
        current_price_str = price_format.format(p['current_price'])
        atr_str = atr_format.format(p['atr'])
        
        # Hitung SL/TP dan Risk-Reward Ratio
        atr = p['atr']
        current_price = p['current_price']
        
        sl_val = 0
        tp_val = 0
        rr_ratio_str = "N/A"

        if p['trend'] == "Naik":
            sl_val = current_price - (1.5 * atr)
            tp_val = current_price + (2.0 * atr)
        elif p['trend'] == "Turun":
            sl_val = current_price + (1.5 * atr)
            tp_val = current_price - (2.0 * atr)
        
        if sl_val != 0 and tp_val != 0:
             # Hitung Risk to Reward
            risk = abs(current_price - sl_val)
            reward = abs(tp_val - current_price)
            if risk > 0:
                rr_ratio = reward / risk
                rr_ratio_str = f"1:{rr_ratio:.2f}"
            
            sl_str = price_format.format(sl_val)
            tp_str = price_format.format(tp_val)

        details.append(
            f"{trend_emoji} **{p['friendly_name']}** | {p['confidence']:.0f}% {color_emoji} {strength}\n"
            f"Harga: {current_price_str} | ATR: {atr_str}\n"
            f"SL/TP: {sl_str} / {tp_str} | R:R {rr_ratio_str}\n"
            f"Alasan: _{p.get('reason', 'Analisis teknikal.')}_\n"
        )
    
    # 4. Footer Pesan
    footer = (
        f"⚠️ **Disclaimer:**\n"
        f"Analisis ini dihasilkan oleh AI D-1T dan bukan saran finansial.\n"
        f"DYOR & kelola risiko dengan bijak.\n"
        f"Data terakhir diperbarui: {now_wib}"
    )

    # 5. Gabungkan semua bagian menjadi satu pesan
    message = header + summary + separator + "\n".join(details) + separator + footer
    
    # Kirim pesan
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, data=params)
        response.raise_for_status()
        logging.info("Pesan berhasil dikirim ke Telegram.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Gagal mengirim pesan ke Telegram: {e}")
        logging.error(f"Response dari Telegram: {e.response.text if e.response else 'No response'}")

