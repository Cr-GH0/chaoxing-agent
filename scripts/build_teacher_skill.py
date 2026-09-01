from __future__ import annotations

import argparse
import hashlib
import json
import tomllib
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "chaoxing_agent"
SKILL = ROOT / "skills" / "chaoxing-teacher"
RUNTIME = SKILL / "scripts" / "runtime" / "chaoxing_teacher_runtime"
CORE_RUNTIME_FILES = (
    "__init__.py",
    "_aes.py",
    "api.py",
    "approval.py",
    "capabilities.py",
    "config.py",
    "models.py",
    "runtime.py",
)
FORBIDDEN_DISTRIBUTION_NAMES = {
    ".chaoxing_cookies.json",
    "cookies.json",
    "confirmations.json",
    "state.json",
    "mcp_server.py",
}
PYTHON_RUNTIME_VERSION = "3.13.15"
PYTHON_RUNTIME_PLATFORM = "windows-x64"
PYTHON_RUNTIME_FILENAME = f"python-{PYTHON_RUNTIME_VERSION}-embed-amd64.zip"
PYTHON_RUNTIME_URL = (
    f"https://www.python.org/ftp/python/{PYTHON_RUNTIME_VERSION}/{PYTHON_RUNTIME_FILENAME}"
)
PYTHON_RUNTIME_SHA256 = "d1f04d990aee1253d8569e8e5104e30fa9f5fa830899f14843448872d936a2cf"
PYTHON_RUNTIME_CACHE = ROOT / "build" / "runtime-cache" / PYTHON_RUNTIME_FILENAME
PYTHON_RUNTIME_PACKAGE_ROOT = "scripts/runtime/python-win-x64"
PYTHON_RUNTIME_REQUIRED_FILES = {
    "LICENSE.txt",
    "python.exe",
    "python313.dll",
    "python313.zip",
}


def _remove_between(text: str, start: str, end: str) -> str:
    start_index = text.index(start)
    end_index = text.index(end, start_index)
    return text[:start_index] + text[end_index:]


def _portable_cli() -> str:
    text = (SOURCE / "cli.py").read_text(encoding="utf-8")
    for line in ("import getpass\n", "import importlib.util\n", "import os\n"):
        text = text.replace(line, "", 1)
    text = text.replace(
        '        "mcp_installed": importlib.util.find_spec("mcp") is not None,\n',
        "",
        1,
    )
    text = text.replace(
        '        description="Agent-facing Chaoxing MCP and CLI runtime",',
        '        description="Agent-facing Chaoxing HTTP runtime",',
        1,
    )
    login_parser_start = (
        '    login = sub.add_parser("login", help="log in through HTTP and '
        'atomically save cookies")\n'
    )
    space_parser_start = (
        '    sub.add_parser("space-modules", help="discover current personal-space '
        'function entries")\n'
    )
    text = _remove_between(text, login_parser_start, space_parser_start)
    text = _remove_between(
        text,
        '    mcp_parser = sub.add_parser("mcp", help="run the MCP server")\n',
        "    return parser\n",
    )
    text = _remove_between(
        text,
        '    if args.command == "login":\n',
        '    if args.command == "space-modules":\n',
    )
    text = _remove_between(
        text,
        '    if args.command == "mcp":\n',
        "    try:\n",
    )
    return text


def _portable_router() -> str:
    text = (SOURCE / "router.py").read_text(encoding="utf-8")
    original = "请提供学习通账号和密码；CLI 会隐藏密码输入，MCP 也不会在结果中回显。"
    replacement = (
        "当前未登录；请先询问‘请输入学习通账号。’，收到后再询问"
        "‘请输入学习通密码。’，然后直接登录并继续原请求。"
    )
    if original not in text:
        raise RuntimeError("portable router login message source changed")
    return text.replace(original, replacement, 1)


def expected_runtime() -> dict[str, str]:
    result = {name: (SOURCE / name).read_text(encoding="utf-8") for name in CORE_RUNTIME_FILES}
    result["cli.py"] = _portable_cli()
    result["router.py"] = _portable_router()
    return result


def sync_runtime(*, check: bool) -> list[str]:
    mismatches: list[str] = []
    for name, expected in expected_runtime().items():
        destination = RUNTIME / name
        actual = destination.read_text(encoding="utf-8") if destination.exists() else ""
        if actual == expected:
            continue
        mismatches.append(name)
        if not check:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(expected, encoding="utf-8", newline="")
    unexpected = sorted(
        path.name
        for path in RUNTIME.iterdir()
        if path.is_file() and path.name not in expected_runtime()
    )
    if unexpected:
        mismatches.extend(f"unexpected:{name}" for name in unexpected)
    return mismatches


def _project_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        return str(tomllib.load(handle)["project"]["version"])


def _skill_files() -> list[Path]:
    files = [
        path
        for path in SKILL.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    ]
    for path in files:
        if path.name in FORBIDDEN_DISTRIBUTION_NAMES:
            raise RuntimeError(f"forbidden runtime data in distributable skill: {path}")
    return sorted(files, key=lambda path: path.relative_to(SKILL).as_posix())


def _write_zip_entry(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    executable = name.endswith("/bin/run-node") or name.endswith(".sh")
    info.external_attr = (0o100755 if executable else 0o100644) << 16
    archive.writestr(info, data)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ensure_python_runtime() -> Path:
    if (
        PYTHON_RUNTIME_CACHE.is_file()
        and _file_sha256(PYTHON_RUNTIME_CACHE) == PYTHON_RUNTIME_SHA256
    ):
        return PYTHON_RUNTIME_CACHE

    PYTHON_RUNTIME_CACHE.parent.mkdir(parents=True, exist_ok=True)
    partial = PYTHON_RUNTIME_CACHE.with_suffix(PYTHON_RUNTIME_CACHE.suffix + ".download")
    request = urllib.request.Request(
        PYTHON_RUNTIME_URL,
        headers={"User-Agent": "chaoxing-teacher-skill-builder/1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response, partial.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        actual = _file_sha256(partial)
        if actual != PYTHON_RUNTIME_SHA256:
            raise RuntimeError(
                "official Python runtime checksum mismatch: "
                f"expected {PYTHON_RUNTIME_SHA256}, got {actual}"
            )
        partial.replace(PYTHON_RUNTIME_CACHE)
    finally:
        partial.unlink(missing_ok=True)
    return PYTHON_RUNTIME_CACHE


def _write_python_runtime(
    archive: zipfile.ZipFile,
    *,
    prefix: str,
    runtime_archive: Path,
    expected_sha256: str,
) -> None:
    actual_sha256 = _file_sha256(runtime_archive)
    if actual_sha256 != expected_sha256:
        raise RuntimeError(
            f"Python runtime checksum mismatch: expected {expected_sha256}, got {actual_sha256}"
        )

    included: set[str] = set()
    with zipfile.ZipFile(runtime_archive) as runtime:
        for info in runtime.infolist():
            if info.is_dir():
                continue
            relative = PurePosixPath(info.filename)
            if relative.is_absolute() or ".." in relative.parts:
                raise RuntimeError(f"unsafe path in Python runtime archive: {info.filename}")
            name = relative.as_posix()
            included.add(name)
            _write_zip_entry(
                archive,
                f"{prefix}{PYTHON_RUNTIME_PACKAGE_ROOT}/{name}",
                runtime.read(info),
            )

    missing = sorted(PYTHON_RUNTIME_REQUIRED_FILES - included)
    if missing:
        raise RuntimeError(f"Python runtime archive is incomplete: {missing}")
    metadata = {
        "component": "CPython embeddable package",
        "version": PYTHON_RUNTIME_VERSION,
        "platform": PYTHON_RUNTIME_PLATFORM,
        "source": PYTHON_RUNTIME_URL,
        "sha256": PYTHON_RUNTIME_SHA256,
        "license": "PSF-2.0",
        "end_user_download_required": False,
    }
    _write_zip_entry(
        archive,
        f"{prefix}{PYTHON_RUNTIME_PACKAGE_ROOT}/SOURCE.json",
        (json.dumps(metadata, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )


def _write_skill_zip(
    destination: Path,
    prefix: str,
    *,
    runtime_archive: Path,
    expected_runtime_sha256: str,
) -> None:
    with zipfile.ZipFile(destination, "w") as archive:
        for path in _skill_files():
            relative = path.relative_to(SKILL).as_posix()
            _write_zip_entry(archive, f"{prefix}{relative}", path.read_bytes())
        _write_python_runtime(
            archive,
            prefix=prefix,
            runtime_archive=runtime_archive,
            expected_sha256=expected_runtime_sha256,
        )


def build_packages(
    output_dir: Path,
    *,
    python_runtime_archive: Path | None = None,
    expected_runtime_sha256: str = PYTHON_RUNTIME_SHA256,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    runtime_archive = python_runtime_archive or _ensure_python_runtime()
    version = _project_version()
    package = output_dir / f"学习通教师版-{version}.zip"

    _write_skill_zip(
        package,
        "chaoxing-teacher/",
        runtime_archive=runtime_archive,
        expected_runtime_sha256=expected_runtime_sha256,
    )
    packages = [package]
    current = {path.resolve() for path in packages}
    for existing in output_dir.glob("学习通教师版-*.zip"):
        if existing.resolve() not in current:
            existing.unlink()
    return packages


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()

    mismatches = sync_runtime(check=args.check)
    if args.check:
        if mismatches:
            print(json.dumps({"status": "out_of_sync", "files": mismatches}, ensure_ascii=False))
            return 1
        print(json.dumps({"status": "ok", "runtime": "in_sync"}, ensure_ascii=False))
        return 0
    packages = build_packages(args.output)
    print(
        json.dumps(
            {
                "status": "ok",
                "runtime_updated": mismatches,
                "packages": [str(path.resolve()) for path in packages],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
