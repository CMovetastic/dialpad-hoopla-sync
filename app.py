import os
import sys
import requests
import logging
from flask import Flask, request, jsonify

# This forces logs to show up in Render's dashboard
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
app = Flask(__name__)

HOOPLA_TOKEN = os.environ.get("3a7875a6b897b3f4a6e6c701/a3a8f8a9ff8433a91f527090cd5ea19383d4cd7b8c9da3fdd2a65560be62500b4f1d1c8a1a43dfb3f1722bd50e34ab783adf107814fb328e447a54f3557b61c0d3b4008d30c04d133599ab4b9f7df325c83252d320c76b63fe7aa18f5b8c1843beda393e379788298335993c08c92bf1f4c24c63045744a28ace3f707961e8b13aca449d01abfb49f1403280c5dac5a7c8c5750013f107f11243257741e54c2876a9da7e435359e121bbf62d33/30de04e519405cc6defe22de1c37f1a3","refresh_token":"06b85e3d5b24c8b9732a4113/3808b64519b1eea740412e351396415d1639269155841f758c38046ebc76c7a6eddcd148fc6ef173b6ab4ec3f1331136480844acdbc1ca49556f247a0e0504f20d2f52ae1c5b1a400107f67d3a667672c9c6a55117892cd76c29667aa47bfc2915b9ad0002b16360ec80a98572ade690d43d1fdcb7/c28f717ccb73da5c5d2c8271b0da2e35","token_type":"bearer","expires_in":1800,"user_id":null,"email":null,"customer_id":"365c2346-7acf-468f-8d67-0af2467c7071","customer_state":"free_trial","role":"External","role_subtype":null,"admin_teams":null}% " )
HOOPLA_METRIC_ID = os.environ.get("ae07c81c-addc-4602-9891-921bd3e6bd35")

@app.route('/webhook', methods=['POST'])
def debug_webhook():
    data = request.json
    app.logger.info("--- NEW EVENT RECEIVED FROM DIALPAD ---")
    app.logger.info(f"Payload: {data}")

    # Dialpad v2 usually nests call info under 'call' or 'event'
    # Let's try to find the email in common locations
    call_data = data.get('call', data) 
    state = call_data.get('state')
    
    # Try multiple ways to find the agent's email
    agent_email = (
        call_data.get('target', {}).get('email') or 
        call_data.get('operator', {}).get('email') or
        data.get('email')
    )

    app.logger.info(f"Detected State: {state} | Detected Email: {agent_email}")

    if state == 'hangup' and agent_email:
        app.logger.info(f"Attempting Hoopla Sync for {agent_email}...")
        
        url = f"https://api.hoopla.net/metrics/{HOOPLA_METRIC_ID}/values"
        headers = {
            "Authorization": f"Bearer {HOOPLA_TOKEN}",
            "Content-Type": "application/json"
        }
