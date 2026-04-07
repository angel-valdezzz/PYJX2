# Flujo de Setup (Preparación)

El comando de `setup` te asiste orquestando automáticamente las entidades en Xray relacionadas con tus planes.

## ¿Cómo funciona bajo la lupa?

1. Examina integralmente un número de ID en especifíco referido a un **Test Plan** existente (e.g., `PROJ-100`).
2. Recopila uno a uno los casos pre-asignados a ése plan.
3. Almacena temporalmente una lista a nivel local y comienza a inyectarlos a un **Test Set** y de vuelta a un **Test Execution**.

## ¿Tests Clonados o Tests Re-usados?

Por defecto, se crearán _clones estandarizados_ de cada test dentro del proyecto destino que especifiques para no entorpecer pruebas pasadas por otros usuarios sobre el caso original. Pero si prefieres rehusar tests (ideal para el regression test), puedes activar la bandera `--reuse-tests` al invocar a PYJX2 para en su lugar amarrar las entidades base existentes a la nueva corrida del Sprint.

## Ejemplo de uso base usando CLI

```bash
pyjx2 setup \
  --project PROJ \
  --test-plan PROJ-100 \
  --execution-summary "Execution (Semana 12)" \
  --test-set-summary "Pruebas Base"
```

El script imprimirá en pantalla las nuevas llaves del Set y del Execution que se han generado para guiarte. Todo lo nuevo quedará atado lógicamente con el Plan Original en la Nube.
