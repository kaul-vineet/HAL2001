"""HAL Agent - Command dispatcher for M365 operations."""

import asyncio
import json
from rich.console import Console
from rich.table import Table

from services.teams import TeamsService
from services.planner import PlannerService
from services.mail import MailService
from services.sharepoint import SharePointService

console = Console()

HELP_TEXT = """
[bold cyan]HAL Agent Commands[/bold cyan]

[bold]Teams[/bold]
  teams list-teams              List your joined teams
  teams list-channels <team_id> List channels in a team
  teams send <team_id> <channel_id> <message>
                                Send a message to a channel

[bold]Planner[/bold]
  planner my-tasks              List tasks assigned to you
  planner list-plans <group_id> List plans for a team/group
  planner create <plan_id> <title> [bucket_id]
                                Create a new task

[bold]Mail[/bold]
  mail inbox [count]            Show recent inbox messages
  mail send <to> <subject> <body>
                                Send an email (comma-separated recipients)

[bold]SharePoint[/bold]
  sp list-sites [query]         Search SharePoint sites
  sp list-files <site_id> [path]
                                List files in a document library
  sp recent <site_id>           Show recently modified documents
  sp search <query>             Search across all documents

[bold]General[/bold]
  help                          Show this help
  whoami                        Show current user info
  exit / quit                   Exit HAL
"""


class Agent:
    """Command dispatcher that routes instructions to M365 services."""

    def __init__(self, graph_client):
        self.client = graph_client
        self.teams = TeamsService(graph_client)
        self.planner = PlannerService(graph_client)
        self.mail = MailService(graph_client)
        self.sharepoint = SharePointService(graph_client)

    async def handle(self, command: str) -> None:
        """Parse and dispatch a command string."""
        parts = command.strip().split(maxsplit=1)
        if not parts:
            return

        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        try:
            if cmd == "help":
                console.print(HELP_TEXT)
            elif cmd == "whoami":
                await self._whoami()
            elif cmd == "teams":
                await self._handle_teams(args)
            elif cmd == "planner":
                await self._handle_planner(args)
            elif cmd == "mail":
                await self._handle_mail(args)
            elif cmd == "sp":
                await self._handle_sharepoint(args)
            elif cmd in ("exit", "quit"):
                raise SystemExit
            else:
                console.print(f"[red]Unknown command:[/red] {cmd}. Type [bold]help[/bold] for available commands.")
        except SystemExit:
            raise
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

    async def _whoami(self):
        """Display current user information."""
        user = await self.client.me.get()
        table = Table(title="Current User")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Name", user.display_name or "N/A")
        table.add_row("Email", user.mail or user.user_principal_name or "N/A")
        table.add_row("ID", user.id or "N/A")
        console.print(table)

    # ── Teams ────────────────────────────────────────────────────────

    async def _handle_teams(self, args: str):
        parts = args.split(maxsplit=3)
        if not parts:
            console.print("[yellow]Usage: teams <list-teams|list-channels|send>[/yellow]")
            return

        subcmd = parts[0].lower()

        if subcmd == "list-teams":
            teams = await self.teams.list_joined_teams()
            table = Table(title="Your Teams")
            table.add_column("Name", style="cyan")
            table.add_column("ID", style="dim")
            for t in teams:
                table.add_row(t["name"], t["id"])
            console.print(table)

        elif subcmd == "list-channels":
            if len(parts) < 2:
                console.print("[yellow]Usage: teams list-channels <team_id>[/yellow]")
                return
            channels = await self.teams.list_channels(parts[1])
            table = Table(title="Channels")
            table.add_column("Name", style="cyan")
            table.add_column("ID", style="dim")
            for c in channels:
                table.add_row(c["name"], c["id"])
            console.print(table)

        elif subcmd == "send":
            if len(parts) < 4:
                console.print("[yellow]Usage: teams send <team_id> <channel_id> <message>[/yellow]")
                return
            sub_parts = parts[1].split(maxsplit=2)
            if len(sub_parts) < 3:
                console.print("[yellow]Usage: teams send <team_id> <channel_id> <message>[/yellow]")
                return
            team_id, channel_id, message = sub_parts[0], sub_parts[1], sub_parts[2]
            msg_id = await self.teams.send_channel_message(team_id, channel_id, message)
            console.print(f"[green]✅ Message sent![/green] (ID: {msg_id})")
        else:
            console.print(f"[yellow]Unknown teams command: {subcmd}[/yellow]")

    # ── Planner ──────────────────────────────────────────────────────

    async def _handle_planner(self, args: str):
        parts = args.split(maxsplit=3)
        if not parts:
            console.print("[yellow]Usage: planner <my-tasks|list-plans|create>[/yellow]")
            return

        subcmd = parts[0].lower()

        if subcmd == "my-tasks":
            tasks = await self.planner.list_my_tasks()
            table = Table(title="My Planner Tasks")
            table.add_column("Title", style="cyan")
            table.add_column("Progress", style="green")
            table.add_column("ID", style="dim")
            for t in tasks:
                pct = f"{t['percent_complete']}%"
                table.add_row(t["title"], pct, t["id"])
            console.print(table)

        elif subcmd == "list-plans":
            if len(parts) < 2:
                console.print("[yellow]Usage: planner list-plans <group_id>[/yellow]")
                return
            plans = await self.planner.list_plans(parts[1])
            table = Table(title="Planner Plans")
            table.add_column("Title", style="cyan")
            table.add_column("ID", style="dim")
            for p in plans:
                table.add_row(p["title"], p["id"])
            console.print(table)

        elif subcmd == "create":
            sub_parts = args.split(maxsplit=3)
            if len(sub_parts) < 3:
                console.print("[yellow]Usage: planner create <plan_id> <title> [bucket_id][/yellow]")
                return
            plan_id = sub_parts[1]
            title = sub_parts[2]
            bucket_id = sub_parts[3] if len(sub_parts) > 3 else None
            task_id = await self.planner.create_task(plan_id, title, bucket_id)
            console.print(f"[green]✅ Task created![/green] (ID: {task_id})")
        else:
            console.print(f"[yellow]Unknown planner command: {subcmd}[/yellow]")

    # ── Mail ─────────────────────────────────────────────────────────

    async def _handle_mail(self, args: str):
        parts = args.split(maxsplit=3)
        if not parts:
            console.print("[yellow]Usage: mail <inbox|send>[/yellow]")
            return

        subcmd = parts[0].lower()

        if subcmd == "inbox":
            count = int(parts[1]) if len(parts) > 1 else 10
            messages = await self.mail.list_inbox(top=count)
            table = Table(title=f"Inbox (latest {count})")
            table.add_column("From", style="cyan", max_width=30)
            table.add_column("Subject", style="green")
            table.add_column("Received", style="dim")
            table.add_column("Read", style="dim")
            for m in messages:
                table.add_row(m["from"], m["subject"], m["received"], "✓" if m["read"] else "•")
            console.print(table)

        elif subcmd == "send":
            sub_parts = args.split(maxsplit=3)
            if len(sub_parts) < 4:
                console.print("[yellow]Usage: mail send <to_emails> <subject> <body>[/yellow]")
                console.print("[dim]  to_emails: comma-separated, e.g. user@org.com,user2@org.com[/dim]")
                return
            to_emails = [e.strip() for e in sub_parts[1].split(",")]
            subject = sub_parts[2]
            body = sub_parts[3]
            await self.mail.send_email(to_emails, subject, body)
            console.print(f"[green]✅ Email sent to {', '.join(to_emails)}![/green]")
        else:
            console.print(f"[yellow]Unknown mail command: {subcmd}[/yellow]")

    # ── SharePoint ───────────────────────────────────────────────────

    async def _handle_sharepoint(self, args: str):
        parts = args.split(maxsplit=2)
        if not parts:
            console.print("[yellow]Usage: sp <list-sites|list-files|recent|search>[/yellow]")
            return

        subcmd = parts[0].lower()

        if subcmd == "list-sites":
            query = parts[1] if len(parts) > 1 else "*"
            sites = await self.sharepoint.list_sites(query)
            table = Table(title="SharePoint Sites")
            table.add_column("Name", style="cyan")
            table.add_column("URL", style="green")
            table.add_column("ID", style="dim")
            for s in sites:
                table.add_row(s["name"], s["url"], s["id"])
            console.print(table)

        elif subcmd == "list-files":
            if len(parts) < 2:
                console.print("[yellow]Usage: sp list-files <site_id> [path][/yellow]")
                return
            site_id = parts[1]
            path = parts[2] if len(parts) > 2 else "root"
            items = await self.sharepoint.list_drive_items(site_id, path)
            table = Table(title="Documents")
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Size", style="dim")
            table.add_column("Modified", style="dim")
            for item in items:
                size = f"{item['size']:,}" if item["size"] else "-"
                table.add_row(item["name"], item["type"], size, item["modified"])
            console.print(table)

        elif subcmd == "recent":
            if len(parts) < 2:
                console.print("[yellow]Usage: sp recent <site_id>[/yellow]")
                return
            items = await self.sharepoint.get_recent_changes(parts[1])
            table = Table(title="Recently Modified")
            table.add_column("Name", style="cyan")
            table.add_column("Modified By", style="green")
            table.add_column("Modified", style="dim")
            for item in items:
                table.add_row(item["name"], item["modified_by"], item["modified"])
            console.print(table)

        elif subcmd == "search":
            if len(parts) < 2:
                console.print("[yellow]Usage: sp search <query>[/yellow]")
                return
            docs = await self.sharepoint.search_documents(parts[1])
            table = Table(title="Search Results")
            table.add_column("Name", style="cyan")
            table.add_column("Summary", style="green", max_width=50)
            table.add_column("URL", style="dim")
            for d in docs:
                table.add_row(d["name"], d["summary"], d["url"])
            console.print(table)
        else:
            console.print(f"[yellow]Unknown sp command: {subcmd}[/yellow]")
