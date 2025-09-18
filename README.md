# VNC noVNC Launcher (Python)

Lanza una interfaz gráfica profesional en tu navegador para conectarte por VNC usando `noVNC` y `websockify`, todo orquestado desde Python.

Características:
- Descarga automática de noVNC (cacheado en `~/.cache/vnc-novnc-launcher`).
- Proxy WebSocket con `websockify` hacia tu servidor VNC.
- UI moderna con autoconexión, reconexión y escalado.
- Compatible con Windows, macOS y Linux.

Aviso de seguridad:
- Este flujo es "inseguro" a propósito (sin TLS), como solicitaste. El tráfico va en claro entre websockify y el servidor VNC objetivo, y el navegador se conecta por `http://`. Úsalo sólo en redes de confianza.

## Requisitos

- Python 3.9+
- Dependencias Python:
  ```
  pip install -r requirements.txt
  ```

## Uso

Ejemplos:

- Conexión básica:
  ```
  python vnc_novnc_launcher.py --host 192.168.1.50 --port 5900
  ```

- Con contraseña:
  ```
  python vnc_novnc_launcher.py --host 192.168.1.50 --port 5901 --password miSecreta
  ```

- No abrir el navegador automáticamente:
  ```
  python vnc_novnc_launcher.py --host 192.168.1.50 --no-open
  ```
  En ese caso, copia/pega la URL que imprime el programa.

- Puerto local fijo:
  ```
  python vnc_novnc_launcher.py --host 192.168.1.50 --local-port 6080
  ```

## Cómo funciona

- El script descarga `noVNC v1.5.0` de GitHub si no lo tienes y lo descomprime en tu cache local.
- Lanza `websockify` sirviendo los estáticos de noVNC y creando un proxy WebSocket hacia tu servidor VNC (`host:port`).
- Abre el navegador en `http://127.0.0.1:<puerto>/vnc.html?...` con parámetros para autoconexión y reconexión.

## Problemas comunes

- "websockify no se encuentra":
  Asegúrate de haber instalado `websockify` con `pip install -r requirements.txt`.

- El visor se queda en "Connecting...":
  - Verifica IP/puerto destino.
  - Comprueba si hay firewall/antivirus bloqueando el puerto VNC o el 6080 local.
  - Prueba con `--verbose` para ver logs de websockify.

- Contraseña incorrecta:
  Vuelve a ejecutar con `--password` correcto. También puedes usar el cuadro de contraseña en la UI si no la pasas por parámetro.

## Mejoras posibles

- Guardar conexiones favoritas (YAML/JSON).
- Soporte TLS (wss://) con certificados locales.
- Empaquetado como binario con PyInstaller.
- GUI nativa con PySide6 que embeba la UI (QWebEngineView).