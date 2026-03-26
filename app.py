import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- CONFIGURATION ---
# We use .get() to avoid errors if these aren't set in Render yet
HOOPLA_TOKEN = os.environ.get("HOOPLA_TOKEN")
HOOPLA_METRIC_ID = os.environ.get("HOOPLA_METRIC_ID")
# Standardizing the URL variable name here
HOOPLA_API_URL = "https://api.hoopla.net/metrics"

@app.route('/', methods=['POST'])
def handle_dialpad_event():
    data = request.json
    
    # 1. Check for 'hangup' state
    if data.get('state') == 'hangup':
        
        # 2. Extract Agent Email
        agent_email = data.get('target', {}).get('email')
        
        if agent_email:
            # 3. Construct the exact Hoopla endpoint
            # Note: We use HOOPLA_API_URL defined above
            hoopla_endpoint = f"{HOOPLA_API_URL}/{HOOPLA_METRIC_ID}/values"
            
            payload = {
                "user": agent_email,
                "value": 1
            }
            
            headers = {
                "Authorization": f"Bearer {HOOPLA_TOKEN}",
                "Content-Type": "application/json"
            }
            
            # 4. Push to Hoopla
            try:
                response = requests.post(hoopla_endpoint, json=payload, headers=headers)
                print(f"Hoopla Sync: {response.status_code} for {agent_email}")
                if response.status_code != 201:
                    print(f"Hoopla Error Detail: {response.text}")
            except Exception as e:
                print(f"Connection Error: {e}")

    # Return 200 so Dialpad knows we received it
    return jsonify({"status": "processed"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
