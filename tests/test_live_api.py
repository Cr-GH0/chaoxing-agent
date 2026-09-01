import json
from pathlib import Path

import pytest

from chaoxing_agent.api import ChaoxingAPI, ChaoxingAPIError


def _room() -> dict[str, object]:
    return {
        "index": 1,
        "room_id": "4000000000000001",
        "stream_room_id": "29000001",
        "active_id": "32000001",
        "video_id": "23000001",
        "title": "测试直播",
        "introduction": "<p>介绍</p>",
        "status": 0,
        "status_label": "未开始",
        "mode": "multi_device",
        "is_cloud": False,
        "scheduled_time": "2026-09-03 11:00",
        "created_at": "2026-09-01 09:00:00",
        "started_at": "",
        "ended_at": "",
        "deleted_at": "",
        "duration_seconds": 0,
        "cover_object_id": "",
        "can_start_with_chaoxing_client": False,
        "watch_url": "https://zhibo.chaoxing.com/4000000000000001",
        "preview_video_object_id": "",
    }


@pytest.mark.parametrize(("if_review", "expected"), [(0, True), (1, False)])
def test_live_room_detail_maps_server_replay_disable_flag(if_review, expected, monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    room = _room()

    def fake_live_json(_session, _referer, path, _operation, **_kwargs):
        if path.endswith("getLiveConfig"):
            return {
                "data": {
                    "liveId": 29000001,
                    "comment": 1,
                    "ifReview": if_review,
                    "onlyInXxt": 0,
                    "contentReview": 1,
                    "loginWatchValue": 0,
                    "pictureLive": 0,
                    "videoPlayStartTime": 5,
                    "configObj": {
                        "forward": 1,
                        "showUserCountInLivingRoom": 1,
                        "ifSubscribe": 0,
                        "preUpload": 0,
                        "allowAccessFids": "23080,43870",
                    },
                }
            }
        return {"title": "测试直播", "introduce": "<p>介绍</p>", "ygdate": "2026-09-03 11:00"}

    monkeypatch.setattr(api, "_live_json", fake_live_json)
    detail = api._live_room_detail(object(), "https://live.chaoxing.com/", room, {})

    assert detail["settings"]["replay_enabled"] is expected
    assert detail["settings"]["allowed_unit_ids"] == ["23080", "43870"]
    assert detail["settings"]["replay_start_offset_seconds"] == 5


def test_live_settings_send_ui_semantics_and_verify_all_fields(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    room = _room()
    base_settings = {
        "comments_enabled": True,
        "forwarding_enabled": False,
        "replay_enabled": False,
        "learning_app_only": False,
        "chat_content_review": True,
        "login_required": False,
        "picture_live": False,
        "access_password": "",
        "show_viewer_count": True,
        "reservations_enabled": False,
        "preupload_enabled": False,
        "allowed_unit_ids": [],
        "replay_start_offset_seconds": 0,
    }
    expected = {
        **base_settings,
        "comments_enabled": False,
        "forwarding_enabled": True,
        "replay_enabled": True,
        "access_password": "1234",
        "allowed_unit_ids": ["23080", "43870"],
        "replay_start_offset_seconds": 5,
    }
    request: dict[str, object] = {}

    monkeypatch.setattr(
        api,
        "_live_context",
        lambda: (
            object(),
            "https://live.chaoxing.com/",
            {"fid": "23080", "puid": "1", "token": "s"},
        ),
    )
    monkeypatch.setattr(api, "_find_live_room", lambda *_args: (room, {}))

    def fake_detail(*_args):
        return {
            "room": room,
            "settings": expected if request else base_settings,
            "_detail": {},
        }

    def fake_json(_session, _referer, path, _operation, **kwargs):
        assert path == "/courseLive/setLive"
        request.update(kwargs["params"])
        return {"result": 1}

    monkeypatch.setattr(api, "_live_room_detail", fake_detail)
    monkeypatch.setattr(api, "_live_json", fake_json)

    result = api.update_live_room_settings(
        "测试直播",
        comments_enabled=False,
        forwarding_enabled=True,
        replay_enabled=True,
        access_password="1234",
        allowed_unit_ids=["23080", "43870"],
        replay_start_offset_seconds=5,
    )

    assert request["reminisce"] == "true"
    assert request["h"] == 0 and request["m"] == 0 and request["s"] == 5
    assert request["allowAccessFids"] == "23080,43870"
    assert result["settings"] == expected


def test_live_recycle_treats_server_null_array_as_empty(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(api, "_live_json", lambda *_args, **_kwargs: [None])
    assert api._live_recycle_records(object(), "https://live.chaoxing.com/") == []


def test_live_verified_mutation_accepts_legacy_false_only_without_error() -> None:
    ChaoxingAPI._live_verified_mutation_ack({"result": False}, "restore")
    with pytest.raises(ChaoxingAPIError, match="denied"):
        ChaoxingAPI._live_verified_mutation_ack({"result": False, "message": "denied"}, "restore")


def test_live_theme_settings_preserve_opaque_existing_config(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    raw = {
        "themedLiveId": "opaque-theme-token",
        "name": "系列直播",
        "description": "说明",
        "status": 0,
        "configJson": json.dumps(
            {
                "isForwardingIsAllowed": False,
                "isRetrospectivesAreAllowed": True,
                "isOnlyXxtAllowed": False,
                "isOnlyLoginAllowed": True,
                "limitViewingFid": "",
                "invitationCode": "preserve-this",
                "futureServerField": {"value": 1},
            }
        ),
    }
    selected = api._normalize_live_theme(raw, 1)
    submitted: dict[str, object] = {}

    monkeypatch.setattr(
        api,
        "_live_context",
        lambda: (
            object(),
            "https://live.chaoxing.com/",
            {"fid": "23080", "puid": "1", "token": "s"},
        ),
    )
    monkeypatch.setattr(api, "_find_live_theme", lambda *_args: (selected, raw))

    def fake_json(_session, _referer, path, _operation, **kwargs):
        assert path == "/themedLive/setThemedLiveConfig"
        submitted.update(json.loads(kwargs["data"]["configJson"]))
        return {"status": 1}

    def refreshed(*_args, **_kwargs):
        updated_raw = {**raw, "configJson": json.dumps(submitted)}
        return [(api._normalize_live_theme(updated_raw, 1), updated_raw)], 1

    monkeypatch.setattr(api, "_live_json", fake_json)
    monkeypatch.setattr(api, "_live_theme_records", refreshed)

    result = api.update_live_theme_settings("系列直播", forwarding_enabled=True)

    assert submitted["invitationCode"] == "preserve-this"
    assert submitted["futureServerField"] == {"value": 1}
    assert result["theme"]["settings"]["forwarding_enabled"] is True


def test_live_helpers_reject_invalid_schedule_and_asset_kind() -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    with pytest.raises(ChaoxingAPIError, match="YYYY-MM-DD HH:MM"):
        api._live_schedule("2026/09/03 11:00")
    with pytest.raises(ChaoxingAPIError, match="cover or preview_video"):
        api.upload_live_asset("missing.bin", kind="archive")
