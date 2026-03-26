import os
import json
import googlemaps
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from twilio.rest import Client

# --- TOOL 1: REAL GOOGLE MAPS REROUTING (WITH CLICKABLE LINK & 3D MAP PIN) ---
def find_nearest_cold_storage(time_to_spoil_mins: int, lat: float, lng: float) -> str:
    """Uses Google Maps to find the nearest cold storage within the safe time window."""
    print(f"\n🌍 [TOOL: Map] Scanning Google Maps near ({lat}, {lng}) for facilities within {time_to_spoil_mins} mins...")
    
    gmaps_key = os.getenv('GMAPS_API_KEY')
    if not gmaps_key:
        return "FAILURE: Google Maps API key missing."
        
    gmaps = googlemaps.Client(key=gmaps_key)
    truck_location = (lat, lng)
    
    try:
        # 1. Search for nearby medical facilities
        places_result = gmaps.places_nearby(
            location=truck_location, 
            radius=50000, 
            keyword="hospital OR cold storage OR pharmaceutical warehouse"
        )
        
        if not places_result.get('results'):
            return "FAILURE: No facilities found in the region."

        # 2. Extract top 3 closest places
        candidates = places_result['results'][:3]
        destinations = [place['geometry']['location'] for place in candidates]
        
        # 3. Get live traffic ETAs
        matrix = gmaps.distance_matrix(
            origins=[truck_location],
            destinations=destinations,
            mode="driving",
            departure_time=datetime.now()
        )
        
        # 4. Find the best match
        for i, element in enumerate(matrix['rows'][0]['elements']):
            if element['status'] == 'OK':
                eta_mins = int(element['duration']['value'] / 60) 
                facility_name = candidates[i]['name']
                facility_address = candidates[i].get('vicinity', 'Address not found')
                
                # OFFICIAL UNIVERSAL MAPS LINK
                dest_lat = candidates[i]['geometry']['location']['lat']
                dest_lng = candidates[i]['geometry']['location']['lng']
                maps_url = f"https://www.google.com/maps/search/?api=1&query={dest_lat},{dest_lng}"
                
                if eta_mins <= time_to_spoil_mins:
                    print(f"   -> FOUND: {facility_name} is {eta_mins} mins away (Safe!)")
                    
                    # ---> NEW: DROP THE PIN FOR THE 3D DASHBOARD <---
                    try:
                        with open("target_location.json", "w") as f:
                            json.dump({"lat": dest_lat, "lng": dest_lng, "name": facility_name}, f)
                    except Exception as e:
                        print(f"   -> Warning: Could not save map pin data: {e}")
                    # ---------------------------------------------
                    
                    return f"SUCCESS: Reroute to {facility_name} at {facility_address}. Live ETA: {eta_mins} mins. Navigation Link: {maps_url}"
                else:
                    print(f"   -> REJECTED: {facility_name} is {eta_mins} mins away (Too far).")

        return "FAILURE: Facilities found, but all are too far away. Payload loss imminent."
        
    except Exception as e:
        return f"Google Maps API Error: {str(e)}"

# --- TOOL 2: THE ULTIMATE HYBRID (WHATSAPP + TWILIO CALL) ---
def send_sms_alert(phone_number: str, message: str) -> str:
    """Sends a WhatsApp message with routing details, then calls the phone via Twilio."""
    print(f"\n📞 [TOOL: Alert] Dispatching WhatsApp Alert and Voice Call to {phone_number}...")
    
    try:
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        # Verify this is your exact sandbox number from the Twilio Console
        twilio_whatsapp_number = "whatsapp:+14155238886" 
        formatted_driver_phone = f"whatsapp:{phone_number}"
        standard_twilio_number = os.getenv('TWILIO_PHONE_NUMBER')

        if account_sid and auth_token:
            client = Client(account_sid, auth_token)
            
            # 1. SEND WHATSAPP MESSAGE
            whatsapp_body = (
                "🚨 *THERMACHAIN CRITICAL ALERT* 🚨\n\n"
                "🧊 *Status:* Cooling Unit Failure Detected.\n"
                "📍 *Action Required:* Immediate Reroute\n\n"
                "*AI Routing Instructions:*\n"
                f"{message}"
            )
            
            client.messages.create(
                body=whatsapp_body,
                from_=twilio_whatsapp_number,
                to=formatted_driver_phone
            )
            print("   -> 💬 WHATSAPP SUCCESS: Rich-text location sent to phone!")
            
            # 2. MAKE VOICE CALL
            twiml_script = f"""
            <Response>
                <Say voice="Polly.Joanna" language="en-US">
                    Critical Alert from Therma Chain AI. 
                    Cooling unit failure detected on your vehicle. 
                    I have just sent a WhatsApp message to your phone with the exact location of the nearest safe cold storage. 
                    Please check your screen and proceed immediately. Goodbye.
                </Say>
            </Response>
            """
            client.calls.create(
                twiml=twiml_script,
                to=phone_number,
                from_=standard_twilio_number
            )
            print("   -> 📞 VOICE SUCCESS: Phone is ringing right now!")
            
            return "Driver was sent a WhatsApp alert AND called successfully."
        else:
            return "Failed: Twilio credentials missing from .env file."
            
    except Exception as e:
        return f"Failed to alert driver: {str(e)}"

# --- TOOL 3: Regulatory Guardrail (PDF Generation) ---
def generate_incident_report(truck_id: str, cargo: str, reached_temp: float, action_taken: str) -> str:
    """Generates a CDSCO/FDA compliant PDF incident report for auditors."""
    print(f"\n🏛️ [TOOL: Compliance] Generating immutable PDF Report for {truck_id}...")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"Incident_Report_{truck_id}_{timestamp}.pdf"
    
    c = canvas.Canvas(filename, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "MANDATORY COMPLIANCE INCIDENT REPORT (CDSCO/FDA)")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, 710, f"Date/Time of Incident: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(50, 690, f"Vehicle Identification: {truck_id}")
    c.drawString(50, 670, f"Payload Cargo: {cargo}")
    
    c.setStrokeColorRGB(1, 0, 0)
    c.line(50, 650, 550, 650) 
    
    c.drawString(50, 620, "CRITICAL INCIDENT DETAILS:")
    c.drawString(50, 600, f"- Temperature Reached: {reached_temp}°C (Exceeded Safe Limits)")
    c.drawString(50, 580, "- Disruption Type: Cooling Unit Compressor Failure")
    
    c.drawString(50, 540, "AUTONOMOUS AI ACTION TAKEN:")
    
    textobject = c.beginText(50, 520)
    textobject.setFont("Helvetica", 11)
    textobject.textLines(str(action_taken))
    c.drawText(textobject)
    
    c.save()
    print(f"   -> PDF SAVED: Look in your folder for '{filename}'")
    return f"Report generated successfully: {filename}"