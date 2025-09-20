from flask import Flask, request, jsonify, abort
from google.cloud import secretmanager
from parking_checker import check_parking_icon
import os
import smtplib
from email.mime.text import MIMEText
import logging
import requests


app = Flask(__name__)

def send_telegram_notification(telegram_bot_api_key):
    url = f"https://api.telegram.org/bot{telegram_bot_api_key}/sendMessage"

    payload = {
        "chat_id": os.environ.get("TELEGRAM_CHAT_ID"),
        "text": os.environ.get("MESSAGE")
    }

    response = requests.post(url, data=payload)

    if response.status_code != 200:
        logging.warning("Telegram Bot API error", response.text)

def get_client_ip():
    # X-Forwarded-For can contain multiple IPs, take the first one
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    return request.remote_addr

def send_notification(smtp_pass):
    msg = MIMEText(os.environ.get("MESSAGE"))
    msg["Subject"] = "Dziś parking na Stadionie Narodowym jest nieczynny."
    msg["From"] = os.environ.get("MAIL_FROM")
    msg["To"] = os.environ.get("MAIL_TO")

    with smtplib.SMTP_SSL(os.environ.get("SMTP_SERVER"), 465) as server:
        server.login(os.environ.get("SMTP_LOGIN"), smtp_pass)
        server.send_message(msg)

def get_secret(project_id: str, secret_id: str | None = None) -> str:
    # https://console.cloud.google.com/security/secret-manager?
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("utf-8")

@app.route('/', methods=['GET'])
def hello_world():
    return jsonify(message=''), 200


@app.route('/cron_endpoint', methods=['GET'])
def cron_endpoint():
    """
    An endpoint for a cron job that checks both the X-AppEngine-Cron header and the source IP.
    gcloud app deploy cron.yaml
    """
    # 1. Verify the X-Appengine-Cron header.
    if request.headers.get('X-Appengine-Cron') is None:
        return jsonify(message='Unauthorized: Missing X-Appengine-Cron header.'), 403

    # 2. Verify the source IP address.
    if get_client_ip() != os.environ.get("CRON_IP_ADDRESS"):
        return jsonify(message='Unauthorized: Missing X-Appengine-Cron header.'), 403

    # 3. Both checks pass - run check
    logging.warning("Run check")
    parking_available = check_parking_icon()
    if parking_available is True:
        logging.warning("Parking True")
        project_id = os.environ.get("GOOGLE_PROJECT_ID")
        secret_id_smtp = os.environ.get("SMTP_API_KEY")
        secret_id_telegram = os.environ.get("TELEGRAM_BOT_API_KEY")
        smtp_pass = get_secret(project_id=project_id, secret_id=secret_id_smtp)
        send_notification(smtp_pass)
        telegram_bot_api_key = get_secret(project_id=project_id, secret_id=secret_id_telegram)
        send_telegram_notification(telegram_bot_api_key)

    return jsonify(message='Cron job ran successfully.'), 200


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)