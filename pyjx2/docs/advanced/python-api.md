# API Python (Para Desarrolladores)

Todos los comandos en CLI son una abstracción que cubre las dependencias físicas para acceder a nuestro núcleo: Nuestro inmenso objeto constructor `PyJX2` (Facade). Puedes importarlo a placer en tus propios repositorios Python y explotar Jira y Xray orgánicamente dentro de tus scripts sin perder compatibilidad y limpieza con la manipulación REST original.

## Inicialización

Empieza leyendo la configuración local tal y como la lee el cli invocando la librería de Config.

```python
from pyjx2.api.client import PyJX2
from pyjx2.infrastructure.config.settings import load_settings

settings = load_settings()
pjx = PyJX2(settings)
```

## Exploración Básica

Con `pjx` al mando, tienes acceso directo, claro, y tipado a operaciones unitarias (Cosa que la CLI a menudo pre-empaqueta pero no expone crudamente).

```python
test = pjx.get_test("PROJ-123")
```

```python
new_test = pjx.create_test("PROJ", "My new test", labels=["regression"])
```

```python
pjx.update_test_status("PROJ-200", "PROJ-123", "PASS")
```

```python
ts = pjx.create_test_set("PROJ", "My Test Set")
pjx.add_tests_to_set(ts.key, ["PROJ-123", "PROJ-124"])
```

## Flujos Grandes Explotables

Si tu propio Script sólo desea un atajo o wrapper rápido para un plan pre-establecido automatizado en el CI, puedes inyectar las funciones macro de `Run/Sync` enviando tus *callbacks* que reciban los Strings por paso a modo de rastreo (Ideal para reenviarlos nativamente a un Logger o Telemetría de App Dynamics o Slack).

```python
def my_custom_slack_logger(msg: str):
    requests.post("https://slack/webhook", data=msg)

result = pjx.setup(
    project_key="PROJ",
    test_plan_key="PROJ-100",
    execution_summary="Execution",
    test_set_summary="Test Set",
    progress_callback=my_custom_slack_logger,
)
```

## Funciones Auxiliares Estáticas de Seguridad

En el caso estricto en que sólo desees usar nuestra funcionalidad interna para procesar Strings `ENC:` sin tocar conexiones de Jira, se exponen dos métodos en la clase principal que pueden llamarse sin instanciar:

```python
from pyjx2.api.client import PyJX2

mi_candado = PyJX2.encrypt_password("12345")
# Retorna: ENC:ZgAAAAABlkX2...

es_igual = PyJX2.decrypt_password(mi_candado)
print("12345" == es_igual) # True
```

## Vías de Escape Crudas

Eventualmente nosotros o Xray actualizarán las APIs, y ciertos Endpoints tardarán un poco en llegar a nivel PYJX2.
Puedes interceptar variables a nivel `JiraClient` y `XrayClient` haciendo uso de tu objeto instanciado con métodos directos y seguros REST que se autenticarán correctamente en Header y Body con Json automático.

```python
un_nuevo_metodo = pjx.jira.post("testexec/12345/test", {"add": ["PROJ-123"]})
```
