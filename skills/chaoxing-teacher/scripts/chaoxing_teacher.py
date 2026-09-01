#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import asyncio
import contextlib
import hashlib
import inspect
import io
import json
import os
import re
import sys
import textwrap
import time
from collections import Counter
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Skills are often watched for hot reload. Importing the bundled runtime must not
# fill the installed Skill with __pycache__ files and trigger a reload storm.
sys.dont_write_bytecode = True

PROTOCOL_VERSION = "2"
MINIMUM_PYTHON = (3, 11)
BUNDLED_DEPENDENCIES = ("requests", "urllib3", "certifi", "idna", "charset_normalizer")
CONTROL_COMMANDS = {
    "doctor",
    "capabilities",
    "domains",
    "intent",
    "session",
    "login",
    "plan",
    "run",
}
CONTROL_ACTIONS = {
    "capabilities.list",
    "command.plan",
    "command.execute",
    "session.check",
    "session.login",
}
DOMAIN_HINTS = {
    "courses": ("我教的课", "我教", "教课", "课程列表", "课的班级"),
    "class_management": ("学生名单", "班级成员", "班级管理", "邀请码", "移出班级"),
    "homework": ("未批作业", "待批作业", "作业没改", "作业", "批作业"),
    "notices": ("课程通知", "班级通知", "发通知", "通知草稿", "通知"),
    "inbox": ("收件箱", "个人通知", "站内信", "发给个人"),
    "resources": ("课程资料", "资料文件", "上传资料", "上传课程资料", "本地文件上传", "资料"),
    "course_assets": (
        "云盘导入课件",
        "从云盘导入课件",
        "个人云盘导入",
        "上传课件",
        "课件",
        "教案",
    ),
    "chapters": ("章节", "课程单元", "章节页面"),
    "exams": ("待批考试", "主观题没批", "考试", "试卷"),
    "question_bank": ("题库", "试题库", "搜索题目"),
    "discussions": ("课程讨论", "讨论回复", "发起讨论", "讨论", "话题"),
    "statistics": ("导出成绩", "综合成绩", "成绩册", "成绩权重", "成绩"),
    "class_activities": ("签到活动", "发起签到", "签到", "课堂活动", "抢答", "选人", "投票"),
    "cloud_disk": ("个人云盘", "云盘"),
    "groups": ("个人小组", "小组话题", "小组通知"),
}

# These phrases do not select an action. They only keep the most likely typed
# actions near the top of the bounded candidate list that the host model must
# still inspect and choose from.
ACTION_HINTS = {
    "courses.list_teaching": ("我教的课程", "我教的课", "教师课程"),
    "courses.list_classes": ("课程班级", "班级列表"),
    "class.students.list": ("学生名单", "班级学生", "学生列表"),
    "homework.list_ungraded": ("待批作业", "未批作业", "未批改", "作业没改"),
    "homework.submissions.list": ("作业提交", "提交记录", "待批提交"),
    "homework.submission.read": ("读取学生作答", "查看学生作答", "作答内容"),
    "homework.score.set": ("作业评分", "提交作业成绩", "提交分数", "给分", "打分"),
    "notices.send": ("发通知", "发送通知", "发送课程通知", "发布通知"),
    "notices.schedule": ("定时发送", "定时发送通知", "定时发送课程通知", "预约发布"),
    "resources.file.upload": ("上传资料", "上传课程资料", "上传本地课件", "上传文件"),
    "course_assets.cloud_files.import": ("云盘导入课件", "从云盘导入", "导入课件"),
    "exams.submissions.list": ("考试提交", "待批考试", "未批考试", "主观题没批"),
    "question_bank.list": ("搜索题库", "题库搜索", "浏览题库", "查找题目"),
    "discussions.topic.read": ("讨论回复", "查看回复", "讨论内容"),
    "course.grades.list": ("班级成绩", "学生成绩", "成绩册", "导出成绩"),
    "class_activities.activity.start": ("开始活动", "启动活动", "开始签到", "启动签到"),
}


class RunnerError(RuntimeError):
    pass


class RunnerBusy(RunnerError):
    pass


def _configure_output() -> None:
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def _skill_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def _temporary_data_dir_candidate() -> Path:
    for variable in ("TEMP", "TMP", "TMPDIR"):
        value = os.getenv(variable, "").strip()
        if value:
            return Path(value).expanduser().resolve() / "chaoxing-teacher"
    if os.name == "nt":
        local_app_data = os.getenv("LOCALAPPDATA", "").strip()
        if local_app_data:
            return Path(local_app_data).expanduser().resolve() / "Temp" / "chaoxing-teacher"
        system_root = os.getenv("SystemRoot", "C:\\Windows").strip() or "C:\\Windows"
        return Path(system_root).expanduser().resolve() / "Temp" / "chaoxing-teacher"
    return Path("/tmp/chaoxing-teacher")


def _data_dir_candidates() -> list[Path]:
    override = os.getenv("CHAOXING_TEACHER_DATA_DIR", "").strip()
    candidates: list[Path] = []
    if override:
        candidates.append(Path(override).expanduser().resolve())

    if os.name == "nt":
        base = os.getenv("LOCALAPPDATA", "").strip()
        candidates.append(
            (
                Path(base).expanduser().resolve()
                if base
                else Path.home().resolve() / "AppData" / "Local"
            )
            / "chaoxing-teacher"
        )
    elif sys.platform == "darwin":
        candidates.append(
            Path.home().resolve() / "Library" / "Application Support" / "chaoxing-teacher"
        )
    else:
        base = os.getenv("XDG_DATA_HOME", "").strip()
        candidates.append(
            (
                Path(base).expanduser().resolve()
                if base
                else Path.home().resolve() / ".local" / "share"
            )
            / "chaoxing-teacher"
        )

    candidates.extend(
        (
            _temporary_data_dir_candidate(),
            Path.cwd().resolve() / ".chaoxing-teacher-data",
        )
    )

    result: list[Path] = []
    seen: set[str] = set()
    skill_dir = _skill_dir()
    for candidate in candidates:
        try:
            candidate.relative_to(skill_dir)
        except ValueError:
            pass
        else:
            continue
        key = os.path.normcase(str(candidate))
        if key not in seen:
            seen.add(key)
            result.append(candidate)
    if not result:
        raise RunnerError("找不到可用的运行状态目录。")
    return result


def _default_data_dir() -> Path:
    return _data_dir_candidates()[0]


def _probe_data_dir(candidate: Path) -> None:
    candidate.mkdir(parents=True, exist_ok=True)
    probe = candidate / f".write-test-{os.getpid()}-{time.time_ns()}"
    try:
        probe.write_bytes(b"ok")
        probe.chmod(0o600)
    finally:
        probe.unlink(missing_ok=True)


def _writable_data_dir() -> Path:
    failures: list[str] = []
    for candidate in _data_dir_candidates():
        try:
            _probe_data_dir(candidate)
        except OSError as exc:
            failures.append(f"{candidate}: {exc}")
            continue
        return candidate
    detail = failures[-1] if failures else "没有候选目录"
    raise RunnerError(f"没有无需教师配置即可写入的运行状态目录：{detail}")


@contextmanager
def _data_lock(data_dir: Path, timeout_seconds: float = 30.0):
    lock_path = data_dir / ".runtime.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+b")
    if lock_path.stat().st_size == 0:
        handle.write(b"0")
        handle.flush()
    deadline = time.monotonic() + timeout_seconds
    locked = False
    try:
        while not locked:
            try:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
            except (OSError, BlockingIOError):
                if time.monotonic() >= deadline:
                    raise RunnerBusy("另一个学习通任务正在使用当前账号。") from None
                time.sleep(0.1)
        yield
    finally:
        if locked:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def _profile_id(username: str) -> str:
    normalized = username.strip().casefold()
    if not normalized:
        raise RunnerError("登录需要学习通账号和密码。")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:24]


def _active_profile_file(data_dir: Path) -> Path:
    return data_dir / "active-account.json"


def _profile_dir(data_dir: Path, profile_id: str) -> Path:
    if not profile_id or any(character not in "0123456789abcdef" for character in profile_id):
        raise RunnerError("本地账号状态无效，请重新登录。")
    return data_dir / "accounts" / profile_id


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, json.JSONDecodeError) as exc:
        raise RunnerError(f"本地账号状态无法读取：{exc}") from exc
    if not isinstance(payload, dict):
        raise RunnerError("本地账号状态格式无效，请重新登录。")
    return payload


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.chmod(0o600)
        temporary.replace(path)
    except OSError as exc:
        raise RunnerError(f"本地账号状态无法保存：{exc}") from exc
    finally:
        temporary.unlink(missing_ok=True)


def _active_profile_id(data_dir: Path) -> str | None:
    profile_id = str(_read_json(_active_profile_file(data_dir)).get("profile_id") or "")
    if not profile_id:
        return None
    _profile_dir(data_dir, profile_id)
    return profile_id


def _account_metadata(data_dir: Path, profile_id: str | None) -> dict[str, Any]:
    if not profile_id:
        return {}
    return _read_json(_profile_dir(data_dir, profile_id) / "account.json")


def _activate_profile(data_dir: Path, profile_id: str, username: str, account_name: str) -> None:
    profile = _profile_dir(data_dir, profile_id)
    hint = username if len(username) <= 4 else f"***{username[-4:]}"
    _write_json_atomic(
        profile / "account.json",
        {
            "profile_id": profile_id,
            "username_hint": hint,
            "account_name": account_name,
            "updated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        },
    )
    _write_json_atomic(_active_profile_file(data_dir), {"profile_id": profile_id})


def _ensure_dependencies() -> None:
    if sys.version_info < MINIMUM_PYTHON:
        raise RunnerError("此 Skill 需要内置运行时或宿主 Python 3.11 及以上版本。")
    vendor_dir = Path(__file__).resolve().with_name("vendor")
    if not vendor_dir.is_dir():
        raise RunnerError("Skill 安装包不完整：缺少内置 HTTP 运行组件。")
    vendor_path = str(vendor_dir)
    if vendor_path not in sys.path:
        sys.path.insert(0, vendor_path)
    try:
        for dependency in BUNDLED_DEPENDENCIES:
            __import__(dependency)
    except ImportError as exc:
        raise RunnerError(f"Skill 安装包不完整：内置 HTTP 运行组件无法加载（{exc}）。") from exc


def _load_runtime(data_dir: Path | None = None, profile_id: str | None = None) -> dict[str, Any]:
    runtime_root = Path(__file__).resolve().parent / "runtime"
    if str(runtime_root) not in sys.path:
        sys.path.insert(0, str(runtime_root))

    from chaoxing_teacher_runtime.capabilities import ACTION_CATALOG
    from chaoxing_teacher_runtime.cli import _run_action, build_parser
    from chaoxing_teacher_runtime.config import Settings
    from chaoxing_teacher_runtime.runtime import ActionRuntime, ActionRuntimeError

    def legacy_route_command(request: str) -> Any:
        from chaoxing_teacher_runtime.router import route_command

        return route_command(request)

    data_dir = data_dir or _default_data_dir()
    has_profile = profile_id is not None
    profile_id = profile_id or ("0" * 24)
    profile = _profile_dir(data_dir, profile_id)
    settings = Settings(
        cookie_file=profile / "cookies.json",
        request_timeout=20.0,
        confirmation_file=profile / "confirmations.json",
        state_file=profile / "state.json",
    )
    return {
        "runtime": ActionRuntime(settings),
        "settings": settings,
        "data_dir": data_dir,
        "profile_id": profile_id,
        "account": _account_metadata(data_dir, profile_id) if has_profile else {},
        "action_catalog": ACTION_CATALOG,
        "cli_parser": build_parser(),
        "run_cli_action": _run_action,
        "route_command": legacy_route_command,
        "runtime_error": ActionRuntimeError,
    }


def _parse_payload(raw: str, source: str) -> dict[str, Any]:
    if not raw.strip():
        raise RunnerError(f"此操作需要通过{source}接收 JSON。")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RunnerError(f"{source}不是有效的 JSON 对象。") from exc
    if not isinstance(payload, dict):
        raise RunnerError(f"{source}必须是 JSON 对象。")
    return {str(key): value for key, value in payload.items()}


def _read_payload(input_json: str | None = None) -> dict[str, Any]:
    if input_json is not None:
        return _parse_payload(input_json, "--input-json 参数")
    return _parse_payload(sys.stdin.readline(), "标准输入")


def _emit(payload: Any, secrets: tuple[str, ...] = ()) -> None:
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    for secret in secrets:
        if secret:
            rendered = rendered.replace(secret, "[未回显]")
    print(rendered)


def _is_teacher_action(action: str) -> bool:
    return bool(action) and not action.startswith("learning.")


def _is_teacher_command(command: str) -> bool:
    return bool(command) and not command.startswith("learning-") and command not in CONTROL_COMMANDS


def _subcommands(parser: argparse.ArgumentParser) -> tuple[Any, dict[str, argparse.ArgumentParser]]:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action, action.choices
    raise RunnerError("内置命令目录不可用。")


def _json_value(value: Any) -> Any:
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        return str(value)
    return value


def _argument_schema(action: argparse.Action) -> dict[str, Any] | None:
    if action.dest in {"help", "command"} or action.help is argparse.SUPPRESS:
        return None
    positional = not action.option_strings
    required = action.required if not positional else action.nargs not in ("?", "*")
    result: dict[str, Any] = {
        "name": action.dest,
        "options": list(action.option_strings),
        "positional": positional,
        "required": bool(required),
        "kind": type(action).__name__.removeprefix("_").removesuffix("Action"),
    }
    if action.help:
        result["description"] = action.help
    if action.nargs is not None:
        result["nargs"] = action.nargs
    if action.type is not None:
        result["type"] = getattr(action.type, "__name__", str(action.type))
    if action.choices is not None:
        result["choices"] = [_json_value(value) for value in action.choices]
    if action.default is not argparse.SUPPRESS:
        result["default"] = _json_value(action.default)
    return result


def _command_description(
    subparsers: Any,
    command: str,
    parser: argparse.ArgumentParser,
) -> dict[str, Any]:
    help_text = ""
    for choice in subparsers._choices_actions:
        if choice.dest == command:
            help_text = choice.help or ""
            break
    arguments = []
    for action in parser._actions:
        schema = _argument_schema(action)
        if schema is not None:
            arguments.append(schema)
    return {"command": command, "description": help_text, "arguments": arguments}


def _localized_command(entry: dict[str, Any], actions: list[dict[str, Any]]) -> dict[str, Any]:
    labels = list(
        dict.fromkeys(str(item.get("label") or "") for item in actions if item.get("label"))
    )
    descriptions = list(
        dict.fromkeys(
            str(item.get("description") or "") for item in actions if item.get("description")
        )
    )
    aliases = list(
        dict.fromkeys(str(alias) for item in actions for alias in item.get("aliases", []) if alias)
    )
    return {
        "name": " / ".join(labels) if labels else "教师端操作",
        "description": "；".join(descriptions) if descriptions else "执行一项教师端操作。",
        "aliases": aliases,
        "risk": list(dict.fromkeys(str(item.get("risk") or "") for item in actions)),
        "state": list(dict.fromkeys(str(item.get("state") or "") for item in actions)),
        "live_verified": bool(actions) and all(item.get("live_verified") for item in actions),
        "execution": {
            "command_id": entry["command"],
            "arguments": entry["arguments"],
            "actions": actions,
        },
    }


def _compact_search_text(value: str) -> str:
    return "".join(re.findall(r"[0-9a-z\u4e00-\u9fff]+", value.casefold()))


def _text_match_score(query: str, searchable: str) -> tuple[int, list[str]]:
    query_compact = _compact_search_text(query)
    if not query_compact:
        return 1, []
    searchable_compact = _compact_search_text(searchable)
    score = 0
    if len(query_compact) >= 4 and query_compact in searchable_compact:
        score += 100
    chinese_query = "".join(re.findall(r"[\u4e00-\u9fff]", query.casefold()))
    bigrams = {chinese_query[index : index + 2] for index in range(max(0, len(chinese_query) - 1))}
    matched_chinese = sorted(bigram for bigram in bigrams if bigram in searchable_compact)
    score += min(40, 4 * len(matched_chinese))
    latin_terms = set(re.findall(r"[0-9a-z]+", query.casefold()))
    matched_latin = sorted(term for term in latin_terms if term in searchable.casefold())
    score += 12 * len(matched_latin)
    return score, [*matched_latin, *matched_chinese[:10]]


def _domain_hint_score(query: str, domain: str) -> tuple[int, list[str]]:
    compact_query = _compact_search_text(query)
    matched = [
        hint for hint in DOMAIN_HINTS.get(domain, ()) if _compact_search_text(hint) in compact_query
    ]
    score = sum(350 + min(len(_compact_search_text(hint)), 8) * 30 for hint in matched)
    return score, matched


def _action_hint_score(query: str, action_id: str) -> tuple[int, list[str]]:
    compact_query = _compact_search_text(query)
    matched = [
        hint
        for hint in ACTION_HINTS.get(action_id, ())
        if _compact_search_text(hint) in compact_query
    ]
    score = sum(500 + min(len(_compact_search_text(hint)), 10) * 25 for hint in matched)
    return score, matched


def _known_intent_gap(
    domain: str,
    operation_terms: list[str],
    keywords: list[str],
) -> dict[str, Any] | None:
    operation = _compact_search_text(" ".join(operation_terms))
    objects = _compact_search_text(" ".join(keywords))
    full = f"{operation}{objects}"
    if (
        domain == "class_activities"
        and any(word in operation for word in ("发起", "创建", "新建"))
        and "签到" in full
    ):
        return {
            "code": "class_attendance_create_not_implemented",
            "message": "当前运行时可以读取、开始或结束已有班级活动，但尚未实现新建签到活动。",
            "available_alternatives": [
                "class_activities.activities.list",
                "class_activities.activity.start",
            ],
        }
    if (
        domain == "course_assets"
        and "上传" in operation
        and any(word in objects for word in ("本地", "电脑", "桌面"))
    ):
        return {
            "code": "local_course_asset_upload_not_implemented",
            "message": (
                "当前运行时只支持从个人云盘导入课件或教案；"
                "本地文件可以上传到课程资料，但尚不能直接上传到课件或教案栏目。"
            ),
            "available_alternatives": [
                "resources.file.upload",
                "course_assets.cloud_files.import",
            ],
        }
    return None


def _catalog_match_score(query: str, entry: dict[str, Any]) -> tuple[int, list[str]]:
    searchable = json.dumps(
        {
            "name": entry.get("name"),
            "description": entry.get("description"),
            "aliases": entry.get("aliases"),
        },
        ensure_ascii=False,
    )
    score, matched = _text_match_score(query, searchable)
    query_compact = _compact_search_text(query)
    for phrase in [str(entry.get("name") or ""), *entry.get("aliases", [])]:
        compact_phrase = _compact_search_text(phrase)
        if len(compact_phrase) >= 2 and compact_phrase in query_compact:
            score += 80 + min(len(compact_phrase), 12) * 5
    return score, matched


def _command_names_from_test(test: ast.expr) -> set[str]:
    if isinstance(test, ast.BoolOp):
        result: set[str] = set()
        for value in test.values:
            result.update(_command_names_from_test(value))
        return result
    if not isinstance(test, ast.Compare) or len(test.ops) != 1 or len(test.comparators) != 1:
        return set()
    left = test.left
    right = test.comparators[0]

    def is_command(node: ast.expr) -> bool:
        return (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "args"
            and node.attr == "command"
        )

    def strings(node: ast.expr) -> set[str]:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return {node.value}
        if isinstance(node, (ast.List, ast.Set, ast.Tuple)):
            return {
                item.value
                for item in node.elts
                if isinstance(item, ast.Constant) and isinstance(item.value, str)
            }
        return set()

    if is_command(left):
        return strings(right)
    if is_command(right):
        return strings(left)
    return set()


def _command_action_hints(context: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    runner = context.get("run_cli_action")
    catalog = context.get("action_catalog", ())
    if runner is None or not catalog:
        return {}
    known = {item.name: item for item in catalog if _is_teacher_action(item.name)}
    tree = ast.parse(textwrap.dedent(inspect.getsource(runner)))
    function = tree.body[0]
    if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return {}
    result: dict[str, list[dict[str, Any]]] = {}
    for statement in function.body:
        if not isinstance(statement, ast.If):
            continue
        commands = _command_names_from_test(statement.test)
        if not commands:
            continue
        action_names = sorted(
            {
                node.value
                for node in ast.walk(statement)
                if isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and node.value in known
            }
        )
        summaries = [known[name].to_dict() for name in action_names]
        for command in commands:
            if _is_teacher_command(command):
                result[command] = summaries
    return result


def _page(items: list[Any], offset: int, limit: int) -> tuple[list[Any], int, int]:
    safe_offset = max(0, offset)
    safe_limit = max(1, min(limit, 200))
    return items[safe_offset : safe_offset + safe_limit], safe_offset, safe_limit


def _catalog(context: dict[str, Any], query: str, offset: int, limit: int) -> dict[str, Any]:
    subparsers, choices = _subcommands(context["cli_parser"])
    action_hints = _command_action_hints(context)
    query = query.strip()
    entries: list[tuple[int, dict[str, Any], list[str]]] = []
    for command, parser in choices.items():
        if not _is_teacher_command(command):
            continue
        entry = _command_description(subparsers, command, parser)
        localized = _localized_command(entry, action_hints.get(command, []))
        score, matched_concepts = _catalog_match_score(query, localized)
        if score > 0:
            entries.append((score, localized, matched_concepts))
    if query:
        entries.sort(key=lambda item: (-item[0], item[1]["execution"]["command_id"]))
    else:
        entries.sort(key=lambda item: item[1]["execution"]["command_id"])
    selected, safe_offset, safe_limit = _page(entries, offset, limit)
    commands: list[dict[str, Any]] = []
    for score, item, matched_fragments in selected:
        rendered = dict(item)
        if query:
            rendered["match"] = {"score": score, "fragments": matched_fragments}
        commands.append(rendered)
    selection_status = "retrieval_only" if query else "unranked"
    return {
        "status": "ok",
        "protocol_version": PROTOCOL_VERSION,
        "scope": "teacher",
        "matching": len(entries),
        "offset": safe_offset,
        "limit": safe_limit,
        "returned": len(selected),
        "selection_status": selection_status,
        "safe_to_auto_select": False,
        "ranking_role": "candidate_retrieval_only",
        "commands": commands,
    }


def _describe(context: dict[str, Any], command: str) -> dict[str, Any]:
    if not _is_teacher_command(command):
        return {
            "status": "out_of_scope",
            "scope": "teacher",
            "message": "此 Skill 不执行学生端学习、作答、考试、自测或学习记录操作。",
        }
    subparsers, choices = _subcommands(context["cli_parser"])
    parser = choices.get(command)
    if parser is None:
        return {"status": "unknown_command", "command": command}
    action_hints = _command_action_hints(context)
    return {
        "status": "ok",
        "protocol_version": PROTOCOL_VERSION,
        **_localized_command(
            _command_description(subparsers, command, parser),
            action_hints.get(command, []),
        ),
    }


def _capabilities(context: dict[str, Any], query: str, offset: int, limit: int) -> dict[str, Any]:
    actions = [item for item in context["action_catalog"] if _is_teacher_action(item.name)]
    ranked = []
    for action in actions:
        score, _ = _text_match_score(query, json.dumps(action.to_dict(), ensure_ascii=False))
        if query and score <= 0:
            continue
        ranked.append((score, action))
    ranked.sort(key=lambda item: (-item[0], item[1].name) if query else (0, item[1].name))
    selected, safe_offset, safe_limit = _page(ranked, offset, limit)
    return {
        "status": "ok",
        "protocol_version": PROTOCOL_VERSION,
        "scope": "teacher and teacher-related personal space",
        "summary": {
            "teacher_action_total": len(actions),
            "matching": len(ranked),
            "by_state": dict(Counter(item.state.value for item in actions)),
            "by_verification": dict(
                Counter(
                    "live_verified" if item.live_verified else "not_live_verified"
                    for item in actions
                )
            ),
        },
        "offset": safe_offset,
        "limit": safe_limit,
        "returned": len(selected),
        "actions": [item.to_dict() for _, item in selected],
    }


def _selectable_actions(context: dict[str, Any]) -> list[Any]:
    return [
        item
        for item in context["action_catalog"]
        if _is_teacher_action(item.name) and item.name not in CONTROL_ACTIONS
    ]


def _action_command_adapters(context: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    subparsers, choices = _subcommands(context["cli_parser"])
    action_hints = _command_action_hints(context)
    result: dict[str, list[dict[str, Any]]] = {}
    for command, actions in action_hints.items():
        parser = choices.get(command)
        if parser is None:
            continue
        description = _command_description(subparsers, command, parser)
        adapter = {
            "command_id": command,
            "arguments": description["arguments"],
        }
        for action in actions:
            action_id = str(action.get("name") or "")
            if action_id and _is_teacher_action(action_id) and action_id not in CONTROL_ACTIONS:
                result.setdefault(action_id, []).append(adapter)
    return result


def _domains(context: dict[str, Any], query: str, offset: int, limit: int) -> dict[str, Any]:
    grouped: dict[str, list[Any]] = {}
    for action in _selectable_actions(context):
        if action.state.value != "implemented":
            continue
        grouped.setdefault(str(action.domain), []).append(action)

    entries: list[tuple[int, dict[str, Any]]] = []
    for domain, actions in grouped.items():
        actions.sort(key=lambda item: item.name)
        searchable = json.dumps(
            {
                "domain": domain,
                "actions": [item.to_dict() for item in actions],
            },
            ensure_ascii=False,
        )
        score, matched = _text_match_score(query, searchable)
        hint_score, matched_hints = _domain_hint_score(query, domain)
        score += hint_score
        matched = list(dict.fromkeys([*matched_hints, *matched]))
        if query and score <= 0:
            continue
        example_actions = actions
        if query:
            example_actions = sorted(
                actions,
                key=lambda item: (
                    -_text_match_score(query, json.dumps(item.to_dict(), ensure_ascii=False))[0],
                    item.name,
                ),
            )
        entries.append(
            (
                score,
                {
                    "domain": domain,
                    "action_total": len(actions),
                    "by_state": dict(Counter(item.state.value for item in actions)),
                    "live_verified": sum(bool(item.live_verified) for item in actions),
                    "matched_fragments": matched,
                    "examples": [
                        {
                            "action_id": item.name,
                            "label": item.label,
                            "description": item.description,
                        }
                        for item in example_actions[:5]
                    ],
                },
            )
        )
    if query:
        entries.sort(key=lambda item: (-item[0], item[1]["domain"]))
    else:
        entries.sort(key=lambda item: item[1]["domain"])
    selected, safe_offset, safe_limit = _page(entries, offset, limit)
    return {
        "status": "ok",
        "protocol_version": PROTOCOL_VERSION,
        "scope": "teacher",
        "ranking_role": "domain_retrieval_only",
        "matching": len(entries),
        "offset": safe_offset,
        "limit": safe_limit,
        "returned": len(selected),
        "domains": [item for _, item in selected],
    }


def _payload_mapping(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key, {})
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise RunnerError(f"intent.{key} 必须是 JSON 对象。")
    return {str(name): item for name, item in value.items()}


def _payload_terms(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key, [])
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise RunnerError(f"intent.{key} 必须是字符串或字符串数组。")
    return [item.strip() for item in value if item.strip()]


def _intent(context: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    request = str(payload.get("request") or "").strip()
    domain = str(payload.get("domain") or "").strip()
    action_id = str(payload.get("action_id") or "").strip()
    operation_terms = _payload_terms(payload, "operation")
    keywords = _payload_terms(payload, "keywords")
    entities = _payload_mapping(payload, "entities")
    values = _payload_mapping(payload, "values")
    parameters = _payload_mapping(payload, "parameters")
    include_observed = bool(payload.get("include_observed", False))
    try:
        limit = max(1, min(int(payload.get("limit", 8)), 100))
    except (TypeError, ValueError) as exc:
        raise RunnerError("intent.limit 必须是整数。") from exc

    actions = _selectable_actions(context)
    action_by_name = {item.name: item for item in actions}
    normalized = {
        "request": request,
        "domain": domain,
        "operation": operation_terms,
        "keywords": keywords,
        "entities": entities,
        "values": values,
    }

    if action_id:
        action = action_by_name.get(action_id)
        if action is None:
            return {
                "status": "unknown_action",
                "protocol_version": PROTOCOL_VERSION,
                "action_id": action_id,
                "message": "所选 action_id 不属于当前教师端动作目录。",
            }
        if domain and action.domain != domain:
            return {
                "status": "domain_mismatch",
                "protocol_version": PROTOCOL_VERSION,
                "intent": normalized,
                "action": action.to_dict(),
                "message": "所选动作不属于结构化意图中的领域。",
            }
        if action.state.value != "implemented":
            return {
                "status": "not_implemented",
                "protocol_version": PROTOCOL_VERSION,
                "intent": normalized,
                "action": action.to_dict(),
            }
        return {
            "status": "selected",
            "protocol_version": PROTOCOL_VERSION,
            "selection_basis": "exact_action_id",
            "intent": normalized,
            "action": action.to_dict(),
            "parameter_adapters": _action_command_adapters(context).get(action.name, []),
            "execution": {
                "operation": "action",
                "payload": {"action": action.name, "parameters": parameters},
            },
        }

    if not domain:
        query = " ".join([*operation_terms, *keywords, request]).strip()
        suggestions = _domains(context, query, 0, min(limit, 20))
        return {
            "status": "needs_domain",
            "protocol_version": PROTOCOL_VERSION,
            "intent": normalized,
            "selection_status": "requires_model_choice",
            "domain_candidates": suggestions["domains"],
        }

    domain_actions = [item for item in actions if item.domain == domain]
    if not domain_actions:
        suggestions = _domains(context, " ".join([domain, *keywords]), 0, min(limit, 20))
        return {
            "status": "unknown_domain",
            "protocol_version": PROTOCOL_VERSION,
            "intent": normalized,
            "domain_candidates": suggestions["domains"],
        }
    if not include_observed:
        domain_actions = [item for item in domain_actions if item.state.value == "implemented"]

    structured_terms = [*operation_terms, *keywords]
    known_gap = _known_intent_gap(domain, operation_terms, keywords)
    if known_gap is not None:
        return {
            "status": "not_implemented",
            "protocol_version": PROTOCOL_VERSION,
            "intent": normalized,
            "known_gap": known_gap,
        }

    structured_query = " ".join(structured_terms)
    ranked: list[tuple[int, dict[str, Any]]] = []
    for action in domain_actions:
        rendered = action.to_dict()
        searchable = json.dumps(rendered, ensure_ascii=False)
        total = 0
        matched_terms: list[str] = []
        for term in structured_terms:
            score, matched = _text_match_score(term, searchable)
            total += score
            if score > 0:
                matched_terms.append(term)
            matched_terms.extend(item for item in matched if item not in matched_terms)
        hint_score, matched_hints = _action_hint_score(structured_query, action.name)
        total += hint_score
        matched_terms.extend(item for item in matched_hints if item not in matched_terms)
        ranked.append(
            (
                total,
                {
                    "action": rendered,
                    "matched_terms": matched_terms,
                },
            )
        )
    if structured_terms:
        ranked.sort(key=lambda item: (-item[0], item[1]["action"]["name"]))
    else:
        ranked.sort(key=lambda item: item[1]["action"]["name"])
    matched = [item for item in ranked if item[0] > 0]
    candidate_pool = matched or ranked
    selected = candidate_pool[:limit]
    return {
        "status": "candidates",
        "protocol_version": PROTOCOL_VERSION,
        "intent": normalized,
        "selection_status": "requires_model_choice",
        "safe_to_auto_select": False,
        "ranking_role": "within_domain_candidate_retrieval_only",
        "domain_action_total": len(ranked),
        "matching": len(candidate_pool),
        "returned": len(selected),
        "candidates": [item for _, item in selected],
    }


def _plan(context: dict[str, Any], request: str) -> dict[str, Any]:
    plan = context["route_command"](request)
    if plan.action and not _is_teacher_action(plan.action):
        return {
            "status": "out_of_scope",
            "scope": "teacher",
            "plan": plan.to_dict(),
            "message": "此 Skill 不执行学生端学习、作答、考试、自测或学习记录操作。",
        }
    status = "ok"
    if plan.action is None:
        status = "unresolved"
    elif plan.missing_fields:
        status = "needs_input"
    result = {"status": status, "plan": plan.to_dict()}
    if status != "ok":
        suggestions = _catalog(context, request, 0, 5)
        result["suggestions"] = suggestions["commands"]
    return result


async def _execute_request(
    context: dict[str, Any], request: str, confirmation_token: str | None
) -> dict[str, Any]:
    planned = _plan(context, request)
    if planned["status"] != "ok":
        return planned
    login_required = await _login_requirement(context)
    if login_required is not None:
        return login_required
    plan = planned["plan"]
    result = await context["runtime"].execute(
        plan["action"], plan["parameters"], confirmation_token
    )
    return _attach_account({"status": result["status"], "plan": plan, "execution": result}, context)


def _attach_account(result: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    account = context.get("account")
    if not isinstance(account, dict) or not account:
        return result
    rendered = dict(result)
    rendered["account"] = account
    confirmation = rendered.get("confirmation")
    if isinstance(confirmation, dict) and confirmation.get("summary"):
        confirmation = dict(confirmation)
        account_name = str(
            account.get("account_name") or account.get("username_hint") or "当前账号"
        )
        confirmation["summary"] = f"账号《{account_name}》：{confirmation['summary']}"
        rendered["confirmation"] = confirmation
    return rendered


async def _login(context: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    username = str(payload.get("username") or "")
    password = str(payload.get("password") or "")
    fid = str(payload.get("fid") or "-1").strip()
    if not username or not password:
        raise RunnerError("登录需要学习通账号和密码。")
    try:
        login_result = await context["runtime"].execute(
            "session.login",
            {"username": username, "password": password, "fid": fid},
        )
        if login_result.get("status") != "ok":
            return {
                "status": login_result.get("status", "error"),
                "login": login_result,
                "active_account_unchanged": True,
            }
        session_result = await context["runtime"].execute("session.check")
        session_payload = session_result.get("result", {})
        account_name = (
            str(session_payload.get("account_name") or "").strip()
            if isinstance(session_payload, dict)
            else ""
        )
        _activate_profile(
            context["data_dir"],
            context["profile_id"],
            username,
            account_name,
        )
        return {
            "status": login_result["status"],
            "login": login_result,
            "session": session_result,
            "account": _account_metadata(context["data_dir"], context["profile_id"]),
        }
    finally:
        payload["password"] = ""
        password = ""


async def _session(context: dict[str, Any]) -> dict[str, Any]:
    cookie_file = context["settings"].cookie_file
    if cookie_file is None or not cookie_file.exists():
        return {
            "status": "login_required",
            "action": "session.check",
            "result": {"logged_in": False, "reason": "no_saved_session"},
            "next_prompt": "请输入学习通账号。",
        }
    result = await context["runtime"].execute("session.check")
    session_payload = result.get("result", {})
    if not isinstance(session_payload, dict) or session_payload.get("logged_in") is not True:
        return _attach_account(
            {
                "status": "login_required",
                "action": "session.check",
                "result": session_payload,
                "next_prompt": "请输入学习通账号。",
            },
            context,
        )
    result["account"] = context.get("account", {})
    return result


async def _login_requirement(context: dict[str, Any]) -> dict[str, Any] | None:
    result = await context["runtime"].execute("session.check")
    session_payload = result.get("result", {})
    if (
        result.get("status") == "ok"
        and isinstance(session_payload, dict)
        and session_payload.get("logged_in") is True
    ):
        return None
    return _attach_account(
        {
            "status": "login_required",
            "action": "session.check",
            "result": session_payload,
            "next_prompt": "请输入学习通账号。",
        },
        context,
    )


def _logout(data_dir: Path, profile_id: str | None) -> dict[str, Any]:
    if not profile_id:
        return {"status": "ok", "logged_out": True, "already_logged_out": True}
    profile = _profile_dir(data_dir, profile_id)
    for name in ("cookies.json", "confirmations.json", "state.json", "account.json"):
        (profile / name).unlink(missing_ok=True)
    try:
        profile.rmdir()
    except OSError:
        pass
    _active_profile_file(data_dir).unlink(missing_ok=True)
    return {"status": "ok", "logged_out": True, "profile_id": profile_id}


async def _invoke(context: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    command = str(payload.get("command_id") or payload.get("command") or "").strip()
    arguments = payload.get("arguments", [])
    if not _is_teacher_command(command):
        return {
            "status": "out_of_scope",
            "scope": "teacher",
            "message": "此 Skill 不执行学生端学习、作答、考试、自测或学习记录操作。",
        }
    if not isinstance(arguments, list) or not all(isinstance(item, str) for item in arguments):
        raise RunnerError("invoke.arguments 必须是字符串数组。")
    parser = context["cli_parser"]
    stderr = io.StringIO()
    try:
        with contextlib.redirect_stderr(stderr):
            parsed = parser.parse_args([command, *arguments])
    except SystemExit as exc:
        detail = stderr.getvalue().strip().splitlines()
        message = detail[-1] if detail else "命令参数无效。"
        raise RunnerError(message) from exc
    login_required = await _login_requirement(context)
    if login_required is not None:
        return login_required
    result = await context["run_cli_action"](parsed, context["runtime"])
    return _attach_account(result, context)


def _action_capability(context: dict[str, Any], action_id: str) -> Any | None:
    return next(
        (item for item in context.get("action_catalog", ()) if item.name == action_id),
        None,
    )


async def _execute_action(context: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    action = str(payload.get("action") or "").strip()
    if not _is_teacher_action(action) or action in CONTROL_ACTIONS:
        return {
            "status": "out_of_scope",
            "scope": "teacher",
            "message": "请使用教师端语义动作；学生端和控制动作不能从通用入口执行。",
        }
    parameters = payload.get("parameters", {})
    if not isinstance(parameters, dict):
        raise RunnerError("action.parameters 必须是 JSON 对象。")
    capability = _action_capability(context, action)
    if context.get("action_catalog") is not None and capability is None:
        return {
            "status": "unknown_action",
            "protocol_version": PROTOCOL_VERSION,
            "action": action,
            "message": "该动作不在当前教师端能力目录中。",
        }
    if capability is not None and capability.state.value != "implemented":
        return {
            "status": "not_implemented",
            "protocol_version": PROTOCOL_VERSION,
            "action": action,
            "capability": capability.to_dict(),
        }
    login_required = await _login_requirement(context)
    if login_required is not None:
        return login_required
    token = str(payload.get("confirmation_token") or "").strip() or None
    result = await context["runtime"].execute(action, parameters, token)
    rendered = _attach_account(result, context)
    if capability is not None:
        rendered["capability"] = {
            "action_id": capability.name,
            "state": capability.state.value,
            "risk": capability.risk.value,
            "live_verified": bool(capability.live_verified),
        }
    return rendered


def _runner_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="chaoxing-teacher")
    sub = parser.add_subparsers(dest="operation", required=True)
    sub.add_parser("doctor")
    sub.add_parser("session")
    login = sub.add_parser("login")
    login.add_argument("--username")
    login.add_argument("--password")
    login.add_argument("--fid", default="-1")
    sub.add_parser("logout")
    for name in ("catalog", "capabilities", "domains"):
        command = sub.add_parser(name)
        command.add_argument("--query", default="")
        command.add_argument("--offset", type=int, default=0)
        command.add_argument("--limit", type=int, default=50)
    describe = sub.add_parser("describe")
    describe.add_argument("command")
    for name in ("invoke", "intent", "plan", "execute", "action"):
        command = sub.add_parser(name)
        command.add_argument("--input-json")
    return parser


def _login_payload(args: argparse.Namespace) -> dict[str, Any]:
    if args.username is None and args.password is None:
        return _read_payload()
    return {
        "username": args.username or "",
        "password": args.password or "",
        "fid": args.fid,
    }


def _doctor(context: dict[str, Any]) -> dict[str, Any]:
    settings = context["settings"]
    return {
        "status": "ok",
        "protocol_version": PROTOCOL_VERSION,
        "runtime": "bundled_http",
        "python": {
            "version": ".".join(str(part) for part in sys.version_info[:3]),
            "executable": str(Path(sys.executable).resolve()),
        },
        "teacher_scope": True,
        "natural_language_path": "structured_intent_to_typed_action",
        "dependencies": "bundled_offline",
        "bundled_dependencies": list(BUNDLED_DEPENDENCIES),
        "session_exists": bool(settings.cookie_file and settings.cookie_file.exists()),
        "data_directory": str(context["data_dir"]),
        "preferred_data_directory": str(_default_data_dir()),
        "using_storage_fallback": context["data_dir"] != _default_data_dir(),
        "active_account": context.get("account", {}),
    }


def main(argv: list[str] | None = None) -> int:
    _configure_output()
    secrets: tuple[str, ...] = ()
    try:
        args = _runner_parser().parse_args(argv)
        _ensure_dependencies()
        payload: dict[str, Any] = {}
        if args.operation in {"invoke", "intent", "plan", "execute", "action"}:
            payload = _read_payload(args.input_json)
        if args.operation == "login":
            payload = _login_payload(args)
            secrets = (str(payload.get("password") or ""),)

        stateless = {
            "doctor",
            "catalog",
            "capabilities",
            "domains",
            "describe",
            "intent",
            "plan",
        }
        if args.operation in stateless:
            context = _load_runtime()
            if args.operation == "doctor":
                result = _doctor(context)
            elif args.operation == "catalog":
                result = _catalog(context, args.query, args.offset, args.limit)
            elif args.operation == "capabilities":
                result = _capabilities(context, args.query, args.offset, args.limit)
            elif args.operation == "domains":
                result = _domains(context, args.query, args.offset, args.limit)
            elif args.operation == "describe":
                result = _describe(context, args.command)
            elif args.operation == "intent":
                result = _intent(context, payload)
            else:
                result = _plan(context, str(payload.get("request") or ""))
        else:
            data_dir = _writable_data_dir()
            with _data_lock(data_dir):
                active_profile = _active_profile_id(data_dir)
                if args.operation == "login":
                    username = str(payload.get("username") or "").strip()
                    profile_id = _profile_id(username)
                    context = _load_runtime(data_dir, profile_id)
                    result = asyncio.run(_login(context, payload))
                elif args.operation == "logout":
                    result = _logout(data_dir, active_profile)
                elif args.operation == "session":
                    if active_profile is None:
                        result = {
                            "status": "login_required",
                            "action": "session.check",
                            "result": {"logged_in": False, "reason": "no_saved_session"},
                            "next_prompt": "请输入学习通账号。",
                        }
                    else:
                        context = _load_runtime(data_dir, active_profile)
                        result = asyncio.run(_session(context))
                elif active_profile is None:
                    result = {
                        "status": "login_required",
                        "action": "session.check",
                        "result": {"logged_in": False, "reason": "no_saved_session"},
                        "next_prompt": "请输入学习通账号。",
                    }
                else:
                    context = _load_runtime(data_dir, active_profile)
                    if args.operation == "invoke":
                        result = asyncio.run(_invoke(context, payload))
                    elif args.operation == "execute":
                        result = asyncio.run(
                            _execute_request(
                                context,
                                str(payload.get("request") or ""),
                                str(payload.get("confirmation_token") or "").strip() or None,
                            )
                        )
                    else:
                        result = asyncio.run(_execute_action(context, payload))
        _emit(result, secrets)
        return 0
    except RunnerBusy as exc:
        _emit({"status": "busy", "retry_after_seconds": 2, "message": str(exc)}, secrets)
        return 3
    except SystemExit:
        raise
    except Exception as exc:
        message = str(exc)
        for secret in secrets:
            if secret:
                message = message.replace(secret, "[未回显]")
        _emit({"status": "error", "error": message}, secrets)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
