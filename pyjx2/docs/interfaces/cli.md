# Interfaz de Línea de Comandos (CLI)

PyJX2 proporciona una interfaz de línea de comandos (CLI) potente y versátil construida sobre `Typer`, permitiendo la integración nativa en pipelines de CI/CD y despliegues automatizados.

## Opciones Globales y Autenticación

Todas las invocaciones de comandos admiten un conjunto de opciones comunes que permiten sobrescribir la configuración detectada automáticamente.

| Opción | Alias | Descripción |
| :--- | :--- | :--- |
| `--config` | `-c` | Ruta absoluta o relativa al archivo `pyjx2.toml` o `pyjx2.json`. |
| `--env` | | Define el entorno de conexión: `QA` (default) o `DEV`. |
| `--jira-username`| `-u` | Identificador de usuario o email para la API de Jira. |
| `--password` | `-p` | Contraseña o API Token (soporta formato `ENC:` cifrado). |

---

## Módulo: `setup`
El subcomando setup se encarga de generar un ambiente en Jira para los casos de prueba.

```bash
# Ejemplo de uso estándar
pyjx2 setup --test-plan QAX-101 --execution-summary "Sprint 10 Validation" --application CRM_WEB
```

### Argumentos Específicos

- **`--test-plan`**: (Obligatorio) Llave del Test Plan origen.
- **`--execution-summary`** (`-e`): (Obligatorio) Título para el nuevo ticket de Test Execution.
- **`--application`** (`-a`): (Obligatorio) Nombre identificador del componente bajo prueba.
- **`--test-mode`** (`-m`): Define el tratamiento de los Test Cases:
    - `clone` (Default): Crea copias nuevas de los tests en el proyecto destino.
    - `add`: Agrega los tests originales directamente sin clonarlos.

---

## Módulo: `sync`

El comando `sync` escanea el sistema de archivos local para cargar evidencias y transicionar estados en Xray de forma masiva.

```bash
# Sincronización recursiva con modo append
pyjx2 sync --execution QAX-200 --folder ./reports --status PASS --recursive
```

### Argumentos Específicos

- **`--execution`** (`-e`): (Obligatorio) Llave del Test Execution destino.
- **`--folder`** (`-f`): (Obligatorio) Ruta al directorio que contiene las evidencias físicas.
- **`--status`** (`-s`): Estado global a aplicar (`PASS`, `FAIL`, `TODO`, `EXECUTING`, `ABORTED`).
- **`--recursive` / `--no-recursive`**: Habilita o deshabilita el escaneo de subdirectorios.
- **`--extensions`**: Lista de extensiones separadas por coma (ej. `.pdf,.png,.jpg`). Por defecto `.pdf`.
- **`--mode`** (`-m`): Define el comportamiento de la subida: `append` (añadir) o `replace` (reemplazar existente).
- **`--status-map`**: Inyecta un JSON para definir estados heterogéneos por llave de test.
    - Ejemplo: `--status-map '{"QAX-1":"FAIL", "QAX-2":"PASS"}'`

---

<!--
## Módulo: `config`

Proporciona utilidades tácticas para el mantenimiento de credenciales y entornos.

### `encrypt-pass`
Genera un token cifrado mediante el algoritmo AES-128 integrado en PyJX2.
```bash
pyjx2 config encrypt-pass "mi_contraseña_real"
# Salida: ENC:yXv5xT2_FqD6s...
```

### `decrypt-pass`
Desencripta un token previamente generado para labores de auditoría técnica.
```bash
pyjx2 config decrypt-pass "ENC:yXv5xT2_FqD6s..."
```
-->

---

## Misceláneos

### `tui`
Lanza la interfaz gráfica táctil-terminal de PyJX2. Ideal para configuraciones manuales asistidas.
```bash
pyjx2 tui
```

### `docs`
Inicia el motor de documentación local (MkDocs) y abre el manual completo en una ventana de navegador. Requiere tener `mkdocs` instalado.
```bash
pyjx2 docs
```
