import os
import requests
import base64
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- CONFIGURATION ---
CLIENT_ID = os.environ.get("HOOPLA_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("HOOPLA_CLIENT_SECRET", "").strip()
CALLS_METRIC_ID = os.environ.get("HOOPLA_CALLS_METRIC_ID", "").strip()
TALK_TIME_METRIC_ID = os.environ.get("HOOPLA_TALK_TIME_METRIC_ID", "").strip()

# --- THE MEMORY (Temporary tracker) ---
# This keeps track of totals while the server is awake.
stats_tracker = {
    "calls": {},    # e.g. {"clare@move-tastic.com": 5}
    "duration": {}  # e.g. {"clare@move-tastic.com": 120}
}

USER_MAP = {
    "elizabeth@move-tastic.com": "829dd5aa-8aba-411d-8802-c75fe76524df",
    "clare@move-tastic.com": "7dca0f5e-03f3-47d9-a53c-63991412bf05",
    "nicole@move-tastic.com": "2e545f80-22bf-4d9c-89a9-1faaa3a59f3d",
    "nicholas@move-tastic.com": "dcca9e27-7eb1-4470-acca-d2aade7dfb3e",
    "wes@move-tastic.com": "c34ddc9a-a54b-42d5-9bdf-7d6edac4a835",
    "bailey@move-tastic.com": "92829845-daf3-40e3-a607-91140e9cb334"
}

def get_access_token():
    url = "https://api.hoopla.net/oauth2/token"
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_auth = base64.b64encode(auth_str.encode('utf-8')).decode('utf-8')
    headers = {"Authorization": f"Basic {encoded_auth}", "Content-Type": "application/x-www-form-urlencoded"}
    payload = {"grant_type": "client_credentials"}
    try:
        res = requests.post(url, data=payload, headers=headers)
        return res.json().get("access_token") if res.status_code == 200 else None
    except: return None

def sync_to_hoopla(token, metric_id, user_id, value):
    url = f"https://api.hoopla.net/metrics/{metric_id}/values"
    user_href = f"https://api.hoopla.net/users/{user_id}"
    payload = {"owner": {"kind": "user", "href": user_href}, "value": int(value)}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/vnd.hoopla.metric-value+json"}
    res = requests.post(url, json=payload, headers=headers)
    return res.status_code

@app.route('/', methods=['GET'])
def home(): return "Tracker Automation is Live!", 200

@app.route('/', methods=['POST'])
def handle_dialpad_event():
    data = request.json
    if not data or data.get('state') != 'hangup':
        return jsonify({"status": "ignored"}), 200

    agent_email = data.get('target', {}).get('email', '').lower().strip()
    duration_secs = int(data.get('duration', 0) / 1000)
    user_id = USER_MAP.get(agent_email)

    if user_id:
        # 1. Update our internal memory
        stats_tracker["calls"][agent_email] = stats_tracker["calls"].get(agent_email, 0) + 1
        stats_tracker["duration"][agent_email] = stats_tracker["duration"].get(agent_email, 0) + duration_secs

        # 2. Get totals from memory
        total_calls = stats_tracker["calls"][agent_email]
        total_duration = stats_tracker["duration"][agent_email]

        # 3. Push the NEW TOTALS to Hoopla
        token = get_access_token()
        if token:
            s1 = sync_to_hoopla(token, CALLS_METRIC_ID, user_id, total_calls)
            s2 = sync_to_hoopla(token, TALK_TIME_METRIC_ID, user_id, total_duration)
            print(f"PUSHED TOTALS: {agent_email} | Calls: {total_calls} | Time: {total_duration}s")
        else:
            print("Token error.")
            
    return jsonify({"status": "processed"}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
