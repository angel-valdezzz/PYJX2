# Flujo de Setup (Preparación)

Si posees un test plan, puedes crear un entorno de pruebas, en el que se incluyen casos de prueba que puedes clonar o agregar, dichos casos se agregaran a test sets y los tests sets se agregaran al test execution para terminar actualizando el test plan con la referencia del test execution.

## ¿Cómo funciona bajo la lupa?

1. **Lectura del Plan**: Se identifica el **Test Plan** origen (ej. `PROJ-100`) para extraer su alcance de pruebas.
2. **Gestión de Casos**: Dependiendo del modo seleccionado, se crean copias independientes (clonación) o se vinculan los casos originales al nuevo entorno.
3. **Agrupación en Sets**: Los casos procesados se organizan dentro de uno o varios **Test Sets** para mantener la estructura lógica.
4. **Ejecución y Cierre**: Todo el ecosistema (Test Sets y Tests) se consolida en un nuevo **Test Execution** y se actualiza el **Test Plan** original para que mantenga la trazabilidad de esta nueva iteración.

## ¿Tests Clonados o Tests Agregados?

Por defecto, se crearán _clones estandarizados_ (`--test-mode clone`) de cada test dentro del proyecto destino para no entorpecer pruebas pasadas por otros usuarios sobre el caso original. Si prefieres utilizar los tests originales (ideal para regresiones), puedes cambiar al modo agregado enviando `--test-mode add` al invocar a PYJX2.

## Ejemplo de uso base usando CLI

```bash
pyjx2 setup \
  --test-plan PROJ-100 \
  --execution-summary "Ejecución Regresión Sep" \
  --application AXA_WEB \
  --test-mode clone
```

El script imprimirá en pantalla las nuevas llaves del Set y del Execution que se han generado para guiarte. Todo lo nuevo quedará atado lógicamente con el Plan Original.
