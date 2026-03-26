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
    return "Service is Live! If you see this, the 'Front Door' is open.", 200

@app.route('/', methods=['POST'])
def handle_dialpad_event():
    data = request.json
    print(f"Received from Dialpad: {data}")
    
    # Check for hangup state
    if data and data.get('state') == 'hangup':
        agent_email = data.get('target', {}).get('email')
        
        if agent_email:
            hoopla_endpoint = f"{HOOPLA_API_URL}/{HOOPLA_METRIC_ID}/values"
            payload = {"user": agent_email, "value": 1}
            headers = {
                "Authorization": f"Bearer {HOOPLA_TOKEN}",
                "Content-Type": "application/json"
            }
            
            try:
                # This is the actual 'action' line
                response = requests.post(hoopla_endpoint, json=payload, headers=headers)
                
                # These lines help us see what happened in the Render logs
                print(f"Hoopla Sync: {response.status_code} for {agent_email}")
                
                # If Hoopla sends back an error (like that 500), this shows us WHY
                if response.status_code >= 400:
                    print(f"Hoopla Error Response: {response.text}")

            except Exception as e:
                # This catches connection issues (like if Hoopla's site is down)
                print(f"Connection Error: {e}")

    return jsonify({"status": "received"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
