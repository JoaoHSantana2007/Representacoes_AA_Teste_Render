import os
import socket
import sys
import threading
import webbrowser

from streamlit.web import cli as stcli


def resource_path(relative_path: str) -> str:
    """Resolve paths for both source execution and PyInstaller onefile."""
    if getattr(sys, "frozen", False):
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)


def open_browser_delayed(url: str, delay_seconds: float = 1.5) -> None:
    """Open default browser shortly after server startup begins."""
    timer = threading.Timer(delay_seconds, lambda: webbrowser.open(url))
    timer.daemon = True
    timer.start()


def find_free_port(host: str = "127.0.0.1", start_port: int = 8501, attempts: int = 20) -> int:
    """Find an available local TCP port, starting from the preferred one."""
    for port in range(start_port, start_port + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
                return port
            except OSError:
                continue
    raise RuntimeError("Nao foi possivel encontrar uma porta livre para iniciar o Streamlit.")


def run_streamlit() -> None:
    base_path = resource_path("")
    app_path = resource_path("app.py")
    server_port = find_free_port()
    server_url = f"http://127.0.0.1:{server_port}"

    if base_path and base_path not in sys.path:
        sys.path.insert(0, base_path)

    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
    os.environ.setdefault("BROWSER", "none")

    open_browser_delayed(server_url)

    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--server.headless=true",
        "--server.address=127.0.0.1",
        f"--server.port={server_port}",
        "--global.developmentMode=false",
    ]
    stcli.main()


def main() -> None:
    run_streamlit()


if __name__ == "__main__":
    main()
