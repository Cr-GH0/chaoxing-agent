from pathlib import Path

import pytest

from chaoxing_agent.api import ChaoxingAPI, ChaoxingAPIError

COURSE = {"course_id": "900000002", "course_name": "文体写作示例", "cpi": "485781386"}
CLAZZ = {"clazz_id": "800000002", "clazz_name": "示例一班"}


def _group(group_id: str = "10", name: str = "课堂练习", **changes):
    item = {
        "group_id": group_id,
        "name": name,
        "course_id": COURSE["course_id"],
        "clazz_id": CLAZZ["clazz_id"],
        "creator_uid": "1",
        "type": 0,
        "sort": 1,
        "deleted": False,
        "is_default": False,
        "created_at": None,
        "updated_at": None,
    }
    item.update(changes)
    return item


def _activity(activity_id: str = "100", name: str = "第一节课签到", **changes):
    item = {
        "activity_id": activity_id,
        "name": name,
        "category_label": "签到",
        "activity_type": 2,
        "clazz_id": CLAZZ["clazz_id"],
        "group_id": "10",
        "group_name": "课堂练习",
        "creator_uid": "1",
        "other_id": "",
        "status": 0,
        "status_label": "not_started",
        "allow_start_end_from_list": True,
        "content": "",
        "content_json": None,
        "created_at": None,
        "start_time": None,
        "end_time": None,
        "sort": 1,
        "group_sort": 1,
        "logo": "",
    }
    item.update(changes)
    return item


def test_class_activity_normalizers_preserve_name_type_state_and_default_group() -> None:
    group = ChaoxingAPI._normalize_class_activity_group(
        {"id": 9, "name": " 默认分组 ", "courseId": 2, "classId": None, "sort": 0}
    )
    activity = ChaoxingAPI._normalize_class_activity(
        {
            "activeId": 100,
            "typeTitle": "第一节课签到",
            "title": "签到",
            "activeType": 2,
            "classId": 3,
            "planId": 9,
            "status": 1,
            "allowBeginEndFromList": 1,
            "content": '{"name":"第一节课签到"}',
        }
    )

    assert group["group_id"] == "9" and group["is_default"] is True
    assert activity["name"] == "第一节课签到" and activity["category_label"] == "签到"
    assert activity["activity_type"] == 2 and activity["status_label"] == "ongoing"
    assert activity["content_json"] == {"name": "第一节课签到"}


def test_class_activity_list_applies_group_search_status_and_type_filters(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"common": {}}
    groups = [_group(), _group("11", "通知")]
    activities = [
        _activity(),
        _activity(
            "101",
            "Unit 1 作业提醒",
            category_label="通知",
            activity_type=45,
            group_id="11",
            group_name="通知",
            status=2,
            status_label="ended",
        ),
    ]
    monkeypatch.setattr(api, "_class_activity_context", lambda *_args: context)
    monkeypatch.setattr(
        api,
        "_class_activity_listing",
        lambda _context: {
            "archived": False,
            "managed_group_ids": ["10", "11"],
            "groups": groups,
            "activities": activities,
        },
    )

    result = api.list_class_activities(
        COURSE,
        CLAZZ,
        group="通知",
        search="作业",
        status="已结束",
        activity_type=45,
    )

    assert result["count"] == 1
    assert result["activities"][0]["activity_id"] == "101"


def test_read_class_activity_preserves_list_fields_omitted_by_info_api(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"common": {"fid": "23080"}}
    selected = _activity(creator_uid="405017213", other_id="1221263127")
    monkeypatch.setattr(api, "_class_activity_context", lambda *_args: context)
    monkeypatch.setattr(
        api,
        "_class_activity_listing",
        lambda _context: {"groups": [_group()], "activities": [selected]},
    )
    monkeypatch.setattr(
        api,
        "_class_activity_json_request",
        lambda *_args, **_kwargs: {
            "result": 1,
            "data": {
                "activeId": "100",
                "typeTitle": "第一节课签到",
                "activeType": 2,
                "status": 0,
            },
        },
    )

    result = api.read_class_activity(COURSE, CLAZZ, "100")

    activity = result["activity"]
    assert activity["creator_uid"] == "405017213"
    assert activity["other_id"] == "1221263127"
    assert activity["allow_start_end_from_list"] is True
    assert activity["group_id"] == "10"


def test_create_class_activity_group_accepts_object_id_and_fresh_verifies(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"common": {}}
    default = _group("1", "默认分组", clazz_id=None, sort=0, is_default=True)
    created = _group("22", "课堂练习")
    states = iter(
        [
            {"groups": [default], "activities": []},
            {"groups": [default, created], "activities": []},
        ]
    )
    request: dict[str, object] = {}
    monkeypatch.setattr(api, "_class_activity_context", lambda *_args: context)
    monkeypatch.setattr(api, "_class_activity_listing", lambda _context: next(states))

    def request_json(_context, path, _operation, **kwargs):
        request.update({"path": path, **kwargs})
        return {"status": True, "data": {"id": 22}}

    monkeypatch.setattr(api, "_class_activity_json_request", request_json)

    result = api.create_class_activity_group(COURSE, CLAZZ, "课堂练习")

    assert request["path"] == "/v2/apis/active/group/add"
    assert request["data"]["classId"] == CLAZZ["clazz_id"]
    assert result["group"]["group_id"] == "22"


def test_group_safeguards_reject_default_nonempty_and_incomplete_order(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"common": {}}
    default = _group("1", "默认分组", clazz_id=None, sort=0, is_default=True)
    custom = _group()
    listing = {"groups": [default, custom], "activities": [_activity()]}
    monkeypatch.setattr(api, "_class_activity_context", lambda *_args: context)
    monkeypatch.setattr(api, "_class_activity_listing", lambda _context: listing)
    monkeypatch.setattr(
        api,
        "_class_activity_json_request",
        lambda *_args, **_kwargs: pytest.fail("unsafe request must not be sent"),
    )

    with pytest.raises(ChaoxingAPIError, match="default"):
        api.rename_class_activity_group(COURSE, CLAZZ, "1", "新名称")
    with pytest.raises(ChaoxingAPIError, match="not empty"):
        api.delete_class_activity_group(COURSE, CLAZZ, "10")
    with pytest.raises(ChaoxingAPIError, match="every custom"):
        api.reorder_class_activity_groups(COURSE, CLAZZ, [])


@pytest.mark.parametrize(
    ("started", "before", "after", "expected_path"),
    [
        (
            True,
            _activity(),
            _activity(status=1, status_label="ongoing"),
            "/v2/apis/active/startActive",
        ),
        (
            False,
            _activity(activity_type=46, status=1, status_label="ongoing"),
            _activity(activity_type=46, status=2, status_label="ended"),
            "/widget/CWareDataController/overFeedback",
        ),
    ],
)
def test_class_activity_start_and_feedback_end_use_type_specific_endpoints(
    monkeypatch, started, before, after, expected_path
) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"common": {}}
    states = iter(
        [
            {"groups": [_group()], "activities": [before]},
            {"groups": [_group()], "activities": [after]},
        ]
    )
    request: dict[str, object] = {}
    monkeypatch.setattr(api, "_class_activity_context", lambda *_args: context)
    monkeypatch.setattr(api, "_class_activity_listing", lambda _context: next(states))

    def request_json(_context, path, _operation, **kwargs):
        request.update({"path": path, **kwargs})
        return {"result": 1}

    monkeypatch.setattr(api, "_class_activity_json_request", request_json)

    result = api.set_class_activity_status(COURSE, CLAZZ, "100", started=started)

    assert request["path"] == expected_path
    assert result["activity"]["status"] == (1 if started else 2)


def test_class_activity_delete_polls_until_active_and_recycle_states_agree(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"common": {}}
    activity = _activity()
    active_states = iter(
        [
            {"groups": [_group()], "activities": [activity]},
            {"groups": [_group()], "activities": [activity]},
            {"groups": [_group()], "activities": []},
        ]
    )
    recycle_states = iter([[], [dict(activity, recycled=True)]])
    monkeypatch.setattr(api, "_class_activity_context", lambda *_args: context)
    monkeypatch.setattr(api, "_class_activity_listing", lambda _context: next(active_states))
    monkeypatch.setattr(api, "_class_activity_recycle_items", lambda _context: next(recycle_states))
    monkeypatch.setattr(
        api, "_class_activity_json_request", lambda *_args, **_kwargs: {"result": 1}
    )
    monkeypatch.setattr("chaoxing_agent.api.sleep", lambda _seconds: None)

    result = api.delete_class_activity(COURSE, CLAZZ, "100")

    assert result["activity"]["recycled"] is True


def test_class_activity_recycle_treats_no_data_as_empty(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"common": {"course_id": COURSE["course_id"], "clazz_id": CLAZZ["clazz_id"]}}
    monkeypatch.setattr(
        api,
        "_class_activity_json_request",
        lambda *_args, **_kwargs: {"result": 0, "errorMsg": "no data"},
    )

    assert api._class_activity_recycle_items(context) == []


def test_class_activity_permanent_delete_requires_unique_recycled_items(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"common": {}}
    item = dict(_activity(), recycled=True)
    monkeypatch.setattr(api, "_class_activity_context", lambda *_args: context)
    monkeypatch.setattr(api, "_class_activity_recycle_items", lambda _context: [item])
    monkeypatch.setattr(
        api,
        "_class_activity_json_request",
        lambda *_args, **_kwargs: pytest.fail("duplicate delete must not be sent"),
    )

    with pytest.raises(ChaoxingAPIError, match="duplicate"):
        api.permanently_delete_class_activities(COURSE, CLAZZ, ["100", "100"])
