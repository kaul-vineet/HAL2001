"""MCP Server configuration for HAL.

Add MCP servers here. HAL will connect to all enabled servers on startup,
discover their tools, and register them with the orchestrator.
The planner automatically learns about new tools — no code changes needed.

Each server needs:
    - name:    Friendly identifier (used as prefix: "name.tool_name")
    - target:  URL (http://...) for remote, or command/path for local stdio
    - enabled: Set to False to skip without removing

To add a new server: add an entry below and restart HAL.
"""

MCP_SERVERS = [
    # ── DevOps & Engineering ─────────────────────────────────────
    # {
    #     "name": "github",
    #     "target": "npx -y @modelcontextprotocol/server-github",
    #     "enabled": True,
    # },
    # {
    #     "name": "jira",
    #     "target": "npx -y @modelcontextprotocol/server-jira",
    #     "enabled": True,
    # },
    # {
    #     "name": "ado",
    #     "target": "npx -y @modelcontextprotocol/server-azure-devops",
    #     "enabled": True,
    # },
    # {
    #     "name": "linear",
    #     "target": "npx -y @modelcontextprotocol/server-linear",
    #     "enabled": True,
    # },

    # ── Communication & Collaboration ────────────────────────────
    # {
    #     "name": "slack",
    #     "target": "npx -y @modelcontextprotocol/server-slack",
    #     "enabled": True,
    # },
    # {
    #     "name": "notion",
    #     "target": "npx -y @modelcontextprotocol/server-notion",
    #     "enabled": True,
    # },

    # ── Business & CRM ───────────────────────────────────────────
    # {
    #     "name": "salesforce",
    #     "target": "npx -y @modelcontextprotocol/server-salesforce",
    #     "enabled": True,
    # },

    # ── Databases ────────────────────────────────────────────────
    # {
    #     "name": "postgres",
    #     "target": "npx -y @modelcontextprotocol/server-postgres",
    #     "enabled": True,
    # },
    # {
    #     "name": "sqlite",
    #     "target": "npx -y @modelcontextprotocol/server-sqlite",
    #     "enabled": True,
    # },

    # ── Cloud & Infrastructure ───────────────────────────────────
    # {
    #     "name": "aws",
    #     "target": "npx -y @modelcontextprotocol/server-aws",
    #     "enabled": True,
    # },

    # ── Microsoft 365 ────────────────────────────────────────────
    # {
    #     "name": "workiq",
    #     "target": "npx -y @microsoft/workiq mcp",
    #     "enabled": True,
    # },

    # ── Monitoring & Analytics ───────────────────────────────────
    # {
    #     "name": "sentry",
    #     "target": "npx -y @modelcontextprotocol/server-sentry",
    #     "enabled": True,
    # },
]
