# OpsDesk — Incident Response with Memory

A small Flask application for demonstrating an incident-response agent backed by Hindsight memory.

The important demo is:

1. Load a few historical incidents.
2. Ask about a new incident that resembles an old one.
3. The backend recalls relevant memories from Hindsight.
4. Groq uses those memories to produce a contextual response.
5. The current interaction is retained so later interactions can build on it.

## Stack

- Flask
- Hindsight Cloud / `hindsight-client`
- Groq (`openai/gpt-oss-20b`)
- SQLite
- Vanilla HTML/CSS/JavaScript

Hindsight is the memory layer. SQLite is only used for the small local incident-history panel.

## 1. Create the environment

Windows PowerShell:

```powershell
py -3.9 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If `py` is unavailable:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 2. Add API keys

Copy `.env.example` to `.env`.

PowerShell:

```powershell
Copy-Item .env.example .env
```

Then edit `.env`:

```env
HINDSIGHT_URL=https://api.hindsight.vectorize.io
HINDSIGHT_API_KEY=your_hindsight_key
HINDSIGHT_BANK=incident-response

GROQ_API_KEY=your_groq_key
GROQ_MODEL=openai/gpt-oss-20b
```

Do not commit `.env`.

## 3. Run

```powershell
python app.py
```

Open:

http://127.0.0.1:5000

## 4. Demo flow

Click **Load sample history**.

Then ask:

> Checkout API is returning 503 errors again. What should I check first?

The right-side panel should show recalled incident memories.

Try another:

> We have payment requests timing out again after a provider slowdown. What happened last time?

The agent should use the corresponding previous incident.

## 5. Add your own incident

The backend already has:

```text
POST /api/incidents
```

Example JSON:

```json
{
  "title": "Inventory service returned 500",
  "service": "inventory-api",
  "severity": "SEV-2",
  "root_cause": "Redis connection exhaustion",
  "resolution": "Restarted affected workers and increased the Redis connection limit."
}
```

## Project structure

```text
incident-memory-agent/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── data/
│   └── incidents.db       # created automatically
├── templates/
│   └── index.html
└── static/
    ├── app.js
    └── style.css
```

## What to customize before submission

Change the product name, text, colors, sample incidents, system prompt, and UI wording.

Add your team's own incident examples instead of leaving only the demo data.

For the final demo, show the sequence:

**old incident → memory retained → later similar incident → memory recalled → better response**

That makes the Hindsight part visible instead of hiding it inside the backend.
