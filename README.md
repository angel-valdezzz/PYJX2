# pyjx2

Herramienta de automatización para **Jira** y **Xray** — arquitectura limpia en Python con interfaces CLI, TUI y API de scripting.

## Características

- **`setup`**: Crea un entorno de pruebas a partir de un Test Plan, permitiendo clonar o agregar casos de prueba, organizarlos en Test Sets y vincularlos a un Test Execution.
- **`sync`**: Escanea carpetas de evidencias, hace coincidencia con casos de prueba y actualiza estados además de subir adjuntos.
- **`docs`**: Lanza el manual de usuario inmersivo en pantalla completa.
- **TUI**: Interfaz gráfica de terminal con áreas dedicadas para Preparación, Sincronización, Configuración y Seguridad.
- **Configuración flexible**: Soporte para archivos `.toml`, `.json` y variables de entorno.
- **Seguridad**: Cifrado simétrico AES para proteger contraseñas en archivos de configuración.

## Instalación

### Usando Pip
A fin de ejecutar una regresión, puedes instalar el proyecto localmente:

```bash
pip install -e .
```

O instalar las dependencias manualmente:

```bash
pip install requests typer rich textual toml jsonschema cryptography
```

### Usando Poetry
```bash
poetry install
poetry shell
```

## Configuración

Crea un archivo `pyjx2.toml` en tu directorio de trabajo:

```toml
[jira]
env = "QA"
username = "usuario@ejemplo.com"
password = "ENC:gAAAAAB..." # Password cifrado opcional
```

> [!NOTE]
> Para el uso de la TUI, los archivos de configuración son opcionales ya que permite el ingreso de datos directamente en la interfaz.

## Seguridad y Cifrado

Para evitar guardar contraseñas en texto plano:

1. Genera tu token cifrado:
```bash
pyjx2 config encrypt-pass TU_PASSWORD
```

2. Usa el resultado `ENC:...` en tus archivos de configuración o variables de entorno.

## Uso de la CLI

### Flujo de Preparación (Setup)
```bash
pyjx2 setup \
  --test-plan PROJ-100 \
  --execution-summary "Regresión Sprint 1" \
  --application AXA_WEB \
  --test-mode clone
```

### Flujo de Sincronización (Sync)
```bash
pyjx2 sync \
  --execution PROJ-200 \
  --folder ./evidencias \
  --status PASS \
  --recursive
```

#### Opciones de `sync`:
| Parámetro | Shorthand | Descripción |
|---|---|---|
| `--execution` | `-e` | ID de la ejecución (MANDATORIO). |
| `--folder` | `-f` | Carpeta de evidencias (MANDATORIO). |
| `--status` | `-s` | Estado por defecto (MANDATORIO: PASS, FAIL, etc.). |
| `--recursive` | `-r` | Escaneo en subcarpetas (Default: True). |
| `--mode` | `-m` | `append` o `replace` evidencias previas. |
| `--extensions` | | Lista separada por coma (ej. `.png, .jpg`). |
| `--status-map` | | JSON para estados específicos por test key. |

### Visualizar Documentación
```bash
pyjx2 docs
```

### Interfaz Gráfica (TUI)
```bash
pyjx2 tui
```

## Python API

```python
from pyjx2.api.client import PyJX2

# Opción 1: Cargar desde configuración (pyjx2.toml o variables de entorno)
pjx = PyJX2.from_config()

# Opción 2: Usar credenciales directas (sin archivos)
pjx = PyJX2.from_credentials(
    username="usuario@ejemplo.com",
    password="mi_password", # Soporta ENC:...
    env="QA"
)

# Ejecutar flujo de Preparación (Setup)
pjx.setup(
    test_plan_key="PROJ-100",
    execution_summary="Regresión Sprint 1",
    application="AXA_WEB",
    test_mode="clone" # u "add" para usar originales
)

# Ejecutar flujo de Sincronización (Sync)
pjx.sync(
    execution_key="PROJ-200",
    folder="./evidencias",
    status="PASS",
    upload_mode="append" # u "replace"
)
```

## Pruebas

```bash
# Ejecutar todos los tests
python -m pytest tests/

# Solo tests unitarios
python -m pytest tests/unit/

# Solo tests de aceptación (BDD)
python -m pytest tests/acceptance/
```

## Arquitectura

```
pyjx2/
├── domain/               # Entidades e interfaces de repositorio (Python puro)
├── application/          # Servicios de casos de uso (Setup, Sync)
├── infrastructure/       # Implementaciones concretas (Jira, Xray, Config)
├── api/                  # Fachada de API pública (PyJX2)
├── cli/                  # Comandos de consola (Typer)
└── tui/                  # Aplicación de interfaz gráfica (Textual)
```

## Calidad De Código

El proyecto incluye análisis estático y de arquitectura:

```bash
poetry run ruff format pyjx2 tests
poetry run ruff check pyjx2 tests
poetry run mypy
poetry run lint-imports
```

### Integración con VS Code

Se añadió configuración en `.vscode/` para:

- formatear Python al guardar con Ruff
- organizar imports y aplicar `fix` de Ruff al guardar
- ejecutar mypy con la configuración del proyecto
- dejar `import-linter` disponible como tarea del editor

`mypy` e `import-linter` no formatean archivos; el autoformato lo hace Ruff.
