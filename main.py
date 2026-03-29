from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from agents import kickoff_recovery_process
import json

app = FastAPI(title="ThermaChain API")

class Telemetry(BaseModel):
    truck_id: str
    timestamp: str
    gps_lat: float
    gps_long: float
    internal_temp_C: float
    external_temp_C: float
    decay_rate: float
    compressor_status: str

# Memory Lock to prevent API spam
active_emergencies = set()

@app.post("/telemetry")
async def receive_telemetry(data: Telemetry, background_tasks: BackgroundTasks):
    
    # Save the latest ping for the 3D Dashboard to read
    try:
        with open("live_status.json", "w") as f:
            json.dump(data.dict(), f)
    except Exception:
        pass

    # Trigger the AI Swarm ONLY if a failure occurs and it hasn't been triggered yet
    if data.compressor_status == "FAILED" and data.truck_id not in active_emergencies:
        print(f"\n🚨 CRITICAL ALERT: {data.truck_id} failing! Locking state and waking AI Swarm...\n")
        active_emergencies.add(data.truck_id)
        
        # Determine cargo (simulated for the prompt)
        cargo_type = "Insulin" if "001" in data.truck_id else "Paracetamol"
        
        background_tasks.add_task(
            kickoff_recovery_process,
            data.truck_id, 
            data.gps_lat, 
            data.gps_long, 
            data.internal_temp_C, 
            data.decay_rate, 
            cargo_type
        )

    return {"status": "received"}