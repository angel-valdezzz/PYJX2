# Interfaz Gráfica (TUI)

!!! abstract "Descripción"
    La Interfaz Textual (TUI) de PyJX2 ofrece una experiencia visual y asistida directamente en la terminal, eliminando la necesidad de recordar argumentos complejos de CLI.

## Navegación y Uso

!!! info "Atajos Globales"
    - **Pestañas (F1 - F4)**: Cambia entre las diferentes herramientas.
    - **Navegación**: Usa `TAB` / `Shift+TAB` para moverte entre campos.
    - **Acción**: `Enter` o `Espacio` para activar botones.
    - **Ratón**: Soporte completo para clics directos.

---

## Panel Global: Autenticación

!!! note "Propósito"
    Ubicado en la parte superior, centraliza el acceso a Jira y Xray para evitar redundancia de datos.

- **Entorno**: Selección rápida entre `QA` y `DEV`.
- **Credenciales**: Usuario y Token (soporta `ENC:...`).

---

## Pestaña F1: Preparación (Setup)

!!! tip "Uso Visual"
    Permite configurar la jerarquía de ejecución en Jira de forma visual. Los campos se validan en tiempo real.

**Proceso:**
1. Ingresa la **Llave del Test Plan**.
2. Define el **Título** y la **Aplicación**.
3. Selecciona el **Modo** (`clone` o `add`).
4. Presiona **Ejecutar**. La TUI mostrará una **barra de progreso** y bitácora detallada.

---

## Pestaña F2: Sincronización (Sync)

!!! tip "Carga Masiva"
    Ideal para subir evidencias físicas desde carpetas locales de forma automatizada y sin errores.

**Proceso:**
1. Define la **Llave de Ejecución**.
2. Selecciona la **Carpeta local** de evidencias.
3. Configura el **Estado** y opciones de escaneo.
4. Presiona **Ejecutar**.

---

<!--
## Pestaña F3: Configuración (Config) ⚠️
... (contenido comentado)
-->

---

## Pestaña F4: Seguridad (Security)

!!! security "Gestión de Tokens"
    Herramientas para cifrar y descifrar credenciales de forma segura.

- **Encriptar**: Genera el string `ENC:...` para tus archivos de configuración.
- **Desencriptar**: Valida el contenido de un token cifrado.

---

!!! success "Ayuda Integrada"
    En la parte inferior de la TUI encontrarás el botón **📖 Visualizar Documentación**. Al pulsarlo, se lanzará automáticamente este manual en tu navegador Chrome.
