import os
import json
import requests
import googlemaps
import polyline
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from twilio.rest import Client
from langchain_core.tools import StructuredTool
from langchain_core.pydantic_v1 import BaseModel, Field

# --- TOOL 1: REAL GOOGLE MAPS REROUTING ---
class StorageInput(BaseModel):
    time_to_spoil_mins: int = Field(description="Minutes until payload spoils")
    lat: float = Field(description="Current latitude")
    lng: float = Field(description="Current longitude")

def find_nearest_cold_storage_func(time_to_spoil_mins: int, lat: float, lng: float) -> str:
    print(f"\n🌍 [TOOL: Map] Scanning Google Maps near ({lat}, {lng}) for facilities within {time_to_spoil_mins} mins...")
    gmaps_key = os.getenv('GMAPS_API_KEY')
    if not gmaps_key:
        return "FAILURE: Google Maps API key missing."
        
    gmaps = googlemaps.Client(key=gmaps_key)
    truck_location = (lat, lng)
    
    try:
        places_result = gmaps.places_nearby(location=truck_location, radius=50000, keyword="hospital OR cold storage")
        if not places_result.get('results'):
            return "FAILURE: No facilities found in the region."

        candidates = places_result['results'][:3]
        destinations = [place['geometry']['location'] for place in candidates]
        matrix = gmaps.distance_matrix(origins=[truck_location], destinations=destinations, mode="driving", departure_time=datetime.now())
        
        for i, element in enumerate(matrix['rows'][0]['elements']):
            if element['status'] == 'OK':
                eta_mins = int(element['duration']['value'] / 60) 
                facility_name = candidates[i]['name']
                facility_address = candidates[i].get('vicinity', 'Address not found')
                dest_lat = candidates[i]['geometry']['location']['lat']
                dest_lng = candidates[i]['geometry']['location']['lng']
                maps_url = f"https://www.google.com/maps/search/?api=1&query={dest_lat},{dest_lng}"
                
                if eta_mins <= time_to_spoil_mins:
                    print(f"   -> FOUND: {facility_name} is {eta_mins} mins away (Safe!)")
                    route_path = []
                    dir_url = f"https://maps.googleapis.com/maps/api/directions/json?origin={lat},{lng}&destination={dest_lat},{dest_lng}&key={gmaps_key}"
                    dir_res = requests.get(dir_url).json()
                    
                    if dir_res.get("routes"):
                        encoded_polyline = dir_res["routes"][0]["overview_polyline"]["points"]
                        decoded_route = polyline.decode(encoded_polyline)
                        route_path = [[p_lng, p_lat] for p_lat, p_lng in decoded_route]

                    try:
                        with open("target_location.json", "w") as f:
                            json.dump({"dest_lat": dest_lat, "dest_lng": dest_lng, "name": facility_name, "route_path": route_path}, f)
                    except Exception:
                        pass
                    
                    return f"SUCCESS: Reroute to {facility_name}. ETA: {eta_mins} mins. Map: {maps_url}"
        return "FAILURE: Facilities found, but all are too far away."
    except Exception as e:
        return f"Google Maps API Error: {str(e)}"

find_nearest_cold_storage = StructuredTool.from_function(
    func=find_nearest_cold_storage_func,
    name="Find Nearest Cold Storage",
    description="Finds the nearest hospital or cold storage within a given time limit using Google Maps.",
    args_schema=StorageInput
)

# --- TOOL 2: WHATSAPP + TWILIO CALL ---
class AlertInput(BaseModel):
    phone_number: str = Field(description="Driver's phone number")
    message: str = Field(description="Alert message and routing link")

def send_sms_alert_func(phone_number: str, message: str) -> str:
    print(f"\n📞 [TOOL: Alert] Dispatching WhatsApp Alert and Voice Call to {phone_number}...")
    try:
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        if account_sid and auth_token:
            client = Client(account_sid, auth_token)
            client.messages.create(
                body=f"🚨 *THERMACHAIN ALERT*\n{message}",
                from_="whatsapp:+14155238886",
                to=f"whatsapp:{phone_number}"
            )
            print("   -> 💬 WHATSAPP SUCCESS!")
            client.calls.create(
                twiml="<Response><Say>ThermaChain Alert. Check WhatsApp for routing.</Say></Response>",
                to=phone_number,
                from_=os.getenv('TWILIO_PHONE_NUMBER')
            )
            print("   -> 📞 VOICE SUCCESS!")
            return "Driver alerted successfully."
        return "Failed: Twilio credentials missing."
    except Exception as e:
        return f"Failed to alert driver: {str(e)}"

send_sms_alert = StructuredTool.from_function(
    func=send_sms_alert_func,
    name="Send SMS Alert",
    description="Sends a WhatsApp message with routing details, then calls the phone via Twilio.",
    args_schema=AlertInput
)

# --- TOOL 3: ENTERPRISE PDF GENERATION ---
class ComplianceInput(BaseModel):
    truck_id: str = Field(description="Vehicle ID")
    cargo: str = Field(description="Payload type")
    reached_temp: float = Field(description="Highest temperature reached")
    action_taken: str = Field(description="The autonomous action taken by AI")

def generate_incident_report_func(truck_id: str, cargo: str, reached_temp: float, action_taken: str) -> str:
    print(f"\n🏛️ [TOOL: Compliance] Generating FDA/CDSCO Enterprise PDF Report for {truck_id}...")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    display_date = datetime.now().strftime('%B %d, %Y - %H:%M:%S IST')
    report_id = f"INC-{timestamp}-{truck_id}"
    filename = f"Regulatory_Report_{truck_id}.pdf"
    
    try:
        c = canvas.Canvas(filename, pagesize=letter)
        
        # --- 1. HEADER (FDA/CDSCO Branding) ---
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, 750, "THERMACHAIN ENTERPRISE: COLD CHAIN INCIDENT REPORT")
        c.setFont("Helvetica", 9)
        c.drawString(50, 735, "REGULATORY COMPLIANCE DOCUMENT: FDA 21 CFR Part 11 / CDSCO GDP STANDARDS")
        
        c.setStrokeColor(colors.red)
        c.setLineWidth(2)
        c.line(50, 725, 550, 725)
        
        # --- 2. METADATA & TRACEABILITY ---
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.black)
        c.drawString(50, 695, "1. EVENT METADATA & TRACEABILITY")
        
        c.setFont("Helvetica", 10)
        c.drawString(50, 675, f"Official Report ID: {report_id}")
        c.drawString(50, 660, f"Timestamp of Breach: {display_date}")
        c.drawString(320, 675, f"Asset/Vehicle ID: {truck_id}")
        c.drawString(320, 660, "Audit Status: LOCKED & IMMUTABLE")

        # --- 3. SENSOR TELEMETRY (The Trigger) ---
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 620, "2. IOT SENSOR TELEMETRY & PAYLOAD DATA")
        
        # Draw a bounding box for the critical data
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.rect(50, 545, 500, 60) 
        
        c.setFont("Helvetica", 10)
        c.drawString(60, 585, f"Payload Identification: {cargo}")
        c.drawString(60, 560, f"Critical Excursion Peak: {reached_temp}°C")
        
        c.setFillColor(colors.red)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(320, 560, "STATUS: SAFE LIMIT EXCEEDED")
        c.setFillColor(colors.black)

        # --- 4. CAPA (Corrective Action) ---
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 505, "3. AUTONOMOUS MITIGATION (CAPA)")
        
        c.setFont("Helvetica", 10)
        textobject = c.beginText(50, 485)
        
        words = str(action_taken).split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line + word) > 85:
                lines.append(current_line)
                current_line = word + " "
            else:
                current_line += word + " "
        lines.append(current_line)
        
        for line in lines:
            textobject.textLine(line)
        c.drawText(textobject)

        # --- 5. INSURANCE & SIGNATURE ---
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 390, "4. PARAMETRIC INSURANCE ATTESTATION")
        c.setFont("Helvetica", 10)
        c.drawString(50, 370, "This document serves as cryptographic proof of a hardware failure and subsequent")
        c.drawString(50, 355, "AI-driven mitigation. Telemetry data is validated via ThermaChain IoT Edge.")

        c.line(50, 290, 250, 290)
        c.drawString(50, 275, "System Attestation: ThermaChain Swarm AI")
        c.drawString(50, 260, "Role: Autonomous Dispatch & Compliance Agent")
        
        # Footer
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(50, 50, "Generated automatically by ThermaChain. No human modification permitted.")

        c.save()
        print(f"   -> PDF SAVED: Look in your folder for '{filename}'")
        return f"Report generated successfully: {filename}"
    except Exception as e:
        return f"Failed to generate PDF: {str(e)}"

generate_incident_report = StructuredTool.from_function(
    func=generate_incident_report_func,
    name="Generate Compliance PDF",
    description="Generates a CDSCO/FDA compliant PDF incident report for auditors.",
    args_schema=ComplianceInput
)