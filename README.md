# VNC noVNC Launcher (Python)

Lanza una interfaz gráfica en tu navegador para conectarte por VNC usando `noVNC` y `websockify`, todo orquestado desde Python.

Características:
- Descarga automática de noVNC (cacheado en `~/.cache/vnc-novnc-launcher`).
- Proxy WebSocket con `websockify` hacia tu servidor VNC.
- UI moderna con autoconexión, reconexión y escalado.
- Compatible con Windows, macOS y Linux.
- Funcionamiento “sin autenticación” desde el lanzador: no se pasa la contraseña por CLI; si tu servidor VNC requiere contraseña, la introducirás en la UI de noVNC.

Aviso de seguridad:
- Este flujo es “inseguro” a propósito (sin TLS). El tráfico va en claro entre websockify y el servidor VNC objetivo, y el navegador se conecta por `http://`. Úsalo sólo en redes de confianza.

## Requisitos

- Python 3.10+ (por el uso de anotaciones como `dict | None`)
- Dependencias Python:
  ```
  pip install -r requirements.txt
  ```

## Uso

Ejemplos:

- Conexión básica (parámetros por CLI):
  ```
  python vnc_novnc_launcher.py --host 192.168.1.50 --port 5900
  ```

- Sin `--host` (te preguntará de forma interactiva):
  ```
  python vnc_novnc_launcher.py
  ```
  Introduce el host/IP cuando lo solicite.

- No abrir el navegador automáticamente:
  ```
  python vnc_novnc_launcher.py --host 192.168.1.50 --no-open
  ```
  En ese caso, copia/pega la URL que imprime el programa.

- Puerto local fijo:
  ```
  python vnc_novnc_launcher.py --host 192.168.1.50 --local-port 6080
  ```

### Apertura del navegador

- Windows: el script intenta abrir Firefox en `C:\Program Files\Mozilla Firefox\firefox.exe`.
  Si no existe esa ruta o usas otro navegador, edita la variable `firefox_path` en el script o ejecuta con `--no-open` y abre la URL manualmente.

- macOS/Linux: edita el script para usar tu navegador o ejecuta con `--no-open` y abre manualmente la URL mostrada.

## Cómo funciona

- El script descarga `noVNC v1.5.0` de GitHub si no lo tienes y lo descomprime en tu caché local.
- Lanza `websockify` sirviendo los estáticos de noVNC y creando un proxy WebSocket hacia tu servidor VNC (`host:port`).
- Abre (opcionalmente) el navegador en `http://127.0.0.1:<puerto>/vnc.html?...` con parámetros para autoconexión y reconexión.
- Si el servidor VNC requiere contraseña, introdúcela en la UI de noVNC.

## Problemas comunes

- “websockify no se encuentra”:
  Asegúrate de haber instalado `websockify` con `pip install -r requirements.txt`.

- El visor se queda en “Connecting...”:
  - Verifica IP/puerto destino.
  - Comprueba si hay firewall/antivirus bloqueando el puerto VNC o el puerto local (por defecto 6080).
  - Prueba con `--verbose` para ver logs de websockify.

- No se abre el navegador:
  - Windows: revisa que `firefox_path` apunte a tu instalación de Firefox o usa `--no-open`.
  - macOS/Linux: usa `--no-open` y abre la URL manualmente, o adapta el script a tu navegador.

## Mejoras posibles

- Detección automática de sistema operativo y navegador predeterminado.
- Parámetro de contraseña opcional (si se desea) y otras opciones de conexión.
- Soporte TLS (wss://) con certificados locales.
- Empaquetado como binario con PyInstaller.
- GUI nativa con PySide6 que embeba la UI (QWebEngineView).