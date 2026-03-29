# 🧊 ThermaChain: Autonomous AI Rerouting for Pharmaceutical Cold Chains

ThermaChain is an event-driven, multi-agent AI logistics platform built to stop medical cargo spoilage before it happens. By reading live IoT telemetry and crunching thermodynamic decay rates against real-time traffic, our AI swarm autonomously reroutes failing trucks to the nearest safe harbor. It also alerts drivers across multiple channels and generates immutable FDA/CDSCO compliance audits—all in under 5 seconds.

---

## 🏗️ Enterprise Architecture Stack

Here is how we broke down the system into five core layers:

1. **The Edge (IoT Telemetry):** `iot_simulator.py` acts as our refrigerated truck, streaming live GPS, internal temperature, and compressor health data.
2. **The Nervous System (API & State):** `main.py` runs a FastAPI webhook equipped with Alert Deduplication (Memory Locks) to handle fleet-wide emergencies without spamming our APIs.
3. **The Brain (CrewAI Swarm):** `agents.py` uses Llama-3 (via Groq) to calculate the exact time-to-spoilage, execute the routing logic, and audit the event.
4. **Omnichannel Execution (Tools):** `tools.py` gives our AI hands in the real world. It integrates the Google Maps Places & Directions APIs, Twilio Programmable Voice & WhatsApp, and ReportLab for dynamic PDF generation.
5. **3D Command Center (UI):** `dashboard.py` uses Streamlit and PyDeck to render a live, Mapbox-bypassing 3D spatial routing map.

---

## ⚙️ Prerequisites

What you'll need before getting started:

* **Python 3.9+**
* **Recommended Python Version: Python 3.10.x or 3.11.x** *(Python 3.12+ may have strict package dependency conflicts with some AI libraries).*
* API Keys for the following services:
  * Groq (For Llama-3 LLM Inference)
  * Google Maps Platform (Places & Directions APIs)
  * Twilio (Programmable SMS/WhatsApp & Voice)

---

## 🔑 API Key Generation Guide

To run the AI agents and communication tools, you must provision free API keys for the following three services:

### 1. Groq (Llama-3 AI Engine)
* Go to the [Groq Cloud Console](https://console.groq.com/).
* Create a free account.
* Navigate to **API Keys** on the left menu.
* Click **Create API Key**, copy the string, and paste it into your `.env` file as `GROQ_API_KEY`.

### 2. Google Maps Platform (Routing & Places)
* Go to the [Google Cloud Console](https://console.cloud.google.com/).
* Create a New Project.
* Go to **APIs & Services > Library**.
* Search for and **Enable** these two specific APIs: 
  * *Places API (New or Legacy)*
  * *Directions API*
* Go to **Credentials > Create Credentials > API Key**. Copy this into your `.env` file as `GMAPS_API_KEY`.

### 3. Twilio (Voice Calls & WhatsApp)
* Go to [Twilio](https://console.twilio.com/) and sign up for a free trial.
* On your console dashboard, click **Get a Trial Phone Number**.
* Copy the **Account SID**, **Auth Token**, and your new **Twilio Phone Number** into your `.env` file.
* *For WhatsApp:* Navigate to **Messaging > Try it out > Send a WhatsApp message**. Follow the instructions to join the Twilio Sandbox by sending a code from your personal phone to their sandbox number.

---


## 🚀 Setup & Installation

### 1. Clone the Repository
git clone https://github.com/YOUR_USERNAME/thermachain.git
cd thermachain

### 2. Create a Virtual Environment
python -m venv venv

# For Windows:
venv\Scripts\activate

# For Mac/Linux:
source venv/bin/activate

### 3. Install Dependencies
pip install fastapi uvicorn crewai langchain-core langchain-groq streamlit pydeck polyline reportlab twilio googlemaps pandas requests

### 4. Configure Environment Variables
Create a file named `.env` in your root folder and drop your API keys in:

GROQ_API_KEY="gsk_your_groq_key_here"
GMAPS_API_KEY="AIza_your_google_maps_key_here"
TWILIO_ACCOUNT_SID="AC_your_twilio_sid_here"
TWILIO_AUTH_TOKEN="your_twilio_auth_token_here"
TWILIO_PHONE_NUMBER="+1234567890"

---

## 🎬 Running the Live Demo

Ready to see the swarm in action? You'll need three terminal windows running side-by-side to watch the magic happen.

**Terminal 1: Start the FastAPI Backend**
uvicorn main:app --reload
*(Wait until you see "Application startup complete")*

**Terminal 2: Launch the 3D Command Center**
streamlit run dashboard.py
*(This will pop open the UI in your web browser. It will sit in standby, waiting for incoming data.)*

**Terminal 3: Trigger the IoT Simulator**
python iot_simulator.py

### What to expect during the simulation:
* The simulator will ping the server with normal coordinates. The UI will show a healthy green dot.
* On the 4th ping, the compressor will fail.
* The FastAPI server instantly locks the state and wakes up the CrewAI swarm.
* The AI calculates the thermodynamic decay, finds a hospital via Google Maps, drops a route polyline, texts/calls the driver via Twilio, and drafts an FDA PDF.
* The Streamlit UI will instantly flash red and draw a glowing 3D path to the safe harbor.

---

## 🛣️ Phase 2 Roadmap

Where we are taking this next:

* **Offline Edge AI:** Implementing "Store-and-Forward" gateway memory and quantized LLMs for zero-connectivity rural routing.
* **Mass Casualty Queues:** Integrating Apache Kafka for asynchronous handling of simultaneous, fleet-wide failures.
* **Smart Contracts:** Linking our immutable Total Loss PDF generator to a Polygon smart contract for automated parametric insurance payouts.