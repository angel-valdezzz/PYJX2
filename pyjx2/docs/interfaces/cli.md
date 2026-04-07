# Interfaz de Línea de Comandos (CLI)

PYJX2 está construido fuertemente en Typer y presenta banderas para los mandatos más estrictos directamente por invocación Shell. 

## Referencia Global 
```bash
pyjx2 [SUBCOMMAND] [OPTIONS]
```
Puedes sobrescribir las claves de la configuración permanentemente empleando `--jira-url`, `--jira-username`, `--password`, `--xray-client-id`, `--xray-client-secret`.
O indicar otro archivo maestro para jalar credenciales empleando `--config /path/to.json`.

---

## Modulo: `setup`
**Propósito:** Transfiere jerarquías creando el Test Execution.

| Flag | Tipo | Descripción |
|---|---|---|
| `--project` / `-p` | Text | Llave general de Proyecto Jira |
| `--test-plan` | Text | Llave del Test Plan Jira (v.g. PROJ-X) |
| `--execution-summary` / `-e` | Text | Summary Name para inyectar |
| `--test-set-summary` / `-s` | Text | Summary Name sobre el Set |
| `--reuse-tests` / `--clone-tests` | Boolean | Cambia método por defecto (clonar) por rehusar |

---

## Modulo: `sync`
**Propósito:** Transefiere datos de reportes físicos (local) hacia Cloud y cambia de estado las transiciones.

| Flag | Tipo | Descripción |
|---|---|---|
| `--execution` / `-e` | Text | El id en Jira referente al caso macro de ejecución |
| `--folder` / `-f` | Text | Path físico contenedor de evidencias |
| `--status` / `-s` | Text | (PASS, FAIL, TODO, EXECUTING, ABORTED) |
| `--recursive` / `--no-recursive` / `-R` | Boolean | Comportamiento del escaner (Activado por Defecto) |

---

## Modulo: `tui`
Levantará en full-screen una Interfaz para el usuario final. No admite flag de I/O a excepción de la carga del custom path de configuración global.
```bash
pyjx2 --config /otro/config.toml tui
```


---

## Modulo: `config` (Subcomandos Tácticos)

Ideal para labores de mantenimiento y utilitarios de tokens locales.

- **`encrypt-pass`**: Permite parsear en vivo una contraseña e imprimir el `ENC:..` del cifrado. (Admite `--help`).
- **`decrypt-pass`**: El caso contrario. Devuelve la frase temporal destilada para revisiones.
