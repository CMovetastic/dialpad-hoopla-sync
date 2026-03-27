import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, request, jsonify
import requests
import base64

app = Flask(__name__)

# --- CONFIG ---
SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")
# Load the full JSON string from Render
GOOGLE_JSON = json.loads(os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON"))

USER_MAP = {
    "elizabeth@move-tastic.com": "829dd5aa-8aba-411d-8802-c75fe76524df",
    "clare@move-tastic.com": "7dca0f5e-03f3-47d9-a53c-63991412bf05",
    "nicole@move-tastic.com": "2e545f80-22bf-4d9c-89a9-1faaa3a59f3d",
    "nicholas@move-tastic.com": "dcca9e27-7eb1-4470-acca-d2aade7dfb3e",
    "wes@move-tastic.com": "c34ddc9a-a54b-42d5-9bdf-7d6edac4a835",
    "bailey@move-tastic.com": "92829845-daf3-40e3-a607-91140e9cb334"
}

def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_JSON, scope)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID).worksheet("Totals")

def update_totals_and_get_new(email, new_duration_secs):
    sheet = get_sheet()
    cell = sheet.find(email)
    
    if cell:
        # Get current values from columns B and C
        current_calls = int(sheet.cell(cell.row, 2).value or 0)
        current_dur = int(sheet.cell(cell.row, 3).value or 0)
        
        # New totals
        new_calls = current_calls + 1
        new_dur = current_dur + new_duration_secs
        
        # Update Sheet
        sheet.update_cell(cell.row, 2, new_calls)
        sheet.update_cell(cell.row, 3, new_dur)
        
        return new_calls, new_dur
    return 1, new_duration_secs # Fallback

# ... (Keep your get_access_token and sync_to_hoopla functions from before) ...

@app.route('/', methods=['POST'])
def handle_dialpad_event():
    data = request.json
    if not data or data.get('state') != 'hangup':
        return jsonify({"status": "ignored"}), 200

    agent_email = data.get('target', {}).get('email', '').lower().strip()
    duration_secs = int(data.get('duration', 0) / 1000)
    user_id = USER_MAP.get(agent_email)

    if user_id:
        # 1. Update the "Memory" in Google Sheets and get the updated Daily Total
        total_calls, total_duration = update_totals_and_get_new(agent_email, duration_secs)
        
        # 2. Push these Daily Totals to Hoopla
        token = get_access_token()
        if token:
            sync_to_hoopla(token, CALLS_METRIC_ID, user_id, total_calls)
            sync_to_hoopla(token, TALK_TIME_METRIC_ID, user_id, total_duration)
            print(f"SHEET UPDATED: {agent_email} | New Daily Calls: {total_calls} | New Daily Time: {total_duration}s")
            
    return jsonify({"status": "processed"}), 200
