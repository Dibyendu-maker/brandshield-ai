import os
import signal
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def get_python_exe():
    venv_py = BASE_DIR / ".venv" / "Scripts" / "python.exe"
    if venv_py.exists():
        return str(venv_py)
    return sys.executable


def main():
    py_exe = get_python_exe()
    print("=" * 65)
    print("      BRANDSHIELD AI — ENTERPRISE BRAND GOVERNANCE PLATFORM")
    print("=" * 65)
    print(f"[BrandShield] Using Python runtime: {py_exe}")
    print("[BrandShield] Initializing database & seed records...")

    # Run database initialization
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BASE_DIR)

    init_proc = subprocess.run(
        [py_exe, "-m", "backend.database.init_db"], env=env, cwd=str(BASE_DIR)
    )
    if init_proc.returncode != 0:
        print("[BrandShield] Error initializing database.")

    # Start FastAPI Backend
    print("[BrandShield] Starting FastAPI Backend on http://127.0.0.1:8000 ...")
    backend_proc = subprocess.Popen(
        [
            py_exe,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ],
        env=env,
        cwd=str(BASE_DIR),
    )

    # Allow backend 1.5 seconds to bind
    time.sleep(1.5)

    # Start Streamlit Frontend
    print("[BrandShield] Starting Streamlit Frontend on http://localhost:8501 ...")
    streamlit_exe = BASE_DIR / ".venv" / "Scripts" / "streamlit.exe"
    if not streamlit_exe.exists():
        streamlit_cmd = [
            py_exe,
            "-m",
            "streamlit",
            "run",
            "frontend/app.py",
            "--server.port",
            "8501",
        ]
    else:
        streamlit_cmd = [
            str(streamlit_exe),
            "run",
            "frontend/app.py",
            "--server.port",
            "8501",
        ]

    frontend_proc = subprocess.Popen(streamlit_cmd, env=env, cwd=str(BASE_DIR))

    print("\n" + "=" * 65)
    print("🚀 BRANDSHIELD AI IS READY!")
    print("👉 Frontend UI:   http://localhost:8501")
    print("👉 Backend API:  http://127.0.0.1:8000")
    print("👉 Swagger Docs: http://127.0.0.1:8000/docs")
    print("=" * 65)
    print("Press Ctrl+C to terminate both servers.\n")

    def signal_handler(sig, frame):
        print("\n[BrandShield] Terminating servers...")
        frontend_proc.terminate()
        backend_proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        frontend_proc.wait()
    except KeyboardInterrupt:
        frontend_proc.terminate()
        backend_proc.terminate()


if __name__ == "__main__":
    main()
