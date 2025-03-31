import json
import os
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = "7772895600:AAH7OY0PODCGQVPnOCw3JB00WjZ3JAp9oMs"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Load or initialize alerts
ALERT_FILE = 'alerts.json'
if os.path.exists(ALERT_FILE):
    with open(ALERT_FILE, 'r') as f:
        user_alerts = json.load(f)
else:
    user_alerts = {}

def save_alerts():
    with open(ALERT_FILE, 'w') as f:
        json.dump(user_alerts, f)

def send_message(chat_id, text, buttons=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if buttons:
        payload["reply_markup"] = json.dumps({"keyboard": buttons, "resize_keyboard": True})
    requests.post(URL + "sendMessage", json=payload)
@app.route("/", methods=["GET"])
def home():
    return "✅ Bot is alive!"
@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    if "message" in data:
        chat_id = str(data["message"]["chat"]["id"])
        text = data["message"].get("text", "")

        if text.startswith("/start"):
            send_message(chat_id,
                         "👋 *Welcome to your Crypto Alert Bot!*\n\nUse /help to see all commands.",
                         buttons=[["/alert", "/list"], ["/cancel", "/help"]])

        elif text.startswith("/help"):
            help_msg = (
                "📖 *Bot Commands:*\n\n"
                "➕ `/alert BTC > 85000` — set alert\n"
                "❌ `/cancel BTC` — cancel all alerts for BTC\n"
                "📋 `/list` — view your active alerts\n"
                "💡 Example: `/alert ETH < 1800`\n"
            )
            send_message(chat_id, help_msg)

        elif text.startswith("/alert"):
            parts = text.split()
            if len(parts) >= 4:
                _, coin, condition, *rest = parts
                coin = coin.upper()
                symbol = condition[0]
                price = float(condition[1:] if symbol in ['>', '<'] else condition)

                if chat_id not in user_alerts:
                    user_alerts[chat_id] = {}
                if coin not in user_alerts[chat_id]:
                    user_alerts[chat_id][coin] = []
                user_alerts[chat_id][coin].append({"type": symbol, "price": price})
                save_alerts()
                send_message(chat_id, f"✅ Alert set: *{coin} {symbol} {price}*")
            else:
                send_message(chat_id, "❌ Format: `/alert BTC > 85000`")

        elif text.startswith("/cancel"):
            parts = text.split()
            if len(parts) == 2:
                _, coin = parts
                coin = coin.upper()
                if chat_id in user_alerts and coin in user_alerts[chat_id]:
                    del user_alerts[chat_id][coin]
                    save_alerts()
                    send_message(chat_id, f"❌ Cancelled all alerts for *{coin}*")
                else:
                    send_message(chat_id, f"⚠️ No alerts found for *{coin}*")
            else:
                send_message(chat_id, "❌ Format: `/cancel BTC`")

        elif text.startswith("/list"):
            if chat_id in user_alerts and user_alerts[chat_id]:
                alert_list = []
                for coin, alerts in user_alerts[chat_id].items():
                    for alert in alerts:
                        alert_list.append(f"{coin} {alert['type']} {alert['price']}")
                send_message(chat_id, "📋 *Your Alerts:*\n" + "\n".join(alert_list))
            else:
                send_message(chat_id, "📭 No active alerts.")

    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
