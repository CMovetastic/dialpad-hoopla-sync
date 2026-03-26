import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- CONFIGURATION (Safe Version) ---
# We pull these from Render's secret settings later
HOOPLA_TOKEN = os.environ.get("HOOPLA_TOKEN")
HOOPLA_METRIC_ID = os.environ.get("HOOPLA_METRIC_ID")
HOOPLA_API_URL = "https://api.hoopla.net/metrics"

@app.route('/webhook', methods=['POST'])
def handle_dialpad_event():
    data = request.json
    
    # 1. Filter: Only act when the call state is 'hangup'
    # This prevents duplicate points for 'ringing' or 'connected' states
    if data.get('state') == 'hangup':
        
        # 2. Extract Agent Email
        # Dialpad puts the agent info in the 'target' or 'operator' field
        agent_email = data.get('target', {}).get('email')
        
        if agent_email:
            # 3. Construct Hoopla Payload
            # Hoopla needs the user's email and the value to add (1 call)
            hoopla_url = f"{HOOPLA_API_BASE}/metrics/{HOOPLA_METRIC_ID}/values"
            payload = {
                "user": agent_email,
                "value": 1
            }
            
            headers = {
                "Authorization": f"Bearer {HOOPLA_TOKEN}",
                "Content-Type": "application/json"
            }
            
            # 4. Push to Hoopla
            try:
                response = requests.post(hoopla_url, json=payload, headers=headers)
                print(f"Hoopla Sync: {response.status_code} for {agent_email}")
            except Exception as e:
                print(f"Error syncing to Hoopla: {e}")

    # Always return 200 to Dialpad so it doesn't retry the webhook
    return jsonify({"status": "processed"}), 200

if __name__ == "__main__":
    # Use the port Render assigns, or default to 5000 for local testing
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
