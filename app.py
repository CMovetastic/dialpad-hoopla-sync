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

def get_current_value(token, metric_id, user_id):
    """Asks Hoopla for the user's current total for a specific metric"""
    # Note: We filter by the user's href to get their specific total
    url = f"https://api.hoopla.net/metrics/{metric_id}/values?owner={user_id}&owner_kind=user"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.hoopla.metric-value+json"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            data = res.json()
            # If the user has data, return the first value, otherwise return 0
            if data and len(data) > 0:
                return data[0].get('value', 0)
        return 0
    except: return 0

def sync_to_hoopla(token, metric_id, user_id, new_total):
    """Sends the NEW SUMmed total to Hoopla"""
    url = f"https://api.hoopla.net/metrics/{metric_id}/values"
    user_href = f"https://api.hoopla.net/users/{user_id}"
    payload = {"owner": {"kind": "user", "href": user_href}, "value": int(new_total)}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/vnd.hoopla.metric-value+json"}
    res = requests.post(url, json=payload, headers=headers)
    return res.status_code

@app.route('/', methods=['GET'])
def home(): return "Smart Summing Automation is Live!", 200

@app.route('/', methods=['POST'])
def handle_dialpad_event():
    data = request.json
    if not data or data.get('state') != 'hangup':
        return jsonify({"status": "ignored"}), 200

    agent_email = data.get('target', {}).get('email', '').lower().strip()
    duration_secs = int(data.get('duration', 0) / 1000)
    user_id = USER_MAP.get(agent_email)

    if user_id:
        token = get_access_token()
        if token:
            # 1. Handle Call Count
            current_calls = get_current_value(token, CALLS_METRIC_ID, user_id)
            s1 = sync_to_hoopla(token, CALLS_METRIC_ID, user_id, current_calls + 1)

            # 2. Handle Talk Time
            current_tt = get_current_value(token, TALK_TIME_METRIC_ID, user_id)
            s2 = sync_to_hoopla(token, TALK_TIME_METRIC_ID, user_id, current_tt + duration_secs)

            print(f"SUMMED: {agent_email} | Calls: {current_calls + 1} | TT: {current_tt + duration_secs}s")
        else:
            print("Token error.")
    return jsonify({"status": "processed"}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
