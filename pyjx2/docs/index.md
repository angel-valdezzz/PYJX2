# Bienvenidos a PYJX2

PYJX2 es una herramienta de automatización para **Jira** y **Xray**, construida sobre arquitectura limpia y moderna en Python. Está diseñada con el propósito fundamental de agilizar la configuración de pruebas y la recolección de evidencias durante los distintos ciclos del desarrollo de software.

## ¿Qué puedes hacer con PYJX2?

En el corazón de PYJX2 operan dos comandos o flujos principales capaces de orquestar operaciones complejas a través de las APIs de Jira y Xray:

1. **Flujo de Preparación (Setup)**
   Si posees un Test Plan, puedes crear un entorno de pruebas completo en el que se incluyen casos de prueba que podrás clonar o agregar. Estos casos se organizarán en Test Sets que, a su vez, se vincularán a un Test Execution, finalizando el flujo con la actualización del Test Plan original mediante la referencia de la ejecución generada.

2. **Flujo de Sincronización (Sync)**
   Incluso si tienes cientos de evidencias generadas de distintas ejecuciones, PYJX2 examina un sistema de directorios buscando archivos compatibles, identificándolos con sus respectivos *Test Cases* para marcarlos con el estatus que se requiera permitiendo agrupar tests por 1 o mas estatus, e inyecta dichas evidencias como adjuntos oficiales dentro del propio Xray, de una sola corrida y sin equivocaciones humanas.

## Interfaces Disponibles

Para mejorar la usabilidad y la experiencia en PYJX2, dotamos a la herramienta de 3 ecosistemas diferentes para interactuar:

- **La Línea de Comandos (CLI):** Usa argumentos precisos como `$ pyjx2 setup ...` para incorporar el script dentro de CI/CD o pipelines nativos por consola.
- **La Interfaz Textual (TUI):** Una Interfaz de Usuario a Pantalla Completa directamente dentro de tu terminal. Perfecta para cuando interactúas de forma asistida y gráfica. ¡Un salvavidas de clicks!
- **El API Python:** Para las mentes creativas, se expusieron funciones compuestas, un robusto patrón Facade y un repositorio extensible para usar dentro de tus propios algoritmos y rutinas codificadas localmente.

¡Descubre más en la sección de Primeros Pasos!
