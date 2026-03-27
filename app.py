import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- CONFIGURATION (From Render Environment Variables) ---
CLIENT_ID = os.environ.get("f05f82d7-bc91-400a-87be-e917675daa7f", "")
CLIENT_SECRET = os.environ.get("c7555fdb3247f21f31b315d584b78384c07e551ac59e", "")
CALLS_METRIC_ID = os.environ.get("ae07c81c-addc-4602-9891-921bd3e6bd35", "")  
TALK_TIME_METRIC_ID = os.environ.get("6123e233-7935-49ac-94cb-28ee5a6b3b24", "") 

# --- THE USER MAP ---
USER_MAP = {
    "elizabeth@move-tastic.com": "829dd5aa-8aba-411d-8802-c75fe76524df",
    "clare@move-tastic.com": "7dca0f5e-03f3-47d9-a53c-63991412bf05",
    "nicole@move-tastic.com": "2e545f80-22bf-4d9c-89a9-1faaa3a59f3d",
    "nicholas@move-tastic.com": "dcca9e27-7eb1-4470-acca-d2aade7dfb3e",
    "wes@move-tastic.com": "c34ddc9a-a54b-42d5-9bdf-7d6edac4a835",
    "bailey@move-tastic.com": "92829845-daf3-40e3-a607-91140e9cb334"
}

def get_access_token():
    """Fetches a fresh token using Client ID and Secret"""
    url = "https://api.hoopla.net/oauth2/token"
    # Hoopla expects a standard URL-encoded POST for OAuth
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            return response.json().get("access_token")
        print(f"Token Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Token request failed: {e}")
    return None

def sync_to_hoopla(token, metric_id, user_id, value):
    """Sends the actual data to Hoopla"""
    url = f"https://api.hoopla.net/metrics/{metric_id}/values"
    user_href = f"https://api.hoopla.net/users/{user_id}"
    
    payload = {
        "owner": {"kind": "user", "href": user_href},
        "value": int(value) # Ensure it's a whole number
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
    if not data:
        return jsonify({"status": "no data"}), 200

    # Process on hangup
    if data.get('state') == 'hangup':
        target = data.get('target', {})
        agent_email = target.get('email', '').lower().strip()
        
        # --- THE FIX: Convert Milliseconds to Seconds ---
        raw_duration = data.get('duration', 0)
        duration_in_seconds = int(raw_duration / 1000) 
        
        user_id = USER_MAP.get(agent_email)
        
        if user_id:
            token = get_access_token()
            if token:
                # 1. Log the Call Count
                s1 = sync_to_hoopla(token, CALLS_METRIC_ID, user_id, 1)
                # 2. Log the Talk Time (as actual seconds)
                s2 = sync_to_hoopla(token, TALK_TIME_METRIC_ID, user_id, duration_in_seconds)
                
                print(f"SUCCESS: {agent_email} | Calls: {s1} | TalkTime: {s2} ({duration_in_seconds}s)")

    return jsonify({"status": "processed"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
