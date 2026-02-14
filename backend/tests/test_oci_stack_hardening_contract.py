"""Ops contract tests for OCI stability hardening.

These are static checks that ensure production infra files keep the guarantees we rely on:
- nginx answers /health on port 80 (even if upstream is restarting)
- api liveness is reachable on port 8000 (/healthz)
- deploy + systemd include post-start verification and fail-fast behavior
- watchdog units/scripts exist (self-heal)
"""

from __future__ import annotations

from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_service_block(compose_text: str, service_name: str) -> str:
    lines = compose_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == f"{service_name}:" and line.startswith("  ") and not line.startswith("    "):
            start = i
            break
    if start is None:
        raise AssertionError(f"service '{service_name}' not found in compose file")

    out = [lines[start]]
    for line in lines[start + 1 :]:
        # Next top-level service starts at exactly 2 spaces.
        if line.startswith("  ") and not line.startswith("    ") and line.rstrip().endswith(":"):
            break
        out.append(line)
    return "\n".join(out) + "\n"


class TestOciProdComposeContract:
    def test_nginx_service_has_port_80_and_healthcheck(self) -> None:
        root = _repo_root()
        compose_path = root / "docker-compose.prod.yml"
        text = _read_text(compose_path)

        nginx_block = _extract_service_block(text, "nginx")
        assert '"80:80"' in nginx_block or "'80:80'" in nginx_block or "80:80" in nginx_block
        assert "healthcheck:" in nginx_block
        assert "/health" in nginx_block

    def test_api_service_exposes_8000_and_has_healthcheck(self) -> None:
        root = _repo_root()
        compose_path = root / "docker-compose.prod.yml"
        text = _read_text(compose_path)

        api_block = _extract_service_block(text, "api")
        assert '"8000:8000"' in api_block or "'8000:8000'" in api_block or "8000:8000" in api_block
        assert "healthcheck:" in api_block
        assert "/healthz" in api_block


class TestNginxHealthEndpointContract:
    def test_nginx_health_route_exists_and_has_fallback(self) -> None:
        root = _repo_root()
        conf_path = root / "nginx" / "conf.d" / "default.conf"
        text = _read_text(conf_path)

        assert "location = /health" in text
        assert "return 200" in text
        assert '"source":"nginx"' in text


class TestSystemdAndDeployFailFastContract:
    def test_systemd_unit_has_post_start_checks_and_remove_orphans(self) -> None:
        root = _repo_root()
        unit_path = root / "docs" / "systemd" / "parlaygorilla.service"
        text = _read_text(unit_path)

        assert "--remove-orphans" in text
        assert "ExecStartPost" in text
        assert "restart nginx" in text
        assert "http://127.0.0.1/health" in text
        assert "http://127.0.0.1:8000/healthz" in text

    def test_deploy_script_verifies_nginx_api_and_readiness(self) -> None:
        root = _repo_root()
        deploy_path = root / "scripts" / "deploy.sh"
        text = _read_text(deploy_path)

        assert "Restarting nginx" in text or "restart nginx" in text
        assert "Verifying stack health" in text
        assert "http://127.0.0.1/health" in text
        assert "http://127.0.0.1:8000/healthz" in text
        assert "http://127.0.0.1:8000/readyz" in text


class TestWatchdogFilesExist:
    def test_watchdog_units_and_script_exist(self) -> None:
        root = _repo_root()
        assert (root / "scripts" / "health-watchdog.sh").is_file()
        assert (root / "docs" / "systemd" / "parlaygorilla-watchdog.service").is_file()
        assert (root / "docs" / "systemd" / "parlaygorilla-watchdog.timer").is_file()

    def test_watchdog_units_check_nginx_and_api(self) -> None:
        root = _repo_root()
        svc_text = _read_text(root / "docs" / "systemd" / "parlaygorilla-watchdog.service")
        assert "NGINX_HEALTH_URL=" in svc_text
        assert "API_HEALTH_URL=" in svc_text
        assert "FAIL_THRESHOLD=" in svc_text

        timer_text = _read_text(root / "docs" / "systemd" / "parlaygorilla-watchdog.timer")
        assert "OnUnitActiveSec=60s" in timer_text

