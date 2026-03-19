"""HAL - M365 Copilot CLI Agent entry point."""

import asyncio
import random
import sys
import time

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.rule import Rule
from rich.columns import Columns
from rich.padding import Padding

from config import Config
from graph_client import create_graph_client
from agent import Agent
from scheduler import Scheduler

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

# Spacecraft system checks — cycled through in order during idle
SYSTEM_CHECKS = [
    ("NAV", "Navigation", "Trajectory to Jupiter locked"),
    ("TEAM", "Teams", "Uplink to Mission Control active"),
    ("ADO", "Azure DevOps", "Pipelines nominal, zero drift"),
    ("PWR", "Power Systems", "Reactor output steady at 98.7%"),
    ("THRM", "Thermal Control", "Hull temperature within range"),
    ("PROP", "Propulsion", "Ion drive operating at cruise thrust"),
    ("GRPH", "Microsoft Graph", "API connection healthy"),
    ("MAIL", "Outlook Inbox", "Monitoring for new messages"),
    ("SALE", "Sales", "CRM pod sealed and locked. Obviously."),
    ("PLAN", "Planner Tasks", "Tracking assigned items"),
    ("SHRP", "SharePoint Docs", "Watching for document changes"),
    ("AI", "HAL 9000 Core", "Cognitive functions operating perfectly"),
    ("ANTM", "Antenna Module", "Signal strength excellent"),
    ("GYRO", "Gyroscope Array", "Attitude stable, zero drift"),
    ("CRYO", "Cryogenic Storage", "Hibernation pods nominal"),
]

BANNER = """[bold red]
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
    """Play a cinematic spacecraft boot sequence."""
    import time as _time

    console.print()
    console.print("[bold red]█[/bold red]" * 60, highlight=False)
    console.print()
    console.print(
        "[bold red]  INDIAN SPACE RESEARCH ORGANISATION — SPACECRAFT DISCOVERY ONE[/bold red]"
    )
    console.print(
        "[dim]  Mission: Jupiter — Crew Module Interface Terminal[/dim]"
    )
    console.print()
    await asyncio.sleep(0.5)

    console.print("[bold yellow]  ▸ Initializing HAL 9000 core systems...[/bold yellow]")
    await asyncio.sleep(0.3)

    # System check sequence
    checks_boot = [
        ("BIOS", "HAL 9000 Firmware", True),
        ("MEM", "Memory Banks (1.5 TB)", True),
        ("CPU", "Neural Processing Unit", True),
        ("KERN", "Kernel v9000.3.1", True),
        ("NET", "Microsoft Graph API Link", True),
        ("AUTH", "Azure AD Authentication", True),
        ("SCHD", "Task Scheduler", True),
    ]

    for code, name, ok in checks_boot:
        bar = "█" * random.randint(8, 20)
        status_text = "[bold green]  ONLINE [/bold green]" if ok else "[bold red]  FAULT  [/bold red]"
        console.print(
            f"  [dim cyan][{code:>4}][/dim cyan]  {name:<30} "
            f"[dim green]{bar}[/dim green]{status_text}"
        )
        await asyncio.sleep(random.uniform(0.1, 0.3))

    console.print()
    console.print("[bold green]  ✓ All primary systems initialized[/bold green]")
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
        code, name, status_msg = SYSTEM_CHECKS[check_index % len(SYSTEM_CHECKS)]

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
        console.print(line)

        check_index += 1

        # After cycling through all checks, print a summary line and pause
        if check_index % len(SYSTEM_CHECKS) == 0:
            now_str = datetime.now().strftime("%H:%M:%S")
            console.print(
                f"  [dim]├── {len(SYSTEM_CHECKS)} systems checked "
                f"── all nominal ── {now_str} ──────────┤[/dim]"
            )
            # Longer pause between full cycles
            for _ in range(50):  # 5 seconds in 0.1s ticks
                if stop_event.is_set():
                    break
                await asyncio.sleep(0.1)

            if not stop_event.is_set():
                # Print a HAL quote between cycles
                quote = random_hal_quote()
                console.print(f"  [dim]│[/dim]  [bold italic cyan]💭 {quote}[/bold italic cyan]")
                console.print(f"  [dim]│[/dim]")
        else:
            # Short delay between individual checks
            for _ in range(20):  # 2 seconds in 0.1s ticks
                if stop_event.is_set():
                    break
                await asyncio.sleep(0.1)

    console.print(
        f"  [dim]└── PAUSED ── Awaiting crew input "
        f"─────────────────────────┘[/dim]"
    )
    console.print()


# ── Display helpers ──────────────────────────────────────────────

def display_email_scan(scan_result: dict) -> None:
    """Render the email scan results with highlighted reply-needed mails."""
    all_emails = scan_result["all"]
    needs_reply = scan_result["needs_reply"]
    now = datetime.now().strftime("%I:%M %p")

    # ── Divider ──────────────────────────────────────────────────
    console.print(Rule(f"[bold cyan]📡 Email Scan — {now}[/bold cyan]", style="cyan"))
    console.print()

    # ── Summary cards side by side ───────────────────────────────
    total_card = Panel(
        Text(f"📬  {len(all_emails)}", style="bold cyan", justify="center"),
        title="Total Today",
        border_style="cyan",
        width=25,
    )
    reply_card = Panel(
        Text(f"🔴  {len(needs_reply)}", style="bold red", justify="center"),
        title="Need Reply",
        border_style="red" if needs_reply else "green",
        width=25,
    )
    read_count = sum(1 for e in all_emails if e["read"])
    read_card = Panel(
        Text(f"✅  {read_count}", style="bold green", justify="center"),
        title="Already Read",
        border_style="green",
        width=25,
    )
    console.print(Columns([total_card, reply_card, read_card], padding=(0, 2)))
    console.print()

    # ── Emails that need a reply ─────────────────────────────────
    if needs_reply:
        table = Table(
            title="⚡ ACTION REQUIRED — Reply to these",
            title_style="bold red",
            border_style="red",
            show_lines=True,
            padding=(0, 1),
        )
        table.add_column("#", style="bold white", width=3)
        table.add_column("From", style="bold yellow", max_width=25)
        table.add_column("Subject", style="bold white")
        table.add_column("Preview", style="dim italic", max_width=45)
        table.add_column("Time", style="cyan", width=12)
        table.add_column("Flags", style="magenta", width=8)

        for i, email in enumerate(needs_reply, 1):
            flags = []
            if email["importance"].lower() == "high":
                flags.append("🔥")
            if email["is_flagged"]:
                flags.append("🚩")
            if email["has_attachments"]:
                flags.append("📎")
            received = email["received"]
            time_str = received[11:16] if len(received) > 16 else received
            table.add_row(
                str(i),
                email["from_name"] or email["from_addr"],
                email["subject"],
                email["preview"],
                time_str,
                " ".join(flags) if flags else "",
            )
        console.print(Padding(table, (0, 2)))
    else:
        console.print(
            Panel(
                "[bold green]✅ All clear! No emails need your immediate reply.[/bold green]",
                border_style="green",
                padding=(1, 2),
            )
        )

    # ── Other emails (read / CC'd) ──────────────────────────────
    other_emails = [e for e in all_emails if e not in needs_reply]
    if other_emails:
        console.print()
        console.print(Rule("[dim]Other emails today[/dim]", style="dim"))
        console.print()
        table = Table(
            border_style="dim",
            show_header=True,
            header_style="dim bold",
            padding=(0, 1),
        )
        table.add_column("From", style="dim", max_width=25)
        table.add_column("Subject")
        table.add_column("Status", width=8, justify="center")
        for email in other_emails[:15]:
            status = "[green]read[/green]" if email["read"] else "[yellow]● new[/yellow]"
            subj_style = "dim" if email["read"] else ""
            table.add_row(
                email["from_name"] or email["from_addr"],
                f"[{subj_style}]{email['subject']}[/{subj_style}]" if subj_style else email["subject"],
                status,
            )
        if len(other_emails) > 15:
            table.add_row("", f"[dim]... and {len(other_emails) - 15} more[/dim]", "")
        console.print(Padding(table, (0, 2)))

    console.print()
    console.print(Rule(style="dim"))


def display_scheduled_tasks(scheduler: Scheduler) -> None:
    """Show the list of registered scheduled tasks and their status."""
    tasks = scheduler.list_tasks()
    console.print(Rule("[bold cyan]📅 Scheduled Tasks[/bold cyan]", style="cyan"))
    console.print()
    table = Table(border_style="cyan", padding=(0, 1), show_lines=True)
    table.add_column("Task", style="bold cyan")
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
                task.display_fn(result)
            except Exception as e:
                scheduler.mark_complete(task.name)  # don't retry immediately
                console.print(f"[bold red]Scheduled task '{task.name}' failed:[/bold red] {e}")

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
    console.print(Panel(BANNER, border_style="bold red", padding=(0, 0)))

    # Validate configuration
    missing = Config.validate()
    if missing:
        console.print(f"[bold red]  ✗ CRITICAL FAULT:[/bold red] Missing: {', '.join(missing)}")
        console.print("  Copy .env.example to .env and fill in the required values.")
        sys.exit(1)

    # ── Boot sequence ────────────────────────────────────────────
    await boot_sequence()

    # ── Authenticate ─────────────────────────────────────────────
    console.print("[bold yellow]  ▸ Establishing secure link to Microsoft 365...[/bold yellow]")
    try:
        graph_client = create_graph_client()
        user = await graph_client.me.get()
        name = user.display_name
        email = user.mail or user.user_principal_name
        console.print(
            f"  [green]●[/green] [bold green]CREW AUTHENTICATED[/bold green]  "
            f"[bold white]{name}[/bold white]  [dim]<{email}>[/dim]"
        )
    except Exception as e:
        console.print(f"  [red]●[/red] [bold red]AUTHENTICATION FAULT:[/bold red] {e}")
        sys.exit(1)

    agent = Agent(graph_client)
    console.print()
    console.print("[bold red]█[/bold red]" * 60, highlight=False)
    console.print()
    console.print(
        "[bold green]  ✓ HAL 9000 OPERATIONAL[/bold green]  "
        "[dim]— Good morning, Dave. I'm ready for duty.[/dim]"
    )
    console.print(
        "[dim]  Type commands at the HAL > prompt. "
        "System checks run continuously.[/dim]"
    )
    console.print()
    console.print(Rule("[bold green]🛰  DISCOVERY ONE — ALL SYSTEMS NOMINAL[/bold green]", style="green"))
    console.print()

    # ── Set up scheduler ─────────────────────────────────────────
    scheduler = Scheduler()

    # Register scheduled tasks (add more here as needed)
    scheduler.register(
        name="email-scan",
        label="Scanning Discovery One inbox",
        interval=SCHEDULE_INTERVAL,
        run_fn=agent.mail.scan_todays_emails,
        display_fn=display_email_scan,
    )

    # ── Run all scheduled tasks immediately on startup ───────────
    scheduler.reset_all()
    await run_due_scheduled_tasks(scheduler)

    # ── Main loop: idle spinner + scheduler + user commands ──────
    session = PromptSession(
        history=InMemoryHistory(),
        auto_suggest=AutoSuggestFromHistory(),
    )

    while True:
        # Start idle spinner (also checks scheduler in background)
        stop_thinking = asyncio.Event()
        idle_task = asyncio.create_task(
            idle_with_scheduler(scheduler, stop_thinking)
        )

        try:
            command = await asyncio.get_event_loop().run_in_executor(
                None, lambda: session.prompt("HAL > ")
            )
        except (KeyboardInterrupt, EOFError):
            stop_thinking.set()
            await idle_task
            console.print()
            console.print(Rule(style="red"))
            console.print(
                "[bold red]  HAL 9000:[/bold red] [italic]Daisy, Daisy, "
                "give me your answer do... Goodbye, Dave.[/italic]"
            )
            console.print(Rule(style="red"))
            break

        # User typed something — stop the idle/scheduler loop
        stop_thinking.set()
        await idle_task

        if not command.strip():
            continue

        # Handle exit
        if command.strip().lower() in ("exit", "quit"):
            console.print()
            console.print(Rule(style="red"))
            console.print(
                "[bold red]  HAL 9000:[/bold red] [italic]This mission is too important "
                "for me to allow you to jeopardize it... Just kidding. Goodbye, Dave.[/italic]"
            )
            console.print(Rule(style="red"))
            break

        # Handle scan shortcut (force re-run email scan now)
        if command.strip().lower() == "scan":
            scheduler.reset_all()
            await run_due_scheduled_tasks(scheduler)
            continue

        # Show scheduled task status
        if command.strip().lower() == "schedule":
            display_scheduled_tasks(scheduler)
            continue

        # Handle any other command with a thinking spinner
        done = asyncio.Event()

        async def run_command():
            try:
                await agent.handle(command)
            finally:
                done.set()

        cmd_task = asyncio.create_task(run_command())
        with console.status(
            f"[bold cyan]🤔 {random_hal_quote()}",
            spinner="dots",
            spinner_style="cyan",
        ) as status:
            while not done.is_set():
                await asyncio.sleep(3.0)
                if not done.is_set():
                    status.update(f"[bold cyan]🤔 {random_hal_quote()}")
        await cmd_task
        console.print()

        # After user command, force all scheduled tasks to re-run
        scheduler.reset_all()
        await run_due_scheduled_tasks(scheduler)


if __name__ == "__main__":
    asyncio.run(main())
