def get_ascii_logo(file_path: str = None) -> str:
    """
    Renderea el ASCII art exacto delineado por el usuario final,
    respetando los márgenes, formas y antialiasing, pero inyectando
    los tintes institucionales correctos (Azul, Rojo y Blanco).
    """
    blue = "#4976BA" # Tono de azul un poco más brillante para que sobresalga en terminales oscuras
    red = "#D24723"
    white_text = "#ffffff"
    
    raw_ascii = [
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@**@",
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#**@@",
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@**@@@@",
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#*#@@@@@",
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@**@@@@@@@",
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@**#@@@@@@@@",
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@**@@@@@@@@@@",
        "@@@@@@@@@@@@@@@@@@@@@@@@@@**%@@@@@@@@@@@",
        "@@@@@@@@@@@@@@@@@@@@@@@@@**@@@@@@@@@@@@@",
        "@@@@@@@@@@@@@@@@@@@@@@@**@@@@@@@@@@@@@@@",
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
        "@@@@@@@@@    -@   @@#  @*    @@@@@@@@@@@",
        "@@@@@@@%  @   @*  .  %@  *   =@@@@@@@@@@",
        "@@@@@@  :@@+   @   .@+  @@@   @@@@@@@@@@",
        "@@@@%          -              .@@@@@@@@@",
        "@@@  #@@@@@@@   @%   @@@@@@@   @@@@@@@@@",
        "@+  @@@@@@@@:        *@@@@@@@   @@@@@@@@",
        "  %@@@@@@@@  @    @   @@@@@@@.   @@@@@@@",
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
    ]
    
    markup_lines = []
    
    for r_idx, line in enumerate(raw_ascii):
        line_markup = ""
        current_color = None
        segment = ""
        
        for char in line:
            # Lógica de iluminación:
            
            # En las primeras 10 líneas se distingue vívidamente la diagonal de slash rojo
            if r_idx < 10:
                if char == "@": c = blue
                elif char in ("*", "#", "%"): c = red
                else: c = white_text
            # En la base, domina el cuadro azul y las piezas de las letras huecas
            else:
                if char in ("@", "#", "%", "*"): c = blue
                else: c = white_text
                
            char_safe = char.replace('[', '\\[').replace(']', '\\]')
                
            if c != current_color:
                if segment:
                    line_markup += f"[{current_color}]{segment}[/]"
                segment = char_safe
                current_color = c
            else:
                segment += char_safe
                
        if segment:
            line_markup += f"[{current_color}]{segment}[/]"
            
        markup_lines.append(line_markup)
        
    return "\n".join(markup_lines)

