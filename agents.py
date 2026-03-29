import os
from crewai import Agent, Task, Crew, Process
from langchain_groq import ChatGroq
from tools import find_nearest_cold_storage, send_sms_alert, generate_incident_report
from dotenv import load_dotenv

load_dotenv()

free_llm = ChatGroq(
    temperature=0, 
    groq_api_key=os.getenv("GROQ_API_KEY"), 
    model_name="llama-3.3-70b-versatile"
)

diagnostician = Agent(
    role='Thermodynamic Diagnostician',
    goal='Calculate time-to-spoilage based on current temperature and decay rate.',
    backstory='Expert in pharmaceutical thermodynamics.',
    verbose=True,
    allow_delegation=False,
    llm=free_llm
)

dispatcher = Agent(
    role='Emergency Dispatcher',
    goal='Find a safe harbor cold storage and alert the driver.',
    backstory='Veteran logistics dispatcher working in high-pressure scenarios.',
    verbose=True,
    allow_delegation=False,
    tools=[find_nearest_cold_storage, send_sms_alert],
    llm=free_llm
)

compliance_officer = Agent(
    role='FDA Compliance Officer',
    goal='Generate a compliance incident report.',
    backstory='Strict regulatory auditor ensuring CDSCO and FDA compliance.',
    verbose=True,
    allow_delegation=False,
    tools=[generate_incident_report],
    llm=free_llm
)

def kickoff_recovery_process(truck_id, lat, lng, current_temp, decay_rate, cargo):
    task1 = Task(
        description=f"Truck {truck_id} carrying {cargo} failed. Temp is {current_temp}C, Decay is {decay_rate}C/min. Max safe temp is 8C. Calculate the exact minutes until the payload hits 8C. Return ONLY the integer number of minutes.",
        expected_output="An integer representing minutes to spoil.",
        agent=diagnostician
    )
    
    task2 = Task(
        # 🚨🚨🚨 REPLACE THE NUMBER BELOW WITH YOUR VERIFIED TWILIO PHONE NUMBER! 🚨🚨🚨
        # Ensure you include your country code (e.g., +91 for India)
        description=f"Using the minutes calculated by the Diagnostician, use the Map tool to find a cold storage near lat: {lat}, lng: {lng}. Then, use the SMS tool to send an alert to your driver at '+918378994271' with the routing info.",
        expected_output="A confirmation of the route found and SMS sent.",
        agent=dispatcher
    )
    
    task3 = Task(
        description=f"Use the PDF tool to generate a compliance report for {truck_id} carrying {cargo}. The temperature reached {current_temp}C. Briefly describe the safe harbor routing action taken by the dispatcher.",
        expected_output="The filename of the generated PDF.",
        agent=compliance_officer
    )

    recovery_crew = Crew(
        agents=[diagnostician, dispatcher, compliance_officer],
        tasks=[task1, task2, task3],
        process=Process.sequential
    )
    
    return recovery_crew.kickoff()