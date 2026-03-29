import streamlit as st
import pydeck as pdk
import json
import time
import os

# Set UI Configuration
st.set_page_config(layout="wide", page_title="ThermaChain Command Center", page_icon="🧊")

# Custom CSS for that dark-mode enterprise look
st.markdown("""
    <style>
    .metric-container { background-color: #1E1E1E; padding: 20px; border-radius: 10px; border: 1px solid #333; }
    .alert-box { background-color: #4A1919; color: #FF4B4B; padding: 15px; border-radius: 5px; border-left: 5px solid #FF4B4B; margin-top: 20px;}
    </style>
""", unsafe_allow_html=True)

st.title("🧊 ThermaChain: 3D Command Center")

# Placeholder for real-time updates
metrics_placeholder = st.empty()
map_placeholder = st.empty()

def load_json(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

while True:
    # 1. Read the live state from the simulator and the AI tools
    truck_data = load_json("live_status.json")
    routing_data = load_json("target_location.json")

    if truck_data:
        # Safely extract variables
        truck_id = truck_data.get("truck_id", "UNKNOWN")
        temp = truck_data.get("internal_temp_C", 0.0)
        decay = truck_data.get("decay_rate", 0.0)
        status = truck_data.get("compressor_status", "OK")
        lat = truck_data.get("gps_lat", 22.2604)
        lng = truck_data.get("gps_long", 84.8536)

        # 2. Render Metrics Dashboard
        with metrics_placeholder.container():
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Active Edge Node", truck_id)
            col2.metric("Internal Temp", f"{temp} °C", delta=f"+{decay}°/min", delta_color="inverse")
            
            if status == "FAILED":
                col3.metric("Compressor", "FAILED 🚨")
                col4.metric("AI Agents", "DISPATCHED 🤖")
                st.markdown("<div class='alert-box'>🚨 CRITICAL ALERT: Payload degrading. Executing AI Swarm rescue protocol.</div>", unsafe_allow_html=True)
            else:
                col3.metric("Compressor", "NOMINAL ✅")
                col4.metric("AI Agents", "STANDBY")

        # 3. Build the 3D Map Layers
        layers = []
        
        # Layer 1: The Truck (Always visible)
        truck_layer = pdk.Layer(
            "ScatterplotLayer",
            data=[{"position": [lng, lat], "color": [255, 75, 75] if status == "FAILED" else [75, 255, 75]}],
            get_position="position",
            get_color="color",
            get_radius=400,
            pickable=True
        )
        layers.append(truck_layer)

        # Layer 2: The Route & Destination (Visible only if AI has rescued it)
        if routing_data and status == "FAILED":
            dest_lat = routing_data.get("dest_lat")
            dest_lng = routing_data.get("dest_lng")
            route_path = routing_data.get("route_path", [])

            # The glowing street-level path
            if route_path:
                path_layer = pdk.Layer(
                    "PathLayer",
                    data=[{"path": route_path}],
                    get_path="path",
                    get_color=[50, 150, 255, 255], # Neon Blue line
                    width_scale=20,
                    width_min_pixels=5,
                    get_width=5,
                )
                layers.append(path_layer)

            # The Hospital Marker
            dest_layer = pdk.Layer(
                "ScatterplotLayer",
                data=[{"position": [dest_lng, dest_lat]}],
                get_position="position",
                get_color=[50, 150, 255],
                get_radius=500,
            )
            layers.append(dest_layer)

        # 4. Render the PyDeck Map
        with map_placeholder.container():
            st.pydeck_chart(pdk.Deck(
                map_style=None, # Bypass Mapbox API Block!
                initial_view_state=pdk.ViewState(latitude=lat, longitude=lng, zoom=12, pitch=45),
                layers=layers
            ))

    time.sleep(2) # Refresh UI every 2 seconds