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
    $primary-light: #00008F;
    $accent-light: #D24723;

    $primary-dark: #4976BA;
    $accent-dark: #8A7333;

    Screen {
        background: $surface;
    }

    Header {
        background: $primary-light;
    }
    .-dark Header {
        background: $primary-dark;
    }

    .panel {
        height: auto;
        border: solid $primary-light;
        padding: 1 2;
        margin: 1 2;
        background: $surface-lighten-1;
    }
    .-dark .panel {
        border: solid $primary-dark;
    }

    .panel-title {
        color: $accent-light;
        text-style: bold;
        margin-bottom: 1;
    }
    .-dark .panel-title {
        color: $accent-dark;
    }

    .field-row {
        layout: horizontal;
        height: auto;
        margin-bottom: 1;
    }

    /* Diseño responsivo: Contraer a vista vertical (mobile default) en consolas estándar pequeñas mediante clasificador '-narrow' */
    .-narrow .field-row {
        layout: vertical;
        height: auto;
        margin-bottom: 2;
    }
    
    .-narrow .field-label {
        width: 100%;
        padding-top: 0;
        margin-bottom: 0;
    }

    .field-label {
        width: 30;
        color: $text;
        text-style: bold;
        padding-top: 1;
    }

    .field-input {
        width: 1fr;
        border: solid $primary-light 50%;
    }
    .-dark .field-input {
        border: solid $primary-dark 50%;
    }

    .field-input:focus {
        border: solid $accent-light;
    }
    .-dark .field-input:focus {
        border: solid $accent-dark;
    }

    .btn-row {
        height: auto;
        margin-top: 1;
        align: right middle;
        margin-right: 2;
    }

    Button.run-btn {
        margin-left: 2;
        background: $primary-light;
        border: none;
    }
    .-dark Button.run-btn {
        background: $primary-dark;
    }

    Button.run-btn:hover {
        background: $accent-light;
    }
    .-dark Button.run-btn:hover {
        background: $accent-dark;
    }

    Button.clear-btn {
        margin-left: 2;
        background: $surface-darken-2;
        border: none;
    }

    Button.clear-btn:hover {
        background: $error;
    }

    Log {
        height: 12;
        border: solid $accent-light 50%;
        margin: 0 2 1 2;
        background: $surface-darken-1;
    }
    .-dark Log {
        border: solid $accent-dark 50%;
    }

    Log:focus {
        border: solid $accent-light;
    }
    .-dark Log:focus {
        border: solid $accent-dark;
    }

    .status-bar {
        height: 1;
        padding: 0 2;
        color: $text-muted;
        background: $surface-darken-1;
    }

    Select {
        width: 1fr;
        border: solid $primary-light 50%;
    }
    .-dark Select {
        border: solid $primary-dark 50%;
    }
    
    Select:focus {
        border: solid $accent-light;
    }
    .-dark Select:focus {
        border: solid $accent-dark;
    }

    #home-container {
        align: center top;
        height: auto;
        margin-top: 1;
    }

    #logo-art {
        margin-bottom: 2;
        padding-bottom: 1;
        width: 100%;
        text-align: center;
        content-align: center middle;
    }

    #home-btn-container {
        height: 5;
        align: center middle;
        margin-top: 1;
    }

    #btn-docs {
        width: 80;
        height: 3;
        text-style: bold;
        content-align: center middle;
    }

    Button.warning-btn {
        background: $accent-light;
        border: tall $error;
        color: white;
    }
    .-dark Button.warning-btn {
        background: $accent-dark;
        border: tall $error;
    }
    Button.warning-btn:hover {
        background: $error;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Salir", show=True),
        Binding("ctrl+c", "quit", "Salir"),
        Binding("f1", "switch_tab('setup')", "Preparación"),
        Binding("f2", "switch_tab('sync')", "Sincronización"),
        Binding("f3", "switch_tab('config')", "Configuración"),
        Binding("f4", "switch_tab('security')", "Seguridad"),
    ]

    TITLE = "pyjx2 — Jira/Xray Automation"
    SUB_TITLE = "Herramienta de Preparación y Sincronización"

    def __init__(self, config_file: Optional[str] = None) -> None:
        super().__init__()
        self._config_file = config_file
        self._pjx: Optional[PyJX2] = None
        self._settings = None
        self.mkdocs_process = None

    def on_mount(self) -> None:
        import atexit
        atexit.register(self._kill_mkdocs)
        
    def on_resize(self, event) -> None:
        if event.size.width <= 95:
            self.add_class("-narrow")
        else:
            self.remove_class("-narrow")
        
    def _kill_mkdocs(self):
        import subprocess
        if getattr(self, "mkdocs_process", None) and self.mkdocs_process.poll() is None:
            self.mkdocs_process.terminate()
            self.mkdocs_process.wait(timeout=2)
            self.mkdocs_process = None

    def action_quit(self):
        self._kill_mkdocs()
        self.exit()

    def _copy_to_clipboard(self, text: str) -> None:
        import platform
        import subprocess
        try:
            os_name = platform.system()
            if os_name == "Windows":
                subprocess.run("clip", input=text, text=True, check=True)
            elif os_name == "Darwin":
                subprocess.run("pbcopy", input=text, text=True, check=True)
            else:
                subprocess.run(["xclip", "-selection", "clipboard"], input=text, text=True, check=True)
        except Exception as e:
            try:
                from textual.widgets import Log
                self.query_one("#sec-log", Log).write_line(f"[ERROR] No se pudo copiar al portapapeles: {e}")
            except Exception:
                pass

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(initial="home", id="tabs"):
            with TabPane("Inicio", id="home"):
                yield from self._compose_home_tab()
            with TabPane("Preparación (F1)", id="setup"):
                yield from self._compose_setup_tab()
            with TabPane("Sincronización (F2)", id="sync"):
                yield from self._compose_sync_tab()
            with TabPane("Configuración (F3)", id="config"):
                yield from self._compose_config_tab()
            with TabPane("Seguridad (F4)", id="security"):
                yield from self._compose_security_tab()
        yield Static("", id="status-bar", classes="status-bar")
        yield Footer()

    def _compose_home_tab(self) -> ComposeResult:
        import os
        from .ascii_parser import get_ascii_logo
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "AXA-Logo.html")
        logo_markup = get_ascii_logo(logo_path)
        
        with ScrollableContainer(id="home-container"):
            yield Static(logo_markup, id="logo-art")
            with Horizontal(id="home-btn-container"):
                yield Button("📖 Visualizar Documentación (MkDocs)", id="btn-docs", classes="run-btn", variant="primary")
        return []

    def _compose_setup_tab(self) -> ComposeResult:
        with ScrollableContainer():
            yield Static("Preparación — Crear Test Execution y Test Set desde un Test Plan", classes="panel-title")
            with Container(classes="panel"):
                yield Static("Conexión a Jira / Xray", classes="panel-title")
                with Horizontal(classes="field-row"):
                    yield Label("Jira URL", classes="field-label")
                    yield Input(placeholder="https://tuorg.atlassian.net", id="setup-jira-url", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Usuario / Email", classes="field-label")
                    yield Input(placeholder="usuario@ejemplo.com", id="setup-jira-username", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Contraseña", classes="field-label")
                    yield Input(placeholder="Contraseña o Token", id="setup-jira-password", password=True, classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Xray Client ID", classes="field-label")
                    yield Input(placeholder="Xray Cloud client ID", id="setup-xray-client-id", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Xray Client Secret", classes="field-label")
                    yield Input(placeholder="Xray Cloud client secret", id="setup-xray-secret", password=True, classes="field-input")

            with Container(classes="panel"):
                yield Static("Parámetros de Preparación", classes="panel-title")
                with Horizontal(classes="field-row"):
                    yield Label("Llave de Proyecto", classes="field-label")
                    yield Input(placeholder="eje. PROJ", id="setup-project-key", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Llave de Test Plan", classes="field-label")
                    yield Input(placeholder="eje. PROJ-100", id="setup-test-plan", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Resumen de Ejecución", classes="field-label")
                    yield Input(placeholder="Resumen para el nuevo Test Execution", id="setup-exec-summary", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Resumen de Test Set", classes="field-label")
                    yield Input(placeholder="Resumen para el nuevo Test Set", id="setup-set-summary", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("¿Reusar Tests?", classes="field-label")
                    yield Checkbox("Reusar tests en lugar de clonarlos", id="setup-reuse-tests")

            with Horizontal(classes="btn-row"):
                yield Button("Ejecutar", id="btn-setup-run", classes="run-btn", variant="primary")
                yield Button("Limpiar Log", id="btn-setup-clear", classes="clear-btn")

            yield Static("Bitácora de Salida (Log)", id="log-title", classes="panel-title")
            yield Log(id="setup-log", highlight=True)

        return []

    def _compose_sync_tab(self) -> ComposeResult:
        with ScrollableContainer():
            yield Static("Sincronización — Rastrear archivos de evidencias y subir a Jira", classes="panel-title")
            with Container(classes="panel"):
                yield Static("Conexión a Jira / Xray", classes="panel-title")
                with Horizontal(classes="field-row"):
                    yield Label("Jira URL", classes="field-label")
                    yield Input(placeholder="https://tuorg.atlassian.net", id="sync-jira-url", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Usuario / Email", classes="field-label")
                    yield Input(placeholder="usuario@ejemplo.com", id="sync-jira-username", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Contraseña", classes="field-label")
                    yield Input(placeholder="Contraseña o Token", id="sync-jira-password", password=True, classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Xray Client ID", classes="field-label")
                    yield Input(placeholder="Xray Cloud client ID", id="sync-xray-client-id", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Xray Client Secret", classes="field-label")
                    yield Input(placeholder="Xray Cloud client secret", id="sync-xray-secret", password=True, classes="field-input")

            with Container(classes="panel"):
                yield Static("Parámetros de Sincronización", classes="panel-title")
                with Horizontal(classes="field-row"):
                    yield Label("Test Execution", classes="field-label")
                    yield Input(placeholder="eje. PROJ-200", id="sync-exec-key", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Ubicación de Evidencias", classes="field-label")
                    yield Input(placeholder="/ruta/hacia/carpeta_evidencias", id="sync-folder", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Estatus a Reportar", classes="field-label")
                    yield Select(
                        options=[(s, s) for s in STATUSES],
                        id="sync-status",
                        value="PASS",
                    )
                with Horizontal(classes="field-row"):
                    yield Label("¿Búsqueda Múltiple?", classes="field-label")
                    yield Checkbox("Escanear dentro de sub-carpetas recursivamente", id="sync-recursive", value=True)

            with Horizontal(classes="btn-row"):
                yield Button("Sincronizar", id="btn-sync-run", classes="run-btn", variant="primary")
                yield Button("Limpiar Log", id="btn-sync-clear", classes="clear-btn")

            yield Static("Bitácora de Salida (Log)", classes="panel-title")
            yield Log(id="sync-log", highlight=True)

        return []

    def _compose_config_tab(self) -> ComposeResult:
        with ScrollableContainer():
            yield Static("Archivo de Configuración Global", classes="panel-title")
            with Container(classes="panel"):
                yield Static(
                    "PYJX2 buscará [b]pyjx2.toml[/b] o [b]pyjx2.json[/b] en el directorio actual emulador.\n"
                    "También puedes declarar variables de entorno como [b]PYJX2_JIRA_URL[/b], "
                    "[b]PYJX2_JIRA_USERNAME[/b], [b]PYJX2_JIRA_PASSWORD[/b], "
                    "[b]PYJX2_XRAY_CLIENT_ID[/b], [b]PYJX2_XRAY_CLIENT_SECRET[/b].\n\n"
                    "Todos los renglones que llenes visualmente en la TUI sobrescribirán al archivo de configuración nativo.",
                    markup=True,
                )
            with Container(classes="panel"):
                yield Static("Ejemplo de plantilla con pyjx2.toml", classes="panel-title")
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

    def _compose_security_tab(self) -> ComposeResult:
        with ScrollableContainer():
            yield Static("Seguridad — Encriptar / Desencriptar credenciales locales", classes="panel-title")
            with Container(classes="panel"):
                yield Static(
                    "Usa esta herramienta en offline para generar un token cifrado para tus archivos.\n"
                    "Emplea la llave simétrica AES robusta integrada pre-empaquetada en tú ecosistema.",
                    markup=True,
                )
            
            with Container(classes="panel"):
                yield Static("Caja de Herramientas de Cifrado", classes="panel-title")
                with Horizontal(classes="field-row"):
                    yield Label("Contraseña Plana", classes="field-label")
                    yield Input(placeholder="Tu texto secreto real aquí", id="sec-plain", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Token Encriptado", classes="field-label")
                    yield Input(placeholder="ENC:...", id="sec-encrypted", classes="field-input")
                
                with Horizontal(classes="btn-row"):
                    yield Button("Copiar Token 📋", id="btn-sec-copy", classes="clear-btn")
                    yield Button("Encriptar ⬇", id="btn-sec-encrypt", classes="run-btn", variant="primary")
                    yield Button("Desencriptar ⬆", id="btn-sec-decrypt", classes="run-btn", variant="warning")
            
            yield Static("Mensajes de Resultados", classes="panel-title")
            yield Log(id="sec-log", highlight=True)

        return []

    # ── Event handlers ─────────────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-docs":
            import os, sys, subprocess, webbrowser
            if not getattr(self, "mkdocs_process", None):
                proj_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                # Lanzar el proceso asíncronamente
                self.mkdocs_process = subprocess.Popen([sys.executable, "-m", "mkdocs", "serve"], cwd=proj_dir)
                # Darle 1.5s al servidor de MkDocs para arrancar en el OS local antes de abrir el navegador
                self.set_timer(1.5, lambda: webbrowser.open("http://127.0.0.1:8000"))
                event.button.label = "Cerrar Documentación"
                event.button.remove_class("run-btn")
                event.button.add_class("warning-btn")
            else:
                self._kill_mkdocs()
                event.button.label = "📖 Visualizar Documentación (MkDocs)"
                event.button.remove_class("warning-btn")
                event.button.add_class("run-btn")
        elif event.button.id == "btn-setup-run":
            self._run_setup()
        elif event.button.id == "btn-setup-clear":
            self.query_one("#setup-log", Log).clear()
        elif event.button.id == "btn-sync-run":
            self._run_sync()
        elif event.button.id == "btn-sync-clear":
            self.query_one("#sync-log", Log).clear()
        elif event.button.id == "btn-sec-copy":
            enc_input = self.query_one("#sec-encrypted", Input)
            val = enc_input.value.strip()
            if val:
                self._copy_to_clipboard(val)
                self.query_one("#sec-log", Log).write_line(f"[ÉXITO] Token copiado al portapapeles exitosamente.")
            else:
                self.query_one("#sec-log", Log).write_line(f"[ERROR] No hay token encriptado para copiar.")
        elif event.button.id == "btn-sec-encrypt":
            self._run_encrypt()
        elif event.button.id == "btn-sec-decrypt":
            self._run_decrypt()

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
            self._log(log_id, f"[ERROR] Archivo de Configuración Global: {e}")
            return None

    def _run_setup(self) -> None:
        log_id = "setup-log"
        self._log(log_id, "Iniciando despliegue de Preparación…")

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
            missing.append("Llave de Proyecto")
        if not test_plan:
            missing.append("Llave de Test Plan")
        if not exec_summary:
            missing.append("Resumen de Ejecución")
        if not set_summary:
            missing.append("Resumen de Test Set")
        if missing:
            self._log(log_id, f"[ERROR] Faltan los siguientes requerimientos obligatorios: {', '.join(missing)}")
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
            self._log(log_id, f"[ÉXITO] Test Execution (Ticket): {result.test_execution.key}")
            self._log(log_id, f"[ÉXITO] Test Set Oficial: {result.test_set.key}")
            self._log(log_id, f"[ÉXITO] Cosecha de Pruebas: {len(result.tests)} totales abordadas ({len(result.reused)} recicladas, {len(result.cloned)} construidas/clonadas)")
        except Exception as e:
            self._log(log_id, f"[ERROR] Operación rechazada: {e}")

    def _run_sync(self) -> None:
        log_id = "sync-log"
        self._log(log_id, "Iniciando escaneo dinámico de Sincronización…")

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
            missing.append("Test Execution (Id Original)")
        if not folder:
            missing.append("Ruta de Evidencias Físicas")
        if missing:
            self._log(log_id, f"[ERROR] Faltan los siguientes campos antes de proceder: {', '.join(missing)}")
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
            self._log(log_id, f"[ÉXITO] Coincidencias de tokens exitosas: {len(result.matches)}")
            self._log(log_id, f"[INFO] Archivos de Carpeta Huerfanizados: {len(result.unmatched_files)}")
            self._log(log_id, f"[INFO] Tests sin archivos emparejados: {len(result.unmatched_tests)}")
            for m in result.matches:
                self._log(log_id, f"  ✓ {m.test_key} ← {m.file_path}")
        except FileNotFoundError as e:
            self._log(log_id, f"[ERROR] Carpeta referida local no encontrada: {e}")
        except Exception as e:
            self._log(log_id, f"[ERROR] Conflicto o rechazo de servidor: {e}")

    def action_switch_tab(self, tab_id: str) -> None:
        self.query_one("#tabs", TabbedContent).active = tab_id

    def _run_encrypt(self) -> None:
        plain = self._get_input("sec-plain")
        if not plain:
            self._log("sec-log", "[ERROR] La contraseña plana se encuentra vacía.")
            return
        from ..infrastructure.security.encryption import SymmetricEncryptionService
        svc = SymmetricEncryptionService()
        encrypted = svc.encrypt(plain)
        self.query_one("#sec-encrypted", Input).value = encrypted
        self._log("sec-log", f"[ÉXITO] El Token seguro fue encriptado exitosamente")

    def _run_decrypt(self) -> None:
        encrypted = self._get_input("sec-encrypted")
        if not encrypted:
            self._log("sec-log", "[ERROR] El recuadro para Token Encriptado se encuentra vacío.")
            return
        from ..infrastructure.security.encryption import SymmetricEncryptionService
        svc = SymmetricEncryptionService()
        try:
            decrypted = svc.decrypt(encrypted)
            self.query_one("#sec-plain", Input).value = decrypted
            self._log("sec-log", f"[ÉXITO] El Token de comprobación fue desempaquetado exitosamente")
        except Exception as e:
            self._log("sec-log", f"[ERROR] Imposible validar la derivación de este token. Verifica su pureza: {e}")
