from __future__ import annotations

from pathlib import Path

import re


REPO_ROOT = Path(__file__).resolve().parents[2]


def _extract_css_block_after_marker(css: str, marker: str) -> str:
    """
    Extract the first '{ ... }' block that starts at the first @media after `marker`.
    This is a lightweight brace matcher suitable for our globals.css structure.
    """
    marker_idx = css.find(marker)
    if marker_idx == -1:
        raise AssertionError(f"Marker not found in CSS: {marker!r}")

    media_idx = css.find("@media", marker_idx)
    if media_idx == -1:
        raise AssertionError("No @media block found after marker")

    brace_start = css.find("{", media_idx)
    if brace_start == -1:
        raise AssertionError("No opening '{' found for @media block")

    depth = 0
    for i in range(brace_start, len(css)):
        ch = css[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return css[brace_start + 1 : i]

    raise AssertionError("No matching closing '}' found for @media block")


def test_affiliates_cashflow_uses_neon_strong_class() -> None:
    hero = (
        REPO_ROOT
        / "frontend"
        / "components"
        / "affiliates"
        / "sections"
        / "AffiliateHeroSection.tsx"
    ).read_text(encoding="utf-8")
    assert 'className="text-neon-strong">cashflow.' in hero


def test_mobile_neon_reduction_is_scoped_to_age_gate_only() -> None:
    """
    Regression: we once applied an aggressive mobile brightness/saturation filter to
    `.text-neon-strong` globally, which made key neon text (e.g., "cashflow.") appear
    missing/dim on mobile. Ensure the aggressive reduction stays scoped to Age Gate.
    """
    css = (REPO_ROOT / "frontend" / "app" / "globals.css").read_text(encoding="utf-8")

    block = _extract_css_block_after_marker(
        css,
        "Reduce neon green intensity on mobile to prevent artifacts - aggressive reduction",
    )

    # Must be scoped within Age Gate
    assert "[data-age-gate] .text-neon-strong" in block
    assert "[data-age-gate] .glow-neon" in block
    assert '[data-age-gate] [style*="box-shadow"][style*="#00DD55"]' in block
    assert '[data-age-gate] [style*="drop-shadow"][style*="#00DD55"]' in block

    # Must NOT be applied globally within that @media block
    assert re.search(r"(?m)^\s*\.text-neon(-strong|-secondary|-highlight|-accent)?\b", block) is None
    assert re.search(r"(?m)^\s*\.glow-neon(-strong|-secondary|-highlight)?\b", block) is None


