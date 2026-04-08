# API Python (Para Desarrolladores)

PyJX2 expone una interfaz programática robusta a través del patrón **Facade**, permitiendo a los desarrolladores integrar las capacidades de Jira y Xray directamente en sus propios scripts y rutinas de automatización.

## Inicialización y Factorías

Existen múltiples formas de instanciar el cliente principal dependiendo del origen de los datos.

### Mediante Configuración Automática
Ideal cuando se cuenta con un archivo `pyjx2.toml` o variables de entorno.

```python
from pyjx2 import PyJX2

# Discovery: looks for pyjx2.toml or pyjx2.json in current directory
pjx = PyJX2.from_config()
```

### Mediante Credenciales Explícitas
Útil para integraciones dinámicas donde las credenciales se obtienen de un Vault o gestor de secretos.

```python
from pyjx2 import PyJX2

pjx = PyJX2.from_credentials(
    username="user@company.com",
    password="api_token_here",
    env="QA"  # or "DEV"
)
```

---

## Gestión de Entidades (CRUD)

El Facade proporciona acceso simplificado a las entidades principales de Xray.

### Tests
Operaciones unitarias sobre casos de prueba individuales.

```python
# Fetch a test
test = pjx.get_test("QAX-123")

# Create a new manual test
new_test = pjx.create_test(
    project_key="QAX",
    summary="Login Validation",
    test_type="Manual",
    labels=["regression", "high-priority"]
)

# Clone an existing test
cloned = pjx.clone_test("QAX-101", "QAX")
```

### Test Sets
Agrupaciones lógicas de casos de prueba.

```python
# Create a test set
ts = pjx.create_test_set("QAX", "Sprint 1 Regression Set")

# Add tests to a set
pjx.add_tests_to_set(ts.key, ["QAX-110", "QAX-111", "QAX-112"])

# Update metadata
pjx.update_test_set(ts.key, summary="Updated Set Title")
```

### Test Executions
Instancias de ejecución donde se registran los resultados.

```python
# Create an execution
exec_issue = pjx.create_test_execution(
    project_key="QAX", 
    summary="Daily Execution - 2024-04-08"
)

# Link a test set to an execution
pjx.add_test_set_to_execution(exec_issue.key, ts.key)
```

---

## Flujos de Negocio (Business Logic)

PyJX2 encapsula procesos complejos en métodos de alto nivel que incluyen orquestación y reporte de progreso.

### Método `setup`
Orquesta la creación de planes de ejecución completos.

```python
def my_logger(msg: str):
    print(f"PyJX2 Event: {msg}")

result = pjx.setup(
    test_plan_key="QAX-100",
    execution_summary="Weekly Regression",
    application="APP_NAME",
    test_mode="clone",  # "clone" or "add"
    progress_callback=my_logger
)

print(f"Created Execution: {result.test_executions[0].key}")
```

### Método `sync`
Sincroniza evidencias locales con Jira en un solo paso.

```python
result = pjx.sync(
    execution_key="QAX-501",
    folder="./test-reports/evidence",
    status="PASS",
    recursive=True,
    upload_mode="append"  # "append" or "replace"
)

print(f"Updated {result.updated_tests} tests with evidence.")
```

---

## Utilidades de Seguridad

Métodos auxiliares para el manejo de credenciales cifradas.

```python
# Encrypt plain text for config files
secret_token = PyJX2.encrypt_password("my_secret_password")
# Result: "ENC:..."

# Decrypt for audit / internal use
plain = PyJX2.decrypt_password(secret_token)
```

## Vías de Escape (Escape Hatches)

Si se requiere realizar operaciones REST crudas que no están expuestas en los métodos simplificados, se puede acceder directamente a los clientes de bajo nivel.

```python
# Post directly to Jira API
pjx.jira.post("issue/QAX-123/comment", {"body": "Automation finished."})

# Call Xray specific endpoints
pjx.xray.get("testrun/123456")
```
