import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, request, jsonify

app = Flask(__name__)
SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "").strip()

def get_google_client():
    raw_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    google_info = json.loads(raw_json.strip())
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(google_info, scope)
    return gspread.authorize(creds)

def update_tab(sheet_obj, email, duration_secs):
    try:
        # Get all emails in Column A of this specific tab
        all_emails = [str(e).lower().strip() for e in sheet_obj.col_values(1)]
        
        if email in all_emails:
            row_idx = all_emails.index(email) + 1
            curr_calls = int(sheet_obj.cell(row_idx, 2).value or 0)
            curr_dur = int(sheet_obj.cell(row_idx, 3).value or 0)
            
            sheet_obj.update_cell(row_idx, 2, curr_calls + 1)
            sheet_obj.update_cell(row_idx, 3, curr_dur + duration_secs)
        else:
            # Auto-add if user is missing from this tab
            sheet_obj.append_row([email, 1, duration_secs])
    except Exception as e:
        print(f"Error updating tab: {e}")

@app.route('/', methods=['POST'])
def handle_dialpad_event():
    data = request.json
    if not data or data.get('state') != 'hangup':
        return jsonify({"status": "ignored"}), 200

    agent_email = data.get('target', {}).get('email', '').lower().strip()
    duration_secs = int(data.get('duration', 0) / 1000)
    
    if not agent_email:
        return jsonify({"status": "no_email"}), 200

    try:
        client = get_google_client()
        spreadsheet = client.open_by_key(SHEET_ID)
        
        # Update both tabs!
        daily_sheet = spreadsheet.worksheet("Daily")
        monthly_sheet = spreadsheet.worksheet("Monthly")
        
        update_tab(daily_sheet, agent_email, duration_secs)
        update_tab(monthly_sheet, agent_email, duration_secs)
        
        print(f"SUCCESS: Recorded call for {agent_email} in Daily and Monthly tabs.")
    except Exception as e:
        print(f"Global Sheet Error: {e}")
            
    return jsonify({"status": "processed"}), 200

@app.route('/', methods=['GET'])
def home(): return "Dialpad Dual-Tab Sync is LIVE!", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
