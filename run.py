"""
run.py
------
Convenience launcher: starts both FastAPI backend and Streamlit frontend
as separate subprocess in the same terminal window using threads.

Usage:
    python run.py
"""

import subprocess
import sys
import os
import threading
import time

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.abspath(__file__))
ENV  = {**os.environ, "PYTHONPATH": ROOT}


def _stream(proc, prefix: str):
    """Stream subprocess stdout line-by-line with a prefix label."""
    for line in proc.stdout:
        print(f"[{prefix}] {line}", end="")


def start_backend():
    print("\033[96m[BACKEND] Starting FastAPI on http://localhost:8000\033[0m")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app",
         "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=ROOT, env=ENV,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    _stream(proc, "BACKEND")


def start_frontend():
    time.sleep(2)  # Let the backend boot first
    print("\033[95m[FRONTEND] Starting Streamlit on http://localhost:8501\033[0m")
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "frontend/app.py",
         "--server.port", "8501", "--server.headless", "false"],
        cwd=ROOT, env=ENV,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    _stream(proc, "FRONTEND")


if __name__ == "__main__":
    print("\033[92m" + "="*60)
    print("  🚀 CareerAI – Starting All Services")
    print("="*60 + "\033[0m")

    # Seed DB first
    print("[SETUP] Seeding database…")
    subprocess.run([sys.executable, "scripts/seed_db.py"], cwd=ROOT, env=ENV)

    t_be = threading.Thread(target=start_backend,  daemon=True)
    t_fe = threading.Thread(target=start_frontend, daemon=True)
    t_be.start()
    t_fe.start()

    try:
        t_be.join()
        t_fe.join()
    except KeyboardInterrupt:
        print("\n\033[91m[INFO] Shutting down…\033[0m")
