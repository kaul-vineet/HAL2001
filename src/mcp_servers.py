"""MCP Server configuration for HAL.

Add MCP servers here. HAL will connect to all of them on startup
and make their tools available for missions and user queries.

Each server needs:
    - name:   Friendly identifier (used in missions and commands)
    - target: URL (http://...) for remote servers, or .py path for local scripts

To add a new server: just add an entry below and restart HAL.
"""

MCP_SERVERS = [
    # ── Examples (uncomment and configure as needed) ─────────────

    # Microsoft 365 MCP server (Softeria/ms-365-mcp-server)
    # {
    #     "name": "m365",
    #     "target": "http://localhost:8080/mcp",
    # },

    # Local Python MCP server script
    # {
    #     "name": "mytools",
    #     "target": "path/to/my_mcp_server.py",
    # },

    # Remote MCP server
    # {
    #     "name": "jira",
    #     "target": "http://jira-mcp.internal:9000/mcp",
    # },
]
