import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from twilio.rest import Client

# --- TOOL 1: Rerouting & Maps ---
def find_nearest_cold_storage(time_to_spoil_mins: int) -> str:
    """Scans for the nearest certified cold storage within the safe time window."""
    print(f"\n🌍 [TOOL: Map] Scanning for facilities within a {time_to_spoil_mins} minute radius...")
    
    # For a reliable live demo, we use a mocked spatial database
    facilities = [
        {"name": "Apollo Cold Storage (Sector 4)", "eta_mins": 22},
        {"name": "BlueDart Pharma Hub", "eta_mins": 55}
    ]
    
    for facility in facilities:
        if facility["eta_mins"] < time_to_spoil_mins:
            print(f"   -> FOUND: {facility['name']} is {facility['eta_mins']} mins away.")
            return f"SUCCESS: Reroute to {facility['name']}. ETA: {facility['eta_mins']} mins."
            
    return "FAILURE: No facilities within safe range. Total payload loss imminent."

# --- TOOL 2: TWILIO AI VOICE CALL ---
def send_sms_alert(phone_number: str, message: str) -> str:
    """Makes an automated phone call to the driver using Twilio Voice."""
    print(f"\n📞 [TOOL: Alert] Initiating AI Voice Call to {phone_number}...")
    
    try:
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        from_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        if account_sid and auth_token:
            client = Client(account_sid, auth_token)
            
            # This XML tells Twilio to create a voice and read the AI's instructions
            twiml_script = f"""
            <Response>
                <Say voice="Polly.Joanna" language="en-US">
                    Critical Alert from Therma Chain AI. 
                    Cooling unit failure detected on your vehicle. 
                    Please listen carefully to your rerouting instructions.
                    {message}.
                    I repeat, please proceed to the safe harbor immediately. Goodbye.
                </Say>
            </Response>
            """
            
            # Trigger the phone call
            call = client.calls.create(
                twiml=twiml_script,
                to=phone_number,
                from_=from_number
            )
            
            print("   -> TWILIO SUCCESS: Phone is ringing right now!")
            return "Driver called and notified successfully."
        else:
            return "Failed: Twilio credentials missing from .env file."
            
    except Exception as e:
        return f"Failed to make call: {str(e)}"

# --- TOOL 3: Regulatory Guardrail (PDF Generation) ---
def generate_incident_report(truck_id: str, cargo: str, reached_temp: float, action_taken: str) -> str:
    """Generates a CDSCO/FDA compliant PDF incident report for auditors."""
    print(f"\n🏛️ [TOOL: Compliance] Generating immutable PDF Report for {truck_id}...")
    
    # Create a unique filename based on the current time
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"Incident_Report_{truck_id}_{timestamp}.pdf"
    
    # Draw the PDF Document
    c = canvas.Canvas(filename, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "MANDATORY COMPLIANCE INCIDENT REPORT (CDSCO/FDA)")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, 710, f"Date/Time of Incident: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(50, 690, f"Vehicle Identification: {truck_id}")
    c.drawString(50, 670, f"Payload Cargo: {cargo}")
    
    # Draw a red line separator
    c.setStrokeColorRGB(1, 0, 0)
    c.line(50, 650, 550, 650) 
    
    c.drawString(50, 620, "CRITICAL INCIDENT DETAILS:")
    c.drawString(50, 600, f"- Temperature Reached: {reached_temp}°C (Exceeded Safe Limits)")
    c.drawString(50, 580, "- Disruption Type: Cooling Unit Compressor Failure")
    
    c.drawString(50, 540, "AUTONOMOUS AI ACTION TAKEN:")
    
    # Text wrapping for the action taken
    textobject = c.beginText(50, 520)
    textobject.setFont("Helvetica", 11)
    textobject.textLines(action_taken)
    c.drawText(textobject)
    
    c.save()
    print(f"   -> PDF SAVED: Look in your folder for '{filename}'")
    return f"Report generated successfully: {filename}"