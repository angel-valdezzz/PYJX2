# Seguridad y Cifrado Simétrico 🔒

PYJX2 se construyó en torno a principios de seguridad y privacidad a lo largo de su arquitectura para asegurar que, sin importar bajo qué contexto operes, tus credenciales de Atlassian Jira no corran alto riesgo dentro de entornos compartidos de repositorio debido a la inadvertencia en archivos `.toml`.

## El Algoritmo 

Hemos provisto capacidades de control empleando la capa **Advanced Encryption Standard (AES) - 128 bit**, concretadas de forma estricta tras la interface **Fernet** nativa gracias a la librería local `cryptography`. Todo recae en un sistema de cifrado simétrico que bloquea miradas curiosas. Durante el ciclo de vida, esta información es ofuscada o inyectada just-in-time bajo demanda sin almacenar nunca transitorios libres en memoria.

## Comandos Interactivos (CLI)

Jamás coloques tus credenciales sin encriptación. Usa los subcomandos especializados adjuntos a la categoría `config` para resguardar tus keys:

### Encriptar credencial en texto plano
```bash
pyjx2 config encrypt-pass TU_PASSWORD_LIGERO_Y_REAL_AQUI
```
El Output emitido será semánticamente similar a `ENC:yXv5xT2_FqD6sYAAK`. Esta string (con la pre-adición `ENC:`) deberá ser pegada idéntica internamente en tu `pyjx2.toml`, o exportada bajo tu clave global de entorno `PYJX2_JIRA_PASSWORD`. ¡La interfaz TUI o CLI lo leerá internamente y se encargará del resto!

### Desencriptar la credencial (Auditoría)
Si olvidaste cuál clave encriptaste para ese proyecto, siempre puedes usar una función inversa para leer temporalmente qué dice. (Ideal para procesos correctivos o comprobaciones).
```bash
pyjx2 config decrypt-pass "ENC:yXv5xT2_FqD6sYAAK..."
```
Esto arrojará temporalmente la revelación textual de vuelta a tu terminal segura.

## Uso en Scripts

PYJX2 habilita la función como métodos estandarizados para que los reuses internamente o construyas tus propios pipelines:

```python
from pyjx2.api.client import PyJX2

# El token regresado por esto guardalo e inyéctalo donde quieras
token = PyJX2.encrypt_password("MypasswordSecret") 
# ENC:...
```
