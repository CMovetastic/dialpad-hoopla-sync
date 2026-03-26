import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- CONFIGURATION ---
# We use .get() to avoid errors if these aren't set in Render yet
HOOPLA_TOKEN = os.environ.get("3a7875a6b897b3f4a6e6c701/a3a8f8a9ff8433a91f527090cd5ea19383d4cd7b8c9da3fdd2a65560be62500b4f1d1c8a1a43dfb3f1722bd50e34ab783adf107814fb328e447a54f3557b61c0d3b4008d30c04d133599ab4b9f7df325c83252d320c76b63fe7aa18f5b8c1843beda393e379788298335993c08c92bf1f4c24c63045744a28ace3f707961e8b13aca449d01abfb49f1403280c5dac5a7c8c5750013f107f11243257741e54c2876a9da7e435359e121bbf62d33/30de04e519405cc6defe22de1c37f1a3","refresh_token":"06b85e3d5b24c8b9732a4113/3808b64519b1eea740412e351396415d1639269155841f758c38046ebc76c7a6eddcd148fc6ef173b6ab4ec3f1331136480844acdbc1ca49556f247a0e0504f20d2f52ae1c5b1a400107f67d3a667672c9c6a55117892cd76c29667aa47bfc2915b9ad0002b16360ec80a98572ade690d43d1fdcb7/c28f717ccb73da5c5d2c8271b0da2e35","token_type":"bearer","expires_in":1800,"user_id":null,"email":null,"customer_id":"365c2346-7acf-468f-8d67-0af2467c7071","customer_state":"free_trial","role":"External","role_subtype":null,"admin_teams":null}%")
HOOPLA_METRIC_ID = os.environ.get("ae07c81c-addc-4602-9891-921bd3e6bd35")
# Standardizing the URL variable name here
HOOPLA_API_URL = "https://api.hoopla.net/metrics"

@app.route('/', methods=['POST'])
def handle_dialpad_event():
    data = request.json
    
    # 1. Check for 'hangup' state
    if data.get('state') == 'hangup':
        
        # 2. Extract Agent Email
        agent_email = data.get('target', {}).get('email')
        
        if agent_email:
            # 3. Construct the exact Hoopla endpoint
            # Note: We use HOOPLA_API_URL defined above
            hoopla_endpoint = f"{HOOPLA_API_URL}/{HOOPLA_METRIC_ID}/values"
            
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
                response = requests.post(hoopla_endpoint, json=payload, headers=headers)
                print(f"Hoopla Sync: {response.status_code} for {agent_email}")
                if response.status_code != 201:
                    print(f"Hoopla Error Detail: {response.text}")
            except Exception as e:
                print(f"Connection Error: {e}")

    # Return 200 so Dialpad knows we received it
    return jsonify({"status": "processed"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

