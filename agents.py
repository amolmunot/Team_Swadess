import os
from crewai import Agent, Task, Crew, Process
from langchain.tools import tool
from dotenv import load_dotenv
from langchain_groq import ChatGroq 
from tools import find_nearest_cold_storage, send_sms_alert, generate_incident_report

load_dotenv()
free_llm = ChatGroq(temperature=0, groq_api_key=os.getenv("GROQ_API_KEY"), model_name="llama-3.3-70b-versatile")

@tool("Find Nearest Cold Storage")
def tool_find_storage(time_to_spoil_mins: int, lat: float, lng: float) -> str:
    """Finds the nearest hospital or cold storage within a given time limit using Google Maps."""
    return find_nearest_cold_storage(time_to_spoil_mins, lat, lng)

@tool("Send SMS Alert")
def tool_send_sms(phone_number: str, message: str) -> str:
    """Sends an emergency WhatsApp message and makes a voice call to the driver."""
    return send_sms_alert(phone_number, message)

@tool("Generate Compliance PDF")
def tool_generate_pdf(truck_id: str, cargo: str, reached_temp: float, action_taken: str) -> str:
    """Generates a mandatory FDA/CDSCO compliant PDF incident report."""
    return generate_incident_report(truck_id, cargo, reached_temp, action_taken)

# NEW: Accepting weather and decay rate
def kickoff_recovery_process(truck_id: str, driver_phone: str, cargo: str, current_temp: float, max_safe_temp: float, lat: float, lng: float, ext_temp: float, decay_rate: float):
    
    diagnostician = Agent(role='Senior Analyst', goal='Calculate spoilage time.', backstory='Expert in thermodynamics.', allow_delegation=False, llm=free_llm)
    dispatcher = Agent(role='Dispatcher', goal='Reroute trucks.', backstory='Logistics expert.', tools=[tool_find_storage, tool_send_sms], allow_delegation=False, llm=free_llm)
    compliance_officer = Agent(role='Compliance Officer', goal='Generate PDFs.', backstory='FDA Auditor.', tools=[tool_generate_pdf], allow_delegation=False, llm=free_llm)

    # NEW: AI now uses the dynamic external temperature and decay rate!
    task1 = Task(
        description=f"Truck {truck_id} carrying {cargo} has failed. Current temp is {current_temp}°C (Max safe: {max_safe_temp}°C). The outside weather is {ext_temp}°C, causing the internal temperature to rise by {decay_rate}°C per minute. Calculate exactly how many minutes until cargo is destroyed.",
        expected_output="A single integer representing the minutes remaining.",
        agent=diagnostician
    )

    task2 = Task(
        description=f"Take the minutes remaining. GPS: Lat {lat}, Lng {lng}. Find a storage facility. Then text the driver at {driver_phone}.",
        expected_output="Confirmation string.",
        agent=dispatcher
    )

    task3 = Task(
        description=f"Generate PDF for {truck_id} ({cargo}). Peak temp: {current_temp}°C. Describe action.",
        expected_output="PDF path.",
        agent=compliance_officer
    )

    recovery_crew = Crew(agents=[diagnostician, dispatcher, compliance_officer], tasks=[task1, task2, task3], process=Process.sequential)
    return recovery_crew.kickoff()