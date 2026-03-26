import pyttsx3
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
from datetime import datetime

from agents import kickoff_recovery_process

app = FastAPI(title="ThermaChain AI Webhook")

try:
    voice_engine = pyttsx3.init()
except:
    voice_engine = None

try:
    manifest_df = pd.read_csv("fleet_manifest.csv")
except:
    manifest_df = pd.DataFrame()

handled_emergencies = set()

# NEW: Accepting weather and decay rate
class TelemetryPayload(BaseModel):
    truck_id: str
    timestamp: str
    gps_lat: float
    gps_long: float
    internal_temp_C: float
    external_temp_C: float  
    decay_rate: float       
    compressor_status: str

@app.post("/telemetry")
async def receive_telemetry(data: TelemetryPayload):
    
    # Save live status for Streamlit
    with open("live_status.json", "w") as f:
        json.dump(data.model_dump(), f)

    # AUTO-RESET: If the truck is fixed/new, clear the memory lock
    if data.compressor_status == "OK":
        if data.truck_id in handled_emergencies:
            handled_emergencies.remove(data.truck_id)
        return {"status": "nominal"}

    if data.truck_id in handled_emergencies:
        return {"status": "ignored"}

    truck_data = manifest_df[manifest_df['truck_id'] == data.truck_id]
    if truck_data.empty: return {"status": "error"}
    
    max_safe_temp = float(truck_data.iloc[0]['max_safe_temp'])
    cargo = truck_data.iloc[0]['cargo_type']

    if data.compressor_status == "FAILED" or data.internal_temp_C > max_safe_temp:
        handled_emergencies.add(data.truck_id)
        print(f"\n🚨 CRITICAL ALERT: {data.truck_id} carrying {cargo} failing!")
        
        if voice_engine:
            voice_engine.say(f"Alert! Failure in {data.truck_id}.")
            voice_engine.runAndWait()
        
        # PASSING WEATHER DATA TO THE AI
        kickoff_recovery_process(
            data.truck_id, 
            truck_data.iloc[0]['driver_phone'], 
            cargo, 
            data.internal_temp_C, 
            max_safe_temp,
            data.gps_lat,   
            data.gps_long,
            data.external_temp_C, 
            data.decay_rate       
        )
        return {"status": "alert_triggered"}
    
    return {"status": "nominal"}