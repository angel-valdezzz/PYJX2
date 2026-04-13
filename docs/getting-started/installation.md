# Instalación

A fin de ejecutar una regresión, necesitas adecuar tu entorno primero. PyJX2 se encuentra empaquetado asimilando una aplicación ejecutable nativa construida a base de librerías modernas como Textual, Typer y Requests, garantizando una instalación rápida.

## Requisitos Previos

!!! info "Requisitos Técnicos"
    - **Python**: Versión 3.10 o superior (Recomendado >= 3.11).
    - **Credenciales**: Acceso a Jira Cloud y Xray API App credentials.

## Métodos de Instalación

=== "Pip (Nativo)"
    La herramienta incluye un archivo `pyproject.toml` optimizado.

    ??? tip "Aislamiento de Entorno (Recomendado)"
        Se recomienda instalar PyJX2 dentro de un entorno virtual (`venv` o `conda`) para evitar conflictos.

    ```bash
    pip install -e .
    ```

    O instale manualmente las dependencias críticas:
    ```bash
    pip install requests typer rich textual toml jsonschema cryptography
    ```

=== "Poetry"
    Mantenemos soporte total para el gestor moderno *Python Poetry*:

    ```bash
    # Instalación automática de dependencias y CLI
    poetry install

    # Acceso al entorno virtual
    poetry shell
    ```

=== "Entorno de Desarrollo"
    Si planeas extender la funcionalidad o la documentación:

    !!! note "Perfiles Adicionales"
        - **Pip**: `pip install ".[dev,docs]"`
        - **Poetry**: `poetry install --with dev,docs`
