from __future__ import annotations

from typing import Any

from mcp.server import MCPServer

from . import __version__
from .runtime import ActionRuntime

mcp = MCPServer(
    "Chaoxing Agent",
    version=__version__,
    instructions=(
        "Use these tools to carry out the user's natural-language requests in Chaoxing. "
        "Start with chaoxing_capabilities when coverage is unclear. Prefer semantic tools "
        "over guessed URLs. The runtime uses authenticated HTTP only and never launches a "
        "browser or requires the Chaoxing client. Reads execute directly. If a tool "
        "returns confirmation_required, show its exact impact and call the same tool again "
        "with the returned one-time confirmation token only after the user confirms."
    ),
)
runtime = ActionRuntime()


@mcp.tool()
async def chaoxing_capabilities() -> dict[str, Any]:
    """List observed, implemented, and live-verified Chaoxing capabilities."""
    return await runtime.execute("capabilities.list")


@mcp.tool()
async def chaoxing_check_session() -> dict[str, Any]:
    """Check whether the configured Chaoxing session is logged in and identify the account."""
    return await runtime.execute("session.check")


@mcp.tool()
async def chaoxing_login(
    username: str,
    password: str,
    fid: str = "-1",
    target_url: str = "",
    learning_course: str = "",
    learning_module: str = "直播课/见面课",
) -> dict[str, Any]:
    """Log in through HTTP using an optional URL or signed learner-course module target."""
    parameters = {"username": username, "password": password, "fid": fid}
    if target_url:
        parameters["target_url"] = target_url
    if learning_course:
        parameters["learning_course"] = learning_course
        parameters["learning_module"] = learning_module
    return await runtime.execute(
        "session.login",
        parameters,
    )


@mcp.tool()
async def chaoxing_list_personal_space_modules() -> dict[str, Any]:
    """List current personal-space function entries and HTTP availability."""
    return await runtime.execute("space.modules.discover")


@mcp.tool()
async def chaoxing_open_personal_space_module(module: str) -> dict[str, Any]:
    """Fetch one personal-space module through authenticated HTTP without a browser."""
    return await runtime.execute("space.module.open", {"module": module})


@mcp.tool()
async def chaoxing_read_job_ability_status() -> dict[str, Any]:
    """Read public and account-specific job-ability availability without returning identity IDs."""
    return await runtime.execute("job_ability.status.read")


@mcp.tool()
async def chaoxing_search_job_ability_jobs(
    keyword: str,
    page: int = 1,
    page_size: int = 20,
    education_level: str = "",
) -> dict[str, Any]:
    """Search current recruitment ads by keyword, page, and education level."""
    return await runtime.execute(
        "job_ability.jobs.search",
        {
            "keyword": keyword,
            "page": page,
            "page_size": page_size,
            "education_level": education_level,
        },
    )


@mcp.tool()
async def chaoxing_read_job_ability_job_ad(
    job: str,
    search: str = "",
    education_level: str = "",
) -> dict[str, Any]:
    """Resolve one current recruitment ad by ID or unique job/company label."""
    return await runtime.execute(
        "job_ability.job_ad.read",
        {"job": job, "search": search, "education_level": education_level},
    )


@mcp.tool()
async def chaoxing_list_popular_job_ability_jobs(
    education_level: str = "本科",
) -> dict[str, Any]:
    """List current popular and high-salary jobs for an education level."""
    return await runtime.execute(
        "job_ability.popular_jobs.list",
        {"education_level": education_level},
    )


@mcp.tool()
async def chaoxing_read_occupation_catalog(
    education_level: str = "本科",
) -> dict[str, Any]:
    """Read the current occupation encyclopedia summary and popular/emerging occupations."""
    return await runtime.execute(
        "job_ability.occupation_catalog.read",
        {"education_level": education_level},
    )


@mcp.tool()
async def chaoxing_search_occupations(
    keyword: str,
    education_level: str = "本科",
) -> dict[str, Any]:
    """Search occupation encyclopedia entries by keyword and education level."""
    return await runtime.execute(
        "job_ability.occupations.search",
        {"keyword": keyword, "education_level": education_level},
    )


@mcp.tool()
async def chaoxing_list_job_ability_industry_types(
    page: int = 1,
    page_size: int = 100,
) -> dict[str, Any]:
    """List current public job-ability industry types."""
    return await runtime.execute(
        "job_ability.industry_types.list",
        {"page": page, "page_size": page_size},
    )


@mcp.tool()
async def chaoxing_list_job_ability_industries(
    industry_type: str,
    education_level: str = "本科",
    page: int = 1,
    page_size: int = 100,
) -> dict[str, Any]:
    """List platform job categories beneath one public industry type."""
    return await runtime.execute(
        "job_ability.industries.list",
        {
            "industry_type": industry_type,
            "education_level": education_level,
            "page": page,
            "page_size": page_size,
        },
    )


@mcp.tool()
async def chaoxing_list_job_ability_industry_jobs(
    industry: str,
    education_level: str = "本科",
    page: int = 1,
    page_size: int = 100,
) -> dict[str, Any]:
    """List standard job-library entries for one platform job category."""
    return await runtime.execute(
        "job_ability.industry_jobs.list",
        {
            "industry": industry,
            "education_level": education_level,
            "page": page,
            "page_size": page_size,
        },
    )


@mcp.tool()
async def chaoxing_list_subjects(
    folder: str = "-1", search: str = "", max_items: int = 1000
) -> dict[str, Any]:
    """List subjects and child folders in the root or one subject folder."""
    return await runtime.execute(
        "subjects.items.list",
        {"folder": folder, "search": search, "max_items": max_items},
    )


@mcp.tool()
async def chaoxing_list_subject_tree(max_folders: int = 1000) -> dict[str, Any]:
    """Read the complete current account subject-creation tree."""
    return await runtime.execute("subjects.tree.list", {"max_folders": max_folders})


@mcp.tool()
async def chaoxing_subject_creation_status() -> dict[str, Any]:
    """Check subject-creation availability and real-name certification status."""
    return await runtime.execute("subjects.creation.status")


@mcp.tool()
async def chaoxing_create_subject_folder(name: str, parent_folder: str = "-1") -> dict[str, Any]:
    """Create and verify an empty subject folder."""
    return await runtime.execute(
        "subjects.folder.create", {"name": name, "parent_folder": parent_folder}
    )


@mcp.tool()
async def chaoxing_rename_subject_folder(folder: str, name: str) -> dict[str, Any]:
    """Rename and verify a subject folder."""
    return await runtime.execute("subjects.folder.rename", {"folder": folder, "name": name})


@mcp.tool()
async def chaoxing_move_subject_folder(folder: str, target_folder: str = "-1") -> dict[str, Any]:
    """Move a subject folder to root or another folder and verify it."""
    return await runtime.execute(
        "subjects.folder.move", {"folder": folder, "target_folder": target_folder}
    )


@mcp.tool()
async def chaoxing_delete_subject_folder(
    folder: str,
    allow_nonempty: bool = False,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting a subject folder; nonempty deletion is opt-in."""
    return await runtime.execute(
        "subjects.folder.delete",
        {"folder": folder, "allow_nonempty": allow_nonempty},
        confirmation_token,
    )


@mcp.tool()
async def chaoxing_set_subject_publish_status(
    subject: str,
    published: bool,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm publishing or unpublishing a subject."""
    return await runtime.execute(
        "subjects.publish_status.update",
        {"subject": subject, "published": published},
        confirmation_token,
    )


@mcp.tool()
async def chaoxing_move_subject(subject: str, target_folder: str = "-1") -> dict[str, Any]:
    """Move a subject to root or another subject folder and verify it."""
    return await runtime.execute(
        "subjects.move", {"subject": subject, "target_folder": target_folder}
    )


@mcp.tool()
async def chaoxing_delete_subject(
    subject: str, confirmation_token: str | None = None
) -> dict[str, Any]:
    """Preview or confirm moving a subject into the recycle bin."""
    return await runtime.execute("subjects.delete", {"subject": subject}, confirmation_token)


@mcp.tool()
async def chaoxing_list_subject_recycle(search: str = "", max_items: int = 1000) -> dict[str, Any]:
    """List or search recycled subjects."""
    return await runtime.execute(
        "subjects.recycle.list", {"search": search, "max_items": max_items}
    )


@mcp.tool()
async def chaoxing_restore_subject(subject: str) -> dict[str, Any]:
    """Restore a self-deleted subject and verify it returned to the active tree."""
    return await runtime.execute("subjects.recycle.restore", {"subject": subject})


@mcp.tool()
async def chaoxing_permanently_delete_subject(
    subject: str, confirmation_token: str | None = None
) -> dict[str, Any]:
    """Preview or confirm permanently deleting a recycled subject."""
    return await runtime.execute(
        "subjects.recycle.delete", {"subject": subject}, confirmation_token
    )


@mcp.tool()
async def chaoxing_list_detection_channels() -> dict[str, Any]:
    """List currently available Daya similarity-check comparison libraries."""
    return await runtime.execute("detection.channels.list")


@mcp.tool()
async def chaoxing_list_detection_records(
    detection_type: str,
    page: int = 1,
    page_size: int = 100,
    status: int = -1,
    begin_date: str = "",
    end_date: str = "",
    search: str = "",
) -> dict[str, Any]:
    """List similarity, AIGC, or two-file comparison records with filters."""
    return await runtime.execute(
        "detection.records.list",
        {
            "type": detection_type,
            "page": page,
            "page_size": page_size,
            "status": status,
            "begin_date": begin_date,
            "end_date": end_date,
            "search": search,
        },
    )


@mcp.tool()
async def chaoxing_read_detection_status(detection_type: str, record: str) -> dict[str, Any]:
    """Read live parse and payment status for one detection record."""
    return await runtime.execute(
        "detection.record.status", {"type": detection_type, "record": record}
    )


@mcp.tool()
async def chaoxing_submit_detection(
    detection_type: str,
    title: str,
    author: str = "",
    content: str | None = None,
    file: str | None = None,
    end_year: str = "",
    channel_ids: list[str] | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm submitting text or a file for similarity or AIGC detection."""
    return await runtime.execute(
        "detection.submit",
        {
            "type": detection_type,
            "title": title,
            "author": author,
            "content": content,
            "file": file,
            "end_year": end_year,
            "channel_ids": channel_ids,
        },
        confirmation_token,
    )


@mcp.tool()
async def chaoxing_submit_detection_comparison(
    title_1: str,
    file_1: str,
    title_2: str,
    file_2: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm submitting two local files for pairwise comparison."""
    return await runtime.execute(
        "detection.comparison.submit",
        {
            "title_1": title_1,
            "file_1": file_1,
            "title_2": title_2,
            "file_2": file_2,
        },
        confirmation_token,
    )


@mcp.tool()
async def chaoxing_read_detection_payment_status(
    detection_type: str, record: str
) -> dict[str, Any]:
    """Read whether a report is available, paid, or eligible for a free entitlement."""
    return await runtime.execute(
        "detection.payment.status", {"type": detection_type, "record": record}
    )


@mcp.tool()
async def chaoxing_use_detection_free_entitlement(
    detection_type: str,
    record: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm consuming a free entitlement to unlock a detection report."""
    return await runtime.execute(
        "detection.free_entitlement.use",
        {"type": detection_type, "record": record},
        confirmation_token,
    )


@mcp.tool()
async def chaoxing_download_detection_report(
    detection_type: str,
    record: str,
    output_path: str,
    result_type: int = 1,
    timeout_seconds: float = 300,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Generate if necessary and download an unlocked detection report."""
    return await runtime.execute(
        "detection.report.download",
        {
            "type": detection_type,
            "record": record,
            "output_path": output_path,
            "result_type": result_type,
            "timeout_seconds": timeout_seconds,
            "overwrite": overwrite,
        },
    )


@mcp.tool()
async def chaoxing_delete_detection_record(
    detection_type: str,
    record: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm permanently deleting a Daya detection record."""
    return await runtime.execute(
        "detection.record.delete",
        {"type": detection_type, "record": record},
        confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_live_rooms(
    search: str = "",
    start_time: str = "",
    end_time: str = "",
    sort_key: int = 0,
    sort_type: int = 0,
    max_items: int = 1000,
) -> dict[str, Any]:
    """List personal live rooms without opening a browser."""
    return await runtime.execute(
        "live.rooms.list",
        {
            "search": search,
            "start_time": start_time,
            "end_time": end_time,
            "sort_key": sort_key,
            "sort_type": sort_type,
            "max_items": max_items,
        },
    )


@mcp.tool()
async def chaoxing_read_live_room(room: str) -> dict[str, Any]:
    """Read one live room's metadata and access settings without exposing its push key."""
    return await runtime.execute("live.room.read", {"room": room})


@mcp.tool()
async def chaoxing_create_live_room(
    title: str,
    scheduled_time: str = "",
    introduction: str = "",
    content_format: str = "plain",
    mode: str = "multi_device",
    chat_content_review: bool = True,
    cover_object_id: str = "",
    preview_video_object_id: str = "",
    extends_info: dict[str, Any] | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm creating a live room; creation never starts broadcasting."""
    return await runtime.execute(
        "live.room.create",
        {
            "title": title,
            "scheduled_time": scheduled_time,
            "introduction": introduction,
            "content_format": content_format,
            "mode": mode,
            "chat_content_review": chat_content_review,
            "cover_object_id": cover_object_id,
            "preview_video_object_id": preview_video_object_id,
            "extends_info": extends_info,
        },
        confirmation_token,
    )


@mcp.tool()
async def chaoxing_update_live_room(
    room: str,
    title: str | None = None,
    scheduled_time: str | None = None,
    introduction: str | None = None,
    content_format: str = "plain",
    cover_object_id: str | None = None,
    preview_video_object_id: str | None = None,
) -> dict[str, Any]:
    """Update and verify live-room metadata."""
    parameters: dict[str, Any] = {"room": room, "content_format": content_format}
    for key, value in {
        "title": title,
        "scheduled_time": scheduled_time,
        "introduction": introduction,
        "cover_object_id": cover_object_id,
        "preview_video_object_id": preview_video_object_id,
    }.items():
        if value is not None:
            parameters[key] = value
    return await runtime.execute("live.room.update", parameters)


@mcp.tool()
async def chaoxing_update_live_room_settings(
    room: str,
    comments_enabled: bool | None = None,
    forwarding_enabled: bool | None = None,
    replay_enabled: bool | None = None,
    learning_app_only: bool | None = None,
    chat_content_review: bool | None = None,
    login_required: bool | None = None,
    picture_live: bool | None = None,
    access_password: str | None = None,
    show_viewer_count: bool | None = None,
    reservations_enabled: bool | None = None,
    preupload_enabled: bool | None = None,
    allowed_unit_ids: list[str] | None = None,
    replay_start_offset_seconds: int | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm changing live-room access, interaction, and replay settings."""
    parameters: dict[str, Any] = {"room": room}
    for key, value in {
        "comments_enabled": comments_enabled,
        "forwarding_enabled": forwarding_enabled,
        "replay_enabled": replay_enabled,
        "learning_app_only": learning_app_only,
        "chat_content_review": chat_content_review,
        "login_required": login_required,
        "picture_live": picture_live,
        "access_password": access_password,
        "show_viewer_count": show_viewer_count,
        "reservations_enabled": reservations_enabled,
        "preupload_enabled": preupload_enabled,
        "allowed_unit_ids": allowed_unit_ids,
        "replay_start_offset_seconds": replay_start_offset_seconds,
    }.items():
        if value is not None:
            parameters[key] = value
    return await runtime.execute("live.room.settings.update", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_read_live_status(room: str) -> dict[str, Any]:
    """Read the room and media-stream status without starting the broadcast."""
    return await runtime.execute("live.room.status", {"room": room})


@mcp.tool()
async def chaoxing_read_live_watch_address(room: str) -> dict[str, Any]:
    """Read a live room's watch URL, invitation code, and expiration."""
    return await runtime.execute("live.room.watch", {"room": room})


@mcp.tool()
async def chaoxing_read_live_stream_credentials(
    room: str, confirmation_token: str | None = None
) -> dict[str, Any]:
    """Preview or confirm revealing RTMP push credentials for client-free broadcasting."""
    return await runtime.execute("live.stream.credentials", {"room": room}, confirmation_token)


@mcp.tool()
async def chaoxing_upload_live_asset(file: str, kind: str, room: str = "") -> dict[str, Any]:
    """Upload a live cover or MP4 preview, optionally attaching it to a room."""
    return await runtime.execute("live.asset.upload", {"file": file, "kind": kind, "room": room})


@mcp.tool()
async def chaoxing_export_live_rooms(
    search: str = "",
    start_time: str = "",
    end_time: str = "",
    sort_key: int = 0,
    sort_type: int = 0,
) -> dict[str, Any]:
    """Queue a filtered live-record export for delivery to the Chaoxing inbox."""
    return await runtime.execute(
        "live.export",
        {
            "search": search,
            "start_time": start_time,
            "end_time": end_time,
            "sort_key": sort_key,
            "sort_type": sort_type,
        },
    )


@mcp.tool()
async def chaoxing_list_live_units() -> dict[str, Any]:
    """List units that may be allowed to watch a live room or theme."""
    return await runtime.execute("live.units.list")


@mcp.tool()
async def chaoxing_delete_live_room(
    room: str, confirmation_token: str | None = None
) -> dict[str, Any]:
    """Preview or confirm moving a live room to the recycle bin."""
    return await runtime.execute("live.room.delete", {"room": room}, confirmation_token)


@mcp.tool()
async def chaoxing_list_live_recycle(search: str = "", max_items: int = 1000) -> dict[str, Any]:
    """List deleted live rooms."""
    return await runtime.execute("live.recycle.list", {"search": search, "max_items": max_items})


@mcp.tool()
async def chaoxing_restore_live_room(room: str) -> dict[str, Any]:
    """Restore and verify a live room from the recycle bin."""
    return await runtime.execute("live.recycle.restore", {"room": room})


@mcp.tool()
async def chaoxing_permanently_delete_live_room(
    room: str, confirmation_token: str | None = None
) -> dict[str, Any]:
    """Preview or confirm permanently deleting a recycled live room."""
    return await runtime.execute("live.recycle.delete", {"room": room}, confirmation_token)


@mcp.tool()
async def chaoxing_list_live_themes(search: str = "", max_items: int = 1000) -> dict[str, Any]:
    """List themed live entries and their access settings."""
    return await runtime.execute("live.themes.list", {"search": search, "max_items": max_items})


@mcp.tool()
async def chaoxing_read_live_theme(theme: str, max_rooms: int = 1000) -> dict[str, Any]:
    """Read a live theme, its watch address, invitation code, and child rooms."""
    return await runtime.execute("live.theme.read", {"theme": theme, "max_rooms": max_rooms})


@mcp.tool()
async def chaoxing_create_live_theme(
    name: str,
    description: str = "",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm creating a themed-live entry without starting a stream."""
    return await runtime.execute(
        "live.theme.create",
        {"name": name, "description": description},
        confirmation_token,
    )


@mcp.tool()
async def chaoxing_update_live_theme(
    theme: str, name: str | None = None, description: str | None = None
) -> dict[str, Any]:
    """Update and verify a live theme's name or description."""
    parameters: dict[str, Any] = {"theme": theme}
    if name is not None:
        parameters["name"] = name
    if description is not None:
        parameters["description"] = description
    return await runtime.execute("live.theme.update", parameters)


@mcp.tool()
async def chaoxing_update_live_theme_settings(
    theme: str,
    forwarding_enabled: bool | None = None,
    replay_enabled: bool | None = None,
    learning_app_only: bool | None = None,
    login_required: bool | None = None,
    allowed_unit_ids: list[str] | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm changing a themed live entry's access settings."""
    parameters: dict[str, Any] = {"theme": theme}
    for key, value in {
        "forwarding_enabled": forwarding_enabled,
        "replay_enabled": replay_enabled,
        "learning_app_only": learning_app_only,
        "login_required": login_required,
        "allowed_unit_ids": allowed_unit_ids,
    }.items():
        if value is not None:
            parameters[key] = value
    return await runtime.execute("live.theme.settings.update", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_add_live_room_to_theme(
    theme: str, room: str, confirmation_token: str | None = None
) -> dict[str, Any]:
    """Preview or confirm adding an existing personal live room to a theme."""
    return await runtime.execute(
        "live.theme.room.add",
        {"theme": theme, "room": room},
        confirmation_token,
    )


@mcp.tool()
async def chaoxing_create_live_room_in_theme(
    theme: str,
    title: str,
    scheduled_time: str = "",
    introduction: str = "",
    content_format: str = "plain",
    mode: str = "multi_device",
    chat_content_review: bool = True,
    cover_object_id: str = "",
    preview_video_object_id: str = "",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm creating a child room in a live theme without broadcasting."""
    return await runtime.execute(
        "live.theme.room.create",
        {
            "theme": theme,
            "title": title,
            "scheduled_time": scheduled_time,
            "introduction": introduction,
            "content_format": content_format,
            "mode": mode,
            "chat_content_review": chat_content_review,
            "cover_object_id": cover_object_id,
            "preview_video_object_id": preview_video_object_id,
        },
        confirmation_token,
    )


@mcp.tool()
async def chaoxing_delete_live_theme(
    theme: str, confirmation_token: str | None = None
) -> dict[str, Any]:
    """Preview or confirm deleting a live theme while retaining its personal rooms."""
    return await runtime.execute("live.theme.delete", {"theme": theme}, confirmation_token)


@mcp.tool()
async def chaoxing_list_notes(search: str = "", max_items: int = 1000) -> dict[str, Any]:
    """List or search the current account's personal notes."""
    return await runtime.execute(
        "notes.list",
        {"search": search, "max_items": max_items},
    )


@mcp.tool()
async def chaoxing_read_note(note: str) -> dict[str, Any]:
    """Read a personal note selected by title, index, or CID."""
    return await runtime.execute("notes.read", {"note": note})


@mcp.tool()
async def chaoxing_create_note(
    title: str,
    content: str = "",
    content_format: str = "plain",
    notebook_cid: str = "root",
) -> dict[str, Any]:
    """Create and verify a private personal note without opening a browser."""
    return await runtime.execute(
        "notes.create",
        {
            "title": title,
            "content": content,
            "content_format": content_format,
            "notebook_cid": notebook_cid,
        },
    )


@mcp.tool()
async def chaoxing_update_note(
    note: str,
    title: str | None = None,
    content: str | None = None,
    content_format: str = "plain",
) -> dict[str, Any]:
    """Update and verify the title or content of an editable personal note."""
    parameters: dict[str, Any] = {"note": note, "content_format": content_format}
    if title is not None:
        parameters["title"] = title
    if content is not None:
        parameters["content"] = content
    return await runtime.execute("notes.update", parameters)


@mcp.tool()
async def chaoxing_delete_note(
    note: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting one personal note."""
    return await runtime.execute(
        "notes.delete",
        {"note": note},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_inbox_notices(
    scope: str = "received",
    search: str = "",
    sender: str = "",
    start_time: str = "",
    end_time: str = "",
    max_items: int = 1000,
) -> dict[str, Any]:
    """List or search received or sent personal inbox notices."""
    return await runtime.execute(
        "inbox.notices.list",
        {
            "scope": scope,
            "search": search,
            "sender": sender,
            "start_time": start_time,
            "end_time": end_time,
            "max_items": max_items,
        },
    )


@mcp.tool()
async def chaoxing_read_inbox_notice(
    notice: str,
    scope: str = "received",
) -> dict[str, Any]:
    """Read one full inbox notice; a received unread notice becomes read."""
    return await runtime.execute(
        "inbox.notice.read",
        {"notice": notice, "scope": scope},
    )


@mcp.tool()
async def chaoxing_mark_inbox_notice_unread(notice: str) -> dict[str, Any]:
    """Mark one received inbox notice unread and verify the refreshed state."""
    return await runtime.execute(
        "inbox.notice.mark_unread",
        {"notice": notice, "scope": "received"},
    )


@mcp.tool()
async def chaoxing_set_inbox_notice_top_status(
    notice: str,
    top: bool,
    scope: str = "received",
) -> dict[str, Any]:
    """Set or clear the top status of one inbox notice."""
    return await runtime.execute(
        "inbox.notice.top_status.update",
        {"notice": notice, "top": top, "scope": scope},
    )


@mcp.tool()
async def chaoxing_set_inbox_notice_collect_status(
    notice: str,
    collect: bool,
    scope: str = "received",
) -> dict[str, Any]:
    """Collect or uncollect one inbox notice and verify the refreshed state."""
    return await runtime.execute(
        "inbox.notice.collect_status.update",
        {"notice": notice, "collect": collect, "scope": scope},
    )


@mcp.tool()
async def chaoxing_delete_inbox_notice(
    notice: str,
    scope: str = "received",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting one received or sent inbox notice."""
    return await runtime.execute(
        "inbox.notice.delete",
        {"notice": notice, "scope": scope},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_send_personal_notice(
    recipients: list[str],
    title: str,
    content: str,
    content_format: str = "plain",
    allow_comments: bool = True,
    show_comments: bool = True,
    hide_read_status: bool = False,
    forbid_forwarding: bool = False,
    permission_password: str = "",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm sending a personal inbox notice to people by name or PUID."""
    return await runtime.execute(
        "inbox.notice.send",
        {
            "recipients": recipients,
            "title": title,
            "content": content,
            "content_format": content_format,
            "allow_comments": allow_comments,
            "show_comments": show_comments,
            "hide_read_status": hide_read_status,
            "forbid_forwarding": forbid_forwarding,
            "permission_password": permission_password,
        },
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_personal_notice_drafts(
    search: str = "",
    max_items: int = 1000,
) -> dict[str, Any]:
    """List personal inbox-notice drafts without mixing in course notice drafts."""
    return await runtime.execute(
        "inbox.drafts.list",
        {"search": search, "max_items": max_items},
    )


@mcp.tool()
async def chaoxing_save_personal_notice_draft(
    title: str,
    content: str,
    recipients: list[str] | None = None,
    draft: str = "",
    content_format: str = "plain",
    allow_comments: bool = True,
    show_comments: bool = True,
    hide_read_status: bool = False,
    forbid_forwarding: bool = False,
) -> dict[str, Any]:
    """Create or update a personal inbox-notice draft and verify it by rereading."""
    return await runtime.execute(
        "inbox.draft.save",
        {
            "title": title,
            "content": content,
            "recipients": recipients,
            "draft": draft,
            "content_format": content_format,
            "allow_comments": allow_comments,
            "show_comments": show_comments,
            "hide_read_status": hide_read_status,
            "forbid_forwarding": forbid_forwarding,
        },
    )


@mcp.tool()
async def chaoxing_delete_personal_notice_draft(
    draft: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting one personal inbox-notice draft."""
    return await runtime.execute(
        "inbox.draft.delete",
        {"draft": draft},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_inbox_folders() -> dict[str, Any]:
    """List personal inbox folders, counts, unread counts, and order."""
    return await runtime.execute("inbox.folders.list")


@mcp.tool()
async def chaoxing_read_inbox_folder_filters(folder: str) -> dict[str, Any]:
    """Read sender and title-keyword rules for one personal inbox folder."""
    return await runtime.execute("inbox.folder.filters.read", {"folder": folder})


@mcp.tool()
async def chaoxing_list_inbox_folder_notices(
    folder: str,
    scope: str = "received",
    search: str = "",
    sender: str = "",
    start_time: str = "",
    end_time: str = "",
    max_items: int = 1000,
) -> dict[str, Any]:
    """List or search notices inside one personal inbox folder."""
    return await runtime.execute(
        "inbox.folder.notices.list",
        {
            "folder": folder,
            "scope": scope,
            "search": search,
            "sender": sender,
            "start_time": start_time,
            "end_time": end_time,
            "max_items": max_items,
        },
    )


@mcp.tool()
async def chaoxing_create_inbox_folder(
    name: str,
    sender_rules: list[dict[str, Any]] | None = None,
    keywords: list[dict[str, Any] | str] | None = None,
) -> dict[str, Any]:
    """Create an inbox folder with optional sender and title-keyword rules."""
    return await runtime.execute(
        "inbox.folder.create",
        {"name": name, "sender_rules": sender_rules, "keywords": keywords},
    )


@mcp.tool()
async def chaoxing_update_inbox_folder(
    folder: str,
    name: str | None = None,
    sender_rules: list[dict[str, Any]] | None = None,
    keywords: list[dict[str, Any] | str] | None = None,
) -> dict[str, Any]:
    """Rename an inbox folder or replace its sender or keyword rules."""
    parameters: dict[str, Any] = {"folder": folder}
    if name is not None:
        parameters["name"] = name
    if sender_rules is not None:
        parameters["sender_rules"] = sender_rules
    if keywords is not None:
        parameters["keywords"] = keywords
    return await runtime.execute("inbox.folder.update", parameters)


@mcp.tool()
async def chaoxing_delete_inbox_folder(
    folder: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting an inbox folder and recycling its notices."""
    return await runtime.execute(
        "inbox.folder.delete",
        {"folder": folder},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_reorder_inbox_folders(
    folders: list[str],
    top: bool = False,
) -> dict[str, Any]:
    """Submit every folder in the default or top group in the desired order."""
    return await runtime.execute(
        "inbox.folders.reorder",
        {"folders": folders, "top": top},
    )


@mcp.tool()
async def chaoxing_move_inbox_notices(
    notices: list[str],
    destination_folder: str,
    scope: str = "received",
    source_folder: str = "",
) -> dict[str, Any]:
    """Move personal inbox notices to a folder or the inbox root."""
    return await runtime.execute(
        "inbox.notices.move",
        {
            "notices": notices,
            "destination_folder": destination_folder,
            "scope": scope,
            "source_folder": source_folder,
        },
    )


@mcp.tool()
async def chaoxing_list_inbox_recycle(
    search: str = "",
    max_items: int = 1000,
) -> dict[str, Any]:
    """List or search personal notices in the inbox recycle bin."""
    return await runtime.execute(
        "inbox.recycle.list",
        {"search": search, "max_items": max_items},
    )


@mcp.tool()
async def chaoxing_restore_inbox_recycle_notices(
    notices: list[str],
) -> dict[str, Any]:
    """Restore up to 60 personal notices from the inbox recycle bin."""
    return await runtime.execute("inbox.recycle.restore", {"notices": notices})


@mcp.tool()
async def chaoxing_permanently_delete_inbox_recycle_notices(
    notices: list[str],
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm permanently deleting selected recycled inbox notices."""
    return await runtime.execute(
        "inbox.recycle.items.delete",
        {"notices": notices},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_empty_inbox_recycle(
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm permanently emptying the personal inbox recycle bin."""
    return await runtime.execute(
        "inbox.recycle.empty",
        {},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_contact_units() -> dict[str, Any]:
    """List address-book units visible to the current account."""
    return await runtime.execute("contacts.units.list")


@mcp.tool()
async def chaoxing_list_contact_departments(
    fid: str,
    parent_id: str = "2C89C38F937992D2",
    department_type: str = "unit",
) -> dict[str, Any]:
    """List child departments in one visible address-book unit or custom team."""
    return await runtime.execute(
        "contacts.departments.list",
        {"fid": fid, "parent_id": parent_id, "department_type": department_type},
    )


@mcp.tool()
async def chaoxing_list_contact_department_members(
    fid: str,
    department_id: str,
    search: str = "",
    max_items: int = 1000,
) -> dict[str, Any]:
    """List visible members of one address-book department."""
    return await runtime.execute(
        "contacts.department.members.list",
        {
            "fid": fid,
            "department_id": department_id,
            "search": search,
            "max_items": max_items,
        },
    )


@mcp.tool()
async def chaoxing_search_contacts(
    search: str,
    fid: str = "",
    department_id: str = "",
    mode: int = -1,
    max_items: int = 300,
) -> dict[str, Any]:
    """Search people visible in the current account's address book."""
    return await runtime.execute(
        "contacts.people.search",
        {
            "search": search,
            "fid": fid,
            "department_id": department_id,
            "mode": mode,
            "max_items": max_items,
        },
    )


@mcp.tool()
async def chaoxing_list_contact_relations(
    relation: str = "followers",
    max_items: int = 1000,
) -> dict[str, Any]:
    """List followers or people followed by the current account."""
    return await runtime.execute(
        "contacts.relations.list",
        {"relation": relation, "max_items": max_items},
    )


@mcp.tool()
async def chaoxing_list_contact_groups(search: str = "") -> dict[str, Any]:
    """List joined groups visible through the address book."""
    return await runtime.execute("contacts.groups.list", {"search": search})


@mcp.tool()
async def chaoxing_list_contact_group_members(
    group: str,
    search: str = "",
    max_items: int = 1000,
) -> dict[str, Any]:
    """List members of one joined group selected by name, index, or ID."""
    return await runtime.execute(
        "contacts.group.members.list",
        {"group": group, "search": search, "max_items": max_items},
    )


@mcp.tool()
async def chaoxing_list_contact_chatgroups(max_items: int = 1000) -> dict[str, Any]:
    """List chat groups joined by the current account."""
    return await runtime.execute("contacts.chatgroups.list", {"max_items": max_items})


@mcp.tool()
async def chaoxing_list_contact_chatgroup_members(
    chatgroup: str,
    max_items: int = 1000,
) -> dict[str, Any]:
    """List members of one chat group selected by name, index, or ID."""
    return await runtime.execute(
        "contacts.chatgroup.members.list",
        {"chatgroup": chatgroup, "max_items": max_items},
    )


@mcp.tool()
async def chaoxing_list_contact_teams() -> dict[str, Any]:
    """List custom address-book teams visible to the current account."""
    return await runtime.execute("contacts.teams.list")


@mcp.tool()
async def chaoxing_list_contact_team_members(
    team: str,
    max_items: int = 1000,
) -> dict[str, Any]:
    """List members of one custom address-book team."""
    return await runtime.execute(
        "contacts.team.members.list",
        {"team": team, "max_items": max_items},
    )


@mcp.tool()
async def chaoxing_set_contact_follow_status(
    person: str,
    followed: bool,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm following or unfollowing one known contact."""
    return await runtime.execute(
        "contacts.follow_status.update",
        {"person": person, "followed": followed},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_create_contact_team(
    name: str,
    members: list[str],
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm creating a custom team from known contacts or PUIDs."""
    return await runtime.execute(
        "contacts.team.create",
        {"name": name, "members": members},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_rename_contact_team(
    team: str,
    name: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm renaming a custom address-book team."""
    return await runtime.execute(
        "contacts.team.rename",
        {"team": team, "name": name},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_add_contact_team_members(
    team: str,
    members: list[str],
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm adding known contacts to a custom team."""
    return await runtime.execute(
        "contacts.team.members.add",
        {"team": team, "members": members},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_remove_contact_team_member(
    team: str,
    member: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm removing one member from a custom team."""
    return await runtime.execute(
        "contacts.team.member.remove",
        {"team": team, "member": member},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_delete_contact_team(
    team: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting a custom address-book team."""
    return await runtime.execute(
        "contacts.team.delete",
        {"team": team},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_exit_contact_team(
    team: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm exiting a custom address-book team created by someone else."""
    return await runtime.execute(
        "contacts.team.exit",
        {"team": team},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_personal_groups(
    folder: str = "",
    search: str = "",
) -> dict[str, Any]:
    """List or search personal groups, optionally inside one personal folder."""
    return await runtime.execute("groups.list", {"folder": folder, "search": search})


@mcp.tool()
async def chaoxing_read_personal_group(group: str) -> dict[str, Any]:
    """Read one personal group's details, settings, and current-account permissions."""
    return await runtime.execute("groups.read", {"group": group})


@mcp.tool()
async def chaoxing_create_personal_group(
    name: str,
    description: str = "",
    folder: str = "",
    logo_url: str = "",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm creating a shared personal group."""
    return await runtime.execute(
        "groups.create",
        {
            "name": name,
            "description": description,
            "folder": folder,
            "logo_url": logo_url,
        },
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_update_personal_group(
    group: str,
    name: str | None = None,
    description: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm changing a personal group's name or description."""
    parameters: dict[str, Any] = {"group": group}
    if name is not None:
        parameters["name"] = name
    if description is not None:
        parameters["description"] = description
    return await runtime.execute(
        "groups.update",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_update_personal_group_logo(
    group: str,
    file: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm uploading a local image as a personal group logo."""
    return await runtime.execute(
        "groups.logo.update",
        {"group": group, "file": file},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_personal_group_modules(group: str) -> dict[str, Any]:
    """List the mandatory and currently configurable personal-group modules."""
    return await runtime.execute("groups.modules.list", {"group": group})


@mcp.tool()
async def chaoxing_update_personal_group_modules(
    group: str,
    enabled_type_ids: list[str],
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm the module type IDs enabled for one personal group."""
    return await runtime.execute(
        "groups.modules.update",
        {"group": group, "enabled_type_ids": enabled_type_ids},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_update_personal_group_settings(
    group: str,
    changes: dict[str, bool],
    sign_ban_start_time: int | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm changing supported boolean settings for one personal group."""
    parameters: dict[str, Any] = {"group": group, "changes": changes}
    if sign_ban_start_time is not None:
        parameters["sign_ban_start_time"] = sign_ban_start_time
    return await runtime.execute(
        "groups.settings.update",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_personal_group_levels(group: str) -> dict[str, Any]:
    """List the level-title series and all 15 growth thresholds for a personal group."""
    return await runtime.execute("groups.levels.list", {"group": group})


@mcp.tool()
async def chaoxing_set_personal_group_level_series(
    group: str,
    series: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm switching between default and saved custom level titles."""
    return await runtime.execute(
        "groups.levels.series.update",
        {"group": group, "series": series},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_update_personal_group_custom_levels(
    group: str,
    levels: list[dict[str, Any]],
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm saving the complete set of 15 custom group levels."""
    return await runtime.execute(
        "groups.levels.custom.update",
        {"group": group, "levels": levels},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_personal_group_growth_rules(group: str) -> dict[str, Any]:
    """List the six growth-value rules configured for a personal group."""
    return await runtime.execute("groups.growth_rules.list", {"group": group})


@mcp.tool()
async def chaoxing_set_personal_group_growth_rule_series(
    group: str,
    series: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm switching the default or saved custom growth-rule series."""
    return await runtime.execute(
        "groups.growth_rules.series.update",
        {"group": group, "series": series},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_update_personal_group_growth_rules(
    group: str,
    changes: dict[str, int],
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm changing one or more personal-group growth values."""
    return await runtime.execute(
        "groups.growth_rules.update",
        {"group": group, "changes": changes},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_update_personal_group_speaking_rules(
    group: str,
    changes: dict[str, int],
    attachment_rules: dict[str, bool] | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm changing topic, reply, and attachment requirements."""
    parameters: dict[str, Any] = {"group": group, "changes": changes}
    if attachment_rules is not None:
        parameters["attachment_rules"] = attachment_rules
    return await runtime.execute(
        "groups.speaking_rules.update",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_send_personal_group_notice(
    group: str,
    title: str,
    content: str,
    pcode: str = "",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm sending a plain-text notice to one personal group."""
    return await runtime.execute(
        "groups.notice.send",
        {"group": group, "title": title, "content": content, "pcode": pcode},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_personal_group_review_reminders(group: str) -> dict[str, Any]:
    """List review reminders and eligible reviewer PUIDs for a personal group."""
    return await runtime.execute("groups.review_reminders.list", {"group": group})


@mcp.tool()
async def chaoxing_create_personal_group_review_reminder(
    group: str,
    start_time: str,
    end_time: str,
    weeks: list[str],
    puids: list[str],
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm creating a weekly review reminder for selected reviewers."""
    return await runtime.execute(
        "groups.review_reminder.create",
        {
            "group": group,
            "start_time": start_time,
            "end_time": end_time,
            "weeks": weeks,
            "puids": puids,
        },
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_update_personal_group_review_reminder(
    group: str,
    reminder: str,
    start_time: str | None = None,
    end_time: str | None = None,
    weeks: list[str] | None = None,
    puids: list[str] | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm changing one review reminder by UUID or list index."""
    parameters: dict[str, Any] = {"group": group, "reminder": reminder}
    for key, value in {
        "start_time": start_time,
        "end_time": end_time,
        "weeks": weeks,
        "puids": puids,
    }.items():
        if value is not None:
            parameters[key] = value
    return await runtime.execute(
        "groups.review_reminder.update",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_delete_personal_group_review_reminders(
    group: str,
    reminders: list[str],
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting review reminders by UUID or list index."""
    return await runtime.execute(
        "groups.review_reminders.delete",
        {"group": group, "reminders": reminders},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_personal_group_labels(group: str) -> dict[str, Any]:
    """List the topic labels configured for one personal group."""
    return await runtime.execute("groups.labels.list", {"group": group})


@mcp.tool()
async def chaoxing_create_personal_group_label(group: str, name: str) -> dict[str, Any]:
    """Create one personal group topic label."""
    return await runtime.execute("groups.label.create", {"group": group, "name": name})


@mcp.tool()
async def chaoxing_rename_personal_group_label(group: str, label: str, name: str) -> dict[str, Any]:
    """Rename one personal group topic label."""
    return await runtime.execute(
        "groups.label.rename", {"group": group, "label": label, "name": name}
    )


@mcp.tool()
async def chaoxing_reorder_personal_group_labels(group: str, labels: list[str]) -> dict[str, Any]:
    """Set the complete label order for one personal group."""
    return await runtime.execute("groups.labels.reorder", {"group": group, "labels": labels})


@mcp.tool()
async def chaoxing_delete_personal_group_labels(
    group: str,
    labels: list[str],
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting personal group topic labels."""
    return await runtime.execute(
        "groups.labels.delete",
        {"group": group, "labels": labels},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_personal_group_deletion_reasons(group: str) -> dict[str, Any]:
    """List preset topic and reply deletion reasons for one personal group."""
    return await runtime.execute("groups.deletion_reasons.list", {"group": group})


@mcp.tool()
async def chaoxing_create_personal_group_deletion_reason(group: str, name: str) -> dict[str, Any]:
    """Create one preset deletion reason for a personal group."""
    return await runtime.execute("groups.deletion_reason.create", {"group": group, "name": name})


@mcp.tool()
async def chaoxing_rename_personal_group_deletion_reason(
    group: str, reason: str, name: str
) -> dict[str, Any]:
    """Rename one preset personal group deletion reason."""
    return await runtime.execute(
        "groups.deletion_reason.rename",
        {"group": group, "reason": reason, "name": name},
    )


@mcp.tool()
async def chaoxing_delete_personal_group_deletion_reasons(
    group: str,
    reasons: list[str],
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting preset personal group deletion reasons."""
    return await runtime.execute(
        "groups.deletion_reasons.delete",
        {"group": group, "reasons": reasons},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_personal_group_recycle_items(group: str) -> dict[str, Any]:
    """List topics, replies, and folders in one personal group recycle bin."""
    return await runtime.execute("groups.recycle.list", {"group": group})


@mcp.tool()
async def chaoxing_restore_personal_group_recycle_items(
    group: str, items: list[str]
) -> dict[str, Any]:
    """Restore selected items from one personal group recycle bin."""
    return await runtime.execute("groups.recycle.restore", {"group": group, "items": items})


@mcp.tool()
async def chaoxing_permanently_delete_personal_group_recycle_items(
    group: str,
    items: list[str],
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm permanently deleting personal group recycle items."""
    return await runtime.execute(
        "groups.recycle.items.delete",
        {"group": group, "items": items},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_empty_personal_group_recycle(
    group: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm permanently emptying one personal group recycle bin."""
    return await runtime.execute(
        "groups.recycle.empty",
        {"group": group},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_personal_group_exports(group: str) -> dict[str, Any]:
    """List export jobs in one personal group's download center."""
    return await runtime.execute("groups.exports.list", {"group": group})


@mcp.tool()
async def chaoxing_create_personal_group_member_export(group: str) -> dict[str, Any]:
    """Create an XLSX member-list export and return its download-center job."""
    return await runtime.execute("groups.members.export.create", {"group": group})


@mcp.tool()
async def chaoxing_download_personal_group_export(
    group: str,
    export: str,
    output_path: str,
    overwrite: bool = False,
    wait_seconds: int = 120,
) -> dict[str, Any]:
    """Download one ready personal group export to a local path."""
    return await runtime.execute(
        "groups.export.download",
        {
            "group": group,
            "export": export,
            "output_path": output_path,
            "overwrite": overwrite,
            "wait_seconds": wait_seconds,
        },
    )


@mcp.tool()
async def chaoxing_wait_personal_group_export(
    group: str,
    export: str,
    timeout_seconds: int = 120,
    poll_seconds: int = 2,
) -> dict[str, Any]:
    """Wait until one personal group export is ready or failed."""
    return await runtime.execute(
        "groups.export.wait",
        {
            "group": group,
            "export": export,
            "timeout_seconds": timeout_seconds,
            "poll_seconds": poll_seconds,
        },
    )


@mcp.tool()
async def chaoxing_retry_personal_group_export(
    group: str,
    export: str,
) -> dict[str, Any]:
    """Retry one failed personal group export job."""
    return await runtime.execute("groups.export.retry", {"group": group, "export": export})


@mcp.tool()
async def chaoxing_cancel_personal_group_export(
    group: str,
    export: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm cancelling and removing a personal group export job."""
    return await runtime.execute(
        "groups.export.cancel",
        {"group": group, "export": export},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_personal_group_activities(
    group: str,
    status: str = "all",
    max_items: int = 1000,
) -> dict[str, Any]:
    """List all, online, or offline activity banners for one personal group."""
    return await runtime.execute(
        "groups.activities.list",
        {"group": group, "status": status, "max_items": max_items},
    )


@mcp.tool()
async def chaoxing_upload_personal_group_activity_image(file: str) -> dict[str, Any]:
    """Upload a local image and return its Chaoxing activity-banner preview URL."""
    return await runtime.execute("groups.activity.image.upload", {"file": file})


@mcp.tool()
async def chaoxing_create_personal_group_activity(
    group: str,
    title: str,
    online: bool = False,
    app_link: str = "",
    pc_link: str = "",
    app_image_url: str = "",
    pc_image_url: str = "",
    app_image_width: int = 0,
    app_image_height: int = 0,
    pc_image_width: int = 0,
    pc_image_height: int = 0,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm creating an online or offline personal group activity."""
    return await runtime.execute(
        "groups.activity.create",
        {
            "group": group,
            "title": title,
            "online": online,
            "app_link": app_link,
            "pc_link": pc_link,
            "app_image_url": app_image_url,
            "pc_image_url": pc_image_url,
            "app_image_width": app_image_width,
            "app_image_height": app_image_height,
            "pc_image_width": pc_image_width,
            "pc_image_height": pc_image_height,
        },
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_update_personal_group_activity(
    group: str,
    activity: str,
    title: str | None = None,
    app_link: str | None = None,
    pc_link: str | None = None,
    app_image_url: str | None = None,
    pc_image_url: str | None = None,
    app_image_width: int | None = None,
    app_image_height: int | None = None,
    pc_image_width: int | None = None,
    pc_image_height: int | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm updating a personal group activity's fields."""
    parameters: dict[str, Any] = {"group": group, "activity": activity}
    optional = {
        "title": title,
        "app_link": app_link,
        "pc_link": pc_link,
        "app_image_url": app_image_url,
        "pc_image_url": pc_image_url,
        "app_image_width": app_image_width,
        "app_image_height": app_image_height,
        "pc_image_width": pc_image_width,
        "pc_image_height": pc_image_height,
    }
    parameters.update({key: value for key, value in optional.items() if value is not None})
    return await runtime.execute(
        "groups.activity.update",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_set_personal_group_activity_online_status(
    group: str,
    activity: str,
    online: bool,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm putting one personal group activity online or offline."""
    return await runtime.execute(
        "groups.activity.online_status.update",
        {"group": group, "activity": activity, "online": online},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_reorder_personal_group_activities(
    group: str,
    activities: list[str],
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm the complete order of all online personal group activities."""
    return await runtime.execute(
        "groups.activities.reorder",
        {"group": group, "activities": activities},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_delete_personal_group_activity(
    group: str,
    activity: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting one personal group activity."""
    return await runtime.execute(
        "groups.activity.delete",
        {"group": group, "activity": activity},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_set_personal_group_top_status(
    group: str,
    top: bool,
) -> dict[str, Any]:
    """Set or clear one personal group's top status."""
    return await runtime.execute(
        "groups.top_status.update",
        {"group": group, "top": top},
    )


@mcp.tool()
async def chaoxing_move_personal_group(
    group: str,
    destination_folder: str,
) -> dict[str, Any]:
    """Move a personal group to a personal group folder or the root."""
    return await runtime.execute(
        "groups.move",
        {"group": group, "destination_folder": destination_folder},
    )


@mcp.tool()
async def chaoxing_quit_personal_group(
    group: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm quitting a group created by someone else."""
    return await runtime.execute(
        "groups.quit",
        {"group": group},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_dismiss_personal_group(
    group: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm dismissing a personal group created by the current account."""
    return await runtime.execute(
        "groups.dismiss",
        {"group": group},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_personal_group_members(
    group: str,
    search: str = "",
) -> dict[str, Any]:
    """List or search every member of one personal group, including roles and PUIDs."""
    return await runtime.execute(
        "groups.members.list",
        {"group": group, "search": search},
    )


@mcp.tool()
async def chaoxing_read_personal_group_bulk_import_status(group: str) -> dict[str, Any]:
    """Read bulk-member-import availability, quota, expiry, and template URL."""
    return await runtime.execute("groups.members.bulk_import.status", {"group": group})


@mcp.tool()
async def chaoxing_download_personal_group_bulk_import_template(
    group: str,
    output_path: str,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Download and verify the current personal-group member-import XLSX template."""
    return await runtime.execute(
        "groups.members.bulk_import.template.download",
        {"group": group, "output_path": output_path, "overwrite": overwrite},
    )


@mcp.tool()
async def chaoxing_bulk_import_personal_group_members(
    group: str,
    file: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm using one daily quota to import group members from XLSX."""
    return await runtime.execute(
        "groups.members.bulk_import",
        {"group": group, "file": file},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_read_personal_group_member(
    group: str,
    member: str,
) -> dict[str, Any]:
    """Read one personal group member by name, PUID, member ID, or index."""
    return await runtime.execute(
        "groups.member.read",
        {"group": group, "member": member},
    )


@mcp.tool()
async def chaoxing_read_personal_group_member_permissions(
    group: str,
    member: str,
) -> dict[str, Any]:
    """Read the delegated permission switches for one personal group manager."""
    return await runtime.execute(
        "groups.member.permissions.read",
        {"group": group, "member": member},
    )


@mcp.tool()
async def chaoxing_update_personal_group_member_permissions(
    group: str,
    member: str,
    changes: dict[str, bool],
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm changing delegated permissions for one group manager."""
    return await runtime.execute(
        "groups.member.permissions.update",
        {"group": group, "member": member, "changes": changes},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_personal_group_member_sources(group: str) -> dict[str, Any]:
    """List existing groups and unit directories available as member-addition sources."""
    return await runtime.execute(
        "groups.member.sources.list",
        {"group": group},
    )


@mcp.tool()
async def chaoxing_list_personal_group_member_candidates(
    group: str,
    source_type: str,
    source: str,
    fid: str = "",
    search: str = "",
    account_type: int = 0,
) -> dict[str, Any]:
    """List addable member candidates from one group, unit, or iBuild source."""
    return await runtime.execute(
        "groups.member.candidates.list",
        {
            "group": group,
            "source_type": source_type,
            "source": source,
            "fid": fid,
            "search": search,
            "account_type": account_type,
        },
    )


@mcp.tool()
async def chaoxing_add_personal_group_members(
    group: str,
    puids: list[str],
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm adding one or more people to a personal group by PUID."""
    return await runtime.execute(
        "groups.members.add",
        {"group": group, "puids": puids},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_set_personal_group_member_manager_status(
    group: str,
    member: str,
    manager: bool,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm granting or revoking one personal group manager role."""
    return await runtime.execute(
        "groups.member.manager_status.update",
        {"group": group, "member": member, "manager": manager},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_remove_personal_group_member(
    group: str,
    member: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm removing one member from a personal group."""
    return await runtime.execute(
        "groups.member.remove",
        {"group": group, "member": member},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_transfer_personal_group_creator(
    group: str,
    member: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm transferring personal group ownership to an existing member."""
    return await runtime.execute(
        "groups.creator.transfer",
        {"group": group, "member": member},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_clear_personal_group_external_members(
    group: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm removing every non-Chaoxing member from one personal group."""
    return await runtime.execute(
        "groups.members.external.clear",
        {"group": group},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_read_personal_group_folder_tree() -> dict[str, Any]:
    """Read the complete hierarchy of personal group folders."""
    return await runtime.execute("groups.folders.tree")


@mcp.tool()
async def chaoxing_list_personal_group_folders(
    parent_folder: str = "",
    search: str = "",
) -> dict[str, Any]:
    """List child personal group folders or search all personal group folders."""
    return await runtime.execute(
        "groups.folders.list",
        {"parent_folder": parent_folder, "search": search},
    )


@mcp.tool()
async def chaoxing_create_personal_group_folder(
    name: str,
    parent_folder: str = "",
) -> dict[str, Any]:
    """Create a personal group folder in the root or another folder."""
    return await runtime.execute(
        "groups.folder.create",
        {"name": name, "parent_folder": parent_folder},
    )


@mcp.tool()
async def chaoxing_rename_personal_group_folder(
    folder: str,
    name: str,
) -> dict[str, Any]:
    """Rename a personal group folder and verify the refreshed tree."""
    return await runtime.execute(
        "groups.folder.rename",
        {"folder": folder, "name": name},
    )


@mcp.tool()
async def chaoxing_move_personal_group_folder(
    folder: str,
    destination_folder: str,
) -> dict[str, Any]:
    """Move a personal group folder under another folder or the root."""
    return await runtime.execute(
        "groups.folder.move",
        {"folder": folder, "destination_folder": destination_folder},
    )


@mcp.tool()
async def chaoxing_set_personal_group_folder_top_status(
    folder: str,
    top: bool,
) -> dict[str, Any]:
    """Set or clear one personal group folder's top status."""
    return await runtime.execute(
        "groups.folder.top_status.update",
        {"folder": folder, "top": top},
    )


@mcp.tool()
async def chaoxing_delete_personal_group_folder(
    folder: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting one personal group folder."""
    return await runtime.execute(
        "groups.folder.delete",
        {"folder": folder},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_personal_group_topics(
    group: str,
    folder: str = "",
    search: str = "",
) -> dict[str, Any]:
    """List or search topics inside one personal group."""
    return await runtime.execute(
        "groups.topics.list",
        {"group": group, "folder": folder, "search": search},
    )


@mcp.tool()
async def chaoxing_read_personal_group_topic(
    group: str,
    topic: str,
    order: int = 2,
    reply_search: str = "",
) -> dict[str, Any]:
    """Read one personal group topic and all of its replies."""
    return await runtime.execute(
        "groups.topic.read",
        {
            "group": group,
            "topic": topic,
            "order": order,
            "reply_search": reply_search,
        },
    )


@mcp.tool()
async def chaoxing_create_personal_group_topic(
    group: str,
    title: str,
    content: str,
    folder: str = "",
    anonymous: bool = False,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm publishing a topic inside one personal group."""
    return await runtime.execute(
        "groups.topic.create",
        {
            "group": group,
            "title": title,
            "content": content,
            "folder": folder,
            "anonymous": anonymous,
        },
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_update_personal_group_topic(
    group: str,
    topic: str,
    title: str | None = None,
    content: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm editing a personal group topic."""
    parameters: dict[str, Any] = {"group": group, "topic": topic}
    if title is not None:
        parameters["title"] = title
    if content is not None:
        parameters["content"] = content
    return await runtime.execute(
        "groups.topic.update",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_delete_personal_group_topic(
    group: str,
    topic: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting a personal group topic."""
    return await runtime.execute(
        "groups.topic.delete",
        {"group": group, "topic": topic},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_set_personal_group_topic_choice_status(
    group: str,
    topic: str,
    choice: bool,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm marking one personal group topic as choice or ordinary."""
    return await runtime.execute(
        "groups.topic.choice_status.update",
        {"group": group, "topic": topic, "choice": choice},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_set_personal_group_topic_praise_status(
    group: str,
    topic: str,
    praised: bool,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm praising or unpraising one personal group topic."""
    return await runtime.execute(
        "groups.topic.praise_status.update",
        {"group": group, "topic": topic, "praised": praised},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_set_personal_group_topics_score(
    group: str,
    topics: list[str],
    score: int,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm applying one score to selected personal group topics."""
    return await runtime.execute(
        "groups.topics.score.set",
        {"group": group, "topics": topics, "score": score},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_move_personal_group_topics(
    group: str,
    topics: list[str],
    destination_folder: str,
) -> dict[str, Any]:
    """Move selected personal group topics to one topic folder or the root."""
    return await runtime.execute(
        "groups.topics.move",
        {
            "group": group,
            "topics": topics,
            "destination_folder": destination_folder,
        },
    )


@mcp.tool()
async def chaoxing_delete_personal_group_topics(
    group: str,
    topics: list[str],
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting selected personal group topics in one batch."""
    return await runtime.execute(
        "groups.topics.delete",
        {"group": group, "topics": topics},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_create_personal_group_topic_reply(
    group: str,
    topic: str,
    content: str,
    reply_to: str = "",
    anonymous: bool = False,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm replying to a personal group topic or one reply."""
    return await runtime.execute(
        "groups.topic.reply.create",
        {
            "group": group,
            "topic": topic,
            "content": content,
            "reply_to": reply_to,
            "anonymous": anonymous,
        },
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_update_personal_group_topic_reply(
    group: str,
    topic: str,
    reply: str,
    content: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm editing a personal group topic reply."""
    return await runtime.execute(
        "groups.topic.reply.update",
        {"group": group, "topic": topic, "reply": reply, "content": content},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_delete_personal_group_topic_reply(
    group: str,
    topic: str,
    reply: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting a personal group topic reply."""
    return await runtime.execute(
        "groups.topic.reply.delete",
        {"group": group, "topic": topic, "reply": reply},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_read_personal_group_topic_folder_tree(group: str) -> dict[str, Any]:
    """Read the topic-folder tree inside one personal group."""
    return await runtime.execute(
        "groups.topic.folders.tree",
        {"group": group},
    )


@mcp.tool()
async def chaoxing_set_personal_group_topic_top_status(
    group: str,
    topic: str,
    top: bool,
) -> dict[str, Any]:
    """Set or clear one personal group topic's top status."""
    return await runtime.execute(
        "groups.topic.top_status.update",
        {"group": group, "topic": topic, "top": top},
    )


@mcp.tool()
async def chaoxing_move_personal_group_topic(
    group: str,
    topic: str,
    destination_folder: str,
) -> dict[str, Any]:
    """Move one personal group topic to a topic folder or the root."""
    return await runtime.execute(
        "groups.topic.move",
        {
            "group": group,
            "topic": topic,
            "destination_folder": destination_folder,
        },
    )


@mcp.tool()
async def chaoxing_create_personal_group_topic_folder(
    group: str,
    name: str,
    parent_folder: str = "",
) -> dict[str, Any]:
    """Create a topic folder inside one personal group."""
    return await runtime.execute(
        "groups.topic.folder.create",
        {"group": group, "name": name, "parent_folder": parent_folder},
    )


@mcp.tool()
async def chaoxing_rename_personal_group_topic_folder(
    group: str,
    folder: str,
    name: str,
) -> dict[str, Any]:
    """Rename a topic folder inside one personal group."""
    return await runtime.execute(
        "groups.topic.folder.rename",
        {"group": group, "folder": folder, "name": name},
    )


@mcp.tool()
async def chaoxing_move_personal_group_topic_folder(
    group: str,
    folder: str,
    destination_folder: str,
) -> dict[str, Any]:
    """Move a topic folder inside one personal group."""
    return await runtime.execute(
        "groups.topic.folder.move",
        {
            "group": group,
            "folder": folder,
            "destination_folder": destination_folder,
        },
    )


@mcp.tool()
async def chaoxing_delete_personal_group_topic_folder(
    group: str,
    folder: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting one topic folder inside a personal group."""
    return await runtime.execute(
        "groups.topic.folder.delete",
        {"group": group, "folder": folder},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_move_personal_group_topic_folders(
    group: str,
    folders: list[str],
    destination_folder: str,
) -> dict[str, Any]:
    """Move selected personal group topic folders to one parent folder or the root."""
    return await runtime.execute(
        "groups.topic.folders.move",
        {
            "group": group,
            "folders": folders,
            "destination_folder": destination_folder,
        },
    )


@mcp.tool()
async def chaoxing_delete_personal_group_topic_folders(
    group: str,
    folders: list[str],
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting selected personal group topic folders in one batch."""
    return await runtime.execute(
        "groups.topic.folders.delete",
        {"group": group, "folders": folders},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_personal_group_topic_drafts(
    group: str,
    search: str = "",
) -> dict[str, Any]:
    """List managed topic drafts and re-read each draft from Chaoxing."""
    return await runtime.execute(
        "groups.topic.drafts.list",
        {"group": group, "search": search},
    )


@mcp.tool()
async def chaoxing_read_personal_group_topic_draft(
    group: str,
    draft: str,
) -> dict[str, Any]:
    """Read one personal group topic draft by its server UUID."""
    return await runtime.execute(
        "groups.topic.draft.read",
        {"group": group, "draft": draft},
    )


@mcp.tool()
async def chaoxing_save_personal_group_topic_draft(
    group: str,
    title: str,
    content: str,
    draft: str = "",
    folder: str = "",
) -> dict[str, Any]:
    """Create or update an unpublished personal group topic draft."""
    return await runtime.execute(
        "groups.topic.draft.save",
        {
            "group": group,
            "title": title,
            "content": content,
            "draft": draft,
            "folder": folder,
        },
    )


@mcp.tool()
async def chaoxing_publish_personal_group_topic_draft(
    group: str,
    draft: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm publishing one personal group topic draft."""
    return await runtime.execute(
        "groups.topic.draft.publish",
        {"group": group, "draft": draft},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_teaching_courses() -> dict[str, Any]:
    """List courses where the current account is a teacher, including class summaries."""
    return await runtime.execute("courses.list_teaching")


@mcp.tool()
async def chaoxing_list_learning_courses(search: str = "") -> dict[str, Any]:
    """List courses joined by the current account as a learner."""
    return await runtime.execute("learning.courses.list", {"search": search})


@mcp.tool()
async def chaoxing_list_learning_course_modules(course: str) -> dict[str, Any]:
    """Discover learner-side entries for one joined course selected by name or ID."""
    return await runtime.execute(
        "learning.course.modules.discover",
        {"course": course},
    )


@mcp.tool()
async def chaoxing_open_learning_course_module(course: str, module: str) -> dict[str, Any]:
    """Read one learner-side course entry through authenticated HTTP."""
    return await runtime.execute(
        "learning.course.module.open",
        {"course": course, "module": module},
    )


@mcp.tool()
async def chaoxing_list_learning_activities(
    course: str,
    search: str = "",
    status: str = "all",
) -> dict[str, Any]:
    """List learner activities without entering or starting an activity."""
    return await runtime.execute(
        "learning.course.activities.list",
        {"course": course, "search": search, "status": status},
    )


@mcp.tool()
async def chaoxing_list_learning_chapters(course: str, search: str = "") -> dict[str, Any]:
    """List learner-visible chapters and pending task-point counts."""
    return await runtime.execute(
        "learning.course.chapters.list",
        {"course": course, "search": search},
    )


@mcp.tool()
async def chaoxing_list_learning_discussions(
    course: str,
    search: str = "",
    class_only: bool = False,
) -> dict[str, Any]:
    """List discussion topics visible to a learner in a course or the current class."""
    return await runtime.execute(
        "learning.course.discussions.list",
        {"course": course, "search": search, "class_only": class_only},
    )


@mcp.tool()
async def chaoxing_list_learning_homeworks(
    course: str,
    search: str = "",
    status: str = "",
) -> dict[str, Any]:
    """List learner homework without opening an assignment or creating answer state."""
    return await runtime.execute(
        "learning.course.homeworks.list",
        {"course": course, "search": search, "status": status},
    )


@mcp.tool()
async def chaoxing_list_learning_exams(
    course: str,
    search: str = "",
    status: str = "",
) -> dict[str, Any]:
    """List learner exams without entering an exam or starting a timer."""
    return await runtime.execute(
        "learning.course.exams.list",
        {"course": course, "search": search, "status": status},
    )


@mcp.tool()
async def chaoxing_list_learning_self_tests(
    course: str,
    search: str = "",
    status: str = "",
) -> dict[str, Any]:
    """List learner self-tests without creating, entering, or submitting one."""
    return await runtime.execute(
        "learning.course.self_tests.list",
        {"course": course, "search": search, "status": status},
    )


@mcp.tool()
async def chaoxing_list_learning_materials(
    course: str,
    folder: str = "",
    search: str = "",
) -> dict[str, Any]:
    """List learner-visible course materials or the contents of one first-level folder."""
    return await runtime.execute(
        "learning.course.materials.list",
        {"course": course, "folder": folder, "search": search},
    )


@mcp.tool()
async def chaoxing_list_learning_ai_tools(course: str) -> dict[str, Any]:
    """List tools currently exposed by a learner AI workbench."""
    return await runtime.execute("learning.course.ai_tools.list", {"course": course})


@mcp.tool()
async def chaoxing_read_learning_wrong_questions(course: str) -> dict[str, Any]:
    """Read the current wrong-question summary without entering a question."""
    return await runtime.execute(
        "learning.course.wrong_questions.summary",
        {"course": course},
    )


@mcp.tool()
async def chaoxing_read_learning_records(course: str) -> dict[str, Any]:
    """Read learner progress, score, attendance, points, and activity metrics."""
    return await runtime.execute("learning.course.records.read", {"course": course})


@mcp.tool()
async def chaoxing_read_learning_knowledge_graph(
    course: str,
    search: str = "",
    level: int | None = None,
) -> dict[str, Any]:
    """Read learner-visible graph nodes, relations, classifications, and display data."""
    return await runtime.execute(
        "learning.course.knowledge_graph.list",
        {"course": course, "search": search, "level": level},
    )


@mcp.tool()
async def chaoxing_read_learning_knowledge_graph_node(
    course: str,
    node: str,
) -> dict[str, Any]:
    """Read one learner-visible graph node by ID, name, or path."""
    return await runtime.execute(
        "learning.course.knowledge_graph.node.read",
        {"course": course, "node": node},
    )


@mcp.tool()
async def chaoxing_list_learning_knowledge_graph_models(
    course: str,
    search: str = "",
) -> dict[str, Any]:
    """List graph models currently visible to a learner in one course."""
    return await runtime.execute(
        "learning.course.knowledge_graph.models.list",
        {"course": course, "search": search},
    )


@mcp.tool()
async def chaoxing_read_learning_knowledge_graph_model(
    course: str,
    model: str,
) -> dict[str, Any]:
    """Read the hierarchy for one learner-visible course-graph model."""
    return await runtime.execute(
        "learning.course.knowledge_graph.model.read",
        {"course": course, "model": model},
    )


@mcp.tool()
async def chaoxing_read_learning_integrity(course: str) -> dict[str, Any]:
    """Read whether a joined course currently requires integrity acceptance."""
    return await runtime.execute(
        "learning.course.integrity.read",
        {"course": course},
    )


@mcp.tool()
async def chaoxing_accept_learning_integrity(
    course: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm accepting a joined course's online-learning commitment."""
    return await runtime.execute(
        "learning.course.integrity.accept",
        {"course": course},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_classes(course: str) -> dict[str, Any]:
    """List classes for one teaching course selected by name, index, or course ID."""
    return await runtime.execute("courses.list_classes", {"course": course})


@mcp.tool()
async def chaoxing_create_class(
    course: str,
    name: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm creating an empty class in a teaching course."""
    return await runtime.execute(
        "classes.create",
        {"course": course, "name": name},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_rename_class(
    course: str,
    clazz: str,
    name: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm renaming one course class."""
    return await runtime.execute(
        "class.rename",
        {"course": course, "clazz": clazz, "name": name},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_read_class_settings(
    course: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Read join, visibility, semester, limit, end-state, and video settings for a class."""
    parameters = {"course": course}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("class.settings.read", parameters)


@mcp.tool()
async def chaoxing_read_class_invitation(
    course: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Read a class invite code, validity, and QR-code URLs through HTTP."""
    parameters = {"course": course}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("class.invitation.read", parameters)


@mcp.tool()
async def chaoxing_update_class_settings(
    course: str,
    clazz: str | None = None,
    allow_student_join: bool | None = None,
    join_requires_approval: bool | None = None,
    unit_binding_requirement: str | None = None,
    allow_student_withdraw: bool | None = None,
    public_scope: str | None = None,
    student_limit: int | None = None,
    ended: bool | None = None,
    ignore_video_restrictions: bool | None = None,
    hidden_from_students: bool | None = None,
    semester_id: str | None = None,
    open_start: str | None = None,
    open_end: str | None = None,
    application_start: str | None = None,
    application_end: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm one or more class-setting changes; omitted fields stay unchanged."""
    parameters: dict[str, Any] = {"course": course}
    if clazz:
        parameters["clazz"] = clazz
    optional = {
        "allow_student_join": allow_student_join,
        "join_requires_approval": join_requires_approval,
        "unit_binding_requirement": unit_binding_requirement,
        "allow_student_withdraw": allow_student_withdraw,
        "public_scope": public_scope,
        "student_limit": student_limit,
        "ended": ended,
        "ignore_video_restrictions": ignore_video_restrictions,
        "hidden_from_students": hidden_from_students,
        "semester_id": semester_id,
        "open_start": open_start,
        "open_end": open_end,
        "application_start": application_start,
        "application_end": application_end,
    }
    parameters.update({key: value for key, value in optional.items() if value is not None})
    return await runtime.execute(
        "class.settings.update",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_delete_class(
    course: str,
    clazz: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting one course class."""
    return await runtime.execute(
        "class.delete",
        {"course": course, "clazz": clazz},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_class_students(
    course: str,
    clazz: str | None = None,
    search: str = "",
    school_status: int = 0,
) -> dict[str, Any]:
    """List students and identity metadata for one teaching class through HTTP."""
    parameters: dict[str, Any] = {
        "course": course,
        "search": search,
        "school_status": school_status,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("class.students.list", parameters)


@mcp.tool()
async def chaoxing_search_student_candidates(
    course: str,
    query: str,
    clazz: str | None = None,
    page: int = 1,
    page_size: int = 30,
) -> dict[str, Any]:
    """Search the school student bank for people available to add to one class."""
    parameters: dict[str, Any] = {
        "course": course,
        "query": query,
        "page": page,
        "page_size": page_size,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("class.student_candidates.search", parameters)


@mcp.tool()
async def chaoxing_add_student_from_bank(
    course: str,
    student: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm adding one selected student-bank candidate to a class."""
    parameters: dict[str, Any] = {"course": course, "student": student}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "class.student.add_from_bank",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_add_student_by_identity(
    course: str,
    name: str,
    identity: str,
    clazz: str | None = None,
    identity_type: str = "student_no",
    school_id: str = "",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm adding a student by name and student number, mobile, or email."""
    parameters: dict[str, Any] = {
        "course": course,
        "name": name,
        "identity": identity,
        "identity_type": identity_type,
        "school_id": school_id,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "class.student.add_by_identity",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_remove_student(
    course: str,
    student: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm removing one student from a class."""
    parameters: dict[str, Any] = {"course": course, "student": student}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "class.student.remove",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_class_join_applications(
    course: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """List pending requests to join one class by invitation code."""
    parameters: dict[str, Any] = {"course": course}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("class.join_applications.list", parameters)


@mcp.tool()
async def chaoxing_decide_class_join_application(
    course: str,
    application: str,
    decision: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm approving or rejecting one pending class-join request."""
    parameters: dict[str, Any] = {
        "course": course,
        "application": application,
        "decision": decision,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "class.join_application.decide",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_move_student(
    course: str,
    source_clazz: str,
    target_clazz: str,
    student: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm moving one student between classes in the same course."""
    return await runtime.execute(
        "class.student.move",
        {
            "course": course,
            "clazz": source_clazz,
            "target_clazz": target_clazz,
            "student": student,
        },
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_student_access_logs(
    course: str,
    student: str,
    year: int,
    month: int,
    clazz: str | None = None,
    day: int = 0,
) -> dict[str, Any]:
    """List one student's monthly or daily course access events through HTTP."""
    parameters: dict[str, Any] = {
        "course": course,
        "student": student,
        "year": year,
        "month": month,
        "day": day,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("class.student.access_logs.list", parameters)


@mcp.tool()
async def chaoxing_list_course_operation_logs(
    course: str,
    clazz: str | None = None,
    module: str = "",
    search: str = "",
    start_date: str = "",
    end_date: str = "",
) -> dict[str, Any]:
    """List teacher-side course operations with optional module, date, and text filters."""
    parameters: dict[str, Any] = {
        "course": course,
        "module": module,
        "search": search,
        "start_date": start_date,
        "end_date": end_date,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("course.operation_logs.list", parameters)


@mcp.tool()
async def chaoxing_list_student_join_logs(
    course: str,
    clazz: str | None = None,
    join_type: int = -1,
    search: str = "",
) -> dict[str, Any]:
    """List class-join records; type -1 all, 0 other, 1 teacher, 2 self, 3 SIS."""
    parameters: dict[str, Any] = {
        "course": course,
        "join_type": join_type,
        "search": search,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("class.student_join_logs.list", parameters)


@mcp.tool()
async def chaoxing_list_student_leave_logs(
    course: str,
    clazz: str | None = None,
    search: str = "",
) -> dict[str, Any]:
    """List students who left or were removed and their restorable record IDs."""
    parameters: dict[str, Any] = {"course": course, "search": search}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("class.student_leave_logs.list", parameters)


@mcp.tool()
async def chaoxing_restore_student(
    course: str,
    student: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm restoring a student from a leave record."""
    parameters: dict[str, Any] = {"course": course, "student": student}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "class.student.restore",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_course_teachers(
    course: str,
    clazz: str | None = None,
    search: str = "",
    role: int = 0,
) -> dict[str, Any]:
    """List the course creator, teachers, assistants, and their identity metadata."""
    parameters: dict[str, Any] = {"course": course, "search": search, "role": role}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("course.teachers.list", parameters)


@mcp.tool()
async def chaoxing_search_teacher_candidates(
    course: str,
    query: str,
    clazz: str | None = None,
    role: str = "teacher",
    page: int = 1,
) -> dict[str, Any]:
    """Search the school teacher bank for people available to add to a course team."""
    parameters: dict[str, Any] = {
        "course": course,
        "query": query,
        "role": role,
        "page": page,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("course.teacher_candidates.search", parameters)


@mcp.tool()
async def chaoxing_add_teacher_from_bank(
    course: str,
    teacher: str,
    clazz: str | None = None,
    role: str = "teacher",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm adding a teacher-bank candidate as a teacher or assistant."""
    parameters: dict[str, Any] = {"course": course, "teacher": teacher, "role": role}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "course.teacher.add_from_bank",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_add_teacher_by_identity(
    course: str,
    name: str,
    identity: str,
    clazz: str | None = None,
    identity_type: str = "employee_no",
    role: str = "teacher",
    school_id: str = "",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm adding a teacher or assistant by identity information."""
    parameters: dict[str, Any] = {
        "course": course,
        "name": name,
        "identity": identity,
        "identity_type": identity_type,
        "role": role,
        "school_id": school_id,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "course.teacher.add_by_identity",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_remove_course_teacher(
    course: str,
    teacher: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm removing one teacher or assistant from a course team."""
    parameters: dict[str, Any] = {"course": course, "teacher": teacher}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "course.teacher.remove",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_read_teacher_permissions(
    course: str,
    teacher: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Read one course-team member's role and current permission payload."""
    parameters: dict[str, Any] = {"course": course, "teacher": teacher}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("course.teacher.permissions.read", parameters)


@mcp.tool()
async def chaoxing_update_teacher_permissions(
    course: str,
    teacher: str,
    changes: dict[str, bool | int],
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm one or more permission changes for a course-team member."""
    parameters: dict[str, Any] = {
        "course": course,
        "teacher": teacher,
        "changes": changes,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "course.teacher.permissions.update",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_read_grade_weights(
    course: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Read the active grade-weight mode, component weights, and settings through HTTP."""
    parameters: dict[str, Any] = {"course": course}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("course.grade_weights.read", parameters)


@mcp.tool()
async def chaoxing_list_course_grades(
    course: str,
    clazz: str | None = None,
    search: str = "",
    raw_scores: bool = False,
    sort: str = "loginName",
    descending: bool = False,
) -> dict[str, Any]:
    """List final grades or raw component scores for every student in one class."""
    parameters: dict[str, Any] = {
        "course": course,
        "search": search,
        "raw_scores": raw_scores,
        "sort": sort,
        "descending": descending,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("course.grades.list", parameters)


@mcp.tool()
async def chaoxing_read_grade_visibility(
    course: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Read grade-visible classes, scheduled opening, rank, and class-average settings."""
    parameters: dict[str, Any] = {"course": course}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("course.grade_visibility.read", parameters)


@mcp.tool()
async def chaoxing_set_grade_visibility(
    course: str,
    visible_classes: list[str],
    clazz: str | None = None,
    scheduled_open: bool = False,
    open_at: str = "",
    students_can_view_rank: bool = False,
    students_can_view_class_average: bool = False,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm the complete class-level grade-visibility configuration."""
    parameters: dict[str, Any] = {
        "course": course,
        "visible_classes": visible_classes,
        "scheduled_open": scheduled_open,
        "open_at": open_at,
        "students_can_view_rank": students_can_view_rank,
        "students_can_view_class_average": students_can_view_class_average,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "course.grade_visibility.set",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_set_grade_override(
    course: str,
    student: str,
    score: float | None,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm a 0-100 final-grade override; null restores automatic calculation."""
    parameters: dict[str, Any] = {"course": course, "student": student, "score": score}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "course.grade_override.set",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_learning_progress(
    course: str,
    clazz: str | None = None,
    search: str = "",
    sort: str = "loginName",
    descending: bool = False,
) -> dict[str, Any]:
    """List task-point, viewing, quiz, homework, exam, and activity progress by student."""
    parameters: dict[str, Any] = {
        "course": course,
        "search": search,
        "sort": sort,
        "descending": descending,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("course.learning_progress.list", parameters)


@mcp.tool()
async def chaoxing_list_study_monitor(
    course: str,
    clazz: str | None = None,
    search: str = "",
    only_abnormal: bool = False,
    anomaly_type: int = 0,
) -> dict[str, Any]:
    """List study-monitor records; anomaly_type is 0 all, 1 video, 2 homework, or 4 exam."""
    parameters: dict[str, Any] = {
        "course": course,
        "search": search,
        "only_abnormal": only_abnormal,
        "anomaly_type": anomaly_type,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("course.study_monitor.list", parameters)


@mcp.tool()
async def chaoxing_send_study_monitor_reminder(
    course: str,
    student: str,
    title: str,
    content: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm an abnormal-study reminder to one student."""
    parameters = {
        "course": course,
        "student": student,
        "title": title,
        "content": content,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "course.study_monitor.remind",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_clear_study_monitor_anomaly(
    course: str,
    student: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm clearing one student's removable study-anomaly record."""
    parameters = {"course": course, "student": student}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "course.study_monitor.clear",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_discover_course_modules(course: str, clazz: str | None = None) -> dict[str, Any]:
    """Read the live teacher-course function entries through authenticated HTTP."""
    parameters = {"course": course}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("course.modules.discover", parameters)


@mcp.tool()
async def chaoxing_open_course_module(
    course: str, module: str, clazz: str | None = None
) -> dict[str, Any]:
    """Fetch a course module such as 作业 or 考试 through HTTP, without opening a browser."""
    parameters = {"course": course, "module": module}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("course.module.open", parameters)


@mcp.tool()
async def chaoxing_read_knowledge_hub_status(
    course: str, clazz: str | None = None
) -> dict[str, Any]:
    """Read the course AI knowledge-hub module status and dictionaries without a browser."""
    parameters = {"course": course}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_hub.status.read", parameters)


@mcp.tool()
async def chaoxing_list_knowledge_hub_bases(
    course: str,
    clazz: str | None = None,
    module: str = "NORMAL_BASE",
    page: int = 1,
    page_size: int = 100,
    category: int = -1,
    state: int = -1,
    creator: str = "",
    search: str = "",
    begin_time: str = "",
    end_time: str = "",
) -> dict[str, Any]:
    """List the course AI knowledge bases with live filters and stable IDs."""
    parameters: dict[str, Any] = {
        "course": course,
        "module": module,
        "page": page,
        "page_size": page_size,
        "category": category,
        "state": state,
        "creator": creator,
        "search": search,
        "begin_time": begin_time,
        "end_time": end_time,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_hub.bases.list", parameters)


@mcp.tool()
async def chaoxing_read_knowledge_hub_base(
    course: str,
    base: str,
    clazz: str | None = None,
    module: str = "NORMAL_BASE",
) -> dict[str, Any]:
    """Read one AI knowledge base by stable ID or unambiguous current name."""
    parameters = {"course": course, "base": base, "module": module}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_hub.base.read", parameters)


@mcp.tool()
async def chaoxing_read_knowledge_hub_statistics(
    course: str,
    clazz: str | None = None,
    module: str = "NORMAL_BASE",
) -> dict[str, Any]:
    """Read live file and segmentation statistics for an AI knowledge-hub module."""
    parameters = {"course": course, "module": module}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_hub.statistics.read", parameters)


@mcp.tool()
async def chaoxing_create_knowledge_hub_base(
    course: str,
    name: str,
    description: str,
    clazz: str | None = None,
    category: int = 0,
    cover: str = "",
    split_rule: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a private course AI knowledge base and verify its new stable ID."""
    parameters: dict[str, Any] = {
        "course": course,
        "name": name,
        "description": description,
        "category": category,
        "cover": cover,
    }
    if split_rule is not None:
        parameters["split_rule"] = split_rule
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_hub.base.create", parameters)


@mcp.tool()
async def chaoxing_update_knowledge_hub_base(
    course: str,
    base: str,
    clazz: str | None = None,
    name: str | None = None,
    description: str | None = None,
    cover: str | None = None,
    split_rule: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Update an AI knowledge base and verify the persisted fields."""
    parameters: dict[str, Any] = {"course": course, "base": base}
    optional = {
        "name": name,
        "description": description,
        "cover": cover,
        "split_rule": split_rule,
    }
    parameters.update({key: value for key, value in optional.items() if value is not None})
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_hub.base.update", parameters)


@mcp.tool()
async def chaoxing_set_knowledge_hub_base_availability(
    course: str,
    base: str,
    enabled: bool,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Enable or disable one AI knowledge base and re-read its state."""
    parameters = {"course": course, "base": base, "enabled": enabled}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_hub.base.availability.update", parameters)


@mcp.tool()
async def chaoxing_set_knowledge_hub_base_priority(
    course: str,
    base: str,
    priority: bool,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Set or clear one AI knowledge base's priority state."""
    parameters = {"course": course, "base": base, "priority": priority}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_hub.base.priority.update", parameters)


@mcp.tool()
async def chaoxing_set_knowledge_hub_base_share(
    course: str,
    base: str,
    shared: bool,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm sharing or unsharing one course AI knowledge base."""
    parameters = {"course": course, "base": base, "shared": shared}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_hub.base.share.update", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_delete_knowledge_hub_base(
    course: str,
    base: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm permanently deleting a non-default AI knowledge base."""
    parameters = {"course": course, "base": base}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_hub.base.delete", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_list_knowledge_hub_documents(
    course: str,
    base: str,
    clazz: str | None = None,
    page: int = 1,
    page_size: int = 100,
    state: str = "",
    source: str = "",
    search: str = "",
    classify_id: str = "",
    file_type: str = "",
    begin_time: str = "",
    end_time: str = "",
    order: str = "",
) -> dict[str, Any]:
    """List documents in one AI knowledge base with live filters."""
    parameters: dict[str, Any] = {
        "course": course,
        "base": base,
        "page": page,
        "page_size": page_size,
        "state": state,
        "source": source,
        "search": search,
        "classify_id": classify_id,
        "file_type": file_type,
        "begin_time": begin_time,
        "end_time": end_time,
        "order": order,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_hub.documents.list", parameters)


@mcp.tool()
async def chaoxing_download_knowledge_hub_document(
    course: str,
    base: str,
    document: str,
    output_path: str,
    clazz: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Download one AI knowledge-base document through HTTP without a browser."""
    parameters = {
        "course": course,
        "base": base,
        "document": document,
        "output_path": output_path,
        "overwrite": overwrite,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_hub.document.download", parameters)


@mcp.tool()
async def chaoxing_upload_knowledge_hub_document(
    course: str,
    base: str,
    file: str,
    clazz: str | None = None,
    classify_id: str = "",
    split_rule: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Upload and register one local file in a course AI knowledge base."""
    parameters: dict[str, Any] = {
        "course": course,
        "base": base,
        "file": file,
        "classify_id": classify_id,
    }
    if split_rule is not None:
        parameters["split_rule"] = split_rule
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_hub.document.upload", parameters)


@mcp.tool()
async def chaoxing_delete_knowledge_hub_document(
    course: str,
    base: str,
    document: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm permanently deleting one AI knowledge-base document."""
    parameters = {"course": course, "base": base, "document": document}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_hub.document.delete", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_list_ai_command_groups(course: str, clazz: str | None = None) -> dict[str, Any]:
    """List the current course AI-workbench command groups in their live order."""
    parameters = {"course": course}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("ai_workbench.groups.list", parameters)


@mcp.tool()
async def chaoxing_create_ai_command_group(
    course: str,
    name: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm creating a course AI command group."""
    parameters = {"course": course, "name": name}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("ai_workbench.group.create", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_rename_ai_command_group(
    course: str,
    group: str,
    name: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm renaming a custom AI command group."""
    parameters = {"course": course, "group": group, "name": name}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("ai_workbench.group.rename", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_reorder_ai_command_groups(
    course: str,
    groups: list[str],
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm a complete AI command-group order, including group 0."""
    parameters: dict[str, Any] = {"course": course, "groups": groups}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("ai_workbench.group.reorder", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_delete_ai_command_group(
    course: str,
    group: str,
    clazz: str | None = None,
    allow_nonempty: bool = False,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting a custom AI command group."""
    parameters: dict[str, Any] = {
        "course": course,
        "group": group,
        "allow_nonempty": allow_nonempty,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("ai_workbench.group.delete", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_list_ai_commands(
    course: str,
    clazz: str | None = None,
    group: str = "",
    search: str = "",
) -> dict[str, Any]:
    """List deduplicated system, custom, and mapped AI commands."""
    parameters = {"course": course, "group": group, "search": search}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("ai_workbench.commands.list", parameters)


@mcp.tool()
async def chaoxing_read_ai_command(
    course: str,
    command: str,
    clazz: str | None = None,
    group: str = "",
) -> dict[str, Any]:
    """Read one AI command by stable ID or an unambiguous current name."""
    parameters = {"course": course, "command": command, "group": group}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("ai_workbench.command.read", parameters)


@mcp.tool()
async def chaoxing_create_ai_command(
    course: str,
    group: str,
    name: str,
    content: str,
    explanation: str,
    clazz: str | None = None,
    prompt_words: str = "",
    role_type: int = 0,
    classify_id: int = 1,
    command_ability: int = 0,
    ability_type: int = 0,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm creating an unpublished course AI command."""
    parameters: dict[str, Any] = {
        "course": course,
        "group": group,
        "name": name,
        "content": content,
        "explanation": explanation,
        "prompt_words": prompt_words,
        "role_type": role_type,
        "classify_id": classify_id,
        "command_ability": command_ability,
        "ability_type": ability_type,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("ai_workbench.command.create", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_update_ai_command(
    course: str,
    command: str,
    clazz: str | None = None,
    group: str = "",
    name: str | None = None,
    content: str | None = None,
    explanation: str | None = None,
    prompt_words: str | None = None,
    role_type: int | None = None,
    classify_id: int | None = None,
    command_ability: int | None = None,
    ability_type: int | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm updating a custom AI command or a mapped command's role."""
    parameters: dict[str, Any] = {"course": course, "command": command, "group": group}
    optional = {
        "name": name,
        "content": content,
        "explanation": explanation,
        "prompt_words": prompt_words,
        "role_type": role_type,
        "classify_id": classify_id,
        "command_ability": command_ability,
        "ability_type": ability_type,
    }
    parameters.update({key: value for key, value in optional.items() if value is not None})
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("ai_workbench.command.update", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_move_ai_command(
    course: str,
    command: str,
    target_group: str,
    clazz: str | None = None,
    group: str = "",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm moving an AI command to another group."""
    parameters = {
        "course": course,
        "command": command,
        "target_group": target_group,
        "group": group,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("ai_workbench.command.move", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_reorder_ai_commands(
    course: str,
    group: str,
    role_type: int,
    commands: list[str],
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm a complete teacher or student AI-command order."""
    parameters: dict[str, Any] = {
        "course": course,
        "group": group,
        "role_type": role_type,
        "commands": commands,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("ai_workbench.command.reorder", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_set_ai_command_publish_status(
    course: str,
    command: str,
    published: bool,
    clazz: str | None = None,
    group: str = "",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm publishing to all internet users, or unpublishing, an AI command."""
    parameters = {
        "course": course,
        "command": command,
        "published": published,
        "group": group,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "ai_workbench.command.publish_status.update", parameters, confirmation_token
    )


@mcp.tool()
async def chaoxing_delete_ai_command(
    course: str,
    command: str,
    clazz: str | None = None,
    group: str = "",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting a custom command or removing a mapped command."""
    parameters = {"course": course, "command": command, "group": group}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("ai_workbench.command.delete", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_list_ai_command_recommendations(
    course: str,
    clazz: str | None = None,
    page: int = 1,
) -> dict[str, Any]:
    """List one page of AI-open-platform command recommendations."""
    parameters: dict[str, Any] = {"course": course, "page": page}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("ai_workbench.recommendations.list", parameters)


@mcp.tool()
async def chaoxing_add_ai_command_recommendation(
    course: str,
    recommendation: str,
    group: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm mapping a recommended AI command into a course group."""
    parameters = {
        "course": course,
        "recommendation": recommendation,
        "group": group,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("ai_workbench.recommendation.add", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_list_task_engine_folders(
    course: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """List task-engine folders by stable ID and current name."""
    parameters = {"course": course}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("task_engine.folders.list", parameters)


@mcp.tool()
async def chaoxing_list_task_engine_tasks(
    course: str,
    clazz: str | None = None,
    folder: str = "",
    search: str = "",
    recycled: bool = False,
    max_items: int = 1000,
) -> dict[str, Any]:
    """List or search active or recycled task-engine tasks."""
    parameters: dict[str, Any] = {
        "course": course,
        "folder": folder,
        "search": search,
        "recycled": recycled,
        "max_items": max_items,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("task_engine.tasks.list", parameters)


@mcp.tool()
async def chaoxing_read_task_engine_task(
    course: str,
    task: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Read one task-engine task and all of its task points."""
    parameters = {"course": course, "task": task}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("task_engine.task.read", parameters)


@mcp.tool()
async def chaoxing_create_task_engine_folder(
    course: str,
    name: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Create a task-engine folder and verify its stable ID."""
    parameters = {"course": course, "name": name}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("task_engine.folder.create", parameters)


@mcp.tool()
async def chaoxing_rename_task_engine_folder(
    course: str,
    folder: str,
    name: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Rename a task-engine folder and verify it by stable ID."""
    parameters = {"course": course, "folder": folder, "name": name}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("task_engine.folder.rename", parameters)


@mcp.tool()
async def chaoxing_delete_task_engine_folder(
    course: str,
    folder: str,
    clazz: str | None = None,
    allow_nonempty: bool = False,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting a task-engine folder; contained tasks move to root."""
    parameters: dict[str, Any] = {
        "course": course,
        "folder": folder,
        "allow_nonempty": allow_nonempty,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("task_engine.folder.delete", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_create_task_engine_task(
    course: str,
    name: str,
    clazz: str | None = None,
    folder: str = "",
    introduce: str = "",
    rich_text: str = "",
    cover: str = "",
    target: str = "",
    selected_modes: list[str] | None = None,
) -> dict[str, Any]:
    """Create an unpublished task-engine task and verify its full record."""
    parameters: dict[str, Any] = {
        "course": course,
        "name": name,
        "folder": folder,
        "introduce": introduce,
        "rich_text": rich_text,
        "cover": cover,
        "target": target,
    }
    if selected_modes is not None:
        parameters["selected_modes"] = selected_modes
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("task_engine.task.create", parameters)


@mcp.tool()
async def chaoxing_update_task_engine_task(
    course: str,
    task: str,
    clazz: str | None = None,
    name: str | None = None,
    introduce: str | None = None,
    rich_text: str | None = None,
    cover: str | None = None,
    target: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    selected_modes: list[str] | None = None,
) -> dict[str, Any]:
    """Update selected task-engine task fields and verify the current task."""
    parameters: dict[str, Any] = {"course": course, "task": task}
    optional: dict[str, Any] = {
        "name": name,
        "introduce": introduce,
        "rich_text": rich_text,
        "cover": cover,
        "target": target,
        "start_date": start_date,
        "end_date": end_date,
        "selected_modes": selected_modes,
    }
    parameters.update({key: value for key, value in optional.items() if value is not None})
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("task_engine.task.update", parameters)


@mcp.tool()
async def chaoxing_move_task_engine_task(
    course: str,
    task: str,
    clazz: str | None = None,
    folder: str = "",
) -> dict[str, Any]:
    """Move a task-engine task to a folder or to root and verify its parent."""
    parameters = {"course": course, "task": task, "folder": folder}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("task_engine.task.move", parameters)


@mcp.tool()
async def chaoxing_reorder_task_engine_items(
    course: str,
    task_order: list[str],
    clazz: str | None = None,
    folder: str = "",
    folder_order: list[str] | None = None,
) -> dict[str, Any]:
    """Set a complete task order and optionally the complete root-folder order."""
    parameters: dict[str, Any] = {
        "course": course,
        "folder": folder,
        "task_order": task_order,
    }
    if folder_order is not None:
        parameters["folder_order"] = folder_order
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("task_engine.order.update", parameters)


@mcp.tool()
async def chaoxing_copy_task_engine_task(
    course: str,
    task: str,
    clazz: str | None = None,
    name: str = "",
    folder: str = "",
) -> dict[str, Any]:
    """Copy a task-engine task and verify the new stable ID."""
    parameters = {
        "course": course,
        "task": task,
        "name": name,
        "folder": folder,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("task_engine.task.copy", parameters)


@mcp.tool()
async def chaoxing_delete_task_engine_task(
    course: str,
    task: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm moving a task-engine task to recycle."""
    parameters = {"course": course, "task": task}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("task_engine.task.delete", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_list_task_engine_recycle(
    course: str,
    clazz: str | None = None,
    search: str = "",
    max_items: int = 1000,
) -> dict[str, Any]:
    """List or search task-engine recycle items."""
    parameters: dict[str, Any] = {
        "course": course,
        "search": search,
        "max_items": max_items,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("task_engine.recycle.list", parameters)


@mcp.tool()
async def chaoxing_restore_task_engine_task(
    course: str,
    task: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Restore a task-engine task from recycle and verify it is active."""
    parameters = {"course": course, "task": task}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("task_engine.task.restore", parameters)


@mcp.tool()
async def chaoxing_list_task_engine_labels(
    course: str,
    clazz: str | None = None,
    task: str = "",
    search: str = "",
) -> dict[str, Any]:
    """List or search task-engine labels, optionally in one task's context."""
    parameters = {"course": course, "task": task, "search": search}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("task_engine.labels.list", parameters)


@mcp.tool()
async def chaoxing_create_task_engine_label(
    course: str,
    name: str,
    clazz: str | None = None,
    task: str = "",
) -> dict[str, Any]:
    """Create a task-engine label and verify its stable ID."""
    parameters = {"course": course, "task": task, "name": name}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("task_engine.label.create", parameters)


@mcp.tool()
async def chaoxing_rename_task_engine_label(
    course: str,
    label: str,
    name: str,
    clazz: str | None = None,
    task: str = "",
) -> dict[str, Any]:
    """Ask the server to rename a task-engine label and verify the current name."""
    parameters = {
        "course": course,
        "task": task,
        "label": label,
        "name": name,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("task_engine.label.rename", parameters)


@mcp.tool()
async def chaoxing_delete_task_engine_label(
    course: str,
    label: str,
    clazz: str | None = None,
    task: str = "",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting a task-engine label, subject to server permission."""
    parameters = {"course": course, "task": task, "label": label}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("task_engine.label.delete", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_request_task_engine_export(
    course: str,
    clazz: str | None = None,
    tasks: list[str] | None = None,
    folder: str = "",
) -> dict[str, Any]:
    """Request an export for selected tasks, a folder, or all visible tasks."""
    parameters: dict[str, Any] = {"course": course, "folder": folder}
    if tasks is not None:
        parameters["tasks"] = tasks
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("task_engine.export.request", parameters)


@mcp.tool()
async def chaoxing_set_task_engine_publish_status(
    course: str,
    task: str,
    published: bool,
    clazz: str | None = None,
    course_publish_param: list[dict[str, Any]] | None = None,
    task_publish_param: list[dict[str, Any]] | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm publishing to selected learners, or unpublishing, a task."""
    parameters: dict[str, Any] = {
        "course": course,
        "task": task,
        "published": published,
    }
    if course_publish_param is not None:
        parameters["course_publish_param"] = course_publish_param
    if task_publish_param is not None:
        parameters["task_publish_param"] = task_publish_param
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "task_engine.publish_status.update", parameters, confirmation_token
    )


@mcp.tool()
async def chaoxing_read_knowledge_graph(
    course: str,
    clazz: str | None = None,
    search: str = "",
    level: int | None = None,
) -> dict[str, Any]:
    """Read graph configuration, nodes, paths, relations, labels, and styles."""
    parameters: dict[str, Any] = {"course": course, "search": search}
    if level is not None:
        parameters["level"] = level
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.graph.read", parameters)


@mcp.tool()
async def chaoxing_read_knowledge_graph_node(
    course: str,
    node: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Read one graph node by stable ID, name, or path and include its relations."""
    parameters = {"course": course, "node": node}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.node.read", parameters)


@mcp.tool()
async def chaoxing_create_knowledge_graph_node(
    course: str,
    name: str,
    node_type: str = "knowledge",
    parent: str = "",
    description: str = "",
    model: str = "",
    clazz: str | None = None,
) -> dict[str, Any]:
    """Create a category, knowledge point, or ability point under an optional parent."""
    parameters = {
        "course": course,
        "name": name,
        "node_type": node_type,
        "parent": parent,
        "description": description,
        "model": model,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.node.create", parameters)


@mcp.tool()
async def chaoxing_update_knowledge_graph_node(
    course: str,
    node: str,
    name: str,
    description: str = "",
    clazz: str | None = None,
) -> dict[str, Any]:
    """Update any non-root graph node's name and description by stable ID or path."""
    parameters = {
        "course": course,
        "node": node,
        "name": name,
        "description": description,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.node.update", parameters)


@mcp.tool()
async def chaoxing_read_knowledge_graph_node_relations(
    course: str,
    node: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Read predecessor, successor, association, and custom relations for one node."""
    parameters = {"course": course, "node": node}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.node.relations.read", parameters)


@mcp.tool()
async def chaoxing_add_knowledge_graph_node_relation(
    course: str,
    node: str,
    relation: str,
    target: str,
    description: str = "",
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm adding a built-in or custom relation between graph nodes."""
    parameters = {
        "course": course,
        "node": node,
        "relation": relation,
        "target": target,
        "description": description,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "knowledge_graph.node.relation.add", parameters, confirmation_token
    )


@mcp.tool()
async def chaoxing_remove_knowledge_graph_node_relation(
    course: str,
    node: str,
    relation: str,
    target: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm removing one relation while preserving every other relation."""
    parameters = {
        "course": course,
        "node": node,
        "relation": relation,
        "target": target,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "knowledge_graph.node.relation.remove", parameters, confirmation_token
    )


@mcp.tool()
async def chaoxing_read_knowledge_graph_settings(
    course: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Read the current student-visible course-graph display settings."""
    parameters = {"course": course}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.settings.read", parameters)


@mcp.tool()
async def chaoxing_update_knowledge_graph_settings(
    course: str,
    clazz: str | None = None,
    show_all_relations: bool | None = None,
    show_all_topic_names: bool | None = None,
    navigation_node_scale: bool | None = None,
    graph_background_color: bool | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm changing student-visible course-graph display settings."""
    parameters: dict[str, Any] = {"course": course}
    for key, value in (
        ("show_all_relations", show_all_relations),
        ("show_all_topic_names", show_all_topic_names),
        ("navigation_node_scale", navigation_node_scale),
        ("graph_background_color", graph_background_color),
    ):
        if value is not None:
            parameters[key] = value
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.settings.update", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_read_knowledge_graph_advanced_settings(
    course: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Read course-graph card, target, study-hour, relation, self-test, and micro settings."""
    parameters = {"course": course}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.advanced_settings.read", parameters)


@mcp.tool()
async def chaoxing_update_knowledge_graph_advanced_settings(
    course: str,
    clazz: str | None = None,
    topic_card: bool | None = None,
    teach_target: bool | None = None,
    study_hours_enabled: bool | None = None,
    classify_relation_data: bool | None = None,
    selftest_included: bool | None = None,
    micro_preview: bool | None = None,
    micro_scale_mode: bool | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm changing selected student-visible advanced graph settings."""
    parameters: dict[str, Any] = {"course": course}
    for key, value in (
        ("topic_card", topic_card),
        ("teach_target", teach_target),
        ("study_hours_enabled", study_hours_enabled),
        ("classify_relation_data", classify_relation_data),
        ("selftest_included", selftest_included),
        ("micro_preview", micro_preview),
        ("micro_scale_mode", micro_scale_mode),
    ):
        if value is not None:
            parameters[key] = value
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "knowledge_graph.advanced_settings.update", parameters, confirmation_token
    )


@mcp.tool()
async def chaoxing_list_knowledge_graph_models(
    course: str,
    clazz: str | None = None,
    search: str = "",
) -> dict[str, Any]:
    """List graph models, their stable IDs, order, mode, style, and visibility."""
    parameters = {"course": course, "search": search}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.models.list", parameters)


@mcp.tool()
async def chaoxing_read_knowledge_graph_model_data(
    course: str,
    model: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Read the model-specific graph tree and flattened node paths."""
    parameters = {"course": course, "model": model}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.model.data.read", parameters)


@mcp.tool()
async def chaoxing_create_knowledge_graph_model(
    course: str,
    name: str,
    style: int = 0,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Create a custom course-graph model."""
    parameters = {"course": course, "name": name, "style": style}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.model.create", parameters)


@mcp.tool()
async def chaoxing_update_knowledge_graph_model(
    course: str,
    model: str,
    name: str,
    style: int | None = None,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Update a course-graph model name and optional style."""
    parameters = {"course": course, "model": model, "name": name}
    if style is not None:
        parameters["style"] = style
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.model.update", parameters)


@mcp.tool()
async def chaoxing_set_knowledge_graph_model_visibility(
    course: str,
    model: str,
    visible: bool,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm showing or hiding a graph model for learners."""
    parameters = {"course": course, "model": model, "visible": visible}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "knowledge_graph.model.visibility.update", parameters, confirmation_token
    )


@mcp.tool()
async def chaoxing_reorder_knowledge_graph_models(
    course: str,
    models: list[str],
    clazz: str | None = None,
) -> dict[str, Any]:
    """Set the complete graph-model order."""
    parameters = {"course": course, "models": models}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.models.reorder", parameters)


@mcp.tool()
async def chaoxing_delete_knowledge_graph_model(
    course: str,
    model: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting a non-default graph model."""
    parameters = {"course": course, "model": model}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.model.delete", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_list_knowledge_graph_model_classes(
    course: str,
    model: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """List class visibility for a graph model."""
    parameters = {"course": course, "model": model}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.model.classes.list", parameters)


@mcp.tool()
async def chaoxing_update_knowledge_graph_model_classes(
    course: str,
    model: str,
    visible_classes: list[str],
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm the complete learner-visible class set for a graph model."""
    parameters = {
        "course": course,
        "model": model,
        "visible_classes": visible_classes,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "knowledge_graph.model.classes.update", parameters, confirmation_token
    )


@mcp.tool()
async def chaoxing_list_knowledge_graph_events(
    course: str,
    clazz: str | None = None,
    search: str = "",
) -> dict[str, Any]:
    """List graph task events, trigger conditions, labels, and execution modules."""
    parameters = {"course": course, "search": search}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.events.list", parameters)


@mcp.tool()
async def chaoxing_create_knowledge_graph_event(
    course: str,
    name: str,
    topic_condition: int | str,
    set_condition: int | str,
    percent1: int,
    executions: list[dict[str, Any]],
    percent2: int = 100,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm creating an active graph task event.

    topic_condition accepts 0/mastery or 1/completion. set_condition accepts
    0 equal, 1 greater-than, 2 less-than, 3 greater-or-equal,
    4 less-or-equal, or 7 between. Each of 1-3 executions supplies a label
    and execute_module=learning_path/0 or microcourse_resources/1.
    """
    parameters: dict[str, Any] = {
        "course": course,
        "name": name,
        "topic_condition": topic_condition,
        "set_condition": set_condition,
        "percent1": percent1,
        "percent2": percent2,
        "executions": executions,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.event.create", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_update_knowledge_graph_event(
    course: str,
    event: str,
    clazz: str | None = None,
    name: str | None = None,
    topic_condition: int | str | None = None,
    set_condition: int | str | None = None,
    percent1: int | None = None,
    percent2: int | None = None,
    executions: list[dict[str, Any]] | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm updating selected fields of an active graph task event."""
    parameters: dict[str, Any] = {"course": course, "event": event}
    for key, value in (
        ("name", name),
        ("topic_condition", topic_condition),
        ("set_condition", set_condition),
        ("percent1", percent1),
        ("percent2", percent2),
        ("executions", executions),
    ):
        if value is not None:
            parameters[key] = value
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.event.update", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_delete_knowledge_graph_event(
    course: str,
    event: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting an active graph task event."""
    parameters = {"course": course, "event": event}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.event.delete", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_download_knowledge_graph_export(
    course: str,
    export_format: str,
    output_path: str,
    model: str = "",
    clazz: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Export a graph model as xmind, excel/xlsx, csv, psg/json, pdf, or rdf."""
    parameters = {
        "course": course,
        "format": export_format,
        "output_path": output_path,
        "model": model,
        "overwrite": overwrite,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.export.download", parameters)


@mcp.tool()
async def chaoxing_list_knowledge_graph_relation_types(
    course: str,
    clazz: str | None = None,
    search: str = "",
) -> dict[str, Any]:
    """List built-in and custom graph relation definitions and visual styles."""
    parameters = {"course": course, "search": search}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.relation_types.list", parameters)


@mcp.tool()
async def chaoxing_create_knowledge_graph_relation_type(
    course: str,
    name: str,
    clazz: str | None = None,
    meaning: str = "",
    relation_types: list[int] | None = None,
    example_html: str = "",
    color: str = "",
) -> dict[str, Any]:
    """Create and verify a custom graph relation definition."""
    parameters: dict[str, Any] = {
        "course": course,
        "name": name,
        "meaning": meaning,
        "example_html": example_html,
        "color": color,
    }
    if relation_types is not None:
        parameters["relation_types"] = relation_types
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.relation_type.create", parameters)


@mcp.tool()
async def chaoxing_update_knowledge_graph_relation_type(
    course: str,
    relation: str,
    clazz: str | None = None,
    name: str | None = None,
    meaning: str | None = None,
    relation_types: list[int] | None = None,
    example_html: str | None = None,
    color: str | None = None,
    arrow_size: int | None = None,
    line_thickness: int | None = None,
) -> dict[str, Any]:
    """Update selected fields of a custom graph relation definition."""
    parameters: dict[str, Any] = {"course": course, "relation": relation}
    for key, value in (
        ("name", name),
        ("meaning", meaning),
        ("relation_types", relation_types),
        ("example_html", example_html),
        ("color", color),
        ("arrow_size", arrow_size),
        ("line_thickness", line_thickness),
    ):
        if value is not None:
            parameters[key] = value
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.relation_type.update", parameters)


@mcp.tool()
async def chaoxing_delete_knowledge_graph_relation_type(
    course: str,
    relation: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting a custom graph relation definition."""
    parameters = {"course": course, "relation": relation}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "knowledge_graph.relation_type.delete", parameters, confirmation_token
    )


@mcp.tool()
async def chaoxing_create_knowledge_graph_category(
    course: str,
    name: str,
    clazz: str | None = None,
    description: str = "",
) -> dict[str, Any]:
    """Create and verify a top-level course-graph category."""
    parameters = {"course": course, "name": name, "description": description}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.category.create", parameters)


@mcp.tool()
async def chaoxing_update_knowledge_graph_category(
    course: str,
    node: str,
    name: str,
    clazz: str | None = None,
    description: str = "",
) -> dict[str, Any]:
    """Update a course-graph category's name and description by stable node ID."""
    parameters = {
        "course": course,
        "node": node,
        "name": name,
        "description": description,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.category.update", parameters)


@mcp.tool()
async def chaoxing_delete_knowledge_graph_node(
    course: str,
    node: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting a graph node and its parent-child descendants."""
    parameters = {"course": course, "node": node}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.node.delete", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_list_knowledge_graph_labels(
    course: str,
    clazz: str | None = None,
    search: str = "",
) -> dict[str, Any]:
    """List graph label groups, labels, preset flags, IDs, and order."""
    parameters = {"course": course, "search": search}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.labels.list", parameters)


@mcp.tool()
async def chaoxing_create_knowledge_graph_label_group(
    course: str,
    name: str,
    clazz: str | None = None,
    group_type: int = 0,
) -> dict[str, Any]:
    """Create a custom, knowledge-type, or cognitive-dimension graph label group."""
    parameters = {"course": course, "name": name, "group_type": group_type}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.label_group.create", parameters)


@mcp.tool()
async def chaoxing_rename_knowledge_graph_label_group(
    course: str,
    group: str,
    name: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Rename and verify a course-graph label group."""
    parameters = {"course": course, "group": group, "name": name}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.label_group.rename", parameters)


@mcp.tool()
async def chaoxing_delete_knowledge_graph_label_group(
    course: str,
    group: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting a non-default graph label group and its labels."""
    parameters = {"course": course, "group": group}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "knowledge_graph.label_group.delete", parameters, confirmation_token
    )


@mcp.tool()
async def chaoxing_reorder_knowledge_graph_label_groups(
    course: str,
    groups: list[str],
    clazz: str | None = None,
) -> dict[str, Any]:
    """Set the complete course-graph label-group order."""
    parameters = {"course": course, "groups": groups}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.label_groups.reorder", parameters)


@mcp.tool()
async def chaoxing_create_knowledge_graph_label(
    course: str,
    group: str,
    name: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Create and verify a label inside one graph label group."""
    parameters = {"course": course, "group": group, "name": name}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.label.create", parameters)


@mcp.tool()
async def chaoxing_rename_knowledge_graph_label(
    course: str,
    label: str,
    name: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Rename and verify a non-preset graph label."""
    parameters = {"course": course, "label": label, "name": name}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.label.rename", parameters)


@mcp.tool()
async def chaoxing_move_knowledge_graph_label(
    course: str,
    label: str,
    group: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Move a graph label into another group and verify its new group."""
    parameters = {"course": course, "label": label, "group": group}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.label.move", parameters)


@mcp.tool()
async def chaoxing_reorder_knowledge_graph_labels(
    course: str,
    group: str,
    labels: list[str],
    clazz: str | None = None,
) -> dict[str, Any]:
    """Set the complete label order inside one graph label group."""
    parameters = {"course": course, "group": group, "labels": labels}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.labels.reorder", parameters)


@mcp.tool()
async def chaoxing_delete_knowledge_graph_label(
    course: str,
    label: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting a non-preset graph label."""
    parameters = {"course": course, "label": label}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("knowledge_graph.label.delete", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_list_class_activity_types(
    course: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """List the activity type IDs currently allowed by the course."""
    parameters = {"course": course}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("class_activities.types.list", parameters)


@mcp.tool()
async def chaoxing_list_class_activity_groups(
    course: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """List default and custom class-activity groups by stable ID."""
    parameters = {"course": course}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("class_activities.groups.list", parameters)


@mcp.tool()
async def chaoxing_create_class_activity_group(
    course: str,
    name: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Create a class-activity group and verify its returned ID."""
    parameters = {"course": course, "name": name}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("class_activities.group.create", parameters)


@mcp.tool()
async def chaoxing_rename_class_activity_group(
    course: str,
    group: str,
    name: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Rename a custom class-activity group and verify its current name."""
    parameters = {"course": course, "group": group, "name": name}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("class_activities.group.rename", parameters)


@mcp.tool()
async def chaoxing_delete_class_activity_group(
    course: str,
    group: str,
    clazz: str | None = None,
    allow_nonempty: bool = False,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting a custom activity group."""
    parameters = {
        "course": course,
        "group": group,
        "allow_nonempty": allow_nonempty,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("class_activities.group.delete", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_reorder_class_activity_groups(
    course: str,
    groups: list[str],
    clazz: str | None = None,
) -> dict[str, Any]:
    """Set the complete order of every custom class-activity group."""
    parameters = {"course": course, "groups": groups}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("class_activities.groups.reorder", parameters)


@mcp.tool()
async def chaoxing_list_class_activities(
    course: str,
    clazz: str | None = None,
    group: str = "",
    search: str = "",
    status: str = "",
    activity_type: int | None = None,
) -> dict[str, Any]:
    """List class activities, optionally filtered by group, name, state, or type."""
    parameters: dict[str, Any] = {
        "course": course,
        "group": group,
        "search": search,
        "status": status,
    }
    if activity_type is not None:
        parameters["activity_type"] = activity_type
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("class_activities.activities.list", parameters)


@mcp.tool()
async def chaoxing_read_class_activity(
    course: str,
    activity: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Read one class activity by stable ID or unique name."""
    parameters = {"course": course, "activity": activity}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("class_activities.activity.read", parameters)


@mcp.tool()
async def chaoxing_rename_class_activity(
    course: str,
    activity: str,
    name: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Rename a supported class activity and verify the new name."""
    parameters = {"course": course, "activity": activity, "name": name}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("class_activities.activity.rename", parameters)


@mcp.tool()
async def chaoxing_move_class_activity(
    course: str,
    activity: str,
    group: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Move one class activity into the requested group."""
    parameters = {"course": course, "activity": activity, "group": group}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("class_activities.activity.move", parameters)


@mcp.tool()
async def chaoxing_reorder_class_activities(
    course: str,
    group: str,
    activities: list[str],
    clazz: str | None = None,
) -> dict[str, Any]:
    """Set the complete activity order inside one group."""
    parameters = {"course": course, "group": group, "activities": activities}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("class_activities.activities.reorder", parameters)


@mcp.tool()
async def chaoxing_start_class_activity(
    course: str,
    activity: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm starting a not-started class activity."""
    parameters = {"course": course, "activity": activity}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("class_activities.activity.start", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_end_class_activity(
    course: str,
    activity: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm ending an ongoing class activity."""
    parameters = {"course": course, "activity": activity}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("class_activities.activity.end", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_delete_class_activity(
    course: str,
    activity: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm moving a class activity to recycle."""
    parameters = {"course": course, "activity": activity}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("class_activities.activity.delete", parameters, confirmation_token)


@mcp.tool()
async def chaoxing_list_class_activity_recycle(
    course: str,
    clazz: str | None = None,
    search: str = "",
    max_items: int = 1000,
) -> dict[str, Any]:
    """List or search the class-activity recycle bin."""
    parameters = {"course": course, "search": search, "max_items": max_items}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("class_activities.recycle.list", parameters)


@mcp.tool()
async def chaoxing_restore_class_activity(
    course: str,
    activity: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Restore a supported class activity from recycle."""
    parameters = {"course": course, "activity": activity}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("class_activities.recycle.restore", parameters)


@mcp.tool()
async def chaoxing_permanently_delete_class_activities(
    course: str,
    activities: list[str],
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm permanently deleting recycled class activities."""
    parameters = {"course": course, "activities": activities}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "class_activities.recycle.items.delete", parameters, confirmation_token
    )


@mcp.tool()
async def chaoxing_list_course_assets(
    course: str,
    kind: str,
    clazz: str | None = None,
    folder: str = "",
    search: str = "",
    page: int = 1,
    page_size: int = 1000,
) -> dict[str, Any]:
    """List direct courseware or teaching-plan items; kind is courseware or teaching_plan."""
    parameters: dict[str, Any] = {
        "course": course,
        "kind": kind,
        "folder": folder,
        "search": search,
        "page": page,
        "page_size": page_size,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("course_assets.items.list", parameters)


@mcp.tool()
async def chaoxing_list_course_asset_tree(
    course: str,
    kind: str,
    clazz: str | None = None,
    search: str = "",
) -> dict[str, Any]:
    """Recursively list all courseware or teaching-plan items and stable IDs."""
    parameters = {"course": course, "kind": kind, "search": search}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("course_assets.tree.list", parameters)


@mcp.tool()
async def chaoxing_create_course_asset_folder(
    course: str,
    kind: str,
    name: str,
    clazz: str | None = None,
    parent: str = "",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm creating a courseware or teaching-plan folder."""
    parameters = {"course": course, "kind": kind, "name": name, "parent": parent}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "course_assets.folder.create",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_import_cloud_files_to_course_assets(
    course: str,
    kind: str,
    resources: list[str],
    clazz: str | None = None,
    destination: str = "",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm importing personal cloud-disk files into courseware or plans."""
    parameters = {
        "course": course,
        "kind": kind,
        "resources": resources,
        "destination": destination,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "course_assets.cloud_files.import",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_rename_course_asset(
    course: str,
    kind: str,
    asset: str,
    name: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Rename one courseware or teaching-plan item and verify it by stable ID."""
    parameters = {"course": course, "kind": kind, "asset": asset, "name": name}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("course_assets.item.rename", parameters)


@mcp.tool()
async def chaoxing_set_course_asset_top_status(
    course: str,
    kind: str,
    asset: str,
    top: bool,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Set or clear top status for courseware, a teaching plan, or a folder."""
    parameters = {"course": course, "kind": kind, "asset": asset, "top": top}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("course_assets.item.top_status.update", parameters)


@mcp.tool()
async def chaoxing_move_course_assets(
    course: str,
    kind: str,
    assets: list[str],
    destination: str = "",
    clazz: str | None = None,
) -> dict[str, Any]:
    """Move courseware or teaching-plan items into a folder and verify every parent ID."""
    parameters = {
        "course": course,
        "kind": kind,
        "assets": assets,
        "destination": destination,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("course_assets.items.move", parameters)


@mcp.tool()
async def chaoxing_copy_course_asset(
    course: str,
    kind: str,
    asset: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm copying one courseware or teaching-plan item."""
    parameters = {"course": course, "kind": kind, "asset": asset}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "course_assets.item.copy",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_delete_course_assets(
    course: str,
    kind: str,
    assets: list[str],
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm moving courseware or teaching-plan items to recycle."""
    parameters = {"course": course, "kind": kind, "assets": assets}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "course_assets.items.delete",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_download_course_asset(
    course: str,
    kind: str,
    asset: str,
    output_path: str,
    clazz: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Download one courseware or teaching-plan file through authenticated HTTP."""
    parameters = {
        "course": course,
        "kind": kind,
        "asset": asset,
        "output_path": output_path,
        "overwrite": overwrite,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("course_assets.item.download", parameters)


@mcp.tool()
async def chaoxing_list_course_asset_recycle(
    course: str,
    kind: str,
    clazz: str | None = None,
    search: str = "",
) -> dict[str, Any]:
    """List a courseware or teaching-plan recycle bin recursively."""
    parameters = {"course": course, "kind": kind, "search": search}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("course_assets.recycle.list", parameters)


@mcp.tool()
async def chaoxing_restore_course_assets(
    course: str,
    kind: str,
    assets: list[str],
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm restoring courseware or teaching-plan recycle items."""
    parameters = {"course": course, "kind": kind, "assets": assets}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "course_assets.recycle.restore",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_permanently_delete_course_asset_recycle_items(
    course: str,
    kind: str,
    assets: list[str],
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm permanent deletion from a course asset recycle bin."""
    parameters = {"course": course, "kind": kind, "assets": assets}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "course_assets.recycle.items.delete",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_chapters(
    course: str, clazz: str | None = None, search: str = ""
) -> dict[str, Any]:
    """List the chapter hierarchy, task points, open state, and class progress."""
    parameters = {"course": course, "search": search}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("chapters.list", parameters)


@mcp.tool()
async def chaoxing_list_chapter_tree(course: str, clazz: str | None = None) -> dict[str, Any]:
    """Read the complete editable chapter tree, including stable IDs and all seven levels."""
    parameters = {"course": course}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("chapters.tree.list", parameters)


@mcp.tool()
async def chaoxing_list_chapter_cards(
    course: str,
    chapter: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Read page titles, HTML, plain text, images, and attachments in one chapter."""
    parameters = {"course": course, "chapter": chapter}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("chapters.cards.list", parameters)


@mcp.tool()
async def chaoxing_create_chapter_card(
    course: str,
    chapter: str,
    title: str,
    clazz: str | None = None,
    content: str = "",
    content_format: str = "plain",
    attachments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create a page in one chapter and verify its title and visible content."""
    parameters: dict[str, Any] = {
        "course": course,
        "chapter": chapter,
        "title": title,
        "content": content,
        "content_format": content_format,
    }
    if clazz:
        parameters["clazz"] = clazz
    if attachments is not None:
        parameters["attachments"] = attachments
    return await runtime.execute("chapters.card.create", parameters)


@mcp.tool()
async def chaoxing_update_chapter_card(
    course: str,
    chapter: str,
    card: str,
    clazz: str | None = None,
    title: str | None = None,
    content: str | None = None,
    content_format: str = "plain",
    attachments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Update selected fields of a chapter page and verify the refreshed content."""
    parameters: dict[str, Any] = {
        "course": course,
        "chapter": chapter,
        "card": card,
        "content_format": content_format,
    }
    if clazz:
        parameters["clazz"] = clazz
    if title is not None:
        parameters["title"] = title
    if content is not None:
        parameters["content"] = content
    if attachments is not None:
        parameters["attachments"] = attachments
    return await runtime.execute("chapters.card.update", parameters)


@mcp.tool()
async def chaoxing_move_chapter_card(
    course: str,
    chapter: str,
    card: str,
    target_position: int,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Move a chapter page to a one-based target position and verify its order."""
    parameters = {
        "course": course,
        "chapter": chapter,
        "card": card,
        "target_position": target_position,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("chapters.card.move", parameters)


@mcp.tool()
async def chaoxing_delete_chapter_card(
    course: str,
    chapter: str,
    card: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm permanent deletion of one chapter page."""
    parameters = {"course": course, "chapter": chapter, "card": card}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "chapters.card.delete",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_create_chapter(
    course: str,
    title: str,
    clazz: str | None = None,
    parent: str = "",
    before: str = "",
) -> dict[str, Any]:
    """Create a top-level chapter or child chapter and verify its ID, title, and parent."""
    parameters = {"course": course, "title": title, "parent": parent, "before": before}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("chapters.create", parameters)


@mcp.tool()
async def chaoxing_rename_chapter(
    course: str,
    chapter: str,
    title: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Rename a chapter selected by index, title, or ID and verify the refreshed tree."""
    parameters = {"course": course, "chapter": chapter, "title": title}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("chapters.rename", parameters)


@mcp.tool()
async def chaoxing_move_chapter(
    course: str,
    chapter: str,
    clazz: str | None = None,
    parent: str = "",
    relative_to: str = "",
    position: str = "after",
) -> dict[str, Any]:
    """Move a chapter under a parent, or place it before/after a sibling, then verify."""
    parameters = {
        "course": course,
        "chapter": chapter,
        "parent": parent,
        "relative_to": relative_to,
        "position": position,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("chapters.move", parameters)


@mcp.tool()
async def chaoxing_import_chapter_outline(
    course: str,
    outline: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Import an indented plain-text chapter outline and return every newly created node."""
    parameters = {"course": course, "outline": outline}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("chapters.outline.import", parameters)


@mcp.tool()
async def chaoxing_set_chapter_open_status(
    course: str,
    chapters: list[str],
    status: str,
    clazz: str | None = None,
    classes: list[str] | None = None,
    begin: str = "",
    end: str = "",
    time_end_review: bool = False,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm chapter open/task/timed/closed/review status for target classes."""
    parameters: dict[str, Any] = {
        "course": course,
        "chapters": chapters,
        "status": status,
        "begin": begin,
        "end": end,
        "time_end_review": time_end_review,
    }
    if clazz:
        parameters["clazz"] = clazz
    if classes:
        parameters["classes"] = classes
    return await runtime.execute(
        "chapters.open_status.update",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_delete_chapters(
    course: str,
    chapters: list[str],
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm permanent deletion of chapters and all descendant content."""
    parameters = {"course": course, "chapters": chapters}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "chapters.delete",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_resources(
    course: str,
    clazz: str | None = None,
    folder: str = "",
    search: str = "",
) -> dict[str, Any]:
    """List course resource folders/files and their metadata through HTTP."""
    parameters = {"course": course, "folder": folder, "search": search}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("resources.list", parameters)


@mcp.tool()
async def chaoxing_list_resource_tree(
    course: str,
    clazz: str | None = None,
    search: str = "",
) -> dict[str, Any]:
    """List the complete recursive course-resource tree through authenticated HTTP."""
    parameters = {"course": course, "search": search}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("resources.tree.list", parameters)


@mcp.tool()
async def chaoxing_download_resource_file(
    course: str,
    resource: str,
    output_path: str,
    clazz: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Download one resource file to an explicit local path without opening a browser."""
    parameters: dict[str, Any] = {
        "course": course,
        "resource": resource,
        "output_path": output_path,
        "overwrite": overwrite,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("resources.file.download", parameters)


@mcp.tool()
async def chaoxing_download_resource_items(
    course: str,
    resources: list[str],
    output_path: str,
    clazz: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Download multiple resources or folders into a local ZIP without the client."""
    parameters: dict[str, Any] = {
        "course": course,
        "resources": resources,
        "output_path": output_path,
        "overwrite": overwrite,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("resources.items.download", parameters)


@mcp.tool()
async def chaoxing_create_resource_folder(
    course: str,
    name: str,
    clazz: str | None = None,
    parent: str = "",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm creating and publishing a resource folder."""
    parameters = {"course": course, "name": name, "parent": parent}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "resources.folder.create", parameters, confirmation_token=confirmation_token
    )


@mcp.tool()
async def chaoxing_rename_resource(
    course: str,
    resource: str,
    name: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Rename one course resource and verify it by stable resource ID."""
    parameters = {"course": course, "resource": resource, "name": name}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("resources.rename", parameters)


@mcp.tool()
async def chaoxing_move_resources(
    course: str,
    resources: list[str],
    destination: str = "",
    clazz: str | None = None,
) -> dict[str, Any]:
    """Move resources to a folder and verify every resulting parent ID."""
    parameters: dict[str, Any] = {
        "course": course,
        "resources": resources,
        "destination": destination,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("resources.move", parameters)


@mcp.tool()
async def chaoxing_reorder_resources(
    course: str,
    resources: list[str],
    clazz: str | None = None,
    folder: str = "",
) -> dict[str, Any]:
    """Replace a folder's complete direct-child order and verify it after refresh."""
    parameters = {"course": course, "resources": resources, "folder": folder}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("resources.reorder", parameters)


@mcp.tool()
async def chaoxing_set_resource_top_status(
    course: str,
    resource: str,
    top: bool,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Set or clear one course resource's top status and verify the refreshed folder."""
    parameters = {"course": course, "resource": resource, "top": top}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("resources.top_status.update", parameters)


@mcp.tool()
async def chaoxing_copy_resource(
    course: str,
    resource: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm copying one file or folder inside its current resource folder."""
    parameters = {"course": course, "resource": resource}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "resources.copy",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_copy_resource_to_cloud_disk(
    course: str,
    resource: str,
    destination: str = "",
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm copying one course file to a personal cloud-disk folder."""
    parameters = {
        "course": course,
        "resource": resource,
        "destination": destination,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "resources.cloud_disk.copy",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_course_cloud_sources(
    course: str,
    clazz: str | None = None,
    path: str = "",
    search: str = "",
    page: int = 1,
    page_size: int = 1000,
    share_id: str = "0",
) -> dict[str, Any]:
    """List cloud-disk sources exposed by the course resource import interface."""
    parameters: dict[str, Any] = {
        "course": course,
        "path": path,
        "search": search,
        "page": page,
        "page_size": page_size,
        "share_id": share_id,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("resources.cloud_sources.list", parameters)


@mcp.tool()
async def chaoxing_import_cloud_files_to_resources(
    course: str,
    resources: list[str],
    clazz: str | None = None,
    source_path: str = "",
    destination: str = "",
    share_id: str = "0",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm importing up to 50 cloud files into course resources."""
    parameters: dict[str, Any] = {
        "course": course,
        "resources": resources,
        "source_path": source_path,
        "destination": destination,
        "share_id": share_id,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "resources.cloud_files.import",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_import_cloud_folder_to_resources(
    course: str,
    resource: str,
    clazz: str | None = None,
    source_path: str = "",
    destination: str = "",
    share_id: str = "0",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm importing one cloud folder into course resources."""
    parameters: dict[str, Any] = {
        "course": course,
        "resource": resource,
        "source_path": source_path,
        "destination": destination,
        "share_id": share_id,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "resources.cloud_folder.import",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_resource_labels(
    course: str,
    resource: str,
    clazz: str | None = None,
    search: str = "",
) -> dict[str, Any]:
    """List course resource labels and indicate which are assigned to one resource."""
    parameters = {"course": course, "resource": resource, "search": search}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("resources.labels.list", parameters)


@mcp.tool()
async def chaoxing_create_resource_label(
    course: str,
    resource: str,
    name: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Create a course resource label and verify its new stable ID."""
    parameters = {"course": course, "resource": resource, "name": name}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("resources.label.create", parameters)


@mcp.tool()
async def chaoxing_rename_resource_label(
    course: str,
    resource: str,
    label: str,
    name: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Rename an editable course resource label and verify it by stable ID."""
    parameters = {
        "course": course,
        "resource": resource,
        "label": label,
        "name": name,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("resources.label.rename", parameters)


@mcp.tool()
async def chaoxing_delete_resource_label(
    course: str,
    resource: str,
    label: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting a deletable course resource label."""
    parameters = {"course": course, "resource": resource, "label": label}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "resources.label.delete",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_update_resource_labels(
    course: str,
    resources: list[str],
    labels: list[str] | None = None,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm replacing complete label sets; omit labels to clear them."""
    parameters: dict[str, Any] = {
        "course": course,
        "resources": resources,
        "labels": labels or [],
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "resources.labels.update",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_delete_resources(
    course: str,
    resources: list[str],
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm permanent deletion of resource files or folders."""
    parameters = {"course": course, "resources": resources}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "resources.delete", parameters, confirmation_token=confirmation_token
    )


@mcp.tool()
async def chaoxing_create_resource_link(
    course: str,
    name: str,
    url: str,
    clazz: str | None = None,
    parent: str = "",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm publishing an HTTP/HTTPS URL as a course resource."""
    parameters = {"course": course, "name": name, "url": url, "parent": parent}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "resources.link.create", parameters, confirmation_token=confirmation_token
    )


@mcp.tool()
async def chaoxing_upload_resource_file(
    course: str,
    file_path: str,
    clazz: str | None = None,
    parent: str = "",
    name: str = "",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm pure-HTTP upload and publication of a local resource file."""
    parameters = {
        "course": course,
        "file_path": file_path,
        "parent": parent,
        "name": name,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "resources.file.upload", parameters, confirmation_token=confirmation_token
    )


@mcp.tool()
async def chaoxing_set_resource_download_permission(
    course: str,
    resources: list[str],
    allow_download: bool,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm allowing or denying student downloads for resources."""
    parameters: dict[str, Any] = {
        "course": course,
        "resources": resources,
        "allow_download": allow_download,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "resources.download_permission.update",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_read_resource_folder_visibility(
    course: str,
    folder: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Read a resource folder's class and teacher-team visibility."""
    parameters = {"course": course, "folder": folder}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("resources.folder.visibility.read", parameters)


@mcp.tool()
async def chaoxing_update_resource_folder_visibility(
    course: str,
    folder: str,
    mode: str,
    clazz: str | None = None,
    classes: list[str] | None = None,
    teacher_ids: list[str] | None = None,
    all_teachers: bool | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm class and teacher-team visibility for a resource folder."""
    parameters: dict[str, Any] = {"course": course, "folder": folder, "mode": mode}
    if clazz:
        parameters["clazz"] = clazz
    if classes is not None:
        parameters["classes"] = classes
    if teacher_ids is not None:
        parameters["teacher_ids"] = teacher_ids
    if all_teachers is not None:
        parameters["all_teachers"] = all_teachers
    return await runtime.execute(
        "resources.folder.visibility.update",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_resource_readers(
    course: str,
    resource: str,
    clazz: str | None = None,
    reader_class: str | None = None,
) -> dict[str, Any]:
    """List readers and non-readers for one resource in a selected class."""
    parameters = {"course": course, "resource": resource}
    if clazz:
        parameters["clazz"] = clazz
    if reader_class:
        parameters["reader_class"] = reader_class
    return await runtime.execute("resources.readers.list", parameters)


@mcp.tool()
async def chaoxing_list_resource_downloaders(
    course: str,
    resource: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """List downloader records for one course resource."""
    parameters = {"course": course, "resource": resource}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("resources.downloaders.list", parameters)


@mcp.tool()
async def chaoxing_list_resource_import_courses(
    course: str,
    clazz: str | None = None,
    search: str = "",
) -> dict[str, Any]:
    """List other courses available as resource-import sources."""
    parameters = {"course": course, "search": search}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("resources.import_courses.list", parameters)


@mcp.tool()
async def chaoxing_list_resource_import_items(
    course: str,
    source_course: str,
    clazz: str | None = None,
    folder_id: str = "",
    search: str = "",
    page: int = 1,
    page_size: int = 100,
) -> dict[str, Any]:
    """List importable files and folders from another course."""
    parameters: dict[str, Any] = {
        "course": course,
        "source_course": source_course,
        "folder_id": folder_id,
        "search": search,
        "page": page,
        "page_size": page_size,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("resources.import_items.list", parameters)


@mcp.tool()
async def chaoxing_import_resources_from_course(
    course: str,
    source_course: str,
    resources: list[str],
    clazz: str | None = None,
    source_folder_id: str = "",
    destination: str = "",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm importing up to 100 resources from another course."""
    parameters: dict[str, Any] = {
        "course": course,
        "source_course": source_course,
        "resources": resources,
        "source_folder_id": source_folder_id,
        "destination": destination,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "resources.import.execute", parameters, confirmation_token=confirmation_token
    )


@mcp.tool()
async def chaoxing_create_resource_share_link(
    course: str,
    resource: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm generating a share URL for one course resource."""
    parameters = {"course": course, "resource": resource}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "resources.share_link.create",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_cloud_disk_items(
    parent: str = "",
    search: str = "",
    page: int = 1,
    page_size: int = 100,
) -> dict[str, Any]:
    """List or globally search active personal cloud-disk items without a client."""
    return await runtime.execute(
        "cloud_disk.items.list",
        {
            "parent": parent,
            "search": search,
            "page": page,
            "page_size": page_size,
        },
    )


@mcp.tool()
async def chaoxing_read_cloud_disk_item(resource: str) -> dict[str, Any]:
    """Resolve one active personal cloud-disk item by ID or name."""
    return await runtime.execute("cloud_disk.item.read", {"resource": resource})


@mcp.tool()
async def chaoxing_delete_cloud_disk_items(
    resources: list[str],
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm removal of owned items from the active cloud-disk list."""
    return await runtime.execute(
        "cloud_disk.items.delete",
        {"resources": resources},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_create_cloud_disk_folder(
    name: str,
    parent: str = "",
    shared: bool = False,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm creating a private or collaborative personal cloud-disk folder."""
    return await runtime.execute(
        "cloud_disk.folder.create",
        {"name": name, "parent": parent, "shared": shared},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_rename_cloud_disk_item(resource: str, name: str) -> dict[str, Any]:
    """Rename one owned personal cloud-disk file or folder."""
    return await runtime.execute(
        "cloud_disk.item.rename",
        {"resource": resource, "name": name},
    )


@mcp.tool()
async def chaoxing_move_cloud_disk_items(
    resources: list[str],
    destination: str = "",
) -> dict[str, Any]:
    """Move up to 100 owned cloud-disk items and verify their destination parent."""
    return await runtime.execute(
        "cloud_disk.items.move",
        {"resources": resources, "destination": destination},
    )


@mcp.tool()
async def chaoxing_set_cloud_disk_top_status(
    resource: str,
    top: bool,
) -> dict[str, Any]:
    """Set or clear one cloud-disk item's top status and verify it after refresh."""
    return await runtime.execute(
        "cloud_disk.item.top_status.update",
        {"resource": resource, "top": top},
    )


@mcp.tool()
async def chaoxing_download_cloud_disk_items(
    resources: list[str],
    output_path: str,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Download files/folders through HTTP; folders become a local ZIP without a client."""
    return await runtime.execute(
        "cloud_disk.items.download",
        {
            "resources": resources,
            "output_path": output_path,
            "overwrite": overwrite,
        },
    )


@mcp.tool()
async def chaoxing_list_cloud_disk_recycle_items(
    page: int = 1,
    page_size: int = 100,
) -> dict[str, Any]:
    """List personal cloud-disk recycle-bin items through authenticated HTTP."""
    return await runtime.execute(
        "cloud_disk.recycle.list",
        {"page": page, "page_size": page_size},
    )


@mcp.tool()
async def chaoxing_restore_cloud_disk_recycle_items(
    resources: list[str],
    conflict_policy: str = "keep_both",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm restore; conflict_policy is keep_both or replace."""
    return await runtime.execute(
        "cloud_disk.recycle.restore",
        {"resources": resources, "conflict_policy": conflict_policy},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_permanently_delete_cloud_disk_recycle_items(
    resources: list[str],
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm permanently deleting selected cloud-disk recycle items."""
    return await runtime.execute(
        "cloud_disk.recycle.items.delete",
        {"resources": resources},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_empty_cloud_disk_recycle(
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm permanently emptying the personal cloud-disk recycle bin."""
    return await runtime.execute(
        "cloud_disk.recycle.empty",
        {},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_homework_library(
    course: str,
    clazz: str | None = None,
    directory: str = "0",
    search: str = "",
) -> dict[str, Any]:
    """List homework-library folders and reusable homework through authenticated HTTP."""
    parameters = {"course": course, "directory": directory, "search": search}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("homework.library.list", parameters)


@mcp.tool()
async def chaoxing_read_homework_library_item(
    course: str,
    homework: str,
    clazz: str | None = None,
    question: str = "",
) -> dict[str, Any]:
    """Read a homework/draft and its stems, options, answers, analysis, scores, and IDs."""
    parameters = {"course": course, "homework": homework, "question": question}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("homework.library.item.read", parameters)


@mcp.tool()
async def chaoxing_add_homework_question(
    course: str,
    homework: str,
    question_type: str,
    stem: str,
    clazz: str | None = None,
    score: float = 5,
    options: list[str] | None = None,
    correct_answer: str = "",
    answers: list[str] | None = None,
    answer: str = "",
    analysis: str = "",
    difficulty: float = 0.8,
    content_format: str = "plain",
) -> dict[str, Any]:
    """Add a core question type to a homework or draft and verify every requested field."""
    parameters: dict[str, Any] = {
        "course": course,
        "homework": homework,
        "question_type": question_type,
        "stem": stem,
        "score": score,
        "options": options,
        "correct_answer": correct_answer,
        "answer": answer,
        "analysis": analysis,
        "difficulty": difficulty,
        "content_format": content_format,
    }
    if answers is not None:
        parameters["answers"] = answers
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("homework.question.add", parameters)


@mcp.tool()
async def chaoxing_update_homework_question(
    course: str,
    homework: str,
    question: str,
    clazz: str | None = None,
    stem: str | None = None,
    score: float | None = None,
    options: list[str] | None = None,
    correct_answer: str | None = None,
    answers: list[str] | None = None,
    answer: str | None = None,
    analysis: str | None = None,
    difficulty: float | None = None,
    content_format: str = "plain",
) -> dict[str, Any]:
    """Update selected fields of one homework question and verify them through HTTP."""
    parameters: dict[str, Any] = {
        "course": course,
        "homework": homework,
        "question": question,
        "content_format": content_format,
    }
    optional = {
        "stem": stem,
        "score": score,
        "options": options,
        "correct_answer": correct_answer,
        "answers": answers,
        "answer": answer,
        "analysis": analysis,
        "difficulty": difficulty,
    }
    parameters.update({key: value for key, value in optional.items() if value is not None})
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("homework.question.update", parameters)


@mcp.tool()
async def chaoxing_delete_homework_question(
    course: str,
    homework: str,
    question: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm permanently deleting one question from a homework or draft."""
    parameters = {"course": course, "homework": homework, "question": question}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "homework.question.delete",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_homework_drafts(
    course: str,
    clazz: str | None = None,
    search: str = "",
) -> dict[str, Any]:
    """List unpublished homework drafts, their IDs, creators, and edit URLs."""
    parameters = {"course": course, "search": search}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("homework.drafts.list", parameters)


@mcp.tool()
async def chaoxing_create_homework_draft(
    course: str,
    title: str,
    clazz: str | None = None,
    directory: str = "0",
) -> dict[str, Any]:
    """Create an unpublished homework draft and verify it through a fresh draft listing."""
    parameters = {"course": course, "title": title, "directory": directory}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("homework.draft.create", parameters)


@mcp.tool()
async def chaoxing_update_homework_draft(
    course: str,
    draft: str,
    title: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Rename an unpublished homework draft and verify the refreshed title."""
    parameters = {"course": course, "draft": draft, "title": title}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("homework.draft.update", parameters)


@mcp.tool()
async def chaoxing_delete_homework_draft(
    course: str,
    draft: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm permanently deleting an unpublished homework draft."""
    parameters = {"course": course, "draft": draft}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "homework.draft.delete",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_publish_homework_from_library(
    course: str,
    homework: str,
    clazz: str | None = None,
    target_classes: list[str] | None = None,
    start_time: str = "now",
    end_time: str = "",
    allow_late_submission: bool = False,
    late_deadline: str = "",
    passing_score: float = 0,
    redo_times: int = 0,
    allow_paste: bool = True,
    show_score: bool = True,
    show_correctness: bool = True,
    randomize_questions: bool = False,
    randomize_options: bool = False,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm publishing one homework-library item to selected classes."""
    parameters: dict[str, Any] = {
        "course": course,
        "homework": homework,
        "start_time": start_time,
        "end_time": end_time,
        "allow_late_submission": allow_late_submission,
        "late_deadline": late_deadline,
        "passing_score": passing_score,
        "redo_times": redo_times,
        "allow_paste": allow_paste,
        "show_score": show_score,
        "show_correctness": show_correctness,
        "randomize_questions": randomize_questions,
        "randomize_options": randomize_options,
    }
    if clazz:
        parameters["clazz"] = clazz
    if target_classes is not None:
        parameters["target_classes"] = target_classes
    return await runtime.execute(
        "homework.library.publish",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_homeworks(
    course: str, clazz: str | None = None, only_ungraded: bool = False
) -> dict[str, Any]:
    """List homework records and submission counts through HTTP, optionally only ungraded."""
    parameters = {"course": course}
    if clazz:
        parameters["clazz"] = clazz
    action = "homework.list_ungraded" if only_ungraded else "homework.list"
    return await runtime.execute(action, parameters)


@mcp.tool()
async def chaoxing_list_homework_submissions(
    course: str,
    homework: str,
    clazz: str | None = None,
    status: int = 0,
) -> dict[str, Any]:
    """List submissions for a homework; status is 0 all, 3 pending, or 4 graded."""
    parameters: dict[str, Any] = {
        "course": course,
        "homework": homework,
        "status": status,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("homework.submissions.list", parameters)


@mcp.tool()
async def chaoxing_read_homework_submission(
    course: str,
    homework: str,
    submission: str,
    clazz: str | None = None,
    max_chars: int = 4000,
) -> dict[str, Any]:
    """Read one student's answer text, image URLs, and attachment metadata through HTTP."""
    parameters: dict[str, Any] = {
        "course": course,
        "homework": homework,
        "submission": submission,
        "max_chars": max_chars,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("homework.submission.read", parameters)


@mcp.tool()
async def chaoxing_set_homework_score(
    course: str,
    homework: str,
    submission: str,
    score: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm one score submission; first call always requires confirmation."""
    parameters = {
        "course": course,
        "homework": homework,
        "submission": submission,
        "score": score,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "homework.score.set", parameters, confirmation_token=confirmation_token
    )


@mcp.tool()
async def chaoxing_list_notices(
    course: str, clazz: str | None = None, search: str = ""
) -> dict[str, Any]:
    """List course notices, full text, recipients, and read counts through HTTP."""
    parameters = {"course": course, "search": search}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("notices.list", parameters)


@mcp.tool()
async def chaoxing_list_notice_drafts(
    course: str,
    search: str = "",
    page_size: int = 100,
) -> dict[str, Any]:
    """List course notice drafts and scheduled-send state through HTTP."""
    return await runtime.execute(
        "notices.drafts.list",
        {"course": course, "search": search, "page_size": page_size},
    )


@mcp.tool()
async def chaoxing_save_notice_draft(
    course: str,
    title: str,
    content: str,
    clazz: str | None = None,
    recipient_classes: list[str] | None = None,
    draft: str | None = None,
    clear_schedule: bool = False,
    allow_comments: bool = True,
    show_comments: bool = False,
    hide_read_status: bool = False,
) -> dict[str, Any]:
    """Create or update a notice draft without publishing it."""
    parameters: dict[str, Any] = {
        "course": course,
        "title": title,
        "content": content,
        "clear_schedule": clear_schedule,
        "allow_comments": allow_comments,
        "show_comments": show_comments,
        "hide_read_status": hide_read_status,
    }
    if clazz:
        parameters["clazz"] = clazz
    if recipient_classes is not None:
        parameters["recipient_classes"] = recipient_classes
    if draft:
        parameters["draft"] = draft
    return await runtime.execute("notices.draft.save", parameters)


@mcp.tool()
async def chaoxing_schedule_notice(
    course: str,
    title: str,
    content: str,
    send_at: str,
    clazz: str | None = None,
    recipient_classes: list[str] | None = None,
    draft: str | None = None,
    allow_comments: bool = True,
    show_comments: bool = False,
    hide_read_status: bool = False,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm scheduling a notice for a future China-local date-time."""
    parameters: dict[str, Any] = {
        "course": course,
        "title": title,
        "content": content,
        "send_at": send_at,
        "allow_comments": allow_comments,
        "show_comments": show_comments,
        "hide_read_status": hide_read_status,
    }
    if clazz:
        parameters["clazz"] = clazz
    if recipient_classes is not None:
        parameters["recipient_classes"] = recipient_classes
    if draft:
        parameters["draft"] = draft
    return await runtime.execute(
        "notices.schedule",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_delete_notice_draft(
    course: str,
    draft: str,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting one course notice draft."""
    return await runtime.execute(
        "notices.draft.delete",
        {"course": course, "draft": draft},
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_send_notice(
    course: str,
    title: str,
    content: str,
    clazz: str | None = None,
    recipient_classes: list[str] | None = None,
    allow_comments: bool = True,
    show_comments: bool = False,
    hide_read_status: bool = False,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm sending a text notice to one or more course classes."""
    parameters: dict[str, Any] = {
        "course": course,
        "title": title,
        "content": content,
        "allow_comments": allow_comments,
        "show_comments": show_comments,
        "hide_read_status": hide_read_status,
    }
    if clazz:
        parameters["clazz"] = clazz
    if recipient_classes is not None:
        parameters["recipient_classes"] = recipient_classes
    return await runtime.execute(
        "notices.send",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_edit_notice(
    course: str,
    notice: str,
    title: str,
    content: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm changing a notice title and body while preserving attachments."""
    parameters = {
        "course": course,
        "notice": notice,
        "title": title,
        "content": content,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "notices.edit",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_set_notice_top(
    course: str,
    notice: str,
    top: bool = True,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm pinning or unpinning a course notice."""
    parameters: dict[str, Any] = {"course": course, "notice": notice, "top": top}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "notices.top.set",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_recall_notice(
    course: str,
    notice: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm recalling a sent course notice."""
    parameters = {"course": course, "notice": notice}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "notices.recall",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_delete_notice(
    course: str,
    notice: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting a course notice."""
    parameters = {"course": course, "notice": notice}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "notices.delete",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_exams(
    course: str,
    clazz: str | None = None,
    status: int = -1,
    search: str = "",
) -> dict[str, Any]:
    """List exams; status is -1 all, 0 not started, 1 active, or 2 ended."""
    parameters: dict[str, Any] = {
        "course": course,
        "status": status,
        "search": search,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("exams.list", parameters)


@mcp.tool()
async def chaoxing_list_exam_paper_library(
    course: str,
    clazz: str | None = None,
    directory_id: str = "0",
    search: str = "",
    page_size: int = 100,
) -> dict[str, Any]:
    """List folders and papers in the authenticated exam paper library through HTTP."""
    parameters: dict[str, Any] = {
        "course": course,
        "directory_id": directory_id,
        "search": search,
        "page_size": page_size,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("exam.paper_library.list", parameters)


@mcp.tool()
async def chaoxing_read_exam_paper(
    course: str,
    paper: str,
    clazz: str | None = None,
    directory_id: str = "0",
    question: str = "",
) -> dict[str, Any]:
    """Read a complete paper, or select one question, from the exam paper library."""
    parameters = {
        "course": course,
        "paper": paper,
        "directory_id": directory_id,
        "question": question,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("exam.paper.read", parameters)


@mcp.tool()
async def chaoxing_read_exam_paper_settings(
    course: str,
    paper: str,
    clazz: str | None = None,
    directory_id: str = "0",
    group_id: str = "0",
) -> dict[str, Any]:
    """Read difficulty, numbering, grouping, question count, and score settings."""
    parameters = {
        "course": course,
        "paper": paper,
        "directory_id": directory_id,
        "group_id": group_id,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("exam.paper.settings.read", parameters)


@mcp.tool()
async def chaoxing_update_exam_paper_settings(
    course: str,
    paper: str,
    clazz: str | None = None,
    difficulty: str | int | None = None,
    numbering: str | int | None = None,
    grouping: str | int | bool | None = None,
    subquestion_numbering: str | int | None = None,
    directory_id: str = "0",
    group_id: str = "0",
) -> dict[str, Any]:
    """Update selected exam-editor settings and verify every requested value."""
    parameters: dict[str, Any] = {
        "course": course,
        "paper": paper,
        "directory_id": directory_id,
        "group_id": group_id,
    }
    optional = {
        "difficulty": difficulty,
        "numbering": numbering,
        "grouping": grouping,
        "subquestion_numbering": subquestion_numbering,
    }
    parameters.update({key: value for key, value in optional.items() if value is not None})
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("exam.paper.settings.update", parameters)


@mcp.tool()
async def chaoxing_add_exam_question(
    course: str,
    paper: str,
    question_type: str,
    stem: str,
    clazz: str | None = None,
    score: float = 5,
    options: list[str] | dict[str, str] | None = None,
    correct_answer: str | list[str] | None = None,
    answers: list[str] | None = None,
    answer: str | bool | None = None,
    analysis: str = "",
    difficulty: float = 0.8,
    content_format: str = "plain",
    directory_id: str = "0",
    group_id: str = "0",
) -> dict[str, Any]:
    """Add a core question to an unpublished exam paper and verify every field."""
    parameters: dict[str, Any] = {
        "course": course,
        "paper": paper,
        "question_type": question_type,
        "stem": stem,
        "score": score,
        "analysis": analysis,
        "difficulty": difficulty,
        "content_format": content_format,
        "directory_id": directory_id,
        "group_id": group_id,
    }
    optional = {
        "options": options,
        "correct_answer": correct_answer,
        "answers": answers,
        "answer": answer,
    }
    parameters.update({key: value for key, value in optional.items() if value is not None})
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("exam.question.add", parameters)


@mcp.tool()
async def chaoxing_update_exam_question(
    course: str,
    paper: str,
    question: str,
    clazz: str | None = None,
    stem: str | None = None,
    score: float | None = None,
    options: list[str] | dict[str, str] | None = None,
    correct_answer: str | list[str] | None = None,
    answers: list[str] | None = None,
    answer: str | bool | None = None,
    analysis: str | None = None,
    difficulty: float | None = None,
    content_format: str = "plain",
    directory_id: str = "0",
    group_id: str = "0",
) -> dict[str, Any]:
    """Update selected fields of one core exam question and verify them over HTTP."""
    parameters: dict[str, Any] = {
        "course": course,
        "paper": paper,
        "question": question,
        "content_format": content_format,
        "directory_id": directory_id,
        "group_id": group_id,
    }
    optional = {
        "stem": stem,
        "score": score,
        "options": options,
        "correct_answer": correct_answer,
        "answers": answers,
        "answer": answer,
        "analysis": analysis,
        "difficulty": difficulty,
    }
    parameters.update({key: value for key, value in optional.items() if value is not None})
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("exam.question.update", parameters)


@mcp.tool()
async def chaoxing_delete_exam_question(
    course: str,
    paper: str,
    question: str,
    clazz: str | None = None,
    directory_id: str = "0",
    group_id: str = "0",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm permanently deleting one question from an exam paper."""
    parameters = {
        "course": course,
        "paper": paper,
        "question": question,
        "directory_id": directory_id,
        "group_id": group_id,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "exam.question.delete",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_move_exam_question(
    course: str,
    paper: str,
    question: str,
    target_position: int,
    clazz: str | None = None,
    directory_id: str = "0",
    group_id: str = "0",
) -> dict[str, Any]:
    """Move one paper question to a 1-based position and verify the full order."""
    parameters = {
        "course": course,
        "paper": paper,
        "question": question,
        "target_position": target_position,
        "directory_id": directory_id,
        "group_id": group_id,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("exam.question.move", parameters)


@mcp.tool()
async def chaoxing_update_exam_question_type(
    course: str,
    paper: str,
    question_type: str,
    clazz: str | None = None,
    description: str | None = None,
    total_score: float | None = None,
    directory_id: str = "0",
    group_id: str = "0",
) -> dict[str, Any]:
    """Update a paper question type's description or total score and verify it."""
    parameters: dict[str, Any] = {
        "course": course,
        "paper": paper,
        "question_type": question_type,
        "directory_id": directory_id,
        "group_id": group_id,
    }
    optional = {"description": description, "total_score": total_score}
    parameters.update({key: value for key, value in optional.items() if value is not None})
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("exam.question_type.update", parameters)


@mcp.tool()
async def chaoxing_move_exam_question_type(
    course: str,
    paper: str,
    question_type: str,
    target_position: int,
    clazz: str | None = None,
    directory_id: str = "0",
    group_id: str = "0",
) -> dict[str, Any]:
    """Move one paper question type to a 1-based position and verify the full order."""
    parameters = {
        "course": course,
        "paper": paper,
        "question_type": question_type,
        "target_position": target_position,
        "directory_id": directory_id,
        "group_id": group_id,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("exam.question_type.move", parameters)


@mcp.tool()
async def chaoxing_delete_exam_question_type(
    course: str,
    paper: str,
    question_type: str,
    clazz: str | None = None,
    directory_id: str = "0",
    group_id: str = "0",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting a type and all of its questions from a paper."""
    parameters = {
        "course": course,
        "paper": paper,
        "question_type": question_type,
        "directory_id": directory_id,
        "group_id": group_id,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "exam.question_type.delete",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_create_exam_paper(
    course: str,
    title: str = "",
    clazz: str | None = None,
    directory_id: str = "0",
) -> dict[str, Any]:
    """Create an unpublished empty paper in the exam paper library."""
    parameters = {"course": course, "title": title, "directory_id": directory_id}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("exam.paper.create", parameters)


@mcp.tool()
async def chaoxing_rename_exam_paper(
    course: str,
    paper: str,
    title: str,
    clazz: str | None = None,
    directory_id: str = "0",
    sync_parallel_titles: bool = False,
) -> dict[str, Any]:
    """Rename one unpublished exam paper and verify the refreshed title."""
    parameters = {
        "course": course,
        "paper": paper,
        "title": title,
        "directory_id": directory_id,
        "sync_parallel_titles": sync_parallel_titles,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("exam.paper.rename", parameters)


@mcp.tool()
async def chaoxing_copy_exam_paper(
    course: str,
    paper: str,
    clazz: str | None = None,
    directory_id: str = "0",
) -> dict[str, Any]:
    """Copy an exam paper within its current paper-library folder."""
    parameters = {"course": course, "paper": paper, "directory_id": directory_id}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("exam.paper.copy", parameters)


@mcp.tool()
async def chaoxing_move_exam_paper(
    course: str,
    paper: str,
    target_directory_id: str,
    clazz: str | None = None,
    source_directory_id: str = "0",
) -> dict[str, Any]:
    """Move an exam paper between two paper-library folders."""
    parameters = {
        "course": course,
        "paper": paper,
        "source_directory_id": source_directory_id,
        "target_directory_id": target_directory_id,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("exam.paper.move", parameters)


@mcp.tool()
async def chaoxing_delete_exam_paper(
    course: str,
    paper: str,
    clazz: str | None = None,
    directory_id: str = "0",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm moving an exam paper to the recycle bin."""
    parameters = {"course": course, "paper": paper, "directory_id": directory_id}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "exam.paper.delete", parameters, confirmation_token=confirmation_token
    )


@mcp.tool()
async def chaoxing_create_exam_paper_folder(
    course: str,
    title: str,
    clazz: str | None = None,
    parent_directory_id: str = "0",
) -> dict[str, Any]:
    """Create a folder in the exam paper library."""
    parameters = {
        "course": course,
        "title": title,
        "parent_directory_id": parent_directory_id,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("exam.paper_folder.create", parameters)


@mcp.tool()
async def chaoxing_rename_exam_paper_folder(
    course: str,
    folder: str,
    title: str,
    clazz: str | None = None,
    parent_directory_id: str = "0",
) -> dict[str, Any]:
    """Rename a folder in the exam paper library."""
    parameters = {
        "course": course,
        "folder": folder,
        "title": title,
        "parent_directory_id": parent_directory_id,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("exam.paper_folder.rename", parameters)


@mcp.tool()
async def chaoxing_move_exam_paper_folder(
    course: str,
    folder: str,
    target_directory_id: str,
    clazz: str | None = None,
    source_directory_id: str = "0",
) -> dict[str, Any]:
    """Move a folder within the exam paper library."""
    parameters = {
        "course": course,
        "folder": folder,
        "source_directory_id": source_directory_id,
        "target_directory_id": target_directory_id,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("exam.paper_folder.move", parameters)


@mcp.tool()
async def chaoxing_delete_exam_paper_folder(
    course: str,
    folder: str,
    clazz: str | None = None,
    parent_directory_id: str = "0",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm moving an exam paper-library folder to the recycle bin."""
    parameters = {
        "course": course,
        "folder": folder,
        "parent_directory_id": parent_directory_id,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "exam.paper_folder.delete",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_exam_submissions(
    course: str,
    exam: str,
    clazz: str | None = None,
    state: int = 1,
    status: int = -1,
    search: str = "",
) -> dict[str, Any]:
    """List submitted or unsubmitted students for one exam through HTTP."""
    parameters: dict[str, Any] = {
        "course": course,
        "exam": exam,
        "state": state,
        "status": status,
        "search": search,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("exams.submissions.list", parameters)


@mcp.tool()
async def chaoxing_read_exam_submission(
    course: str,
    exam: str,
    submission: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Read one student's exam questions, answers, keys, and per-question scores."""
    parameters = {"course": course, "exam": exam, "submission": submission}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("exams.submission.read", parameters)


@mcp.tool()
async def chaoxing_list_question_bank(
    course: str,
    clazz: str | None = None,
    page: int = 1,
    page_size: int = 30,
    search: str = "",
    directory_id: str = "0",
) -> dict[str, Any]:
    """Page through question-bank folders and questions through HTTP."""
    parameters: dict[str, Any] = {
        "course": course,
        "page": page,
        "page_size": page_size,
        "search": search,
        "directory_id": directory_id,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.list", parameters)


@mcp.tool()
async def chaoxing_read_question_bank_question(
    course: str,
    question: str,
    clazz: str | None = None,
    directory_id: str = "0",
) -> dict[str, Any]:
    """Read one complete question-bank item, including options, answer, and assets."""
    parameters = {
        "course": course,
        "question": question,
        "directory_id": directory_id,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.question.read", parameters)


@mcp.tool()
async def chaoxing_list_question_bank_directories(
    course: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Read the complete question-bank directory tree and sharing metadata."""
    parameters = {"course": course}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.directories.list", parameters)


@mcp.tool()
async def chaoxing_read_question_bank_directory_permissions(
    course: str,
    directory: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Read a question-bank directory's sharing and student self-practice settings."""
    parameters = {"course": course, "directory": directory}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.directory.permissions.read", parameters)


@mcp.tool()
async def chaoxing_update_question_bank_directory_permissions(
    course: str,
    directory: str,
    clazz: str | None = None,
    allow_student_self_practice: bool | None = None,
    share_scope: str | None = None,
    selected_teachers: list[str] | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm directory sharing and student self-practice changes.

    share_scope accepts all_team, private, or selected_teachers. When selected_teachers
    is used, selected_teachers must identify at least one current teaching-team member.
    """
    parameters: dict[str, Any] = {"course": course, "directory": directory}
    optional = {
        "allow_student_self_practice": allow_student_self_practice,
        "share_scope": share_scope,
        "selected_teachers": selected_teachers,
    }
    parameters.update({key: value for key, value in optional.items() if value is not None})
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "question_bank.directory.permissions.update",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_question_bank_question_types(
    course: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """List current question-bank question types and creatable base types."""
    parameters = {"course": course}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.question_types.list", parameters)


@mcp.tool()
async def chaoxing_add_question_bank_question_type(
    course: str,
    name: str,
    base_type: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Create a named question type derived from a currently supported base type."""
    parameters = {"course": course, "name": name, "base_type": base_type}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.question_type.add", parameters)


@mcp.tool()
async def chaoxing_rename_question_bank_question_type(
    course: str,
    question_type: str,
    name: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Rename a question-bank question type and verify it by ID."""
    parameters = {
        "course": course,
        "question_type": question_type,
        "name": name,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.question_type.rename", parameters)


@mcp.tool()
async def chaoxing_move_question_bank_question_type(
    course: str,
    question_type: str,
    target_position: int,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Move a question-bank question type to a one-based position."""
    parameters = {
        "course": course,
        "question_type": question_type,
        "target_position": target_position,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.question_type.move", parameters)


@mcp.tool()
async def chaoxing_delete_question_bank_question_type(
    course: str,
    question_type: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting a question type when the current UI permits it."""
    parameters = {"course": course, "question_type": question_type}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "question_bank.question_type.delete",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_question_bank_labels(
    course: str,
    clazz: str | None = None,
    question: str = "",
    directory_id: str = "0",
) -> dict[str, Any]:
    """List the label tree and optionally one question's selected labels."""
    parameters = {
        "course": course,
        "question": question,
        "directory_id": directory_id,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.labels.list", parameters)


@mcp.tool()
async def chaoxing_create_question_bank_label(
    course: str,
    name: str,
    clazz: str | None = None,
    parent_label: str = "0",
) -> dict[str, Any]:
    """Create a root or child question-bank label."""
    parameters = {
        "course": course,
        "name": name,
        "parent_label": parent_label,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.label.create", parameters)


@mcp.tool()
async def chaoxing_rename_question_bank_label(
    course: str,
    label: str,
    name: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Rename a question-bank label and verify it by ID."""
    parameters = {"course": course, "label": label, "name": name}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.label.rename", parameters)


@mcp.tool()
async def chaoxing_delete_question_bank_label(
    course: str,
    label: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting a question-bank label and all child labels."""
    parameters = {"course": course, "label": label}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "question_bank.label.delete",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_set_question_bank_question_labels(
    course: str,
    questions: list[str],
    labels: list[str],
    clazz: str | None = None,
    directory_id: str = "0",
    mode: str = "replace",
) -> dict[str, Any]:
    """Replace, add, or remove labels without changing referenced homework or exams."""
    parameters = {
        "course": course,
        "questions": questions,
        "labels": labels,
        "directory_id": directory_id,
        "mode": mode,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.question.labels.set", parameters)


@mcp.tool()
async def chaoxing_sync_question_bank_question_labels(
    course: str,
    questions: list[str],
    labels: list[str],
    clazz: str | None = None,
    directory_id: str = "0",
    mode: str = "replace",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm label changes synchronized to referenced homework and exams."""
    parameters = {
        "course": course,
        "questions": questions,
        "labels": labels,
        "directory_id": directory_id,
        "mode": mode,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "question_bank.question.labels.sync",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_question_bank_topics(
    course: str,
    clazz: str | None = None,
    question: str = "",
    directory_id: str = "0",
    search: str = "",
) -> dict[str, Any]:
    """List the knowledge-point tree and optionally one question's selected topics."""
    parameters = {
        "course": course,
        "question": question,
        "directory_id": directory_id,
        "search": search,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.topics.list", parameters)


@mcp.tool()
async def chaoxing_create_question_bank_topic(
    course: str,
    name: str,
    clazz: str | None = None,
    kind: str = "knowledge_point",
    parent_topic: str | None = None,
    after_topic: str = "",
) -> dict[str, Any]:
    """Create a knowledge point or category, optionally below or after another node."""
    parameters: dict[str, Any] = {
        "course": course,
        "name": name,
        "kind": kind,
        "after_topic": after_topic,
    }
    if clazz:
        parameters["clazz"] = clazz
    if parent_topic is not None:
        parameters["parent_topic"] = parent_topic
    return await runtime.execute("question_bank.topic.create", parameters)


@mcp.tool()
async def chaoxing_rename_question_bank_topic(
    course: str,
    topic: str,
    name: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Rename a knowledge point or category and verify it by node ID."""
    parameters = {"course": course, "topic": topic, "name": name}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.topic.rename", parameters)


@mcp.tool()
async def chaoxing_delete_question_bank_topic(
    course: str,
    topic: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting a topic and every descendant node."""
    parameters = {"course": course, "topic": topic}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "question_bank.topic.delete",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_set_question_bank_question_topics(
    course: str,
    questions: list[str],
    topics: list[str],
    clazz: str | None = None,
    directory_id: str = "0",
    mode: str = "replace",
) -> dict[str, Any]:
    """Replace, add, or remove topics without changing referenced homework or exams."""
    parameters = {
        "course": course,
        "questions": questions,
        "topics": topics,
        "directory_id": directory_id,
        "mode": mode,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.question.topics.set", parameters)


@mcp.tool()
async def chaoxing_sync_question_bank_question_topics(
    course: str,
    questions: list[str],
    topics: list[str],
    clazz: str | None = None,
    directory_id: str = "0",
    mode: str = "replace",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm topic changes synchronized to referenced homework and exams."""
    parameters = {
        "course": course,
        "questions": questions,
        "topics": topics,
        "directory_id": directory_id,
        "mode": mode,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "question_bank.question.topics.sync",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_question_bank_recycle_bin(
    course: str,
    clazz: str | None = None,
    page: int = 1,
    page_size: int = 0,
    search: str = "",
    directory_id: str = "",
    directory_path_ids: list[str] | None = None,
    order: str = "desc",
) -> dict[str, Any]:
    """List recycled question-bank questions and directories."""
    parameters: dict[str, Any] = {
        "course": course,
        "page": page,
        "page_size": page_size,
        "search": search,
        "directory_id": directory_id,
        "directory_path_ids": directory_path_ids or [],
        "order": order,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.recycle.list", parameters)


@mcp.tool()
async def chaoxing_list_locked_question_bank_items(
    course: str,
    clazz: str | None = None,
    page: int = 1,
    page_size: int = 0,
    search: str = "",
    directory_id: str = "",
    directory_path_ids: list[str] | None = None,
    order: str = "desc",
    lock_time_filters: list[str] | None = None,
) -> dict[str, Any]:
    """List locked question-bank questions and directories."""
    parameters: dict[str, Any] = {
        "course": course,
        "page": page,
        "page_size": page_size,
        "search": search,
        "directory_id": directory_id,
        "directory_path_ids": directory_path_ids or [],
        "order": order,
        "lock_time_filters": lock_time_filters or [],
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.locked.list", parameters)


@mcp.tool()
async def chaoxing_lock_question_bank_items(
    course: str,
    clazz: str | None = None,
    questions: list[str] | None = None,
    directories: list[str] | None = None,
    directory_id: str = "0",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm locking active questions and directories."""
    parameters: dict[str, Any] = {
        "course": course,
        "questions": questions or [],
        "directories": directories or [],
        "directory_id": directory_id,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "question_bank.items.lock",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_unlock_question_bank_items(
    course: str,
    items: list[str],
    clazz: str | None = None,
    directory_id: str = "",
    directory_path_ids: list[str] | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm unlocking selected locked questions or directories."""
    parameters: dict[str, Any] = {
        "course": course,
        "items": items,
        "directory_id": directory_id,
        "directory_path_ids": directory_path_ids or [],
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "question_bank.items.unlock",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_restore_question_bank_recycle_items(
    course: str,
    items: list[str],
    clazz: str | None = None,
    directory_id: str = "",
    directory_path_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Restore selected questions or directories from the question-bank recycle bin."""
    parameters: dict[str, Any] = {
        "course": course,
        "items": items,
        "directory_id": directory_id,
        "directory_path_ids": directory_path_ids or [],
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.recycle.restore", parameters)


@mcp.tool()
async def chaoxing_delete_question_bank_recycle_items(
    course: str,
    items: list[str],
    clazz: str | None = None,
    directory_id: str = "",
    directory_path_ids: list[str] | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm permanently deleting selected recycle-bin items."""
    parameters: dict[str, Any] = {
        "course": course,
        "items": items,
        "directory_id": directory_id,
        "directory_path_ids": directory_path_ids or [],
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "question_bank.recycle.delete",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_empty_question_bank_recycle_bin(
    course: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm permanently emptying the whole question-bank recycle bin."""
    parameters = {"course": course}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "question_bank.recycle.empty",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_update_question_bank_questions_difficulty(
    course: str,
    questions: list[str],
    difficulty: float | str,
    clazz: str | None = None,
    directory_id: str = "0",
) -> dict[str, Any]:
    """Set numeric or categorical difficulty on one or more question-bank questions."""
    parameters: dict[str, Any] = {
        "course": course,
        "questions": questions,
        "difficulty": difficulty,
        "directory_id": directory_id,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.questions.difficulty.update", parameters)


@mcp.tool()
async def chaoxing_update_question_bank_questions_type(
    course: str,
    questions: list[str],
    question_type: str,
    clazz: str | None = None,
    directory_id: str = "0",
) -> dict[str, Any]:
    """Change one or more questions to a system or custom question type."""
    parameters = {
        "course": course,
        "questions": questions,
        "question_type": question_type,
        "directory_id": directory_id,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.questions.type.update", parameters)


@mcp.tool()
async def chaoxing_copy_question_bank_items(
    course: str,
    clazz: str | None = None,
    questions: list[str] | None = None,
    directories: list[str] | None = None,
    source_directory_id: str = "0",
    target_directory: str = "0",
) -> dict[str, Any]:
    """Copy selected questions or directories into a target directory in the course."""
    parameters: dict[str, Any] = {
        "course": course,
        "questions": questions or [],
        "directories": directories or [],
        "source_directory_id": source_directory_id,
        "target_directory": target_directory,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.items.copy", parameters)


@mcp.tool()
async def chaoxing_preview_question_bank_smart_import(
    course: str,
    clazz: str | None = None,
    source_text: str | None = None,
    file_path: str | None = None,
    content_format: str = "plain",
    parse_latex_code: bool = False,
    parse_latex_formula: bool = False,
) -> dict[str, Any]:
    """Parse one text or local Word/PDF/image source without adding questions to Chaoxing."""
    parameters: dict[str, Any] = {
        "course": course,
        "source_text": source_text,
        "file_path": file_path,
        "content_format": content_format,
        "parse_latex_code": parse_latex_code,
        "parse_latex_formula": parse_latex_formula,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.smart_import.preview", parameters)


@mcp.tool()
async def chaoxing_import_question_bank_smart(
    course: str,
    target_directory: str = "0",
    clazz: str | None = None,
    source_text: str | None = None,
    file_path: str | None = None,
    questions: list[dict[str, Any]] | None = None,
    content_format: str = "plain",
    parse_latex_code: bool = False,
    parse_latex_formula: bool = False,
    allow_parser_warnings: bool = False,
) -> dict[str, Any]:
    """Import one text/file source or reviewed preview questions into a question-bank folder."""
    parameters: dict[str, Any] = {
        "course": course,
        "target_directory": target_directory,
        "source_text": source_text,
        "file_path": file_path,
        "questions": questions,
        "content_format": content_format,
        "parse_latex_code": parse_latex_code,
        "parse_latex_formula": parse_latex_formula,
        "allow_parser_warnings": allow_parser_warnings,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.smart_import.commit", parameters)


@mcp.tool()
async def chaoxing_list_question_bank_source_courses(
    course: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """List personal course question banks available for cross-course importing."""
    parameters = {"course": course}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.source_courses.list", parameters)


@mcp.tool()
async def chaoxing_list_question_bank_source_questions(
    course: str,
    source_course: str,
    clazz: str | None = None,
    page: int = 1,
    page_size: int = 30,
    search: str = "",
    directory_id: str = "0",
) -> dict[str, Any]:
    """Browse or search another personal course question bank before importing."""
    parameters: dict[str, Any] = {
        "course": course,
        "source_course": source_course,
        "page": page,
        "page_size": page_size,
        "search": search,
        "directory_id": directory_id,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.source_questions.list", parameters)


@mcp.tool()
async def chaoxing_import_question_bank_questions_from_course(
    course: str,
    source_course: str,
    questions: list[str],
    clazz: str | None = None,
    source_directory_id: str = "0",
    target_directory: str = "0",
) -> dict[str, Any]:
    """Import selected questions from another personal course bank into a target directory."""
    parameters: dict[str, Any] = {
        "course": course,
        "source_course": source_course,
        "questions": questions,
        "source_directory_id": source_directory_id,
        "target_directory": target_directory,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.questions.import_from_course", parameters)


@mcp.tool()
async def chaoxing_export_question_bank(
    course: str,
    export_type: str,
    clazz: str | None = None,
    questions: list[str] | None = None,
    directories: list[str] | None = None,
    export_all: bool = False,
    source_directory_id: str = "0",
    output_path: str | None = None,
    include_answers: bool = True,
    include_analysis: bool = True,
    include_difficulty: bool = False,
    include_type_names: bool = False,
    include_topics: bool = False,
    include_targets: bool = False,
    include_correct_rate: bool = False,
    include_use_count: bool = False,
    excel_plain_text: bool = False,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Export selected questions/directories or the whole bank as Ti, Word, Excel, or PDF."""
    parameters: dict[str, Any] = {
        "course": course,
        "export_type": export_type,
        "questions": questions or [],
        "directories": directories or [],
        "export_all": export_all,
        "source_directory_id": source_directory_id,
        "output_path": output_path,
        "include_answers": include_answers,
        "include_analysis": include_analysis,
        "include_difficulty": include_difficulty,
        "include_type_names": include_type_names,
        "include_topics": include_topics,
        "include_targets": include_targets,
        "include_correct_rate": include_correct_rate,
        "include_use_count": include_use_count,
        "excel_plain_text": excel_plain_text,
        "overwrite": overwrite,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.export.create", parameters)


@mcp.tool()
async def chaoxing_list_question_bank_downloads(
    course: str,
    clazz: str | None = None,
    page: int = 1,
    order: str = "down",
) -> dict[str, Any]:
    """List question-bank export tasks and completed files in the download center."""
    parameters: dict[str, Any] = {"course": course, "page": page, "order": order}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.downloads.list", parameters)


@mcp.tool()
async def chaoxing_get_question_bank_download(
    course: str,
    record: str,
    clazz: str | None = None,
    output_path: str | None = None,
    password: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Get an export URL or save one completed question-bank export to a local path."""
    parameters: dict[str, Any] = {
        "course": course,
        "record": record,
        "output_path": output_path,
        "password": password,
        "overwrite": overwrite,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.downloads.get", parameters)


@mcp.tool()
async def chaoxing_rename_question_bank_download(
    course: str,
    record: str,
    name: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Rename a question-bank download-center record and verify the refreshed name."""
    parameters = {"course": course, "record": record, "name": name}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.downloads.rename", parameters)


@mcp.tool()
async def chaoxing_delete_question_bank_download(
    course: str,
    record: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting one question-bank download-center record."""
    parameters = {"course": course, "record": record}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "question_bank.downloads.delete",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_create_question_bank_directory(
    course: str,
    name: str,
    clazz: str | None = None,
    parent_directory: str = "0",
) -> dict[str, Any]:
    """Create a question-bank directory under the root or a selected parent."""
    parameters = {
        "course": course,
        "name": name,
        "parent_directory": parent_directory,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.directory.create", parameters)


@mcp.tool()
async def chaoxing_rename_question_bank_directory(
    course: str,
    directory: str,
    name: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Rename one question-bank directory and verify it by ID."""
    parameters = {"course": course, "directory": directory, "name": name}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.directory.rename", parameters)


@mcp.tool()
async def chaoxing_move_question_bank_directory(
    course: str,
    directory: str,
    target_directory: str,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Move a question-bank directory under another directory or the root."""
    parameters = {
        "course": course,
        "directory": directory,
        "target_directory": target_directory,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.directory.move", parameters)


@mcp.tool()
async def chaoxing_reorder_question_bank_directory(
    course: str,
    directory: str,
    target_position: int,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Move a non-topped question-bank directory within its current parent."""
    parameters = {
        "course": course,
        "directory": directory,
        "target_position": target_position,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.directory.reorder", parameters)


@mcp.tool()
async def chaoxing_set_question_bank_directory_top(
    course: str,
    directory: str,
    top: bool = True,
    clazz: str | None = None,
) -> dict[str, Any]:
    """Set or clear a question-bank directory's top status and verify it."""
    parameters = {"course": course, "directory": directory, "top": top}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.directory.top.set", parameters)


@mcp.tool()
async def chaoxing_delete_question_bank_directory(
    course: str,
    directory: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm moving a question-bank directory and contents to recycle."""
    parameters = {"course": course, "directory": directory}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "question_bank.directory.delete",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_add_question_bank_question(
    course: str,
    question_type: str,
    stem: str,
    clazz: str | None = None,
    directory: str = "0",
    options: list[str] | dict[str, str] | None = None,
    correct_answer: str | list[str] | None = None,
    answers: list[str] | None = None,
    answer: str | bool | None = None,
    analysis: str = "",
    difficulty: float = 0.8,
    content_format: str = "plain",
) -> dict[str, Any]:
    """Add a core question-bank question and verify its fields and directory."""
    parameters: dict[str, Any] = {
        "course": course,
        "question_type": question_type,
        "stem": stem,
        "directory": directory,
        "analysis": analysis,
        "difficulty": difficulty,
        "content_format": content_format,
    }
    optional = {
        "options": options,
        "correct_answer": correct_answer,
        "answers": answers,
        "answer": answer,
    }
    parameters.update({key: value for key, value in optional.items() if value is not None})
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.question.add", parameters)


@mcp.tool()
async def chaoxing_update_question_bank_question(
    course: str,
    question: str,
    clazz: str | None = None,
    directory_id: str = "0",
    stem: str | None = None,
    options: list[str] | dict[str, str] | None = None,
    correct_answer: str | list[str] | None = None,
    answers: list[str] | None = None,
    answer: str | bool | None = None,
    analysis: str | None = None,
    difficulty: float | None = None,
    content_format: str = "plain",
) -> dict[str, Any]:
    """Update selected fields of a core question-bank question and verify them."""
    parameters: dict[str, Any] = {
        "course": course,
        "question": question,
        "directory_id": directory_id,
        "content_format": content_format,
    }
    optional = {
        "stem": stem,
        "options": options,
        "correct_answer": correct_answer,
        "answers": answers,
        "answer": answer,
        "analysis": analysis,
        "difficulty": difficulty,
    }
    parameters.update({key: value for key, value in optional.items() if value is not None})
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.question.update", parameters)


@mcp.tool()
async def chaoxing_move_question_bank_question(
    course: str,
    question: str,
    target_directory: str,
    clazz: str | None = None,
    source_directory_id: str = "0",
) -> dict[str, Any]:
    """Move a question-bank question between directories and verify both sides."""
    parameters = {
        "course": course,
        "question": question,
        "target_directory": target_directory,
        "source_directory_id": source_directory_id,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.question.move", parameters)


@mcp.tool()
async def chaoxing_reorder_question_bank_question(
    course: str,
    question: str,
    target_position: int,
    clazz: str | None = None,
    directory_id: str = "0",
) -> dict[str, Any]:
    """Move a question-bank question within its current directory."""
    parameters = {
        "course": course,
        "question": question,
        "target_position": target_position,
        "directory_id": directory_id,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.question.reorder", parameters)


@mcp.tool()
async def chaoxing_update_question_bank_question_difficulty(
    course: str,
    question: str,
    difficulty: float,
    clazz: str | None = None,
    directory_id: str = "0",
) -> dict[str, Any]:
    """Set numeric question-bank difficulty from 0.1 to 1.0 and verify it."""
    parameters = {
        "course": course,
        "question": question,
        "difficulty": difficulty,
        "directory_id": directory_id,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("question_bank.question.difficulty.update", parameters)


@mcp.tool()
async def chaoxing_delete_question_bank_question(
    course: str,
    question: str,
    clazz: str | None = None,
    directory_id: str = "0",
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm moving one question-bank question to the recycle bin."""
    parameters = {
        "course": course,
        "question": question,
        "directory_id": directory_id,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "question_bank.question.delete",
        parameters,
        confirmation_token=confirmation_token,
    )


@mcp.tool()
async def chaoxing_list_discussions(
    course: str,
    clazz: str | None = None,
    search: str = "",
    class_only: bool = False,
) -> dict[str, Any]:
    """List discussion topics and engagement counts through HTTP."""
    parameters: dict[str, Any] = {
        "course": course,
        "search": search,
        "class_only": class_only,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("discussions.list", parameters)


@mcp.tool()
async def chaoxing_read_discussion_topic(
    course: str,
    topic: str,
    clazz: str | None = None,
    class_only: bool = False,
    order: int = 2,
    reply_search: str = "",
) -> dict[str, Any]:
    """Read one discussion topic and all replies; order is 1 oldest or 2 newest."""
    parameters: dict[str, Any] = {
        "course": course,
        "topic": topic,
        "class_only": class_only,
        "order": order,
        "reply_search": reply_search,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute("discussions.topic.read", parameters)


@mcp.tool()
async def chaoxing_create_discussion_topic(
    course: str,
    title: str,
    content: str,
    clazz: str | None = None,
    class_only: bool = False,
    anonymous: bool = False,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm publishing a text discussion to one class or all classes."""
    parameters: dict[str, Any] = {
        "course": course,
        "title": title,
        "content": content,
        "class_only": class_only,
        "anonymous": anonymous,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "discussions.topic.create", parameters, confirmation_token=confirmation_token
    )


@mcp.tool()
async def chaoxing_edit_discussion_topic(
    course: str,
    topic: str,
    clazz: str | None = None,
    title: str | None = None,
    content: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm editing a discussion title or body while preserving assets."""
    parameters: dict[str, Any] = {"course": course, "topic": topic}
    if clazz:
        parameters["clazz"] = clazz
    if title is not None:
        parameters["title"] = title
    if content is not None:
        parameters["content"] = content
    return await runtime.execute(
        "discussions.topic.edit", parameters, confirmation_token=confirmation_token
    )


@mcp.tool()
async def chaoxing_set_discussion_topic_top(
    course: str,
    topic: str,
    top: bool = True,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm pinning or unpinning a discussion topic."""
    parameters: dict[str, Any] = {"course": course, "topic": topic, "top": top}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "discussions.topic.top.set", parameters, confirmation_token=confirmation_token
    )


@mcp.tool()
async def chaoxing_delete_discussion_topic(
    course: str,
    topic: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting a discussion topic."""
    parameters: dict[str, Any] = {"course": course, "topic": topic}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "discussions.topic.delete", parameters, confirmation_token=confirmation_token
    )


@mcp.tool()
async def chaoxing_create_discussion_reply(
    course: str,
    topic: str,
    content: str,
    clazz: str | None = None,
    reply_to: str = "",
    anonymous: bool = False,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm replying to a discussion topic or an existing reply."""
    parameters: dict[str, Any] = {
        "course": course,
        "topic": topic,
        "content": content,
        "reply_to": reply_to,
        "anonymous": anonymous,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "discussions.reply.create", parameters, confirmation_token=confirmation_token
    )


@mcp.tool()
async def chaoxing_edit_discussion_reply(
    course: str,
    topic: str,
    reply: str,
    content: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm editing one discussion reply."""
    parameters: dict[str, Any] = {
        "course": course,
        "topic": topic,
        "reply": reply,
        "content": content,
    }
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "discussions.reply.edit", parameters, confirmation_token=confirmation_token
    )


@mcp.tool()
async def chaoxing_delete_discussion_reply(
    course: str,
    topic: str,
    reply: str,
    clazz: str | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Preview or confirm deleting one discussion reply."""
    parameters: dict[str, Any] = {"course": course, "topic": topic, "reply": reply}
    if clazz:
        parameters["clazz"] = clazz
    return await runtime.execute(
        "discussions.reply.delete", parameters, confirmation_token=confirmation_token
    )


@mcp.tool()
async def chaoxing_plan_command(command: str) -> dict[str, Any]:
    """Parse a Chinese natural-language request into an action, parameters, and missing fields."""
    return await runtime.execute("command.plan", {"command": command})


@mcp.tool()
async def chaoxing_execute_command(
    command: str, confirmation_token: str | None = None
) -> dict[str, Any]:
    """Parse and execute a supported Chinese natural-language Chaoxing command."""
    return await runtime.execute_command(command, confirmation_token)


@mcp.tool()
async def chaoxing_execute_action(
    action: str,
    parameters: dict[str, Any] | None = None,
    confirmation_token: str | None = None,
) -> dict[str, Any]:
    """Execute an exact catalog action; use this for composable multi-step agent workflows."""
    return await runtime.execute(action, parameters, confirmation_token)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
