from pathlib import Path

import pytest

from chaoxing_agent.api import ChaoxingAPI, ChaoxingAPIError

COURSE = {"course_id": "900000002", "course_name": "文体写作示例", "cpi": "485781386"}
CLAZZ = {"clazz_id": "800000002", "clazz_name": "示例一班"}


def _group(group_id: str = "7", name: str = "备课") -> dict[str, object]:
    return {
        "index": 1,
        "group_id": group_id,
        "name": name,
        "course_id": COURSE["course_id"],
        "is_system": group_id == "0",
        "can_rename": group_id != "0",
        "can_delete": group_id != "0",
    }


def _command(**changes) -> dict[str, object]:
    command = {
        "index": 1,
        "command_id": "99",
        "group_id": "7",
        "group_name": "备课",
        "name": "生成提纲",
        "content": "主题为：{请输入主题}",
        "explanation": "生成结构清楚的提纲",
        "prompt_words": "保持准确",
        "classify_id": 1,
        "mapping_id": 202,
        "publish_status": 0,
        "published": False,
        "role_type": 0,
        "role": "teacher",
        "command_ability": 0,
        "ability_type": 0,
        "kind": "mapped",
        "can_edit": True,
        "can_move": True,
        "can_delete": True,
        "can_publish": False,
        "can_reorder": True,
    }
    command.update(changes)
    return command


def test_ai_command_parser_deduplicates_role_views_and_preserves_capabilities() -> None:
    html = """
    <ul id="zlSortAll_7">
      <li class="commandInfo" id="commandLiCls_99"
          commandname="生成&amp;检查" commanddesc="内容"
          commandexplain="说明" promptwords="提示"
          classifyid="2" mapping="0" publishStatus="1" curRoleType="2"
          commandability="1" abilitytype="1">
        <i class="toolDrag"></i>
        <span onclick="editCustomCommandPop(this, 99, '7')"></span>
        <span onclick="publishAiWork(99, this, event, 'command', '7', 0)"></span>
        <li onclick="showMoveCommandToGroupPop(99)">移动</li>
        <li onclick="showDeleteCommandPop(99, '7')">删除</li>
      </li>
      <li class="commandInfo" id="commandLiCls_1" commandname="系统指令"
          commanddesc="系统内容" commandexplain="系统说明" promptwords=""
          classifyid="1" mapping="0" publishStatus="0" curRoleType="0"
          commandability="$tea.commandAbility" abilitytype="$tea.abilityType"></li>
    </ul>
    <ul id="zlSortTea_7">
      <li class="commandInfo" id="commandLiCls_99" commandname="生成&amp;检查"
          commanddesc="内容" commandexplain="说明" promptwords="提示"
          classifyid="2" mapping="0" publishStatus="1" curRoleType="2"
          commandability="1" abilitytype="1"><i class="toolDrag"></i></li>
      <li class="commandInfo" id="commandLiCls_1" commandname="系统指令"
          commanddesc="系统内容" commandexplain="系统说明" promptwords=""
          classifyid="1" mapping="0" publishStatus="0" curRoleType="0"></li>
    </ul>
    <ul id="zlSortStu_7">
      <li class="commandInfo" id="commandLiCls_99" commandname="生成&amp;检查"></li>
    </ul>
    """

    commands = ChaoxingAPI._parse_ai_workbench_commands(html, _group())

    assert [item["command_id"] for item in commands] == ["99", "1"]
    assert commands[0]["name"] == "生成&检查"
    assert commands[0]["kind"] == "custom" and commands[0]["published"] is True
    assert commands[0]["can_edit"] and commands[0]["can_move"] and commands[0]["can_delete"]
    assert commands[0]["can_publish"] and commands[0]["can_reorder"]
    assert commands[1]["kind"] == "system" and commands[1]["command_ability"] == 0
    assert ChaoxingAPI._parse_ai_workbench_role_order(html, "7", 0) == ["99", "1"]
    assert ChaoxingAPI._parse_ai_workbench_role_order(html, "7", 1) == ["99"]


def test_ai_group_create_verifies_new_id(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"common": {"clazzId": "1", "courseId": "2", "cpi": "3", "ut": "t"}}
    before = [_group("0", "系统指令")]
    after = [*before, _group("7", "备课")]
    calls = 0
    request: dict[str, object] = {}

    monkeypatch.setattr(api, "_ai_workbench_context", lambda *_args: context)

    def groups(_context):
        nonlocal calls
        calls += 1
        return before if calls == 1 else after

    def request_json(_context, path, _operation, **kwargs):
        request.update({"path": path, **kwargs})
        return {"status": True, "data": {"id": 7}}

    monkeypatch.setattr(api, "_ai_workbench_groups_from_context", groups)
    monkeypatch.setattr(api, "_ai_workbench_json_request", request_json)

    result = api.create_ai_workbench_group(COURSE, CLAZZ, "备课")

    assert result["group"]["group_id"] == "7"
    assert request["path"] == "/course-ans/ai/add-command-group"
    assert request["params"]["groupName"] == "备课"


def test_mapped_ai_command_update_only_changes_role(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"common": {"clazzId": "1", "courseId": "2", "cpi": "3", "ut": "t"}}
    before = _command()
    after = _command(role_type=2, role="teacher_and_student")
    calls = 0
    request: dict[str, object] = {}

    monkeypatch.setattr(api, "_ai_workbench_context", lambda *_args: context)

    def all_commands(_context, **_kwargs):
        nonlocal calls
        calls += 1
        return ([before], []) if calls == 1 else ([after], [])

    def request_json(_context, path, _operation, **kwargs):
        request.update({"path": path, **kwargs})
        return {"status": True}

    monkeypatch.setattr(api, "_ai_workbench_all_commands", all_commands)
    monkeypatch.setattr(api, "_ai_workbench_json_request", request_json)

    result = api.update_ai_workbench_command(COURSE, CLAZZ, "99", role_type=2)

    assert result["command"]["role_type"] == 2
    assert request["path"] == "/course-ans/ai/updateMappingCommandSwitch"
    assert request["params"]["commandId"] == "99"
    with pytest.raises(ChaoxingAPIError, match="only supports role_type"):
        api.update_ai_workbench_command(COURSE, CLAZZ, "99", name="新名称")


def test_ai_group_delete_rejects_nonempty_group_before_request(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"common": {"clazzId": "1", "courseId": "2", "cpi": "3", "ut": "t"}}
    monkeypatch.setattr(api, "_ai_workbench_context", lambda *_args: context)
    monkeypatch.setattr(api, "_ai_workbench_groups_from_context", lambda *_args: [_group()])
    monkeypatch.setattr(
        api,
        "_ai_workbench_commands_for_group",
        lambda *_args, **_kwargs: {"commands": [_command()]},
    )
    monkeypatch.setattr(
        api,
        "_ai_workbench_json_request",
        lambda *_args, **_kwargs: pytest.fail("delete request must not be sent"),
    )

    with pytest.raises(ChaoxingAPIError, match="not empty"):
        api.delete_ai_workbench_group(COURSE, CLAZZ, "7")


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("name", "x" * 129, "name must not exceed 128"),
        ("content", "", "content is required"),
        ("role_type", 4, "role_type must be"),
    ],
)
def test_ai_command_validation_enforces_live_frontend_limits(field, value, message) -> None:
    values = {
        "name": "指令",
        "content": "内容",
        "explanation": "说明",
        "prompt_words": "提示",
        "role_type": 0,
        "classify_id": 1,
        "command_ability": 0,
        "ability_type": 0,
    }
    values[field] = value
    with pytest.raises(ChaoxingAPIError, match=message):
        ChaoxingAPI._ai_workbench_validate_command_fields(**values)


def test_ai_recommendation_normalization_uses_open_id_for_mapping() -> None:
    item = ChaoxingAPI._normalize_ai_workbench_recommendation(
        {
            "id": 202,
            "openId": 12703,
            "name": "教学设计",
            "commandDesc": "课程名称是……",
            "commandExplain": "设计教学方案",
            "publishStatus": 1,
            "roleType": 0,
        },
        1,
    )
    assert item["recommendation_id"] == "202"
    assert item["open_id"] == "12703"
    assert item["role"] == "teacher"
