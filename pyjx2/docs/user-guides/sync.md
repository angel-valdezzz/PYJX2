# Flujo de Sync (Sincronización)

La herramienta se vuelve excepcional en el rastreo de incidencias gracias al comando de `sync`. Es responsable de cargar tus archivos, vincularlos con las iteraciones, cambiar los estados e incrustarlos en una Execution.

## El modelo de coincidencia (Matching)

El algoritmo busca similitudes al listar una carpeta (y sus sub-carpetas, si no desactivas el escaneo recursivo mediante `--no-recursive`).
Para cada archivo recolectado tomará el *stem* (Nombre textual descartando el formato de extensión `.png`, `.pdf`) e iterará su búsqueda en este orden frente al Ticket objetivo:

1. **Test Key:** Por ej. `PROJ-123.jpg` detectará nativamente la llave originaria de pruebas pre-armada con `PROJ-123`.
2. **Text Summary:** Por ej. `Login Flow Correcto.jpg` aplicará normalización convirtiendo espacios, guiones bajos o camelCase y tratará de hacer coincidencia exacta en el sistema de búsqueda con `LOGIN FLOW CORRECTO`.

Si una similitud salta a la luz, automáticamente realizará un `PUT` cambiando el estado del Test que indiques (`PASS`, `FAIL`, etc) en esa Instancia y un `POST` adjuntando la fotografía, reporte o base de datos temporal recabada a lo largo del proceso del Tester (Humano u otro robot en otro end de CI).

## Modo de Uso (CLI)

```bash
pyjx2 sync \
  --execution PROJ-200 \
  --folder ./ejecucion_final_repo_evidence \
  --status FAIL
```

Al concluir el proceso verás en consola todo un árbol semántico enumerando satisfactoriamente cuáles archivos y llaves se anexaron con triunfo y alertando si quedaron archivos sueltos no identificados.
