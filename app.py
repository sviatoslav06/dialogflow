import os
import json
import logging
from flask import Flask, request, jsonify
import requests
from google.cloud import dialogflowcx_v3beta1 as dialogflowcx

# ---------- CONFIG ----------
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
PROJECT_ID = os.environ["DIALOGFLOW_PROJECT_ID"]
AGENT_LOCATION = os.environ["DIALOGFLOW_AGENT_LOCATION"]
AGENT_ID = os.environ["DIALOGFLOW_AGENT_ID"]
LANGUAGE_CODE = "en"

# ---------- CREDENTIALS ----------
# Декодуємо JSON-ключ, переданий як змінна середовища
with open("credentials.json", "w") as f:
    f.write(os.environ["GOOGLE_CREDENTIALS_JSON"])

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"

# ---------- FLASK APP ----------
app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

session_client = dialogflowcx.SessionsClient()

@app.route('/')
def home():
    return 'Telegram → Dialogflow CX бот активний!'

@app.route(f'/webhook/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        logging.info(f"Data: {data}")

        if 'message' not in data:
            return jsonify({"status": "ignored"})

        chat_id = data['message']['chat']['id']
        text = data['message']['text']

        # Створюємо сесію
        session_id = str(chat_id)
        session_path = session_client.session_path(PROJECT_ID, AGENT_LOCATION, AGENT_ID, session_id)

        text_input = dialogflowcx.TextInput(text=text)
        query_input = dialogflowcx.QueryInput(text=text_input, language_code=LANGUAGE_CODE)

        request_dialogflow = dialogflowcx.DetectIntentRequest(
            session=session_path,
            query_input=query_input
        )

        response = session_client.detect_intent(request=request_dialogflow)
        fulfillment = response.query_result.response_messages

        reply_text = ""
        for message in fulfillment:
            if message.text:
                reply_text += " ".join(message.text.text)

        # Відправити відповідь назад у Telegram
        send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(send_url, json={"chat_id": chat_id, "text": reply_text})

        return jsonify({"status": "ok"})

    except Exception as e:
        logging.exception("Webhook error:")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
