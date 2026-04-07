"""
pyjx2 — Jira/Xray automation tool
===================================
CLI, TUI, and scripting API for automating test management workflows.

Quick start:
    # CLI
    pyjx2 setup --project PROJ --test-plan PROJ-100 --execution-summary "Sprint 1" --test-set-summary "Sprint 1 Set"
    pyjx2 sync --execution PROJ-200 --folder ./evidence --status PASS
    pyjx2 tui

    # API
    from pyjx2.api import PyJX2, load_settings
    settings = load_settings()
    pjx = PyJX2(settings)
    test = pjx.get_test("PROJ-123")
"""

__version__ = "0.1.0"

from .api import PyJX2, load_settings

__all__ = ["PyJX2", "load_settings", "__version__"]
