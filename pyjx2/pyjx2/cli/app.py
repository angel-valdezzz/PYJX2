from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..infrastructure.config import load_settings
from ..api.client import PyJX2

app = typer.Typer(
    name="pyjx2",
    help="Jira/Xray automation tool — setup test executions and sync evidence files.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

console = Console()


def _common_options(
    config: Optional[str],
    jira_url: Optional[str],
    jira_username: Optional[str],
    jira_password: Optional[str],
    xray_client_id: Optional[str],
    xray_client_secret: Optional[str],
) -> PyJX2:
    """Build overrides dict and load settings, then return a PyJX2 instance."""
    overrides: dict = {}
    if jira_url or jira_username or jira_password:
        overrides["jira"] = {
            "url": jira_url,
            "username": jira_username,
            "password": jira_password,
        }
    if xray_client_id or xray_client_secret:
        overrides["xray"] = {
            "client_id": xray_client_id,
            "client_secret": xray_client_secret,
        }
    settings = load_settings(config_file=config, overrides=overrides or None)
    return PyJX2(settings)


# ── Shared options ─────────────────────────────────────────────────────────────

def _config_option():
    return typer.Option(None, "--config", "-c", help="Path to pyjx2.toml or pyjx2.json config file.")

def _jira_url_option():
    return typer.Option(None, "--jira-url", help="Jira base URL (e.g. https://yourorg.atlassian.net).")

def _jira_username_option():
    return typer.Option(None, "--jira-username", "-u", help="Jira username or email.")

def _jira_password_option():
    return typer.Option(None, "--password", help="Jira password.")

def _xray_client_id_option():
    return typer.Option(None, "--xray-client-id", help="Xray Cloud client ID.")

def _xray_client_secret_option():
    return typer.Option(None, "--xray-client-secret", help="Xray Cloud client secret.")


# ── setup command ──────────────────────────────────────────────────────────────

@app.command()
def setup(
    project_key: str = typer.Option(..., "--project", "-p", help="Jira project key (e.g. PROJ)."),
    test_plan_key: str = typer.Option(..., "--test-plan", help="Key of the Jira Test Plan issue."),
    execution_summary: str = typer.Option(..., "--execution-summary", "-e", help="Summary for the new Test Execution issue."),
    test_set_summary: str = typer.Option(..., "--test-set-summary", "-s", help="Summary for the new Test Set issue."),
    reuse_tests: bool = typer.Option(False, "--reuse-tests/--clone-tests", help="Reuse existing tests instead of cloning them."),
    config: Optional[str] = _config_option(),
    jira_url: Optional[str] = _jira_url_option(),
    jira_username: Optional[str] = _jira_username_option(),
    jira_password: Optional[str] = _jira_password_option(),
    xray_client_id: Optional[str] = _xray_client_id_option(),
    xray_client_secret: Optional[str] = _xray_client_secret_option(),
) -> None:
    """
    [bold]Setup[/bold] — create a Test Execution + Test Set from a Test Plan.

    Reads tests from the given test plan, then creates or reuses/clones each test,
    assembles them into a new test set, and links everything into a new test execution.
    """
    try:
        pjx = _common_options(config, jira_url, jira_username, jira_password, xray_client_id, xray_client_secret)
    except ValueError as e:
        console.print(f"[bold red]Configuration error:[/bold red] {e}")
        raise typer.Exit(code=1)

    messages: list[str] = []

    def on_progress(msg: str) -> None:
        console.print(f"  [dim]→[/dim] {msg}")
        messages.append(msg)

    console.print(f"\n[bold cyan]Running setup for project [white]{project_key}[/white] with test plan [white]{test_plan_key}[/white][/bold cyan]\n")

    try:
        result = pjx.setup(
            project_key=project_key,
            test_plan_key=test_plan_key,
            execution_summary=execution_summary,
            test_set_summary=test_set_summary,
            reuse_tests=reuse_tests,
            progress_callback=on_progress,
        )
    except Exception as e:
        console.print(f"\n[bold red]Setup failed:[/bold red] {e}")
        raise typer.Exit(code=1)

    console.print("\n[bold green]Setup completed successfully![/bold green]\n")

    table = Table(title="Setup Summary", show_header=True, header_style="bold magenta")
    table.add_column("Item", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Test Execution", result.test_execution.key)
    table.add_row("Test Set", result.test_set.key)
    table.add_row("Tests (total)", str(len(result.tests)))
    table.add_row("Tests reused", str(len(result.reused)))
    table.add_row("Tests cloned", str(len(result.cloned)))
    table.add_row("Tests created", str(len(result.created)))
    console.print(table)


# ── sync command ───────────────────────────────────────────────────────────────

@app.command()
def sync(
    execution_key: str = typer.Option(..., "--execution", "-e", help="Key of the Test Execution issue."),
    folder: str = typer.Option(..., "--folder", "-f", help="Path to the folder to scan for evidence files."),
    status: str = typer.Option(..., "--status", "-s", help="Status to set on matched tests (PASS, FAIL, TODO, EXECUTING, ABORTED)."),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive", "-r/-R", help="Scan folder recursively."),
    config: Optional[str] = _config_option(),
    jira_url: Optional[str] = _jira_url_option(),
    jira_username: Optional[str] = _jira_username_option(),
    jira_password: Optional[str] = _jira_password_option(),
    xray_client_id: Optional[str] = _xray_client_id_option(),
    xray_client_secret: Optional[str] = _xray_client_secret_option(),
) -> None:
    """
    [bold]Sync[/bold] — match evidence files to test cases and upload results.

    Scans a folder (recursively by default) and matches filenames (by stem) to test
    keys or summaries in the given test execution. For each match, updates the test
    status and uploads the file as evidence.
    """
    valid_statuses = {"PASS", "FAIL", "TODO", "EXECUTING", "ABORTED"}
    if status.upper() not in valid_statuses:
        console.print(f"[bold red]Invalid status:[/bold red] '{status}'. Must be one of: {', '.join(sorted(valid_statuses))}")
        raise typer.Exit(code=1)

    try:
        pjx = _common_options(config, jira_url, jira_username, jira_password, xray_client_id, xray_client_secret)
    except ValueError as e:
        console.print(f"[bold red]Configuration error:[/bold red] {e}")
        raise typer.Exit(code=1)

    def on_progress(msg: str) -> None:
        console.print(f"  [dim]→[/dim] {msg}")

    console.print(f"\n[bold cyan]Syncing execution [white]{execution_key}[/white] with folder [white]{folder}[/white][/bold cyan]\n")

    try:
        result = pjx.sync(
            execution_key=execution_key,
            folder=folder,
            status=status.upper(),
            recursive=recursive,
            progress_callback=on_progress,
        )
    except FileNotFoundError as e:
        console.print(f"\n[bold red]Folder not found:[/bold red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"\n[bold red]Sync failed:[/bold red] {e}")
        raise typer.Exit(code=1)

    console.print("\n[bold green]Sync completed![/bold green]\n")

    if result.matches:
        table = Table(title="Matched Tests", show_header=True, header_style="bold magenta")
        table.add_column("Test Key", style="cyan")
        table.add_column("Summary", style="white")
        table.add_column("File", style="dim")
        table.add_column("Status Updated", style="green")
        table.add_column("Evidence Uploaded", style="green")
        for m in result.matches:
            table.add_row(
                m.test_key,
                m.test_summary,
                m.file_path,
                "✓" if m.status_updated else "✗",
                "✓" if m.uploaded else "✗",
            )
        console.print(table)

    if result.unmatched_tests:
        console.print(f"\n[yellow]Unmatched tests ({len(result.unmatched_tests)}):[/yellow] {', '.join(result.unmatched_tests)}")

    if result.unmatched_files:
        console.print(f"[yellow]Unmatched files ({len(result.unmatched_files)}):[/yellow]")
        for f in result.unmatched_files:
            console.print(f"  [dim]{f}[/dim]")


# ── tui command ────────────────────────────────────────────────────────────────

@app.command()
def tui(
    config: Optional[str] = _config_option(),
) -> None:
    """
    [bold]TUI[/bold] — launch the interactive terminal user interface.

    Opens a full-screen terminal UI where you can run setup and sync flows
    without remembering CLI arguments.
    """
    from ..tui.app import PyJX2App
    app_instance = PyJX2App(config_file=config)
    app_instance.run()
