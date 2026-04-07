from __future__ import annotations

from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header,
    Footer,
    TabbedContent,
    TabPane,
    Input,
    Button,
    Label,
    Checkbox,
    Log,
    Static,
    Select,
)
from textual.reactive import reactive

from ..infrastructure.config import load_settings
from ..api.client import PyJX2


STATUSES = ["PASS", "FAIL", "TODO", "EXECUTING", "ABORTED"]


class PyJX2App(App):
    """Interactive terminal UI for pyjx2 — Jira/Xray automation."""

    CSS = """
    Screen {
        background: $surface;
    }

    Header {
        background: $primary;
    }

    .panel {
        border: solid $primary;
        padding: 1 2;
        margin: 1;
    }

    .panel-title {
        color: $primary;
        text-style: bold;
        margin-bottom: 1;
    }

    .field-row {
        height: auto;
        margin-bottom: 1;
    }

    .field-label {
        width: 22;
        color: $text-muted;
        padding-top: 1;
    }

    .field-input {
        width: 1fr;
    }

    .btn-row {
        height: auto;
        margin-top: 1;
        align: right middle;
    }

    #log-panel {
        height: 18;
        border: solid $accent;
        padding: 0 1;
        margin: 1;
    }

    #log-title {
        color: $accent;
        text-style: bold;
    }

    .status-bar {
        height: 1;
        padding: 0 2;
        color: $text-muted;
        background: $surface-darken-1;
    }

    Button.run-btn {
        margin-left: 1;
        background: $primary;
    }

    Button.clear-btn {
        margin-left: 1;
        background: $surface-darken-2;
    }

    .success-msg {
        color: $success;
        text-style: bold;
    }

    .error-msg {
        color: $error;
        text-style: bold;
    }

    Select {
        width: 1fr;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+c", "quit", "Quit"),
        Binding("f1", "switch_tab('setup')", "Setup"),
        Binding("f2", "switch_tab('sync')", "Sync"),
        Binding("f3", "switch_tab('config')", "Config"),
    ]

    TITLE = "pyjx2 — Jira/Xray Automation"
    SUB_TITLE = "Setup & Sync tool"

    def __init__(self, config_file: Optional[str] = None) -> None:
        super().__init__()
        self._config_file = config_file
        self._pjx: Optional[PyJX2] = None
        self._settings = None

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(id="tabs"):
            with TabPane("Setup (F1)", id="setup"):
                yield self._compose_setup_tab()
            with TabPane("Sync (F2)", id="sync"):
                yield self._compose_sync_tab()
            with TabPane("Config (F3)", id="config"):
                yield self._compose_config_tab()
        yield Static("", id="status-bar", classes="status-bar")
        yield Footer()

    def _compose_setup_tab(self) -> ComposeResult:
        with ScrollableContainer():
            yield Static("Setup — Create Test Execution & Test Set from a Test Plan", classes="panel-title")
            with Container(classes="panel"):
                yield Static("Jira / Xray Connection", classes="panel-title")
                with Horizontal(classes="field-row"):
                    yield Label("Jira URL", classes="field-label")
                    yield Input(placeholder="https://yourorg.atlassian.net", id="setup-jira-url", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Username / Email", classes="field-label")
                    yield Input(placeholder="user@example.com", id="setup-jira-username", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Contraseña", classes="field-label")
                    yield Input(placeholder="Jira password", id="setup-jira-password", password=True, classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Xray Client ID", classes="field-label")
                    yield Input(placeholder="Xray Cloud client ID", id="setup-xray-client-id", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Xray Client Secret", classes="field-label")
                    yield Input(placeholder="Xray Cloud client secret", id="setup-xray-secret", password=True, classes="field-input")

            with Container(classes="panel"):
                yield Static("Setup Parameters", classes="panel-title")
                with Horizontal(classes="field-row"):
                    yield Label("Project Key", classes="field-label")
                    yield Input(placeholder="e.g. PROJ", id="setup-project-key", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Test Plan Key", classes="field-label")
                    yield Input(placeholder="e.g. PROJ-100", id="setup-test-plan", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Execution Summary", classes="field-label")
                    yield Input(placeholder="Summary for the new Test Execution", id="setup-exec-summary", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Test Set Summary", classes="field-label")
                    yield Input(placeholder="Summary for the new Test Set", id="setup-set-summary", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Reuse Tests?", classes="field-label")
                    yield Checkbox("Reuse existing tests instead of cloning", id="setup-reuse-tests")

            with Horizontal(classes="btn-row"):
                yield Button("Run Setup", id="btn-setup-run", classes="run-btn", variant="primary")
                yield Button("Clear Log", id="btn-setup-clear", classes="clear-btn")

            yield Static("Log", id="log-title", classes="panel-title")
            yield Log(id="setup-log", highlight=True)

        return []

    def _compose_sync_tab(self) -> ComposeResult:
        with ScrollableContainer():
            yield Static("Sync — Match files to tests and upload evidence", classes="panel-title")
            with Container(classes="panel"):
                yield Static("Jira / Xray Connection", classes="panel-title")
                with Horizontal(classes="field-row"):
                    yield Label("Jira URL", classes="field-label")
                    yield Input(placeholder="https://yourorg.atlassian.net", id="sync-jira-url", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Username / Email", classes="field-label")
                    yield Input(placeholder="user@example.com", id="sync-jira-username", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Contraseña", classes="field-label")
                    yield Input(placeholder="Jira password", id="sync-jira-password", password=True, classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Xray Client ID", classes="field-label")
                    yield Input(placeholder="Xray Cloud client ID", id="sync-xray-client-id", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Xray Client Secret", classes="field-label")
                    yield Input(placeholder="Xray Cloud client secret", id="sync-xray-secret", password=True, classes="field-input")

            with Container(classes="panel"):
                yield Static("Sync Parameters", classes="panel-title")
                with Horizontal(classes="field-row"):
                    yield Label("Execution Key", classes="field-label")
                    yield Input(placeholder="e.g. PROJ-200", id="sync-exec-key", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Folder Path", classes="field-label")
                    yield Input(placeholder="/path/to/evidence/folder", id="sync-folder", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Status", classes="field-label")
                    yield Select(
                        options=[(s, s) for s in STATUSES],
                        id="sync-status",
                        value="PASS",
                    )
                with Horizontal(classes="field-row"):
                    yield Label("Recursive scan?", classes="field-label")
                    yield Checkbox("Scan folder recursively", id="sync-recursive", value=True)

            with Horizontal(classes="btn-row"):
                yield Button("Run Sync", id="btn-sync-run", classes="run-btn", variant="primary")
                yield Button("Clear Log", id="btn-sync-clear", classes="clear-btn")

            yield Static("Log", classes="panel-title")
            yield Log(id="sync-log", highlight=True)

        return []

    def _compose_config_tab(self) -> ComposeResult:
        with ScrollableContainer():
            yield Static("Config File", classes="panel-title")
            with Container(classes="panel"):
                yield Static(
                    "pyjx2 looks for [b]pyjx2.toml[/b] or [b]pyjx2.json[/b] in the current directory.\n"
                    "You can also set environment variables like [b]PYJX2_JIRA_URL[/b], "
                    "[b]PYJX2_JIRA_USERNAME[/b], [b]PYJX2_JIRA_PASSWORD[/b], "
                    "[b]PYJX2_XRAY_CLIENT_ID[/b], [b]PYJX2_XRAY_CLIENT_SECRET[/b].\n\n"
                    "All fields in the TUI connection panels override the config file for that session.",
                    markup=True,
                )
            with Container(classes="panel"):
                yield Static("Example pyjx2.toml", classes="panel-title")
                yield Static(
                    "[b][jira][/b]\n"
                    'url = "https://yourorg.atlassian.net"\n'
                    'username = "user@example.com"\n'
                    'password = "YOUR_JIRA_PASSWORD"\n'
                    'project_key = "PROJ"\n\n'
                    "[b][xray][/b]\n"
                    'client_id = "YOUR_XRAY_CLIENT_ID"\n'
                    'client_secret = "YOUR_XRAY_CLIENT_SECRET"\n\n'
                    "[b][setup][/b]\n"
                    'test_plan_key = "PROJ-100"\n'
                    'execution_summary = "Sprint 1 Execution"\n'
                    'test_set_summary = "Sprint 1 Test Set"\n'
                    "reuse_tests = false\n\n"
                    "[b][sync][/b]\n"
                    'execution_key = "PROJ-200"\n'
                    'folder = "./evidence"\n'
                    'status = "PASS"\n'
                    "recursive = true",
                    markup=True,
                )
        return []

    # ── Event handlers ─────────────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-setup-run":
            self._run_setup()
        elif event.button.id == "btn-setup-clear":
            self.query_one("#setup-log", Log).clear()
        elif event.button.id == "btn-sync-run":
            self._run_sync()
        elif event.button.id == "btn-sync-clear":
            self.query_one("#sync-log", Log).clear()

    def _get_input(self, widget_id: str) -> str:
        return self.query_one(f"#{widget_id}", Input).value.strip()

    def _log(self, log_id: str, msg: str) -> None:
        self.query_one(f"#{log_id}", Log).write_line(msg)

    def _build_pjx(self, prefix: str, log_id: str) -> Optional[PyJX2]:
        overrides: dict = {}
        jira_url = self._get_input(f"{prefix}-jira-url")
        jira_user = self._get_input(f"{prefix}-jira-username")
        jira_password = self._get_input(f"{prefix}-jira-password")
        xray_id = self._get_input(f"{prefix}-xray-client-id")
        xray_secret = self._get_input(f"{prefix}-xray-secret")

        if jira_url or jira_user or jira_password:
            overrides["jira"] = {"url": jira_url or None, "username": jira_user or None, "password": jira_password or None}
        if xray_id or xray_secret:
            overrides["xray"] = {"client_id": xray_id or None, "client_secret": xray_secret or None}

        try:
            settings = load_settings(config_file=self._config_file, overrides=overrides or None)
            return PyJX2(settings)
        except ValueError as e:
            self._log(log_id, f"[ERROR] Configuration: {e}")
            return None

    def _run_setup(self) -> None:
        log_id = "setup-log"
        self._log(log_id, "Starting setup…")

        pjx = self._build_pjx("setup", log_id)
        if not pjx:
            return

        project_key = self._get_input("setup-project-key")
        test_plan = self._get_input("setup-test-plan")
        exec_summary = self._get_input("setup-exec-summary")
        set_summary = self._get_input("setup-set-summary")
        reuse = self.query_one("#setup-reuse-tests", Checkbox).value

        missing = []
        if not project_key:
            missing.append("Project Key")
        if not test_plan:
            missing.append("Test Plan Key")
        if not exec_summary:
            missing.append("Execution Summary")
        if not set_summary:
            missing.append("Test Set Summary")
        if missing:
            self._log(log_id, f"[ERROR] Missing required fields: {', '.join(missing)}")
            return

        def on_progress(msg: str) -> None:
            self._log(log_id, f"  → {msg}")

        try:
            result = pjx.setup(
                project_key=project_key,
                test_plan_key=test_plan,
                execution_summary=exec_summary,
                test_set_summary=set_summary,
                reuse_tests=reuse,
                progress_callback=on_progress,
            )
            self._log(log_id, f"[SUCCESS] Test Execution: {result.test_execution.key}")
            self._log(log_id, f"[SUCCESS] Test Set: {result.test_set.key}")
            self._log(log_id, f"[SUCCESS] Tests: {len(result.tests)} total ({len(result.reused)} reused, {len(result.cloned)} cloned)")
        except Exception as e:
            self._log(log_id, f"[ERROR] {e}")

    def _run_sync(self) -> None:
        log_id = "sync-log"
        self._log(log_id, "Starting sync…")

        pjx = self._build_pjx("sync", log_id)
        if not pjx:
            return

        exec_key = self._get_input("sync-exec-key")
        folder = self._get_input("sync-folder")
        status_widget = self.query_one("#sync-status", Select)
        status = str(status_widget.value) if status_widget.value else "PASS"
        recursive = self.query_one("#sync-recursive", Checkbox).value

        missing = []
        if not exec_key:
            missing.append("Execution Key")
        if not folder:
            missing.append("Folder Path")
        if missing:
            self._log(log_id, f"[ERROR] Missing required fields: {', '.join(missing)}")
            return

        def on_progress(msg: str) -> None:
            self._log(log_id, f"  → {msg}")

        try:
            result = pjx.sync(
                execution_key=exec_key,
                folder=folder,
                status=status,
                recursive=recursive,
                progress_callback=on_progress,
            )
            self._log(log_id, f"[SUCCESS] Matches: {len(result.matches)}")
            self._log(log_id, f"[INFO] Unmatched tests: {len(result.unmatched_tests)}")
            self._log(log_id, f"[INFO] Unmatched files: {len(result.unmatched_files)}")
            for m in result.matches:
                self._log(log_id, f"  ✓ {m.test_key} ← {m.file_path}")
        except FileNotFoundError as e:
            self._log(log_id, f"[ERROR] Folder not found: {e}")
        except Exception as e:
            self._log(log_id, f"[ERROR] {e}")

    def action_switch_tab(self, tab_id: str) -> None:
        self.query_one("#tabs", TabbedContent).active = tab_id
