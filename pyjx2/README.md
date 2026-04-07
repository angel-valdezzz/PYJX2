# pyjx2

Jira/Xray automation tool — clean architecture Python CLI + TUI + scripting API.

## Features

- **`setup`** command — reads a Test Plan, creates/clones/reuses test cases, builds a Test Set and Test Execution, and links everything together.
- **`sync`** command — reads tests from a Test Execution, scans a folder recursively, matches files to test keys/names, updates statuses and uploads evidence.
- **Config file** (`pyjx2.toml` or `pyjx2.json`) with JSON Schema validation — auto-discovered in the current directory.
- **Environment variable overrides** — `PYJX2_JIRA_URL`, `PYJX2_JIRA_USERNAME`, `PYJX2_JIRA_API_TOKEN`, `PYJX2_XRAY_CLIENT_ID`, `PYJX2_XRAY_CLIENT_SECRET`.
- **TUI** — full-screen terminal UI built with [Textual](https://textual.textualize.io/).
- **Python API** — composable functions for building custom automation scripts.

## Installation

```bash
pip install -e .
```

Or install dependencies manually:

```bash
pip install httpx typer rich textual toml jsonschema
```

## Configuration

Copy `pyjx2.toml.example` to `pyjx2.toml` in your working directory and fill in your credentials:

```toml
[jira]
url = "https://yourorg.atlassian.net"
username = "user@example.com"
api_token = "YOUR_JIRA_API_TOKEN"

[xray]
client_id = "YOUR_XRAY_CLIENT_ID"
client_secret = "YOUR_XRAY_CLIENT_SECRET"
```

JSON format is also supported (`pyjx2.json`).

## CLI Usage

```bash
# Show help
pyjx2 --help

# Setup command — create Test Execution + Test Set from a Test Plan
pyjx2 setup \
  --project PROJ \
  --test-plan PROJ-100 \
  --execution-summary "Sprint 1 Execution" \
  --test-set-summary "Sprint 1 Test Set"

# Setup with cloned tests (default) or reuse existing tests
pyjx2 setup --project PROJ --test-plan PROJ-100 \
  --execution-summary "Sprint 1" --test-set-summary "Sprint 1 Set" \
  --reuse-tests

# Sync command — match files to tests and upload evidence
pyjx2 sync \
  --execution PROJ-200 \
  --folder ./evidence \
  --status PASS

# Override config values via CLI arguments
pyjx2 setup --project PROJ --test-plan PROJ-100 \
  --execution-summary "Sprint 1" --test-set-summary "Sprint 1 Set" \
  --jira-url https://myorg.atlassian.net \
  --jira-username me@myorg.com \
  --jira-token MY_TOKEN \
  --xray-client-id MY_ID \
  --xray-client-secret MY_SECRET

# Launch the interactive TUI
pyjx2 tui

# Use a specific config file
pyjx2 --config /path/to/my-config.toml setup ...
```

## Sync — how file matching works

The `sync` command scans the given folder (recursively by default) and matches each file's **stem** (filename without extension) to:
1. The test **key** (e.g. `PROJ-123.png` → matches test `PROJ-123`)
2. The test **summary** (spaces/underscores normalized to dashes, uppercase)

For each match it:
- Updates the test run status in the Test Execution
- Uploads the file as evidence (attachment) for that test run

## Python API

```python
from pyjx2.api import PyJX2, load_settings

# Load from pyjx2.toml / environment / overrides
settings = load_settings()
pjx = PyJX2(settings)

# Get a test
test = pjx.get_test("PROJ-123")

# Create a test
new_test = pjx.create_test("PROJ", "My new test", labels=["regression"])

# Clone a test
cloned = pjx.clone_test("PROJ-123", "PROJ")

# Get all tests in a test execution
tests = pjx.get_tests_from_execution("PROJ-200")

# Update test run status
pjx.update_test_status("PROJ-200", "PROJ-123", "PASS")

# Upload evidence
pjx.upload_test_evidence("PROJ-200", "PROJ-123", "./screenshots/PROJ-123.png")

# Create and manage test sets
ts = pjx.create_test_set("PROJ", "My Test Set")
pjx.add_tests_to_set(ts.key, ["PROJ-123", "PROJ-124"])
pjx.update_test_set(ts.key, summary="Updated title")

# Create a test execution and link a test set
te = pjx.create_test_execution("PROJ", "My Execution")
pjx.add_test_set_to_execution(te.key, ts.key)

# Run the full setup flow
result = pjx.setup(
    project_key="PROJ",
    test_plan_key="PROJ-100",
    execution_summary="Sprint 1 Execution",
    test_set_summary="Sprint 1 Test Set",
    reuse_tests=False,
    progress_callback=print,
)
print(result.test_execution.key, result.test_set.key)

# Run the full sync flow
result = pjx.sync(
    execution_key="PROJ-200",
    folder="./evidence",
    status="PASS",
    recursive=True,
    progress_callback=print,
)
for match in result.matches:
    print(match.test_key, match.file_path)

# Raw API access (escape hatch)
data = pjx.jira.get("issue/PROJ-123")
pjx.xray.post("testexec/12345/test", {"add": ["PROJ-123"]})
```

## Testing

### Requisitos previos

```bash
pip install -e ".[dev]"
# o manualmente:
pip install pytest pytest-bdd pytest-mock
```

### Ejecutar todos los tests

```bash
cd pyjx2
python -m pytest tests/
```

### Solo tests unitarios

```bash
python -m pytest tests/unit/
```

### Solo tests de aceptación (Cucumber/BDD)

```bash
python -m pytest tests/acceptance/
```

### Ver los escenarios Gherkin mientras se ejecutan

```bash
python -m pytest tests/acceptance/ -v
```

### Filtrar por marcador

```bash
# Solo unitarios
python -m pytest -m unit

# Solo aceptación
python -m pytest -m acceptance
```

### Estructura de los tests

```
tests/
├── unit/                          # Tests unitarios rápidos (sin I/O)
│   ├── test_entities.py           # Entidades de dominio
│   ├── test_settings.py           # Carga de configuración
│   ├── test_setup_service.py      # SetupService
│   └── test_sync_service.py       # SyncService
└── acceptance/                    # Tests de aceptación BDD (Cucumber/Gherkin)
    ├── features/                  # Archivos .feature con escenarios en lenguaje natural
    │   ├── setup_flow.feature
    │   ├── sync_flow.feature
    │   ├── cli_setup.feature
    │   ├── cli_sync.feature
    │   └── config_flow.feature
    └── step_defs/                 # Implementación de los pasos Given/When/Then
        ├── conftest.py            # Fixtures y pasos compartidos
        ├── test_setup_steps.py
        ├── test_sync_steps.py
        ├── test_cli_steps.py
        └── test_config_steps.py
```

Los tests de aceptación usan **pytest-bdd** y siguen la convención Cucumber:
cada `Feature` describe un comportamiento del sistema, cada `Scenario` es un caso concreto,
y los pasos `Given / When / Then` son implementados en Python con repositorios y servicios externos mockeados.

---

## Architecture

```
pyjx2/
├── domain/               # Entities + repository interfaces (pure Python, no dependencies)
│   ├── entities/         # Test, TestSet, TestExecution, TestPlan
│   └── repositories/     # Abstract repository contracts
├── application/          # Use case services (SetupService, SyncService)
│   └── services/
├── infrastructure/       # Concrete implementations
│   ├── config/           # Settings loader + JSON Schema validator
│   ├── jira/             # Jira REST API client
│   └── xray/             # Xray Cloud REST + GraphQL client + repository implementations
├── api/                  # High-level public API facade (PyJX2)
├── cli/                  # Typer CLI commands (setup, sync, tui)
└── tui/                  # Textual TUI application
```
