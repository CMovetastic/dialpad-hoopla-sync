import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

HOOPLA_TOKEN = os.environ.get("HOOPLA_TOKEN", "")
HOOPLA_METRIC_ID = os.environ.get("HOOPLA_METRIC_ID", "")
HOOPLA_API_URL = "https://api.hoopla.net/metrics"

@app.route('/', methods=['GET'])
def home():
    return "Service is Live!", 200

@app.route('/', methods=['POST'])
def handle_dialpad_event():
    data = request.json
    if not data:
        return jsonify({"status": "no data"}), 200

    if data.get('state') == 'hangup':
        target = data.get('target', {})
        agent_email = target.get('email')
        
        if agent_email and HOOPLA_TOKEN and HOOPLA_METRIC_ID:
            metric_id = HOOPLA_METRIC_ID.strip()
            user_path = f"/users/{agent_email.lower().strip()}"
            hoopla_endpoint = f"{HOOPLA_API_URL}/{metric_id}/values"
            
            # The "Ultra-Lean" payload with all brackets closed
            payload = {
          "owner": {
                    "kind": "user",
                    "href": user_path
                },
                "value": 1
            }
            
            headers = {
                "Authorization": f"Bearer {HOOPLA_TOKEN.strip()}",
                "Content-Type": "application/vnd.hoopla.metric-value+json",
                "Accept": "application/vnd.hoopla.metric-value+json"
            }
            
            try:
                print(f"Attempting sync for: {agent_email}")
                response = requests.post(hoopla_endpoint, json=payload, headers=headers)
                print(f"Hoopla Sync: {response.status_code} | Response: {response.text}")
            except Exception as e:
                print(f"Request failed: {e}")

    return jsonify({"status": "received"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
