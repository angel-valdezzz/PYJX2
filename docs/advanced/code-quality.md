# Calidad de Código

PyJX2 incluye tres capas de validación para sostener la arquitectura limpia y reducir regresiones de mantenimiento:

## Herramientas

### Ruff

Ruff cubre dos responsabilidades:

- formateo automático del código Python
- lint rápido para imports y errores sintácticos de alta señal

```bash
poetry run ruff format pyjx2 tests
poetry run ruff check pyjx2 tests
```

### mypy

`mypy` valida tipado estático del núcleo del sistema. En esta primera etapa el alcance está centrado en:

- `pyjx2/domain`
- `pyjx2/application`

```bash
poetry run mypy
```

### import-linter

`import-linter` valida contratos de arquitectura entre capas para proteger la estructura hexagonal:

- `domain` no debe depender de capas externas
- `application` no debe depender de infraestructura o delivery
- `cli` y `tui` no deben acoplarse directamente a Jira/Xray

```bash
poetry run lint-imports
```

## Integración con VS Code

El repositorio incluye configuración en `.vscode/` para mejorar la experiencia en el editor:

- Ruff como formateador por defecto de Python
- formato al guardar
- `fix` y organización de imports al guardar
- integración de `mypy` con el entorno del proyecto
- compatibilidad con extensiones como Error Lens a través del panel de diagnósticos

> Importante: `mypy` e `import-linter` no formatean código. El formateo automático al guardar lo hace Ruff.

## Flujo recomendado

Para cambios locales antes de abrir un PR:

```bash
poetry run ruff format pyjx2 tests
poetry run ruff check pyjx2 tests
poetry run mypy
poetry run lint-imports
poetry run pytest tests -q
```
