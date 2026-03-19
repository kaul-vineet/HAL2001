"""HAL Command Center Dashboard — Fixed-grid terminal UI.

A Rich Live Layout dashboard that shows all mission results in fixed panels.
Panels flash yellow/green when refreshed, then fade back to normal.
Bottom bar is an always-on input prompt: "Talk to me, Dave ▸"

Usage:
    dashboard = Dashboard(missions)
    dashboard.update_panel("email-scan", "12 emails, 3 need reply")
    dashboard.set_quote("Singing Daisy Bell...")
    dashboard.set_status("Next scan: 22s")
    
    with dashboard.live():
        # dashboard refreshes automatically
        ...
"""

import time
import asyncio
from datetime import datetime

from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align

console = Console()


# Mission code → emoji mapping
MISSION_ICONS = {
    "MAIL": "📬",
    "TEAM": "💬",
    "MEET": "🎙️",
    "PLAN": "✅",
    "ADO": "🔧",
    "SHRP": "📁",
    "SALE": "💰",
    "PLCY": "📄",
    "COMP": "🛡️",
    "PROJ": "📊",
    "KNOW": "📚",
    "DOCS": "🔍",
    "BREF": "☀️",
}


class DashboardPanel:
    """A single mission panel in the dashboard."""

    def __init__(self, mission_id: str, code: str, label: str):
        self.mission_id = mission_id
        self.code = code
        self.label = label
        self.icon = MISSION_ICONS.get(code, "⚙️")
        self.content = "[dim]Waiting for first scan...[/dim]"
        self.status = "pending"  # pending, ok, error
        self.last_updated = 0.0
        self.flash_duration = 4.0  # seconds to stay highlighted

    @property
    def is_fresh(self) -> bool:
        return (time.monotonic() - self.last_updated) < self.flash_duration

    def update(self, content: str, status: str = "ok"):
        """Update panel content and trigger flash."""
        self.content = content[:200]  # truncate for panel fit
        self.status = status
        self.last_updated = time.monotonic()

    def render(self, height: int = 5) -> Panel:
        """Render the panel with flash effect if recently updated."""
        if self.is_fresh and self.status == "ok":
            # Flash: yellow border, green text
            return Panel(
                f"[bold green]{self.content}[/bold green]",
                title=f"[bold yellow]{self.icon} {self.code} ⚡[/bold yellow]",
                border_style="bold yellow",
                height=height,
            )
        elif self.status == "error":
            return Panel(
                f"[red]{self.content}[/red]",
                title=f"[bold red]{self.icon} {self.code} ✗[/bold red]",
                border_style="red",
                height=height,
            )
        elif self.status == "pending":
            return Panel(
                f"[dim]{self.content}[/dim]",
                title=f"[dim]{self.icon} {self.code}[/dim]",
                border_style="dim",
                height=height,
            )
        else:
            # Normal: dim cyan border
            return Panel(
                self.content,
                title=f"[cyan]{self.icon} {self.code}[/cyan]",
                border_style="dim cyan",
                height=height,
            )


class Dashboard:
    """Fixed-grid command center dashboard using Rich Live Layout."""

    def __init__(self, missions: list[dict]):
        self.panels: dict[str, DashboardPanel] = {}
        self.quote = "Initializing HAL 9000..."
        self.next_scan_text = ""
        self.briefing = ""
        self.audit_summary = ""
        self._live: Live | None = None
        self._user_input = ""
        self._response = ""

        # Create panels for each mission
        for m in missions:
            mid = m["id"]
            code = m.get("code", "SYS")
            label = m["label"]
            self.panels[mid] = DashboardPanel(mid, code, label)

    def update_panel(self, mission_id: str, content: str, status: str = "ok"):
        """Update a specific mission panel."""
        if mission_id in self.panels:
            self.panels[mission_id].update(content, status)

    def set_quote(self, quote: str):
        self.quote = quote

    def set_status(self, text: str):
        self.next_scan_text = text

    def set_briefing(self, text: str):
        self.briefing = text[:200]

    def set_audit_summary(self, text: str):
        self.audit_summary = text

    def set_response(self, text: str):
        """Show HAL's response to user query."""
        self._response = text[:300]

    def clear_response(self):
        self._response = ""

    def _build_layout(self) -> Layout:
        """Build the full dashboard layout."""
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="grid"),
            Layout(name="briefing", size=4),
            Layout(name="footer", size=5),
        )

        # Header
        now = datetime.now().strftime("%I:%M:%S %p")
        header_text = Text()
        header_text.append("  HAL 9000 COMMAND CENTER", style="bold red")
        header_text.append(f"          Last scan: {now}", style="dim")
        layout["header"].update(
            Panel(header_text, border_style="red", style="on black")
        )

        # Grid: arrange panels in 2-column rows
        panel_list = list(self.panels.values())
        # Exclude BREF from grid (it goes in briefing row)
        grid_panels = [p for p in panel_list if p.code != "BREF"]
        bref_panel = next((p for p in panel_list if p.code == "BREF"), None)

        # Build rows of 2 panels each
        rows = []
        for i in range(0, len(grid_panels), 2):
            pair = grid_panels[i:i + 2]
            if len(pair) == 2:
                row = Layout()
                row.split_row(
                    Layout(pair[0].render(height=4)),
                    Layout(pair[1].render(height=4)),
                )
                rows.append(Layout(row, size=4))
            else:
                rows.append(Layout(pair[0].render(height=4), size=4))

        if rows:
            layout["grid"].split_column(*rows)

        # Briefing row
        if self._response:
            # Show HAL's response instead of briefing
            layout["briefing"].update(
                Panel(
                    f"[bold green]{self._response}[/bold green]",
                    title="[bold yellow]🧠 HAL RESPONSE[/bold yellow]",
                    border_style="bold yellow",
                )
            )
        elif bref_panel and bref_panel.status != "pending":
            layout["briefing"].update(bref_panel.render(height=4))
        elif self.briefing:
            layout["briefing"].update(
                Panel(
                    self.briefing,
                    title="[cyan]☀️ BRIEFING[/cyan]",
                    border_style="dim cyan",
                )
            )
        else:
            layout["briefing"].update(
                Panel(
                    "[dim]Awaiting first briefing...[/dim]",
                    title="[dim]☀️ BRIEFING[/dim]",
                    border_style="dim",
                )
            )

        # Footer: quote + audit + input prompt
        footer_layout = Layout()
        footer_layout.split_column(
            Layout(name="info", size=2),
            Layout(name="prompt", size=3),
        )

        # Info bar: quote + next scan + audit
        info_text = Text()
        info_text.append(f"  💭 {self.quote}", style="italic cyan")
        if self.next_scan_text:
            info_text.append(f"     {self.next_scan_text}", style="dim yellow")
        if self.audit_summary:
            info_text.append(f"  │  {self.audit_summary}", style="dim")
        footer_layout["info"].update(Panel(info_text, border_style="dim"))

        # Input prompt
        footer_layout["prompt"].update(
            Panel(
                "[bold red]🔴 Talk to me, Dave ▸[/bold red] [dim]Type your question and press Enter[/dim]",
                border_style="bold red",
                style="on black",
            )
        )

        layout["footer"].update(footer_layout)

        return layout

    def render(self) -> Layout:
        """Return the current dashboard layout for Live rendering."""
        return self._build_layout()

    def start_live(self) -> Live:
        """Create and return a Live instance for the dashboard."""
        self._live = Live(
            self.render(),
            console=console,
            refresh_per_second=2,
            screen=True,
        )
        return self._live

    def refresh(self):
        """Update the Live display with current state."""
        if self._live:
            self._live.update(self.render())
