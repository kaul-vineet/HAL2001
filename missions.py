"""HAL Missions — Scheduled system checks sent to M365 Copilot APIs.

Each mission IS a system check. When HAL runs system checks, it's
actually calling Copilot APIs and displaying real results.

Mission types:
    "chat"     → Copilot Chat API (natural language Q&A)
    "meeting"  → Meeting Insights API (action items, summaries)
    "search"   → Search API (document discovery)

To add a new mission: add an entry to MISSIONS below. That's it.
"""

MISSIONS = [
    # ── Email & Communications ───────────────────────────────────
    {
        "id": "email-scan",
        "code": "MAIL",
        "label": "Outlook Inbox",
        "type": "chat",
        "prompt": (
            "In ONE line: how many emails today, how many need my reply, "
            "and top 3 senders. No detail, just counts."
        ),
        "interval": 30,
    },
    {
        "id": "teams-activity",
        "code": "TEAM",
        "label": "Teams",
        "type": "chat",
        "prompt": (
            "In ONE line: how many unread Teams messages or mentions need "
            "my attention today. Just the count and who from."
        ),
        "interval": 30,
    },

    # ── Meetings ─────────────────────────────────────────────────
    {
        "id": "meeting-insights",
        "code": "MEET",
        "label": "Meeting Insights",
        "type": "meeting",
        "prompt": None,
        "interval": 30,
    },

    # ── Tasks & Projects ─────────────────────────────────────────
    {
        "id": "planner-tasks",
        "code": "PLAN",
        "label": "Planner Tasks",
        "type": "chat",
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
        "type": "chat",
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
        "type": "chat",
        "prompt": (
            "In ONE line: any documents shared with me or modified in my "
            "SharePoint sites in the last 24 hours. Just count and names."
        ),
        "interval": 30,
    },

    # ── Sales ────────────────────────────────────────────────────
    {
        "id": "sales-check",
        "code": "SALE",
        "label": "Sales",
        "type": "chat",
        "prompt": (
            "In ONE line: any time-sensitive sales emails, proposals, or "
            "customer follow-ups from today. Just count and deal names."
        ),
        "interval": 30,
    },

    # ── Retrieval-based checks (RAG from org docs) ───────────────
    {
        "id": "policy-updates",
        "code": "PLCY",
        "label": "Policy Updates",
        "type": "retrieval",
        "query": "latest policy changes or updates this week",
        "data_source": "sharePoint",
        "instruction": (
            "In ONE line: any policy changes this week? "
            "If none, just say 'No policy updates'. "
            "If yes, state the policy name and one-line summary."
        ),
        "interval": 30,
    },
    {
        "id": "compliance-check",
        "code": "COMP",
        "label": "Compliance",
        "type": "retrieval",
        "query": "compliance requirements data retention security updates",
        "data_source": "sharePoint",
        "instruction": (
            "In ONE line: any compliance updates needing attention? "
            "If none, say 'All clear'. If yes, one-line summary."
        ),
        "interval": 30,
    },
    {
        "id": "project-docs",
        "code": "PROJ",
        "label": "Project Docs",
        "type": "retrieval",
        "query": "project status updates milestones deliverables this week",
        "data_source": "sharePoint",
        "instruction": (
            "In ONE line: any project doc updates this week? "
            "Just count and doc names. If none, say 'No updates'."
        ),
        "interval": 30,
    },
    {
        "id": "knowledge-base",
        "code": "KNOW",
        "label": "Knowledge Base",
        "type": "retrieval",
        "query": "recently added or updated knowledge articles how-to guides",
        "data_source": "sharePoint",
        "instruction": (
            "In ONE line: any new knowledge base articles? "
            "Just count and titles. If none, say 'No new articles'."
        ),
        "interval": 30,
    },

    # ── Search-based checks (document discovery) ─────────────────
    {
        "id": "recent-docs",
        "code": "DOCS",
        "label": "Recent Documents",
        "type": "search",
        "query": "documents shared with me or modified in the last 24 hours",
        "interval": 30,
    },

    # ── Daily Briefing (startup only) ────────────────────────────
    {
        "id": "daily-briefing",
        "code": "BREF",
        "label": "Daily Briefing",
        "type": "chat",
        "prompt": (
            "Give me a 4-line morning briefing. One line each for: "
            "1) Calendar today (count + any conflicts) "
            "2) Urgent unread emails (count + top sender) "
            "3) Unread Teams messages (count) "
            "4) Overdue tasks (count). "
            "No extra detail. Be terse."
        ),
        "interval": 0,
    },
]
