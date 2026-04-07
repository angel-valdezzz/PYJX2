# Terminal User Interface (TUI)

Para aquellos equipos de testing o manuales que no prefieren operar estrictamente por comando interactivo puro, PYJX2 cuenta con una interfaz gráfica basada en terminal que puede ser invocada escribiendo en plano:

```bash
pyjx2 tui
```

Tu terminal se repintará a modo envolvente con bloques, cajas y flujos interactivos para llenar (empleando tu ratón o las secuencias TAB e Intro en el teclado).

## Pestañas de Funcionamiento:

Se encuentran listadas en el borde superior o intercambiables usando la fila F1-F4.

1. **Setup (F1)**
   Alberga los inputs necesarios con ejemplos para que pegues el Test Plan sin cometer errores de tipeo e inicies el Setup. Al lado inferior derecho, tendrás la caja de Logs.
2. **Sync (F2)**
   Cuenta con los menús drop-down seleccionables para el estatus de las pruebas además de casillas para desactivar el rastreo dinámico recursivo o encenderlo con un checkmark visual.
3. **Config (F3)**
   Un manual in-situ a la mano con los recordatorios base de que componentes ir y colocar en el archivo TOML y cómo está dispuesta la jerarquía local.
4. **Security (F4)**
   Un útil sandbox del entorno del cifrado AES que permite pegar la frase plana del password y mediante los botones convertirla al String asimilable en el JSON/TOML, o viceversa, usar la misma pantalla para extraer visualmente a nivel humano un token cifrado ajeno.
