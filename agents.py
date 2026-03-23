import os
from crewai import Agent, Task, Crew, Process
from langchain.tools import tool
from dotenv import load_dotenv

from langchain_groq import ChatGroq 

from tools import find_nearest_cold_storage, send_sms_alert, generate_incident_report

load_dotenv()

free_llm = ChatGroq(
    temperature=0, 
    groq_api_key=os.getenv("GROQ_API_KEY"),   
    model_name="llama-3.3-70b-versatile"
)

# --- 1. Wrap your functions into AI Tools ---
@tool("Find Nearest Cold Storage")
def tool_find_storage(time_to_spoil_mins: int) -> str:
    """Use this tool to find a safe cold storage facility within the spoilage time limit."""
    return find_nearest_cold_storage(time_to_spoil_mins)

@tool("Send SMS Alert")
def tool_send_sms(phone_number: str, message: str) -> str:
    """Use this tool to send emergency routing instructions to the driver's phone."""
    return send_sms_alert(phone_number, message)

@tool("Generate Compliance PDF")
def tool_generate_pdf(truck_id: str, cargo: str, reached_temp: float, action_taken: str) -> str:
    """Use this tool to generate the mandatory CDSCO/FDA incident report PDF."""
    return generate_incident_report(truck_id, cargo, reached_temp, action_taken)


# --- 2. Define the System Trigger ---
def kickoff_recovery_process(truck_id: str, driver_phone: str, cargo: str, current_temp: float, max_safe_temp: float):
    print("\n" + "="*50)
    print(f"🤖 CREW AI ACTIVATED: EMERGENCY PROTOCOL FOR {truck_id}")
    print("="*50 + "\n")

    # --- 3. Create the Agents ---
    diagnostician = Agent(
        role='Senior Thermal Logistics Analyst',
        goal='Calculate thermal decay and time-to-spoilage for medical cargo.',
        backstory='You are an expert in thermodynamics and pharmaceutical safety. You analyze temperature anomalies to prevent payload loss.',
        verbose=True,
        allow_delegation=False,
        llm=free_llm # 3. GAVE THE AGENT THE GROQ BRAIN
    )

    dispatcher = Agent(
        role='Emergency Fleet Dispatcher',
        goal='Autonomously reroute failing trucks to the nearest cold storage and notify the driver.',
        backstory='You are a hyper-efficient logistics coordinator. You never panic. You find the closest safe harbor and text the driver immediately.',
        tools=[tool_find_storage, tool_send_sms],
        verbose=True,
        allow_delegation=False,
        llm=free_llm # 3. GAVE THE AGENT THE GROQ BRAIN
    )

    compliance_officer = Agent(
        role='CDSCO Pharmaceutical Compliance Officer',
        goal='Audit emergency logistics events and generate immutable legal PDF reports.',
        backstory='You are a strict regulatory auditor. You ensure every temperature excursion is documented perfectly for the FDA and CDSCO.',
        tools=[tool_generate_pdf],
        verbose=True,
        allow_delegation=False,
        llm=free_llm # 3. GAVE THE AGENT THE GROQ BRAIN
    )

    # --- 4. Define the Tasks ---
    task1 = Task(
        description=f"Truck {truck_id} carrying {cargo} has suffered a compressor failure. Current temp is {current_temp}°C (Max safe is {max_safe_temp}°C). The temperature is rising by 0.5°C per minute. Calculate exactly how many minutes we have until the cargo is destroyed.",
        expected_output="A single integer representing the minutes remaining until spoilage.",
        agent=diagnostician
    )

    task2 = Task(
        description=f"Take the minutes remaining from the Diagnostician. Use your 'Find Nearest Cold Storage' tool to find a facility. Once found, use your 'Send SMS Alert' tool to text the driver at {driver_phone} with the new route.",
        expected_output="A confirmation string detailing the chosen facility and confirming the SMS was sent.",
        agent=dispatcher
    )

    task3 = Task(
        description=f"Review the crisis. Use your 'Generate Compliance PDF' tool to draft a report for Truck {truck_id} carrying {cargo}. Note the peak temperature of {current_temp}°C and describe the rerouting action taken by the Dispatcher.",
        expected_output="The final file path of the generated PDF report.",
        agent=compliance_officer
    )

    # --- 5. Assemble the Crew and Launch ---
    recovery_crew = Crew(
        agents=[diagnostician, dispatcher, compliance_officer],
        tasks=[task1, task2, task3],
        process=Process.sequential 
    )

    # Start the autonomous process
    result = recovery_crew.kickoff()
    
    print("\n✅ INCIDENT RESOLVED. AGENTS STANDING DOWN.")
    return result
