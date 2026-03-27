import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- CONFIGURATION ---
HOOPLA_TOKEN = os.environ.get("HOOPLA_TOKEN", "")
HOOPLA_METRIC_ID = os.environ.get("HOOPLA_METRIC_ID", "")
HOOPLA_API_URL = "https://api.hoopla.net/metrics"

# --- THE PHONE BOOK ---
# Add everyone's email and their long ID from the terminal here
USER_MAP = {
    "elizabeth@move-tastic.com": "829dd5aa-8aba-411d-8802-c75fe76524df",
    "clare@move-tastic.com": "7dca0f5e-03f3-47d9-a53c-63991412bf05",
    "nicole@move-tastic.com": "2e545f80-22bf-4d9c-89a9-1faaa3a59f3d",
    "nicholas@move-tastic.com": "dcca9e27-7eb1-4470-acca-d2aade7dfb3e",
    "wes@move-tastic.com": "c34ddc9a-a54b-42d5-9bdf-7d6edac4a835",
    "bailey@move-tastic.com": "92829845-daf3-40e3-a607-91140e9cb334"
}

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
        agent_email = target.get('email', '').lower().strip()
        
        # Look up the ID in our phone book
        user_id = USER_MAP.get(agent_email)
        
        if user_id and HOOPLA_TOKEN and HOOPLA_METRIC_ID:
            metric_id = HOOPLA_METRIC_ID.strip()
            hoopla_endpoint = f"{HOOPLA_API_URL}/{metric_id}/values"
            user_href = f"https://api.hoopla.net/users/{user_id}"
            
            payload = {
                "owner": {
                    "kind": "user",
                    "href": user_href
                },
                "value": 1
            }
            
            headers = {
                "Authorization": f"Bearer {HOOPLA_TOKEN.strip()}",
                "Content-Type": "application/vnd.hoopla.metric-value+json",
                "Accept": "application/vnd.hoopla.metric-value+json"
            }
            
            try:
                response = requests.post(hoopla_endpoint, json=payload, headers=headers)
                print(f"Sync for {agent_email}: {response.status_code}")
            except Exception as e:
                print(f"Request failed: {e}")
        else:
            print(f"No ID found for {agent_email} - skipping sync.")

    return jsonify({"status": "received"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
