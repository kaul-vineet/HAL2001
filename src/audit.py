"""HAL Audit Logger — Logs orchestrator decisions, tool selections, and results.

Every orchestrated execution is logged with:
- Timestamp
- User/mission prompt
- Planner reasoning (WHY these tools)
- Plan (WHICH tools, WHAT order)
- Execution results (per step: status, duration, preview)
- Final answer

Logs are written to:
- Console (Rich formatted, when verbose)
- JSON Lines file (machine-readable, for audit)
"""

import json
import os
import time
from datetime import datetime, timezone
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule

console = Console()

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "hal_audit.jsonl")

# Unique session ID for this HAL run
SESSION_ID = f"session_{int(time.time())}"


def _ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def log_session_start():
    """Write a session separator at HAL startup."""
    _ensure_log_dir()
    now = datetime.now(timezone.utc).isoformat()
    separator = {
        "type": "session_start",
        "session_id": SESSION_ID,
        "timestamp": now,
        "message": "═" * 60,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("\n")
        f.write(f"# ══════════════════════════════════════════════════════════\n")
        f.write(f"# HAL 9000 SESSION: {SESSION_ID}  |  {now}\n")
        f.write(f"# ══════════════════════════════════════════════════════════\n")
        f.write(json.dumps(separator, ensure_ascii=False) + "\n")


def log_plan(
    prompt: str,
    reasoning: str,
    plan: list[dict],
    source: str = "mission",
) -> str:
    """Log an orchestrator plan decision.

    Args:
        prompt: The user/mission prompt.
        reasoning: The planner's reasoning for tool selection.
        plan: List of planned steps.
        source: "mission" or "user".

    Returns:
        A unique execution_id for correlating with results.
    """
    _ensure_log_dir()
    execution_id = f"{int(time.time() * 1000)}"
    now = datetime.now(timezone.utc).isoformat()

    entry = {
        "type": "plan",
        "session_id": SESSION_ID,
        "execution_id": execution_id,
        "timestamp": now,
        "source": source,
        "prompt": prompt,
        "reasoning": reasoning,
        "plan": plan,
    }

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return execution_id


def log_step(
    execution_id: str,
    step: int,
    tool: str,
    description: str,
    status: str,
    duration_ms: int,
    result_preview: str,
) -> None:
    """Log a single tool execution step.

    Args:
        execution_id: Correlates with the plan.
        step: Step number.
        tool: Tool name (e.g., "chat", "jira.get_sprint").
        description: What this step does.
        status: "ok" or "error".
        duration_ms: Execution time in milliseconds.
        result_preview: First 500 chars of result.
    """
    _ensure_log_dir()
    now = datetime.now(timezone.utc).isoformat()

    entry = {
        "type": "step",
        "session_id": SESSION_ID,
        "execution_id": execution_id,
        "timestamp": now,
        "step": step,
        "tool": tool,
        "description": description,
        "status": status,
        "duration_ms": duration_ms,
        "result_preview": result_preview[:500],
    }

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def log_result(
    execution_id: str,
    prompt: str,
    final_answer: str,
    total_steps: int,
    steps_ok: int,
    steps_failed: int,
    total_duration_ms: int,
) -> None:
    """Log the final execution result.

    Args:
        execution_id: Correlates with plan and steps.
        prompt: Original prompt.
        final_answer: The combined final answer.
        total_steps: Number of steps executed.
        steps_ok: Steps that succeeded.
        steps_failed: Steps that failed.
        total_duration_ms: Total execution time.
    """
    _ensure_log_dir()
    now = datetime.now(timezone.utc).isoformat()

    entry = {
        "type": "result",
        "session_id": SESSION_ID,
        "execution_id": execution_id,
        "timestamp": now,
        "prompt": prompt,
        "final_answer": final_answer[:1000],
        "total_steps": total_steps,
        "steps_ok": steps_ok,
        "steps_failed": steps_failed,
        "total_duration_ms": total_duration_ms,
    }

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def display_audit_trail(result: dict, execution_id: str) -> None:
    """Show a formatted audit trail on console.

    Args:
        result: The orchestrated result dict.
        execution_id: The execution ID.
    """
    reasoning = result.get("reasoning", "")
    steps = result.get("steps", [])

    console.print()
    console.print(Rule("[dim]📋 Audit Trail[/dim]", style="dim"))
    console.print(f"  [dim]Execution ID: {execution_id}[/dim]")

    if reasoning:
        console.print(
            f"  [dim]🧠 Reasoning: [italic]{reasoning}[/italic][/dim]"
        )

    if steps:
        table = Table(
            border_style="dim",
            show_header=True,
            header_style="dim bold",
            padding=(0, 1),
        )
        table.add_column("#", style="dim", width=3)
        table.add_column("Tool", style="dim cyan")
        table.add_column("Description", style="dim")
        table.add_column("Status", width=6, justify="center")

        for s in steps:
            status_icon = "[green]✓[/green]" if s["status"] == "ok" else "[red]✗[/red]"
            table.add_row(
                str(s["step"]),
                s["tool"],
                s["description"],
                status_icon,
            )
        console.print(table)

    console.print(Rule(style="dim"))
