from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
from datetime import datetime

# ---> THIS IS THE CRUCIAL CONNECTION TO YOUR AI <---
from agents import kickoff_recovery_process

app = FastAPI(title="ThermaChain AI Webhook")

# Load the digital manifest (our database)
try:
    manifest_df = pd.read_csv("fleet_manifest.csv")
except FileNotFoundError:
    print("Error: fleet_manifest.csv not found!")
    manifest_df = pd.DataFrame()

# Define the expected JSON payload from the truck
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

    # 2. The "Dumb Filter" Logic
    if data.compressor_status == "FAILED" or data.internal_temp_C > max_safe_temp:
        print(f"🚨 CRITICAL ALERT: {data.truck_id} carrying {cargo} is failing!")
        print(f"   Current Temp: {data.internal_temp_C}°C (Max Allowed: {max_safe_temp}°C)")
        
        # ---> WAKE UP THE AI AGENTS <---
        driver_phone = truck_data.iloc[0]['driver_phone']
        kickoff_recovery_process(data.truck_id, driver_phone, cargo, data.internal_temp_C, max_safe_temp)
        
        return {"status": "alert_triggered", "message": "AI Agents Dispatched"}
    
    # If everything is fine, do nothing and save API costs
    return {"status": "nominal", "message": "Data logged successfully"}