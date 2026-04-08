# Interfaz de Línea de Comandos (CLI)

!!! abstract "Descripción"
    PyJX2 proporciona una interfaz de línea de comandos (CLI) potente y versátil construida sobre `Typer`, permitiendo la integración nativa en pipelines de CI/CD.

## Opciones Globales y Autenticación

| Opción | Alias | Descripción |
| :--- | :--- | :--- |
| `--config` | `-c` | Ruta al archivo `pyjx2.toml` o `pyjx2.json`. |
| `--env` | | Entorno: `QA` (default) o `DEV`. |
| `--jira-username`| `-u` | Email o ID de usuario para Jira. |
| `--password` | `-p` | API Token (soporta texto plano o `ENC:`). |

---

## Módulo: `setup`

!!! info "Función"
    El subcomando setup se encarga de generar un ambiente en Jira para los casos de prueba.

!!! example "Ejemplo de preparación"
    ```bash
    pyjx2 setup --test-plan QAX-101 --execution-summary "Sprint 10" --application CRM_WEB  # (1)
    ```

    1. El argumento `--application` es crucial para identificar el componente en la trazabilidad de Jira.

### Argumentos Específicos
- **`--test-plan`**: (Obligatorio) Llave del Test Plan origen.
- **`--execution-summary`**: Título del nuevo Test Execution.
- **`--application`**: Nombre del componente bajo prueba.
- **`--test-mode`**: `clone` (Default) o `add`.

---

## Módulo: `sync`

!!! info "Función"
    El comando `sync` escanea el sistema de archivos local para cargar evidencias y transicionar estados en Xray de forma masiva.

!!! example "Subida masiva de evidencias"
    ```bash
    pyjx2 sync --execution QAX-200 --folder ./reports --status PASS --recursive  # (1)
    ```

    1. Usa `--recursive` para asegurar que las evidencias en subcarpetas (ej. por navegador) sean procesadas.

### Argumentos Específicos
- **`--execution`**: Llave del Test Execution destino.
- **`--folder`**: Ruta al directorio de evidencias.
- **`--status`**: Estado global (`PASS`, `FAIL`, etc.).
- **`--recursive`**: Escaneo de subdirectorios.
- **`--extensions`**: Lista (ej. `.pdf,.png`). Por defecto `.pdf`.

---

<!--
## Módulo: `config`
... (contenido comentado)
-->

## Comandos de Utilidad

### `tui`
Lanza la interfaz gráfica táctil-terminal de PyJX2. Ideal para configuraciones manuales asistidas.
```bash
pyjx2 tui
```

### `docs`
Inicia el motor de documentación local (MkDocs) y abre el manual completo.
```bash
pyjx2 docs
```
