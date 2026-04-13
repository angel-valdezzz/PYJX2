# Flujo de Setup (Preparación)

Si posees un test plan, puedes crear un entorno de pruebas, en el que se incluyen casos de prueba que puedes clonar o agregar, dichos casos se agregaran a test sets y los tests sets se agregaran al test execution para terminar actualizando el test plan con la referencia del test execution.

## ¿Cómo funciona bajo la lupa?

1. **Lectura del Plan**: Se identifica el **Test Plan** origen (ej. `PROJ-100`) para extraer su alcance de pruebas.
2. **Gestión de Casos**: Dependiendo del modo seleccionado, se crean copias independientes (clonación) o se vinculan los casos originales al nuevo entorno.
3. **Agrupación en Sets**: Los casos procesados se organizan dentro de uno o varios **Test Sets** para mantener la estructura lógica.
4. **Ejecución y Cierre**: Todo el ecosistema (Test Sets y Tests) se consolida en un nuevo **Test Execution** y se actualiza el **Test Plan** original para que mantenga la trazabilidad de esta nueva iteración.

## ¿Tests Clonados o Tests Agregados?

- **Modo `clone`** (Predeterminado): Crea copias físicas de cada caso de prueba en el proyecto destino. Es el modo más seguro para no alterar la historia de los casos originales.
- **Modo `add`**: Vincula directamente los casos de prueba originales al Test Set y a la Ejecución. Ideal para regresiones rápidas donde los casos no cambian.

---

## Ejemplo de uso base usando CLI

```bash
pyjx2 setup \
  --test-plan QAX-100 \
  --execution-summary "Ejecución Regresión Sprint 8" \
  --application AXA_WEB \
  --test-mode clone
```

El script imprimirá una tabla resumen con las llaves del **Test Set** y del **Test Execution** generados. Todo este ecosistema quedará vinculado automáticamente al Test Plan Original para mantener la trazabilidad.
