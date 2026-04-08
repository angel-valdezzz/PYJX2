# Configuración de PyJX2

PyJX2 utiliza un sistema de configuración jerárquico que permite definir parámetros a través de archivos fijos (`TOML`/`JSON`), variables de entorno o argumentos de línea de comandos.

## Orden de Prioridad

Cuando se lee una clave de configuración, PyJX2 sigue este orden de precedencia (de mayor a menor):

1. **Argumento CLI Único** (`--test-plan`, `--status`, etc.)
2. **Argumentos de Sobrescritura de Credenciales CLI** (`--jira-username`, `--password`)
3. **Variables de Entorno** (`PYJX2_*`)
4. **Archivo de Configuración Explícito** (Proporcionado vía `--config`)
5. **Archivo Autodetectado** (`pyjx2.toml` o `pyjx2.json` en el directorio actual)

---

## Esquema Técnico (Referencia Continua)

A continuación se detallan todas las secciones y claves admitidas por el motor de PyJX2.

### Sección `[auth]`
Configuración base para el motor de conexión con Atlassian.

| Clave | Tipo | Valor por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `username` | String | (Requerido) | Usuario o email con permisos de API en Jira Cloud. |
| `password` | String | (Requerido) | API Token de Jira. Se recomienda usar formato cifrado `ENC:`. |
| `env` | String | `QA` | Entorno de conexión. Valores: `QA`, `DEV`. |


### Sección `[setup]`
Valores predeterminados para el flujo de preparación.

| Clave | Tipo | Descripción |
| :--- | :--- | :--- |
| `test_plan_key` | String | Llave del Test Plan por defecto. |
| `execution_summary` | String | Título genérico para nuevas ejecuciones. |
| `test_mode` | String | Modo de operación: `clone` (Default) o `add`. |

### Sección `[sync]`
Valores predeterminados para el flujo de sincronización de evidencias.

| Clave | Tipo | Valor por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `execution_key` | String | | Llave del Test Execution por defecto. |
| `folder` | String | | Path local a la carpeta de evidencias. |
| `status` | String | `PASS` | Estado base a aplicar tras la sincronización. |
| `recursive` | Boolean | `true` | Habilita el escaneo de subcarpetas. |
| `upload_mode` | String | `append` | Modo de subida: `append` o `replace`. |
| `allowed_extensions`| Array | `[".pdf"]` | Lista de extensiones a considerar. |

---

## Variables de Entorno

PyJX2 escanea automáticamente el entorno local buscando el prefijo `PYJX2_`. Esto es ideal para integrar con secretos de CI/CD (Github Secrets, Jenkins Credentials).

- `PYJX2_AUTH_USERNAME`
- `PYJX2_AUTH_PASSWORD` (Soporta `ENC:`)
- `PYJX2_AUTH_ENV`

---

## Ejemplo Completo (`pyjx2.toml`)

```toml
[auth]
username = "admin@example.com"
password = "ENC:gAAAAABlkX2..."
env = "QA"

[setup]
test_mode = "add"
execution_summary = "Nightly Test Execution"

[sync]
folder = "./evidence"
status = "PASS"
recursive = true
allowed_extensions = [".pdf", ".png", ".jpg"]
```
