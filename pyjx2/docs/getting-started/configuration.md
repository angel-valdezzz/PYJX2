# Configuración de PYJX2

PYJX2 está fuertemente gobernado por el concepto de Configuration files explícitos que puedes guardar directamente en el directorio en el que correrás los comandos para que este lo ingiera dinámicamente, ahorrándote el laborioso proceso de tener que reescribir tus credenciales en cada ocasión.

## Prioridad de Esquema

1. Valores inyectados por argumento directo en CLI (`--jira-url xxx`).
2. Entorno / Interfaz Visual en vivo (TUI).
3. Variables de entorno (`PYJX2_...`).
4. Archivo interno `.toml`.
5. Archivo interno `.json`.

## Archivos Soportados

Al correr, PYJX2 examina nativamente el actual directorio para extraer un archivo base.

### pyjx2.toml (Recomendado)

Crea el archivo `pyjx2.toml` copiando el ejemplo de la raíz:

```toml
[jira]
url = "https://tuorg.atlassian.net"
username = "admin@example.com"
password = "ENC:gAAAAA..." 
project_key = "PROJ"

[xray]
client_id = "XRAY_CLIENT_ID"
client_secret = "XRAY_CLIENT_SECRET"

[setup]
test_plan_key = "PROJ-100"
execution_summary = "Sprint 1 Execution"
test_set_summary = "Sprint 1 Test Set"
reuse_tests = false

[sync]
execution_key = "PROJ-200"
folder = "./evidence"
status = "PASS"
recursive = true
```

### pyjx2.json

Alternativamente, es compatible un esquema en sintaxis JSON clásico si los integradores de CI son más propensos a inyectar tokens directamente.

```json
{
  "jira": {
    "url": "https://tuorg.atlassian.net",
    "username": "admin@example.com",
    "password": "ENC:gAAAAA...",
    "project_key": "PROJ"
  },
  "xray": {
    "client_id": "XRAY_CLIENT_ID",
    "client_secret": "XRAY_CLIENT_SECRET"
  },
  "setup": {
    "test_plan_key": "PROJ-100",
    "execution_summary": "Sprint 1 Execution",
    "test_set_summary": "Sprint 1 Test Set",
    "reuse_tests": false
  },
  "sync": {
    "execution_key": "PROJ-200",
    "folder": "./evidence",
    "status": "PASS",
    "recursive": true
  }
}
```


## Variables de Entorno Seguras

PYJX2 cargará un esquema automático si detecta los flag del sistema local. Útil en DevOps pipelines:

- `PYJX2_JIRA_URL`: Ejemplo `https://org.atlassian.net`
- `PYJX2_JIRA_USERNAME`: Tu usuario de dominio.
- `PYJX2_JIRA_PASSWORD`: Tu texto de autenticación (preferible en formato ENC cifrado).
- `PYJX2_XRAY_CLIENT_ID`
- `PYJX2_XRAY_CLIENT_SECRET`
