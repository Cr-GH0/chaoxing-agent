from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from chaoxing_agent.api import ChaoxingAPI, ChaoxingAPIError


def _api() -> ChaoxingAPI:
    return ChaoxingAPI(Path("cookies.json"))


def test_job_ability_signature_matches_live_client_contract() -> None:
    assert (
        ChaoxingAPI._job_ability_signature("英语", day="2026-09-01")
        == "3359fd1692edf93693c187c8ef4dce5e"
    )


def test_job_ad_normalizer_removes_html_and_preserves_public_fields() -> None:
    result = ChaoxingAPI._normalize_job_ability_ad(
        {
            "id": 42,
            "zpgw": "英语教师招聘",
            "zwmc": "英语教师",
            "zpqy": "示例学校",
            "xqrs": "3",
            "xzdy": "8-12K",
            "gwms": "<p>教授 <b>英语写作</b></p>",
            "qyjs": "<div>学校简介</div>",
            "jlxqydz": "https://example.invalid/jobs/42",
        },
        1,
    )
    assert result["job_ad_id"] == "42"
    assert result["demand_count"] == 3
    assert result["job_description"] == "教授 英语写作"
    assert result["company_description"] == "学校简介"
    assert "<" not in json.dumps(result, ensure_ascii=False)


def test_job_ability_status_omits_identity_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    api = _api()
    monkeypatch.setattr(api, "_job_ability_context", lambda: {"session": object()})
    monkeypatch.setattr(
        api,
        "_job_ability_json_request",
        lambda *_args, **_kwargs: {
            "status": True,
            "data": {
                "uid": "private-uid",
                "fid": "private-fid",
                "realName": "Private Name",
                "majortrend": 1,
                "schoolBaseLibrary": 0,
                "civilPostgraduate": "false",
            },
        },
    )
    result = api.read_job_ability_status()
    encoded = json.dumps(result, ensure_ascii=False)
    assert result["major_trend_enabled"] is True
    assert result["school_base_library_enabled"] is False
    assert result["civil_postgraduate_enabled"] is False
    assert "private-uid" not in encoded
    assert "Private Name" not in encoded


def test_job_search_signs_keyword_and_normalizes_page(monkeypatch: pytest.MonkeyPatch) -> None:
    api = _api()
    calls: list[tuple[str, dict[str, Any]]] = []
    monkeypatch.setattr(api, "_job_ability_context", lambda: {"session": object()})
    monkeypatch.setattr(api, "_job_ability_signature", lambda value: f"sig:{value}")

    def request(
        _context: dict[str, Any],
        path: str,
        *,
        params: dict[str, Any] | None = None,
        operation: str,
    ) -> dict[str, Any]:
        del operation
        calls.append((path, dict(params or {})))
        return {
            "status": True,
            "total": 8,
            "data": [{"id": "9", "zwmc": "英语教师", "zpqy": "示例学校"}],
        }

    monkeypatch.setattr(api, "_job_ability_json_request", request)
    result = api.search_job_ability_jobs(
        "英语",
        page=2,
        page_size=5,
        education_level="本科",
    )
    assert calls == [
        (
            "/jobability/job/qwjs",
            {"sw": "英语", "enc": "sig:英语", "page": 2, "size": 5, "cc": "本科"},
        )
    ]
    assert result["jobs"][0]["index"] == 6
    assert result["jobs"][0]["job_ad_id"] == "9"


def test_job_ad_resolver_requires_a_unique_match() -> None:
    jobs = [
        {
            "index": 1,
            "job_ad_id": "1",
            "job_title": "英语教师",
            "recruitment_title": "英语教师招聘",
            "company": "甲校",
        },
        {
            "index": 2,
            "job_ad_id": "2",
            "job_title": "英语教师",
            "recruitment_title": "英语教师招聘",
            "company": "乙校",
        },
    ]
    assert ChaoxingAPI._resolve_job_ability_ad(jobs, "2")["company"] == "乙校"
    assert ChaoxingAPI._resolve_job_ability_ad(jobs, "甲校 英语教师")["job_ad_id"] == "1"
    with pytest.raises(ChaoxingAPIError, match="multiple job ads match"):
        ChaoxingAPI._resolve_job_ability_ad(jobs, "英语教师")


def test_occupation_and_industry_endpoints_use_distinct_signatures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _api()
    calls: list[tuple[str, dict[str, Any]]] = []
    monkeypatch.setattr(api, "_job_ability_context", lambda: {"session": object()})
    monkeypatch.setattr(api, "_job_ability_signature", lambda value: f"sig:{value}")

    def request(
        _context: dict[str, Any],
        path: str,
        *,
        params: dict[str, Any] | None = None,
        operation: str,
    ) -> dict[str, Any]:
        del operation
        calls.append((path, dict(params or {})))
        if path.endswith("joblibrary/index"):
            return {
                "status": True,
                "data": {
                    "yijcount": 1,
                    "erjcount": 2,
                    "sanjcount": 3,
                    "sijcount": 4,
                    "rmzylist": [{"zymc": "教师", "xqrs": 10}],
                    "xxzylist": [{"zymc": "人工智能训练师", "xqrs": 5}],
                },
            }
        if path.endswith("industrytype/list"):
            return {"status": True, "total": 2, "data": ["教育", "互联网技术"]}
        if path.endswith("industry/list"):
            return {"status": True, "total": 1, "data": ["教学人员"]}
        return {
            "status": True,
            "total": 1,
            "data": [{"id": 7, "gwmc": "英语教师", "gwzz": "<p>教学</p>"}],
        }

    monkeypatch.setattr(api, "_job_ability_json_request", request)
    catalog = api.read_job_ability_occupation_catalog()
    types = api.list_job_ability_industry_types()
    industries = api.list_job_ability_industries("教育")
    jobs = api.list_job_ability_industry_jobs("教学人员")

    assert catalog["counts"] == {"level_1": 1, "level_2": 2, "level_3": 3, "level_4": 4}
    assert types["industry_types"] == ["教育", "互联网技术"]
    assert industries["industries"] == ["教学人员"]
    assert jobs["jobs"][0]["responsibilities"] == "教学"
    assert [params["enc"] for _path, params in calls] == [
        "sig:index",
        "sig:industrytype",
        "sig:教育",
        "sig:教学人员",
    ]


def test_job_ability_page_validation_rejects_unbounded_requests() -> None:
    with pytest.raises(ChaoxingAPIError, match="page_size"):
        ChaoxingAPI._job_ability_page_values(1, 101)
