from pathlib import Path

import pytest

from chaoxing_agent.api import (
    ChaoxingAPI,
    ChaoxingAPIError,
    parse_knowledge_graph_relation_html,
)

COURSE = {"course_id": "900000001", "course_name": "语言与测试", "cpi": "485781386"}
CLAZZ = {"clazz_id": "800000001", "clazz_name": "默认班级"}


def _graph(*nodes: tuple[str, str, int, str]) -> dict:
    raw_nodes = [
        {
            "id": f"courseid-{COURSE['course_id']}",
            "topicid": 0,
            "name": COURSE["course_name"],
            "level": 0,
        }
    ]
    links = []
    for node_id, name, level, parent_id in nodes:
        raw_nodes.append(
            {
                "id": node_id,
                "topicid": int(node_id),
                "name": name,
                "level": level,
                "tag": "重点,难点" if level == 1 else "",
            }
        )
        links.append(
            {
                "source": parent_id,
                "target": node_id,
                "type": 1,
                "relation": "父子关系",
            }
        )
    return {"status": True, "nodes": raw_nodes, "links": links}


def _label_groups(*, include_custom: bool = True) -> list[dict]:
    groups = [
        {
            "index": 1,
            "group_id": "1",
            "name": "默认标签组",
            "is_default": True,
            "group_type": 0,
            "label_count": 1,
            "labels": [
                {
                    "index": 1,
                    "label_id": "10",
                    "group_id": "1",
                    "name": "重点",
                    "precast": True,
                }
            ],
        }
    ]
    if include_custom:
        groups.append(
            {
                "index": 2,
                "group_id": "2",
                "name": "自定义",
                "is_default": False,
                "group_type": 0,
                "label_count": 1,
                "labels": [
                    {
                        "index": 1,
                        "label_id": "20",
                        "group_id": "2",
                        "name": "复习",
                        "precast": False,
                    }
                ],
            }
        )
    return groups


def _model_data(*, include_custom: bool = False, custom_name: str = "临时图谱") -> dict:
    models = [
        {
            "id": 1,
            "name": "知识图谱",
            "modeType": 1,
            "style": 0,
            "type": 1,
            "hide": 0,
            "flagDefault": True,
        },
        {
            "id": 2,
            "name": "学习地图",
            "modeType": 2,
            "style": 1,
            "type": 2,
            "hide": 1,
            "flagDefault": True,
        },
    ]
    if include_custom:
        models.append(
            {
                "id": 3,
                "name": custom_name,
                "modeType": 0,
                "style": 0,
                "type": 0,
                "hide": 0,
                "flagDefault": False,
            }
        )
    return {"topicModelData": models, "switchStatusData": {"problemMapStatus": False}}


def test_knowledge_graph_normalizer_builds_paths_tags_and_relations() -> None:
    payload = _graph(
        ("100", "第一单元", 1, f"courseid-{COURSE['course_id']}"),
        ("101", "概念", 2, "100"),
    )

    result = ChaoxingAPI._normalize_knowledge_graph(payload)

    child = next(item for item in result["nodes"] if item["node_id"] == "101")
    parent = next(item for item in result["nodes"] if item["node_id"] == "100")
    assert child["parent_id"] == "100"
    assert child["path"] == "语言与测试 / 第一单元 / 概念"
    assert parent["children_ids"] == ["101"] and parent["tags"] == ["重点", "难点"]
    assert result["relations"][0]["type"] == 1


def test_node_relation_html_parser_handles_builtins_custom_and_unquoted_ids() -> None:
    parsed = parse_knowledge_graph_relation_html(
        """
        <ul class="relationType_1" data-relationId="1">
          <li data=101><span class="zpSpan">前置节点</span></li>
        </ul>
        <ul class="relationType_2"></ul>
        <ul class="relationType_0" data-relationid="0">
          <li data="102" olddesc="旧说明" relationdesc="当前说明">
            <span class="icon"></span><span class="zpSpan">关联节点</span>
          </li>
        </ul>
        <ul data-relationId="88">
          <li data='103'><span class='zpSpan'>自定义节点</span></li>
        </ul>
        """
    )

    assert parsed["1"] == [{"topic_id": "101", "name": "前置节点", "description": ""}]
    assert parsed["2"] == []
    assert parsed["0"][0]["description"] == "当前说明"
    assert parsed["88"][0]["topic_id"] == "103"


def test_list_knowledge_graph_combines_config_and_filtered_data(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"common": {}}
    monkeypatch.setattr(api, "_knowledge_graph_context", lambda *_args: context)
    monkeypatch.setattr(
        api,
        "_knowledge_graph_config_data",
        lambda _context: {
            "allowEditGraph": True,
            "topicClassifyArray": [{"id": 1, "name": "事实性"}],
            "dataJson": {"relationTypeDesc": [{"relationDescId": 1}]},
        },
    )
    monkeypatch.setattr(
        api,
        "_knowledge_graph_raw_data",
        lambda _context: _graph(
            ("100", "第一单元", 1, f"courseid-{COURSE['course_id']}"),
            ("101", "概念", 2, "100"),
        ),
    )

    result = api.list_knowledge_graph(COURSE, CLAZZ, search="概念", level=2)

    assert result["allow_edit"] is True and result["total_count"] == 3
    assert [item["node_id"] for item in result["nodes"]] == ["101"]
    assert result["relation_types"] == [{"relationDescId": 1}]


def test_relation_normalizer_preserves_custom_style_and_default_state() -> None:
    relations = ChaoxingAPI._normalize_knowledge_graph_relation_types(
        {
            "dataJson": {
                "relationTypeDesc": [
                    {
                        "relationDescId": 0,
                        "relationDescName": "关联关系",
                        "relationDescType": 0,
                        "isDefault": True,
                    },
                    {
                        "relationDescId": 88,
                        "relationDescName": "支持关系",
                        "relationDescMean": "A 支持 B",
                        "relationDescType": 0,
                        "relationDescExample": "<p>例子</p>",
                        "isDefault": False,
                        "color": "#336699",
                        "arrowSize": 7,
                        "lineThickness": 2,
                        "defaultType": -1,
                    },
                ]
            }
        }
    )

    assert relations[0]["is_default"] is True
    assert relations[1]["relation_id"] == "88" and relations[1]["meaning"] == "A 支持 B"
    assert relations[1]["arrow_size"] == 7 and relations[1]["line_thickness"] == 2


def test_graph_model_normalizer_and_resolver_preserve_modes_visibility_and_order() -> None:
    models = ChaoxingAPI._normalize_knowledge_graph_models(_model_data(include_custom=True))

    assert [item["model_id"] for item in models] == ["1", "2", "3"]
    assert models[0]["mode_name"] == "知识图谱" and models[0]["visible"] is True
    assert models[1]["mode_name"] == "学习地图" and models[1]["hidden"] is True
    assert ChaoxingAPI._resolve_knowledge_graph_model(models, "自定义图谱")["model_id"] == "3"


def test_graph_model_create_update_visibility_reorder_and_delete_contracts(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"common": {"courseid": COURSE["course_id"], "cpi": COURSE["cpi"]}}
    base = _model_data()
    created = _model_data(include_custom=True)
    renamed = _model_data(include_custom=True, custom_name="已改名")
    hidden = _model_data(include_custom=True, custom_name="已改名")
    hidden["topicModelData"][2]["hide"] = 1
    reordered = {
        **hidden,
        "topicModelData": [
            hidden["topicModelData"][2],
            hidden["topicModelData"][0],
            hidden["topicModelData"][1],
        ],
    }
    states = iter(
        [
            base,
            created,
            created,
            renamed,
            renamed,
            hidden,
            hidden,
            reordered,
            reordered,
            base,
        ]
    )
    requests: list[dict] = []
    monkeypatch.setattr(api, "_knowledge_graph_context", lambda *_args: context)
    monkeypatch.setattr(api, "_knowledge_graph_topic_setting_data", lambda _context: next(states))

    def request(_context, path, _operation, **kwargs):
        requests.append({"path": path, **kwargs})
        if path.endswith("addtopicmodel"):
            return {"status": True, "coruseTopicModelId": 3}
        return {"status": True}

    monkeypatch.setattr(api, "_knowledge_graph_json_request", request)

    new_model = api.create_knowledge_graph_model(COURSE, CLAZZ, "临时图谱")
    changed = api.update_knowledge_graph_model(COURSE, CLAZZ, "3", "已改名")
    visibility = api.set_knowledge_graph_model_visibility(COURSE, CLAZZ, "3", visible=False)
    ordered = api.reorder_knowledge_graph_models(COURSE, CLAZZ, ["3", "1", "2"])
    deleted = api.delete_knowledge_graph_model(COURSE, CLAZZ, "3")

    assert new_model["model"]["model_id"] == "3"
    assert changed["model"]["name"] == "已改名"
    assert requests[1]["params"]["style"] == -1
    assert requests[2]["params"]["hide"] == 1
    assert visibility["model"]["visible"] is False
    assert requests[3]["params"]["topicModelIds"] == "3,1,2"
    assert [item["model_id"] for item in ordered["models"]] == ["3", "1", "2"]
    assert deleted["deleted_model"]["model_id"] == "3"


def test_graph_model_class_visibility_and_model_data_contracts(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"common": {"courseid": COURSE["course_id"], "cpi": COURSE["cpi"]}}
    classes_before = [
        {"index": 1, "clazz_id": "11", "clazz_name": "一班", "hidden": False, "visible": True},
        {"index": 2, "clazz_id": "12", "clazz_name": "二班", "hidden": False, "visible": True},
    ]
    classes_after = [
        classes_before[0],
        {**classes_before[1], "hidden": True, "visible": False},
    ]
    class_states = iter([classes_before, classes_after])
    requests: list[dict] = []
    monkeypatch.setattr(api, "_knowledge_graph_context", lambda *_args: context)
    monkeypatch.setattr(api, "_knowledge_graph_topic_setting_data", lambda _context: _model_data())
    monkeypatch.setattr(api, "_knowledge_graph_model_classes", lambda *_args: next(class_states))
    monkeypatch.setattr(
        api,
        "_knowledge_graph_config_data",
        lambda _context: {"dataJson": {"exportCourseTopicEnc": "enc"}},
    )

    def request(_context, path, _operation, **kwargs):
        requests.append({"path": path, **kwargs})
        if path.endswith("mapmodeldata"):
            return {
                "status": True,
                "data": {
                    "name": "课程",
                    "children": [{"topicId": 100, "name": "第一单元"}],
                },
            }
        return {"status": True}

    monkeypatch.setattr(api, "_knowledge_graph_json_request", request)

    visibility = api.update_knowledge_graph_model_classes(COURSE, CLAZZ, "1", ["11"])
    model_data = api.read_knowledge_graph_model_data(COURSE, CLAZZ, "1")

    assert requests[0]["method"] == "POST"
    assert requests[0]["data"]["clazzIds"] == "12"
    assert [item["clazz_id"] for item in visibility["classes"] if item["visible"]] == ["11"]
    assert model_data["data"]["count"] == 2
    assert model_data["data"]["nodes"][1]["path"] == "课程 / 第一单元"


def test_custom_relation_create_update_delete_use_observed_forms(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"common": {}}
    default = {
        "index": 1,
        "relation_id": "0",
        "name": "关联关系",
        "meaning": "",
        "example_html": "",
        "relation_type": 0,
        "filter_type": 0,
        "default_type": 0,
        "is_default": True,
        "color": "",
        "arrow_size": 6,
        "line_thickness": 1,
    }
    custom = {
        **default,
        "index": 2,
        "relation_id": "88",
        "name": "支持关系",
        "meaning": "A 支持 B",
        "example_html": "<p>例子</p>",
        "default_type": -1,
        "is_default": False,
        "color": "#336699",
    }
    updated = {
        **custom,
        "name": "促进关系",
        "meaning": "促进",
        "example_html": "<p>更新</p>",
        "color": "#663399",
        "arrow_size": 7,
        "line_thickness": 2,
    }
    config_states = iter(
        [
            [default],
            [default, custom],
            [default, custom],
            [default, updated],
            [default, updated],
            [default],
        ]
    )
    requests: list[dict] = []
    monkeypatch.setattr(api, "_knowledge_graph_context", lambda *_args: context)
    monkeypatch.setattr(api, "_knowledge_graph_config_data", lambda _context: {})
    monkeypatch.setattr(
        api,
        "_normalize_knowledge_graph_relation_types",
        lambda _config: next(config_states),
    )

    def request(_context, path, _operation, **kwargs):
        requests.append({"path": path, **kwargs})
        if path.endswith("createselfdefinetopicrelation"):
            return {"status": True, "saveTopicRelationDescId": 88}
        return {"status": True}

    monkeypatch.setattr(api, "_knowledge_graph_json_request", request)

    created = api.create_knowledge_graph_relation_type(
        COURSE,
        CLAZZ,
        "支持关系",
        meaning="A 支持 B",
        relation_types=[0],
        example_html="<p>例子</p>",
        color="#336699",
    )
    changed = api.update_knowledge_graph_relation_type(
        COURSE,
        CLAZZ,
        "88",
        name="促进关系",
        meaning="促进",
        example_html="<p>更新</p>",
        color="#663399",
        arrow_size=7,
        line_thickness=2,
    )
    deleted = api.delete_knowledge_graph_relation_type(COURSE, CLAZZ, "88")

    assert created["relation"]["relation_id"] == "88"
    assert requests[0]["data"]["relationType[0]"] == 0
    assert requests[1]["data"]["relationId"] == "88"
    assert requests[1]["data"]["arrowSize"] == 7
    assert requests[2]["data"]["relationTypeId"] == "88"
    assert changed["relation"]["name"] == "促进关系"
    assert deleted["deleted_relation"]["relation_id"] == "88"


def test_graph_settings_normalizer_reads_observed_configuration_fields() -> None:
    result = ChaoxingAPI._normalize_knowledge_graph_settings(
        {
            "showSetData": {
                "showAllRelation": 1,
                "showAllTopicname": 0,
                "navNodeScale": True,
                "graphBackgroundColor": False,
            },
            "dataJson": {"advancedSet": {"threedMapState": 1}},
        }
    )

    assert result["show_all_relations"] is True
    assert result["show_all_topic_names"] is False
    assert result["navigation_node_scale"] is True
    assert result["graph_background_color"] is False
    assert result["raw_advanced_settings"] == {"threedMapState": 1}


def test_graph_settings_update_uses_observed_methods_and_fresh_verification(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {
        "common": {
            "courseid": COURSE["course_id"],
            "cpi": COURSE["cpi"],
        }
    }
    configurations = iter(
        [
            {
                "showSetData": {
                    "showAllRelation": 0,
                    "showAllTopicname": 0,
                    "navNodeScale": 1,
                    "graphBackgroundColor": 0,
                }
            },
            {
                "showSetData": {
                    "showAllRelation": 1,
                    "showAllTopicname": 0,
                    "navNodeScale": 0,
                    "graphBackgroundColor": 0,
                }
            },
        ]
    )
    requests: list[dict] = []
    monkeypatch.setattr(api, "_knowledge_graph_context", lambda *_args: context)
    monkeypatch.setattr(api, "_knowledge_graph_config_data", lambda _context: next(configurations))

    def request(_context, path, _operation, **kwargs):
        requests.append({"path": path, **kwargs})
        return {"status": True}

    monkeypatch.setattr(api, "_knowledge_graph_json_request", request)

    result = api.update_knowledge_graph_settings(
        COURSE,
        CLAZZ,
        show_all_relations=True,
        navigation_node_scale=False,
    )

    assert requests[0]["method"] == "GET"
    assert requests[0]["params"]["showAllRelation"] == 1
    assert requests[1]["method"] == "POST"
    assert requests[1]["data"]["navNodeScale"] == 0
    assert result["changed_fields"] == ["show_all_relations", "navigation_node_scale"]
    assert result["settings"]["show_all_relations"] is True


def test_graph_settings_update_rolls_back_completed_fields_on_failure(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {
        "common": {
            "courseid": COURSE["course_id"],
            "cpi": COURSE["cpi"],
        }
    }
    calls: list[tuple[str, bool]] = []
    monkeypatch.setattr(api, "_knowledge_graph_context", lambda *_args: context)
    monkeypatch.setattr(
        api,
        "_knowledge_graph_config_data",
        lambda _context: {
            "showSetData": {
                "showAllRelation": 0,
                "showAllTopicname": 0,
                "navNodeScale": 1,
                "graphBackgroundColor": 0,
            }
        },
    )

    def update(_context, field, value):
        calls.append((field, value))
        if field == "showAllTopicname":
            raise ChaoxingAPIError("simulated failure")

    monkeypatch.setattr(api, "_update_knowledge_graph_setting_field", update)

    with pytest.raises(ChaoxingAPIError, match="settings update failed"):
        api.update_knowledge_graph_settings(
            COURSE,
            CLAZZ,
            show_all_relations=True,
            show_all_topic_names=True,
        )

    assert calls == [
        ("showAllRelation", True),
        ("showAllTopicname", True),
        ("showAllRelation", False),
    ]


def test_graph_advanced_settings_normalizer_and_atomic_topic_pair(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {
        "common": {
            "courseid": COURSE["course_id"],
            "cpi": COURSE["cpi"],
        }
    }
    before = {
        "topicCard": 0,
        "teachTarget": 0,
        "studyHoursEnabled": 0,
        "classifyRelationData": 0,
        "microPreview": 0,
        "microScaleMode": 0,
        "switchStatusData": {"selftestIncluded": 0},
        "showMicroTab": {"showMicroData": 1},
    }
    after = {
        **before,
        "topicCard": 1,
        "teachTarget": 1,
        "studyHoursEnabled": 1,
    }
    states = iter([before, after])
    requests: list[dict] = []
    monkeypatch.setattr(api, "_knowledge_graph_context", lambda *_args: context)
    monkeypatch.setattr(api, "_knowledge_graph_topic_setting_data", lambda _context: next(states))

    def request(_context, path, _operation, **kwargs):
        requests.append({"path": path, **kwargs})
        return {"status": True}

    monkeypatch.setattr(api, "_knowledge_graph_json_request", request)

    result = api.update_knowledge_graph_advanced_settings(
        COURSE,
        CLAZZ,
        topic_card=True,
        teach_target=True,
        study_hours_enabled=True,
    )

    assert requests[0]["path"].endswith("updatetopiccardstatus")
    assert requests[0]["params"]["topicCard"] == 1
    assert requests[0]["params"]["teachTarget"] == 1
    assert requests[1]["path"].endswith("updateStudyHoursEnabled")
    assert result["changed_groups"] == ["topic_pair", "study_hours_enabled"]
    assert result["settings"]["raw_micro_tabs"] == {"showMicroData": 1}


def test_graph_advanced_settings_roll_back_completed_groups(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"common": {"courseid": COURSE["course_id"], "cpi": COURSE["cpi"]}}
    before = {
        "topicCard": 0,
        "teachTarget": 0,
        "studyHoursEnabled": 0,
        "classifyRelationData": 0,
        "microPreview": 0,
        "microScaleMode": 0,
        "switchStatusData": {"selftestIncluded": 0},
    }
    calls: list[tuple[str, dict]] = []
    monkeypatch.setattr(api, "_knowledge_graph_context", lambda *_args: context)
    monkeypatch.setattr(api, "_knowledge_graph_topic_setting_data", lambda _context: before)

    def update(_context, group, values):
        calls.append((group, values))
        if group == "study_hours_enabled":
            raise ChaoxingAPIError("simulated failure")

    monkeypatch.setattr(api, "_update_knowledge_graph_advanced_setting_group", update)

    with pytest.raises(ChaoxingAPIError, match="advanced knowledge-graph settings update failed"):
        api.update_knowledge_graph_advanced_settings(
            COURSE,
            CLAZZ,
            topic_card=True,
            study_hours_enabled=True,
        )

    assert [group for group, _values in calls] == [
        "topic_pair",
        "study_hours_enabled",
        "topic_pair",
    ]
    assert calls[-1][1]["topic_card"] is False


def test_create_update_and_delete_graph_nodes_use_observed_contracts(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"common": {"courseid": COURSE["course_id"], "clazzid": CLAZZ["clazz_id"]}}
    root_id = f"courseid-{COURSE['course_id']}"
    states = iter(
        [
            _graph(),
            _graph(("100", "临时分类", 1, root_id)),
            _graph(("100", "临时分类", 1, root_id)),
            _graph(("100", "已改名", 1, root_id)),
            _graph(
                ("100", "已改名", 1, root_id),
                ("101", "子节点", 2, "100"),
            ),
            _graph(),
        ]
    )
    requests: list[dict] = []
    monkeypatch.setattr(api, "_knowledge_graph_context", lambda *_args: context)
    monkeypatch.setattr(api, "_knowledge_graph_raw_data", lambda _context: next(states))

    def request(_context, path, _operation, **kwargs):
        requests.append({"path": path, **kwargs})
        if path.endswith("addtopicwithexpand"):
            return {"status": True, "topicId": 100}
        return {"status": True}

    monkeypatch.setattr(api, "_knowledge_graph_json_request", request)
    monkeypatch.setattr("chaoxing_agent.api.sleep", lambda _seconds: None)

    created = api.create_knowledge_graph_category(COURSE, CLAZZ, "临时分类", description="说明")
    updated = api.update_knowledge_graph_category(COURSE, CLAZZ, "100", "已改名")
    deleted = api.delete_knowledge_graph_node(COURSE, CLAZZ, "100")

    assert created["category"]["topic_id"] == "100"
    assert requests[0]["method"] == "POST"
    assert requests[0]["data"]["addNodeType"] == 1
    assert requests[1]["data"]["topicId"] == "100"
    assert requests[2]["params"]["topicId"] == "100"
    assert updated["category"]["name"] == "已改名"
    assert deleted["deleted_descendant_count"] == 1


def test_generic_graph_node_create_uses_editor_model_type_parent_and_fresh_id(
    monkeypatch,
) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    root_id = f"courseid-{COURSE['course_id']}"
    before = _graph(("100", "父节点", 1, root_id))
    after = _graph(
        ("100", "父节点", 1, root_id),
        ("101", "新技能点", 2, "100"),
    )
    for node in after["nodes"]:
        if node.get("topicid") == 101:
            node["pile"] = 0
            node["tag"] = "23004933"
    states = iter([before, after])
    context = {
        "common": {
            "courseid": COURSE["course_id"],
            "clazzid": CLAZZ["clazz_id"],
            "cpi": COURSE["cpi"],
        }
    }
    requests: list[dict] = []
    monkeypatch.setattr(api, "_knowledge_graph_context", lambda *_args: context)
    monkeypatch.setattr(api, "_knowledge_graph_raw_data", lambda _context: next(states))
    monkeypatch.setattr(api, "_knowledge_graph_topic_setting_data", lambda _context: _model_data())

    def request(_context, path, _operation, **kwargs):
        requests.append({"path": path, **kwargs})
        return {"status": True, "topicId": 101}

    monkeypatch.setattr(api, "_knowledge_graph_json_request", request)
    monkeypatch.setattr("chaoxing_agent.api.sleep", lambda _seconds: None)

    result = api.create_knowledge_graph_node(
        COURSE,
        CLAZZ,
        "新技能点",
        node_type="ability",
        parent="父节点",
    )

    assert result["node"]["topic_id"] == "101"
    assert result["node_type"] == "ability"
    assert requests[0]["path"].endswith("/addtopic")
    assert requests[0]["data"]["curOperateTopicId"] == "100"
    assert requests[0]["data"]["addNodeType"] == 0
    assert requests[0]["data"]["isAbilityPoint"] == 1
    assert requests[0]["data"]["topicModelId"] == "1"


def test_generic_graph_node_update_refreshes_stable_node_name(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    root_id = f"courseid-{COURSE['course_id']}"
    states = iter(
        [
            _graph(("100", "原知识点", 1, root_id)),
            _graph(("100", "新知识点", 1, root_id)),
        ]
    )
    context = {"common": {"courseid": COURSE["course_id"], "cpi": COURSE["cpi"]}}
    requests: list[dict] = []
    monkeypatch.setattr(api, "_knowledge_graph_context", lambda *_args: context)
    monkeypatch.setattr(api, "_knowledge_graph_raw_data", lambda _context: next(states))

    def request(_context, path, _operation, **kwargs):
        requests.append({"path": path, **kwargs})
        return {"status": True}

    monkeypatch.setattr(api, "_knowledge_graph_json_request", request)

    result = api.update_knowledge_graph_node(
        COURSE, CLAZZ, "100", "新知识点", description="节点说明"
    )

    assert requests[0]["path"].endswith("updatenameanddesc")
    assert requests[0]["data"]["topicDesc"] == "节点说明"
    assert result["node"]["name"] == "新知识点"


def _relation_config() -> dict:
    return {
        "dataJson": {
            "relationTypeDesc": [
                {
                    "relationDescId": 0,
                    "relationDescName": "关联关系",
                    "relationDescType": 0,
                    "isDefault": True,
                },
                {
                    "relationDescId": 1,
                    "relationDescName": "前置关系",
                    "relationDescType": 1,
                    "isDefault": True,
                },
                {
                    "relationDescId": 2,
                    "relationDescName": "后置关系",
                    "relationDescType": 2,
                    "isDefault": True,
                },
                {
                    "relationDescId": 88,
                    "relationDescName": "支持关系",
                    "relationDescType": 0,
                    "isDefault": False,
                },
            ]
        }
    }


def test_node_relation_add_preserves_other_groups_and_verifies_full_state(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    root_id = f"courseid-{COURSE['course_id']}"
    graph = _graph(
        ("100", "源节点", 1, root_id),
        ("101", "目标节点", 1, root_id),
        ("102", "原前置", 1, root_id),
        ("103", "原自定义", 1, root_id),
    )
    before_html = """
      <ul data-relationId="1"><li data="102"><span class="zpSpan">原前置</span></li></ul>
      <ul data-relationId="2"></ul><ul data-relationId="0"></ul>
      <ul data-relationId="88"><li data="103"><span class="zpSpan">原自定义</span></li></ul>
    """
    after_html = """
      <ul data-relationId="1"><li data="102"><span class="zpSpan">原前置</span></li></ul>
      <ul data-relationId="2"></ul>
      <ul data-relationId="0"><li data="101" relationdesc="解释">
        <span class="zpSpan">目标节点</span></li></ul>
      <ul data-relationId="88"><li data="103"><span class="zpSpan">原自定义</span></li></ul>
    """
    html_states = iter([before_html, after_html])
    context = {
        "common": {
            "courseid": COURSE["course_id"],
            "clazzid": CLAZZ["clazz_id"],
            "cpi": COURSE["cpi"],
        }
    }
    requests: list[dict] = []
    monkeypatch.setattr(api, "_knowledge_graph_context", lambda *_args: context)
    monkeypatch.setattr(api, "_knowledge_graph_raw_data", lambda _context: graph)
    monkeypatch.setattr(api, "_knowledge_graph_config_data", lambda _context: _relation_config())
    monkeypatch.setattr(api, "_knowledge_graph_relation_html", lambda *_args: next(html_states))

    def request(_context, path, _operation, **kwargs):
        requests.append({"path": path, **kwargs})
        return {"status": True}

    monkeypatch.setattr(api, "_knowledge_graph_json_request", request)

    result = api.add_knowledge_graph_node_relation(
        COURSE,
        CLAZZ,
        "源节点",
        "association",
        "目标节点",
        description="解释",
    )

    params = requests[0]["params"]
    assert params["relationTopicIds"] == "101,"
    assert params["relationTopicPrevIds"] == "102,"
    assert params["relationTopicNextIds"] == ""
    assert params["relationDesc"] == "解释"
    assert params["selfDefineTopicsMap"] == '{"88":["103"]}'
    assert result["changed"] is True and result["relation_count"] == 3


def test_node_relation_remove_and_mismatch_rollback_use_complete_replace(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    root_id = f"courseid-{COURSE['course_id']}"
    graph = _graph(
        ("100", "源节点", 1, root_id),
        ("101", "目标节点", 1, root_id),
    )
    present_html = """
      <ul data-relationId="1"></ul><ul data-relationId="2"></ul>
      <ul data-relationId="0"><li data="101" relationdesc="解释">
        <span class="zpSpan">目标节点</span></li></ul>
    """
    empty_html = (
        '<ul data-relationId="1"></ul><ul data-relationId="2"></ul><ul data-relationId="0"></ul>'
    )
    context = {"common": {"courseid": COURSE["course_id"], "cpi": COURSE["cpi"]}}
    requests: list[dict] = []
    monkeypatch.setattr(api, "_knowledge_graph_context", lambda *_args: context)
    monkeypatch.setattr(api, "_knowledge_graph_raw_data", lambda _context: graph)
    monkeypatch.setattr(api, "_knowledge_graph_config_data", lambda _context: _relation_config())
    html_states = iter([present_html, empty_html])
    monkeypatch.setattr(api, "_knowledge_graph_relation_html", lambda *_args: next(html_states))

    def request(_context, path, _operation, **kwargs):
        requests.append({"path": path, **kwargs})
        return {"status": True}

    monkeypatch.setattr(api, "_knowledge_graph_json_request", request)

    removed = api.remove_knowledge_graph_node_relation(
        COURSE, CLAZZ, "源节点", "association", "目标节点"
    )

    assert removed["changed"] is True and removed["relation_count"] == 0
    assert requests[0]["params"]["relationTopicIds"] == ""

    rollback_api = ChaoxingAPI(Path("unused-cookies.json"))
    rollback_requests: list[dict] = []
    rollback_states = iter([empty_html, empty_html, empty_html])
    monkeypatch.setattr(rollback_api, "_knowledge_graph_context", lambda *_args: context)
    monkeypatch.setattr(rollback_api, "_knowledge_graph_raw_data", lambda _context: graph)
    monkeypatch.setattr(
        rollback_api, "_knowledge_graph_config_data", lambda _context: _relation_config()
    )
    monkeypatch.setattr(
        rollback_api,
        "_knowledge_graph_relation_html",
        lambda *_args: next(rollback_states),
    )

    def rollback_request(_context, path, _operation, **kwargs):
        rollback_requests.append({"path": path, **kwargs})
        return {"status": True}

    monkeypatch.setattr(rollback_api, "_knowledge_graph_json_request", rollback_request)

    with pytest.raises(ChaoxingAPIError, match="original relation set was restored"):
        rollback_api.add_knowledge_graph_node_relation(
            COURSE, CLAZZ, "源节点", "successor", "目标节点"
        )

    assert len(rollback_requests) == 2


def test_label_group_normalizer_preserves_default_and_preset_flags() -> None:
    groups = ChaoxingAPI._normalize_knowledge_graph_label_groups(
        {
            "data": {
                "topicLabelGroupArray": [
                    {
                        "labelGroupId": 9,
                        "labelGroupName": "默认标签组",
                        "isDefault": 1,
                        "topicLabelArray": [{"id": 11, "name": " 重点 ", "precastLabel": 1}],
                    }
                ]
            }
        }
    )

    assert groups[0]["group_id"] == "9" and groups[0]["is_default"] is True
    assert groups[0]["labels"][0]["name"] == "重点"
    assert groups[0]["labels"][0]["precast"] is True


def test_create_group_and_label_verify_new_ids(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"common": {}}
    base = _label_groups(include_custom=False)
    created_group = _label_groups(include_custom=True)
    created_label = _label_groups(include_custom=True)
    created_label[1]["labels"].append(
        {
            "index": 2,
            "label_id": "21",
            "group_id": "2",
            "name": "检测",
            "precast": False,
        }
    )
    created_label[1]["label_count"] = 2
    states = iter([base, created_group, created_group, created_label])
    requests: list[dict] = []
    monkeypatch.setattr(api, "_knowledge_graph_context", lambda *_args: context)
    monkeypatch.setattr(api, "_knowledge_graph_label_groups", lambda _context: next(states))

    def request(_context, path, _operation, **kwargs):
        requests.append({"path": path, **kwargs})
        if path.endswith("addtopiclable"):
            return {"status": True, "saveTopiclabelId": 21}
        return {"status": True}

    monkeypatch.setattr(api, "_knowledge_graph_json_request", request)

    group_result = api.create_knowledge_graph_label_group(COURSE, CLAZZ, "自定义")
    label_result = api.create_knowledge_graph_label(COURSE, CLAZZ, "2", "检测")

    assert group_result["group"]["group_id"] == "2"
    assert label_result["label"]["label_id"] == "21"
    assert requests[0]["params"]["labelgrouptype"] == 0
    assert requests[1]["params"]["labelGroupId"] == "2"


def test_label_safeguards_stop_default_preset_and_incomplete_orders(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"common": {}}
    groups = _label_groups(include_custom=True)
    monkeypatch.setattr(api, "_knowledge_graph_context", lambda *_args: context)
    monkeypatch.setattr(api, "_knowledge_graph_label_groups", lambda _context: groups)
    monkeypatch.setattr(
        api,
        "_knowledge_graph_json_request",
        lambda *_args, **_kwargs: pytest.fail("unsafe request must not be sent"),
    )

    with pytest.raises(ChaoxingAPIError, match="default"):
        api.delete_knowledge_graph_label_group(COURSE, CLAZZ, "1")
    with pytest.raises(ChaoxingAPIError, match="preset"):
        api.rename_knowledge_graph_label(COURSE, CLAZZ, "10", "新名")
    with pytest.raises(ChaoxingAPIError, match="every label group"):
        api.reorder_knowledge_graph_label_groups(COURSE, CLAZZ, ["2"])
    with pytest.raises(ChaoxingAPIError, match="every label"):
        api.reorder_knowledge_graph_labels(COURSE, CLAZZ, "2", [])


def test_delete_label_and_group_fresh_verify_absence(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"common": {}}
    states = iter(
        [
            _label_groups(),
            [
                {
                    **_label_groups()[1],
                    "label_count": 0,
                    "labels": [],
                },
                _label_groups()[0],
            ],
            _label_groups(),
            _label_groups(include_custom=False),
        ]
    )
    monkeypatch.setattr(api, "_knowledge_graph_context", lambda *_args: context)
    monkeypatch.setattr(api, "_knowledge_graph_label_groups", lambda _context: next(states))
    monkeypatch.setattr(
        api,
        "_knowledge_graph_json_request",
        lambda *_args, **_kwargs: {"status": True},
    )

    deleted_label = api.delete_knowledge_graph_label(COURSE, CLAZZ, "20")
    deleted_group = api.delete_knowledge_graph_label_group(COURSE, CLAZZ, "2")

    assert deleted_label["deleted_label"]["label_id"] == "20"
    assert deleted_group["deleted_group"]["group_id"] == "2"


def _graph_events(*, updated: bool = False) -> list[dict]:
    return [
        {
            "index": 1,
            "event_id": "677",
            "name": "已改事件" if updated else "临时事件",
            "topic_condition": 1,
            "topic_condition_name": "knowledge_point_completion_rate",
            "set_condition": 3,
            "set_condition_name": "greater_than_or_equal",
            "percent1": 80,
            "percent2": 100,
            "execution_count": 1,
            "executions": [
                {
                    "index": 1,
                    "label_id": "10",
                    "label_name": "重点",
                    "execute_module": 0,
                    "execute_module_name": "learning_path",
                    "tag_content": 0,
                    "tag_content_name": "knowledge_point",
                }
            ],
        }
    ]


def test_graph_event_normalizer_preserves_conditions_and_executions() -> None:
    events = ChaoxingAPI._normalize_knowledge_graph_events(
        {
            "data": {
                "eventData": [
                    {
                        "id": 677,
                        "name": "完成事件",
                        "topicCondition": 1,
                        "setCondition": 7,
                        "percent1": 60,
                        "percent2": 80,
                        "exechteData": [
                            {
                                "labelId": 10,
                                "labelName": "重点",
                                "executeModule": 1,
                            }
                        ],
                    }
                ]
            },
            "status": True,
        }
    )

    assert events[0]["event_id"] == "677"
    assert events[0]["topic_condition_name"] == "knowledge_point_completion_rate"
    assert events[0]["set_condition_name"] == "between"
    assert events[0]["executions"][0]["execute_module_name"] == "microcourse_resources"
    assert events[0]["executions"][0]["tag_content_name"] == "resource"


def test_graph_event_create_update_delete_use_observed_contracts(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {
        "common": {
            "courseid": COURSE["course_id"],
            "cpi": COURSE["cpi"],
        }
    }
    states = iter(
        [
            [],
            _graph_events(),
            _graph_events(),
            _graph_events(updated=True),
            _graph_events(updated=True),
            [],
        ]
    )
    requests: list[dict] = []
    monkeypatch.setattr(api, "_knowledge_graph_context", lambda *_args: context)
    monkeypatch.setattr(api, "_knowledge_graph_events", lambda _context: next(states))
    monkeypatch.setattr(
        api,
        "_knowledge_graph_label_groups",
        lambda _context: _label_groups(include_custom=False),
    )

    def request(_context, path, _operation, **kwargs):
        requests.append({"path": path, **kwargs})
        return {"status": True}

    monkeypatch.setattr(api, "_knowledge_graph_json_request", request)

    created = api.create_knowledge_graph_event(
        COURSE,
        CLAZZ,
        "临时事件",
        topic_condition="知识点完成率",
        set_condition="大于等于",
        percent1=80,
        executions=[{"label": "重点", "module": "学习路径"}],
    )
    changed = api.update_knowledge_graph_event(COURSE, CLAZZ, "677", name="已改事件")
    deleted = api.delete_knowledge_graph_event(COURSE, CLAZZ, "677")

    create_form = requests[0]["data"]
    assert requests[0]["path"].endswith("addtopicevent")
    assert create_form["topicCondition"] == 1 and create_form["setCondition"] == 3
    assert '"executeModule":0' in create_form["executiveModuleParam"]
    assert requests[1]["path"].endswith("updatetopicevent")
    assert requests[1]["data"]["eventId"] == "677"
    assert requests[2]["path"].endswith("deletetopicevent")
    assert created["event"]["event_id"] == "677"
    assert changed["event"]["name"] == "已改事件"
    assert deleted["deleted_event"]["event_id"] == "677"


def test_graph_event_validation_rejects_invalid_range_and_execution_count(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"common": {"courseid": COURSE["course_id"], "cpi": COURSE["cpi"]}}
    monkeypatch.setattr(
        api,
        "_knowledge_graph_label_groups",
        lambda _context: _label_groups(include_custom=False),
    )

    with pytest.raises(ChaoxingAPIError, match="range start"):
        api._knowledge_graph_event_form(
            context,
            name="事件",
            topic_condition=1,
            set_condition=7,
            percent1=90,
            percent2=80,
            executions=[{"label": "重点", "execute_module": 0}],
        )
    with pytest.raises(ChaoxingAPIError, match="1-3"):
        api._knowledge_graph_event_form(
            context,
            name="事件",
            topic_condition=1,
            set_condition=0,
            percent1=80,
            percent2=100,
            executions=[],
        )


def test_graph_export_downloads_server_format_and_verifies_signature(monkeypatch, tmp_path) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))

    class Response:
        url = "https://mooc1.chaoxing.com/import-export-ans/file"
        headers = {
            "Content-Type": "application/vnd.ms-excel;charset=UTF-8",
            "Content-Disposition": "attachment;filename=course.xlsx",
        }

        @staticmethod
        def raise_for_status() -> None:
            return None

        @staticmethod
        def iter_content(chunk_size):
            assert chunk_size == 1024 * 256
            return iter([b"PK\x03\x04", b"workbook"])

    class Session:
        @staticmethod
        def get(url, **kwargs):
            assert url == "https://mooc1.chaoxing.com/import-export-ans/file"
            assert kwargs["stream"] is True
            return Response()

    context = {
        "session": Session(),
        "common": {"courseid": COURSE["course_id"], "cpi": COURSE["cpi"]},
        "referer": "https://mooc2-ans.chaoxing.com/topic-ans/knowgraph/index.html",
    }
    requests: list[dict] = []
    monkeypatch.setattr(api, "_knowledge_graph_context", lambda *_args: context)
    monkeypatch.setattr(api, "_knowledge_graph_topic_setting_data", lambda _context: _model_data())
    monkeypatch.setattr(
        api,
        "_knowledge_graph_config_data",
        lambda _context: {"dataJson": {"exportCourseTopicEnc": "enc"}},
    )

    def request(_context, path, _operation, **kwargs):
        requests.append({"path": path, **kwargs})
        return {
            "status": True,
            "data": "https://mooc1.chaoxing.com/import-export-ans/file",
        }

    monkeypatch.setattr(api, "_knowledge_graph_json_request", request)

    result = api.download_knowledge_graph_export(
        COURSE,
        CLAZZ,
        "xlsx",
        tmp_path,
    )

    assert requests[0]["path"].endswith("export-knowledge-points")
    assert requests[0]["params"]["topicModelId"] == "1"
    assert "exportType" not in requests[0]["params"]
    assert result["format"] == "excel" and result["byte_count"] == 12
    assert (tmp_path / "course.xlsx").read_bytes() == b"PK\x03\x04workbook"
