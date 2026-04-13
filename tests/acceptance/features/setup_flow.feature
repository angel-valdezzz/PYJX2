# language: es
Característica: Flujo de Setup
  Como ingeniero QA
  Deseo automatizar la creación de Test Executions y Test Sets desde un Test Plan
  Para ejecutar pruebas de forma consistente sin configuración manual
  
  Antecedentes:
    Dado un cliente PyJX2 configurado
    Y el plan de pruebas "PROJ-1" tiene 2 pruebas
    
  Escenario: El setup completo crea una ejecución y un test set
    Cuando ejecuto el comando setup con test plan "PROJ-1" y aplicacion "APP_1"
    Entonces se crea una ejecución de pruebas
    Y se crea un test set
    
  Escenario: El test set se enlaza a la ejecución después del setup
    Cuando ejecuto el comando setup con test plan "PROJ-1" y aplicacion "APP_1"
    Entonces el test set queda enlazado a la ejecución de pruebas
    
  Escenario: Setup clona las pruebas por defecto
    Cuando ejecuto el comando setup con modo de clonacion
    Entonces 2 pruebas son clonadas
    Y 0 pruebas son reusadas
    
  Escenario: Setup agrega pruebas sin clonarlas si se usa modo agregar
    Cuando ejecuto el comando setup con modo de agregar
    Entonces 0 pruebas son clonadas
    Y 2 pruebas son reusadas
    
  Escenario: Las pruebas clonadas se agregan al test set
    Cuando ejecuto el comando setup con modo de clonacion
    Entonces todas las pruebas clonadas se agregan al test set
    
  Escenario: Setup falla si el test plan no existe
    Dado que el plan de pruebas "PROJ-999" no existe
    Cuando ejecuto el comando setup con test plan "PROJ-999"
    Entonces se lanza una excepción de tipo "ValueError" conteniendo "invalido o no existe"
    
  Escenario: Se emiten mensajes de progreso durante el setup
    Cuando ejecuto el comando setup con un callback de progreso
    Entonces al menos 4 mensajes de progreso son recibidos
    
  Escenario: Un test plan vacío aún produce una ejecución y un test set
    Dado que el plan de pruebas "PROJ-1" tiene 0 pruebas
    Cuando ejecuto el comando setup con test plan "PROJ-1" y aplicacion "APP_1"
    Entonces se crea una ejecución de pruebas
    Y se crea un test set
    Y 0 pruebas son procesadas
