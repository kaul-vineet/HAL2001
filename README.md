# 🔴 HAL 9000 — M365 Copilot CLI Agent

A spacecraft-themed autonomous CLI agent that connects to **Microsoft 365 Copilot APIs** and **MCP servers** to scan, summarize, and analyze your enterprise data — emails, Teams, Planner, SharePoint, meetings, and external systems — all from a command center dashboard in your terminal.

## 🚀 How It Works

HAL runs as a **fixed-grid command center dashboard** powered by Rich Live Layout. Each mission gets its own panel that updates in place — no scrolling.

- 🔄 **Scheduled missions** run every 30 seconds via the orchestrator
- 🧠 **Copilot Chat API acts as the planner** — decides which tools to call
- ⚡ **Panels flash yellow** when new data arrives, then fade back
- 🔴 **"Talk to me, Dave"** prompt at the bottom — type any question anytime

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  HAL 9000 (runs on your machine)                                │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ COMMAND CENTER DASHBOARD (Rich Live Layout)               │  │
│  │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │  │
│  │ │ 📬 MAIL  │ │ 💬 TEAM  │ │ 🎙️ MEET  │ │ ✅ PLAN  │     │  │
│  │ └──────────┘ └──────────┘ └──────────┘ └──────────┘     │  │
│  │ 🔴 Talk to me, Dave ▸ _                                  │  │
│  └───────────────────────────────────────────────────────────┘  │
│       │                                                         │
│       ▼                                                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ SCHEDULER (scheduler.py)                                  │  │
│  │ Fires missions every 30s from missions.py                 │  │
│  └──────────────────────────┬────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ ORCHESTRATOR (orchestrator.py)                            │  │
│  │                                                           │  │
│  │ Step 1: Send prompt + tool registry to Copilot Chat API   │  │
│  │ Step 2: Copilot returns a JSON execution plan             │  │
│  │ Step 3: HAL executes the plan step by step                │  │
│  │ Step 4: Results logged to audit trail                     │  │
│  └──────────────┬──────────────────────────┬─────────────────┘  │
│                  │                          │                    │
│    ┌─────────────▼──────────────┐  ┌───────▼────────────────┐   │
│    │ COPILOT APIs (M365 data)   │  │ MCP SERVERS (external) │   │
│    │                            │  │                        │   │
│    │ 💬 Chat API                │  │ 🔧 GitHub              │   │
│    │ 🔍 Search API              │  │ 📋 Jira                │   │
│    │ 📄 Retrieval API           │  │ 💰 Salesforce          │   │
│    │ 🎙️ Meeting Insights API    │  │ 🗄️ PostgreSQL          │   │
│    └────────────────────────────┘  │ 💬 Slack               │   │
│                                    └────────────────────────┘   │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ AUDIT LOG (logs/hal_audit.jsonl)                          │  │
│  │ Every plan, tool call, result, and timing is logged       │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Orchestration: How Decisions Are Made

HAL uses a **Plan-and-Execute** pattern where the LLM plans and code executes:

```
User/Mission: "Prepare for my 2pm sprint review"
                    │
                    ▼
    ┌─── STEP 1: PLAN (1 Chat API call) ───┐
    │                                       │
    │  Copilot Chat API receives:           │
    │  • The user's prompt                  │
    │  • Full tool registry:                │
    │    - chat, search, retrieval, meeting │
    │    - jira.get_sprint, github.list_prs │
    │  • Routing rules (when to use what)   │
    │  • Output format (strict JSON)        │
    │                                       │
    │  Copilot returns:                     │
    │  {                                    │
    │    "reasoning": "Need meeting data    │
    │     + Jira tickets + related docs",   │
    │    "plan": [                          │
    │      {"step":1, "tool":"meeting"},    │
    │      {"step":2, "tool":"jira.get..."},│
    │      {"step":3, "tool":"search"},     │
    │      {"step":4, "tool":"chat",        │
    │       "args": "Combine all above"}    │
    │    ]                                  │
    │  }                                    │
    └───────────────┬───────────────────────┘
                    │
                    ▼
    ┌─── STEP 2: EXECUTE (deterministic) ──┐
    │                                       │
    │  HAL runs each step in order:         │
    │  ✓ Step 1: Meeting Insights API       │
    │  ✓ Step 2: Jira MCP server            │
    │  ✓ Step 3: Copilot Search API         │
    │  ✓ Step 4: Chat API (merge results)   │
    │                                       │
    │  Each step is timed and logged.       │
    └───────────────┬───────────────────────┘
                    │
                    ▼
    ┌─── STEP 3: DISPLAY + AUDIT ──────────┐
    │                                       │
    │  Dashboard panel flashes ⚡ yellow     │
    │  Audit log records: plan, reasoning,  │
    │  each tool call, duration, result     │
    └───────────────────────────────────────┘
```

### Decision Logic: Which Tool Gets Called

The orchestrator prompt includes routing rules that tell the LLM which tool to use:

| Data needed | Tool | Why |
|-------------|------|-----|
| Emails, calendar, Teams, tasks | `chat` | Copilot has live M365 data access |
| Find specific documents | `search` | Returns real file names + URLs |
| Exact text from a document | `retrieval` | Zero hallucination, verbatim quotes |
| Meeting action items, notes | `meeting` | **Exclusive source** — only API with structured meeting data |
| Jira tickets, GitHub PRs | MCP tool | **Exclusive source** — Copilot can't see external systems |
| Combined answer from multiple tools | `chat` (final step) | LLM merges all tool results |

**Key principle:** The LLM plans, code executes. The LLM never touches tools directly — HAL's executor handles all API calls, error handling, and retry logic.

### Data Access Boundaries

```
┌─────────────────────────────┐  ┌──────────────────────────────┐
│  COPILOT APIs               │  │  MCP SERVERS                 │
│  (M365 data only)           │  │  (external systems only)     │
│                             │  │                              │
│  ✅ Emails                  │  │  ✅ Jira / Azure DevOps      │
│  ✅ Calendar                │  │  ✅ GitHub / GitLab           │
│  ✅ Teams messages          │  │  ✅ Salesforce / HubSpot     │
│  ✅ Planner tasks           │  │  ✅ PostgreSQL / MongoDB     │
│  ✅ SharePoint documents    │  │  ✅ Slack / Notion           │
│  ✅ OneDrive files          │  │  ✅ Custom REST APIs         │
│  ✅ Meeting transcripts     │  │                              │
│  ✅ People directory        │  │  ❌ Cannot see M365 data     │
│                             │  │                              │
│  ❌ Cannot see Jira, GitHub │  │                              │
│  ❌ Cannot see databases    │  │                              │
└─────────────────────────────┘  └──────────────────────────────┘

The orchestrator knows these boundaries and routes accordingly.
```

## 🧠 Copilot APIs Used

| API | Purpose | Endpoint |
|-----|---------|----------|
| 💬 **Chat API** | Natural language Q&A + orchestrator planner | `POST /beta/copilot/conversations/{id}/chat` |
| 🔍 **Search API** | Semantic document discovery across OneDrive | `POST /beta/copilot/search` |
| 📄 **Retrieval API** | Extract exact text chunks for RAG grounding | `POST /beta/copilot/retrieval` |
| 🎙️ **Meeting Insights API** | AI-generated notes, action items, mentions | `GET /copilot/users/{id}/onlineMeetings/{id}/aiInsights` |

## 📋 Prerequisites

- 🐍 **Python 3.10+**
- 🪪 **Microsoft 365 Copilot license** (required for all Copilot APIs)
- 🔐 **Azure AD App Registration** with these **delegated** permissions:
  - `Mail.Read`, `Chat.Read`, `ChannelMessage.Read.All`
  - `People.Read.All`, `Sites.Read.All`
  - `OnlineMeetingTranscript.Read.All`, `ExternalItem.Read.All`
  - `Calendars.Read`

## ⚡ Setup

### 1️⃣ Register an Azure AD App

1. Go to [Azure Portal - App Registrations](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade)
2. **New registration** - Name: `HAL 9000`, Single tenant
3. **Redirect URI**: Public client - `http://localhost`
4. **Authentication** - Enable **Allow public client flows**
5. **API permissions** - Add all delegated permissions listed above
6. **Grant admin consent**
7. Copy **Application (client) ID** and **Directory (tenant) ID**

### 2️⃣ Configure

```bash
cd C:\demoprojects\HAL
copy .env.example .env
```

Edit `.env`:

```
AZURE_CLIENT_ID=your-app-client-id
AZURE_TENANT_ID=your-tenant-id
```

### 3️⃣ Install

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 4️⃣ Run

```bash
python main.py
```

🌐 First run opens a browser for login. Subsequent runs use cached tokens.

### 🔄 Force Re-login

```bash
python main.py --relogin
```

## 📡 Missions

Missions are scheduled prompts. The **orchestrator decides which tools to call** based on the prompt — you don't specify the tool type, just what you want to know. Edit `src/missions.py` to customize.

| Code | Label | What it asks |
|------|-------|-------------|
| 📬 `MAIL` | Outlook Inbox | List emails with sender, subject, date |
| 💬 `TEAM` | Teams | List messages with sender, channel, text |
| 🎙️ `MEET` | Meeting Insights | Action items and notes from recent meetings |
| ✅ `PLAN` | Planner Tasks | Overdue or due-today tasks |
| 🔧 `ADO` | Azure DevOps | Work items in progress or blocked |
| 📁 `SHRP` | SharePoint Docs | Recently modified documents |
| 💰 `SALE` | Sales | Time-sensitive sales activity |
| 📄 `PLCY` | Motor Control Brief | Extract and summarize from SharePoint docs |
| 🛡️ `COMP` | Compliance | Compliance updates from org docs |
| 📊 `PROJ` | Project Docs | Project status updates |
| 📚 `KNOW` | Knowledge Base | New knowledge articles |
| ☀️ `BREF` | Daily Briefing | Morning briefing with calendar, emails, tasks (startup only) |

### ➕ Adding a Mission

Add to `src/missions.py`:

```python
{
    "id": "hr-updates",
    "code": "HR",
    "label": "HR Updates",
    "type": "smart",
    "prompt": "List any HR announcements or policy changes from the last 30 days.",
    "interval": 30,
},
```

The orchestrator automatically decides whether to use Chat, Search, Retrieval, or MCP tools.

## 💻 User Commands

Type at the `Talk to me, Dave` prompt:

| Input | What happens |
|-------|-------------|
| 💬 *any question* | Orchestrator plans tools, executes, shows answer |
| 🔄 `scan` | Force re-run all missions now |
| 🔁 `reset` | Start fresh Copilot conversation |
| 👋 `exit` | Quit HAL |

## 📂 Project Structure

```
HAL/
├── main.py              <- 🚀 Entry point + boot sequence + dashboard loop
├── requirements.txt     <- 📦 Python dependencies
├── README.md
├── .env                 <- 🔐 Your credentials (gitignored)
├── .env.example         <- 📝 Template for .env
├── .gitignore
├── logs/                <- 📋 Audit logs (gitignored)
│   └── hal_audit.jsonl
└── src/
    ├── __init__.py
    ├── auth.py          <- 🔑 MSAL authentication with persistent token cache
    ├── brain.py         <- 🧠 Copilot APIs + plan_and_execute orchestrator
    ├── orchestrator.py  <- 📋 Planner prompt with dynamic tool registry
    ├── missions.py      <- 📡 Mission definitions (edit prompts here)
    ├── scheduler.py     <- ⏱️ Task timer and scheduling logic
    ├── dashboard.py     <- 🖥️ Rich Live Layout command center UI
    ├── sounds.py        <- 🔊 Spacecraft beeps and tones
    ├── audit.py         <- 📋 Audit logging (plan, steps, results)
    ├── config.py        <- ⚙️ Environment config loader
    ├── mcp_client.py    <- 🔌 MCP hub - connect to any MCP server
    └── mcp_servers.py   <- 🌐 MCP server config (add servers here)
```

## 🔌 MCP Integration

HAL can consume external **Model Context Protocol (MCP)** servers. Configure in `src/mcp_servers.py`:

```python
MCP_SERVERS = [
    {"name": "github", "target": "npx -y @modelcontextprotocol/server-github", "enabled": True},
    {"name": "jira", "target": "npx -y @modelcontextprotocol/server-jira", "enabled": True},
    {"name": "postgres", "target": "npx -y @modelcontextprotocol/server-postgres", "enabled": True},
]
```

MCP tools are **automatically registered** with the orchestrator on startup. The planner discovers them and includes them in its routing decisions.

## 📋 Audit Trail

All orchestrator decisions and tool executions are logged to `logs/hal_audit.jsonl`. Each HAL session is separated with a clear header.

### Log location

```
C:\demoprojects\HAL\logs\hal_audit.jsonl
```

### Session separators

Each time HAL starts, a session block is written:

```
# ══════════════════════════════════════════════════════════
# HAL 9000 SESSION: session_1710886234  |  2026-03-19T21:02:00Z
# ══════════════════════════════════════════════════════════
```

### Log entry types

Every execution produces 3 correlated entries sharing the same `execution_id` and `session_id`:

**1. Plan** — what the orchestrator decided

```json
{
  "type": "plan",
  "session_id": "session_1710886234",
  "execution_id": "1710886247123",
  "timestamp": "2026-03-19T21:02:15Z",
  "source": "mission",
  "prompt": "List my emails with sender, subject, date",
  "reasoning": "Email query — chat tool has live M365 data access",
  "plan": [
    {"step": 1, "tool": "chat", "args": {"query": "..."}, "description": "Query emails"}
  ]
}
```

**2. Step** (one per tool call) — what happened at each step

```json
{
  "type": "step",
  "session_id": "session_1710886234",
  "execution_id": "1710886247123",
  "step": 1,
  "tool": "chat",
  "description": "Query emails from M365",
  "status": "ok",
  "duration_ms": 2340,
  "result_preview": "You have 12 emails today..."
}
```

**3. Result** — final outcome

```json
{
  "type": "result",
  "session_id": "session_1710886234",
  "execution_id": "1710886247123",
  "prompt": "List my emails...",
  "final_answer": "12 emails today...",
  "total_steps": 1,
  "steps_ok": 1,
  "steps_failed": 0,
  "total_duration_ms": 3200
}
```

### Querying logs (PowerShell)

```powershell
# Last 10 entries
Get-Content .\logs\hal_audit.jsonl | Select-Object -Last 10

# Pretty print latest result
Get-Content .\logs\hal_audit.jsonl | Select-Object -Last 1 | ConvertFrom-Json | ConvertTo-Json -Depth 5

# All plans from current session
Get-Content .\logs\hal_audit.jsonl | Where-Object { $_ -match '"type":"plan"' } | Select-Object -Last 5

# All errors
Get-Content .\logs\hal_audit.jsonl | Where-Object { $_ -match '"status":"error"' }

# Filter by session
Get-Content .\logs\hal_audit.jsonl | Where-Object { $_ -match 'session_1710886234' }
```

### What's auditable

| Field | Logged |
|-------|--------|
| Session ID | ✅ Which HAL run |
| What was asked | ✅ `prompt` |
| Why these tools | ✅ `reasoning` |
| Which tools, what order | ✅ `plan[]` |
| Each step result + timing | ✅ `step` entries with `duration_ms` |
| Success/failure per step | ✅ `status` |
| Final answer | ✅ `final_answer` |
| Source (mission vs user) | ✅ `source` |

Logs are gitignored and stay local only.

## 🔊 Sound Effects

| Event | Sound |
|-------|-------|
| 🚀 Boot | Ascending chime |
| ✅ Auth success | Double high beep |
| ▶️ Mission start | Soft blip |
| ✔️ Mission complete | Quick double-blip |
| ❌ Mission error | Low buzz |
| ⚙️ System check tick | Tiny tick |
| 💭 HAL quote | Soft chime |
| ⌨️ User interrupt | Descending tone |
| 🔄 Resume auto-pilot | Ascending tone |
| 👋 Goodbye | Descending Daisy Bell |

🔇 Sounds are silently skipped on non-Windows systems.

## 📜 License

MIT
