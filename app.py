import os
import requests
import base64
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- CONFIGURATION (Pulls from Render Environment Variables) ---
CLIENT_ID = os.environ.get("HOOPLA_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("HOOPLA_CLIENT_SECRET", "").strip()
CALLS_METRIC_ID = os.environ.get("HOOPLA_CALLS_METRIC_ID", "").strip()
TALK_TIME_METRIC_ID = os.environ.get("HOOPLA_TALK_TIME_METRIC_ID", "").strip()

# --- THE USER MAP (Email to Hoopla ID) ---
# We still keep this map here so the script knows which ID belongs to which email.
USER_MAP = {
    "elizabeth@move-tastic.com": "829dd5aa-8aba-411d-8802-c75fe76524df",
    "clare@move-tastic.com": "7dca0f5e-03f3-47d9-a53c-63991412bf05",
    "nicole@move-tastic.com": "2e545f80-22bf-4d9c-89a9-1faaa3a59f3d",
    "nicholas@move-tastic.com": "dcca9e27-7eb1-4470-acca-d2aade7dfb3e",
    "wes@move-tastic.com": "c34ddc9a-a54b-42d5-9bdf-7d6edac4a835",
    "bailey@move-tastic.com": "92829845-daf3-40e3-a607-91140e9cb334"
}


def get_access_token():
    """Fetches a fresh token using Basic Auth"""
    url = "https://api.hoopla.net/oauth2/token"
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_auth = base64.b64encode(auth_str.encode('utf-8')).decode('utf-8')
    
    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {"grant_type": "client_credentials"}
    
    try:
        response = requests.post(url, data=payload, headers=headers)
        if response.status_code == 200:
            return response.json().get("access_token")
        print(f"Auth Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Token Request Error: {e}")
    return None

def sync_to_hoopla(token, metric_id, user_id, value):
    """Sends the actual data to Hoopla"""
    url = f"https://api.hoopla.net/metrics/{metric_id}/values"
    user_href = f"https://api.hoopla.net/users/{user_id}"
    
    payload = {
        "owner": {"kind": "user", "href": user_href},
        "value": int(value)
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/vnd.hoopla.metric-value+json",
        "Accept": "application/vnd.hoopla.metric-value+json"
    }
    res = requests.post(url, json=payload, headers=headers)
    return res.status_code

@app.route('/', methods=['GET'])
def home():
    return "Automation is Live and Token-Ready!", 200

@app.route('/', methods=['POST'])
def handle_dialpad_event():
    data = request.json
    if not data or data.get('state') != 'hangup':
        return jsonify({"status": "ignored"}), 200

    target = data.get('target', {})
    agent_email = target.get('email', '').lower().strip()
    
    # Convert Dialpad Milliseconds to Seconds
    raw_duration = data.get('duration', 0)
    duration_in_seconds = int(raw_duration / 1000)
    
    user_id = USER_MAP.get(agent_email)
    
    if user_id:
        token = get_access_token()
        if token:
            s1 = sync_to_hoopla(token, CALLS_METRIC_ID, user_id, 1)
            s2 = sync_to_hoopla(token, TALK_TIME_METRIC_ID, user_id, duration_in_seconds)
            print(f"SUCCESS: {agent_email} | Calls: {s1} | TalkTime: {s2} ({duration_in_seconds}s)")
        else:
            print("Could not get a fresh token.")
    else:
        print(f"User {agent_email} not found in USER_MAP.")

    return jsonify({"status": "processed"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
