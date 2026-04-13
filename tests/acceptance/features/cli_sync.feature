# language: es
Característica: CLI Sync
  Como ingeniero de QA
  Quiero ejecutar el comando sync desde la terminal
  Para poder emparejar automáticamente archivos de evidencia con resultados de tests

  Escenario: El comando sync tiene éxito con todos los argumentos requeridos
    Cuando invoco "pyjx2 sync" con todos los argumentos requeridos
    Entonces el código de salida es 0

  Escenario: La salida del comando sync muestra la tabla de tests emparejados
    Cuando invoco "pyjx2 sync" con todos los argumentos requeridos
    Entonces el código de salida es 0
    Y la salida contiene "PROJ-10"

  Escenario: El comando sync falla cuando falta --execution
    Cuando invoco "pyjx2 sync" sin "--execution"
    Entonces el código de salida no es 0

  Escenario: El comando sync falla cuando falta --folder
    Cuando invoco "pyjx2 sync" sin "--folder"
    Entonces el código de salida no es 0

  Escenario: El comando sync falla cuando falta --status
    Cuando invoco "pyjx2 sync" sin "--status"
    Entonces el código de salida no es 0

  Escenario: El comando sync rechaza un valor de status inválido
    Cuando invoco "pyjx2 sync" con el status "INVALID_STATUS"
    Entonces el código de salida no es 0

  Esquema del escenario: El comando sync acepta todos los valores de status válidos
    Cuando invoco "pyjx2 sync" con el status "<status>"
    Entonces el código de salida es 0

    Ejemplos:
      | status     |
      | PASS       |
      | FAIL       |
      | TODO       |
      | EXECUTING  |
      | ABORTED    |

  Escenario: El comando sync falla elegantemente cuando no se encuentra la folder
    Dado que la API de sync lanza un error FileNotFoundError
    Cuando invoco "pyjx2 sync" con todos los argumentos requeridos
    Entonces el código de salida no es 0

  Escenario: El comando sync muestra tests no emparejados en la salida
    Dado que el resultado de sync tiene 2 tests sin emparejar
    Cuando invoco "pyjx2 sync" con todos los argumentos requeridos
    Entonces la salida muestra los tests sin evidencia

  Escenario: El comando sync pasa el flag --no-recursive a la API
    Cuando invoco "pyjx2 sync" con "--no-recursive"
    Entonces el parámetro recursive es False en la llamada a la API

  Escenario: El comando sync usa modo recursive por defecto
    Cuando invoco "pyjx2 sync" con todos los argumentos requeridos
    Entonces el parámetro recursive es True en la llamada a la API
