import time
import random
import requests
import pandas as pd
from datetime import datetime
import os

WEBHOOK_URL = "http://localhost:8000/telemetry"
CSV_FILE = "fleet_manifest.csv"

def run_simulator():
    print("🚛 Starting ThermaChain Enterprise Edge Simulator...")
    try:
        df = pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        print(f"❌ Error: '{CSV_FILE}' not found!")
        return

    # 1. Clear old map targets so we start with a fresh UI
    if os.path.exists("target_location.json"):
        os.remove("target_location.json")

    # 2. Pick a random truck & random weather
    target_truck = df.sample(1).iloc[0]
    truck_id = target_truck['truck_id']
    max_safe_temp = float(target_truck['max_safe_temp'])
    cargo = target_truck['cargo_type']
    
    ext_temp = random.uniform(35.0, 45.0) # Summer weather in India
    decay_rate = random.uniform(3.5, 4.5) # Degrees lost per minute

    print(f"\n==================================================")
    print(f"🎯 NEW ROUTE INITIALIZED: {truck_id} carrying {cargo}")
    print(f"🌦️ Outside Temp: {round(ext_temp,1)}°C | Decay Rate: {round(decay_rate,2)}°C/min")
    
    current_temp = max_safe_temp - random.uniform(2.0, 5.0) 
    compressor_status = "OK"
    
    # Base Coordinates (Rourkela)
    lat = 22.2604
    lng = 84.8536

    # Drive for a few pings, fail the compressor, let the AI respond, then STOP
    for iteration in range(1, 10):
        lat += random.uniform(-0.001, 0.001)
        lng += random.uniform(-0.001, 0.001)

        if iteration == 4:
            print(f"💥 {truck_id} COMPRESSOR FAILURE DETECTED!")
            compressor_status = "FAILED"
            
        if compressor_status == "FAILED":
            current_temp = max_safe_temp + random.uniform(0.5, 2.0)

        payload = {
            "truck_id": truck_id,
            "timestamp": datetime.now().isoformat(),
            "gps_lat": round(lat, 6),
            "gps_long": round(lng, 6),
            "internal_temp_C": round(current_temp, 2),
            "external_temp_C": round(ext_temp, 1),
            "decay_rate": round(decay_rate, 2),
            "compressor_status": compressor_status
        }

        try:
            requests.post(WEBHOOK_URL, json=payload)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 📡 Ping | Temp: {round(current_temp, 2)}°C | Status: {compressor_status}")
        except Exception:
            pass

        time.sleep(4) # Wait between GPS pings
        
    # Program breaks out of the loop and gracefully ends here.
    print(f"\n✅ Simulation Complete. AI Swarm has taken over.")
    print(f"🛑 Shutting down edge simulator.")

if __name__ == "__main__":
    run_simulator()