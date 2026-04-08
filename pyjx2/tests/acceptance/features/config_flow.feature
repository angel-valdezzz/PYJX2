# language: es

Característica: Carga de Configuración
  Como usuario de pyjx2
  Quiero configurar la herramienta mediante archivos, variables de entorno o argumentos de CLI
  Para poder adaptarla a cualquier flujo de trabajo sin repetir credenciales

  Escenario: Los ajustes se cargan desde un archivo de configuración TOML
    Dado un archivo de configuración TOML con credenciales válidas
    Cuando cargo los ajustes desde ese archivo
    Entonces el entorno de Jira es "QA"
    Y el ID de cliente de Xray es "my_client"
    Y la clave del plan de pruebas de preparación es "PROJ-100"
    Y el estado de sincronización es "PASS"

  Escenario: Los ajustes se cargan desde un archivo de configuración JSON
    Dado un archivo de configuración JSON con credenciales válidas
    Cuando cargo los ajustes desde ese archivo
    Entonces el usuario de Jira es "user@example.com"
    Y el ID de cliente de Xray es "json_client"
    Y el valor de reutilizar pruebas en preparación es Verdadero
    Y el valor de recursividad en sincronización es Falso

  Escenario: pyjx2.toml es auto-descubierto en el directorio actual
    Dado que existe un archivo "pyjx2.toml" en el directorio actual
    Cuando cargo los ajustes sin especificar un archivo
    Entonces el entorno de Jira es "QA"

  Escenario: pyjx2.json es auto-descubierto en el directorio actual
    Dado que existe un archivo "pyjx2.json" en el directorio actual
    Cuando cargo los ajustes sin especificar un archivo
    Entonces el entorno de Jira es "DEV"

  Escenario: Los valores en tiempo de ejecución tienen prioridad sobre el archivo
    Dado un archivo de configuración TOML con credenciales válidas
    Cuando cargo los ajustes desde ese archivo con el password sobreescrito como "runtime_token"
    Entonces el password de Jira es "runtime_token"
    Y el entorno de Jira sigue siendo "QA"

  Escenario: Las variables de entorno tienen prioridad sobre el archivo
    Dado un archivo de configuración TOML con credenciales válidas
    Y la variable de entorno "PYJX2_JIRA_PASSWORD" está establecida como "env_token"
    Cuando cargo los ajustes desde ese archivo
    Entonces el password de Jira es "env_token"

  Escenario: La falta de campos obligatorios lanza un error descriptivo
    Cuando cargo los ajustes sin ninguna configuración
    Entonces se lanza un error de tipo "ValueError"
    Y el mensaje de error menciona "jira.username"
    Y el mensaje de error menciona "xray.client_id"

  Escenario: Un estado de sincronización inválido falla la validación del esquema
    Dado un archivo de configuración TOML con un estado de sincronización inválido "NOT_VALID"
    Cuando cargo los ajustes desde ese archivo
    Entonces se lanza un error de validación de esquema

  Escenario: La falta del campo obligatorio jira.username en JSON falla la validación
    Dado un archivo de configuración JSON al que le falta el campo "username" en la sección jira
    Cuando cargo los ajustes desde ese archivo
    Entonces se lanza un error de validación de esquema

  Escenario: Las credenciales de Jira se reciclan para Xray si faltan
    Dado un archivo de configuración TOML sin sección Xray
    Cuando cargo los ajustes desde ese archivo con el password sobreescrito como "recycled_token"
    Entonces el ID de cliente de Xray es "user@example.com"
    Y el password de Jira es "recycled_token"
