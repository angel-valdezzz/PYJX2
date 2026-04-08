# Flujo de Sync (Sincronización)

La herramienta se vuelve excepcional en el rastreo de incidencias gracias al comando de `sync`. Es responsable de cargar tus archivos y cambiar los estados.

## El modelo de coincidencia (Matching)

El algoritmo busca similitudes al listar una carpeta (y sus sub-carpetas, si no desactivas el escaneo recursivo mediante `--no-recursive`).
Para cada archivo recolectado tomará el *stem* (Nombre textual descartando el formato de extensión `.png`, `.pdf`) e iterará su búsqueda en este orden frente al Ticket objetivo:

1. **Test Key:** Por ej. `PROJ-123.jpg` detectará nativamente la llave originaria de pruebas pre-armada con `PROJ-123`.
2. **Text Summary:** Por ej. `Login Flow Correcto.jpg` aplicará normalización convirtiendo espacios, guiones bajos o camelCase y tratará de hacer coincidencia exacta en el sistema de búsqueda con `LOGIN FLOW CORRECTO`.

Si una similitud salta a la luz, automáticamente realizará un `PUT` cambiando el estado del Test que indiques para marcarlos con el estatus que se requiera permitiendo agrupar tests por 1 o mas estatus en esa Instancia y un `POST` adjuntando la fotografía o reporte recabada a lo largo del proceso del Tester.

## Modos de Subida (`--mode`)

- **`append`** (Predeterminado): Añade las nuevas evidencias a los casos de prueba sin borrar las que ya existan.
- **`replace`**: Elimina todos los archivos adjuntos previos del Test Run antes de subir los nuevos. Útil para re-ejecuciones limpias.

## Filtro de Extensiones (`--extensions`)

Por seguridad, PYJX2 solo procesa archivos `.pdf` por defecto. Puedes expandir esto pasando una lista separada por comas:

```bash
--extensions .png,.jpg,.jpeg,.pdf
```

## Mapeo de Estados (`--status-map`)

Si quieres que ciertos archivos marquen estados distintos al global (`--status`), puedes pasar un JSON:

```bash
--status-map '{"PROJ-101":"FAIL", "PROJ-102":"ABORTED"}'
```

## Modo de Uso (CLI)

```bash
pyjx2 sync \
  --execution QAX-200 \
  --folder ./evidencias \
  --status PASS \
  --mode append \
  --extensions .png,.jpg \
  --recursive
```

Al concluir el proceso verás en consola una tabla resumen enumerando cuántos tests fueron actualizados, cuántos archivos se subieron y si quedaron archivos sueltos no identificados.
