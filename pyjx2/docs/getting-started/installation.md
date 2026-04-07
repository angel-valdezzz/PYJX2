# Instalación

A fin de correr PYJX2 y ejecutar tus despliegues contra Jira, necesitas adecuar tu entorno primero. PyJX2 se encuentra empaquetado asimilando una aplicación ejecutable nativa construida a base de librerías modernas como Textual, Typer y Requests, garantizando una instalación rápida.

## Requisitos Previos

- Python 3.10 o superior (Recomendado >= 3.11).
- Credenciales vigentes de Atlassian Jira Cloud y Xray API App credentials.

## Método 1: Pip Módulo Nativo

La herramienta incluye un archivo `pyproject.toml` optimizado. Clonando el proyecto puedes inyectarlo directamente en tu carpeta de entorno global o en tu entorno virtual:

```bash
pip install -e .
```

Si prefieres omitir el archivo `.toml` e instalar manual y estrictamente las dependencias críticas por alguna limitante en tu control de red, emplea:

```bash
pip install requests typer rich textual toml jsonschema cryptography
```

## Método 2: Empleando Poetry

Mantenemos soporte total para el gestor moderno *Python Poetry*. La estructura lo interpretará nativamente para generar tu nuevo environment sin que debas ocuparte de nada más:

```bash
poetry install
```

Para ingresar dentro del shell configurado y correr localmente `pyjx2`:

```bash
poetry shell
```

## Dependencias Extra de Documentación e Infraestructura

En caso de que planees aportar código o extender esta valiosa documentación, instala las herramientas del perfil Dev habilitadas:

```bash
# Como entorno global
pip install ".[dev,docs]"

# Para Poetry:
poetry install --with dev,docs
```
