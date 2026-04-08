# language: es
Característica: CLI Setup
  Como ingeniero de QA
  Quiero ejecutar el comando setup desde la terminal
  Para poder crear la infraestructura de pruebas sin escribir scripts de Python

  Escenario: El comando setup tiene éxito con todos los argumentos requeridos
    Cuando invoco "pyjx2 setup" con todos los argumentos requeridos
    Entonces el código de salida es 0
    Y la salida contiene la clave de test execution "PROJ-30"
    Y la salida contiene la clave de test set "PROJ-20"

  Escenario: El comando setup muestra una tabla de resumen
    Cuando invoco "pyjx2 setup" con todos los argumentos requeridos
    Entonces el código de salida es 0
    Y la salida contiene "Test Execution"
    Y la salida contiene "Test Set"

  Escenario: El comando setup falla cuando falta --test-plan
    Cuando invoco "pyjx2 setup" sin "--test-plan"
    Entonces el código de salida no es 0

  Escenario: El comando setup falla cuando falta --execution-summary
    Cuando invoco "pyjx2 setup" sin "--execution-summary"
    Entonces el código de salida no es 0

  Escenario: El comando setup falla cuando faltan las credentials de Jira
    Cuando invoco "pyjx2 setup" sin credentials
    Entonces el código de salida no es 0

  Escenario: El comando setup usa --test-mode add para agregar sin clonar
    Cuando invoco "pyjx2 setup" con modo agregar "--test-mode add"
    Entonces el parámetro test_mode es "add" en la llamada a la API

  Escenario: El comando setup usa modo clone por defecto
    Cuando invoco "pyjx2 setup" con todos los argumentos requeridos
    Entonces el parámetro test_mode es "clone" en la llamada a la API

  Escenario: El comando setup falla elegantemente cuando la API lanza un error
    Dado que la API de setup lanza un error RuntimeError "Jira connection failed"
    Cuando invoco "pyjx2 setup" con todos los argumentos requeridos
    Entonces el código de salida no es 0
    Y la salida contiene un mensaje de error

  Escenario: El comando setup acepta un archivo config explícito
    Dado un archivo de configuración config TOML válido
    Cuando invoco "pyjx2 setup" con "--config" apuntando a ese archivo
    Entonces el código de salida es 0
