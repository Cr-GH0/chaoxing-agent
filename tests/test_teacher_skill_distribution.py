from __future__ import annotations

import hashlib
import importlib.util
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_teacher_skill.py"
SKILL = ROOT / "skills" / "chaoxing-teacher" / "SKILL.md"
OPENAI_INTERFACE = ROOT / "skills" / "chaoxing-teacher" / "agents" / "openai.yaml"
PROTOCOL = ROOT / "skills" / "chaoxing-teacher" / "references" / "protocol.md"
PORTABLE_ROUTER = (
    ROOT
    / "skills"
    / "chaoxing-teacher"
    / "scripts"
    / "runtime"
    / "chaoxing_teacher_runtime"
    / "router.py"
)
PLUGIN_MANIFESTS = (
    ROOT / "skills" / "chaoxing-teacher" / ".codex-plugin" / "plugin.json",
    ROOT / "skills" / "chaoxing-teacher" / ".codebuddy-plugin" / "plugin.json",
)


def _load_builder():
    spec = importlib.util.spec_from_file_location("build_teacher_skill", BUILDER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_portable_runtime_snapshot_is_reproducible() -> None:
    builder = _load_builder()
    assert builder.sync_runtime(check=True) == []


def test_skill_frontmatter_stays_portable_and_trigger_first() -> None:
    skill_text = SKILL.read_text(encoding="utf-8")
    frontmatter = skill_text.split("---", 2)[1].strip().splitlines()
    fields = dict(line.split(":", 1) for line in frontmatter)

    assert set(fields) == {"name", "description", "allowed-tools"}
    assert fields["name"].strip() == "chaoxing-teacher"
    assert fields["allowed-tools"].strip() == "PowerShell(*chaoxing-teacher*scripts*run.ps1*)"
    description = fields["description"].strip()
    assert len(description) <= 250
    assert "教师" in description
    assert "学习通" in description


def test_host_adapter_versions_match_the_distribution_version() -> None:
    builder = _load_builder()
    assert {
        json.loads(path.read_text(encoding="utf-8"))["version"] for path in PLUGIN_MANIFESTS
    } == {builder._project_version()}


def test_openai_interface_asks_for_plaintext_account_then_password_in_chat() -> None:
    interface = OPENAI_INTERFACE.read_text(encoding="utf-8")
    assert "请输入学习通账号。" in interface
    assert "请输入学习通密码。" in interface
    assert "把两项明文传给登录命令" in interface
    assert "系统登录框" not in interface


def test_all_portable_login_guidance_uses_the_plaintext_chat_flow() -> None:
    skill = SKILL.read_text(encoding="utf-8")
    protocol = PROTOCOL.read_text(encoding="utf-8")
    router = PORTABLE_ROUTER.read_text(encoding="utf-8")

    for text in (skill, protocol, router):
        assert "请输入学习通账号。" in text
        assert "请输入学习通密码。" in text
        assert "login-dialog" not in text
        assert "系统登录框" not in text
        assert "不在对话中索要密码" not in text
    assert "login '--username=" in skill
    assert "login '--username=" in protocol


def _fake_python_runtime(path: Path) -> str:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("LICENSE.txt", "PSF test fixture")
        archive.writestr("python.exe", b"MZ test fixture")
        archive.writestr("python313.dll", b"test fixture")
        archive.writestr("python313.zip", b"test fixture")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_distribution_packages_have_clean_host_compatible_layouts(tmp_path) -> None:
    builder = _load_builder()
    runtime_archive = tmp_path / "python-embed.zip"
    runtime_sha256 = _fake_python_runtime(runtime_archive)
    for stale_name in (
        "学习通教师版-0.1.0.zip",
        "学习通教师版-0.1.0-通用Skill.zip",
        "学习通教师版-0.1.0-WorkBuddy.zip",
        "学习通教师版-0.1.0-ZCode插件.zip",
    ):
        (tmp_path / stale_name).write_bytes(b"stale")
    (package,) = builder.build_packages(
        tmp_path,
        python_runtime_archive=runtime_archive,
        expected_runtime_sha256=runtime_sha256,
    )

    assert not list(tmp_path.glob("学习通教师版-0.1.0-*.zip"))

    assert package.name == f"学习通教师版-{builder._project_version()}.zip"

    with zipfile.ZipFile(package) as archive:
        names = set(archive.namelist())
        assert "chaoxing-teacher/SKILL.md" in names
        assert "chaoxing-teacher/scripts/chaoxing_teacher.py" in names
        assert "chaoxing-teacher/.codex-plugin/plugin.json" in names
        assert "chaoxing-teacher/.codebuddy-plugin/plugin.json" in names
        assert "chaoxing-teacher/hooks/hooks.json" in names
        assert "chaoxing-teacher/scripts/workbuddy_permission_hook.mjs" in names
        hook_runner = archive.getinfo("chaoxing-teacher/bin/run-node")
        assert (hook_runner.external_attr >> 16) & 0o111
        wrapper = archive.read("chaoxing-teacher/scripts/run.ps1").decode("utf-8")
        assert "@args" in wrapper
        assert "chaoxing-teacher/scripts/run.cmd" not in names
        assert (
            "chaoxing-teacher/scripts/runtime/chaoxing_teacher_runtime/windows_credentials.py"
        ) not in names
        assert "chaoxing-teacher/scripts/runtime/python-win-x64/python.exe" in names
        assert "chaoxing-teacher/scripts/runtime/python-win-x64/SOURCE.json" in names
        lowered = [name.casefold() for name in archive.namelist()]
        assert not any("__pycache__" in name for name in lowered)
        assert not any(name.endswith("mcp_server.py") for name in lowered)
        assert not any(name.endswith("cookies.json") for name in lowered)
        assert not any(name.endswith("confirmations.json") for name in lowered)
        assert not any(name.endswith("state.json") for name in lowered)
