from __future__ import annotations

import math
from typing import Any

from .api import ChaoxingAPI, ChaoxingAPIError, resolve_class
from .approval import ConfirmationError, ConfirmationGate
from .capabilities import ACTION_BY_NAME, capability_report
from .config import Settings
from .models import CapabilityState
from .router import route_command


class ActionRuntimeError(RuntimeError):
    pass


class ActionRuntime:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.from_env()
        self.confirmations = ConfirmationGate(storage_path=self.settings.confirmation_file)

    def _api(self) -> ChaoxingAPI:
        if self.settings.cookie_file is None:
            raise ActionRuntimeError(
                "CHAOXING_COOKIE_FILE is required for authenticated HTTP actions"
            )
        return ChaoxingAPI(
            self.settings.cookie_file,
            timeout=self.settings.request_timeout,
            state_file=self.settings.state_file,
        )

    async def execute(
        self,
        action: str,
        parameters: dict[str, Any] | None = None,
        confirmation_token: str | None = None,
    ) -> dict[str, Any]:
        parameters = dict(parameters or {})
        spec = ACTION_BY_NAME.get(action)
        if spec is None:
            raise ActionRuntimeError(f"unknown action: {action}")
        if spec.state is not CapabilityState.IMPLEMENTED:
            return {
                "status": "not_implemented",
                "action": action,
                "message": spec.description,
            }
        if spec.risk.requires_confirmation:
            summary = self._confirmation_summary(action, parameters)
            if not confirmation_token:
                challenge = self.confirmations.issue(action, parameters, summary)
                return {
                    "status": "confirmation_required",
                    "action": action,
                    "risk": spec.risk.value,
                    "confirmation": challenge.to_dict(),
                }
            self.confirmations.consume(confirmation_token, action, parameters)

        try:
            result = await self._dispatch(action, parameters)
        except (ChaoxingAPIError, ConfirmationError) as exc:
            raise ActionRuntimeError(str(exc)) from exc
        return {
            "status": "ok",
            "action": action,
            "risk": spec.risk.value,
            "result": result,
        }

    async def _dispatch(self, action: str, parameters: dict[str, Any]) -> Any:
        if action == "capabilities.list":
            return capability_report()
        if action == "session.check":
            return self._api().check_session()
        if action == "session.login":
            username = self._required(parameters, "username")
            password = self._required(parameters, "password")
            api = self._api()
            login_options: dict[str, Any] = {
                "fid": str(parameters.get("fid") or "-1"),
            }
            target_url = str(parameters.get("target_url") or "").strip()
            learning_course = str(parameters.get("learning_course") or "").strip()
            learning_module = str(parameters.get("learning_module") or "直播课/见面课").strip()
            target_context: dict[str, str] | None = None
            if target_url and learning_course:
                raise ActionRuntimeError("target_url and learning_course cannot be used together")
            if learning_course:
                course, module, target_url = api.resolve_learning_course_module_login_target(
                    learning_course,
                    learning_module,
                )
                target_context = {
                    "course_id": str(course.get("course_id") or ""),
                    "course_name": str(course.get("course_name") or ""),
                    "clazz_id": str(course.get("clazz_id") or ""),
                    "module": str(module.get("module") or ""),
                    "module_label": str(module.get("label") or ""),
                }
            if target_url:
                login_options["target_url"] = target_url
            result = api.login(
                username,
                password,
                **login_options,
            )
            if target_context is not None:
                result["target_context"] = target_context
            return result
        if action == "space.modules.discover":
            return self._api().list_personal_space_modules()
        if action == "space.module.open":
            return self._api().inspect_personal_space_module(self._required(parameters, "module"))
        if action.startswith("job_ability."):
            api = self._api()
            if action == "job_ability.status.read":
                return api.read_job_ability_status()
            if action == "job_ability.jobs.search":
                return api.search_job_ability_jobs(
                    self._required(parameters, "keyword"),
                    page=self._integer(parameters.get("page", 1), "page"),
                    page_size=self._integer(parameters.get("page_size", 20), "page_size"),
                    education_level=str(parameters.get("education_level") or ""),
                )
            if action == "job_ability.job_ad.read":
                return api.read_job_ability_job_ad(
                    self._required(parameters, "job"),
                    search=str(parameters.get("search") or ""),
                    education_level=str(parameters.get("education_level") or ""),
                )
            if action == "job_ability.popular_jobs.list":
                return api.list_popular_job_ability_jobs(
                    education_level=str(parameters.get("education_level") or "本科")
                )
            if action == "job_ability.occupation_catalog.read":
                return api.read_job_ability_occupation_catalog(
                    education_level=str(parameters.get("education_level") or "本科")
                )
            if action == "job_ability.occupations.search":
                return api.search_job_ability_occupations(
                    self._required(parameters, "keyword"),
                    education_level=str(parameters.get("education_level") or "本科"),
                )
            if action == "job_ability.industry_types.list":
                return api.list_job_ability_industry_types(
                    page=self._integer(parameters.get("page", 1), "page"),
                    page_size=self._integer(parameters.get("page_size", 100), "page_size"),
                )
            if action == "job_ability.industries.list":
                return api.list_job_ability_industries(
                    self._required(parameters, "industry_type"),
                    education_level=str(parameters.get("education_level") or "本科"),
                    page=self._integer(parameters.get("page", 1), "page"),
                    page_size=self._integer(parameters.get("page_size", 100), "page_size"),
                )
            if action == "job_ability.industry_jobs.list":
                return api.list_job_ability_industry_jobs(
                    self._required(parameters, "industry"),
                    education_level=str(parameters.get("education_level") or "本科"),
                    page=self._integer(parameters.get("page", 1), "page"),
                    page_size=self._integer(parameters.get("page_size", 100), "page_size"),
                )
        if action == "subjects.items.list":
            return self._api().list_subject_creation_items(
                folder=str(parameters.get("folder") or "-1"),
                search=str(parameters.get("search") or ""),
                max_items=self._integer(parameters.get("max_items", 1000), "max_items"),
            )
        if action == "subjects.tree.list":
            return self._api().list_subject_creation_tree(
                max_folders=self._integer(parameters.get("max_folders", 1000), "max_folders")
            )
        if action == "subjects.creation.status":
            return self._api().subject_creation_status()
        if action == "subjects.folder.create":
            return self._api().create_subject_creation_folder(
                self._required(parameters, "name"),
                parent_folder=str(parameters.get("parent_folder") or "-1"),
            )
        if action == "subjects.folder.rename":
            return self._api().rename_subject_creation_folder(
                self._required(parameters, "folder"),
                self._required(parameters, "name"),
            )
        if action == "subjects.folder.move":
            return self._api().move_subject_creation_folder(
                self._required(parameters, "folder"),
                target_folder=str(parameters.get("target_folder") or "-1"),
            )
        if action == "subjects.folder.delete":
            return self._api().delete_subject_creation_folder(
                self._required(parameters, "folder"),
                allow_nonempty=self._boolean(
                    parameters.get("allow_nonempty", False), "allow_nonempty"
                ),
            )
        if action == "subjects.publish_status.update":
            return self._api().set_subject_creation_publish_status(
                self._required(parameters, "subject"),
                self._boolean(parameters.get("published"), "published"),
            )
        if action == "subjects.move":
            return self._api().move_subject_creation_subject(
                self._required(parameters, "subject"),
                target_folder=str(parameters.get("target_folder") or "-1"),
            )
        if action == "subjects.delete":
            return self._api().delete_subject_creation_subject(
                self._required(parameters, "subject")
            )
        if action == "subjects.recycle.list":
            return self._api().list_subject_creation_recycle(
                search=str(parameters.get("search") or ""),
                max_items=self._integer(parameters.get("max_items", 1000), "max_items"),
            )
        if action == "subjects.recycle.restore":
            return self._api().restore_subject_creation_subject(
                self._required(parameters, "subject")
            )
        if action == "subjects.recycle.delete":
            return self._api().permanently_delete_subject_creation_subject(
                self._required(parameters, "subject")
            )
        if action == "detection.channels.list":
            return self._api().list_detection_channels()
        if action == "detection.records.list":
            return self._api().list_detection_records(
                self._required(parameters, "type"),
                page=self._integer(parameters.get("page", 1), "page"),
                page_size=self._integer(parameters.get("page_size", 100), "page_size"),
                status=self._integer(parameters.get("status", -1), "status"),
                begin_date=str(parameters.get("begin_date") or ""),
                end_date=str(parameters.get("end_date") or ""),
                search=str(parameters.get("search") or ""),
            )
        if action == "detection.record.status":
            return self._api().read_detection_record_status(
                self._required(parameters, "type"),
                self._required(parameters, "record"),
            )
        if action == "detection.submit":
            return self._api().submit_detection(
                self._required(parameters, "type"),
                self._required(parameters, "title"),
                author=str(parameters.get("author") or ""),
                content=(
                    str(parameters["content"]) if parameters.get("content") is not None else None
                ),
                file=parameters.get("file"),
                end_year=str(parameters.get("end_year") or ""),
                channel_ids=self._optional_string_list(parameters.get("channel_ids")),
            )
        if action == "detection.comparison.submit":
            return self._api().submit_detection_comparison(
                self._required(parameters, "title_1"),
                self._required(parameters, "file_1"),
                self._required(parameters, "title_2"),
                self._required(parameters, "file_2"),
            )
        if action == "detection.payment.status":
            return self._api().read_detection_payment_status(
                self._required(parameters, "type"),
                self._required(parameters, "record"),
            )
        if action == "detection.free_entitlement.use":
            return self._api().use_detection_free_entitlement(
                self._required(parameters, "type"),
                self._required(parameters, "record"),
            )
        if action == "detection.report.download":
            timeout_seconds = self._number(
                parameters.get("timeout_seconds", 300), "timeout_seconds"
            )
            return self._api().download_detection_report(
                self._required(parameters, "type"),
                self._required(parameters, "record"),
                self._required(parameters, "output_path"),
                result_type=self._integer(parameters.get("result_type", 1), "result_type"),
                overwrite=self._boolean(parameters.get("overwrite", False), "overwrite"),
                timeout_seconds=timeout_seconds,
            )
        if action == "detection.record.delete":
            return self._api().delete_detection_record(
                self._required(parameters, "type"),
                self._required(parameters, "record"),
            )
        if action == "live.rooms.list":
            return self._api().list_live_rooms(
                search=str(parameters.get("search") or ""),
                start_time=str(parameters.get("start_time") or ""),
                end_time=str(parameters.get("end_time") or ""),
                sort_key=self._integer(parameters.get("sort_key", 0), "sort_key"),
                sort_type=self._integer(parameters.get("sort_type", 0), "sort_type"),
                max_items=self._integer(parameters.get("max_items", 1000), "max_items"),
            )
        if action == "live.room.read":
            return self._api().read_live_room(self._required(parameters, "room"))
        if action == "live.room.create":
            extends_info = parameters.get("extends_info")
            if extends_info is not None and not isinstance(extends_info, dict):
                raise ActionRuntimeError("extends_info must be an object")
            return self._api().create_live_room(
                self._required(parameters, "title"),
                scheduled_time=str(parameters.get("scheduled_time") or ""),
                introduction=str(parameters.get("introduction") or ""),
                content_format=str(parameters.get("content_format") or "plain"),
                mode=str(parameters.get("mode") or "multi_device"),
                chat_content_review=self._boolean(
                    parameters.get("chat_content_review", True), "chat_content_review"
                ),
                cover_object_id=str(parameters.get("cover_object_id") or ""),
                preview_video_object_id=str(parameters.get("preview_video_object_id") or ""),
                extends_info=extends_info,
            )
        if action == "live.room.update":
            return self._api().update_live_room(
                self._required(parameters, "room"),
                title=(str(parameters["title"]) if "title" in parameters else None),
                scheduled_time=(
                    str(parameters["scheduled_time"]) if "scheduled_time" in parameters else None
                ),
                introduction=(
                    str(parameters["introduction"]) if "introduction" in parameters else None
                ),
                content_format=str(parameters.get("content_format") or "plain"),
                cover_object_id=(
                    str(parameters["cover_object_id"]) if "cover_object_id" in parameters else None
                ),
                preview_video_object_id=(
                    str(parameters["preview_video_object_id"])
                    if "preview_video_object_id" in parameters
                    else None
                ),
            )
        if action == "live.room.settings.update":
            return self._api().update_live_room_settings(
                self._required(parameters, "room"),
                comments_enabled=self._optional_boolean(parameters, "comments_enabled"),
                forwarding_enabled=self._optional_boolean(parameters, "forwarding_enabled"),
                replay_enabled=self._optional_boolean(parameters, "replay_enabled"),
                learning_app_only=self._optional_boolean(parameters, "learning_app_only"),
                chat_content_review=self._optional_boolean(parameters, "chat_content_review"),
                login_required=self._optional_boolean(parameters, "login_required"),
                picture_live=self._optional_boolean(parameters, "picture_live"),
                access_password=(
                    str(parameters["access_password"]) if "access_password" in parameters else None
                ),
                show_viewer_count=self._optional_boolean(parameters, "show_viewer_count"),
                reservations_enabled=self._optional_boolean(parameters, "reservations_enabled"),
                preupload_enabled=self._optional_boolean(parameters, "preupload_enabled"),
                allowed_unit_ids=(
                    self._string_list(parameters["allowed_unit_ids"], "allowed_unit_ids")
                    if "allowed_unit_ids" in parameters
                    else None
                ),
                replay_start_offset_seconds=(
                    self._integer(
                        parameters["replay_start_offset_seconds"],
                        "replay_start_offset_seconds",
                    )
                    if "replay_start_offset_seconds" in parameters
                    else None
                ),
            )
        if action == "live.room.status":
            return self._api().read_live_room_status(self._required(parameters, "room"))
        if action == "live.room.watch":
            return self._api().read_live_watch_address(self._required(parameters, "room"))
        if action == "live.stream.credentials":
            return self._api().read_live_stream_credentials(self._required(parameters, "room"))
        if action == "live.asset.upload":
            return self._api().upload_live_asset(
                self._required(parameters, "file"),
                kind=self._required(parameters, "kind"),
                room=str(parameters.get("room") or ""),
            )
        if action == "live.export":
            return self._api().export_live_rooms(
                search=str(parameters.get("search") or ""),
                start_time=str(parameters.get("start_time") or ""),
                end_time=str(parameters.get("end_time") or ""),
                sort_key=self._integer(parameters.get("sort_key", 0), "sort_key"),
                sort_type=self._integer(parameters.get("sort_type", 0), "sort_type"),
            )
        if action == "live.units.list":
            return self._api().list_live_units()
        if action == "live.room.delete":
            return self._api().delete_live_room(self._required(parameters, "room"))
        if action == "live.recycle.list":
            return self._api().list_live_recycle(
                search=str(parameters.get("search") or ""),
                max_items=self._integer(parameters.get("max_items", 1000), "max_items"),
            )
        if action == "live.recycle.restore":
            return self._api().restore_live_room(self._required(parameters, "room"))
        if action == "live.recycle.delete":
            return self._api().permanently_delete_live_room(self._required(parameters, "room"))
        if action == "live.themes.list":
            return self._api().list_live_themes(
                search=str(parameters.get("search") or ""),
                max_items=self._integer(parameters.get("max_items", 1000), "max_items"),
            )
        if action == "live.theme.read":
            return self._api().read_live_theme(
                self._required(parameters, "theme"),
                max_rooms=self._integer(parameters.get("max_rooms", 1000), "max_rooms"),
            )
        if action == "live.theme.create":
            return self._api().create_live_theme(
                self._required(parameters, "name"),
                description=str(parameters.get("description") or ""),
            )
        if action == "live.theme.update":
            return self._api().update_live_theme(
                self._required(parameters, "theme"),
                name=(str(parameters["name"]) if "name" in parameters else None),
                description=(
                    str(parameters["description"]) if "description" in parameters else None
                ),
            )
        if action == "live.theme.settings.update":
            return self._api().update_live_theme_settings(
                self._required(parameters, "theme"),
                forwarding_enabled=self._optional_boolean(parameters, "forwarding_enabled"),
                replay_enabled=self._optional_boolean(parameters, "replay_enabled"),
                learning_app_only=self._optional_boolean(parameters, "learning_app_only"),
                login_required=self._optional_boolean(parameters, "login_required"),
                allowed_unit_ids=(
                    self._string_list(parameters["allowed_unit_ids"], "allowed_unit_ids")
                    if "allowed_unit_ids" in parameters
                    else None
                ),
            )
        if action == "live.theme.room.add":
            return self._api().add_live_room_to_theme(
                self._required(parameters, "theme"),
                self._required(parameters, "room"),
            )
        if action == "live.theme.room.create":
            return self._api().create_live_room_in_theme(
                self._required(parameters, "theme"),
                self._required(parameters, "title"),
                scheduled_time=str(parameters.get("scheduled_time") or ""),
                introduction=str(parameters.get("introduction") or ""),
                content_format=str(parameters.get("content_format") or "plain"),
                mode=str(parameters.get("mode") or "multi_device"),
                chat_content_review=self._boolean(
                    parameters.get("chat_content_review", True), "chat_content_review"
                ),
                cover_object_id=str(parameters.get("cover_object_id") or ""),
                preview_video_object_id=str(parameters.get("preview_video_object_id") or ""),
            )
        if action == "live.theme.delete":
            return self._api().delete_live_theme(self._required(parameters, "theme"))
        if action == "notes.list":
            return self._api().list_notes(
                search=str(parameters.get("search") or ""),
                max_items=self._integer(parameters.get("max_items", 1000), "max_items"),
            )
        if action == "notes.read":
            return self._api().read_note(self._required(parameters, "note"))
        if action == "notes.create":
            return self._api().create_note(
                self._required(parameters, "title"),
                str(parameters.get("content") or ""),
                content_format=str(parameters.get("content_format") or "plain"),
                notebook_cid=str(parameters.get("notebook_cid") or "root"),
            )
        if action == "notes.update":
            return self._api().update_note(
                self._required(parameters, "note"),
                title=(str(parameters["title"]) if "title" in parameters else None),
                content=(str(parameters["content"]) if "content" in parameters else None),
                content_format=str(parameters.get("content_format") or "plain"),
            )
        if action == "notes.delete":
            return self._api().delete_note(self._required(parameters, "note"))
        if action == "inbox.notices.list":
            return self._api().list_inbox_notices(
                scope=str(parameters.get("scope") or "received"),
                search=str(parameters.get("search") or ""),
                sender=str(parameters.get("sender") or ""),
                start_time=str(parameters.get("start_time") or ""),
                end_time=str(parameters.get("end_time") or ""),
                max_items=self._integer(parameters.get("max_items", 1000), "max_items"),
            )
        if action == "inbox.notice.read":
            return self._api().read_inbox_notice(
                self._required(parameters, "notice"),
                scope=str(parameters.get("scope") or "received"),
            )
        if action == "inbox.notice.mark_unread":
            return self._api().mark_inbox_notice_unread(
                self._required(parameters, "notice"),
                scope=str(parameters.get("scope") or "received"),
            )
        if action == "inbox.notice.top_status.update":
            return self._api().set_inbox_notice_top_status(
                self._required(parameters, "notice"),
                self._boolean(parameters.get("top"), "top"),
                scope=str(parameters.get("scope") or "received"),
            )
        if action == "inbox.notice.collect_status.update":
            return self._api().set_inbox_notice_collect_status(
                self._required(parameters, "notice"),
                self._boolean(parameters.get("collect"), "collect"),
                scope=str(parameters.get("scope") or "received"),
            )
        if action == "inbox.notice.delete":
            return self._api().delete_inbox_notice(
                self._required(parameters, "notice"),
                scope=str(parameters.get("scope") or "received"),
            )
        if action == "inbox.notice.send":
            return self._api().send_personal_notice(
                self._string_list(parameters.get("recipients"), "recipients"),
                self._required(parameters, "title"),
                self._required(parameters, "content"),
                content_format=str(parameters.get("content_format") or "plain"),
                allow_comments=self._boolean(
                    parameters.get("allow_comments", True), "allow_comments"
                ),
                show_comments=self._boolean(parameters.get("show_comments", True), "show_comments"),
                hide_read_status=self._boolean(
                    parameters.get("hide_read_status", False), "hide_read_status"
                ),
                forbid_forwarding=self._boolean(
                    parameters.get("forbid_forwarding", False), "forbid_forwarding"
                ),
                permission_password=str(parameters.get("permission_password") or ""),
            )
        if action == "inbox.drafts.list":
            return self._api().list_personal_notice_drafts(
                search=str(parameters.get("search") or ""),
                max_items=self._integer(parameters.get("max_items", 1000), "max_items"),
            )
        if action == "inbox.draft.save":
            recipients = (
                self._string_list(parameters.get("recipients"), "recipients")
                if parameters.get("recipients") is not None
                else None
            )
            return self._api().save_personal_notice_draft(
                self._required(parameters, "title"),
                self._required(parameters, "content"),
                recipients=recipients,
                draft_query=str(parameters.get("draft") or ""),
                content_format=str(parameters.get("content_format") or "plain"),
                allow_comments=self._boolean(
                    parameters.get("allow_comments", True), "allow_comments"
                ),
                show_comments=self._boolean(parameters.get("show_comments", True), "show_comments"),
                hide_read_status=self._boolean(
                    parameters.get("hide_read_status", False), "hide_read_status"
                ),
                forbid_forwarding=self._boolean(
                    parameters.get("forbid_forwarding", False), "forbid_forwarding"
                ),
            )
        if action == "inbox.draft.delete":
            return self._api().delete_personal_notice_draft(self._required(parameters, "draft"))
        if action == "inbox.folders.list":
            return self._api().list_inbox_folders()
        if action == "inbox.folder.filters.read":
            return self._api().read_inbox_folder_filters(self._required(parameters, "folder"))
        if action == "inbox.folder.notices.list":
            return self._api().list_inbox_folder_notices(
                self._required(parameters, "folder"),
                scope=str(parameters.get("scope") or "received"),
                search=str(parameters.get("search") or ""),
                sender=str(parameters.get("sender") or ""),
                start_time=str(parameters.get("start_time") or ""),
                end_time=str(parameters.get("end_time") or ""),
                max_items=self._integer(parameters.get("max_items", 1000), "max_items"),
            )
        if action == "inbox.folder.create":
            return self._api().create_inbox_folder(
                self._required(parameters, "name"),
                sender_rules=parameters.get("sender_rules"),
                keywords=parameters.get("keywords"),
            )
        if action == "inbox.folder.update":
            return self._api().update_inbox_folder(
                self._required(parameters, "folder"),
                name=(str(parameters["name"]) if "name" in parameters else None),
                sender_rules=parameters.get("sender_rules"),
                keywords=parameters.get("keywords"),
            )
        if action == "inbox.folder.delete":
            return self._api().delete_inbox_folder(self._required(parameters, "folder"))
        if action == "inbox.folders.reorder":
            return self._api().reorder_inbox_folders(
                self._string_list(parameters.get("folders"), "folders"),
                top=self._boolean(parameters.get("top", False), "top"),
            )
        if action == "inbox.notices.move":
            return self._api().move_inbox_notices(
                self._string_list(parameters.get("notices"), "notices"),
                self._required(parameters, "destination_folder"),
                scope=str(parameters.get("scope") or "received"),
                source_folder=str(parameters.get("source_folder") or ""),
            )
        if action == "inbox.recycle.list":
            return self._api().list_inbox_recycle(
                search=str(parameters.get("search") or ""),
                max_items=self._integer(parameters.get("max_items", 1000), "max_items"),
            )
        if action == "inbox.recycle.restore":
            return self._api().restore_inbox_recycle_notices(
                self._string_list(parameters.get("notices"), "notices")
            )
        if action == "inbox.recycle.items.delete":
            return self._api().permanently_delete_inbox_recycle_notices(
                self._string_list(parameters.get("notices"), "notices")
            )
        if action == "inbox.recycle.empty":
            return self._api().empty_inbox_recycle()
        if action == "contacts.units.list":
            return self._api().list_contact_units()
        if action == "contacts.departments.list":
            return self._api().list_contact_departments(
                self._required(parameters, "fid"),
                parent_id=str(parameters.get("parent_id") or "2C89C38F937992D2"),
                department_type=str(parameters.get("department_type") or "unit"),
            )
        if action == "contacts.department.members.list":
            return self._api().list_contact_department_members(
                self._required(parameters, "fid"),
                self._required(parameters, "department_id"),
                search=str(parameters.get("search") or ""),
                max_items=self._integer(parameters.get("max_items", 1000), "max_items"),
            )
        if action == "contacts.people.search":
            return self._api().search_contact_people(
                self._required(parameters, "search"),
                fid=str(parameters.get("fid") or ""),
                department_id=str(parameters.get("department_id") or ""),
                mode=self._integer(parameters.get("mode", -1), "mode"),
                max_items=self._integer(parameters.get("max_items", 300), "max_items"),
            )
        if action == "contacts.relations.list":
            return self._api().list_contact_relations(
                str(parameters.get("relation") or "followers"),
                max_items=self._integer(parameters.get("max_items", 1000), "max_items"),
            )
        if action == "contacts.groups.list":
            return self._api().list_contact_groups(search=str(parameters.get("search") or ""))
        if action == "contacts.group.members.list":
            return self._api().list_contact_group_members(
                self._required(parameters, "group"),
                search=str(parameters.get("search") or ""),
                max_items=self._integer(parameters.get("max_items", 1000), "max_items"),
            )
        if action == "contacts.chatgroups.list":
            return self._api().list_contact_chatgroups(
                max_items=self._integer(parameters.get("max_items", 1000), "max_items")
            )
        if action == "contacts.chatgroup.members.list":
            return self._api().list_contact_chatgroup_members(
                self._required(parameters, "chatgroup"),
                max_items=self._integer(parameters.get("max_items", 1000), "max_items"),
            )
        if action == "contacts.teams.list":
            return self._api().list_contact_teams()
        if action == "contacts.team.members.list":
            return self._api().list_contact_team_members(
                self._required(parameters, "team"),
                max_items=self._integer(parameters.get("max_items", 1000), "max_items"),
            )
        if action == "contacts.follow_status.update":
            return self._api().set_contact_follow_status(
                self._required(parameters, "person"),
                self._boolean(parameters.get("followed"), "followed"),
            )
        if action == "contacts.team.create":
            return self._api().create_contact_team(
                self._required(parameters, "name"),
                self._string_list(parameters.get("members"), "members"),
            )
        if action == "contacts.team.rename":
            return self._api().rename_contact_team(
                self._required(parameters, "team"),
                self._required(parameters, "name"),
            )
        if action == "contacts.team.members.add":
            return self._api().add_contact_team_members(
                self._required(parameters, "team"),
                self._string_list(parameters.get("members"), "members"),
            )
        if action == "contacts.team.member.remove":
            return self._api().remove_contact_team_member(
                self._required(parameters, "team"),
                self._required(parameters, "member"),
            )
        if action == "contacts.team.delete":
            return self._api().delete_contact_team(self._required(parameters, "team"))
        if action == "contacts.team.exit":
            return self._api().exit_contact_team(self._required(parameters, "team"))
        if action == "groups.list":
            return self._api().list_personal_groups(
                folder=str(parameters.get("folder") or ""),
                search=str(parameters.get("search") or ""),
            )
        if action == "groups.read":
            return self._api().read_personal_group(self._required(parameters, "group"))
        if action == "groups.create":
            return self._api().create_personal_group(
                self._required(parameters, "name"),
                description=str(parameters.get("description") or ""),
                folder=str(parameters.get("folder") or ""),
                logo_url=str(parameters.get("logo_url") or ""),
            )
        if action == "groups.update":
            return self._api().update_personal_group(
                self._required(parameters, "group"),
                name=(str(parameters["name"]) if "name" in parameters else None),
                description=(
                    str(parameters["description"]) if "description" in parameters else None
                ),
            )
        if action == "groups.logo.update":
            return self._api().update_personal_group_logo(
                self._required(parameters, "group"),
                self._required(parameters, "file"),
            )
        if action == "groups.modules.list":
            return self._api().list_personal_group_modules(self._required(parameters, "group"))
        if action == "groups.modules.update":
            return self._api().update_personal_group_modules(
                self._required(parameters, "group"),
                self._string_list(parameters.get("enabled_type_ids"), "enabled_type_ids"),
            )
        if action == "groups.settings.update":
            changes = parameters.get("changes")
            if not isinstance(changes, dict) or not changes:
                raise ActionRuntimeError(
                    "changes must be a non-empty personal group setting mapping"
                )
            start_time = parameters.get("sign_ban_start_time")
            return self._api().update_personal_group_settings(
                self._required(parameters, "group"),
                changes,
                sign_ban_start_time=(
                    self._integer(start_time, "sign_ban_start_time")
                    if start_time is not None
                    else None
                ),
            )
        if action == "groups.levels.list":
            return self._api().list_personal_group_levels(self._required(parameters, "group"))
        if action == "groups.levels.series.update":
            return self._api().set_personal_group_level_series(
                self._required(parameters, "group"),
                self._required(parameters, "series"),
            )
        if action == "groups.levels.custom.update":
            levels = parameters.get("levels")
            if not isinstance(levels, list):
                raise ActionRuntimeError("levels must be a list of 15 personal group levels")
            return self._api().update_personal_group_custom_levels(
                self._required(parameters, "group"),
                levels,
            )
        if action == "groups.growth_rules.list":
            return self._api().list_personal_group_growth_rules(self._required(parameters, "group"))
        if action == "groups.growth_rules.series.update":
            return self._api().set_personal_group_growth_rule_series(
                self._required(parameters, "group"),
                self._required(parameters, "series"),
            )
        if action == "groups.growth_rules.update":
            changes = parameters.get("changes")
            if not isinstance(changes, dict) or not changes:
                raise ActionRuntimeError(
                    "changes must be a non-empty personal group growth-rule mapping"
                )
            return self._api().update_personal_group_growth_rules(
                self._required(parameters, "group"),
                changes,
            )
        if action == "groups.speaking_rules.update":
            changes = parameters.get("changes")
            if not isinstance(changes, dict):
                raise ActionRuntimeError("changes must be a personal group speaking-rule mapping")
            attachment_rules = parameters.get("attachment_rules")
            if attachment_rules is not None and not isinstance(attachment_rules, dict):
                raise ActionRuntimeError("attachment_rules must be an object")
            return self._api().update_personal_group_speaking_rules(
                self._required(parameters, "group"),
                changes,
                attachment_rules=attachment_rules,
            )
        if action == "groups.notice.send":
            return self._api().send_personal_group_notice(
                self._required(parameters, "group"),
                self._required(parameters, "title"),
                self._required(parameters, "content"),
                pcode=str(parameters.get("pcode") or ""),
            )
        if action == "groups.review_reminders.list":
            return self._api().list_personal_group_review_reminders(
                self._required(parameters, "group")
            )
        if action == "groups.review_reminder.create":
            return self._api().create_personal_group_review_reminder(
                self._required(parameters, "group"),
                self._required(parameters, "start_time"),
                self._required(parameters, "end_time"),
                self._string_list(parameters.get("weeks"), "weeks"),
                self._string_list(parameters.get("puids"), "puids"),
            )
        if action == "groups.review_reminder.update":
            weeks = parameters.get("weeks")
            puids = parameters.get("puids")
            return self._api().update_personal_group_review_reminder(
                self._required(parameters, "group"),
                self._required(parameters, "reminder"),
                start_time=(
                    str(parameters["start_time"])
                    if parameters.get("start_time") is not None
                    else None
                ),
                end_time=(
                    str(parameters["end_time"]) if parameters.get("end_time") is not None else None
                ),
                weeks=self._string_list(weeks, "weeks") if weeks is not None else None,
                puids=self._string_list(puids, "puids") if puids is not None else None,
            )
        if action == "groups.review_reminders.delete":
            return self._api().delete_personal_group_review_reminders(
                self._required(parameters, "group"),
                self._string_list(parameters.get("reminders"), "reminders"),
            )
        if action == "groups.labels.list":
            return self._api().list_personal_group_labels(self._required(parameters, "group"))
        if action == "groups.label.create":
            return self._api().create_personal_group_label(
                self._required(parameters, "group"),
                self._required(parameters, "name"),
            )
        if action == "groups.label.rename":
            return self._api().rename_personal_group_label(
                self._required(parameters, "group"),
                self._required(parameters, "label"),
                self._required(parameters, "name"),
            )
        if action == "groups.labels.reorder":
            return self._api().reorder_personal_group_labels(
                self._required(parameters, "group"),
                self._string_list(parameters.get("labels"), "labels"),
            )
        if action == "groups.labels.delete":
            return self._api().delete_personal_group_labels(
                self._required(parameters, "group"),
                self._string_list(parameters.get("labels"), "labels"),
            )
        if action == "groups.deletion_reasons.list":
            return self._api().list_personal_group_deletion_reasons(
                self._required(parameters, "group")
            )
        if action == "groups.deletion_reason.create":
            return self._api().create_personal_group_deletion_reason(
                self._required(parameters, "group"),
                self._required(parameters, "name"),
            )
        if action == "groups.deletion_reason.rename":
            return self._api().rename_personal_group_deletion_reason(
                self._required(parameters, "group"),
                self._required(parameters, "reason"),
                self._required(parameters, "name"),
            )
        if action == "groups.deletion_reasons.delete":
            return self._api().delete_personal_group_deletion_reasons(
                self._required(parameters, "group"),
                self._string_list(parameters.get("reasons"), "reasons"),
            )
        if action == "groups.recycle.list":
            return self._api().list_personal_group_recycle_items(
                self._required(parameters, "group")
            )
        if action == "groups.recycle.restore":
            return self._api().restore_personal_group_recycle_items(
                self._required(parameters, "group"),
                self._string_list(parameters.get("items"), "items"),
            )
        if action == "groups.recycle.items.delete":
            return self._api().permanently_delete_personal_group_recycle_items(
                self._required(parameters, "group"),
                self._string_list(parameters.get("items"), "items"),
            )
        if action == "groups.recycle.empty":
            return self._api().empty_personal_group_recycle(self._required(parameters, "group"))
        if action == "groups.exports.list":
            return self._api().list_personal_group_exports(self._required(parameters, "group"))
        if action == "groups.members.export.create":
            return self._api().create_personal_group_member_export(
                self._required(parameters, "group")
            )
        if action == "groups.export.download":
            return self._api().download_personal_group_export(
                self._required(parameters, "group"),
                self._required(parameters, "export"),
                self._required(parameters, "output_path"),
                overwrite=self._boolean(parameters.get("overwrite", False), "overwrite"),
                wait_seconds=self._integer(parameters.get("wait_seconds", 120), "wait_seconds"),
            )
        if action == "groups.export.wait":
            return self._api().wait_personal_group_export(
                self._required(parameters, "group"),
                self._required(parameters, "export"),
                timeout_seconds=self._integer(
                    parameters.get("timeout_seconds", 120), "timeout_seconds"
                ),
                poll_seconds=self._integer(parameters.get("poll_seconds", 2), "poll_seconds"),
            )
        if action == "groups.export.retry":
            return self._api().retry_personal_group_export(
                self._required(parameters, "group"),
                self._required(parameters, "export"),
            )
        if action == "groups.export.cancel":
            return self._api().cancel_personal_group_export(
                self._required(parameters, "group"),
                self._required(parameters, "export"),
            )
        if action == "groups.activities.list":
            return self._api().list_personal_group_activities(
                self._required(parameters, "group"),
                status=str(parameters.get("status") or "all"),
                max_items=self._integer(parameters.get("max_items", 1000), "max_items"),
            )
        if action == "groups.activity.image.upload":
            return self._api().upload_personal_group_activity_image(
                self._required(parameters, "file")
            )
        if action == "groups.activity.create":
            return self._api().create_personal_group_activity(
                self._required(parameters, "group"),
                self._required(parameters, "title"),
                online=self._boolean(parameters.get("online", False), "online"),
                app_link=str(parameters.get("app_link") or ""),
                pc_link=str(parameters.get("pc_link") or ""),
                app_image_url=str(parameters.get("app_image_url") or ""),
                pc_image_url=str(parameters.get("pc_image_url") or ""),
                app_image_width=self._integer(
                    parameters.get("app_image_width", 0), "app_image_width"
                ),
                app_image_height=self._integer(
                    parameters.get("app_image_height", 0), "app_image_height"
                ),
                pc_image_width=self._integer(parameters.get("pc_image_width", 0), "pc_image_width"),
                pc_image_height=self._integer(
                    parameters.get("pc_image_height", 0), "pc_image_height"
                ),
            )
        if action == "groups.activity.update":
            integer_fields = (
                "app_image_width",
                "app_image_height",
                "pc_image_width",
                "pc_image_height",
            )
            integer_values = {
                field: self._integer(parameters[field], field)
                for field in integer_fields
                if field in parameters
            }
            return self._api().update_personal_group_activity(
                self._required(parameters, "group"),
                self._required(parameters, "activity"),
                title=(str(parameters["title"]) if "title" in parameters else None),
                app_link=(str(parameters["app_link"]) if "app_link" in parameters else None),
                pc_link=(str(parameters["pc_link"]) if "pc_link" in parameters else None),
                app_image_url=(
                    str(parameters["app_image_url"]) if "app_image_url" in parameters else None
                ),
                pc_image_url=(
                    str(parameters["pc_image_url"]) if "pc_image_url" in parameters else None
                ),
                **integer_values,
            )
        if action == "groups.activity.online_status.update":
            return self._api().set_personal_group_activity_online_status(
                self._required(parameters, "group"),
                self._required(parameters, "activity"),
                self._boolean(parameters.get("online"), "online"),
            )
        if action == "groups.activities.reorder":
            return self._api().reorder_personal_group_activities(
                self._required(parameters, "group"),
                self._string_list(parameters.get("activities"), "activities"),
            )
        if action == "groups.activity.delete":
            return self._api().delete_personal_group_activity(
                self._required(parameters, "group"),
                self._required(parameters, "activity"),
            )
        if action == "groups.top_status.update":
            return self._api().set_personal_group_top_status(
                self._required(parameters, "group"),
                self._boolean(parameters.get("top"), "top"),
            )
        if action == "groups.move":
            return self._api().move_personal_group(
                self._required(parameters, "group"),
                self._required(parameters, "destination_folder"),
            )
        if action == "groups.quit":
            return self._api().quit_personal_group(self._required(parameters, "group"))
        if action == "groups.dismiss":
            return self._api().dismiss_personal_group(self._required(parameters, "group"))
        if action == "groups.members.list":
            return self._api().list_personal_group_members(
                self._required(parameters, "group"),
                search=str(parameters.get("search") or ""),
            )
        if action == "groups.members.bulk_import.status":
            return self._api().read_personal_group_bulk_import_status(
                self._required(parameters, "group")
            )
        if action == "groups.members.bulk_import.template.download":
            return self._api().download_personal_group_bulk_import_template(
                self._required(parameters, "group"),
                self._required(parameters, "output_path"),
                overwrite=self._boolean(parameters.get("overwrite", False), "overwrite"),
            )
        if action == "groups.members.bulk_import":
            return self._api().bulk_import_personal_group_members(
                self._required(parameters, "group"),
                self._required(parameters, "file"),
            )
        if action == "groups.member.read":
            return self._api().read_personal_group_member(
                self._required(parameters, "group"),
                self._required(parameters, "member"),
            )
        if action == "groups.member.permissions.read":
            return self._api().read_personal_group_member_permissions(
                self._required(parameters, "group"),
                self._required(parameters, "member"),
            )
        if action == "groups.member.permissions.update":
            changes = parameters.get("changes")
            if not isinstance(changes, dict) or not changes:
                raise ActionRuntimeError("changes must be a non-empty manager permission mapping")
            return self._api().update_personal_group_member_permissions(
                self._required(parameters, "group"),
                self._required(parameters, "member"),
                changes,
            )
        if action == "groups.member.sources.list":
            return self._api().list_personal_group_member_sources(
                self._required(parameters, "group")
            )
        if action == "groups.member.candidates.list":
            return self._api().list_personal_group_member_candidates(
                self._required(parameters, "group"),
                source_type=self._required(parameters, "source_type"),
                source=self._required(parameters, "source"),
                fid=str(parameters.get("fid") or ""),
                search=str(parameters.get("search") or ""),
                account_type=int(parameters.get("account_type") or 0),
            )
        if action == "groups.members.add":
            return self._api().add_personal_group_members(
                self._required(parameters, "group"),
                self._string_list(parameters.get("puids"), "puids"),
            )
        if action == "groups.member.manager_status.update":
            return self._api().set_personal_group_member_manager_status(
                self._required(parameters, "group"),
                self._required(parameters, "member"),
                self._boolean(parameters.get("manager"), "manager"),
            )
        if action == "groups.member.remove":
            return self._api().remove_personal_group_member(
                self._required(parameters, "group"),
                self._required(parameters, "member"),
            )
        if action == "groups.creator.transfer":
            return self._api().transfer_personal_group_creator(
                self._required(parameters, "group"),
                self._required(parameters, "member"),
            )
        if action == "groups.members.external.clear":
            return self._api().clear_personal_group_external_members(
                self._required(parameters, "group")
            )
        if action == "groups.folders.tree":
            return self._api().list_personal_group_folder_tree()
        if action == "groups.folders.list":
            return self._api().list_personal_group_folders(
                parent_folder=str(parameters.get("parent_folder") or ""),
                search=str(parameters.get("search") or ""),
            )
        if action == "groups.folder.create":
            return self._api().create_personal_group_folder(
                self._required(parameters, "name"),
                parent_folder=str(parameters.get("parent_folder") or ""),
            )
        if action == "groups.folder.rename":
            return self._api().rename_personal_group_folder(
                self._required(parameters, "folder"),
                self._required(parameters, "name"),
            )
        if action == "groups.folder.move":
            return self._api().move_personal_group_folder(
                self._required(parameters, "folder"),
                self._required(parameters, "destination_folder"),
            )
        if action == "groups.folder.top_status.update":
            return self._api().set_personal_group_folder_top_status(
                self._required(parameters, "folder"),
                self._boolean(parameters.get("top"), "top"),
            )
        if action == "groups.folder.delete":
            return self._api().delete_personal_group_folder(self._required(parameters, "folder"))
        if action == "groups.topics.list":
            return self._api().list_personal_group_topics(
                self._required(parameters, "group"),
                folder=str(parameters.get("folder") or ""),
                search=str(parameters.get("search") or ""),
            )
        if action == "groups.topic.read":
            return self._api().read_personal_group_topic(
                self._required(parameters, "group"),
                self._required(parameters, "topic"),
                order=int(parameters.get("order") or 2),
                reply_search=str(parameters.get("reply_search") or ""),
            )
        if action == "groups.topic.create":
            return self._api().create_personal_group_topic(
                self._required(parameters, "group"),
                str(parameters.get("title") or ""),
                str(parameters.get("content") or ""),
                folder=str(parameters.get("folder") or ""),
                anonymous=self._boolean(parameters.get("anonymous", False), "anonymous"),
            )
        if action == "groups.topic.update":
            return self._api().update_personal_group_topic(
                self._required(parameters, "group"),
                self._required(parameters, "topic"),
                title=(str(parameters["title"]) if "title" in parameters else None),
                content=(str(parameters["content"]) if "content" in parameters else None),
            )
        if action == "groups.topic.delete":
            return self._api().delete_personal_group_topic(
                self._required(parameters, "group"),
                self._required(parameters, "topic"),
            )
        if action == "groups.topic.choice_status.update":
            return self._api().set_personal_group_topic_choice_status(
                self._required(parameters, "group"),
                self._required(parameters, "topic"),
                self._boolean(parameters.get("choice"), "choice"),
            )
        if action == "groups.topic.praise_status.update":
            return self._api().set_personal_group_topic_praise_status(
                self._required(parameters, "group"),
                self._required(parameters, "topic"),
                self._boolean(parameters.get("praised"), "praised"),
            )
        if action == "groups.topics.score.set":
            return self._api().set_personal_group_topics_score(
                self._required(parameters, "group"),
                self._string_list(parameters.get("topics"), "topics"),
                self._integer(parameters.get("score"), "score"),
            )
        if action == "groups.topics.move":
            return self._api().move_personal_group_topics(
                self._required(parameters, "group"),
                self._string_list(parameters.get("topics"), "topics"),
                self._required(parameters, "destination_folder"),
            )
        if action == "groups.topics.delete":
            return self._api().delete_personal_group_topics(
                self._required(parameters, "group"),
                self._string_list(parameters.get("topics"), "topics"),
            )
        if action == "groups.topic.reply.create":
            return self._api().create_personal_group_topic_reply(
                self._required(parameters, "group"),
                self._required(parameters, "topic"),
                self._required(parameters, "content"),
                reply_to=str(parameters.get("reply_to") or ""),
                anonymous=self._boolean(parameters.get("anonymous", False), "anonymous"),
            )
        if action == "groups.topic.reply.update":
            return self._api().update_personal_group_topic_reply(
                self._required(parameters, "group"),
                self._required(parameters, "topic"),
                self._required(parameters, "reply"),
                self._required(parameters, "content"),
            )
        if action == "groups.topic.reply.delete":
            return self._api().delete_personal_group_topic_reply(
                self._required(parameters, "group"),
                self._required(parameters, "topic"),
                self._required(parameters, "reply"),
            )
        if action == "groups.topic.folders.tree":
            return self._api().list_personal_group_topic_folder_tree(
                self._required(parameters, "group")
            )
        if action == "groups.topic.top_status.update":
            return self._api().set_personal_group_topic_top_status(
                self._required(parameters, "group"),
                self._required(parameters, "topic"),
                self._boolean(parameters.get("top"), "top"),
            )
        if action == "groups.topic.move":
            return self._api().move_personal_group_topic(
                self._required(parameters, "group"),
                self._required(parameters, "topic"),
                self._required(parameters, "destination_folder"),
            )
        if action == "groups.topic.folder.create":
            return self._api().create_personal_group_topic_folder(
                self._required(parameters, "group"),
                self._required(parameters, "name"),
                parent_folder=str(parameters.get("parent_folder") or ""),
            )
        if action == "groups.topic.folder.rename":
            return self._api().rename_personal_group_topic_folder(
                self._required(parameters, "group"),
                self._required(parameters, "folder"),
                self._required(parameters, "name"),
            )
        if action == "groups.topic.folder.move":
            return self._api().move_personal_group_topic_folder(
                self._required(parameters, "group"),
                self._required(parameters, "folder"),
                self._required(parameters, "destination_folder"),
            )
        if action == "groups.topic.folder.delete":
            return self._api().delete_personal_group_topic_folder(
                self._required(parameters, "group"),
                self._required(parameters, "folder"),
            )
        if action == "groups.topic.folders.move":
            return self._api().move_personal_group_topic_folders(
                self._required(parameters, "group"),
                self._string_list(parameters.get("folders"), "folders"),
                self._required(parameters, "destination_folder"),
            )
        if action == "groups.topic.folders.delete":
            return self._api().delete_personal_group_topic_folders(
                self._required(parameters, "group"),
                self._string_list(parameters.get("folders"), "folders"),
            )
        if action == "groups.topic.drafts.list":
            return self._api().list_personal_group_topic_drafts(
                self._required(parameters, "group"),
                search=str(parameters.get("search") or ""),
            )
        if action == "groups.topic.draft.read":
            return self._api().read_personal_group_topic_draft(
                self._required(parameters, "group"),
                self._required(parameters, "draft"),
            )
        if action == "groups.topic.draft.save":
            return self._api().save_personal_group_topic_draft(
                self._required(parameters, "group"),
                str(parameters.get("title") or ""),
                str(parameters.get("content") or ""),
                draft_query=str(parameters.get("draft") or ""),
                folder=str(parameters.get("folder") or ""),
            )
        if action == "groups.topic.draft.publish":
            return self._api().publish_personal_group_topic_draft(
                self._required(parameters, "group"),
                self._required(parameters, "draft"),
            )
        if action == "courses.list_teaching":
            courses = self._api().list_teaching_courses()
            return {"count": len(courses), "courses": courses}
        if action == "courses.list_classes":
            return self._api().list_classes(self._required(parameters, "course"))
        if action == "learning.courses.list":
            courses = self._api().list_learning_courses(
                search=str(parameters.get("search") or ""),
                folder=str(parameters.get("folder") or "0"),
            )
            return {"count": len(courses), "courses": courses}
        if action == "learning.course.modules.discover":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.discover_learning_course_modules(course)
        if action == "learning.course.module.open":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.inspect_learning_course_module(
                course,
                self._required(parameters, "module"),
            )
        if action == "learning.course.activities.list":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.list_learning_activities(
                course,
                search=str(parameters.get("search") or ""),
                status=str(parameters.get("status") or "all"),
            )
        if action == "learning.course.chapters.list":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.list_learning_chapters(
                course,
                search=str(parameters.get("search") or ""),
            )
        if action == "learning.course.discussions.list":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.list_learning_discussions(
                course,
                search=str(parameters.get("search") or ""),
                class_only=self._boolean(parameters.get("class_only", False), "class_only"),
            )
        if action == "learning.course.discussions.topic.read":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            try:
                order = int(parameters.get("order", 2))
            except (TypeError, ValueError) as exc:
                raise ActionRuntimeError("order must be 1 or 2") from exc
            return api.read_learning_discussion_topic(
                course,
                self._required(parameters, "topic"),
                class_only=self._boolean(parameters.get("class_only", False), "class_only"),
                order=order,
                reply_search=str(parameters.get("reply_search") or ""),
            )
        if action == "learning.course.discussions.topic.create":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.create_learning_discussion_topic(
                course,
                str(parameters.get("title") or ""),
                str(parameters.get("content") or ""),
                anonymous=self._boolean(parameters.get("anonymous", False), "anonymous"),
            )
        if action == "learning.course.discussions.topic.update":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.update_learning_discussion_topic(
                course,
                self._required(parameters, "topic"),
                title=(str(parameters["title"]) if parameters.get("title") is not None else None),
                content=(
                    str(parameters["content"]) if parameters.get("content") is not None else None
                ),
            )
        if action == "learning.course.discussions.topic.delete":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.delete_learning_discussion_topic(
                course,
                self._required(parameters, "topic"),
            )
        if action == "learning.course.discussions.reply.create":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.create_learning_discussion_reply(
                course,
                self._required(parameters, "topic"),
                self._required(parameters, "content"),
                reply_to=str(parameters.get("reply_to") or ""),
                anonymous=self._boolean(parameters.get("anonymous", False), "anonymous"),
            )
        if action == "learning.course.discussions.reply.update":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.update_learning_discussion_reply(
                course,
                self._required(parameters, "topic"),
                self._required(parameters, "reply"),
                self._required(parameters, "content"),
            )
        if action == "learning.course.discussions.reply.delete":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.delete_learning_discussion_reply(
                course,
                self._required(parameters, "topic"),
                self._required(parameters, "reply"),
            )
        if action == "learning.course.homeworks.list":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.list_learning_homeworks(
                course,
                search=str(parameters.get("search") or ""),
                status=str(parameters.get("status") or ""),
            )
        if action == "learning.course.homework.read":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.read_learning_homework(
                course,
                self._required(parameters, "homework"),
            )
        if action == "learning.course.homework.answer.enter":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.enter_learning_homework_answer(
                course,
                self._required(parameters, "homework"),
            )
        if action == "learning.course.homework.redo":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.redo_learning_homework(
                course,
                self._required(parameters, "homework"),
            )
        if action == "learning.course.homework.attempts.list":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.list_learning_homework_attempts(
                course,
                self._required(parameters, "homework"),
            )
        if action == "learning.course.homework.attempt.read":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.read_learning_homework_attempt(
                course,
                self._required(parameters, "homework"),
                self._required(parameters, "attempt"),
            )
        if action == "learning.course.exams.list":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.list_learning_exams(
                course,
                search=str(parameters.get("search") or ""),
                status=str(parameters.get("status") or ""),
            )
        if action == "learning.course.self_tests.list":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.list_learning_self_tests(
                course,
                search=str(parameters.get("search") or ""),
                status=str(parameters.get("status") or ""),
            )
        if action == "learning.course.materials.list":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.list_learning_materials(
                course,
                folder=str(parameters.get("folder") or ""),
                search=str(parameters.get("search") or ""),
            )
        if action == "learning.course.ai_tools.list":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.list_learning_ai_tools(course)
        if action == "learning.course.wrong_questions.summary":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.read_learning_wrong_questions(course)
        if action == "learning.course.records.read":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.read_learning_records(course)
        if action == "learning.course.knowledge_graph.list":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            level = None
            if parameters.get("level") is not None:
                level = self._integer(parameters["level"], "level")
            return api.list_learning_knowledge_graph(
                course,
                search=str(parameters.get("search") or ""),
                level=level,
            )
        if action == "learning.course.knowledge_graph.node.read":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.read_learning_knowledge_graph_node(
                course,
                self._required(parameters, "node"),
            )
        if action == "learning.course.knowledge_graph.models.list":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.list_learning_knowledge_graph_models(
                course,
                search=str(parameters.get("search") or ""),
            )
        if action == "learning.course.knowledge_graph.model.read":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.read_learning_knowledge_graph_model(
                course,
                self._required(parameters, "model"),
            )
        if action == "learning.course.integrity.read":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.read_learning_integrity(course)
        if action == "learning.course.integrity.accept":
            api = self._api()
            course = api.get_learning_course(self._required(parameters, "course"))
            return api.accept_learning_integrity(course)
        if action == "classes.create":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            return api.create_class(course, self._required(parameters, "name"))
        if action == "class.rename":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.rename_class(course, clazz, self._required(parameters, "name"))
        if action == "class.settings.read":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.read_class_settings(course, clazz)
        if action == "class.invitation.read":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.read_class_invitation(course, clazz)
        if action == "class.settings.update":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))

            def optional_boolean(key: str) -> bool | None:
                return self._boolean(parameters[key], key) if key in parameters else None

            student_limit: int | None = None
            if "student_limit" in parameters:
                try:
                    student_limit = int(parameters["student_limit"])
                except (TypeError, ValueError) as exc:
                    raise ActionRuntimeError("student_limit must be an integer") from exc
            return api.update_class_settings(
                course,
                clazz,
                allow_student_join=optional_boolean("allow_student_join"),
                join_requires_approval=optional_boolean("join_requires_approval"),
                unit_binding_requirement=(
                    str(parameters["unit_binding_requirement"])
                    if "unit_binding_requirement" in parameters
                    else None
                ),
                allow_student_withdraw=optional_boolean("allow_student_withdraw"),
                public_scope=(
                    str(parameters["public_scope"]) if "public_scope" in parameters else None
                ),
                student_limit=student_limit,
                ended=optional_boolean("ended"),
                ignore_video_restrictions=optional_boolean("ignore_video_restrictions"),
                hidden_from_students=optional_boolean("hidden_from_students"),
                semester_id=(
                    str(parameters["semester_id"]) if "semester_id" in parameters else None
                ),
                open_start=(str(parameters["open_start"]) if "open_start" in parameters else None),
                open_end=str(parameters["open_end"]) if "open_end" in parameters else None,
                application_start=(
                    str(parameters["application_start"])
                    if "application_start" in parameters
                    else None
                ),
                application_end=(
                    str(parameters["application_end"]) if "application_end" in parameters else None
                ),
            )
        if action == "class.delete":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.delete_class(course, clazz)
        if action == "class.students.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            try:
                school_status = int(parameters.get("school_status", 0))
            except (TypeError, ValueError) as exc:
                raise ActionRuntimeError("school_status must be an integer") from exc
            return api.list_class_students(
                course,
                clazz,
                search=str(parameters.get("search") or "").strip(),
                school_status=school_status,
            )
        if action == "class.student_candidates.search":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            try:
                page = int(parameters.get("page", 1))
                page_size = int(parameters.get("page_size", 30))
            except (TypeError, ValueError) as exc:
                raise ActionRuntimeError("page and page_size must be integers") from exc
            return api.search_student_bank_candidates(
                course,
                clazz,
                self._required(parameters, "query"),
                page=page,
                page_size=page_size,
            )
        if action == "class.student.add_from_bank":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.add_student_from_bank(
                course,
                clazz,
                self._required(parameters, "student"),
            )
        if action == "class.student.add_by_identity":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.add_student_by_identity(
                course,
                clazz,
                name=self._required(parameters, "name"),
                identity=self._required(parameters, "identity"),
                identity_type=str(parameters.get("identity_type") or "student_no"),
                school_id=str(parameters.get("school_id") or ""),
            )
        if action == "class.student.remove":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.remove_student(
                course,
                clazz,
                self._required(parameters, "student"),
            )
        if action == "class.join_applications.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.list_class_join_applications(course, clazz)
        if action == "class.join_application.decide":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.decide_class_join_application(
                course,
                clazz,
                self._required(parameters, "application"),
                self._required(parameters, "decision"),
            )
        if action == "class.student.move":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            source_clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.move_student(
                course,
                source_clazz,
                self._required(parameters, "target_clazz"),
                self._required(parameters, "student"),
            )
        if action == "class.student.access_logs.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            try:
                year = int(parameters["year"]) if parameters.get("year") is not None else None
                month = int(parameters["month"]) if parameters.get("month") is not None else None
                day = int(parameters.get("day", 0))
            except (TypeError, ValueError) as exc:
                raise ActionRuntimeError("year, month, and day must be integers") from exc
            return api.list_student_access_logs(
                course,
                clazz,
                self._required(parameters, "student"),
                year=year,
                month=month,
                day=day,
            )
        if action == "course.operation_logs.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.list_course_operation_logs(
                course,
                clazz,
                module=str(parameters.get("module") or "").strip(),
                search=str(parameters.get("search") or "").strip(),
                start_date=str(parameters.get("start_date") or "").strip(),
                end_date=str(parameters.get("end_date") or "").strip(),
            )
        if action == "class.student_join_logs.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            try:
                join_type = int(parameters.get("join_type", -1))
            except (TypeError, ValueError) as exc:
                raise ActionRuntimeError("join_type must be -1, 0, 1, 2, or 3") from exc
            return api.list_student_join_logs(
                course,
                clazz,
                join_type=join_type,
                search=str(parameters.get("search") or "").strip(),
            )
        if action == "class.student_leave_logs.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.list_student_leave_logs(
                course,
                clazz,
                search=str(parameters.get("search") or "").strip(),
            )
        if action == "class.student.restore":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.restore_student_from_leave_log(
                course,
                clazz,
                self._required(parameters, "student"),
            )
        if action == "course.teachers.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            try:
                role = int(parameters.get("role", 0))
            except (TypeError, ValueError) as exc:
                raise ActionRuntimeError("role must be an integer") from exc
            return api.list_course_teachers(
                course,
                clazz,
                search=str(parameters.get("search") or "").strip(),
                role=role,
            )
        if action == "course.teacher_candidates.search":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            try:
                page = int(parameters.get("page", 1))
            except (TypeError, ValueError) as exc:
                raise ActionRuntimeError("page must be an integer") from exc
            return api.search_teacher_bank_candidates(
                course,
                clazz,
                self._required(parameters, "query"),
                role=str(parameters.get("role") or "teacher"),
                page=page,
            )
        if action == "course.teacher.add_from_bank":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.add_course_teacher_from_bank(
                course,
                clazz,
                self._required(parameters, "teacher"),
                role=str(parameters.get("role") or "teacher"),
            )
        if action == "course.teacher.add_by_identity":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.add_course_teacher_by_identity(
                course,
                clazz,
                name=self._required(parameters, "name"),
                identity=self._required(parameters, "identity"),
                identity_type=str(parameters.get("identity_type") or "employee_no"),
                role=str(parameters.get("role") or "teacher"),
                school_id=str(parameters.get("school_id") or ""),
            )
        if action == "course.teacher.remove":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.remove_course_teacher(
                course,
                clazz,
                self._required(parameters, "teacher"),
            )
        if action == "course.teacher.permissions.read":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.read_course_teacher_permissions(
                course,
                clazz,
                self._required(parameters, "teacher"),
            )
        if action == "course.teacher.permissions.update":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            changes = parameters.get("changes")
            if not isinstance(changes, dict) or not changes:
                raise ActionRuntimeError("changes must be a non-empty permission mapping")
            return api.update_course_teacher_permissions(
                course,
                clazz,
                self._required(parameters, "teacher"),
                changes,
            )
        if action == "course.grade_weights.read":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.read_grade_weights(course, clazz)
        if action == "course.grades.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.list_course_grades(
                course,
                clazz,
                search=str(parameters.get("search") or "").strip(),
                raw_scores=self._boolean(parameters.get("raw_scores", False), "raw_scores"),
                sort=str(parameters.get("sort") or "loginName").strip(),
                descending=self._boolean(parameters.get("descending", False), "descending"),
            )
        if action == "course.grade_visibility.read":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.read_grade_visibility(course, clazz)
        if action == "course.grade_visibility.set":
            if "visible_classes" not in parameters:
                raise ActionRuntimeError("missing required parameter: visible_classes")
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.set_grade_visibility(
                course,
                clazz,
                self._string_list(parameters["visible_classes"], "visible_classes"),
                scheduled_open=self._boolean(
                    parameters.get("scheduled_open", False), "scheduled_open"
                ),
                open_at=str(parameters.get("open_at") or "").strip(),
                students_can_view_rank=self._boolean(
                    parameters.get("students_can_view_rank", False),
                    "students_can_view_rank",
                ),
                students_can_view_class_average=self._boolean(
                    parameters.get("students_can_view_class_average", False),
                    "students_can_view_class_average",
                ),
            )
        if action == "course.grade_override.set":
            if "score" not in parameters:
                raise ActionRuntimeError("missing required parameter: score")
            raw_score = parameters.get("score")
            if raw_score is None or str(raw_score).strip().lower() in {
                "clear",
                "auto",
                "automatic",
                "恢复自动",
            }:
                score: int | float | None = None
            else:
                try:
                    parsed_score = float(raw_score)
                except (TypeError, ValueError) as exc:
                    raise ActionRuntimeError(
                        "score must be 0-100 or clear to restore automatic calculation"
                    ) from exc
                score = int(parsed_score) if parsed_score.is_integer() else parsed_score
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.set_course_grade_override(
                course,
                clazz,
                self._required(parameters, "student"),
                score,
            )
        if action == "course.learning_progress.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.list_course_learning_progress(
                course,
                clazz,
                search=str(parameters.get("search") or "").strip(),
                sort=str(parameters.get("sort") or "loginName").strip(),
                descending=self._boolean(parameters.get("descending", False), "descending"),
            )
        if action == "course.study_monitor.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            try:
                anomaly_type = int(parameters.get("anomaly_type", 0))
            except (TypeError, ValueError) as exc:
                raise ActionRuntimeError("anomaly_type must be 0, 1, 2, or 4") from exc
            return api.list_study_monitor(
                course,
                clazz,
                search=str(parameters.get("search") or "").strip(),
                only_abnormal=self._boolean(
                    parameters.get("only_abnormal", False), "only_abnormal"
                ),
                anomaly_type=anomaly_type,
            )
        if action == "course.study_monitor.remind":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.send_study_monitor_reminder(
                course,
                clazz,
                self._required(parameters, "student"),
                self._required(parameters, "title"),
                self._required(parameters, "content"),
            )
        if action == "course.study_monitor.clear":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.clear_study_monitor_anomaly(
                course,
                clazz,
                self._required(parameters, "student"),
            )
        if action in {"course.modules.discover", "course.module.open"}:
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            if action == "course.modules.discover":
                return api.discover_course_modules(course, clazz)
            return api.inspect_course_module(course, clazz, self._required(parameters, "module"))
        if action.startswith("knowledge_hub."):
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            if action == "knowledge_hub.status.read":
                return api.read_knowledge_hub_status(course, clazz)
            if action == "knowledge_hub.bases.list":
                return api.list_knowledge_hub_bases(
                    course,
                    clazz,
                    module=str(parameters.get("module") or "NORMAL_BASE"),
                    page=self._integer(parameters.get("page", 1), "page"),
                    page_size=self._integer(parameters.get("page_size", 100), "page_size"),
                    category=self._integer(parameters.get("category", -1), "category"),
                    state=self._integer(parameters.get("state", -1), "state"),
                    creator=str(parameters.get("creator") or ""),
                    search=str(parameters.get("search") or ""),
                    begin_time=str(parameters.get("begin_time") or ""),
                    end_time=str(parameters.get("end_time") or ""),
                )
            if action == "knowledge_hub.base.read":
                return api.read_knowledge_hub_base(
                    course,
                    clazz,
                    self._required(parameters, "base"),
                    module=str(parameters.get("module") or "NORMAL_BASE"),
                )
            if action == "knowledge_hub.statistics.read":
                return api.read_knowledge_hub_statistics(
                    course,
                    clazz,
                    module=str(parameters.get("module") or "NORMAL_BASE"),
                )
            if action == "knowledge_hub.base.create":
                split_rule = parameters.get("split_rule")
                if split_rule is not None and not isinstance(split_rule, dict):
                    raise ActionRuntimeError("split_rule must be a JSON object")
                return api.create_knowledge_hub_base(
                    course,
                    clazz,
                    self._required(parameters, "name"),
                    self._required(parameters, "description"),
                    category=self._integer(parameters.get("category", 0), "category"),
                    cover=str(parameters.get("cover") or ""),
                    split_rule=split_rule,
                )
            if action == "knowledge_hub.base.update":
                split_rule = parameters.get("split_rule")
                if split_rule is not None and not isinstance(split_rule, dict):
                    raise ActionRuntimeError("split_rule must be a JSON object")
                changes = {
                    key: parameters[key]
                    for key in ("name", "description", "cover")
                    if key in parameters and parameters[key] is not None
                }
                if split_rule is not None:
                    changes["split_rule"] = split_rule
                return api.update_knowledge_hub_base(
                    course,
                    clazz,
                    self._required(parameters, "base"),
                    **changes,
                )
            if action == "knowledge_hub.base.availability.update":
                if "enabled" not in parameters:
                    raise ActionRuntimeError("missing required parameter: enabled")
                return api.set_knowledge_hub_base_availability(
                    course,
                    clazz,
                    self._required(parameters, "base"),
                    self._boolean(parameters["enabled"], "enabled"),
                )
            if action == "knowledge_hub.base.priority.update":
                if "priority" not in parameters:
                    raise ActionRuntimeError("missing required parameter: priority")
                return api.set_knowledge_hub_base_priority(
                    course,
                    clazz,
                    self._required(parameters, "base"),
                    self._boolean(parameters["priority"], "priority"),
                )
            if action == "knowledge_hub.base.share.update":
                if "shared" not in parameters:
                    raise ActionRuntimeError("missing required parameter: shared")
                return api.set_knowledge_hub_base_share(
                    course,
                    clazz,
                    self._required(parameters, "base"),
                    self._boolean(parameters["shared"], "shared"),
                )
            if action == "knowledge_hub.base.delete":
                return api.delete_knowledge_hub_base(
                    course, clazz, self._required(parameters, "base")
                )
            if action == "knowledge_hub.documents.list":
                return api.list_knowledge_hub_documents(
                    course,
                    clazz,
                    self._required(parameters, "base"),
                    page=self._integer(parameters.get("page", 1), "page"),
                    page_size=self._integer(parameters.get("page_size", 100), "page_size"),
                    state=str(parameters.get("state") or ""),
                    source=str(parameters.get("source") or ""),
                    search=str(parameters.get("search") or ""),
                    classify_id=str(parameters.get("classify_id") or ""),
                    file_type=str(parameters.get("file_type") or ""),
                    begin_time=str(parameters.get("begin_time") or ""),
                    end_time=str(parameters.get("end_time") or ""),
                    order=str(parameters.get("order") or ""),
                )
            if action == "knowledge_hub.document.download":
                return api.download_knowledge_hub_document(
                    course,
                    clazz,
                    self._required(parameters, "base"),
                    self._required(parameters, "document"),
                    self._required(parameters, "output_path"),
                    overwrite=self._boolean(parameters.get("overwrite", False), "overwrite"),
                )
            if action == "knowledge_hub.document.upload":
                split_rule = parameters.get("split_rule")
                if split_rule is not None and not isinstance(split_rule, dict):
                    raise ActionRuntimeError("split_rule must be a JSON object")
                return api.upload_knowledge_hub_document(
                    course,
                    clazz,
                    self._required(parameters, "base"),
                    self._required(parameters, "file"),
                    classify_id=str(parameters.get("classify_id") or ""),
                    split_rule=split_rule,
                )
            if action == "knowledge_hub.document.delete":
                return api.delete_knowledge_hub_document(
                    course,
                    clazz,
                    self._required(parameters, "base"),
                    self._required(parameters, "document"),
                )
        if action.startswith("ai_workbench."):
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            if action == "ai_workbench.groups.list":
                return api.list_ai_workbench_groups(course, clazz)
            if action == "ai_workbench.group.create":
                return api.create_ai_workbench_group(
                    course, clazz, self._required(parameters, "name")
                )
            if action == "ai_workbench.group.rename":
                return api.rename_ai_workbench_group(
                    course,
                    clazz,
                    self._required(parameters, "group"),
                    self._required(parameters, "name"),
                )
            if action == "ai_workbench.group.reorder":
                return api.reorder_ai_workbench_groups(
                    course,
                    clazz,
                    self._string_list(parameters.get("groups"), "groups"),
                )
            if action == "ai_workbench.group.delete":
                return api.delete_ai_workbench_group(
                    course,
                    clazz,
                    self._required(parameters, "group"),
                    allow_nonempty=self._boolean(
                        parameters.get("allow_nonempty", False), "allow_nonempty"
                    ),
                )
            if action == "ai_workbench.commands.list":
                return api.list_ai_workbench_commands(
                    course,
                    clazz,
                    group=str(parameters.get("group") or ""),
                    search=str(parameters.get("search") or ""),
                )
            if action == "ai_workbench.command.read":
                return api.read_ai_workbench_command(
                    course,
                    clazz,
                    self._required(parameters, "command"),
                    group=str(parameters.get("group") or ""),
                )
            if action == "ai_workbench.command.create":
                return api.create_ai_workbench_command(
                    course,
                    clazz,
                    self._required(parameters, "group"),
                    self._required(parameters, "name"),
                    self._required(parameters, "content"),
                    self._required(parameters, "explanation"),
                    prompt_words=str(parameters.get("prompt_words") or ""),
                    role_type=self._integer(parameters.get("role_type", 0), "role_type"),
                    classify_id=self._integer(parameters.get("classify_id", 1), "classify_id"),
                    command_ability=self._integer(
                        parameters.get("command_ability", 0), "command_ability"
                    ),
                    ability_type=self._integer(parameters.get("ability_type", 0), "ability_type"),
                )
            if action == "ai_workbench.command.update":
                optional_integer_keys = (
                    "role_type",
                    "classify_id",
                    "command_ability",
                    "ability_type",
                )
                integer_changes = {
                    key: self._integer(parameters[key], key)
                    for key in optional_integer_keys
                    if key in parameters and parameters[key] is not None
                }
                optional_text_keys = ("name", "content", "explanation", "prompt_words")
                text_changes = {
                    key: str(parameters[key])
                    for key in optional_text_keys
                    if key in parameters and parameters[key] is not None
                }
                return api.update_ai_workbench_command(
                    course,
                    clazz,
                    self._required(parameters, "command"),
                    group=str(parameters.get("group") or ""),
                    **text_changes,
                    **integer_changes,
                )
            if action == "ai_workbench.command.move":
                return api.move_ai_workbench_command(
                    course,
                    clazz,
                    self._required(parameters, "command"),
                    self._required(parameters, "target_group"),
                    group=str(parameters.get("group") or ""),
                )
            if action == "ai_workbench.command.reorder":
                return api.reorder_ai_workbench_commands(
                    course,
                    clazz,
                    self._required(parameters, "group"),
                    self._integer(parameters.get("role_type"), "role_type"),
                    self._string_list(parameters.get("commands"), "commands"),
                )
            if action == "ai_workbench.command.publish_status.update":
                if "published" not in parameters:
                    raise ActionRuntimeError("missing required parameter: published")
                return api.set_ai_workbench_command_publish_status(
                    course,
                    clazz,
                    self._required(parameters, "command"),
                    self._boolean(parameters["published"], "published"),
                    group=str(parameters.get("group") or ""),
                )
            if action == "ai_workbench.command.delete":
                return api.delete_ai_workbench_command(
                    course,
                    clazz,
                    self._required(parameters, "command"),
                    group=str(parameters.get("group") or ""),
                )
            if action == "ai_workbench.recommendations.list":
                return api.list_ai_workbench_recommendations(
                    course,
                    clazz,
                    page=self._integer(parameters.get("page", 1), "page"),
                )
            if action == "ai_workbench.recommendation.add":
                return api.add_ai_workbench_recommendation(
                    course,
                    clazz,
                    self._required(parameters, "recommendation"),
                    self._required(parameters, "group"),
                )
        if action.startswith("task_engine."):
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            if action == "task_engine.folders.list":
                return api.list_task_engine_folders(course, clazz)
            if action == "task_engine.tasks.list":
                return api.list_task_engine_tasks(
                    course,
                    clazz,
                    folder=str(parameters.get("folder") or ""),
                    search=str(parameters.get("search") or ""),
                    recycled=self._boolean(parameters.get("recycled", False), "recycled"),
                    max_items=self._integer(parameters.get("max_items", 1000), "max_items"),
                )
            if action == "task_engine.task.read":
                return api.read_task_engine_task(course, clazz, self._required(parameters, "task"))
            if action == "task_engine.folder.create":
                return api.create_task_engine_folder(
                    course, clazz, self._required(parameters, "name")
                )
            if action == "task_engine.folder.rename":
                return api.rename_task_engine_folder(
                    course,
                    clazz,
                    self._required(parameters, "folder"),
                    self._required(parameters, "name"),
                )
            if action == "task_engine.folder.delete":
                return api.delete_task_engine_folder(
                    course,
                    clazz,
                    self._required(parameters, "folder"),
                    allow_nonempty=self._boolean(
                        parameters.get("allow_nonempty", False), "allow_nonempty"
                    ),
                )
            if action == "task_engine.task.create":
                modes = (
                    self._string_list(parameters.get("selected_modes"), "selected_modes")
                    if parameters.get("selected_modes") is not None
                    else None
                )
                return api.create_task_engine_task(
                    course,
                    clazz,
                    self._required(parameters, "name"),
                    introduce=str(parameters.get("introduce") or ""),
                    rich_text=str(parameters.get("rich_text") or ""),
                    cover=str(parameters.get("cover") or ""),
                    target=str(parameters.get("target") or ""),
                    folder=str(parameters.get("folder") or ""),
                    selected_modes=modes,
                )
            if action == "task_engine.task.update":
                changes: dict[str, Any] = {}
                for key in ("name", "introduce", "rich_text", "cover", "target"):
                    if key in parameters and parameters[key] is not None:
                        changes[key] = str(parameters[key])
                if "start_date" in parameters:
                    changes["start_date"] = parameters["start_date"]
                if "end_date" in parameters:
                    changes["end_date"] = parameters["end_date"]
                if parameters.get("selected_modes") is not None:
                    changes["selected_modes"] = self._string_list(
                        parameters["selected_modes"], "selected_modes"
                    )
                if not changes:
                    raise ActionRuntimeError("task update requires at least one changed field")
                return api.update_task_engine_task(
                    course,
                    clazz,
                    self._required(parameters, "task"),
                    **changes,
                )
            if action == "task_engine.task.move":
                return api.move_task_engine_task(
                    course,
                    clazz,
                    self._required(parameters, "task"),
                    folder=str(parameters.get("folder") or ""),
                )
            if action == "task_engine.order.update":
                folder_order = None
                if parameters.get("folder_order") is not None:
                    folder_order = self._string_list(parameters["folder_order"], "folder_order")
                return api.reorder_task_engine_items(
                    course,
                    clazz,
                    task_order=self._string_list(parameters.get("task_order"), "task_order"),
                    folder_order=folder_order,
                    folder=str(parameters.get("folder") or ""),
                )
            if action == "task_engine.task.copy":
                return api.copy_task_engine_task(
                    course,
                    clazz,
                    self._required(parameters, "task"),
                    name=str(parameters.get("name") or ""),
                    folder=str(parameters.get("folder") or ""),
                )
            if action == "task_engine.task.delete":
                return api.delete_task_engine_task(
                    course, clazz, self._required(parameters, "task")
                )
            if action == "task_engine.recycle.list":
                return api.list_task_engine_recycle(
                    course,
                    clazz,
                    search=str(parameters.get("search") or ""),
                    max_items=self._integer(parameters.get("max_items", 1000), "max_items"),
                )
            if action == "task_engine.task.restore":
                return api.restore_task_engine_task(
                    course, clazz, self._required(parameters, "task")
                )
            if action == "task_engine.labels.list":
                return api.list_task_engine_labels(
                    course,
                    clazz,
                    task=str(parameters.get("task") or ""),
                    search=str(parameters.get("search") or ""),
                )
            if action == "task_engine.label.create":
                return api.create_task_engine_label(
                    course,
                    clazz,
                    self._required(parameters, "name"),
                    task=str(parameters.get("task") or ""),
                )
            if action == "task_engine.label.rename":
                return api.rename_task_engine_label(
                    course,
                    clazz,
                    self._required(parameters, "label"),
                    self._required(parameters, "name"),
                    task=str(parameters.get("task") or ""),
                )
            if action == "task_engine.label.delete":
                return api.delete_task_engine_label(
                    course,
                    clazz,
                    self._required(parameters, "label"),
                    task=str(parameters.get("task") or ""),
                )
            if action == "task_engine.export.request":
                selected_tasks = None
                if parameters.get("tasks") is not None:
                    selected_tasks = self._string_list(parameters["tasks"], "tasks")
                return api.request_task_engine_export(
                    course,
                    clazz,
                    selected_tasks,
                    folder=str(parameters.get("folder") or ""),
                )
            if action == "task_engine.publish_status.update":
                if "published" not in parameters:
                    raise ActionRuntimeError("missing required parameter: published")
                course_publish_param = parameters.get("course_publish_param")
                task_publish_param = parameters.get("task_publish_param")
                if course_publish_param is not None and not isinstance(course_publish_param, list):
                    raise ActionRuntimeError("course_publish_param must be a JSON list")
                if task_publish_param is not None and not isinstance(task_publish_param, list):
                    raise ActionRuntimeError("task_publish_param must be a JSON list")
                return api.set_task_engine_publish_status(
                    course,
                    clazz,
                    self._required(parameters, "task"),
                    publish=self._boolean(parameters["published"], "published"),
                    course_publish_param=course_publish_param,
                    task_publish_param=task_publish_param,
                )
        if action.startswith("knowledge_graph."):
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            if action == "knowledge_graph.graph.read":
                level = None
                if parameters.get("level") is not None:
                    level = self._integer(parameters["level"], "level")
                return api.list_knowledge_graph(
                    course,
                    clazz,
                    search=str(parameters.get("search") or ""),
                    level=level,
                )
            if action == "knowledge_graph.node.read":
                return api.read_knowledge_graph_node(
                    course, clazz, self._required(parameters, "node")
                )
            if action == "knowledge_graph.node.create":
                return api.create_knowledge_graph_node(
                    course,
                    clazz,
                    self._required(parameters, "name"),
                    node_type=str(parameters.get("node_type") or "knowledge"),
                    parent=str(parameters.get("parent") or ""),
                    description=str(parameters.get("description") or ""),
                    model=str(parameters.get("model") or ""),
                )
            if action == "knowledge_graph.node.update":
                return api.update_knowledge_graph_node(
                    course,
                    clazz,
                    self._required(parameters, "node"),
                    self._required(parameters, "name"),
                    description=str(parameters.get("description") or ""),
                )
            if action == "knowledge_graph.node.relations.read":
                return api.read_knowledge_graph_node_relations(
                    course, clazz, self._required(parameters, "node")
                )
            if action == "knowledge_graph.node.relation.add":
                return api.add_knowledge_graph_node_relation(
                    course,
                    clazz,
                    self._required(parameters, "node"),
                    self._required(parameters, "relation"),
                    self._required(parameters, "target"),
                    description=str(parameters.get("description") or ""),
                )
            if action == "knowledge_graph.node.relation.remove":
                return api.remove_knowledge_graph_node_relation(
                    course,
                    clazz,
                    self._required(parameters, "node"),
                    self._required(parameters, "relation"),
                    self._required(parameters, "target"),
                )
            if action == "knowledge_graph.settings.read":
                return api.read_knowledge_graph_settings(course, clazz)
            if action == "knowledge_graph.settings.update":
                return api.update_knowledge_graph_settings(
                    course,
                    clazz,
                    show_all_relations=(
                        self._boolean(parameters["show_all_relations"], "show_all_relations")
                        if "show_all_relations" in parameters
                        else None
                    ),
                    show_all_topic_names=(
                        self._boolean(parameters["show_all_topic_names"], "show_all_topic_names")
                        if "show_all_topic_names" in parameters
                        else None
                    ),
                    navigation_node_scale=(
                        self._boolean(parameters["navigation_node_scale"], "navigation_node_scale")
                        if "navigation_node_scale" in parameters
                        else None
                    ),
                    graph_background_color=(
                        self._boolean(
                            parameters["graph_background_color"], "graph_background_color"
                        )
                        if "graph_background_color" in parameters
                        else None
                    ),
                )
            if action == "knowledge_graph.advanced_settings.read":
                return api.read_knowledge_graph_advanced_settings(course, clazz)
            if action == "knowledge_graph.advanced_settings.update":
                return api.update_knowledge_graph_advanced_settings(
                    course,
                    clazz,
                    topic_card=self._optional_boolean(parameters, "topic_card"),
                    teach_target=self._optional_boolean(parameters, "teach_target"),
                    study_hours_enabled=self._optional_boolean(parameters, "study_hours_enabled"),
                    classify_relation_data=self._optional_boolean(
                        parameters, "classify_relation_data"
                    ),
                    selftest_included=self._optional_boolean(parameters, "selftest_included"),
                    micro_preview=self._optional_boolean(parameters, "micro_preview"),
                    micro_scale_mode=self._optional_boolean(parameters, "micro_scale_mode"),
                )
            if action == "knowledge_graph.models.list":
                return api.list_knowledge_graph_models(
                    course, clazz, search=str(parameters.get("search") or "")
                )
            if action == "knowledge_graph.model.data.read":
                return api.read_knowledge_graph_model_data(
                    course, clazz, self._required(parameters, "model")
                )
            if action == "knowledge_graph.model.create":
                return api.create_knowledge_graph_model(
                    course,
                    clazz,
                    self._required(parameters, "name"),
                    style=self._integer(parameters.get("style", 0), "style"),
                )
            if action == "knowledge_graph.model.update":
                return api.update_knowledge_graph_model(
                    course,
                    clazz,
                    self._required(parameters, "model"),
                    self._required(parameters, "name"),
                    style=(
                        self._integer(parameters["style"], "style")
                        if "style" in parameters
                        else None
                    ),
                )
            if action == "knowledge_graph.model.visibility.update":
                if "visible" not in parameters:
                    raise ActionRuntimeError("missing required parameter: visible")
                return api.set_knowledge_graph_model_visibility(
                    course,
                    clazz,
                    self._required(parameters, "model"),
                    visible=self._boolean(parameters["visible"], "visible"),
                )
            if action == "knowledge_graph.models.reorder":
                return api.reorder_knowledge_graph_models(
                    course,
                    clazz,
                    self._string_list(parameters.get("models"), "models"),
                )
            if action == "knowledge_graph.model.delete":
                return api.delete_knowledge_graph_model(
                    course, clazz, self._required(parameters, "model")
                )
            if action == "knowledge_graph.model.classes.list":
                return api.list_knowledge_graph_model_classes(
                    course, clazz, self._required(parameters, "model")
                )
            if action == "knowledge_graph.model.classes.update":
                if "visible_classes" not in parameters:
                    raise ActionRuntimeError("missing required parameter: visible_classes")
                return api.update_knowledge_graph_model_classes(
                    course,
                    clazz,
                    self._required(parameters, "model"),
                    self._string_list(parameters["visible_classes"], "visible_classes"),
                )
            if action == "knowledge_graph.events.list":
                return api.list_knowledge_graph_events(
                    course,
                    clazz,
                    search=str(parameters.get("search") or ""),
                )
            if action == "knowledge_graph.event.create":
                executions = parameters.get("executions")
                if not isinstance(executions, list):
                    raise ActionRuntimeError("executions must be a JSON list")
                return api.create_knowledge_graph_event(
                    course,
                    clazz,
                    self._required(parameters, "name"),
                    topic_condition=self._required(parameters, "topic_condition"),
                    set_condition=self._required(parameters, "set_condition"),
                    percent1=self._integer(parameters.get("percent1"), "percent1"),
                    percent2=self._integer(parameters.get("percent2", 100), "percent2"),
                    executions=executions,
                )
            if action == "knowledge_graph.event.update":
                executions = parameters.get("executions")
                if executions is not None and not isinstance(executions, list):
                    raise ActionRuntimeError("executions must be a JSON list")
                return api.update_knowledge_graph_event(
                    course,
                    clazz,
                    self._required(parameters, "event"),
                    name=str(parameters["name"]) if "name" in parameters else None,
                    topic_condition=parameters.get("topic_condition"),
                    set_condition=parameters.get("set_condition"),
                    percent1=parameters.get("percent1"),
                    percent2=parameters.get("percent2"),
                    executions=executions,
                )
            if action == "knowledge_graph.event.delete":
                return api.delete_knowledge_graph_event(
                    course,
                    clazz,
                    self._required(parameters, "event"),
                )
            if action == "knowledge_graph.export.download":
                return api.download_knowledge_graph_export(
                    course,
                    clazz,
                    self._required(parameters, "format"),
                    self._required(parameters, "output_path"),
                    model=str(parameters.get("model") or ""),
                    overwrite=self._boolean(parameters.get("overwrite", False), "overwrite"),
                )
            if action == "knowledge_graph.relation_types.list":
                return api.list_knowledge_graph_relation_types(
                    course,
                    clazz,
                    search=str(parameters.get("search") or ""),
                )
            if action == "knowledge_graph.relation_type.create":
                relation_types = None
                if parameters.get("relation_types") is not None:
                    relation_types = [
                        self._integer(item, "relation_types")
                        for item in self._string_list(
                            parameters.get("relation_types"), "relation_types"
                        )
                    ]
                return api.create_knowledge_graph_relation_type(
                    course,
                    clazz,
                    self._required(parameters, "name"),
                    meaning=str(parameters.get("meaning") or ""),
                    relation_types=relation_types,
                    example_html=str(parameters.get("example_html") or ""),
                    color=str(parameters.get("color") or ""),
                )
            if action == "knowledge_graph.relation_type.update":
                relation_types = None
                if parameters.get("relation_types") is not None:
                    relation_types = [
                        self._integer(item, "relation_types")
                        for item in self._string_list(
                            parameters.get("relation_types"), "relation_types"
                        )
                    ]
                return api.update_knowledge_graph_relation_type(
                    course,
                    clazz,
                    self._required(parameters, "relation"),
                    name=str(parameters["name"]) if "name" in parameters else None,
                    meaning=(str(parameters["meaning"]) if "meaning" in parameters else None),
                    relation_types=relation_types,
                    example_html=(
                        str(parameters["example_html"]) if "example_html" in parameters else None
                    ),
                    color=str(parameters["color"]) if "color" in parameters else None,
                    arrow_size=(
                        self._integer(parameters["arrow_size"], "arrow_size")
                        if "arrow_size" in parameters
                        else None
                    ),
                    line_thickness=(
                        self._integer(parameters["line_thickness"], "line_thickness")
                        if "line_thickness" in parameters
                        else None
                    ),
                )
            if action == "knowledge_graph.relation_type.delete":
                return api.delete_knowledge_graph_relation_type(
                    course, clazz, self._required(parameters, "relation")
                )
            if action == "knowledge_graph.category.create":
                return api.create_knowledge_graph_category(
                    course,
                    clazz,
                    self._required(parameters, "name"),
                    description=str(parameters.get("description") or ""),
                )
            if action == "knowledge_graph.category.update":
                return api.update_knowledge_graph_category(
                    course,
                    clazz,
                    self._required(parameters, "node"),
                    self._required(parameters, "name"),
                    description=str(parameters.get("description") or ""),
                )
            if action == "knowledge_graph.node.delete":
                return api.delete_knowledge_graph_node(
                    course, clazz, self._required(parameters, "node")
                )
            if action == "knowledge_graph.labels.list":
                return api.list_knowledge_graph_labels(
                    course,
                    clazz,
                    search=str(parameters.get("search") or ""),
                )
            if action == "knowledge_graph.label_group.create":
                return api.create_knowledge_graph_label_group(
                    course,
                    clazz,
                    self._required(parameters, "name"),
                    group_type=self._integer(parameters.get("group_type", 0), "group_type"),
                )
            if action == "knowledge_graph.label_group.rename":
                return api.rename_knowledge_graph_label_group(
                    course,
                    clazz,
                    self._required(parameters, "group"),
                    self._required(parameters, "name"),
                )
            if action == "knowledge_graph.label_group.delete":
                return api.delete_knowledge_graph_label_group(
                    course, clazz, self._required(parameters, "group")
                )
            if action == "knowledge_graph.label_groups.reorder":
                return api.reorder_knowledge_graph_label_groups(
                    course,
                    clazz,
                    self._string_list(parameters.get("groups"), "groups"),
                )
            if action == "knowledge_graph.label.create":
                return api.create_knowledge_graph_label(
                    course,
                    clazz,
                    self._required(parameters, "group"),
                    self._required(parameters, "name"),
                )
            if action == "knowledge_graph.label.rename":
                return api.rename_knowledge_graph_label(
                    course,
                    clazz,
                    self._required(parameters, "label"),
                    self._required(parameters, "name"),
                )
            if action == "knowledge_graph.label.move":
                return api.move_knowledge_graph_label(
                    course,
                    clazz,
                    self._required(parameters, "label"),
                    self._required(parameters, "group"),
                )
            if action == "knowledge_graph.labels.reorder":
                return api.reorder_knowledge_graph_labels(
                    course,
                    clazz,
                    self._required(parameters, "group"),
                    self._string_list(parameters.get("labels"), "labels"),
                )
            if action == "knowledge_graph.label.delete":
                return api.delete_knowledge_graph_label(
                    course, clazz, self._required(parameters, "label")
                )
        if action.startswith("class_activities."):
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            if action == "class_activities.types.list":
                return api.list_class_activity_types(course, clazz)
            if action == "class_activities.groups.list":
                return api.list_class_activity_groups(course, clazz)
            if action == "class_activities.group.create":
                return api.create_class_activity_group(
                    course, clazz, self._required(parameters, "name")
                )
            if action == "class_activities.group.rename":
                return api.rename_class_activity_group(
                    course,
                    clazz,
                    self._required(parameters, "group"),
                    self._required(parameters, "name"),
                )
            if action == "class_activities.group.delete":
                return api.delete_class_activity_group(
                    course,
                    clazz,
                    self._required(parameters, "group"),
                    allow_nonempty=self._boolean(
                        parameters.get("allow_nonempty", False), "allow_nonempty"
                    ),
                )
            if action == "class_activities.groups.reorder":
                return api.reorder_class_activity_groups(
                    course,
                    clazz,
                    self._string_list(parameters.get("groups"), "groups"),
                )
            if action == "class_activities.activities.list":
                activity_type = None
                if parameters.get("activity_type") is not None:
                    activity_type = self._integer(parameters["activity_type"], "activity_type")
                return api.list_class_activities(
                    course,
                    clazz,
                    group=str(parameters.get("group") or ""),
                    search=str(parameters.get("search") or ""),
                    status=str(parameters.get("status") or ""),
                    activity_type=activity_type,
                )
            if action == "class_activities.activity.read":
                return api.read_class_activity(
                    course, clazz, self._required(parameters, "activity")
                )
            if action == "class_activities.activity.rename":
                return api.rename_class_activity(
                    course,
                    clazz,
                    self._required(parameters, "activity"),
                    self._required(parameters, "name"),
                )
            if action == "class_activities.activity.move":
                return api.move_class_activity(
                    course,
                    clazz,
                    self._required(parameters, "activity"),
                    self._required(parameters, "group"),
                )
            if action == "class_activities.activities.reorder":
                return api.reorder_class_activities(
                    course,
                    clazz,
                    self._required(parameters, "group"),
                    self._string_list(parameters.get("activities"), "activities"),
                )
            if action == "class_activities.activity.start":
                return api.set_class_activity_status(
                    course,
                    clazz,
                    self._required(parameters, "activity"),
                    started=True,
                )
            if action == "class_activities.activity.end":
                return api.set_class_activity_status(
                    course,
                    clazz,
                    self._required(parameters, "activity"),
                    started=False,
                )
            if action == "class_activities.activity.delete":
                return api.delete_class_activity(
                    course, clazz, self._required(parameters, "activity")
                )
            if action == "class_activities.recycle.list":
                return api.list_class_activity_recycle(
                    course,
                    clazz,
                    search=str(parameters.get("search") or ""),
                    max_items=self._integer(parameters.get("max_items", 1000), "max_items"),
                )
            if action == "class_activities.recycle.restore":
                return api.restore_class_activity(
                    course, clazz, self._required(parameters, "activity")
                )
            if action == "class_activities.recycle.items.delete":
                return api.permanently_delete_class_activities(
                    course,
                    clazz,
                    self._string_list(parameters.get("activities"), "activities"),
                )
        if action.startswith("course_assets."):
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            kind = self._required(parameters, "kind")
            if action == "course_assets.items.list":
                return api.list_course_assets(
                    course,
                    clazz,
                    kind,
                    folder=str(parameters.get("folder") or "").strip(),
                    search=str(parameters.get("search") or "").strip(),
                    page=self._integer(parameters.get("page", 1), "page"),
                    page_size=self._integer(parameters.get("page_size", 1000), "page_size"),
                )
            if action == "course_assets.tree.list":
                return api.list_course_asset_tree(
                    course,
                    clazz,
                    kind,
                    search=str(parameters.get("search") or "").strip(),
                )
            if action == "course_assets.folder.create":
                return api.create_course_asset_folder(
                    course,
                    clazz,
                    kind,
                    self._required(parameters, "name"),
                    parent=str(parameters.get("parent") or "").strip(),
                )
            if action == "course_assets.cloud_files.import":
                return api.import_cloud_files_to_course_assets(
                    course,
                    clazz,
                    kind,
                    self._string_list(parameters.get("resources"), "resources"),
                    destination=str(parameters.get("destination") or "").strip(),
                )
            if action == "course_assets.item.rename":
                return api.rename_course_asset(
                    course,
                    clazz,
                    kind,
                    self._required(parameters, "asset"),
                    self._required(parameters, "name"),
                )
            if action == "course_assets.item.top_status.update":
                return api.set_course_asset_top_status(
                    course,
                    clazz,
                    kind,
                    self._required(parameters, "asset"),
                    top=self._boolean(parameters.get("top", True), "top"),
                )
            if action == "course_assets.items.move":
                return api.move_course_assets(
                    course,
                    clazz,
                    kind,
                    self._string_list(parameters.get("assets"), "assets"),
                    destination=str(parameters.get("destination") or "").strip(),
                )
            if action == "course_assets.item.copy":
                return api.copy_course_asset(
                    course,
                    clazz,
                    kind,
                    self._required(parameters, "asset"),
                )
            if action == "course_assets.items.delete":
                return api.delete_course_assets(
                    course,
                    clazz,
                    kind,
                    self._string_list(parameters.get("assets"), "assets"),
                )
            if action == "course_assets.item.download":
                return api.download_course_asset(
                    course,
                    clazz,
                    kind,
                    self._required(parameters, "asset"),
                    self._required(parameters, "output_path"),
                    overwrite=self._boolean(parameters.get("overwrite", False), "overwrite"),
                )
            if action == "course_assets.recycle.list":
                return api.list_course_asset_recycle(
                    course,
                    clazz,
                    kind,
                    search=str(parameters.get("search") or "").strip(),
                )
            if action == "course_assets.recycle.restore":
                return api.restore_course_asset_recycle_items(
                    course,
                    clazz,
                    kind,
                    self._string_list(parameters.get("assets"), "assets"),
                )
            if action == "course_assets.recycle.items.delete":
                return api.permanently_delete_course_asset_recycle_items(
                    course,
                    clazz,
                    kind,
                    self._string_list(parameters.get("assets"), "assets"),
                )
        if action == "chapters.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.list_chapters(
                course,
                clazz,
                search=str(parameters.get("search") or "").strip(),
            )
        if action == "chapters.tree.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.list_chapter_tree(course, clazz)
        if action == "chapters.cards.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.list_chapter_cards(
                course,
                clazz,
                self._required(parameters, "chapter"),
            )
        if action == "chapters.card.create":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.create_chapter_card(
                course,
                clazz,
                self._required(parameters, "chapter"),
                self._required(parameters, "title"),
                content=str(parameters.get("content") or ""),
                content_format=str(parameters.get("content_format") or "plain"),
                attachments=parameters.get("attachments"),
            )
        if action == "chapters.card.update":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.update_chapter_card(
                course,
                clazz,
                self._required(parameters, "chapter"),
                self._required(parameters, "card"),
                title=str(parameters["title"]) if "title" in parameters else None,
                content=str(parameters["content"]) if "content" in parameters else None,
                content_format=str(parameters.get("content_format") or "plain"),
                attachments=parameters.get("attachments"),
            )
        if action == "chapters.card.move":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            try:
                target_position = int(parameters.get("target_position"))
            except (TypeError, ValueError) as exc:
                raise ActionRuntimeError("target_position must be an integer") from exc
            return api.move_chapter_card(
                course,
                clazz,
                self._required(parameters, "chapter"),
                self._required(parameters, "card"),
                target_position,
            )
        if action == "chapters.card.delete":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.delete_chapter_card(
                course,
                clazz,
                self._required(parameters, "chapter"),
                self._required(parameters, "card"),
            )
        if action == "chapters.create":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.create_chapter(
                course,
                clazz,
                self._required(parameters, "title"),
                parent=str(parameters.get("parent") or "").strip(),
                before=str(parameters.get("before") or "").strip(),
            )
        if action == "chapters.rename":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.rename_chapter(
                course,
                clazz,
                self._required(parameters, "chapter"),
                self._required(parameters, "title"),
            )
        if action == "chapters.move":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.move_chapter(
                course,
                clazz,
                self._required(parameters, "chapter"),
                parent=str(parameters.get("parent") or "").strip(),
                relative_to=str(parameters.get("relative_to") or "").strip(),
                position=str(parameters.get("position") or "after").strip(),
            )
        if action == "chapters.outline.import":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.import_chapter_outline(
                course,
                clazz,
                self._required(parameters, "outline"),
            )
        if action == "chapters.open_status.update":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            target_classes = None
            if parameters.get("classes"):
                target_classes = [
                    resolve_class(course, query)
                    for query in self._string_list(parameters["classes"], "classes")
                ]
            return api.set_chapter_open_status(
                course,
                clazz,
                self._string_list(parameters.get("chapters"), "chapters"),
                self._required(parameters, "status"),
                target_classes=target_classes,
                begin=str(parameters.get("begin") or "").strip(),
                end=str(parameters.get("end") or "").strip(),
                time_end_review=self._boolean(
                    parameters.get("time_end_review", False), "time_end_review"
                ),
            )
        if action == "chapters.delete":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.delete_chapters(
                course,
                clazz,
                self._string_list(parameters.get("chapters"), "chapters"),
            )
        if action == "resources.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.list_resources(
                course,
                clazz,
                folder=str(parameters.get("folder") or "").strip(),
                search=str(parameters.get("search") or "").strip(),
            )
        if action == "resources.tree.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.list_resource_tree(
                course,
                clazz,
                search=str(parameters.get("search") or "").strip(),
            )
        if action == "resources.file.download":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.download_resource_file(
                course,
                clazz,
                self._required(parameters, "resource"),
                self._required(parameters, "output_path"),
                overwrite=self._boolean(parameters.get("overwrite", False), "overwrite"),
            )
        if action == "resources.items.download":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.download_resource_items(
                course,
                clazz,
                self._string_list(parameters.get("resources"), "resources"),
                self._required(parameters, "output_path"),
                overwrite=self._boolean(parameters.get("overwrite", False), "overwrite"),
            )
        if action == "resources.folder.create":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.create_resource_folder(
                course,
                clazz,
                self._required(parameters, "name"),
                parent=str(parameters.get("parent") or "").strip(),
            )
        if action == "resources.rename":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.rename_resource(
                course,
                clazz,
                self._required(parameters, "resource"),
                self._required(parameters, "name"),
            )
        if action == "resources.move":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.move_resources(
                course,
                clazz,
                self._string_list(parameters.get("resources"), "resources"),
                destination=str(parameters.get("destination") or "").strip(),
            )
        if action == "resources.reorder":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.reorder_resources(
                course,
                clazz,
                self._string_list(parameters.get("resources"), "resources"),
                folder=str(parameters.get("folder") or "").strip(),
            )
        if action == "resources.top_status.update":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.set_resource_top_status(
                course,
                clazz,
                self._required(parameters, "resource"),
                top=self._boolean(parameters.get("top"), "top"),
            )
        if action == "resources.copy":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.copy_resource(
                course,
                clazz,
                self._required(parameters, "resource"),
            )
        if action == "resources.cloud_disk.copy":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.copy_resource_to_cloud_disk(
                course,
                clazz,
                self._required(parameters, "resource"),
                destination=str(parameters.get("destination") or "").strip(),
            )
        if action == "resources.cloud_sources.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.list_course_cloud_sources(
                course,
                clazz,
                path=str(parameters.get("path") or "").strip(),
                search=str(parameters.get("search") or "").strip(),
                page=self._integer(parameters.get("page", 1), "page"),
                page_size=self._integer(parameters.get("page_size", 1000), "page_size"),
                share_id=str(parameters.get("share_id") or "0").strip(),
            )
        if action == "resources.cloud_files.import":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.import_cloud_files_to_resources(
                course,
                clazz,
                self._string_list(parameters.get("resources"), "resources"),
                source_path=str(parameters.get("source_path") or "").strip(),
                destination=str(parameters.get("destination") or "").strip(),
                share_id=str(parameters.get("share_id") or "0").strip(),
            )
        if action == "resources.cloud_folder.import":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.import_cloud_folder_to_resources(
                course,
                clazz,
                self._required(parameters, "resource"),
                source_path=str(parameters.get("source_path") or "").strip(),
                destination=str(parameters.get("destination") or "").strip(),
                share_id=str(parameters.get("share_id") or "0").strip(),
            )
        if action == "resources.labels.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.list_resource_labels(
                course,
                clazz,
                self._required(parameters, "resource"),
                search=str(parameters.get("search") or "").strip(),
            )
        if action == "resources.label.create":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.create_resource_label(
                course,
                clazz,
                self._required(parameters, "resource"),
                self._required(parameters, "name"),
            )
        if action == "resources.label.rename":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.rename_resource_label(
                course,
                clazz,
                self._required(parameters, "resource"),
                self._required(parameters, "label"),
                self._required(parameters, "name"),
            )
        if action == "resources.label.delete":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.delete_resource_label(
                course,
                clazz,
                self._required(parameters, "resource"),
                self._required(parameters, "label"),
            )
        if action == "resources.labels.update":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.update_resource_labels(
                course,
                clazz,
                self._string_list(parameters.get("resources"), "resources"),
                self._optional_string_list(parameters.get("labels")),
            )
        if action == "resources.delete":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.delete_resources(
                course,
                clazz,
                self._string_list(parameters.get("resources"), "resources"),
            )
        if action == "resources.link.create":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.create_resource_link(
                course,
                clazz,
                self._required(parameters, "name"),
                self._required(parameters, "url"),
                parent=str(parameters.get("parent") or "").strip(),
            )
        if action == "resources.file.upload":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.upload_resource_file(
                course,
                clazz,
                self._required(parameters, "file_path"),
                parent=str(parameters.get("parent") or "").strip(),
                name=str(parameters.get("name") or "").strip(),
            )
        if action == "resources.download_permission.update":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.set_resource_download_permission(
                course,
                clazz,
                self._string_list(parameters.get("resources"), "resources"),
                allow_download=self._boolean(parameters.get("allow_download"), "allow_download"),
            )
        if action == "resources.folder.visibility.read":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.read_resource_folder_visibility(
                course,
                clazz,
                self._required(parameters, "folder"),
            )
        if action == "resources.folder.visibility.update":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            class_queries = None
            if "classes" in parameters:
                class_queries = self._string_list(parameters.get("classes"), "classes")
            teacher_ids = None
            if "teacher_ids" in parameters:
                teacher_ids = self._string_list(parameters.get("teacher_ids"), "teacher_ids")
            all_teachers = None
            if "all_teachers" in parameters:
                all_teachers = self._boolean(parameters["all_teachers"], "all_teachers")
            return api.update_resource_folder_visibility(
                course,
                clazz,
                self._required(parameters, "folder"),
                mode=self._required(parameters, "mode"),
                classes=class_queries,
                teacher_ids=teacher_ids,
                all_teachers=all_teachers,
            )
        if action == "resources.readers.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            reader_class = None
            if parameters.get("reader_class"):
                reader_class = resolve_class(course, parameters["reader_class"])
            return api.list_resource_readers(
                course,
                clazz,
                self._required(parameters, "resource"),
                reader_class=reader_class,
            )
        if action == "resources.downloaders.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.list_resource_downloaders(
                course,
                clazz,
                self._required(parameters, "resource"),
            )
        if action == "resources.import_courses.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.list_resource_import_courses(
                course,
                clazz,
                search=str(parameters.get("search") or "").strip(),
            )
        if action == "resources.import_items.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            try:
                page = int(parameters.get("page", 1))
                page_size = int(parameters.get("page_size", 100))
            except (TypeError, ValueError) as exc:
                raise ActionRuntimeError("page and page_size must be integers") from exc
            return api.list_resource_import_items(
                course,
                clazz,
                self._required(parameters, "source_course"),
                folder_id=str(parameters.get("folder_id") or "").strip(),
                search=str(parameters.get("search") or "").strip(),
                page=page,
                page_size=page_size,
            )
        if action == "resources.import.execute":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.import_resources_from_course(
                course,
                clazz,
                self._required(parameters, "source_course"),
                self._string_list(parameters.get("resources"), "resources"),
                source_folder_id=str(parameters.get("source_folder_id") or "").strip(),
                destination=str(parameters.get("destination") or "").strip(),
            )
        if action == "resources.share_link.create":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.create_resource_share_link(
                course,
                clazz,
                self._required(parameters, "resource"),
            )
        if action == "cloud_disk.items.list":
            try:
                page = int(parameters.get("page", 1))
                page_size = int(parameters.get("page_size", 100))
            except (TypeError, ValueError) as exc:
                raise ActionRuntimeError("page and page_size must be integers") from exc
            return self._api().list_cloud_disk_items(
                parent=str(parameters.get("parent") or "").strip(),
                search=str(parameters.get("search") or "").strip(),
                page=page,
                page_size=page_size,
            )
        if action == "cloud_disk.item.read":
            return self._api().read_cloud_disk_item(self._required(parameters, "resource"))
        if action == "cloud_disk.items.delete":
            return self._api().delete_cloud_disk_items(
                self._string_list(parameters.get("resources"), "resources")
            )
        if action == "cloud_disk.folder.create":
            return self._api().create_cloud_disk_folder(
                self._required(parameters, "name"),
                parent=str(parameters.get("parent") or "").strip(),
                shared=self._boolean(parameters.get("shared", False), "shared"),
            )
        if action == "cloud_disk.item.rename":
            return self._api().rename_cloud_disk_item(
                self._required(parameters, "resource"),
                self._required(parameters, "name"),
            )
        if action == "cloud_disk.items.move":
            return self._api().move_cloud_disk_items(
                self._string_list(parameters.get("resources"), "resources"),
                destination=str(parameters.get("destination") or "").strip(),
            )
        if action == "cloud_disk.item.top_status.update":
            return self._api().set_cloud_disk_top_status(
                self._required(parameters, "resource"),
                top=self._boolean(parameters.get("top"), "top"),
            )
        if action == "cloud_disk.items.download":
            return self._api().download_cloud_disk_items(
                self._string_list(parameters.get("resources"), "resources"),
                self._required(parameters, "output_path"),
                overwrite=self._boolean(parameters.get("overwrite", False), "overwrite"),
            )
        if action == "cloud_disk.recycle.list":
            try:
                page = int(parameters.get("page", 1))
                page_size = int(parameters.get("page_size", 100))
            except (TypeError, ValueError) as exc:
                raise ActionRuntimeError("page and page_size must be integers") from exc
            return self._api().list_cloud_disk_recycle_items(
                page=page,
                page_size=page_size,
            )
        if action == "cloud_disk.recycle.restore":
            return self._api().restore_cloud_disk_recycle_items(
                self._string_list(parameters.get("resources"), "resources"),
                conflict_policy=str(parameters.get("conflict_policy") or "keep_both"),
            )
        if action == "cloud_disk.recycle.items.delete":
            return self._api().permanently_delete_cloud_disk_recycle_items(
                self._string_list(parameters.get("resources"), "resources")
            )
        if action == "cloud_disk.recycle.empty":
            return self._api().empty_cloud_disk_recycle()
        if action == "homework.library.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.list_homework_library(
                course,
                clazz,
                directory_id=str(parameters.get("directory") or "0"),
                search=str(parameters.get("search") or "").strip(),
            )
        if action == "homework.library.item.read":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.read_homework_library_item(
                course,
                clazz,
                self._required(parameters, "homework"),
                question=str(parameters.get("question") or "").strip(),
            )
        if action == "homework.question.add":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            answers = None
            if "answers" in parameters:
                answers = self._string_list(parameters["answers"], "answers")
            return api.add_homework_question(
                course,
                clazz,
                self._required(parameters, "homework"),
                self._required(parameters, "question_type"),
                self._required(parameters, "stem"),
                score=parameters.get("score", 5),
                options=parameters.get("options"),
                correct_answer=parameters.get("correct_answer"),
                answers=answers,
                answer=parameters.get("answer"),
                analysis=str(parameters.get("analysis") or ""),
                difficulty=parameters.get("difficulty", 0.8),
                content_format=str(parameters.get("content_format") or "plain"),
            )
        if action == "homework.question.update":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            answers = None
            if "answers" in parameters:
                answers = self._string_list(parameters["answers"], "answers")
            return api.update_homework_question(
                course,
                clazz,
                self._required(parameters, "homework"),
                self._required(parameters, "question"),
                stem=(str(parameters["stem"]) if "stem" in parameters else None),
                score=parameters.get("score"),
                options=parameters.get("options"),
                correct_answer=parameters.get("correct_answer"),
                answers=answers,
                answer=parameters.get("answer") if "answer" in parameters else None,
                analysis=(str(parameters["analysis"]) if "analysis" in parameters else None),
                difficulty=parameters.get("difficulty"),
                content_format=str(parameters.get("content_format") or "plain"),
            )
        if action == "homework.question.delete":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.delete_homework_question(
                course,
                clazz,
                self._required(parameters, "homework"),
                self._required(parameters, "question"),
            )
        if action == "homework.drafts.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.list_homework_drafts(
                course,
                clazz,
                search=str(parameters.get("search") or "").strip(),
            )
        if action == "homework.draft.create":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.create_homework_draft(
                course,
                clazz,
                self._required(parameters, "title"),
                directory=str(parameters.get("directory") or "0"),
            )
        if action == "homework.draft.update":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.update_homework_draft(
                course,
                clazz,
                self._required(parameters, "draft"),
                self._required(parameters, "title"),
            )
        if action == "homework.draft.delete":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.delete_homework_draft(
                course,
                clazz,
                self._required(parameters, "draft"),
            )
        if action == "homework.library.publish":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            try:
                redo_times = int(parameters.get("redo_times", 0))
            except (TypeError, ValueError) as exc:
                raise ActionRuntimeError("redo_times must be an integer") from exc
            target_classes = None
            if "target_classes" in parameters:
                target_classes = self._string_list(parameters["target_classes"], "target_classes")
            return api.publish_homework_from_library(
                course,
                clazz,
                self._required(parameters, "homework"),
                target_classes=target_classes,
                start_time=str(parameters.get("start_time") or "now"),
                end_time=str(parameters.get("end_time") or ""),
                allow_late_submission=self._boolean(
                    parameters.get("allow_late_submission", False),
                    "allow_late_submission",
                ),
                late_deadline=str(parameters.get("late_deadline") or ""),
                passing_score=parameters.get("passing_score", 0),
                redo_times=redo_times,
                allow_paste=self._boolean(parameters.get("allow_paste", True), "allow_paste"),
                show_score=self._boolean(parameters.get("show_score", True), "show_score"),
                show_correctness=self._boolean(
                    parameters.get("show_correctness", True),
                    "show_correctness",
                ),
                randomize_questions=self._boolean(
                    parameters.get("randomize_questions", False),
                    "randomize_questions",
                ),
                randomize_options=self._boolean(
                    parameters.get("randomize_options", False),
                    "randomize_options",
                ),
            )
        if action in {"homework.list", "homework.list_ungraded"}:
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.list_homeworks(
                course,
                clazz,
                only_ungraded=action == "homework.list_ungraded",
            )
        if action == "homework.submissions.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            try:
                status = int(parameters.get("status", 0))
            except (TypeError, ValueError) as exc:
                raise ActionRuntimeError("status must be 0, 3, or 4") from exc
            return api.list_homework_submissions(
                course,
                clazz,
                self._required(parameters, "homework"),
                status=status,
            )
        if action == "homework.submission.read":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            try:
                max_chars = int(parameters.get("max_chars", 4000))
            except (TypeError, ValueError) as exc:
                raise ActionRuntimeError("max_chars must be an integer") from exc
            return api.read_homework_submission(
                course,
                clazz,
                self._required(parameters, "homework"),
                self._required(parameters, "submission"),
                max_chars=max_chars,
            )
        if action == "homework.score.set":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.set_homework_score(
                course,
                clazz,
                self._required(parameters, "homework"),
                self._required(parameters, "submission"),
                self._required(parameters, "score"),
            )
        if action == "notices.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.list_notices(
                course,
                clazz,
                search=str(parameters.get("search") or "").strip(),
            )
        if action == "notices.drafts.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            try:
                page_size = int(parameters.get("page_size", 100))
            except (TypeError, ValueError) as exc:
                raise ActionRuntimeError("page_size must be an integer") from exc
            return api.list_notice_drafts(
                course,
                search=str(parameters.get("search") or "").strip(),
                page_size=page_size,
            )
        if action in {"notices.draft.save", "notices.schedule"}:
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            recipient_classes = (
                self._string_list(parameters["recipient_classes"], "recipient_classes")
                if "recipient_classes" in parameters
                else None
            )
            scheduled_send_time = parameters.get("send_at")
            if action == "notices.schedule" and scheduled_send_time is None:
                raise ActionRuntimeError("missing required parameter: send_at")
            return api.save_notice_draft(
                course,
                clazz,
                self._required(parameters, "title"),
                self._required(parameters, "content"),
                recipient_classes=recipient_classes,
                draft_query=str(parameters.get("draft") or "").strip(),
                scheduled_send_time=scheduled_send_time,
                clear_schedule=self._boolean(
                    parameters.get("clear_schedule", False), "clear_schedule"
                ),
                allow_comments=self._boolean(
                    parameters.get("allow_comments", True), "allow_comments"
                ),
                show_comments=self._boolean(
                    parameters.get("show_comments", False), "show_comments"
                ),
                hide_read_status=self._boolean(
                    parameters.get("hide_read_status", False), "hide_read_status"
                ),
            )
        if action == "notices.draft.delete":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            return api.delete_notice_draft(
                course,
                self._required(parameters, "draft"),
            )
        if action == "notices.send":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            recipient_classes = (
                self._string_list(parameters["recipient_classes"], "recipient_classes")
                if "recipient_classes" in parameters
                else None
            )
            return api.send_notice(
                course,
                clazz,
                self._required(parameters, "title"),
                self._required(parameters, "content"),
                recipient_classes=recipient_classes,
                allow_comments=self._boolean(
                    parameters.get("allow_comments", True), "allow_comments"
                ),
                show_comments=self._boolean(
                    parameters.get("show_comments", False), "show_comments"
                ),
                hide_read_status=self._boolean(
                    parameters.get("hide_read_status", False), "hide_read_status"
                ),
            )
        if action == "notices.edit":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.edit_notice(
                course,
                clazz,
                self._required(parameters, "notice"),
                self._required(parameters, "title"),
                self._required(parameters, "content"),
            )
        if action == "notices.top.set":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.set_notice_top(
                course,
                clazz,
                self._required(parameters, "notice"),
                self._boolean(parameters.get("top", True), "top"),
            )
        if action in {"notices.recall", "notices.delete"}:
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            notice = self._required(parameters, "notice")
            if action == "notices.recall":
                return api.recall_notice(course, clazz, notice)
            return api.delete_notice(course, clazz, notice)
        if action == "exam.paper_library.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            try:
                page_size = int(parameters.get("page_size", 100))
            except (TypeError, ValueError) as exc:
                raise ActionRuntimeError("page_size must be an integer") from exc
            return api.list_exam_paper_library(
                course,
                clazz,
                directory_id=str(parameters.get("directory_id") or "0"),
                search=str(parameters.get("search") or "").strip(),
                page_size=page_size,
            )
        if action == "exam.paper.read":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.read_exam_paper(
                course,
                clazz,
                self._required(parameters, "paper"),
                directory_id=str(parameters.get("directory_id") or "0"),
                question=str(parameters.get("question") or "").strip(),
            )
        if action == "exam.paper.settings.read":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.read_exam_paper_settings(
                course,
                clazz,
                self._required(parameters, "paper"),
                directory_id=str(parameters.get("directory_id") or "0"),
                group_id=str(parameters.get("group_id") or "0"),
            )
        if action == "exam.paper.settings.update":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.update_exam_paper_settings(
                course,
                clazz,
                self._required(parameters, "paper"),
                difficulty=parameters.get("difficulty"),
                numbering=parameters.get("numbering"),
                grouping=parameters.get("grouping"),
                subquestion_numbering=parameters.get("subquestion_numbering"),
                directory_id=str(parameters.get("directory_id") or "0"),
                group_id=str(parameters.get("group_id") or "0"),
            )
        if action == "exam.question.add":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.add_exam_question(
                course,
                clazz,
                self._required(parameters, "paper"),
                self._required(parameters, "question_type"),
                self._required(parameters, "stem"),
                score=parameters.get("score", 5),
                options=parameters.get("options"),
                correct_answer=parameters.get("correct_answer"),
                answers=parameters.get("answers"),
                answer=parameters.get("answer"),
                analysis=str(parameters.get("analysis") or ""),
                difficulty=parameters.get("difficulty", 0.8),
                content_format=str(parameters.get("content_format") or "plain"),
                directory_id=str(parameters.get("directory_id") or "0"),
                group_id=str(parameters.get("group_id") or "0"),
            )
        if action == "exam.question.update":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.update_exam_question(
                course,
                clazz,
                self._required(parameters, "paper"),
                self._required(parameters, "question"),
                stem=parameters.get("stem"),
                score=parameters.get("score"),
                options=parameters.get("options"),
                correct_answer=parameters.get("correct_answer"),
                answers=parameters.get("answers"),
                answer=parameters.get("answer"),
                analysis=parameters.get("analysis"),
                difficulty=parameters.get("difficulty"),
                content_format=str(parameters.get("content_format") or "plain"),
                directory_id=str(parameters.get("directory_id") or "0"),
                group_id=str(parameters.get("group_id") or "0"),
            )
        if action == "exam.question.delete":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.delete_exam_question(
                course,
                clazz,
                self._required(parameters, "paper"),
                self._required(parameters, "question"),
                directory_id=str(parameters.get("directory_id") or "0"),
                group_id=str(parameters.get("group_id") or "0"),
            )
        if action == "exam.question.move":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.move_exam_question(
                course,
                clazz,
                self._required(parameters, "paper"),
                self._required(parameters, "question"),
                self._required(parameters, "target_position"),
                directory_id=str(parameters.get("directory_id") or "0"),
                group_id=str(parameters.get("group_id") or "0"),
            )
        if action == "exam.question_type.update":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.update_exam_question_type(
                course,
                clazz,
                self._required(parameters, "paper"),
                self._required(parameters, "question_type"),
                description=parameters.get("description"),
                total_score=parameters.get("total_score"),
                directory_id=str(parameters.get("directory_id") or "0"),
                group_id=str(parameters.get("group_id") or "0"),
            )
        if action == "exam.question_type.move":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.move_exam_question_type(
                course,
                clazz,
                self._required(parameters, "paper"),
                self._required(parameters, "question_type"),
                self._required(parameters, "target_position"),
                directory_id=str(parameters.get("directory_id") or "0"),
                group_id=str(parameters.get("group_id") or "0"),
            )
        if action == "exam.question_type.delete":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.delete_exam_question_type(
                course,
                clazz,
                self._required(parameters, "paper"),
                self._required(parameters, "question_type"),
                directory_id=str(parameters.get("directory_id") or "0"),
                group_id=str(parameters.get("group_id") or "0"),
            )
        if action == "exam.paper.create":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.create_exam_paper(
                course,
                clazz,
                title=str(parameters.get("title") or "").strip(),
                directory_id=str(parameters.get("directory_id") or "0"),
            )
        if action == "exam.paper.rename":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.rename_exam_paper(
                course,
                clazz,
                self._required(parameters, "paper"),
                self._required(parameters, "title"),
                directory_id=str(parameters.get("directory_id") or "0"),
                sync_parallel_titles=self._boolean(
                    parameters.get("sync_parallel_titles", False),
                    "sync_parallel_titles",
                ),
            )
        if action == "exam.paper.copy":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.copy_exam_paper(
                course,
                clazz,
                self._required(parameters, "paper"),
                directory_id=str(parameters.get("directory_id") or "0"),
            )
        if action == "exam.paper.delete":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.delete_exam_paper(
                course,
                clazz,
                self._required(parameters, "paper"),
                directory_id=str(parameters.get("directory_id") or "0"),
            )
        if action == "exam.paper_folder.create":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.create_exam_paper_folder(
                course,
                clazz,
                self._required(parameters, "title"),
                parent_directory_id=str(parameters.get("parent_directory_id") or "0"),
            )
        if action == "exam.paper_folder.rename":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.rename_exam_paper_folder(
                course,
                clazz,
                self._required(parameters, "folder"),
                self._required(parameters, "title"),
                parent_directory_id=str(parameters.get("parent_directory_id") or "0"),
            )
        if action == "exam.paper_folder.delete":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.delete_exam_paper_folder(
                course,
                clazz,
                self._required(parameters, "folder"),
                parent_directory_id=str(parameters.get("parent_directory_id") or "0"),
            )
        if action in {"exam.paper.move", "exam.paper_folder.move"}:
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            is_folder = action == "exam.paper_folder.move"
            return api.move_exam_paper_library_item(
                course,
                clazz,
                self._required(parameters, "folder" if is_folder else "paper"),
                self._required(parameters, "target_directory_id"),
                source_directory_id=str(parameters.get("source_directory_id") or "0"),
                target_parent_directory_id=str(parameters.get("target_parent_directory_id") or "0"),
                is_folder=is_folder,
            )
        if action == "exams.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            try:
                status = int(parameters.get("status", -1))
            except (TypeError, ValueError) as exc:
                raise ActionRuntimeError("status must be -1, 0, 1, or 2") from exc
            return api.list_exams(
                course,
                clazz,
                status=status,
                search=str(parameters.get("search") or "").strip(),
            )
        if action == "exams.submissions.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            try:
                state = int(parameters.get("state", 1))
                status = int(parameters.get("status", -1))
            except (TypeError, ValueError) as exc:
                raise ActionRuntimeError("state and status must be integers") from exc
            return api.list_exam_submissions(
                course,
                clazz,
                self._required(parameters, "exam"),
                state=state,
                status=status,
                search=str(parameters.get("search") or "").strip(),
            )
        if action == "exams.submission.read":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.read_exam_submission(
                course,
                clazz,
                self._required(parameters, "exam"),
                self._required(parameters, "submission"),
            )
        if action == "question_bank.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            try:
                page = int(parameters.get("page", 1))
                page_size = int(parameters.get("page_size", 30))
            except (TypeError, ValueError) as exc:
                raise ActionRuntimeError("page and page_size must be integers") from exc
            return api.list_question_bank(
                course,
                clazz,
                page=page,
                page_size=page_size,
                search=str(parameters.get("search") or "").strip(),
                directory_id=str(parameters.get("directory_id") or "0").strip(),
            )
        if action == "question_bank.question.read":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.read_question_bank_question(
                course,
                clazz,
                self._required(parameters, "question"),
                directory_id=str(parameters.get("directory_id") or "0").strip(),
            )
        if action == "question_bank.directories.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.list_question_bank_directories(course, clazz)
        if action == "question_bank.directory.permissions.read":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.read_question_bank_directory_permissions(
                course,
                clazz,
                self._required(parameters, "directory"),
            )
        if action == "question_bank.directory.permissions.update":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.update_question_bank_directory_permissions(
                course,
                clazz,
                self._required(parameters, "directory"),
                allow_student_self_practice=(
                    self._boolean(
                        parameters["allow_student_self_practice"],
                        "allow_student_self_practice",
                    )
                    if "allow_student_self_practice" in parameters
                    else None
                ),
                share_scope=(
                    str(parameters["share_scope"])
                    if parameters.get("share_scope") is not None
                    else None
                ),
                selected_teachers=parameters.get("selected_teachers"),
            )
        if action == "question_bank.question_types.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.list_question_bank_question_types(course, clazz)
        if action == "question_bank.question_type.add":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.add_question_bank_question_type(
                course,
                clazz,
                self._required(parameters, "name"),
                self._required(parameters, "base_type"),
            )
        if action == "question_bank.question_type.rename":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.rename_question_bank_question_type(
                course,
                clazz,
                self._required(parameters, "question_type"),
                self._required(parameters, "name"),
            )
        if action == "question_bank.question_type.move":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            try:
                target_position = int(self._required(parameters, "target_position"))
            except (TypeError, ValueError) as exc:
                raise ActionRuntimeError("target_position must be an integer") from exc
            return api.move_question_bank_question_type(
                course,
                clazz,
                self._required(parameters, "question_type"),
                target_position,
            )
        if action == "question_bank.question_type.delete":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.delete_question_bank_question_type(
                course,
                clazz,
                self._required(parameters, "question_type"),
            )
        if action == "question_bank.labels.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.list_question_bank_labels(
                course,
                clazz,
                question_query=str(parameters.get("question") or ""),
                directory_id=str(parameters.get("directory_id") or "0"),
            )
        if action == "question_bank.label.create":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.create_question_bank_label(
                course,
                clazz,
                self._required(parameters, "name"),
                parent_label=str(parameters.get("parent_label") or "0"),
            )
        if action == "question_bank.label.rename":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.rename_question_bank_label(
                course,
                clazz,
                self._required(parameters, "label"),
                self._required(parameters, "name"),
            )
        if action == "question_bank.label.delete":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.delete_question_bank_label(
                course,
                clazz,
                self._required(parameters, "label"),
            )
        if action in {
            "question_bank.question.labels.set",
            "question_bank.question.labels.sync",
        }:
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            questions = parameters.get("questions", parameters.get("question"))
            if questions is None:
                raise ActionRuntimeError("missing required parameter: questions")
            return api.set_question_bank_question_labels(
                course,
                clazz,
                questions,
                parameters.get("labels"),
                directory_id=str(parameters.get("directory_id") or "0"),
                mode=str(parameters.get("mode") or "replace"),
                sync_references=action == "question_bank.question.labels.sync",
            )
        if action == "question_bank.topics.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.list_question_bank_topics(
                course,
                clazz,
                question_query=str(parameters.get("question") or ""),
                directory_id=str(parameters.get("directory_id") or "0"),
                search=str(parameters.get("search") or ""),
            )
        if action == "question_bank.topic.create":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.create_question_bank_topic(
                course,
                clazz,
                self._required(parameters, "name"),
                kind=str(parameters.get("kind") or "knowledge_point"),
                parent_topic=(
                    str(parameters["parent_topic"])
                    if parameters.get("parent_topic") is not None
                    else None
                ),
                after_topic=str(parameters.get("after_topic") or ""),
            )
        if action == "question_bank.topic.rename":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.rename_question_bank_topic(
                course,
                clazz,
                self._required(parameters, "topic"),
                self._required(parameters, "name"),
            )
        if action == "question_bank.topic.delete":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.delete_question_bank_topic(
                course,
                clazz,
                self._required(parameters, "topic"),
            )
        if action in {
            "question_bank.question.topics.set",
            "question_bank.question.topics.sync",
        }:
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            questions = parameters.get("questions", parameters.get("question"))
            if questions is None:
                raise ActionRuntimeError("missing required parameter: questions")
            return api.set_question_bank_question_topics(
                course,
                clazz,
                questions,
                parameters.get("topics"),
                directory_id=str(parameters.get("directory_id") or "0"),
                mode=str(parameters.get("mode") or "replace"),
                sync_references=action == "question_bank.question.topics.sync",
            )
        if action in {"question_bank.recycle.list", "question_bank.locked.list"}:
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            try:
                page = int(parameters.get("page") or 1)
                page_size = int(parameters.get("page_size") or 0)
            except (TypeError, ValueError) as exc:
                raise ActionRuntimeError("page and page_size must be integers") from exc
            return api.list_question_bank_inactive_items(
                course,
                clazz,
                state="recycle" if action.endswith("recycle.list") else "locked",
                page=page,
                page_size=page_size,
                search=str(parameters.get("search") or ""),
                directory_id=str(parameters.get("directory_id") or ""),
                directory_path_ids=parameters.get("directory_path_ids"),
                order=str(parameters.get("order") or "desc"),
                lock_time_filters=parameters.get("lock_time_filters"),
            )
        if action == "question_bank.items.lock":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.lock_question_bank_items(
                course,
                clazz,
                questions=parameters.get("questions"),
                directories=parameters.get("directories"),
                directory_id=str(parameters.get("directory_id") or "0"),
            )
        if action in {
            "question_bank.items.unlock",
            "question_bank.recycle.restore",
            "question_bank.recycle.delete",
        }:
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            items = parameters.get("items", parameters.get("item"))
            if items is None:
                raise ActionRuntimeError("missing required parameter: items")
            if action == "question_bank.items.unlock":
                source_state, operation = "locked", "unlock"
            elif action == "question_bank.recycle.restore":
                source_state, operation = "recycle", "restore"
            else:
                source_state, operation = "recycle", "delete"
            return api.transition_question_bank_inactive_items(
                course,
                clazz,
                items,
                source_state=source_state,
                operation=operation,
                directory_id=str(parameters.get("directory_id") or ""),
                directory_path_ids=parameters.get("directory_path_ids"),
            )
        if action == "question_bank.recycle.empty":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.empty_question_bank_recycle_bin(course, clazz)
        if action == "question_bank.questions.difficulty.update":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            questions = parameters.get("questions", parameters.get("question"))
            if questions is None:
                raise ActionRuntimeError("missing required parameter: questions")
            return api.update_question_bank_questions_difficulty(
                course,
                clazz,
                questions,
                self._required(parameters, "difficulty"),
                directory_id=str(parameters.get("directory_id") or "0"),
            )
        if action == "question_bank.questions.type.update":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            questions = parameters.get("questions", parameters.get("question"))
            if questions is None:
                raise ActionRuntimeError("missing required parameter: questions")
            return api.update_question_bank_questions_type(
                course,
                clazz,
                questions,
                self._required(parameters, "question_type"),
                directory_id=str(parameters.get("directory_id") or "0"),
            )
        if action == "question_bank.items.copy":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.copy_question_bank_items(
                course,
                clazz,
                questions=parameters.get("questions"),
                directories=parameters.get("directories"),
                source_directory_id=str(parameters.get("source_directory_id") or "0"),
                target_directory=str(parameters.get("target_directory") or "0"),
            )
        if action == "question_bank.smart_import.preview":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.preview_question_bank_smart_import(
                course,
                clazz,
                source_text=(
                    str(parameters["source_text"])
                    if parameters.get("source_text") is not None
                    else None
                ),
                file_path=parameters.get("file_path", parameters.get("source_file")),
                content_format=str(parameters.get("content_format") or "plain"),
                parse_latex_code=self._boolean(
                    parameters.get("parse_latex_code", False), "parse_latex_code"
                ),
                parse_latex_formula=self._boolean(
                    parameters.get("parse_latex_formula", False), "parse_latex_formula"
                ),
            )
        if action == "question_bank.smart_import.commit":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.import_question_bank_smart(
                course,
                clazz,
                target_directory=str(parameters.get("target_directory") or "0"),
                source_text=(
                    str(parameters["source_text"])
                    if parameters.get("source_text") is not None
                    else None
                ),
                file_path=parameters.get("file_path", parameters.get("source_file")),
                questions=parameters.get("questions"),
                content_format=str(parameters.get("content_format") or "plain"),
                parse_latex_code=self._boolean(
                    parameters.get("parse_latex_code", False), "parse_latex_code"
                ),
                parse_latex_formula=self._boolean(
                    parameters.get("parse_latex_formula", False), "parse_latex_formula"
                ),
                allow_parser_warnings=self._boolean(
                    parameters.get("allow_parser_warnings", False), "allow_parser_warnings"
                ),
            )
        if action == "question_bank.source_courses.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.list_question_bank_source_courses(course, clazz)
        if action == "question_bank.source_questions.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            try:
                page = int(parameters.get("page", 1))
                page_size = int(parameters.get("page_size", 30))
            except (TypeError, ValueError) as exc:
                raise ActionRuntimeError("page and page_size must be integers") from exc
            return api.list_question_bank_source_questions(
                course,
                clazz,
                self._required(parameters, "source_course"),
                page=page,
                page_size=page_size,
                search=str(parameters.get("search") or ""),
                directory_id=str(parameters.get("directory_id") or "0"),
            )
        if action == "question_bank.questions.import_from_course":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            questions = parameters.get("questions", parameters.get("question"))
            if questions is None:
                raise ActionRuntimeError("missing required parameter: questions")
            return api.import_question_bank_questions_from_course(
                course,
                clazz,
                self._required(parameters, "source_course"),
                questions,
                target_directory=str(parameters.get("target_directory") or "0"),
                source_directory_id=str(parameters.get("source_directory_id") or "0"),
            )
        if action == "question_bank.export.create":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.export_question_bank(
                course,
                clazz,
                export_type=self._required(parameters, "export_type"),
                questions=parameters.get("questions"),
                directories=parameters.get("directories"),
                export_all=self._boolean(parameters.get("export_all", False), "export_all"),
                source_directory_id=str(parameters.get("source_directory_id") or "0"),
                output_path=parameters.get("output_path", parameters.get("output")),
                include_answers=self._boolean(
                    parameters.get("include_answers", True), "include_answers"
                ),
                include_analysis=self._boolean(
                    parameters.get("include_analysis", True), "include_analysis"
                ),
                include_difficulty=self._boolean(
                    parameters.get("include_difficulty", False), "include_difficulty"
                ),
                include_type_names=self._boolean(
                    parameters.get("include_type_names", False), "include_type_names"
                ),
                include_topics=self._boolean(
                    parameters.get("include_topics", False), "include_topics"
                ),
                include_targets=self._boolean(
                    parameters.get("include_targets", False), "include_targets"
                ),
                include_correct_rate=self._boolean(
                    parameters.get("include_correct_rate", False), "include_correct_rate"
                ),
                include_use_count=self._boolean(
                    parameters.get("include_use_count", False), "include_use_count"
                ),
                excel_plain_text=self._boolean(
                    parameters.get("excel_plain_text", False), "excel_plain_text"
                ),
                overwrite=self._boolean(parameters.get("overwrite", False), "overwrite"),
            )
        if action == "question_bank.downloads.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            try:
                page = int(parameters.get("page") or 1)
            except (TypeError, ValueError) as exc:
                raise ActionRuntimeError("page must be an integer") from exc
            return api.list_question_bank_download_center(
                course,
                clazz,
                page=page,
                order=str(parameters.get("order") or "down"),
            )
        if action == "question_bank.downloads.get":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.get_question_bank_download(
                course,
                clazz,
                self._required(parameters, "record"),
                output_path=parameters.get("output_path", parameters.get("output")),
                password=(
                    str(parameters["password"]) if parameters.get("password") is not None else None
                ),
                overwrite=self._boolean(parameters.get("overwrite", False), "overwrite"),
            )
        if action == "question_bank.downloads.rename":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.rename_question_bank_download_record(
                course,
                clazz,
                self._required(parameters, "record"),
                self._required(parameters, "name"),
            )
        if action == "question_bank.downloads.delete":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.delete_question_bank_download_record(
                course,
                clazz,
                self._required(parameters, "record"),
            )
        if action == "question_bank.directory.create":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.create_question_bank_directory(
                course,
                clazz,
                self._required(parameters, "name"),
                parent_directory=str(parameters.get("parent_directory") or "0"),
            )
        if action == "question_bank.directory.rename":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.rename_question_bank_directory(
                course,
                clazz,
                self._required(parameters, "directory"),
                self._required(parameters, "name"),
            )
        if action == "question_bank.directory.move":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.move_question_bank_directory(
                course,
                clazz,
                self._required(parameters, "directory"),
                self._required(parameters, "target_directory"),
            )
        if action == "question_bank.directory.reorder":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            try:
                target_position = int(self._required(parameters, "target_position"))
            except (TypeError, ValueError) as exc:
                raise ActionRuntimeError("target_position must be an integer") from exc
            return api.reorder_question_bank_directory(
                course,
                clazz,
                self._required(parameters, "directory"),
                target_position,
            )
        if action == "question_bank.directory.top.set":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.set_question_bank_directory_top(
                course,
                clazz,
                self._required(parameters, "directory"),
                self._boolean(parameters.get("top", True), "top"),
            )
        if action == "question_bank.directory.delete":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.delete_question_bank_directory(
                course,
                clazz,
                self._required(parameters, "directory"),
            )
        if action == "question_bank.question.add":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.add_question_bank_question(
                course,
                clazz,
                self._required(parameters, "question_type"),
                self._required(parameters, "stem"),
                directory=str(parameters.get("directory") or "0"),
                options=parameters.get("options"),
                correct_answer=parameters.get("correct_answer"),
                answers=parameters.get("answers"),
                answer=parameters.get("answer"),
                analysis=str(parameters.get("analysis") or ""),
                difficulty=parameters.get("difficulty", 0.8),
                content_format=str(parameters.get("content_format") or "plain"),
            )
        if action == "question_bank.question.update":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.update_question_bank_question(
                course,
                clazz,
                self._required(parameters, "question"),
                directory_id=str(parameters.get("directory_id") or "0"),
                stem=parameters.get("stem"),
                options=parameters.get("options"),
                correct_answer=parameters.get("correct_answer"),
                answers=parameters.get("answers"),
                answer=parameters.get("answer"),
                analysis=parameters.get("analysis"),
                difficulty=parameters.get("difficulty"),
                content_format=str(parameters.get("content_format") or "plain"),
            )
        if action == "question_bank.question.move":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.move_question_bank_question(
                course,
                clazz,
                self._required(parameters, "question"),
                self._required(parameters, "target_directory"),
                source_directory_id=str(parameters.get("source_directory_id") or "0"),
            )
        if action == "question_bank.question.reorder":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            try:
                target_position = int(self._required(parameters, "target_position"))
            except (TypeError, ValueError) as exc:
                raise ActionRuntimeError("target_position must be an integer") from exc
            return api.reorder_question_bank_question(
                course,
                clazz,
                self._required(parameters, "question"),
                target_position,
                directory_id=str(parameters.get("directory_id") or "0"),
            )
        if action == "question_bank.question.difficulty.update":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.update_question_bank_question_difficulty(
                course,
                clazz,
                self._required(parameters, "question"),
                self._required(parameters, "difficulty"),
                directory_id=str(parameters.get("directory_id") or "0"),
            )
        if action == "question_bank.question.delete":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.delete_question_bank_question(
                course,
                clazz,
                self._required(parameters, "question"),
                directory_id=str(parameters.get("directory_id") or "0"),
            )
        if action == "discussions.list":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.list_discussions(
                course,
                clazz,
                search=str(parameters.get("search") or "").strip(),
                class_only=bool(parameters.get("class_only", False)),
            )
        if action == "discussions.topic.read":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            try:
                order = int(parameters.get("order", 2))
            except (TypeError, ValueError) as exc:
                raise ActionRuntimeError("order must be 1 or 2") from exc
            return api.read_discussion_topic(
                course,
                clazz,
                self._required(parameters, "topic"),
                class_only=bool(parameters.get("class_only", False)),
                order=order,
                reply_search=str(parameters.get("reply_search") or "").strip(),
            )
        if action == "discussions.topic.create":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.create_discussion_topic(
                course,
                clazz,
                str(parameters.get("title") or ""),
                str(parameters.get("content") or ""),
                class_only=self._boolean(parameters.get("class_only", False), "class_only"),
                anonymous=self._boolean(parameters.get("anonymous", False), "anonymous"),
            )
        if action == "discussions.topic.edit":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.edit_discussion_topic(
                course,
                clazz,
                self._required(parameters, "topic"),
                title=(str(parameters["title"]) if parameters.get("title") is not None else None),
                content=(
                    str(parameters["content"]) if parameters.get("content") is not None else None
                ),
            )
        if action == "discussions.topic.top.set":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.set_discussion_topic_top(
                course,
                clazz,
                self._required(parameters, "topic"),
                self._boolean(parameters.get("top", True), "top"),
            )
        if action == "discussions.topic.delete":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.delete_discussion_topic(
                course,
                clazz,
                self._required(parameters, "topic"),
            )
        if action == "discussions.reply.create":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.create_discussion_reply(
                course,
                clazz,
                self._required(parameters, "topic"),
                self._required(parameters, "content"),
                reply_to=str(parameters.get("reply_to") or "").strip(),
                anonymous=self._boolean(parameters.get("anonymous", False), "anonymous"),
            )
        if action == "discussions.reply.edit":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.edit_discussion_reply(
                course,
                clazz,
                self._required(parameters, "topic"),
                self._required(parameters, "reply"),
                self._required(parameters, "content"),
            )
        if action == "discussions.reply.delete":
            api = self._api()
            course = api.get_course(self._required(parameters, "course"))
            clazz = resolve_class(course, parameters.get("clazz") or parameters.get("class"))
            return api.delete_discussion_reply(
                course,
                clazz,
                self._required(parameters, "topic"),
                self._required(parameters, "reply"),
            )
        if action == "command.plan":
            return route_command(self._required(parameters, "command")).to_dict()
        if action == "command.execute":
            return await self.execute_command(
                self._required(parameters, "command"), parameters.get("confirmation_token")
            )
        raise ActionRuntimeError(f"action has no handler: {action}")

    async def execute_command(
        self, command: str, confirmation_token: str | None = None
    ) -> dict[str, Any]:
        plan = route_command(command)
        if plan.action is None:
            return {"status": "unresolved", "plan": plan.to_dict()}
        if plan.missing_fields:
            return {"status": "needs_input", "plan": plan.to_dict()}
        result = await self.execute(plan.action, plan.parameters, confirmation_token)
        return {"status": result["status"], "plan": plan.to_dict(), "execution": result}

    @staticmethod
    def _required(parameters: dict[str, Any], key: str) -> str:
        value = str(parameters.get(key) or "").strip()
        if not value:
            raise ActionRuntimeError(f"missing required parameter: {key}")
        return value

    @staticmethod
    def _integer(value: Any, key: str) -> int:
        if isinstance(value, bool):
            raise ActionRuntimeError(f"{key} must be an integer")
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise ActionRuntimeError(f"{key} must be an integer") from exc

    @staticmethod
    def _number(value: Any, key: str) -> float:
        if isinstance(value, bool):
            raise ActionRuntimeError(f"{key} must be a finite number")
        try:
            result = float(value)
        except (TypeError, ValueError) as exc:
            raise ActionRuntimeError(f"{key} must be a finite number") from exc
        if not math.isfinite(result):
            raise ActionRuntimeError(f"{key} must be a finite number")
        return result

    @staticmethod
    def _boolean(value: Any, key: str) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, int) and value in (0, 1):
            return bool(value)
        normalized = str(value).strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off", ""}:
            return False
        raise ActionRuntimeError(f"{key} must be a boolean")

    @classmethod
    def _optional_boolean(cls, parameters: dict[str, Any], key: str) -> bool | None:
        if key not in parameters or parameters[key] is None:
            return None
        return cls._boolean(parameters[key], key)

    @staticmethod
    def _string_list(value: Any, key: str) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, (list, tuple)):
            return [str(item).strip() for item in value if str(item).strip()]
        raise ActionRuntimeError(f"{key} must be a list of strings")

    @classmethod
    def _optional_string_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        return cls._string_list(value, "labels")

    @staticmethod
    def _confirmation_summary(action: str, parameters: dict[str, Any]) -> str:
        if action == "learning.course.homework.redo":
            return (
                f"重做我学课程 {parameters.get('course')} 的作业 {parameters.get('homework')}；"
                "上一份作答记录会被覆盖，最终成绩以本次作答为准"
            )
        if action == "learning.course.integrity.accept":
            return (
                "代表当前学习通账号签署我学课程 "
                f"{parameters.get('course')} 的《在线学习诚信承诺书》；"
                "该操作会改变平台上的承诺状态"
            )
        if action == "subjects.folder.delete":
            suffix = "，并允许非空目录" if parameters.get("allow_nonempty") else ""
            return f"删除专题创作文件夹 {parameters.get('folder')}{suffix}"
        if action == "subjects.publish_status.update":
            operation = "发布" if parameters.get("published") else "取消发布"
            return f"{operation}专题 {parameters.get('subject')}"
        if action == "subjects.delete":
            return f"把专题 {parameters.get('subject')} 移入专题回收站"
        if action == "subjects.recycle.delete":
            return f"从专题回收站永久删除专题 {parameters.get('subject')}"
        if action == "detection.submit":
            source = parameters.get("file") or "粘贴文本"
            return (
                f"把 {source} 作为《{parameters.get('title')}》提交到大雅 "
                f"{parameters.get('type')} 检测；内容将发送给检测服务"
            )
        if action == "detection.comparison.submit":
            return (
                f"把文件 {parameters.get('file_1')} 与 {parameters.get('file_2')} "
                "提交到大雅两两比对服务"
            )
        if action == "detection.free_entitlement.use":
            return (
                f"消耗一次当前可用的单位免费检测权限，以解锁 "
                f"{parameters.get('type')} 记录 {parameters.get('record')} 的报告"
            )
        if action == "detection.record.delete":
            return (
                f"永久删除大雅 {parameters.get('type')} 检测记录 "
                f"{parameters.get('record')}；删除后不可恢复"
            )
        if action == "live.room.create":
            return f"新建不会自动开播的个人直播间《{parameters.get('title')}》"
        if action == "live.room.settings.update":
            labels = {
                "comments_enabled": "评论",
                "forwarding_enabled": "转发",
                "replay_enabled": "回看",
                "learning_app_only": "仅在学习通观看",
                "chat_content_review": "聊天内容审核",
                "login_required": "登录后观看",
                "picture_live": "图片直播",
                "access_password": "观看密码（值不回显）",
                "show_viewer_count": "观看人数显示",
                "reservations_enabled": "直播预约",
                "preupload_enabled": "预上传",
                "allowed_unit_ids": "观看单位限制",
                "replay_start_offset_seconds": "回看开始偏移",
            }
            changed = ", ".join(labels.get(key, key) for key in parameters if key != "room")
            return f"修改直播间 {parameters.get('room')} 的访问与互动设置：{changed or '无变更项'}"
        if action == "live.stream.credentials":
            return (
                f"读取直播间 {parameters.get('room')} 的完整 RTMP 推流凭据；"
                "该凭据可直接控制对外直播"
            )
        if action == "live.room.delete":
            return f"把个人直播间 {parameters.get('room')} 移入直播回收站"
        if action == "live.recycle.delete":
            return f"从直播回收站永久删除直播 {parameters.get('room')}"
        if action == "live.theme.create":
            return f"新建主题直播入口《{parameters.get('name')}》"
        if action == "live.theme.settings.update":
            labels = {
                "forwarding_enabled": "转发",
                "replay_enabled": "回看",
                "learning_app_only": "仅在学习通观看",
                "login_required": "登录后观看",
                "allowed_unit_ids": "观看单位限制",
            }
            changed = ", ".join(labels.get(key, key) for key in parameters if key != "theme")
            return f"修改主题直播 {parameters.get('theme')} 的访问设置：{changed or '无变更项'}"
        if action == "live.theme.room.add":
            return f"把个人直播 {parameters.get('room')} 加入主题直播 {parameters.get('theme')}"
        if action == "live.theme.room.create":
            return (
                f"在主题直播 {parameters.get('theme')} 中新建不会自动开播的子直播"
                f"《{parameters.get('title')}》"
            )
        if action == "live.theme.delete":
            return f"删除主题直播入口 {parameters.get('theme')}；其中个人直播仍保留"
        if action == "knowledge_hub.base.share.update":
            operation = "共享" if parameters.get("shared") else "取消共享"
            return (
                f"{operation}课程 {parameters.get('course')} 的 AI 知识库 "
                f"{parameters.get('base')}；共享状态会改变其他用户能否复用该知识库"
            )
        if action == "knowledge_hub.base.delete":
            return (
                f"永久删除课程 {parameters.get('course')} 的 AI 知识库 "
                f"{parameters.get('base')} 及其中内容；默认知识库受保护"
            )
        if action == "knowledge_hub.document.delete":
            return (
                f"永久删除课程 {parameters.get('course')} 的 AI 知识库 "
                f"{parameters.get('base')} 中的文档 {parameters.get('document')}"
            )
        if action == "ai_workbench.group.create":
            return (
                f"在课程 {parameters.get('course')} 的 AI 工作台新建指令分组"
                f"《{parameters.get('name')}》"
            )
        if action == "ai_workbench.group.rename":
            return (
                f"把课程 {parameters.get('course')} 的 AI 指令分组 "
                f"{parameters.get('group')} 重命名为《{parameters.get('name')}》"
            )
        if action == "ai_workbench.group.reorder":
            return (
                f"将课程 {parameters.get('course')} 的全部 AI 指令分组顺序调整为 "
                f"{parameters.get('groups')}"
            )
        if action == "ai_workbench.group.delete":
            suffix = "，并允许删除非空分组" if parameters.get("allow_nonempty") else ""
            return (
                f"删除课程 {parameters.get('course')} 的 AI 指令分组 "
                f"{parameters.get('group')}{suffix}"
            )
        if action == "ai_workbench.command.create":
            return (
                f"在课程 {parameters.get('course')} 的 AI 指令分组 "
                f"{parameters.get('group')} 新建默认未公开的指令《{parameters.get('name')}》"
            )
        if action == "ai_workbench.command.update":
            changed = {
                key: value
                for key, value in parameters.items()
                if key not in {"course", "clazz", "class", "command", "group"}
            }
            return (
                f"修改课程 {parameters.get('course')} 的 AI 指令 "
                f"{parameters.get('command')}：{changed}"
            )
        if action == "ai_workbench.command.move":
            return (
                f"把课程 {parameters.get('course')} 的 AI 指令 {parameters.get('command')} "
                f"移到分组 {parameters.get('target_group')}"
            )
        if action == "ai_workbench.command.reorder":
            role = "教师端" if str(parameters.get("role_type")) == "0" else "学生端"
            return (
                f"调整课程 {parameters.get('course')} 的分组 {parameters.get('group')} "
                f"{role}完整 AI 指令顺序为 {parameters.get('commands')}"
            )
        if action == "ai_workbench.command.publish_status.update":
            if parameters.get("published"):
                return (
                    f"把课程 {parameters.get('course')} 的 AI 指令 "
                    f"{parameters.get('command')} 发布到开放平台；"
                    "发布后所有互联网用户均可见并可引用"
                )
            return f"取消发布课程 {parameters.get('course')} 的 AI 指令 {parameters.get('command')}"
        if action == "ai_workbench.command.delete":
            return (
                f"删除或移除课程 {parameters.get('course')} 的 AI 指令 {parameters.get('command')}"
            )
        if action == "ai_workbench.recommendation.add":
            return (
                f"把推荐 AI 指令 {parameters.get('recommendation')} 引用到课程 "
                f"{parameters.get('course')} 的分组 {parameters.get('group')}"
            )
        if action == "task_engine.folder.delete":
            suffix = "，其中任务将移至根目录" if parameters.get("allow_nonempty") else ""
            return (
                f"删除课程 {parameters.get('course')} 的任务引擎文件夹 "
                f"{parameters.get('folder')}{suffix}"
            )
        if action == "task_engine.task.delete":
            return (
                f"把课程 {parameters.get('course')} 的任务引擎任务 "
                f"{parameters.get('task')} 移入回收站"
            )
        if action == "task_engine.label.delete":
            return f"删除课程 {parameters.get('course')} 的任务引擎标签 {parameters.get('label')}"
        if action == "task_engine.publish_status.update":
            operation = "发布给所选学习对象" if parameters.get("published") else "取消发布"
            return (
                f"{operation}课程 {parameters.get('course')} 的任务引擎任务 "
                f"{parameters.get('task')}；此操作会改变学生是否可学习该任务"
            )
        if action == "knowledge_graph.event.create":
            return (
                f"在课程 {parameters.get('course')} 中创建并立即启用课程图谱任务事件"
                f"《{parameters.get('name')}》；满足条件时会自动改变学生端显示内容"
            )
        if action == "knowledge_graph.event.update":
            return (
                f"修改课程 {parameters.get('course')} 的课程图谱任务事件 "
                f"{parameters.get('event')}；新条件和执行动作会立即生效"
            )
        if action == "knowledge_graph.event.delete":
            return (
                f"删除课程 {parameters.get('course')} 的课程图谱任务事件 "
                f"{parameters.get('event')}；删除后自动执行规则将停止且无法恢复"
            )
        if action == "knowledge_graph.node.delete":
            return (
                f"删除课程 {parameters.get('course')} 的课程图谱节点 "
                f"{parameters.get('node')} 及其全部父子关系后代；删除后无法恢复"
            )
        if action == "knowledge_graph.node.relation.add":
            return (
                f"在课程 {parameters.get('course')} 中，为图谱节点 {parameters.get('node')} "
                f"添加指向 {parameters.get('target')} 的 {parameters.get('relation')}；"
                "保存后学生端图谱关系会立即变化"
            )
        if action == "knowledge_graph.node.relation.remove":
            return (
                f"从课程 {parameters.get('course')} 的图谱节点 {parameters.get('node')} "
                f"移除指向 {parameters.get('target')} 的 {parameters.get('relation')}；"
                "该节点关系将不再显示"
            )
        if action == "knowledge_graph.relation_type.delete":
            return (
                f"删除课程 {parameters.get('course')} 的自定义图谱关系定义 "
                f"{parameters.get('relation')}；使用该定义的关系将受影响，删除后无法恢复"
            )
        if action == "knowledge_graph.label_group.delete":
            return (
                f"删除课程 {parameters.get('course')} 的课程图谱标签组 "
                f"{parameters.get('group')} 及其中全部标签；删除后无法恢复"
            )
        if action == "knowledge_graph.label.delete":
            return (
                f"删除课程 {parameters.get('course')} 的课程图谱标签 "
                f"{parameters.get('label')}；相关节点将失去该标签，删除后无法恢复"
            )
        if action == "knowledge_graph.settings.update":
            changed = [
                label
                for key, label in (
                    ("show_all_relations", "显示全部关系"),
                    ("show_all_topic_names", "显示全部节点名称"),
                    ("navigation_node_scale", "导航节点缩放"),
                    ("graph_background_color", "图谱背景色"),
                )
                if key in parameters
            ]
            return (
                f"修改课程 {parameters.get('course')} 的课程图谱显示设置："
                f"{'、'.join(changed) or '未提供字段'}；保存后学生端图谱外观会随之变化"
            )
        if action == "knowledge_graph.advanced_settings.update":
            changed = [
                label
                for key, label in (
                    ("topic_card", "知识点卡片"),
                    ("teach_target", "教学目标"),
                    ("study_hours_enabled", "学时"),
                    ("classify_relation_data", "分类关系"),
                    ("selftest_included", "纳入自测"),
                    ("micro_preview", "微课预览"),
                    ("micro_scale_mode", "微课缩放模式"),
                )
                if key in parameters
            ]
            return (
                f"修改课程 {parameters.get('course')} 的课程图谱高级设置："
                f"{'、'.join(changed) or '未提供字段'}；保存后学生端课程图谱与微课行为会随之变化"
            )
        if action == "knowledge_graph.model.visibility.update":
            operation = "显示" if parameters.get("visible") else "隐藏"
            return (
                f"在课程 {parameters.get('course')} 中{operation}图谱模型 "
                f"{parameters.get('model')}；学生端可见性会随之变化"
            )
        if action == "knowledge_graph.model.classes.update":
            classes = parameters.get("visible_classes") or []
            return (
                f"把课程 {parameters.get('course')} 的图谱模型 {parameters.get('model')} "
                f"开放给这些班级：{classes}；其他班级将看不到该模型"
            )
        if action == "knowledge_graph.model.delete":
            return (
                f"删除课程 {parameters.get('course')} 的自定义图谱模型 "
                f"{parameters.get('model')} 及其中专属配置；删除后无法恢复"
            )
        if action == "class_activities.group.delete":
            suffix = "，其中活动将保留并移出该分组" if parameters.get("allow_nonempty") else ""
            return (
                f"删除课程 {parameters.get('course')} 的班级活动分组 "
                f"{parameters.get('group')}{suffix}"
            )
        if action == "class_activities.activity.start":
            return (
                f"开始课程 {parameters.get('course')} 的班级活动 "
                f"{parameters.get('activity')}；学生将可以参与"
            )
        if action == "class_activities.activity.end":
            return (
                f"结束课程 {parameters.get('course')} 的班级活动 "
                f"{parameters.get('activity')}；学生将不能继续参与"
            )
        if action == "class_activities.activity.delete":
            return (
                f"把课程 {parameters.get('course')} 的班级活动 "
                f"{parameters.get('activity')} 移入回收站"
            )
        if action == "class_activities.recycle.items.delete":
            return (
                f"从课程 {parameters.get('course')} 的班级活动回收站永久删除 "
                f"{parameters.get('activities')}，删除后无法恢复"
            )
        if action == "notes.delete":
            return f"永久删除当前账号的个人笔记 {parameters.get('note')}"
        if action == "inbox.notice.delete":
            return (
                f"删除当前账号 {parameters.get('scope') or 'received'} 收件箱中的通知 "
                f"{parameters.get('notice')}，使其从活动列表移入回收站"
            )
        if action == "inbox.notice.send":
            return (
                f"向个人收件人 {parameters.get('recipients')} 发送通知《{parameters.get('title')}》"
            )
        if action == "inbox.draft.delete":
            return f"删除个人通知草稿 {parameters.get('draft')}"
        if action == "inbox.folder.delete":
            return f"删除收件箱文件夹 {parameters.get('folder')}，其中通知将移入回收站"
        if action == "inbox.recycle.items.delete":
            return f"从收件箱回收站永久删除通知 {parameters.get('notices')}，删除后无法恢复"
        if action == "inbox.recycle.empty":
            return "永久清空收件箱通知回收站，全部内容删除后无法恢复"
        if action == "contacts.follow_status.update":
            operation = "关注" if parameters.get("followed") else "取消关注"
            return f"{operation}联系人 {parameters.get('person')}"
        if action == "contacts.team.create":
            return (
                f"用联系人 {parameters.get('members')} 新建通讯录团队《{parameters.get('name')}》"
            )
        if action == "contacts.team.rename":
            return f"将通讯录团队 {parameters.get('team')} 重命名为《{parameters.get('name')}》"
        if action == "contacts.team.members.add":
            return f"向通讯录团队 {parameters.get('team')} 添加成员 {parameters.get('members')}"
        if action == "contacts.team.member.remove":
            return f"从通讯录团队 {parameters.get('team')} 移除成员 {parameters.get('member')}"
        if action == "contacts.team.delete":
            return f"删除自建通讯录团队 {parameters.get('team')}"
        if action == "contacts.team.exit":
            return f"退出他人创建的通讯录团队 {parameters.get('team')}"
        if action == "groups.create":
            return (
                f"新建共享小组《{parameters.get('name')}》，简介为 "
                f"{parameters.get('description') or '空'}"
            )
        if action == "groups.update":
            return (
                f"修改共享小组 {parameters.get('group')} 的公开信息："
                f"名称={parameters.get('name')}，简介={parameters.get('description')}"
            )
        if action == "groups.logo.update":
            return (
                f"将本地图像 {parameters.get('file')} 上传并设为个人小组 "
                f"{parameters.get('group')} 的头像"
            )
        if action == "groups.modules.update":
            return (
                f"将个人小组 {parameters.get('group')} 的启用模块类型设为 "
                f"{parameters.get('enabled_type_ids')}；视频类型 1 始终保留"
            )
        if action == "groups.settings.update":
            return f"修改个人小组 {parameters.get('group')} 的设置：{parameters.get('changes')}"
        if action == "groups.levels.series.update":
            return (
                f"将个人小组 {parameters.get('group')} 的等级头衔系列切换为 "
                f"{parameters.get('series')}"
            )
        if action == "groups.levels.custom.update":
            levels = parameters.get("levels")
            count = len(levels) if isinstance(levels, list) else 0
            return f"保存个人小组 {parameters.get('group')} 的完整 {count} 级自定义头衔"
        if action == "groups.growth_rules.update":
            return (
                f"修改个人小组 {parameters.get('group')} 的成长值规则：{parameters.get('changes')}"
            )
        if action == "groups.growth_rules.series.update":
            return (
                f"将个人小组 {parameters.get('group')} 的成长值规则系列切换为 "
                f"{parameters.get('series')}"
            )
        if action == "groups.speaking_rules.update":
            return (
                f"修改个人小组 {parameters.get('group')} 的发言规则："
                f"{parameters.get('changes')}，附件要求={parameters.get('attachment_rules')}"
            )
        if action == "groups.notice.send":
            return (
                f"向个人小组 {parameters.get('group')} 发送通知"
                f"《{parameters.get('title')}》：{parameters.get('content')}"
            )
        if action == "groups.review_reminder.create":
            return (
                f"在个人小组 {parameters.get('group')} 为审核人员 PUID "
                f"{parameters.get('puids')} 创建审核提醒：{parameters.get('weeks')} "
                f"{parameters.get('start_time')}-{parameters.get('end_time')}"
            )
        if action == "groups.review_reminder.update":
            changes = {
                key: value for key, value in parameters.items() if key not in {"group", "reminder"}
            }
            return (
                f"修改个人小组 {parameters.get('group')} 的审核提醒 "
                f"{parameters.get('reminder')}：{changes}"
            )
        if action == "groups.review_reminders.delete":
            return (
                f"删除个人小组 {parameters.get('group')} 的审核提醒 {parameters.get('reminders')}"
            )
        if action == "groups.labels.delete":
            return f"删除个人小组 {parameters.get('group')} 的标签 {parameters.get('labels')}"
        if action == "groups.deletion_reasons.delete":
            return (
                f"删除个人小组 {parameters.get('group')} 的预设删除原因 {parameters.get('reasons')}"
            )
        if action == "groups.recycle.items.delete":
            return (
                f"永久删除个人小组 {parameters.get('group')} 回收站项目 "
                f"{parameters.get('items')}，删除后无法恢复"
            )
        if action == "groups.recycle.empty":
            return (
                f"永久清空个人小组 {parameters.get('group')} 的回收站，"
                "其中全部话题、评论和文件夹删除后无法恢复"
            )
        if action == "groups.export.cancel":
            return (
                f"取消并移除个人小组 {parameters.get('group')} 的导出任务 "
                f"{parameters.get('export')}"
            )
        if action == "groups.activity.create":
            status = "上线" if parameters.get("online") else "保存为未上线"
            return (
                f"在个人小组 {parameters.get('group')} 新建活动图"
                f"《{parameters.get('title')}》并{status}"
            )
        if action == "groups.activity.update":
            fields = {
                key: value for key, value in parameters.items() if key not in {"group", "activity"}
            }
            return (
                f"修改个人小组 {parameters.get('group')} 的活动图 "
                f"{parameters.get('activity')}：{fields}"
            )
        if action == "groups.activity.online_status.update":
            operation = "上线" if parameters.get("online") else "下线"
            return (
                f"{operation}个人小组 {parameters.get('group')} 的活动图 "
                f"{parameters.get('activity')}"
            )
        if action == "groups.activities.reorder":
            return (
                f"将个人小组 {parameters.get('group')} 的已上线活动图顺序调整为 "
                f"{parameters.get('activities')}"
            )
        if action == "groups.activity.delete":
            return f"删除个人小组 {parameters.get('group')} 的活动图 {parameters.get('activity')}"
        if action == "groups.quit":
            return f"退出小组 {parameters.get('group')}，当前账号将失去该小组的成员访问"
        if action == "groups.dismiss":
            return f"解散本人创建的小组 {parameters.get('group')}，小组将从成员列表中消失"
        if action == "groups.members.add":
            return f"向个人小组 {parameters.get('group')} 添加成员 PUID {parameters.get('puids')}"
        if action == "groups.members.bulk_import":
            return (
                f"从 XLSX 文件 {parameters.get('file')} 向个人小组 "
                f"{parameters.get('group')} 批量导入成员；该操作会占用一次每日额度"
            )
        if action == "groups.member.manager_status.update":
            operation = "设为管理员" if parameters.get("manager") else "取消管理员"
            return (
                f"将个人小组 {parameters.get('group')} 的成员 "
                f"{parameters.get('member')} {operation}"
            )
        if action == "groups.member.permissions.update":
            return (
                f"修改个人小组 {parameters.get('group')} 的管理员 "
                f"{parameters.get('member')} 权限：{parameters.get('changes')}"
            )
        if action == "groups.member.remove":
            return f"从个人小组 {parameters.get('group')} 移除成员 {parameters.get('member')}"
        if action == "groups.creator.transfer":
            return (
                f"将个人小组 {parameters.get('group')} 的创建者身份转让给成员 "
                f"{parameters.get('member')}，当前账号将立即失去创建者身份和相应权限"
            )
        if action == "groups.members.external.clear":
            return f"清除个人小组 {parameters.get('group')} 中全部非学习通成员"
        if action == "groups.folder.delete":
            return f"删除个人小组文件夹 {parameters.get('folder')}"
        if action == "groups.topic.create":
            return (
                f"向个人小组 {parameters.get('group')} 发布话题"
                f"《{parameters.get('title') or ''}》："
                f"{parameters.get('content') or ''}"
            )
        if action == "groups.topic.update":
            return (
                f"编辑个人小组 {parameters.get('group')} 的话题 {parameters.get('topic')}："
                f"标题={parameters.get('title')}，正文={parameters.get('content')}"
            )
        if action == "groups.topic.delete":
            return f"删除个人小组 {parameters.get('group')} 的话题 {parameters.get('topic')}"
        if action == "groups.topic.choice_status.update":
            operation = "设为精华" if parameters.get("choice") else "取消精华"
            return (
                f"将个人小组 {parameters.get('group')} 的话题 {parameters.get('topic')} {operation}"
            )
        if action == "groups.topic.praise_status.update":
            operation = "点赞" if parameters.get("praised") else "取消点赞"
            return (
                f"对个人小组 {parameters.get('group')} 的话题 {parameters.get('topic')} {operation}"
            )
        if action == "groups.topics.score.set":
            return (
                f"给个人小组 {parameters.get('group')} 的话题 "
                f"{parameters.get('topics')} 批量评分 {parameters.get('score')}"
            )
        if action == "groups.topics.delete":
            return f"批量删除个人小组 {parameters.get('group')} 的话题 {parameters.get('topics')}"
        if action == "groups.topic.reply.create":
            target = f"，回复 {parameters.get('reply_to')}" if parameters.get("reply_to") else ""
            return (
                f"回复个人小组 {parameters.get('group')} 的话题 {parameters.get('topic')}"
                f"{target}：{parameters.get('content')}"
            )
        if action == "groups.topic.reply.update":
            return (
                f"将个人小组 {parameters.get('group')} 的话题 {parameters.get('topic')} 中回复 "
                f"{parameters.get('reply')} 修改为：{parameters.get('content')}"
            )
        if action == "groups.topic.reply.delete":
            return (
                f"删除个人小组 {parameters.get('group')} 的话题 {parameters.get('topic')} 中回复 "
                f"{parameters.get('reply')}"
            )
        if action == "groups.topic.folder.delete":
            return f"删除个人小组 {parameters.get('group')} 的话题文件夹 {parameters.get('folder')}"
        if action == "groups.topic.folders.delete":
            return (
                f"批量删除个人小组 {parameters.get('group')} 的话题文件夹 "
                f"{parameters.get('folders')}"
            )
        if action == "groups.topic.draft.publish":
            return (
                f"将个人小组 {parameters.get('group')} 的未发布话题草稿 "
                f"{parameters.get('draft')} 正式发布"
            )
        if action == "classes.create":
            return f"在课程 {parameters.get('course')} 中新建班级《{parameters.get('name')}》"
        if action == "class.rename":
            return (
                f"将课程 {parameters.get('course')} 的班级 "
                f"{parameters.get('clazz') or parameters.get('class') or '当前班级'} "
                f"重命名为《{parameters.get('name')}》"
            )
        if action == "class.settings.update":
            changes = {
                key: value
                for key, value in parameters.items()
                if key not in {"course", "clazz", "class"}
            }
            return (
                f"修改课程 {parameters.get('course')} 的班级 "
                f"{parameters.get('clazz') or parameters.get('class') or '当前班级'} 设置："
                f"{changes}"
            )
        if action == "class.delete":
            return (
                f"删除课程 {parameters.get('course')} 的班级 "
                f"{parameters.get('clazz') or parameters.get('class') or '当前班级'}"
            )
        if action == "course_assets.folder.create":
            return (
                f"在课程 {parameters.get('course')} 的 {parameters.get('kind')} 目录 "
                f"{parameters.get('parent') or '根目录'} 新建文件夹《{parameters.get('name')}》"
            )
        if action == "course_assets.cloud_files.import":
            return (
                f"把个人云盘文件 {parameters.get('resources')} 导入课程 "
                f"{parameters.get('course')} 的 {parameters.get('kind')} 目录 "
                f"{parameters.get('destination') or '根目录'}"
            )
        if action == "course_assets.item.copy":
            return (
                f"在课程 {parameters.get('course')} 的 {parameters.get('kind')} 中复制 "
                f"{parameters.get('asset')}"
            )
        if action == "course_assets.items.delete":
            return (
                f"将课程 {parameters.get('course')} 的 {parameters.get('kind')} 内容 "
                f"{parameters.get('assets')} 移入对应回收站"
            )
        if action == "course_assets.recycle.restore":
            return (
                f"从课程 {parameters.get('course')} 的 {parameters.get('kind')} 回收站恢复 "
                f"{parameters.get('assets')}"
            )
        if action == "course_assets.recycle.items.delete":
            return (
                f"从课程 {parameters.get('course')} 的 {parameters.get('kind')} 回收站永久删除 "
                f"{parameters.get('assets')}"
            )
        if action == "chapters.open_status.update":
            return (
                f"将课程 {parameters.get('course')} 的章节 {parameters.get('chapters')} "
                f"在班级 {parameters.get('classes') or parameters.get('clazz') or '当前班级'} "
                f"设置为 {parameters.get('status')}；开始={parameters.get('begin', '')}，"
                f"结束={parameters.get('end', '')}"
            )
        if action == "chapters.delete":
            return (
                f"永久删除课程 {parameters.get('course')} 的章节 "
                f"{parameters.get('chapters')} 及其全部子目录和页面内容"
            )
        if action == "chapters.card.delete":
            return (
                f"永久删除课程 {parameters.get('course')} 的章节 "
                f"{parameters.get('chapter')} 中的页面 {parameters.get('card')}"
            )
        if action == "resources.folder.create":
            return (
                f"在课程 {parameters.get('course')} 的资料目录 "
                f"{parameters.get('parent') or '根目录'} 新建并公开文件夹"
                f"《{parameters.get('name')}》"
            )
        if action == "resources.link.create":
            return (
                f"在课程 {parameters.get('course')} 的资料目录 "
                f"{parameters.get('parent') or '根目录'} 发布网址资料《{parameters.get('name')}》"
            )
        if action == "resources.file.upload":
            return (
                f"把本地文件 {parameters.get('file_path')} 上传并发布到课程 "
                f"{parameters.get('course')} 的资料目录 {parameters.get('parent') or '根目录'}"
            )
        if action == "resources.import.execute":
            return (
                f"从课程 {parameters.get('source_course')} 向课程 {parameters.get('course')} "
                f"导入资料 {parameters.get('resources')}，目标目录为 "
                f"{parameters.get('destination') or '根目录'}"
            )
        if action == "resources.download_permission.update":
            return (
                f"将课程 {parameters.get('course')} 的资料 {parameters.get('resources')} "
                f"下载权限设为 {parameters.get('allow_download')}"
            )
        if action == "resources.folder.visibility.update":
            return (
                f"将课程 {parameters.get('course')} 的资料文件夹 {parameters.get('folder')} "
                f"可见范围设为 {parameters.get('mode')}，班级={parameters.get('classes', [])}"
            )
        if action == "resources.share_link.create":
            return (
                f"为课程 {parameters.get('course')} 的资料 {parameters.get('resource')} "
                "生成可分享访问链接"
            )
        if action == "resources.copy":
            return (
                f"在课程 {parameters.get('course')} 中复制资料 "
                f"{parameters.get('resource')}，并在原目录创建副本"
            )
        if action == "resources.cloud_disk.copy":
            return (
                f"把课程 {parameters.get('course')} 的资料 {parameters.get('resource')} "
                f"复制到个人云盘目录 {parameters.get('destination') or '根目录'}"
            )
        if action == "resources.cloud_files.import":
            return (
                f"把云盘文件 {parameters.get('resources')} 导入课程 "
                f"{parameters.get('course')} 的资料目录 "
                f"{parameters.get('destination') or '根目录'}"
            )
        if action == "resources.cloud_folder.import":
            return (
                f"把云盘文件夹 {parameters.get('resource')} 导入课程 "
                f"{parameters.get('course')} 的资料目录 "
                f"{parameters.get('destination') or '根目录'}"
            )
        if action == "resources.label.delete":
            return f"删除课程 {parameters.get('course')} 的资料标签 {parameters.get('label')}"
        if action == "resources.labels.update":
            return (
                f"将课程 {parameters.get('course')} 的资料 {parameters.get('resources')} "
                f"完整标签集合替换为 {parameters.get('labels', [])}"
            )
        if action == "resources.delete":
            return (
                f"永久删除课程 {parameters.get('course')} 的资料 "
                f"{parameters.get('resources')}；文件夹将连同内部内容一起删除"
            )
        if action == "cloud_disk.items.delete":
            return (
                f"从当前账号个人云盘的活动区删除 {parameters.get('resources')}；"
                "执行后将用全局搜索确认其消失"
            )
        if action == "cloud_disk.folder.create":
            return (
                f"在个人云盘目录 {parameters.get('parent') or '根目录'} 新建"
                f"{'协作' if parameters.get('shared') else '私有'}文件夹"
                f"《{parameters.get('name')}》"
            )
        if action == "cloud_disk.recycle.restore":
            return (
                f"从个人云盘回收站恢复 {parameters.get('resources')}；同名冲突策略为 "
                f"{parameters.get('conflict_policy') or 'keep_both'}"
            )
        if action == "cloud_disk.recycle.items.delete":
            return f"从个人云盘回收站永久删除 {parameters.get('resources')}"
        if action == "cloud_disk.recycle.empty":
            return "永久清空当前账号的个人云盘回收站"
        if action == "homework.score.set":
            return (
                f"为 {parameters.get('submission')} 在课程 {parameters.get('course')} 的作业 "
                f"{parameters.get('homework')} 提交分数 {parameters.get('score')}"
            )
        if action == "homework.draft.delete":
            return f"永久删除课程 {parameters.get('course')} 的作业草稿 {parameters.get('draft')}"
        if action == "homework.question.delete":
            return (
                f"永久删除课程 {parameters.get('course')} 的作业 "
                f"{parameters.get('homework')} 中的题目 {parameters.get('question')}"
            )
        if action == "exam.question.delete":
            return (
                f"永久删除课程 {parameters.get('course')} 的试卷 "
                f"{parameters.get('paper')} 中的题目 {parameters.get('question')}"
            )
        if action == "exam.question_type.delete":
            return (
                f"永久删除课程 {parameters.get('course')} 的试卷 "
                f"{parameters.get('paper')} 中的题型 {parameters.get('question_type')}，"
                "以及该题型在这份试卷中的全部题目"
            )
        if action == "exam.paper.delete":
            return (
                f"将课程 {parameters.get('course')} 试卷库中的试卷 "
                f"{parameters.get('paper')} 移入回收站"
            )
        if action == "exam.paper_folder.delete":
            return (
                f"将课程 {parameters.get('course')} 试卷库中的文件夹 "
                f"{parameters.get('folder')} 及其内容移入回收站"
            )
        if action == "question_bank.directory.permissions.update":
            changes: list[str] = []
            if "share_scope" in parameters:
                changes.append(f"共享范围={parameters.get('share_scope')}")
            if "selected_teachers" in parameters:
                changes.append(f"指定教师={parameters.get('selected_teachers')}")
            if "allow_student_self_practice" in parameters:
                changes.append(
                    "学生抽题自测="
                    + ("允许" if parameters.get("allow_student_self_practice") else "禁止")
                )
            private_effect = (
                "；设为私有时，平台会把目录中非本人创建的题目移到题库根目录"
                if str(parameters.get("share_scope") or "").strip().lower()
                in {"1", "private", "self", "私有", "仅自己"}
                else ""
            )
            return (
                f"修改课程 {parameters.get('course')} 的题库目录 "
                f"{parameters.get('directory')} 权限：{', '.join(changes) or '按请求更新'}"
                f"{private_effect}"
            )
        if action == "question_bank.question_type.delete":
            return (
                f"删除课程 {parameters.get('course')} 题库中的题型 "
                f"{parameters.get('question_type')}"
            )
        if action == "question_bank.label.delete":
            return (
                f"删除课程 {parameters.get('course')} 题库中的标签 "
                f"{parameters.get('label')} 及其全部子标签"
            )
        if action == "question_bank.question.labels.sync":
            return (
                f"按 {parameters.get('mode', 'replace')} 模式设置课程 "
                f"{parameters.get('course')} 题库题目 "
                f"{parameters.get('questions') or parameters.get('question')} 的标签 "
                f"{parameters.get('labels') or []}，并同步修改引用这些题目的作业和考试"
            )
        if action == "question_bank.topic.delete":
            return (
                f"删除课程 {parameters.get('course')} 题库中的知识点或分类 "
                f"{parameters.get('topic')}；若为分类，将一并删除全部后代节点及其关联"
            )
        if action == "question_bank.question.topics.sync":
            return (
                f"按 {parameters.get('mode', 'replace')} 模式设置课程 "
                f"{parameters.get('course')} 题库题目 "
                f"{parameters.get('questions') or parameters.get('question')} 的知识点 "
                f"{parameters.get('topics') or []}，并同步修改引用这些题目的作业和考试"
            )
        if action == "question_bank.items.lock":
            return (
                f"锁定课程 {parameters.get('course')} 题库中的题目 "
                f"{parameters.get('questions') or []} 和目录 "
                f"{parameters.get('directories') or []}"
            )
        if action == "question_bank.items.unlock":
            return (
                f"解锁课程 {parameters.get('course')} 题库中的项目 "
                f"{parameters.get('items') or parameters.get('item')}"
            )
        if action == "question_bank.recycle.delete":
            return (
                f"永久删除课程 {parameters.get('course')} 题库回收站中的项目 "
                f"{parameters.get('items') or parameters.get('item')}，删除后无法恢复"
            )
        if action == "question_bank.recycle.empty":
            return f"永久清空课程 {parameters.get('course')} 的全部题库回收站内容"
        if action == "question_bank.directory.delete":
            return (
                f"将课程 {parameters.get('course')} 题库中的目录 "
                f"{parameters.get('directory')} 及其内容移入回收站"
            )
        if action == "question_bank.question.delete":
            return (
                f"将课程 {parameters.get('course')} 题库中的题目 "
                f"{parameters.get('question')} 移入回收站"
            )
        if action == "homework.library.publish":
            target = parameters.get("target_classes") or parameters.get("clazz") or "当前班级"
            return (
                f"将课程 {parameters.get('course')} 作业库中的《{parameters.get('homework')}》"
                f"发放到班级 {target}；"
                f"开始={parameters.get('start_time', 'now')}，结束={parameters.get('end_time', '')}"
            )
        if action == "course.study_monitor.remind":
            return (
                f"向课程 {parameters.get('course')} 中的学生 {parameters.get('student')} "
                f"发送异常学习提醒《{parameters.get('title')}》：{parameters.get('content')}"
            )
        if action == "class.student.restore":
            return (
                f"将课程 {parameters.get('course')} 的班级 "
                f"{parameters.get('clazz') or parameters.get('class') or '当前班级'} 中的退课记录 "
                f"{parameters.get('student')} 恢复为在班学习状态"
            )
        if action == "class.student.add_from_bank":
            return (
                f"将学校学生库中的 {parameters.get('student')} 添加到课程 "
                f"{parameters.get('course')} 的班级 "
                f"{parameters.get('clazz') or parameters.get('class') or '当前班级'}"
            )
        if action == "class.student.add_by_identity":
            return (
                f"将学生 {parameters.get('name')}（{parameters.get('identity_type', 'student_no')}="
                f"{parameters.get('identity')}）添加到课程 {parameters.get('course')} 的班级 "
                f"{parameters.get('clazz') or parameters.get('class') or '当前班级'}"
            )
        if action == "class.student.remove":
            return (
                f"从课程 {parameters.get('course')} 的班级 "
                f"{parameters.get('clazz') or parameters.get('class') or '当前班级'} 移除学生 "
                f"{parameters.get('student')}"
            )
        if action == "class.join_application.decide":
            decision = "批准" if parameters.get("decision") == "approve" else "拒绝"
            return (
                f"{decision}课程 {parameters.get('course')} 的班级 "
                f"{parameters.get('clazz') or parameters.get('class') or '当前班级'} 中的入班申请 "
                f"{parameters.get('application')}"
            )
        if action == "class.student.move":
            return (
                f"将课程 {parameters.get('course')} 的学生 {parameters.get('student')} 从班级 "
                f"{parameters.get('clazz') or parameters.get('class') or '当前班级'} 移动到班级 "
                f"{parameters.get('target_clazz')}"
            )
        if action == "course.teacher.add_from_bank":
            role = "助教" if parameters.get("role") == "assistant" else "教师"
            return (
                f"将教师库中的 {parameters.get('teacher')} 以{role}身份加入课程 "
                f"{parameters.get('course')} 的教学团队"
            )
        if action == "course.teacher.add_by_identity":
            role = "助教" if parameters.get("role") == "assistant" else "教师"
            return (
                f"将 {parameters.get('name')}（{parameters.get('identity_type', 'employee_no')}="
                f"{parameters.get('identity')}）以{role}身份加入课程 {parameters.get('course')} "
                "的教学团队"
            )
        if action == "course.teacher.remove":
            return f"从课程 {parameters.get('course')} 的教学团队移除 {parameters.get('teacher')}"
        if action == "course.teacher.permissions.update":
            return (
                f"修改课程 {parameters.get('course')} 中教学团队成员 "
                f"{parameters.get('teacher')} 的权限：{parameters.get('changes')}"
            )
        if action == "course.study_monitor.clear":
            return (
                f"清除课程 {parameters.get('course')} 中学生 {parameters.get('student')} "
                "当前可清除的异常学习记录"
            )
        if action == "course.grade_visibility.set":
            return (
                f"将课程 {parameters.get('course')} 的成绩可见班级完整设置为 "
                f"{parameters.get('visible_classes')}；"
                f"定时开放={parameters.get('scheduled_open', False)}，"
                f"开放时间={parameters.get('open_at', '')}，"
                f"显示排名={parameters.get('students_can_view_rank', False)}，"
                "显示班级平均分="
                f"{parameters.get('students_can_view_class_average', False)}"
            )
        if action == "course.grade_override.set":
            requested = parameters.get("score")
            value = (
                "恢复自动计算"
                if requested is None or str(requested) in {"clear", "auto"}
                else requested
            )
            return (
                f"将课程 {parameters.get('course')} 中学生 {parameters.get('student')} 的综合成绩"
                f"设置为 {value}"
            )
        if action == "notices.send":
            recipients = (
                parameters.get("recipient_classes") or parameters.get("clazz") or ("当前班级")
            )
            return (
                f"向课程 {parameters.get('course')} 的 {recipients} 发送通知"
                f"《{parameters.get('title')}》：{parameters.get('content')}"
            )
        if action == "notices.schedule":
            recipients = (
                parameters.get("recipient_classes") or parameters.get("clazz") or ("当前班级")
            )
            return (
                f"将课程 {parameters.get('course')} 的 {recipients} 通知"
                f"《{parameters.get('title')}》设置为 {parameters.get('send_at')} 定时发送："
                f"{parameters.get('content')}"
            )
        if action == "notices.draft.delete":
            return f"删除课程 {parameters.get('course')} 的通知草稿 {parameters.get('draft')}"
        if action == "notices.edit":
            return (
                f"将课程 {parameters.get('course')} 的通知 {parameters.get('notice')} 修改为"
                f"《{parameters.get('title')}》：{parameters.get('content')}"
            )
        if action == "notices.top.set":
            operation = "置顶" if parameters.get("top", True) else "取消置顶"
            return f"{operation}课程 {parameters.get('course')} 的通知 {parameters.get('notice')}"
        if action == "notices.recall":
            return f"撤回课程 {parameters.get('course')} 的通知 {parameters.get('notice')}"
        if action == "notices.delete":
            return f"删除课程 {parameters.get('course')} 的通知 {parameters.get('notice')}"
        if action == "discussions.topic.create":
            scope = "当前班级" if parameters.get("class_only") else "课程全部班级"
            return (
                f"向课程 {parameters.get('course')} 的{scope}发布讨论"
                f"《{parameters.get('title')}》：{parameters.get('content')}"
            )
        if action == "discussions.topic.edit":
            return (
                f"编辑课程 {parameters.get('course')} 的讨论 {parameters.get('topic')}；"
                f"新标题={parameters.get('title')}，新正文={parameters.get('content')}"
            )
        if action == "discussions.topic.top.set":
            operation = "置顶" if parameters.get("top", True) else "取消置顶"
            return f"{operation}课程 {parameters.get('course')} 的讨论 {parameters.get('topic')}"
        if action == "discussions.topic.delete":
            return f"删除课程 {parameters.get('course')} 的讨论 {parameters.get('topic')}"
        if action == "discussions.reply.create":
            target = f"中的回复 {parameters.get('reply_to')}" if parameters.get("reply_to") else ""
            return (
                f"回复课程 {parameters.get('course')} 的讨论 {parameters.get('topic')}{target}："
                f"{parameters.get('content')}"
            )
        if action == "discussions.reply.edit":
            return (
                f"将课程 {parameters.get('course')} 的讨论 {parameters.get('topic')} 中回复 "
                f"{parameters.get('reply')} 修改为：{parameters.get('content')}"
            )
        if action == "discussions.reply.delete":
            return (
                f"删除课程 {parameters.get('course')} 的讨论 {parameters.get('topic')} 中回复 "
                f"{parameters.get('reply')}"
            )
        return f"execute {action} with parameters {parameters}"
