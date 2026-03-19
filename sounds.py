"""HAL Sound Effects — Spacecraft audio feedback using Windows beeps.

Uses winsound (built-in on Windows) to play tones at different frequencies
to simulate a spacecraft console. No external dependencies needed.

On non-Windows systems, sounds are silently skipped.
"""

import sys

try:
    import winsound
    HAS_SOUND = True
except ImportError:
    HAS_SOUND = False


def _beep(freq: int, duration: int) -> None:
    """Play a beep if on Windows, otherwise silently skip."""
    if HAS_SOUND:
        try:
            winsound.Beep(freq, duration)
        except Exception:
            pass


# ── Spacecraft sound effects ─────────────────────────────────────

def boot_chime():
    """Ascending tones on startup — system powering up."""
    _beep(400, 100)
    _beep(500, 100)
    _beep(600, 100)
    _beep(800, 200)


def auth_success():
    """Two quick high beeps — authentication confirmed."""
    _beep(880, 100)
    _beep(1100, 150)


def auth_fail():
    """Low descending buzz — authentication failed."""
    _beep(300, 200)
    _beep(200, 300)


def mission_start():
    """Single soft blip — mission/scan starting."""
    _beep(600, 80)


def mission_complete():
    """Quick double-blip — mission finished successfully."""
    _beep(800, 60)
    _beep(1000, 80)


def mission_error():
    """Low buzz — mission failed."""
    _beep(250, 200)


def alert():
    """Urgent triple-beep — action required (e.g., emails need reply)."""
    _beep(1000, 100)
    _beep(1000, 100)
    _beep(1000, 100)


def user_interrupt():
    """Soft descending tone — user pressed Enter to interrupt."""
    _beep(700, 60)
    _beep(500, 60)


def resume():
    """Soft ascending tone — returning to auto-pilot."""
    _beep(500, 60)
    _beep(700, 60)


def goodbye():
    """Descending Daisy Bell-ish tones — HAL shutting down."""
    _beep(800, 150)
    _beep(700, 150)
    _beep(600, 150)
    _beep(500, 150)
    _beep(400, 200)
    _beep(300, 300)


def system_check_tick():
    """Tiny tick — each system check line."""
    _beep(1200, 30)


def quote_chime():
    """Soft chime when HAL says something funny."""
    _beep(900, 50)
    _beep(1100, 50)
