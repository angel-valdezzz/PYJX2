# Interfaz Gráfica (TUI)

PYJX2 cuenta con una interfaz gráfica basada en terminal (Terminal User Interface) diseñada para facilitar la operación sin necesidad de recordar comandos complejos. Se invoca con:

```bash
pyjx2 tui
```

## Navegación y Uso
- **Pestañas (F1 - F4)**: Cambia entre las diferentes herramientas de la aplicación.
- **Autenticación Global**: El panel superior de credenciales es compartido por todas las herramientas.
- **Teclado**: Usa `TAB` y `Shift+TAB` para navegar entre campos, y `Enter` o `Espacio` para activar botones.
- **Ratón**: Soporta clics directos sobre botones y campos de entrada.

---

## Panel Global: Autenticación
Ubicado en la parte superior de la interfaz, este panel centraliza el acceso a Jira y Xray.

- **Entorno**: Cambia entre `QA` y `DEV`.
- **Usuario**: Tu correo o username de Jira.
- **Contraseña**: Soporta texto plano o tokens cifrados `ENC:...`.

Una vez ingresados, estos datos son utilizados automáticamente por los flujos de Preparación y Sincronización.

---

## Pestaña F1: Preparación (Setup)
Esta pestaña permite configurar la jerarquía de ejecución en Jira de forma visual.

**Proceso de Uso:**
- Ingresa la **Llave del Test Plan**.
- Define un **Título para la Ejecución**.
- Selecciona la **Aplicación** (ej. AXA_WEB).
- Elige el **Modo de Test** (`clone` para replicar o `add` para añadir).
- Haz clic en **Ejecutar**. Verás el progreso en tiempo real mediante la **barra de progreso** y la bitácora inferior.

---

## Pestaña F2: Sincronización (Sync)
Ideal para subir evidencias masivas desde tu computadora a Jira de forma automatizada.

**Proceso de Uso:**
- Pega la **Llave de la Ejecución** (Test Execution).
- Selecciona la **Carpeta local** de evidencias.
- Define el **Estado por defecto** y las opciones de escaneo.
- Presiona **Ejecutar**. La interfaz mostrará el % de avance en la **barra de progreso**.

---

<!--
## Pestaña F3: Configuración (Config) ⚠️
> [!NOTE]
> Esta pestaña se encuentra **deshabilitada** temporalmente en esta versión, ya que el manejo de credenciales se trasladó al panel global superior para mayor agilidad.
-->

---

## Pestaña F4: Seguridad (Security)
Herramientas para la gestión de tokens y contraseñas seguras.

**Utilidad:**
- **Encriptar**: Genera el string `ENC:...` para tus archivos de configuración.
- **Desencriptar**: Valida el contenido de un token cifrado.

---

## Ayuda y Documentación
En la parte inferior de la TUI encontrarás el botón **📖 Visualizar Documentación (MkDocs)**. Al pulsarlo, se lanzará automáticamente este manual en tu navegador Chrome para consulta inmediata.
