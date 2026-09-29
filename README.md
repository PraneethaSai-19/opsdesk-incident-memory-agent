# OpsDesk — AI Incident Response Agent with Memory

> An AI-powered incident response assistant that remembers previous production incidents and uses that knowledge to help engineers troubleshoot new incidents.

OpsDesk combines **Hindsight persistent memory** with a **Groq-powered LLM** to create an incident response assistant that can recall historical incidents, root causes, fixes, and operational context.

Instead of answering every incident from scratch, OpsDesk can use what the team has learned from previous incidents.

---

## Overview

Production incidents are often repetitive.

Teams may encounter the same API failures, database problems, traffic spikes, configuration issues, or service degradations multiple times. The information needed to solve these incidents may already exist in previous incident reports and postmortems, but engineers often have to search for that information manually.

OpsDesk addresses this problem by giving an AI incident response agent a persistent memory layer.

The core idea is:

```text
Previous Incidents
       ↓
Hindsight Memory
       ↓
Relevant Historical Knowledge
       ↓
New Incident / Question
       ↓
AI Response

Key Features
- 🧠 Persistent incident memory using Hindsight
- 🔎 Recall of relevant historical incidents
- 🤖 AI-powered incident analysis using Groq
- 📋 Historical root-cause and resolution recall
- 💬 Natural-language incident queries
- 👀 Visible memory results in the UI
- 🖥️ Simple web interface for incident investigation
- 💾 Local incident data storage using SQLite
The Problem
When a production incident occurs, engineers commonly need to answer questions such as:
- Have we seen this problem before?
- What caused the previous incident?
- How did we resolve it?
- What should we check first?
- Was this related to a traffic spike, database issue, or configuration change?
A traditional AI assistant may provide a generic troubleshooting response based only on the current prompt.
OpsDesk adds historical context.
If a similar incident happened previously, the agent can retrieve the relevant memory and use it when constructing its response.
How Hindsight Is Used
Hindsight is the persistent memory layer of OpsDesk.
It is used for two important operations:
1. Retain
Historical incident information is stored in the Hindsight memory bank.
await client.aretain(    content=incident_content,    context=incident_context)


The retained information can include:
- Incident description
- Service
- Severity
- Root cause
- Resolution
- Operational context
2. Recall
When an engineer asks a question, OpsDesk queries Hindsight for relevant historical memories.
memories = await client.arecall(    query=incident_question)


The retrieved memories are then used as context for the AI response.
Hindsight Memory Flow
                   Historical Incident
                           │
                           ▼
                  ┌─────────────────┐
                  │ Hindsight       │
                  │    Retain       │
                  └────────┬────────┘
                           │
                           ▼
                   Persistent Memory
                           │
                           │
                           ▼
                 New Incident / Query
                           │
                           ▼
                  ┌─────────────────┐
                  │ Hindsight       │
                  │    Recall       │
                  └────────┬────────┘
                           │
                           ▼
                 Relevant Memories
                           │
                           ▼
                    ┌────────────┐
                    │  Groq LLM  │
                    └─────┬──────┘
                          │
                          ▼
                 Context-Aware Answer
                          │
                          ▼
                       Engineer

This makes memory a central part of the incident-response workflow rather than an additional feature.
Example Incident
Suppose OpsDesk has previously stored an incident like:
Service: Checkout API
Severity: SEV-2
Error: HTTP 503

Root Cause:
Database connection pool exhaustion during a traffic spike.

Resolution:
The connection pool was increased from 20 to 50
and affected workers were restarted.

An engineer can later ask:
Have we seen a Checkout API 503 before?
What caused it and how was it fixed?

OpsDesk can recall the historical incident through Hindsight and use that memory to provide a context-aware response.
The UI also exposes the relevant memories retrieved by the system.
System Architecture
┌──────────────────────┐
│       Engineer       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│     OpsDesk UI       │
│   HTML/CSS/JS        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│    Flask Backend     │
│       Python         │
└──────────┬───────────┘
           │
           ├───────────────────────┐
           │                       │
           ▼                       ▼
┌──────────────────────┐  ┌──────────────────────┐
│      Hindsight       │  │       Groq LLM       │
│   Persistent Memory  │  │   AI Response Layer  │
└──────────┬───────────┘  └──────────┬───────────┘
           │                         │
           ▼                         │
┌──────────────────────┐             │
│ Historical Incidents │─────────────┘
│     & Memories       │
└──────────────────────┘
           │
           ▼
   Context-Aware Response

Technology Stack
Layer	Technology
Frontend	HTML, CSS, JavaScript
Backend	Python, Flask
AI / LLM	Groq
Model	openai/gpt-oss-20b
Memory	Hindsight by Vectorize
Local Storage	SQLite
Environment	Python virtual environment


Project Structure
incident-memory-agent/
│
├── app.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
│
├── static/
│   ├── app.js
│   └── style.css
│
├── templates/
│   └── index.html
│
└── data/
    └── local database files

Getting Started
Prerequisites
Make sure you have:
- Python 3.11+
- Git
- A Groq API key
- A running Hindsight instance
1. Clone the Repository
git clone https://github.com/PraneethaSai-19/opsdesk-incident-memory-agent.git

Move into the project:
cd opsdesk-incident-memory-agent

2. Create a Virtual Environment
Windows
python -m venv .venv

Activate it:
.\.venv\Scripts\Activate.ps1

3. Install Dependencies
pip install -r requirements.txt

4. Configure Environment Variables
Create a .env file in the project root.
Use .env.example as the template:
HINDSIGHT_URL=http://127.0.0.1:8888
HINDSIGHT_BANK=incident-response

GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b

Security
Never commit the .env file or a real API key to GitHub.
The repository's .gitignore already excludes:
.env
.venv/
data/*.db
__pycache__/

Running Hindsight Locally
OpsDesk is configured to communicate with a local Hindsight instance.
Start Hindsight so that it is available at:
http://127.0.0.1:8888

The Hindsight service must be running before using the memory functionality of OpsDesk.
Running OpsDesk
After activating the virtual environment and starting Hindsight:
python app.py

Open the local Flask URL displayed in the terminal.
Example Workflow
A typical OpsDesk interaction follows these steps:
Step 1 — Historical incident
An incident is retained in Hindsight.
Checkout API
HTTP 503
Database connection pool exhausted
Pool increased from 20 → 50
Affected workers restarted

Step 2 — New question
An engineer asks:
Have we seen a Checkout API 503 before?
What was the root cause and how was it fixed?

Step 3 — Memory recall
OpsDesk sends the question to Hindsight and retrieves relevant historical memories.
Step 4 — AI response
The retrieved memories are provided as context to the Groq-powered model.
Step 5 — Context-aware answer
OpsDesk produces an answer using both:
Current Question
       +
Historical Memory
       ↓
AI Response

Step 6 — Memory visibility
The interface displays the relevant memories retrieved from Hindsight.
Why Persistent Memory Matters
Without historical memory:
New Incident
     ↓
Generic AI Response

With Hindsight:
New Incident
     +
Historical Incidents
     ↓
Context-Aware AI Response

The difference is that OpsDesk can use information the team has already learned instead of treating every incident as completely new.
Current Scope
OpsDesk is a prototype focused on demonstrating persistent memory for incident response.
The current implementation uses realistic incident data for demonstration and is not connected to a production monitoring or incident-management platform.
Future Improvements
Possible extensions include:
- Automatic ingestion of incident reports
- Integration with monitoring and alerting systems
- Automated postmortem ingestion
- Runbook retrieval
- Incident severity classification
- Suggested remediation steps
- Feedback-driven memory refinement
- Slack integration
- Integration with incident management platforms
- Automatic incident summarization
Security Notes
Do not commit secrets.
The following files should remain local:
.env
.venv/
data/*.db

Only .env.example should be shared in the repository.
Hindsight Resources
- Hindsight GitHub: https://github.com/vectorize-io/hindsight
- Hindsight Documentation: https://hindsight.vectorize.io/
- Vectorize Agent Memory: https://vectorize.io/what-is-agent-memory
Project
OpsDesk
AI Incident Response Agent with Persistent Memory
Built with:
Python · Flask · Hindsight · Groq · SQLite · HTML · CSS · JavaScript
Team
This project was developed collaboratively as a team project.
Team members:
- Praneetha Sai Mogilisetti
- Dhanush
- Likhitha
- Bhargavi
- Avinash