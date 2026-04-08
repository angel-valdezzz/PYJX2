from __future__ import annotations

from typing import Optional

import os
import subprocess
import threading
import time
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

config_app = typer.Typer(help="Configuration utility commands.")
app.add_typer(config_app, name="config")


def _common_options(
    config: Optional[str],
    env: Optional[str],
    jira_username: Optional[str],
    jira_password: Optional[str],
    xray_client_id: Optional[str],
    xray_client_secret: Optional[str],
) -> PyJX2:
    """Build overrides dict and load settings, then return a PyJX2 instance."""
    overrides: dict = {}
    if env or jira_username or jira_password:
        overrides["jira"] = {
            "env": env,
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

def _env_option():
    return typer.Option("QA", "--env", help="Environment URL to use (QA or DEV).")

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
    test_plan_key: str = typer.Option(..., "--test-plan", help="QAX Test Plan key."),
    execution_summary: str = typer.Option(..., "--execution-summary", "-e", help="Titulo del nuevo Test Execution."),
    test_set_summary: str = typer.Option(None, "--test-set-summary", "-s", help="Titulo del nuevo Test Set (cae en fallback a execution-summary)."),
    application_target: str = typer.Option(..., "--application", "-a", help="Application mandatory qualifier (e.g. AXA_WEB)."),
    test_mode: str = typer.Option("clone", "--test-mode", "-m",
        help="Modo de tests: 'clone' (copiar en QAX) o 'add' (agregar sin clonar).",
        metavar="clone|add"),
    config: Optional[str] = _config_option(),
    env: Optional[str] = _env_option(),
    jira_username: Optional[str] = _jira_username_option(),
    jira_password: Optional[str] = _jira_password_option(),
    xray_client_id: Optional[str] = _xray_client_id_option(),
    xray_client_secret: Optional[str] = _xray_client_secret_option(),
) -> None:
    """
    [bold]Setup[/bold] — create a Test Execution + Test Set from a Test Plan.

    Reads tests from the given test plan, then clones or adds each test,
    assembles them into a new test set, and links everything into a new test execution.
    """
    try:
        pjx = _common_options(config, env, jira_username, jira_password, xray_client_id, xray_client_secret)
    except ValueError as e:
        console.print(f"[bold red]Configuration error:[/bold red] {e}")
        raise typer.Exit(code=1)

    messages: list[str] = []

    def on_progress(msg: str) -> None:
        console.print(f"  [dim]→[/dim] {msg}")
        messages.append(msg)

    console.print(f"\n[bold cyan]Running setup for project [white]QAX[/white] with test plan [white]{test_plan_key}[/white][/bold cyan]\n")

    try:
        result = pjx.setup(
            test_plan_key=test_plan_key,
            execution_summary=execution_summary,
            test_set_summary=test_set_summary or execution_summary,
            application=application_target,
            test_mode=test_mode,
            progress_callback=on_progress,
        )
    except Exception as e:
        console.print(f"\n[bold red]Setup failed:[/bold red] {e}")
        raise typer.Exit(code=1)

    console.print("\n[bold green]Setup completed successfully![/bold green]\n")

    table = Table(title="Setup Summary", show_header=True, header_style="bold magenta")
    table.add_column("Item", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Test Executions", ", ".join(ex.key for ex in result.test_executions))
    table.add_row("Test Sets", ", ".join(ts.key for ts in result.test_sets))
    table.add_row("Tests (total procesados)", str(len(result.tests)))
    label_added = "Tests agregados" if test_mode == "add" else "Tests linked/reused"
    label_cloned = "Tests clonados" if test_mode == "clone" else "Tests cloned/created"
    table.add_row(label_added, str(result.metrics.tests_linked))
    table.add_row(label_cloned, str(result.metrics.tests_cloned))
    console.print(table)


# ── sync command ───────────────────────────────────────────────────────────────

@app.command()
def sync(
    execution_key: str = typer.Option(..., "--execution", "-e", help="Key of the Test Execution issue."),
    folder: str = typer.Option(..., "--folder", "-f", help="Path to the folder to scan for evidence files."),
    status: str = typer.Option("PASS", "--status", "-s", help="Default status to set on matched tests (PASS, FAIL, TODO, EXECUTING, ABORTED)."),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive", "-r/-R", help="Scan folder recursively."),
    extensions: Optional[str] = typer.Option(None, "--extensions", help="Comma-separated list of allowed extensions (e.g. .jpg,.png)."),
    upload_mode: str = typer.Option("append", "--mode", "-m", help="Upload mode: 'append' to add or 'replace' to clear existing evidence."),
    status_map: Optional[str] = typer.Option(None, "--status-map", help="JSON string mapping test keys to statuses (e.g. '{\"TC-1\":\"FAIL\"}')."),
    config: Optional[str] = _config_option(),
    env: Optional[str] = _env_option(),
    jira_username: Optional[str] = _jira_username_option(),
    jira_password: Optional[str] = _jira_password_option(),
    xray_client_id: Optional[str] = _xray_client_id_option(),
    xray_client_secret: Optional[str] = _xray_client_secret_option(),
) -> None:
    """
    [bold]Sync[/bold] — match evidence files to test cases by summary prefix.

    Scans a folder and matches filenames to test summaries in the given execution.
    If a file name starts with the test summary, it is uploaded as evidence.
    """
    valid_statuses = {"PASS", "FAIL", "TODO", "EXECUTING", "ABORTED"}
    if status.upper() not in valid_statuses:
        console.print(f"[bold red]Invalid default status:[/bold red] '{status}'.")
        raise typer.Exit(code=1)

    overrides = {}
    if status_map:
        try:
            import json
            overrides = json.loads(status_map)
        except Exception as e:
            console.print(f"[bold red]Invalid JSON in --status-map:[/bold red] {e}")
            raise typer.Exit(code=1)

    allowed_ext = [e.strip() for e in extensions.split(",")] if extensions else [".pdf"]

    try:
        pjx = _common_options(config, env, jira_username, jira_password, xray_client_id, xray_client_secret)
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
            status_overrides=overrides,
            upload_mode=upload_mode,
            allowed_extensions=allowed_ext,
            recursive=recursive,
            progress_callback=on_progress,
        )

        table = Table(title=f"Resultados de Sincronización ({execution_key})")
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", style="white")
        table.add_row("Tests Procesados", str(result.processed_tests))
        table.add_row("Tests Actualizados", f"[bold green]{result.updated_tests}[/bold green]")
        table.add_row("Tests sin Evidencia", str(len(result.tests_without_evidence)))
        table.add_row("Archivos Subidos", str(result.files_uploaded))
        table.add_row("Archivos No Utilizados", str(len(result.files_unused)))
        
        console.print("\n", table)

        if result.errors:
            console.print("\n[bold red]Errores durante el proceso:[/bold red]")
            for err in result.errors:
                console.print(f" - {err}")

        if result.files_unused:
            console.print(f"\n[yellow]Aviso:[/yellow] {len(result.files_unused)} archivos no coinciden con ningún test.")

    except Exception as e:
        console.print(f"\n[bold red]Error fatal durante sync:[/bold red] {e}")
        raise typer.Exit(code=1)
        console.print(f"\n[yellow]Unmatched tests ({len(result.unmatched_tests)}):[/yellow] {', '.join(result.unmatched_tests)}")

    if result.unmatched_files:
        console.print(f"[yellow]Unmatched files ({len(result.unmatched_files)}):[/yellow]")
        for f in result.unmatched_files:
            console.print(f"  [dim]{f}[/dim]")


# ── docs command ───────────────────────────────────────────────────────────────

@app.command()
def docs() -> None:
    """
    [bold]Docs[/bold] — launch the user manual in full-screen mode.
    
    Starts a local documentation server and opens Google Chrome in full-screen.
    The server will stop automatically when you interrupt this command (Ctrl+C).
    """
    import webbrowser

    # script is in pyjx2/pyjx2/cli/app.py
    # we need to go up to pyjx2/ (where mkdocs.yml is)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    if not os.path.isdir(os.path.join(base_dir, "docs")):
        console.print(f"[bold red]Error:[/bold red] Directorio de documentación no encontrado en {base_dir}")
        raise typer.Exit(code=1)

    console.print(f"\n[bold cyan]Iniciando Servidor de Documentación...[/bold cyan]")
    console.print(f"[dim]Ruta: {base_dir}[/dim]\n")
    
    proc = None
    try:
        # Start mkdocs server in background
        proc = subprocess.Popen(
            ["mkdocs", "serve"], 
            cwd=base_dir, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        
        def open_browser():
            time.sleep(1.5) # Give it a bit more time for CLI environment
            url = "http://127.0.0.1:8000"
            try:
                if os.name == "nt": # Windows
                    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
                    
                    if os.path.isfile(chrome_path):
                        subprocess.Popen([chrome_path, "--new-window", "--start-fullscreen", url])
                    elif os.path.isfile(edge_path):
                        subprocess.Popen([edge_path, "--new-window", "--start-fullscreen", url])
                    else:
                        webbrowser.open(url)
                else:
                    webbrowser.open(url)
            except Exception:
                webbrowser.open(url)

        threading.Thread(target=open_browser, daemon=True).start()
        
        console.print("[bold green]¡Documentación abierta![/bold green]")
        console.print("[yellow]Presiona Ctrl+C para cerrar el manual y detener el servidor.[/yellow]\n")
        
        # Idle until interrupted
        while True:
            if proc.poll() is not None:
                console.print("[bold red]El servidor de MkDocs se detuvo inesperadamente.[/bold red]")
                break
            time.sleep(1)
            
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Deteniendo servidor...[/bold yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Error inesperado:[/bold red] {e}")
    finally:
        if proc:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except Exception:
                try: proc.kill()
                except Exception: pass
        console.print("[green]Servidor cerrado correctamente.[/green]\n")


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


# ── config commands ────────────────────────────────────────────────────────────

@config_app.command("encrypt-pass")
def encrypt_pass(
    password: str = typer.Argument(..., help="Plaintext password to encrypt.")
) -> None:
    """
    [bold]Encrypt Password[/bold] — generates an encrypted string for your config file.
    """
    from ..infrastructure.security.encryption import SymmetricEncryptionService
    svc = SymmetricEncryptionService()
    encrypted = svc.encrypt(password)
    console.print(f"\n[bold green]Success![/bold green] Encrypted password:")
    console.print(f"\n[bold cyan]{encrypted}[/bold cyan]\n")
    console.print("Paste this exact string (including ENC:) into your pyjx2.toml, pyjx2.json or environment variable.\n")

@config_app.command("decrypt-pass")
def decrypt_pass(
    token: str = typer.Argument(..., help="Encrypted password token starting with ENC:.")
) -> None:
    """
    [bold]Decrypt Password[/bold] — reveals the original password from an encrypted token.
    """
    from ..infrastructure.security.encryption import SymmetricEncryptionService
    svc = SymmetricEncryptionService()
    if not token.startswith("ENC:"):
        console.print(f"\n[bold yellow]Warning:[/bold yellow] Token does not start with ENC:. Returning as raw text.\n")
    
    decrypted = svc.decrypt(token)
    console.print(f"\n[bold green]Decrypted password:[/bold green]")
    console.print(f"\n[bold cyan]{decrypted}[/bold cyan]\n")
