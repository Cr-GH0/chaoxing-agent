from pathlib import Path

import pytest

from chaoxing_agent.api import ChaoxingAPI, ChaoxingAPIError

COURSE = {"course_id": "900000002", "course_name": "文体写作示例", "cpi": "485781386"}
CLAZZ = {"clazz_id": "800000002", "clazz_name": "示例一班"}


def _task(task_id: str = "task-1", name: str = "过程分析", **changes):
    item = {
        "task_id": task_id,
        "name": name,
        "folder_id": None,
        "publish_status": False,
        "recycled": False,
    }
    item.update(changes)
    return item


def test_task_engine_normalizers_preserve_ids_status_labels_and_folder() -> None:
    folder = ChaoxingAPI._normalize_task_engine_folder(
        {"id": 14600, "name": " 单元一 ", "count": "2", "sort": "3"}
    )
    task = ChaoxingAPI._normalize_task_engine_task(
        {
            "taskId": "encrypted-task",
            "name": "过程分析",
            "courseId": 900000002,
            "labelList": [{"id": 11646, "name": "复习"}],
            "publishStatus": 1,
            "taskPointsNumber": "4",
            "taskStudentsNumber": "31",
            "isCreator": 1,
        },
        folder_id="14600",
        recycled=False,
    )

    assert folder == {"folder_id": "14600", "name": "单元一", "task_count": 2, "sort": 3}
    assert task["task_id"] == "encrypted-task" and task["folder_id"] == "14600"
    assert task["labels"] == [{"label_id": "11646", "name": "复习"}]
    assert task["publish_status"] is True and task["task_point_count"] == 4


def test_read_task_engine_task_returns_complete_group_and_point_structure(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"common": {"course_id": COURSE["course_id"]}}
    monkeypatch.setattr(api, "_task_engine_context", lambda *_args: context)
    monkeypatch.setattr(api, "_task_engine_all_tasks", lambda *_args, **_kwargs: [_task()])
    monkeypatch.setattr(
        api,
        "_task_engine_task_data",
        lambda *_args: {
            "taskId": "task-1",
            "courseId": COURSE["course_id"],
            "name": "过程分析",
            "introduce": "阅读材料",
            "target": "完成分析",
            "selectedModes": ["list", "frame"],
            "taskPointsNumber": 1,
            "taskLabelList": [{"id": 11646, "name": "复习", "allowDelete": False}],
            "groups": [
                {
                    "id": 10,
                    "encryGroupDataId": "group-encrypted",
                    "name": "第一组",
                    "detail": [
                        {
                            "id": 20,
                            "encryPlanDataId": "point-encrypted",
                            "type": 6,
                            "planTypeTitle": "资料",
                            "name": "阅读 PDF",
                            "haveTaskPermission": True,
                        }
                    ],
                }
            ],
        },
    )

    result = api.read_task_engine_task(COURSE, CLAZZ, "过程分析")

    assert result["task"]["selected_modes"] == ["list", "frame"]
    assert result["task"]["labels"][0]["label_id"] == "11646"
    assert result["task"]["groups"][0]["points"][0]["point_id"] == "20"
    assert result["task"]["groups"][0]["points"][0]["have_permission"] is True


def test_create_task_engine_task_commits_frontend_fields_and_fresh_verifies(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {
        "common": {
            "course_id": COURSE["course_id"],
            "encrypted_course_id": "course-encrypted",
            "encrypted_type": "type-encrypted",
            "business_code": "business",
        }
    }
    committed: dict[str, object] = {}
    monkeypatch.setattr(api, "_task_engine_context", lambda *_args: context)
    monkeypatch.setattr(
        api,
        "_task_engine_json_request",
        lambda *_args, **_kwargs: {"code": 200, "data": {"encryTaskId": "task-new"}},
    )
    monkeypatch.setattr(
        api,
        "_task_engine_task_data",
        lambda *_args: {"taskId": "task-new", "courseId": COURSE["course_id"], "cover": ""},
    )

    def commit(_context, data, operation):
        committed.update({"data": dict(data), "operation": operation})
        return "task-new"

    monkeypatch.setattr(api, "_commit_task_engine_task", commit)
    monkeypatch.setattr(
        api,
        "_task_engine_all_tasks",
        lambda *_args, **_kwargs: [_task("task-new", "过程分析")],
    )

    result = api.create_task_engine_task(
        COURSE,
        CLAZZ,
        "过程分析",
        introduce="阅读材料",
        target="完成比较",
        selected_modes=["list", "frame"],
    )

    data = committed["data"]
    assert data["introduceRichText"] == "<div>阅读材料</div>"
    assert data["target"] == "完成比较"
    assert data["selectedModes"] == ["list", "frame"]
    assert result["task"]["task_id"] == "task-new"


def test_delete_task_engine_task_polls_until_recycle_is_consistent(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"common": {"course_id": COURSE["course_id"]}}
    selected = _task()
    active_states = iter([[selected], [selected], []])
    recycle_states = iter([[], [dict(selected, recycled=True)]])
    requests: list[str] = []

    monkeypatch.setattr(api, "_task_engine_context", lambda *_args: context)
    monkeypatch.setattr(
        api, "_task_engine_all_tasks", lambda *_args, **_kwargs: next(active_states)
    )

    def recycle(_context, **kwargs):
        assert kwargs["recycled"] is True
        return next(recycle_states)

    monkeypatch.setattr(api, "_task_engine_tasks_from_context", recycle)

    def request(_context, path, _operation, **_kwargs):
        requests.append(path)
        return {"code": 200, "data": True}

    monkeypatch.setattr(api, "_task_engine_json_request", request)
    monkeypatch.setattr("chaoxing_agent.api.sleep", lambda _seconds: None)

    result = api.delete_task_engine_task(COURSE, CLAZZ, "task-1")

    assert requests == ["/task/removeTaskPermissionValidate", "/task/deleteTaskInfo"]
    assert result["task"]["recycled"] is True


def test_reorder_task_engine_items_requires_complete_current_order(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"common": {"course_id": COURSE["course_id"]}}
    monkeypatch.setattr(api, "_task_engine_context", lambda *_args: context)
    monkeypatch.setattr(api, "_task_engine_folders_from_context", lambda *_args: [])
    monkeypatch.setattr(
        api,
        "_task_engine_tasks_from_context",
        lambda *_args, **_kwargs: [_task("task-1", "任务一"), _task("task-2", "任务二")],
    )
    monkeypatch.setattr(
        api,
        "_task_engine_json_request",
        lambda *_args, **_kwargs: pytest.fail("incomplete order must not be sent"),
    )

    with pytest.raises(ChaoxingAPIError, match="every task"):
        api.reorder_task_engine_items(COURSE, CLAZZ, task_order=["task-1"], folder_order=[])


def test_task_engine_label_rename_never_false_reports_server_noop(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"common": {"course_id": COURSE["course_id"]}}
    task = _task()
    label = {
        "label_id": "11646",
        "name": "复习",
        "operator_user_id": "1",
        "allow_delete": False,
        "selected": False,
        "created_at": "",
        "updated_at": "",
    }
    monkeypatch.setattr(api, "_task_engine_context", lambda *_args: context)
    monkeypatch.setattr(api, "_task_engine_all_tasks", lambda *_args, **_kwargs: [task])
    monkeypatch.setattr(api, "_task_engine_labels_from_context", lambda *_args, **_kwargs: [label])
    monkeypatch.setattr(
        api,
        "_task_engine_json_request",
        lambda *_args, **_kwargs: {"code": 200, "message": "success"},
    )

    with pytest.raises(ChaoxingAPIError, match="refreshed label did not match"):
        api.rename_task_engine_label(COURSE, CLAZZ, "11646", "期末复习")


def test_task_engine_publish_rejects_empty_task_before_publish_request(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"common": {"course_id": COURSE["course_id"]}}
    monkeypatch.setattr(api, "_task_engine_context", lambda *_args: context)
    monkeypatch.setattr(api, "_task_engine_all_tasks", lambda *_args, **_kwargs: [_task()])
    monkeypatch.setattr(
        api,
        "_task_engine_task_data",
        lambda *_args: {
            "taskId": "task-1",
            "courseId": COURSE["course_id"],
            "taskPointsNumber": 0,
        },
    )
    monkeypatch.setattr(
        api,
        "_task_engine_json_request",
        lambda *_args, **_kwargs: pytest.fail("empty task must not be published"),
    )

    with pytest.raises(ChaoxingAPIError, match="at least one task point"):
        api.set_task_engine_publish_status(COURSE, CLAZZ, "task-1", publish=True)
