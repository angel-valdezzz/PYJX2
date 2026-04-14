"""
pyjx2 Public API
================
High-level, composable functions for scripting custom Jira/Xray flows.

Usage example::

    from pyjx2.api import PyJX2, load_settings

    settings = load_settings()
    pjx = PyJX2(settings)

    test = pjx.get_test("PROJ-123")
    new_test = pjx.create_test("PROJ", "My new test")
    cloned = pjx.clone_test("PROJ-123", "PROJ")
    pjx.update_test_execution("PROJ-456", summary="Updated execution")
    pjx.update_test_set("PROJ-789", summary="Updated set")
"""

from ..infrastructure.config import load_settings
from .client import PyJX2

__all__ = ["PyJX2", "load_settings"]
