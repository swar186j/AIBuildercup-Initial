"""Windows-compatible local release regression with owned production-style servers."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / os.environ.get("MAADHYAM_RELEASE_QA_OUTPUT", "qa/evidence/m11-local")
OUT.mkdir(parents=True, exist_ok=True)
API = ROOT / "Maadhyam/apps/api"
WEB = ROOT / "Maadhyam/apps/web"


def port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def main():
    api_port, web_port = port(), port()
    env = {**os.environ, "MAADHYAM_GEMINI_API_KEY": "", "MAADHYAM_GEMINI_VERTEXAI": "false",
           "MAADHYAM_PRODUCTION": "false", "PYTHONUNBUFFERED": "1",
           "MAADHYAM_TEST_API": f"http://127.0.0.1:{api_port}",
           "MAADHYAM_TEST_WEB": f"http://127.0.0.1:{web_port}",
           "MAADHYAM_QA_EVIDENCE": str(OUT / "screenshots")}
    owned = []
    try:
        for name, args, cwd in [
            ("api", [sys.executable, "-m", "uvicorn", "maadhyam_api.main:app", "--host", "127.0.0.1", "--port", str(api_port)], API),
            ("web", ["node", "node_modules/vite/bin/vite.js", "preview", "--host", "127.0.0.1", "--port", str(web_port), "--strictPort"], WEB),
        ]:
            log = (OUT / f"{name}.log").open("w")
            proc = subprocess.Popen(args, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT,
                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            owned.append((proc, log))
        for url in [env["MAADHYAM_TEST_API"] + "/api/health", env["MAADHYAM_TEST_WEB"]]:
            deadline = time.monotonic() + 40
            while True:
                try:
                    with urllib.request.urlopen(url, timeout=2) as response:
                        assert response.status == 200
                    break
                except OSError:
                    if time.monotonic() > deadline:
                        raise RuntimeError(f"Server failed readiness: {url}")
                    time.sleep(0.2)
        print("Production-style API and built frontend ready", flush=True)
        with (OUT / "tests.log").open("w") as log:
            selection = sys.argv[1:] or ["qa/test_http.py", "qa/test_browser.py", "qa/test_completion.py", "qa/test_final_journeys.py"]
            result = subprocess.run([sys.executable, "-m", "pytest", *selection, "-q", "--tb=short",
                                     f"--junitxml={OUT / 'tests.xml'}"], cwd=ROOT, env=env,
                                    stdout=log, stderr=subprocess.STDOUT)
        print(f"Local regression exit: {result.returncode}; evidence: {OUT}", flush=True)
        return result.returncode
    finally:
        for proc, log in reversed(owned):
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
            log.close()


if __name__ == "__main__":
    sys.exit(main())
