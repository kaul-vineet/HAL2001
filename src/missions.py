"""HAL Missions — Scheduled prompts sent to the orchestrator.

Each mission is just a natural language prompt. The orchestrator (Copilot Chat API)
decides which tools to call (Chat, Search, Retrieval, Meeting Insights, MCP servers)
and in what order. HAL executes the plan and displays results.

Mission types:
    "smart"  → Orchestrator plans tools automatically (recommended)
    "chat"   → Force direct Chat API call (bypass orchestrator)

To add a new mission: add an entry to MISSIONS below. That's it.
The orchestrator figures out the rest.
"""

MISSIONS = [
    # ── Email & Communications ───────────────────────────────────
    {
        "id": "email-scan",
        "code": "MAIL",
        "label": "Outlook Inbox",
        "type": "smart",
        "prompt": (
            "List my emails from the last 100 days. For each email show: "
            "sender name, subject line, and date received. "
            "Group by sender. Show actual email subjects, not summaries."
        ),
        "interval": 30,
    },
    {
        "id": "teams-activity",
        "code": "TEAM",
        "label": "Teams",
        "type": "smart",
        "prompt": (
            "List my Teams messages and mentions from the last 100 days. "
            "For each show: who sent it, which channel or chat, "
            "the actual message text (first line), and date. "
            "Show real messages, not a summary."
        ),
        "interval": 30,
    },

    # ── Meetings ─────────────────────────────────────────────────
    {
        "id": "meeting-insights",
        "code": "MEET",
        "label": "Meeting Insights",
        "type": "smart",
        "prompt": (
            "Get my recent meeting action items, notes, and any mentions "
            "of me. List action items with owners."
        ),
        "interval": 30,
    },

    # ── Tasks & Projects ─────────────────────────────────────────
    {
        "id": "planner-tasks",
        "code": "PLAN",
        "label": "Planner Tasks",
        "type": "smart",
        "prompt": (
            "In ONE line: how many Planner tasks are overdue or due today, "
            "and their titles. Max 3 items."
        ),
        "interval": 30,
    },
    {
        "id": "ado-check",
        "code": "ADO",
        "label": "Azure DevOps",
        "type": "smart",
        "prompt": (
            "In ONE line: how many ADO work items are assigned to me that "
            "are in progress or blocked. Just count and titles."
        ),
        "interval": 30,
    },

    # ── Documents & SharePoint ───────────────────────────────────
    {
        "id": "sharepoint-docs",
        "code": "SHRP",
        "label": "SharePoint Docs",
        "type": "smart",
        "prompt": (
            "Find documents shared with me or modified in my "
            "SharePoint sites in the last 100 days. List file names."
        ),
        "interval": 30,
    },

    # ── Sales ────────────────────────────────────────────────────
    {
        "id": "sales-check",
        "code": "SALE",
        "label": "Sales",
        "type": "smart",
        "prompt": (
            "In ONE line: any time-sensitive sales emails, proposals, or "
            "customer follow-ups from today. Just count and deal names."
        ),
        "interval": 30,
    },

    # ── Document content (orchestrator will use Retrieval API) ───
    {
        "id": "policy-updates",
        "code": "PLCY",
        "label": "Motor Control Brief",
        "type": "smart",
        "prompt": (
            "Find and extract the Motor Control Optimization Brief from "
            "SharePoint. Summarize key points, objectives, and action items."
        ),
        "interval": 30,
    },
    {
        "id": "compliance-check",
        "code": "COMP",
        "label": "Compliance",
        "type": "smart",
        "prompt": (
            "Check SharePoint for any compliance updates, data retention "
            "or security policy changes in the last 100 days. "
            "Extract exact text if found. If none, say 'All clear'."
        ),
        "interval": 30,
    },
    {
        "id": "project-docs",
        "code": "PROJ",
        "label": "Project Docs",
        "type": "smart",
        "prompt": (
            "Find any project status updates, milestones, or deliverables "
            "documents modified in the last 100 days. List file names and summarize."
        ),
        "interval": 30,
    },
    {
        "id": "knowledge-base",
        "code": "KNOW",
        "label": "Knowledge Base",
        "type": "smart",
        "prompt": (
            "Search for recently added or updated knowledge base articles "
            "and how-to guides in SharePoint from the last 100 days. "
            "List titles."
        ),
        "interval": 30,
    },

    # ── Daily Briefing (startup only) ────────────────────────────
    {
        "id": "daily-briefing",
        "code": "BREF",
        "label": "Daily Briefing",
        "type": "smart",
        "prompt": (
            "Give me a morning briefing. Include: "
            "1) Calendar for today with any conflicts "
            "2) Urgent unread emails "
            "3) Unread Teams messages "
            "4) Overdue Planner tasks "
            "5) Action items from recent meetings. "
            "Keep each point to one line."
        ),
        "interval": 0,
    },
]

