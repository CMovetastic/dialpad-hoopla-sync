import os
import json
import gspread
import requests
import base64
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- CONFIGURATION (Pulls from Render) ---
CLIENT_ID = os.environ.get("HOOPLA_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("HOOPLA_CLIENT_SECRET", "").strip()
CALLS_METRIC_ID = os.environ.get("HOOPLA_CALLS_METRIC_ID", "").strip()
TALK_TIME_METRIC_ID = os.environ.get("HOOPLA_TALK_TIME_METRIC_ID", "").strip()
SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "").strip()

# --- THE USER MAP ---
USER_MAP = {
    "elizabeth@move-tastic.com": "829dd5aa-8aba-411d-8802-c75fe76524df",
    "clare@move-tastic.com": "7dca0f5e-03f3-47d9-a53c-63991412bf05",
    "nicole@move-tastic.com": "2e545f80-22bf-4d9c-89a9-1faaa3a59f3d",
    "nicholas@move-tastic.com": "dcca9e27-7eb1-4470-acca-d2aade7dfb3e",
    "wes@move-tastic.com": "c34ddc9a-a54b-42d5-9bdf-7d6edac4a835",
    "bailey@move-tastic.com": "92829845-daf3-40e3-a607-91140e9cb334"
}

# --- GOOGLE SHEETS LOGIC ---
def get_sheet():
    raw_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    try:
        google_info = json.loads(raw_json.strip())
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(google_info, scope)
        client = gspread.authorize(creds)
        return client.open_by_key(SHEET_ID).worksheet("Totals")
    except Exception as e:
        print(f"Google Sheet Auth Error: {e}")
        return None

def update_totals_and_get_new(email, new_duration_secs):
    sheet = get_sheet()
    if not sheet: return 0, 0
    try:
        cell = sheet.find(email)
        if cell:
            current_calls = int(sheet.cell(cell.row, 2).value or 0)
            current_dur = int(sheet.cell(cell.row, 3).value or 0)
            
            new_calls = current_calls + 1
            new_dur = current_dur + new_duration_secs
            
            sheet.update_cell(cell.row, 2, new_calls)
            sheet.update_cell(cell.row, 3, new_dur)
            return new_calls, new_dur
    except Exception as e:
        print(f"Sheet Update Error: {e}")
    return 0, 0

# --- HOOPLA LOGIC ---
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

# --- ROUTES ---
@app.route('/', methods=['GET'])
def home():
    return "Google Sheets + Hoopla Sync is LIVE!", 200

@app.route('/', methods=['POST'])
def handle_dialpad_event():
    data = request.json
    if not data or data.get('state') != 'hangup':
        return jsonify({"status": "ignored"}), 200

    target = data.get('target', {})
    agent_email = target.get('email', '').lower().strip()
    duration_secs = int(data.get('duration', 0) / 1000)
    
    user_id = USER_MAP.get(agent_email)
    
    if user_id:
        # 1. Update Sheet & Get Summed Totals
        total_calls, total_duration = update_totals_and_get_new(agent_email, duration_secs)
        
        if total_calls > 0:
            # 2. Push Sums to Hoopla
            token = get_access_token()
            if token:
                s1 = sync_to_hoopla(token, CALLS_METRIC_ID, user_id, total_calls)
                s2 = sync_to_hoopla(token, TALK_TIME_METRIC_ID, user_id, total_duration)
                print(f"SUCCESS: {agent_email} | Total Calls: {total_calls} | Total Time: {total_duration}s")
            else:
                print("Hoopla Token Error")
    
    return jsonify({"status": "processed"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
