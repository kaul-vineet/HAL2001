"""HAL MCP Client — Connect to any MCP server and use its tools.

HAL can consume external MCP servers to gain new capabilities.
Each server is registered with a name and connection target (URL or script).
Tools from connected servers become available to HAL's brain and missions.

Usage:
    # In mcp_servers.py, configure your servers:
    MCP_SERVERS = [
        {"name": "m365", "target": "http://localhost:8080/mcp"},
        {"name": "jira", "target": "path/to/jira_mcp_server.py"},
    ]

    # In code:
    hub = MCPHub()
    await hub.connect_all()
    result = await hub.call("m365", "list_emails", {"count": 10})
    tools = await hub.list_tools("m365")
    await hub.disconnect_all()
"""

from fastmcp import Client
from rich.console import Console

console = Console()


class MCPHub:
    """Manages connections to multiple MCP servers.

    Each server is identified by a name and connected via FastMCP Client.
    Supports stdio (Python scripts) and HTTP (remote servers) transports.
    """

    def __init__(self):
        self._clients: dict[str, Client] = {}
        self._contexts: dict[str, object] = {}

    async def connect(self, name: str, target: str) -> None:
        """Connect to an MCP server.

        Args:
            name: Friendly name for this server (e.g., "m365", "jira").
            target: Connection target — a URL (http://...) or a .py script path.
        """
        client = Client(target)
        ctx = await client.__aenter__()
        self._clients[name] = client
        self._contexts[name] = ctx
        console.print(
            f"  [green]●[/green] [bold green]MCP[/bold green]  "
            f"Connected to [bold cyan]{name}[/bold cyan] → [dim]{target}[/dim]"
        )

    async def connect_all(self, servers: list[dict]) -> None:
        """Connect to all configured MCP servers.

        Args:
            servers: List of {"name": ..., "target": ...} dicts.
        """
        for server in servers:
            try:
                await self.connect(server["name"], server["target"])
            except Exception as e:
                console.print(
                    f"  [red]●[/red] [bold red]MCP[/bold red]  "
                    f"Failed to connect to [bold]{server['name']}[/bold]: {e}"
                )

    async def disconnect(self, name: str) -> None:
        """Disconnect from a specific MCP server."""
        if name in self._clients:
            try:
                await self._clients[name].__aexit__(None, None, None)
            except Exception:
                pass
            del self._clients[name]
            del self._contexts[name]

    async def disconnect_all(self) -> None:
        """Disconnect from all MCP servers."""
        for name in list(self._clients.keys()):
            await self.disconnect(name)

    async def list_tools(self, name: str) -> list[dict]:
        """List available tools on an MCP server.

        Returns list of {"name": ..., "description": ...} dicts.
        """
        if name not in self._clients:
            return []
        tools = await self._clients[name].list_tools()
        return [
            {"name": t.get("name", t.name if hasattr(t, 'name') else str(t)),
             "description": t.get("description", getattr(t, 'description', ''))}
            if isinstance(t, dict) else
            {"name": t.name, "description": t.description or ""}
            for t in tools
        ]

    async def list_all_tools(self) -> dict[str, list[dict]]:
        """List tools from all connected servers.

        Returns {"server_name": [tools...], ...}
        """
        result = {}
        for name in self._clients:
            result[name] = await self.list_tools(name)
        return result

    async def call(self, server_name: str, tool_name: str, args: dict = None) -> str:
        """Call a tool on a specific MCP server.

        Args:
            server_name: Which server to call.
            tool_name: Name of the tool to invoke.
            args: Arguments to pass to the tool.

        Returns:
            Tool result as a string.
        """
        if server_name not in self._clients:
            raise ValueError(f"MCP server '{server_name}' not connected")

        result = await self._clients[server_name].call_tool(
            tool_name, args or {}
        )

        # Extract text from result
        if isinstance(result, dict) and "content" in result:
            contents = result["content"]
            if isinstance(contents, list):
                return "\n".join(
                    c.get("text", str(c)) if isinstance(c, dict) else str(c)
                    for c in contents
                )
            return str(contents)
        return str(result)

    @property
    def connected_servers(self) -> list[str]:
        """Names of currently connected MCP servers."""
        return list(self._clients.keys())

    @property
    def is_connected(self) -> bool:
        """True if any MCP servers are connected."""
        return len(self._clients) > 0
