# language: es
Característica: Flujo de Sync
  Como ingeniero de QA
  Quiero emparejar archivos de evidence con test cases en una test execution
  Para poder subir resultados automáticamente y actualizar el status de los tests

  Antecedentes:
    Dado un cliente PyJX2 configurado
    Y una test execution "PROJ-30" con los tests "PROJ-10" (Login), "PROJ-11" (Logout), "PROJ-12" (Register)

  Escenario: Los archivos que coinciden con los prefijos del summary de los tests son emparejados
    Dado una carpeta de evidence con los archivos "Login flow.png" y "Logout flow.pdf"
    Cuando ejecuto el comando sync para la execution "PROJ-30" con el status "PASS"
    Entonces 2 tests son emparejados
    Y los tests emparejados son "PROJ-10" y "PROJ-11"

  Escenario: Los tests emparejados actualizan su status
    Dado una carpeta de evidence con los archivos "Login flow.png" y "Logout flow.pdf"
    Cuando ejecuto el comando sync para la execution "PROJ-30" con el status "FAIL"
    Entonces el status "FAIL" se establece para todos los tests emparejados

  Escenario: Los tests emparejados suben su evidence
    Dado una carpeta de evidence con los archivos "Login flow.png" y "Logout flow.pdf"
    Cuando ejecuto el comando sync para la execution "PROJ-30" con el status "PASS"
    Entonces se sube la evidence para todos los tests emparejados

  Escenario: El escaneo recursive detecta archivos en subdirectorios
    Dado una carpeta de evidence con un archivo anidado "subdir/Register user.png"
    Cuando ejecuto el comando sync con el modo recursive habilitado
    Entonces "PROJ-12" es emparejado

  Escenario: El escaneo no recursive ignora archivos en subdirectorios
    Dado una carpeta de evidence con un archivo anidado "subdir/Register user.png"
    Cuando ejecuto el comando sync con el modo recursive deshabilitado
    Entonces "PROJ-12" no es emparejado

  Escenario: Se informan los tests no emparejados
    Dado una carpeta de evidence solo con el archivo "Login flow.png"
    Cuando ejecuto el comando sync para la execution "PROJ-30" con el status "PASS"
    Entonces los tests sin emparejar incluyen "PROJ-11" y "PROJ-12"

  Escenario: Se informan los archivos no emparejados
    Dado una carpeta de evidence con los archivos "Login flow.png" y "unrelated.txt"
    Cuando ejecuto el comando sync para la execution "PROJ-30" con el status "PASS"
    Entonces los archivos no utilizados incluyen "unrelated.txt"

  Escenario: Una carpeta de evidence vacía no produce emparejamientos
    Dado una carpeta de evidence vacía
    Cuando ejecuto el comando sync para la execution "PROJ-30" con el status "PASS"
    Entonces 0 tests son emparejados
    Y los 3 tests resultan sin emparejar

  Escenario: Sync falla cuando la carpeta de evidence no existe
    Cuando ejecuto el comando sync con la carpeta "/ruta/no/existente/para/pyjx2"
    Entonces se lanza un error "FileNotFoundError"

  Escenario: El emparejamiento de archivos no distingue entre mayúsculas y minúsculas para los summaries
    Dado una carpeta de evidence con el archivo "login flow.png"
    Cuando ejecuto el comando sync para la execution "PROJ-30" con el status "PASS"
    Entonces "PROJ-10" es emparejado
