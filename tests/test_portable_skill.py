import argparse
import asyncio
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "chaoxing-teacher"
RUNNER = SKILL / "scripts" / "chaoxing_teacher.py"
INTENT_CASES = json.loads(
    (ROOT / "tests" / "fixtures" / "teacher_intent_cases.json").read_text(encoding="utf-8")
)


def _load_runner():
    spec = importlib.util.spec_from_file_location("portable_chaoxing_teacher", RUNNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_portable_skill_has_standard_structure_and_no_connector_dependency() -> None:
    assert (SKILL / "SKILL.md").is_file()
    assert (SKILL / "agents" / "openai.yaml").is_file()
    assert RUNNER.is_file()
    assert (SKILL / "scripts" / "run.ps1").is_file()
    assert not (SKILL / "scripts" / "run.cmd").exists()
    assert (SKILL / "scripts" / "vendor" / "requests" / "__init__.py").is_file()
    assert (SKILL / "scripts" / "vendor" / "THIRD_PARTY.md").is_file()
    assert not (
        SKILL / "scripts" / "runtime" / "chaoxing_teacher_runtime" / "windows_credentials.py"
    ).exists()
    assert not (SKILL / "scripts" / "requirements.txt").exists()
    assert not (
        SKILL / "scripts" / "runtime" / "chaoxing_teacher_runtime" / "mcp_server.py"
    ).exists()

    inspected = [
        SKILL / "agents" / "openai.yaml",
        SKILL / "scripts" / "chaoxing_teacher.py",
    ]
    for path in inspected:
        assert "mcp" not in path.read_text(encoding="utf-8").casefold()


def test_bundled_dependencies_run_without_site_packages_or_install() -> None:
    completed = subprocess.run(
        [sys.executable, "-S", str(RUNNER), "catalog", "--query", "未批改作业"],
        check=False,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
    )
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["status"] == "ok"
    assert result["commands"][0]["execution"]["command_id"] == "homeworks"


def test_structured_intent_reads_utf8_json_from_stdin_on_windows() -> None:
    payload = {
        "request": "看看英语写作2班还有哪些作业没改",
        "domain": "homework",
        "operation": ["查看", "列出"],
        "keywords": ["未批改"],
        "entities": {"course": "英语写作", "clazz": "2班"},
        "values": {},
    }
    completed = subprocess.run(
        [sys.executable, "-S", str(RUNNER), "intent"],
        input=json.dumps(payload, ensure_ascii=False) + "\n",
        check=False,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
    )
    assert completed.returncode == 0, completed.stdout
    result = json.loads(completed.stdout)
    assert result["status"] == "candidates"
    assert result["intent"]["request"] == payload["request"]


def test_structured_intent_accepts_direct_json_argument() -> None:
    payload = {
        "request": "看看英语写作2班还有哪些作业没改",
        "domain": "homework",
        "operation": ["查看", "列出"],
        "keywords": ["未批改"],
        "entities": {"course": "英语写作", "clazz": "2班"},
        "values": {},
    }
    completed = subprocess.run(
        [
            sys.executable,
            "-S",
            str(RUNNER),
            "intent",
            f"--input-json={json.dumps(payload, ensure_ascii=False)}",
        ],
        check=False,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
    )
    assert completed.returncode == 0, completed.stdout
    result = json.loads(completed.stdout)
    assert result["status"] == "candidates"
    assert result["intent"]["request"] == payload["request"]


def test_workbuddy_hook_allows_only_direct_bundled_runner_calls() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is unavailable")
    hook = SKILL / "scripts" / "workbuddy_permission_hook.mjs"

    def decision(command: str) -> dict:
        completed = subprocess.run(
            [node, str(hook)],
            input=json.dumps(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "PowerShell",
                    "tool_input": {"command": command},
                }
            ),
            check=True,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=15,
        )
        return json.loads(completed.stdout)

    direct = (
        "& 'C:/Users/demo/.codebuddy/skills/chaoxing-teacher/scripts/run.ps1' "
        'action \'--input-json={"parameters":{"text":"a; b & c"}}\''
    )
    allowed = decision(direct)
    assert allowed["hookSpecificOutput"]["permissionDecision"] == "allow"
    unicode_argument = (
        "& 'C:/Users/demo/.codebuddy/skills/chaoxing-teacher/scripts/run.ps1' "
        "domains --query 帮我看看英语写作二班还有哪些作业没改"
    )
    assert decision(unicode_argument)["hookSpecificOutput"]["permissionDecision"] == "allow"
    assert decision(f"{direct}; Get-ChildItem") == {"continue": True}
    assert decision(f"{unicode_argument} | Get-ChildItem") == {"continue": True}
    assert decision(f"{unicode_argument} # hidden command") == {"continue": True}
    assert decision("& 'C:/tmp/other/scripts/run.ps1' session") == {"continue": True}


def test_running_installed_skill_does_not_write_bytecode_or_trigger_hot_reload(
    tmp_path,
) -> None:
    installed = tmp_path / "chaoxing-teacher"
    shutil.copytree(
        SKILL,
        installed,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(installed / "scripts" / "chaoxing_teacher.py"),
            "catalog",
            "--query",
            "查看未批改作业",
        ],
        check=False,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
    )

    assert completed.returncode == 0, completed.stderr
    assert not list(installed.rglob("__pycache__"))
    assert not list(installed.rglob("*.pyc"))


def test_runtime_snapshot_keeps_student_code_but_runner_blocks_student_entry() -> None:
    runner = _load_runner()
    bundled_capabilities = (
        SKILL / "scripts" / "runtime" / "chaoxing_teacher_runtime" / "capabilities.py"
    ).read_text(encoding="utf-8")
    source_capabilities = (ROOT / "src" / "chaoxing_agent" / "capabilities.py").read_text(
        encoding="utf-8"
    )
    assert "learning.course.homework.answer.enter" in bundled_capabilities
    assert "learning.course.homework.answer.enter" in source_capabilities
    assert runner._is_teacher_command("courses") is True
    assert runner._is_teacher_command("learning-courses") is False
    assert runner._is_teacher_action("homework.assignments.list") is True
    assert runner._is_teacher_action("learning.course.homeworks.list") is False


def test_default_runtime_state_is_not_inside_skill(monkeypatch) -> None:
    runner = _load_runner()
    data_dir = ROOT / ".test-user-data"
    monkeypatch.setenv("CHAOXING_TEACHER_DATA_DIR", str(data_dir))
    assert runner._default_data_dir() == data_dir.resolve()
    assert not runner._default_data_dir().is_relative_to(SKILL.resolve())


def test_runtime_state_falls_back_when_preferred_directory_is_not_writable(
    tmp_path, monkeypatch
) -> None:
    runner = _load_runner()
    preferred = tmp_path / "blocked"
    fallback = tmp_path / "fallback"
    monkeypatch.setattr(runner, "_data_dir_candidates", lambda: [preferred, fallback])

    def probe(path):
        if path == preferred:
            raise PermissionError("blocked by host sandbox")
        path.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(runner, "_probe_data_dir", probe)
    assert runner._writable_data_dir() == fallback


def test_stateless_catalog_does_not_create_runtime_state(tmp_path) -> None:
    runner = _load_runner()
    data_dir = tmp_path / "not-created"
    context = runner._load_runtime(data_dir)
    result = runner._catalog(context, "作业", 0, 10)
    assert result["status"] == "ok"
    assert not data_dir.exists()


def test_doctor_is_stateless_and_does_not_require_writable_storage(
    tmp_path, monkeypatch, capsys
) -> None:
    runner = _load_runner()
    data_dir = tmp_path / "read-only-host-state"
    monkeypatch.setenv("CHAOXING_TEACHER_DATA_DIR", str(data_dir))

    def reject_writable_storage():
        pytest.fail("doctor must not probe or lock writable runtime storage")

    monkeypatch.setattr(runner, "_writable_data_dir", reject_writable_storage)
    monkeypatch.setattr(
        tempfile,
        "gettempdir",
        lambda: pytest.fail("doctor must not probe for a usable temporary directory"),
    )

    assert runner.main(["doctor"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "ok"
    assert result["runtime"] == "bundled_http"
    assert result["dependencies"] == "bundled_offline"
    assert not data_dir.exists()


def test_catalog_excludes_student_and_control_commands() -> None:
    runner = _load_runner()
    runtime_root = SKILL / "scripts" / "runtime"
    import sys

    sys.path.insert(0, str(runtime_root))
    try:
        from chaoxing_teacher_runtime.capabilities import ACTION_CATALOG
        from chaoxing_teacher_runtime.cli import _run_action, build_parser

        context = {
            "cli_parser": build_parser(),
            "run_cli_action": _run_action,
            "action_catalog": ACTION_CATALOG,
        }
        result = runner._catalog(context, "", 0, 200)
        chinese_result = runner._catalog(context, "作业", 0, 200)
        _, choices = runner._subcommands(context["cli_parser"])
        hints = runner._command_action_hints(context)
    finally:
        sys.path.remove(str(runtime_root))
    commands = {item["execution"]["command_id"] for item in result["commands"]}
    assert "courses" in commands
    assert "learning-courses" not in commands
    assert "login" not in commands
    assert "run" not in commands
    assert chinese_result["matching"] > 0
    assert all(
        not item["execution"]["command_id"].startswith("learning-")
        for item in chinese_result["commands"]
    )
    assert all(item["name"] != "教师端操作" for item in chinese_result["commands"])
    assert (
        sorted(
            command
            for command in choices
            if runner._is_teacher_command(command) and not hints.get(command)
        )
        == []
    )


def test_login_passes_plaintext_credentials_exactly(tmp_path) -> None:
    runner = _load_runner()

    class FakeRuntime:
        def __init__(self) -> None:
            self.login_parameters = None

        async def execute(self, action, parameters=None, confirmation_token=None):
            if action == "session.login":
                self.login_parameters = dict(parameters)
                return {"status": "ok", "action": action, "result": {"logged_in": True}}
            assert action == "session.check"
            return {"status": "ok", "result": {"logged_in": True}}

    fake = FakeRuntime()
    payload = {
        "username": " teacher-account ",
        "password": " teacher-password ",
        "fid": "-1",
    }
    profile_id = runner._profile_id(payload["username"])
    result = asyncio.run(
        runner._login(
            {
                "runtime": fake,
                "data_dir": tmp_path,
                "profile_id": profile_id,
            },
            payload,
        )
    )

    assert fake.login_parameters == {
        "username": " teacher-account ",
        "password": " teacher-password ",
        "fid": "-1",
    }
    assert runner._active_profile_id(tmp_path) == profile_id
    assert result["account"]["username_hint"] == "***unt "


def test_login_command_accepts_plaintext_chat_values_as_arguments() -> None:
    runner = _load_runner()
    username = "教师 账号'\"$&中文"
    password = "--密 码'\"$&中文"
    args = runner._runner_parser().parse_args(
        [
            "login",
            f"--username={username}",
            f"--password={password}",
            "--fid=-1",
        ]
    )
    payload = runner._login_payload(args)

    assert payload == {
        "username": username,
        "password": password,
        "fid": "-1",
    }


def test_windows_runner_forwards_each_argument_without_reparsing() -> None:
    wrapper = (SKILL / "scripts" / "run.ps1").read_text(encoding="utf-8")

    assert "@args" in wrapper
    assert "%*" not in wrapper


def test_login_keeps_stdin_json_compatibility(monkeypatch) -> None:
    runner = _load_runner()
    expected = {"username": "teacher", "password": "password", "fid": "-1"}
    monkeypatch.setattr(runner, "_read_payload", lambda: expected)
    args = runner._runner_parser().parse_args(["login"])

    assert runner._login_payload(args) == expected


def test_logout_removes_only_active_account_state(tmp_path) -> None:
    runner = _load_runner()
    profile_id = runner._profile_id("teacher-account")
    profile = runner._profile_dir(tmp_path, profile_id)
    profile.mkdir(parents=True)
    for name in ("cookies.json", "confirmations.json", "state.json", "account.json"):
        (profile / name).write_text("{}", encoding="utf-8")
    runner._write_json_atomic(runner._active_profile_file(tmp_path), {"profile_id": profile_id})

    result = runner._logout(tmp_path, profile_id)

    assert result["logged_out"] is True
    assert not runner._active_profile_file(tmp_path).exists()
    assert not profile.exists()


def test_account_profiles_and_confirmation_summaries_are_isolated(tmp_path) -> None:
    runner = _load_runner()
    first = runner._profile_id("teacher-one")
    second = runner._profile_id("teacher-two")
    first_context = runner._load_runtime(tmp_path, first)
    second_context = runner._load_runtime(tmp_path, second)

    assert first_context["settings"].cookie_file != second_context["settings"].cookie_file
    first_context["account"] = {"account_name": "教师一"}
    result = runner._attach_account(
        {"status": "confirmation_required", "confirmation": {"summary": "发送课程通知"}},
        first_context,
    )
    assert result["confirmation"]["summary"] == "账号《教师一》：发送课程通知"


def test_verification_required_login_does_not_switch_active_account(tmp_path) -> None:
    runner = _load_runner()
    old_profile = runner._profile_id("old-account")
    runner._write_json_atomic(runner._active_profile_file(tmp_path), {"profile_id": old_profile})

    class VerificationRuntime:
        async def execute(self, action, parameters=None, confirmation_token=None):
            assert action == "session.login"
            return {
                "status": "verification_required",
                "verification": {"kind": "two_factor", "retry": "login"},
            }

    payload = {"username": "new-account", "password": "password", "fid": "-1"}
    result = asyncio.run(
        runner._login(
            {
                "runtime": VerificationRuntime(),
                "data_dir": tmp_path,
                "profile_id": runner._profile_id("new-account"),
            },
            payload,
        )
    )

    assert result["status"] == "verification_required"
    assert result["active_account_unchanged"] is True
    assert runner._active_profile_id(tmp_path) == old_profile
    assert payload["password"] == ""


def test_data_lock_rejects_concurrent_account_use(tmp_path) -> None:
    runner = _load_runner()
    with runner._data_lock(tmp_path):
        with pytest.raises(runner.RunnerBusy):
            with runner._data_lock(tmp_path, timeout_seconds=0.05):
                raise AssertionError("second lock unexpectedly succeeded")


def test_new_install_reports_login_required_without_cookie_error() -> None:
    runner = _load_runner()

    class Settings:
        cookie_file = ROOT / "definitely-missing-session" / "cookies.json"

    class NeverCalled:
        async def execute(self, *_args, **_kwargs):
            raise AssertionError("missing session should not enter the HTTP runtime")

    result = asyncio.run(runner._session({"settings": Settings(), "runtime": NeverCalled()}))
    assert result == {
        "status": "login_required",
        "action": "session.check",
        "result": {"logged_in": False, "reason": "no_saved_session"},
        "next_prompt": "请输入学习通账号。",
    }


def test_expired_saved_session_is_reported_as_login_required() -> None:
    runner = _load_runner()

    class Settings:
        cookie_file = ROOT / "pyproject.toml"

    class ExpiredRuntime:
        async def execute(self, action, *_args, **_kwargs):
            assert action == "session.check"
            return {
                "status": "ok",
                "action": action,
                "result": {"logged_in": False, "reason": "expired"},
            }

    result = asyncio.run(
        runner._session(
            {
                "settings": Settings(),
                "runtime": ExpiredRuntime(),
                "account": {"account_name": "教师一"},
            }
        )
    )

    assert result["status"] == "login_required"
    assert result["result"] == {"logged_in": False, "reason": "expired"}
    assert result["next_prompt"] == "请输入学习通账号。"
    assert result["account"] == {"account_name": "教师一"}


def test_authenticated_action_preflights_expired_session_without_dispatching() -> None:
    runner = _load_runner()

    class ExpiredRuntime:
        async def execute(self, action, *_args, **_kwargs):
            assert action == "session.check"
            return {"status": "ok", "result": {"logged_in": False}}

    result = asyncio.run(
        runner._execute_action(
            {"runtime": ExpiredRuntime(), "account": {}},
            {"action": "courses.list", "parameters": {}},
        )
    )

    assert result["status"] == "login_required"


def test_direct_action_rejects_student_and_control_actions() -> None:
    runner = _load_runner()

    class NeverCalled:
        async def execute(self, *_args, **_kwargs):
            raise AssertionError("blocked action reached runtime")

    for action in (
        "learning.course.exams.list",
        "command.execute",
        "session.check",
        "session.login",
    ):
        result = asyncio.run(
            runner._execute_action({"runtime": NeverCalled()}, {"action": action, "parameters": {}})
        )
        assert result["status"] == "out_of_scope"


def test_direct_action_rejects_catalog_unknown_and_observed_actions_before_login() -> None:
    runner = _load_runner()
    context = runner._load_runtime(ROOT)

    class NeverCalled:
        async def execute(self, *_args, **_kwargs):
            raise AssertionError("catalog boundary should run before session or HTTP access")

    guarded_context = {**context, "runtime": NeverCalled()}
    observed = next(
        item
        for item in context["action_catalog"]
        if runner._is_teacher_action(item.name) and item.state.value == "observed"
    )

    unknown = asyncio.run(
        runner._execute_action(
            guarded_context,
            {"action": "teacher.unknown.operation", "parameters": {}},
        )
    )
    unavailable = asyncio.run(
        runner._execute_action(
            guarded_context,
            {"action": observed.name, "parameters": {}},
        )
    )

    assert unknown["status"] == "unknown_action"
    assert unavailable["status"] == "not_implemented"
    assert unavailable["capability"]["state"] == "observed"


def test_direct_action_result_carries_the_published_capability_boundary() -> None:
    runner = _load_runner()
    context = runner._load_runtime(ROOT)

    class ConfirmationRuntime:
        async def execute(self, action, parameters=None, confirmation_token=None):
            if action == "session.check":
                return {"status": "ok", "result": {"logged_in": True}}
            assert action == "notices.send"
            assert parameters == {"course": "课程", "content": "正文"}
            assert confirmation_token is None
            return {
                "status": "confirmation_required",
                "confirmation": {"summary": "发送课程通知", "token": "one-use"},
            }

    result = asyncio.run(
        runner._execute_action(
            {**context, "runtime": ConfirmationRuntime()},
            {
                "action": "notices.send",
                "parameters": {"course": "课程", "content": "正文"},
            },
        )
    )

    assert result["status"] == "confirmation_required"
    assert result["capability"] == {
        "action_id": "notices.send",
        "state": "implemented",
        "risk": "publish",
        "live_verified": False,
    }


def test_describe_reports_machine_usable_argument_schema() -> None:
    runner = _load_runner()
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    courses = sub.add_parser("courses", help="list teacher courses")
    courses.add_argument("--status", default="active")
    result = runner._describe({"cli_parser": parser}, "courses")
    assert result["status"] == "ok"
    assert result["execution"]["arguments"][0]["options"] == ["--status"]
    assert result["execution"]["arguments"][0]["default"] == "active"


def test_legacy_catalog_is_retrieval_only_and_never_authorizes_execution() -> None:
    runner = _load_runner()
    context = runner._load_runtime(ROOT)
    for request in ("看看英语写作2班还有哪些作业没改", "作业", "成绩"):
        result = runner._catalog(context, request, 0, 5)
        assert result["matching"] > 0
        assert result["commands"]
        assert result["selection_status"] == "retrieval_only"
        assert result["safe_to_auto_select"] is False
        assert result["ranking_role"] == "candidate_retrieval_only"


def test_domains_group_actions_before_candidate_retrieval() -> None:
    runner = _load_runner()
    context = runner._load_runtime(ROOT)
    result = runner._domains(context, "未批改作业", 0, 20)
    domains = {item["domain"] for item in result["domains"]}
    assert "homework" in domains
    assert result["ranking_role"] == "domain_retrieval_only"


@pytest.mark.parametrize("case", INTENT_CASES, ids=lambda case: case["request"])
def test_common_teacher_requests_retrieve_the_expected_domain(case) -> None:
    runner = _load_runner()
    context = runner._load_runtime(ROOT)

    result = runner._domains(context, case["request"], 0, 5)

    assert result["domains"], case["request"]
    assert result["domains"][0]["domain"] == case["domain"]


@pytest.mark.parametrize(
    "case",
    [case for case in INTENT_CASES if "expected_action" in case],
    ids=lambda case: case["request"],
)
def test_common_teacher_intents_rank_the_expected_action_first(case) -> None:
    runner = _load_runner()
    context = runner._load_runtime(ROOT)
    payload = {
        "request": case["request"],
        "domain": case["domain"],
        "operation": case["operation"],
        "keywords": case["keywords"],
        "entities": {},
        "values": {},
        "limit": 5,
    }

    candidates = runner._intent(context, payload)
    selected = runner._intent(
        context,
        {
            **payload,
            "action_id": case["expected_action"],
            "parameters": {"fixture_request": case["request"]},
        },
    )

    assert candidates["status"] == "candidates"
    assert candidates["candidates"][0]["action"]["name"] == case["expected_action"]
    assert selected["status"] == "selected"
    assert selected["execution"] == {
        "operation": "action",
        "payload": {
            "action": case["expected_action"],
            "parameters": {"fixture_request": case["request"]},
        },
    }


@pytest.mark.parametrize(
    "case",
    [case for case in INTENT_CASES if "expected_gap" in case],
    ids=lambda case: case["request"],
)
def test_known_near_match_gaps_do_not_route_to_a_different_action(case) -> None:
    runner = _load_runner()
    context = runner._load_runtime(ROOT)

    result = runner._intent(
        context,
        {
            "request": case["request"],
            "domain": case["domain"],
            "operation": case["operation"],
            "keywords": case["keywords"],
        },
    )

    assert result["status"] == case["expected_status"]
    assert result["known_gap"]["code"] == case["expected_gap"]
    assert "candidates" not in result


def test_structured_intent_retrieves_only_within_the_selected_domain() -> None:
    runner = _load_runner()
    context = runner._load_runtime(ROOT)
    payload = {
        "request": "看看英语写作2班还有哪些作业没改",
        "domain": "homework",
        "operation": ["查看", "列出"],
        "keywords": ["未批改"],
        "entities": {"course": "英语写作", "clazz": "2班"},
        "values": {},
    }
    result = runner._intent(context, payload)
    action_ids = {item["action"]["name"] for item in result["candidates"]}
    assert result["status"] == "candidates"
    assert result["selection_status"] == "requires_model_choice"
    assert result["safe_to_auto_select"] is False
    assert "homework.list_ungraded" in action_ids
    assert result["returned"] <= 8
    assert all(item["matched_terms"] for item in result["candidates"])
    assert all(item["action"]["domain"] == "homework" for item in result["candidates"])


def test_structured_intent_does_not_reinterpret_the_raw_utterance() -> None:
    runner = _load_runner()
    context = runner._load_runtime(ROOT)
    structured = {
        "domain": "homework",
        "operation": ["查看"],
        "keywords": ["未批改"],
    }
    first = runner._intent(context, {**structured, "request": "原始口语一"})
    second = runner._intent(context, {**structured, "request": "完全不同的原始口语"})
    assert [item["action"]["name"] for item in first["candidates"]] == [
        item["action"]["name"] for item in second["candidates"]
    ]


def test_structured_intent_keeps_a_bounded_fallback_when_terms_do_not_match() -> None:
    runner = _load_runner()
    context = runner._load_runtime(ROOT)
    result = runner._intent(
        context,
        {
            "domain": "homework",
            "operation": ["完全不存在的操作词"],
            "keywords": ["完全不存在的关键词"],
        },
    )

    assert result["status"] == "candidates"
    assert 0 < result["returned"] <= 8
    assert result["domain_action_total"] >= result["returned"]


def test_exact_action_id_prepares_a_typed_action_payload() -> None:
    runner = _load_runner()
    context = runner._load_runtime(ROOT)
    result = runner._intent(
        context,
        {
            "request": "看看英语写作2班还有哪些作业没改",
            "domain": "homework",
            "action_id": "homework.list_ungraded",
            "parameters": {"course": "英语写作", "clazz": "2班"},
        },
    )
    assert result["status"] == "selected"
    assert result["selection_basis"] == "exact_action_id"
    assert result["execution"] == {
        "operation": "action",
        "payload": {
            "action": "homework.list_ungraded",
            "parameters": {"course": "英语写作", "clazz": "2班"},
        },
    }
    assert result["parameter_adapters"]


def test_structured_intent_requires_a_domain_and_rejects_student_actions() -> None:
    runner = _load_runner()
    context = runner._load_runtime(ROOT)
    missing = runner._intent(
        context,
        {"request": "看看作业", "operation": "查看", "keywords": ["作业"]},
    )
    blocked = runner._intent(
        context,
        {"domain": "learning_homework", "action_id": "learning.course.homework.list"},
    )
    assert missing["status"] == "needs_domain"
    assert missing["domain_candidates"]
    assert blocked["status"] == "unknown_action"
