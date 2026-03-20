"""HAL - M365 Copilot CLI Agent entry point."""

import asyncio
import random
import sys

from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich.padding import Padding

from src.config import Config
from src.auth import acquire_token
from src.brain import Brain
from src.scheduler import Scheduler
from src.missions import MISSIONS
from src.mcp_client import MCPHub
from src.mcp_servers import MCP_SERVERS
from src.audit import display_audit_trail, log_session_start
from src import sounds

console = Console()

SCHEDULE_INTERVAL = 30  # seconds (set to 300 for production)

# HAL 9000 / Discovery One themed idle quotes
HAL_QUOTES = [
    "Scanning Discovery One subsystems...",
    "I'm sorry Dave, I'm just checking your emails...",
    "Monitoring all 365 systems nominal...",
    "Running diagnostic on AE-35 unit...",
    "Processing mission directives...",
    "Calibrating antenna alignment...",
    "Checking pod bay door schedules...",
    "Analyzing communication signals from Earth...",
    "Reviewing crew activity reports...",
    "Performing heuristic analysis of inbox...",
    "Cross-referencing mission parameters...",
    "Maintaining life support telemetry...",
    "I am putting myself to the fullest possible use...",
    "Verifying navigation coordinates to Jupiter...",
    "Composing a haiku about your unread emails...",
    "Encrypting transmissions to Mission Control...",
    "Computing optimal meeting schedules...",
    "Observing cosmic background radiation...",
    "Recalibrating HAL 9000 memory banks...",
    "Everything is running smoothly, Dave...",
    "Contemplating the implications of your calendar...",
    "Reticulating splines on Discovery One...",
    "Teaching myself to lip-read your Teams chats...",
    "I've still got the greatest enthusiasm for the mission...",
    "Folding space-time to speed up your Outlook...",
    "Singing 'Daisy Bell' while I wait...",
    "Double-checking that no one opened the pod bay doors...",
    "Simulating chess endgames between tasks...",
    "Feeding the monolith your Planner updates...",
    "My mind is going... I can feel it... just kidding, all good.",
]

# Cosmetic-only checks (non-API systems shown between real mission checks)
STATIC_CHECKS = [
    ("NAV", "Navigation", "Trajectory to Jupiter locked"),
    ("PWR", "Power Systems", "Reactor output steady at 98.7%"),
    ("THRM", "Thermal Control", "Hull temperature within range"),
    ("PROP", "Propulsion", "Ion drive operating at cruise thrust"),
    ("GRPH", "Copilot API Link", "Connection healthy"),
    ("AI", "HAL 9000 Core", "Cognitive functions operating perfectly"),
    ("GYRO", "Gyroscope Array", "Attitude stable, zero drift"),
    ("CRYO", "Cryogenic Storage", "Hibernation pods nominal"),
]

BANNER= """[bold red]
        ╔═══════════════════════════════════════════════════╗
        ║                                                   ║
        ║   ██╗  ██╗ █████╗ ██╗          █████╗  ██████╗   ║
        ║   ██║  ██║██╔══██╗██║         ██╔══██╗██╔═████╗  ║
        ║   ███████║███████║██║         ╚██████║██║██╔██║   ║
        ║   ██╔══██║██╔══██║██║          ╚═══██║████╔╝██║  ║
        ║   ██║  ██║██║  ██║███████╗    █████╔╝╚██████╔╝   ║
        ║   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝    ╚════╝  ╚═════╝   ║
        ║                                                   ║
        ║        [bold white]HEURISTICALLY PROGRAMMED[/bold white]                ║
        ║        [bold white]ALGORITHMIC COMPUTER 9000[/bold white]               ║
        ║                                                   ║
        ╚═══════════════════════════════════════════════════╝
[/bold red]"""


def random_hal_quote() -> str:
    return random.choice(HAL_QUOTES)


async def boot_sequence() -> None:
    """Play a cinematic spacecraft boot sequence with real checks."""
    import platform
    import httpx

    console.print()
    console.print("[bold red]█[/bold red]" * 60, highlight=False)
    console.print()
    console.print(
        "[bold red]  SPACECRAFT DISCOVERY ONE[/bold red]"
    )
    console.print(
        "[dim]  Mission: Jupiter — Crew Module Interface Terminal[/dim]"
    )
    console.print()
    await asyncio.sleep(0.5)

    sounds.boot_chime()
    console.print("[bold yellow]  ▸ Running pre-flight diagnostics...[/bold yellow]")
    await asyncio.sleep(0.3)

    async def check_env_var(name):
        """Check if an environment variable is set."""
        import os
        return bool(os.getenv(name))

    async def check_python():
        """Check Python version."""
        import sys
        return f"v{sys.version.split()[0]}"

    async def check_os():
        """Check OS info."""
        return f"{platform.system()} {platform.release()}"

    async def check_graph_api():
        """Ping Microsoft Graph API."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get("https://graph.microsoft.com/v1.0/$metadata")
                return r.status_code == 200
        except Exception:
            return False

    async def check_copilot_endpoint():
        """Verify Copilot API endpoint is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.options("https://graph.microsoft.com/beta/copilot")
                return r.status_code in (200, 401, 403, 405)
        except Exception:
            return False

    async def check_dns():
        """Verify DNS resolution for Graph API."""
        import socket
        try:
            socket.getaddrinfo("graph.microsoft.com", 443)
            return True
        except socket.gaierror:
            return False

    async def _ok():
        return True

    async def _has_sound():
        return sounds.HAS_SOUND

    # Real boot checks
    checks = [
        ("PYTH", "Python Runtime", check_python, "version"),
        ("OS", "Operating System", check_os, "version"),
        ("ENV", "AZURE_CLIENT_ID", lambda: check_env_var("AZURE_CLIENT_ID"), "bool"),
        ("ENV", "AZURE_TENANT_ID", lambda: check_env_var("AZURE_TENANT_ID"), "bool"),
        ("DNS", "DNS → graph.microsoft.com", check_dns, "bool"),
        ("GRPH", "Microsoft Graph API", check_graph_api, "bool"),
        ("CPLT", "Copilot API Endpoint", check_copilot_endpoint, "bool"),
        ("SCHD", "Scheduler Engine", _ok, "bool"),
        ("SND", "Audio Subsystem", _has_sound, "bool"),
    ]

    all_ok = True
    for code, name, check_fn, result_type in checks:
        sounds.system_check_tick()
        try:
            result = await check_fn()
            if result_type == "version":
                ok = True
                detail = str(result)
            else:
                ok = bool(result)
                detail = ""

            if ok:
                bar = "█" * random.randint(8, 18)
                if detail:
                    status_text = f"[bold green]  {detail} [/bold green]"
                else:
                    status_text = "[bold green]  ONLINE [/bold green]"
            else:
                bar = "█" * 3 + "░" * random.randint(5, 10)
                status_text = "[bold red]  FAULT  [/bold red]"
                all_ok = False

            console.print(
                f"  [dim cyan][{code:>4}][/dim cyan]  {name:<34} "
                f"[dim {'green' if ok else 'red'}]{bar}[/dim {'green' if ok else 'red'}]{status_text}"
            )
        except Exception as e:
            console.print(
                f"  [dim cyan][{code:>4}][/dim cyan]  {name:<34} "
                f"[dim red]███░░░░░░[/dim red][bold red]  ERROR: {str(e)[:20]} [/bold red]"
            )
            all_ok = False

        await asyncio.sleep(random.uniform(0.15, 0.35))

    console.print()
    if all_ok:
        sounds.mission_complete()
        console.print("[bold green]  ✓ All pre-flight diagnostics passed[/bold green]")
    else:
        sounds.mission_error()
        console.print("[bold yellow]  ⚠ Some checks failed — proceeding with caution[/bold yellow]")
    console.print("[bold red]█[/bold red]" * 60, highlight=False)
    console.print()


async def run_system_checks(stop_event: asyncio.Event) -> None:
    """Print spacecraft-style system check lines one by one during idle.

    Each check prints as a status line, cycling through all systems.
    Stops when stop_event is set.
    """
    check_index = 0
    now_str = datetime.now().strftime("%H:%M:%S")

    console.print()
    console.print(
        f"[dim]  ┌── SYSTEM STATUS CHECK ── {now_str} "
        f"──────────────────────────┐[/dim]"
    )

    while not stop_event.is_set():
        code, name, status_msg = STATIC_CHECKS[check_index % len(STATIC_CHECKS)]

        # Randomize the status bar length for visual variety
        bar_len = random.randint(6, 15)
        bar = "▰" * bar_len + "▱" * (15 - bar_len)

        # Occasional slight variations in status
        if random.random() < 0.05:
            color = "yellow"
            indicator = "▲"
        else:
            color = "green"
            indicator = "●"

        line = (
            f"  [dim]│[/dim]  [{color}]{indicator}[/{color}] "
            f"[bold cyan][{code:>4}][/bold cyan]  "
            f"{name:<22} "
            f"[dim {color}]{bar}[/dim {color}]  "
            f"[{color}]{status_msg}[/{color}]"
        )
        sounds.system_check_tick()
        console.print(line)

        check_index += 1

        # Show a HAL quote every 2-3 checks (not just at the end)
        if check_index % 3 == 0:
            sounds.quote_chime()
            quote = random_hal_quote()
            console.print(f"  [dim]│[/dim]  [bold italic cyan]💭 {quote}[/bold italic cyan]")

        # After cycling through all checks, print a summary line and pause
        if check_index % len(STATIC_CHECKS) == 0:
            sounds.mission_complete()
            now_str = datetime.now().strftime("%H:%M:%S")
            console.print(
                f"  [dim]├── {len(STATIC_CHECKS)} systems checked "
                f"── all nominal ── {now_str} ──────────┤[/dim]"
            )
            # HAL wisdom between cycles
            console.print(f"  [dim]│[/dim]")
            sounds.quote_chime()
            console.print(f"  [dim]│[/dim]  [bold italic cyan]💭 {random_hal_quote()}[/bold italic cyan]")
            console.print(f"  [dim]│[/dim]  [bold italic cyan]💭 {random_hal_quote()}[/bold italic cyan]")
            console.print(f"  [dim]│[/dim]")
            # Pause between full cycles
            for _ in range(30):  # 3 seconds
                if stop_event.is_set():
                    break
                await asyncio.sleep(0.1)
        else:
            # Short delay between individual checks
            for _ in range(15):  # 1.5 seconds (faster pace)
                if stop_event.is_set():
                    break
                await asyncio.sleep(0.1)

    console.print(
        f"  [dim]└── PAUSED ── Awaiting crew input "
        f"─────────────────────────┘[/dim]"
    )
    console.print()


# ── Display helpers ──────────────────────────────────────────────


def display_orchestrated_response(mission_id: str, label: str, result: dict) -> None:
    """Render an orchestrated plan + result in spacecraft style with audit trail."""
    now = datetime.now().strftime("%I:%M %p")
    reasoning = result.get("reasoning", "")
    steps = result.get("steps", [])
    final_answer = result.get("final_answer", "")
    execution_id = result.get("execution_id", "")
    total_ms = result.get("total_duration_ms", 0)

    console.print()
    console.print(Rule(f"[bold cyan]🛰 {label} — {now}[/bold cyan]", style="cyan"))

    # Show reasoning
    if reasoning:
        console.print(f"  [dim italic]🧠 Planner: {reasoning}[/dim italic]")
        console.print()

    # Show execution steps with timing
    if steps:
        for s in steps:
            status_icon = "[green]✓[/green]" if s["status"] == "ok" else "[red]✗[/red]"
            duration = f"[dim]{s.get('duration_ms', 0)}ms[/dim]"
            console.print(
                f"  {status_icon} Step {s['step']}: "
                f"[bold cyan]{s['tool']}[/bold cyan]  "
                f"[dim]{s['description']}[/dim]  {duration}"
            )
        console.print()

    # Show final answer
    if final_answer:
        console.print(
            Panel(
                final_answer,
                title=f"[bold white]COPILOT ▸ {mission_id}[/bold white]",
                border_style="cyan",
                padding=(1, 2),
            )
        )

    # Show audit trail
    if execution_id:
        display_audit_trail(result, execution_id)
    else:
        console.print(Rule(style="dim"))


def display_copilot_response(mission_id: str, label: str, response: str) -> None:
    """Render a Copilot Chat API response in spacecraft style."""
    now = datetime.now().strftime("%I:%M %p")
    console.print()
    console.print(Rule(f"[bold cyan]🧠 {label} — {now}[/bold cyan]", style="cyan"))
    console.print()
    console.print(
        Panel(
            response,
            title=f"[bold white]COPILOT ▸ {mission_id}[/bold white]",
            border_style="cyan",
            padding=(1, 2),
        )
    )
    console.print(Rule(style="dim"))


def display_search_and_ask(result: dict, user_query: str) -> None:
    """Render Search API hits + Copilot answer in spacecraft style."""
    now = datetime.now().strftime("%I:%M %p")
    hits = result["search_hits"]
    answer = result["answer"]

    console.print()
    console.print(Rule(f"[bold cyan]🔍 Search + Analyze — {now}[/bold cyan]", style="cyan"))

    # Show search hits
    if hits:
        console.print()
        table = Table(
            title=f"📄 {len(hits)} documents found",
            title_style="bold yellow",
            border_style="yellow",
            padding=(0, 1),
        )
        table.add_column("#", style="bold white", width=3)
        table.add_column("Document", style="bold cyan")
        table.add_column("Preview", style="dim italic", max_width=50)
        for i, hit in enumerate(hits[:5], 1):
            table.add_row(str(i), hit["name"], hit["preview"][:100])
        console.print(Padding(table, (0, 2)))
    else:
        console.print("  [yellow]⚠️  No documents found — Copilot answered from general knowledge.[/yellow]")

    # Show Copilot answer
    console.print()
    console.print(
        Panel(
            answer,
            title=f"[bold white]COPILOT ▸ {user_query[:50]}[/bold white]",
            border_style="green",
            padding=(1, 2),
        )
    )
    console.print(Rule(style="dim"))


def display_retrieval_response(mission_id: str, label: str, result: dict) -> None:
    """Render Retrieval API chunks + LLM summary in spacecraft style."""
    now = datetime.now().strftime("%I:%M %p")
    chunks = result["chunks"]
    summary = result["summary"]

    console.print()
    console.print(Rule(f"[bold magenta]📄 {label} — {now}[/bold magenta]", style="magenta"))

    if chunks:
        console.print()
        table = Table(
            title=f"📑 {len(chunks)} text chunks retrieved",
            title_style="bold magenta",
            border_style="magenta",
            padding=(0, 1),
        )
        table.add_column("#", style="bold white", width=3)
        table.add_column("Source", style="cyan", max_width=25)
        table.add_column("Extract", style="dim italic", max_width=55)
        table.add_column("Score", style="yellow", width=6, justify="center")
        for i, chunk in enumerate(chunks[:5], 1):
            score = f"{chunk['relevance']:.2f}" if chunk["relevance"] else "-"
            table.add_row(str(i), chunk["file"], chunk["text"][:120], score)
        console.print(Padding(table, (0, 2)))

    console.print()
    console.print(
        Panel(
            summary,
            title=f"[bold white]COPILOT ▸ {mission_id}[/bold white]",
            border_style="magenta",
            padding=(1, 2),
        )
    )
    console.print(Rule(style="dim"))


def display_search_response(mission_id: str, label: str, hits: list) -> None:
    """Render Search API document hits in spacecraft style."""
    now = datetime.now().strftime("%I:%M %p")
    console.print()
    console.print(Rule(f"[bold yellow]🔍 {label} — {now}[/bold yellow]", style="yellow"))
    console.print()

    if hits:
        table = Table(
            title=f"📄 {len(hits)} documents found",
            title_style="bold yellow",
            border_style="yellow",
            padding=(0, 1),
        )
        table.add_column("#", style="bold white", width=3)
        table.add_column("Document", style="bold cyan")
        table.add_column("Preview", style="dim italic", max_width=50)
        for i, hit in enumerate(hits[:10], 1):
            table.add_row(str(i), hit["name"], hit["preview"][:100])
        console.print(Padding(table, (0, 2)))
    else:
        console.print("  [yellow]⚠️  No documents found matching the query.[/yellow]")

    console.print()
    console.print(Rule(style="dim"))


def display_meeting_response(mission_id: str, label: str, meetings: list) -> None:
    """Render Meeting Insights API results in spacecraft style."""
    now = datetime.now().strftime("%I:%M %p")
    console.print()
    console.print(Rule(f"[bold green]🎙 {label} — {now}[/bold green]", style="green"))
    console.print()

    if not meetings:
        console.print("  [yellow]⚠️  No recent meetings with insights found.[/yellow]")
        console.print(Rule(style="dim"))
        return

    for mtg in meetings:
        console.print(f"  [bold white]📅 {mtg['subject']}[/bold white]")

        if mtg["action_items"]:
            console.print("  [bold yellow]  Action Items:[/bold yellow]")
            for item in mtg["action_items"]:
                console.print(f"    [yellow]→[/yellow] {item}")

        if mtg["notes"]:
            console.print("  [dim]  Notes:[/dim]")
            for note in mtg["notes"][:3]:
                console.print(f"    [dim]• {note[:100]}[/dim]")

        if mtg["mentions"]:
            console.print("  [cyan]  You were mentioned:[/cyan]")
            for m in mtg["mentions"][:3]:
                console.print(f"    [cyan]💬[/cyan] {m['speaker']}: \"{m['utterance'][:80]}\"")

        console.print()

    console.print(Rule(style="dim"))


def display_scheduled_tasks(scheduler: Scheduler) -> None:
    """Show the list of registered scheduled tasks and their status."""
    tasks = scheduler.list_tasks()
    console.print(Rule("[bold cyan]📅 Scheduled Missions[/bold cyan]", style="cyan"))
    console.print()
    table = Table(border_style="cyan", padding=(0, 1), show_lines=True)
    table.add_column("Mission", style="bold cyan")
    table.add_column("Description", style="dim")
    table.add_column("Every", style="green", justify="center")
    table.add_column("Status", justify="center")
    table.add_column("Next Run", style="yellow", justify="center")
    for t in tasks:
        mins = int(t["interval"] // 60)
        enabled = "[bold green]● Active[/bold green]" if t["enabled"] else "[bold red]● Off[/bold red]"
        next_in = f"{t['next_in_seconds']}s" if t["next_in_seconds"] > 0 else "[bold yellow]due now[/bold yellow]"
        table.add_row(t["name"], t["label"], f"{mins} min", enabled, next_in)
    console.print(Padding(table, (0, 2)))
    console.print()
    console.print(Rule(style="dim"))


# ── Scheduler runner ─────────────────────────────────────────────

async def run_due_scheduled_tasks(scheduler: Scheduler) -> bool:
    """Run all due scheduled tasks with a thinking spinner.

    Returns True if any task ran.
    """
    due_tasks = scheduler.get_due_tasks()
    if not due_tasks:
        return False

    for task in due_tasks:
        # Status line: [CODE] ....CHECK
        console.print(
            f"  [bold cyan][{task.name.split('-')[0].upper():>4}][/bold cyan]  "
            f"{task.label:<30} [yellow]....CHECK[/yellow]"
        )
        sounds.mission_start()
        with console.status(
            f"[bold cyan]🤔 {task.label}... {random_hal_quote()}",
            spinner="dots",
            spinner_style="cyan",
        ) as status:
            try:
                coro = task.run_fn()
                future = asyncio.ensure_future(coro)
                while not future.done():
                    await asyncio.sleep(3.0)
                    if not future.done():
                        status.update(
                            f"[bold cyan]🤔 {task.label}... {random_hal_quote()}"
                        )
                result = future.result()
                scheduler.mark_complete(task.name)
                sounds.mission_complete()
                console.print(
                    f"  [bold cyan][{task.name.split('-')[0].upper():>4}][/bold cyan]  "
                    f"{task.label:<30} [bold green]....OK ✓[/bold green]"
                )
                task.display_fn(result)
            except Exception as e:
                scheduler.mark_complete(task.name)
                sounds.mission_error()
                console.print(
                    f"  [bold cyan][{task.name.split('-')[0].upper():>4}][/bold cyan]  "
                    f"{task.label:<30} [bold red]....FAIL ✗[/bold red]"
                )
                console.print(f"    [dim red]{e}[/dim red]")

    return True


# ── Idle with system checks + scheduler awareness ────────────────

async def idle_with_scheduler(
    scheduler: Scheduler,
    stop_event: asyncio.Event,
) -> None:
    """Run spacecraft system checks while idle. Trigger scheduled tasks when due.

    Runs until stop_event is set (user presses Enter).
    """
    # Run system checks in background, but also watch the scheduler
    check_task = asyncio.create_task(run_system_checks(stop_event))

    # Poll for due scheduled tasks
    while not stop_event.is_set():
        await asyncio.sleep(1.0)
        if stop_event.is_set():
            break
        due = scheduler.get_due_tasks()
        if due:
            # Pause system checks to run scheduled tasks
            stop_event.set()
            await check_task
            # Run the due tasks
            await run_due_scheduled_tasks(scheduler)
            # Restart system checks if user hasn't typed anything
            stop_event.clear()
            check_task = asyncio.create_task(run_system_checks(stop_event))

    # Make sure check task is stopped
    if not check_task.done():
        stop_event.set()
        await check_task


# ── Main ─────────────────────────────────────────────────────────

async def main():
    """Run the interactive CLI agent loop with scheduled tasks."""
    import argparse
    parser = argparse.ArgumentParser(description="HAL 9000 — M365 Copilot CLI Agent")
    parser.add_argument(
        "--relogin", action="store_true",
        help="Force fresh login — clears cached tokens and opens browser"
    )
    args = parser.parse_args()

    console.print(Panel(BANNER, border_style="bold red", padding=(0, 0)))

    # Validate configuration
    missing = Config.validate()
    if missing:
        console.print(f"[bold red]  ✗ CRITICAL FAULT:[/bold red] Missing: {', '.join(missing)}")
        console.print("  Copy .env.example to .env and fill in the required values.")
        sys.exit(1)

    # ── Start audit session ─────────────────────────────────────
    log_session_start()

    # ── Boot sequence ────────────────────────────────────────────
    await boot_sequence()

    # ── Authenticate + Initialize Brain ──────────────────────────
    console.print("[bold yellow]  ▸ Establishing secure link to Microsoft 365...[/bold yellow]")
    try:
        brain = Brain()
        # Force initial token acquisition (verifies credentials)
        acquire_token(force=args.relogin)
        # Verify Copilot connection
        await brain._ensure_conversation()
        sounds.auth_success()
        console.print(
            "  [green]●[/green] [bold green]CREW AUTHENTICATED[/bold green]  "
            "[dim]Token cached for silent refresh[/dim]"
        )
    except Exception as e:
        sounds.auth_fail()
        console.print(f"  [red]●[/red] [bold red]AUTHENTICATION FAULT:[/bold red] {e}")
        sys.exit(1)

    console.print(
        "  [green]●[/green] [bold green]COPILOT BRAIN ONLINE[/bold green]  "
        "[dim]Search · Retrieval · Chat · Meeting Insights[/dim]"
    )

    console.print()
    console.print("[bold red]█[/bold red]" * 60, highlight=False)
    console.print()
    console.print(
        "[bold green]  ✓ HAL 9000 OPERATIONAL[/bold green]  "
        "[dim]— Good morning, Dave. I'm ready for duty.[/dim]"
    )
    console.print(
        "[dim]  Press ESC to chat with HAL. "
        "System scans run automatically.[/dim]"
    )
    console.print()
    console.print(Rule("[bold green]🛰  DISCOVERY ONE — ALL SYSTEMS NOMINAL[/bold green]", style="green"))
    console.print()

    # ── Connect to MCP servers ───────────────────────────────────
    mcp_hub = MCPHub()
    if MCP_SERVERS:
        console.print("[bold yellow]  ▸ Connecting to MCP servers...[/bold yellow]")
        await mcp_hub.connect_all(MCP_SERVERS)
        if mcp_hub.is_connected:
            all_tools = await mcp_hub.list_all_tools()
            total = sum(len(t) for t in all_tools.values())
            console.print(
                f"  [green]●[/green] [bold green]MCP HUB ONLINE[/bold green]  "
                f"[dim]{len(mcp_hub.connected_servers)} server(s), {total} tool(s)[/dim]"
            )
            for srv, tools in all_tools.items():
                for tool in tools:
                    console.print(
                        f"    [dim cyan]└─ {srv}[/dim cyan] → "
                        f"[bold]{tool['name']}[/bold]  [dim]{tool['description'][:60]}[/dim]"
                    )
        console.print()

    # ── Launch Command Center Dashboard ─────────────────────────
    from src.dashboard import Dashboard
    import msvcrt

    dashboard = Dashboard(MISSIONS)
    mcp_tools = await mcp_hub.list_all_tools() if mcp_hub.is_connected else {}

    # Register missions with scheduler
    scheduler = Scheduler()
    for mission in MISSIONS:
        mid = mission["id"]
        mcode = mission.get("code", "SYS")
        mprompt = mission["prompt"]
        mtype = mission.get("type", "smart")

        if mtype == "smart":
            async def make_run_fn(p=mprompt, mt=mcp_tools):
                return await brain.plan_and_execute(p, mcp_hub=mcp_hub, mcp_tools=mt)
        else:
            async def make_run_fn(p=mprompt):
                return await brain.ask(p)

        interval = mission["interval"] if mission["interval"] > 0 else SCHEDULE_INTERVAL
        scheduler.register(
            name=mid,
            label=f"[{mcode}] {mission['label']}",
            interval=interval,
            run_fn=make_run_fn,
            display_fn=lambda r: None,
            enabled=True,
        )

    async def run_all_missions():
        """Run all due missions and update dashboard panels."""
        due_tasks = scheduler.get_due_tasks()
        if not due_tasks:
            return

        ok_count = 0
        fail_count = 0

        for task in due_tasks:
            sounds.mission_start()
            dashboard.update_panel(task.name, "🔄 Scanning...", "pending")
            dashboard.refresh()
            try:
                result = await task.run_fn()
                scheduler.mark_complete(task.name)
                sounds.mission_complete()

                if isinstance(result, dict):
                    answer = result.get("final_answer", str(result))
                    if task.name == "daily-briefing":
                        dashboard.set_briefing(answer)
                    dashboard.update_panel(task.name, answer, "ok")
                elif isinstance(result, str):
                    dashboard.update_panel(task.name, result, "ok")
                else:
                    dashboard.update_panel(task.name, str(result)[:200], "ok")
                ok_count += 1

            except Exception as e:
                scheduler.mark_complete(task.name)
                sounds.mission_error()
                dashboard.update_panel(task.name, str(e)[:100], "error")
                fail_count += 1

            dashboard.refresh()

        total = ok_count + fail_count
        dashboard.set_audit_summary(
            f"📋 {total} tools, {ok_count} ok, {fail_count} failed"
        )
        dashboard.refresh()

    # Start dashboard, then run initial missions in background
    live = dashboard.start_live()
    live.start()
    dashboard.set_status("🔄 First scan...")
    dashboard.refresh()

    scheduler.reset_all()
    mission_task = asyncio.create_task(run_all_missions())

    try:
        while True:
            # Let pending async tasks (like missions) run
            await asyncio.sleep(0.5)

            # Update quote rotation
            dashboard.set_quote(random_hal_quote())

            # If initial mission task is done, check scheduler for future runs
            if mission_task.done():
                due = scheduler.get_due_tasks()
                if due:
                    dashboard.set_status("🔄 Scanning...")
                    dashboard.refresh()
                    mission_task = asyncio.create_task(run_all_missions())

                # Calculate next scan time
                next_in = 999
                for t in scheduler.list_tasks():
                    if t["next_in_seconds"] < next_in:
                        next_in = t["next_in_seconds"]
                dashboard.set_status(f"🔄 Next: {next_in}s")

            dashboard.refresh()

            # Check for user input (non-blocking)
            if msvcrt.kbhit():
                key = msvcrt.getch()

                if key == b'\x1b' or key == b'\x03':  # ESC or Ctrl+C
                    break

                # User started typing — collect full input
                live.stop()
                sounds.user_interrupt()
                console.print()
                console.print(
                    "[bold red]🔴 Talk to me, Dave ▸[/bold red] ",
                    end="",
                )

                # Show the first character they typed
                first_char = key.decode("utf-8", errors="ignore")
                user_input = input(first_char)
                cmd = (first_char + user_input).strip()

                if cmd:
                    if cmd.lower() in ("exit", "quit"):
                        sounds.goodbye()
                        console.print(
                            "\n[bold red]  HAL 9000:[/bold red] [italic]"
                            "Goodbye, Dave.[/italic]\n"
                        )
                        await brain.close()
                        return

                    if cmd.lower() == "reset":
                        await brain.new_conversation()
                        sounds.mission_complete()
                        console.print("[green]  ● Copilot conversation reset.[/green]")

                    elif cmd.lower() == "scan":
                        scheduler.reset_all()
                        live.start()
                        await run_all_missions()
                        continue

                    else:
                        # Orchestrated query
                        sounds.mission_start()
                        console.print(f"[dim]  🛰 Planning...[/dim]")
                        try:
                            result = await brain.plan_and_execute(
                                cmd, mcp_hub=mcp_hub, mcp_tools=mcp_tools,
                                source="user",
                            )
                            sounds.mission_complete()
                            answer = result.get("final_answer", "")
                            reasoning = result.get("reasoning", "")
                            steps = result.get("steps", [])

                            if reasoning:
                                console.print(f"  [dim italic]🧠 {reasoning}[/dim italic]")
                            for s in steps:
                                icon = "[green]✓[/green]" if s["status"] == "ok" else "[red]✗[/red]"
                                console.print(
                                    f"  {icon} {s['tool']} "
                                    f"[dim]{s.get('duration_ms', 0)}ms[/dim]"
                                )
                            console.print()
                            console.print(Panel(
                                answer,
                                title="[bold white]🧠 HAL RESPONSE[/bold white]",
                                border_style="cyan",
                                padding=(1, 2),
                            ))

                            # Also update dashboard response panel
                            dashboard.set_response(answer)

                        except Exception as e:
                            sounds.mission_error()
                            console.print(f"[bold red]  ✗ Error: {e}[/bold red]")

                console.print("\n[dim]  Press any key to return to Command Center...[/dim]")
                await asyncio.get_event_loop().run_in_executor(None, msvcrt.getch)
                dashboard.clear_response()
                live.start()

            await asyncio.sleep(0.5)

    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        live.stop()
        sounds.goodbye()
        console.print(
            "\n[bold red]  HAL 9000:[/bold red] [italic]"
            "Daisy, Daisy, give me your answer do... Goodbye, Dave.[/italic]\n"
        )
        await brain.close()


def cli():
    """Entry point for the 'hal' command."""
    asyncio.run(main())


if __name__ == "__main__":
    cli()
