# 🔴 HAL 9000 — M365 Copilot CLI Agent

A spacecraft-themed autonomous CLI agent that connects to **Microsoft 365 Copilot APIs** (Chat, Search, Retrieval, Meeting Insights) to scan, summarize, and analyze your M365 data — emails, Teams, Planner, SharePoint, meetings — all from your terminal.

## 🚀 How It Works

HAL runs in two modes:

### 🛰️ Auto-Pilot Mode (default)

- 🔄 Runs scheduled **missions** every 30 seconds
- 🧠 Each mission sends a prompt to M365 Copilot APIs
- 📊 Results display in spacecraft-style UI with system sounds
- ⚙️ Cosmetic system checks scroll between mission cycles

### ⌨️ Crew Input Mode (press ESC)

- 🛑 Press **ESC** to interrupt and ask HAL anything
- 🔍 Your question goes through **Search API** (find docs) then **Chat API** (analyze)
- ⏱️ 10 seconds of silence returns to auto-pilot

## 🧠 Copilot APIs Used

| API | Purpose | Endpoint |
|-----|---------|----------|
| 💬 **Chat API** | Natural language Q&A grounded in M365 data | `POST /beta/copilot/conversations/{id}/chat` |
| 🔍 **Search API** | Semantic document discovery across OneDrive | `POST /beta/copilot/search` |
| 📄 **Retrieval API** | Extract text chunks from SharePoint/OneDrive for RAG | `POST /beta/copilot/retrieval` |
| 🎙️ **Meeting Insights API** | AI-generated notes, action items from Teams meetings | `GET /copilot/users/{id}/onlineMeetings/{id}/aiInsights` |

## 📋 Prerequisites

- 🐍 **Python 3.10+**
- 🪪 **Microsoft 365 Copilot license** (required for all Copilot APIs)
- 🔐 **Azure AD App Registration** with these **delegated** permissions:
  - `Mail.Read`
  - `Chat.Read`
  - `ChannelMessage.Read.All`
  - `People.Read.All`
  - `Sites.Read.All`
  - `OnlineMeetingTranscript.Read.All`
  - `ExternalItem.Read.All`
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

🌐 First run opens a browser for login. Subsequent runs use cached tokens (silent refresh).

### 🔄 Force Re-login

```bash
python main.py --relogin
```

## 📡 Missions

Missions are scheduled prompts sent to Copilot APIs. Edit `src/missions.py` to customize — no code changes needed elsewhere.

| Code | Label | API | What it asks |
|------|-------|-----|-------------|
| 📬 `MAIL` | Outlook Inbox | Chat | Summarize emails with topic highlights |
| 💬 `TEAM` | Teams | Chat | Summarize Teams messages and mentions |
| 🎙️ `MEET` | Meeting Insights | Meeting API | Action items and notes from recent meetings |
| ✅ `PLAN` | Planner Tasks | Chat | Overdue or due-today tasks |
| 🔧 `ADO` | Azure DevOps | Chat | Work items in progress or blocked |
| 📁 `SHRP` | SharePoint Docs | Chat | Recently modified documents |
| 💰 `SALE` | Sales | Chat | Time-sensitive sales activity |
| 📄 `PLCY` | Motor Control Brief | Retrieval | Extract and summarize from SharePoint docs |
| 🛡️ `COMP` | Compliance | Retrieval | Compliance updates from org docs |
| 📊 `PROJ` | Project Docs | Retrieval | Project status updates |
| 📚 `KNOW` | Knowledge Base | Retrieval | New knowledge articles |
| 🔍 `DOCS` | Recent Documents | Search | Find recently modified files |
| ☀️ `BREF` | Daily Briefing | Chat | 4-line morning briefing (startup only) |

### ➕ Adding a Mission

Add to `src/missions.py`:

```python
{
    "id": "hr-updates",
    "code": "HR",
    "label": "HR Updates",
    "type": "retrieval",
    "query": "HR announcements benefits changes",
    "data_source": "sharePoint",
    "instruction": "In ONE line: any HR updates this week?",
    "interval": 30,
},
```

## 💻 User Commands (in Crew Input Mode)

| Command | Action |
|---------|--------|
| 💬 *any question* | Search API + Chat API - smart answer |
| 🔄 `scan` | Force re-run all missions now |
| 📅 `missions` | Show mission schedule and status |
| 🔁 `reset` | Start fresh Copilot conversation |
| 👋 `exit` | Quit HAL |

## 🏗️ Architecture

```
HAL/
├── main.py              <- 🚀 Entry point (run this)
├── requirements.txt     <- 📦 Python dependencies
├── README.md
├── .env                 <- 🔐 Your credentials (gitignored)
├── .env.example         <- 📝 Template for .env
├── .gitignore
└── src/
    ├── __init__.py
    ├── auth.py          <- 🔑 MSAL authentication with persistent token cache
    ├── brain.py         <- 🧠 Copilot APIs (Chat, Search, Retrieval, Meeting Insights)
    ├── missions.py      <- 📡 Mission definitions (edit prompts here)
    ├── scheduler.py     <- ⏱️ Task timer and scheduling logic
    ├── sounds.py        <- 🔊 Spacecraft beeps and tones (winsound)
    ├── config.py        <- ⚙️ Environment config loader
    ├── mcp_client.py    <- 🔌 MCP hub - connect to any MCP server
    └── mcp_servers.py   <- 🌐 MCP server config (add servers here)
```

## 🔌 MCP Integration

HAL can consume external **Model Context Protocol (MCP)** servers to gain new capabilities. Configure servers in `src/mcp_servers.py`:

```python
MCP_SERVERS = [
    {"name": "m365", "target": "http://localhost:8080/mcp"},
    {"name": "mytools", "target": "path/to/my_mcp_server.py"},
]
```

🔗 HAL connects on startup, discovers tools, and makes them available. Supports both HTTP (remote) and stdio (local script) transports via FastMCP.

## 🔊 Sound Effects

HAL plays spacecraft-style beeps using Windows `winsound`:

| Event | Sound |
|-------|-------|
| 🚀 Boot | Ascending chime |
| ✅ Auth success | Double high beep |
| ▶️ Mission start | Soft blip |
| ✔️ Mission complete | Quick double-blip |
| ❌ Mission error | Low buzz |
| ⚙️ System check tick | Tiny tick |
| 💭 HAL quote | Soft chime |
| ⌨️ User interrupt (ESC) | Descending tone |
| 🔄 Resume auto-pilot | Ascending tone |
| 👋 Goodbye | Descending Daisy Bell |

🔇 Sounds are silently skipped on non-Windows systems.

## 📜 License

MIT
