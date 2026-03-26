import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- CONFIGURATION ---
HOOPLA_TOKEN = os.environ.get("HOOPLA_TOKEN")
HOOPLA_METRIC_ID = os.environ.get("HOOPLA_METRIC_ID")
HOOPLA_API_URL = "https://api.hoopla.net/metrics"

@app.route('/', methods=['GET'])
def home():
    return "Service is Live!", 200

@app.route('/', methods=['POST'])
def handle_dialpad_event():
    data = request.json
    
    # Check if the call state is 'hangup'
    if data and data.get('state') == 'hangup':
        # Dialpad puts email inside the 'target' object
        agent_email = data.get('target', {}).get('email')
        
        if agent_email:
            # Clean up the ID and Token (removes accidental spaces/slashes)
            metric_id = HOOPLA_METRIC_ID.strip()
            token = HOOPLA_TOKEN.strip()
            
            hoopla_endpoint = f"{HOOPLA_API_URL}/{metric_id}/values"
            
            payload = {
                "user": agent_email.lower().strip(),
                "value": 1
            }
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            try:
                response = requests.post(hoopla_endpoint, json=payload, headers=headers)
                print(f"Hoopla Sync Attempt: {response.status_code} for {agent_email}")
                if response.status_code >= 400:
                    print(f"Hoopla Error: {response.text}")
            except Exception as e:
                print(f"Request failed: {e}")

    return jsonify({"status": "received"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
