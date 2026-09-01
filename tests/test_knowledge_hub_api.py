import json
from pathlib import Path

import pytest

from chaoxing_agent.api import ChaoxingAPI, ChaoxingAPIError

COURSE = {"course_id": "900000001", "course_name": "语言与测试", "cpi": "485781386"}
CLAZZ = {"clazz_id": "800000001", "clazz_name": "默认班级"}


def _raw_base(**changes) -> dict[str, object]:
    raw: dict[str, object] = {
        "baseId": 3263707,
        "baseName": "默认知识库",
        "desc": "课程默认知识库",
        "category": 0,
        "state": 0,
        "enable": True,
        "defaultBase": True,
        "shared": False,
        "priority": 0,
        "cover": "https://robot-lc.chaoxing.com/static/default.png",
        "resourceSize": 0,
        "segmentNum": 0,
        "segmentCharNum": "0",
        "rule": {"splitStrategy": 0, "enableOcr": True},
        "permissions": {"setting": True, "delete": False},
    }
    raw.update(changes)
    return raw


def _base(**changes) -> dict[str, object]:
    normalized = ChaoxingAPI._normalize_knowledge_hub_base(_raw_base(**changes), 1)
    return normalized


def _document(**changes) -> dict[str, object]:
    raw: dict[str, object] = {
        "id": 77,
        "fileKey": "file-key-1",
        "objectId": "object-1",
        "docName": "课程说明.pdf",
        "fileType": "pdf",
        "fileSize": 1234,
        "state": 0,
        "fileEnable": True,
        "allowDownload": True,
    }
    raw.update(changes)
    return ChaoxingAPI._normalize_knowledge_hub_document(raw, 1)


def test_knowledge_hub_bootstrap_parser_reads_only_required_scalar_values() -> None:
    values = ChaoxingAPI._knowledge_hub_js_values(
        """
        <script>
          const unitId = '23080';
          var courseRobotId = "991";
          let rbtoken = 'private-token';
          var courseId = 900000001;
          var type = 0;
        </script>
        """
    )

    assert values["unitId"] == "23080"
    assert values["courseRobotId"] == "991"
    assert values["rbtoken"] == "private-token"
    assert values["courseId"] == "900000001"
    assert ChaoxingAPI._knowledge_hub_public_value(values).get("rbtoken") is None


def test_knowledge_hub_normalizers_preserve_state_and_resolve_unique_names() -> None:
    default = _base()
    custom = _base(
        baseId=3263881,
        baseName="期末复习库",
        desc="复习材料",
        defaultBase=False,
        enable=False,
        shared=True,
        priority=1,
    )

    assert default["category_name"] == "文档库" and default["state_name"] == "completed"
    assert custom["enabled"] is False and custom["shared"] is True
    assert (
        ChaoxingAPI._resolve_knowledge_hub_base([default, custom], "期末")["base_id"] == "3263881"
    )
    with pytest.raises(ChaoxingAPIError, match="multiple"):
        ChaoxingAPI._resolve_knowledge_hub_base(
            [custom, {**custom, "base_id": "3263882", "name": "期末资料库"}],
            "期末",
        )


def test_create_knowledge_hub_base_uses_existing_cover_and_verifies_new_id(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"course": COURSE, "clazz": CLAZZ}
    before = [_base()]
    created = _base(
        baseId=3263881,
        baseName="期末复习库",
        desc="期末复习资料",
        defaultBase=False,
    )
    pages = iter([(before, {"total": 1}), ([*before, created], {"total": 2})])
    request: dict[str, object] = {}

    monkeypatch.setattr(api, "_knowledge_hub_context", lambda *_args: context)
    monkeypatch.setattr(
        api, "_knowledge_hub_bases_from_context", lambda *_args, **_kwargs: next(pages)
    )

    def request_json(_context, path, _operation, **kwargs):
        request.update({"path": path, **kwargs})
        return {"code": 200, "data": {"baseId": 3263881}}

    monkeypatch.setattr(api, "_knowledge_hub_json_request", request_json)
    monkeypatch.setattr(
        api,
        "_knowledge_hub_base_detail_raw",
        lambda *_args, **_kwargs: _raw_base(
            baseId=3263881,
            baseName="期末复习库",
            desc="期末复习资料",
            defaultBase=False,
        ),
    )

    result = api.create_knowledge_hub_base(COURSE, CLAZZ, "期末复习库", "期末复习资料")

    assert result["base"]["base_id"] == "3263881"
    assert request["path"] == "/v1/manage/multi/knowledge/base/addOrUpdate"
    assert request["params"] == {"mode": "ADD"}
    assert request["json_body"]["cover"].endswith("default.png")
    assert request["json_body"]["rule"] == {"splitStrategy": 0, "enableOcr": True}


def test_share_knowledge_hub_base_posts_boolean_and_rechecks_detail(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"course": COURSE, "clazz": CLAZZ}
    request: dict[str, object] = {}

    monkeypatch.setattr(api, "_knowledge_hub_context", lambda *_args: context)
    monkeypatch.setattr(
        api, "_knowledge_hub_resolve_from_context", lambda *_args, **_kwargs: _base()
    )
    monkeypatch.setattr(
        api,
        "_knowledge_hub_base_detail_raw",
        lambda *_args, **_kwargs: _raw_base(shared=True),
    )

    def request_json(_context, path, _operation, **kwargs):
        request.update({"path": path, **kwargs})
        return {"code": 200}

    monkeypatch.setattr(api, "_knowledge_hub_json_request", request_json)

    result = api.set_knowledge_hub_base_share(COURSE, CLAZZ, "默认知识库", True)

    assert result["base"]["shared"] is True
    assert request["path"] == "/v1/manage/multi/knowledge/switch/share"
    assert request["json_body"] == {"baseId": "3263707", "shared": True}


def test_delete_knowledge_hub_default_base_stops_before_request(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {"course": COURSE, "clazz": CLAZZ}
    monkeypatch.setattr(api, "_knowledge_hub_context", lambda *_args: context)
    monkeypatch.setattr(api, "_knowledge_hub_resolve_from_context", lambda *_args: _base())
    monkeypatch.setattr(
        api,
        "_knowledge_hub_json_request",
        lambda *_args, **_kwargs: pytest.fail("default base deletion must not be sent"),
    )

    with pytest.raises(ChaoxingAPIError, match="default"):
        api.delete_knowledge_hub_base(COURSE, CLAZZ, "默认知识库")


def test_knowledge_hub_document_upload_keeps_authorization_out_of_result(
    monkeypatch, tmp_path
) -> None:
    source = tmp_path / "课程说明.txt"
    source.write_text("课程材料", encoding="utf-8")
    api = ChaoxingAPI(Path("unused-cookies.json"))
    selected_base = _base()
    created_document = _document(
        fileKey="file-new",
        objectId="object-new",
        docName=source.name,
    )
    document_pages = iter([[], [created_document]])
    upload_call: dict[str, object] = {}

    class UploadResponse:
        content = json.dumps({"result": True, "data": {"objectId": "object-new"}}).encode()
        encoding = "utf-8"
        apparent_encoding = "utf-8"

        @staticmethod
        def raise_for_status() -> None:
            return None

    class UploadSession:
        @staticmethod
        def post(url, **kwargs):
            upload_call.update({"url": url, **kwargs})
            return UploadResponse()

    context = {"course": COURSE, "clazz": CLAZZ, "session": UploadSession()}
    monkeypatch.setattr(api, "_knowledge_hub_context", lambda *_args: context)
    monkeypatch.setattr(
        api,
        "_knowledge_hub_resolve_from_context",
        lambda *_args, **_kwargs: selected_base,
    )
    monkeypatch.setattr(
        api,
        "_knowledge_hub_all_documents",
        lambda *_args, **_kwargs: next(document_pages),
    )
    registrations: list[dict[str, object]] = []

    def request_json(_context, path, _operation, **kwargs):
        if path.endswith("/upload/token"):
            return {
                "code": 200,
                "data": {
                    "puid": "100",
                    "clientIp": "127.0.0.1",
                    "token": "private-upload-token",
                    "uploadUrl": "https://pan-yz.chaoxing.com/upload/v2",
                },
            }
        registrations.append({"path": path, **kwargs})
        return {"code": 200}

    monkeypatch.setattr(api, "_knowledge_hub_json_request", request_json)
    monkeypatch.setattr(api, "_knowledge_hub_default_classify_id", lambda _context: "2")

    result = api.upload_knowledge_hub_document(COURSE, CLAZZ, "默认知识库", source)

    assert result["document"]["file_key"] == "file-new"
    assert "private-upload-token" not in str(result)
    assert upload_call["url"] == "https://pan-yz.chaoxing.com/upload/v2"
    assert registrations[0]["path"].endswith("/file/multi/upload")
    assert registrations[0]["json_body"]["fileList"] == [
        {"fileName": source.name, "objectId": "object-new"}
    ]
