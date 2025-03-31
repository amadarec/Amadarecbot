from flask import Flask, request
import requests
import threading
import time

app = Flask(__name__)

# Telegram setup 
TELEGRAM_TOKEN = "7772895600:AAH7OY0PODCGQVPnOCw3JB00WjZ3JAp9oMs"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Tracked coins (CoinGecko IDs)
SUPPORTED_COINS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "WLD": "worldcoin-wld",
    "BNB": "binancecoin",
    "SOL": "solana",
    "XRP": "ripple",
    "HBAR": "hedera-hashgraph"
}

# Alert storage: {user_id: {COIN: [ {type, price} ]}}
user_alerts = {}

def send_message(chat_id, text):
    requests.post(
        f"{TELEGRAM_API_URL}/sendMessage",
        json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    )

# Fetch live price from CoinGecko
def get_price(symbol):
    if symbol not in SUPPORTED_COINS:
        return None
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={SUPPORTED_COINS[symbol]}&vs_currencies=usd"
    response = requests.get(url).json()
    return response[SUPPORTED_COINS[symbol]]["usd"]

# Background price checker
def check_alerts_loop():
    while True:
        for user_id, alerts in user_alerts.items():
            for coin, conditions in alerts.items():
                price = get_price(coin)
                for condition in conditions:
                    target = condition["price"]
                    if (
                        condition["type"] == ">" and price > target or
                        condition["type"] == "<" and price < target or
                        condition["type"] == "=" and price == target
                    ):
                        send_message(user_id, f"⚡ *{coin}* just hit your alert: `{condition['type']} {target}` (Now: ${price})")
                        conditions.remove(condition)
        time.sleep(30)

# Start background thread
threading.Thread(target=check_alerts_loop, daemon=True).start()

@app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        print("📥 Incoming Telegram data:", data)

        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "").strip()
            print(f"📨 Message from {chat_id}: {text}")

            if text.startswith("/start"):
                send_message(chat_id, "👋 Welcome to @Amadarecbot!\nUse `/alert BTC 80000` to get started.")
            elif text.startswith("/alert"):
                # [keep the rest of your alert logic here...]
                send_message(chat_id, "⚙️ Alert command received!")
            elif text.startswith("/list"):
                send_message(chat_id, "📋 List command received.")
            elif text.startswith("/cancel"):
                send_message(chat_id, "🗑 Cancel command received.")
            else:
                send_message(chat_id, "❓ Unknown command.")
        return {"ok": True}

    except Exception as e:
        print("❌ ERROR in webhook():", e)
        traceback.print_exc()
        return {"ok": False}, 500


import os
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
import traceback
