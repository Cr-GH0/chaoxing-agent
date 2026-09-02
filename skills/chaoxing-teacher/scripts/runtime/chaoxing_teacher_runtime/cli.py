from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from .api import ChaoxingAPI, load_cookie_records
from .config import Settings
from .runtime import ActionRuntime, ActionRuntimeError


def _configure_output() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def _emit(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def _parse_json_list(value: str | None, label: str) -> list[Any] | None:
    if value is None:
        return None
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ActionRuntimeError(f"{label} must be a valid JSON array") from exc
    if not isinstance(decoded, list):
        raise ActionRuntimeError(f"{label} must be a JSON array")
    return decoded


def _parse_json_object(value: str | None, label: str) -> dict[str, Any] | None:
    if value is None:
        return None
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ActionRuntimeError(f"{label} must be a valid JSON object") from exc
    if not isinstance(decoded, dict):
        raise ActionRuntimeError(f"{label} must be a JSON object")
    return {str(key): item for key, item in decoded.items()}


def _parse_permission_changes(values: list[str]) -> dict[str, bool | int]:
    changes: dict[str, bool | int] = {}
    for item in values:
        if "=" not in item:
            raise ActionRuntimeError(f"permission change must use KEY=VALUE: {item}")
        key, raw_value = item.split("=", 1)
        key = key.strip()
        normalized = raw_value.strip().lower()
        if not key or not normalized:
            raise ActionRuntimeError(f"permission change must use KEY=VALUE: {item}")
        if normalized in {"true", "on", "yes", "1", "开启", "启用", "允许"}:
            value: bool | int = True
        elif normalized in {"false", "off", "no", "0", "关闭", "禁用", "不允许"}:
            value = False
        else:
            try:
                value = int(normalized)
            except ValueError as exc:
                raise ActionRuntimeError(
                    f"permission value must be true, false, or an integer: {raw_value}"
                ) from exc
        changes[key] = value
    return changes


def _doctor(settings: Settings, live: bool) -> dict[str, Any]:
    cookie_exists = bool(settings.cookie_file and settings.cookie_file.exists())
    cookie_count = 0
    cookie_error = ""
    if cookie_exists and settings.cookie_file:
        try:
            cookie_count = len(load_cookie_records(settings.cookie_file))
        except Exception as exc:  # reported as diagnostic data
            cookie_error = str(exc)
    result: dict[str, Any] = {
        "status": "ok" if cookie_exists and not cookie_error else "configuration_needed",
        "cookie_file_configured": settings.cookie_file is not None,
        "cookie_file_exists": cookie_exists,
        "cookie_count": cookie_count,
        "cookie_error": cookie_error,
        "confirmation_store_configured": settings.confirmation_file is not None,
        "state_store_configured": settings.state_file is not None,
        "runtime": "http_only",
    }
    if live and cookie_exists and settings.cookie_file:
        result["live_session"] = ChaoxingAPI(
            settings.cookie_file, settings.request_timeout
        ).check_session()
        if not result["live_session"]["logged_in"]:
            result["status"] = "login_required"
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chaoxing-agent",
        description="Agent-facing Chaoxing HTTP runtime",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="check local configuration and optional live login")
    doctor.add_argument("--live", action="store_true")

    sub.add_parser("capabilities", help="show capability coverage")
    sub.add_parser("session", help="check the configured Chaoxing session")
    sub.add_parser("space-modules", help="discover current personal-space function entries")
    space_module = sub.add_parser(
        "space-open", help="fetch one personal-space function through authenticated HTTP"
    )
    space_module.add_argument("module")

    sub.add_parser("job-ability-status", help="read public and private job-ability availability")
    job_search = sub.add_parser("job-search", help="search current recruitment job ads")
    job_search.add_argument("keyword")
    job_search.add_argument("--page", type=int, default=1)
    job_search.add_argument("--page-size", type=int, default=20)
    job_search.add_argument("--education", default="")
    job_read = sub.add_parser("job-read", help="read one current recruitment job ad")
    job_read.add_argument("job")
    job_read.add_argument("--search", default="")
    job_read.add_argument("--education", default="")
    job_popular = sub.add_parser("job-popular", help="list popular and high-salary jobs")
    job_popular.add_argument("--education", default="本科")
    occupation_catalog = sub.add_parser(
        "occupation-catalog", help="read the occupation encyclopedia summary"
    )
    occupation_catalog.add_argument("--education", default="本科")
    occupation_search = sub.add_parser(
        "occupation-search", help="search the occupation encyclopedia"
    )
    occupation_search.add_argument("keyword")
    occupation_search.add_argument("--education", default="本科")
    industry_types = sub.add_parser("industry-types", help="list job-ability industry types")
    industry_types.add_argument("--page", type=int, default=1)
    industry_types.add_argument("--page-size", type=int, default=100)
    industries = sub.add_parser("industries", help="list job categories under an industry type")
    industries.add_argument("industry_type")
    industries.add_argument("--education", default="本科")
    industries.add_argument("--page", type=int, default=1)
    industries.add_argument("--page-size", type=int, default=100)
    industry_jobs = sub.add_parser("industry-jobs", help="list standard jobs in one category")
    industry_jobs.add_argument("industry")
    industry_jobs.add_argument("--education", default="本科")
    industry_jobs.add_argument("--page", type=int, default=1)
    industry_jobs.add_argument("--page-size", type=int, default=100)

    subjects = sub.add_parser("subjects", help="list subjects and folders")
    subjects.add_argument("--folder", default="-1")
    subjects.add_argument("--search", default="")
    subjects.add_argument("--max-items", type=int, default=1000)
    subject_tree = sub.add_parser("subject-tree", help="read the complete subject folder tree")
    subject_tree.add_argument("--max-folders", type=int, default=1000)
    sub.add_parser("subject-create-status", help="check subject-creation eligibility")
    subject_folder_create = sub.add_parser("subject-folder-create", help="create a subject folder")
    subject_folder_create.add_argument("name")
    subject_folder_create.add_argument("--parent-folder", default="-1")
    subject_folder_rename = sub.add_parser("subject-folder-rename", help="rename a subject folder")
    subject_folder_rename.add_argument("folder")
    subject_folder_rename.add_argument("name")
    subject_folder_move = sub.add_parser("subject-folder-move", help="move a subject folder")
    subject_folder_move.add_argument("folder")
    subject_folder_move.add_argument("--target-folder", default="-1")
    subject_folder_delete = sub.add_parser(
        "subject-folder-delete", help="preview or confirm deleting a subject folder"
    )
    subject_folder_delete.add_argument("folder")
    subject_folder_delete.add_argument("--allow-nonempty", action="store_true")
    subject_folder_delete.add_argument("--confirmation-token")
    subject_publish = sub.add_parser(
        "subject-publish", help="preview or confirm publishing or unpublishing a subject"
    )
    subject_publish.add_argument("subject")
    subject_publish.add_argument("--off", action="store_true")
    subject_publish.add_argument("--confirmation-token")
    subject_move = sub.add_parser("subject-move", help="move a subject")
    subject_move.add_argument("subject")
    subject_move.add_argument("--target-folder", default="-1")
    subject_delete = sub.add_parser(
        "subject-delete", help="preview or confirm moving a subject to recycle"
    )
    subject_delete.add_argument("subject")
    subject_delete.add_argument("--confirmation-token")
    subject_recycle = sub.add_parser("subject-recycle", help="list recycled subjects")
    subject_recycle.add_argument("--search", default="")
    subject_recycle.add_argument("--max-items", type=int, default=1000)
    subject_restore = sub.add_parser("subject-restore", help="restore a recycled subject")
    subject_restore.add_argument("subject")
    subject_recycle_delete = sub.add_parser(
        "subject-recycle-delete", help="preview or confirm permanently deleting a subject"
    )
    subject_recycle_delete.add_argument("subject")
    subject_recycle_delete.add_argument("--confirmation-token")

    sub.add_parser("detection-channels", help="list similarity-check comparison libraries")
    detections = sub.add_parser("detections", help="list Daya detection records")
    detections.add_argument("type", choices=("similarity", "aigc", "comparison"))
    detections.add_argument("--page", type=int, default=1)
    detections.add_argument("--page-size", type=int, default=100)
    detections.add_argument("--status", type=int, default=-1)
    detections.add_argument("--begin-date", default="")
    detections.add_argument("--end-date", default="")
    detections.add_argument("--search", default="")
    detection_status = sub.add_parser("detection-status", help="read one detection status")
    detection_status.add_argument("type", choices=("similarity", "aigc", "comparison"))
    detection_status.add_argument("record")
    detection_submit = sub.add_parser(
        "detection-submit", help="preview or confirm a similarity or AIGC submission"
    )
    detection_submit.add_argument("type", choices=("similarity", "aigc"))
    detection_submit.add_argument("title")
    detection_submit.add_argument("--author", default="")
    input_group = detection_submit.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--content")
    input_group.add_argument("--file")
    detection_submit.add_argument("--end-year", default="")
    detection_submit.add_argument("--channel-id", dest="channel_ids", action="append")
    detection_submit.add_argument("--confirmation-token")
    detection_compare = sub.add_parser(
        "detection-compare", help="preview or confirm a two-file comparison"
    )
    detection_compare.add_argument("title_1")
    detection_compare.add_argument("file_1")
    detection_compare.add_argument("title_2")
    detection_compare.add_argument("file_2")
    detection_compare.add_argument("--confirmation-token")
    detection_payment = sub.add_parser(
        "detection-payment-status", help="read payment or free-entitlement status"
    )
    detection_payment.add_argument("type", choices=("similarity", "aigc", "comparison"))
    detection_payment.add_argument("record")
    detection_free = sub.add_parser(
        "detection-use-free", help="preview or confirm consuming a free detection entitlement"
    )
    detection_free.add_argument("type", choices=("similarity", "aigc", "comparison"))
    detection_free.add_argument("record")
    detection_free.add_argument("--confirmation-token")
    detection_report = sub.add_parser("detection-report", help="download a detection report")
    detection_report.add_argument("type", choices=("similarity", "aigc", "comparison"))
    detection_report.add_argument("record")
    detection_report.add_argument("output_path")
    detection_report.add_argument("--result-type", type=int, default=1)
    detection_report.add_argument("--timeout-seconds", type=float, default=300)
    detection_report.add_argument("--overwrite", action="store_true")
    detection_delete = sub.add_parser(
        "detection-delete", help="preview or confirm permanently deleting a detection record"
    )
    detection_delete.add_argument("type", choices=("similarity", "aigc", "comparison"))
    detection_delete.add_argument("record")
    detection_delete.add_argument("--confirmation-token")

    lives = sub.add_parser("lives", help="list personal live rooms")
    lives.add_argument("--search", default="")
    lives.add_argument("--start-time", default="")
    lives.add_argument("--end-time", default="")
    lives.add_argument("--sort-key", type=int, default=0)
    lives.add_argument("--sort-type", type=int, default=0)
    lives.add_argument("--max-items", type=int, default=1000)
    live_read = sub.add_parser("live-read", help="read a live room and its settings")
    live_read.add_argument("room")
    live_create = sub.add_parser("live-create", help="preview or confirm creating a live room")
    live_create.add_argument("title")
    live_create.add_argument("--scheduled-time", default="")
    live_create.add_argument("--introduction", default="")
    live_create.add_argument("--content-format", choices=("plain", "html"), default="plain")
    live_create.add_argument(
        "--mode", choices=("multi_device", "chaoxing_pc_client"), default="multi_device"
    )
    live_create.add_argument(
        "--chat-content-review",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    live_create.add_argument("--cover-object-id", default="")
    live_create.add_argument("--preview-video-object-id", default="")
    live_create.add_argument("--extends-info-json")
    live_create.add_argument("--confirmation-token")
    live_update = sub.add_parser("live-update", help="update a live room")
    live_update.add_argument("room")
    live_update.add_argument("--title")
    live_update.add_argument("--scheduled-time")
    live_update.add_argument("--introduction")
    live_update.add_argument("--content-format", choices=("plain", "html"), default="plain")
    live_update.add_argument("--cover-object-id")
    live_update.add_argument("--preview-video-object-id")
    live_settings = sub.add_parser(
        "live-settings", help="preview or confirm changing live-room settings"
    )
    live_settings.add_argument("room")
    for flag in (
        "comments-enabled",
        "forwarding-enabled",
        "replay-enabled",
        "learning-app-only",
        "chat-content-review",
        "login-required",
        "picture-live",
        "show-viewer-count",
        "reservations-enabled",
        "preupload-enabled",
    ):
        live_settings.add_argument(f"--{flag}", action=argparse.BooleanOptionalAction, default=None)
    live_settings.add_argument("--access-password")
    live_settings.add_argument("--allowed-unit-id", dest="allowed_unit_ids", action="append")
    live_settings.add_argument("--replay-start-offset-seconds", type=int)
    live_settings.add_argument("--confirmation-token")
    live_status = sub.add_parser("live-status", help="read a live room and stream status")
    live_status.add_argument("room")
    live_watch = sub.add_parser("live-watch", help="read a live watch URL and invitation code")
    live_watch.add_argument("room")
    live_stream = sub.add_parser(
        "live-stream-credentials", help="preview or confirm reading RTMP push credentials"
    )
    live_stream.add_argument("room")
    live_stream.add_argument("--confirmation-token")
    live_asset = sub.add_parser("live-asset-upload", help="upload a live cover or preview video")
    live_asset.add_argument("kind", choices=("cover", "preview_video"))
    live_asset.add_argument("file")
    live_asset.add_argument("--room", default="")
    live_export = sub.add_parser("live-export", help="queue a live-record export")
    live_export.add_argument("--search", default="")
    live_export.add_argument("--start-time", default="")
    live_export.add_argument("--end-time", default="")
    live_export.add_argument("--sort-key", type=int, default=0)
    live_export.add_argument("--sort-type", type=int, default=0)
    sub.add_parser("live-units", help="list units available for live access restrictions")
    live_delete = sub.add_parser(
        "live-delete", help="preview or confirm moving a live room to recycle"
    )
    live_delete.add_argument("room")
    live_delete.add_argument("--confirmation-token")
    live_recycle = sub.add_parser("live-recycle", help="list recycled live rooms")
    live_recycle.add_argument("--search", default="")
    live_recycle.add_argument("--max-items", type=int, default=1000)
    live_restore = sub.add_parser("live-restore", help="restore a recycled live room")
    live_restore.add_argument("room")
    live_recycle_delete = sub.add_parser(
        "live-recycle-delete", help="preview or confirm permanently deleting a live room"
    )
    live_recycle_delete.add_argument("room")
    live_recycle_delete.add_argument("--confirmation-token")
    live_themes = sub.add_parser("live-themes", help="list themed live entries")
    live_themes.add_argument("--search", default="")
    live_themes.add_argument("--max-items", type=int, default=1000)
    live_theme_read = sub.add_parser("live-theme-read", help="read one live theme")
    live_theme_read.add_argument("theme")
    live_theme_read.add_argument("--max-rooms", type=int, default=1000)
    live_theme_create = sub.add_parser(
        "live-theme-create", help="preview or confirm creating a live theme"
    )
    live_theme_create.add_argument("name")
    live_theme_create.add_argument("--description", default="")
    live_theme_create.add_argument("--confirmation-token")
    live_theme_update = sub.add_parser("live-theme-update", help="update a live theme")
    live_theme_update.add_argument("theme")
    live_theme_update.add_argument("--name")
    live_theme_update.add_argument("--description")
    live_theme_settings = sub.add_parser(
        "live-theme-settings", help="preview or confirm changing live-theme settings"
    )
    live_theme_settings.add_argument("theme")
    for flag in (
        "forwarding-enabled",
        "replay-enabled",
        "learning-app-only",
        "login-required",
    ):
        live_theme_settings.add_argument(
            f"--{flag}", action=argparse.BooleanOptionalAction, default=None
        )
    live_theme_settings.add_argument("--allowed-unit-id", dest="allowed_unit_ids", action="append")
    live_theme_settings.add_argument("--confirmation-token")
    live_theme_add = sub.add_parser(
        "live-theme-add-room", help="preview or confirm adding a room to a live theme"
    )
    live_theme_add.add_argument("theme")
    live_theme_add.add_argument("room")
    live_theme_add.add_argument("--confirmation-token")
    live_theme_room_create = sub.add_parser(
        "live-theme-create-room", help="preview or confirm creating a room in a live theme"
    )
    live_theme_room_create.add_argument("theme")
    live_theme_room_create.add_argument("title")
    live_theme_room_create.add_argument("--scheduled-time", default="")
    live_theme_room_create.add_argument("--introduction", default="")
    live_theme_room_create.add_argument(
        "--content-format", choices=("plain", "html"), default="plain"
    )
    live_theme_room_create.add_argument(
        "--mode", choices=("multi_device", "chaoxing_pc_client"), default="multi_device"
    )
    live_theme_room_create.add_argument(
        "--chat-content-review",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    live_theme_room_create.add_argument("--cover-object-id", default="")
    live_theme_room_create.add_argument("--preview-video-object-id", default="")
    live_theme_room_create.add_argument("--confirmation-token")
    live_theme_delete = sub.add_parser(
        "live-theme-delete", help="preview or confirm deleting a live theme"
    )
    live_theme_delete.add_argument("theme")
    live_theme_delete.add_argument("--confirmation-token")

    notes = sub.add_parser("notes", help="list or search personal notes")
    notes.add_argument("--search", default="")
    notes.add_argument("--max-items", type=int, default=1000)

    note_read = sub.add_parser("note-read", help="read one personal note")
    note_read.add_argument("note")

    note_create = sub.add_parser("note-create", help="create a private personal note")
    note_create.add_argument("title")
    note_create.add_argument("--content", default="")
    note_create.add_argument("--content-format", choices=("plain", "html"), default="plain")
    note_create.add_argument("--notebook-cid", default="root")

    note_update = sub.add_parser("note-update", help="update one personal note")
    note_update.add_argument("note")
    note_update.add_argument("--title")
    note_update.add_argument("--content")
    note_update.add_argument("--content-format", choices=("plain", "html"), default="plain")

    note_delete = sub.add_parser("note-delete", help="preview or confirm deleting a note")
    note_delete.add_argument("note")
    note_delete.add_argument("--confirmation-token")

    inbox = sub.add_parser("inbox", help="list or search received or sent inbox notices")
    inbox.add_argument("--scope", choices=("received", "sent"), default="received")
    inbox.add_argument("--search", default="")
    inbox.add_argument("--sender", default="")
    inbox.add_argument("--start-time", default="")
    inbox.add_argument("--end-time", default="")
    inbox.add_argument("--max-items", type=int, default=1000)

    inbox_read = sub.add_parser("inbox-read", help="read one full inbox notice")
    inbox_read.add_argument("notice")
    inbox_read.add_argument("--scope", choices=("received", "sent"), default="received")

    inbox_unread = sub.add_parser("inbox-unread", help="mark one received notice unread")
    inbox_unread.add_argument("notice")

    inbox_top = sub.add_parser("inbox-top", help="set or clear inbox notice top status")
    inbox_top.add_argument("notice")
    inbox_top.add_argument("--scope", choices=("received", "sent"), default="received")
    inbox_top.add_argument("--off", action="store_true")

    inbox_collect = sub.add_parser("inbox-collect", help="collect or uncollect one inbox notice")
    inbox_collect.add_argument("notice")
    inbox_collect.add_argument("--scope", choices=("received", "sent"), default="received")
    inbox_collect.add_argument("--off", action="store_true")

    inbox_delete = sub.add_parser(
        "inbox-delete", help="preview or confirm deleting one inbox notice"
    )
    inbox_delete.add_argument("notice")
    inbox_delete.add_argument("--scope", choices=("received", "sent"), default="received")
    inbox_delete.add_argument("--confirmation-token")

    inbox_send = sub.add_parser("inbox-send", help="preview or confirm sending a personal notice")
    inbox_send.add_argument("title")
    inbox_send.add_argument("content")
    inbox_send.add_argument("--recipient", dest="recipients", action="append", required=True)
    inbox_send.add_argument("--content-format", choices=("plain", "html"), default="plain")
    inbox_send.add_argument("--forbid-comments", action="store_true")
    inbox_send.add_argument("--hide-comments", action="store_true")
    inbox_send.add_argument("--hide-read-status", action="store_true")
    inbox_send.add_argument("--forbid-forwarding", action="store_true")
    inbox_send.add_argument("--permission-password", default="")
    inbox_send.add_argument("--confirmation-token")

    inbox_drafts = sub.add_parser("inbox-drafts", help="list personal notice drafts")
    inbox_drafts.add_argument("--search", default="")
    inbox_drafts.add_argument("--max-items", type=int, default=1000)

    inbox_draft_save = sub.add_parser(
        "inbox-draft-save", help="create or update a personal notice draft"
    )
    inbox_draft_save.add_argument("title")
    inbox_draft_save.add_argument("content")
    inbox_draft_save.add_argument("--draft", default="")
    inbox_draft_save.add_argument("--recipient", dest="recipients", action="append")
    inbox_draft_save.add_argument("--content-format", choices=("plain", "html"), default="plain")
    inbox_draft_save.add_argument("--forbid-comments", action="store_true")
    inbox_draft_save.add_argument("--hide-comments", action="store_true")
    inbox_draft_save.add_argument("--hide-read-status", action="store_true")
    inbox_draft_save.add_argument("--forbid-forwarding", action="store_true")

    inbox_draft_delete = sub.add_parser(
        "inbox-draft-delete", help="preview or confirm deleting a personal notice draft"
    )
    inbox_draft_delete.add_argument("draft")
    inbox_draft_delete.add_argument("--confirmation-token")

    sub.add_parser("inbox-folders", help="list personal inbox folders")

    inbox_folder_rules = sub.add_parser(
        "inbox-folder-rules", help="read sender and keyword rules for one inbox folder"
    )
    inbox_folder_rules.add_argument("folder")

    inbox_folder_notices = sub.add_parser(
        "inbox-folder-notices", help="list or search notices in one inbox folder"
    )
    inbox_folder_notices.add_argument("folder")
    inbox_folder_notices.add_argument("--scope", choices=("received", "sent"), default="received")
    inbox_folder_notices.add_argument("--search", default="")
    inbox_folder_notices.add_argument("--sender", default="")
    inbox_folder_notices.add_argument("--start-time", default="")
    inbox_folder_notices.add_argument("--end-time", default="")
    inbox_folder_notices.add_argument("--max-items", type=int, default=1000)

    inbox_folder_create = sub.add_parser(
        "inbox-folder-create", help="create a personal inbox folder"
    )
    inbox_folder_create.add_argument("name")
    inbox_folder_create.add_argument("--sender-rules-json")
    inbox_folder_create.add_argument("--keywords-json")

    inbox_folder_update = sub.add_parser(
        "inbox-folder-update", help="rename or replace rules for one inbox folder"
    )
    inbox_folder_update.add_argument("folder")
    inbox_folder_update.add_argument("--name")
    inbox_folder_update.add_argument("--sender-rules-json")
    inbox_folder_update.add_argument("--keywords-json")

    inbox_folder_delete = sub.add_parser(
        "inbox-folder-delete", help="preview or confirm deleting one inbox folder"
    )
    inbox_folder_delete.add_argument("folder")
    inbox_folder_delete.add_argument("--confirmation-token")

    inbox_folder_reorder = sub.add_parser(
        "inbox-folder-reorder", help="submit the complete order of one inbox folder group"
    )
    inbox_folder_reorder.add_argument("folders", nargs="+")
    inbox_folder_reorder.add_argument("--top", action="store_true")

    inbox_move = sub.add_parser(
        "inbox-move", help="move inbox notices to a folder or the inbox root"
    )
    inbox_move.add_argument("destination_folder")
    inbox_move.add_argument("notices", nargs="+")
    inbox_move.add_argument("--scope", choices=("received", "sent"), default="received")
    inbox_move.add_argument("--source-folder", default="")

    inbox_recycle = sub.add_parser("inbox-recycle", help="list personal inbox recycle notices")
    inbox_recycle.add_argument("--search", default="")
    inbox_recycle.add_argument("--max-items", type=int, default=1000)

    inbox_recycle_restore = sub.add_parser(
        "inbox-recycle-restore", help="restore notices from the personal inbox recycle bin"
    )
    inbox_recycle_restore.add_argument("notices", nargs="+")

    inbox_recycle_delete = sub.add_parser(
        "inbox-recycle-delete",
        help="preview or confirm permanently deleting personal inbox recycle notices",
    )
    inbox_recycle_delete.add_argument("notices", nargs="+")
    inbox_recycle_delete.add_argument("--confirmation-token")

    inbox_recycle_empty = sub.add_parser(
        "inbox-recycle-empty", help="preview or confirm emptying personal inbox recycle"
    )
    inbox_recycle_empty.add_argument("--confirmation-token")

    sub.add_parser("contact-units", help="list visible address-book units")

    contact_departments = sub.add_parser(
        "contact-departments", help="list child address-book departments"
    )
    contact_departments.add_argument("fid")
    contact_departments.add_argument("--parent-id", default="2C89C38F937992D2")
    contact_departments.add_argument(
        "--department-type", choices=("unit", "custom"), default="unit"
    )

    contact_department_members = sub.add_parser(
        "contact-department-members", help="list address-book department members"
    )
    contact_department_members.add_argument("fid")
    contact_department_members.add_argument("department_id")
    contact_department_members.add_argument("--search", default="")
    contact_department_members.add_argument("--max-items", type=int, default=1000)

    contact_search = sub.add_parser("contact-search", help="search visible address-book people")
    contact_search.add_argument("search")
    contact_search.add_argument("--fid", default="")
    contact_search.add_argument("--department-id", default="")
    contact_search.add_argument("--mode", type=int, default=-1)
    contact_search.add_argument("--max-items", type=int, default=300)

    contact_relations = sub.add_parser("contacts", help="list followers or followed people")
    contact_relations.add_argument(
        "--relation", choices=("followers", "following"), default="followers"
    )
    contact_relations.add_argument("--max-items", type=int, default=1000)

    contact_groups = sub.add_parser("contact-groups", help="list joined groups")
    contact_groups.add_argument("--search", default="")

    contact_group_members = sub.add_parser(
        "contact-group-members", help="list members of one joined group"
    )
    contact_group_members.add_argument("group")
    contact_group_members.add_argument("--search", default="")
    contact_group_members.add_argument("--max-items", type=int, default=1000)

    contact_chatgroups = sub.add_parser("contact-chatgroups", help="list joined chat groups")
    contact_chatgroups.add_argument("--max-items", type=int, default=1000)

    contact_chatgroup_members = sub.add_parser(
        "contact-chatgroup-members", help="list members of one chat group"
    )
    contact_chatgroup_members.add_argument("chatgroup")
    contact_chatgroup_members.add_argument("--max-items", type=int, default=1000)

    sub.add_parser("contact-teams", help="list custom address-book teams")

    contact_team_members = sub.add_parser(
        "contact-team-members", help="list members of one custom team"
    )
    contact_team_members.add_argument("team")
    contact_team_members.add_argument("--max-items", type=int, default=1000)

    contact_follow = sub.add_parser(
        "contact-follow", help="preview or confirm following or unfollowing a person"
    )
    contact_follow.add_argument("person")
    contact_follow.add_argument("--off", action="store_true")
    contact_follow.add_argument("--confirmation-token")

    contact_team_create = sub.add_parser(
        "contact-team-create", help="preview or confirm creating a custom contact team"
    )
    contact_team_create.add_argument("name")
    contact_team_create.add_argument("members", nargs="+")
    contact_team_create.add_argument("--confirmation-token")

    contact_team_rename = sub.add_parser(
        "contact-team-rename", help="preview or confirm renaming a custom contact team"
    )
    contact_team_rename.add_argument("team")
    contact_team_rename.add_argument("name")
    contact_team_rename.add_argument("--confirmation-token")

    contact_team_add = sub.add_parser(
        "contact-team-add", help="preview or confirm adding custom-team members"
    )
    contact_team_add.add_argument("team")
    contact_team_add.add_argument("members", nargs="+")
    contact_team_add.add_argument("--confirmation-token")

    contact_team_remove = sub.add_parser(
        "contact-team-remove", help="preview or confirm removing one custom-team member"
    )
    contact_team_remove.add_argument("team")
    contact_team_remove.add_argument("member")
    contact_team_remove.add_argument("--confirmation-token")

    contact_team_delete = sub.add_parser(
        "contact-team-delete", help="preview or confirm deleting a custom contact team"
    )
    contact_team_delete.add_argument("team")
    contact_team_delete.add_argument("--confirmation-token")

    contact_team_exit = sub.add_parser(
        "contact-team-exit", help="preview or confirm exiting a custom contact team"
    )
    contact_team_exit.add_argument("team")
    contact_team_exit.add_argument("--confirmation-token")

    personal_groups = sub.add_parser("groups", help="list or search personal groups")
    personal_groups.add_argument("--folder", default="")
    personal_groups.add_argument("--search", default="")

    personal_group_read = sub.add_parser("group-read", help="read one personal group")
    personal_group_read.add_argument("group")

    personal_group_create = sub.add_parser(
        "group-create", help="preview or confirm creating a shared personal group"
    )
    personal_group_create.add_argument("name")
    personal_group_create.add_argument("--description", default="")
    personal_group_create.add_argument("--folder", default="")
    personal_group_create.add_argument("--logo-url", default="")
    personal_group_create.add_argument("--confirmation-token")

    personal_group_update = sub.add_parser(
        "group-update", help="preview or confirm updating personal group information"
    )
    personal_group_update.add_argument("group")
    personal_group_update.add_argument("--name")
    personal_group_update.add_argument("--description")
    personal_group_update.add_argument("--confirmation-token")

    personal_group_logo_update = sub.add_parser(
        "group-logo-update", help="preview or confirm uploading a personal group logo"
    )
    personal_group_logo_update.add_argument("group")
    personal_group_logo_update.add_argument("file")
    personal_group_logo_update.add_argument("--confirmation-token")

    personal_group_modules = sub.add_parser(
        "group-modules", help="list personal group module configuration"
    )
    personal_group_modules.add_argument("group")

    personal_group_modules_update = sub.add_parser(
        "group-modules-update",
        help="preview or confirm setting enabled personal group module type IDs",
    )
    personal_group_modules_update.add_argument("group")
    personal_group_modules_update.add_argument("enabled_type_ids", nargs="*")
    personal_group_modules_update.add_argument("--confirmation-token")

    personal_group_settings_update = sub.add_parser(
        "group-settings-update", help="preview or confirm changing personal group settings"
    )
    personal_group_settings_update.add_argument("group")
    personal_group_settings_update.add_argument(
        "--set",
        dest="setting_changes",
        action="append",
        default=[],
        metavar="KEY=VALUE",
    )
    personal_group_settings_update.add_argument("--sign-ban-start-time", type=int)
    personal_group_settings_update.add_argument("--confirmation-token")

    personal_group_levels = sub.add_parser(
        "group-levels", help="list personal group level titles and thresholds"
    )
    personal_group_levels.add_argument("group")

    personal_group_level_series = sub.add_parser(
        "group-level-series", help="preview or confirm switching a personal group level series"
    )
    personal_group_level_series.add_argument("group")
    personal_group_level_series.add_argument("series", choices=("default", "custom"))
    personal_group_level_series.add_argument("--confirmation-token")

    personal_group_levels_custom = sub.add_parser(
        "group-levels-custom",
        help="preview or confirm saving all 15 custom personal group levels",
    )
    personal_group_levels_custom.add_argument("group")
    personal_group_levels_custom.add_argument("levels_json")
    personal_group_levels_custom.add_argument("--confirmation-token")

    personal_group_growth_rules = sub.add_parser(
        "group-growth-rules", help="list personal group growth-value rules"
    )
    personal_group_growth_rules.add_argument("group")

    personal_group_growth_rule_series = sub.add_parser(
        "group-growth-rule-series",
        help="preview or confirm switching a personal group growth-rule series",
    )
    personal_group_growth_rule_series.add_argument("group")
    personal_group_growth_rule_series.add_argument("series", choices=("default", "custom"))
    personal_group_growth_rule_series.add_argument("--confirmation-token")

    personal_group_growth_rules_update = sub.add_parser(
        "group-growth-rules-update",
        help="preview or confirm changing personal group growth-value rules",
    )
    personal_group_growth_rules_update.add_argument("group")
    personal_group_growth_rules_update.add_argument(
        "--set",
        dest="growth_rule_changes",
        action="append",
        default=[],
        metavar="TYPE=VALUE",
    )
    personal_group_growth_rules_update.add_argument("--confirmation-token")

    personal_group_speaking_rules = sub.add_parser(
        "group-speaking-rules-update",
        help="preview or confirm changing personal group speaking rules",
    )
    personal_group_speaking_rules.add_argument("group")
    personal_group_speaking_rules.add_argument(
        "--set",
        dest="rule_changes",
        action="append",
        default=[],
        metavar="KEY=VALUE",
    )
    personal_group_speaking_rules.add_argument("--attachment-rules")
    personal_group_speaking_rules.add_argument("--confirmation-token")

    personal_group_notice_send = sub.add_parser(
        "group-notice-send", help="preview or confirm sending a personal group notice"
    )
    personal_group_notice_send.add_argument("group")
    personal_group_notice_send.add_argument("title")
    personal_group_notice_send.add_argument("content")
    personal_group_notice_send.add_argument("--pcode", default="")
    personal_group_notice_send.add_argument("--confirmation-token")

    personal_group_review_reminders = sub.add_parser(
        "group-review-reminders", help="list personal group review reminders and reviewers"
    )
    personal_group_review_reminders.add_argument("group")

    personal_group_review_reminder_create = sub.add_parser(
        "group-review-reminder-create",
        help="preview or confirm creating a personal group review reminder",
    )
    personal_group_review_reminder_create.add_argument("group")
    personal_group_review_reminder_create.add_argument("start_time")
    personal_group_review_reminder_create.add_argument("end_time")
    personal_group_review_reminder_create.add_argument("weeks", nargs="+")
    personal_group_review_reminder_create.add_argument(
        "--puid", dest="puids", action="append", required=True
    )
    personal_group_review_reminder_create.add_argument("--confirmation-token")

    personal_group_review_reminder_update = sub.add_parser(
        "group-review-reminder-update",
        help="preview or confirm updating a personal group review reminder",
    )
    personal_group_review_reminder_update.add_argument("group")
    personal_group_review_reminder_update.add_argument("reminder")
    personal_group_review_reminder_update.add_argument("--start-time")
    personal_group_review_reminder_update.add_argument("--end-time")
    personal_group_review_reminder_update.add_argument("--week", dest="weeks", action="append")
    personal_group_review_reminder_update.add_argument("--puid", dest="puids", action="append")
    personal_group_review_reminder_update.add_argument("--confirmation-token")

    personal_group_review_reminders_delete = sub.add_parser(
        "group-review-reminders-delete",
        help="preview or confirm deleting personal group review reminders",
    )
    personal_group_review_reminders_delete.add_argument("group")
    personal_group_review_reminders_delete.add_argument("reminders", nargs="+")
    personal_group_review_reminders_delete.add_argument("--confirmation-token")

    personal_group_labels = sub.add_parser("group-labels", help="list personal group labels")
    personal_group_labels.add_argument("group")

    personal_group_label_create = sub.add_parser(
        "group-label-create", help="create a personal group label"
    )
    personal_group_label_create.add_argument("group")
    personal_group_label_create.add_argument("name")

    personal_group_label_rename = sub.add_parser(
        "group-label-rename", help="rename a personal group label"
    )
    personal_group_label_rename.add_argument("group")
    personal_group_label_rename.add_argument("label")
    personal_group_label_rename.add_argument("name")

    personal_group_labels_reorder = sub.add_parser(
        "group-labels-reorder", help="set the full personal group label order"
    )
    personal_group_labels_reorder.add_argument("group")
    personal_group_labels_reorder.add_argument("labels", nargs="+")

    personal_group_labels_delete = sub.add_parser(
        "group-labels-delete", help="preview or confirm deleting personal group labels"
    )
    personal_group_labels_delete.add_argument("group")
    personal_group_labels_delete.add_argument("labels", nargs="+")
    personal_group_labels_delete.add_argument("--confirmation-token")

    personal_group_deletion_reasons = sub.add_parser(
        "group-deletion-reasons", help="list personal group deletion reasons"
    )
    personal_group_deletion_reasons.add_argument("group")

    personal_group_deletion_reason_create = sub.add_parser(
        "group-deletion-reason-create", help="create a personal group deletion reason"
    )
    personal_group_deletion_reason_create.add_argument("group")
    personal_group_deletion_reason_create.add_argument("name")

    personal_group_deletion_reason_rename = sub.add_parser(
        "group-deletion-reason-rename", help="rename a personal group deletion reason"
    )
    personal_group_deletion_reason_rename.add_argument("group")
    personal_group_deletion_reason_rename.add_argument("reason")
    personal_group_deletion_reason_rename.add_argument("name")

    personal_group_deletion_reasons_delete = sub.add_parser(
        "group-deletion-reasons-delete",
        help="preview or confirm deleting personal group deletion reasons",
    )
    personal_group_deletion_reasons_delete.add_argument("group")
    personal_group_deletion_reasons_delete.add_argument("reasons", nargs="+")
    personal_group_deletion_reasons_delete.add_argument("--confirmation-token")

    personal_group_recycle = sub.add_parser(
        "group-recycle", help="list personal group recycle items"
    )
    personal_group_recycle.add_argument("group")

    personal_group_recycle_restore = sub.add_parser(
        "group-recycle-restore", help="restore personal group recycle items"
    )
    personal_group_recycle_restore.add_argument("group")
    personal_group_recycle_restore.add_argument("items", nargs="+")

    personal_group_recycle_delete = sub.add_parser(
        "group-recycle-delete",
        help="preview or confirm permanently deleting personal group recycle items",
    )
    personal_group_recycle_delete.add_argument("group")
    personal_group_recycle_delete.add_argument("items", nargs="+")
    personal_group_recycle_delete.add_argument("--confirmation-token")

    personal_group_recycle_empty = sub.add_parser(
        "group-recycle-empty", help="preview or confirm emptying a personal group recycle bin"
    )
    personal_group_recycle_empty.add_argument("group")
    personal_group_recycle_empty.add_argument("--confirmation-token")

    personal_group_exports = sub.add_parser("group-exports", help="list personal group export jobs")
    personal_group_exports.add_argument("group")

    personal_group_member_export = sub.add_parser(
        "group-member-export", help="create a personal group member-list export"
    )
    personal_group_member_export.add_argument("group")

    personal_group_export_download = sub.add_parser(
        "group-export-download", help="download a ready personal group export"
    )
    personal_group_export_download.add_argument("group")
    personal_group_export_download.add_argument("export")
    personal_group_export_download.add_argument("output_path")
    personal_group_export_download.add_argument("--overwrite", action="store_true")
    personal_group_export_download.add_argument("--wait-seconds", type=int, default=120)

    personal_group_export_wait = sub.add_parser(
        "group-export-wait", help="wait for a personal group export to finish"
    )
    personal_group_export_wait.add_argument("group")
    personal_group_export_wait.add_argument("export")
    personal_group_export_wait.add_argument("--timeout-seconds", type=int, default=120)
    personal_group_export_wait.add_argument("--poll-seconds", type=int, default=2)

    personal_group_export_retry = sub.add_parser(
        "group-export-retry", help="retry a failed personal group export"
    )
    personal_group_export_retry.add_argument("group")
    personal_group_export_retry.add_argument("export")

    personal_group_export_cancel = sub.add_parser(
        "group-export-cancel", help="preview or confirm cancelling a group export"
    )
    personal_group_export_cancel.add_argument("group")
    personal_group_export_cancel.add_argument("export")
    personal_group_export_cancel.add_argument("--confirmation-token")

    personal_group_activities = sub.add_parser(
        "group-activities", help="list personal group activities"
    )
    personal_group_activities.add_argument("group")
    personal_group_activities.add_argument(
        "--status", choices=("all", "online", "offline"), default="all"
    )
    personal_group_activities.add_argument("--max-items", type=int, default=1000)

    personal_group_activity_image_upload = sub.add_parser(
        "group-activity-image-upload", help="upload a personal group activity image"
    )
    personal_group_activity_image_upload.add_argument("file")

    personal_group_activity_create = sub.add_parser(
        "group-activity-create", help="preview or confirm creating a personal group activity"
    )
    personal_group_activity_create.add_argument("group")
    personal_group_activity_create.add_argument("title")
    personal_group_activity_create.add_argument("--online", action="store_true")
    personal_group_activity_create.add_argument("--app-link", default="")
    personal_group_activity_create.add_argument("--pc-link", default="")
    personal_group_activity_create.add_argument("--app-image-url", default="")
    personal_group_activity_create.add_argument("--pc-image-url", default="")
    personal_group_activity_create.add_argument("--app-image-width", type=int, default=0)
    personal_group_activity_create.add_argument("--app-image-height", type=int, default=0)
    personal_group_activity_create.add_argument("--pc-image-width", type=int, default=0)
    personal_group_activity_create.add_argument("--pc-image-height", type=int, default=0)
    personal_group_activity_create.add_argument("--confirmation-token")

    personal_group_activity_update = sub.add_parser(
        "group-activity-update", help="preview or confirm updating a personal group activity"
    )
    personal_group_activity_update.add_argument("group")
    personal_group_activity_update.add_argument("activity")
    personal_group_activity_update.add_argument("--title")
    personal_group_activity_update.add_argument("--app-link")
    personal_group_activity_update.add_argument("--pc-link")
    personal_group_activity_update.add_argument("--app-image-url")
    personal_group_activity_update.add_argument("--pc-image-url")
    personal_group_activity_update.add_argument("--app-image-width", type=int)
    personal_group_activity_update.add_argument("--app-image-height", type=int)
    personal_group_activity_update.add_argument("--pc-image-width", type=int)
    personal_group_activity_update.add_argument("--pc-image-height", type=int)
    personal_group_activity_update.add_argument("--confirmation-token")

    personal_group_activity_status = sub.add_parser(
        "group-activity-status",
        help="preview or confirm putting a personal group activity online or offline",
    )
    personal_group_activity_status.add_argument("group")
    personal_group_activity_status.add_argument("activity")
    personal_group_activity_status.add_argument("status", choices=("online", "offline"))
    personal_group_activity_status.add_argument("--confirmation-token")

    personal_group_activities_reorder = sub.add_parser(
        "group-activities-reorder",
        help="preview or confirm the complete online personal group activity order",
    )
    personal_group_activities_reorder.add_argument("group")
    personal_group_activities_reorder.add_argument("activities", nargs="+")
    personal_group_activities_reorder.add_argument("--confirmation-token")

    personal_group_activity_delete = sub.add_parser(
        "group-activity-delete", help="preview or confirm deleting a personal group activity"
    )
    personal_group_activity_delete.add_argument("group")
    personal_group_activity_delete.add_argument("activity")
    personal_group_activity_delete.add_argument("--confirmation-token")

    personal_group_top = sub.add_parser("group-top", help="set personal group top status")
    personal_group_top.add_argument("group")
    personal_group_top.add_argument("--off", action="store_true")

    personal_group_move = sub.add_parser("group-move", help="move a personal group to a folder")
    personal_group_move.add_argument("group")
    personal_group_move.add_argument("destination_folder")

    personal_group_quit = sub.add_parser(
        "group-quit", help="preview or confirm quitting a personal group"
    )
    personal_group_quit.add_argument("group")
    personal_group_quit.add_argument("--confirmation-token")

    personal_group_dismiss = sub.add_parser(
        "group-dismiss", help="preview or confirm dismissing a personal group you created"
    )
    personal_group_dismiss.add_argument("group")
    personal_group_dismiss.add_argument("--confirmation-token")

    personal_group_members = sub.add_parser(
        "group-members", help="list or search members of a personal group"
    )
    personal_group_members.add_argument("group")
    personal_group_members.add_argument("--search", default="")

    personal_group_bulk_import_status = sub.add_parser(
        "group-member-bulk-import-status",
        help="read personal group bulk-member-import availability and quota",
    )
    personal_group_bulk_import_status.add_argument("group")

    personal_group_bulk_import_template = sub.add_parser(
        "group-member-bulk-import-template",
        help="download and verify the personal group bulk-member-import XLSX template",
    )
    personal_group_bulk_import_template.add_argument("group")
    personal_group_bulk_import_template.add_argument("output_path")
    personal_group_bulk_import_template.add_argument("--overwrite", action="store_true")

    personal_group_bulk_import = sub.add_parser(
        "group-members-bulk-import",
        help="preview or confirm bulk importing personal group members from XLSX",
    )
    personal_group_bulk_import.add_argument("group")
    personal_group_bulk_import.add_argument("file")
    personal_group_bulk_import.add_argument("--confirmation-token")

    personal_group_member_read = sub.add_parser(
        "group-member-read", help="read one personal group member"
    )
    personal_group_member_read.add_argument("group")
    personal_group_member_read.add_argument("member")

    personal_group_member_permissions_read = sub.add_parser(
        "group-member-permissions",
        help="read one personal group manager's delegated permissions",
    )
    personal_group_member_permissions_read.add_argument("group")
    personal_group_member_permissions_read.add_argument("member")

    personal_group_member_permissions_update = sub.add_parser(
        "group-member-permissions-update",
        help="preview or confirm changing one personal group manager's permissions",
    )
    personal_group_member_permissions_update.add_argument("group")
    personal_group_member_permissions_update.add_argument("member")
    personal_group_member_permissions_update.add_argument(
        "--set",
        dest="permission_changes",
        action="append",
        default=[],
        metavar="KEY=VALUE",
    )
    personal_group_member_permissions_update.add_argument("--confirmation-token")

    personal_group_member_sources = sub.add_parser(
        "group-member-sources", help="list sources for adding personal group members"
    )
    personal_group_member_sources.add_argument("group")

    personal_group_member_candidates = sub.add_parser(
        "group-member-candidates", help="list candidates from a group or unit source"
    )
    personal_group_member_candidates.add_argument("group")
    personal_group_member_candidates.add_argument(
        "source_type", choices=("circle", "unit", "ibuild")
    )
    personal_group_member_candidates.add_argument("source")
    personal_group_member_candidates.add_argument("--fid", default="")
    personal_group_member_candidates.add_argument("--search", default="")
    personal_group_member_candidates.add_argument(
        "--account-type", type=int, choices=(0, 1), default=0
    )

    personal_group_members_add = sub.add_parser(
        "group-members-add", help="preview or confirm adding personal group members by PUID"
    )
    personal_group_members_add.add_argument("group")
    personal_group_members_add.add_argument("puids", nargs="+")
    personal_group_members_add.add_argument("--confirmation-token")

    personal_group_member_manager = sub.add_parser(
        "group-member-manager", help="preview or confirm setting personal group manager status"
    )
    personal_group_member_manager.add_argument("group")
    personal_group_member_manager.add_argument("member")
    personal_group_member_manager.add_argument("--off", action="store_true")
    personal_group_member_manager.add_argument("--confirmation-token")

    personal_group_member_remove = sub.add_parser(
        "group-member-remove", help="preview or confirm removing a personal group member"
    )
    personal_group_member_remove.add_argument("group")
    personal_group_member_remove.add_argument("member")
    personal_group_member_remove.add_argument("--confirmation-token")

    personal_group_transfer = sub.add_parser(
        "group-transfer", help="preview or confirm transferring personal group ownership"
    )
    personal_group_transfer.add_argument("group")
    personal_group_transfer.add_argument("member")
    personal_group_transfer.add_argument("--confirmation-token")

    personal_group_clear_external = sub.add_parser(
        "group-members-clear-external",
        help="preview or confirm clearing all non-Chaoxing personal group members",
    )
    personal_group_clear_external.add_argument("group")
    personal_group_clear_external.add_argument("--confirmation-token")

    group_folders = sub.add_parser("group-folders", help="list personal group folders")
    group_folders.add_argument("--parent-folder", default="")
    group_folders.add_argument("--search", default="")

    sub.add_parser("group-folder-tree", help="read the complete personal group folder tree")

    group_folder_create = sub.add_parser(
        "group-folder-create", help="create a personal group folder"
    )
    group_folder_create.add_argument("name")
    group_folder_create.add_argument("--parent-folder", default="")

    group_folder_rename = sub.add_parser(
        "group-folder-rename", help="rename a personal group folder"
    )
    group_folder_rename.add_argument("folder")
    group_folder_rename.add_argument("name")

    group_folder_move = sub.add_parser("group-folder-move", help="move a personal group folder")
    group_folder_move.add_argument("folder")
    group_folder_move.add_argument("destination_folder")

    group_folder_top = sub.add_parser(
        "group-folder-top", help="set personal group folder top status"
    )
    group_folder_top.add_argument("folder")
    group_folder_top.add_argument("--off", action="store_true")

    group_folder_delete = sub.add_parser(
        "group-folder-delete", help="preview or confirm deleting a personal group folder"
    )
    group_folder_delete.add_argument("folder")
    group_folder_delete.add_argument("--confirmation-token")

    group_topics = sub.add_parser("group-topics", help="list or search topics in a personal group")
    group_topics.add_argument("group")
    group_topics.add_argument("--folder", default="")
    group_topics.add_argument("--search", default="")

    group_topic_read = sub.add_parser(
        "group-topic-read", help="read one personal group topic and all replies"
    )
    group_topic_read.add_argument("group")
    group_topic_read.add_argument("topic")
    group_topic_read.add_argument("--order", type=int, choices=(1, 2), default=2)
    group_topic_read.add_argument("--reply-search", default="")

    group_topic_create = sub.add_parser(
        "group-topic-create", help="preview or confirm publishing a personal group topic"
    )
    group_topic_create.add_argument("group")
    group_topic_create.add_argument("title")
    group_topic_create.add_argument("content")
    group_topic_create.add_argument("--folder", default="")
    group_topic_create.add_argument("--anonymous", action="store_true")
    group_topic_create.add_argument("--confirmation-token")

    group_topic_update = sub.add_parser(
        "group-topic-update", help="preview or confirm editing a personal group topic"
    )
    group_topic_update.add_argument("group")
    group_topic_update.add_argument("topic")
    group_topic_update.add_argument("--title")
    group_topic_update.add_argument("--content")
    group_topic_update.add_argument("--confirmation-token")

    group_topic_delete = sub.add_parser(
        "group-topic-delete", help="preview or confirm deleting a personal group topic"
    )
    group_topic_delete.add_argument("group")
    group_topic_delete.add_argument("topic")
    group_topic_delete.add_argument("--confirmation-token")

    group_topic_choice = sub.add_parser(
        "group-topic-choice", help="preview or confirm setting a topic's choice status"
    )
    group_topic_choice.add_argument("group")
    group_topic_choice.add_argument("topic")
    group_topic_choice.add_argument("--off", action="store_true")
    group_topic_choice.add_argument("--confirmation-token")

    group_topic_praise = sub.add_parser(
        "group-topic-praise", help="preview or confirm praising or unpraising a topic"
    )
    group_topic_praise.add_argument("group")
    group_topic_praise.add_argument("topic")
    group_topic_praise.add_argument("--off", action="store_true")
    group_topic_praise.add_argument("--confirmation-token")

    group_topics_score = sub.add_parser(
        "group-topics-score", help="preview or confirm scoring personal group topics"
    )
    group_topics_score.add_argument("group")
    group_topics_score.add_argument("score", type=int)
    group_topics_score.add_argument("topics", nargs="+")
    group_topics_score.add_argument("--confirmation-token")

    group_topics_move = sub.add_parser(
        "group-topics-move", help="move personal group topics to one topic folder"
    )
    group_topics_move.add_argument("group")
    group_topics_move.add_argument("destination_folder")
    group_topics_move.add_argument("topics", nargs="+")

    group_topics_delete = sub.add_parser(
        "group-topics-delete", help="preview or confirm deleting personal group topics"
    )
    group_topics_delete.add_argument("group")
    group_topics_delete.add_argument("topics", nargs="+")
    group_topics_delete.add_argument("--confirmation-token")

    group_topic_reply = sub.add_parser(
        "group-topic-reply", help="preview or confirm replying to a personal group topic"
    )
    group_topic_reply.add_argument("group")
    group_topic_reply.add_argument("topic")
    group_topic_reply.add_argument("content")
    group_topic_reply.add_argument("--reply-to", default="")
    group_topic_reply.add_argument("--anonymous", action="store_true")
    group_topic_reply.add_argument("--confirmation-token")

    group_topic_reply_update = sub.add_parser(
        "group-topic-reply-update",
        help="preview or confirm editing a personal group topic reply",
    )
    group_topic_reply_update.add_argument("group")
    group_topic_reply_update.add_argument("topic")
    group_topic_reply_update.add_argument("reply")
    group_topic_reply_update.add_argument("content")
    group_topic_reply_update.add_argument("--confirmation-token")

    group_topic_reply_delete = sub.add_parser(
        "group-topic-reply-delete",
        help="preview or confirm deleting a personal group topic reply",
    )
    group_topic_reply_delete.add_argument("group")
    group_topic_reply_delete.add_argument("topic")
    group_topic_reply_delete.add_argument("reply")
    group_topic_reply_delete.add_argument("--confirmation-token")

    group_topic_folders = sub.add_parser(
        "group-topic-folder-tree", help="read the personal group's topic-folder tree"
    )
    group_topic_folders.add_argument("group")

    group_topic_top = sub.add_parser(
        "group-topic-top", help="set a personal group topic's top status"
    )
    group_topic_top.add_argument("group")
    group_topic_top.add_argument("topic")
    group_topic_top.add_argument("--off", action="store_true")

    group_topic_move = sub.add_parser(
        "group-topic-move", help="move a personal group topic to a topic folder"
    )
    group_topic_move.add_argument("group")
    group_topic_move.add_argument("topic")
    group_topic_move.add_argument("destination_folder")

    group_topic_folder_create = sub.add_parser(
        "group-topic-folder-create", help="create a topic folder inside a personal group"
    )
    group_topic_folder_create.add_argument("group")
    group_topic_folder_create.add_argument("name")
    group_topic_folder_create.add_argument("--parent-folder", default="")

    group_topic_folder_rename = sub.add_parser(
        "group-topic-folder-rename", help="rename a topic folder inside a personal group"
    )
    group_topic_folder_rename.add_argument("group")
    group_topic_folder_rename.add_argument("folder")
    group_topic_folder_rename.add_argument("name")

    group_topic_folder_move = sub.add_parser(
        "group-topic-folder-move", help="move a topic folder inside a personal group"
    )
    group_topic_folder_move.add_argument("group")
    group_topic_folder_move.add_argument("folder")
    group_topic_folder_move.add_argument("destination_folder")

    group_topic_folder_delete = sub.add_parser(
        "group-topic-folder-delete",
        help="preview or confirm deleting a topic folder inside a personal group",
    )
    group_topic_folder_delete.add_argument("group")
    group_topic_folder_delete.add_argument("folder")
    group_topic_folder_delete.add_argument("--confirmation-token")

    group_topic_folders_move = sub.add_parser(
        "group-topic-folders-move", help="move personal group topic folders in one batch"
    )
    group_topic_folders_move.add_argument("group")
    group_topic_folders_move.add_argument("destination_folder")
    group_topic_folders_move.add_argument("folders", nargs="+")

    group_topic_folders_delete = sub.add_parser(
        "group-topic-folders-delete",
        help="preview or confirm deleting personal group topic folders in one batch",
    )
    group_topic_folders_delete.add_argument("group")
    group_topic_folders_delete.add_argument("folders", nargs="+")
    group_topic_folders_delete.add_argument("--confirmation-token")

    group_topic_drafts = sub.add_parser(
        "group-topic-drafts", help="list managed topic drafts inside a personal group"
    )
    group_topic_drafts.add_argument("group")
    group_topic_drafts.add_argument("--search", default="")

    group_topic_draft_read = sub.add_parser(
        "group-topic-draft-read", help="read a personal group topic draft by UUID"
    )
    group_topic_draft_read.add_argument("group")
    group_topic_draft_read.add_argument("draft")

    group_topic_draft_save = sub.add_parser(
        "group-topic-draft-save", help="create or update a personal group topic draft"
    )
    group_topic_draft_save.add_argument("group")
    group_topic_draft_save.add_argument("title")
    group_topic_draft_save.add_argument("content")
    group_topic_draft_save.add_argument("--draft", default="")
    group_topic_draft_save.add_argument("--folder", default="")

    group_topic_draft_publish = sub.add_parser(
        "group-topic-draft-publish",
        help="preview or confirm publishing a personal group topic draft",
    )
    group_topic_draft_publish.add_argument("group")
    group_topic_draft_publish.add_argument("draft")
    group_topic_draft_publish.add_argument("--confirmation-token")

    sub.add_parser("courses", help="list teaching courses")

    learning_courses = sub.add_parser(
        "learning-courses", help="list courses joined by the current account as a learner"
    )
    learning_courses.add_argument("--search", default="")

    learning_modules = sub.add_parser(
        "learning-modules", help="discover current learner-side entries for one course"
    )
    learning_modules.add_argument("course")

    learning_open = sub.add_parser(
        "learning-open", help="read one learner-side course entry through HTTP"
    )
    learning_open.add_argument("course")
    learning_open.add_argument("module")

    learning_activities = sub.add_parser(
        "learning-activities", help="list learner activities without entering or starting them"
    )
    learning_activities.add_argument("course")
    learning_activities.add_argument("--search", default="")
    learning_activities.add_argument(
        "--status", choices=("all", "not_started", "ongoing", "ended"), default="all"
    )

    learning_chapters = sub.add_parser(
        "learning-chapters", help="list learner-visible chapters and pending task points"
    )
    learning_chapters.add_argument("course")
    learning_chapters.add_argument("--search", default="")

    learning_discussions = sub.add_parser(
        "learning-discussions", help="list discussions visible to a learner"
    )
    learning_discussions.add_argument("course")
    learning_discussions.add_argument("--search", default="")
    learning_discussions.add_argument("--class-only", action="store_true")

    learning_discussion_read = sub.add_parser(
        "learning-discussion-read",
        help="read one learner discussion topic and all visible replies",
    )
    learning_discussion_read.add_argument("course")
    learning_discussion_read.add_argument("topic")
    learning_discussion_read.add_argument("--class-only", action="store_true")
    learning_discussion_read.add_argument("--order", choices=(1, 2), type=int, default=2)
    learning_discussion_read.add_argument("--reply-search", default="")

    learning_discussion_create = sub.add_parser(
        "learning-discussion-create",
        help="publish a learner discussion after an action-bound confirmation",
    )
    learning_discussion_create.add_argument("course")
    learning_discussion_create.add_argument("title")
    learning_discussion_create.add_argument("content")
    learning_discussion_create.add_argument("--anonymous", action="store_true")
    learning_discussion_create.add_argument("--confirmation-token")

    learning_discussion_update = sub.add_parser(
        "learning-discussion-update",
        help="update an editable learner discussion after confirmation",
    )
    learning_discussion_update.add_argument("course")
    learning_discussion_update.add_argument("topic")
    learning_discussion_update.add_argument("--title")
    learning_discussion_update.add_argument("--content")
    learning_discussion_update.add_argument("--confirmation-token")

    learning_discussion_delete = sub.add_parser(
        "learning-discussion-delete",
        help="delete an allowed learner discussion after confirmation",
    )
    learning_discussion_delete.add_argument("course")
    learning_discussion_delete.add_argument("topic")
    learning_discussion_delete.add_argument("--confirmation-token")

    learning_discussion_reply_create = sub.add_parser(
        "learning-discussion-reply-create",
        help="reply to a learner discussion after confirmation",
    )
    learning_discussion_reply_create.add_argument("course")
    learning_discussion_reply_create.add_argument("topic")
    learning_discussion_reply_create.add_argument("content")
    learning_discussion_reply_create.add_argument("--reply-to", default="")
    learning_discussion_reply_create.add_argument("--anonymous", action="store_true")
    learning_discussion_reply_create.add_argument("--confirmation-token")

    learning_discussion_reply_update = sub.add_parser(
        "learning-discussion-reply-update",
        help="update an owned learner discussion reply after confirmation",
    )
    learning_discussion_reply_update.add_argument("course")
    learning_discussion_reply_update.add_argument("topic")
    learning_discussion_reply_update.add_argument("reply")
    learning_discussion_reply_update.add_argument("content")
    learning_discussion_reply_update.add_argument("--confirmation-token")

    learning_discussion_reply_delete = sub.add_parser(
        "learning-discussion-reply-delete",
        help="delete an owned learner discussion reply after confirmation",
    )
    learning_discussion_reply_delete.add_argument("course")
    learning_discussion_reply_delete.add_argument("topic")
    learning_discussion_reply_delete.add_argument("reply")
    learning_discussion_reply_delete.add_argument("--confirmation-token")

    for command, help_text in (
        ("learning-homeworks", "list learner homework without opening an assignment"),
        ("learning-exams", "list learner exams without entering or starting an exam"),
        ("learning-self-tests", "list learner self-tests without creating or starting one"),
    ):
        learning_task_parser = sub.add_parser(command, help=help_text)
        learning_task_parser.add_argument("course")
        learning_task_parser.add_argument("--search", default="")
        learning_task_parser.add_argument("--status", default="")

    learning_homework_read = sub.add_parser(
        "learning-homework-read",
        help="read learner homework questions and current answer without saving or submitting",
    )
    learning_homework_read.add_argument("course")
    learning_homework_read.add_argument("homework")

    learning_homework_answer_enter = sub.add_parser(
        "learning-homework-answer-enter",
        help="enter a learner homework answer form without saving or submitting",
    )
    learning_homework_answer_enter.add_argument("course")
    learning_homework_answer_enter.add_argument("homework")

    learning_homework_answer_save = sub.add_parser(
        "learning-homework-answer-save",
        help="partially update and temporarily save learner homework answers",
    )
    learning_homework_answer_save.add_argument("course")
    learning_homework_answer_save.add_argument("homework")
    learning_homework_answer_save.add_argument("--updates-json", required=True)

    learning_homework_submit = sub.add_parser(
        "learning-homework-submit",
        help="submit current learner homework answers after an action-bound confirmation",
    )
    learning_homework_submit.add_argument("course")
    learning_homework_submit.add_argument("homework")
    learning_homework_submit.add_argument("--confirmation-token")

    learning_homework_redo = sub.add_parser(
        "learning-homework-redo",
        help="redo learner homework after an action-bound confirmation",
    )
    learning_homework_redo.add_argument("course")
    learning_homework_redo.add_argument("homework")
    learning_homework_redo.add_argument("--confirmation-token")

    learning_homework_attempts = sub.add_parser(
        "learning-homework-attempts",
        help="list learner homework answer records without opening an attempt",
    )
    learning_homework_attempts.add_argument("course")
    learning_homework_attempts.add_argument("homework")

    learning_homework_attempt_read = sub.add_parser(
        "learning-homework-attempt-read",
        help="read one historical learner homework attempt without saving or submitting",
    )
    learning_homework_attempt_read.add_argument("course")
    learning_homework_attempt_read.add_argument("homework")
    learning_homework_attempt_read.add_argument("attempt")

    learning_materials = sub.add_parser(
        "learning-materials", help="list learner-visible course materials or one folder"
    )
    learning_materials.add_argument("course")
    learning_materials.add_argument("--folder", default="")
    learning_materials.add_argument("--search", default="")

    learning_ai_tools = sub.add_parser(
        "learning-ai-tools", help="list tools exposed by a learner AI workbench"
    )
    learning_ai_tools.add_argument("course")

    learning_wrong_questions = sub.add_parser(
        "learning-wrong-questions", help="read a learner course's wrong-question summary"
    )
    learning_wrong_questions.add_argument("course")

    learning_records = sub.add_parser(
        "learning-records", help="read learner progress, score, attendance, and activity metrics"
    )
    learning_records.add_argument("course")

    learning_graph = sub.add_parser(
        "learning-graph", help="read a learner-visible course graph without opening a browser"
    )
    learning_graph.add_argument("course")
    learning_graph.add_argument("--search", default="")
    learning_graph.add_argument("--level", type=int)

    learning_graph_node = sub.add_parser(
        "learning-graph-node", help="read one learner-visible graph node and its relations"
    )
    learning_graph_node.add_argument("course")
    learning_graph_node.add_argument("node")

    learning_graph_models = sub.add_parser(
        "learning-graph-models", help="list learner-visible graph models"
    )
    learning_graph_models.add_argument("course")
    learning_graph_models.add_argument("--search", default="")

    learning_graph_model = sub.add_parser(
        "learning-graph-model", help="read one learner-visible graph model"
    )
    learning_graph_model.add_argument("course")
    learning_graph_model.add_argument("model")

    learning_integrity = sub.add_parser(
        "learning-integrity", help="read the online-learning integrity commitment status"
    )
    learning_integrity.add_argument("course")

    learning_integrity_accept = sub.add_parser(
        "learning-integrity-accept",
        help="preview or confirm accepting a course integrity commitment",
    )
    learning_integrity_accept.add_argument("course")
    learning_integrity_accept.add_argument("--confirmation-token")

    classes = sub.add_parser("classes", help="list classes for one course")
    classes.add_argument("course")

    create_class = sub.add_parser("class-create", help="preview or confirm creating a class")
    create_class.add_argument("course")
    create_class.add_argument("name")
    create_class.add_argument("--confirmation-token")

    rename_class = sub.add_parser("class-rename", help="preview or confirm renaming a class")
    rename_class.add_argument("course")
    rename_class.add_argument("clazz")
    rename_class.add_argument("name")
    rename_class.add_argument("--confirmation-token")

    class_settings = sub.add_parser("class-settings", help="read current class settings")
    class_settings.add_argument("course")
    class_settings.add_argument("--class", dest="clazz")

    class_invitation = sub.add_parser(
        "class-invitation", help="read a class invite code and QR-code URLs"
    )
    class_invitation.add_argument("course")
    class_invitation.add_argument("--class", dest="clazz")

    update_class_settings = sub.add_parser(
        "class-settings-update", help="preview or confirm class-setting changes"
    )
    update_class_settings.add_argument("course")
    update_class_settings.add_argument("--class", dest="clazz")
    for option in (
        "allow-student-join",
        "join-requires-approval",
        "allow-student-withdraw",
        "ended",
        "ignore-video-restrictions",
        "hidden-from-students",
    ):
        update_class_settings.add_argument(f"--{option}", choices=("true", "false"))
    update_class_settings.add_argument(
        "--unit-binding-requirement", choices=("none", "any_unit", "course_unit")
    )
    update_class_settings.add_argument("--public-scope", choices=("closed", "school", "network"))
    update_class_settings.add_argument("--student-limit", type=int)
    update_class_settings.add_argument("--semester-id")
    update_class_settings.add_argument("--open-start")
    update_class_settings.add_argument("--open-end")
    update_class_settings.add_argument("--application-start")
    update_class_settings.add_argument("--application-end")
    update_class_settings.add_argument("--confirmation-token")

    delete_class = sub.add_parser("class-delete", help="preview or confirm deleting a class")
    delete_class.add_argument("course")
    delete_class.add_argument("clazz")
    delete_class.add_argument("--confirmation-token")

    students = sub.add_parser("students", help="list students for one teaching class")
    students.add_argument("course")
    students.add_argument("--class", dest="clazz")
    students.add_argument("--search", default="")
    students.add_argument("--school-status", type=int, default=0)

    candidate_search = sub.add_parser(
        "student-candidates", help="search students available to add from the school bank"
    )
    candidate_search.add_argument("course")
    candidate_search.add_argument("query")
    candidate_search.add_argument("--class", dest="clazz")
    candidate_search.add_argument("--page", type=int, default=1)
    candidate_search.add_argument("--page-size", type=int, choices=(30, 50, 100), default=30)

    add_from_bank = sub.add_parser(
        "add-student-from-bank", help="preview or confirm adding a student-bank candidate"
    )
    add_from_bank.add_argument("course")
    add_from_bank.add_argument("student")
    add_from_bank.add_argument("--class", dest="clazz")
    add_from_bank.add_argument("--confirmation-token")

    add_student = sub.add_parser(
        "add-student", help="preview or confirm adding a student by identity"
    )
    add_student.add_argument("course")
    add_student.add_argument("name")
    add_student.add_argument("identity")
    add_student.add_argument("--class", dest="clazz")
    add_student.add_argument(
        "--identity-type",
        choices=("student_no", "employee_no", "mobile", "email"),
        default="student_no",
    )
    add_student.add_argument("--school-id", default="")
    add_student.add_argument("--confirmation-token")

    remove_student = sub.add_parser(
        "remove-student", help="preview or confirm removing a student from a class"
    )
    remove_student.add_argument("course")
    remove_student.add_argument("student")
    remove_student.add_argument("--class", dest="clazz")
    remove_student.add_argument("--confirmation-token")

    join_applications = sub.add_parser("join-applications", help="list pending class-join requests")
    join_applications.add_argument("course")
    join_applications.add_argument("--class", dest="clazz")

    decide_join = sub.add_parser(
        "decide-join-application", help="preview or confirm a class-join decision"
    )
    decide_join.add_argument("course")
    decide_join.add_argument("application")
    decide_join.add_argument("decision", choices=("approve", "reject"))
    decide_join.add_argument("--class", dest="clazz")
    decide_join.add_argument("--confirmation-token")

    move_student = sub.add_parser(
        "move-student", help="preview or confirm moving a student between course classes"
    )
    move_student.add_argument("course")
    move_student.add_argument("source_clazz")
    move_student.add_argument("target_clazz")
    move_student.add_argument("student")
    move_student.add_argument("--confirmation-token")

    access_logs = sub.add_parser(
        "access-logs", help="list one student's monthly or daily course access events"
    )
    access_logs.add_argument("course")
    access_logs.add_argument("student")
    access_logs.add_argument("year", type=int)
    access_logs.add_argument("month", type=int)
    access_logs.add_argument("--class", dest="clazz")
    access_logs.add_argument("--day", type=int, default=0)

    operation_logs = sub.add_parser("operation-logs", help="list teacher course operations")
    operation_logs.add_argument("course")
    operation_logs.add_argument("--class", dest="clazz")
    operation_logs.add_argument("--module", default="")
    operation_logs.add_argument("--search", default="")
    operation_logs.add_argument("--start-date", default="")
    operation_logs.add_argument("--end-date", default="")

    join_logs = sub.add_parser("student-join-logs", help="list student class-join records")
    join_logs.add_argument("course")
    join_logs.add_argument("--class", dest="clazz")
    join_logs.add_argument(
        "--type", dest="join_type", type=int, choices=(-1, 0, 1, 2, 3), default=-1
    )
    join_logs.add_argument("--search", default="")

    leave_logs = sub.add_parser("student-leave-logs", help="list restorable leave records")
    leave_logs.add_argument("course")
    leave_logs.add_argument("--class", dest="clazz")
    leave_logs.add_argument("--search", default="")

    restore_student = sub.add_parser(
        "restore-student", help="preview or confirm restoring a student from a leave record"
    )
    restore_student.add_argument("course")
    restore_student.add_argument("student")
    restore_student.add_argument("--class", dest="clazz")
    restore_student.add_argument("--confirmation-token")

    teachers = sub.add_parser("teachers", help="list the course teaching team")
    teachers.add_argument("course")
    teachers.add_argument("--class", dest="clazz")
    teachers.add_argument("--search", default="")
    teachers.add_argument("--role", type=int, default=0)

    teacher_candidates = sub.add_parser(
        "teacher-candidates", help="search people available to add to a course team"
    )
    teacher_candidates.add_argument("course")
    teacher_candidates.add_argument("query")
    teacher_candidates.add_argument("--class", dest="clazz")
    teacher_candidates.add_argument("--role", choices=("teacher", "assistant"), default="teacher")
    teacher_candidates.add_argument("--page", type=int, default=1)

    add_teacher_bank = sub.add_parser(
        "add-teacher-from-bank", help="preview or confirm adding a teacher-bank candidate"
    )
    add_teacher_bank.add_argument("course")
    add_teacher_bank.add_argument("teacher")
    add_teacher_bank.add_argument("--class", dest="clazz")
    add_teacher_bank.add_argument("--role", choices=("teacher", "assistant"), default="teacher")
    add_teacher_bank.add_argument("--confirmation-token")

    add_teacher = sub.add_parser(
        "add-teacher", help="preview or confirm adding a course-team member by identity"
    )
    add_teacher.add_argument("course")
    add_teacher.add_argument("name")
    add_teacher.add_argument("identity")
    add_teacher.add_argument("--class", dest="clazz")
    add_teacher.add_argument(
        "--identity-type",
        choices=("employee_no", "student_no", "mobile", "chaoxing_no"),
        default="employee_no",
    )
    add_teacher.add_argument("--role", choices=("teacher", "assistant"), default="teacher")
    add_teacher.add_argument("--school-id", default="")
    add_teacher.add_argument("--confirmation-token")

    remove_teacher = sub.add_parser(
        "remove-teacher", help="preview or confirm removing a course-team member"
    )
    remove_teacher.add_argument("course")
    remove_teacher.add_argument("teacher")
    remove_teacher.add_argument("--class", dest="clazz")
    remove_teacher.add_argument("--confirmation-token")

    teacher_permissions = sub.add_parser(
        "teacher-permissions", help="read one course-team member's permissions"
    )
    teacher_permissions.add_argument("course")
    teacher_permissions.add_argument("teacher")
    teacher_permissions.add_argument("--class", dest="clazz")

    update_teacher_permissions = sub.add_parser(
        "teacher-permissions-update",
        help="preview or confirm permission changes for one course-team member",
    )
    update_teacher_permissions.add_argument("course")
    update_teacher_permissions.add_argument("teacher")
    update_teacher_permissions.add_argument("--class", dest="clazz")
    update_teacher_permissions.add_argument(
        "--set",
        dest="permission_changes",
        action="append",
        required=True,
        metavar="KEY=VALUE",
        help="repeat for each permission, for example --set homework=true",
    )
    update_teacher_permissions.add_argument("--confirmation-token")

    grade_weights = sub.add_parser(
        "grade-weights", help="read the active grade-weight configuration"
    )
    grade_weights.add_argument("course")
    grade_weights.add_argument("--class", dest="clazz")

    grades = sub.add_parser(
        "grades", help="list weighted grades or raw component scores for one class"
    )
    grades.add_argument("course")
    grades.add_argument("--class", dest="clazz")
    grades.add_argument("--search", default="")
    grades.add_argument("--raw", dest="raw_scores", action="store_true")
    grades.add_argument("--sort", default="loginName")
    grades.add_argument("--descending", action="store_true")

    grade_visibility = sub.add_parser(
        "grade-visibility", help="read which classes can view grades and related settings"
    )
    grade_visibility.add_argument("course")
    grade_visibility.add_argument("--class", dest="clazz")

    set_grade_visibility = sub.add_parser(
        "set-grade-visibility", help="preview or confirm the complete grade-visibility settings"
    )
    set_grade_visibility.add_argument("course")
    set_grade_visibility.add_argument("visible_classes", nargs="*")
    set_grade_visibility.add_argument("--class", dest="clazz")
    set_grade_visibility.add_argument("--scheduled-open", action="store_true")
    set_grade_visibility.add_argument("--open-at", default="")
    set_grade_visibility.add_argument("--show-rank", action="store_true")
    set_grade_visibility.add_argument("--show-average", action="store_true")
    set_grade_visibility.add_argument("--confirmation-token")

    override_grade = sub.add_parser(
        "override-grade", help="preview or confirm a student final-grade override"
    )
    override_grade.add_argument("course")
    override_grade.add_argument("student")
    override_grade.add_argument("score", help="0-100, or clear to restore automatic calculation")
    override_grade.add_argument("--class", dest="clazz")
    override_grade.add_argument("--confirmation-token")

    progress = sub.add_parser("progress", help="list student learning progress for one class")
    progress.add_argument("course")
    progress.add_argument("--class", dest="clazz")
    progress.add_argument("--search", default="")
    progress.add_argument("--sort", default="loginName")
    progress.add_argument("--descending", action="store_true")

    monitor = sub.add_parser("monitor", help="list normal or abnormal study-monitor records")
    monitor.add_argument("course")
    monitor.add_argument("--class", dest="clazz")
    monitor.add_argument("--search", default="")
    monitor.add_argument("--abnormal", dest="only_abnormal", action="store_true")
    monitor.add_argument("--type", dest="anomaly_type", type=int, choices=(0, 1, 2, 4), default=0)

    monitor_remind = sub.add_parser(
        "monitor-remind", help="preview or confirm an abnormal-study reminder"
    )
    monitor_remind.add_argument("course")
    monitor_remind.add_argument("student")
    monitor_remind.add_argument("title")
    monitor_remind.add_argument("content")
    monitor_remind.add_argument("--class", dest="clazz")
    monitor_remind.add_argument("--confirmation-token")

    monitor_clear = sub.add_parser(
        "monitor-clear", help="preview or confirm clearing one student's anomaly record"
    )
    monitor_clear.add_argument("course")
    monitor_clear.add_argument("student")
    monitor_clear.add_argument("--class", dest="clazz")
    monitor_clear.add_argument("--confirmation-token")

    modules = sub.add_parser("modules", help="discover live course function entries")
    modules.add_argument("course")
    modules.add_argument("--class", dest="clazz")

    open_module = sub.add_parser(
        "open-module", help="fetch one course function through authenticated HTTP"
    )
    open_module.add_argument("course")
    open_module.add_argument("module")
    open_module.add_argument("--class", dest="clazz")

    knowledge_hub_status = sub.add_parser(
        "knowledge-hub-status", help="read the course AI knowledge-hub status and dictionaries"
    )
    knowledge_hub_status.add_argument("course")
    knowledge_hub_status.add_argument("--class", dest="clazz")

    knowledge_hub_bases = sub.add_parser(
        "knowledge-hub-bases", help="list course AI knowledge bases"
    )
    knowledge_hub_bases.add_argument("course")
    knowledge_hub_bases.add_argument("--class", dest="clazz")
    knowledge_hub_bases.add_argument("--module", default="NORMAL_BASE")
    knowledge_hub_bases.add_argument("--page", type=int, default=1)
    knowledge_hub_bases.add_argument("--page-size", type=int, default=100)
    knowledge_hub_bases.add_argument("--category", type=int, default=-1)
    knowledge_hub_bases.add_argument("--state", type=int, default=-1)
    knowledge_hub_bases.add_argument("--creator", default="")
    knowledge_hub_bases.add_argument("--search", default="")
    knowledge_hub_bases.add_argument("--begin-time", default="")
    knowledge_hub_bases.add_argument("--end-time", default="")

    knowledge_hub_base = sub.add_parser(
        "knowledge-hub-base", help="read one course AI knowledge base"
    )
    knowledge_hub_base.add_argument("course")
    knowledge_hub_base.add_argument("base")
    knowledge_hub_base.add_argument("--class", dest="clazz")
    knowledge_hub_base.add_argument("--module", default="NORMAL_BASE")

    knowledge_hub_statistics = sub.add_parser(
        "knowledge-hub-statistics", help="read course AI knowledge-hub statistics"
    )
    knowledge_hub_statistics.add_argument("course")
    knowledge_hub_statistics.add_argument("--class", dest="clazz")
    knowledge_hub_statistics.add_argument("--module", default="NORMAL_BASE")

    knowledge_hub_base_create = sub.add_parser(
        "knowledge-hub-base-create", help="create a private course AI knowledge base"
    )
    knowledge_hub_base_create.add_argument("course")
    knowledge_hub_base_create.add_argument("name")
    knowledge_hub_base_create.add_argument("description")
    knowledge_hub_base_create.add_argument("--class", dest="clazz")
    knowledge_hub_base_create.add_argument("--category", type=int, choices=(0, 4, 9, 10), default=0)
    knowledge_hub_base_create.add_argument("--cover", default="")
    knowledge_hub_base_create.add_argument("--split-rule-json")

    knowledge_hub_base_update = sub.add_parser(
        "knowledge-hub-base-update", help="update a course AI knowledge base"
    )
    knowledge_hub_base_update.add_argument("course")
    knowledge_hub_base_update.add_argument("base")
    knowledge_hub_base_update.add_argument("--class", dest="clazz")
    knowledge_hub_base_update.add_argument("--name")
    knowledge_hub_base_update.add_argument("--description")
    knowledge_hub_base_update.add_argument("--cover")
    knowledge_hub_base_update.add_argument("--split-rule-json")

    knowledge_hub_base_availability = sub.add_parser(
        "knowledge-hub-base-availability", help="enable or disable a course AI knowledge base"
    )
    knowledge_hub_base_availability.add_argument("course")
    knowledge_hub_base_availability.add_argument("base")
    knowledge_hub_base_availability.add_argument("status", choices=("enable", "disable"))
    knowledge_hub_base_availability.add_argument("--class", dest="clazz")

    knowledge_hub_base_priority = sub.add_parser(
        "knowledge-hub-base-priority", help="set or clear a course AI knowledge-base priority"
    )
    knowledge_hub_base_priority.add_argument("course")
    knowledge_hub_base_priority.add_argument("base")
    knowledge_hub_base_priority.add_argument("--off", action="store_true")
    knowledge_hub_base_priority.add_argument("--class", dest="clazz")

    knowledge_hub_base_share = sub.add_parser(
        "knowledge-hub-base-share", help="preview or confirm sharing a course AI knowledge base"
    )
    knowledge_hub_base_share.add_argument("course")
    knowledge_hub_base_share.add_argument("base")
    knowledge_hub_base_share.add_argument("--off", action="store_true")
    knowledge_hub_base_share.add_argument("--class", dest="clazz")
    knowledge_hub_base_share.add_argument("--confirmation-token")

    knowledge_hub_base_delete = sub.add_parser(
        "knowledge-hub-base-delete", help="preview or confirm deleting an AI knowledge base"
    )
    knowledge_hub_base_delete.add_argument("course")
    knowledge_hub_base_delete.add_argument("base")
    knowledge_hub_base_delete.add_argument("--class", dest="clazz")
    knowledge_hub_base_delete.add_argument("--confirmation-token")

    knowledge_hub_documents = sub.add_parser(
        "knowledge-hub-documents", help="list documents in a course AI knowledge base"
    )
    knowledge_hub_documents.add_argument("course")
    knowledge_hub_documents.add_argument("base")
    knowledge_hub_documents.add_argument("--class", dest="clazz")
    knowledge_hub_documents.add_argument("--page", type=int, default=1)
    knowledge_hub_documents.add_argument("--page-size", type=int, default=100)
    knowledge_hub_documents.add_argument("--state", default="")
    knowledge_hub_documents.add_argument("--source", default="")
    knowledge_hub_documents.add_argument("--search", default="")
    knowledge_hub_documents.add_argument("--classify-id", default="")
    knowledge_hub_documents.add_argument("--file-type", default="")
    knowledge_hub_documents.add_argument("--begin-time", default="")
    knowledge_hub_documents.add_argument("--end-time", default="")
    knowledge_hub_documents.add_argument("--order", default="")

    knowledge_hub_document_download = sub.add_parser(
        "knowledge-hub-document-download", help="download an AI knowledge-base document"
    )
    knowledge_hub_document_download.add_argument("course")
    knowledge_hub_document_download.add_argument("base")
    knowledge_hub_document_download.add_argument("document")
    knowledge_hub_document_download.add_argument("output_path")
    knowledge_hub_document_download.add_argument("--class", dest="clazz")
    knowledge_hub_document_download.add_argument("--overwrite", action="store_true")

    knowledge_hub_document_upload = sub.add_parser(
        "knowledge-hub-document-upload", help="upload a local file to an AI knowledge base"
    )
    knowledge_hub_document_upload.add_argument("course")
    knowledge_hub_document_upload.add_argument("base")
    knowledge_hub_document_upload.add_argument("file")
    knowledge_hub_document_upload.add_argument("--class", dest="clazz")
    knowledge_hub_document_upload.add_argument("--classify-id", default="")
    knowledge_hub_document_upload.add_argument("--split-rule-json")

    knowledge_hub_document_delete = sub.add_parser(
        "knowledge-hub-document-delete",
        help="preview or confirm deleting an AI knowledge-base document",
    )
    knowledge_hub_document_delete.add_argument("course")
    knowledge_hub_document_delete.add_argument("base")
    knowledge_hub_document_delete.add_argument("document")
    knowledge_hub_document_delete.add_argument("--class", dest="clazz")
    knowledge_hub_document_delete.add_argument("--confirmation-token")

    ai_groups = sub.add_parser("ai-groups", help="list course AI-workbench command groups")
    ai_groups.add_argument("course")
    ai_groups.add_argument("--class", dest="clazz")

    ai_group_create = sub.add_parser("ai-group-create", help="create an AI command group")
    ai_group_create.add_argument("course")
    ai_group_create.add_argument("name")
    ai_group_create.add_argument("--class", dest="clazz")
    ai_group_create.add_argument("--confirmation-token")

    ai_group_rename = sub.add_parser("ai-group-rename", help="rename an AI command group")
    ai_group_rename.add_argument("course")
    ai_group_rename.add_argument("group")
    ai_group_rename.add_argument("name")
    ai_group_rename.add_argument("--class", dest="clazz")
    ai_group_rename.add_argument("--confirmation-token")

    ai_group_reorder = sub.add_parser(
        "ai-group-reorder", help="set the complete AI command-group order"
    )
    ai_group_reorder.add_argument("course")
    ai_group_reorder.add_argument("groups", nargs="+")
    ai_group_reorder.add_argument("--class", dest="clazz")
    ai_group_reorder.add_argument("--confirmation-token")

    ai_group_delete = sub.add_parser("ai-group-delete", help="delete an AI command group")
    ai_group_delete.add_argument("course")
    ai_group_delete.add_argument("group")
    ai_group_delete.add_argument("--allow-nonempty", action="store_true")
    ai_group_delete.add_argument("--class", dest="clazz")
    ai_group_delete.add_argument("--confirmation-token")

    ai_commands = sub.add_parser("ai-commands", help="list course AI commands")
    ai_commands.add_argument("course")
    ai_commands.add_argument("--group", default="")
    ai_commands.add_argument("--search", default="")
    ai_commands.add_argument("--class", dest="clazz")

    ai_command_read = sub.add_parser("ai-command-read", help="read one AI command")
    ai_command_read.add_argument("course")
    ai_command_read.add_argument("ai_command", metavar="command")
    ai_command_read.add_argument("--group", default="")
    ai_command_read.add_argument("--class", dest="clazz")

    ai_command_create = sub.add_parser("ai-command-create", help="create an AI command")
    ai_command_create.add_argument("course")
    ai_command_create.add_argument("group")
    ai_command_create.add_argument("name")
    ai_command_create.add_argument("content")
    ai_command_create.add_argument("explanation")
    ai_command_create.add_argument("--prompt-words", default="")
    ai_command_create.add_argument("--role-type", type=int, choices=(0, 1, 2, 3), default=0)
    ai_command_create.add_argument("--classify-id", type=int, default=1)
    ai_command_create.add_argument("--command-ability", type=int, choices=(0, 1), default=0)
    ai_command_create.add_argument("--ability-type", type=int, default=0)
    ai_command_create.add_argument("--class", dest="clazz")
    ai_command_create.add_argument("--confirmation-token")

    ai_command_update = sub.add_parser("ai-command-update", help="update an AI command")
    ai_command_update.add_argument("course")
    ai_command_update.add_argument("ai_command", metavar="command")
    ai_command_update.add_argument("--group", default="")
    ai_command_update.add_argument("--name")
    ai_command_update.add_argument("--content")
    ai_command_update.add_argument("--explanation")
    ai_command_update.add_argument("--prompt-words")
    ai_command_update.add_argument("--role-type", type=int, choices=(0, 1, 2, 3))
    ai_command_update.add_argument("--classify-id", type=int)
    ai_command_update.add_argument("--command-ability", type=int, choices=(0, 1))
    ai_command_update.add_argument("--ability-type", type=int)
    ai_command_update.add_argument("--class", dest="clazz")
    ai_command_update.add_argument("--confirmation-token")

    ai_command_move = sub.add_parser("ai-command-move", help="move an AI command")
    ai_command_move.add_argument("course")
    ai_command_move.add_argument("ai_command", metavar="command")
    ai_command_move.add_argument("target_group")
    ai_command_move.add_argument("--group", default="")
    ai_command_move.add_argument("--class", dest="clazz")
    ai_command_move.add_argument("--confirmation-token")

    ai_command_reorder = sub.add_parser(
        "ai-command-reorder", help="set a complete teacher or student AI-command order"
    )
    ai_command_reorder.add_argument("course")
    ai_command_reorder.add_argument("group")
    ai_command_reorder.add_argument("role_type", type=int, choices=(0, 1))
    ai_command_reorder.add_argument("commands", nargs="+")
    ai_command_reorder.add_argument("--class", dest="clazz")
    ai_command_reorder.add_argument("--confirmation-token")

    ai_command_publish = sub.add_parser(
        "ai-command-publish", help="publish or unpublish an AI command"
    )
    ai_command_publish.add_argument("course")
    ai_command_publish.add_argument("ai_command", metavar="command")
    ai_command_publish.add_argument("--group", default="")
    ai_command_publish.add_argument("--off", action="store_true")
    ai_command_publish.add_argument("--class", dest="clazz")
    ai_command_publish.add_argument("--confirmation-token")

    ai_command_delete = sub.add_parser("ai-command-delete", help="delete an AI command")
    ai_command_delete.add_argument("course")
    ai_command_delete.add_argument("ai_command", metavar="command")
    ai_command_delete.add_argument("--group", default="")
    ai_command_delete.add_argument("--class", dest="clazz")
    ai_command_delete.add_argument("--confirmation-token")

    ai_recommendations = sub.add_parser(
        "ai-recommendations", help="list AI command recommendations"
    )
    ai_recommendations.add_argument("course")
    ai_recommendations.add_argument("--page", type=int, default=1)
    ai_recommendations.add_argument("--class", dest="clazz")

    ai_recommendation_add = sub.add_parser(
        "ai-recommendation-add", help="map a recommended AI command into a group"
    )
    ai_recommendation_add.add_argument("course")
    ai_recommendation_add.add_argument("recommendation")
    ai_recommendation_add.add_argument("group")
    ai_recommendation_add.add_argument("--class", dest="clazz")
    ai_recommendation_add.add_argument("--confirmation-token")

    task_folders = sub.add_parser("task-folders", help="list task-engine folders")
    task_folders.add_argument("course")
    task_folders.add_argument("--class", dest="clazz")

    task_list = sub.add_parser("task-list", help="list active or recycled task-engine tasks")
    task_list.add_argument("course")
    task_list.add_argument("--class", dest="clazz")
    task_list.add_argument("--folder", default="")
    task_list.add_argument("--search", default="")
    task_list.add_argument("--recycled", action="store_true")
    task_list.add_argument("--max-items", type=int, default=1000)

    task_read = sub.add_parser("task-read", help="read one task-engine task and its points")
    task_read.add_argument("course")
    task_read.add_argument("task")
    task_read.add_argument("--class", dest="clazz")

    task_folder_create = sub.add_parser("task-folder-create", help="create a task-engine folder")
    task_folder_create.add_argument("course")
    task_folder_create.add_argument("name")
    task_folder_create.add_argument("--class", dest="clazz")

    task_folder_rename = sub.add_parser("task-folder-rename", help="rename a task-engine folder")
    task_folder_rename.add_argument("course")
    task_folder_rename.add_argument("folder")
    task_folder_rename.add_argument("name")
    task_folder_rename.add_argument("--class", dest="clazz")

    task_folder_delete = sub.add_parser(
        "task-folder-delete", help="preview or confirm deleting a task-engine folder"
    )
    task_folder_delete.add_argument("course")
    task_folder_delete.add_argument("folder")
    task_folder_delete.add_argument("--allow-nonempty", action="store_true")
    task_folder_delete.add_argument("--class", dest="clazz")
    task_folder_delete.add_argument("--confirmation-token")

    task_create = sub.add_parser("task-create", help="create an unpublished task-engine task")
    task_create.add_argument("course")
    task_create.add_argument("name")
    task_create.add_argument("--class", dest="clazz")
    task_create.add_argument("--folder", default="")
    task_create.add_argument("--introduce", default="")
    task_create.add_argument("--rich-text", default="")
    task_create.add_argument("--cover", default="")
    task_create.add_argument("--target", default="")
    task_create.add_argument(
        "--mode",
        dest="selected_modes",
        action="append",
        choices=("list", "frame", "knowledge"),
    )

    task_update = sub.add_parser("task-update", help="update a task-engine task")
    task_update.add_argument("course")
    task_update.add_argument("task")
    task_update.add_argument("--class", dest="clazz")
    task_update.add_argument("--name")
    task_update.add_argument("--introduce")
    task_update.add_argument("--rich-text")
    task_update.add_argument("--cover")
    task_update.add_argument("--target")
    task_update.add_argument("--start-date")
    task_update.add_argument("--end-date")
    task_update.add_argument(
        "--mode",
        dest="selected_modes",
        action="append",
        choices=("list", "frame", "knowledge"),
    )

    task_move = sub.add_parser("task-move", help="move a task-engine task")
    task_move.add_argument("course")
    task_move.add_argument("task")
    task_move.add_argument("--folder", default="", help="folder name/ID, or omit for root")
    task_move.add_argument("--class", dest="clazz")

    task_reorder = sub.add_parser(
        "task-reorder", help="set complete task and optional root-folder orders"
    )
    task_reorder.add_argument("course")
    task_reorder.add_argument("task_order", nargs="+")
    task_reorder.add_argument("--folder", default="")
    task_reorder.add_argument("--folder-order", nargs="*")
    task_reorder.add_argument("--class", dest="clazz")

    task_copy = sub.add_parser("task-copy", help="copy a task-engine task")
    task_copy.add_argument("course")
    task_copy.add_argument("task")
    task_copy.add_argument("--name", default="")
    task_copy.add_argument("--folder", default="")
    task_copy.add_argument("--class", dest="clazz")

    task_delete = sub.add_parser(
        "task-delete", help="preview or confirm moving a task-engine task to recycle"
    )
    task_delete.add_argument("course")
    task_delete.add_argument("task")
    task_delete.add_argument("--class", dest="clazz")
    task_delete.add_argument("--confirmation-token")

    task_recycle = sub.add_parser("task-recycle", help="list task-engine recycle")
    task_recycle.add_argument("course")
    task_recycle.add_argument("--class", dest="clazz")
    task_recycle.add_argument("--search", default="")
    task_recycle.add_argument("--max-items", type=int, default=1000)

    task_restore = sub.add_parser("task-restore", help="restore a recycled task-engine task")
    task_restore.add_argument("course")
    task_restore.add_argument("task")
    task_restore.add_argument("--class", dest="clazz")

    task_labels = sub.add_parser("task-labels", help="list or search task-engine labels")
    task_labels.add_argument("course")
    task_labels.add_argument("--task", default="")
    task_labels.add_argument("--search", default="")
    task_labels.add_argument("--class", dest="clazz")

    task_label_create = sub.add_parser("task-label-create", help="create a task-engine label")
    task_label_create.add_argument("course")
    task_label_create.add_argument("name")
    task_label_create.add_argument("--task", default="")
    task_label_create.add_argument("--class", dest="clazz")

    task_label_rename = sub.add_parser("task-label-rename", help="rename a task-engine label")
    task_label_rename.add_argument("course")
    task_label_rename.add_argument("label")
    task_label_rename.add_argument("name")
    task_label_rename.add_argument("--task", default="")
    task_label_rename.add_argument("--class", dest="clazz")

    task_label_delete = sub.add_parser(
        "task-label-delete", help="preview or confirm deleting a task-engine label"
    )
    task_label_delete.add_argument("course")
    task_label_delete.add_argument("label")
    task_label_delete.add_argument("--task", default="")
    task_label_delete.add_argument("--class", dest="clazz")
    task_label_delete.add_argument("--confirmation-token")

    task_export = sub.add_parser("task-export", help="request task-engine export")
    task_export.add_argument("course")
    task_export.add_argument("tasks", nargs="*")
    task_export.add_argument("--folder", default="")
    task_export.add_argument("--class", dest="clazz")

    task_publish = sub.add_parser(
        "task-publish", help="preview or confirm publishing or unpublishing a task-engine task"
    )
    task_publish.add_argument("course")
    task_publish.add_argument("task")
    task_publish.add_argument("--off", action="store_true")
    task_publish.add_argument("--course-publish-json")
    task_publish.add_argument("--task-publish-json")
    task_publish.add_argument("--class", dest="clazz")
    task_publish.add_argument("--confirmation-token")

    graph = sub.add_parser("graph", help="read the course knowledge graph")
    graph.add_argument("course")
    graph.add_argument("--class", dest="clazz")
    graph.add_argument("--search", default="")
    graph.add_argument("--level", type=int)

    graph_node = sub.add_parser("graph-node", help="read one course-graph node and relations")
    graph_node.add_argument("course")
    graph_node.add_argument("node")
    graph_node.add_argument("--class", dest="clazz")

    graph_node_create = sub.add_parser(
        "graph-node-create", help="create a category, knowledge point, or ability point"
    )
    graph_node_create.add_argument("course")
    graph_node_create.add_argument("name")
    graph_node_create.add_argument(
        "--type",
        dest="node_type",
        choices=("knowledge", "category", "ability"),
        default="knowledge",
    )
    graph_node_create.add_argument("--parent", default="")
    graph_node_create.add_argument("--description", default="")
    graph_node_create.add_argument("--model", default="")
    graph_node_create.add_argument("--class", dest="clazz")

    graph_node_update = sub.add_parser(
        "graph-node-update", help="update any non-root course-graph node"
    )
    graph_node_update.add_argument("course")
    graph_node_update.add_argument("node")
    graph_node_update.add_argument("name")
    graph_node_update.add_argument("--description", default="")
    graph_node_update.add_argument("--class", dest="clazz")

    graph_node_relations = sub.add_parser(
        "graph-node-relations",
        help="read predecessor, successor, association, and custom relations",
    )
    graph_node_relations.add_argument("course")
    graph_node_relations.add_argument("node")
    graph_node_relations.add_argument("--class", dest="clazz")

    graph_node_relation_add = sub.add_parser(
        "graph-node-relation-add",
        help="preview or confirm adding a relation between two graph nodes",
    )
    graph_node_relation_add.add_argument("course")
    graph_node_relation_add.add_argument("node")
    graph_node_relation_add.add_argument("relation")
    graph_node_relation_add.add_argument("target")
    graph_node_relation_add.add_argument("--description", default="")
    graph_node_relation_add.add_argument("--class", dest="clazz")
    graph_node_relation_add.add_argument("--confirmation-token")

    graph_node_relation_remove = sub.add_parser(
        "graph-node-relation-remove",
        help="preview or confirm removing a relation between two graph nodes",
    )
    graph_node_relation_remove.add_argument("course")
    graph_node_relation_remove.add_argument("node")
    graph_node_relation_remove.add_argument("relation")
    graph_node_relation_remove.add_argument("target")
    graph_node_relation_remove.add_argument("--class", dest="clazz")
    graph_node_relation_remove.add_argument("--confirmation-token")

    graph_settings = sub.add_parser("graph-settings", help="read course-graph display settings")
    graph_settings.add_argument("course")
    graph_settings.add_argument("--class", dest="clazz")

    graph_settings_update = sub.add_parser(
        "graph-settings-update",
        help="preview or confirm updating student-visible course-graph display settings",
    )
    graph_settings_update.add_argument("course")
    for flag in (
        "show-all-relations",
        "show-all-topic-names",
        "navigation-node-scale",
        "graph-background-color",
    ):
        graph_settings_update.add_argument(
            f"--{flag}", action=argparse.BooleanOptionalAction, default=None
        )
    graph_settings_update.add_argument("--class", dest="clazz")
    graph_settings_update.add_argument("--confirmation-token")

    graph_advanced_settings = sub.add_parser(
        "graph-advanced-settings", help="read course-graph advanced settings"
    )
    graph_advanced_settings.add_argument("course")
    graph_advanced_settings.add_argument("--class", dest="clazz")

    graph_advanced_settings_update = sub.add_parser(
        "graph-advanced-settings-update",
        help="preview or confirm updating student-visible advanced graph settings",
    )
    graph_advanced_settings_update.add_argument("course")
    for flag in (
        "topic-card",
        "teach-target",
        "study-hours-enabled",
        "classify-relation-data",
        "selftest-included",
        "micro-preview",
        "micro-scale-mode",
    ):
        graph_advanced_settings_update.add_argument(
            f"--{flag}", action=argparse.BooleanOptionalAction, default=None
        )
    graph_advanced_settings_update.add_argument("--class", dest="clazz")
    graph_advanced_settings_update.add_argument("--confirmation-token")

    graph_models = sub.add_parser("graph-models", help="list course-graph models")
    graph_models.add_argument("course")
    graph_models.add_argument("--class", dest="clazz")
    graph_models.add_argument("--search", default="")

    graph_model_data = sub.add_parser(
        "graph-model-data", help="read model-specific course-graph data"
    )
    graph_model_data.add_argument("course")
    graph_model_data.add_argument("model")
    graph_model_data.add_argument("--class", dest="clazz")

    graph_model_create = sub.add_parser(
        "graph-model-create", help="create a custom course-graph model"
    )
    graph_model_create.add_argument("course")
    graph_model_create.add_argument("name")
    graph_model_create.add_argument("--style", type=int, default=0)
    graph_model_create.add_argument("--class", dest="clazz")

    graph_model_update = sub.add_parser(
        "graph-model-update", help="update a course-graph model name or style"
    )
    graph_model_update.add_argument("course")
    graph_model_update.add_argument("model")
    graph_model_update.add_argument("name")
    graph_model_update.add_argument("--style", type=int)
    graph_model_update.add_argument("--class", dest="clazz")

    graph_model_visibility = sub.add_parser(
        "graph-model-visibility",
        help="preview or confirm showing or hiding a course-graph model",
    )
    graph_model_visibility.add_argument("course")
    graph_model_visibility.add_argument("model")
    graph_model_visibility.add_argument("status", choices=("show", "hide"))
    graph_model_visibility.add_argument("--class", dest="clazz")
    graph_model_visibility.add_argument("--confirmation-token")

    graph_model_reorder = sub.add_parser(
        "graph-model-reorder", help="set the complete course-graph model order"
    )
    graph_model_reorder.add_argument("course")
    graph_model_reorder.add_argument("models", nargs="+")
    graph_model_reorder.add_argument("--class", dest="clazz")

    graph_model_delete = sub.add_parser(
        "graph-model-delete", help="preview or confirm deleting a custom graph model"
    )
    graph_model_delete.add_argument("course")
    graph_model_delete.add_argument("model")
    graph_model_delete.add_argument("--class", dest="clazz")
    graph_model_delete.add_argument("--confirmation-token")

    graph_model_classes = sub.add_parser(
        "graph-model-classes", help="list class visibility for a course-graph model"
    )
    graph_model_classes.add_argument("course")
    graph_model_classes.add_argument("model")
    graph_model_classes.add_argument("--class", dest="clazz")

    graph_model_classes_update = sub.add_parser(
        "graph-model-classes-update",
        help="preview or confirm the complete visible-class set for a graph model",
    )
    graph_model_classes_update.add_argument("course")
    graph_model_classes_update.add_argument("model")
    graph_model_classes_update.add_argument("visible_classes", nargs="*")
    graph_model_classes_update.add_argument("--class", dest="clazz")
    graph_model_classes_update.add_argument("--confirmation-token")

    graph_events = sub.add_parser("graph-events", help="list course-graph task events")
    graph_events.add_argument("course")
    graph_events.add_argument("--class", dest="clazz")
    graph_events.add_argument("--search", default="")

    graph_event_create = sub.add_parser(
        "graph-event-create", help="preview or confirm creating a course-graph task event"
    )
    graph_event_create.add_argument("course")
    graph_event_create.add_argument("name")
    graph_event_create.add_argument("topic_condition")
    graph_event_create.add_argument("set_condition")
    graph_event_create.add_argument("percent1", type=int)
    graph_event_create.add_argument("executions_json")
    graph_event_create.add_argument("--percent2", type=int, default=100)
    graph_event_create.add_argument("--class", dest="clazz")
    graph_event_create.add_argument("--confirmation-token")

    graph_event_update = sub.add_parser(
        "graph-event-update", help="preview or confirm updating a course-graph task event"
    )
    graph_event_update.add_argument("course")
    graph_event_update.add_argument("event")
    graph_event_update.add_argument("--name")
    graph_event_update.add_argument("--topic-condition")
    graph_event_update.add_argument("--set-condition")
    graph_event_update.add_argument("--percent1", type=int)
    graph_event_update.add_argument("--percent2", type=int)
    graph_event_update.add_argument("--executions-json")
    graph_event_update.add_argument("--class", dest="clazz")
    graph_event_update.add_argument("--confirmation-token")

    graph_event_delete = sub.add_parser(
        "graph-event-delete", help="preview or confirm deleting a course-graph task event"
    )
    graph_event_delete.add_argument("course")
    graph_event_delete.add_argument("event")
    graph_event_delete.add_argument("--class", dest="clazz")
    graph_event_delete.add_argument("--confirmation-token")

    graph_export = sub.add_parser(
        "graph-export", help="download a course-graph export without opening a browser"
    )
    graph_export.add_argument("course")
    graph_export.add_argument(
        "format", choices=("xmind", "excel", "xlsx", "csv", "psg", "json", "pdf", "rdf")
    )
    graph_export.add_argument("output_path")
    graph_export.add_argument("--model", default="")
    graph_export.add_argument("--overwrite", action="store_true")
    graph_export.add_argument("--class", dest="clazz")

    graph_relations = sub.add_parser(
        "graph-relations", help="list built-in and custom course-graph relation definitions"
    )
    graph_relations.add_argument("course")
    graph_relations.add_argument("--class", dest="clazz")
    graph_relations.add_argument("--search", default="")

    graph_relation_create = sub.add_parser(
        "graph-relation-create", help="create a custom course-graph relation definition"
    )
    graph_relation_create.add_argument("course")
    graph_relation_create.add_argument("name")
    graph_relation_create.add_argument("--meaning", default="")
    graph_relation_create.add_argument(
        "--relation-type", dest="relation_types", action="append", type=int, choices=(0, 1, 2)
    )
    graph_relation_create.add_argument("--example-html", default="")
    graph_relation_create.add_argument("--color", default="")
    graph_relation_create.add_argument("--class", dest="clazz")

    graph_relation_update = sub.add_parser(
        "graph-relation-update", help="update a custom course-graph relation definition"
    )
    graph_relation_update.add_argument("course")
    graph_relation_update.add_argument("relation")
    graph_relation_update.add_argument("--name")
    graph_relation_update.add_argument("--meaning")
    graph_relation_update.add_argument(
        "--relation-type", dest="relation_types", action="append", type=int, choices=(0, 1, 2)
    )
    graph_relation_update.add_argument("--example-html")
    graph_relation_update.add_argument("--color")
    graph_relation_update.add_argument("--arrow-size", type=int)
    graph_relation_update.add_argument("--line-thickness", type=int)
    graph_relation_update.add_argument("--class", dest="clazz")

    graph_relation_delete = sub.add_parser(
        "graph-relation-delete",
        help="preview or confirm deleting a custom course-graph relation definition",
    )
    graph_relation_delete.add_argument("course")
    graph_relation_delete.add_argument("relation")
    graph_relation_delete.add_argument("--class", dest="clazz")
    graph_relation_delete.add_argument("--confirmation-token")

    graph_category_create = sub.add_parser(
        "graph-category-create", help="create a top-level course-graph category"
    )
    graph_category_create.add_argument("course")
    graph_category_create.add_argument("name")
    graph_category_create.add_argument("--description", default="")
    graph_category_create.add_argument("--class", dest="clazz")

    graph_category_update = sub.add_parser(
        "graph-category-update", help="update a course-graph category"
    )
    graph_category_update.add_argument("course")
    graph_category_update.add_argument("node")
    graph_category_update.add_argument("name")
    graph_category_update.add_argument("--description", default="")
    graph_category_update.add_argument("--class", dest="clazz")

    graph_node_delete = sub.add_parser(
        "graph-node-delete", help="preview or confirm deleting a course-graph node"
    )
    graph_node_delete.add_argument("course")
    graph_node_delete.add_argument("node")
    graph_node_delete.add_argument("--class", dest="clazz")
    graph_node_delete.add_argument("--confirmation-token")

    graph_labels = sub.add_parser("graph-labels", help="list course-graph label groups")
    graph_labels.add_argument("course")
    graph_labels.add_argument("--class", dest="clazz")
    graph_labels.add_argument("--search", default="")

    graph_label_group_create = sub.add_parser(
        "graph-label-group-create", help="create a course-graph label group"
    )
    graph_label_group_create.add_argument("course")
    graph_label_group_create.add_argument("name")
    graph_label_group_create.add_argument("--group-type", type=int, choices=(0, 1, 2), default=0)
    graph_label_group_create.add_argument("--class", dest="clazz")

    graph_label_group_rename = sub.add_parser(
        "graph-label-group-rename", help="rename a course-graph label group"
    )
    graph_label_group_rename.add_argument("course")
    graph_label_group_rename.add_argument("group")
    graph_label_group_rename.add_argument("name")
    graph_label_group_rename.add_argument("--class", dest="clazz")

    graph_label_group_delete = sub.add_parser(
        "graph-label-group-delete",
        help="preview or confirm deleting a course-graph label group",
    )
    graph_label_group_delete.add_argument("course")
    graph_label_group_delete.add_argument("group")
    graph_label_group_delete.add_argument("--class", dest="clazz")
    graph_label_group_delete.add_argument("--confirmation-token")

    graph_label_group_reorder = sub.add_parser(
        "graph-label-group-reorder", help="set the complete course-graph label-group order"
    )
    graph_label_group_reorder.add_argument("course")
    graph_label_group_reorder.add_argument("groups", nargs="+")
    graph_label_group_reorder.add_argument("--class", dest="clazz")

    graph_label_create = sub.add_parser(
        "graph-label-create", help="create a label in a course-graph label group"
    )
    graph_label_create.add_argument("course")
    graph_label_create.add_argument("group")
    graph_label_create.add_argument("name")
    graph_label_create.add_argument("--class", dest="clazz")

    graph_label_rename = sub.add_parser("graph-label-rename", help="rename a course-graph label")
    graph_label_rename.add_argument("course")
    graph_label_rename.add_argument("label")
    graph_label_rename.add_argument("name")
    graph_label_rename.add_argument("--class", dest="clazz")

    graph_label_move = sub.add_parser(
        "graph-label-move", help="move a course-graph label into another group"
    )
    graph_label_move.add_argument("course")
    graph_label_move.add_argument("label")
    graph_label_move.add_argument("group")
    graph_label_move.add_argument("--class", dest="clazz")

    graph_label_reorder = sub.add_parser(
        "graph-label-reorder", help="set the complete label order in one graph label group"
    )
    graph_label_reorder.add_argument("course")
    graph_label_reorder.add_argument("group")
    graph_label_reorder.add_argument("labels", nargs="+")
    graph_label_reorder.add_argument("--class", dest="clazz")

    graph_label_delete = sub.add_parser(
        "graph-label-delete", help="preview or confirm deleting a course-graph label"
    )
    graph_label_delete.add_argument("course")
    graph_label_delete.add_argument("label")
    graph_label_delete.add_argument("--class", dest="clazz")
    graph_label_delete.add_argument("--confirmation-token")

    activity_types = sub.add_parser(
        "class-activity-types", help="list available class-activity type IDs"
    )
    activity_types.add_argument("course")
    activity_types.add_argument("--class", dest="clazz")

    activity_groups = sub.add_parser("class-activity-groups", help="list class-activity groups")
    activity_groups.add_argument("course")
    activity_groups.add_argument("--class", dest="clazz")

    activity_group_create = sub.add_parser(
        "class-activity-group-create", help="create a class-activity group"
    )
    activity_group_create.add_argument("course")
    activity_group_create.add_argument("name")
    activity_group_create.add_argument("--class", dest="clazz")

    activity_group_rename = sub.add_parser(
        "class-activity-group-rename", help="rename a class-activity group"
    )
    activity_group_rename.add_argument("course")
    activity_group_rename.add_argument("group")
    activity_group_rename.add_argument("name")
    activity_group_rename.add_argument("--class", dest="clazz")

    activity_group_delete = sub.add_parser(
        "class-activity-group-delete",
        help="preview or confirm deleting a class-activity group",
    )
    activity_group_delete.add_argument("course")
    activity_group_delete.add_argument("group")
    activity_group_delete.add_argument("--allow-nonempty", action="store_true")
    activity_group_delete.add_argument("--class", dest="clazz")
    activity_group_delete.add_argument("--confirmation-token")

    activity_group_reorder = sub.add_parser(
        "class-activity-group-reorder", help="set the complete custom activity-group order"
    )
    activity_group_reorder.add_argument("course")
    activity_group_reorder.add_argument("groups", nargs="+")
    activity_group_reorder.add_argument("--class", dest="clazz")

    attendance_create = sub.add_parser(
        "class-attendance-create",
        help="preview or confirm creating and optionally starting an attendance activity",
    )
    attendance_create.add_argument("course")
    attendance_create.add_argument(
        "--mode", choices=("normal", "gesture", "location", "qr", "code"), default="normal"
    )
    attendance_create.add_argument("--title", default="")
    attendance_create.add_argument("--duration-minutes", type=int, default=30)
    attendance_create.add_argument("--manual-end", action="store_true")
    attendance_create.add_argument("--late-minutes", type=int, default=10)
    attendance_create.add_argument("--require-photo", action="store_true")
    attendance_create.add_argument("--qr-refresh-seconds", type=int, default=0)
    attendance_create.add_argument("--sign-code", default="")
    attendance_create.add_argument("--gesture-code", default="")
    attendance_create.add_argument("--location-name", default="")
    attendance_create.add_argument("--latitude")
    attendance_create.add_argument("--longitude")
    attendance_create.add_argument("--location-range-m", type=int, default=500)
    attendance_create.add_argument("--save", action="store_true")
    attendance_create.add_argument("--group", default="")
    attendance_create.add_argument("--class", dest="clazz")
    attendance_create.add_argument("--confirmation-token")

    activities = sub.add_parser("class-activities", help="list or filter class activities")
    activities.add_argument("course")
    activities.add_argument("--class", dest="clazz")
    activities.add_argument("--group", default="")
    activities.add_argument("--search", default="")
    activities.add_argument(
        "--status", choices=("not_started", "ongoing", "ended", "0", "1", "2"), default=""
    )
    activities.add_argument("--activity-type", type=int)

    activity_read = sub.add_parser("class-activity-read", help="read one class activity")
    activity_read.add_argument("course")
    activity_read.add_argument("activity")
    activity_read.add_argument("--class", dest="clazz")

    activity_rename = sub.add_parser("class-activity-rename", help="rename a class activity")
    activity_rename.add_argument("course")
    activity_rename.add_argument("activity")
    activity_rename.add_argument("name")
    activity_rename.add_argument("--class", dest="clazz")

    activity_move = sub.add_parser("class-activity-move", help="move an activity into a group")
    activity_move.add_argument("course")
    activity_move.add_argument("activity")
    activity_move.add_argument("group")
    activity_move.add_argument("--class", dest="clazz")

    activity_reorder = sub.add_parser(
        "class-activity-reorder", help="set the complete activity order in one group"
    )
    activity_reorder.add_argument("course")
    activity_reorder.add_argument("group")
    activity_reorder.add_argument("activities", nargs="+")
    activity_reorder.add_argument("--class", dest="clazz")

    activity_start = sub.add_parser(
        "class-activity-start", help="preview or confirm starting a class activity"
    )
    activity_start.add_argument("course")
    activity_start.add_argument("activity")
    activity_start.add_argument("--class", dest="clazz")
    activity_start.add_argument("--confirmation-token")

    activity_end = sub.add_parser(
        "class-activity-end", help="preview or confirm ending a class activity"
    )
    activity_end.add_argument("course")
    activity_end.add_argument("activity")
    activity_end.add_argument("--class", dest="clazz")
    activity_end.add_argument("--confirmation-token")

    activity_delete = sub.add_parser(
        "class-activity-delete", help="preview or confirm moving a class activity to recycle"
    )
    activity_delete.add_argument("course")
    activity_delete.add_argument("activity")
    activity_delete.add_argument("--class", dest="clazz")
    activity_delete.add_argument("--confirmation-token")

    activity_recycle = sub.add_parser(
        "class-activity-recycle", help="list or search class-activity recycle"
    )
    activity_recycle.add_argument("course")
    activity_recycle.add_argument("--class", dest="clazz")
    activity_recycle.add_argument("--search", default="")
    activity_recycle.add_argument("--max-items", type=int, default=1000)

    activity_restore = sub.add_parser(
        "class-activity-restore", help="restore a recycled class activity"
    )
    activity_restore.add_argument("course")
    activity_restore.add_argument("activity")
    activity_restore.add_argument("--class", dest="clazz")

    activity_recycle_delete = sub.add_parser(
        "class-activity-recycle-delete",
        help="preview or confirm permanently deleting recycled class activities",
    )
    activity_recycle_delete.add_argument("course")
    activity_recycle_delete.add_argument("activities", nargs="+")
    activity_recycle_delete.add_argument("--class", dest="clazz")
    activity_recycle_delete.add_argument("--confirmation-token")

    course_assets = sub.add_parser("course-assets", help="list courseware or teaching-plan items")
    course_assets.add_argument("course")
    course_assets.add_argument("kind", choices=("courseware", "teaching_plan"))
    course_assets.add_argument("--class", dest="clazz")
    course_assets.add_argument("--folder", default="")
    course_assets.add_argument("--search", default="")
    course_assets.add_argument("--page", type=int, default=1)
    course_assets.add_argument("--page-size", type=int, default=1000)

    course_asset_tree = sub.add_parser(
        "course-asset-tree", help="list the complete courseware or teaching-plan tree"
    )
    course_asset_tree.add_argument("course")
    course_asset_tree.add_argument("kind", choices=("courseware", "teaching_plan"))
    course_asset_tree.add_argument("--class", dest="clazz")
    course_asset_tree.add_argument("--search", default="")

    course_asset_folder = sub.add_parser(
        "course-asset-folder-create",
        help="preview or confirm creating a courseware or teaching-plan folder",
    )
    course_asset_folder.add_argument("course")
    course_asset_folder.add_argument("kind", choices=("courseware", "teaching_plan"))
    course_asset_folder.add_argument("name")
    course_asset_folder.add_argument("--class", dest="clazz")
    course_asset_folder.add_argument("--parent", default="")
    course_asset_folder.add_argument("--confirmation-token")

    course_asset_cloud_import = sub.add_parser(
        "course-asset-cloud-import",
        help="preview or confirm importing cloud-disk files into courseware or teaching plans",
    )
    course_asset_cloud_import.add_argument("course")
    course_asset_cloud_import.add_argument("kind", choices=("courseware", "teaching_plan"))
    course_asset_cloud_import.add_argument("resources", nargs="+")
    course_asset_cloud_import.add_argument("--class", dest="clazz")
    course_asset_cloud_import.add_argument("--destination", default="")
    course_asset_cloud_import.add_argument("--confirmation-token")

    course_asset_upload = sub.add_parser(
        "course-asset-upload",
        help="preview or confirm uploading a local file into courseware or teaching plans",
    )
    course_asset_upload.add_argument("course")
    course_asset_upload.add_argument("kind", choices=("courseware", "teaching_plan"))
    course_asset_upload.add_argument("file_path")
    course_asset_upload.add_argument("--class", dest="clazz")
    course_asset_upload.add_argument("--destination", default="")
    course_asset_upload.add_argument("--name", default="")
    course_asset_upload.add_argument("--confirmation-token")

    course_asset_rename = sub.add_parser(
        "course-asset-rename", help="rename a courseware or teaching-plan item"
    )
    course_asset_rename.add_argument("course")
    course_asset_rename.add_argument("kind", choices=("courseware", "teaching_plan"))
    course_asset_rename.add_argument("asset")
    course_asset_rename.add_argument("name")
    course_asset_rename.add_argument("--class", dest="clazz")

    course_asset_top = sub.add_parser(
        "course-asset-top", help="set or clear a courseware or teaching-plan top status"
    )
    course_asset_top.add_argument("course")
    course_asset_top.add_argument("kind", choices=("courseware", "teaching_plan"))
    course_asset_top.add_argument("asset")
    course_asset_top.add_argument("status", choices=("top", "untop"))
    course_asset_top.add_argument("--class", dest="clazz")

    course_asset_move = sub.add_parser(
        "course-asset-move", help="move courseware or teaching-plan items to a folder"
    )
    course_asset_move.add_argument("course")
    course_asset_move.add_argument("kind", choices=("courseware", "teaching_plan"))
    course_asset_move.add_argument("destination")
    course_asset_move.add_argument("assets", nargs="+")
    course_asset_move.add_argument("--class", dest="clazz")

    course_asset_copy = sub.add_parser(
        "course-asset-copy", help="preview or confirm copying courseware or a teaching plan"
    )
    course_asset_copy.add_argument("course")
    course_asset_copy.add_argument("kind", choices=("courseware", "teaching_plan"))
    course_asset_copy.add_argument("asset")
    course_asset_copy.add_argument("--class", dest="clazz")
    course_asset_copy.add_argument("--confirmation-token")

    course_asset_delete = sub.add_parser(
        "course-asset-delete", help="preview or confirm moving course assets to recycle"
    )
    course_asset_delete.add_argument("course")
    course_asset_delete.add_argument("kind", choices=("courseware", "teaching_plan"))
    course_asset_delete.add_argument("assets", nargs="+")
    course_asset_delete.add_argument("--class", dest="clazz")
    course_asset_delete.add_argument("--confirmation-token")

    course_asset_download = sub.add_parser(
        "course-asset-download", help="download one courseware or teaching-plan file"
    )
    course_asset_download.add_argument("course")
    course_asset_download.add_argument("kind", choices=("courseware", "teaching_plan"))
    course_asset_download.add_argument("asset")
    course_asset_download.add_argument("output_path")
    course_asset_download.add_argument("--class", dest="clazz")
    course_asset_download.add_argument("--overwrite", action="store_true")

    course_asset_recycle = sub.add_parser(
        "course-asset-recycle", help="list a courseware or teaching-plan recycle bin"
    )
    course_asset_recycle.add_argument("course")
    course_asset_recycle.add_argument("kind", choices=("courseware", "teaching_plan"))
    course_asset_recycle.add_argument("--class", dest="clazz")
    course_asset_recycle.add_argument("--search", default="")

    course_asset_restore = sub.add_parser(
        "course-asset-restore", help="preview or confirm restoring recycled course assets"
    )
    course_asset_restore.add_argument("course")
    course_asset_restore.add_argument("kind", choices=("courseware", "teaching_plan"))
    course_asset_restore.add_argument("assets", nargs="+")
    course_asset_restore.add_argument("--class", dest="clazz")
    course_asset_restore.add_argument("--confirmation-token")

    course_asset_recycle_delete = sub.add_parser(
        "course-asset-recycle-delete",
        help="preview or confirm permanently deleting recycled course assets",
    )
    course_asset_recycle_delete.add_argument("course")
    course_asset_recycle_delete.add_argument("kind", choices=("courseware", "teaching_plan"))
    course_asset_recycle_delete.add_argument("assets", nargs="+")
    course_asset_recycle_delete.add_argument("--class", dest="clazz")
    course_asset_recycle_delete.add_argument("--confirmation-token")

    chapters = sub.add_parser("chapters", help="list the structured chapter hierarchy")
    chapters.add_argument("course")
    chapters.add_argument("--class", dest="clazz")
    chapters.add_argument("--search", default="")

    chapter_tree = sub.add_parser("chapter-tree", help="list the complete editable chapter tree")
    chapter_tree.add_argument("course")
    chapter_tree.add_argument("--class", dest="clazz")

    chapter_cards = sub.add_parser("chapter-cards", help="read pages and content in one chapter")
    chapter_cards.add_argument("course")
    chapter_cards.add_argument("chapter")
    chapter_cards.add_argument("--class", dest="clazz")

    chapter_card_create = sub.add_parser(
        "chapter-card-create", help="create a page inside one chapter"
    )
    chapter_card_create.add_argument("course")
    chapter_card_create.add_argument("chapter")
    chapter_card_create.add_argument("title")
    chapter_card_create.add_argument("--class", dest="clazz")
    chapter_card_create.add_argument("--content", default="")
    chapter_card_create.add_argument("--content-format", choices=("plain", "html"), default="plain")

    chapter_card_update = sub.add_parser(
        "chapter-card-update", help="update a chapter page title or content"
    )
    chapter_card_update.add_argument("course")
    chapter_card_update.add_argument("chapter")
    chapter_card_update.add_argument("card")
    chapter_card_update.add_argument("--class", dest="clazz")
    chapter_card_update.add_argument("--title")
    chapter_card_update.add_argument("--content")
    chapter_card_update.add_argument("--content-format", choices=("plain", "html"), default="plain")

    chapter_card_move = sub.add_parser(
        "chapter-card-move", help="move a chapter page to a one-based position"
    )
    chapter_card_move.add_argument("course")
    chapter_card_move.add_argument("chapter")
    chapter_card_move.add_argument("card")
    chapter_card_move.add_argument("target_position", type=int)
    chapter_card_move.add_argument("--class", dest="clazz")

    chapter_card_delete = sub.add_parser(
        "chapter-card-delete", help="preview or confirm permanently deleting a chapter page"
    )
    chapter_card_delete.add_argument("course")
    chapter_card_delete.add_argument("chapter")
    chapter_card_delete.add_argument("card")
    chapter_card_delete.add_argument("--class", dest="clazz")
    chapter_card_delete.add_argument("--confirmation-token")

    chapter_create = sub.add_parser("chapter-create", help="create a chapter or subchapter")
    chapter_create.add_argument("course")
    chapter_create.add_argument("title")
    chapter_create.add_argument("--class", dest="clazz")
    chapter_create.add_argument("--parent", default="")
    chapter_create.add_argument("--before", default="")

    chapter_rename = sub.add_parser("chapter-rename", help="rename a chapter")
    chapter_rename.add_argument("course")
    chapter_rename.add_argument("chapter")
    chapter_rename.add_argument("title")
    chapter_rename.add_argument("--class", dest="clazz")

    chapter_move = sub.add_parser("chapter-move", help="move or reorder a chapter")
    chapter_move.add_argument("course")
    chapter_move.add_argument("chapter")
    chapter_move.add_argument("--class", dest="clazz")
    chapter_move_target = chapter_move.add_mutually_exclusive_group(required=True)
    chapter_move_target.add_argument("--parent")
    chapter_move_target.add_argument("--relative-to")
    chapter_move.add_argument("--position", choices=("before", "after"), default="after")

    chapter_import = sub.add_parser(
        "chapter-import-outline", help="import an indented plain-text chapter outline"
    )
    chapter_import.add_argument("course")
    chapter_import.add_argument("outline")
    chapter_import.add_argument("--class", dest="clazz")

    chapter_status = sub.add_parser(
        "chapter-status", help="preview or confirm chapter open-status changes"
    )
    chapter_status.add_argument("course")
    chapter_status.add_argument("status", choices=("open", "task", "time", "close", "review"))
    chapter_status.add_argument("chapters", nargs="+")
    chapter_status.add_argument("--class", dest="clazz")
    chapter_status.add_argument("--target-class", dest="classes", action="append")
    chapter_status.add_argument("--begin", default="")
    chapter_status.add_argument("--end", default="")
    chapter_status.add_argument("--time-end-review", action="store_true")
    chapter_status.add_argument("--confirmation-token")

    chapter_delete = sub.add_parser(
        "chapter-delete", help="preview or confirm deleting chapters and descendants"
    )
    chapter_delete.add_argument("course")
    chapter_delete.add_argument("chapters", nargs="+")
    chapter_delete.add_argument("--class", dest="clazz")
    chapter_delete.add_argument("--confirmation-token")

    resources = sub.add_parser("resources", help="list course resource files and folders")
    resources.add_argument("course")
    resources.add_argument("--class", dest="clazz")
    resources.add_argument("--folder", default="")
    resources.add_argument("--search", default="")

    resource_tree = sub.add_parser("resource-tree", help="list the complete resource tree")
    resource_tree.add_argument("course")
    resource_tree.add_argument("--class", dest="clazz")
    resource_tree.add_argument("--search", default="")

    resource_download = sub.add_parser(
        "resource-download", help="download one course resource file"
    )
    resource_download.add_argument("course")
    resource_download.add_argument("resource")
    resource_download.add_argument("output_path")
    resource_download.add_argument("--class", dest="clazz")
    resource_download.add_argument("--overwrite", action="store_true")

    resource_download_items = sub.add_parser(
        "resource-download-items",
        help="download multiple course resources or folders without the client",
    )
    resource_download_items.add_argument("course")
    resource_download_items.add_argument("output_path")
    resource_download_items.add_argument("resources", nargs="+")
    resource_download_items.add_argument("--class", dest="clazz")
    resource_download_items.add_argument("--overwrite", action="store_true")

    resource_folder_create = sub.add_parser(
        "resource-folder-create", help="preview or confirm creating a resource folder"
    )
    resource_folder_create.add_argument("course")
    resource_folder_create.add_argument("name")
    resource_folder_create.add_argument("--class", dest="clazz")
    resource_folder_create.add_argument("--parent", default="")
    resource_folder_create.add_argument("--confirmation-token")

    resource_rename = sub.add_parser("resource-rename", help="rename a resource")
    resource_rename.add_argument("course")
    resource_rename.add_argument("resource")
    resource_rename.add_argument("name")
    resource_rename.add_argument("--class", dest="clazz")

    resource_move = sub.add_parser("resource-move", help="move resources to a folder")
    resource_move.add_argument("course")
    resource_move.add_argument("destination")
    resource_move.add_argument("resources", nargs="+")
    resource_move.add_argument("--class", dest="clazz")

    resource_reorder = sub.add_parser(
        "resource-reorder", help="replace the complete order inside a resource folder"
    )
    resource_reorder.add_argument("course")
    resource_reorder.add_argument("resources", nargs="+")
    resource_reorder.add_argument("--class", dest="clazz")
    resource_reorder.add_argument("--folder", default="")

    resource_top = sub.add_parser("resource-top", help="set or clear one resource's top status")
    resource_top.add_argument("course")
    resource_top.add_argument("resource")
    resource_top.add_argument("status", choices=("top", "untop"))
    resource_top.add_argument("--class", dest="clazz")

    resource_copy = sub.add_parser(
        "resource-copy", help="preview or confirm copying one course resource"
    )
    resource_copy.add_argument("course")
    resource_copy.add_argument("resource")
    resource_copy.add_argument("--class", dest="clazz")
    resource_copy.add_argument("--confirmation-token")

    resource_copy_to_cloud = sub.add_parser(
        "resource-copy-to-cloud",
        help="preview or confirm copying a course file to personal cloud disk",
    )
    resource_copy_to_cloud.add_argument("course")
    resource_copy_to_cloud.add_argument("resource")
    resource_copy_to_cloud.add_argument("--class", dest="clazz")
    resource_copy_to_cloud.add_argument("--destination", default="")
    resource_copy_to_cloud.add_argument("--confirmation-token")

    resource_cloud_sources = sub.add_parser(
        "resource-cloud-sources",
        help="list cloud-disk sources exposed by the course resource interface",
    )
    resource_cloud_sources.add_argument("course")
    resource_cloud_sources.add_argument("--class", dest="clazz")
    resource_cloud_sources.add_argument("--path", default="")
    resource_cloud_sources.add_argument("--search", default="")
    resource_cloud_sources.add_argument("--page", type=int, default=1)
    resource_cloud_sources.add_argument("--page-size", type=int, default=1000)
    resource_cloud_sources.add_argument("--share-id", default="0")

    resource_cloud_import = sub.add_parser(
        "resource-cloud-import",
        help="preview or confirm importing cloud files into course resources",
    )
    resource_cloud_import.add_argument("course")
    resource_cloud_import.add_argument("resources", nargs="+")
    resource_cloud_import.add_argument("--class", dest="clazz")
    resource_cloud_import.add_argument("--source-path", default="")
    resource_cloud_import.add_argument("--destination", default="")
    resource_cloud_import.add_argument("--share-id", default="0")
    resource_cloud_import.add_argument("--confirmation-token")

    resource_cloud_folder_import = sub.add_parser(
        "resource-cloud-folder-import",
        help="preview or confirm importing one cloud folder into course resources",
    )
    resource_cloud_folder_import.add_argument("course")
    resource_cloud_folder_import.add_argument("resource")
    resource_cloud_folder_import.add_argument("--class", dest="clazz")
    resource_cloud_folder_import.add_argument("--source-path", default="")
    resource_cloud_folder_import.add_argument("--destination", default="")
    resource_cloud_folder_import.add_argument("--share-id", default="0")
    resource_cloud_folder_import.add_argument("--confirmation-token")

    resource_labels = sub.add_parser(
        "resource-labels", help="list labels available to one course resource"
    )
    resource_labels.add_argument("course")
    resource_labels.add_argument("resource")
    resource_labels.add_argument("--class", dest="clazz")
    resource_labels.add_argument("--search", default="")

    resource_label_create = sub.add_parser(
        "resource-label-create", help="create a course resource label"
    )
    resource_label_create.add_argument("course")
    resource_label_create.add_argument("resource")
    resource_label_create.add_argument("name")
    resource_label_create.add_argument("--class", dest="clazz")

    resource_label_rename = sub.add_parser(
        "resource-label-rename", help="rename an editable course resource label"
    )
    resource_label_rename.add_argument("course")
    resource_label_rename.add_argument("resource")
    resource_label_rename.add_argument("label")
    resource_label_rename.add_argument("name")
    resource_label_rename.add_argument("--class", dest="clazz")

    resource_label_delete = sub.add_parser(
        "resource-label-delete", help="preview or confirm deleting a course resource label"
    )
    resource_label_delete.add_argument("course")
    resource_label_delete.add_argument("resource")
    resource_label_delete.add_argument("label")
    resource_label_delete.add_argument("--class", dest="clazz")
    resource_label_delete.add_argument("--confirmation-token")

    resource_labels_update = sub.add_parser(
        "resource-labels-update",
        help="preview or confirm replacing the complete label set on course resources",
    )
    resource_labels_update.add_argument("course")
    resource_labels_update.add_argument("resources", nargs="+")
    resource_labels_update.add_argument("--class", dest="clazz")
    resource_labels_update.add_argument("--label", dest="labels", action="append", default=[])
    resource_labels_update.add_argument("--confirmation-token")

    resource_delete = sub.add_parser(
        "resource-delete", help="preview or confirm deleting resources"
    )
    resource_delete.add_argument("course")
    resource_delete.add_argument("resources", nargs="+")
    resource_delete.add_argument("--class", dest="clazz")
    resource_delete.add_argument("--confirmation-token")

    resource_link_create = sub.add_parser(
        "resource-link-create", help="preview or confirm publishing a URL resource"
    )
    resource_link_create.add_argument("course")
    resource_link_create.add_argument("name")
    resource_link_create.add_argument("url")
    resource_link_create.add_argument("--class", dest="clazz")
    resource_link_create.add_argument("--parent", default="")
    resource_link_create.add_argument("--confirmation-token")

    resource_upload = sub.add_parser(
        "resource-upload", help="preview or confirm uploading a local resource file"
    )
    resource_upload.add_argument("course")
    resource_upload.add_argument("file_path")
    resource_upload.add_argument("--class", dest="clazz")
    resource_upload.add_argument("--parent", default="")
    resource_upload.add_argument("--name", default="")
    resource_upload.add_argument("--confirmation-token")

    resource_download_permission = sub.add_parser(
        "resource-download-permission",
        help="preview or confirm allowing or denying resource downloads",
    )
    resource_download_permission.add_argument("course")
    resource_download_permission.add_argument("permission", choices=("allow", "deny"))
    resource_download_permission.add_argument("resources", nargs="+")
    resource_download_permission.add_argument("--class", dest="clazz")
    resource_download_permission.add_argument("--confirmation-token")

    resource_visibility = sub.add_parser(
        "resource-visibility", help="read a resource folder's class and teacher visibility"
    )
    resource_visibility.add_argument("course")
    resource_visibility.add_argument("folder")
    resource_visibility.add_argument("--class", dest="clazz")

    resource_visibility_update = sub.add_parser(
        "resource-visibility-update",
        help="preview or confirm a resource folder visibility update",
    )
    resource_visibility_update.add_argument("course")
    resource_visibility_update.add_argument("folder")
    resource_visibility_update.add_argument(
        "mode", choices=("all_classes", "selected_classes", "no_classes")
    )
    resource_visibility_update.add_argument("--class", dest="clazz")
    resource_visibility_update.add_argument("--visible-class", dest="classes", action="append")
    resource_visibility_update.add_argument("--teacher-id", dest="teacher_ids", action="append")
    resource_visibility_update.add_argument(
        "--all-teachers", action=argparse.BooleanOptionalAction, default=None
    )
    resource_visibility_update.add_argument("--confirmation-token")

    resource_readers = sub.add_parser("resource-readers", help="list readers and non-readers")
    resource_readers.add_argument("course")
    resource_readers.add_argument("resource")
    resource_readers.add_argument("--class", dest="clazz")
    resource_readers.add_argument("--reader-class")

    resource_downloaders = sub.add_parser(
        "resource-downloaders", help="list resource download records"
    )
    resource_downloaders.add_argument("course")
    resource_downloaders.add_argument("resource")
    resource_downloaders.add_argument("--class", dest="clazz")

    resource_import_courses = sub.add_parser(
        "resource-import-courses", help="list courses available as resource import sources"
    )
    resource_import_courses.add_argument("course")
    resource_import_courses.add_argument("--class", dest="clazz")
    resource_import_courses.add_argument("--search", default="")

    resource_import_items = sub.add_parser(
        "resource-import-items", help="list resources in one source course folder"
    )
    resource_import_items.add_argument("course")
    resource_import_items.add_argument("source_course")
    resource_import_items.add_argument("--class", dest="clazz")
    resource_import_items.add_argument("--folder-id", default="")
    resource_import_items.add_argument("--search", default="")
    resource_import_items.add_argument("--page", type=int, default=1)
    resource_import_items.add_argument("--page-size", type=int, default=100)

    resource_import = sub.add_parser(
        "resource-import", help="preview or confirm importing resources from another course"
    )
    resource_import.add_argument("course")
    resource_import.add_argument("source_course")
    resource_import.add_argument("resources", nargs="+")
    resource_import.add_argument("--class", dest="clazz")
    resource_import.add_argument("--source-folder-id", default="")
    resource_import.add_argument("--destination", default="")
    resource_import.add_argument("--confirmation-token")

    resource_share_link = sub.add_parser(
        "resource-share-link", help="preview or confirm creating a resource share URL"
    )
    resource_share_link.add_argument("course")
    resource_share_link.add_argument("resource")
    resource_share_link.add_argument("--class", dest="clazz")
    resource_share_link.add_argument("--confirmation-token")

    cloud_list = sub.add_parser(
        "cloud-list", help="list or search personal cloud-disk items through HTTP"
    )
    cloud_list.add_argument("--parent", default="")
    cloud_list.add_argument("--search", default="")
    cloud_list.add_argument("--page", type=int, default=1)
    cloud_list.add_argument("--page-size", type=int, default=100)

    cloud_read = sub.add_parser("cloud-read", help="read one active cloud-disk item")
    cloud_read.add_argument("resource")

    cloud_delete = sub.add_parser(
        "cloud-delete", help="preview or confirm deleting personal cloud-disk items"
    )
    cloud_delete.add_argument("resources", nargs="+")
    cloud_delete.add_argument("--confirmation-token")

    cloud_folder_create = sub.add_parser(
        "cloud-folder-create", help="preview or confirm creating a cloud-disk folder"
    )
    cloud_folder_create.add_argument("name")
    cloud_folder_create.add_argument("--parent", default="")
    cloud_folder_create.add_argument("--shared", action="store_true")
    cloud_folder_create.add_argument("--confirmation-token")

    cloud_rename = sub.add_parser("cloud-rename", help="rename one cloud-disk item")
    cloud_rename.add_argument("resource")
    cloud_rename.add_argument("name")

    cloud_move = sub.add_parser("cloud-move", help="move cloud-disk items to a folder")
    cloud_move.add_argument("destination")
    cloud_move.add_argument("resources", nargs="+")

    cloud_top = sub.add_parser("cloud-top", help="set or clear cloud-disk top status")
    cloud_top.add_argument("resource")
    cloud_top.add_argument("status", choices=("top", "untop"))

    cloud_download = sub.add_parser(
        "cloud-download", help="download cloud-disk files or folders without the client"
    )
    cloud_download.add_argument("output_path")
    cloud_download.add_argument("resources", nargs="+")
    cloud_download.add_argument("--overwrite", action="store_true")

    cloud_recycle = sub.add_parser("cloud-recycle", help="list cloud-disk recycle items")
    cloud_recycle.add_argument("--page", type=int, default=1)
    cloud_recycle.add_argument("--page-size", type=int, default=100)

    cloud_restore = sub.add_parser(
        "cloud-restore", help="preview or confirm restoring cloud-disk recycle items"
    )
    cloud_restore.add_argument("resources", nargs="+")
    cloud_restore.add_argument(
        "--conflict-policy", choices=("keep_both", "replace"), default="keep_both"
    )
    cloud_restore.add_argument("--confirmation-token")

    cloud_recycle_delete = sub.add_parser(
        "cloud-recycle-delete",
        help="preview or confirm permanently deleting cloud-disk recycle items",
    )
    cloud_recycle_delete.add_argument("resources", nargs="+")
    cloud_recycle_delete.add_argument("--confirmation-token")

    cloud_recycle_empty = sub.add_parser(
        "cloud-recycle-empty", help="preview or confirm emptying cloud-disk recycle"
    )
    cloud_recycle_empty.add_argument("--confirmation-token")

    homework_library = sub.add_parser(
        "homework-library", help="list reusable homework and folders through HTTP"
    )
    homework_library.add_argument("course")
    homework_library.add_argument("--class", dest="clazz")
    homework_library.add_argument("--directory", default="0")
    homework_library.add_argument("--search", default="")

    homework_read = sub.add_parser(
        "homework-read", help="read questions and answers from a homework or draft"
    )
    homework_read.add_argument("course")
    homework_read.add_argument("homework")
    homework_read.add_argument("--class", dest="clazz")
    homework_read.add_argument("--question", default="")

    homework_question_add = sub.add_parser(
        "homework-question-add", help="add a question to a homework or draft"
    )
    homework_question_add.add_argument("course")
    homework_question_add.add_argument("homework")
    homework_question_add.add_argument("question_type")
    homework_question_add.add_argument("stem")
    homework_question_add.add_argument("--class", dest="clazz")
    homework_question_add.add_argument("--score", type=float, default=5)
    homework_question_add.add_argument("--option", dest="options", action="append")
    homework_question_add.add_argument("--correct-answer", default="")
    homework_question_add.add_argument("--blank-answer", dest="answers", action="append")
    homework_question_add.add_argument("--answer", default="")
    homework_question_add.add_argument("--analysis", default="")
    homework_question_add.add_argument("--difficulty", type=float, default=0.8)
    homework_question_add.add_argument(
        "--content-format", choices=("plain", "html"), default="plain"
    )

    homework_question_update = sub.add_parser(
        "homework-question-update", help="update selected fields of one homework question"
    )
    homework_question_update.add_argument("course")
    homework_question_update.add_argument("homework")
    homework_question_update.add_argument("question")
    homework_question_update.add_argument("--class", dest="clazz")
    homework_question_update.add_argument("--stem")
    homework_question_update.add_argument("--score", type=float)
    homework_question_update.add_argument("--option", dest="options", action="append")
    homework_question_update.add_argument("--correct-answer")
    homework_question_update.add_argument("--blank-answer", dest="answers", action="append")
    homework_question_update.add_argument("--answer")
    homework_question_update.add_argument("--analysis")
    homework_question_update.add_argument("--difficulty", type=float)
    homework_question_update.add_argument(
        "--content-format", choices=("plain", "html"), default="plain"
    )

    homework_question_delete = sub.add_parser(
        "homework-question-delete", help="preview or confirm deleting one homework question"
    )
    homework_question_delete.add_argument("course")
    homework_question_delete.add_argument("homework")
    homework_question_delete.add_argument("question")
    homework_question_delete.add_argument("--class", dest="clazz")
    homework_question_delete.add_argument("--confirmation-token")

    homework_drafts = sub.add_parser(
        "homework-drafts", help="list unpublished homework drafts through HTTP"
    )
    homework_drafts.add_argument("course")
    homework_drafts.add_argument("--class", dest="clazz")
    homework_drafts.add_argument("--search", default="")

    homework_draft_create = sub.add_parser(
        "homework-draft-create", help="create an unpublished homework draft"
    )
    homework_draft_create.add_argument("course")
    homework_draft_create.add_argument("title")
    homework_draft_create.add_argument("--class", dest="clazz")
    homework_draft_create.add_argument("--directory", default="0")

    homework_draft_update = sub.add_parser(
        "homework-draft-update", help="rename an unpublished homework draft"
    )
    homework_draft_update.add_argument("course")
    homework_draft_update.add_argument("draft")
    homework_draft_update.add_argument("title")
    homework_draft_update.add_argument("--class", dest="clazz")

    homework_draft_delete = sub.add_parser(
        "homework-draft-delete", help="preview or confirm permanently deleting a draft"
    )
    homework_draft_delete.add_argument("course")
    homework_draft_delete.add_argument("draft")
    homework_draft_delete.add_argument("--class", dest="clazz")
    homework_draft_delete.add_argument("--confirmation-token")

    homework_publish = sub.add_parser(
        "homework-publish", help="preview or confirm publishing a homework-library item"
    )
    homework_publish.add_argument("course")
    homework_publish.add_argument("homework")
    homework_publish.add_argument("--class", dest="clazz")
    homework_publish.add_argument("--target-class", dest="target_classes", action="append")
    homework_publish.add_argument("--start", dest="start_time", default="now")
    homework_publish.add_argument("--end", dest="end_time", default="")
    homework_publish.add_argument("--allow-late", dest="allow_late_submission", action="store_true")
    homework_publish.add_argument("--late-deadline", default="")
    homework_publish.add_argument("--passing-score", type=float, default=0)
    homework_publish.add_argument("--redo-times", type=int, default=0)
    homework_publish.add_argument("--no-paste", dest="allow_paste", action="store_false")
    homework_publish.add_argument("--hide-score", dest="show_score", action="store_false")
    homework_publish.add_argument(
        "--hide-correctness", dest="show_correctness", action="store_false"
    )
    homework_publish.add_argument("--randomize-questions", action="store_true")
    homework_publish.add_argument("--randomize-options", action="store_true")
    homework_publish.add_argument("--confirmation-token")

    homeworks = sub.add_parser("homeworks", help="list course homeworks through HTTP")
    homeworks.add_argument("course")
    homeworks.add_argument("--class", dest="clazz")
    homeworks.add_argument("--ungraded", action="store_true")

    submissions = sub.add_parser(
        "submissions", help="list submissions for one homework through HTTP"
    )
    submissions.add_argument("course")
    submissions.add_argument("homework")
    submissions.add_argument("--class", dest="clazz")
    submissions.add_argument("--status", type=int, choices=(0, 3, 4), default=0)

    review = sub.add_parser("review", help="read one student's homework answer through HTTP")
    review.add_argument("course")
    review.add_argument("homework")
    review.add_argument("submission")
    review.add_argument("--class", dest="clazz")
    review.add_argument("--max-chars", type=int, default=4000)

    score = sub.add_parser("score", help="preview or confirm one homework score")
    score.add_argument("course")
    score.add_argument("homework")
    score.add_argument("submission")
    score.add_argument("score")
    score.add_argument("--class", dest="clazz")
    score.add_argument("--confirmation-token")

    notices = sub.add_parser("notices", help="list course notices through HTTP")
    notices.add_argument("course")
    notices.add_argument("--class", dest="clazz")
    notices.add_argument("--search", default="")

    notice_drafts = sub.add_parser("notice-drafts", help="list course notice drafts through HTTP")
    notice_drafts.add_argument("course")
    notice_drafts.add_argument("--search", default="")
    notice_drafts.add_argument("--page-size", type=int, default=100)

    notice_draft_save = sub.add_parser(
        "notice-draft-save", help="save a course notice draft without publishing"
    )
    notice_draft_save.add_argument("course")
    notice_draft_save.add_argument("title")
    notice_draft_save.add_argument("content")
    notice_draft_save.add_argument("--class", dest="clazz")
    notice_draft_save.add_argument("--recipient-class", dest="recipient_classes", action="append")
    notice_draft_save.add_argument("--draft")
    notice_draft_save.add_argument("--clear-schedule", action="store_true")
    notice_draft_save.add_argument("--disable-comments", action="store_true")
    notice_draft_save.add_argument("--show-comments", action="store_true")
    notice_draft_save.add_argument("--hide-read-status", action="store_true")

    notice_schedule = sub.add_parser(
        "notice-schedule", help="preview or confirm a scheduled class notice"
    )
    notice_schedule.add_argument("course")
    notice_schedule.add_argument("title")
    notice_schedule.add_argument("content")
    notice_schedule.add_argument("send_at")
    notice_schedule.add_argument("--class", dest="clazz")
    notice_schedule.add_argument("--recipient-class", dest="recipient_classes", action="append")
    notice_schedule.add_argument("--draft")
    notice_schedule.add_argument("--disable-comments", action="store_true")
    notice_schedule.add_argument("--show-comments", action="store_true")
    notice_schedule.add_argument("--hide-read-status", action="store_true")
    notice_schedule.add_argument("--confirmation-token")

    notice_draft_delete = sub.add_parser(
        "notice-draft-delete", help="preview or confirm deleting a notice draft"
    )
    notice_draft_delete.add_argument("course")
    notice_draft_delete.add_argument("draft")
    notice_draft_delete.add_argument("--confirmation-token")

    notice_send = sub.add_parser("notice-send", help="preview or confirm a class notice")
    notice_send.add_argument("course")
    notice_send.add_argument("title")
    notice_send.add_argument("content")
    notice_send.add_argument("--class", dest="clazz")
    notice_send.add_argument("--recipient-class", dest="recipient_classes", action="append")
    notice_send.add_argument("--disable-comments", action="store_true")
    notice_send.add_argument("--show-comments", action="store_true")
    notice_send.add_argument("--hide-read-status", action="store_true")
    notice_send.add_argument("--confirmation-token")

    notice_edit = sub.add_parser("notice-edit", help="preview or confirm editing a notice")
    notice_edit.add_argument("course")
    notice_edit.add_argument("notice")
    notice_edit.add_argument("title")
    notice_edit.add_argument("content")
    notice_edit.add_argument("--class", dest="clazz")
    notice_edit.add_argument("--confirmation-token")

    notice_top = sub.add_parser("notice-top", help="preview or confirm notice top status")
    notice_top.add_argument("course")
    notice_top.add_argument("notice")
    notice_top.add_argument("--class", dest="clazz")
    notice_top.add_argument("--off", action="store_true")
    notice_top.add_argument("--confirmation-token")

    notice_recall = sub.add_parser("notice-recall", help="preview or confirm recalling a notice")
    notice_recall.add_argument("course")
    notice_recall.add_argument("notice")
    notice_recall.add_argument("--class", dest="clazz")
    notice_recall.add_argument("--confirmation-token")

    notice_delete = sub.add_parser("notice-delete", help="preview or confirm deleting a notice")
    notice_delete.add_argument("course")
    notice_delete.add_argument("notice")
    notice_delete.add_argument("--class", dest="clazz")
    notice_delete.add_argument("--confirmation-token")

    exams = sub.add_parser("exams", help="list course exams through HTTP")
    exams.add_argument("course")
    exams.add_argument("--class", dest="clazz")
    exams.add_argument("--status", type=int, choices=(-1, 0, 1, 2), default=-1)
    exams.add_argument("--search", default="")

    exam_papers = sub.add_parser(
        "exam-papers", help="list folders and papers in the exam paper library"
    )
    exam_papers.add_argument("course")
    exam_papers.add_argument("--class", dest="clazz")
    exam_papers.add_argument("--directory-id", default="0")
    exam_papers.add_argument("--search", default="")
    exam_papers.add_argument("--page-size", type=int, default=100)

    exam_paper = sub.add_parser(
        "exam-paper", help="read a complete exam paper or one selected question"
    )
    exam_paper.add_argument("course")
    exam_paper.add_argument("paper")
    exam_paper.add_argument("--class", dest="clazz")
    exam_paper.add_argument("--directory-id", default="0")
    exam_paper.add_argument("--question", default="")

    exam_paper_settings = sub.add_parser(
        "exam-paper-settings", help="read exam-paper difficulty and numbering settings"
    )
    exam_paper_settings.add_argument("course")
    exam_paper_settings.add_argument("paper")
    exam_paper_settings.add_argument("--class", dest="clazz")
    exam_paper_settings.add_argument("--directory-id", default="0")
    exam_paper_settings.add_argument("--group-id", default="0")

    exam_paper_settings_update = sub.add_parser(
        "exam-paper-settings-update", help="update selected exam-paper editor settings"
    )
    exam_paper_settings_update.add_argument("course")
    exam_paper_settings_update.add_argument("paper")
    exam_paper_settings_update.add_argument("--class", dest="clazz")
    exam_paper_settings_update.add_argument("--difficulty")
    exam_paper_settings_update.add_argument("--numbering")
    exam_paper_settings_update.add_argument("--grouping")
    exam_paper_settings_update.add_argument("--subquestion-numbering")
    exam_paper_settings_update.add_argument("--directory-id", default="0")
    exam_paper_settings_update.add_argument("--group-id", default="0")

    exam_question_add = sub.add_parser(
        "exam-question-add", help="add a core question to an unpublished exam paper"
    )
    exam_question_add.add_argument("course")
    exam_question_add.add_argument("paper")
    exam_question_add.add_argument("question_type")
    exam_question_add.add_argument("stem")
    exam_question_add.add_argument("--class", dest="clazz")
    exam_question_add.add_argument("--score", type=float, default=5)
    exam_question_add.add_argument("--option", dest="options", action="append")
    exam_question_add.add_argument("--correct-answer")
    exam_question_add.add_argument("--blank-answer", dest="answers", action="append")
    exam_question_add.add_argument("--answer")
    exam_question_add.add_argument("--analysis", default="")
    exam_question_add.add_argument("--difficulty", type=float, default=0.8)
    exam_question_add.add_argument("--content-format", choices=("plain", "html"), default="plain")
    exam_question_add.add_argument("--directory-id", default="0")
    exam_question_add.add_argument("--group-id", default="0")

    exam_question_update = sub.add_parser(
        "exam-question-update", help="update selected fields of one exam-paper question"
    )
    exam_question_update.add_argument("course")
    exam_question_update.add_argument("paper")
    exam_question_update.add_argument("question")
    exam_question_update.add_argument("--class", dest="clazz")
    exam_question_update.add_argument("--stem")
    exam_question_update.add_argument("--score", type=float)
    exam_question_update.add_argument("--option", dest="options", action="append")
    exam_question_update.add_argument("--correct-answer")
    exam_question_update.add_argument("--blank-answer", dest="answers", action="append")
    exam_question_update.add_argument("--answer")
    exam_question_update.add_argument("--analysis")
    exam_question_update.add_argument("--difficulty", type=float)
    exam_question_update.add_argument(
        "--content-format", choices=("plain", "html"), default="plain"
    )
    exam_question_update.add_argument("--directory-id", default="0")
    exam_question_update.add_argument("--group-id", default="0")

    exam_question_delete = sub.add_parser(
        "exam-question-delete", help="preview or confirm deleting one exam-paper question"
    )
    exam_question_delete.add_argument("course")
    exam_question_delete.add_argument("paper")
    exam_question_delete.add_argument("question")
    exam_question_delete.add_argument("--class", dest="clazz")
    exam_question_delete.add_argument("--directory-id", default="0")
    exam_question_delete.add_argument("--group-id", default="0")
    exam_question_delete.add_argument("--confirmation-token")

    exam_question_move = sub.add_parser(
        "exam-question-move", help="move one exam-paper question to a 1-based position"
    )
    exam_question_move.add_argument("course")
    exam_question_move.add_argument("paper")
    exam_question_move.add_argument("question")
    exam_question_move.add_argument("target_position", type=int)
    exam_question_move.add_argument("--class", dest="clazz")
    exam_question_move.add_argument("--directory-id", default="0")
    exam_question_move.add_argument("--group-id", default="0")

    exam_question_type_update = sub.add_parser(
        "exam-question-type-update", help="update a paper question type's description or score"
    )
    exam_question_type_update.add_argument("course")
    exam_question_type_update.add_argument("paper")
    exam_question_type_update.add_argument("question_type")
    exam_question_type_update.add_argument("--description")
    exam_question_type_update.add_argument("--total-score", type=float)
    exam_question_type_update.add_argument("--class", dest="clazz")
    exam_question_type_update.add_argument("--directory-id", default="0")
    exam_question_type_update.add_argument("--group-id", default="0")

    exam_question_type_move = sub.add_parser(
        "exam-question-type-move", help="move one exam-paper question type to a 1-based position"
    )
    exam_question_type_move.add_argument("course")
    exam_question_type_move.add_argument("paper")
    exam_question_type_move.add_argument("question_type")
    exam_question_type_move.add_argument("target_position", type=int)
    exam_question_type_move.add_argument("--class", dest="clazz")
    exam_question_type_move.add_argument("--directory-id", default="0")
    exam_question_type_move.add_argument("--group-id", default="0")

    exam_question_type_delete = sub.add_parser(
        "exam-question-type-delete",
        help="preview or confirm deleting a type and all of its paper questions",
    )
    exam_question_type_delete.add_argument("course")
    exam_question_type_delete.add_argument("paper")
    exam_question_type_delete.add_argument("question_type")
    exam_question_type_delete.add_argument("--class", dest="clazz")
    exam_question_type_delete.add_argument("--directory-id", default="0")
    exam_question_type_delete.add_argument("--group-id", default="0")
    exam_question_type_delete.add_argument("--confirmation-token")

    exam_paper_create = sub.add_parser(
        "exam-paper-create", help="create an unpublished empty exam paper"
    )
    exam_paper_create.add_argument("course")
    exam_paper_create.add_argument("title", nargs="?", default="")
    exam_paper_create.add_argument("--class", dest="clazz")
    exam_paper_create.add_argument("--directory-id", default="0")

    exam_paper_rename = sub.add_parser("exam-paper-rename", help="rename an exam paper")
    exam_paper_rename.add_argument("course")
    exam_paper_rename.add_argument("paper")
    exam_paper_rename.add_argument("title")
    exam_paper_rename.add_argument("--class", dest="clazz")
    exam_paper_rename.add_argument("--directory-id", default="0")
    exam_paper_rename.add_argument("--sync-parallel-titles", action="store_true")

    exam_paper_copy = sub.add_parser("exam-paper-copy", help="copy an exam paper")
    exam_paper_copy.add_argument("course")
    exam_paper_copy.add_argument("paper")
    exam_paper_copy.add_argument("--class", dest="clazz")
    exam_paper_copy.add_argument("--directory-id", default="0")

    exam_paper_move = sub.add_parser("exam-paper-move", help="move an exam paper")
    exam_paper_move.add_argument("course")
    exam_paper_move.add_argument("paper")
    exam_paper_move.add_argument("target_directory_id")
    exam_paper_move.add_argument("--class", dest="clazz")
    exam_paper_move.add_argument("--source-directory-id", default="0")

    exam_paper_delete = sub.add_parser(
        "exam-paper-delete", help="preview or confirm moving an exam paper to the recycle bin"
    )
    exam_paper_delete.add_argument("course")
    exam_paper_delete.add_argument("paper")
    exam_paper_delete.add_argument("--class", dest="clazz")
    exam_paper_delete.add_argument("--directory-id", default="0")
    exam_paper_delete.add_argument("--confirmation-token")

    exam_folder_create = sub.add_parser(
        "exam-folder-create", help="create an exam paper-library folder"
    )
    exam_folder_create.add_argument("course")
    exam_folder_create.add_argument("title")
    exam_folder_create.add_argument("--class", dest="clazz")
    exam_folder_create.add_argument("--parent-directory-id", default="0")

    exam_folder_rename = sub.add_parser(
        "exam-folder-rename", help="rename an exam paper-library folder"
    )
    exam_folder_rename.add_argument("course")
    exam_folder_rename.add_argument("folder")
    exam_folder_rename.add_argument("title")
    exam_folder_rename.add_argument("--class", dest="clazz")
    exam_folder_rename.add_argument("--parent-directory-id", default="0")

    exam_folder_move = sub.add_parser("exam-folder-move", help="move an exam paper-library folder")
    exam_folder_move.add_argument("course")
    exam_folder_move.add_argument("folder")
    exam_folder_move.add_argument("target_directory_id")
    exam_folder_move.add_argument("--class", dest="clazz")
    exam_folder_move.add_argument("--source-directory-id", default="0")

    exam_folder_delete = sub.add_parser(
        "exam-folder-delete",
        help="preview or confirm moving a paper-library folder to the recycle bin",
    )
    exam_folder_delete.add_argument("course")
    exam_folder_delete.add_argument("folder")
    exam_folder_delete.add_argument("--class", dest="clazz")
    exam_folder_delete.add_argument("--parent-directory-id", default="0")
    exam_folder_delete.add_argument("--confirmation-token")

    exam_submissions = sub.add_parser(
        "exam-submissions", help="list submitted or unsubmitted students for one exam"
    )
    exam_submissions.add_argument("course")
    exam_submissions.add_argument("exam")
    exam_submissions.add_argument("--class", dest="clazz")
    exam_submissions.add_argument("--state", type=int, choices=(0, 1), default=1)
    exam_submissions.add_argument("--status", type=int, default=-1)
    exam_submissions.add_argument("--search", default="")

    exam_answer = sub.add_parser(
        "exam-answer", help="read one student's exam answer sheet through HTTP"
    )
    exam_answer.add_argument("course")
    exam_answer.add_argument("exam")
    exam_answer.add_argument("submission")
    exam_answer.add_argument("--class", dest="clazz")

    qbank = sub.add_parser("qbank", help="page through the course question bank")
    qbank.add_argument("course")
    qbank.add_argument("--class", dest="clazz")
    qbank.add_argument("--page", type=int, default=1)
    qbank.add_argument("--page-size", type=int, default=30)
    qbank.add_argument("--search", default="")
    qbank.add_argument("--directory-id", default="0")

    qbank_smart_preview = sub.add_parser(
        "qbank-smart-preview",
        help="parse text, Word, PDF, or an image without adding questions",
    )
    qbank_smart_preview.add_argument("course")
    preview_source = qbank_smart_preview.add_mutually_exclusive_group(required=True)
    preview_source.add_argument("--text", dest="source_text")
    preview_source.add_argument("--file", dest="file_path")
    qbank_smart_preview.add_argument("--content-format", choices=("plain", "html"), default="plain")
    qbank_smart_preview.add_argument("--parse-latex-code", action="store_true")
    qbank_smart_preview.add_argument("--parse-latex-formula", action="store_true")
    qbank_smart_preview.add_argument("--class", dest="clazz")

    qbank_smart_import = sub.add_parser(
        "qbank-smart-import",
        help="parse and import questions or import a reviewed preview JSON",
    )
    qbank_smart_import.add_argument("course")
    import_source = qbank_smart_import.add_mutually_exclusive_group(required=True)
    import_source.add_argument("--text", dest="source_text")
    import_source.add_argument("--file", dest="file_path")
    import_source.add_argument("--questions-json")
    qbank_smart_import.add_argument("--target-directory", default="0")
    qbank_smart_import.add_argument("--content-format", choices=("plain", "html"), default="plain")
    qbank_smart_import.add_argument("--parse-latex-code", action="store_true")
    qbank_smart_import.add_argument("--parse-latex-formula", action="store_true")
    qbank_smart_import.add_argument("--allow-parser-warnings", action="store_true")
    qbank_smart_import.add_argument("--class", dest="clazz")

    qbank_source_courses = sub.add_parser(
        "qbank-source-courses", help="list personal course question banks available as sources"
    )
    qbank_source_courses.add_argument("course")
    qbank_source_courses.add_argument("--class", dest="clazz")

    qbank_source_questions = sub.add_parser(
        "qbank-source-questions", help="browse another course question bank"
    )
    qbank_source_questions.add_argument("course")
    qbank_source_questions.add_argument("source_course")
    qbank_source_questions.add_argument("--page", type=int, default=1)
    qbank_source_questions.add_argument("--page-size", type=int, default=30)
    qbank_source_questions.add_argument("--search", default="")
    qbank_source_questions.add_argument("--directory-id", default="0")
    qbank_source_questions.add_argument("--class", dest="clazz")

    qbank_import_from_course = sub.add_parser(
        "qbank-import-from-course", help="import questions from another course question bank"
    )
    qbank_import_from_course.add_argument("course")
    qbank_import_from_course.add_argument("source_course")
    qbank_import_from_course.add_argument("questions", nargs="+")
    qbank_import_from_course.add_argument("--source-directory-id", default="0")
    qbank_import_from_course.add_argument("--target-directory", default="0")
    qbank_import_from_course.add_argument("--class", dest="clazz")

    qbank_export = sub.add_parser(
        "qbank-export", help="export selected question-bank items or the whole bank"
    )
    qbank_export.add_argument("course")
    qbank_export.add_argument("export_type", choices=("ti", "word", "excel", "pdf"))
    qbank_export.add_argument("--question", dest="questions", action="append", default=[])
    qbank_export.add_argument("--directory", dest="directories", action="append", default=[])
    qbank_export.add_argument("--all", dest="export_all", action="store_true")
    qbank_export.add_argument("--source-directory-id", default="0")
    qbank_export.add_argument("--output", dest="output_path")
    qbank_export.add_argument("--no-answers", dest="include_answers", action="store_false")
    qbank_export.add_argument("--no-analysis", dest="include_analysis", action="store_false")
    qbank_export.add_argument("--include-difficulty", action="store_true")
    qbank_export.add_argument("--include-type-names", action="store_true")
    qbank_export.add_argument("--include-topics", action="store_true")
    qbank_export.add_argument("--include-targets", action="store_true")
    qbank_export.add_argument("--include-correct-rate", action="store_true")
    qbank_export.add_argument("--include-use-count", action="store_true")
    qbank_export.add_argument("--excel-plain-text", action="store_true")
    qbank_export.add_argument("--overwrite", action="store_true")
    qbank_export.add_argument("--class", dest="clazz")

    qbank_downloads = sub.add_parser(
        "qbank-downloads", help="list question-bank export tasks and files"
    )
    qbank_downloads.add_argument("course")
    qbank_downloads.add_argument("--page", type=int, default=1)
    qbank_downloads.add_argument("--order", choices=("down", "up"), default="down")
    qbank_downloads.add_argument("--class", dest="clazz")

    qbank_download = sub.add_parser(
        "qbank-download", help="get a question-bank export URL or save its file"
    )
    qbank_download.add_argument("course")
    qbank_download.add_argument("record")
    qbank_download.add_argument("--output", dest="output_path")
    qbank_download.add_argument("--password")
    qbank_download.add_argument("--overwrite", action="store_true")
    qbank_download.add_argument("--class", dest="clazz")

    qbank_download_rename = sub.add_parser(
        "qbank-download-rename", help="rename a question-bank download-center record"
    )
    qbank_download_rename.add_argument("course")
    qbank_download_rename.add_argument("record")
    qbank_download_rename.add_argument("name")
    qbank_download_rename.add_argument("--class", dest="clazz")

    qbank_download_delete = sub.add_parser(
        "qbank-download-delete",
        help="preview or confirm deleting a question-bank download-center record",
    )
    qbank_download_delete.add_argument("course")
    qbank_download_delete.add_argument("record")
    qbank_download_delete.add_argument("--class", dest="clazz")
    qbank_download_delete.add_argument("--confirmation-token")

    qbank_question = sub.add_parser("qbank-question", help="read one complete question-bank item")
    qbank_question.add_argument("course")
    qbank_question.add_argument("question")
    qbank_question.add_argument("--class", dest="clazz")
    qbank_question.add_argument("--directory-id", default="0")

    qbank_directories = sub.add_parser(
        "qbank-directories", help="read the complete question-bank directory tree"
    )
    qbank_directories.add_argument("course")
    qbank_directories.add_argument("--class", dest="clazz")

    qbank_folder_permissions = sub.add_parser(
        "qbank-folder-permissions", help="read question-bank directory permissions"
    )
    qbank_folder_permissions.add_argument("course")
    qbank_folder_permissions.add_argument("directory")
    qbank_folder_permissions.add_argument("--class", dest="clazz")

    qbank_folder_permissions_update = sub.add_parser(
        "qbank-folder-permissions-update",
        help="preview or confirm question-bank directory permission changes",
    )
    qbank_folder_permissions_update.add_argument("course")
    qbank_folder_permissions_update.add_argument("directory")
    qbank_folder_permissions_update.add_argument(
        "--self-practice", choices=("true", "false"), dest="allow_student_self_practice"
    )
    qbank_folder_permissions_update.add_argument(
        "--share-scope",
        choices=("all_team", "private", "selected_teachers"),
    )
    qbank_folder_permissions_update.add_argument(
        "--teacher", dest="selected_teachers", action="append"
    )
    qbank_folder_permissions_update.add_argument("--class", dest="clazz")
    qbank_folder_permissions_update.add_argument("--confirmation-token")

    qbank_question_types = sub.add_parser(
        "qbank-question-types", help="list question-bank question types"
    )
    qbank_question_types.add_argument("course")
    qbank_question_types.add_argument("--class", dest="clazz")

    qbank_question_type_add = sub.add_parser(
        "qbank-question-type-add", help="create a named question-bank question type"
    )
    qbank_question_type_add.add_argument("course")
    qbank_question_type_add.add_argument("name")
    qbank_question_type_add.add_argument("base_type")
    qbank_question_type_add.add_argument("--class", dest="clazz")

    qbank_question_type_rename = sub.add_parser(
        "qbank-question-type-rename", help="rename a question-bank question type"
    )
    qbank_question_type_rename.add_argument("course")
    qbank_question_type_rename.add_argument("question_type")
    qbank_question_type_rename.add_argument("name")
    qbank_question_type_rename.add_argument("--class", dest="clazz")

    qbank_question_type_move = sub.add_parser(
        "qbank-question-type-move", help="move a question-bank question type"
    )
    qbank_question_type_move.add_argument("course")
    qbank_question_type_move.add_argument("question_type")
    qbank_question_type_move.add_argument("target_position", type=int)
    qbank_question_type_move.add_argument("--class", dest="clazz")

    qbank_question_type_delete = sub.add_parser(
        "qbank-question-type-delete",
        help="preview or confirm deleting a question-bank question type",
    )
    qbank_question_type_delete.add_argument("course")
    qbank_question_type_delete.add_argument("question_type")
    qbank_question_type_delete.add_argument("--class", dest="clazz")
    qbank_question_type_delete.add_argument("--confirmation-token")

    qbank_labels = sub.add_parser("qbank-labels", help="list question-bank labels")
    qbank_labels.add_argument("course")
    qbank_labels.add_argument("--question", default="")
    qbank_labels.add_argument("--directory-id", default="0")
    qbank_labels.add_argument("--class", dest="clazz")

    qbank_label_create = sub.add_parser(
        "qbank-label-create", help="create a root or child question-bank label"
    )
    qbank_label_create.add_argument("course")
    qbank_label_create.add_argument("name")
    qbank_label_create.add_argument("--parent-label", default="0")
    qbank_label_create.add_argument("--class", dest="clazz")

    qbank_label_rename = sub.add_parser("qbank-label-rename", help="rename a question-bank label")
    qbank_label_rename.add_argument("course")
    qbank_label_rename.add_argument("label")
    qbank_label_rename.add_argument("name")
    qbank_label_rename.add_argument("--class", dest="clazz")

    qbank_label_delete = sub.add_parser(
        "qbank-label-delete", help="preview or confirm deleting a label and its children"
    )
    qbank_label_delete.add_argument("course")
    qbank_label_delete.add_argument("label")
    qbank_label_delete.add_argument("--class", dest="clazz")
    qbank_label_delete.add_argument("--confirmation-token")

    qbank_question_labels_set = sub.add_parser(
        "qbank-question-labels-set", help="set labels on one or more question-bank questions"
    )
    qbank_question_labels_set.add_argument("course")
    qbank_question_labels_set.add_argument("questions", nargs="+")
    qbank_question_labels_set.add_argument("--label", dest="labels", action="append", default=[])
    qbank_question_labels_set.add_argument(
        "--mode", choices=("replace", "add", "remove"), default="replace"
    )
    qbank_question_labels_set.add_argument("--directory-id", default="0")
    qbank_question_labels_set.add_argument("--sync-references", action="store_true")
    qbank_question_labels_set.add_argument("--class", dest="clazz")
    qbank_question_labels_set.add_argument("--confirmation-token")

    qbank_topics = sub.add_parser("qbank-topics", help="list question-bank knowledge points")
    qbank_topics.add_argument("course")
    qbank_topics.add_argument("--question", default="")
    qbank_topics.add_argument("--directory-id", default="0")
    qbank_topics.add_argument("--search", default="")
    qbank_topics.add_argument("--class", dest="clazz")

    qbank_topic_create = sub.add_parser(
        "qbank-topic-create", help="create a knowledge point or category"
    )
    qbank_topic_create.add_argument("course")
    qbank_topic_create.add_argument("name")
    qbank_topic_create.add_argument(
        "--kind", choices=("knowledge_point", "category"), default="knowledge_point"
    )
    qbank_topic_create.add_argument("--parent-topic")
    qbank_topic_create.add_argument("--after-topic", default="")
    qbank_topic_create.add_argument("--class", dest="clazz")

    qbank_topic_rename = sub.add_parser(
        "qbank-topic-rename", help="rename a knowledge point or category"
    )
    qbank_topic_rename.add_argument("course")
    qbank_topic_rename.add_argument("topic")
    qbank_topic_rename.add_argument("name")
    qbank_topic_rename.add_argument("--class", dest="clazz")

    qbank_topic_delete = sub.add_parser(
        "qbank-topic-delete", help="preview or confirm deleting a topic and descendants"
    )
    qbank_topic_delete.add_argument("course")
    qbank_topic_delete.add_argument("topic")
    qbank_topic_delete.add_argument("--class", dest="clazz")
    qbank_topic_delete.add_argument("--confirmation-token")

    qbank_question_topics_set = sub.add_parser(
        "qbank-question-topics-set",
        help="set knowledge points on one or more question-bank questions",
    )
    qbank_question_topics_set.add_argument("course")
    qbank_question_topics_set.add_argument("questions", nargs="+")
    qbank_question_topics_set.add_argument("--topic", dest="topics", action="append", default=[])
    qbank_question_topics_set.add_argument(
        "--mode", choices=("replace", "add", "remove"), default="replace"
    )
    qbank_question_topics_set.add_argument("--directory-id", default="0")
    qbank_question_topics_set.add_argument("--sync-references", action="store_true")
    qbank_question_topics_set.add_argument("--class", dest="clazz")
    qbank_question_topics_set.add_argument("--confirmation-token")

    qbank_recycle = sub.add_parser("qbank-recycle", help="list question-bank recycle-bin items")
    qbank_recycle.add_argument("course")
    qbank_recycle.add_argument("--page", type=int, default=1)
    qbank_recycle.add_argument("--page-size", type=int, default=0)
    qbank_recycle.add_argument("--search", default="")
    qbank_recycle.add_argument("--directory-id", default="")
    qbank_recycle.add_argument(
        "--directory-path-id", dest="directory_path_ids", action="append", default=[]
    )
    qbank_recycle.add_argument("--order", choices=("asc", "desc"), default="desc")
    qbank_recycle.add_argument("--class", dest="clazz")

    qbank_locked = sub.add_parser("qbank-locked", help="list locked question-bank items")
    qbank_locked.add_argument("course")
    qbank_locked.add_argument("--page", type=int, default=1)
    qbank_locked.add_argument("--page-size", type=int, default=0)
    qbank_locked.add_argument("--search", default="")
    qbank_locked.add_argument("--directory-id", default="")
    qbank_locked.add_argument(
        "--directory-path-id", dest="directory_path_ids", action="append", default=[]
    )
    qbank_locked.add_argument("--order", choices=("asc", "desc"), default="desc")
    qbank_locked.add_argument("--lock-time", dest="lock_time_filters", action="append", default=[])
    qbank_locked.add_argument("--class", dest="clazz")

    qbank_lock = sub.add_parser(
        "qbank-lock", help="preview or confirm locking active questions or directories"
    )
    qbank_lock.add_argument("course")
    qbank_lock.add_argument("--question", dest="questions", action="append", default=[])
    qbank_lock.add_argument("--directory", dest="directories", action="append", default=[])
    qbank_lock.add_argument("--directory-id", default="0")
    qbank_lock.add_argument("--class", dest="clazz")
    qbank_lock.add_argument("--confirmation-token")

    qbank_unlock = sub.add_parser(
        "qbank-unlock", help="preview or confirm unlocking question-bank items"
    )
    qbank_unlock.add_argument("course")
    qbank_unlock.add_argument("items", nargs="+")
    qbank_unlock.add_argument("--directory-id", default="")
    qbank_unlock.add_argument(
        "--directory-path-id", dest="directory_path_ids", action="append", default=[]
    )
    qbank_unlock.add_argument("--class", dest="clazz")
    qbank_unlock.add_argument("--confirmation-token")

    qbank_recycle_restore = sub.add_parser(
        "qbank-recycle-restore", help="restore questions or directories from recycle"
    )
    qbank_recycle_restore.add_argument("course")
    qbank_recycle_restore.add_argument("items", nargs="+")
    qbank_recycle_restore.add_argument("--directory-id", default="")
    qbank_recycle_restore.add_argument(
        "--directory-path-id", dest="directory_path_ids", action="append", default=[]
    )
    qbank_recycle_restore.add_argument("--class", dest="clazz")

    qbank_recycle_delete = sub.add_parser(
        "qbank-recycle-delete", help="preview or confirm permanently deleting recycle items"
    )
    qbank_recycle_delete.add_argument("course")
    qbank_recycle_delete.add_argument("items", nargs="+")
    qbank_recycle_delete.add_argument("--directory-id", default="")
    qbank_recycle_delete.add_argument(
        "--directory-path-id", dest="directory_path_ids", action="append", default=[]
    )
    qbank_recycle_delete.add_argument("--class", dest="clazz")
    qbank_recycle_delete.add_argument("--confirmation-token")

    qbank_recycle_empty = sub.add_parser(
        "qbank-recycle-empty", help="preview or confirm permanently emptying recycle"
    )
    qbank_recycle_empty.add_argument("course")
    qbank_recycle_empty.add_argument("--class", dest="clazz")
    qbank_recycle_empty.add_argument("--confirmation-token")

    qbank_questions_type = sub.add_parser(
        "qbank-questions-type", help="change one or more questions to another question type"
    )
    qbank_questions_type.add_argument("course")
    qbank_questions_type.add_argument("question_type")
    qbank_questions_type.add_argument("questions", nargs="+")
    qbank_questions_type.add_argument("--directory-id", default="0")
    qbank_questions_type.add_argument("--class", dest="clazz")

    qbank_questions_difficulty = sub.add_parser(
        "qbank-questions-difficulty", help="change difficulty for one or more questions"
    )
    qbank_questions_difficulty.add_argument("course")
    qbank_questions_difficulty.add_argument("difficulty")
    qbank_questions_difficulty.add_argument("questions", nargs="+")
    qbank_questions_difficulty.add_argument("--directory-id", default="0")
    qbank_questions_difficulty.add_argument("--class", dest="clazz")

    qbank_copy = sub.add_parser(
        "qbank-copy", help="copy questions or directories into a target directory"
    )
    qbank_copy.add_argument("course")
    qbank_copy.add_argument("target_directory")
    qbank_copy.add_argument("--question", dest="questions", action="append", default=[])
    qbank_copy.add_argument("--directory", dest="directories", action="append", default=[])
    qbank_copy.add_argument("--source-directory-id", default="0")
    qbank_copy.add_argument("--class", dest="clazz")

    qbank_folder_create = sub.add_parser(
        "qbank-folder-create", help="create a question-bank directory"
    )
    qbank_folder_create.add_argument("course")
    qbank_folder_create.add_argument("name")
    qbank_folder_create.add_argument("--parent-directory", default="0")
    qbank_folder_create.add_argument("--class", dest="clazz")

    qbank_folder_rename = sub.add_parser(
        "qbank-folder-rename", help="rename a question-bank directory"
    )
    qbank_folder_rename.add_argument("course")
    qbank_folder_rename.add_argument("directory")
    qbank_folder_rename.add_argument("name")
    qbank_folder_rename.add_argument("--class", dest="clazz")

    qbank_folder_move = sub.add_parser("qbank-folder-move", help="move a question-bank directory")
    qbank_folder_move.add_argument("course")
    qbank_folder_move.add_argument("directory")
    qbank_folder_move.add_argument("target_directory")
    qbank_folder_move.add_argument("--class", dest="clazz")

    qbank_folder_reorder = sub.add_parser(
        "qbank-folder-reorder", help="move a question-bank directory within its parent"
    )
    qbank_folder_reorder.add_argument("course")
    qbank_folder_reorder.add_argument("directory")
    qbank_folder_reorder.add_argument("target_position", type=int)
    qbank_folder_reorder.add_argument("--class", dest="clazz")

    qbank_folder_top = sub.add_parser(
        "qbank-folder-top", help="set or clear question-bank directory top status"
    )
    qbank_folder_top.add_argument("course")
    qbank_folder_top.add_argument("directory")
    qbank_folder_top.add_argument("--clear", action="store_true")
    qbank_folder_top.add_argument("--class", dest="clazz")

    qbank_folder_delete = sub.add_parser(
        "qbank-folder-delete", help="preview or confirm recycling a question-bank directory"
    )
    qbank_folder_delete.add_argument("course")
    qbank_folder_delete.add_argument("directory")
    qbank_folder_delete.add_argument("--class", dest="clazz")
    qbank_folder_delete.add_argument("--confirmation-token")

    qbank_question_add = sub.add_parser(
        "qbank-question-add", help="add a core question-bank question"
    )
    qbank_question_add.add_argument("course")
    qbank_question_add.add_argument("question_type")
    qbank_question_add.add_argument("stem")
    qbank_question_add.add_argument("--directory", default="0")
    qbank_question_add.add_argument("--class", dest="clazz")
    qbank_question_add.add_argument("--option", dest="options", action="append")
    qbank_question_add.add_argument("--correct-answer")
    qbank_question_add.add_argument("--blank-answer", dest="answers", action="append")
    qbank_question_add.add_argument("--answer")
    qbank_question_add.add_argument("--analysis", default="")
    qbank_question_add.add_argument("--difficulty", type=float, default=0.8)
    qbank_question_add.add_argument("--content-format", choices=("plain", "html"), default="plain")

    qbank_question_update = sub.add_parser(
        "qbank-question-update", help="update selected fields of a question-bank question"
    )
    qbank_question_update.add_argument("course")
    qbank_question_update.add_argument("question")
    qbank_question_update.add_argument("--directory-id", default="0")
    qbank_question_update.add_argument("--class", dest="clazz")
    qbank_question_update.add_argument("--stem")
    qbank_question_update.add_argument("--option", dest="options", action="append")
    qbank_question_update.add_argument("--correct-answer")
    qbank_question_update.add_argument("--blank-answer", dest="answers", action="append")
    qbank_question_update.add_argument("--answer")
    qbank_question_update.add_argument("--analysis")
    qbank_question_update.add_argument("--difficulty", type=float)
    qbank_question_update.add_argument(
        "--content-format", choices=("plain", "html"), default="plain"
    )

    qbank_question_move = sub.add_parser(
        "qbank-question-move", help="move a question-bank question between directories"
    )
    qbank_question_move.add_argument("course")
    qbank_question_move.add_argument("question")
    qbank_question_move.add_argument("target_directory")
    qbank_question_move.add_argument("--source-directory-id", default="0")
    qbank_question_move.add_argument("--class", dest="clazz")

    qbank_question_reorder = sub.add_parser(
        "qbank-question-reorder", help="move a question within its current directory"
    )
    qbank_question_reorder.add_argument("course")
    qbank_question_reorder.add_argument("question")
    qbank_question_reorder.add_argument("target_position", type=int)
    qbank_question_reorder.add_argument("--directory-id", default="0")
    qbank_question_reorder.add_argument("--class", dest="clazz")

    qbank_question_difficulty = sub.add_parser(
        "qbank-question-difficulty", help="set numeric difficulty for a question-bank item"
    )
    qbank_question_difficulty.add_argument("course")
    qbank_question_difficulty.add_argument("question")
    qbank_question_difficulty.add_argument("difficulty", type=float)
    qbank_question_difficulty.add_argument("--directory-id", default="0")
    qbank_question_difficulty.add_argument("--class", dest="clazz")

    qbank_question_delete = sub.add_parser(
        "qbank-question-delete", help="preview or confirm recycling a question-bank question"
    )
    qbank_question_delete.add_argument("course")
    qbank_question_delete.add_argument("question")
    qbank_question_delete.add_argument("--directory-id", default="0")
    qbank_question_delete.add_argument("--class", dest="clazz")
    qbank_question_delete.add_argument("--confirmation-token")

    discussions = sub.add_parser("discussions", help="list course discussions through HTTP")
    discussions.add_argument("course")
    discussions.add_argument("--class", dest="clazz")
    discussions.add_argument("--search", default="")
    discussions.add_argument("--class-only", action="store_true")

    topic = sub.add_parser("discussion-topic", help="read one topic and all replies through HTTP")
    topic.add_argument("course")
    topic.add_argument("topic")
    topic.add_argument("--class", dest="clazz")
    topic.add_argument("--class-only", action="store_true")
    topic.add_argument("--order", type=int, choices=(1, 2), default=2)
    topic.add_argument("--reply-search", default="")

    topic_create = sub.add_parser(
        "discussion-create", help="preview or confirm publishing a discussion topic"
    )
    topic_create.add_argument("course")
    topic_create.add_argument("title")
    topic_create.add_argument("content")
    topic_create.add_argument("--class", dest="clazz")
    topic_create.add_argument("--class-only", action="store_true")
    topic_create.add_argument("--anonymous", action="store_true")
    topic_create.add_argument("--confirmation-token")

    topic_edit = sub.add_parser(
        "discussion-edit", help="preview or confirm editing a discussion topic"
    )
    topic_edit.add_argument("course")
    topic_edit.add_argument("topic")
    topic_edit.add_argument("--class", dest="clazz")
    topic_edit.add_argument("--title")
    topic_edit.add_argument("--content")
    topic_edit.add_argument("--confirmation-token")

    topic_top = sub.add_parser("discussion-top", help="preview or confirm discussion top status")
    topic_top.add_argument("course")
    topic_top.add_argument("topic")
    topic_top.add_argument("--class", dest="clazz")
    topic_top.add_argument("--off", action="store_true")
    topic_top.add_argument("--confirmation-token")

    topic_delete = sub.add_parser(
        "discussion-delete", help="preview or confirm deleting a discussion topic"
    )
    topic_delete.add_argument("course")
    topic_delete.add_argument("topic")
    topic_delete.add_argument("--class", dest="clazz")
    topic_delete.add_argument("--confirmation-token")

    reply_create = sub.add_parser(
        "discussion-reply", help="preview or confirm publishing a discussion reply"
    )
    reply_create.add_argument("course")
    reply_create.add_argument("topic")
    reply_create.add_argument("content")
    reply_create.add_argument("--class", dest="clazz")
    reply_create.add_argument("--reply-to", default="")
    reply_create.add_argument("--anonymous", action="store_true")
    reply_create.add_argument("--confirmation-token")

    reply_edit = sub.add_parser(
        "discussion-reply-edit", help="preview or confirm editing a discussion reply"
    )
    reply_edit.add_argument("course")
    reply_edit.add_argument("topic")
    reply_edit.add_argument("reply")
    reply_edit.add_argument("content")
    reply_edit.add_argument("--class", dest="clazz")
    reply_edit.add_argument("--confirmation-token")

    reply_delete = sub.add_parser(
        "discussion-reply-delete", help="preview or confirm deleting a discussion reply"
    )
    reply_delete.add_argument("course")
    reply_delete.add_argument("topic")
    reply_delete.add_argument("reply")
    reply_delete.add_argument("--class", dest="clazz")
    reply_delete.add_argument("--confirmation-token")

    plan = sub.add_parser("plan", help="parse a natural-language command")
    plan.add_argument("text", nargs="+")

    run = sub.add_parser("run", help="execute a natural-language command")
    run.add_argument("text", nargs="+")
    run.add_argument("--confirmation-token")

    return parser


async def _run_action(args: argparse.Namespace, runtime: ActionRuntime) -> dict[str, Any]:
    if args.command == "capabilities":
        return await runtime.execute("capabilities.list")
    if args.command == "session":
        return await runtime.execute("session.check")
    if args.command == "space-modules":
        return await runtime.execute("space.modules.discover")
    if args.command == "space-open":
        return await runtime.execute("space.module.open", {"module": args.module})
    if args.command == "job-ability-status":
        return await runtime.execute("job_ability.status.read")
    if args.command == "job-search":
        return await runtime.execute(
            "job_ability.jobs.search",
            {
                "keyword": args.keyword,
                "page": args.page,
                "page_size": args.page_size,
                "education_level": args.education,
            },
        )
    if args.command == "job-read":
        return await runtime.execute(
            "job_ability.job_ad.read",
            {
                "job": args.job,
                "search": args.search,
                "education_level": args.education,
            },
        )
    if args.command == "job-popular":
        return await runtime.execute(
            "job_ability.popular_jobs.list",
            {"education_level": args.education},
        )
    if args.command == "occupation-catalog":
        return await runtime.execute(
            "job_ability.occupation_catalog.read",
            {"education_level": args.education},
        )
    if args.command == "occupation-search":
        return await runtime.execute(
            "job_ability.occupations.search",
            {"keyword": args.keyword, "education_level": args.education},
        )
    if args.command == "industry-types":
        return await runtime.execute(
            "job_ability.industry_types.list",
            {"page": args.page, "page_size": args.page_size},
        )
    if args.command == "industries":
        return await runtime.execute(
            "job_ability.industries.list",
            {
                "industry_type": args.industry_type,
                "education_level": args.education,
                "page": args.page,
                "page_size": args.page_size,
            },
        )
    if args.command == "industry-jobs":
        return await runtime.execute(
            "job_ability.industry_jobs.list",
            {
                "industry": args.industry,
                "education_level": args.education,
                "page": args.page,
                "page_size": args.page_size,
            },
        )
    if args.command == "subjects":
        return await runtime.execute(
            "subjects.items.list",
            {"folder": args.folder, "search": args.search, "max_items": args.max_items},
        )
    if args.command == "subject-tree":
        return await runtime.execute("subjects.tree.list", {"max_folders": args.max_folders})
    if args.command == "subject-create-status":
        return await runtime.execute("subjects.creation.status")
    if args.command == "subject-folder-create":
        return await runtime.execute(
            "subjects.folder.create",
            {"name": args.name, "parent_folder": args.parent_folder},
        )
    if args.command == "subject-folder-rename":
        return await runtime.execute(
            "subjects.folder.rename", {"folder": args.folder, "name": args.name}
        )
    if args.command == "subject-folder-move":
        return await runtime.execute(
            "subjects.folder.move",
            {"folder": args.folder, "target_folder": args.target_folder},
        )
    if args.command == "subject-folder-delete":
        return await runtime.execute(
            "subjects.folder.delete",
            {"folder": args.folder, "allow_nonempty": args.allow_nonempty},
            args.confirmation_token,
        )
    if args.command == "subject-publish":
        return await runtime.execute(
            "subjects.publish_status.update",
            {"subject": args.subject, "published": not args.off},
            args.confirmation_token,
        )
    if args.command == "subject-move":
        return await runtime.execute(
            "subjects.move",
            {"subject": args.subject, "target_folder": args.target_folder},
        )
    if args.command == "subject-delete":
        return await runtime.execute(
            "subjects.delete",
            {"subject": args.subject},
            args.confirmation_token,
        )
    if args.command == "subject-recycle":
        return await runtime.execute(
            "subjects.recycle.list",
            {"search": args.search, "max_items": args.max_items},
        )
    if args.command == "subject-restore":
        return await runtime.execute("subjects.recycle.restore", {"subject": args.subject})
    if args.command == "subject-recycle-delete":
        return await runtime.execute(
            "subjects.recycle.delete",
            {"subject": args.subject},
            args.confirmation_token,
        )
    if args.command == "detection-channels":
        return await runtime.execute("detection.channels.list")
    if args.command == "detections":
        return await runtime.execute(
            "detection.records.list",
            {
                "type": args.type,
                "page": args.page,
                "page_size": args.page_size,
                "status": args.status,
                "begin_date": args.begin_date,
                "end_date": args.end_date,
                "search": args.search,
            },
        )
    if args.command == "detection-status":
        return await runtime.execute(
            "detection.record.status", {"type": args.type, "record": args.record}
        )
    if args.command == "detection-submit":
        return await runtime.execute(
            "detection.submit",
            {
                "type": args.type,
                "title": args.title,
                "author": args.author,
                "content": args.content,
                "file": args.file,
                "end_year": args.end_year,
                "channel_ids": args.channel_ids,
            },
            args.confirmation_token,
        )
    if args.command == "detection-compare":
        return await runtime.execute(
            "detection.comparison.submit",
            {
                "title_1": args.title_1,
                "file_1": args.file_1,
                "title_2": args.title_2,
                "file_2": args.file_2,
            },
            args.confirmation_token,
        )
    if args.command == "detection-payment-status":
        return await runtime.execute(
            "detection.payment.status", {"type": args.type, "record": args.record}
        )
    if args.command == "detection-use-free":
        return await runtime.execute(
            "detection.free_entitlement.use",
            {"type": args.type, "record": args.record},
            args.confirmation_token,
        )
    if args.command == "detection-report":
        return await runtime.execute(
            "detection.report.download",
            {
                "type": args.type,
                "record": args.record,
                "output_path": args.output_path,
                "result_type": args.result_type,
                "timeout_seconds": args.timeout_seconds,
                "overwrite": args.overwrite,
            },
        )
    if args.command == "detection-delete":
        return await runtime.execute(
            "detection.record.delete",
            {"type": args.type, "record": args.record},
            args.confirmation_token,
        )
    if args.command == "lives":
        return await runtime.execute(
            "live.rooms.list",
            {
                "search": args.search,
                "start_time": args.start_time,
                "end_time": args.end_time,
                "sort_key": args.sort_key,
                "sort_type": args.sort_type,
                "max_items": args.max_items,
            },
        )
    if args.command == "live-read":
        return await runtime.execute("live.room.read", {"room": args.room})
    if args.command == "live-create":
        return await runtime.execute(
            "live.room.create",
            {
                "title": args.title,
                "scheduled_time": args.scheduled_time,
                "introduction": args.introduction,
                "content_format": args.content_format,
                "mode": args.mode,
                "chat_content_review": args.chat_content_review,
                "cover_object_id": args.cover_object_id,
                "preview_video_object_id": args.preview_video_object_id,
                "extends_info": _parse_json_object(args.extends_info_json, "extends_info_json"),
            },
            args.confirmation_token,
        )
    if args.command == "live-update":
        parameters = {"room": args.room, "content_format": args.content_format}
        for key in (
            "title",
            "scheduled_time",
            "introduction",
            "cover_object_id",
            "preview_video_object_id",
        ):
            value = getattr(args, key)
            if value is not None:
                parameters[key] = value
        return await runtime.execute("live.room.update", parameters)
    if args.command == "live-settings":
        parameters = {"room": args.room}
        for key in (
            "comments_enabled",
            "forwarding_enabled",
            "replay_enabled",
            "learning_app_only",
            "chat_content_review",
            "login_required",
            "picture_live",
            "access_password",
            "show_viewer_count",
            "reservations_enabled",
            "preupload_enabled",
            "allowed_unit_ids",
            "replay_start_offset_seconds",
        ):
            value = getattr(args, key)
            if value is not None:
                parameters[key] = value
        return await runtime.execute(
            "live.room.settings.update", parameters, args.confirmation_token
        )
    if args.command == "live-status":
        return await runtime.execute("live.room.status", {"room": args.room})
    if args.command == "live-watch":
        return await runtime.execute("live.room.watch", {"room": args.room})
    if args.command == "live-stream-credentials":
        return await runtime.execute(
            "live.stream.credentials", {"room": args.room}, args.confirmation_token
        )
    if args.command == "live-asset-upload":
        return await runtime.execute(
            "live.asset.upload",
            {"kind": args.kind, "file": args.file, "room": args.room},
        )
    if args.command == "live-export":
        return await runtime.execute(
            "live.export",
            {
                "search": args.search,
                "start_time": args.start_time,
                "end_time": args.end_time,
                "sort_key": args.sort_key,
                "sort_type": args.sort_type,
            },
        )
    if args.command == "live-units":
        return await runtime.execute("live.units.list")
    if args.command == "live-delete":
        return await runtime.execute(
            "live.room.delete", {"room": args.room}, args.confirmation_token
        )
    if args.command == "live-recycle":
        return await runtime.execute(
            "live.recycle.list",
            {"search": args.search, "max_items": args.max_items},
        )
    if args.command == "live-restore":
        return await runtime.execute("live.recycle.restore", {"room": args.room})
    if args.command == "live-recycle-delete":
        return await runtime.execute(
            "live.recycle.delete", {"room": args.room}, args.confirmation_token
        )
    if args.command == "live-themes":
        return await runtime.execute(
            "live.themes.list",
            {"search": args.search, "max_items": args.max_items},
        )
    if args.command == "live-theme-read":
        return await runtime.execute(
            "live.theme.read", {"theme": args.theme, "max_rooms": args.max_rooms}
        )
    if args.command == "live-theme-create":
        return await runtime.execute(
            "live.theme.create",
            {"name": args.name, "description": args.description},
            args.confirmation_token,
        )
    if args.command == "live-theme-update":
        parameters = {"theme": args.theme}
        if args.name is not None:
            parameters["name"] = args.name
        if args.description is not None:
            parameters["description"] = args.description
        return await runtime.execute("live.theme.update", parameters)
    if args.command == "live-theme-settings":
        parameters = {"theme": args.theme}
        for key in (
            "forwarding_enabled",
            "replay_enabled",
            "learning_app_only",
            "login_required",
            "allowed_unit_ids",
        ):
            value = getattr(args, key)
            if value is not None:
                parameters[key] = value
        return await runtime.execute(
            "live.theme.settings.update", parameters, args.confirmation_token
        )
    if args.command == "live-theme-add-room":
        return await runtime.execute(
            "live.theme.room.add",
            {"theme": args.theme, "room": args.room},
            args.confirmation_token,
        )
    if args.command == "live-theme-create-room":
        return await runtime.execute(
            "live.theme.room.create",
            {
                "theme": args.theme,
                "title": args.title,
                "scheduled_time": args.scheduled_time,
                "introduction": args.introduction,
                "content_format": args.content_format,
                "mode": args.mode,
                "chat_content_review": args.chat_content_review,
                "cover_object_id": args.cover_object_id,
                "preview_video_object_id": args.preview_video_object_id,
            },
            args.confirmation_token,
        )
    if args.command == "live-theme-delete":
        return await runtime.execute(
            "live.theme.delete", {"theme": args.theme}, args.confirmation_token
        )
    if args.command == "notes":
        return await runtime.execute(
            "notes.list",
            {"search": args.search, "max_items": args.max_items},
        )
    if args.command == "note-read":
        return await runtime.execute("notes.read", {"note": args.note})
    if args.command == "note-create":
        return await runtime.execute(
            "notes.create",
            {
                "title": args.title,
                "content": args.content,
                "content_format": args.content_format,
                "notebook_cid": args.notebook_cid,
            },
        )
    if args.command == "note-update":
        params = {"note": args.note, "content_format": args.content_format}
        if args.title is not None:
            params["title"] = args.title
        if args.content is not None:
            params["content"] = args.content
        return await runtime.execute("notes.update", params)
    if args.command == "note-delete":
        return await runtime.execute(
            "notes.delete",
            {"note": args.note},
            args.confirmation_token,
        )
    if args.command == "inbox":
        return await runtime.execute(
            "inbox.notices.list",
            {
                "scope": args.scope,
                "search": args.search,
                "sender": args.sender,
                "start_time": args.start_time,
                "end_time": args.end_time,
                "max_items": args.max_items,
            },
        )
    if args.command == "inbox-read":
        return await runtime.execute(
            "inbox.notice.read",
            {"notice": args.notice, "scope": args.scope},
        )
    if args.command == "inbox-unread":
        return await runtime.execute(
            "inbox.notice.mark_unread",
            {"notice": args.notice, "scope": "received"},
        )
    if args.command == "inbox-top":
        return await runtime.execute(
            "inbox.notice.top_status.update",
            {"notice": args.notice, "scope": args.scope, "top": not args.off},
        )
    if args.command == "inbox-collect":
        return await runtime.execute(
            "inbox.notice.collect_status.update",
            {"notice": args.notice, "scope": args.scope, "collect": not args.off},
        )
    if args.command == "inbox-delete":
        return await runtime.execute(
            "inbox.notice.delete",
            {"notice": args.notice, "scope": args.scope},
            args.confirmation_token,
        )
    if args.command == "inbox-send":
        return await runtime.execute(
            "inbox.notice.send",
            {
                "recipients": args.recipients,
                "title": args.title,
                "content": args.content,
                "content_format": args.content_format,
                "allow_comments": not args.forbid_comments,
                "show_comments": not args.hide_comments,
                "hide_read_status": args.hide_read_status,
                "forbid_forwarding": args.forbid_forwarding,
                "permission_password": args.permission_password,
            },
            args.confirmation_token,
        )
    if args.command == "inbox-drafts":
        return await runtime.execute(
            "inbox.drafts.list",
            {"search": args.search, "max_items": args.max_items},
        )
    if args.command == "inbox-draft-save":
        return await runtime.execute(
            "inbox.draft.save",
            {
                "title": args.title,
                "content": args.content,
                "draft": args.draft,
                "recipients": args.recipients,
                "content_format": args.content_format,
                "allow_comments": not args.forbid_comments,
                "show_comments": not args.hide_comments,
                "hide_read_status": args.hide_read_status,
                "forbid_forwarding": args.forbid_forwarding,
            },
        )
    if args.command == "inbox-draft-delete":
        return await runtime.execute(
            "inbox.draft.delete",
            {"draft": args.draft},
            args.confirmation_token,
        )
    if args.command == "inbox-folders":
        return await runtime.execute("inbox.folders.list")
    if args.command == "inbox-folder-rules":
        return await runtime.execute("inbox.folder.filters.read", {"folder": args.folder})
    if args.command == "inbox-folder-notices":
        return await runtime.execute(
            "inbox.folder.notices.list",
            {
                "folder": args.folder,
                "scope": args.scope,
                "search": args.search,
                "sender": args.sender,
                "start_time": args.start_time,
                "end_time": args.end_time,
                "max_items": args.max_items,
            },
        )
    if args.command == "inbox-folder-create":
        return await runtime.execute(
            "inbox.folder.create",
            {
                "name": args.name,
                "sender_rules": _parse_json_list(args.sender_rules_json, "sender-rules-json"),
                "keywords": _parse_json_list(args.keywords_json, "keywords-json"),
            },
        )
    if args.command == "inbox-folder-update":
        params: dict[str, Any] = {"folder": args.folder}
        if args.name is not None:
            params["name"] = args.name
        if args.sender_rules_json is not None:
            params["sender_rules"] = _parse_json_list(args.sender_rules_json, "sender-rules-json")
        if args.keywords_json is not None:
            params["keywords"] = _parse_json_list(args.keywords_json, "keywords-json")
        return await runtime.execute("inbox.folder.update", params)
    if args.command == "inbox-folder-delete":
        return await runtime.execute(
            "inbox.folder.delete",
            {"folder": args.folder},
            args.confirmation_token,
        )
    if args.command == "inbox-folder-reorder":
        return await runtime.execute(
            "inbox.folders.reorder",
            {"folders": args.folders, "top": args.top},
        )
    if args.command == "inbox-move":
        return await runtime.execute(
            "inbox.notices.move",
            {
                "notices": args.notices,
                "destination_folder": args.destination_folder,
                "scope": args.scope,
                "source_folder": args.source_folder,
            },
        )
    if args.command == "inbox-recycle":
        return await runtime.execute(
            "inbox.recycle.list",
            {"search": args.search, "max_items": args.max_items},
        )
    if args.command == "inbox-recycle-restore":
        return await runtime.execute(
            "inbox.recycle.restore",
            {"notices": args.notices},
        )
    if args.command == "inbox-recycle-delete":
        return await runtime.execute(
            "inbox.recycle.items.delete",
            {"notices": args.notices},
            args.confirmation_token,
        )
    if args.command == "inbox-recycle-empty":
        return await runtime.execute(
            "inbox.recycle.empty",
            {},
            args.confirmation_token,
        )
    if args.command == "contact-units":
        return await runtime.execute("contacts.units.list")
    if args.command == "contact-departments":
        return await runtime.execute(
            "contacts.departments.list",
            {
                "fid": args.fid,
                "parent_id": args.parent_id,
                "department_type": args.department_type,
            },
        )
    if args.command == "contact-department-members":
        return await runtime.execute(
            "contacts.department.members.list",
            {
                "fid": args.fid,
                "department_id": args.department_id,
                "search": args.search,
                "max_items": args.max_items,
            },
        )
    if args.command == "contact-search":
        return await runtime.execute(
            "contacts.people.search",
            {
                "search": args.search,
                "fid": args.fid,
                "department_id": args.department_id,
                "mode": args.mode,
                "max_items": args.max_items,
            },
        )
    if args.command == "contacts":
        return await runtime.execute(
            "contacts.relations.list",
            {"relation": args.relation, "max_items": args.max_items},
        )
    if args.command == "contact-groups":
        return await runtime.execute("contacts.groups.list", {"search": args.search})
    if args.command == "contact-group-members":
        return await runtime.execute(
            "contacts.group.members.list",
            {"group": args.group, "search": args.search, "max_items": args.max_items},
        )
    if args.command == "contact-chatgroups":
        return await runtime.execute("contacts.chatgroups.list", {"max_items": args.max_items})
    if args.command == "contact-chatgroup-members":
        return await runtime.execute(
            "contacts.chatgroup.members.list",
            {"chatgroup": args.chatgroup, "max_items": args.max_items},
        )
    if args.command == "contact-teams":
        return await runtime.execute("contacts.teams.list")
    if args.command == "contact-team-members":
        return await runtime.execute(
            "contacts.team.members.list",
            {"team": args.team, "max_items": args.max_items},
        )
    if args.command == "contact-follow":
        return await runtime.execute(
            "contacts.follow_status.update",
            {"person": args.person, "followed": not args.off},
            args.confirmation_token,
        )
    if args.command == "contact-team-create":
        return await runtime.execute(
            "contacts.team.create",
            {"name": args.name, "members": args.members},
            args.confirmation_token,
        )
    if args.command == "contact-team-rename":
        return await runtime.execute(
            "contacts.team.rename",
            {"team": args.team, "name": args.name},
            args.confirmation_token,
        )
    if args.command == "contact-team-add":
        return await runtime.execute(
            "contacts.team.members.add",
            {"team": args.team, "members": args.members},
            args.confirmation_token,
        )
    if args.command == "contact-team-remove":
        return await runtime.execute(
            "contacts.team.member.remove",
            {"team": args.team, "member": args.member},
            args.confirmation_token,
        )
    if args.command == "contact-team-delete":
        return await runtime.execute(
            "contacts.team.delete",
            {"team": args.team},
            args.confirmation_token,
        )
    if args.command == "contact-team-exit":
        return await runtime.execute(
            "contacts.team.exit",
            {"team": args.team},
            args.confirmation_token,
        )
    if args.command == "groups":
        return await runtime.execute(
            "groups.list",
            {"folder": args.folder, "search": args.search},
        )
    if args.command == "group-read":
        return await runtime.execute("groups.read", {"group": args.group})
    if args.command == "group-create":
        return await runtime.execute(
            "groups.create",
            {
                "name": args.name,
                "description": args.description,
                "folder": args.folder,
                "logo_url": args.logo_url,
            },
            args.confirmation_token,
        )
    if args.command == "group-update":
        params: dict[str, Any] = {"group": args.group}
        if args.name is not None:
            params["name"] = args.name
        if args.description is not None:
            params["description"] = args.description
        return await runtime.execute("groups.update", params, args.confirmation_token)
    if args.command == "group-logo-update":
        return await runtime.execute(
            "groups.logo.update",
            {"group": args.group, "file": args.file},
            args.confirmation_token,
        )
    if args.command == "group-modules":
        return await runtime.execute("groups.modules.list", {"group": args.group})
    if args.command == "group-modules-update":
        return await runtime.execute(
            "groups.modules.update",
            {"group": args.group, "enabled_type_ids": args.enabled_type_ids},
            args.confirmation_token,
        )
    if args.command == "group-settings-update":
        parameters: dict[str, Any] = {
            "group": args.group,
            "changes": _parse_permission_changes(args.setting_changes),
        }
        if args.sign_ban_start_time is not None:
            parameters["sign_ban_start_time"] = args.sign_ban_start_time
        return await runtime.execute(
            "groups.settings.update",
            parameters,
            args.confirmation_token,
        )
    if args.command == "group-levels":
        return await runtime.execute("groups.levels.list", {"group": args.group})
    if args.command == "group-level-series":
        return await runtime.execute(
            "groups.levels.series.update",
            {"group": args.group, "series": args.series},
            args.confirmation_token,
        )
    if args.command == "group-levels-custom":
        levels = _parse_json_list(args.levels_json, "custom personal group levels")
        return await runtime.execute(
            "groups.levels.custom.update",
            {"group": args.group, "levels": levels or []},
            args.confirmation_token,
        )
    if args.command == "group-growth-rules":
        return await runtime.execute("groups.growth_rules.list", {"group": args.group})
    if args.command == "group-growth-rule-series":
        return await runtime.execute(
            "groups.growth_rules.series.update",
            {"group": args.group, "series": args.series},
            args.confirmation_token,
        )
    if args.command == "group-growth-rules-update":
        return await runtime.execute(
            "groups.growth_rules.update",
            {
                "group": args.group,
                "changes": _parse_permission_changes(args.growth_rule_changes),
            },
            args.confirmation_token,
        )
    if args.command == "group-speaking-rules-update":
        parameters = {
            "group": args.group,
            "changes": _parse_permission_changes(args.rule_changes),
        }
        attachment_rules = _parse_json_object(args.attachment_rules, "attachment rules")
        if attachment_rules is not None:
            parameters["attachment_rules"] = attachment_rules
        return await runtime.execute(
            "groups.speaking_rules.update",
            parameters,
            args.confirmation_token,
        )
    if args.command == "group-notice-send":
        return await runtime.execute(
            "groups.notice.send",
            {
                "group": args.group,
                "title": args.title,
                "content": args.content,
                "pcode": args.pcode,
            },
            args.confirmation_token,
        )
    if args.command == "group-review-reminders":
        return await runtime.execute("groups.review_reminders.list", {"group": args.group})
    if args.command == "group-review-reminder-create":
        return await runtime.execute(
            "groups.review_reminder.create",
            {
                "group": args.group,
                "start_time": args.start_time,
                "end_time": args.end_time,
                "weeks": args.weeks,
                "puids": args.puids,
            },
            args.confirmation_token,
        )
    if args.command == "group-review-reminder-update":
        parameters = {"group": args.group, "reminder": args.reminder}
        for key in ("start_time", "end_time", "weeks", "puids"):
            value = getattr(args, key)
            if value is not None:
                parameters[key] = value
        return await runtime.execute(
            "groups.review_reminder.update", parameters, args.confirmation_token
        )
    if args.command == "group-review-reminders-delete":
        return await runtime.execute(
            "groups.review_reminders.delete",
            {"group": args.group, "reminders": args.reminders},
            args.confirmation_token,
        )
    if args.command == "group-labels":
        return await runtime.execute("groups.labels.list", {"group": args.group})
    if args.command == "group-label-create":
        return await runtime.execute(
            "groups.label.create", {"group": args.group, "name": args.name}
        )
    if args.command == "group-label-rename":
        return await runtime.execute(
            "groups.label.rename",
            {"group": args.group, "label": args.label, "name": args.name},
        )
    if args.command == "group-labels-reorder":
        return await runtime.execute(
            "groups.labels.reorder", {"group": args.group, "labels": args.labels}
        )
    if args.command == "group-labels-delete":
        return await runtime.execute(
            "groups.labels.delete",
            {"group": args.group, "labels": args.labels},
            args.confirmation_token,
        )
    if args.command == "group-deletion-reasons":
        return await runtime.execute("groups.deletion_reasons.list", {"group": args.group})
    if args.command == "group-deletion-reason-create":
        return await runtime.execute(
            "groups.deletion_reason.create", {"group": args.group, "name": args.name}
        )
    if args.command == "group-deletion-reason-rename":
        return await runtime.execute(
            "groups.deletion_reason.rename",
            {"group": args.group, "reason": args.reason, "name": args.name},
        )
    if args.command == "group-deletion-reasons-delete":
        return await runtime.execute(
            "groups.deletion_reasons.delete",
            {"group": args.group, "reasons": args.reasons},
            args.confirmation_token,
        )
    if args.command == "group-recycle":
        return await runtime.execute("groups.recycle.list", {"group": args.group})
    if args.command == "group-recycle-restore":
        return await runtime.execute(
            "groups.recycle.restore", {"group": args.group, "items": args.items}
        )
    if args.command == "group-recycle-delete":
        return await runtime.execute(
            "groups.recycle.items.delete",
            {"group": args.group, "items": args.items},
            args.confirmation_token,
        )
    if args.command == "group-recycle-empty":
        return await runtime.execute(
            "groups.recycle.empty",
            {"group": args.group},
            args.confirmation_token,
        )
    if args.command == "group-exports":
        return await runtime.execute("groups.exports.list", {"group": args.group})
    if args.command == "group-member-export":
        return await runtime.execute("groups.members.export.create", {"group": args.group})
    if args.command == "group-export-download":
        return await runtime.execute(
            "groups.export.download",
            {
                "group": args.group,
                "export": args.export,
                "output_path": args.output_path,
                "overwrite": args.overwrite,
                "wait_seconds": args.wait_seconds,
            },
        )
    if args.command == "group-export-wait":
        return await runtime.execute(
            "groups.export.wait",
            {
                "group": args.group,
                "export": args.export,
                "timeout_seconds": args.timeout_seconds,
                "poll_seconds": args.poll_seconds,
            },
        )
    if args.command == "group-export-retry":
        return await runtime.execute(
            "groups.export.retry",
            {"group": args.group, "export": args.export},
        )
    if args.command == "group-export-cancel":
        return await runtime.execute(
            "groups.export.cancel",
            {"group": args.group, "export": args.export},
            args.confirmation_token,
        )
    if args.command == "group-activities":
        return await runtime.execute(
            "groups.activities.list",
            {"group": args.group, "status": args.status, "max_items": args.max_items},
        )
    if args.command == "group-activity-image-upload":
        return await runtime.execute("groups.activity.image.upload", {"file": args.file})
    if args.command == "group-activity-create":
        return await runtime.execute(
            "groups.activity.create",
            {
                "group": args.group,
                "title": args.title,
                "online": args.online,
                "app_link": args.app_link,
                "pc_link": args.pc_link,
                "app_image_url": args.app_image_url,
                "pc_image_url": args.pc_image_url,
                "app_image_width": args.app_image_width,
                "app_image_height": args.app_image_height,
                "pc_image_width": args.pc_image_width,
                "pc_image_height": args.pc_image_height,
            },
            args.confirmation_token,
        )
    if args.command == "group-activity-update":
        parameters = {"group": args.group, "activity": args.activity}
        for field in (
            "title",
            "app_link",
            "pc_link",
            "app_image_url",
            "pc_image_url",
            "app_image_width",
            "app_image_height",
            "pc_image_width",
            "pc_image_height",
        ):
            value = getattr(args, field)
            if value is not None:
                parameters[field] = value
        return await runtime.execute("groups.activity.update", parameters, args.confirmation_token)
    if args.command == "group-activity-status":
        return await runtime.execute(
            "groups.activity.online_status.update",
            {
                "group": args.group,
                "activity": args.activity,
                "online": args.status == "online",
            },
            args.confirmation_token,
        )
    if args.command == "group-activities-reorder":
        return await runtime.execute(
            "groups.activities.reorder",
            {"group": args.group, "activities": args.activities},
            args.confirmation_token,
        )
    if args.command == "group-activity-delete":
        return await runtime.execute(
            "groups.activity.delete",
            {"group": args.group, "activity": args.activity},
            args.confirmation_token,
        )
    if args.command == "group-top":
        return await runtime.execute(
            "groups.top_status.update",
            {"group": args.group, "top": not args.off},
        )
    if args.command == "group-move":
        return await runtime.execute(
            "groups.move",
            {"group": args.group, "destination_folder": args.destination_folder},
        )
    if args.command == "group-quit":
        return await runtime.execute(
            "groups.quit",
            {"group": args.group},
            args.confirmation_token,
        )
    if args.command == "group-dismiss":
        return await runtime.execute(
            "groups.dismiss",
            {"group": args.group},
            args.confirmation_token,
        )
    if args.command == "group-members":
        return await runtime.execute(
            "groups.members.list",
            {"group": args.group, "search": args.search},
        )
    if args.command == "group-member-bulk-import-status":
        return await runtime.execute("groups.members.bulk_import.status", {"group": args.group})
    if args.command == "group-member-bulk-import-template":
        return await runtime.execute(
            "groups.members.bulk_import.template.download",
            {
                "group": args.group,
                "output_path": args.output_path,
                "overwrite": args.overwrite,
            },
        )
    if args.command == "group-members-bulk-import":
        return await runtime.execute(
            "groups.members.bulk_import",
            {"group": args.group, "file": args.file},
            args.confirmation_token,
        )
    if args.command == "group-member-read":
        return await runtime.execute(
            "groups.member.read",
            {"group": args.group, "member": args.member},
        )
    if args.command == "group-member-permissions":
        return await runtime.execute(
            "groups.member.permissions.read",
            {"group": args.group, "member": args.member},
        )
    if args.command == "group-member-permissions-update":
        return await runtime.execute(
            "groups.member.permissions.update",
            {
                "group": args.group,
                "member": args.member,
                "changes": _parse_permission_changes(args.permission_changes),
            },
            args.confirmation_token,
        )
    if args.command == "group-member-sources":
        return await runtime.execute(
            "groups.member.sources.list",
            {"group": args.group},
        )
    if args.command == "group-member-candidates":
        return await runtime.execute(
            "groups.member.candidates.list",
            {
                "group": args.group,
                "source_type": args.source_type,
                "source": args.source,
                "fid": args.fid,
                "search": args.search,
                "account_type": args.account_type,
            },
        )
    if args.command == "group-members-add":
        return await runtime.execute(
            "groups.members.add",
            {"group": args.group, "puids": args.puids},
            args.confirmation_token,
        )
    if args.command == "group-member-manager":
        return await runtime.execute(
            "groups.member.manager_status.update",
            {"group": args.group, "member": args.member, "manager": not args.off},
            args.confirmation_token,
        )
    if args.command == "group-member-remove":
        return await runtime.execute(
            "groups.member.remove",
            {"group": args.group, "member": args.member},
            args.confirmation_token,
        )
    if args.command == "group-transfer":
        return await runtime.execute(
            "groups.creator.transfer",
            {"group": args.group, "member": args.member},
            args.confirmation_token,
        )
    if args.command == "group-members-clear-external":
        return await runtime.execute(
            "groups.members.external.clear",
            {"group": args.group},
            args.confirmation_token,
        )
    if args.command == "group-folders":
        return await runtime.execute(
            "groups.folders.list",
            {"parent_folder": args.parent_folder, "search": args.search},
        )
    if args.command == "group-folder-tree":
        return await runtime.execute("groups.folders.tree")
    if args.command == "group-folder-create":
        return await runtime.execute(
            "groups.folder.create",
            {"name": args.name, "parent_folder": args.parent_folder},
        )
    if args.command == "group-folder-rename":
        return await runtime.execute(
            "groups.folder.rename",
            {"folder": args.folder, "name": args.name},
        )
    if args.command == "group-folder-move":
        return await runtime.execute(
            "groups.folder.move",
            {"folder": args.folder, "destination_folder": args.destination_folder},
        )
    if args.command == "group-folder-top":
        return await runtime.execute(
            "groups.folder.top_status.update",
            {"folder": args.folder, "top": not args.off},
        )
    if args.command == "group-folder-delete":
        return await runtime.execute(
            "groups.folder.delete",
            {"folder": args.folder},
            args.confirmation_token,
        )
    if args.command == "group-topics":
        return await runtime.execute(
            "groups.topics.list",
            {"group": args.group, "folder": args.folder, "search": args.search},
        )
    if args.command == "group-topic-read":
        return await runtime.execute(
            "groups.topic.read",
            {
                "group": args.group,
                "topic": args.topic,
                "order": args.order,
                "reply_search": args.reply_search,
            },
        )
    if args.command == "group-topic-create":
        return await runtime.execute(
            "groups.topic.create",
            {
                "group": args.group,
                "title": args.title,
                "content": args.content,
                "folder": args.folder,
                "anonymous": args.anonymous,
            },
            args.confirmation_token,
        )
    if args.command == "group-topic-update":
        parameters = {"group": args.group, "topic": args.topic}
        if args.title is not None:
            parameters["title"] = args.title
        if args.content is not None:
            parameters["content"] = args.content
        return await runtime.execute(
            "groups.topic.update",
            parameters,
            args.confirmation_token,
        )
    if args.command == "group-topic-delete":
        return await runtime.execute(
            "groups.topic.delete",
            {"group": args.group, "topic": args.topic},
            args.confirmation_token,
        )
    if args.command == "group-topic-choice":
        return await runtime.execute(
            "groups.topic.choice_status.update",
            {"group": args.group, "topic": args.topic, "choice": not args.off},
            args.confirmation_token,
        )
    if args.command == "group-topic-praise":
        return await runtime.execute(
            "groups.topic.praise_status.update",
            {"group": args.group, "topic": args.topic, "praised": not args.off},
            args.confirmation_token,
        )
    if args.command == "group-topics-score":
        return await runtime.execute(
            "groups.topics.score.set",
            {"group": args.group, "topics": args.topics, "score": args.score},
            args.confirmation_token,
        )
    if args.command == "group-topics-move":
        return await runtime.execute(
            "groups.topics.move",
            {
                "group": args.group,
                "topics": args.topics,
                "destination_folder": args.destination_folder,
            },
        )
    if args.command == "group-topics-delete":
        return await runtime.execute(
            "groups.topics.delete",
            {"group": args.group, "topics": args.topics},
            args.confirmation_token,
        )
    if args.command == "group-topic-reply":
        return await runtime.execute(
            "groups.topic.reply.create",
            {
                "group": args.group,
                "topic": args.topic,
                "content": args.content,
                "reply_to": args.reply_to,
                "anonymous": args.anonymous,
            },
            args.confirmation_token,
        )
    if args.command == "group-topic-reply-update":
        return await runtime.execute(
            "groups.topic.reply.update",
            {
                "group": args.group,
                "topic": args.topic,
                "reply": args.reply,
                "content": args.content,
            },
            args.confirmation_token,
        )
    if args.command == "group-topic-reply-delete":
        return await runtime.execute(
            "groups.topic.reply.delete",
            {"group": args.group, "topic": args.topic, "reply": args.reply},
            args.confirmation_token,
        )
    if args.command == "group-topic-folder-tree":
        return await runtime.execute(
            "groups.topic.folders.tree",
            {"group": args.group},
        )
    if args.command == "group-topic-top":
        return await runtime.execute(
            "groups.topic.top_status.update",
            {"group": args.group, "topic": args.topic, "top": not args.off},
        )
    if args.command == "group-topic-move":
        return await runtime.execute(
            "groups.topic.move",
            {
                "group": args.group,
                "topic": args.topic,
                "destination_folder": args.destination_folder,
            },
        )
    if args.command == "group-topic-folder-create":
        return await runtime.execute(
            "groups.topic.folder.create",
            {
                "group": args.group,
                "name": args.name,
                "parent_folder": args.parent_folder,
            },
        )
    if args.command == "group-topic-folder-rename":
        return await runtime.execute(
            "groups.topic.folder.rename",
            {"group": args.group, "folder": args.folder, "name": args.name},
        )
    if args.command == "group-topic-folder-move":
        return await runtime.execute(
            "groups.topic.folder.move",
            {
                "group": args.group,
                "folder": args.folder,
                "destination_folder": args.destination_folder,
            },
        )
    if args.command == "group-topic-folder-delete":
        return await runtime.execute(
            "groups.topic.folder.delete",
            {"group": args.group, "folder": args.folder},
            args.confirmation_token,
        )
    if args.command == "group-topic-folders-move":
        return await runtime.execute(
            "groups.topic.folders.move",
            {
                "group": args.group,
                "folders": args.folders,
                "destination_folder": args.destination_folder,
            },
        )
    if args.command == "group-topic-folders-delete":
        return await runtime.execute(
            "groups.topic.folders.delete",
            {"group": args.group, "folders": args.folders},
            args.confirmation_token,
        )
    if args.command == "group-topic-drafts":
        return await runtime.execute(
            "groups.topic.drafts.list",
            {"group": args.group, "search": args.search},
        )
    if args.command == "group-topic-draft-read":
        return await runtime.execute(
            "groups.topic.draft.read",
            {"group": args.group, "draft": args.draft},
        )
    if args.command == "group-topic-draft-save":
        return await runtime.execute(
            "groups.topic.draft.save",
            {
                "group": args.group,
                "title": args.title,
                "content": args.content,
                "draft": args.draft,
                "folder": args.folder,
            },
        )
    if args.command == "group-topic-draft-publish":
        return await runtime.execute(
            "groups.topic.draft.publish",
            {"group": args.group, "draft": args.draft},
            args.confirmation_token,
        )
    if args.command == "courses":
        return await runtime.execute("courses.list_teaching")
    if args.command == "learning-courses":
        return await runtime.execute(
            "learning.courses.list",
            {"search": args.search},
        )
    if args.command == "learning-modules":
        return await runtime.execute(
            "learning.course.modules.discover",
            {"course": args.course},
        )
    if args.command == "learning-open":
        return await runtime.execute(
            "learning.course.module.open",
            {"course": args.course, "module": args.module},
        )
    if args.command == "learning-activities":
        return await runtime.execute(
            "learning.course.activities.list",
            {"course": args.course, "search": args.search, "status": args.status},
        )
    if args.command == "learning-chapters":
        return await runtime.execute(
            "learning.course.chapters.list",
            {"course": args.course, "search": args.search},
        )
    if args.command == "learning-discussions":
        return await runtime.execute(
            "learning.course.discussions.list",
            {
                "course": args.course,
                "search": args.search,
                "class_only": args.class_only,
            },
        )
    if args.command == "learning-discussion-read":
        return await runtime.execute(
            "learning.course.discussions.topic.read",
            {
                "course": args.course,
                "topic": args.topic,
                "class_only": args.class_only,
                "order": args.order,
                "reply_search": args.reply_search,
            },
        )
    if args.command == "learning-discussion-create":
        return await runtime.execute(
            "learning.course.discussions.topic.create",
            {
                "course": args.course,
                "title": args.title,
                "content": args.content,
                "anonymous": args.anonymous,
            },
            args.confirmation_token,
        )
    if args.command == "learning-discussion-update":
        return await runtime.execute(
            "learning.course.discussions.topic.update",
            {
                "course": args.course,
                "topic": args.topic,
                "title": args.title,
                "content": args.content,
            },
            args.confirmation_token,
        )
    if args.command == "learning-discussion-delete":
        return await runtime.execute(
            "learning.course.discussions.topic.delete",
            {"course": args.course, "topic": args.topic},
            args.confirmation_token,
        )
    if args.command == "learning-discussion-reply-create":
        return await runtime.execute(
            "learning.course.discussions.reply.create",
            {
                "course": args.course,
                "topic": args.topic,
                "content": args.content,
                "reply_to": args.reply_to,
                "anonymous": args.anonymous,
            },
            args.confirmation_token,
        )
    if args.command == "learning-discussion-reply-update":
        return await runtime.execute(
            "learning.course.discussions.reply.update",
            {
                "course": args.course,
                "topic": args.topic,
                "reply": args.reply,
                "content": args.content,
            },
            args.confirmation_token,
        )
    if args.command == "learning-discussion-reply-delete":
        return await runtime.execute(
            "learning.course.discussions.reply.delete",
            {
                "course": args.course,
                "topic": args.topic,
                "reply": args.reply,
            },
            args.confirmation_token,
        )
    if args.command in {"learning-homeworks", "learning-exams", "learning-self-tests"}:
        action = {
            "learning-homeworks": "learning.course.homeworks.list",
            "learning-exams": "learning.course.exams.list",
            "learning-self-tests": "learning.course.self_tests.list",
        }[args.command]
        return await runtime.execute(
            action,
            {"course": args.course, "search": args.search, "status": args.status},
        )
    if args.command == "learning-homework-read":
        return await runtime.execute(
            "learning.course.homework.read",
            {"course": args.course, "homework": args.homework},
        )
    if args.command == "learning-homework-answer-enter":
        return await runtime.execute(
            "learning.course.homework.answer.enter",
            {"course": args.course, "homework": args.homework},
        )
    if args.command == "learning-homework-answer-save":
        return await runtime.execute(
            "learning.course.homework.answers.save",
            {
                "course": args.course,
                "homework": args.homework,
                "updates": _parse_json_list(args.updates_json, "updates-json"),
            },
        )
    if args.command == "learning-homework-submit":
        return await runtime.execute(
            "learning.course.homework.submit",
            {"course": args.course, "homework": args.homework},
            confirmation_token=args.confirmation_token,
        )
    if args.command == "learning-homework-redo":
        return await runtime.execute(
            "learning.course.homework.redo",
            {"course": args.course, "homework": args.homework},
            confirmation_token=args.confirmation_token,
        )
    if args.command == "learning-homework-attempts":
        return await runtime.execute(
            "learning.course.homework.attempts.list",
            {"course": args.course, "homework": args.homework},
        )
    if args.command == "learning-homework-attempt-read":
        return await runtime.execute(
            "learning.course.homework.attempt.read",
            {
                "course": args.course,
                "homework": args.homework,
                "attempt": args.attempt,
            },
        )
    if args.command == "learning-materials":
        return await runtime.execute(
            "learning.course.materials.list",
            {"course": args.course, "folder": args.folder, "search": args.search},
        )
    if args.command == "learning-ai-tools":
        return await runtime.execute(
            "learning.course.ai_tools.list",
            {"course": args.course},
        )
    if args.command == "learning-wrong-questions":
        return await runtime.execute(
            "learning.course.wrong_questions.summary",
            {"course": args.course},
        )
    if args.command == "learning-records":
        return await runtime.execute(
            "learning.course.records.read",
            {"course": args.course},
        )
    if args.command == "learning-graph":
        return await runtime.execute(
            "learning.course.knowledge_graph.list",
            {"course": args.course, "search": args.search, "level": args.level},
        )
    if args.command == "learning-graph-node":
        return await runtime.execute(
            "learning.course.knowledge_graph.node.read",
            {"course": args.course, "node": args.node},
        )
    if args.command == "learning-graph-models":
        return await runtime.execute(
            "learning.course.knowledge_graph.models.list",
            {"course": args.course, "search": args.search},
        )
    if args.command == "learning-graph-model":
        return await runtime.execute(
            "learning.course.knowledge_graph.model.read",
            {"course": args.course, "model": args.model},
        )
    if args.command == "learning-integrity":
        return await runtime.execute(
            "learning.course.integrity.read",
            {"course": args.course},
        )
    if args.command == "learning-integrity-accept":
        return await runtime.execute(
            "learning.course.integrity.accept",
            {"course": args.course},
            args.confirmation_token,
        )
    if args.command == "classes":
        return await runtime.execute("courses.list_classes", {"course": args.course})
    if args.command == "class-create":
        return await runtime.execute(
            "classes.create",
            {"course": args.course, "name": args.name},
            args.confirmation_token,
        )
    if args.command == "class-rename":
        return await runtime.execute(
            "class.rename",
            {"course": args.course, "clazz": args.clazz, "name": args.name},
            args.confirmation_token,
        )
    if args.command == "class-settings":
        params = {"course": args.course}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("class.settings.read", params)
    if args.command == "class-invitation":
        params = {"course": args.course}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("class.invitation.read", params)
    if args.command == "class-settings-update":
        params = {"course": args.course}
        if args.clazz:
            params["clazz"] = args.clazz
        option_names = (
            "allow_student_join",
            "join_requires_approval",
            "unit_binding_requirement",
            "allow_student_withdraw",
            "public_scope",
            "student_limit",
            "ended",
            "ignore_video_restrictions",
            "hidden_from_students",
            "semester_id",
            "open_start",
            "open_end",
            "application_start",
            "application_end",
        )
        params.update(
            {name: getattr(args, name) for name in option_names if getattr(args, name) is not None}
        )
        return await runtime.execute("class.settings.update", params, args.confirmation_token)
    if args.command == "class-delete":
        return await runtime.execute(
            "class.delete",
            {"course": args.course, "clazz": args.clazz},
            args.confirmation_token,
        )
    if args.command == "students":
        params = {
            "course": args.course,
            "search": args.search,
            "school_status": args.school_status,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("class.students.list", params)
    if args.command == "student-candidates":
        params = {
            "course": args.course,
            "query": args.query,
            "page": args.page,
            "page_size": args.page_size,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("class.student_candidates.search", params)
    if args.command == "add-student-from-bank":
        params = {"course": args.course, "student": args.student}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "class.student.add_from_bank",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "add-student":
        params = {
            "course": args.course,
            "name": args.name,
            "identity": args.identity,
            "identity_type": args.identity_type,
            "school_id": args.school_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "class.student.add_by_identity",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "remove-student":
        params = {"course": args.course, "student": args.student}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "class.student.remove",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "join-applications":
        params = {"course": args.course}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("class.join_applications.list", params)
    if args.command == "decide-join-application":
        params = {
            "course": args.course,
            "application": args.application,
            "decision": args.decision,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "class.join_application.decide",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "move-student":
        return await runtime.execute(
            "class.student.move",
            {
                "course": args.course,
                "clazz": args.source_clazz,
                "target_clazz": args.target_clazz,
                "student": args.student,
            },
            confirmation_token=args.confirmation_token,
        )
    if args.command == "access-logs":
        params = {
            "course": args.course,
            "student": args.student,
            "year": args.year,
            "month": args.month,
            "day": args.day,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("class.student.access_logs.list", params)
    if args.command == "operation-logs":
        params = {
            "course": args.course,
            "module": args.module,
            "search": args.search,
            "start_date": args.start_date,
            "end_date": args.end_date,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("course.operation_logs.list", params)
    if args.command == "student-join-logs":
        params = {
            "course": args.course,
            "join_type": args.join_type,
            "search": args.search,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("class.student_join_logs.list", params)
    if args.command == "student-leave-logs":
        params = {"course": args.course, "search": args.search}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("class.student_leave_logs.list", params)
    if args.command == "restore-student":
        params = {"course": args.course, "student": args.student}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "class.student.restore",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "teachers":
        params = {"course": args.course, "search": args.search, "role": args.role}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("course.teachers.list", params)
    if args.command == "teacher-candidates":
        params = {
            "course": args.course,
            "query": args.query,
            "role": args.role,
            "page": args.page,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("course.teacher_candidates.search", params)
    if args.command == "add-teacher-from-bank":
        params = {"course": args.course, "teacher": args.teacher, "role": args.role}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "course.teacher.add_from_bank",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "add-teacher":
        params = {
            "course": args.course,
            "name": args.name,
            "identity": args.identity,
            "identity_type": args.identity_type,
            "role": args.role,
            "school_id": args.school_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "course.teacher.add_by_identity",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "remove-teacher":
        params = {"course": args.course, "teacher": args.teacher}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "course.teacher.remove",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "teacher-permissions":
        params = {"course": args.course, "teacher": args.teacher}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("course.teacher.permissions.read", params)
    if args.command == "teacher-permissions-update":
        params = {
            "course": args.course,
            "teacher": args.teacher,
            "changes": _parse_permission_changes(args.permission_changes),
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "course.teacher.permissions.update",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "grade-weights":
        params = {"course": args.course}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("course.grade_weights.read", params)
    if args.command == "grades":
        params = {
            "course": args.course,
            "search": args.search,
            "raw_scores": args.raw_scores,
            "sort": args.sort,
            "descending": args.descending,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("course.grades.list", params)
    if args.command == "grade-visibility":
        params = {"course": args.course}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("course.grade_visibility.read", params)
    if args.command == "set-grade-visibility":
        params = {
            "course": args.course,
            "visible_classes": args.visible_classes,
            "scheduled_open": args.scheduled_open,
            "open_at": args.open_at,
            "students_can_view_rank": args.show_rank,
            "students_can_view_class_average": args.show_average,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "course.grade_visibility.set",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "override-grade":
        params = {
            "course": args.course,
            "student": args.student,
            "score": args.score,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "course.grade_override.set",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "progress":
        params = {
            "course": args.course,
            "search": args.search,
            "sort": args.sort,
            "descending": args.descending,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("course.learning_progress.list", params)
    if args.command == "monitor":
        params = {
            "course": args.course,
            "search": args.search,
            "only_abnormal": args.only_abnormal,
            "anomaly_type": args.anomaly_type,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("course.study_monitor.list", params)
    if args.command == "monitor-remind":
        params = {
            "course": args.course,
            "student": args.student,
            "title": args.title,
            "content": args.content,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "course.study_monitor.remind",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "monitor-clear":
        params = {"course": args.course, "student": args.student}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "course.study_monitor.clear",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "modules":
        params = {"course": args.course}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("course.modules.discover", params)
    if args.command == "open-module":
        params = {"course": args.course, "module": args.module}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("course.module.open", params)
    if args.command == "knowledge-hub-status":
        params = {"course": args.course}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_hub.status.read", params)
    if args.command == "knowledge-hub-bases":
        params = {
            "course": args.course,
            "module": args.module,
            "page": args.page,
            "page_size": args.page_size,
            "category": args.category,
            "state": args.state,
            "creator": args.creator,
            "search": args.search,
            "begin_time": args.begin_time,
            "end_time": args.end_time,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_hub.bases.list", params)
    if args.command == "knowledge-hub-base":
        params = {"course": args.course, "base": args.base, "module": args.module}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_hub.base.read", params)
    if args.command == "knowledge-hub-statistics":
        params = {"course": args.course, "module": args.module}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_hub.statistics.read", params)
    if args.command == "knowledge-hub-base-create":
        params = {
            "course": args.course,
            "name": args.name,
            "description": args.description,
            "category": args.category,
            "cover": args.cover,
        }
        split_rule = _parse_json_object(args.split_rule_json, "split-rule-json")
        if split_rule is not None:
            params["split_rule"] = split_rule
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_hub.base.create", params)
    if args.command == "knowledge-hub-base-update":
        params = {"course": args.course, "base": args.base}
        for key in ("name", "description", "cover"):
            value = getattr(args, key)
            if value is not None:
                params[key] = value
        split_rule = _parse_json_object(args.split_rule_json, "split-rule-json")
        if split_rule is not None:
            params["split_rule"] = split_rule
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_hub.base.update", params)
    if args.command == "knowledge-hub-base-availability":
        params = {
            "course": args.course,
            "base": args.base,
            "enabled": args.status == "enable",
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_hub.base.availability.update", params)
    if args.command == "knowledge-hub-base-priority":
        params = {"course": args.course, "base": args.base, "priority": not args.off}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_hub.base.priority.update", params)
    if args.command == "knowledge-hub-base-share":
        params = {"course": args.course, "base": args.base, "shared": not args.off}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "knowledge_hub.base.share.update",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "knowledge-hub-base-delete":
        params = {"course": args.course, "base": args.base}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "knowledge_hub.base.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "knowledge-hub-documents":
        params = {
            "course": args.course,
            "base": args.base,
            "page": args.page,
            "page_size": args.page_size,
            "state": args.state,
            "source": args.source,
            "search": args.search,
            "classify_id": args.classify_id,
            "file_type": args.file_type,
            "begin_time": args.begin_time,
            "end_time": args.end_time,
            "order": args.order,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_hub.documents.list", params)
    if args.command == "knowledge-hub-document-download":
        params = {
            "course": args.course,
            "base": args.base,
            "document": args.document,
            "output_path": args.output_path,
            "overwrite": args.overwrite,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_hub.document.download", params)
    if args.command == "knowledge-hub-document-upload":
        params = {
            "course": args.course,
            "base": args.base,
            "file": args.file,
            "classify_id": args.classify_id,
        }
        split_rule = _parse_json_object(args.split_rule_json, "split-rule-json")
        if split_rule is not None:
            params["split_rule"] = split_rule
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_hub.document.upload", params)
    if args.command == "knowledge-hub-document-delete":
        params = {
            "course": args.course,
            "base": args.base,
            "document": args.document,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "knowledge_hub.document.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "ai-groups":
        params = {"course": args.course}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("ai_workbench.groups.list", params)
    if args.command == "ai-group-create":
        params = {"course": args.course, "name": args.name}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "ai_workbench.group.create",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "ai-group-rename":
        params = {"course": args.course, "group": args.group, "name": args.name}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "ai_workbench.group.rename",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "ai-group-reorder":
        params = {"course": args.course, "groups": args.groups}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "ai_workbench.group.reorder",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "ai-group-delete":
        params = {
            "course": args.course,
            "group": args.group,
            "allow_nonempty": args.allow_nonempty,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "ai_workbench.group.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "ai-commands":
        params = {
            "course": args.course,
            "group": args.group,
            "search": args.search,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("ai_workbench.commands.list", params)
    if args.command == "ai-command-read":
        params = {"course": args.course, "command": args.ai_command, "group": args.group}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("ai_workbench.command.read", params)
    if args.command == "ai-command-create":
        params = {
            "course": args.course,
            "group": args.group,
            "name": args.name,
            "content": args.content,
            "explanation": args.explanation,
            "prompt_words": args.prompt_words,
            "role_type": args.role_type,
            "classify_id": args.classify_id,
            "command_ability": args.command_ability,
            "ability_type": args.ability_type,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "ai_workbench.command.create",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "ai-command-update":
        params = {"course": args.course, "command": args.ai_command, "group": args.group}
        for key in (
            "name",
            "content",
            "explanation",
            "prompt_words",
            "role_type",
            "classify_id",
            "command_ability",
            "ability_type",
        ):
            value = getattr(args, key)
            if value is not None:
                params[key] = value
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "ai_workbench.command.update",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "ai-command-move":
        params = {
            "course": args.course,
            "command": args.ai_command,
            "target_group": args.target_group,
            "group": args.group,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "ai_workbench.command.move",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "ai-command-reorder":
        params = {
            "course": args.course,
            "group": args.group,
            "role_type": args.role_type,
            "commands": args.commands,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "ai_workbench.command.reorder",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "ai-command-publish":
        params = {
            "course": args.course,
            "command": args.ai_command,
            "group": args.group,
            "published": not args.off,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "ai_workbench.command.publish_status.update",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "ai-command-delete":
        params = {"course": args.course, "command": args.ai_command, "group": args.group}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "ai_workbench.command.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "ai-recommendations":
        params = {"course": args.course, "page": args.page}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("ai_workbench.recommendations.list", params)
    if args.command == "ai-recommendation-add":
        params = {
            "course": args.course,
            "recommendation": args.recommendation,
            "group": args.group,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "ai_workbench.recommendation.add",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "task-folders":
        params = {"course": args.course}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("task_engine.folders.list", params)
    if args.command == "task-list":
        params = {
            "course": args.course,
            "folder": args.folder,
            "search": args.search,
            "recycled": args.recycled,
            "max_items": args.max_items,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("task_engine.tasks.list", params)
    if args.command == "task-read":
        params = {"course": args.course, "task": args.task}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("task_engine.task.read", params)
    if args.command == "task-folder-create":
        params = {"course": args.course, "name": args.name}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("task_engine.folder.create", params)
    if args.command == "task-folder-rename":
        params = {"course": args.course, "folder": args.folder, "name": args.name}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("task_engine.folder.rename", params)
    if args.command == "task-folder-delete":
        params = {
            "course": args.course,
            "folder": args.folder,
            "allow_nonempty": args.allow_nonempty,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "task_engine.folder.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "task-create":
        params = {
            "course": args.course,
            "name": args.name,
            "folder": args.folder,
            "introduce": args.introduce,
            "rich_text": args.rich_text,
            "cover": args.cover,
            "target": args.target,
        }
        if args.selected_modes is not None:
            params["selected_modes"] = args.selected_modes
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("task_engine.task.create", params)
    if args.command == "task-update":
        params = {"course": args.course, "task": args.task}
        for key in (
            "name",
            "introduce",
            "rich_text",
            "cover",
            "target",
            "start_date",
            "end_date",
            "selected_modes",
        ):
            value = getattr(args, key)
            if value is not None:
                params[key] = value
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("task_engine.task.update", params)
    if args.command == "task-move":
        params = {"course": args.course, "task": args.task, "folder": args.folder}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("task_engine.task.move", params)
    if args.command == "task-reorder":
        params = {
            "course": args.course,
            "folder": args.folder,
            "task_order": args.task_order,
        }
        if args.folder_order is not None:
            params["folder_order"] = args.folder_order
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("task_engine.order.update", params)
    if args.command == "task-copy":
        params = {
            "course": args.course,
            "task": args.task,
            "name": args.name,
            "folder": args.folder,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("task_engine.task.copy", params)
    if args.command == "task-delete":
        params = {"course": args.course, "task": args.task}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "task_engine.task.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "task-recycle":
        params = {
            "course": args.course,
            "search": args.search,
            "max_items": args.max_items,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("task_engine.recycle.list", params)
    if args.command == "task-restore":
        params = {"course": args.course, "task": args.task}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("task_engine.task.restore", params)
    if args.command == "task-labels":
        params = {
            "course": args.course,
            "task": args.task,
            "search": args.search,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("task_engine.labels.list", params)
    if args.command == "task-label-create":
        params = {"course": args.course, "task": args.task, "name": args.name}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("task_engine.label.create", params)
    if args.command == "task-label-rename":
        params = {
            "course": args.course,
            "task": args.task,
            "label": args.label,
            "name": args.name,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("task_engine.label.rename", params)
    if args.command == "task-label-delete":
        params = {"course": args.course, "task": args.task, "label": args.label}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "task_engine.label.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "task-export":
        params = {
            "course": args.course,
            "folder": args.folder,
            "tasks": args.tasks,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("task_engine.export.request", params)
    if args.command == "task-publish":
        params = {
            "course": args.course,
            "task": args.task,
            "published": not args.off,
        }
        course_publish = _parse_json_list(args.course_publish_json, "course-publish-json")
        task_publish = _parse_json_list(args.task_publish_json, "task-publish-json")
        if course_publish is not None:
            params["course_publish_param"] = course_publish
        if task_publish is not None:
            params["task_publish_param"] = task_publish
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "task_engine.publish_status.update",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "graph":
        params = {"course": args.course, "search": args.search}
        if args.level is not None:
            params["level"] = args.level
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.graph.read", params)
    if args.command == "graph-node":
        params = {"course": args.course, "node": args.node}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.node.read", params)
    if args.command == "graph-node-create":
        params = {
            "course": args.course,
            "name": args.name,
            "node_type": args.node_type,
            "parent": args.parent,
            "description": args.description,
            "model": args.model,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.node.create", params)
    if args.command == "graph-node-update":
        params = {
            "course": args.course,
            "node": args.node,
            "name": args.name,
            "description": args.description,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.node.update", params)
    if args.command == "graph-node-relations":
        params = {"course": args.course, "node": args.node}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.node.relations.read", params)
    if args.command == "graph-node-relation-add":
        params = {
            "course": args.course,
            "node": args.node,
            "relation": args.relation,
            "target": args.target,
            "description": args.description,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "knowledge_graph.node.relation.add",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "graph-node-relation-remove":
        params = {
            "course": args.course,
            "node": args.node,
            "relation": args.relation,
            "target": args.target,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "knowledge_graph.node.relation.remove",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "graph-settings":
        params = {"course": args.course}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.settings.read", params)
    if args.command == "graph-settings-update":
        params = {"course": args.course}
        for key in (
            "show_all_relations",
            "show_all_topic_names",
            "navigation_node_scale",
            "graph_background_color",
        ):
            value = getattr(args, key)
            if value is not None:
                params[key] = value
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "knowledge_graph.settings.update",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "graph-advanced-settings":
        params = {"course": args.course}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.advanced_settings.read", params)
    if args.command == "graph-advanced-settings-update":
        params = {"course": args.course}
        for key in (
            "topic_card",
            "teach_target",
            "study_hours_enabled",
            "classify_relation_data",
            "selftest_included",
            "micro_preview",
            "micro_scale_mode",
        ):
            value = getattr(args, key)
            if value is not None:
                params[key] = value
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "knowledge_graph.advanced_settings.update",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "graph-models":
        params = {"course": args.course, "search": args.search}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.models.list", params)
    if args.command == "graph-model-data":
        params = {"course": args.course, "model": args.model}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.model.data.read", params)
    if args.command == "graph-model-create":
        params = {"course": args.course, "name": args.name, "style": args.style}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.model.create", params)
    if args.command == "graph-model-update":
        params = {"course": args.course, "model": args.model, "name": args.name}
        if args.style is not None:
            params["style"] = args.style
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.model.update", params)
    if args.command == "graph-model-visibility":
        params = {
            "course": args.course,
            "model": args.model,
            "visible": args.status == "show",
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "knowledge_graph.model.visibility.update",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "graph-model-reorder":
        params = {"course": args.course, "models": args.models}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.models.reorder", params)
    if args.command == "graph-model-delete":
        params = {"course": args.course, "model": args.model}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "knowledge_graph.model.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "graph-model-classes":
        params = {"course": args.course, "model": args.model}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.model.classes.list", params)
    if args.command == "graph-model-classes-update":
        params = {
            "course": args.course,
            "model": args.model,
            "visible_classes": args.visible_classes,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "knowledge_graph.model.classes.update",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "graph-events":
        params = {"course": args.course, "search": args.search}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.events.list", params)
    if args.command == "graph-event-create":
        params = {
            "course": args.course,
            "name": args.name,
            "topic_condition": args.topic_condition,
            "set_condition": args.set_condition,
            "percent1": args.percent1,
            "percent2": args.percent2,
            "executions": _parse_json_list(args.executions_json, "executions-json"),
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "knowledge_graph.event.create",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "graph-event-update":
        params = {"course": args.course, "event": args.event}
        for key in (
            "name",
            "topic_condition",
            "set_condition",
            "percent1",
            "percent2",
        ):
            value = getattr(args, key)
            if value is not None:
                params[key] = value
        if args.executions_json is not None:
            params["executions"] = _parse_json_list(args.executions_json, "executions-json")
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "knowledge_graph.event.update",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "graph-event-delete":
        params = {"course": args.course, "event": args.event}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "knowledge_graph.event.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "graph-export":
        params = {
            "course": args.course,
            "format": args.format,
            "output_path": args.output_path,
            "model": args.model,
            "overwrite": args.overwrite,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.export.download", params)
    if args.command == "graph-relations":
        params = {"course": args.course, "search": args.search}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.relation_types.list", params)
    if args.command == "graph-relation-create":
        params = {
            "course": args.course,
            "name": args.name,
            "meaning": args.meaning,
            "example_html": args.example_html,
            "color": args.color,
        }
        if args.relation_types is not None:
            params["relation_types"] = args.relation_types
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.relation_type.create", params)
    if args.command == "graph-relation-update":
        params = {"course": args.course, "relation": args.relation}
        for key in (
            "name",
            "meaning",
            "relation_types",
            "example_html",
            "color",
            "arrow_size",
            "line_thickness",
        ):
            value = getattr(args, key)
            if value is not None:
                params[key] = value
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.relation_type.update", params)
    if args.command == "graph-relation-delete":
        params = {"course": args.course, "relation": args.relation}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "knowledge_graph.relation_type.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "graph-category-create":
        params = {
            "course": args.course,
            "name": args.name,
            "description": args.description,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.category.create", params)
    if args.command == "graph-category-update":
        params = {
            "course": args.course,
            "node": args.node,
            "name": args.name,
            "description": args.description,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.category.update", params)
    if args.command == "graph-node-delete":
        params = {"course": args.course, "node": args.node}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "knowledge_graph.node.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "graph-labels":
        params = {"course": args.course, "search": args.search}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.labels.list", params)
    if args.command == "graph-label-group-create":
        params = {
            "course": args.course,
            "name": args.name,
            "group_type": args.group_type,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.label_group.create", params)
    if args.command == "graph-label-group-rename":
        params = {"course": args.course, "group": args.group, "name": args.name}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.label_group.rename", params)
    if args.command == "graph-label-group-delete":
        params = {"course": args.course, "group": args.group}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "knowledge_graph.label_group.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "graph-label-group-reorder":
        params = {"course": args.course, "groups": args.groups}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.label_groups.reorder", params)
    if args.command == "graph-label-create":
        params = {"course": args.course, "group": args.group, "name": args.name}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.label.create", params)
    if args.command == "graph-label-rename":
        params = {"course": args.course, "label": args.label, "name": args.name}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.label.rename", params)
    if args.command == "graph-label-move":
        params = {"course": args.course, "label": args.label, "group": args.group}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.label.move", params)
    if args.command == "graph-label-reorder":
        params = {"course": args.course, "group": args.group, "labels": args.labels}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("knowledge_graph.labels.reorder", params)
    if args.command == "graph-label-delete":
        params = {"course": args.course, "label": args.label}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "knowledge_graph.label.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "class-activity-types":
        params = {"course": args.course}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("class_activities.types.list", params)
    if args.command == "class-activity-groups":
        params = {"course": args.course}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("class_activities.groups.list", params)
    if args.command == "class-activity-group-create":
        params = {"course": args.course, "name": args.name}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("class_activities.group.create", params)
    if args.command == "class-activity-group-rename":
        params = {"course": args.course, "group": args.group, "name": args.name}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("class_activities.group.rename", params)
    if args.command == "class-activity-group-delete":
        params = {
            "course": args.course,
            "group": args.group,
            "allow_nonempty": args.allow_nonempty,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "class_activities.group.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "class-activity-group-reorder":
        params = {"course": args.course, "groups": args.groups}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("class_activities.groups.reorder", params)
    if args.command == "class-attendance-create":
        params = {
            "course": args.course,
            "mode": args.mode,
            "title": args.title,
            "duration_minutes": args.duration_minutes,
            "manual_end": args.manual_end,
            "late_minutes": args.late_minutes,
            "require_photo": args.require_photo,
            "qr_refresh_seconds": args.qr_refresh_seconds,
            "sign_code": args.sign_code,
            "gesture_code": args.gesture_code,
            "location_name": args.location_name,
            "latitude": args.latitude or "",
            "longitude": args.longitude or "",
            "location_range_m": args.location_range_m,
            "start": not args.save,
            "group": args.group,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "class_activities.attendance.create",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "class-activities":
        params = {
            "course": args.course,
            "group": args.group,
            "search": args.search,
            "status": args.status,
        }
        if args.activity_type is not None:
            params["activity_type"] = args.activity_type
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("class_activities.activities.list", params)
    if args.command == "class-activity-read":
        params = {"course": args.course, "activity": args.activity}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("class_activities.activity.read", params)
    if args.command == "class-activity-rename":
        params = {
            "course": args.course,
            "activity": args.activity,
            "name": args.name,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("class_activities.activity.rename", params)
    if args.command == "class-activity-move":
        params = {
            "course": args.course,
            "activity": args.activity,
            "group": args.group,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("class_activities.activity.move", params)
    if args.command == "class-activity-reorder":
        params = {
            "course": args.course,
            "group": args.group,
            "activities": args.activities,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("class_activities.activities.reorder", params)
    if args.command == "class-activity-start":
        params = {"course": args.course, "activity": args.activity}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "class_activities.activity.start",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "class-activity-end":
        params = {"course": args.course, "activity": args.activity}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "class_activities.activity.end",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "class-activity-delete":
        params = {"course": args.course, "activity": args.activity}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "class_activities.activity.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "class-activity-recycle":
        params = {
            "course": args.course,
            "search": args.search,
            "max_items": args.max_items,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("class_activities.recycle.list", params)
    if args.command == "class-activity-restore":
        params = {"course": args.course, "activity": args.activity}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("class_activities.recycle.restore", params)
    if args.command == "class-activity-recycle-delete":
        params = {"course": args.course, "activities": args.activities}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "class_activities.recycle.items.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "course-assets":
        params = {
            "course": args.course,
            "kind": args.kind,
            "folder": args.folder,
            "search": args.search,
            "page": args.page,
            "page_size": args.page_size,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("course_assets.items.list", params)
    if args.command == "course-asset-tree":
        params = {"course": args.course, "kind": args.kind, "search": args.search}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("course_assets.tree.list", params)
    if args.command == "course-asset-folder-create":
        params = {
            "course": args.course,
            "kind": args.kind,
            "name": args.name,
            "parent": args.parent,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "course_assets.folder.create",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "course-asset-cloud-import":
        params = {
            "course": args.course,
            "kind": args.kind,
            "resources": args.resources,
            "destination": args.destination,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "course_assets.cloud_files.import",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "course-asset-upload":
        params = {
            "course": args.course,
            "kind": args.kind,
            "file_path": args.file_path,
            "destination": args.destination,
            "name": args.name,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "course_assets.file.upload",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "course-asset-rename":
        params = {
            "course": args.course,
            "kind": args.kind,
            "asset": args.asset,
            "name": args.name,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("course_assets.item.rename", params)
    if args.command == "course-asset-top":
        params = {
            "course": args.course,
            "kind": args.kind,
            "asset": args.asset,
            "top": args.status == "top",
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("course_assets.item.top_status.update", params)
    if args.command == "course-asset-move":
        params = {
            "course": args.course,
            "kind": args.kind,
            "assets": args.assets,
            "destination": args.destination,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("course_assets.items.move", params)
    if args.command == "course-asset-copy":
        params = {"course": args.course, "kind": args.kind, "asset": args.asset}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "course_assets.item.copy",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "course-asset-delete":
        params = {"course": args.course, "kind": args.kind, "assets": args.assets}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "course_assets.items.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "course-asset-download":
        params = {
            "course": args.course,
            "kind": args.kind,
            "asset": args.asset,
            "output_path": args.output_path,
            "overwrite": args.overwrite,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("course_assets.item.download", params)
    if args.command == "course-asset-recycle":
        params = {"course": args.course, "kind": args.kind, "search": args.search}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("course_assets.recycle.list", params)
    if args.command == "course-asset-restore":
        params = {"course": args.course, "kind": args.kind, "assets": args.assets}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "course_assets.recycle.restore",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "course-asset-recycle-delete":
        params = {"course": args.course, "kind": args.kind, "assets": args.assets}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "course_assets.recycle.items.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "chapters":
        params = {"course": args.course, "search": args.search}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("chapters.list", params)
    if args.command == "chapter-tree":
        params = {"course": args.course}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("chapters.tree.list", params)
    if args.command == "chapter-cards":
        params = {"course": args.course, "chapter": args.chapter}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("chapters.cards.list", params)
    if args.command == "chapter-card-create":
        params = {
            "course": args.course,
            "chapter": args.chapter,
            "title": args.title,
            "content": args.content,
            "content_format": args.content_format,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("chapters.card.create", params)
    if args.command == "chapter-card-update":
        params = {
            "course": args.course,
            "chapter": args.chapter,
            "card": args.card,
            "content_format": args.content_format,
        }
        if args.title is not None:
            params["title"] = args.title
        if args.content is not None:
            params["content"] = args.content
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("chapters.card.update", params)
    if args.command == "chapter-card-move":
        params = {
            "course": args.course,
            "chapter": args.chapter,
            "card": args.card,
            "target_position": args.target_position,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("chapters.card.move", params)
    if args.command == "chapter-card-delete":
        params = {"course": args.course, "chapter": args.chapter, "card": args.card}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "chapters.card.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "chapter-create":
        params = {
            "course": args.course,
            "title": args.title,
            "parent": args.parent,
            "before": args.before,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("chapters.create", params)
    if args.command == "chapter-rename":
        params = {"course": args.course, "chapter": args.chapter, "title": args.title}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("chapters.rename", params)
    if args.command == "chapter-move":
        params = {
            "course": args.course,
            "chapter": args.chapter,
            "parent": args.parent,
            "relative_to": args.relative_to,
            "position": args.position,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("chapters.move", params)
    if args.command == "chapter-import-outline":
        params = {"course": args.course, "outline": args.outline}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("chapters.outline.import", params)
    if args.command == "chapter-status":
        params = {
            "course": args.course,
            "status": args.status,
            "chapters": args.chapters,
            "classes": args.classes,
            "begin": args.begin,
            "end": args.end,
            "time_end_review": args.time_end_review,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "chapters.open_status.update",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "chapter-delete":
        params = {"course": args.course, "chapters": args.chapters}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "chapters.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "resources":
        params = {
            "course": args.course,
            "folder": args.folder,
            "search": args.search,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("resources.list", params)
    if args.command == "resource-tree":
        params = {"course": args.course, "search": args.search}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("resources.tree.list", params)
    if args.command == "resource-download":
        params = {
            "course": args.course,
            "resource": args.resource,
            "output_path": args.output_path,
            "overwrite": args.overwrite,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("resources.file.download", params)
    if args.command == "resource-download-items":
        params = {
            "course": args.course,
            "resources": args.resources,
            "output_path": args.output_path,
            "overwrite": args.overwrite,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("resources.items.download", params)
    if args.command == "resource-folder-create":
        params = {"course": args.course, "name": args.name, "parent": args.parent}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "resources.folder.create",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "resource-rename":
        params = {"course": args.course, "resource": args.resource, "name": args.name}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("resources.rename", params)
    if args.command == "resource-move":
        params = {
            "course": args.course,
            "destination": args.destination,
            "resources": args.resources,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("resources.move", params)
    if args.command == "resource-reorder":
        params = {
            "course": args.course,
            "resources": args.resources,
            "folder": args.folder,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("resources.reorder", params)
    if args.command == "resource-top":
        params = {
            "course": args.course,
            "resource": args.resource,
            "top": args.status == "top",
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("resources.top_status.update", params)
    if args.command == "resource-copy":
        params = {"course": args.course, "resource": args.resource}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "resources.copy",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "resource-copy-to-cloud":
        params = {
            "course": args.course,
            "resource": args.resource,
            "destination": args.destination,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "resources.cloud_disk.copy",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "resource-cloud-sources":
        params = {
            "course": args.course,
            "path": args.path,
            "search": args.search,
            "page": args.page,
            "page_size": args.page_size,
            "share_id": args.share_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("resources.cloud_sources.list", params)
    if args.command == "resource-cloud-import":
        params = {
            "course": args.course,
            "resources": args.resources,
            "source_path": args.source_path,
            "destination": args.destination,
            "share_id": args.share_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "resources.cloud_files.import",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "resource-cloud-folder-import":
        params = {
            "course": args.course,
            "resource": args.resource,
            "source_path": args.source_path,
            "destination": args.destination,
            "share_id": args.share_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "resources.cloud_folder.import",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "resource-labels":
        params = {
            "course": args.course,
            "resource": args.resource,
            "search": args.search,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("resources.labels.list", params)
    if args.command == "resource-label-create":
        params = {
            "course": args.course,
            "resource": args.resource,
            "name": args.name,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("resources.label.create", params)
    if args.command == "resource-label-rename":
        params = {
            "course": args.course,
            "resource": args.resource,
            "label": args.label,
            "name": args.name,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("resources.label.rename", params)
    if args.command == "resource-label-delete":
        params = {
            "course": args.course,
            "resource": args.resource,
            "label": args.label,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "resources.label.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "resource-labels-update":
        params = {
            "course": args.course,
            "resources": args.resources,
            "labels": args.labels,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "resources.labels.update",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "resource-delete":
        params = {"course": args.course, "resources": args.resources}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "resources.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "resource-link-create":
        params = {
            "course": args.course,
            "name": args.name,
            "url": args.url,
            "parent": args.parent,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "resources.link.create",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "resource-upload":
        params = {
            "course": args.course,
            "file_path": args.file_path,
            "parent": args.parent,
            "name": args.name,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "resources.file.upload",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "resource-download-permission":
        params = {
            "course": args.course,
            "resources": args.resources,
            "allow_download": args.permission == "allow",
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "resources.download_permission.update",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "resource-visibility":
        params = {"course": args.course, "folder": args.folder}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("resources.folder.visibility.read", params)
    if args.command == "resource-visibility-update":
        params = {
            "course": args.course,
            "folder": args.folder,
            "mode": args.mode,
        }
        if args.classes is not None:
            params["classes"] = args.classes
        if args.teacher_ids is not None:
            params["teacher_ids"] = args.teacher_ids
        if args.all_teachers is not None:
            params["all_teachers"] = args.all_teachers
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "resources.folder.visibility.update",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "resource-readers":
        params = {"course": args.course, "resource": args.resource}
        if args.reader_class:
            params["reader_class"] = args.reader_class
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("resources.readers.list", params)
    if args.command == "resource-downloaders":
        params = {"course": args.course, "resource": args.resource}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("resources.downloaders.list", params)
    if args.command == "resource-import-courses":
        params = {"course": args.course, "search": args.search}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("resources.import_courses.list", params)
    if args.command == "resource-import-items":
        params = {
            "course": args.course,
            "source_course": args.source_course,
            "folder_id": args.folder_id,
            "search": args.search,
            "page": args.page,
            "page_size": args.page_size,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("resources.import_items.list", params)
    if args.command == "resource-import":
        params = {
            "course": args.course,
            "source_course": args.source_course,
            "resources": args.resources,
            "source_folder_id": args.source_folder_id,
            "destination": args.destination,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "resources.import.execute",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "resource-share-link":
        params = {"course": args.course, "resource": args.resource}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "resources.share_link.create",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "cloud-list":
        return await runtime.execute(
            "cloud_disk.items.list",
            {
                "parent": args.parent,
                "search": args.search,
                "page": args.page,
                "page_size": args.page_size,
            },
        )
    if args.command == "cloud-read":
        return await runtime.execute(
            "cloud_disk.item.read",
            {"resource": args.resource},
        )
    if args.command == "cloud-delete":
        return await runtime.execute(
            "cloud_disk.items.delete",
            {"resources": args.resources},
            confirmation_token=args.confirmation_token,
        )
    if args.command == "cloud-folder-create":
        return await runtime.execute(
            "cloud_disk.folder.create",
            {"name": args.name, "parent": args.parent, "shared": args.shared},
            confirmation_token=args.confirmation_token,
        )
    if args.command == "cloud-rename":
        return await runtime.execute(
            "cloud_disk.item.rename",
            {"resource": args.resource, "name": args.name},
        )
    if args.command == "cloud-move":
        return await runtime.execute(
            "cloud_disk.items.move",
            {"destination": args.destination, "resources": args.resources},
        )
    if args.command == "cloud-top":
        return await runtime.execute(
            "cloud_disk.item.top_status.update",
            {"resource": args.resource, "top": args.status == "top"},
        )
    if args.command == "cloud-download":
        return await runtime.execute(
            "cloud_disk.items.download",
            {
                "resources": args.resources,
                "output_path": args.output_path,
                "overwrite": args.overwrite,
            },
        )
    if args.command == "cloud-recycle":
        return await runtime.execute(
            "cloud_disk.recycle.list",
            {"page": args.page, "page_size": args.page_size},
        )
    if args.command == "cloud-restore":
        return await runtime.execute(
            "cloud_disk.recycle.restore",
            {
                "resources": args.resources,
                "conflict_policy": args.conflict_policy,
            },
            confirmation_token=args.confirmation_token,
        )
    if args.command == "cloud-recycle-delete":
        return await runtime.execute(
            "cloud_disk.recycle.items.delete",
            {"resources": args.resources},
            confirmation_token=args.confirmation_token,
        )
    if args.command == "cloud-recycle-empty":
        return await runtime.execute(
            "cloud_disk.recycle.empty",
            {},
            confirmation_token=args.confirmation_token,
        )
    if args.command == "homework-library":
        params = {
            "course": args.course,
            "directory": args.directory,
            "search": args.search,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("homework.library.list", params)
    if args.command == "homework-read":
        params = {
            "course": args.course,
            "homework": args.homework,
            "question": args.question,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("homework.library.item.read", params)
    if args.command == "homework-question-add":
        params = {
            "course": args.course,
            "homework": args.homework,
            "question_type": args.question_type,
            "stem": args.stem,
            "score": args.score,
            "options": args.options,
            "correct_answer": args.correct_answer,
            "answer": args.answer,
            "analysis": args.analysis,
            "difficulty": args.difficulty,
            "content_format": args.content_format,
        }
        if args.answers:
            params["answers"] = args.answers
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("homework.question.add", params)
    if args.command == "homework-question-update":
        params = {
            "course": args.course,
            "homework": args.homework,
            "question": args.question,
            "content_format": args.content_format,
        }
        optional = {
            "stem": args.stem,
            "score": args.score,
            "options": args.options,
            "correct_answer": args.correct_answer,
            "answers": args.answers,
            "answer": args.answer,
            "analysis": args.analysis,
            "difficulty": args.difficulty,
        }
        params.update({key: value for key, value in optional.items() if value is not None})
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("homework.question.update", params)
    if args.command == "homework-question-delete":
        params = {
            "course": args.course,
            "homework": args.homework,
            "question": args.question,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "homework.question.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "homework-drafts":
        params = {"course": args.course, "search": args.search}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("homework.drafts.list", params)
    if args.command == "homework-draft-create":
        params = {
            "course": args.course,
            "title": args.title,
            "directory": args.directory,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("homework.draft.create", params)
    if args.command == "homework-draft-update":
        params = {"course": args.course, "draft": args.draft, "title": args.title}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("homework.draft.update", params)
    if args.command == "homework-draft-delete":
        params = {"course": args.course, "draft": args.draft}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "homework.draft.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "homework-publish":
        params = {
            "course": args.course,
            "homework": args.homework,
            "start_time": args.start_time,
            "end_time": args.end_time,
            "allow_late_submission": args.allow_late_submission,
            "late_deadline": args.late_deadline,
            "passing_score": args.passing_score,
            "redo_times": args.redo_times,
            "allow_paste": args.allow_paste,
            "show_score": args.show_score,
            "show_correctness": args.show_correctness,
            "randomize_questions": args.randomize_questions,
            "randomize_options": args.randomize_options,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        if args.target_classes:
            params["target_classes"] = args.target_classes
        return await runtime.execute(
            "homework.library.publish",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "homeworks":
        params = {"course": args.course}
        if args.clazz:
            params["clazz"] = args.clazz
        action = "homework.list_ungraded" if args.ungraded else "homework.list"
        return await runtime.execute(action, params)
    if args.command == "submissions":
        params = {
            "course": args.course,
            "homework": args.homework,
            "status": args.status,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("homework.submissions.list", params)
    if args.command == "review":
        params = {
            "course": args.course,
            "homework": args.homework,
            "submission": args.submission,
            "max_chars": args.max_chars,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("homework.submission.read", params)
    if args.command == "score":
        params = {
            "course": args.course,
            "homework": args.homework,
            "submission": args.submission,
            "score": args.score,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "homework.score.set", params, confirmation_token=args.confirmation_token
        )
    if args.command == "notices":
        params = {"course": args.course, "search": args.search}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("notices.list", params)
    if args.command == "notice-drafts":
        return await runtime.execute(
            "notices.drafts.list",
            {
                "course": args.course,
                "search": args.search,
                "page_size": args.page_size,
            },
        )
    if args.command in {"notice-draft-save", "notice-schedule"}:
        params = {
            "course": args.course,
            "title": args.title,
            "content": args.content,
            "allow_comments": not args.disable_comments,
            "show_comments": args.show_comments,
            "hide_read_status": args.hide_read_status,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        if args.recipient_classes is not None:
            params["recipient_classes"] = args.recipient_classes
        if args.draft:
            params["draft"] = args.draft
        if args.command == "notice-draft-save":
            params["clear_schedule"] = args.clear_schedule
            return await runtime.execute("notices.draft.save", params)
        params["send_at"] = args.send_at
        return await runtime.execute(
            "notices.schedule",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "notice-draft-delete":
        return await runtime.execute(
            "notices.draft.delete",
            {"course": args.course, "draft": args.draft},
            confirmation_token=args.confirmation_token,
        )
    if args.command == "notice-send":
        params = {
            "course": args.course,
            "title": args.title,
            "content": args.content,
            "allow_comments": not args.disable_comments,
            "show_comments": args.show_comments,
            "hide_read_status": args.hide_read_status,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        if args.recipient_classes is not None:
            params["recipient_classes"] = args.recipient_classes
        return await runtime.execute(
            "notices.send",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "notice-edit":
        params = {
            "course": args.course,
            "notice": args.notice,
            "title": args.title,
            "content": args.content,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "notices.edit",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "notice-top":
        params = {"course": args.course, "notice": args.notice, "top": not args.off}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "notices.top.set",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command in {"notice-recall", "notice-delete"}:
        params = {"course": args.course, "notice": args.notice}
        if args.clazz:
            params["clazz"] = args.clazz
        action = "notices.recall" if args.command == "notice-recall" else "notices.delete"
        return await runtime.execute(
            action,
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "exams":
        params = {"course": args.course, "status": args.status, "search": args.search}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("exams.list", params)
    if args.command == "exam-papers":
        params = {
            "course": args.course,
            "directory_id": args.directory_id,
            "search": args.search,
            "page_size": args.page_size,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("exam.paper_library.list", params)
    if args.command == "exam-paper":
        params = {
            "course": args.course,
            "paper": args.paper,
            "directory_id": args.directory_id,
            "question": args.question,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("exam.paper.read", params)
    if args.command == "exam-paper-settings":
        params = {
            "course": args.course,
            "paper": args.paper,
            "directory_id": args.directory_id,
            "group_id": args.group_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("exam.paper.settings.read", params)
    if args.command == "exam-paper-settings-update":
        params = {
            "course": args.course,
            "paper": args.paper,
            "directory_id": args.directory_id,
            "group_id": args.group_id,
        }
        optional = {
            "difficulty": args.difficulty,
            "numbering": args.numbering,
            "grouping": args.grouping,
            "subquestion_numbering": args.subquestion_numbering,
        }
        params.update({key: value for key, value in optional.items() if value is not None})
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("exam.paper.settings.update", params)
    if args.command == "exam-question-add":
        params = {
            "course": args.course,
            "paper": args.paper,
            "question_type": args.question_type,
            "stem": args.stem,
            "score": args.score,
            "analysis": args.analysis,
            "difficulty": args.difficulty,
            "content_format": args.content_format,
            "directory_id": args.directory_id,
            "group_id": args.group_id,
        }
        optional = {
            "options": args.options,
            "correct_answer": args.correct_answer,
            "answers": args.answers,
            "answer": args.answer,
        }
        params.update({key: value for key, value in optional.items() if value is not None})
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("exam.question.add", params)
    if args.command == "exam-question-update":
        params = {
            "course": args.course,
            "paper": args.paper,
            "question": args.question,
            "content_format": args.content_format,
            "directory_id": args.directory_id,
            "group_id": args.group_id,
        }
        optional = {
            "stem": args.stem,
            "score": args.score,
            "options": args.options,
            "correct_answer": args.correct_answer,
            "answers": args.answers,
            "answer": args.answer,
            "analysis": args.analysis,
            "difficulty": args.difficulty,
        }
        params.update({key: value for key, value in optional.items() if value is not None})
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("exam.question.update", params)
    if args.command == "exam-question-delete":
        params = {
            "course": args.course,
            "paper": args.paper,
            "question": args.question,
            "directory_id": args.directory_id,
            "group_id": args.group_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "exam.question.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "exam-question-move":
        params = {
            "course": args.course,
            "paper": args.paper,
            "question": args.question,
            "target_position": args.target_position,
            "directory_id": args.directory_id,
            "group_id": args.group_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("exam.question.move", params)
    if args.command == "exam-question-type-update":
        params = {
            "course": args.course,
            "paper": args.paper,
            "question_type": args.question_type,
            "directory_id": args.directory_id,
            "group_id": args.group_id,
        }
        optional = {
            "description": args.description,
            "total_score": args.total_score,
        }
        params.update({key: value for key, value in optional.items() if value is not None})
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("exam.question_type.update", params)
    if args.command == "exam-question-type-move":
        params = {
            "course": args.course,
            "paper": args.paper,
            "question_type": args.question_type,
            "target_position": args.target_position,
            "directory_id": args.directory_id,
            "group_id": args.group_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("exam.question_type.move", params)
    if args.command == "exam-question-type-delete":
        params = {
            "course": args.course,
            "paper": args.paper,
            "question_type": args.question_type,
            "directory_id": args.directory_id,
            "group_id": args.group_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "exam.question_type.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "exam-paper-create":
        params = {
            "course": args.course,
            "title": args.title,
            "directory_id": args.directory_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("exam.paper.create", params)
    if args.command == "exam-paper-rename":
        params = {
            "course": args.course,
            "paper": args.paper,
            "title": args.title,
            "directory_id": args.directory_id,
            "sync_parallel_titles": args.sync_parallel_titles,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("exam.paper.rename", params)
    if args.command == "exam-paper-copy":
        params = {
            "course": args.course,
            "paper": args.paper,
            "directory_id": args.directory_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("exam.paper.copy", params)
    if args.command == "exam-paper-move":
        params = {
            "course": args.course,
            "paper": args.paper,
            "source_directory_id": args.source_directory_id,
            "target_directory_id": args.target_directory_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("exam.paper.move", params)
    if args.command == "exam-paper-delete":
        params = {
            "course": args.course,
            "paper": args.paper,
            "directory_id": args.directory_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "exam.paper.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "exam-folder-create":
        params = {
            "course": args.course,
            "title": args.title,
            "parent_directory_id": args.parent_directory_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("exam.paper_folder.create", params)
    if args.command == "exam-folder-rename":
        params = {
            "course": args.course,
            "folder": args.folder,
            "title": args.title,
            "parent_directory_id": args.parent_directory_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("exam.paper_folder.rename", params)
    if args.command == "exam-folder-move":
        params = {
            "course": args.course,
            "folder": args.folder,
            "source_directory_id": args.source_directory_id,
            "target_directory_id": args.target_directory_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("exam.paper_folder.move", params)
    if args.command == "exam-folder-delete":
        params = {
            "course": args.course,
            "folder": args.folder,
            "parent_directory_id": args.parent_directory_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "exam.paper_folder.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "exam-submissions":
        params = {
            "course": args.course,
            "exam": args.exam,
            "state": args.state,
            "status": args.status,
            "search": args.search,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("exams.submissions.list", params)
    if args.command == "exam-answer":
        params = {
            "course": args.course,
            "exam": args.exam,
            "submission": args.submission,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("exams.submission.read", params)
    if args.command == "qbank":
        params = {
            "course": args.course,
            "page": args.page,
            "page_size": args.page_size,
            "search": args.search,
            "directory_id": args.directory_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.list", params)
    if args.command in {"qbank-smart-preview", "qbank-smart-import"}:
        params = {
            "course": args.course,
            "source_text": args.source_text,
            "file_path": args.file_path,
            "content_format": args.content_format,
            "parse_latex_code": args.parse_latex_code,
            "parse_latex_formula": args.parse_latex_formula,
        }
        params = {key: value for key, value in params.items() if value is not None}
        if args.clazz:
            params["clazz"] = args.clazz
        if args.command == "qbank-smart-import":
            params["target_directory"] = args.target_directory
            params["allow_parser_warnings"] = args.allow_parser_warnings
            if args.questions_json:
                try:
                    document = json.loads(
                        Path(args.questions_json).expanduser().read_text(encoding="utf-8")
                    )
                except (OSError, json.JSONDecodeError) as exc:
                    raise ActionRuntimeError(f"cannot read questions JSON: {exc}") from exc
                questions = document.get("questions") if isinstance(document, dict) else document
                if not isinstance(questions, list):
                    raise ActionRuntimeError(
                        "questions JSON must be an array or an object with a questions array"
                    )
                params["questions"] = questions
            return await runtime.execute("question_bank.smart_import.commit", params)
        return await runtime.execute("question_bank.smart_import.preview", params)
    if args.command == "qbank-source-courses":
        params = {"course": args.course}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.source_courses.list", params)
    if args.command == "qbank-source-questions":
        params = {
            "course": args.course,
            "source_course": args.source_course,
            "page": args.page,
            "page_size": args.page_size,
            "search": args.search,
            "directory_id": args.directory_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.source_questions.list", params)
    if args.command == "qbank-import-from-course":
        params = {
            "course": args.course,
            "source_course": args.source_course,
            "questions": args.questions,
            "source_directory_id": args.source_directory_id,
            "target_directory": args.target_directory,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.questions.import_from_course", params)
    if args.command == "qbank-export":
        params = {
            "course": args.course,
            "export_type": args.export_type,
            "questions": args.questions,
            "directories": args.directories,
            "export_all": args.export_all,
            "source_directory_id": args.source_directory_id,
            "output_path": args.output_path,
            "include_answers": args.include_answers,
            "include_analysis": args.include_analysis,
            "include_difficulty": args.include_difficulty,
            "include_type_names": args.include_type_names,
            "include_topics": args.include_topics,
            "include_targets": args.include_targets,
            "include_correct_rate": args.include_correct_rate,
            "include_use_count": args.include_use_count,
            "excel_plain_text": args.excel_plain_text,
            "overwrite": args.overwrite,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.export.create", params)
    if args.command == "qbank-downloads":
        params = {"course": args.course, "page": args.page, "order": args.order}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.downloads.list", params)
    if args.command == "qbank-download":
        params = {
            "course": args.course,
            "record": args.record,
            "output_path": args.output_path,
            "password": args.password,
            "overwrite": args.overwrite,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.downloads.get", params)
    if args.command == "qbank-download-rename":
        params = {"course": args.course, "record": args.record, "name": args.name}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.downloads.rename", params)
    if args.command == "qbank-download-delete":
        params = {"course": args.course, "record": args.record}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "question_bank.downloads.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "qbank-question":
        params = {
            "course": args.course,
            "question": args.question,
            "directory_id": args.directory_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.question.read", params)
    if args.command == "qbank-directories":
        params = {"course": args.course}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.directories.list", params)
    if args.command == "qbank-folder-permissions":
        params = {"course": args.course, "directory": args.directory}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.directory.permissions.read", params)
    if args.command == "qbank-folder-permissions-update":
        params = {"course": args.course, "directory": args.directory}
        for name in (
            "allow_student_self_practice",
            "share_scope",
            "selected_teachers",
        ):
            value = getattr(args, name)
            if value is not None:
                params[name] = value
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "question_bank.directory.permissions.update",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "qbank-question-types":
        params = {"course": args.course}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.question_types.list", params)
    if args.command == "qbank-question-type-add":
        params = {
            "course": args.course,
            "name": args.name,
            "base_type": args.base_type,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.question_type.add", params)
    if args.command == "qbank-question-type-rename":
        params = {
            "course": args.course,
            "question_type": args.question_type,
            "name": args.name,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.question_type.rename", params)
    if args.command == "qbank-question-type-move":
        params = {
            "course": args.course,
            "question_type": args.question_type,
            "target_position": args.target_position,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.question_type.move", params)
    if args.command == "qbank-question-type-delete":
        params = {"course": args.course, "question_type": args.question_type}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "question_bank.question_type.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "qbank-labels":
        params = {
            "course": args.course,
            "question": args.question,
            "directory_id": args.directory_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.labels.list", params)
    if args.command == "qbank-label-create":
        params = {
            "course": args.course,
            "name": args.name,
            "parent_label": args.parent_label,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.label.create", params)
    if args.command == "qbank-label-rename":
        params = {"course": args.course, "label": args.label, "name": args.name}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.label.rename", params)
    if args.command == "qbank-label-delete":
        params = {"course": args.course, "label": args.label}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "question_bank.label.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "qbank-question-labels-set":
        params = {
            "course": args.course,
            "questions": args.questions,
            "labels": args.labels,
            "mode": args.mode,
            "directory_id": args.directory_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        action = (
            "question_bank.question.labels.sync"
            if args.sync_references
            else "question_bank.question.labels.set"
        )
        return await runtime.execute(
            action,
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "qbank-topics":
        params = {
            "course": args.course,
            "question": args.question,
            "directory_id": args.directory_id,
            "search": args.search,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.topics.list", params)
    if args.command == "qbank-topic-create":
        params = {
            "course": args.course,
            "name": args.name,
            "kind": args.kind,
            "after_topic": args.after_topic,
        }
        if args.parent_topic is not None:
            params["parent_topic"] = args.parent_topic
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.topic.create", params)
    if args.command == "qbank-topic-rename":
        params = {"course": args.course, "topic": args.topic, "name": args.name}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.topic.rename", params)
    if args.command == "qbank-topic-delete":
        params = {"course": args.course, "topic": args.topic}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "question_bank.topic.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "qbank-question-topics-set":
        params = {
            "course": args.course,
            "questions": args.questions,
            "topics": args.topics,
            "mode": args.mode,
            "directory_id": args.directory_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        action = (
            "question_bank.question.topics.sync"
            if args.sync_references
            else "question_bank.question.topics.set"
        )
        return await runtime.execute(
            action,
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command in {"qbank-recycle", "qbank-locked"}:
        params = {
            "course": args.course,
            "page": args.page,
            "page_size": args.page_size,
            "search": args.search,
            "directory_id": args.directory_id,
            "directory_path_ids": args.directory_path_ids,
            "order": args.order,
        }
        if args.command == "qbank-locked":
            params["lock_time_filters"] = args.lock_time_filters
        if args.clazz:
            params["clazz"] = args.clazz
        action = (
            "question_bank.recycle.list"
            if args.command == "qbank-recycle"
            else "question_bank.locked.list"
        )
        return await runtime.execute(action, params)
    if args.command == "qbank-lock":
        params = {
            "course": args.course,
            "questions": args.questions,
            "directories": args.directories,
            "directory_id": args.directory_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "question_bank.items.lock",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command in {"qbank-unlock", "qbank-recycle-restore", "qbank-recycle-delete"}:
        params = {
            "course": args.course,
            "items": args.items,
            "directory_id": args.directory_id,
            "directory_path_ids": args.directory_path_ids,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        action = {
            "qbank-unlock": "question_bank.items.unlock",
            "qbank-recycle-restore": "question_bank.recycle.restore",
            "qbank-recycle-delete": "question_bank.recycle.delete",
        }[args.command]
        return await runtime.execute(
            action,
            params,
            confirmation_token=(
                args.confirmation_token
                if args.command in {"qbank-unlock", "qbank-recycle-delete"}
                else None
            ),
        )
    if args.command == "qbank-recycle-empty":
        params = {"course": args.course}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "question_bank.recycle.empty",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "qbank-questions-difficulty":
        try:
            difficulty: str | float = float(args.difficulty)
        except ValueError:
            difficulty = args.difficulty
        params = {
            "course": args.course,
            "difficulty": difficulty,
            "questions": args.questions,
            "directory_id": args.directory_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.questions.difficulty.update", params)
    if args.command == "qbank-questions-type":
        params = {
            "course": args.course,
            "question_type": args.question_type,
            "questions": args.questions,
            "directory_id": args.directory_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.questions.type.update", params)
    if args.command == "qbank-copy":
        params = {
            "course": args.course,
            "questions": args.questions,
            "directories": args.directories,
            "source_directory_id": args.source_directory_id,
            "target_directory": args.target_directory,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.items.copy", params)
    if args.command == "qbank-folder-create":
        params = {
            "course": args.course,
            "name": args.name,
            "parent_directory": args.parent_directory,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.directory.create", params)
    if args.command == "qbank-folder-rename":
        params = {"course": args.course, "directory": args.directory, "name": args.name}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.directory.rename", params)
    if args.command == "qbank-folder-move":
        params = {
            "course": args.course,
            "directory": args.directory,
            "target_directory": args.target_directory,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.directory.move", params)
    if args.command == "qbank-folder-reorder":
        params = {
            "course": args.course,
            "directory": args.directory,
            "target_position": args.target_position,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.directory.reorder", params)
    if args.command == "qbank-folder-top":
        params = {"course": args.course, "directory": args.directory, "top": not args.clear}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.directory.top.set", params)
    if args.command == "qbank-folder-delete":
        params = {"course": args.course, "directory": args.directory}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "question_bank.directory.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "qbank-question-add":
        params = {
            "course": args.course,
            "question_type": args.question_type,
            "stem": args.stem,
            "directory": args.directory,
            "analysis": args.analysis,
            "difficulty": args.difficulty,
            "content_format": args.content_format,
        }
        optional = {
            "options": args.options,
            "correct_answer": args.correct_answer,
            "answers": args.answers,
            "answer": args.answer,
        }
        params.update({key: value for key, value in optional.items() if value is not None})
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.question.add", params)
    if args.command == "qbank-question-update":
        params = {
            "course": args.course,
            "question": args.question,
            "directory_id": args.directory_id,
            "content_format": args.content_format,
        }
        optional = {
            "stem": args.stem,
            "options": args.options,
            "correct_answer": args.correct_answer,
            "answers": args.answers,
            "answer": args.answer,
            "analysis": args.analysis,
            "difficulty": args.difficulty,
        }
        params.update({key: value for key, value in optional.items() if value is not None})
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.question.update", params)
    if args.command == "qbank-question-move":
        params = {
            "course": args.course,
            "question": args.question,
            "target_directory": args.target_directory,
            "source_directory_id": args.source_directory_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.question.move", params)
    if args.command == "qbank-question-reorder":
        params = {
            "course": args.course,
            "question": args.question,
            "target_position": args.target_position,
            "directory_id": args.directory_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.question.reorder", params)
    if args.command == "qbank-question-difficulty":
        params = {
            "course": args.course,
            "question": args.question,
            "difficulty": args.difficulty,
            "directory_id": args.directory_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("question_bank.question.difficulty.update", params)
    if args.command == "qbank-question-delete":
        params = {
            "course": args.course,
            "question": args.question,
            "directory_id": args.directory_id,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute(
            "question_bank.question.delete",
            params,
            confirmation_token=args.confirmation_token,
        )
    if args.command == "discussions":
        params = {
            "course": args.course,
            "search": args.search,
            "class_only": args.class_only,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("discussions.list", params)
    if args.command == "discussion-topic":
        params = {
            "course": args.course,
            "topic": args.topic,
            "class_only": args.class_only,
            "order": args.order,
            "reply_search": args.reply_search,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("discussions.topic.read", params)
    if args.command == "discussion-create":
        params = {
            "course": args.course,
            "title": args.title,
            "content": args.content,
            "class_only": args.class_only,
            "anonymous": args.anonymous,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("discussions.topic.create", params, args.confirmation_token)
    if args.command == "discussion-edit":
        params = {"course": args.course, "topic": args.topic}
        if args.clazz:
            params["clazz"] = args.clazz
        if args.title is not None:
            params["title"] = args.title
        if args.content is not None:
            params["content"] = args.content
        return await runtime.execute("discussions.topic.edit", params, args.confirmation_token)
    if args.command == "discussion-top":
        params = {"course": args.course, "topic": args.topic, "top": not args.off}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("discussions.topic.top.set", params, args.confirmation_token)
    if args.command == "discussion-delete":
        params = {"course": args.course, "topic": args.topic}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("discussions.topic.delete", params, args.confirmation_token)
    if args.command == "discussion-reply":
        params = {
            "course": args.course,
            "topic": args.topic,
            "content": args.content,
            "reply_to": args.reply_to,
            "anonymous": args.anonymous,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("discussions.reply.create", params, args.confirmation_token)
    if args.command == "discussion-reply-edit":
        params = {
            "course": args.course,
            "topic": args.topic,
            "reply": args.reply,
            "content": args.content,
        }
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("discussions.reply.edit", params, args.confirmation_token)
    if args.command == "discussion-reply-delete":
        params = {"course": args.course, "topic": args.topic, "reply": args.reply}
        if args.clazz:
            params["clazz"] = args.clazz
        return await runtime.execute("discussions.reply.delete", params, args.confirmation_token)
    if args.command == "plan":
        from .router import route_command

        return route_command(" ".join(args.text)).to_dict()
    if args.command == "run":
        return await runtime.execute_command(" ".join(args.text), args.confirmation_token)
    raise ActionRuntimeError(f"unsupported command: {args.command}")


def main() -> None:
    _configure_output()
    parser = build_parser()
    args = parser.parse_args()
    settings = Settings.from_env()
    if args.command == "doctor":
        _emit(_doctor(settings, args.live))
        return
    try:
        _emit(asyncio.run(_run_action(args, ActionRuntime(settings))))
    except (ActionRuntimeError, ValueError, OSError) as exc:
        _emit({"status": "error", "error": str(exc)})
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
