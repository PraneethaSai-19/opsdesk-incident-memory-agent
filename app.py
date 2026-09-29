import os
import asyncio
import threading
import sqlite3
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from groq import Groq
from hindsight_client import Hindsight


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "incidents.db"

app = Flask(__name__)


# =========================================================
# CONFIG
# =========================================================

HINDSIGHT_URL = os.getenv(
    "HINDSIGHT_URL",
    "http://127.0.0.1:8888"
)

HINDSIGHT_BANK = os.getenv(
    "HINDSIGHT_BANK",
    "incident-response"
)

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY",
    ""
)

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b"
)


# =========================================================
# GROQ CLIENT
# =========================================================

groq = (
    Groq(api_key=GROQ_API_KEY)
    if GROQ_API_KEY
    else None
)


# =========================================================
# PERSISTENT HINDSIGHT EVENT LOOP
# =========================================================

class HindsightManager:
    """
    Keeps one persistent asyncio event loop alive for the
    entire Flask application.

    The Hindsight client is created INSIDE this event-loop
    thread so its async HTTP resources stay attached to the
    correct loop.
    """

    def __init__(self, base_url):

        self.base_url = base_url

        self.loop = asyncio.new_event_loop()

        self.client = None

        self.ready = threading.Event()

        self.thread = threading.Thread(
            target=self._worker,
            daemon=True
        )

        self.thread.start()

        # Wait until the loop and client are ready.
        self.ready.wait(timeout=10)

    def _worker(self):

        asyncio.set_event_loop(self.loop)

        # IMPORTANT:
        # Create the Hindsight client inside this thread.
        self.client = Hindsight(
            base_url=self.base_url
        )

        self.ready.set()

        self.loop.run_forever()

    def run(self, coroutine_function, *args, **kwargs):

        if not self.ready.is_set():
            raise RuntimeError(
                "Hindsight event loop is not ready."
            )

        coroutine = coroutine_function(
            self.client,
            *args,
            **kwargs
        )

        future = asyncio.run_coroutine_threadsafe(
            coroutine,
            self.loop
        )

        return future.result(timeout=120)


# Create ONE persistent Hindsight manager.
hindsight_manager = HindsightManager(
    HINDSIGHT_URL
)


# =========================================================
# DATABASE
# =========================================================

def init_db():

    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with sqlite3.connect(DB_PATH) as conn:

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                service TEXT NOT NULL,
                severity TEXT NOT NULL,
                root_cause TEXT NOT NULL,
                resolution TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        conn.commit()


def save_incident(
    title,
    service,
    severity,
    root_cause,
    resolution
):

    with sqlite3.connect(DB_PATH) as conn:

        conn.execute(
            """
            INSERT INTO incidents
            (
                title,
                service,
                severity,
                root_cause,
                resolution,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                service,
                severity,
                root_cause,
                resolution,
                datetime.utcnow().isoformat(
                    timespec="seconds"
                ),
            ),
        )

        conn.commit()


def incident_exists(title, service):

    with sqlite3.connect(DB_PATH) as conn:

        row = conn.execute(
            """
            SELECT 1
            FROM incidents
            WHERE title = ? AND service = ?
            LIMIT 1
            """,
            (
                title,
                service
            ),
        ).fetchone()

    return row is not None


def get_incidents():

    with sqlite3.connect(DB_PATH) as conn:

        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """
            SELECT *
            FROM incidents
            ORDER BY id DESC
            """
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


# =========================================================
# HINDSIGHT ASYNC OPERATIONS
# =========================================================

async def _create_bank(client):

    try:

        result = await client.acreate_bank(
            bank_id=HINDSIGHT_BANK,
            name="Incident Response Memory",
            background=(
                "Memory bank for production incidents, "
                "root causes, resolutions, troubleshooting "
                "steps and engineering lessons."
            ),
        )

        print(
            "Hindsight bank ready:",
            result
        )

        return True

    except Exception as exc:

        # Usually means the bank already exists.
        message = str(exc).lower()

        if (
            "already exists" in message
            or "409" in message
            or "conflict" in message
        ):
            return True

        print(
            "Hindsight bank error:",
            exc
        )

        return False


async def _retain(
    client,
    content,
    context
):

    # Make sure the bank exists.
    bank_ready = await _create_bank(client)

    if not bank_ready:
        return False

    try:

        result = await client.aretain(
            bank_id=HINDSIGHT_BANK,
            content=content,
            context=context,
        )

        print(
            "Hindsight retain successful:",
            result
        )

        return True

    except Exception as exc:

        print(
            "Hindsight retain error:",
            exc
        )

        return False


async def _recall(
    client,
    query
):

    # Make sure the bank exists.
    bank_ready = await _create_bank(client)

    if not bank_ready:
        return []

    try:

        result = await client.arecall(
            bank_id=HINDSIGHT_BANK,
            query=query,
            max_tokens=3000,
            budget="mid",
        )

        memories = []

        for item in result.results[:6]:

            memories.append(
                {
                    "text": item.text,
                    "type": getattr(
                        item,
                        "type",
                        "memory"
                    ),
                }
            )

        print(
            f"Hindsight recall returned "
            f"{len(memories)} memories."
        )

        return memories

    except Exception as exc:

        print(
            "Hindsight recall error:",
            exc
        )

        return []


# =========================================================
# HINDSIGHT PUBLIC FUNCTIONS
# =========================================================

def ensure_bank():

    try:

        return hindsight_manager.run(
            _create_bank
        )

    except Exception as exc:

        print(
            "Hindsight bank error:",
            exc
        )

        return False


def retain_memory(
    content,
    context="incident response"
):

    try:

        return hindsight_manager.run(
            _retain,
            content,
            context
        )

    except Exception as exc:

        print(
            "Hindsight retain error:",
            exc
        )

        return False


def recall_memories(query):

    try:

        return hindsight_manager.run(
            _recall,
            query
        )

    except Exception as exc:

        print(
            "Hindsight recall error:",
            exc
        )

        return []


# =========================================================
# GROQ ANSWER GENERATION
# =========================================================

def generate_answer(
    user_message,
    memories
):

    if not groq:

        return (
            "GROQ_API_KEY is not configured. "
            "Please add it to your .env file "
            "and restart the server."
        )

    if memories:

        memory_text = "\n\n".join(
            [
                (
                    f"Historical memory {index + 1}:\n"
                    f"{item['text']}"
                )
                for index, item
                in enumerate(memories)
            ]
        )

    else:

        memory_text = (
            "No relevant historical incident "
            "was found in Hindsight memory."
        )

    system_prompt = f"""
You are OpsDesk, an incident response assistant
for a software engineering team.

Your job is to help engineers troubleshoot
production incidents using historical memory.

IMPORTANT MEMORY RULES:

1. Historical memories below come from Hindsight.
2. Do not invent previous incidents.
3. Do not claim that an incident happened before
   unless it appears in the historical memory.
4. Clearly distinguish historical memory from
   your own troubleshooting suggestions.
5. If a historical incident is relevant, explicitly
   mention it.
6. Explain its root cause and resolution.
7. Give practical next checks.
8. Never claim that you changed production systems.

HISTORICAL MEMORY FROM HINDSIGHT:

{memory_text}

USER QUESTION:

{user_message}
"""

    try:

        completion = groq.chat.completions.create(
            model=GROQ_MODEL,

            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ],

            temperature=0.3,

            max_completion_tokens=900,
        )

        return (
            completion
            .choices[0]
            .message
            .content
        )

    except Exception as exc:

        print(
            "Groq error:",
            exc
        )

        return (
            "I couldn't generate an AI response "
            "right now. Please check the Groq "
            "configuration."
        )


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# HEALTH
# =========================================================

@app.get("/api/health")
def health():

    hindsight_status = False

    try:

        hindsight_status = ensure_bank()

    except Exception as exc:

        print(
            "Health check Hindsight error:",
            exc
        )

    return jsonify(
        {
            "hindsight_configured":
                hindsight_status,

            "hindsight_url":
                HINDSIGHT_URL,

            "groq_configured":
                bool(GROQ_API_KEY),

            "bank":
                HINDSIGHT_BANK,
        }
    )


# =========================================================
# INCIDENT LIST
# =========================================================

@app.get("/api/incidents")
def incidents():

    return jsonify(
        get_incidents()
    )


# =========================================================
# SEED SAMPLE INCIDENTS
# =========================================================

@app.post("/api/seed")
def seed():

    sample_incidents = [

        {
            "title":
                "Checkout API returned 503",

            "service":
                "checkout-api",

            "severity":
                "SEV-2",

            "root_cause":
                (
                    "Database connection pool was "
                    "exhausted during a traffic spike."
                ),

            "resolution":
                (
                    "Increased the connection pool "
                    "from 20 to 50 and restarted "
                    "the affected workers."
                ),
        },

        {
            "title":
                "Payment requests timed out",

            "service":
                "payment-service",

            "severity":
                "SEV-2",

            "root_cause":
                (
                    "A downstream payment provider "
                    "was slow and the client timeout "
                    "was too aggressive."
                ),

            "resolution":
                (
                    "Raised the provider timeout "
                    "and added a circuit-breaker "
                    "fallback."
                ),
        },

        {
            "title":
                "Checkout errors after deployment",

            "service":
                "checkout-api",

            "severity":
                "SEV-1",

            "root_cause":
                (
                    "A new database migration created "
                    "lock contention on the orders table."
                ),

            "resolution":
                (
                    "Rolled back the migration, "
                    "cleared the long-running transaction, "
                    "then applied the migration during "
                    "a maintenance window."
                ),
        },

    ]

    created = 0
    skipped = 0

    # Check Hindsight first.
    bank_ready = ensure_bank()

    for index, item in enumerate(sample_incidents):

        # -------------------------------------------------
        # PREVENT DUPLICATE SAMPLE INCIDENTS
        # -------------------------------------------------

        if incident_exists(
            item["title"],
            item["service"]
        ):

            print(
                "Skipping duplicate incident:",
                item["title"]
            )

            skipped += 1

            continue

        # -------------------------------------------------
        # SAVE LOCALLY
        # -------------------------------------------------

        save_incident(
            item["title"],
            item["service"],
            item["severity"],
            item["root_cause"],
            item["resolution"],
        )

        # -------------------------------------------------
        # CREATE HINDSIGHT MEMORY
        # -------------------------------------------------

        content = (
            f"Incident: {item['title']}. "
            f"Service: {item['service']}. "
            f"Severity: {item['severity']}. "
            f"Root cause: {item['root_cause']} "
            f"Resolution: {item['resolution']}"
        )

        if bank_ready:

            retained = retain_memory(
                content,
                context="historical production incident"
            )

            if retained:
                created += 1

        # -------------------------------------------------
        # RATE-LIMIT PROTECTION
        # -------------------------------------------------
        # Give Groq's TPM window time to recover before
        # processing another NEW historical incident.

        if index < len(sample_incidents) - 1:

            time.sleep(20)

    return jsonify(
        {
            "message": (
                "Sample history ready. "
                f"{created} new memories retained, "
                f"{skipped} duplicates skipped."
            ),

            "memories_retained":
                created,

            "duplicates_skipped":
                skipped,

            "hindsight_ready":
                bank_ready,
        }
    )


# =========================================================
# CREATE INCIDENT
# =========================================================

@app.post("/api/incidents")
def create_incident():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    required = [
        "title",
        "service",
        "severity",
        "root_cause",
        "resolution",
    ]

    missing = [
        field
        for field in required
        if not data.get(field)
    ]

    if missing:

        return jsonify(
            {
                "error":
                    "Missing: "
                    + ", ".join(missing)
            }
        ), 400

    save_incident(
        data["title"],
        data["service"],
        data["severity"],
        data["root_cause"],
        data["resolution"],
    )

    content = (
        f"Incident: {data['title']}. "
        f"Service: {data['service']}. "
        f"Severity: {data['severity']}. "
        f"Root cause: {data['root_cause']} "
        f"Resolution: {data['resolution']}"
    )

    retained = retain_memory(
        content,
        context="resolved production incident"
    )

    return jsonify(
        {
            "message":
                "Incident saved.",

            "hindsight_retained":
                retained,
        }
    )


# =========================================================
# CHAT
# =========================================================

@app.post("/api/chat")
def chat():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    message = (
        data.get("message")
        or ""
    ).strip()

    if not message:

        return jsonify(
            {
                "error":
                    "Message is required."
            }
        ), 400

    # Make sure Hindsight bank exists.
    ensure_bank()

    # Retrieve relevant memories.
    memories = recall_memories(
        message
    )

    # Generate AI response using
    # recalled Hindsight memories.
    answer = generate_answer(
        message,
        memories
    )

    # Remember this interaction so
    # future questions can build on it.
    retain_memory(
        (
            f"Engineer asked: {message}\n"
            f"Assistant response: {answer}"
        ),
        context="incident response conversation"
    )

    return jsonify(
        {
            "answer":
                answer,

            "memories":
                memories,

            "memory_count":
                len(memories),
        }
    )


# =========================================================
# CLEAR LOCAL DATABASE
# =========================================================

@app.post("/api/clear-local")
def clear_local():

    with sqlite3.connect(DB_PATH) as conn:

        conn.execute(
            "DELETE FROM incidents"
        )

        conn.commit()

    return jsonify(
        {
            "message":
                "Local incident history cleared."
        }
    )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    init_db()

    print()
    print("=" * 60)
    print("OpsDesk Incident Response Agent")
    print("=" * 60)

    print(
        f"Hindsight: {HINDSIGHT_URL}"
    )

    print(
        f"Memory Bank: {HINDSIGHT_BANK}"
    )

    print(
        f"Groq Model: {GROQ_MODEL}"
    )

    print("=" * 60)
    print()

    # Start Flask.
    #
    # IMPORTANT:
    # use_reloader=False prevents Flask from starting
    # a second process and interfering with the persistent
    # Hindsight asyncio event loop.

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000,
        use_reloader=False
    )