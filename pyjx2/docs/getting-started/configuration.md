# Configuración de PYJX2

PYJX2 utiliza archivos de configuración para gestionar las credenciales y parámetros de conexión. Dependiendo de la interfaz que utilices, el manejo de estos archivos varía.

## Flexibilidad de Configuración

1. **Uso en CLI y API (Obligatorio)**: Para operar mediante la línea de comandos o integrarlo como librería, es **estrictamente necesario** contar con un archivo `pyjx2.toml` o `pyjx2.json` en el directorio de ejecución, o definir las variables de entorno correspondientes.
2. **Uso en TUI (Autónomo)**: La interfaz gráfica permite un funcionamiento sin archivos pre-existentes, ya que los datos pueden ser ingresados y gestionados directamente en los formularios de la aplicación.

## Prioridad de Esquema (CLI/API)

Si existen múltiples fuentes de configuración, el orden de prioridad es:

1. Argumentos directos en CLI (`--jira-username xxx`).
2. Variables de entorno (`PYJX2_...`).
3. Archivo `pyjx2.toml`.
4. Archivo `pyjx2.json`.

## Archivos Soportados

### pyjx2.toml (Recomendado)

Crea el archivo `pyjx2.toml` copiando el ejemplo de la raíz:

```toml
[jira]
env = "QA"
username = "tu_usuario@ejemplo.com"
password = "ENC:gAAAAA..." # Password cifrado

[setup]
test_plan_key = "PROJ-100"
execution_summary = "Pruebas de Regresión"
test_mode = "clone"         # "clone" u "add"

[sync]
execution_key = "PROJ-200"
folder = "./evidencias"
status = "PASS"
upload_mode = "append"      # "append" o "replace"
allowed_extensions = [".pdf", ".png"]
```

### pyjx2.json

Alternativamente, puedes usar un archivo JSON si es preferido por tus sistemas de automatización:

```json
{
  "jira": {
    "env": "QA",
    "username": "admin@example.com",
    "password": "ENC:gAAAAA..."
  },
  "setup": {
    "test_plan_key": "PROJ-100",
    "execution_summary": "Pruebas",
    "test_mode": "clone"
  },
  "sync": {
    "execution_key": "PROJ-200",
    "folder": "./evidencias",
    "status": "PASS",
    "upload_mode": "append",
    "allowed_extensions": [".pdf"]
  }
}
```

## Variables de Entorno

PYJX2 leerá automáticamente las siguientes variables si están presentes en el sistema:

- `PYJX2_JIRA_ENV`: "QA" o "DEV".
- `PYJX2_JIRA_USERNAME`: Correo o usuario de Jira.
- `PYJX2_JIRA_PASSWORD`: Contraseña (plana o cifrada con prefix `ENC:`).
- `PYJX2_XRAY_CLIENT_ID`: ID de cliente (opcional, cae en fallback al usuario de Jira).
- `PYJX2_XRAY_CLIENT_SECRET`: Secreto de cliente (opcional, cae en fallback a la contraseña de Jira).
