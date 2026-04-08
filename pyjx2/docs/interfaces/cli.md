# Interfaz de Línea de Comandos (CLI)

PYJX2 está construido sobre Typer y ofrece una interfaz para automatizaciones y pipelines mediante el uso de comandos y opciones directas.

## Referencia Global 

```bash
pyjx2 [SUBCOMMAND] [OPTIONS]
```

Opciones globales comunes:
- `--config` / `-c`: Especifica una ruta personalizada para el archivo de configuración.
- `--env`: Define el entorno (`QA` o `DEV`).
- `--jira-username` / `-u`: Sobrescribe el usuario de Jira.
- `--password`: Sobrescribe la contraseña de Jira.

---

## Modulo: `setup`
**Propósito:** Crea la estructura de ejecución en Jira (Test Execution + Test Set).

| Flag | Tipo | Descripción |
|---|---|---|
| `--test-plan` | Text | Llave del Test Plan Jira (ej. PROJ-X). |
| `--execution-summary` / `-e` | Text | Título para el nuevo Test Execution. |
| `--application` / `-a` | Text | Calificador de aplicación (ej. AXA_WEB). |
| `--test-mode` / `-m` | Text | `clone` (copiar tests) o `add` (usar tests originales). |

---

## Modulo: `sync`
**Propósito:** Sincroniza evidencias locales con las ejecuciones.

| Flag | Tipo | Descripción |
|---|---|---|
| `--execution` / `-e` | Text | ID de la ejecución en Jira. |
| `--folder` / `-f` | Text | Carpeta local con las evidencias. |
| `--status` / `-s` | Text | Estado por defecto (PASS, FAIL, TODO, etc.). |
| `--recursive` / `-r` | Boolean | Escaneo recursivo de subcarpetas. |

---

## Modulo: `docs`
Accede al manual de usuario directamente desde la terminal.
```bash
pyjx2 docs
```
Este comando activa un servidor local y abre automáticamente **Google Chrome** en modo pantalla completa con la documentación actual. Para detener el servidor, presiona `Ctrl+C`.

---

## Modulo: `tui`
Inicia la interfaz gráfica envolvente.
```bash
pyjx2 tui
```

---

## Modulo: `config` (Utilidades)

- **`encrypt-pass`**: Cifra una contraseña para su uso seguro en archivos de configuración.
- **`decrypt-pass`**: Revela el texto original de un token `ENC:`.
