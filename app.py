import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, request, jsonify

app = Flask(__name__)

# Only one ID needed: the Sheet!
SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "").strip()

def get_sheet():
    raw_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    try:
        google_info = json.loads(raw_json.strip())
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(google_info, scope)
        client = gspread.authorize(creds)
        # Make sure your tab name is exactly "Totals"
        return client.open_by_key(SHEET_ID).worksheet("Totals")
    except Exception as e:
        print(f"Sheet Access Error: {e}")
        return None

@app.route('/', methods=['POST'])
def handle_dialpad_event():
    data = request.json
    if not data or data.get('state') != 'hangup':
        return jsonify({"status": "ignored"}), 200

    target = data.get('target', {})
    agent_email = target.get('email', '').lower().strip()
    duration_secs = int(data.get('duration', 0) / 1000)
    
    if not agent_email:
        return jsonify({"status": "no_email"}), 200

    sheet = get_sheet()
    if sheet:
        try:
            # 1. Get all emails from Column A
            all_emails = [str(e).lower().strip() for e in sheet.col_values(1)]
            
            if agent_email in all_emails:
                # --- UPDATE EXISTING USER ---
                row_number = all_emails.index(agent_email) + 1
                current_calls = int(sheet.cell(row_number, 2).value or 0)
                current_dur = int(sheet.cell(row_number, 3).value or 0)
                
                sheet.update_cell(row_number, 2, current_calls + 1)
                sheet.update_cell(row_number, 3, current_dur + duration_secs)
                print(f"UPDATED: {agent_email} (Row {row_number})")
            else:
                # --- AUTO-ADD NEW USER ---
                # This adds a new row at the bottom: [Email, 1 Call, Duration]
                new_row = [agent_email, 1, duration_secs]
                sheet.append_row(new_row)
                print(f"AUTO-ADDED NEW USER: {agent_email}")
                
        except Exception as e:
            print(f"Sheet error: {e}")
            
    return jsonify({"status": "processed"}), 200

@app.route('/', methods=['GET'])
def home(): return "Dialpad-to-Sheet Sync is LIVE!", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
