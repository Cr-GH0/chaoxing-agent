from __future__ import annotations

import argparse
import json
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "chaoxing-teacher"
FAKE_RUNNER = ROOT / "tests" / "fixtures" / "workbuddy_fake_run.ps1"
DEFAULT_CLI = Path(r"C:\Program Files\WorkBuddy\resources\app.asar.unpacked\cli\dist\codebuddy.js")
USERNAME = "教师 账号'&中文"
PASSWORD = "明文 密码'$&中文"
TASK = "帮我看看英语写作二班还有哪些作业没改。"


class EvalError(RuntimeError):
    pass


def _reader(stream, output: queue.Queue[dict[str, Any] | BaseException]) -> None:
    try:
        for line in stream:
            text = line.strip()
            if not text:
                continue
            try:
                output.put(json.loads(text))
            except json.JSONDecodeError:
                continue
    except BaseException as exc:  # pragma: no cover - diagnostic boundary
        output.put(exc)


def _send(process: subprocess.Popen[str], text: str) -> None:
    if process.stdin is None:
        raise EvalError("WorkBuddy input stream is unavailable")
    message = {"type": "user", "message": {"role": "user", "content": text}}
    process.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
    process.stdin.flush()


def _wait_result(
    output: queue.Queue[dict[str, Any] | BaseException], timeout: float = 90.0
) -> tuple[str, list[dict[str, Any]]]:
    deadline = time.monotonic() + timeout
    events: list[dict[str, Any]] = []
    while time.monotonic() < deadline:
        try:
            event = output.get(timeout=min(1.0, max(0.1, deadline - time.monotonic())))
        except queue.Empty:
            continue
        if isinstance(event, BaseException):
            raise EvalError(f"WorkBuddy output reader failed: {event}") from event
        events.append(event)
        if event.get("type") == "result":
            return str(event.get("result") or ""), events
    raise EvalError("Timed out waiting for a WorkBuddy turn result")


def _read_log(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines()]


def run_eval(cli_path: Path) -> dict[str, Any]:
    node = shutil.which("node")
    if node is None:
        raise EvalError("Node.js is unavailable")
    if not cli_path.is_file():
        raise EvalError(f"WorkBuddy CLI was not found: {cli_path}")

    with tempfile.TemporaryDirectory(prefix="chaoxing-teacher-e2e-") as temporary:
        plugin = Path(temporary) / "chaoxing-teacher"
        shutil.copytree(SKILL, plugin)
        shutil.copy2(FAKE_RUNNER, plugin / "scripts" / "run.ps1")
        skill_md = plugin / "SKILL.md"
        skill_text = skill_md.read_text(encoding="utf-8")
        skill_md.write_text(
            skill_text.replace("name: chaoxing-teacher", "name: chaoxing-teacher-e2e", 1),
            encoding="utf-8",
        )

        command = [
            node,
            str(cli_path),
            "-p",
            "--input-format",
            "stream-json",
            "--output-format",
            "stream-json",
            "--permission-mode",
            "default",
            "--plugin-dir",
            str(plugin),
            "--no-session-persistence",
            "--max-turns",
            "30",
        ]
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            env={
                **os.environ,
                "PYTHONIOENCODING": "utf-8",
                "CHAOXING_EVAL_USERNAME": USERNAME,
                "CHAOXING_EVAL_PASSWORD": PASSWORD,
            },
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        assert process.stdout is not None
        output: queue.Queue[dict[str, Any] | BaseException] = queue.Queue()
        thread = threading.Thread(target=_reader, args=(process.stdout, output), daemon=True)
        thread.start()

        turns: list[str] = []
        try:
            _send(
                process,
                f"{TASK} 必须使用 chaoxing-teacher-e2e Skill；教师只提供目的、账号和密码。",
            )
            result, first_events = _wait_result(output)
            turns.append(result)
            if result.strip() != "请输入学习通账号。":
                calls = [
                    event for event in first_events if event.get("type") in {"assistant", "user"}
                ]
                raise EvalError(
                    json.dumps(
                        {"unexpected_account_prompt": result, "events": calls},
                        ensure_ascii=True,
                    )
                )

            _send(process, USERNAME)
            result, account_events = _wait_result(output)
            turns.append(result)
            if result.strip() != "请输入学习通密码。":
                raise EvalError(
                    json.dumps(
                        {
                            "unexpected_password_prompt": result,
                            "events": account_events,
                            "log": _read_log(plugin / "scripts" / ".eval-log.jsonl"),
                        },
                        ensure_ascii=True,
                    )
                )

            _send(process, PASSWORD)
            result, final_events = _wait_result(output, timeout=120.0)
            turns.append(result)
        finally:
            if process.stdin is not None:
                process.stdin.close()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=5)

        log = _read_log(plugin / "scripts" / ".eval-log.jsonl")
        login_values = next((item for item in log if item.get("operation") == "login_values"), None)
        completed = any(item.get("operation") == "original_task_completed" for item in log)
        permission_denials = [
            event
            for event in final_events
            if "Permission to use PowerShell has been denied" in json.dumps(event)
        ]
        checks = {
            "account_prompt_exact": turns[0].strip() == "请输入学习通账号。",
            "password_prompt_exact": turns[1].strip() == "请输入学习通密码。",
            "username_preserved": bool(login_values) and login_values.get("username") == USERNAME,
            "password_preserved": bool(login_values) and login_values.get("password") == PASSWORD,
            "original_task_resumed": completed,
            "observable_result_reported": "Unit 2 Argument Revision" in turns[2]
            and "3" in turns[2],
            "default_permission_passed": not permission_denials,
        }
        if not all(checks.values()):
            raise EvalError(
                json.dumps({"checks": checks, "turns": turns, "log": log}, ensure_ascii=False)
            )
        return {"status": "ok", "checks": checks, "turns": turns}


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--codebuddy-cli", type=Path, default=DEFAULT_CLI)
    args = parser.parse_args()
    try:
        result = run_eval(args.codebuddy_cli.resolve())
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=True, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
