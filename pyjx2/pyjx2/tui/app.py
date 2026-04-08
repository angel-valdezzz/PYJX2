from __future__ import annotations

import os
import platform
import subprocess
import threading
import re
from typing import Optional, List, Dict

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
    RadioSet,
    RadioButton,
    TextArea,
)
from textual.reactive import reactive

from ..infrastructure.config import load_settings
from ..infrastructure.config.settings import Settings, JiraSettings, XraySettings
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

    .section-subtitle {
        color: $accent-light;
        text-style: underline;
        margin-top: 1;
        margin-bottom: 1;
    }
    .-dark .section-subtitle {
        color: $accent-dark;
    }

    .field-row {
        layout: horizontal;
        height: auto;
        margin-bottom: 1;
    }

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

    .field-input.input-error {
        border: solid $error;
    }

    .browse-btn {
        min-width: 10;
        margin-left: 1;
        background: $primary-light;
    }
    .-dark .browse-btn {
        background: $primary-dark;
    }

    .subgroup-row {
        height: auto;
        margin: 0 0 1 0;
        border: solid $primary-light 10%;
        padding: 0 1;
    }

    #sync-subgroups-container {
        height: auto;
        margin: 1 0;
        border-left: solid $primary-light 10%;
        padding-left: 1;
    }
    .-dark .subgroup-row {
        border: solid $primary-dark 10%;
    }

    .subgroup-qaxs {
        width: 1fr;
    }

    .subgroup-status {
        width: 25;
        margin-left: 1;
    }

    .remove-btn {
        min-width: 6;
        margin-left: 1;
        background: $error;
    }

    .field-hint {
        color: $text-muted;
        text-style: italic;
        padding-left: 30;
        margin-bottom: 1;
    }

    .field-error {
        width: 1fr;
        padding-top: 0;
        color: $error;
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

    sync_subgroups = reactive([])

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
        try:
            self.query_one("#setup-source-xray-row").display = False
            self.query_one("#setup-source-manual-row").display = False
            self.query_one("#setup-source-manual-error-row").display = False
            self.query_one("#setup-concat-row").display = False
        except Exception: pass
        
    def on_resize(self, event) -> None:
        if event.size.width <= 95: self.add_class("-narrow")
        else: self.remove_class("-narrow")
        
    def _kill_mkdocs(self):
        if getattr(self, "mkdocs_process", None) and self.mkdocs_process.poll() is None:
            self.mkdocs_process.terminate()
            self.mkdocs_process.wait(timeout=2)
            self.mkdocs_process = None

    def action_quit(self):
        self._kill_mkdocs()
        self.exit()

    def action_switch_tab(self, tab_id: str) -> None:
        self.query_one("#tabs", TabbedContent).active = tab_id

    def _copy_to_clipboard(self, text: str) -> None:
        try:
            os_name = platform.system()
            if os_name == "Windows": subprocess.run("clip", input=text, text=True, check=True)
            elif os_name == "Darwin": subprocess.run("pbcopy", input=text, text=True, check=True)
            else: subprocess.run(["xclip", "-selection", "clipboard"], input=text, text=True, check=True)
        except Exception as e:
            try: self._log("sec-log", f"[ERROR] No se pudo copiar: {e}")
            except Exception: pass

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(initial="home", id="tabs"):
            with TabPane("Inicio", id="home"): yield from self._compose_home_tab()
            with TabPane("Preparación (F1)", id="setup"): yield from self._compose_setup_tab()
            with TabPane("Sincronización (F2)", id="sync"): yield from self._compose_sync_tab()
            with TabPane("Configuración (F3)", id="config"): yield from self._compose_config_tab()
            with TabPane("Seguridad (F4)", id="security"): yield from self._compose_security_tab()
        yield Static("", id="status-bar", classes="status-bar")
        yield Footer()

    def _compose_home_tab(self) -> ComposeResult:
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
                    yield Label("Entorno", classes="field-label")
                    yield RadioSet(RadioButton("QA", id="setup-env-qa", value=True), RadioButton("DEV", id="setup-env-dev"), id="setup-env")
                with Horizontal(classes="field-row"):
                    yield Label("Usuario / Email", classes="field-label")
                    yield Input(placeholder="usuario@ejemplo.com", id="setup-jira-username", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Contraseña", classes="field-label")
                    yield Input(placeholder="Contraseña o Token", id="setup-jira-password", password=True, classes="field-input")

            with Container(classes="panel"):
                yield Static("Parámetros de Preparación", classes="panel-title")
                with Horizontal(classes="field-row"):
                    yield Label("QAX Test Plan", classes="field-label")
                    yield Input(placeholder="eje. PROJ-100", id="setup-test-plan", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Titulo Test Execution", classes="field-label")
                    yield Input(placeholder="Resumen para el nuevo Test Execution", id="setup-exec-summary", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Titulo Test Set", classes="field-label")
                    yield Input(placeholder="(Si vacio: usará Titulo Execution)", id="setup-set-summary", classes="field-input")
                
                yield Static("⚙ Configuración de Tests", classes="section-subtitle")
                with Horizontal(classes="field-row"):
                    yield Label("Modo de Tests", classes="field-label")
                    yield RadioSet(RadioButton("📄 Clonar", id="test-mode-clone", value=True), RadioButton("🔗 Agregar", id="test-mode-add"), id="setup-test-mode")
                with Horizontal(classes="field-row"):
                    yield Label("Fuente de Tests", classes="field-label")
                    yield RadioSet(RadioButton("Archivo", id="source-file", value=True), RadioButton("ID Xray", id="source-xray"), RadioButton("Manual", id="source-manual"), id="setup-source-mode")
                with Horizontal(classes="field-row", id="setup-source-file-row"):
                    yield Label("", classes="field-label")
                    yield Button("📂", id="btn-file-picker", classes="browse-btn")
                    yield Input(placeholder=".txt o .csv seleccionado...", id="setup-source-file-path", classes="field-input", disabled=True)
                with Horizontal(classes="field-row", id="setup-source-xray-row"):
                    yield Label("", classes="field-label")
                    yield Input(placeholder="ID Numerico", id="setup-source-xray-id", classes="field-input")
                with Horizontal(classes="field-row", id="setup-source-manual-row"):
                    yield Label("", classes="field-label")
                    yield Input(placeholder="QAX-1, QAX-2", id="setup-source-manual-text", classes="field-input")
                with Horizontal(classes="field-row", id="setup-source-manual-error-row"):
                    yield Label("", classes="field-label")
                    yield Static("", id="setup-manual-error", classes="field-error")
                with Horizontal(classes="field-row", id="setup-concat-row"):
                    yield Label("", classes="field-label")
                    yield Checkbox("Concatenar previos", id="setup-concat")
                with Horizontal(classes="field-row", id="setup-source-log-row"):
                    yield Label("Bitácora QAX", classes="field-label")
                    yield TextArea("", id="setup-source-log-area")
                with Horizontal(classes="field-row"):
                    yield Label("Aplicación", classes="field-label")
                    yield Input(placeholder="e.g. AXA_WEB", id="setup-application", classes="field-input")

            with Horizontal(classes="btn-row"):
                yield Button("Ejecutar", id="btn-setup-run", classes="run-btn", variant="primary")
                yield Button("Limpiar", id="btn-setup-clear", classes="clear-btn")
            yield Log(id="setup-log", highlight=True)
        return []

    def _compose_sync_tab(self) -> ComposeResult:
        with ScrollableContainer():
            yield Static("Sincronización — Rastrear evidencias y actualizar Jira", classes="panel-title")
            with Container(classes="panel"):
                yield Static("Conexión Jira / Xray", classes="panel-title")
                with Horizontal(classes="field-row"):
                    yield Label("Entorno", classes="field-label")
                    yield RadioSet(RadioButton("QA", id="sync-env-qa", value=True), RadioButton("DEV", id="sync-env-dev"), id="sync-env")
                with Horizontal(classes="field-row"):
                    yield Label("Usuario", classes="field-label")
                    yield Input(placeholder="user@example.com", id="sync-jira-username", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Password", classes="field-label")
                    yield Input(placeholder="Token", id="sync-jira-password", password=True, classes="field-input")

            with Container(classes="panel"):
                yield Static("Parámetros de Sincronización", classes="panel-title")
                with Horizontal(classes="field-row"):
                    yield Label("Test Execution", classes="field-label")
                    yield Input(placeholder="ID Ej: PROJ-200", id="sync-exec-key", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Evidencias", classes="field-label")
                    yield Input(placeholder="/ruta/carpeta", id="sync-folder", classes="field-input")
                    yield Button("📁", id="btn-sync-browse", classes="browse-btn")
                
                yield Static("⚙ Matching y Estados", classes="section-subtitle")
                with Horizontal(classes="field-row"):
                    yield Label("Estatus Default", classes="field-label")
                    yield Select(options=[(s, s) for s in STATUSES], id="sync-status", value="PASS")
                with Horizontal(classes="field-row"):
                    yield Label("Subida", classes="field-label")
                    yield RadioSet(RadioButton("Append", id="sync-mode-append", value=True), RadioButton("Replace", id="sync-mode-replace"), id="sync-upload-mode")
                with Horizontal(classes="field-row"):
                    yield Label("Extensiones", classes="field-label")
                    yield Input(placeholder=".pdf, .png...", id="sync-extensions", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Recursivo", classes="field-label")
                    yield Checkbox("Habilitar", id="sync-recursive", value=True)

                yield Static("Subgrupos de Estatus (Max. 5)", classes="section-subtitle")
                with Vertical(id="sync-subgroups-container"): pass
                with Horizontal(classes="btn-row"):
                    yield Button("➕ Añadir", id="btn-sync-add-subgroup", variant="success")

            with Horizontal(classes="btn-row"):
                yield Button("Ejecutar", id="btn-sync-run", classes="run-btn", variant="primary")
                yield Button("Limpiar", id="btn-sync-clear", classes="clear-btn")
            yield Log(id="sync-log", highlight=True)
        return []

    def _compose_config_tab(self) -> ComposeResult:
        with ScrollableContainer():
            yield Static("Archivo de Configuración", classes="panel-title")
            with Container(classes="panel"): yield Static("PYJX2 buscará pyjx2.toml o pyjx2.json en la raíz.", markup=True)
            with Container(classes="panel"):
                yield Static("[b][sync][/b]\nexecution_key = 'PROJ-200'\nfolder = './evidencias'\nstatus = 'PASS'\nrecursive = true", markup=True)
        return []

    def _compose_security_tab(self) -> ComposeResult:
        with ScrollableContainer():
            yield Static("Seguridad — Encriptación", classes="panel-title")
            with Container(classes="panel"):
                with Horizontal(classes="field-row"):
                    yield Label("Plano", classes="field-label")
                    yield Input(placeholder="Texto", id="sec-plain", classes="field-input")
                with Horizontal(classes="field-row"):
                    yield Label("Token", classes="field-label")
                    yield Input(placeholder="ENC:...", id="sec-encrypted", classes="field-input")
                with Horizontal(classes="btn-row"):
                    yield Button("Copiar", id="btn-sec-copy", classes="clear-btn")
                    yield Button("Encriptar", id="btn-sec-encrypt", classes="run-btn", variant="primary")
                    yield Button("Desencriptar", id="btn-sec-decrypt", classes="run-btn", variant="warning")
            yield Log(id="sec-log")
        return []

    # ── Logic ──────────────────────────────────────────────────────────────────

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.radio_set.id == "setup-source-mode":
            p = event.pressed.id
            self.query_one("#setup-source-file-row").display = (p == "source-file")
            self.query_one("#setup-source-xray-row").display = (p == "source-xray")
            self.query_one("#setup-source-manual-row").display = (p == "source-manual")
            self.query_one("#setup-concat-row").display = (p != "source-file")

    def on_input_changed(self, event: Input.Changed) -> None:
        is_sub = event.input.id and event.input.id.startswith("sync-sub-qaxs-")
        if is_sub or event.input.id == "setup-source-manual-text":
            has_err = bool(event.value and re.search(r'[^a-zA-Z0-9\-,\s]', event.value))
            event.input.set_class(has_err, "input-error")
            if is_sub:
                idx = int(event.input.id.split("-")[-1])
                if idx < len(self.sync_subgroups): self.sync_subgroups[idx]["qaxs"] = event.value

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id and event.select.id.startswith("sync-sub-status-"):
            idx = int(event.select.id.split("-")[-1])
            if idx < len(self.sync_subgroups): self.sync_subgroups[idx]["status"] = str(event.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-docs": self._toggle_docs(event.button)
        elif bid == "btn-file-picker": self._open_picker("file")
        elif bid == "btn-sync-browse": self._open_picker("folder")
        elif bid == "btn-sync-add-subgroup": self._add_subgroup()
        elif bid and bid.startswith("btn-remove-subgroup-"): self._remove_subgroup(int(bid.split("-")[-1]))
        elif bid == "btn-setup-run": self.run_worker(self._run_setup, thread=True)
        elif bid == "btn-sync-run": self.run_worker(self._run_sync, thread=True)

        elif bid == "btn-setup-clear": self.query_one("#setup-log", Log).clear()
        elif bid == "btn-sync-clear": self.query_one("#sync-log", Log).clear()
        elif bid == "btn-sec-copy":
            val = self.query_one("#sec-encrypted", Input).value
            if val: self._copy_to_clipboard(val)
        elif bid == "btn-sec-encrypt": self._run_encrypt()
        elif bid == "btn-sec-decrypt": self._run_decrypt()

    def _open_picker(self, mode: str) -> None:
        def _pick():
            import sys
            import subprocess
            
            # Universal Python-native picker using tkinter (looks native and Image 2 style on Windows)
            py_code = ""
            if mode == "file":
                py_code = "import tkinter as tk; from tkinter import filedialog; root=tk.Tk(); root.withdraw(); print(filedialog.askopenfilename(title='Seleccionar Archivo de Tests', filetypes=[('Tests', '*.txt;*.csv'), ('Todos', '*.*')]))"
            else:
                py_code = "import tkinter as tk; from tkinter import filedialog; root=tk.Tk(); root.withdraw(); print(filedialog.askdirectory(title='Seleccionar Carpeta de Evidencias'))"
            
            cmd = [sys.executable, "-c", py_code]
            try:
                # Run the picker in its own process to avoid GUI/Thread conflicts
                # This is 100% robust and gives the "Image 2" look the user wants
                res = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()
                if res:
                    self.call_from_thread(self._set_path, mode, res)
            except Exception:
                # Simple PowerShell fallback as last resort
                if platform.system() == "Windows":
                    cmd_back = "powershell -Command \"[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms'); $d=New-Object System.Windows.Forms.FolderBrowserDialog; $d.ShowDialog(); $d.SelectedPath\""
                    res = subprocess.run(cmd_back, shell=True, capture_output=True, text=True).stdout.strip()
                    if res: self.call_from_thread(self._set_path, mode, res)

        threading.Thread(target=_pick, daemon=True).start()

    def _set_path(self, mode: str, path: str):
        if mode == "file":
            self.query_one("#setup-source-file-path", Input).value = path
            self._load_file(path)
        else: self.query_one("#sync-folder", Input).value = path

    def _load_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            keys = re.findall(r'[a-zA-Z]+-\d+', content)
            self.query_one("#setup-source-log-area", TextArea).text = "\n".join(list(dict.fromkeys(keys)))
        except Exception: pass

    def _add_subgroup(self):
        if len(self.sync_subgroups) >= 5: return
        self.sync_subgroups = self.sync_subgroups + [{"qaxs": "", "status": "PASS"}]
        self._refresh_subgroups()

    def _remove_subgroup(self, i: int):
        lst = list(self.sync_subgroups)
        lst.pop(i)
        self.sync_subgroups = lst
        self._refresh_subgroups()

    def _refresh_subgroups(self):
        c = self.query_one("#sync-subgroups-container", Vertical)
        c.remove_children()
        
        widgets = []
        for i, g in enumerate(self.sync_subgroups):
            widgets.append(Horizontal(
                Input(value=g["qaxs"], placeholder="QAX-1...", classes="subgroup-qaxs", id=f"sync-sub-qaxs-{i}"),
                Select(options=[(s, s) for s in STATUSES], value=g["status"], classes="subgroup-status", id=f"sync-sub-status-{i}"),
                Button("🗑️", id=f"btn-remove-subgroup-{i}", classes="remove-btn"),
                classes="subgroup-row"
            ))
        
        if widgets:
            c.mount(*widgets)
            
        self.query_one("#btn-sync-add-subgroup", Button).disabled = (len(self.sync_subgroups) >= 5)

    def _run_setup(self):
        log = "setup-log"
        pjx = self._build_pjx("setup", log)
        if not pjx: return
        self._log(log, "Iniciando Preparación...")
        try:
            res = pjx.setup(
                test_plan_key=self._get_input("setup-test-plan"),
                execution_summary=self._get_input("setup-exec-summary"),
                application=self._get_input("setup-application"),
                test_mode="add" if self.query_one("#setup-test-mode", RadioSet).pressed_button.id == "test-mode-add" else "clone",
                progress_callback=lambda m: self._log(log, f" → {m}")
            )
            self._log(log, "[ÉXITO] Preparación finalizada.")
        except Exception as e: self._log(log, f"[ERROR] {e}")

    def _run_sync(self):
        log = "sync-log"
        pjx = self._build_pjx("sync", log)
        if not pjx: return
        self._log(log, "Iniciando Sincronización...")
        overrides = {}
        for g in self.sync_subgroups:
            for k in re.findall(r'[a-zA-Z]+-\d+', g["qaxs"]): overrides[k] = g["status"]
        mode = "replace" if self.query_one("#sync-upload-mode", RadioSet).pressed_button.id == "sync-mode-replace" else "append"
        try:
            res = pjx.sync(
                execution_key=self._get_input("sync-exec-key"),
                folder=self._get_input("sync-folder"),
                status=str(self.query_one("#sync-status", Select).value or "PASS"),
                status_overrides=overrides,
                upload_mode=mode,
                allowed_extensions=[e.strip() for e in self._get_input("sync-extensions").split(",")] if self._get_input("sync-extensions") else [".pdf"],
                progress_callback=lambda m: self._log(log, f" → {m}")
            )
            self._log(log, f"[ÉXITO] Sincronización finalizada (Modo: {mode.upper()}).")
        except Exception as e: self._log(log, f"[ERROR] {e}")

    def _toggle_docs(self, btn):
        if not self.mkdocs_process:
            # Calculate absolute path to the directory containing mkdocs.yml
            # script is in pyjx2/pyjx2/tui/app.py
            # we need to go up to pyjx2/ (where mkdocs.yml is)
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            
            try:
                self.mkdocs_process = subprocess.Popen(["mkdocs", "serve"], cwd=base_dir)
                btn.label = "Cerrar Docs"; btn.add_class("warning-btn")
                
                # Wait a bit for the server to initialize and open browser in full screen
                def open_browser():
                    import time
                    import os
                    import webbrowser
                    import subprocess
                    time.sleep(1.0)
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
                        webbrowser.open(url) # Fallback


                
                threading.Thread(target=open_browser, daemon=True).start()

                
            except Exception as e:

                # Fallback if somehow base_dir doesn't exist
                try: self._log("setup-log", f"[ERROR] No se pudo iniciar MkDocs: {e}")
                except Exception: pass
        else:
            self._kill_mkdocs()
            btn.label = "📖 Visualizar Documentación (MkDocs)"
            btn.remove_class("warning-btn")


    def _run_encrypt(self):
        p = self._get_input("sec-plain")
        if not p: return
        from ..infrastructure.security.encryption import SymmetricEncryptionService
        self.query_one("#sec-encrypted", Input).value = SymmetricEncryptionService().encrypt(p)
        self._log("sec-log", "[ÉXITO] Encriptado.")

    def _run_decrypt(self):
        e = self._get_input("sec-encrypted")
        if not e: return
        if not e.startswith("ENC:"):
            self._log("sec-log", "[ERROR] Formato inválido: debe iniciar con 'ENC:'.")
            return

        from ..infrastructure.security.encryption import SymmetricEncryptionService
        try:
            self.query_one("#sec-plain", Input).value = SymmetricEncryptionService().decrypt(e)
            self._log("sec-log", "[ÉXITO] Desencriptado.")
        except Exception:
            self.query_one("#sec-plain", Input).value = ""
            self._log("sec-log", "[ERROR] Token corrupto o llave incorrecta.")

    def _get_input(self, id: str) -> str:
        try: return str(self.query_one(f"#{id}", Input).value or "").strip()
        except Exception: return ""

    def _log(self, id: str, msg: str):
        try: self.query_one(f"#{id}", Log).write(msg + "\n")
        except Exception: pass

    def _build_pjx(self, mode, log_id):
        try:
            # Capture environment and credentials from UI
            is_qa = self.query_one("#sync-env-qa", RadioButton).value
            env = "QA" if is_qa else "DEV"
            
            username = self._get_input("sync-jira-username")
            password = self._get_input("sync-jira-password")
            
            # Construct Jira and Xray settings (recycling credentials)
            jira = JiraSettings(username=username, password=password, env=env)
            xray = XraySettings(client_id=username, client_secret=password)
            
            # Create in-memory settings container
            settings = Settings(jira=jira, xray=xray)
            
            return PyJX2(settings)
            
        except Exception as e:
            self._log(log_id, f"[ERROR] No se pudo inicializar el motor: {e}")
            return None

    def _kill_mkdocs(self):
        if self.mkdocs_process:
            try: self.mkdocs_process.terminate()
            except Exception: pass
            self.mkdocs_process = None

    def _copy_to_clipboard(self, text: str):
        import subprocess
        try:
            # Use PowerShell to set clipboard to avoid potential issues with CMD/Shell
            subprocess.run(["powershell", "-Command", f"Set-Clipboard -Value '{text}'"], shell=True)
        except Exception: pass
