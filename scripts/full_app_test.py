from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class RunnerConfig:
    live: bool
    backend_host: str
    backend_port: int
    backend_start_timeout_seconds: float


class CommandRunner:
    def run(self, *, cmd: list[str], cwd: Path, env: Dict[str, str], name: str) -> None:
        print(f"\n==> {name}")
        print(f"cwd: {cwd}")
        print(f"cmd: {' '.join(cmd)}")
        subprocess.run(cmd, cwd=str(cwd), env=env, check=True)


class BackendServer:
    def __init__(self, *, cfg: RunnerConfig, repo_root: Path, env: Dict[str, str]):
        self._cfg = cfg
        self._repo_root = repo_root
        self._env = env
        self._proc: Optional[subprocess.Popen] = None
        self._log_path = repo_root / "scripts" / ".artifacts" / "full_app_test_backend.log"

    @property
    def base_url(self) -> str:
        return f"http://{self._cfg.backend_host}:{self._cfg.backend_port}"

    def start(self) -> None:
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        backend_dir = self._repo_root / "backend"
        python_exe = sys.executable

        cmd = [
            python_exe,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            self._cfg.backend_host,
            "--port",
            str(self._cfg.backend_port),
        ]

        print("\n==> Starting backend")
        print(f"cmd: {' '.join(cmd)}")
        print(f"log: {self._log_path}")

        log_fp = self._log_path.open("w", encoding="utf-8")

        creationflags = 0
        if os.name == "nt":
            creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

        self._proc = subprocess.Popen(
            cmd,
            cwd=str(backend_dir),
            env=self._env,
            stdout=log_fp,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
        )

    def wait_ready(self) -> None:
        deadline = time.time() + self._cfg.backend_start_timeout_seconds
        url = f"{self.base_url}/health"
        last_err: Optional[str] = None

        while time.time() < deadline:
            if self._proc and self._proc.poll() is not None:
                raise RuntimeError(
                    f"Backend exited early with code {self._proc.returncode}. See log: {self._log_path}"
                )
            try:
                with urllib.request.urlopen(url, timeout=2) as resp:
                    if resp.status == 200:
                        return
            except Exception as exc:  # noqa: BLE001
                last_err = str(exc)
                time.sleep(0.5)

        raise TimeoutError(f"Backend did not become healthy at {url}. Last error: {last_err}. Log: {self._log_path}")

    def stop(self) -> None:
        if not self._proc:
            return

        print("\n==> Stopping backend")
        try:
            if os.name == "nt":
                # Best-effort: send CTRL+BREAK to process group.
                self._proc.send_signal(getattr(signal, "CTRL_BREAK_EVENT", signal.SIGTERM))
            else:
                self._proc.terminate()
        except Exception:  # noqa: BLE001
            pass

        try:
            self._proc.wait(timeout=8)
        except Exception:  # noqa: BLE001
            try:
                self._proc.kill()
            except Exception:  # noqa: BLE001
                pass
            try:
                self._proc.wait(timeout=5)
            except Exception:  # noqa: BLE001
                pass


class ApiSmokeTester:
    def __init__(self, base_url: str):
        self._base_url = base_url.rstrip("/")

    def run(self) -> None:
        print("\n==> API smoke tests")
        token = self._register_and_get_token()
        self._smoke_parlay_suggest(token)
        self._smoke_parlay_triple(token)
        self._smoke_analysis_list_and_detail()

    def _request_json(
        self,
        *,
        method: str,
        path: str,
        body: Optional[dict] = None,
        headers: Optional[dict] = None,
        timeout_seconds: float = 30.0,
    ) -> Tuple[int, dict]:
        url = f"{self._base_url}{path}"
        data = None
        req_headers = {"Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)
        if body is not None:
            data = json.dumps(body).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                payload = resp.read().decode("utf-8")
                return resp.status, json.loads(payload) if payload else {}
        except urllib.error.HTTPError as exc:
            payload = exc.read().decode("utf-8") if exc.fp else ""
            raise RuntimeError(f"{method} {path} -> HTTP {exc.code}: {payload[:500]}") from exc

    def _register_and_get_token(self) -> str:
        email = f"smoke-{int(time.time())}@example.com"
        password = "Passw0rd!"

        status, payload = self._request_json(
            method="POST",
            path="/api/auth/register",
            body={"email": email, "password": password},
            timeout_seconds=15.0,
        )
        if status != 200 or "access_token" not in payload:
            raise RuntimeError(f"Register did not return access_token. status={status} payload={payload}")
        return str(payload["access_token"])

    def _smoke_parlay_suggest(self, token: str) -> None:
        status, payload = self._request_json(
            method="POST",
            path="/api/parlay/suggest",
            body={"num_legs": 3, "risk_profile": "balanced", "sports": ["NFL"]},
            headers={"Authorization": f"Bearer {token}"},
            timeout_seconds=60.0,
        )
        if status != 200 or not isinstance(payload.get("legs"), list):
            raise RuntimeError(f"/api/parlay/suggest unexpected payload: {payload}")

    def _smoke_parlay_triple(self, token: str) -> None:
        status, payload = self._request_json(
            method="POST",
            path="/api/parlay/suggest/triple",
            body={"sports": ["NFL"]},
            headers={"Authorization": f"Bearer {token}"},
            timeout_seconds=90.0,
        )
        if status != 200 or not isinstance(payload, dict):
            raise RuntimeError(f"/api/parlay/suggest/triple unexpected payload: {payload}")
        for key in ("safe", "balanced", "degen"):
            if key not in payload:
                raise RuntimeError(f"/api/parlay/suggest/triple missing '{key}' block")

    def _smoke_analysis_list_and_detail(self) -> None:
        status, payload = self._request_json(
            method="GET",
            path="/api/analysis/nfl/upcoming?limit=5",
            timeout_seconds=30.0,
        )
        if status != 200 or not isinstance(payload, list):
            raise RuntimeError(f"/api/analysis/nfl/upcoming unexpected payload: {payload}")

        if not payload:
            # Not an error: empty DB during local dev.
            return

        first = payload[0] if isinstance(payload[0], dict) else {}
        slug = str(first.get("slug") or "")
        if not slug:
            return

        slug_param = slug
        prefix = "nfl/"
        if slug.lower().startswith(prefix):
            slug_param = slug[len(prefix) :]

        _status, detail = self._request_json(
            method="GET",
            path=f"/api/analysis/nfl/{slug_param}",
            timeout_seconds=30.0,
        )
        if not isinstance(detail, dict) or "analysis_content" not in detail:
            raise RuntimeError(f"/api/analysis/nfl/{{slug}} unexpected payload: {detail}")


def _is_port_free(host: str, port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            return True
    except OSError:
        return False


def _pick_backend_port(host: str) -> int:
    for port in (8000, 8001, 8002, 8003, 8004):
        if _is_port_free(host, port):
            return port
    # Fall back to ephemeral.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        return int(s.getsockname()[1])


def _npm_exe() -> str:
    return "npm.cmd" if os.name == "nt" else "npm"


def _build_env(*, base: Dict[str, str], overrides: Dict[str, str]) -> Dict[str, str]:
    env = dict(base)
    env.update(overrides)
    return env


def main() -> int:
    parser = argparse.ArgumentParser(description="Run backend+frontend full app test suite.")
    parser.add_argument("--live", action="store_true", help="Allow external API calls (OpenAI/ESPN/Weather).")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    backend_host = "127.0.0.1"
    backend_port = _pick_backend_port(backend_host)

    cfg = RunnerConfig(
        live=bool(args.live),
        backend_host=backend_host,
        backend_port=backend_port,
        backend_start_timeout_seconds=30.0,
    )

    common_env = dict(os.environ)

    offline_overrides = {
        # Offline-safe defaults: keep requests deterministic and fast.
        "PROBABILITY_EXTERNAL_FETCH_ENABLED": "false",
        "PROBABILITY_PREFETCH_ENABLED": "false",
        "OPENAI_ENABLED": "false",
        "ENABLE_BACKGROUND_JOBS": "false",
    }

    backend_env = _build_env(base=common_env, overrides={} if cfg.live else offline_overrides)
    backend = BackendServer(cfg=cfg, repo_root=repo_root, env=backend_env)

    runner = CommandRunner()
    try:
        backend.start()
        backend.wait_ready()
        print(f"Backend ready at {backend.base_url}")

        # Backend tests
        runner.run(
            cmd=[sys.executable, "-m", "pytest"],
            cwd=repo_root / "backend",
            env=backend_env,
            name="Backend pytest",
        )

        # API smoke tests
        ApiSmokeTester(backend.base_url).run()

        # Frontend build
        frontend_dir = repo_root / "frontend"
        runner.run(
            cmd=[_npm_exe(), "run", "build"],
            cwd=frontend_dir,
            env=common_env,
            name="Frontend build",
        )

        # Playwright e2e
        e2e_env = _build_env(
            base=common_env,
            overrides={
                "PG_BACKEND_URL": backend.base_url,
            },
        )
        runner.run(
            cmd=[_npm_exe(), "run", "test:e2e"],
            cwd=frontend_dir,
            env=e2e_env,
            name="Playwright e2e",
        )

        print("\n✅ Full app test suite passed.")
        return 0
    finally:
        backend.stop()


if __name__ == "__main__":
    raise SystemExit(main())




