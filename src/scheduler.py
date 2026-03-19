"""Scheduler for HAL agent — runs periodic tasks in the background.

To add a new scheduled task:
    1. Create an async function that returns a result
    2. Create a display function that renders the result to console
    3. Register it with scheduler.register(...)
"""

import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

# Type aliases
RunFn = Callable[[], Awaitable[Any]]
DisplayFn = Callable[[Any], None]


@dataclass
class ScheduledTask:
    """A single recurring task."""

    name: str
    label: str  # shown in the spinner while running
    interval: float  # seconds between runs
    run_fn: RunFn  # async callable that returns a result
    display_fn: DisplayFn  # callable that renders result to console
    last_run: float = 0.0  # monotonic timestamp of last execution
    enabled: bool = True

    @property
    def is_due(self) -> bool:
        """True if enough time has passed since last run."""
        if self.last_run == 0.0:
            return True  # never run yet → run immediately
        return (time.monotonic() - self.last_run) >= self.interval


class Scheduler:
    """Manages a list of periodic tasks.

    Usage:
        scheduler = Scheduler()
        scheduler.register("email-scan", "Scanning inbox", 300, scan_fn, display_fn)

        # In the main loop:
        due = scheduler.get_due_tasks()
        for task in due:
            result = await task.run_fn()
            task.display_fn(result)
            scheduler.mark_complete(task.name)
    """

    def __init__(self):
        self._tasks: dict[str, ScheduledTask] = {}

    def register(
        self,
        name: str,
        label: str,
        interval: float,
        run_fn: RunFn,
        display_fn: DisplayFn,
        enabled: bool = True,
    ) -> None:
        """Register a new scheduled task."""
        self._tasks[name] = ScheduledTask(
            name=name,
            label=label,
            interval=interval,
            run_fn=run_fn,
            display_fn=display_fn,
            enabled=enabled,
        )

    def get_due_tasks(self) -> list[ScheduledTask]:
        """Return all enabled tasks that are due to run."""
        return [t for t in self._tasks.values() if t.enabled and t.is_due]

    def mark_complete(self, name: str) -> None:
        """Record that a task just finished running."""
        if name in self._tasks:
            self._tasks[name].last_run = time.monotonic()

    def reset_all(self) -> None:
        """Force all tasks to re-run on next check (e.g., after user interrupt)."""
        for task in self._tasks.values():
            task.last_run = 0.0

    def enable(self, name: str) -> None:
        if name in self._tasks:
            self._tasks[name].enabled = True

    def disable(self, name: str) -> None:
        if name in self._tasks:
            self._tasks[name].enabled = False

    def list_tasks(self) -> list[dict]:
        """Return task info for display."""
        now = time.monotonic()
        result = []
        for t in self._tasks.values():
            next_in = max(0, t.interval - (now - t.last_run)) if t.last_run else 0
            result.append({
                "name": t.name,
                "label": t.label,
                "interval": t.interval,
                "enabled": t.enabled,
                "last_run": t.last_run,
                "next_in_seconds": round(next_in),
            })
        return result

    @property
    def task_names(self) -> list[str]:
        return list(self._tasks.keys())
