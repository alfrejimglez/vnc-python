#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import io
import os
import signal
import socket
import subprocess
import sys
import time
import webbrowser
import zipfile
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    print("Falta 'requests'. Ejecuta: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

try:
    from platformdirs import user_cache_dir
except ImportError:
    # Fallback simple si no está platformdirs
    def user_cache_dir(appname):
        return str(Path.home() / ".cache" / appname)


NOVNC_VERSION = "1.5.0"
NOVNC_RELEASE_ZIP = f"https://github.com/novnc/noVNC/archive/refs/tags/v{NOVNC_VERSION}.zip"
APP_CACHE_DIR = Path(user_cache_dir("vnc-novnc-launcher"))


def find_free_port(start=6080, end=65000):
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No se encontró un puerto libre entre 6080 y 65000.")


def ensure_novnc(version=NOVNC_VERSION):
    """
    Descarga y descomprime noVNC v{version} si no existe en caché.
    Devuelve la ruta al directorio que contiene vnc.html.
    """
    target_dir = APP_CACHE_DIR / f"noVNC-{version}"
    vnc_html = target_dir / "vnc.html"

    if vnc_html.exists():
        return target_dir

    target_dir.parent.mkdir(parents=True, exist_ok=True)

    print(f"Descargando noVNC v{version} ...")
    resp = requests.get(NOVNC_RELEASE_ZIP, stream=True, timeout=120)
    resp.raise_for_status()
    data = io.BytesIO(resp.content)

    print("Extrayendo noVNC ...")
    with zipfile.ZipFile(data) as zf:
        root_folder = None
        # El zip trae carpeta raíz noVNC-{version}
        for info in zf.infolist():
            if info.is_dir():
                if root_folder is None and info.filename.rstrip("/").endswith(f"noVNC-{version}"):
                    root_folder = info.filename.rstrip("/")
                continue
        if root_folder is None:
            # fallback si cambia el nombre
            for name in zf.namelist():
                if name.rstrip("/").endswith("vnc.html"):
                    root_folder = name.split("/")[0]
                    break

        # Extraemos sólo bajo target_dir
        for info in zf.infolist():
            if not info.filename.startswith(root_folder + "/"):
                continue
            rel = Path(info.filename).relative_to(root_folder)
            dest = target_dir / rel
            if info.is_dir():
                dest.mkdir(parents=True, exist_ok=True)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as src, open(dest, "wb") as dst:
                    dst.write(src.read())

    if not vnc_html.exists():
        raise RuntimeError("No se encontró vnc.html tras extraer noVNC.")
    return target_dir


def wait_for_port(host, port, timeout=10.0):
    start = time.time()
    while time.time() - start < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            try:
                s.connect((host, port))
                return True
            except OSError:
                time.sleep(0.2)
    return False


def launch_websockify(novnc_dir: Path, local_port: int, target_host: str, target_port: int, verbose: bool):
    """
    Lanza websockify sirviendo los estáticos de noVNC y proxy a host:port VNC.
    Requiere tener instalado 'websockify' (pip install websockify).
    """
    cmd = [
        sys.executable, "-m", "websockify",
        "--web", str(novnc_dir),
        str(local_port),
        f"{target_host}:{target_port}",
    ]
    if verbose:
        print("Ejecutando:", " ".join(cmd))

    # En Windows, CTRL+C no siempre envía SIGINT a procesos hijos; usamos creationflags si hace falta.
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

    proc = subprocess.Popen(
        cmd,
        stdout=None if verbose else subprocess.DEVNULL,
        stderr=None if verbose else subprocess.DEVNULL,
        creationflags=creationflags,
    )
    return proc


def build_novnc_url(local_port: int, password: Optional[str], extra_params: Optional[dict] = None):
    params = {
        "host": "127.0.0.1",
        "port": str(local_port),
        "path": "websockify",
        "autoconnect": "1",
        "reconnect": "1",
        "reconnect_delay": "1000",
        "resize": "scale",
        "view_only": "false",
    }
    if password:
        params["password"] = password
    if extra_params:
        params.update({k: str(v) for k, v in extra_params.items()})

    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"http://127.0.0.1:{local_port}/vnc.html?{query}"


def main():
    parser = argparse.ArgumentParser(
        description="Lanza un visor VNC profesional usando noVNC + websockify desde Python."
    )
    parser.add_argument("--host", required=True, help="Host o IP del servidor VNC (ej. 192.168.1.10)")
    parser.add_argument("--port", type=int, default=5900, help="Puerto VNC (por defecto 5900)")
    parser.add_argument("--password", help="Contraseña VNC (opcional, se pasa a la UI)")
    parser.add_argument("--local-port", type=int, default=0, help="Puerto local para servir noVNC (0 = automático)")
    parser.add_argument("--no-open", action="store_true", help="No abrir el navegador automáticamente")
    parser.add_argument("--verbose", action="store_true", help="Mostrar logs de websockify")
    args = parser.parse_args()

    try:
        novnc_dir = ensure_novnc(NOVNC_VERSION)
    except Exception as e:
        print(f"Error preparando noVNC: {e}", file=sys.stderr)
        sys.exit(2)

    local_port = args.local_port or find_free_port()
    print(f"Usando puerto local {local_port} para la UI y el proxy WebSocket.")
    proc = None

    def shutdown():
        if proc and proc.poll() is None:
            if os.name == "nt":
                # En Windows, enviar CTRL_BREAK no es trivial; usamos terminate.
                proc.terminate()
            else:
                proc.send_signal(signal.SIGINT)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    try:
        proc = launch_websockify(novnc_dir, local_port, args.host, args.port, args.verbose)
        if not wait_for_port("127.0.0.1", local_port, timeout=8.0):
            print("websockify no arrancó a tiempo o el puerto no está accesible.", file=sys.stderr)
            shutdown()
            sys.exit(3)

        url = build_novnc_url(local_port, args.password)
        print(f"URL de conexión: {url}")
        if not args.no_open:
            webbrowser.open(url)
            print("Abriendo el navegador...")

        print("Pulsa Ctrl+C para finalizar. Dejando el proxy/UI en marcha.")
        # Mantener vivo mientras el proceso hijo esté activo
        while proc.poll() is None:
            time.sleep(0.5)

        rc = proc.returncode
        if rc not in (0, None):
            print(f"websockify terminó con código {rc}", file=sys.stderr)
            sys.exit(rc)
    except KeyboardInterrupt:
        print("\nCerrando...")
    finally:
        shutdown()


if __name__ == "__main__":
    main()