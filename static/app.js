const chat = document.getElementById("chat");
const form = document.getElementById("chatForm");
const input = document.getElementById("message");
const memories = document.getElementById("memories");
const incidents = document.getElementById("incidents");
const memorySummary = document.getElementById("memorySummary");
const status = document.getElementById("status");
const seedBtn = document.getElementById("seedBtn");

function addMessage(role, text) {
    const el = document.createElement("div");
    el.className = `message ${role}`;

    if (role === "assistant") {
        el.innerHTML = `<div class="message-label">OPSDESK</div>${escapeHtml(text).replace(/\n/g, "<br>")}`;
    } else {
        el.innerHTML = escapeHtml(text).replace(/\n/g, "<br>");
    }

    chat.appendChild(el);
    chat.scrollTop = chat.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

async function checkHealth() {
    try {
        const response = await fetch("/api/health");
        const data = await response.json();

        if (data.hindsight_configured && data.groq_configured) {
            status.textContent = "Hindsight + Groq connected";
        } else {
            status.textContent = "Add API keys in .env";
        }
    } catch {
        status.textContent = "server unavailable";
    }
}

async function loadIncidents() {
    const response = await fetch("/api/incidents");
    const data = await response.json();

    incidents.innerHTML = "";

    if (!data.length) {
        incidents.innerHTML = `<div class="empty">No local incidents yet.</div>`;
        return;
    }

    data.slice(0, 8).forEach((item) => {
        const el = document.createElement("div");
        el.className = "incident-item";
        el.innerHTML = `
            <div class="incident-title">${escapeHtml(item.title)}</div>
            <div class="incident-meta">
                ${escapeHtml(item.service)} · ${escapeHtml(item.severity)}
            </div>
        `;
        incidents.appendChild(el);
    });
}

function showMemories(items) {
    memories.innerHTML = "";

    if (!items.length) {
        memorySummary.textContent = "No matching memory found.";
        memories.innerHTML = `<div class="empty">The agent had no relevant previous incident in memory.</div>`;
        return;
    }

    memorySummary.textContent = `${items.length} relevant memory result${items.length > 1 ? "s" : ""} recalled.`;

    items.forEach((item) => {
        const el = document.createElement("div");
        el.className = "memory-item";
        el.innerHTML = `
            <div class="memory-type">${escapeHtml(item.type || "memory")}</div>
            <div>${escapeHtml(item.text)}</div>
        `;
        memories.appendChild(el);
    });
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const message = input.value.trim();
    if (!message) return;

    addMessage("user", message);
    input.value = "";

    const button = form.querySelector("button");
    button.disabled = true;
    button.textContent = "Checking...";

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({message}),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Request failed");
        }

        addMessage("assistant", data.answer);
        showMemories(data.memories || []);
        await loadIncidents();
    } catch (error) {
        addMessage("assistant", `Something went wrong: ${error.message}`);
    } finally {
        button.disabled = false;
        button.textContent = "Investigate";
    }
});

seedBtn.addEventListener("click", async () => {
    seedBtn.disabled = true;
    seedBtn.textContent = "Loading...";

    try {
        const response = await fetch("/api/seed", {method: "POST"});
        const data = await response.json();

        addMessage(
            "assistant",
            `${data.message} Hindsight retained ${data.memories_retained} historical incident memories.`
        );

        await loadIncidents();
        await checkHealth();
    } catch (error) {
        addMessage("assistant", `Could not load sample history: ${error.message}`);
    } finally {
        seedBtn.disabled = false;
        seedBtn.textContent = "Load sample history";
    }
});

checkHealth();
loadIncidents();
