import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- CONFIGURATION ---
HOOPLA_TOKEN = os.environ.get("HOOPLA_TOKEN", "")
HOOPLA_METRIC_ID = os.environ.get("HOOPLA_METRIC_ID", "")
HOOPLA_API_URL = "https://api.hoopla.net/metrics"

@app.route('/', methods=['GET'])
def home():
    return "Service is Live!", 200

@app.route('/', methods=['POST'])
def handle_dialpad_event():
    data = request.json
    
    # Safety check: make sure we actually got data
    if not data:
        return jsonify({"status": "no data"}), 200

    # Dialpad hangup trigger
    if data.get('state') == 'hangup':
        # Safely grab the email
        target = data.get('target', {})
        agent_email = target.get('email')
        
if agent_email:
            # Clean up the ID and Token
            metric_id = HOOPLA_METRIC_ID.strip()
            
            # THE FIX: Hoopla often expects the user as a full relative path
            # Instead of just "email@co.com", we send "/users/email@co.com"
            user_path = f"/users/{agent_email.lower().strip()}"
            
            hoopla_endpoint = f"{HOOPLA_API_URL}/{metric_id}/values"
            
            payload = {
                "user": user_path,
                "value": 1
            }
            
            headers = {
                "Authorization": f"Bearer {HOOPLA_TOKEN.strip()}",
                "Content-Type": "application/vnd.hoopla.metric-value+json",
                "Accept": "application/vnd.hoopla.metric-value+json"
            }
            
            try:
                response = requests.post(hoopla_endpoint, json=payload, headers=headers)
                # This line will now print EVERYTHING so we can see the exact error
                print(f"Hoopla Sync: {response.status_code} | Response: {response.text}")
            except Exception as e:
                print(f"Request failed: {e}")

    return jsonify({"status": "received"}), 200

if __name__ == "__main__":
    # Render provides the PORT environment variable automatically
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
