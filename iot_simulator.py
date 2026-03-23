import requests
import time
from datetime import datetime

# The URL of your local FastAPI server
WEBHOOK_URL = "http://localhost:8000/telemetry"

# Initial healthy truck state
payload = {
    "truck_id": "TRK-002", # This truck carries mRNA vaccines (Max temp -15.0C)
    "timestamp": "",
    "gps_lat": 28.7041,
    "gps_long": 77.1025,
    "internal_temp_C": -20.0,
    "compressor_status": "ONLINE"
}

print("Starting Edge IoT Simulator...")
print("Simulating healthy transit for 10 seconds, then triggering a failure.")

for i in range(10):
    payload["timestamp"] = datetime.utcnow().isoformat()
    
    # After 3 pings (approx 9 seconds), simulate a mechanical failure
    if i == 3:
        print("\n💥 SIMULATING COMPRESSOR FAILURE 💥\n")
        payload["compressor_status"] = "FAILED"
    
    # If the compressor is failed, the temperature starts rising rapidly
    if payload["compressor_status"] == "FAILED":
        payload["internal_temp_C"] += 2.5  # Temp goes up by 2.5 degrees every 3 seconds

    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        print(f"Sent: {payload['internal_temp_C']}°C | Server Response: {response.json()['status']}")
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the FastAPI server. Is it running?")
    
    time.sleep(3) # Wait 3 seconds before the next ping