import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

HOOPLA_TOKEN = os.environ.get("HOOPLA_TOKEN")
HOOPLA_METRIC_ID = os.environ.get("HOOPLA_METRIC_ID")
HOOPLA_API_URL = "https://api.hoopla.net/metrics"

@app.route('/webhook', methods=['POST'])
def debug_webhook():
    data = request.json
    app.logger.info("--- NEW EVENT RECEIVED FROM DIALPAD ---")
    app.logger.info(f"Payload: {data}")

    # Dialpad v2 usually nests call info under 'call' or 'event'
    # Let's try to find the email in common locations
    call_data = data.get('call', data) 
    state = call_data.get('state')
    
    # Try multiple ways to find the agent's email
    agent_email = (
        call_data.get('target', {}).get('email') or 
        call_data.get('operator', {}).get('email') or
        data.get('email')
    )

    app.logger.info(f"Detected State: {state} | Detected Email: {agent_email}")

    if state == 'hangup' and agent_email:
        app.logger.info(f"Attempting Hoopla Sync for {agent_email}...")
        
        url = f"https://api.hoopla.net/metrics/{HOOPLA_METRIC_ID}/values"
        headers = {
            "Authorization": f"Bearer {HOOPLA_TOKEN}",
            "Content-Type": "application/json"
        }
