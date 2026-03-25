import pyttsx3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
from datetime import datetime

from agents import kickoff_recovery_process

app = FastAPI(title="ThermaChain AI Webhook")

# Initialize the voice engine for the loud presentation alarm
try:
    voice_engine = pyttsx3.init()
except Exception as e:
    print(f"Warning: Voice engine failed to initialize: {e}")
    voice_engine = None

# Load the digital manifest (our database)
try:
    manifest_df = pd.read_csv("fleet_manifest.csv")
except FileNotFoundError:
    print("Error: fleet_manifest.csv not found!")
    manifest_df = pd.DataFrame()

# --- NEW: ALERT MEMORY LOCK ---
# This dictionary remembers which trucks are currently in an active failure state.
# It prevents the AI from being triggered 100 times for the same broken truck.
active_alerts = {}

# Define the expected JSON payload from the edge-device
class TelemetryPayload(BaseModel):
    truck_id: str
    timestamp: str
    gps_lat: float
    gps_long: float
    internal_temp_C: float
    compressor_status: str

@app.post("/telemetry")
async def receive_telemetry(data: TelemetryPayload):
    # 1. Look up the specific truck in our database
    truck_data = manifest_df[manifest_df['truck_id'] == data.truck_id]
    
    if truck_data.empty:
        raise HTTPException(status_code=404, detail="Truck ID not found in manifest")
    
    max_safe_temp = float(truck_data.iloc[0]['max_safe_temp'])
    cargo = truck_data.iloc[0]['cargo_type']
    
    print(f"[{data.timestamp}] Ping from {data.truck_id} | Temp: {data.internal_temp_C}°C | Compressor: {data.compressor_status}")

    # 2. The "Smart Filter" Logic
    if data.compressor_status == "FAILED" or data.internal_temp_C > max_safe_temp:
        
        # ---> CHECK THE MEMORY LOCK <---
        if data.truck_id in active_alerts:
            # We already triggered the AI for this truck. Ignore the duplicate ping.
            return {"status": "alert_active", "message": "Duplicate alert suppressed"}
        
        # If it's not locked, this is a NEW failure! Lock it down.
        active_alerts[data.truck_id] = True
        
        print(f"\n🚨 CRITICAL ALERT: {data.truck_id} carrying {cargo} is failing!")
        print(f"   Current Temp: {data.internal_temp_C}°C (Max Allowed: {max_safe_temp}°C)")
        
        # ---> THE LOUD ALARM <---
        if voice_engine:
            voice_engine.say(f"Critical Alert! Compressor failure detected in {data.truck_id}. Initiating AI emergency protocol.")
            voice_engine.runAndWait()
        
        # ---> WAKE UP THE AI AGENTS <---
        driver_phone = truck_data.iloc[0]['driver_phone']
        
        kickoff_recovery_process(
            data.truck_id, 
            driver_phone, 
            cargo, 
            data.internal_temp_C, 
            max_safe_temp,
            data.gps_lat,   
            data.gps_long   
        )
        
        return {"status": "alert_triggered", "message": "AI Agents Dispatched"}
    
    else:
        # ---> RESET THE LOCK IF THE TRUCK IS FIXED <---
        if data.truck_id in active_alerts:
            print(f"\n✅ SYSTEM NOMINAL: {data.truck_id} has recovered. Resetting alert memory.")
            del active_alerts[data.truck_id]
            
        return {"status": "nominal", "message": "Data logged successfully"}