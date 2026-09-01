from __future__ import annotations

import ast
import tomllib
from pathlib import Path

from chaoxing_agent.capabilities import IMPLEMENTED_ACTIONS, OBSERVED_ACTIONS

ROOT = Path(__file__).resolve().parents[1]


def test_runtime_dependencies_do_not_include_browser_automation() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    dependencies = {
        str(item).split("[")[0].split("=")[0].split("<")[0].lower()
        for item in project["dependencies"]
    }
    forbidden = {
        "selenium",
        "playwright",
        "pyppeteer",
        "webdriver-manager",
        "undetected-chromedriver",
    }
    assert dependencies.isdisjoint(forbidden)


def test_repository_ignores_local_sessions_and_runtime_state() -> None:
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".chaoxing-agent/" in ignore
    assert "*cookies*.json" in ignore
    assert ".env" in ignore
    assert "storage-state.json" in ignore
    assert "artifacts/" in ignore


def test_documented_capability_counts_match_the_catalog() -> None:
    implemented = len(IMPLEMENTED_ACTIONS)
    observed = len(OBSERVED_ACTIONS)
    live_verified = sum(action.live_verified for action in IMPLEMENTED_ACTIONS)
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    capability_map = (ROOT / "docs" / "capability-map.md").read_text(encoding="utf-8")
    assert f"{implemented} 个已实现动作" in readme
    assert f"| `implemented` | {implemented} |" in capability_map
    assert f"| `live_verified` | {live_verified} |" in capability_map
    assert f"| `observed` surface marker | {observed} |" in capability_map


def test_every_platform_action_has_a_direct_natural_language_route() -> None:
    tree = ast.parse((ROOT / "src" / "chaoxing_agent" / "router.py").read_text(encoding="utf-8"))
    route_literals = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    platform_actions = {
        action.name
        for action in IMPLEMENTED_ACTIONS
        if action.name not in {"command.plan", "command.execute"}
    }
    assert platform_actions <= route_literals
