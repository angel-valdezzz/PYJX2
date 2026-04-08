# Configuración de PyJX2

PyJX2 utiliza un sistema de configuración jerárquico que permite definir parámetros a través de archivos fijos (`TOML`/`JSON`), variables de entorno o argumentos de línea de comandos.

## Orden de Prioridad

!!! note "Jerarquía de Precedencia"
    PyJX2 busca configuraciones en el siguiente orden. El primero que encuentre "gana":
    1.  **Parámetros CLI específicos** (`--test-plan`, etc.)
    2.  **Credenciales CLI** (`--jira-username`, etc.)
    3.  **Variables de Entorno** (`PYJX2_AUTH_*`)
    4.  **Archivo de Configuración** (`pyjx2.toml` o `.json`)

---

## Esquema Técnico

### Sección `[auth]`
Configuración base para el motor de conexión con Atlassian.

| Clave | Tipo | Descripción |
| :--- | :--- | :--- |
| `username` | String | **(Requerido)** Usuario o email de la API de Jira. |
| `password` | String | **(Requerido)** API Token. Soporta formato cifrado `ENC:`. |
| `env` | String | Entorno: `QA` (Default) o `DEV`. |

!!! warning "Seguridad de Credenciales"
    Nunca compartas o subas a control de versiones archivos que contengan contraseñas en texto plano. Utiliza el comando `pyjx2 config encrypt-pass` para cifrarlas antes de agregarlas al archivo `.toml`.

### Sección `[setup]`
Valores predeterminados para el flujo de preparación.

| Clave | Tipo | Descripción |
| :--- | :--- | :--- |
| `test_plan_key` | String | Llave del Test Plan por defecto. |
| `execution_summary` | String | Título genérico para nuevas ejecuciones. |
| `test_mode` | String | Modo: `clone` (Default) o `add`. |

---

## Variables de Entorno

PyJX2 escanea automáticamente el entorno local buscando el prefijo `PYJX2_AUTH_`. Ideal para **Pipelines CI/CD**.

- `PYJX2_AUTH_USERNAME`
- `PYJX2_AUTH_PASSWORD` (Soporta `ENC:`)
- `PYJX2_AUTH_ENV`

---

## Ejemplo Completo (`pyjx2.toml`)

```toml
[auth]
username = "admin@example.com"  # (1)
password = "ENC:gAAAAABlkX2..."  # (2)
env = "QA"                      # (3)

[setup]
test_mode = "add"               # (4)
execution_summary = "Nightly Test Execution"

[sync]
folder = "./evidence"           # (5)
status = "PASS"                 # (6)
recursive = true
allowed_extensions = [".pdf", ".png", ".jpg"]
```

1.  Tu correo electrónico o identificador de usuario en Atlassian.
2.  Token de API (altamente recomendado usar el formato cifrado `ENC:`).
3.  Entorno de destino: `QA` o `DEV`.
4.  Controla si los casos de prueba se clonan o se agregan directamente.
5.  Ruta local donde se encuentran los archivos de evidencia.
6.  Estado que se aplicará a los tests sincronizados con éxito.
