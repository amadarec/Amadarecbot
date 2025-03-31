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

            if text.startswith("/start") or text.startswith("/help"):
                send_message(chat_id, """👋 Welcome to @Amadarecbot!

📌 *Available Commands:*
/set COIN PRICE → Set alert (ex: `/set BTC 80000`)
/set COIN > PRICE → Set condition alert (ex: `/set ETH <1800`)
/cancel COIN → Cancel alerts for a coin
/myalerts → View your active alerts
/help → Show this menu again
""")

            elif text.startswith("/set"):
                try:
                    parts = text.split()
                    if len(parts) not in [3, 4]:
                        raise ValueError
                    coin = parts[1].upper()
                    if coin not in SUPPORTED_COINS:
                        send_message(chat_id, f"❌ Unsupported coin: {coin}")
                        return
                    alert_type = "="
                    price = None
                    if len(parts) == 3:
                        price = float(parts[2])
                    elif len(parts) == 4:
                        alert_type = parts[2]
                        price = float(parts[3])
                        if alert_type not in ["<", ">", "="]:
                            raise ValueError
                    user_alerts.setdefault(chat_id, {}).setdefault(coin, []).append({
                        "type": alert_type,
                        "price": price
                    })
                    send_message(chat_id, f"✅ Alert set: *{coin} {alert_type} {price}*")
                except:
                    send_message(chat_id, "⚠️ Use: `/set BTC 80000` or `/set ETH <1900`")

            elif text.startswith("/cancel"):
                parts = text.split()
                if len(parts) != 2:
                    send_message(chat_id, "⚠️ Use: `/cancel BTC`")
                    return
                coin = parts[1].upper()
                if chat_id in user_alerts and coin in user_alerts[chat_id]:
                    del user_alerts[chat_id][coin]
                    send_message(chat_id, f"🗑 Alerts for {coin} canceled.")
                else:
                    send_message(chat_id, "❌ No alerts found for that coin.")

            elif text.startswith("/myalerts"):
                if chat_id not in user_alerts or not user_alerts[chat_id]:
                    send_message(chat_id, "📭 No active alerts.")
                    return
                msg = "📋 *Your Alerts:*\n"
                for coin, conds in user_alerts[chat_id].items():
                    for c in conds:
                        msg += f"• {coin} {c['type']} {c['price']}\n"
                send_message(chat_id, msg)

            else:
                send_message(chat_id, "❓ Unknown command. Type /help to see options.")

        return {"ok": True}

    except Exception as e:
        print("❌ ERROR in webhook():", e)
        import traceback
        traceback.print_exc()
        return {"ok": False}, 500



import os
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
import traceback
