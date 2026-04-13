# Casos de Uso Comunes

Esta sección describe escenarios típicos de implementación de PyJX2 en entornos profesionales de ingeniería de software y control de calidad (QA).

## 1. Integración en Pipelines de CI/CD (Jenkins / GitLab CI)

El uso principal de PyJX2 en entornos automatizados es la preparación de ejecuciones antes del despliegue y la sincronización de resultados después de las pruebas.

### Escenario: Post-Ejecución de Selenium/Cypress
Si tu suite de automatización genera capturas de pantalla o reportes PDF, puedes sincronizarlos automáticamente.

**Configuración recomendada:**
Usa variables de entorno para evitar almacenar credenciales en el código del pipeline.

```bash
# Jenkins Pipeline Snippet
sh "pyjx2 sync --execution ${JIRA_EXEC_KEY} --folder ./automated-results/screenshots --status PASS"
```

## 2. Automatización mediante Scripts Python

Si tu organización utiliza Python para orquestar herramientas de bajo nivel, puedes usar el cliente `PyJX2` como motor de comunicación.

### Escenario: Clonación Masiva para Regresión
Carga un plan de pruebas y genera una ejecución de forma programática.

```python
from pyjx2 import PyJX2

# 1. Initialize with config (reads env vars for security)
pjx = PyJX2.from_config()

# 2. Daily Setup
result = pjx.setup(
    test_plan_key="QAX-50",
    execution_summary="Daily Regression Cycle",
    application="CORE_API",
    test_mode="clone"
)

print(f"Test Execution created: {result.test_executions[0].key}")
```

## 3. Uso de Interfaz

Los probadores manuales pueden utilizar la **TUI** (Terminal User Interface) para evitar errores de tipeo al subir evidencias.

### Escenario: Recopilación de Pantallazos en Lote
1. Realiza tus pruebas manuales y guarda los pantallazos con el nombre del Ticket (ej: `QAX-10.png`, `QAX-11.png`).
2. Abre PyJX2 TUI: `pyjx2 tui`.
3. Navega a la pestaña de **Sincronización (F3)**.
4. Selecciona la carpeta y presiona **Ejecutar**.
5. PyJX2 se encargará de emparejar cada imagen con su respectivo ticket en Jira automáticamente.

