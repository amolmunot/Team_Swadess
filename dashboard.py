import streamlit as st
import pandas as pd
import pydeck as pdk
import json
import time
import os

st.set_page_config(page_title="ThermaChain Command Center", layout="wide")
st.title("🧊 ThermaChain: 3D Command Center")
st.markdown("---")

try:
    with open("live_status.json", "r") as f:
        data = json.load(f)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Active Edge Node", data["truck_id"])
    
    is_failed = data["compressor_status"] == "FAILED"
    
    if not is_failed:
        col2.metric("Internal Temp", f"{data['internal_temp_C']} °C", delta="Nominal", delta_color="normal")
        col3.metric("Compressor", "ONLINE")
        col4.metric("AI Agents", "Standing By")
    else:
        decay_rate = data.get('decay_rate', 'Unknown')
        col2.metric("Internal Temp", f"{data['internal_temp_C']} °C", delta=f"+{decay_rate}°/min", delta_color="inverse")
        col3.metric("Compressor", "FAILED 🚨")
        col4.metric("AI Agents", "DISPATCHED 🤖")
        st.error(f"🚨 CRITICAL ALERT: Payload degrading. Driver notified via WhatsApp.")

    # --- THE 3D MAP ---
    truck_lat, truck_lng = data["gps_lat"], data["gps_long"]
    layers = []

    # 1. The Truck Dot
    layers.append(pdk.Layer(
        "ScatterplotLayer",
        data=[{"position": [truck_lng, truck_lat], "color": [255, 0, 0] if is_failed else [0, 255, 0]}],
        get_position="position", get_color="color", get_radius=300, pickable=True
    ))

    # 2. The Routing Arc & Destination (Appears when AI finishes!)
    if is_failed and os.path.exists("target_location.json"):
        with open("target_location.json", "r") as f:
            target = json.load(f)
        
        # Draw Hospital Dot
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=[{"position": [target["lng"], target["lat"]], "color": [0, 150, 255]}],
            get_position="position", get_color="color", get_radius=400
        ))
        
        # Draw 3D Arc from Truck to Hospital
        layers.append(pdk.Layer(
            "ArcLayer",
            data=[{"source": [truck_lng, truck_lat], "target": [target["lng"], target["lat"]]}],
            get_source_position="source", get_target_position="target",
            get_source_color=[255, 0, 0], get_target_color=[0, 150, 255], get_width=5
        ))

    # Render Map
    st.pydeck_chart(pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(latitude=truck_lat, longitude=truck_lng, zoom=12, pitch=45),
        layers=layers
    ))

except FileNotFoundError:
    st.warning("📡 Waiting for Edge Telemetry Connection...")
except json.JSONDecodeError:
    pass 

time.sleep(2)
st.rerun()