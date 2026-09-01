import json
import zipfile
from pathlib import Path
from urllib.parse import quote

import pytest
import requests

from chaoxing_agent.api import (
    COURSE_ASSET_KINDS,
    PERSONAL_GROUP_MANAGER_AUTHORITY_FIELDS,
    PERSONAL_GROUP_SPEAKING_RULE_FIELDS,
    ChaoxingAPI,
    ChaoxingAPIError,
    aes_encrypt_base64,
    content_disposition_filename,
    grade_component_schema,
    normalize_learning_activity,
    normalize_learning_record_sections,
    normalize_question_bank_smart_import_paper,
    parse_chapter_cards,
    parse_chapter_editor_tree,
    parse_chapter_items,
    parse_class_join_applications,
    parse_class_settings,
    parse_class_student_table,
    parse_course_data_items,
    parse_course_operation_log_rows,
    parse_discussion_payload,
    parse_discussion_replies,
    parse_discussion_topic,
    parse_exam_answer_sheet,
    parse_exam_editor_outline,
    parse_exam_items,
    parse_exam_paper,
    parse_exam_paper_library_items,
    parse_exam_question_detail,
    parse_exam_submission_payload,
    parse_grade_score_payload,
    parse_grade_summary_payload,
    parse_grade_visibility_payload,
    parse_grade_weight_configuration,
    parse_homework_drafts,
    parse_homework_editor_outline,
    parse_homework_items,
    parse_homework_library_items,
    parse_homework_question_detail,
    parse_learning_ai_tools,
    parse_learning_chapters,
    parse_learning_courses,
    parse_learning_homework_answer_form,
    parse_learning_homework_attempts,
    parse_learning_homework_detail,
    parse_learning_materials,
    parse_learning_progress_payload,
    parse_learning_task_entries,
    parse_learning_wrong_question_summary,
    parse_note_detail_html,
    parse_note_detail_user,
    parse_notice_draft_payload,
    parse_notice_payload,
    parse_notice_send_time,
    parse_personal_group_manage_context,
    parse_personal_notice_compose_context,
    parse_personal_space_modules,
    parse_question_bank_directory_tree,
    parse_question_bank_download_center,
    parse_question_bank_export_context,
    parse_question_bank_inactive_items,
    parse_question_bank_items,
    parse_question_bank_label_tree,
    parse_question_bank_permission_teachers,
    parse_question_bank_question_types,
    parse_question_bank_smart_import_context,
    parse_question_bank_source_courses,
    parse_question_bank_source_questions,
    parse_question_bank_topic_tree,
    parse_resource_import_courses,
    parse_resource_import_items,
    parse_resource_labels,
    parse_review_summary,
    parse_statistics_navigation,
    parse_student_access_log_payload,
    parse_student_access_summary,
    parse_student_bank_candidates,
    parse_student_join_log_rows,
    parse_student_leave_log_rows,
    parse_study_monitor_payload,
    parse_submission_rows,
    parse_teacher_bank_candidates,
    parse_teacher_nav_items,
    parse_teacher_team,
    parse_teaching_courses,
    reposition_identifier,
    resolve_chapter_editor_item,
    resolve_class,
    resolve_class_join_application,
    resolve_class_student,
    resolve_course,
    resolve_discussion_reply,
    resolve_exam,
    resolve_exam_editor_question,
    resolve_exam_paper_library_item,
    resolve_exam_paper_question,
    resolve_exam_question_type_group,
    resolve_exam_submission,
    resolve_homework,
    resolve_homework_draft,
    resolve_homework_editor_target,
    resolve_homework_library_item,
    resolve_homework_question,
    resolve_learning_course,
    resolve_learning_material,
    resolve_module,
    resolve_notice,
    resolve_notice_draft,
    resolve_personal_space_module,
    resolve_question_bank_directory,
    resolve_question_bank_download_record,
    resolve_question_bank_inactive_item,
    resolve_question_bank_label,
    resolve_question_bank_question,
    resolve_question_bank_question_type,
    resolve_question_bank_topic,
    resolve_resource_item,
    resolve_student_bank_candidate,
    resolve_student_leave_log,
    resolve_study_monitor_student,
    resolve_submission,
    resolve_teacher_bank_candidate,
)


class LoginResponse:
    def __init__(
        self,
        *,
        url: str,
        body: str = "",
        payload: dict | None = None,
        status_code: int = 200,
    ) -> None:
        self.url = url
        self.content = body.encode("utf-8")
        self.encoding = "utf-8"
        self.apparent_encoding = "utf-8"
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        if self._payload is None:
            raise ValueError("not JSON")
        return self._payload


class LoginSession:
    def __init__(
        self,
        login_payload: dict,
        *,
        target_url: str = "",
        target_final_url: str = "",
        target_body: str = "",
    ) -> None:
        self.headers: dict[str, str] = {}
        self.cookies = requests.cookies.RequestsCookieJar()
        self.login_payload = login_payload
        self.target_url = target_url
        self.target_final_url = target_final_url
        self.target_body = target_body
        self.calls: list[tuple[str, str, dict]] = []

    def get(self, url: str, **kwargs) -> LoginResponse:
        self.calls.append(("GET", url, kwargs))
        if "passport2.chaoxing.com/login?" in url:
            return LoginResponse(
                url=url,
                body=(
                    '<input type="hidden" name="t" value="true">'
                    '<input type="hidden" name="fid" value="-1">'
                    '<input type="hidden" name="forbidotherlogin" value="0">'
                ),
            )
        if self.target_url and url == self.target_url:
            return LoginResponse(
                url=self.target_final_url or self.target_url,
                body=self.target_body,
            )
        return LoginResponse(
            url="https://i.chaoxing.com/",
            body='<main id="frame_content" aria-label="账号：测试账号">课程教学</main>',
        )

    def post(self, url: str, **kwargs) -> LoginResponse:
        self.calls.append(("POST", url, kwargs))
        self.cookies.set("JSESSIONID", "cookie-secret", domain=".chaoxing.com", path="/")
        return LoginResponse(url=url, payload=self.login_payload)


class RecordingJSONSession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict]] = []

    @staticmethod
    def _response(payload: dict):
        class Response:
            content = json.dumps(payload).encode("utf-8")
            encoding = "utf-8"
            apparent_encoding = "utf-8"

            @staticmethod
            def raise_for_status() -> None:
                return None

        return Response()

    def get(self, url: str, **kwargs):
        self.calls.append(("GET", url, kwargs))
        return self._response({"status": True})

    def post(self, url: str, **kwargs):
        self.calls.append(("POST", url, kwargs))
        if url.endswith("updatePaperLibraryRelationScore") or url.endswith(
            "deleteDataFromFukPaper"
        ):
            return self._response({"success": True})
        return self._response({"status": True})


def test_login_transfer_encryption_matches_known_values() -> None:
    assert aes_encrypt_base64("13800138000") == "yYcVatS+4J+JGnm88UM56A=="
    assert aes_encrypt_base64("密码123") == "6Hzxr9z21jWH8a7krVur2g=="


def test_http_login_verifies_then_atomically_saves_cookies(tmp_path, monkeypatch) -> None:
    cookie_file = tmp_path / "session.json"
    session = LoginSession({"status": True, "url": "https%3A//i.chaoxing.com/"})
    monkeypatch.setattr(ChaoxingAPI, "_new_session", staticmethod(lambda: session))

    result = ChaoxingAPI(cookie_file).login("13800138000", "密码123")

    assert result["logged_in"] is True
    assert result["account_name"] == "测试账号"
    assert result["cookies_saved"] == 1
    saved = json.loads(cookie_file.read_text(encoding="utf-8"))
    assert saved["cookies"][0]["name"] == "JSESSIONID"
    assert saved["cookies"][0]["value"] == "cookie-secret"
    post = next(call for call in session.calls if call[0] == "POST")
    assert post[2]["data"]["uname"] == aes_encrypt_base64("13800138000")
    assert post[2]["data"]["password"] == aes_encrypt_base64("密码123")
    assert "密码123" not in json.dumps(result, ensure_ascii=False)
    assert "cookie-secret" not in json.dumps(result, ensure_ascii=False)


def test_failed_http_login_preserves_existing_cookie_file(tmp_path, monkeypatch) -> None:
    cookie_file = tmp_path / "session.json"
    original = '{"cookies":[{"name":"old","value":"still-valid"}]}\n'
    cookie_file.write_text(original, encoding="utf-8")
    session = LoginSession({"status": False, "msg2": "账号或密码错误"})
    monkeypatch.setattr(ChaoxingAPI, "_new_session", staticmethod(lambda: session))

    with pytest.raises(ChaoxingAPIError, match="账号或密码错误"):
        ChaoxingAPI(cookie_file).login("13800138000", "wrong-password")

    assert cookie_file.read_text(encoding="utf-8") == original


def test_failed_http_login_redacts_server_reflected_password(tmp_path, monkeypatch) -> None:
    cookie_file = tmp_path / "session.json"
    password = "server-reflected-password"
    session = LoginSession({"status": False, "msg2": f"password {password} is invalid"})
    monkeypatch.setattr(ChaoxingAPI, "_new_session", staticmethod(lambda: session))

    with pytest.raises(ChaoxingAPIError) as error:
        ChaoxingAPI(cookie_file).login("13800138000", password)

    assert password not in str(error.value)
    assert "[redacted]" in str(error.value)


def test_http_login_verifies_cross_application_target_without_returning_signed_queries(
    tmp_path,
    monkeypatch,
) -> None:
    cookie_file = tmp_path / "session.json"
    target_url = (
        "https://xueyinonline.chaoxing.com/schoolcourseInfo/"
        "teachingclassmanage/livecoursenew?courseId=1&stuenc=student-secret"
    )
    session = LoginSession(
        {
            "status": True,
            "url": ("https%3A//xueyinonline.chaoxing.com/sso/callback%3Fticket%3Dticket-secret"),
        },
        target_url=target_url,
        target_body="<title>直播课</title><main>直播安排</main>",
    )
    monkeypatch.setattr(ChaoxingAPI, "_new_session", staticmethod(lambda: session))

    result = ChaoxingAPI(cookie_file).login(
        "13800138000",
        "密码123",
        target_url=target_url,
    )

    assert result["logged_in"] is True
    assert result["target"] == {
        "requested_host": "xueyinonline.chaoxing.com",
        "requested_path": "/schoolcourseInfo/teachingclassmanage/livecoursenew",
        "final_host": "xueyinonline.chaoxing.com",
        "final_path": "/schoolcourseInfo/teachingclassmanage/livecoursenew",
        "http_status": 200,
        "title": "直播课",
        "login_redirected": False,
        "target_reached": True,
        "verification": "target host reached without a Chaoxing login page",
    }
    serialized = json.dumps(result, ensure_ascii=False)
    assert "student-secret" not in serialized
    assert "ticket-secret" not in serialized
    assert cookie_file.exists()
    assert any(call[0] == "GET" and call[1] == target_url for call in session.calls)
    assert any(call[0] == "GET" and call[1] == "https://i.chaoxing.com/" for call in session.calls)


def test_cross_application_login_redirect_preserves_existing_cookie_file(
    tmp_path,
    monkeypatch,
) -> None:
    cookie_file = tmp_path / "session.json"
    original = '{"cookies":[{"name":"old","value":"still-valid"}]}\n'
    cookie_file.write_text(original, encoding="utf-8")
    target_url = (
        "https://xueyinonline.chaoxing.com/schoolcourseInfo/"
        "teachingclassmanage/livecoursenew?stuenc=student-secret"
    )
    session = LoginSession(
        {"status": True, "url": "https%3A//i.chaoxing.com/"},
        target_url=target_url,
        target_final_url=("https://passport2.chaoxing.com/login?refer=target-secret"),
        target_body=('<form action="/fanyalogin"><input name="uname"></form>'),
    )
    monkeypatch.setattr(ChaoxingAPI, "_new_session", staticmethod(lambda: session))

    with pytest.raises(ChaoxingAPIError, match="requested Chaoxing target") as error:
        ChaoxingAPI(cookie_file).login(
            "13800138000",
            "密码123",
            target_url=target_url,
        )

    assert "student-secret" not in str(error.value)
    assert "target-secret" not in str(error.value)
    assert cookie_file.read_text(encoding="utf-8") == original


def test_learning_course_module_login_target_is_resolved_only_in_memory(
    tmp_path,
    monkeypatch,
) -> None:
    api = ChaoxingAPI(tmp_path / "session.json")
    course = {
        "course_id": "265813684",
        "course_name": "测试课程",
        "clazz_id": "123456789",
        "cpi": "987654321",
    }
    context = {
        "final_url": "https://mooc2-ans.chaoxing.com/mooc2-ans/mycourse/stu",
        "values": {
            "courseid": course["course_id"],
            "clazzid": course["clazz_id"],
            "cpi": course["cpi"],
            "t": "true",
            "enc": "student-secret",
        },
        "modules": [
            {
                "module": "zb_jm",
                "label": "直播课/见面课",
                "data_url": (
                    "https://xueyinonline.chaoxing.com/schoolcourseInfo/"
                    "teachingclassmanage/livecoursenew"
                ),
            }
        ],
    }
    monkeypatch.setattr(api, "get_learning_course", lambda _query: course)
    monkeypatch.setattr(api, "_session", lambda: object())
    monkeypatch.setattr(api, "_learning_course_context", lambda _session, _course: context)

    selected_course, module, target_url = api.resolve_learning_course_module_login_target(
        "测试课程",
        "直播课/见面课",
    )

    assert selected_course == course
    assert module["module"] == "zb_jm"
    assert target_url.startswith(
        "https://xueyinonline.chaoxing.com/schoolcourseInfo/teachingclassmanage/livecoursenew?"
    )
    assert "courseId=265813684" in target_url
    assert "classId=123456789" in target_url
    assert "stuenc=student-secret" in target_url


def test_subject_creation_listing_normalizes_folders_subjects_and_recycle_flags(
    monkeypatch,
) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    payload = {
        "show": True,
        "totalNum": 1,
        "folders": [
            {
                "id": 21,
                "folderName": "课程专题",
                "cfid": -1,
                "hasChilds": False,
                "subCount": 0,
            }
        ],
        "specials": [
            {
                "id": 31,
                "course_Id": 41,
                "encCourseId": "encrypted",
                "name": "写作专题",
                "published": 1,
                "author": "教师",
            }
        ],
    }
    monkeypatch.setattr(api, "_subject_creation_request", lambda *args, **kwargs: payload)

    listing = api._subject_creation_listing(object(), "https://example.test")
    assert listing["folders"][0]["id"] == "21"
    assert listing["subjects"][0]["course_id"] == "41"
    assert listing["subjects"][0]["published"] is True
    assert (
        api._resolve_subject_creation_item(listing["subjects"], "写作专题", "subject")["id"] == "31"
    )
    recycled = api._normalize_subject_creation_subject(
        {"course_Id": 41, "name": "写作专题", "selfDeleted": 0}, 1, ""
    )
    assert recycled["deleted_by_admin"] is True


def test_detection_record_parser_preserves_token_status_links_and_pagination() -> None:
    html = """
    <input type="hidden" id="isFree" value="true">
    <ul id="ul_record-token">
      <li><span class="personal_testRecords_title_name">论文标题</span></li>
      <li><span class="personal_testRecords_title_status">状态：完成</span></li>
      <li><a href="/smas/aigc/report?webArticleStr=record-token">下载报告</a></li>
    </ul>
    <script>setPage('2', '10', '21');</script>
    """
    parsed = ChaoxingAPI._parse_detection_records(html, "aigc")
    assert parsed["page"] == 2 and parsed["page_size"] == 10 and parsed["total"] == 21
    assert parsed["free_entitlement_page"] is True
    assert parsed["records"][0]["token"] == "record-token"
    assert parsed["records"][0]["title"] == "论文标题"
    assert parsed["records"][0]["status_text"] == "状态：完成"
    assert parsed["records"][0]["links"][0]["label"] == "下载报告"


def test_detection_type_aliases_and_file_validation(tmp_path) -> None:
    assert ChaoxingAPI._detection_type("查重")[0] == "similarity"
    assert ChaoxingAPI._detection_type("AIGC")[0] == "aigc"
    assert ChaoxingAPI._detection_type("两两比对")[0] == "comparison"
    document = tmp_path / "paper.txt"
    document.write_text("content", encoding="utf-8")
    assert ChaoxingAPI._validate_detection_file(document) == document.resolve()
    unsupported = tmp_path / "paper.exe"
    unsupported.write_bytes(b"content")
    with pytest.raises(ChaoxingAPIError, match="detection file must"):
        ChaoxingAPI._validate_detection_file(unsupported)


def sample_payload() -> dict:
    return {
        "result": 1,
        "channelList": [
            {
                "cpi": "485781386",
                "content": {
                    "id": "900000001",
                    "name": "语言测试示例",
                    "teacherfactor": "张三",
                    "schools": "2026-2027-1",
                    "clazz": [
                        {
                            "clazzId": "800000001",
                            "clazzName": "英日2301-2302",
                            "clazzStudentCount": 61,
                            "chatid": "323050429022212",
                            "state": 0,
                        }
                    ],
                },
            }
        ],
    }


def test_parse_teaching_courses_preserves_chinese() -> None:
    courses = parse_teaching_courses(sample_payload())
    assert courses[0]["course_name"] == "语言测试示例"
    assert courses[0]["classes"][0]["clazz_name"] == "英日2301-2302"
    assert courses[0]["class_count"] == 1


def test_resolve_course_by_name_id_and_index() -> None:
    courses = parse_teaching_courses(sample_payload())
    assert resolve_course(courses, "语言测试示例")["course_id"] == "900000001"
    assert resolve_course(courses, "900000001")["course_name"] == "语言测试示例"
    assert resolve_course(courses, "1")["course_id"] == "900000001"


def sample_learning_course_list_html() -> str:
    return """
    <div class="course clearfix learnCourse stu_125867890"
         info="125867890_485781386" roleId="stu_125867890" id="c_254641935">
      <input class="clazzId" value="125867890">
      <input class="courseId" value="254641935">
      <input class="role" value="0">
      <input class="curPersonId" value="485781386">
      <a href="https://mooc1.chaoxing.com/visit/stucoursemiddle?courseid=254641935&amp;clazzid=125867890&amp;cpi=485781386&amp;ismooc2=1&amp;v=2">
        <img data-original="https://p.ananas.chaoxing.com/star.png">
        <span class="course-name overHidden2" title="英语文体与写作">英语文体与写作</span>
      </a>
      <p class="color3" title="张老师">张老师</p>
      <p>开课时间：2025-2026-2</p>
      <a onclick="quitTheCourse('125867890')">退课</a>
    </div>
    <div class="course clearfix learnCourse endCourse stu_145388184"
         info="145388184_549097219" roleId="stu_145388184" id="c_262819125">
      <input class="clazzId" value="145388184">
      <input class="courseId" value="262819125">
      <input class="role" value="0">
      <input class="curPersonId" value="549097219">
      <a href="https://mooc1.chaoxing.com/visit/stucoursemiddle?courseid=262819125&amp;clazzid=145388184&amp;cpi=549097219&amp;ismooc2=1&amp;v=2">
        <span class="course-name" title="实验室安全培训">实验室安全培训</span>
      </a>
      <p class="color3" title="学校培训中心">学校培训中心</p>
      <p>开课时间：2026</p>
      <span>已结束课程</span>
    </div>
    """


def sample_learning_course_page_html(*, course_status: str = "-1") -> str:
    return f"""
    <html><head><title>英语文体与写作</title></head><body>
      <input type="hidden" id="courseid" value="254641935">
      <input type="hidden" id="clazzid" value="125867890">
      <input type="hidden" id="cpi" value="485781386">
      <input type="hidden" id="personid" value="485781386">
      <input type="hidden" id="enc" value="student-enc">
      <input type="hidden" id="workEnc" value="work-enc">
      <input type="hidden" id="examEnc" value="exam-enc">
      <input type="hidden" id="oldenc" value="old-enc">
      <input type="hidden" id="openc" value="open-enc">
      <input type="hidden" id="t" value="token-t">
      <ul>
        <li dataname="zj" pageHeader="1">
          <a data-url="/mooc2-ans/mycourse/studentstudy?chapterId=0" title="章节">章节</a>
        </li>
        <li dataname="zy">
          <a data-url="https://mooc1.chaoxing.com/mooc2/work/list?foo=bar" title="作业">作业</a>
        </li>
      </ul>
      <script>
        var notAgreeCommitment = false;
        var notAgreeCourseCommitment = {course_status};
      </script>
    </body></html>
    """


def test_parse_and_resolve_learning_courses() -> None:
    courses = parse_learning_courses(sample_learning_course_list_html())

    assert len(courses) == 2
    assert courses[0]["course_name"] == "英语文体与写作"
    assert courses[0]["clazz_id"] == "125867890"
    assert courses[0]["teacher"] == "张老师"
    assert courses[0]["term"] == "2025-2026-2"
    assert courses[0]["can_quit"] is True
    assert courses[1]["ended"] is True
    assert resolve_learning_course(courses, "英语文体与写作")["course_id"] == "254641935"
    assert resolve_learning_course(courses, "145388184")["course_name"] == "实验室安全培训"


def test_learning_course_list_modules_open_and_integrity_are_http_only(monkeypatch) -> None:
    class Response:
        def __init__(self, url: str, body: str, *, payload: dict | None = None) -> None:
            self.url = url
            self.content = body.encode("utf-8")
            self.encoding = "utf-8"
            self.apparent_encoding = "utf-8"
            self.status_code = 200
            self.headers = {"Content-Type": "text/html; charset=utf-8"}
            self._payload = payload

        @staticmethod
        def raise_for_status() -> None:
            return None

    class Session:
        def __init__(self) -> None:
            self.calls: list[tuple[str, str, dict]] = []

        def post(self, url: str, **kwargs) -> Response:
            self.calls.append(("POST", url, kwargs))
            return Response(url, sample_learning_course_list_html())

        def get(self, url: str, **kwargs) -> Response:
            self.calls.append(("GET", url, kwargs))
            if "studentstudy" in url:
                return Response(url, "<html><title>章节学习</title><main>第一章</main></html>")
            return Response(
                "https://mooc2-ans.chaoxing.com/mooc2-ans/mycourse/stu?courseid=254641935",
                sample_learning_course_page_html(),
            )

    api = ChaoxingAPI(Path("unused-cookies.json"))
    session = Session()
    landing = Response(
        "https://mooc2-ans.chaoxing.com/visit/interaction",
        '<input type="hidden" id="fid" value="23080">',
    )
    monkeypatch.setattr(
        api,
        "_personal_space_module_context",
        lambda _query: (session, landing, {"label": "课程教学"}),
    )
    courses = api.list_learning_courses()
    assert len(courses) == 2
    assert session.calls[0][2]["data"]["courseType"] == "1"

    course = courses[0]
    monkeypatch.setattr(api, "_session", lambda: session)
    modules = api.discover_learning_course_modules(course)
    assert [item["label"] for item in modules["modules"]] == ["章节", "作业"]
    opened = api.inspect_learning_course_module(course, "章节")
    assert opened["title"] == "章节学习"
    assert "pageHeader=1" in opened["request_url"]
    integrity = api.read_learning_integrity(course)
    assert integrity["commitment"]["required"] is False
    assert integrity["commitment"]["basis"].startswith("account commitment is accepted")


def test_learning_integrity_accept_requires_acknowledgement_and_refresh(monkeypatch) -> None:
    class Response:
        def __init__(self, url: str, body: str, content_type: str = "text/html") -> None:
            self.url = url
            self.content = body.encode("utf-8")
            self.encoding = "utf-8"
            self.apparent_encoding = "utf-8"
            self.status_code = 200
            self.headers = {"Content-Type": content_type}

        @staticmethod
        def raise_for_status() -> None:
            return None

    class Session:
        def __init__(self) -> None:
            self.page_reads = 0
            self.calls: list[tuple[str, dict]] = []

        def get(self, url: str, **kwargs) -> Response:
            self.calls.append((url, kwargs))
            if url.endswith("/update-person-status"):
                return Response(url, '{"status":true,"msg":"ok"}', "application/json")
            self.page_reads += 1
            status = "0" if self.page_reads == 1 else "1"
            return Response(
                "https://mooc2-ans.chaoxing.com/mooc2-ans/mycourse/stu?courseid=254641935",
                sample_learning_course_page_html(course_status=status).replace(
                    "var notAgreeCommitment = false;",
                    "var notAgreeCommitment = true;",
                ),
            )

    course = {
        "course_id": "254641935",
        "course_name": "英语文体与写作",
        "clazz_id": "125867890",
        "cpi": "485781386",
        "entry_url": (
            "https://mooc1.chaoxing.com/visit/stucoursemiddle?"
            "courseid=254641935&clazzid=125867890&cpi=485781386"
        ),
    }
    api = ChaoxingAPI(Path("unused-cookies.json"))
    session = Session()
    monkeypatch.setattr(api, "_session", lambda: session)

    result = api.accept_learning_integrity(course)

    assert result["changed"] is True
    assert result["before"]["required"] is True
    assert result["after"]["accepted"] is True
    update = next(call for call in session.calls if call[0].endswith("update-person-status"))
    assert update[1]["params"] == {
        "courseid": "254641935",
        "clazzid": "125867890",
        "personid": "485781386",
        "type": "1",
    }


def test_learning_integrity_missing_flags_are_unknown_not_accepted() -> None:
    state = ChaoxingAPI._learning_integrity_state({"values": {}})

    assert state["required"] is False
    assert state["accepted"] is None
    assert state["state_known"] is False


def test_parse_learner_semantic_pages_without_exposing_session_tokens() -> None:
    ai_tools = parse_learning_ai_tools(
        """
        <ul>
          <li iframeId="assistant" hrefStr="https://robot.example/tool?enc=secret&amp;x=1">
            <span class="workName">写作AI助教</span>
          </li>
        </ul>
        <input iframeId="resources" agentName="资料助手"
               hrefStr="https://resource.example/search?token=secret">
        """
    )
    assert [item["name"] for item in ai_tools] == ["写作AI助教", "资料助手"]
    assert "secret" not in str(ai_tools)
    assert "%5Bredacted%5D" in ai_tools[0]["entry_url"]

    chapters = parse_learning_chapters(
        """
        <div class="chapter_unit">
          <div class="chapter_item">
            <div class="catalog_num fl"><em>1</em></div>
            <div class="catalog_name"><span title="Essay Writing">Essay Writing</span></div>
          </div>
          <div class="chapter_item" id="cur101" title="Learning Guide">
            <span class="catalog_sbar">1.1</span>
            <input type="hidden" class="knowledgeJobCount" value="2">
            <span class="bntHoverTips">2个待完成任务点</span>
          </div>
          <div class="chapter_item" id="cur102" title="The Writing Process">
            <span class="catalog_sbar">1.2</span>
            <input value="0" class="knowledgeJobCount" type="hidden">
          </div>
        </div>
        """
    )
    assert chapters["units"][0]["title"] == "Essay Writing"
    assert chapters["units"][0]["pending_task_count"] == 2
    assert chapters["chapters"][1]["chapter_id"] == "102"

    tasks = parse_learning_task_entries(
        """
        <ul><li onclick="goTask(this);"
          data="https://mooc1.example/task?workId=88&amp;answerId=0&amp;enc=secret"
          aria-label="写作调查 ; 未交">
          <p class="overHidden2 fl">写作调查</p><p class="status fl">未交</p>
        </li></ul>
        """
    )
    assert tasks[0]["work_id"] == "88"
    assert tasks[0]["status_key"] == "unsubmitted"
    assert "secret" not in str(tasks)

    homework_detail = parse_learning_homework_detail(
        """
        <input type="hidden" id="courseId" value="10">
        <input type="hidden" id="classId" value="20">
        <input type="hidden" id="workId" value="88">
        <input type="hidden" id="answerId" value="99">
        <div class="detailsHead">
          <div class="classtips">作业当前可修改</div>
          <h2 class="mark_title">BOPPPS 设计</h2>
          <div class="infoHead">题量: 1 满分: 100 作答时间: 01-09 10:06 至 01-17 10:06</div>
        </div>
        <div class="mark_item">
          <h2 class="type_tit">一. 简答题（共1题，100分）</h2>
          <div class="questionLi" id="question405540058" data="405540058">
            <h3 class="mark_name">1. <span class="colorShallow">(简答题, 100分)</span>
              <span class="qtContent"><p>请设计一个课堂导入。</p>
                <img src="/question.png?enc=secret&amp;token=image-token">
              </span>
            </h3>
            <dd class="stuAnswerContent"><p>使用真实问题引入。</p></dd>
          </div>
        </div>
        <a href="/mooc-ans/mooc2/work/dowork?enc=secret">继续作答</a>
        <button onclick="redoWork()">重做</button>
        <script>function redoWork() { var redoTimes = 3 + 1 - 2; }</script>
        """
    )
    assert homework_detail["title"] == "BOPPPS 设计"
    assert homework_detail["declared_question_count"] == 1
    assert homework_detail["declared_full_score"] == 100
    assert homework_detail["answer_start_time"] == "01-09 10:06"
    assert homework_detail["questions"][0]["question_type"] == "short_answer"
    assert homework_detail["questions"][0]["stem"] == "请设计一个课堂导入。"
    assert "redacted" in homework_detail["questions"][0]["stem_images"][0]
    assert homework_detail["questions"][0]["student_answer"] == "使用真实问题引入。"
    assert homework_detail["can_answer"] is True
    assert homework_detail["can_redo"] is True
    assert homework_detail["redo_times_remaining"] == 2
    assert "secret" not in str(homework_detail)
    assert "image-token" not in str(homework_detail)

    answer_form = parse_learning_homework_answer_form(
        """
        <input type="hidden" id="courseId" value="10">
        <input type="hidden" id="classId" value="20">
        <input type="hidden" id="workId" value="88">
        <input type="hidden" id="answerId" value="101">
        <form id="workForm" method="post" action="/work/save?enc=secret">
          <div class="mark_item"><h2 class="type_tit">一. 简答题（共1题，100分）</h2>
            <div class="questionLi" data="1">
              <h3 class="mark_name">1. <span class="colorShallow">(简答题)</span>
                <span class="qtContent">说明课堂导入。</span>
              </h3>
              <textarea id="answer1" name="answer1"></textarea>
            </div>
          </div>
          <button type="button" onclick="saveWork()">暂存</button>
          <button type="button" onclick="submitWork()">提交</button>
        </form>
        """
    )
    assert answer_form["answer_form_detected"] is True
    assert answer_form["question_count"] == 1
    assert answer_form["save_available"] is True
    assert answer_form["submit_available"] is True
    assert answer_form["forms"][0]["action"]["query_keys"] == ["enc"]
    assert "secret" not in str(answer_form)

    attempts = parse_learning_homework_attempts(
        """
        <div class="recordTab">
          <a onclick="showAnswer(1)">第 1 次作答 80 分</a>
          <a onclick="showAnswer('2')">第 2 次作答 90 分</a>
        </div>
        <script>function showAnswer(times) { window.open('/view?enc=secret'); }</script>
        """
    )
    assert attempts["attempt_count"] == 2
    assert attempts["history_available"] is True
    assert attempts["attempts"][1] == {
        "index": 2,
        "attempt_id": "2",
        "times": "2",
        "label": "第 2 次作答 90 分",
    }
    assert "secret" not in str(attempts)
    empty_attempts = parse_learning_homework_attempts(
        '<div class="recordTab">没有作答记录...</div>'
    )
    assert empty_attempts["attempt_count"] == 0
    assert empty_attempts["history_available"] is True
    assert empty_attempts["empty_message"] == "没有作答记录..."
    invalid_attempts = parse_learning_homework_attempts(
        '<div class="recordTab">提示 无效的作答</div>'
    )
    assert invalid_attempts["history_available"] is False
    unknown_attempts = parse_learning_homework_attempts(
        '<div class="recordTab">系统繁忙，请稍后重试</div>'
    )
    assert unknown_attempts["history_available"] is None


def test_learning_homework_detail_read_keeps_list_state_unchanged(monkeypatch) -> None:
    list_html = """
    <ul><li onclick="goTask(this);"
      data="https://mooc1.chaoxing.com/mooc-ans/mooc2/work/task?workId=88&amp;answerId=99&amp;enc=secret"
      aria-label="BOPPPS 设计 ; 未交">
      <p class="overHidden2 fl">BOPPPS 设计</p><p class="status fl">未交</p>
    </li></ul>
    """
    detail_html = """
    <input type="hidden" id="courseId" value="10">
    <input type="hidden" id="classId" value="20">
    <input type="hidden" id="workId" value="88">
    <input type="hidden" id="answerId" value="99">
    <h2 class="mark_title">BOPPPS 设计</h2>
    <div class="infoHead">题量: 1 满分: 100</div>
    <div class="mark_item"><h2 class="type_tit">一. 简答题（共1题，100分）</h2>
      <div class="questionLi" id="question1" data="1">
        <h3 class="mark_name">1. <span class="colorShallow">(简答题)</span>
          <span class="qtContent">说明课堂导入。</span>
        </h3>
        <dd class="stuAnswerContent">已有草稿</dd>
      </div>
    </div>
    """

    class Response:
        url = "https://mooc1.chaoxing.com/mooc-ans/mooc2/work/view?enc=secret"
        status_code = 200
        headers = {"Content-Type": "text/html;charset=UTF-8"}
        encoding = "utf-8"
        apparent_encoding = "utf-8"
        content = detail_html.encode("utf-8")

        @staticmethod
        def raise_for_status() -> None:
            return None

    class Session:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict]] = []

        def get(self, url: str, **kwargs) -> Response:
            self.calls.append((url, kwargs))
            return Response()

    session = Session()
    page = type(
        "Page",
        (),
        {"url": "https://mooc2-ans.chaoxing.com/mooc2-ans/mycourse/stu?courseid=10"},
    )()
    api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        api,
        "_learning_module_response",
        lambda _course, _module: {
            "session": session,
            "response": page,
            "html": list_html,
        },
    )
    course = {"course_id": "10", "course_name": "Writing", "clazz_id": "20"}

    result = api.read_learning_homework(course, "BOPPPS 设计")

    assert result["work_id"] == "88"
    assert result["answer_id"] == "99"
    assert result["questions"][0]["student_answer"] == "已有草稿"
    assert result["state_unchanged"] is True
    assert result["page"] == {
        "host": "mooc1.chaoxing.com",
        "path": "/mooc-ans/mooc2/work/view",
        "http_status": 200,
    }
    assert session.calls[0][1]["headers"]["Referer"] == page.url
    assert "secret" not in str(result)

    monkeypatch.setattr(
        api,
        "list_learning_homeworks",
        lambda _course: {
            "homeworks": [
                {
                    "index": 1,
                    "title": "BOPPPS 设计",
                    "status": "已交",
                    "status_key": "submitted",
                    "work_id": "88",
                    "answer_id": "100",
                }
            ]
        },
    )
    with pytest.raises(ChaoxingAPIError, match="state changed while reading"):
        api.read_learning_homework(course, "BOPPPS 设计")


def test_learning_homework_read_stops_before_answer_form_redirect(monkeypatch) -> None:
    list_html = """
    <ul><li onclick="goTask(this);"
      data="https://mooc1.chaoxing.com/mooc-ans/mooc2/work/task?workId=88&amp;answerId=0&amp;enc=secret"
      aria-label="可作答作业 ; 未交">
      <p class="overHidden2 fl">可作答作业</p><p class="status fl">未交</p>
    </li></ul>
    """

    class Response:
        url = "https://mooc1.chaoxing.com/mooc-ans/mooc2/work/task?enc=secret"
        status_code = 302
        headers = {"Location": "/mooc-ans/mooc2/work/dowork?workId=88&answerId=0&enc=secret"}

        @staticmethod
        def raise_for_status() -> None:
            return None

    class Session:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict]] = []

        def get(self, url: str, **kwargs) -> Response:
            self.calls.append((url, kwargs))
            return Response()

    session = Session()
    page = type(
        "Page",
        (),
        {"url": "https://mooc2-ans.chaoxing.com/mooc2-ans/mycourse/stu?courseid=10"},
    )()
    api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        api,
        "_learning_module_response",
        lambda _course, _module: {
            "session": session,
            "response": page,
            "html": list_html,
        },
    )
    course = {"course_id": "10", "course_name": "Writing", "clazz_id": "20"}

    with pytest.raises(ChaoxingAPIError, match="stopped before requesting that form"):
        api.read_learning_homework(course, "可作答作业")

    assert len(session.calls) == 1
    assert session.calls[0][1]["allow_redirects"] is False


def test_learning_homework_answer_enter_follows_only_explicit_answer_action(monkeypatch) -> None:
    list_html = """
    <ul><li onclick="goTask(this);"
      data="https://mooc1.chaoxing.com/mooc-ans/mooc2/work/task?workId=88&amp;answerId=0&amp;enc=secret"
      aria-label="可作答作业 ; 未交">
      <p class="overHidden2 fl">可作答作业</p><p class="status fl">未交</p>
    </li></ul>
    """
    answer_html = """
    <input type="hidden" id="courseId" value="10">
    <input type="hidden" id="classId" value="20">
    <input type="hidden" id="workId" value="88">
    <input type="hidden" id="answerId" value="101">
    <h2 class="mark_title">可作答作业</h2>
    <form id="workForm" method="post" action="/work/save?enc=secret">
      <div class="mark_item"><h2 class="type_tit">一. 简答题（共1题，100分）</h2>
        <div class="questionLi" data="1">
          <h3 class="mark_name">1. <span class="colorShallow">(简答题)</span>
            <span class="qtContent">说明课堂导入。</span>
          </h3>
          <textarea id="answer1" name="answer1"></textarea>
        </div>
      </div>
      <button type="button" onclick="saveWork()">暂存</button>
      <button type="button" onclick="submitWork()">提交</button>
    </form>
    """

    class Response:
        encoding = "utf-8"
        apparent_encoding = "utf-8"

        def __init__(
            self,
            url: str,
            status_code: int,
            html: str = "",
            location: str = "",
        ) -> None:
            self.url = url
            self.status_code = status_code
            self.content = html.encode("utf-8")
            self.headers = {"Content-Type": "text/html;charset=UTF-8"}
            if location:
                self.headers["Location"] = location

        @staticmethod
        def raise_for_status() -> None:
            return None

    class Session:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict]] = []

        def get(self, url: str, **kwargs) -> Response:
            self.calls.append((url, kwargs))
            if url.endswith("/mooc-ans/mooc2/work/dowork?workId=88&answerId=0&enc=secret"):
                return Response(
                    "https://mooc1.chaoxing.com/mooc-ans/mooc2/work/dowork"
                    "?workId=88&answerId=101&enc=secret",
                    200,
                    answer_html,
                )
            return Response(
                url,
                302,
                location=("/mooc-ans/mooc2/work/dowork?workId=88&answerId=0&enc=secret"),
            )

    session = Session()
    page = type(
        "Page",
        (),
        {"url": "https://mooc2-ans.chaoxing.com/mooc2-ans/mycourse/stu?courseid=10"},
    )()
    api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        api,
        "_learning_module_response",
        lambda _course, _module: {
            "session": session,
            "response": page,
            "html": list_html,
        },
    )
    course = {"course_id": "10", "course_name": "Writing", "clazz_id": "20"}

    result = api.enter_learning_homework_answer(course, "可作答作业")

    assert result["page"]["path"] == "/mooc-ans/mooc2/work/dowork"
    assert result["form"]["answer_form_detected"] is True
    assert result["form"]["work_id"] == "88"
    assert result["form"]["answer_id"] == "101"
    assert result["answer_instance_created"] is True
    assert len(session.calls) == 2
    assert all(call[1]["allow_redirects"] is False for call in session.calls)
    assert "secret" not in str(result)


def test_learning_homework_redo_uses_observed_endpoint_then_requires_answer_form(
    monkeypatch,
) -> None:
    class Response:
        encoding = "utf-8"
        apparent_encoding = "utf-8"

        def __init__(self, url: str, content: str, content_type: str) -> None:
            self.url = url
            self.status_code = 200
            self.headers = {"Content-Type": content_type}
            self.content = content.encode("utf-8")

        @staticmethod
        def raise_for_status() -> None:
            return None

    class Session:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict]] = []

        def get(self, url: str, **kwargs) -> Response:
            self.calls.append((url, kwargs))
            if url.endswith("/mooc-ans/work/phone/redo"):
                return Response(url, '{"status":1,"msg":"ok"}', "application/json")
            return Response(
                "https://mooc1.chaoxing.com/mooc-ans/mooc2/work/dowork"
                "?workId=88&answerId=100&enc=secret",
                answer_html,
                "text/html;charset=UTF-8",
            )

    session = Session()
    homework = {
        "title": "可重做作业",
        "work_id": "88",
        "answer_id": "99",
        "status": "已交",
        "status_key": "submitted",
        "entry_url": "https://mooc1.chaoxing.com/task?enc=secret",
    }
    detail_html = """
    <input type="hidden" id="courseId" value="10">
    <input type="hidden" id="classId" value="20">
    <input type="hidden" id="cpi" value="30">
    <input type="hidden" id="workId" value="88">
    <input type="hidden" id="answerId" value="99">
    <script>
      function modifyAnswer() {
        location.href = "/mooc-ans/mooc2/work/dowork?courseId=10&classId=20&cpi=30&workId=88"
          + "&answerId=99&standardEnc=fake&enc=secret";
      }
    </script>
    """
    answer_html = """
    <input type="hidden" id="courseId" value="10">
    <input type="hidden" id="classId" value="20">
    <input type="hidden" id="workId" value="88">
    <input type="hidden" id="answerId" value="100">
    <form id="workForm" method="post" action="/work/save?enc=secret">
      <div class="mark_item"><h2 class="type_tit">一. 简答题（共1题，100分）</h2>
        <div class="questionLi" data="1">
          <h3 class="mark_name">1. <span class="colorShallow">(简答题)</span>
            <span class="qtContent">说明课堂导入。</span>
          </h3>
          <textarea id="answer1" name="answer1"></textarea>
        </div>
      </div>
    </form>
    """
    page = type(
        "Page",
        (),
        {"url": "https://mooc1.chaoxing.com/mooc-ans/mooc2/work/view?enc=secret"},
    )()
    api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        api,
        "_learning_homework_detail_context",
        lambda _course, _homework: {
            "homework": homework,
            "detail": {"can_redo": True, "redo_times_remaining": 1},
            "html": detail_html,
            "response": page,
            "session": session,
        },
    )
    monkeypatch.setattr(
        api,
        "list_learning_homeworks",
        lambda _course: {
            "homeworks": [
                {
                    **homework,
                    "answer_id": "100",
                    "status": "未交",
                    "status_key": "unsubmitted",
                }
            ]
        },
    )
    course = {
        "course_id": "10",
        "course_name": "Writing",
        "clazz_id": "20",
        "cpi": "30",
    }

    result = api.redo_learning_homework(course, "可重做作业")

    assert result["redo_times_before"] == 1
    assert result["redo_request"]["path"] == "/mooc-ans/work/phone/redo"
    assert result["answer"]["form"]["answer_form_detected"] is True
    assert result["answer"]["form"]["answer_id"] == "100"
    assert len(session.calls) == 2
    assert session.calls[0][1]["params"] == {
        "courseId": "10",
        "classId": "20",
        "cpi": "30",
        "workId": "88",
        "workAnswerId": "99",
    }
    assert "secret" not in str(result)


def test_learning_homework_attempt_history_uses_observed_select_times_route(
    monkeypatch,
) -> None:
    list_html = """
    <ul><li onclick="goTask(this);"
      data="https://mooc1.chaoxing.com/mooc-ans/mooc2/work/task?workId=88&amp;answerId=99&amp;enc=secret"
      aria-label="BOPPPS 设计 ; 未交">
      <p class="overHidden2 fl">BOPPPS 设计</p><p class="status fl">未交</p>
    </li></ul>
    """
    detail_html = """
    <input type="hidden" id="courseId" value="10">
    <input type="hidden" id="classId" value="20">
    <input type="hidden" id="workId" value="88">
    <input type="hidden" id="answerId" value="99">
    <h2 class="mark_title">BOPPPS 设计</h2>
    """
    history_html = """
    <div class="recordTab">
      <a onclick="showAnswer(1)">第 1 次作答 80 分</a>
      <a onclick="showAnswer('2')">第 2 次作答 90 分</a>
    </div>
    <script>
      function showAnswer(times) {
        window.open('/mooc2/work/view?answerId=99&enc=secret&selectTimes=' + times);
      }
    </script>
    """
    attempt_html = """
    <input type="hidden" id="courseId" value="10">
    <input type="hidden" id="classId" value="20">
    <input type="hidden" id="workId" value="88">
    <input type="hidden" id="answerId" value="99">
    <h2 class="mark_title">BOPPPS 设计</h2>
    <div class="mark_item"><h2 class="type_tit">一. 简答题（共1题，100分）</h2>
      <div class="questionLi" id="question1" data="1">
        <h3 class="mark_name">1. <span class="colorShallow">(简答题)</span>
          <span class="qtContent">说明课堂导入。</span>
        </h3>
        <dd class="stuAnswerContent">第二次历史答案</dd>
      </div>
    </div>
    """

    class Response:
        headers = {"Content-Type": "text/html;charset=UTF-8"}
        encoding = "utf-8"
        apparent_encoding = "utf-8"
        status_code = 200

        def __init__(self, url: str, html: str) -> None:
            self.url = url
            self.content = html.encode("utf-8")

        @staticmethod
        def raise_for_status() -> None:
            return None

    class Session:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict]] = []

        def get(self, url: str, **kwargs) -> Response:
            self.calls.append((url, kwargs))
            if url.endswith("/mooc-ans/mooc2/work/answer-list"):
                return Response(url, history_html)
            if url.endswith("/mooc-ans/mooc2/work/view"):
                assert kwargs["params"]["selectTimes"] == "2"
                return Response(url + "?selectTimes=2&enc=secret", attempt_html)
            return Response(
                "https://mooc1.chaoxing.com/mooc-ans/mooc2/work/view?enc=secret",
                detail_html,
            )

    session = Session()
    page = type(
        "Page",
        (),
        {"url": "https://mooc2-ans.chaoxing.com/mooc2-ans/mycourse/stu?courseid=10"},
    )()
    api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        api,
        "_learning_module_response",
        lambda _course, _module: {
            "session": session,
            "response": page,
            "html": list_html,
        },
    )
    course = {
        "course_id": "10",
        "course_name": "Writing",
        "clazz_id": "20",
        "cpi": "30",
    }

    history = api.list_learning_homework_attempts(course, "BOPPPS 设计")
    attempt = api.read_learning_homework_attempt(course, "BOPPPS 设计", "2")

    assert history["attempt_count"] == 2
    assert history["history_available"] is True
    assert history["attempts"][0]["attempt_id"] == "1"
    assert history["state_unchanged"] is True
    assert history["page"]["path"] == "/mooc-ans/mooc2/work/answer-list"
    assert attempt["attempt"]["attempt_id"] == "2"
    assert attempt["questions"][0]["student_answer"] == "第二次历史答案"
    assert attempt["state_unchanged"] is True
    assert attempt["page"]["path"] == "/mooc-ans/mooc2/work/view"
    assert "secret" not in str(history)
    assert "secret" not in str(attempt)


def test_parse_learning_materials_wrong_questions_activities_and_records() -> None:
    materials = parse_learning_materials(
        """
        <ul class="dataBody_td" id="10" dataName="Week 1" type="afolder"
            isdown="1" isOpen="0" source="1" order="10">
          <li class="dataBody_size_stu">-</li>
          <li class="dataBody_creater_stu"><span>教师甲</span></li>
        </ul>
        <ul class="dataBody_td" id="11" dataName="Guide.pdf" type="pdf"
            isdown="0" isOpen="1" objectId="object-1"
            url="https://example.test/view?pEnc=secret">
          <li class="dataBody_size_stu">2 MB</li>
          <li class="dataBody_creater_stu">教师乙</li>
        </ul>
        """
    )
    assert materials[0]["is_folder"] is True
    assert materials[1]["size"] == "2 MB"
    assert resolve_learning_material(materials, "Week 1", folders_only=True)["data_id"] == "10"
    assert "secret" not in str(materials)

    wrong = parse_learning_wrong_question_summary(
        """
        <input type="hidden" id="groupCount" value="3">
        <input type="hidden" id="lastExamId" value="42">
        <input type="hidden" id="showSelfTest" value="1">
        <input type="hidden" id="queType" value="-1">
        <input type="hidden" id="topicArr" value="7,8">
        """
    )
    assert wrong["has_wrong_questions"] is True
    assert wrong["selected_topic_ids"] == ["7", "8"]

    activity = normalize_learning_activity(
        {
            "id": 5001,
            "nameOne": "课堂讨论",
            "activeType": 5,
            "status": 2,
            "userStatus": 1,
            "extraInfo": {"topicId": "99", "token": "secret"},
        },
        source="class_activity",
    )
    assert activity["name"] == "课堂讨论"
    assert activity["status_label"] == "ended"
    assert activity["metadata"] == {"topicId": "99"}

    records = normalize_learning_record_sections(
        {
            "job": {"data": {"job": 2, "publishJobNum": 4, "jobPer": 50}},
            "work": {"data": {"finishCount": 1, "receivedNum": 2, "finishPer": 50}},
            "score": {
                "data": {
                    "showScore": True,
                    "score": {"score": "85", "userName": "不应返回", "loginName": "secret"},
                    "weightList": [{"name": "章节任务点", "value": 80}],
                }
            },
            "attendance": {"allCount": 3, "attendanceCount": 3, "signPer": 100},
        },
        {"examFinishNum": "1", "examPublishNum": "2"},
    )
    assert records["chapter_tasks"]["completion_percent"] == 50
    assert records["course_exams"] == {"completed": 1, "assigned": 2}
    assert records["score"]["overall"] == "85"
    assert "不应返回" not in str(records) and "secret" not in str(records)

    malformed_counts = normalize_learning_record_sections(
        {}, {"examFinishNum": "--", "examPublishNum": None}
    )
    assert malformed_counts["course_exams"] == {"completed": 0, "assigned": 0}


def test_learning_discussion_class_search_filters_locally(monkeypatch) -> None:
    class Response:
        url = "https://groupweb.chaoxing.com/course/topic/bbs-1/getTopicList"
        status_code = 200
        headers = {"Content-Type": "application/json"}
        encoding = "utf-8"
        apparent_encoding = "utf-8"

        def __init__(self, payload: dict) -> None:
            self.content = json.dumps(payload, ensure_ascii=False).encode()

        @staticmethod
        def raise_for_status() -> None:
            return None

    class Session:
        def __init__(self) -> None:
            self.params: list[dict] = []

        def post(self, _url: str, *, params: dict, **_kwargs) -> Response:
            self.params.append(params)
            return Response(
                {
                    "status": True,
                    "datas": [
                        {"id": 1, "uuid": "a", "title": "Environmental issue"},
                        {"id": 2, "uuid": "b", "title": "Writing process"},
                    ],
                    "folder_list": [],
                    "poff": {"lastPage": True},
                }
            )

    session = Session()
    api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        api,
        "_learning_module_response",
        lambda _course, _module: {
            "session": session,
            "course_context": {"values": {"bbsid": "bbs-1"}},
            "response": type("Page", (), {"url": "https://groupweb.chaoxing.com/course"})(),
        },
    )
    course = {
        "course_id": "10",
        "course_name": "Writing",
        "clazz_id": "20",
    }

    result = api.list_learning_discussions(
        course,
        search="environmental",
        class_only=True,
    )

    assert session.params[0]["kw"] == ""
    assert session.params[0]["searchType"] == "4"
    assert [topic["title"] for topic in result["topics"]] == ["Environmental issue"]


def test_learning_knowledge_graph_reads_hide_bootstrap_tokens(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    course = {
        "course_id": "254641935",
        "course_name": "英语文体与写作",
        "clazz_id": "125867890",
        "cpi": "485781386",
    }
    context = {
        "session": object(),
        "common": {
            "courseid": course["course_id"],
            "clazzid": course["clazz_id"],
            "cpi": course["cpi"],
            "ut": "s",
            "enc": "secret-bootstrap-token",
        },
        "referer": "https://example.test/graph?enc=secret-bootstrap-token",
    }
    config = {
        "status": True,
        "dataJson": {
            "exportCourseTopicEnc": "secret-export-token",
            "relationTypeDesc": [
                {
                    "relationDescId": "1",
                    "relationDescName": "父子",
                    "bootstrapToken": "secret-relation-token",
                }
            ],
        },
        "topicClassifyArray": [],
        "graphLabelShow": [],
        "showSetData": {},
    }
    raw_graph = {
        "status": True,
        "nodes": [
            {"id": "courseid-1", "name": "课程", "bootstrap": "secret-node-token"},
            {"id": "101", "topicid": "101", "name": "Punctuation"},
        ],
        "links": [
            {
                "source": "courseid-1",
                "target": "101",
                "type": 1,
                "token": "secret-link-token",
            }
        ],
    }
    model_settings = {
        "topicModelData": [
            {
                "id": "458578",
                "name": "知识图谱",
                "modeType": 1,
                "bootstrap": "secret-model-token",
            }
        ]
    }
    monkeypatch.setattr(api, "_learning_knowledge_graph_context", lambda _course: context)
    monkeypatch.setattr(api, "_knowledge_graph_config_data", lambda _context: config)
    monkeypatch.setattr(api, "_knowledge_graph_raw_data", lambda _context: raw_graph)
    monkeypatch.setattr(
        api,
        "_knowledge_graph_topic_setting_data",
        lambda _context: model_settings,
    )
    monkeypatch.setattr(
        api,
        "_knowledge_graph_json_request",
        lambda *_args, **_kwargs: {
            "status": True,
            "data": {
                "id": "root",
                "name": "课程",
                "token": "secret-model-data-token",
                "children": [{"topicId": "101", "name": "Punctuation"}],
            },
        },
    )

    graph = api.list_learning_knowledge_graph(course)
    node = api.read_learning_knowledge_graph_node(course, "Punctuation")
    models = api.list_learning_knowledge_graph_models(course)
    model = api.read_learning_knowledge_graph_model(course, "知识图谱")

    assert graph["total_count"] == 2 and graph["relation_count"] == 1
    assert node["node"]["node_id"] == "101"
    assert models["models"][0]["model_id"] == "458578"
    assert model["count"] == 2
    assert "raw" not in graph["nodes"][0]
    assert "secret" not in str((graph, node, models, model))


def test_resolve_class_defaults_to_first() -> None:
    course = parse_teaching_courses(sample_payload())[0]
    assert resolve_class(course)["clazz_id"] == "800000001"
    assert resolve_class(course, "英日2301-2302")["student_count"] == 61


def test_parse_class_settings_preserves_switches_and_semesters() -> None:
    html = """
    <input id="clazzState" value="0">
    <input onclick="updateEnableInvitecode(this)" checked="true">
    <input onclick="updateIntoClazzValidation(this)" checked>
    <input onclick="updateOnlyBindUnitStudent(this)" checked>
    <input onclick="updateOnlyCourseUnitStudent(this)">
    <input onclick="changeisretire(this)" checked>
    <input id="setClassApply" onclick="updateispublic(this)" checked>
    <input id="networkopenId" checked>
    <input id="applyStartTime" value="2026-09-01 08:00">
    <input id="applyEndTime" value="2026-09-30 18:00">
    <input id="selectTerm" value="2026-2027第一学期">
    <span id="classLimit" stunum="120">120</span>
    <input id="registDate" value="2026-09-01 08:00">
    <input id="endTime" value="2027-01-15 18:00">
    <input onclick="ignoreVideoCtrl(this)" checked>
    <input onclick="hideClazz(this)">
    <script>selectTerm([{"texts":"2026-2027第一学期","id":47178}]);</script>
    """
    settings = parse_class_settings(html)
    assert settings["allow_student_join"] is True
    assert settings["join_requires_approval"] is True
    assert settings["unit_binding_requirement"] == "any_unit"
    assert settings["public_scope"] == "network"
    assert settings["student_limit"] == 120
    assert settings["ignore_video_restrictions"] is True
    assert settings["hidden_from_students"] is False
    assert settings["available_semesters"][0]["semester_id"] == "47178"


def test_parse_and_resolve_student_bank_candidates() -> None:
    html = """
    <input type="hidden" id="searchStuCount" value="1">
    <ul class="tabBody_td">
      <li class="tab-check" data-personid="410512079" data-enc="token">
        <input type="checkbox">
      </li>
      <li class="li_name"><p>杨子昂</p></li>
      <li><p>2024000273</p></li>
      <li>否</li>
      <li><p>1917641</p></li>
      <li><p>10956843</p></li>
      <li><p>吉林外国语大学</p></li>
    </ul>
    """
    candidates, total = parse_student_bank_candidates(html)
    assert total == 1
    assert candidates[0]["student_name"] == "杨子昂"
    assert candidates[0]["student_no"] == "2024000273"
    assert candidates[0]["at_school"] is False
    assert candidates[0]["organization_values"] == ["1917641", "10956843"]
    assert resolve_student_bank_candidate(candidates, "2024000273")["person_id"] == "410512079"


def test_parse_and_resolve_class_join_applications() -> None:
    html = """
    <input type="hidden" id="codeaddstuApplyCount" value="1">
    <ul class="dataBody_codeapply_td" data="99123">
      <li><input type="checkbox"></li>
      <li>李华</li>
      <li>2024001234</li>
      <li>英语学院</li>
      <li>2026-08-31 09:30</li>
      <li><a class="allowAdopt">通过</a><a class="prohibitAdopt">拒绝</a></li>
    </ul>
    """
    applications, total = parse_class_join_applications(html)
    assert total == 1
    assert applications[0]["log_id"] == "99123"
    assert applications[0]["student_name"] == "李华"
    assert applications[0]["student_no"] == "2024001234"
    assert applications[0]["applied_at"] == "2026-08-31 09:30"
    assert resolve_class_join_application(applications, "99123")["student_name"] == "李华"


def test_parse_teacher_nav_and_resolve_visible_title() -> None:
    html = """
    <ul>
      <li dataname="zy" pageHeader="6" data="42161" openType="0">
        <a title="作业" data-url="/mooc2-ans/work/list">作业 <em>NEW</em></a>
      </li>
    </ul>
    """
    modules = parse_teacher_nav_items(html)
    assert modules[0]["module"] == "zy"
    assert modules[0]["title"] == "作业"
    assert resolve_module(modules, "作业")["data_url"] == "/mooc2-ans/work/list"


def test_parse_and_resolve_personal_space_modules() -> None:
    html = """
    <div role="menuitem" level="1" name="笔记" id="first901261"
         dataurl="https://groupyd2.chaoxing.com/pc/activity/activityList">
      <span></span><h3 title="笔记">笔记</h3>
    </div>
    <div role="menuitem" level="1" name="课程大纲管理" id="first197497"
         dataurl=""><h3 title="课程大纲管理">课程大纲管理</h3></div>
    <div role="menuitem" level="2" name="子项" id="second1"
         dataurl="https://example.com/child"><h3>子项</h3></div>
    """
    modules = parse_personal_space_modules(html)
    assert len(modules) == 2
    assert modules[0]["app_id"] == "901261"
    assert modules[0]["available"] is True
    assert modules[1]["available"] is False
    assert resolve_personal_space_module(modules, "笔记")["app_id"] == "901261"
    assert resolve_personal_space_module(modules, "2")["label"] == "课程大纲管理"


def test_parse_note_detail_html_extracts_embedded_json_object() -> None:
    html = """
    <script>
      window.page = {note:{"cid":"note-1","title":"标题","content":"正文",
        "userAuth":{"operationAuth":{"update":1,"delete":1}}},
        user:{"uid":12,"puid":34},other:true};
    </script>
    """
    note = parse_note_detail_html(html)
    assert note["cid"] == "note-1"
    assert note["title"] == "标题"
    assert note["userAuth"]["operationAuth"]["delete"] == 1
    assert parse_note_detail_user(html)["puid"] == 34


def test_personal_note_list_create_update_and_delete_contracts(monkeypatch) -> None:
    raw_note = {
        "cid": "note-1",
        "title": "原题",
        "content": "原文",
        "rtf_content": "<p>原文</p>",
        "openedState": 0,
        "category": 0,
        "notebookCid": "root",
        "attachment": [],
        "imgs": [],
        "userAuth": {"operationAuth": {"update": 1, "delete": 1}},
    }

    list_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(list_api, "_session", object)
    pages = iter(
        [
            {
                "result": 1,
                "data": {
                    "list": [{"type": 2, "note": raw_note}, {"type": 1}],
                    "index_Id": "cursor-1",
                    "index_updateTime": 100,
                },
            },
            {
                "result": 1,
                "data": {"list": [], "index_Id": "", "index_updateTime": -1},
            },
        ]
    )
    monkeypatch.setattr(list_api, "_note_json_request", lambda *args, **kwargs: next(pages))
    listed = list_api.list_notes()
    assert listed["count"] == 1
    assert listed["notes"][0]["visibility"] == "private"
    assert listed["notes"][0]["can_delete"] is True

    create_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(create_api, "_session", object)
    written: list[dict] = []

    def record_write(*args, **kwargs):
        written.append(kwargs)
        return {"result": 1, "msg": "ok"}

    monkeypatch.setattr(create_api, "_write_note", record_write)
    monkeypatch.setattr(
        create_api,
        "_read_note_by_cid",
        lambda session, cid: {**raw_note, "cid": cid, "title": "新题", "content": "第一行\n第二行"},
    )
    created = create_api.create_note("新题", "第一行\n第二行")
    assert created["note"]["title"] == "新题"
    assert written[0]["content_html"] == "<p>第一行<br>第二行</p>"
    assert written[0]["notebook_cid"] == "root"

    update_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(update_api, "_session", object)
    monkeypatch.setattr(
        update_api,
        "list_notes",
        lambda **kwargs: {"notes": [update_api._normalize_note(raw_note, 1)]},
    )
    details = iter(
        [raw_note, {**raw_note, "title": "新题", "content": "新文", "rtf_content": "<p>新文</p>"}]
    )
    monkeypatch.setattr(update_api, "_read_note_by_cid", lambda *args: next(details))
    update_calls: list[dict] = []
    monkeypatch.setattr(
        update_api,
        "_write_note",
        lambda *args, **kwargs: update_calls.append(kwargs) or {"result": 1},
    )
    updated = update_api.update_note("note-1", title="新题", content="新文")
    assert updated["note"]["title"] == "新题"
    assert update_calls[0]["editing"] is True

    delete_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(delete_api, "_session", object)
    note_lists = iter(
        [
            {"notes": [delete_api._normalize_note(raw_note, 1)]},
            {"notes": []},
        ]
    )
    monkeypatch.setattr(delete_api, "list_notes", lambda **kwargs: next(note_lists))
    monkeypatch.setattr(delete_api, "_read_note_by_cid", lambda *args: raw_note)
    monkeypatch.setattr(
        delete_api,
        "_note_json_request",
        lambda *args, **kwargs: {"result": 1, "msg": "ok"},
    )
    deleted = delete_api.delete_note("note-1")
    assert deleted["deleted"]["note_cid"] == "note-1"


def test_personal_inbox_list_read_and_state_contracts(monkeypatch) -> None:
    raw_notice = {
        "idCode": "notice-1",
        "uuid": "$CACG$notice-uuid",
        "title": "系统通知",
        "content": "正文",
        "createrName": "系统",
        "sendTag": 0,
        "isread": 0,
        "redDot": 0,
        "collect": 0,
        "top": 0,
        "status": 0,
        "sourceType": 0,
        "count_read": 2,
        "count_all": 3,
    }
    landing = type("Landing", (), {"url": "https://notice.chaoxing.com/pc/notice/myNotice"})()

    list_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        list_api,
        "_personal_space_module_context",
        lambda module: (object(), landing, {"label": module}),
    )
    list_calls: list[dict] = []

    def list_request(*args, **kwargs):
        list_calls.append(kwargs)
        return {
            "status": True,
            "folders": [
                {
                    "uuid": "folder-1",
                    "folderName": "重要",
                    "top": 1,
                    "noReadCount": 2,
                }
            ],
            "topNotices": [],
            "notices": {"list": [raw_notice], "lastGetId": "cursor", "lastPage": 1},
        }

    monkeypatch.setattr(list_api, "_inbox_json_request", list_request)
    listed = list_api.list_inbox_notices(search="系统", max_items=10)
    assert listed["count"] == 1
    assert listed["notices"][0]["is_read"] is False
    assert listed["folders"][0]["unread_count"] == 2
    assert list_calls[0]["data"]["type"] == "2"
    assert list_calls[0]["data"]["kw"] == "系统"

    selected = listed["notices"][0]
    read_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(read_api, "_find_inbox_notice", lambda *args: selected)
    monkeypatch.setattr(
        read_api,
        "_personal_space_module_context",
        lambda module: (object(), landing, {"label": module}),
    )
    monkeypatch.setattr(
        read_api,
        "_inbox_json_request",
        lambda *args, **kwargs: {"status": True, "msg": raw_notice},
    )
    detailed = read_api.read_inbox_notice("notice-1")
    assert detailed["notice"]["content"] == "正文"
    assert detailed["notice"]["is_read"] is True

    unread_api = ChaoxingAPI(Path("unused-cookies.json"))
    unread_selected = {**selected, "is_read": True, "can_mark_unread": True}
    unread_refreshed = {**selected, "is_read": False, "can_mark_unread": False}
    unread_resolutions = iter([unread_selected, unread_refreshed])
    monkeypatch.setattr(unread_api, "_find_inbox_notice", lambda *args: next(unread_resolutions))
    monkeypatch.setattr(
        unread_api,
        "_personal_space_module_context",
        lambda module: (object(), landing, {"label": module}),
    )
    unread_calls: list[dict] = []
    monkeypatch.setattr(
        unread_api,
        "_inbox_json_request",
        lambda *args, **kwargs: unread_calls.append(kwargs) or {"status": True, "count_read": 2},
    )
    unread = unread_api.mark_inbox_notice_unread("notice-1")
    assert unread["notice"]["is_read"] is False
    assert unread_calls[0]["data"] == {"noticeId": "notice-1"}

    for method_name, state_key, requested_key in (
        ("set_inbox_notice_top_status", "is_top", "top"),
        ("set_inbox_notice_collect_status", "is_collected", "collect"),
    ):
        state_api = ChaoxingAPI(Path("unused-cookies.json"))
        resolutions = iter([selected, {**selected, state_key: True}])
        monkeypatch.setattr(
            state_api,
            "_find_inbox_notice",
            lambda *args, values=resolutions: next(values),
        )
        monkeypatch.setattr(
            state_api,
            "_personal_space_module_context",
            lambda module: (object(), landing, {"label": module}),
        )
        mutation_calls: list[dict] = []
        monkeypatch.setattr(
            state_api,
            "_inbox_json_request",
            lambda *args, calls=mutation_calls, **kwargs: calls.append(kwargs) or {"status": True},
        )
        result = getattr(state_api, method_name)("notice-1", True)
        assert result["notice"][state_key] is True
        if "data" in mutation_calls[0]:
            assert mutation_calls[0]["data"][requested_key] == 1
        else:
            assert mutation_calls[0]["params"][requested_key] == 1

    delete_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(delete_api, "_find_inbox_notice", lambda *args: selected)
    monkeypatch.setattr(
        delete_api,
        "_personal_space_module_context",
        lambda module: (object(), landing, {"label": module}),
    )
    delete_calls: list[dict] = []
    monkeypatch.setattr(
        delete_api,
        "_inbox_json_request",
        lambda *args, **kwargs: delete_calls.append(kwargs) or {"status": True},
    )
    monkeypatch.setattr(delete_api, "list_inbox_notices", lambda **kwargs: {"notices": []})
    monkeypatch.setattr(
        delete_api,
        "list_inbox_recycle",
        lambda **kwargs: {"notices": [selected]},
    )
    deleted_notice = delete_api.delete_inbox_notice("notice-1")
    assert deleted_notice["deleted"]["notice_id"] == "notice-1"
    assert deleted_notice["recycled_notice"]["notice_id"] == "notice-1"
    assert delete_calls[0]["data"]["sendTag"] == 0


def test_parse_personal_notice_compose_context() -> None:
    parsed = parse_personal_notice_compose_context(
        """
        <script>
        window.authUser = {info:{"fid":23080,"uid":356823822,"puid":405017213,
            "name":"张三","pic":"https://photo.example/self.jpg"}};
        window.myFunDepts = [{"creatorId":405017213,"name":"张三","checked":1}];
        window.uuidTemp = "$CACG$compose-1";
        window.uuidEncTemp = "uuid-enc";
        window.sourceType = '0';
        window.isRtf = '1';
        window.operationType = 'add';
        window.oType = '';
        window.oId = '';
        window.oEnc = '';
        window.oCustomParams = '';
        window.foldCode = '';
        window.tag = '';
        window.tagEnc = '';
        window.fidsCode = '';
        </script>
        """
    )
    assert parsed["user"]["puid"] == 405017213
    assert parsed["issuing_puid"] == "405017213"
    assert parsed["uuid"] == "$CACG$compose-1"
    assert parsed["is_rich_text"] is True


def test_personal_notice_send_and_draft_http_contracts(monkeypatch) -> None:
    api = ChaoxingAPI(Path("cookies.json"))
    editor = {
        "session": object(),
        "landing_url": "https://notice.chaoxing.com/pc/notice/myNotice",
        "editor_url": "https://notice.chaoxing.com/pc/notice/richtextNotice?sourceType=0",
        "user": {
            "puid": "405017213",
            "user_id": "356823822",
            "fid": "23080",
            "name": "张三",
            "picture_url": "https://photo.example/self.jpg",
        },
        "issuing_puid": "405017213",
        "uuid": "$CACG$compose-1",
        "uuid_enc": "",
        "original_type": "",
        "original_id": "",
        "original_encoding": "",
        "original_custom_parameters": "",
        "folder_id": "",
        "tag": "",
        "tag_encoding": "",
        "fid_codes": "",
    }
    monkeypatch.setattr(api, "_personal_notice_editor_context", lambda **kwargs: editor)
    people = [
        {
            "puid": "405017213",
            "name": "张三",
            "picture_url": "https://photo.example/self.jpg",
        }
    ]
    monkeypatch.setattr(api, "_resolve_personal_notice_people", lambda *args: people)
    requests: list[dict] = []

    def inbox_request(*args, **kwargs):
        requests.append(kwargs)
        return {"status": True, "msg": {"idCode": "sent-1", "id": "draft-1"}}

    monkeypatch.setattr(api, "_inbox_json_request", inbox_request)
    sent = {
        "notice_id": "sent-1",
        "uuid": "$CACG$sent-1",
        "index": 1,
        "title": "仅本人验证",
    }

    def inbox_list(*, scope, **kwargs):
        notice = dict(sent)
        notice["scope"] = scope
        return {"notices": [notice]}

    monkeypatch.setattr(api, "list_inbox_notices", inbox_list)
    result = api.send_personal_notice(
        ["本人"],
        "仅本人验证",
        "正文",
        hide_read_status=True,
        forbid_forwarding=True,
        permission_password="permission-code",
    )
    sent_payload = requests[-1]["data"]
    assert sent_payload["puids"] == "405017213"
    assert sent_payload["passportId"] == "405017213"
    assert sent_payload["issuingPuid"] == "405017213"
    assert sent_payload["showRead"] == "2"
    assert sent_payload["visible"] == "1"
    assert sent_payload["pcode"] == "permission-code"
    assert json.loads(sent_payload["orderlyReceive"])[0]["puid"] == "405017213"
    assert result["notice"]["notice_id"] == "sent-1"
    assert result["self_received_notice"] is not None

    personal_draft = {
        "draft_id": "draft-1",
        "draft_uuid": "draft-uuid-1",
        "version": 1,
        "title": "个人草稿",
        "content": "草稿正文",
        "source_type": 0,
        "operation": "add",
        "recipients": [],
        "notice_id": "",
        "notice_uuid": "$CACG$compose-1",
    }
    monkeypatch.setattr(
        api,
        "list_personal_notice_drafts",
        lambda **kwargs: {"drafts": [personal_draft]},
    )
    draft_result = api.save_personal_notice_draft("个人草稿", "草稿正文")
    draft_payload = requests[-1]["data"]
    assert draft_payload["source_type"] == "0"
    assert draft_payload["puids"] == ""
    assert draft_payload["rtf_content"] == "<p>草稿正文</p>"
    assert draft_result["draft"]["draft_id"] == "draft-1"


def test_personal_notice_draft_list_filters_course_drafts(monkeypatch) -> None:
    api = ChaoxingAPI(Path("cookies.json"))
    landing = type("Landing", (), {"url": "https://notice.chaoxing.com/pc/notice/myNotice"})()
    monkeypatch.setattr(
        api,
        "_personal_space_module_context",
        lambda *args: (object(), landing, {}),
    )
    monkeypatch.setattr(
        api,
        "_inbox_json_request",
        lambda *args, **kwargs: {
            "status": True,
            "draftList": [
                {
                    "id": 1,
                    "uuid": "personal-1",
                    "title": "个人草稿",
                    "content": "A",
                    "sourceType": 0,
                },
                {
                    "id": 2,
                    "uuid": "course-1",
                    "title": "课程草稿",
                    "content": "B",
                    "sourceType": 14,
                },
            ],
            "pagesOffset": {"lastPage": 1, "lastValue": ""},
        },
    )
    result = api.list_personal_notice_drafts()
    assert result["count"] == 1
    assert result["drafts"][0]["title"] == "个人草稿"


def test_personal_inbox_folder_http_contracts(monkeypatch) -> None:
    landing = type("Landing", (), {"url": "https://notice.chaoxing.com/pc/notice/myNotice"})()
    raw_folder = {
        "uuid": "folder-1",
        "folderName": "重要",
        "top": 0,
        "order": 2,
        "noticeCount": 3,
        "noReadCount": 1,
    }
    normalized_folder = ChaoxingAPI._normalize_inbox_folder(raw_folder, 1)

    list_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        list_api,
        "_personal_space_module_context",
        lambda *args: (object(), landing, {}),
    )
    list_calls: list[dict] = []
    monkeypatch.setattr(
        list_api,
        "_inbox_json_request",
        lambda *args, **kwargs: list_calls.append(kwargs) or {"status": True, "msg": [raw_folder]},
    )
    listed = list_api.list_inbox_folders()
    assert listed["folders"][0]["folder_uuid"] == "folder-1"
    assert listed["folders"][0]["notice_count"] == 3
    assert list_calls[0]["data"] == {}

    read_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(read_api, "_find_inbox_folder", lambda *args: normalized_folder)
    monkeypatch.setattr(
        read_api,
        "_personal_space_module_context",
        lambda *args: (object(), landing, {}),
    )
    monkeypatch.setattr(
        read_api,
        "_inbox_json_request",
        lambda *args, **kwargs: {
            "status": True,
            "folderName": "重要",
            "filters": [{"id": "filter-1", "dataId": "405017213", "type": 1, "name": "本人"}],
            "keywordRules": json.dumps(
                {"keyword": [{"keyword": "课程", "logic": 0, "type": 0}]},
                ensure_ascii=False,
            ),
            "keywordId": "keyword-filter-1",
        },
    )
    filters = read_api.read_inbox_folder_filters("重要")
    assert filters["sender_rules"][0]["data_id"] == "405017213"
    assert filters["keyword_rules"][0]["keyword"] == "课程"

    create_api = ChaoxingAPI(Path("unused-cookies.json"))
    folder_lists = iter([{"folders": []}, {"folders": [normalized_folder]}])
    monkeypatch.setattr(create_api, "list_inbox_folders", lambda: next(folder_lists))
    monkeypatch.setattr(
        create_api,
        "_personal_space_module_context",
        lambda *args: (object(), landing, {}),
    )
    create_calls: list[dict] = []
    monkeypatch.setattr(
        create_api,
        "_inbox_json_request",
        lambda *args, **kwargs: create_calls.append(kwargs) or {"status": True, "msg": raw_folder},
    )
    monkeypatch.setattr(
        create_api,
        "read_inbox_folder_filters",
        lambda *args: {"folder": normalized_folder, "sender_rules": [], "keyword_rules": []},
    )
    created = create_api.create_inbox_folder(
        "重要",
        sender_rules=[{"puid": "405017213", "name": "本人", "type": "person"}],
        keywords=[{"keyword": "课程", "logic": "and", "type": "contains"}],
    )
    create_payload = create_calls[0]["data"]
    assert json.loads(create_payload["rules"])[0]["dataId"] == "405017213"
    assert json.loads(create_payload["keywordRule"])["keyword"][0]["keyword"] == "课程"
    assert created["folder"]["folder_uuid"] == "folder-1"

    before_filters = {
        "folder": normalized_folder,
        "sender_rules": [
            {
                "filter_id": "filter-1",
                "data_id": "405017213",
                "type": 1,
                "name": "本人",
            }
        ],
        "keyword_rules": [{"keyword": "课程", "logic": 0, "type": 0}],
        "keyword_filter_id": "keyword-filter-1",
    }
    after_filters = {
        **before_filters,
        "folder": {**normalized_folder, "name": "待办"},
    }
    update_api = ChaoxingAPI(Path("unused-cookies.json"))
    reads = iter([before_filters, after_filters])
    monkeypatch.setattr(update_api, "read_inbox_folder_filters", lambda *args: next(reads))
    monkeypatch.setattr(
        update_api,
        "_personal_space_module_context",
        lambda *args: (object(), landing, {}),
    )
    update_calls: list[dict] = []
    monkeypatch.setattr(
        update_api,
        "_inbox_json_request",
        lambda *args, **kwargs: update_calls.append(kwargs) or {"status": True},
    )
    updated = update_api.update_inbox_folder("重要", name="待办")
    assert updated["after"]["folder"]["name"] == "待办"
    assert update_calls[0]["params"]["rules"] == "[]"
    assert json.loads(update_calls[0]["params"]["keywordRule"])["keyword"][0]["keyword"] == "课程"

    delete_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(delete_api, "_find_inbox_folder", lambda *args: normalized_folder)
    monkeypatch.setattr(delete_api, "list_inbox_folders", lambda: {"folders": []})
    monkeypatch.setattr(
        delete_api,
        "_personal_space_module_context",
        lambda *args: (object(), landing, {}),
    )
    delete_calls: list[dict] = []
    monkeypatch.setattr(
        delete_api,
        "_inbox_json_request",
        lambda *args, **kwargs: delete_calls.append(kwargs) or {"status": True},
    )
    deleted = delete_api.delete_inbox_folder("重要")
    assert deleted["deleted"]["folder_uuid"] == "folder-1"
    assert delete_calls[0]["data"]["folder_uuids"] == "folder-1"


def test_personal_inbox_folder_reorder_and_notice_move_contracts(monkeypatch) -> None:
    landing = type("Landing", (), {"url": "https://notice.chaoxing.com/pc/notice/myNotice"})()
    first = ChaoxingAPI._normalize_inbox_folder(
        {"uuid": "folder-1", "folderName": "重要", "top": 0}, 1
    )
    second = ChaoxingAPI._normalize_inbox_folder(
        {"uuid": "folder-2", "folderName": "待办", "top": 0}, 2
    )
    reorder_api = ChaoxingAPI(Path("unused-cookies.json"))
    folder_reads = iter([{"folders": [first, second]}, {"folders": [second, first]}])
    monkeypatch.setattr(reorder_api, "list_inbox_folders", lambda: next(folder_reads))
    monkeypatch.setattr(
        reorder_api,
        "_personal_space_module_context",
        lambda *args: (object(), landing, {}),
    )
    reorder_calls: list[dict] = []
    monkeypatch.setattr(
        reorder_api,
        "_inbox_json_request",
        lambda *args, **kwargs: reorder_calls.append(kwargs) or {"status": True},
    )
    reordered = reorder_api.reorder_inbox_folders(["待办", "重要"])
    assert [folder["name"] for folder in reordered["folders"]] == ["待办", "重要"]
    order_payload = json.loads(reorder_calls[0]["data"]["folderOrders"])
    assert order_payload["default"][0] == {"uuid": "folder-2", "order": 2}

    notice = {
        "notice_id": "notice-1",
        "uuid": "$CACG$notice-1",
        "title": "课程通知",
        "scope": "received",
        "send_tag": 0,
        "folder_uuid": "",
    }
    move_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(move_api, "list_inbox_folders", lambda: {"folders": [first]})
    moved = False

    def list_notices(*, folder_uuid="", **kwargs):
        if folder_uuid == "":
            return {"notices": [] if moved else [notice]}
        return {"notices": [{**notice, "folder_uuid": "folder-1"}] if moved else []}

    monkeypatch.setattr(move_api, "list_inbox_notices", list_notices)
    monkeypatch.setattr(
        move_api,
        "_personal_space_module_context",
        lambda *args: (object(), landing, {}),
    )
    move_calls: list[dict] = []

    def move_request(*args, **kwargs):
        nonlocal moved
        moved = True
        move_calls.append(kwargs)
        return {"status": True}

    monkeypatch.setattr(move_api, "_inbox_json_request", move_request)
    result = move_api.move_inbox_notices(["课程通知"], "重要")
    assert result["destination"]["folder_uuid"] == "folder-1"
    assert move_calls[0]["data"] == {"noticeIds": "notice-1", "folder_uuid": "folder-1"}


def test_personal_inbox_recycle_http_contracts(monkeypatch) -> None:
    landing = type("Landing", (), {"url": "https://notice.chaoxing.com/pc/notice/myNotice"})()
    raw_notice = {
        "idCode": "notice-1",
        "uuid": "$CACG$notice-1",
        "title": "已删除通知",
        "content": "正文",
        "sendTag": 0,
        "isread": 1,
        "deleteTime": "2026-09-01 10:00:00",
    }
    list_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        list_api,
        "_personal_space_module_context",
        lambda *args: (object(), landing, {}),
    )
    list_calls: list[dict] = []
    monkeypatch.setattr(
        list_api,
        "_inbox_json_request",
        lambda *args, **kwargs: (
            list_calls.append(kwargs) or {"status": True, "list": [raw_notice], "lastPage": 1}
        ),
    )
    listed = list_api.list_inbox_recycle(search="已删除")
    recycled_notice = listed["notices"][0]
    assert recycled_notice["notice_id"] == "notice-1"
    assert recycled_notice["deleted_at"] == "2026-09-01 10:00:00"
    assert list_calls[0]["data"]["kw"] == quote("已删除", safe="")

    restore_api = ChaoxingAPI(Path("unused-cookies.json"))
    recycle_reads = iter([{"notices": [recycled_notice]}, {"notices": []}])
    monkeypatch.setattr(restore_api, "list_inbox_recycle", lambda **kwargs: next(recycle_reads))
    monkeypatch.setattr(
        restore_api,
        "list_inbox_notices",
        lambda **kwargs: {"notices": [recycled_notice]},
    )
    monkeypatch.setattr(
        restore_api,
        "_personal_space_module_context",
        lambda *args: (object(), landing, {}),
    )
    restore_calls: list[dict] = []
    monkeypatch.setattr(
        restore_api,
        "_inbox_json_request",
        lambda *args, **kwargs: restore_calls.append(kwargs) or {"status": True},
    )
    restored = restore_api.restore_inbox_recycle_notices(["notice-1"])
    assert restored["restored"][0]["notice_id"] == "notice-1"
    assert restore_calls[0]["data"] == {"ids": "notice-1", "sendTag": "0"}

    delete_api = ChaoxingAPI(Path("unused-cookies.json"))
    delete_reads = iter([{"notices": [recycled_notice]}, {"notices": []}])
    monkeypatch.setattr(delete_api, "list_inbox_recycle", lambda **kwargs: next(delete_reads))
    monkeypatch.setattr(
        delete_api,
        "_personal_space_module_context",
        lambda *args: (object(), landing, {}),
    )
    delete_calls: list[dict] = []
    monkeypatch.setattr(
        delete_api,
        "_inbox_json_request",
        lambda *args, **kwargs: delete_calls.append(kwargs) or {"status": True},
    )
    permanently_deleted = delete_api.permanently_delete_inbox_recycle_notices(["notice-1"])
    assert permanently_deleted["deleted"][0]["notice_id"] == "notice-1"
    assert delete_calls[0]["data"]["ids"] == "notice-1"

    empty_api = ChaoxingAPI(Path("unused-cookies.json"))
    empty_reads = iter([{"notices": [recycled_notice]}, {"count": 0}])
    monkeypatch.setattr(empty_api, "list_inbox_recycle", lambda **kwargs: next(empty_reads))
    monkeypatch.setattr(
        empty_api,
        "_personal_space_module_context",
        lambda *args: (object(), landing, {}),
    )
    empty_calls: list[dict] = []
    monkeypatch.setattr(
        empty_api,
        "_inbox_json_request",
        lambda *args, **kwargs: empty_calls.append(kwargs) or {"status": True},
    )
    emptied = empty_api.empty_inbox_recycle()
    assert emptied["deleted_count"] == 1
    assert empty_calls[0]["data"]["sendTag"] == "0"


def test_parse_personal_group_manage_context() -> None:
    parsed = parse_personal_group_manage_context(
        """
        <script>
        window.obj = {
          authUser:{"puid":405017213,"name":"张三","fid":23080},
          circle:{"id":7,"bbsid":"bbs-1","name":"写作小组","introduce":"简介",
            "isCreater":1,"groupAuth":{"modifyName":1,"quit":0}}
        };
        </script>
        """
    )
    assert parsed["account"]["puid"] == 405017213
    assert parsed["group"]["bbsid"] == "bbs-1"
    assert parsed["group"]["introduce"] == "简介"


def test_personal_group_read_and_folder_list_contracts(monkeypatch) -> None:
    landing = type("Landing", (), {"url": "https://groupweb.chaoxing.com/pc/circle/circleIndex"})()
    api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(api, "_personal_groups_context", lambda: (object(), landing))
    raw_folder = {
        "id": 10,
        "pid": 0,
        "name": "教学",
        "top": 1,
        "list": [{"id": 11, "pid": 10, "name": "写作", "top": 0}],
    }
    raw_group = {
        "id": 7,
        "bbsid": "bbs-1",
        "name": "写作小组",
        "folderId": 0,
        "mem_count": 12,
        "topic_Count": 3,
        "isCreater": 0,
        "groupAuth": {"quit": 1, "modifyName": 0},
    }

    def group_request(_session, path, _operation, **kwargs):
        if path.endswith("getCircleFolderTree"):
            return {"status": True, "data": [raw_folder]}
        if path.endswith("getCircleFolderList"):
            return {"status": True, "data": [raw_folder]}
        if path.endswith("getCircleList"):
            return {"status": True, "data": [raw_group]}
        raise AssertionError(path)

    monkeypatch.setattr(api, "_personal_group_json_request", group_request)
    tree = api.list_personal_group_folder_tree()
    assert tree["count"] == 2
    assert tree["folders"][1]["parent_id"] == "10"
    folders = api.list_personal_group_folders()
    assert folders["folders"][0]["name"] == "教学"
    groups = api.list_personal_groups()
    assert groups["groups"][0]["can_quit"] is True
    assert groups["groups"][0]["member_count"] == 12

    detailed_raw = {
        **raw_group,
        "introduce": "完整简介",
        "createRealName": "创建者",
        "showQrcode": 1,
    }
    html = (
        '<script>window.obj={authUser:{"puid":405017213,"name":"张三"},circle:'
        + json.dumps(detailed_raw, ensure_ascii=False)
        + "};</script>"
    )

    class Response:
        url = "https://groupweb.chaoxing.com/pc/circle/manage/index?bbsid=bbs-1"
        content = html.encode()
        encoding = "utf-8"
        apparent_encoding = "utf-8"

        @staticmethod
        def raise_for_status():
            return None

    class Session:
        @staticmethod
        def get(*args, **kwargs):
            return Response()

    read_api = ChaoxingAPI(Path("unused-cookies.json"))
    selected = read_api._normalize_personal_group(raw_group, 1)
    monkeypatch.setattr(read_api, "_find_personal_group", lambda *args: selected)
    monkeypatch.setattr(read_api, "_personal_groups_context", lambda: (Session(), landing))
    detail = read_api.read_personal_group("写作小组")
    assert detail["group"]["description"] == "完整简介"
    assert detail["settings"]["showQrcode"] == 1


def test_personal_group_folder_mutation_contracts(monkeypatch) -> None:
    landing = type("Landing", (), {"url": "https://groupweb.chaoxing.com/pc/circle/circleIndex"})()
    folder = {
        "index": 1,
        "flat_index": 1,
        "folder_id": "10",
        "parent_id": "0",
        "name": "教学",
        "is_top": False,
        "sort": 1,
        "children": [],
    }

    create_api = ChaoxingAPI(Path("unused-cookies.json"))
    create_trees = iter([{"folders": []}, {"folders": [folder]}])
    monkeypatch.setattr(create_api, "_personal_group_folder_id", lambda *args: "0")
    monkeypatch.setattr(create_api, "list_personal_group_folder_tree", lambda: next(create_trees))
    monkeypatch.setattr(create_api, "_personal_groups_context", lambda: (object(), landing))
    create_calls: list[dict] = []
    monkeypatch.setattr(
        create_api,
        "_personal_group_json_request",
        lambda *args, **kwargs: create_calls.append(kwargs) or {"status": True},
    )
    created = create_api.create_personal_group_folder("教学")
    assert created["folder"]["folder_id"] == "10"
    assert create_calls[0]["params"]["name"] == quote("教学", safe="")

    rename_api = ChaoxingAPI(Path("unused-cookies.json"))
    renamed = {**folder, "name": "课程"}
    rename_trees = iter([{"folders": [folder]}, {"folders": [renamed]}])
    monkeypatch.setattr(rename_api, "list_personal_group_folder_tree", lambda: next(rename_trees))
    monkeypatch.setattr(rename_api, "_personal_groups_context", lambda: (object(), landing))
    rename_calls: list[dict] = []
    monkeypatch.setattr(
        rename_api,
        "_personal_group_json_request",
        lambda *args, **kwargs: rename_calls.append(kwargs) or {"status": True},
    )
    assert rename_api.rename_personal_group_folder("教学", "课程")["folder"]["name"] == "课程"
    assert rename_calls[0]["params"]["folderId"] == "10"

    move_api = ChaoxingAPI(Path("unused-cookies.json"))
    moved = {**folder, "parent_id": "20"}
    move_trees = iter([{"folders": [folder]}, {"folders": [moved]}])
    monkeypatch.setattr(move_api, "list_personal_group_folder_tree", lambda: next(move_trees))
    monkeypatch.setattr(move_api, "_personal_group_folder_id", lambda *args: "20")
    monkeypatch.setattr(move_api, "_personal_groups_context", lambda: (object(), landing))
    move_calls: list[dict] = []
    monkeypatch.setattr(
        move_api,
        "_personal_group_json_request",
        lambda *args, **kwargs: move_calls.append(kwargs) or {"status": True},
    )
    assert move_api.move_personal_group_folder("教学", "目标")["folder"]["parent_id"] == "20"

    top_api = ChaoxingAPI(Path("unused-cookies.json"))
    topped = {**folder, "is_top": True}
    top_trees = iter([{"folders": [folder]}, {"folders": [topped]}])
    monkeypatch.setattr(top_api, "list_personal_group_folder_tree", lambda: next(top_trees))
    monkeypatch.setattr(top_api, "_personal_groups_context", lambda: (object(), landing))
    top_calls: list[dict] = []
    monkeypatch.setattr(
        top_api,
        "_personal_group_json_request",
        lambda *args, **kwargs: top_calls.append(kwargs) or {"status": True},
    )
    assert top_api.set_personal_group_folder_top_status("教学", True)["folder"]["is_top"]
    assert top_calls[0]["params"]["operate"] == "setTop"

    delete_api = ChaoxingAPI(Path("unused-cookies.json"))
    delete_trees = iter([{"folders": [folder]}, {"folders": []}])
    monkeypatch.setattr(delete_api, "list_personal_group_folder_tree", lambda: next(delete_trees))
    monkeypatch.setattr(delete_api, "_personal_groups_context", lambda: (object(), landing))
    delete_calls: list[dict] = []
    monkeypatch.setattr(
        delete_api,
        "_personal_group_json_request",
        lambda *args, **kwargs: delete_calls.append(kwargs) or {"status": True},
    )
    assert delete_api.delete_personal_group_folder("教学")["deleted"]["folder_id"] == "10"


def test_personal_group_mutation_contracts(monkeypatch) -> None:
    landing = type("Landing", (), {"url": "https://groupweb.chaoxing.com/pc/circle/circleIndex"})()
    raw_group = {
        "id": 7,
        "bbsid": "bbs-1",
        "name": "写作小组",
        "introduce": "简介",
        "folderId": 0,
        "top": 0,
        "isCreater": 0,
        "groupAuth": {"quit": 1, "modifyName": 1},
    }
    group = ChaoxingAPI._normalize_personal_group(raw_group, 1)

    create_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(create_api, "_personal_group_folder_id", lambda *args: "0")
    monkeypatch.setattr(create_api, "_personal_groups_context", lambda: (object(), landing))
    create_calls: list[dict] = []

    def create_request(*args, **kwargs):
        create_calls.append(kwargs)
        raw_group["bbsid"] = kwargs["params"]["bbsid"]
        return {"status": True}

    monkeypatch.setattr(create_api, "_personal_group_json_request", create_request)
    monkeypatch.setattr(
        create_api,
        "_all_personal_groups",
        lambda: [create_api._normalize_personal_group(raw_group, 1)],
    )
    created = create_api.create_personal_group("写作小组", description="简介")
    assert created["group"]["name"] == "写作小组"
    assert create_calls[0]["params"]["name"] == quote("写作小组", safe="")

    update_api = ChaoxingAPI(Path("unused-cookies.json"))
    updated_group = {**group, "name": "课程小组", "description": "新简介"}
    details = iter([{"group": group}, {"group": updated_group}])
    monkeypatch.setattr(update_api, "read_personal_group", lambda *args: next(details))
    monkeypatch.setattr(update_api, "_personal_groups_context", lambda: (object(), landing))
    update_calls: list[dict] = []
    monkeypatch.setattr(
        update_api,
        "_personal_group_json_request",
        lambda *args, **kwargs: update_calls.append(kwargs) or {"status": True},
    )
    updated = update_api.update_personal_group("写作小组", name="课程小组", description="新简介")
    assert updated["group"]["name"] == "课程小组"

    top_api = ChaoxingAPI(Path("unused-cookies.json"))
    finds = iter([group, {**group, "is_top": True}])
    monkeypatch.setattr(top_api, "_find_personal_group", lambda *args: next(finds))
    monkeypatch.setattr(top_api, "_personal_groups_context", lambda: (object(), landing))
    monkeypatch.setattr(
        top_api,
        "_personal_group_json_request",
        lambda *args, **kwargs: {"status": True},
    )
    assert top_api.set_personal_group_top_status("写作小组", True)["group"]["is_top"]

    move_api = ChaoxingAPI(Path("unused-cookies.json"))
    move_finds = iter([group, {**group, "folder_id": "10"}])
    monkeypatch.setattr(move_api, "_find_personal_group", lambda *args: next(move_finds))
    monkeypatch.setattr(move_api, "_personal_group_folder_id", lambda *args: "10")
    monkeypatch.setattr(move_api, "_personal_groups_context", lambda: (object(), landing))
    monkeypatch.setattr(
        move_api,
        "_personal_group_json_request",
        lambda *args, **kwargs: {"status": True},
    )
    assert move_api.move_personal_group("写作小组", "教学")["group"]["folder_id"] == "10"

    quit_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(quit_api, "_find_personal_group", lambda *args: group)
    monkeypatch.setattr(quit_api, "_personal_groups_context", lambda: (object(), landing))
    monkeypatch.setattr(
        quit_api,
        "_personal_group_json_request",
        lambda *args, **kwargs: {"status": True},
    )
    monkeypatch.setattr(quit_api, "_all_personal_groups", lambda: [])
    assert quit_api.quit_personal_group("写作小组")["quit"]["bbs_id"] == "bbs-1"

    dismiss_api = ChaoxingAPI(Path("unused-cookies.json"))
    owner_group = {**group, "is_creator": True, "permissions": {"dismiss": 1}}
    monkeypatch.setattr(dismiss_api, "_find_personal_group", lambda *args: owner_group)
    monkeypatch.setattr(dismiss_api, "_personal_groups_context", lambda: (object(), landing))
    dismiss_calls: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        dismiss_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: (
            dismiss_calls.append((path, kwargs)) or {"status": True}
        ),
    )
    monkeypatch.setattr(dismiss_api, "_all_personal_groups", lambda: [])
    dismissed = dismiss_api.dismiss_personal_group("写作小组")
    assert dismissed["dismissed"]["bbs_id"] == "bbs-1"
    assert dismiss_calls[0][0] == "/pc/cmem/quitCircle"


def test_personal_group_setting_and_speaking_rule_contracts(monkeypatch) -> None:
    landing = type("Landing", (), {"url": "https://groupweb.chaoxing.com/pc/circle"})()
    group = {
        "bbs_id": "bbs-1",
        "name": "课程小组",
        "description": "课程交流",
        "is_creator": True,
        "permissions": {},
        "management_url": "https://groupweb.chaoxing.com/pc/circle/manage/index?bbsid=bbs-1",
    }
    before_settings = {
        "isCheck": 1,
        "showManager": 0,
        **{field: 0 for field in PERSONAL_GROUP_SPEAKING_RULE_FIELDS},
        "topicNeedAttachment": "{}",
    }
    after_settings = {**before_settings, "isCheck": 0, "showManager": 1}

    settings_api = ChaoxingAPI(Path("unused-cookies.json"))
    details = iter(
        [
            {"group": group, "settings": before_settings},
            {"group": group, "settings": after_settings},
        ]
    )
    monkeypatch.setattr(settings_api, "read_personal_group", lambda *args: next(details))
    monkeypatch.setattr(settings_api, "_personal_groups_context", lambda: (object(), landing))
    setting_calls: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        settings_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: (
            setting_calls.append((path, kwargs)) or {"status": True}
        ),
    )
    updated = settings_api.update_personal_group_settings(
        "课程小组", {"isCheck": False, "showManager": True}
    )
    assert updated["changes"] == {"isCheck": False, "showManager": True}
    assert setting_calls[0][0].endswith("/updateCircle")
    assert setting_calls[0][1]["params"]["name"] == quote("课程小组", safe="")
    assert setting_calls[0][1]["params"]["introduce"] == quote("课程交流", safe="")
    assert setting_calls[1][0].endswith("/updateCircleExtend")

    speaking_api = ChaoxingAPI(Path("unused-cookies.json"))
    speaking_after = {
        **before_settings,
        "leastTopicWord": 30,
        "replyInvitationWord": 10,
        "topicNeedAttachment": '{"image":1}',
    }
    speaking_details = iter(
        [
            {"group": group, "settings": before_settings},
            {"group": group, "settings": speaking_after},
        ]
    )
    monkeypatch.setattr(speaking_api, "read_personal_group", lambda *args: next(speaking_details))
    monkeypatch.setattr(speaking_api, "_personal_groups_context", lambda: (object(), landing))
    speaking_calls: list[dict] = []
    monkeypatch.setattr(
        speaking_api,
        "_personal_group_json_request",
        lambda *args, **kwargs: speaking_calls.append(kwargs) or {"status": True},
    )
    rules = speaking_api.update_personal_group_speaking_rules(
        "课程小组",
        {"leastTopicWord": 30, "replyInvitationWord": 10},
        attachment_rules={"image": True},
    )
    assert rules["speaking_rules"]["leastTopicWord"] == 30
    assert speaking_calls[0]["params"]["replyInvitationWord"] == 10
    assert speaking_calls[0]["params"]["topicNeedAttachment"] == '{"image":1}'


def test_personal_group_notice_send_contract(monkeypatch) -> None:
    landing = type("Landing", (), {"url": "https://groupweb.chaoxing.com/pc/circle"})()
    group = {
        "bbs_id": "bbs-1",
        "name": "课程小组",
        "is_creator": True,
        "permissions": {"sendNotice": 1},
        "management_url": "https://groupweb.chaoxing.com/pc/circle/manage/index?bbsid=bbs-1",
    }

    class Response:
        content = json.dumps({"status": True, "data": {"idCode": "notice-1"}}).encode()
        encoding = "utf-8"
        apparent_encoding = "utf-8"

        @staticmethod
        def raise_for_status() -> None:
            return None

    class Session:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict]] = []

        def post(self, url: str, **kwargs):
            self.calls.append((url, kwargs))
            return Response()

    session = Session()
    api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(api, "_find_personal_group", lambda *args: group)
    monkeypatch.setattr(api, "_personal_groups_context", lambda: (session, landing))
    monkeypatch.setattr(
        api,
        "list_inbox_notices",
        lambda **kwargs: {"notices": [{"notice_id": "notice-1", "uuid": "", "title": "开课通知"}]},
    )
    sent = api.send_personal_group_notice("课程小组", "开课通知", "周一开始上课。")
    assert sent["notice"]["notice_id"] == "notice-1"
    assert session.calls[0][0].endswith("/pc/circle/manage/addCircleNotice")
    payload = session.calls[0][1]["data"]
    assert payload["bbsid"] == "bbs-1"
    assert payload["content"] == "周一开始上课。"
    assert "周一开始上课" in payload["rtf_content"]


def test_personal_group_review_reminder_contracts(monkeypatch) -> None:
    landing = type("Landing", (), {"url": "https://groupweb.chaoxing.com/pc/circle"})()
    group = {
        "bbs_id": "bbs-1",
        "name": "课程小组",
        "is_creator": True,
        "permissions": {"showTopicNeedCheck": 1},
        "management_url": "https://groupweb.chaoxing.com/pc/circle/manage/index?bbsid=bbs-1",
    }
    account = {"puid": "100", "name": "创建者", "fid": "1"}

    class Response:
        encoding = "utf-8"
        apparent_encoding = "utf-8"

        def __init__(self, content: str) -> None:
            self.content = content.encode()

        @staticmethod
        def raise_for_status() -> None:
            return None

    class Session:
        def get(self, url: str, **kwargs):
            if url.endswith("/pc/checkRemind/getRemindList"):
                return Response(json.dumps({"msg": "操作失败", "status": False}))
            return Response(
                '<div class="adminItem" puid="100">'
                '<span class="personName managerName">创建者</span></div>'
            )

    list_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        list_api,
        "read_personal_group",
        lambda *args: {"group": group, "account": account},
    )
    monkeypatch.setattr(list_api, "_personal_groups_context", lambda: (Session(), landing))
    empty = list_api.list_personal_group_review_reminders("课程小组")
    assert empty["count"] == 0
    assert empty["reviewers"] == [{"puid": "100", "name": "创建者"}]

    class ExistingSession(Session):
        def get(self, url: str, **kwargs):
            if url.endswith("/pc/checkRemind/getRemindList"):
                return Response(
                    json.dumps(
                        {
                            "status": True,
                            "records": [
                                {
                                    "uuid": "reminder-1",
                                    "startTime": "23:58",
                                    "endTime": "23:59",
                                    "weeks": "星期日",
                                    "puids": "100",
                                    "namesList": ["创建者"],
                                }
                            ],
                        },
                        ensure_ascii=False,
                    )
                )
            return super().get(url, **kwargs)

    monkeypatch.setattr(list_api, "_personal_groups_context", lambda: (ExistingSession(), landing))
    existing = list_api.list_personal_group_review_reminders("课程小组")
    assert existing["reminders"][0]["uuid"] == "reminder-1"
    assert existing["reminders"][0]["puids"] == ["100"]

    reminder = {
        "index": 1,
        "uuid": "reminder-1",
        "start_time": "23:58",
        "end_time": "23:59",
        "weeks": ["星期日"],
        "week_text": "星期日",
        "puids": ["100"],
        "names": ["创建者"],
        "puids_source": "server",
    }
    before = {"group": group, "count": 0, "reminders": []}
    after_create = {"group": group, "count": 1, "reminders": [reminder]}
    create_api = ChaoxingAPI(Path("unused-cookies.json"))
    create_reads = iter([before, after_create])
    monkeypatch.setattr(
        create_api, "list_personal_group_review_reminders", lambda *args: next(create_reads)
    )
    monkeypatch.setattr(create_api, "_session", object)
    create_calls: list[dict] = []
    monkeypatch.setattr(
        create_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: (
            create_calls.append({"path": path, **kwargs}) or {"status": True}
        ),
    )
    created = create_api.create_personal_group_review_reminder(
        "课程小组", "23:58", "23:59", ["周日"], ["100"]
    )
    assert created["reminder"]["uuid"] == "reminder-1"
    assert create_calls[0]["path"].endswith("/addRemind")
    assert create_calls[0]["data"]["weeks"] == quote("星期日", safe="")

    changed_reminder = {**reminder, "start_time": "23:57"}
    update_api = ChaoxingAPI(Path("unused-cookies.json"))
    update_reads = iter(
        [after_create, {"group": group, "count": 1, "reminders": [changed_reminder]}]
    )
    monkeypatch.setattr(
        update_api, "list_personal_group_review_reminders", lambda *args: next(update_reads)
    )
    monkeypatch.setattr(update_api, "_session", object)
    update_calls: list[dict] = []
    monkeypatch.setattr(
        update_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: (
            update_calls.append({"path": path, **kwargs}) or {"status": True}
        ),
    )
    updated = update_api.update_personal_group_review_reminder(
        "课程小组", "reminder-1", start_time="23:57"
    )
    assert updated["reminder"]["start_time"] == "23:57"
    assert update_calls[0]["data"]["uuid"] == "reminder-1"

    delete_api = ChaoxingAPI(Path("unused-cookies.json"))
    delete_reads = iter([after_create, {"group": group, "count": 0, "reminders": []}])
    monkeypatch.setattr(
        delete_api, "list_personal_group_review_reminders", lambda *args: next(delete_reads)
    )
    monkeypatch.setattr(delete_api, "_session", object)
    delete_calls: list[dict] = []
    monkeypatch.setattr(
        delete_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: (
            delete_calls.append({"path": path, **kwargs}) or {"status": True}
        ),
    )
    deleted = delete_api.delete_personal_group_review_reminders("课程小组", ["reminder-1"])
    assert deleted["deleted"][0]["uuid"] == "reminder-1"
    assert delete_calls[0]["data"]["uuids"] == "reminder-1"


def test_personal_group_label_and_deletion_reason_contracts(monkeypatch) -> None:
    landing = type("Landing", (), {"url": "https://groupweb.chaoxing.com/pc/circle"})()
    group = {
        "bbs_id": "bbs-1",
        "name": "课程小组",
        "is_creator": True,
        "permissions": {"addLebel": 1, "showNeedDelReasonSet": 1},
        "management_url": "https://groupweb.chaoxing.com/pc/circle/manage/index?bbsid=bbs-1",
    }
    raw_label = {
        "id": 10,
        "uuid": "label-1",
        "bbsid": "bbs-1",
        "name": "重点",
        "sort": 1,
    }
    label_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        label_api,
        "_personal_group_topic_context",
        lambda *args: {"group": group, "session": object(), "landing_url": landing.url},
    )
    monkeypatch.setattr(
        label_api,
        "_personal_group_json_request",
        lambda *args, **kwargs: {
            "status": True,
            "msg": json.dumps({"result": 1, "data": [raw_label]}),
        },
    )
    labels = label_api.list_personal_group_labels("课程小组")
    assert labels["labels"][0]["label_uuid"] == "label-1"

    created_label = {**labels["labels"][0], "label_uuid": "label-2", "name": "新增"}
    create_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(create_api, "_find_personal_group", lambda *args: group)
    label_reads = iter(
        [{"labels": labels["labels"]}, {"labels": [*labels["labels"], created_label]}]
    )
    monkeypatch.setattr(create_api, "list_personal_group_labels", lambda *args: next(label_reads))
    monkeypatch.setattr(create_api, "_personal_group_account_puid", lambda *args: "100")
    monkeypatch.setattr(create_api, "_personal_groups_context", lambda: (object(), landing))
    label_calls: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        create_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: (
            label_calls.append((path, kwargs)) or {"status": True, "msg": "操作成功"}
        ),
    )
    created = create_api.create_personal_group_label("课程小组", "新增")
    assert created["label"]["label_uuid"] == "label-2"
    assert label_calls[0][0].endswith("/addLabel")
    assert label_calls[0][1]["data"]["label"] == quote("新增", safe="")

    reason_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(reason_api, "_find_personal_group", lambda *args: group)
    monkeypatch.setattr(reason_api, "_personal_groups_context", lambda: (object(), landing))
    monkeypatch.setattr(
        reason_api,
        "_personal_group_json_request",
        lambda *args, **kwargs: {
            "status": True,
            "msg": json.dumps(
                {
                    "result": 1,
                    "data": [
                        {
                            "id": 20,
                            "uuid": "reason-1",
                            "bbsid": "bbs-1",
                            "name": "内容重复",
                        }
                    ],
                }
            ),
        },
    )
    reasons = reason_api.list_personal_group_deletion_reasons("课程小组")
    assert reasons["reasons"][0]["reason_uuid"] == "reason-1"


def test_personal_group_recycle_contracts(monkeypatch) -> None:
    landing = type("Landing", (), {"url": "https://groupweb.chaoxing.com/pc/circle"})()
    group = {
        "bbs_id": "bbs-1",
        "name": "课程小组",
        "is_creator": True,
        "permissions": {"showRecycleBin": 1},
        "management_url": "https://groupweb.chaoxing.com/pc/circle/manage/index?bbsid=bbs-1",
    }
    payload = {
        "status": True,
        "datas": [
            {
                "id": 10,
                "dataType": "topic",
                "content": {"uuid": "topic-1", "title": "讨论", "content": "正文"},
            },
            {
                "id": 11,
                "dataType": "invitation",
                "content": {
                    "topic": {"title": "讨论"},
                    "invitation": {"uuid": "reply-1", "content": "回复"},
                },
            },
            {
                "id": 12,
                "dataType": "folder",
                "content": {"folder_uuid": "folder-1", "name": "归档"},
            },
        ],
        "poff": {"lastPage": 1},
    }
    api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(api, "_find_personal_group", lambda *args: group)
    monkeypatch.setattr(api, "_personal_groups_context", lambda: (object(), landing))
    monkeypatch.setattr(api, "_personal_group_json_request", lambda *args, **kwargs: payload)
    listing = api.list_personal_group_recycle_items("课程小组")
    assert [item["item_type"] for item in listing["items"]] == ["topic", "reply", "folder"]

    restore_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(restore_api, "_find_personal_group", lambda *args: group)
    recycle_reads = iter([listing, {"items": []}])
    monkeypatch.setattr(
        restore_api, "list_personal_group_recycle_items", lambda *args: next(recycle_reads)
    )
    monkeypatch.setattr(restore_api, "_personal_groups_context", lambda: (object(), landing))
    restore_calls: list[str] = []
    monkeypatch.setattr(
        restore_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: (
            restore_calls.append(path) or {"status": True, "msg": "操作成功"}
        ),
    )
    restored = restore_api.restore_personal_group_recycle_items("课程小组", ["10", "11", "12"])
    assert len(restored["restored_items"]) == 3
    assert restore_calls == [
        "/pc/recycle/recoveryTopicFolder",
        "/pc/recycle/recoveryTopic",
        "/pc/recycle/recoveryInvitation",
    ]


def test_personal_group_export_job_contracts(monkeypatch) -> None:
    group = {
        "bbs_id": "bbs-1",
        "name": "课程小组",
        "management_url": "https://groupweb.chaoxing.com/pc/circle/manage/index?bbsid=bbs-1",
    }
    ready_raw = {
        "id": 21203,
        "fileName": "成员名单.xlsx",
        "fileSize": 4,
        "ftime": "刚刚",
        "downloadURL": "https://sharewh.chaoxing.com/share/download/token",
        "status": "1",
    }
    ready = ChaoxingAPI._normalize_personal_group_export_job(ready_raw, 1)

    list_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(list_api, "_find_personal_group", lambda *args: group)
    monkeypatch.setattr(list_api, "_session", lambda: object())
    monkeypatch.setattr(
        list_api,
        "_personal_group_json_request",
        lambda *args, **kwargs: {
            "status": True,
            "list": [ready_raw],
            "poff": {"lastPage": 1},
        },
    )
    listing = list_api.list_personal_group_exports("课程小组")
    assert listing["exports"] == [ready]

    wait_api = ChaoxingAPI(Path("unused-cookies.json"))
    exporting = {**ready, "status": "exporting", "status_code": 0}
    wait_listings = iter([{"exports": [exporting]}, {"exports": [ready]}])
    monkeypatch.setattr(wait_api, "_find_personal_group", lambda *args: group)
    monkeypatch.setattr(wait_api, "list_personal_group_exports", lambda *args: next(wait_listings))
    clock = iter([0.0, 0.1, 0.2])
    monkeypatch.setattr("chaoxing_agent.api.monotonic", lambda: next(clock))
    monkeypatch.setattr("chaoxing_agent.api.sleep", lambda _seconds: None)
    waited = wait_api.wait_personal_group_export(
        "课程小组", "21203", timeout_seconds=10, poll_seconds=1
    )
    assert waited["export"]["status"] == "ready"

    create_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(create_api, "_find_personal_group", lambda *args: group)
    create_listings = iter([{"exports": []}, {"exports": [ready]}])
    monkeypatch.setattr(
        create_api, "list_personal_group_exports", lambda *args: next(create_listings)
    )
    monkeypatch.setattr(create_api, "_session", lambda: object())
    create_calls: list[str] = []
    monkeypatch.setattr(
        create_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: create_calls.append(path) or {"status": True},
    )
    created = create_api.create_personal_group_member_export("课程小组")
    assert created["export"]["export_id"] == "21203"
    assert create_calls == ["/pc/export/cmem/exportMembers"]

    retry_api = ChaoxingAPI(Path("unused-cookies.json"))
    failed = {**ready, "status": "failed", "status_code": 2, "download_url": ""}
    exporting = {**failed, "status": "exporting", "status_code": 0}
    retry_listings = iter([{"exports": [failed]}, {"exports": [exporting]}])
    monkeypatch.setattr(retry_api, "_find_personal_group", lambda *args: group)
    monkeypatch.setattr(
        retry_api, "list_personal_group_exports", lambda *args: next(retry_listings)
    )
    monkeypatch.setattr(retry_api, "_session", lambda: object())
    retry_calls: list[str] = []
    monkeypatch.setattr(
        retry_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: retry_calls.append(path) or {"status": True},
    )
    retried = retry_api.retry_personal_group_export("课程小组", "21203")
    assert retried["export"]["status"] == "exporting"
    assert retry_calls == ["/pc/statistics/reExport"]

    cancel_api = ChaoxingAPI(Path("unused-cookies.json"))
    cancel_listings = iter([{"exports": [ready]}, {"exports": []}])
    monkeypatch.setattr(cancel_api, "_find_personal_group", lambda *args: group)
    monkeypatch.setattr(
        cancel_api, "list_personal_group_exports", lambda *args: next(cancel_listings)
    )
    monkeypatch.setattr(cancel_api, "_session", lambda: object())
    cancel_calls: list[str] = []
    monkeypatch.setattr(
        cancel_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: cancel_calls.append(path) or {"status": True},
    )
    cancelled = cancel_api.cancel_personal_group_export("课程小组", "21203")
    assert cancelled["cancelled_export"]["export_id"] == "21203"
    assert cancel_calls == ["/pc/statistics/cancelExport"]


def test_personal_group_export_download_contract(monkeypatch, tmp_path: Path) -> None:
    group = {
        "bbs_id": "bbs-1",
        "name": "课程小组",
        "management_url": "https://groupweb.chaoxing.com/pc/circle/manage/index?bbsid=bbs-1",
    }
    job = {
        "index": 1,
        "export_id": "21203",
        "file_name": "成员名单.xlsx",
        "file_size": 4,
        "formatted_time": "刚刚",
        "status": "ready",
        "status_code": 1,
        "download_url": "https://sharewh.chaoxing.com/share/download/token",
    }

    class WrapperResponse:
        content = b"<script>var downloadUrl = 'https://d0.cldisk.com/download/file';</script>"
        encoding = "utf-8"
        apparent_encoding = "utf-8"
        headers = {"Content-Type": "text/html;charset=UTF-8"}
        url = job["download_url"]

        @staticmethod
        def raise_for_status() -> None:
            return None

    class FileResponse:
        content = b"PK12"
        encoding = None
        apparent_encoding = None
        headers = {
            "Content-Type": "application/octet-stream",
            "Content-Disposition": "attachment; filename*=UTF-8''members.xlsx",
        }
        url = "https://d0.cldisk.com/download/file"

        @staticmethod
        def raise_for_status() -> None:
            return None

        @staticmethod
        def iter_content(chunk_size: int):
            assert chunk_size > 0
            yield b"PK"
            yield b"12"

    class ExportSession:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict]] = []

        def get(self, url: str, **kwargs):
            self.calls.append((url, kwargs))
            return WrapperResponse() if "sharewh.chaoxing.com" in url else FileResponse()

    api = ChaoxingAPI(Path("unused-cookies.json"))
    session = ExportSession()
    monkeypatch.setattr(api, "_find_personal_group", lambda *args: group)
    monkeypatch.setattr(
        api,
        "list_personal_group_exports",
        lambda *args: {"group": group, "exports": [job]},
    )
    monkeypatch.setattr(api, "_session", lambda: session)
    result = api.download_personal_group_export("课程小组", "21203", tmp_path)
    assert result["file_name"] == "members.xlsx"
    assert (tmp_path / "members.xlsx").read_bytes() == b"PK12"
    assert session.calls[1][1]["headers"]["Referer"] == job["download_url"]


def test_personal_group_activity_list_and_write_contracts(monkeypatch) -> None:
    landing = type("Landing", (), {"url": "https://groupweb.chaoxing.com/pc/circle"})()
    group = {
        "bbs_id": "bbs-1",
        "name": "课程小组",
        "can_manage": True,
        "management_url": "https://groupweb.chaoxing.com/pc/circle/manage/index?bbsid=bbs-1",
    }
    online_raw = {
        "id": 10,
        "uuid": "activity-online",
        "bbsid": "bbs-1",
        "title": "课程入口",
        "onlineOrNot": 1,
        "sortValue": 1,
        "activeLinkAPP": "https://example.com/app",
        "activeLink": "https://example.com/pc",
        "appImgUrl": "https://example.com/app.png",
        "pcImgUrl": "https://example.com/pc.png",
    }
    offline_raw = {
        **online_raw,
        "id": 11,
        "uuid": "activity-offline",
        "title": "待上线入口",
        "onlineOrNot": 2,
    }
    api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(api, "_find_personal_group", lambda *args: group)
    monkeypatch.setattr(api, "_personal_groups_context", lambda: (object(), landing))
    list_calls: list[dict] = []

    def activity_request(_session, path, _operation, **kwargs):
        list_calls.append({"path": path, **kwargs})
        raw = online_raw if kwargs["params"]["onlineOrNot"] == 1 else offline_raw
        return {
            "result": 1,
            "msg": {"result": 1, "data": {"list": [raw], "poff": {"lastPage": 1}}},
        }

    monkeypatch.setattr(api, "_personal_group_json_request", activity_request)
    listing = api.list_personal_group_activities("课程小组")
    assert [item["status"] for item in listing["activities"]] == ["online", "offline"]
    assert listing["activities"][0]["pc_link"] == "https://example.com/pc"
    assert list_calls[0]["path"].endswith("/apis/circle/getCircleActivityList")
    assert list_calls[1]["params"]["onlineOrNot"] == 2

    created_raw = {**offline_raw, "id": 12, "uuid": "activity-created", "title": "新入口"}
    created = api._normalize_personal_group_activity(created_raw, 2)
    create_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(create_api, "_find_personal_group", lambda *args: group)
    activity_reads = iter(
        [
            {"online_count": 1, "activities": listing["activities"]},
            {"online_count": 1, "activities": [*listing["activities"], created]},
        ]
    )
    monkeypatch.setattr(
        create_api, "list_personal_group_activities", lambda *args, **kwargs: next(activity_reads)
    )
    monkeypatch.setattr(create_api, "_personal_groups_context", lambda: (object(), landing))
    saved_forms: list[dict] = []
    monkeypatch.setattr(
        create_api,
        "_save_personal_group_activity",
        lambda _session, form, **kwargs: saved_forms.append(form) or {"uuid": "activity-created"},
    )
    result = create_api.create_personal_group_activity("课程小组", "新入口")
    assert result["activity"]["activity_uuid"] == "activity-created"
    assert saved_forms[0]["onlineOrNot"] == 2
    assert saved_forms[0]["title"] == "新入口"


def test_personal_group_activity_status_order_and_delete_contracts(monkeypatch) -> None:
    landing = type("Landing", (), {"url": "https://groupweb.chaoxing.com/pc/circle"})()
    group = {"bbs_id": "bbs-1", "name": "课程小组", "can_manage": True}
    first = {
        "index": 1,
        "activity_id": "10",
        "activity_uuid": "activity-1",
        "title": "入口一",
        "online": True,
        "online_code": 1,
        "status": "online",
        "sort": 1,
        "app_link": "",
        "pc_link": "",
        "app_image_url": "https://example.com/app.png",
        "pc_image_url": "https://example.com/pc.png",
        "app_image_width": 0,
        "app_image_height": 0,
        "pc_image_width": 0,
        "pc_image_height": 0,
    }
    second = {
        **first,
        "index": 2,
        "activity_id": "11",
        "activity_uuid": "activity-2",
        "title": "入口二",
        "sort": 2,
    }

    status_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(status_api, "_find_personal_group", lambda *args: group)
    status_reads = iter(
        [
            {"online_count": 2, "activities": [first, second]},
            {
                "online_count": 1,
                "activities": [{**first, "online": False, "online_code": 2}, second],
            },
        ]
    )
    monkeypatch.setattr(
        status_api, "list_personal_group_activities", lambda *args, **kwargs: next(status_reads)
    )
    monkeypatch.setattr(status_api, "_personal_groups_context", lambda: (object(), landing))
    status_calls: list[dict] = []
    monkeypatch.setattr(
        status_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: (
            status_calls.append({"path": path, **kwargs}) or {"result": 1}
        ),
    )
    status = status_api.set_personal_group_activity_online_status("课程小组", "activity-1", False)
    assert status["activity"]["online"] is False
    assert status_calls[0]["params"]["onlineOrNot"] == 1
    assert status_calls[0]["path"].endswith("/checkCircleActivity")

    reorder_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(reorder_api, "_find_personal_group", lambda *args: group)
    reorder_reads = iter(
        [
            {"activities": [first, second]},
            {"activities": [second, first]},
        ]
    )
    monkeypatch.setattr(
        reorder_api, "list_personal_group_activities", lambda *args, **kwargs: next(reorder_reads)
    )
    monkeypatch.setattr(reorder_api, "_personal_groups_context", lambda: (object(), landing))
    reorder_calls: list[dict] = []
    monkeypatch.setattr(
        reorder_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: (
            reorder_calls.append({"path": path, **kwargs}) or {"result": 1}
        ),
    )
    ordered = reorder_api.reorder_personal_group_activities(
        "课程小组", ["activity-2", "activity-1"]
    )
    assert ordered["activities"][0]["activity_uuid"] == "activity-2"
    assert reorder_calls[0]["params"]["sortValues"] == "1,2"

    delete_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(delete_api, "_find_personal_group", lambda *args: group)
    delete_reads = iter([{"activities": [first]}, {"activities": []}])
    monkeypatch.setattr(
        delete_api, "list_personal_group_activities", lambda *args, **kwargs: next(delete_reads)
    )
    monkeypatch.setattr(delete_api, "_personal_groups_context", lambda: (object(), landing))
    delete_calls: list[dict] = []
    monkeypatch.setattr(
        delete_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: (
            delete_calls.append({"path": path, **kwargs}) or {"result": 1}
        ),
    )
    deleted = delete_api.delete_personal_group_activity("课程小组", "activity-1")
    assert deleted["deleted"]["activity_uuid"] == "activity-1"
    assert delete_calls[0]["path"].endswith("/deleteActivity")


def test_personal_group_activity_image_dimensions(tmp_path) -> None:
    png = tmp_path / "banner.png"
    png.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\rIHDR"
        + (345).to_bytes(4, "big")
        + (120).to_bytes(4, "big")
        + b"\x08\x06\x00\x00\x00"
    )
    assert ChaoxingAPI._local_image_dimensions(png) == (345, 120)


def test_personal_group_logo_update_contract(monkeypatch) -> None:
    old_logo = "https://groupweb.chaoxing.com/res/pc/images/moren.jpg"
    new_logo = "https://p.ananas.chaoxing.com/star3/origin/test.png"
    before = {
        "bbs_id": "bbs-1",
        "name": "课程小组",
        "is_creator": True,
        "logo_url": old_logo,
        "management_url": "https://groupweb.chaoxing.com/pc/circle/manage/index?bbsid=bbs-1",
    }
    after = {**before, "logo_url": new_logo}
    api = ChaoxingAPI(Path("unused-cookies.json"))
    groups = iter([before, after])
    monkeypatch.setattr(api, "_find_personal_group", lambda *args: next(groups))
    monkeypatch.setattr(api, "_session", object)
    calls: list[dict] = []
    monkeypatch.setattr(
        api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: (
            calls.append({"path": path, **kwargs}) or {"result": 1, "msg": "ok"}
        ),
    )
    result = api._set_personal_group_logo_url("课程小组", new_logo)
    assert result["group"]["logo_url"] == new_logo
    assert calls[0]["path"].endswith("/bbs-1/logoUpload")
    assert calls[0]["params"] == {"newLogo": new_logo, "type": "logo"}

    public_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        public_api,
        "upload_personal_group_activity_image",
        lambda file: {"file": str(file), "preview_url": new_logo},
    )
    monkeypatch.setattr(
        public_api,
        "_set_personal_group_logo_url",
        lambda group, logo_url: {"group": after, "requested_logo_url": logo_url},
    )
    updated = public_api.update_personal_group_logo("课程小组", r"D:\Images\logo.png")
    assert updated["requested_logo_url"] == new_logo
    assert updated["upload"]["file"] == r"D:\Images\logo.png"


def test_personal_group_level_and_growth_rule_contracts(monkeypatch) -> None:
    group = {
        "bbs_id": "bbs-1",
        "name": "课程小组",
        "is_creator": True,
        "permissions": {},
        "management_url": "https://groupweb.chaoxing.com/pc/circle/manage/index?bbsid=bbs-1",
    }
    detail = {
        "group": group,
        "settings": {
            "growthEnable": 0,
            "levelTitleSeries": "default",
            "scoreRuleSeries": "default",
        },
    }
    list_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(list_api, "read_personal_group", lambda *args: detail)
    monkeypatch.setattr(list_api, "_session", object)
    monkeypatch.setattr(
        list_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: {"result": 1, "data": []},
    )
    listing = list_api.list_personal_group_levels("课程小组")
    assert listing["series"] == "default" and listing["count"] == 15
    assert listing["levels"][0]["growth_value"] == 5

    custom_levels = [
        {
            "level": level,
            "title": f"L{level}",
            "growth_value": threshold,
            "title_image": "",
        }
        for level, threshold in enumerate(
            (5, 10, 15, 30, 50, 100, 200, 500, 1000, 3000, 5000, 10000, 15000, 20000, 50000),
            1,
        )
    ]
    before_levels = {**listing, "group": group}
    after_levels = {
        **before_levels,
        "series": "custom",
        "levels": custom_levels,
    }
    custom_api = ChaoxingAPI(Path("unused-cookies.json"))
    level_reads = iter([before_levels, after_levels])
    monkeypatch.setattr(custom_api, "list_personal_group_levels", lambda *args: next(level_reads))
    monkeypatch.setattr(custom_api, "_session", object)
    custom_calls: list[dict] = []
    monkeypatch.setattr(
        custom_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: (
            custom_calls.append({"path": path, **kwargs}) or {"result": 1}
        ),
    )
    custom = custom_api.update_personal_group_custom_levels("课程小组", custom_levels)
    assert custom["series"] == "custom"
    assert custom_calls[0]["path"].endswith("/switchLevelTitle")
    assert custom_calls[0]["data"]["mode"] == "custom"

    rules = [
        {
            "growth_type": growth_type,
            "type_name": f"type-{growth_type}",
            "trigger_condition": "",
            "description": "",
            "growth_value": value,
            "daily_limit": limit,
            "topic_min_length": 0,
            "reply_min_length": 0,
        }
        for growth_type, value, limit in (
            (1, 5, 0),
            (2, 5, 50),
            (3, 2, 10),
            (4, 2, 30),
            (5, 1, 20),
            (6, 1, 50),
        )
    ]
    before_rules = {"group": group, "series": "default", "count": 6, "rules": rules}
    after_rules = {
        **before_rules,
        "series": "custom",
        "rules": [
            {**rule, "growth_value": 6} if rule["growth_type"] == 2 else rule for rule in rules
        ],
    }
    growth_api = ChaoxingAPI(Path("unused-cookies.json"))
    growth_reads = iter([before_rules, after_rules])
    monkeypatch.setattr(
        growth_api, "list_personal_group_growth_rules", lambda *args: next(growth_reads)
    )
    monkeypatch.setattr(growth_api, "_session", object)
    growth_calls: list[dict] = []
    monkeypatch.setattr(
        growth_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: (
            growth_calls.append({"path": path, **kwargs}) or {"result": 1}
        ),
    )
    changed = growth_api.update_personal_group_growth_rules("课程小组", {"2": 6})
    assert changed["changes"] == {2: 6}
    assert growth_calls[0]["path"].endswith("/switchGrowthRule")
    assert growth_calls[0]["data"]["mode"] == "custom"

    series_api = ChaoxingAPI(Path("unused-cookies.json"))
    series_reads = iter([after_rules, before_rules])
    monkeypatch.setattr(
        series_api, "list_personal_group_growth_rules", lambda *args: next(series_reads)
    )
    monkeypatch.setattr(series_api, "_session", object)
    series_calls: list[dict] = []
    monkeypatch.setattr(
        series_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: (
            series_calls.append({"path": path, **kwargs}) or {"result": 1}
        ),
    )
    restored = series_api.set_personal_group_growth_rule_series("课程小组", "default")
    assert restored["series"] == "default"
    assert series_calls[0]["data"]["mode"] == "default"
    assert series_calls[0]["data"]["rules"] == "[]"


def test_personal_group_member_read_contracts(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    landing = type("Landing", (), {"url": "https://groupweb.chaoxing.com/pc/circle"})()
    group = {
        "bbs_id": "bbs-1",
        "group_id": "7",
        "name": "课程小组",
        "management_url": "https://groupweb.chaoxing.com/pc/circle/manage/index?bbsid=bbs-1",
    }
    monkeypatch.setattr(api, "_find_personal_group", lambda *args: group)
    monkeypatch.setattr(api, "_personal_groups_context", lambda: (object(), landing))
    calls: list[dict] = []

    def request(_session, path, _operation, **kwargs):
        calls.append({"path": path, **kwargs})
        if kwargs["params"]["page"] == 1:
            return {
                "status": True,
                "datas": {
                    "list": [
                        {
                            "id": 10,
                            "puid": 100,
                            "name": "创建者",
                            "manager": 5,
                            "joinTime": 1000,
                        },
                        {
                            "id": 11,
                            "puid": 101,
                            "personName": "普通成员",
                            "manager": 0,
                            "joinTime": 1100,
                        },
                    ],
                    "lastId": 11,
                    "lastJoinTime": 1100,
                    "lastPage": 0,
                },
            }
        return {
            "status": True,
            "datas": {
                "list": [{"id": 12, "puid": 102, "name": "管理员", "manager": 1}],
                "lastPage": 1,
            },
        }

    monkeypatch.setattr(api, "_personal_group_json_request", request)
    listing = api.list_personal_group_members("课程小组", search="成员")
    assert listing["count"] == 3
    assert listing["members"][0]["role"] == "creator"
    assert listing["members"][2]["role"] == "manager"
    assert calls[1]["params"]["lastId"] == "11"
    assert calls[1]["params"]["lastJoinTime"] == "1100"

    monkeypatch.setattr(api, "list_personal_group_members", lambda *args, **kwargs: listing)
    selected = api.read_personal_group_member("课程小组", "普通成员")["member"]
    assert selected["puid"] == "101"


def test_personal_group_bulk_import_contracts(monkeypatch, tmp_path) -> None:
    landing = type("Landing", (), {"url": "https://groupweb.chaoxing.com/pc/circle"})()
    raw_group = {
        "id": 7,
        "bbsid": "bbs-1",
        "name": "课程小组",
        "isCreater": 1,
        "isBulkImport": 1,
        "bulkImportnumber": 1,
        "bulkImportTime": 1788200000000,
        "effective": 30,
        "groupAuth": {"addMem": 1},
    }
    html = (
        '<script>window.obj={authUser:{"puid":100,"name":"创建者"},circle:'
        + json.dumps(raw_group, ensure_ascii=False)
        + "};</script>"
        '<a href="https://sharewh1.xuexi365.com/share/download/template?forceDownload=1">'
        "下载模板</a>"
    )

    class ManageResponse:
        url = "https://groupweb.chaoxing.com/pc/circle/manage/index?bbsid=bbs-1"
        content = html.encode()
        encoding = "utf-8"
        apparent_encoding = "utf-8"

        @staticmethod
        def raise_for_status() -> None:
            return None

    class ManageSession:
        @staticmethod
        def get(*args, **kwargs):
            return ManageResponse()

    status_api = ChaoxingAPI(Path("unused-cookies.json"))
    selected_group = status_api._normalize_personal_group(raw_group, 1)
    monkeypatch.setattr(status_api, "_find_personal_group", lambda *args: selected_group)
    monkeypatch.setattr(status_api, "_personal_groups_context", lambda: (ManageSession(), landing))
    status = status_api.read_personal_group_bulk_import_status("课程小组")
    assert status["enabled"] is True
    assert status["used_today"] == 1 and status["remaining_today"] == 2
    assert status["template_url"].startswith("https://sharewh1.xuexi365.com/")

    source = tmp_path / "source.xlsx"
    with zipfile.ZipFile(source, "w") as workbook:
        workbook.writestr("xl/workbook.xml", "<workbook/>")
        workbook.writestr("[Content_Types].xml", "<Types/>")
    workbook_bytes = source.read_bytes()

    class DownloadResponse:
        headers = {
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "Content-Disposition": 'attachment; filename="group-template.xlsx"',
        }

        @staticmethod
        def raise_for_status() -> None:
            return None

        @staticmethod
        def iter_content(chunk_size: int):
            return iter([workbook_bytes])

    class DownloadSession:
        @staticmethod
        def get(*args, **kwargs):
            return DownloadResponse()

    download_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        download_api, "read_personal_group_bulk_import_status", lambda *args: status
    )
    monkeypatch.setattr(download_api, "_session", DownloadSession)
    downloaded = download_api.download_personal_group_bulk_import_template(
        "课程小组", tmp_path / "downloaded.xlsx"
    )
    assert downloaded["byte_count"] == len(workbook_bytes)
    assert zipfile.is_zipfile(downloaded["output_path"])

    member_before = {
        "group": selected_group,
        "count": 1,
        "members": [{"member_id": "1", "puid": "100"}],
    }
    member_after = {
        "group": selected_group,
        "count": 2,
        "members": [
            {"member_id": "1", "puid": "100"},
            {"member_id": "2", "puid": "101", "name": "新增成员"},
        ],
    }
    refreshed_status = {**status, "used_today": 2, "remaining_today": 1}

    class ImportResponse:
        content = json.dumps({"result": True, "msg": "导入成功"}).encode()
        encoding = "utf-8"
        apparent_encoding = "utf-8"

        @staticmethod
        def raise_for_status() -> None:
            return None

    class ImportSession:
        @staticmethod
        def post(*args, **kwargs):
            return ImportResponse()

    import_api = ChaoxingAPI(Path("unused-cookies.json"))
    status_reads = iter([status, refreshed_status])
    member_reads = iter([member_before, member_after])
    monkeypatch.setattr(
        import_api,
        "read_personal_group_bulk_import_status",
        lambda *args: next(status_reads),
    )
    monkeypatch.setattr(import_api, "list_personal_group_members", lambda *args: next(member_reads))
    monkeypatch.setattr(import_api, "_personal_groups_context", lambda: (ImportSession(), landing))
    quota_calls: list[dict] = []
    monkeypatch.setattr(
        import_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: (
            quota_calls.append({"path": path, **kwargs}) or {"result": 1}
        ),
    )
    imported = import_api.bulk_import_personal_group_members("课程小组", source)
    assert imported["added_members"][0]["puid"] == "101"
    assert imported["quota"]["used_today"] == 2
    assert quota_calls[0]["path"].endswith("/bulkImportnumber")


def test_personal_group_module_configuration_contracts(monkeypatch) -> None:
    landing = type("Landing", (), {"url": "https://groupweb.chaoxing.com/pc/circle"})()
    raw_group = {
        "id": 7,
        "bbsid": "bbs-1",
        "name": "课程小组",
        "isCreater": 1,
        "groupAuth": {"showCircleSet": 1},
    }
    html = (
        '<script>window.obj={authUser:{"puid":100},circle:'
        + json.dumps(raw_group, ensure_ascii=False)
        + "};</script>"
        '<div class="centerConfiguration"><div class="configurationItem">'
        '<input data-type="2" checked>直播</div></div>'
        '<div class="popBottom"></div>'
    )

    class Response:
        content = html.encode()
        encoding = "utf-8"
        apparent_encoding = "utf-8"

        @staticmethod
        def raise_for_status() -> None:
            return None

    class Session:
        @staticmethod
        def get(*args, **kwargs):
            return Response()

    list_api = ChaoxingAPI(Path("unused-cookies.json"))
    group = list_api._normalize_personal_group(raw_group, 1)
    monkeypatch.setattr(list_api, "_find_personal_group", lambda *args: group)
    monkeypatch.setattr(list_api, "_personal_groups_context", lambda: (Session(), landing))
    listing = list_api.list_personal_group_modules("课程小组")
    assert listing["enabled_type_ids"] == [1, 2]
    assert listing["modules"][1]["name"] == "直播"

    update_api = ChaoxingAPI(Path("unused-cookies.json"))
    before = listing
    after = {**listing, "enabled_type_ids": [1]}
    reads = iter([before, after])
    monkeypatch.setattr(update_api, "list_personal_group_modules", lambda *args: next(reads))
    monkeypatch.setattr(update_api, "_session", object)
    calls: list[dict] = []
    monkeypatch.setattr(
        update_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: (
            calls.append({"path": path, **kwargs}) or {"result": 1}
        ),
    )
    updated = update_api.update_personal_group_modules("课程小组", [])
    assert updated["enabled_type_ids"] == [1]
    assert calls[0]["params"]["types"] == "1"


def test_personal_group_member_source_and_candidate_contracts(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    landing = type("Landing", (), {"url": "https://groupweb.chaoxing.com/pc/circle"})()
    group = {
        "bbs_id": "bbs-1",
        "group_id": "7",
        "name": "目标小组",
        "is_creator": True,
        "permissions": {"addMem": 1},
        "management_url": "https://groupweb.chaoxing.com/pc/circle/manage/index?bbsid=bbs-1",
    }
    monkeypatch.setattr(api, "_find_personal_group", lambda *args: group)
    monkeypatch.setattr(api, "_personal_groups_context", lambda: (object(), landing))
    calls: list[tuple[str, dict]] = []

    def request(_session, path, _operation, **kwargs):
        calls.append((path, kwargs))
        if path == "/pc/cmem/getCamType" and kwargs["params"]["camType"] == "circle":
            return {"status": True, "datas": [{"id": 8, "bbsid": "bbs-2", "name": "来源小组"}]}
        if path == "/pc/cmem/getCamType":
            return {"result": 1, "msg": [{"id": 9, "fid": 10, "name": "第一单位"}]}
        return {
            "result": 1,
            "data": [
                {
                    "id": 20,
                    "puid": 200,
                    "name": "候选成员",
                    "pic": "https://photo.example/200",
                    "hasJoinCircle": False,
                }
            ],
        }

    monkeypatch.setattr(api, "_personal_group_json_request", request)
    sources = api.list_personal_group_member_sources("目标小组")
    assert sources["count"] == 2
    assert sources["circle_sources"][0]["source_id"] == "8"
    assert sources["unit_sources"][0]["fid"] == "10"

    candidates = api.list_personal_group_member_candidates(
        "目标小组", source_type="circle", source="8", search="候选"
    )
    assert candidates["candidates"][0]["puid"] == "200"
    assert calls[-1][1]["params"]["circleId"] == "7"
    assert calls[-1][1]["allow_result"] is True


def test_personal_group_manager_permission_contracts(monkeypatch) -> None:
    landing = type("Landing", (), {"url": "https://groupweb.chaoxing.com/pc/circle"})()
    group = {
        "bbs_id": "bbs-1",
        "group_id": "7",
        "name": "目标小组",
        "is_creator": True,
        "permissions": {"addManager": 1},
        "management_url": "https://groupweb.chaoxing.com/pc/circle/manage/index?bbsid=bbs-1",
    }
    manager = ChaoxingAPI._normalize_personal_group_member(
        {"id": 11, "puid": 101, "name": "管理员", "manager": 1}, 1
    )
    read_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(read_api, "_find_personal_group", lambda *args: group)
    monkeypatch.setattr(
        read_api,
        "read_personal_group_member",
        lambda *args: {"member": manager},
    )
    monkeypatch.setattr(read_api, "_personal_group_account_puid", lambda *args: "100")
    monkeypatch.setattr(read_api, "_personal_groups_context", lambda: (object(), landing))
    monkeypatch.setattr(
        read_api,
        "_personal_group_json_request",
        lambda *args, **kwargs: {
            "status": True,
            "datas": {"authority": '{"showBarcode":1,"showSpeechSet":1}'},
        },
    )
    permissions = read_api.read_personal_group_member_permissions("目标小组", "101")
    assert permissions["permissions"]["showBarcode"] is True
    assert permissions["permissions"]["modifyExpose"] is False

    update_api = ChaoxingAPI(Path("unused-cookies.json"))
    before_permissions = {field: False for field in PERSONAL_GROUP_MANAGER_AUTHORITY_FIELDS}
    after_permissions = {**before_permissions, "showBarcode": True}
    reads = iter(
        [
            {"group": group, "member": manager, "permissions": before_permissions},
            {"group": group, "member": manager, "permissions": after_permissions},
        ]
    )
    monkeypatch.setattr(
        update_api,
        "read_personal_group_member_permissions",
        lambda *args: next(reads),
    )
    monkeypatch.setattr(update_api, "_personal_group_account_puid", lambda *args: "100")
    monkeypatch.setattr(update_api, "_personal_groups_context", lambda: (object(), landing))
    calls: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        update_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: calls.append((path, kwargs)) or {"status": True},
    )
    updated = update_api.update_personal_group_member_permissions(
        "目标小组", "101", {"showBarcode": True}
    )
    assert updated["permissions"]["showBarcode"] is True
    assert calls[0][0].endswith("/insertOrUpdateGroupAuthority")
    assert "%22showBarcode%22" in calls[0][1]["data"]["authority"]


def test_personal_group_member_mutation_contracts(monkeypatch) -> None:
    landing = type("Landing", (), {"url": "https://groupweb.chaoxing.com/pc/circle"})()
    group = {
        "bbs_id": "bbs-1",
        "group_id": "7",
        "name": "目标小组",
        "is_creator": True,
        "creator_puid": "100",
        "permissions": {"addMem": 1, "delMem": 1, "addManager": 1},
        "management_url": "https://groupweb.chaoxing.com/pc/circle/manage/index?bbsid=bbs-1",
    }
    ordinary = ChaoxingAPI._normalize_personal_group_member(
        {"id": 11, "puid": 101, "name": "普通成员", "manager": 0}, 1
    )
    manager = {**ordinary, "manager_level": 1, "role": "manager", "is_manager": True}

    manager_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(manager_api, "_find_personal_group", lambda *args: group)
    monkeypatch.setattr(
        manager_api,
        "list_personal_group_members",
        lambda *args, **kwargs: {"members": [ordinary]},
    )
    monkeypatch.setattr(manager_api, "_personal_group_account_puid", lambda *args: "100")
    monkeypatch.setattr(manager_api, "_personal_groups_context", lambda: (object(), landing))
    manager_calls: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        manager_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: (
            manager_calls.append((path, kwargs)) or {"status": True}
        ),
    )
    monkeypatch.setattr(
        manager_api,
        "read_personal_group_member",
        lambda *args: {"member": manager},
    )
    changed = manager_api.set_personal_group_member_manager_status("目标小组", "101", True)
    assert changed["member"]["is_manager"] is True
    assert manager_calls[0][0] == "/pc/cmem/setManager"
    assert manager_calls[0][1]["params"]["operate"] == "1"

    remove_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(remove_api, "_find_personal_group", lambda *args: group)
    listings = iter([{"members": [ordinary]}, {"members": []}])
    monkeypatch.setattr(remove_api, "list_personal_group_members", lambda *args: next(listings))
    monkeypatch.setattr(remove_api, "_personal_group_account_puid", lambda *args: "100")
    monkeypatch.setattr(remove_api, "_personal_groups_context", lambda: (object(), landing))
    remove_calls: list[str] = []
    monkeypatch.setattr(
        remove_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: remove_calls.append(path) or {"status": True},
    )
    assert remove_api.remove_personal_group_member("目标小组", "101")["removed"]["puid"] == "101"
    assert remove_calls == ["/pc/cmem/delMember"]

    add_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(add_api, "_find_personal_group", lambda *args: group)
    add_listings = iter([{"members": []}, {"members": [ordinary]}])
    monkeypatch.setattr(add_api, "list_personal_group_members", lambda *args: next(add_listings))
    monkeypatch.setattr(add_api, "_personal_groups_context", lambda: (object(), landing))
    add_calls: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        add_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: (
            add_calls.append((path, kwargs)) or {"status": True}
        ),
    )
    added = add_api.add_personal_group_members("目标小组", ["101"])
    assert added["count"] == 1
    assert add_calls[0][0] == "/pc/cmem/addMembers"

    transfer_api = ChaoxingAPI(Path("unused-cookies.json"))
    transferred_group = {**group, "is_creator": False, "creator_puid": "101"}
    groups = iter([group, transferred_group])
    monkeypatch.setattr(transfer_api, "_find_personal_group", lambda *args: next(groups))
    monkeypatch.setattr(
        transfer_api,
        "list_personal_group_members",
        lambda *args: {"members": [ordinary]},
    )
    monkeypatch.setattr(transfer_api, "_personal_groups_context", lambda: (object(), landing))
    transfer_calls: list[str] = []
    monkeypatch.setattr(
        transfer_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: transfer_calls.append(path) or {"status": True},
    )
    transferred = transfer_api.transfer_personal_group_creator("目标小组", "101")
    assert transferred["group"]["creator_puid"] == "101"
    assert transfer_calls == ["/pc/cmem/setCreater"]

    clear_api = ChaoxingAPI(Path("unused-cookies.json"))
    external = {**ordinary, "member_id": "12", "puid": "", "name": "外部成员"}
    monkeypatch.setattr(clear_api, "_find_personal_group", lambda *args: group)
    clear_listings = iter([{"members": [ordinary, external]}, {"members": [ordinary]}])
    monkeypatch.setattr(
        clear_api, "list_personal_group_members", lambda *args: next(clear_listings)
    )
    monkeypatch.setattr(clear_api, "_personal_groups_context", lambda: (object(), landing))
    clear_calls: list[str] = []
    monkeypatch.setattr(
        clear_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: clear_calls.append(path) or {"status": True},
    )
    cleared = clear_api.clear_personal_group_external_members("目标小组")
    assert cleared["removed_count"] == 1
    assert clear_calls == ["/pc/cmem/clearNonCXCmems"]


def test_personal_group_topic_read_contracts(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    group = {
        "bbs_id": "bbs-1",
        "name": "课程小组",
        "topics_url": "https://groupweb.chaoxing.com/pc/topic/topiclist/index?bbsid=bbs-1",
    }
    context = {
        "group": group,
        "session": object(),
        "landing_url": group["topics_url"],
        "landing_html": "",
        "url_token": "token-1",
    }
    monkeypatch.setattr(api, "_personal_group_topic_context", lambda *args: context)
    folder_payload = {
        "status": True,
        "datas": [
            {
                "id": 10,
                "folder_uuid": "folder-1",
                "pid": 0,
                "name": "讨论",
                "count": 1,
            }
        ],
    }
    topic_raw = {
        "id": 20,
        "uuid": "topic-1",
        "bbsid": "bbs-1",
        "title": "如何修改论文",
        "content": "先判断问题。",
        "top": 0,
    }

    def request(_session, path, _operation, **kwargs):
        if path.endswith("getFolderTree"):
            return folder_payload
        if path.endswith("getTopTopicList"):
            return {"status": True, "datas": []}
        if path.endswith("getTopicList"):
            return {
                "status": True,
                "datas": [topic_raw],
                "folder_list": [],
                "userAuth": {"operationAuth": {"reply": 1}},
                "poff": {"lastPage": 1},
            }
        if path.endswith("getTopReplyList") or path.endswith("getReplyList"):
            return {"status": True, "datas": [], "poff": {"lastPage": 1}}
        raise AssertionError(path)

    monkeypatch.setattr(api, "_personal_group_json_request", request)
    tree = api.list_personal_group_topic_folder_tree("课程小组")
    assert tree["folders"][0]["folder_uuid"] == "folder-1"
    listing = api.list_personal_group_topics("课程小组", folder="讨论")
    assert listing["topics"][0]["uuid"] == "topic-1"
    assert listing["folder"]["folder_id"] == "10"

    monkeypatch.setattr(
        api,
        "_discussion_topic_payload",
        lambda *args, **kwargs: (topic_raw, parse_discussion_topic(topic_raw)),
    )
    monkeypatch.setattr(api, "_session", lambda: object())
    detail = api.read_personal_group_topic("课程小组", "如何修改论文")
    assert detail["topic"]["content"] == "先判断问题。"
    assert detail["reply_count"] == 0
    monkeypatch.setattr(api, "_find_personal_group", lambda *args: group)
    direct = api.read_personal_group_topic("课程小组", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    assert direct["group"]["bbs_id"] == "bbs-1"
    assert direct["topic"]["uuid"] == "topic-1"


def test_personal_group_topic_mutation_contracts(monkeypatch) -> None:
    group = {
        "bbs_id": "bbs-1",
        "name": "课程小组",
        "topics_url": "https://groupweb.chaoxing.com/pc/topic/topiclist/index?bbsid=bbs-1",
    }
    topic_raw = {
        "id": 20,
        "uuid": "topic-1",
        "bbsid": "bbs-1",
        "title": "写作问题",
        "content": "先判断问题。",
        "userAuth": {
            "operationAuth": {"delete": 1, "reply": 1, "update": 1},
            "replyAuth": {"updateOwn": 1},
        },
    }
    topic = parse_discussion_topic(topic_raw)

    create_api = ChaoxingAPI(Path("unused-cookies.json"))
    context = {
        "group": group,
        "session": object(),
        "landing_url": group["topics_url"],
        "landing_html": "",
        "url_token": "token-1",
    }
    monkeypatch.setattr(create_api, "_personal_group_topic_context", lambda *args: context)
    create_calls: list[tuple[str, dict]] = []

    def create_request(_session, path, _operation, **kwargs):
        create_calls.append((path, kwargs))
        return {"status": True, "objs": {"uuid": "topic-1"}}

    monkeypatch.setattr(create_api, "_personal_group_json_request", create_request)
    monkeypatch.setattr(
        create_api,
        "_discussion_topic_payload",
        lambda *args, **kwargs: (topic_raw, topic),
    )
    created = create_api.create_personal_group_topic("课程小组", "写作问题", "先判断问题。")
    assert created["topic"]["uuid"] == "topic-1"
    assert create_calls[0][0].endswith("/addTopic")
    assert create_calls[0][1]["data"]["urlToken"] == "token-1"

    update_api = ChaoxingAPI(Path("unused-cookies.json"))
    updated_raw = {**topic_raw, "title": "课程写作问题", "content": "先修改论点。"}
    topic_payloads = iter(
        [
            (topic_raw, topic),
            (updated_raw, parse_discussion_topic(updated_raw)),
        ]
    )
    monkeypatch.setattr(
        update_api,
        "list_personal_group_topics",
        lambda *args, **kwargs: {"group": group, "topics": [topic]},
    )
    monkeypatch.setattr(update_api, "_session", lambda: object())
    monkeypatch.setattr(
        update_api,
        "_discussion_topic_payload",
        lambda *args, **kwargs: next(topic_payloads),
    )
    update_calls: list[dict] = []
    monkeypatch.setattr(
        update_api,
        "_personal_group_json_request",
        lambda *args, **kwargs: update_calls.append(kwargs) or {"status": True},
    )
    updated = update_api.update_personal_group_topic(
        "课程小组", "写作问题", title="课程写作问题", content="先修改论点。"
    )
    assert updated["topic"]["title"] == "课程写作问题"
    assert update_calls[0]["data"]["isRichText"] == "0"

    delete_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        delete_api,
        "read_personal_group_topic",
        lambda *args, **kwargs: {"group": group, "topic": topic, "replies": []},
    )
    monkeypatch.setattr(delete_api, "_session", lambda: object())
    delete_calls: list[str] = []
    monkeypatch.setattr(
        delete_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: delete_calls.append(path) or {"status": True},
    )
    monkeypatch.setattr(
        delete_api,
        "list_personal_group_topics",
        lambda *args, **kwargs: {"topics": []},
    )
    deleted = delete_api.delete_personal_group_topic("课程小组", "写作问题")
    assert deleted["deleted_topic"]["uuid"] == "topic-1"
    assert delete_calls[0].endswith("/topic-1/deleteTopic")

    reply_api = ChaoxingAPI(Path("unused-cookies.json"))
    created_reply = {
        "reply_id": "30",
        "uuid": "reply-1",
        "content": "先看论点。",
        "replies": [],
    }
    reply_reads = iter(
        [
            {"group": group, "topic": topic, "replies": []},
            {"group": group, "topic": topic, "replies": [created_reply]},
        ]
    )
    monkeypatch.setattr(
        reply_api,
        "read_personal_group_topic",
        lambda *args, **kwargs: next(reply_reads),
    )
    monkeypatch.setattr(
        reply_api,
        "_personal_group_topic_detail_context",
        lambda *args: {"session": object(), "detail_url": "detail", "url_token": "token-2"},
    )
    reply_calls: list[dict] = []
    monkeypatch.setattr(
        reply_api,
        "_personal_group_json_request",
        lambda *args, **kwargs: reply_calls.append(kwargs) or {"status": True, "datas": {}},
    )
    monkeypatch.setattr("chaoxing_agent.api.uuid4", lambda: type("U", (), {"hex": "reply-1"})())
    reply_result = reply_api.create_personal_group_topic_reply("课程小组", "写作问题", "先看论点。")
    assert reply_result["reply"]["uuid"] == "reply-1"
    assert reply_calls[0]["data"]["urlToken"] == "token-2"

    reply_update_api = ChaoxingAPI(Path("unused-cookies.json"))
    updated_reply = {**created_reply, "content": "先看中心论点。"}
    reply_update_reads = iter(
        [
            {"group": group, "topic": topic, "replies": [created_reply]},
            {"group": group, "topic": topic, "replies": [updated_reply]},
        ]
    )
    monkeypatch.setattr(
        reply_update_api,
        "read_personal_group_topic",
        lambda *args, **kwargs: next(reply_update_reads),
    )
    monkeypatch.setattr(
        reply_update_api,
        "_personal_group_topic_detail_context",
        lambda *args: {"session": object(), "detail_url": "detail", "url_token": "token-2"},
    )
    reply_update_calls: list[dict] = []
    monkeypatch.setattr(
        reply_update_api,
        "_personal_group_json_request",
        lambda *args, **kwargs: reply_update_calls.append(kwargs) or {"status": True},
    )
    reply_updated = reply_update_api.update_personal_group_topic_reply(
        "课程小组", "写作问题", "reply-1", "先看中心论点。"
    )
    assert reply_updated["reply"]["content"] == "先看中心论点。"
    assert reply_update_calls[0]["data"]["uuid"] == "reply-1"

    reply_delete_api = ChaoxingAPI(Path("unused-cookies.json"))
    delete_reads = iter(
        [
            {"group": group, "topic": topic, "replies": [created_reply]},
            {"group": group, "topic": topic, "replies": []},
        ]
    )
    monkeypatch.setattr(
        reply_delete_api,
        "read_personal_group_topic",
        lambda *args, **kwargs: next(delete_reads),
    )
    monkeypatch.setattr(
        reply_delete_api,
        "_personal_group_topic_detail_context",
        lambda *args: {"session": object(), "detail_url": "detail", "url_token": "token-2"},
    )
    reply_delete_calls: list[dict] = []
    monkeypatch.setattr(
        reply_delete_api,
        "_personal_group_json_request",
        lambda *args, **kwargs: reply_delete_calls.append(kwargs) or {"status": True},
    )
    reply_deleted = reply_delete_api.delete_personal_group_topic_reply(
        "课程小组", "写作问题", "reply-1"
    )
    assert reply_deleted["deleted_reply"]["uuid"] == "reply-1"
    assert reply_delete_calls[0]["params"]["uuid"] == "reply-1"


def test_personal_group_topic_folder_mutation_contracts(monkeypatch) -> None:
    group = {
        "bbs_id": "bbs-1",
        "name": "课程小组",
        "topics_url": "https://groupweb.chaoxing.com/pc/topic/topiclist/index?bbsid=bbs-1",
        "permissions": {
            "addTopicFolder": 1,
            "modifyTopicFolder": 1,
            "delTopicFolder": 1,
        },
    }
    context = {
        "group": group,
        "session": object(),
        "landing_url": group["topics_url"],
        "landing_html": "",
        "url_token": "token-1",
    }
    root_folder = {
        "index": 1,
        "folder_id": "10",
        "folder_uuid": "folder-1",
        "parent_id": "0",
        "name": "讨论",
        "path_ids": "0/",
        "topic_count": 0,
    }
    child_folder = {
        "index": 2,
        "folder_id": "11",
        "folder_uuid": "folder-2",
        "parent_id": "10",
        "name": "论文",
        "path_ids": "0/10/",
        "topic_count": 0,
    }

    create_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(create_api, "_personal_group_topic_context", lambda *args: context)
    create_trees = iter(
        [
            {"folders": []},
            {"folders": [root_folder]},
        ]
    )
    monkeypatch.setattr(
        create_api,
        "list_personal_group_topic_folder_tree",
        lambda *args: next(create_trees),
    )
    create_calls: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        create_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: (
            create_calls.append((path, kwargs)) or {"status": True}
        ),
    )
    created = create_api.create_personal_group_topic_folder("课程小组", "讨论")
    assert created["folder"]["folder_uuid"] == "folder-1"
    assert create_calls[0][0] == "/pc/topicFolder/addFolder"
    assert create_calls[0][1]["params"]["folderId"] == "0"

    rename_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(rename_api, "_personal_group_topic_context", lambda *args: context)
    renamed_folder = {**root_folder, "name": "课程讨论"}
    rename_trees = iter([{"folders": [root_folder]}, {"folders": [renamed_folder]}])
    monkeypatch.setattr(
        rename_api,
        "list_personal_group_topic_folder_tree",
        lambda *args: next(rename_trees),
    )
    rename_calls: list[dict] = []
    monkeypatch.setattr(
        rename_api,
        "_personal_group_json_request",
        lambda *args, **kwargs: rename_calls.append(kwargs) or {"status": True},
    )
    renamed = rename_api.rename_personal_group_topic_folder("课程小组", "讨论", "课程讨论")
    assert renamed["folder"]["name"] == "课程讨论"
    assert rename_calls[0]["params"]["folder_uuid"] == "folder-1"

    move_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(move_api, "_personal_group_topic_context", lambda *args: context)
    moved_folder = {**child_folder, "parent_id": "0", "path_ids": "0/"}
    move_trees = iter(
        [
            {"folders": [root_folder, child_folder]},
            {"folders": [root_folder, moved_folder]},
        ]
    )
    monkeypatch.setattr(
        move_api,
        "list_personal_group_topic_folder_tree",
        lambda *args: next(move_trees),
    )
    move_calls: list[dict] = []
    monkeypatch.setattr(
        move_api,
        "_personal_group_json_request",
        lambda *args, **kwargs: move_calls.append(kwargs) or {"status": True},
    )
    moved = move_api.move_personal_group_topic_folder("课程小组", "论文", "root")
    assert moved["folder"]["parent_id"] == "0"
    assert move_calls[0]["data"]["targetFolder_uuid"] == ""
    assert move_calls[0]["data"]["folderIds"] == "11"

    delete_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(delete_api, "_personal_group_topic_context", lambda *args: context)
    delete_trees = iter([{"folders": [root_folder]}, {"folders": []}])
    monkeypatch.setattr(
        delete_api,
        "list_personal_group_topic_folder_tree",
        lambda *args: next(delete_trees),
    )
    delete_calls: list[dict] = []
    monkeypatch.setattr(
        delete_api,
        "_personal_group_json_request",
        lambda *args, **kwargs: delete_calls.append(kwargs) or {"status": True},
    )
    deleted = delete_api.delete_personal_group_topic_folder("课程小组", "讨论")
    assert deleted["deleted_folder"]["folder_uuid"] == "folder-1"
    assert delete_calls[0]["params"]["folder_uuid"] == "folder-1"


def test_personal_group_topic_top_and_move_contracts(monkeypatch) -> None:
    group = {
        "bbs_id": "bbs-1",
        "name": "课程小组",
        "topics_url": "https://groupweb.chaoxing.com/pc/topic/topiclist/index?bbsid=bbs-1",
    }
    topic = {
        "topic_id": "20",
        "uuid": "topic-1",
        "title": "写作问题",
        "folder_id": "",
        "is_top": False,
        "permissions": {
            "operationAuth": {"topSet": 1, "addTopicToFolder": 1},
        },
    }

    top_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        top_api,
        "read_personal_group_topic",
        lambda *args, **kwargs: {"group": group, "topic": topic},
    )
    monkeypatch.setattr(top_api, "_session", lambda: object())
    top_calls: list[str] = []
    monkeypatch.setattr(
        top_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: top_calls.append(path) or {"status": True},
    )
    monkeypatch.setattr(
        top_api,
        "list_personal_group_topics",
        lambda *args, **kwargs: {"topics": [{**topic, "is_top": True}]},
    )
    topped = top_api.set_personal_group_topic_top_status("课程小组", "写作问题", True)
    assert topped["topic"]["is_top"] is True
    assert top_calls[0].endswith("/topic-1/set/top")

    move_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        move_api,
        "read_personal_group_topic",
        lambda *args, **kwargs: {"group": group, "topic": topic},
    )
    monkeypatch.setattr(move_api, "_session", lambda: object())
    destination = {
        "index": 1,
        "folder_id": "10",
        "folder_uuid": "folder-1",
        "parent_id": "0",
        "name": "讨论",
        "path_ids": "0/",
        "topic_count": 0,
    }
    monkeypatch.setattr(
        move_api,
        "list_personal_group_topic_folder_tree",
        lambda *args: {"folders": [destination]},
    )
    move_calls: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        move_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: (
            move_calls.append((path, kwargs)) or {"status": True}
        ),
    )
    monkeypatch.setattr(
        move_api,
        "list_personal_group_topics",
        lambda *args, **kwargs: {"topics": [{**topic, "folder_id": "10"}]},
    )
    moved = move_api.move_personal_group_topic("课程小组", "写作问题", "讨论")
    assert moved["destination_folder"]["folder_uuid"] == "folder-1"
    assert move_calls[0][0].endswith("/addTopicsToFolder")
    assert move_calls[0][1]["data"] == {
        "targetFolder_uuid": "folder-1",
        "uuids": "topic-1",
    }


def test_personal_group_topic_choice_praise_and_score_contracts(monkeypatch) -> None:
    group = {
        "bbs_id": "bbs-1",
        "name": "课程小组",
        "topics_url": "https://groupweb.chaoxing.com/pc/topic/topiclist/index?bbsid=bbs-1",
    }
    first = {
        "topic_id": "20",
        "uuid": "topic-1",
        "bbs_id": "bbs-1",
        "title": "问题一",
        "folder_id": "",
        "is_choice": False,
        "is_praised": False,
        "score": {"scoreRange": {"minscore": 0, "maxscore": 100}, "my_score": 0},
        "permissions": {"operationAuth": {"choiceSet": 1, "scoreSet": 1}},
    }
    second = {
        **first,
        "topic_id": "21",
        "uuid": "topic-2",
        "title": "问题二",
    }

    choice_api = ChaoxingAPI(Path("unused-cookies.json"))
    choice_reads = iter(
        [
            {"group": group, "topic": first},
            {"group": group, "topic": {**first, "is_choice": True}},
        ]
    )
    monkeypatch.setattr(choice_api, "read_personal_group_topic", lambda *args: next(choice_reads))
    monkeypatch.setattr(choice_api, "_session", lambda: object())
    choice_calls: list[str] = []
    monkeypatch.setattr(
        choice_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: choice_calls.append(path) or {"status": True},
    )
    chosen = choice_api.set_personal_group_topic_choice_status("课程小组", "问题一", True)
    assert chosen["topic"]["is_choice"] is True
    assert choice_calls == ["/pc/topic/topic-1/set/choice"]

    praise_api = ChaoxingAPI(Path("unused-cookies.json"))
    praise_reads = iter(
        [
            {"group": group, "topic": first},
            {"group": group, "topic": {**first, "is_praised": True}},
        ]
    )
    monkeypatch.setattr(praise_api, "read_personal_group_topic", lambda *args: next(praise_reads))
    monkeypatch.setattr(praise_api, "_session", lambda: object())
    praise_calls: list[str] = []
    monkeypatch.setattr(
        praise_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: praise_calls.append(path) or {"status": True},
    )
    praised = praise_api.set_personal_group_topic_praise_status("课程小组", "问题一", True)
    assert praised["topic"]["is_praised"] is True
    assert praise_calls == ["/pc/praise/topic-1/addTopicPraise"]

    score_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        score_api,
        "_list_all_personal_group_topics",
        lambda *args: {"group": group, "topics": [first, second]},
    )
    detailed_topics = iter([first, second])
    monkeypatch.setattr(
        score_api,
        "_discussion_topic_payload",
        lambda *args, **kwargs: ({}, next(detailed_topics)),
    )
    refreshed_topics = iter(
        [
            {"group": group, "topic": {**first, "score": {"my_score": 85}}},
            {"group": group, "topic": {**second, "score": {"my_score": 85}}},
        ]
    )
    monkeypatch.setattr(
        score_api, "read_personal_group_topic", lambda *args: next(refreshed_topics)
    )
    monkeypatch.setattr(score_api, "_session", lambda: object())
    score_calls: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        score_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: (
            score_calls.append((path, kwargs)) or {"status": True}
        ),
    )
    scored = score_api.set_personal_group_topics_score("课程小组", ["问题一", "问题二"], 85)
    assert [item["score"]["my_score"] for item in scored["topics"]] == [85, 85]
    assert score_calls[0][0] == "/pc/score/addTopicScoreByBatch"
    assert score_calls[0][1]["data"]["uuids"] == "topic-1,topic-2"


def test_personal_group_topic_and_folder_batch_contracts(monkeypatch) -> None:
    group = {
        "bbs_id": "bbs-1",
        "name": "课程小组",
        "topics_url": "https://groupweb.chaoxing.com/pc/topic/topiclist/index?bbsid=bbs-1",
        "is_creator": True,
    }
    first = {
        "topic_id": "20",
        "uuid": "topic-1",
        "bbs_id": "bbs-1",
        "title": "问题一",
        "folder_id": "",
        "permissions": {"operationAuth": {"addTopicToFolder": 1, "delete": 1}},
    }
    second = {**first, "topic_id": "21", "uuid": "topic-2", "title": "问题二"}
    destination = {
        "index": 1,
        "folder_id": "10",
        "folder_uuid": "folder-1",
        "parent_id": "0",
        "name": "讨论",
        "path_ids": "0/",
        "topic_count": 0,
    }

    move_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        move_api,
        "_list_all_personal_group_topics",
        lambda *args: {"group": group, "topics": [first, second]},
    )
    move_details = iter([first, second])
    monkeypatch.setattr(
        move_api,
        "_discussion_topic_payload",
        lambda *args, **kwargs: ({}, next(move_details)),
    )
    monkeypatch.setattr(
        move_api,
        "list_personal_group_topic_folder_tree",
        lambda *args: {"folders": [destination]},
    )
    monkeypatch.setattr(
        move_api,
        "list_personal_group_topics",
        lambda *args, **kwargs: {
            "topics": [
                {**first, "folder_id": "10"},
                {**second, "folder_id": "10"},
            ]
        },
    )
    monkeypatch.setattr(move_api, "_session", lambda: object())
    move_calls: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        move_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: (
            move_calls.append((path, kwargs)) or {"status": True}
        ),
    )
    moved = move_api.move_personal_group_topics("课程小组", ["问题一", "问题二"], "讨论")
    assert len(moved["topics"]) == 2
    assert move_calls[0][1]["data"]["uuids"] == "topic-1,topic-2"

    delete_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        delete_api,
        "_list_all_personal_group_topics",
        lambda *args: {"group": group, "topics": [first, second]},
    )
    delete_details = iter([first, second])
    monkeypatch.setattr(
        delete_api,
        "_discussion_topic_payload",
        lambda *args, **kwargs: ({}, next(delete_details)),
    )
    monkeypatch.setattr(delete_api, "_session", lambda: object())
    monkeypatch.setattr(
        delete_api,
        "list_personal_group_topics",
        lambda *args, **kwargs: {"topics": []},
    )
    delete_calls: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        delete_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: (
            delete_calls.append((path, kwargs)) or {"status": True}
        ),
    )
    deleted = delete_api.delete_personal_group_topics("课程小组", ["问题一", "问题二"])
    assert len(deleted["deleted_topics"]) == 2
    assert delete_calls[0][0].endswith("/batchDeleteTopics")

    folder_a = {
        "index": 1,
        "folder_id": "11",
        "folder_uuid": "folder-a",
        "parent_id": "10",
        "name": "论文",
        "path_ids": "0/10/",
        "topic_count": 0,
    }
    folder_b = {
        **folder_a,
        "index": 2,
        "folder_id": "12",
        "folder_uuid": "folder-b",
        "name": "读书会",
    }
    context = {
        "group": group,
        "session": object(),
        "landing_url": group["topics_url"],
    }
    folder_move_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(folder_move_api, "_personal_group_topic_context", lambda *args: context)
    folder_move_trees = iter(
        [
            {"folders": [folder_a, folder_b]},
            {
                "folders": [
                    {**folder_a, "parent_id": "0", "path_ids": "0/"},
                    {**folder_b, "parent_id": "0", "path_ids": "0/"},
                ]
            },
        ]
    )
    monkeypatch.setattr(
        folder_move_api,
        "list_personal_group_topic_folder_tree",
        lambda *args: next(folder_move_trees),
    )
    folder_move_calls: list[dict] = []
    monkeypatch.setattr(
        folder_move_api,
        "_personal_group_json_request",
        lambda *args, **kwargs: folder_move_calls.append(kwargs) or {"status": True},
    )
    folders_moved = folder_move_api.move_personal_group_topic_folders(
        "课程小组", ["论文", "读书会"], "root"
    )
    assert all(folder["parent_id"] == "0" for folder in folders_moved["folders"])
    assert folder_move_calls[0]["data"]["folderIds"] == "11,12"

    folder_delete_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(folder_delete_api, "_personal_group_topic_context", lambda *args: context)
    folder_delete_trees = iter(
        [
            {"folders": [folder_a, folder_b]},
            {"folders": []},
        ]
    )
    monkeypatch.setattr(
        folder_delete_api,
        "list_personal_group_topic_folder_tree",
        lambda *args: next(folder_delete_trees),
    )
    folder_delete_calls: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        folder_delete_api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: (
            folder_delete_calls.append((path, kwargs)) or {"status": True}
        ),
    )
    folders_deleted = folder_delete_api.delete_personal_group_topic_folders(
        "课程小组", ["论文", "读书会"]
    )
    assert len(folders_deleted["deleted_folders"]) == 2
    assert folder_delete_calls[0][1]["data"]["folderIds"] == "11,12"


def test_personal_group_topic_draft_read_contract(monkeypatch) -> None:
    group = {
        "bbs_id": "bbs-1",
        "name": "课程小组",
        "topics_url": "https://groupweb.chaoxing.com/pc/topic/topiclist/index?bbsid=bbs-1",
    }
    raw = {
        "uuid": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "bbsid": "bbs-1",
        "title": "草稿标题",
        "content": "草稿正文",
        "rtf_content": "<p>草稿正文</p>",
        "folderId": 10,
        "img_data": [],
        "attachment": [],
        "labelList": [],
    }
    html = (
        '<input type="hidden" name="isEdit" value="0">'
        f"<script>window.obj = {{topic:{json.dumps(raw, ensure_ascii=False)},"
        "isManager:true};</script>"
    )

    class Response:
        content = html.encode()
        encoding = "utf-8"
        apparent_encoding = "utf-8"
        url = "https://groupweb.chaoxing.com/pc/topic/jumpToUpdateTopicDraft"

        @staticmethod
        def raise_for_status() -> None:
            return None

    class Session:
        @staticmethod
        def get(*args, **kwargs):
            return Response()

    api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        api,
        "_personal_group_topic_context",
        lambda *args: {
            "group": group,
            "session": Session(),
            "landing_url": group["topics_url"],
        },
    )
    result = api.read_personal_group_topic_draft("课程小组", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    assert result["draft"]["title"] == "草稿标题"
    assert result["draft"]["folder_id"] == "10"
    assert result["draft"]["is_edit"] is False


def test_personal_group_topic_draft_save_list_and_publish_contracts(monkeypatch, tmp_path) -> None:
    group = {
        "bbs_id": "bbs-1",
        "name": "课程小组",
        "topics_url": "https://groupweb.chaoxing.com/pc/topic/topiclist/index?bbsid=bbs-1",
    }
    context = {
        "group": group,
        "session": object(),
        "landing_url": group["topics_url"],
        "landing_html": "",
        "url_token": "token-1",
    }
    api = ChaoxingAPI(Path("unused-cookies.json"), state_file=tmp_path / "state.json")
    monkeypatch.setattr(api, "_personal_group_topic_context", lambda *args: context)
    calls: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        api,
        "_personal_group_json_request",
        lambda _session, path, *args, **kwargs: (
            calls.append((path, kwargs)) or {"status": True, "msg": "ok"}
        ),
    )

    def read_draft(_group, draft_uuid):
        return {
            "group": group,
            "draft": {
                "draft_uuid": draft_uuid,
                "bbs_id": "bbs-1",
                "title": "草稿标题",
                "content": "草稿正文",
                "rtf_content": "<p>草稿正文</p>",
                "folder_id": "0",
                "is_edit": False,
                "images": [],
                "attachments": [],
                "labels": [],
            },
        }

    monkeypatch.setattr(api, "read_personal_group_topic_draft", read_draft)
    saved = api.save_personal_group_topic_draft("课程小组", "草稿标题", "草稿正文")
    draft_uuid = saved["draft"]["draft_uuid"]
    assert calls[0][0] == "/pc/topic/addTopicDraft"
    assert calls[0][1]["params"]["uuid"] == draft_uuid
    assert calls[0][1]["data"]["isRichText"] == "1"

    monkeypatch.setattr(api, "_find_personal_group", lambda *args: group)
    listing = api.list_personal_group_topic_drafts("课程小组")
    assert listing["count"] == 1
    assert listing["drafts"][0]["draft_uuid"] == draft_uuid

    published_topic = {
        "uuid": draft_uuid,
        "title": "草稿标题",
        "content": "草稿正文",
    }
    monkeypatch.setattr(
        api,
        "_discussion_topic_payload",
        lambda *args, **kwargs: ({}, published_topic),
    )
    published = api.publish_personal_group_topic_draft("课程小组", "草稿标题")
    assert published["topic"]["uuid"] == draft_uuid
    assert calls[-1][0].endswith("/addTopic")
    assert calls[-1][1]["data"]["urlToken"] == "token-1"
    assert api._read_local_state()["topic_drafts"] == []


def test_personal_contacts_read_contracts(monkeypatch) -> None:
    landing = type("Landing", (), {"url": "https://contactsyd.chaoxing.com/pc/contacts/home"})()
    api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(api, "_contacts_context", lambda: (object(), landing))

    def contact_request(_session, path, _operation, **kwargs):
        if path.endswith("getUnits"):
            return {"result": 1, "msg": [{"fid": 23080, "name": "吉林外国语大学"}]}
        if path.endswith("getCircles"):
            return {
                "result": 1,
                "msg": {
                    "list": [
                        {
                            "id": "group-1",
                            "bbsid": "bbs-1",
                            "name": "教师发展小组",
                            "memCount": 2,
                        }
                    ]
                },
            }
        if path.endswith("getJoinedChatgroups"):
            return {
                "result": 1,
                "msg": {
                    "lastPage": 1,
                    "list": [
                        {
                            "groupid": "chat-1",
                            "groupname": "张三、李四",
                            "disabled": "false",
                        }
                    ],
                },
            }
        if path.endswith("getDepts"):
            params = kwargs.get("params") or {}
            if params.get("type") == "custom" and not params.get("pid"):
                return {
                    "result": 1,
                    "msg": {
                        "list": [
                            {
                                "id": "team-1",
                                "fid": -1,
                                "name": "项目组",
                                "usercount": 1,
                                "isCreator": True,
                            }
                        ]
                    },
                }
            return {
                "result": 1,
                "msg": {
                    "list": [
                        {
                            "id": "dept-1",
                            "pid": "root",
                            "fid": 23080,
                            "name": "英语学院",
                            "usercount": 20,
                        }
                    ]
                },
            }
        if path.endswith("getFollowers"):
            return {
                "result": 1,
                "msg": {
                    "lastPage": 1,
                    "list": [
                        {
                            "uid": 12,
                            "puid": 34,
                            "name": "张三",
                            "isMyFollower": 1,
                            "isFollowedByMe": False,
                        }
                    ],
                },
            }
        if (
            path.endswith("getDeptUsers")
            or path.endswith("getCircleMembers")
            or path.endswith("getChatgroupMembers")
        ):
            return {
                "result": 1,
                "msg": {
                    "lastPage": 1,
                    "list": [{"uid": 12, "puid": 34, "name": "张三"}],
                },
            }
        raise AssertionError(path)

    monkeypatch.setattr(api, "_contacts_json_request", contact_request)
    assert api.list_contact_units()["units"][0]["fid"] == "23080"
    assert (
        api.list_contact_departments("23080", parent_id="root")["departments"][0]["name"]
        == "英语学院"
    )
    assert api.search_contact_people("张三")["people"][0]["puid"] == "34"
    assert api.list_contact_department_members("23080", "dept-1")["count"] == 1
    followers = api.list_contact_relations("followers")
    assert followers["people"][0]["is_my_follower"] is True
    assert api.list_contact_groups()["groups"][0]["bbs_id"] == "bbs-1"
    assert api.list_contact_group_members("教师发展小组")["count"] == 1
    assert api.list_contact_chatgroups()["chatgroups"][0]["chatgroup_id"] == "chat-1"
    assert api.list_contact_chatgroup_members("chat-1")["count"] == 1
    assert api.list_contact_teams()["teams"][0]["is_creator"] is True


def test_personal_contacts_mutation_contracts(monkeypatch) -> None:
    landing = type("Landing", (), {"url": "https://contactsyd.chaoxing.com/pc/contacts/home"})()
    person = {"index": 1, "puid": "34", "user_id": "12", "name": "张三"}
    team = {
        "index": 1,
        "team_id": "team-1",
        "fid": "-1",
        "name": "项目组",
        "is_creator": True,
    }

    follow_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(follow_api, "_resolve_known_contact_person", lambda query: person)
    monkeypatch.setattr(follow_api, "_contacts_context", lambda: (object(), landing))
    follow_calls: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        follow_api,
        "_contacts_json_request",
        lambda _session, path, _operation, **kwargs: (
            follow_calls.append((path, kwargs)) or {"result": 1, "msg": {}}
        ),
    )
    monkeypatch.setattr(
        follow_api,
        "list_contact_relations",
        lambda *args, **kwargs: {"people": [person]},
    )
    assert follow_api.set_contact_follow_status("张三", True)["followed"] is True
    assert follow_calls[0][0].endswith("addUserFollow")
    assert follow_calls[0][1]["params"]["followedPuid"] == "34"

    create_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(create_api, "_resolve_contact_people", lambda queries: [person])
    monkeypatch.setattr(create_api, "_contacts_context", lambda: (object(), landing))
    create_calls: list[dict] = []
    monkeypatch.setattr(
        create_api,
        "_contacts_json_request",
        lambda *args, **kwargs: (
            create_calls.append(kwargs) or {"result": 1, "msg": {"id": "team-1"}}
        ),
    )
    monkeypatch.setattr(create_api, "_find_contact_team", lambda query: team)
    created = create_api.create_contact_team("项目组", ["张三"])
    assert created["team"]["team_id"] == "team-1"
    assert create_calls[0]["data"]["puids"] == "34,"

    rename_api = ChaoxingAPI(Path("unused-cookies.json"))
    renamed_team = {**team, "name": "新项目组"}
    team_reads = iter([team, renamed_team])
    monkeypatch.setattr(rename_api, "_find_contact_team", lambda query: next(team_reads))
    monkeypatch.setattr(rename_api, "_contacts_context", lambda: (object(), landing))
    rename_calls: list[dict] = []
    monkeypatch.setattr(
        rename_api,
        "_contacts_json_request",
        lambda *args, **kwargs: rename_calls.append(kwargs) or {"result": 1},
    )
    assert rename_api.rename_contact_team("team-1", "新项目组")["team"]["name"] == "新项目组"
    assert rename_calls[0]["data"]["deptId"] == "team-1"

    member_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(member_api, "_find_contact_team", lambda query: team)
    monkeypatch.setattr(member_api, "_resolve_contact_people", lambda queries: [person])
    monkeypatch.setattr(member_api, "_contacts_context", lambda: (object(), landing))
    member_calls: list[dict] = []
    monkeypatch.setattr(
        member_api,
        "_contacts_json_request",
        lambda *args, **kwargs: member_calls.append(kwargs) or {"result": 1},
    )
    monkeypatch.setattr(
        member_api,
        "list_contact_team_members",
        lambda *args, **kwargs: {"team": team, "people": [person], "count": 1},
    )
    added = member_api.add_contact_team_members("team-1", ["张三"])
    assert added["added"][0]["puid"] == "34"
    assert member_calls[0]["data"]["addPuids"] == "34,"

    remove_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(remove_api, "_find_contact_team", lambda query: team)
    member_reads = iter(
        [
            {"team": team, "people": [person], "count": 1},
            {"team": team, "people": [], "count": 0},
        ]
    )
    monkeypatch.setattr(
        remove_api, "list_contact_team_members", lambda *args, **kwargs: next(member_reads)
    )
    monkeypatch.setattr(remove_api, "_contacts_context", lambda: (object(), landing))
    remove_calls: list[dict] = []
    monkeypatch.setattr(
        remove_api,
        "_contacts_json_request",
        lambda *args, **kwargs: remove_calls.append(kwargs) or {"result": 1},
    )
    removed = remove_api.remove_contact_team_member("team-1", "张三")
    assert removed["removed"]["puid"] == "34"
    assert remove_calls[0]["data"]["deletePuid"] == "34"

    delete_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(delete_api, "_find_contact_team", lambda query: team)
    monkeypatch.setattr(delete_api, "_contacts_context", lambda: (object(), landing))
    monkeypatch.setattr(delete_api, "_contacts_json_request", lambda *args, **kwargs: {"result": 1})
    monkeypatch.setattr(delete_api, "list_contact_teams", lambda: {"teams": []})
    assert delete_api.delete_contact_team("team-1")["deleted"]["team_id"] == "team-1"

    exit_api = ChaoxingAPI(Path("unused-cookies.json"))
    joined_team = {**team, "is_creator": False}
    monkeypatch.setattr(exit_api, "_find_contact_team", lambda query: joined_team)
    monkeypatch.setattr(exit_api, "_contacts_context", lambda: (object(), landing))
    monkeypatch.setattr(exit_api, "_contacts_json_request", lambda *args, **kwargs: {"result": 1})
    monkeypatch.setattr(exit_api, "list_contact_teams", lambda: {"teams": []})
    assert exit_api.exit_contact_team("team-1")["exited"]["team_id"] == "team-1"


def test_parse_grade_weight_configuration_all_modes() -> None:
    html = """
    <input type="hidden" id="weightType" value="1">
    <input type="hidden" id="weightId" value="61613313">
    <input type="hidden" id="visibleScore" value="1">
    <p class="classicMode switchMode">经典模式</p>
    <p class="taskMode switchMode tab-active">学习任务模式</p>
    <form id="weightForm">
      <input type="number" class="num" name="video" value="50">
      <input type="number" class="num" name="ceyan" value="25">
      <input type="number" class="num" name="bbs" value="25">
      <input type="number" id="activeLimit" value="300">
      <input type="checkbox" id="cleanConfigButton" checked>
    </form>
    <form id="taskWeightForm">
      <li class="flex no-base videoWeightDiv" data="video">
        <input type="number" class="weightInput" name="video" value="60">
      </li>
      <li class="flex no-base workWeightDiv" data="work" style="display: none">
        <input type="number" class="weightInput" name="work" value="40">
      </li>
      <input type="checkbox" id="cleanConfigButtonV2" checked>
    </form>
    """
    custom_payload = {
        "status": True,
        "data": {
            "cleanCustomScore": 1,
            "list": [
                {
                    "weightId": 10,
                    "name": "过程考核",
                    "weight": 100,
                    "children": [
                        {
                            "weightId": 11,
                            "name": "章节任务",
                            "weight": 60,
                            "weightTypeIndex": 0,
                            "settings": '{"job_finish_percent": 100}',
                        },
                        {
                            "weightId": 12,
                            "name": "作业",
                            "weight": 40,
                            "weightTypeIndex": 2,
                            "settings": {},
                        },
                    ],
                }
            ],
        },
    }
    result = parse_grade_weight_configuration(html, custom_payload)
    assert result["active_mode"] == "task"
    assert result["scores_visible_to_students"] is True
    assert result["profiles"]["classic"]["total_weight"] == 100
    assert result["profiles"]["classic"]["clean_direct_scores"] is True
    assert result["profiles"]["classic"]["settings"]["activeLimit"] == 300
    assert result["profiles"]["task"]["total_weight"] == 60
    assert result["profiles"]["task"]["components"][1]["available"] is False
    assert result["profiles"]["custom"]["total_weight"] == 100
    assert result["profiles"]["custom"]["groups"][0]["children"][0]["settings"] == {
        "job_finish_percent": 100
    }


def test_parse_grade_list_payload_distinguishes_weighted_and_raw_scores() -> None:
    initialization = {
        "weight": {
            "weightType": 0,
            "modelType": 0,
            "video": 50,
            "ceyan": 25,
            "bbs": 25,
        }
    }
    components = grade_component_schema(initialization)
    payload = {
        "code": 0,
        "data": [
            {
                "dataNo": 1,
                "personId": 410890414,
                "userid": "346130878",
                "loginName": "2024001686",
                "userName": "赵英竹",
                "img": "https://photo.chaoxing.com/p/346130878_80",
                "score": "72.03",
                "video": 50,
                "ceyan": 18.53,
                "bbs": 3.5,
                "customScore": "-1",
            }
        ],
        "pageInfo": {
            "currentPageNo": 1,
            "pagesize": 100,
            "totalPage": 1,
            "totalResult": 1,
        },
    }
    weighted, page = parse_grade_score_payload(payload, components, raw_scores=False)
    raw, _ = parse_grade_score_payload(payload, components, raw_scores=True)
    assert [item["label"] for item in components] == ["章节任务点", "章节测验", "讨论"]
    assert weighted[0]["total_score"] == 72.03
    assert weighted[0]["component_scores"][1]["value"] == 18.53
    assert weighted[0]["component_scores"][1]["value_kind"] == "weighted_contribution"
    assert weighted[0]["custom_score"] is None
    assert raw[0]["total_score"] is None
    assert raw[0]["component_scores"][0]["value_kind"] == "raw_score"
    assert page == {"page": 1, "page_size": 100, "total_pages": 1, "total_count": 1}


def test_parse_grade_summary_and_statistics_navigation() -> None:
    summary = parse_grade_summary_payload(
        {
            "studentNum": 31,
            "count": 31,
            "avg": 73,
            "min": 45,
            "max": 82,
            "array": [{"name": "80分及以上", "value": 5}],
            "firstScoreUpper": 80,
            "secondScoreUpper": 80,
            "secondScoreLower": 60,
            "thirdScoreUpper": 60,
        }
    )
    navigation = parse_statistics_navigation(
        {
            "status": True,
            "data": [
                {
                    "name": "学生成绩",
                    "show": True,
                    "sort": 4,
                    "url": "https://stat2-ans.chaoxing.com/score-data/index?courseid=1",
                }
            ],
        }
    )
    assert summary["average"] == 73
    assert summary["distribution"][0] == {"label": "80分及以上", "count": 5}
    assert navigation[0]["visible"] is True
    assert "/score-data/index" in navigation[0]["url"]


def test_parse_grade_visibility_payload_keeps_only_actionable_fields() -> None:
    result = parse_grade_visibility_payload(
        {
            "openScore": {
                "openCheck": True,
                "openScoreTime": "2026-09-01 08:00",
                "viewRankCheck": True,
                "viewClazzAvgScoreCheck": False,
            },
            "data": [
                {
                    "id": 125882448,
                    "name": "英语2401",
                    "studentCount": 31,
                    "visibleScore": 1,
                    "isFiled": 0,
                    "isStart": True,
                    "irrelevant": "not returned",
                }
            ],
        }
    )
    assert result["scheduled_open"] is True
    assert result["students_can_view_rank"] is True
    assert result["visible_class_count"] == 1
    assert result["classes"][0] == {
        "clazz_id": "125882448",
        "clazz_name": "英语2401",
        "student_count": 31,
        "scores_visible": True,
        "archived": False,
        "active": True,
    }


def test_parse_learning_progress_payload_normalizes_counts_and_minutes() -> None:
    students, page = parse_learning_progress_payload(
        {
            "code": 0,
            "data": [
                {
                    "dataNo": 1,
                    "personId": 410890414,
                    "userid": "346130878",
                    "loginName": "2024001686",
                    "userName": "赵英竹",
                    "job": "63/63",
                    "totalTime": "2 小时 1.5 分钟",
                    "ceyan": "7/22",
                    "work": "1/1",
                    "exam": "1/1",
                    "attend": "1/1",
                    "pbl": "0",
                    "active": 3,
                    "bbs": 6,
                    "visitTime": 44,
                    "readTime": "1.6 分钟",
                    "liveTime": "0 分钟",
                    "cxClass": "0 分钟",
                }
            ],
            "pageInfo": {
                "currentPageNo": 1,
                "pagesize": 100,
                "totalPage": 1,
                "totalResult": 1,
            },
        }
    )
    assert students[0]["task_points"] == {"completed": 63, "total": 63, "display": "63/63"}
    assert students[0]["video_view_minutes"] == 121.5
    assert students[0]["chapter_quizzes"]["completed"] == 7
    assert students[0]["discussion_activity_value"] == 6
    assert page["total_count"] == 1


def test_parse_study_monitor_payload_preserves_anomaly_state() -> None:
    students, page, appeal_count = parse_study_monitor_payload(
        {
            "code": 0,
            "data": [
                {
                    "dataNo": 1,
                    "personId": 410668292,
                    "userid": "345962414",
                    "loginName": "2024002794",
                    "userName": "蔡佳妍",
                    "studyStatus": 1,
                    "unnormalType": 4,
                    "unnormalTypeDescript": "考试",
                    "unnormalCount": 1,
                    "dealType": 0,
                    "dealCount": 0,
                }
            ],
            "pageInfo": {
                "currentPageNo": 1,
                "pagesize": 100,
                "totalPage": 1,
                "totalResult": 1,
            },
            "appealCount": 2,
        }
    )
    assert students[0]["study_status"] == "abnormal"
    assert students[0]["anomaly_type"] == "考试"
    assert students[0]["can_clear_anomaly"] is True
    assert page["total_count"] == 1
    assert appeal_count == 2
    assert resolve_study_monitor_student(students, "2024002794")["person_id"] == "410668292"


def test_statistics_module_url_uses_exact_runtime_parameters() -> None:
    url = ChaoxingAPI._module_url(
        {
            "final_url": "https://mooc2-ans.chaoxing.com/course",
            "hidden": {"enc": "must-not-leak", "cpi": "485781386"},
        },
        {
            "module": "tj",
            "data_url": "https://stat2-ans.chaoxing.com/stat2-vue/stat",
        },
        {"course_id": "254641935", "cpi": "485781386"},
        {"clazz_id": "125882448"},
    )
    assert url == (
        "https://stat2-ans.chaoxing.com/stat2-vue/stat?"
        "courseid=254641935&clazzid=125882448&cpi=485781386&ut=t"
    )


def test_knowledge_hub_module_url_preserves_signed_query_without_duplicates() -> None:
    signed = (
        "https://robot-lc.chaoxing.com/v1/front/goCourseKnowledgeBase?"
        "belongschoolid=23080&clazzId=800000001&courseId=900000001&"
        "courseName=%E8%AF%AD%E8%A8%80%E4%B8%8E%E6%B5%8B%E8%AF%95&"
        "cpi=485781386&enc=signed-value"
    )
    url = ChaoxingAPI._module_url(
        {
            "final_url": "https://mooc2-ans.chaoxing.com/course",
            "hidden": {"cpi": "485781386", "enc": "different-value"},
        },
        {"module": "knowledge_hub", "data_url": signed},
        {"course_id": "900000001", "cpi": "485781386"},
        {"clazz_id": "800000001"},
    )

    assert url == signed
    assert url.count("courseId=") == 1 and url.count("enc=") == 1


def test_module_url_places_parameters_before_spa_fragment() -> None:
    url = ChaoxingAPI._module_url(
        {
            "final_url": "https://mooc2-ans.chaoxing.com/course",
            "hidden": {"cpi": "485781386", "enc": "enc-1"},
        },
        {
            "module": "zsd",
            "data_url": "/topic-ans/knowgraph/index.html#/knowledgeMapTempPage",
        },
        {"course_id": "900000002", "cpi": "485781386"},
        {"clazz_id": "800000002"},
    )

    assert url.startswith(
        "https://mooc2-ans.chaoxing.com/topic-ans/knowgraph/index.html?"
        "courseid=900000002&clazzid=800000002"
    )
    assert url.endswith("#/knowledgeMapTempPage")


def test_parse_homework_items_preserves_counts_and_title() -> None:
    html = """
    <ul>
      <li id="work987">
        <a href="/mooc2-ans/work/mark?id=987&courseId=900000001">批阅</a>
        <span>第1周作业：语境词汇基础题</span>
        <span>英日2301-2302</span>
        <span>作答时间：08-27 16:50至 08-31 22:00</span>
        <span>3 待批 44 已交 17 未交</span>
        <button>修改设置</button>
      </li>
    </ul>
    """
    items = parse_homework_items(
        html,
        "https://mooc2-ans.chaoxing.com/mooc2-ans/work/list",
        {"clazz_name": "英日2301-2302"},
    )
    assert items == [
        {
            "work_id": "987",
            "title": "第1周作业：语境词汇基础题",
            "pending_count": 3,
            "submitted_count": 44,
            "unsubmitted_count": 17,
            "answer_time": "08-27 16:50至 08-31 22:00",
            "mark_url": (
                "https://mooc2-ans.chaoxing.com/mooc2-ans/work/mark?id=987&courseId=900000001"
            ),
        }
    ]
    assert resolve_homework(items, "987")["title"] == "第1周作业：语境词汇基础题"


def test_parse_homework_library_and_drafts() -> None:
    library_html = """
    <ul class="dataBody_td" data="20150798" type="0">
      <li><a class="rename_title" title="Diagram description">Diagram description</a>
      <span class="work_count">共 23 份</span></li>
      <li class="dataHead_questionNum">---</li><li class="dataHead_score">---</li>
      <li class="dataBody_read">邹红</li>
    </ul>
    <ul class="dataBody_td lib-td" data="work-1" type="1">
      <li><div onclick="viewWork('work-1', '0');"><a title="Process analysis">x</a></div></li>
      <li class="dataHead_questionNum">1</li><li class="dataHead_score">100</li>
      <li class="dataBody_read">张三</li>
      <li><a href="/mooc2-ans/work/goToWorkEditor?courseid=2&amp;workid=work-1">编辑</a></li>
    </ul>
    """
    items = parse_homework_library_items(library_html)
    assert items[0]["is_folder"] is True
    assert items[0]["child_count"] == 23
    assert items[1]["question_count"] == 1
    assert items[1]["score"] == 100
    for index, item in enumerate(items, 1):
        item["index"] = index
    assert resolve_homework_library_item(items, "Process analysis")["item_id"] == "work-1"

    draft_html = """
    <ul class="dataBody_td">
      <li><div class="dataBody_ellipsis draftsWork" title="Unit 1 draft">Unit 1 draft</div></li>
      <li class="dataBody_read">张三</li>
      <li class="dataBody_time">08-31 15:00</li>
      <li><a href="/mooc2-ans/work/goToWorkEditor?courseid=2&amp;workid=draft-1">编辑</a></li>
    </ul>
    """
    drafts = parse_homework_drafts(draft_html)
    drafts[0]["index"] = 1
    assert drafts[0]["created_at"] == "08-31 15:00"
    assert resolve_homework_draft(drafts, "draft-1")["title"] == "Unit 1 draft"


def test_parse_homework_editor_outline_and_resolve_targets() -> None:
    html = """
    <form id="workForm">
      <input type="hidden" id="workid" name="workid" value="work-1">
      <input type="hidden" id="directoryid" name="directoryid" value="0">
      <input type="hidden" id="grading" name="grading" value="0">
      <input type="hidden" id="questionGroup" name="questionGroup" value="0">
      <input type="hidden" id="workUsed" value="false">
      <input type="text" id="title" name="title" value="Unit 1">
      <div class="catalogDiv relationLi" id="relation-1" data="0" typeId="0">
        <input type="hidden" name="qTypeValue" value="0" courseQuestionTypeId="0">
        <label class="questionTypeNum">1</label> 单选题
        <input class="questionScore" type="text" value="5.0">
        <ul class="typeList">
          <li id="question-1" data="1" qidx="1"
              onclick="viewQuestion('question-1','0','0','relation-1');">
            <span class="queliTitle">Which option...</span>
          </li>
        </ul>
      </div>
      <script>var fake = '<div class="catalogDiv" id="fake">';</script>
    </form>
    """
    outline = parse_homework_editor_outline(html)
    assert outline["work_id"] == "work-1"
    assert outline["title"] == "Unit 1"
    assert outline["question_count"] == 1
    assert outline["groups"][0]["question_type"] == "single_choice"
    assert outline["groups"][0]["total_score"] == 5
    question = resolve_homework_question(outline["questions"], "1")
    assert question["question_id"] == "question-1"
    assert question["relation_id"] == "relation-1"

    library = [{"item_id": "work-1", "title": "Unit 1", "is_folder": False}]
    drafts = [{"work_id": "draft-1", "title": "Unit 2"}]
    assert resolve_homework_editor_target(library, drafts, "Unit 1")["source"] == "library"
    assert resolve_homework_editor_target(library, drafts, "draft-1")["source"] == "draft"


def test_parse_homework_question_detail_for_core_types() -> None:
    choice = parse_homework_question_detail(
        """
        <input name="score" value="5.0">
        <textarea name="content">&lt;p&gt;Choose one.&lt;/p&gt;</textarea>
        <textarea name="A">&lt;p&gt;Alpha&lt;/p&gt;</textarea>
        <input name="defAnswer" type="radio" value="B" checked>
        <textarea name="B">&lt;p&gt;Beta&lt;/p&gt;</textarea>
        <textarea name="answerAnalysis">&lt;p&gt;Because beta.&lt;/p&gt;</textarea>
        <input name="difficulty" value="0.8">
        """,
        question_id="question-1",
        question_type_code="0",
        relation_id="relation-1",
        index=1,
    )
    assert choice["stem"] == "Choose one."
    assert choice["answer"] == "B"
    assert choice["options"][1] == {
        "label": "B",
        "text": "Beta",
        "html": "<p>Beta</p>",
        "correct": True,
    }
    assert choice["answer_analysis"] == "Because beta."
    assert choice["difficulty"] == 0.8

    fill = parse_homework_question_detail(
        """
        <textarea name="content">&lt;p&gt;Complete both blanks.&lt;/p&gt;</textarea>
        <textarea name="1">&lt;p&gt;first;one&lt;/p&gt;</textarea>
        <textarea name="2">&lt;p&gt;second;two&lt;/p&gt;</textarea>
        """,
        question_type_code="2",
    )
    assert [item["text"] for item in fill["answer"]] == ["first;one", "second;two"]

    true_false = parse_homework_question_detail(
        """
        <textarea name="content">&lt;p&gt;The statement is false.&lt;/p&gt;</textarea>
        <a onclick="checkTrueFalse(true);" class="num_option">A</a>
        <a onclick="checkTrueFalse(false);" class="num_option check_answer">B</a>
        """,
        question_type_code="3",
    )
    assert true_false["answer"] is False

    short = parse_homework_question_detail(
        """
        <textarea name="content">&lt;p&gt;Explain.&lt;/p&gt;</textarea>
        <textarea name="answer">&lt;p&gt;A model answer.&lt;/p&gt;</textarea>
        """,
        question_type_code="4",
    )
    assert short["answer"] == "A model answer."


def test_parse_submission_rows() -> None:
    html = """
    <input type="hidden" id="totalPage" value="2">
    <ul class="dataBody_td" id="answer-1" createId="person-1">
      <li><div class="py_name">张三</div></li>
      <li>20230001</li>
      <li>2026-08-31 10:20</li>
      <li>10.0.0.1</li>
      <li>已批</li>
      <li>张三</li>
      <li>批阅 打回</li>
      <input class="scoreInput" value="92" data="score-data">
      <button data="/mooc2-ans/work/library/review-work?answerId=answer-1">批阅</button>
    </ul>
    """
    rows, total_pages = parse_submission_rows(html)
    assert total_pages == 2
    assert rows[0]["answer_id"] == "answer-1"
    assert rows[0]["student_name"] == "张三"
    assert rows[0]["student_no"] == "20230001"
    assert rows[0]["score"] == "92"
    assert rows[0]["review_url"].endswith("review-work?answerId=answer-1")
    assert resolve_submission(rows, "20230001")["answer_id"] == "answer-1"


def test_parse_review_summary_extracts_answer_assets() -> None:
    html = """
    <input type="hidden" id="workAnswerId" value="answer-1">
    <input type="hidden" id="workId" value="work-1">
    <input type="hidden" id="fullScore" value="100">
    <dd class="stuAnswerWords">
      My answer.
      <img src="/upload/answer.png">
      <iframe class="attach-iframe" filename="essay.docx"
              filetype="docx" objectid="object-1"></iframe>
    </dd>
    """
    summary = parse_review_summary(html)
    assert summary["work_answer_id"] == "answer-1"
    assert summary["full_score"] == "100"
    assert summary["student_answers"][0]["text"] == "My answer."
    assert summary["answer_images"] == ["https://mooc2-ans.chaoxing.com/upload/answer.png"]
    assert summary["attachments"][0]["objectid"] == "object-1"


def test_parse_notice_payload() -> None:
    notices, next_value = parse_notice_payload(
        {
            "status": True,
            "notices": {
                "lastGetId": "notice-1",
                "list": [
                    {
                        "idCode": "notice-1",
                        "title": "第1周作业通知",
                        "content": "请按时完成。",
                        "createrName": "张三",
                        "sendTime": "2026-08-27 16:53:23",
                        "toNames": ["英日2301-2302"],
                        "count_all": 62,
                        "count_read": 39,
                    }
                ],
            },
        }
    )
    assert next_value == "notice-1"
    assert notices[0]["title"] == "第1周作业通知"
    assert notices[0]["recipient_count"] == 62
    assert notices[0]["read_count"] == 39
    notices[0]["index"] = 1
    assert resolve_notice(notices, "第1周作业通知")["notice_id"] == "notice-1"


def test_parse_notice_draft_payload_and_resolve() -> None:
    drafts, next_value, last_page = parse_notice_draft_payload(
        {
            "status": True,
            "draftList": [
                {
                    "id": 10942329,
                    "uuid": "draft-uuid",
                    "version": 2,
                    "title": "第2周通知草稿",
                    "content": "请预习第二章。",
                    "rtf_content": "<p>请预习第二章。</p>",
                    "sourceType": 14,
                    "operTypeStr": "add",
                    "sendTime": 4092688800000,
                    "toreceiver": '[{"type":4,"clazzId":"800000001","name":"英日2301"}]',
                    "attachment": "[]",
                    "content_imgs": "[]",
                    "draftParamVo": {
                        "uuid": "$CACG$notice-uuid",
                        "noticeTarget": '[{"classId":"800000001"}]',
                        "sendTime": 4092688800000,
                        "noticeSubmeterExtend": {
                            "allowComments": 0,
                            "orderlyReceive": (
                                '[{"name":"英日2301","opt":0,"clazzId":"800000001","type":4}]'
                            ),
                        },
                    },
                }
            ],
            "pagesOffset": {"lastValue": "cursor-1", "lastPage": True},
        }
    )
    assert next_value == "cursor-1"
    assert last_page is True
    assert drafts[0]["draft_id"] == "10942329"
    assert drafts[0]["is_scheduled"] is True
    assert drafts[0]["recipients"][0]["clazzId"] == "800000001"
    drafts[0]["index"] = 1
    assert resolve_notice_draft(drafts, "第2周通知草稿")["draft_uuid"] == "draft-uuid"


def test_parse_notice_send_time_uses_china_timezone_for_naive_input() -> None:
    timestamp = parse_notice_send_time("2099-01-02 03:04")
    assert timestamp == 4070977440000


def test_parse_exam_items() -> None:
    html = """
    <div class="taskList"><ul>
      <li data="8114284">
        <div class="list_li_content list_li_content_wid56"
             data="483895341" type="0" parallelpaper="0">
          <h2 class="list_li_tit color1">期中测试</h2>
          <div class="list_class fs14" title="英语2401">英语2401</div>
          <p><span>考试时间：2025-11-13 08:01 至 2025-11-13 11:40</span></p>
        </div>
        <p><span>0 待批</span><span>31 已交</span><span>0 未交</span></p>
        <a href="/mooc2-ans/exam/test/topublishsettings?id=8114284">修改设置</a>
        <a href="/mooc2-ans/exam/test/marklist?id=8114284&paperId=483895341">批阅</a>
      </li>
    </ul></div>
    """
    items = parse_exam_items(html, "https://mooc2-ans.chaoxing.com/mooc2-ans/exam/test")
    assert items[0]["exam_id"] == "8114284"
    assert items[0]["paper_id"] == "483895341"
    assert items[0]["title"] == "期中测试"
    assert items[0]["submitted_count"] == 31
    assert items[0]["mark_url"].endswith("id=8114284&paperId=483895341")
    items[0]["index"] = 1
    assert resolve_exam(items, "期中测试")["exam_id"] == "8114284"


def test_parse_exam_paper_library_items_and_resolve() -> None:
    html = """
    <ul class="dataBody_td" data="6256236" type="0">
      <li class="dataBody_disabled"></li><li class="dataBody_file"></li>
      <li class="dataBody_name"><a class="rename_title" onclick="searchDirec(6256236)">
        Argumentation
      </a></li>
      <li class="dataBody_read">---</li><li class="dataBody_down">---</li>
      <li class="dataBody_down">---</li><li class="dataBody_down">邹红</li>
      <li class="dataBody_down">---</li><li class="dataBody_time"></li>
    </ul>
    <ul class="dataBody_td" data="556080015" type="1" createruid="79371038">
      <li class="dataBody_check"></li>
      <li class="dataBody_name"><a id="paperTitle_556080015" class="rename_title"
        title="Process Analysis Test"
        onclick="paperLibLookPaper(0, 556080015, '0')">Process Analysis Test</a></li>
      <li class="dataBody_read">10</li><li class="dataBody_read">100.0</li>
      <li class="dataBody_down">中</li><li class="dataBody_down">邹红</li>
      <li class="dataBody_down">3</li><li class="dataBody_time">
        <a onclick="checkPaperAnswer(556080015,0,
          '/mooc2-ans/exam/test/topublish?paperid=556080015&amp;score=100.0')">发布</a>
      </li>
    </ul>
    """
    items = parse_exam_paper_library_items(html)
    assert len(items) == 2
    assert items[0] == {
        "item_id": "6256236",
        "folder_id": "6256236",
        "title": "Argumentation",
        "item_type": "folder",
        "is_folder": True,
        "creator": "邹红",
    }
    assert items[1]["paper_id"] == "556080015"
    assert items[1]["question_count"] == 10
    assert items[1]["total_score"] == 100
    assert items[1]["difficulty"] == "中"
    assert items[1]["creator"] == "邹红"
    assert items[1]["usage_count"] == 3
    assert items[1]["publish_url"].endswith("paperid=556080015&score=100.0")
    for index, item in enumerate(items, 1):
        item["index"] = index
    assert (
        resolve_exam_paper_library_item(items, "Process Analysis", folders=False)["paper_id"]
        == "556080015"
    )
    assert resolve_exam_paper_library_item(items, "1", folders=True)["folder_id"] == "6256236"


def test_parse_exam_paper_mixed_question_types() -> None:
    html = """
    <h2 class="lookTit fl">Sample Paper</h2>
    <div class="volumeLookDetails">总题量 <span class="colorBlue">3</span>，总分值
      <span class="colorBlue">25</span></div>
    <div class="typeDiv ans-cc">
      <h2 class="title">一、 单选题（共1题，5分）</h2>
      <p class="typeinfo">题型说明：Choose one.</p>
      <div class="stem_con" id="section101">1.<span class="colorShallow">
        (单选题，5分)</span><p>Which is correct?</p></div>
      <div class="stem_answer">
        <span class="num_option">A.</span><div class="answer_p"><p>Alpha</p></div>
        <span class="num_option">B.</span><div class="answer_p"><p>Beta</p></div>
      </div>
      <div class="answerDiv"><div class="answer_tit">答案：<p>B</p></div>
        <div class="complete_bom"><span>答案解析：</span>
          <div class="p_764"><p>Because B.</p></div></div>
        <div class="complete_bom"><span>难度：</span><p class="p_764">0.8 (易)</p></div>
        <div class="complete_bom"><span>知识点：</span>
          <p topicid="77">Process analysis</p></div>
      </div>
    </div>
    <div class="typeDiv ans-cc">
      <h2 class="title">二、 填空题与连线题（共2题，20分）</h2>
      <div class="stem_con" id="section102">2.<span class="colorShallow">
        (填空题，10分)</span><p>Complete <img src="/image.png"></p></div>
      <div class="answerDiv"><div class="stem_answer"><span>答案：</span>
        <div class="ans-wid-cRight"><p>first</p></div>
        <div class="ans-wid-cRight"><p>second</p></div></div>
        <div class="complete_bom"><span>难度：</span><p class="p_764">0.5 (中)</p></div>
      </div>
      <div class="stem_con" id="section103">3.<span class="colorShallow">
        (连线题，10分)</span><p>Match them.</p></div>
      <div class="stem_answer">
        <div class="line_wid_550"><div class="lineCt"><span>1.</span>
          <div><p>left</p></div></div></div>
        <div class="line_wid_550"><div class="lineCt"><span>A.</span>
          <div><p>right</p></div></div></div>
      </div>
      <div class="answerDiv"><div class="line_answer_ct">
        <span class="line_option">1</span><span class="line_center"></span>
        <span class="line_option_answer">A</span></div></div>
    </div>
    """
    paper = parse_exam_paper(html, "55")
    assert paper["title"] == "Sample Paper"
    assert paper["declared_question_count"] == 3
    assert paper["declared_total_score"] == 25
    assert paper["question_count"] == 3
    assert paper["computed_total_score"] == 25
    assert paper["group_count"] == 2
    first = paper["questions"][0]
    assert first["question_type"] == "single_choice"
    assert first["stem"] == "Which is correct?"
    assert first["options"][1] == {
        "label": "B",
        "content_html": "<p>Beta</p>",
        "content": "Beta",
    }
    assert first["answer"] == "B"
    assert first["analysis"] == "Because B."
    assert first["difficulty"] == 0.8
    assert first["topics"] == [{"topic_id": "77", "title": "Process analysis"}]
    fill = paper["questions"][1]
    assert [item["answer"] for item in fill["fill_answers"]] == ["first", "second"]
    assert fill["images"] == ["https://mooc2-ans.chaoxing.com/image.png"]
    matching = paper["questions"][2]
    assert matching["question_type"] == "matching"
    assert matching["matching_pairs"] == [{"left": "1", "right": "A"}]
    assert matching["matching_columns"][0][0]["content"] == "left"
    assert resolve_exam_paper_question(paper["questions"], "103")["number"] == 3


def test_parse_exam_editor_outline_ignores_templates_and_resolves_questions() -> None:
    html = """
    <input type="hidden" id="courseid" name="courseid" value="900000002">
    <input type="hidden" id="paperid" name="paperid" value="556080015">
    <input type="hidden" id="isOpen" name="isOpen" value="1">
    <input type="hidden" id="currPaperGroupId" value="0">
    <input type="hidden" id="questionGroup" value="0">
    <input type="hidden" id="serialNumberMode" value="0">
    <input type="hidden" id="itemSerialNumberMode" value="1">
    <input type="text" id="examPaperTitle" name="examPaperTitle" value="Unit 1 Test">
    <strong class="selectBox" id="selectBox"><p><span value="2">难</span></p></strong>
    <i id="totalQuestionNum">1</i><i id="questionScoreSum">5.0</i>
    <div class="catalogDiv volumeDiv">
      <div class="quesTypeBlock" id="relation-1" type="0">
        <div class="cata_tit">
          <input type="hidden" name="qTypeValue" value="0"
                 courseQuestionTypeId="0" systemType="0">
          <span class="questionTypeName">单选题</span>
          <input class="questionScore" value="5.0">
        </div>
        <div class="typeInfo_tit"><p title="Choose one.">题型说明</p></div>
        <ul class="typeList">
          <li id="question-1" onclick="doQuestionLiClick('question-1','0','0',false);">
            <span><span class="quesIndex">1</span>
              (<span class="quesScore">5.0</span>分)
              <span class="contentTitle">Which is...</span>
            </span>
          </li>
        </ul>
      </div>
    </div>
    <script type="text/x-jqote-template">
      <div class="quesTypeBlock" id="&lt;%=relationId%&gt;"></div>
    </script>
    """
    outline = parse_exam_editor_outline(html)
    assert outline["paper_id"] == "556080015"
    assert outline["title"] == "Unit 1 Test"
    assert outline["question_count"] == 1
    assert outline["total_score"] == 5
    assert outline["group_count"] == 1
    assert outline["difficulty_code"] == "2"
    assert outline["difficulty_label"] == "难"
    assert outline["serial_number_mode"] == "0"
    assert outline["item_serial_number_mode"] == "1"
    assert outline["groups"][0]["description"] == "Choose one."
    assert outline["groups"][0]["total_score"] == 5
    assert outline["groups"][0]["index"] == 1
    question = resolve_exam_editor_question(outline["questions"], "1")
    assert question["question_id"] == "question-1"
    assert question["relation_id"] == "relation-1"
    assert question["question_type"] == "single_choice"


def test_resolve_exam_question_type_and_reposition_identifiers() -> None:
    groups = [
        {
            "index": 1,
            "relation_id": "relation-1",
            "question_type_code": "0",
            "question_type": "single_choice",
            "question_type_label": "单选题",
            "description": "Choose one.",
        },
        {
            "index": 2,
            "relation_id": "relation-2",
            "question_type_code": "3",
            "question_type": "true_false",
            "question_type_label": "判断题",
            "description": "Decide whether it is true.",
        },
    ]
    assert resolve_exam_question_type_group(groups, "判断题")["relation_id"] == "relation-2"
    assert resolve_exam_question_type_group(groups, "relation-1")["index"] == 1
    assert reposition_identifier(["q1", "q2", "q3"], "q3", 1) == ["q3", "q1", "q2"]


def test_parse_exam_question_detail_for_core_types() -> None:
    choice = parse_exam_question_detail(
        """
        <input name="score" value="5.0">
        <textarea name="content">&lt;p&gt;Choose one.&lt;/p&gt;</textarea>
        <textarea name="A">&lt;p&gt;Alpha&lt;/p&gt;</textarea>
        <input name="defAnswer" type="radio" value="B" checked>
        <textarea name="B">&lt;p&gt;Beta&lt;/p&gt;</textarea>
        <textarea name="answerAnalysis">&lt;p&gt;Because beta.&lt;/p&gt;</textarea>
        <input name="difficulty" value="0.8"><input name="easy" value="0">
        """,
        question_id="question-1",
        question_type_code="0",
        relation_id="relation-1",
        index=1,
    )
    assert choice["stem"] == "Choose one."
    assert choice["answer"] == "B"
    assert choice["options"][1]["correct"] is True
    assert choice["answer_analysis"] == "Because beta."
    assert choice["difficulty"] == 0.8

    fill = parse_exam_question_detail(
        """
        <textarea name="content">&lt;p&gt;Complete both.&lt;/p&gt;</textarea>
        <textarea name="1">&lt;p&gt;first&lt;/p&gt;</textarea>
        <textarea name="2">&lt;p&gt;second&lt;/p&gt;</textarea>
        <span class="blankSubjectCheck checked_dx"></span>
        """,
        question_type_code="2",
    )
    assert [item["text"] for item in fill["answer"]] == ["first", "second"]
    assert fill["blank_subject"] is True

    true_false = parse_exam_question_detail(
        """
        <textarea name="content">&lt;p&gt;This is false.&lt;/p&gt;</textarea>
        <a onclick="checkTrueFalse(true);" class="num_option">A</a>
        <a onclick="checkTrueFalse(false);" class="num_option check_answer">B</a>
        """,
        question_type_code="3",
    )
    assert true_false["answer"] is False

    short = parse_exam_question_detail(
        """
        <textarea name="content">&lt;p&gt;Explain.&lt;/p&gt;</textarea>
        <textarea name="answer">&lt;p&gt;A model answer.&lt;/p&gt;</textarea>
        <input name="wordMinNum" value="20"><input name="wordnum" value="100">
        """,
        question_type_code="4",
    )
    assert short["answer"] == "A model answer."
    assert short["word_min"] == 20
    assert short["word_max"] == 100


def test_compose_exam_question_forms_match_core_editor_contracts() -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    editor = {"outline": {"is_open": "1"}}
    detail = """
      <input name="score" value="5"><textarea name="content">&lt;p&gt;Blank&lt;/p&gt;</textarea>
      <textarea name="answerAnalysis"></textarea><input name="difficulty" value="0.8">
      <input name="easy" value="0"><input name="topicId" value="0">
      <input name="schoolTopicIds" value=""><input name="labelIdArr" value="">
    """

    choice_form, choice_expected = api._compose_exam_question_form(
        editor,
        detail,
        {
            "course_id": "course-1",
            "paper_id": "paper-1",
            "question_id": "question-1",
            "relation_id": "relation-1",
            "question_type_code": "0",
        },
        stem="Choose one.",
        options=["Alpha", "Beta"],
        correct_answer="B",
        creating=True,
    )
    assert choice_form["typeId"] == "relation-1"
    assert choice_form["defAnswer"] == "B"
    assert choice_form["A"] == "<p>Alpha</p>"
    assert choice_form["B"] == "<p>Beta</p>"
    assert choice_form["Z"] == ""
    assert choice_expected["answer"] == "B"
    assert api._exam_question_save_path("0").endswith("editPaperSingleChoiceV2")

    fill_form, fill_expected = api._compose_exam_question_form(
        editor,
        detail,
        {
            "course_id": "course-1",
            "paper_id": "paper-1",
            "question_id": "question-2",
            "relation_id": "relation-2",
            "question_type_code": "2",
        },
        stem="Complete both.",
        answers=["first", "second"],
        creating=True,
    )
    assert fill_form["answer"] == "<p>first</p>★<p>second</p>"
    assert fill_expected["answer"][1] == {"blank": 2, "text": "second"}
    assert api._exam_question_save_path("2").endswith("editPaperBlankFillingV2")

    true_false_form, true_false_expected = api._compose_exam_question_form(
        editor,
        detail,
        {
            "course_id": "course-1",
            "paper_id": "paper-1",
            "question_id": "question-3",
            "relation_id": "relation-3",
            "question_type_code": "3",
        },
        stem="This is false.",
        answer="错",
        creating=True,
    )
    assert true_false_form["answer"] == "false"
    assert true_false_expected["answer"] is False

    short_form, short_expected = api._compose_exam_question_form(
        editor,
        detail,
        {
            "course_id": "course-1",
            "paper_id": "paper-1",
            "question_id": "question-4",
            "relation_id": "relation-4",
            "question_type_code": "4",
        },
        stem="Explain.",
        answer="A model answer.",
        creating=True,
    )
    assert short_form["answer"] == "<p>A model answer.</p>"
    assert short_expected["answer"] == "A model answer."
    assert api._exam_question_save_path("4").endswith("editPaperAnswerV2")


def test_exam_question_type_update_uses_current_editor_contracts(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    session = RecordingJSONSession()
    course = {"course_id": "course-1", "course_name": "Course", "cpi": "cpi-1"}
    clazz = {"clazz_id": "class-1", "clazz_name": "Class"}
    paper = {"paper_id": "paper-1", "title": "Paper"}
    before = {
        "index": 1,
        "relation_id": "relation-1",
        "question_type_code": "0",
        "question_type": "single_choice",
        "question_type_label": "单选题",
        "description": "Old",
        "total_score": 5,
        "questions": [],
    }
    after = {**before, "description": "Choose one.", "total_score": 20}
    contexts = iter(
        [
            {"outline": {"groups": [before]}, "referer": "https://editor/1"},
            {"outline": {"groups": [after]}, "referer": "https://editor/1"},
        ]
    )
    monkeypatch.setattr(api, "_session", lambda: session)
    monkeypatch.setattr(api, "_resolve_exam_editable_paper", lambda *args, **kwargs: ({}, paper))
    monkeypatch.setattr(api, "_exam_editor_context", lambda *args, **kwargs: next(contexts))

    result = api.update_exam_question_type(
        course,
        clazz,
        "Paper",
        "单选题",
        description="Choose one.",
        total_score=20,
    )

    assert result["after"]["description"] == "Choose one."
    assert session.calls[0][0:2] == (
        "GET",
        "https://mooc2-ans.chaoxing.com/mooc2-ans/exam/updateTypeDesc",
    )
    assert session.calls[0][2]["params"] == {
        "courseid": "course-1",
        "cpi": "cpi-1",
        "paperId": "paper-1",
        "typeId": "relation-1",
        "typeDsc": "Choose one.",
        "groupId": "0",
    }
    assert session.calls[1][1].endswith("/updatePaperLibraryRelationScore")
    assert session.calls[1][2]["data"]["paperLibraryRelationId"] == "relation-1"
    assert session.calls[1][2]["data"]["score"] == 20


def test_exam_question_and_type_reorder_submit_complete_orders(monkeypatch) -> None:
    course = {"course_id": "course-1", "course_name": "Course", "cpi": "cpi-1"}
    clazz = {"clazz_id": "class-1", "clazz_name": "Class"}
    paper = {"paper_id": "paper-1", "title": "Paper"}
    q1 = {"question_id": "q1", "relation_id": "r1", "index": 1, "preview": "One"}
    q2 = {"question_id": "q2", "relation_id": "r1", "index": 2, "preview": "Two"}
    group = {
        "index": 1,
        "relation_id": "r1",
        "question_type_code": "0",
        "question_type": "single_choice",
        "question_type_label": "单选题",
        "questions": [q1, q2],
    }

    api = ChaoxingAPI(Path("unused-cookies.json"))
    session = RecordingJSONSession()
    contexts = iter(
        [
            {
                "outline": {"question_group": "0", "groups": [group], "questions": [q1, q2]},
                "referer": "https://editor/1",
            },
            {
                "outline": {
                    "question_group": "0",
                    "groups": [{**group, "questions": [q2, q1]}],
                    "questions": [q2, q1],
                },
                "referer": "https://editor/1",
            },
        ]
    )
    monkeypatch.setattr(api, "_session", lambda: session)
    monkeypatch.setattr(api, "_resolve_exam_editable_paper", lambda *args, **kwargs: ({}, paper))
    monkeypatch.setattr(api, "_exam_editor_context", lambda *args, **kwargs: next(contexts))
    moved = api.move_exam_question(course, clazz, "Paper", "q2", 1)
    assert moved["after_order"] == ["q2", "q1"]
    assert session.calls[0][1].endswith("/exam/movesort")
    assert session.calls[0][2]["data"]["questionids"] == "q2,q1"

    type_api = ChaoxingAPI(Path("unused-cookies.json"))
    type_session = RecordingJSONSession()
    r2 = {**group, "index": 2, "relation_id": "r2", "question_type_label": "判断题"}
    type_contexts = iter(
        [
            {"outline": {"groups": [group, r2]}, "referer": "https://editor/1"},
            {"outline": {"groups": [r2, group]}, "referer": "https://editor/1"},
        ]
    )
    monkeypatch.setattr(type_api, "_session", lambda: type_session)
    monkeypatch.setattr(
        type_api, "_resolve_exam_editable_paper", lambda *args, **kwargs: ({}, paper)
    )
    monkeypatch.setattr(
        type_api, "_exam_editor_context", lambda *args, **kwargs: next(type_contexts)
    )
    moved_type = type_api.move_exam_question_type(course, clazz, "Paper", "r2", 1)
    assert moved_type["after_order"] == ["r2", "r1"]
    assert type_session.calls[0][1].endswith("/exam/papertype-movesort")
    assert type_session.calls[0][2]["data"]["relationids"] == "r2,r1"


def test_exam_question_type_delete_marks_relation_scope() -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    session = RecordingJSONSession()
    api._delete_exam_question_type_request(
        session,
        {"course_id": "course-1"},
        "paper-1",
        "relation-1",
        referer="https://editor/1",
    )
    assert session.calls[0][1].endswith("/exam/deleteDataFromFukPaper")
    assert session.calls[0][2]["data"] == {
        "courseid": "course-1",
        "paperLibraryId": "paper-1",
        "delParam": "relation-1",
        "isPaperLibraryRelation": "true",
        "groupId": "0",
    }


def test_parse_exam_submission_payload() -> None:
    rows = parse_exam_submission_payload(
        {
            "data": [
                {
                    "id": 167712668,
                    "createUserId": 410890414,
                    "createUserName": "赵英竹",
                    "loginName": "2024001686",
                    "answerScore": 90.8,
                    "rightRate": "---",
                    "receiveTime": "2025-11-13 09:08",
                    "submitTime": "2025-11-13 09:27",
                    "piyueTime": "2025-12-22 14:49",
                    "piyueUserName": "刁慧莹",
                    "examConsumeTime": "19分钟",
                    "submitStyle": "36.49.211.5/吉林",
                    "status": 3,
                    "mark": "已完成",
                    "tchPiYueExam": True,
                    "markUrl": "/mooc2-ans/exam/test/markpaper?id=167712668",
                }
            ]
        }
    )
    rows[0]["index"] = 1
    assert rows[0]["answer_id"] == "167712668"
    assert rows[0]["student_no"] == "2024001686"
    assert rows[0]["score"] == 90.8
    assert rows[0]["review_url"].endswith("markpaper?id=167712668")
    assert resolve_exam_submission(rows, "赵英竹")["student_no"] == "2024001686"


def test_parse_exam_answer_sheet_objective_and_subjective() -> None:
    html = """
    <input type="hidden" id="stuRealName" value="赵英竹">
    <input type="hidden" id="_title" value="期中测试">
    <input type="hidden" id="status" name="status" value="3">
    <input type="hidden" id="examFullScore" value="100.0">
    <input type="hidden" id="testPaperId" value="8114284">
    <input type="hidden" id="answerId" value="167712668">
    <input type="hidden" id="courseId" value="254641935">
    <input type="hidden" id="classId" value="125882448">
    <div class="questionWrap" index="1" name="单选题">
      <input type="hidden" value="1.5" id="input885038501">
      <input type="hidden" value="0" id="type885038501">
      <input type="hidden" value="1032941948" id="relationid885038501">
      <input type="hidden" value="21828884" id="recordid885038501">
      <h3 class="mark_name">1. <span class="colorShallow">(单选题, 1.5分)</span>
        <p>Which tense is most common?</p>
      </h3>
      <ul class="mark_letter">
        <li>A.<p>Past Tense</p></li><li>B.<p>Present Simple Tense</p></li>
      </ul>
      <span><i class="fontWeight">学生答案:</i> B</span>
      <input type="text" name="score885038501" value="1.5" readonly="readonly">
      <span><i class="fontWeight">正确答案:</i> B</span>
      <div class="AnalysisCon">Present simple describes habitual steps.</div>
    </div>
    <div class="questionWrap" index="2" name="简答题">
      <input type="hidden" value="2.5" id="input885038525">
      <input type="hidden" value="4" id="type885038525">
      <input type="hidden" value="21829361" id="recordid885038525">
      <div id="bbsStem_885038525"
        content='&lt;div&gt;&lt;p&gt;Write a thesis statement.&lt;/p&gt;&lt;/div&gt;'
        answer='&lt;div&gt;&lt;p&gt;Hand washing prevents illness.&lt;/p&gt;&lt;/div&gt;'
        rightanwer='&lt;div&gt;&lt;p&gt;Regular washing prevents illness.&lt;/p&gt;&lt;/div&gt;'>
      </div>
      <input type="text" name="score885038525" value="2.5" markStatus="1">
    </div>
    """
    sheet = parse_exam_answer_sheet(html)
    assert sheet["answer_id"] == "167712668"
    assert sheet["student_name"] == "赵英竹"
    assert sheet["question_count"] == 2
    assert sheet["questions"][0]["stem"] == "Which tense is most common?"
    assert sheet["questions"][0]["options"][1] == {
        "label": "B",
        "text": "Present Simple Tense",
    }
    assert sheet["questions"][0]["student_answer"] == "B"
    assert sheet["questions"][0]["correct_answer"] == "B"
    assert sheet["questions"][1]["question_type"] == "简答题"
    assert sheet["questions"][1]["student_answer"] == "Hand washing prevents illness."
    assert sheet["questions"][1]["correct_answer"] == "Regular washing prevents illness."


def test_parse_question_bank_directories_and_questions() -> None:
    html = """
    <ul>
      <li class="list directory showitems" data-type="folder" id="folder-1"
          courseid="254641935" isshare="0" createrid="112855604">
        <span class="dirname">Unit 8 Picture description</span>
        <span class="tips">公开</span>
        <span class="question-num">共 13 题</span>
        <span class="auth-name">邹红</span>
      </li>
      <li class="list questions questionBank showitems" data-type="que"
          id="question-1" index="0" courseid="254641935" originType="4" topicid="9">
        <span class="choose-name" title="Write the first paragraph.">题干</span>
        <div class="questions-details"><img src="/upload/prompt.png"></div>
        <iframe class="attach-iframe" filename="prompt.pdf" filetype="pdf"
                objectid="object-1"></iframe>
        <span class="overHidden1 choose" title="简答题">简答题</span>
        <span class="hard">0.7 (中)</span>
        <span class="dose">23</span>
        <span class="accuracy">-</span>
        <span class="auth-name">邹红</span>
      </li>
    </ul>
    """
    directories, questions = parse_question_bank_items(html)
    assert directories[0]["directory_id"] == "folder-1"
    assert directories[0]["question_count"] == 13
    assert questions[0]["question_id"] == "question-1"
    assert questions[0]["question_type"] == "简答题"
    assert questions[0]["stem"] == "Write the first paragraph."
    assert questions[0]["attachments"][0]["objectid"] == "object-1"


def test_parse_question_bank_question_details() -> None:
    html = """
    <li class="list questions questionBank" data-type="que" id="question-choice"
        index="59" courseid="254641935" originType="0" topicid="0">
      <span class="choose-name"
            title="How should you write a number at the start of a sentence?">Question</span>
      <div class="questions-details fontLabel">
        <div><p>How should you write a number at the start of a sentence?</p></div>
        <ul class="option">
          <li>A. <p>25 students were absent.</p></li>
          <li>B. <p>Twenty-five students were absent.</p></li>
        </ul>
        <div class="question clearfix">
          <p class="fontw">答案：</p><div class="question-box"> B </div>
        </div>
      </div>
      <ul class="question-titles question-titles1">
        <span class="overHidden1 choose" title="单选题">单选题</span>
        <span class="hard">0.8 (易)</span><span class="dose">70</span>
        <span class="accuracy">90%</span><span class="auth-name">邹红</span>
      </ul>
    </li>
    """
    _, questions = parse_question_bank_items(html)
    question = questions[0]
    assert question["question_id"] == "question-choice"
    assert question["question_type"] == "单选题"
    assert question["options"][1]["label"] == "B"
    assert question["options"][1]["text"] == "Twenty-five students were absent."
    assert question["answer"] == "B"
    assert resolve_question_bank_question(questions, "question-choice")["answer"] == "B"


def test_parse_question_bank_directory_tree_and_resolve_paths() -> None:
    directories = parse_question_bank_directory_tree(
        {
            "directorysMap": {
                "0": [
                    {
                        "id": 10,
                        "dirName": "Unit 1",
                        "pid": 0,
                        "courseId": 20,
                        "questionCount": 3,
                        "examNum": 1,
                        "isOpen": 1,
                        "isShare": 2,
                        "top": 1,
                    }
                ],
                "10": [
                    {
                        "id": 11,
                        "dirName": "Review",
                        "pid": 10,
                        "courseId": 20,
                        "questionCount": 2,
                    }
                ],
            }
        }
    )
    assert directories[0]["is_top"] is True
    assert directories[0]["child_count"] == 1
    assert directories[1]["path"] == "Unit 1 / Review"
    assert resolve_question_bank_directory(directories, "Unit 1 / Review")["directory_id"] == "11"
    assert (
        resolve_question_bank_directory(directories, "root", allow_root=True)["directory_id"] == "0"
    )


def test_parse_question_bank_permission_teachers() -> None:
    html = """
    <div class="check-item" id="teacherList">
      <span class="ipt-checkbox" data="person-1"><input type="checkbox"></span>
      <span class="ipt-txt">邹红</span>
      <span class="ipt-checkbox" data="person-2"><input type="checkbox"></span>
      <span class="ipt-txt">张三</span>
    </div>
    """
    teachers = parse_question_bank_permission_teachers(html)
    assert teachers == [
        {"index": 1, "person_id": "person-1", "teacher_name": "邹红"},
        {"index": 2, "person_id": "person-2", "teacher_name": "张三"},
    ]


def test_parse_and_resolve_question_bank_question_types() -> None:
    html = """
    <li class="type-list courseQtype" typeid="type-1" systemtype="1"
        sort="0" origintype="0">
      <p class="overHidden1" title="单选题">单选题</p>
      <span class="resetName">重命名</span>
    </li>
    <li class="type-list courseQtype" typeid="type-2" systemtype="4"
        sort="1" origintype="4">
      <p class="overHidden1" title="术语解释">术语解释</p>
      <span class="resetName">重命名</span><span class="deleteType">删除</span>
    </li>
    """
    question_types = parse_question_bank_question_types(html)
    assert question_types[0]["base_type"] == "single_choice"
    assert question_types[1]["can_delete"] is True
    assert resolve_question_bank_question_type(question_types, "术语解释")["type_id"] == "type-2"


def test_question_bank_question_type_request_contract() -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    session = RecordingJSONSession()
    payload = api._question_bank_qtype_json_request(
        session,
        "/mooc2-ans/qbank/add-qtype",
        {
            "courseid": "course-1",
            "cpi": "cpi-1",
            "typename": "术语解释",
            "originType": "4",
            "pMessage": "false",
        },
        referer="https://qbank/1",
        operation="question-type creation",
    )
    assert payload["status"] is True
    assert session.calls[0][0] == "GET"
    assert session.calls[0][1].endswith("/qbank/add-qtype")
    assert session.calls[0][2]["params"]["originType"] == "4"


def test_parse_and_resolve_question_bank_labels() -> None:
    payload = {
        "status": True,
        "data": [
            {
                "id": 11,
                "parentId": 0,
                "name": "写作",
                "index": 1,
                "children": [
                    {
                        "id": 12,
                        "parentId": 11,
                        "name": "求职信",
                        "index": 2,
                    }
                ],
            }
        ],
    }
    labels = parse_question_bank_label_tree(payload)
    assert labels[0]["path"] == "写作"
    assert labels[0]["child_count"] == 1
    assert labels[1]["path"] == "写作 / 求职信"
    assert labels[1]["level"] == 2
    assert resolve_question_bank_label(labels, "求职信")["label_id"] == "12"
    assert resolve_question_bank_label(labels, "写作 / 求职信")["parent_id"] == "11"


def test_question_bank_label_endpoint_contracts() -> None:
    class LabelSession(RecordingJSONSession):
        def post(self, url: str, **kwargs):
            self.calls.append(("POST", url, kwargs))
            if url.endswith("/question-label/list"):
                return self._response(
                    {
                        "status": True,
                        "data": [{"id": 11, "parentId": 0, "name": "写作"}],
                        "checkedIds": [11],
                    }
                )
            return self._response({"status": True, "msg": "ok"})

    api = ChaoxingAPI(Path("unused-cookies.json"))
    session = LabelSession()
    course = {"course_id": "course-1", "cpi": "cpi-1"}
    listing = api._question_bank_label_listing(
        session,
        course,
        referer="https://qbank/1",
        question_id="question-1",
    )
    payload = api._question_bank_label_assignment_request(
        session,
        course,
        "question-1",
        ["11", "12"],
        sync_references=True,
        referer="https://qbank/1",
    )
    assert listing["checked_ids"] == ["11"]
    assert payload["status"] is True
    assert session.calls[0][1].endswith("/question-label/list")
    assert session.calls[0][2]["data"] == {
        "courseid": "course-1",
        "cpi": "cpi-1",
        "qid": "question-1",
    }
    assert session.calls[1][1].endswith("/qbank/update-label")
    assert session.calls[1][2]["params"]["labelIds"] == "11,12,"
    assert session.calls[1][2]["params"]["updateExamWord"] == "true"
    assert session.calls[1][2]["data"] == {"qids": "question-1"}


def test_parse_and_resolve_question_bank_topics() -> None:
    payload = {
        "status": True,
        "data": {
            "selects": [{"id": 22, "content": "Topic Sentence"}],
            "list": [
                {
                    "id": 21,
                    "parent": 0,
                    "content": "Paragraph Writing",
                    "type": 1,
                    "level": 2,
                    "hasSub": True,
                    "subList": [
                        {
                            "id": 22,
                            "parent": 21,
                            "content": "Topic Sentence",
                            "type": 0,
                            "level": 3,
                            "select": True,
                        }
                    ],
                }
            ],
        },
    }
    topics, selected_ids = parse_question_bank_topic_tree(payload)
    assert topics[0]["kind"] == "category"
    assert topics[0]["child_count"] == 1
    assert topics[1]["path"] == "Paragraph Writing / Topic Sentence"
    assert topics[1]["kind"] == "knowledge_point"
    assert topics[1]["selected"] is True
    assert selected_ids == ["22"]
    assert resolve_question_bank_topic(topics, "Topic Sentence")["topic_id"] == "22"
    assert resolve_question_bank_topic(topics, "Paragraph Writing")["node_type"] == "1"


def test_question_bank_topic_endpoint_contracts() -> None:
    class TopicSession(RecordingJSONSession):
        def get(self, url: str, **kwargs):
            self.calls.append(("GET", url, kwargs))
            return self._response(
                {
                    "status": True,
                    "data": {
                        "selects": [{"id": 22}],
                        "list": [
                            {
                                "id": 22,
                                "parent": 0,
                                "content": "Topic Sentence",
                                "type": 0,
                            }
                        ],
                    },
                }
            )

        def post(self, url: str, **kwargs):
            self.calls.append(("POST", url, kwargs))
            return self._response({"status": True, "msg": "ok"})

    api = ChaoxingAPI(Path("unused-cookies.json"))
    session = TopicSession()
    course = {"course_id": "course-1", "cpi": "cpi-1"}
    listing = api._question_bank_topic_listing(
        session,
        course,
        referer="https://qbank/1",
        question_id="question-1",
    )
    payload = api._question_bank_topic_assignment_request(
        session,
        course,
        "question-1",
        ["22", "23"],
        sync_references=True,
        referer="https://qbank/1",
    )
    assert listing["selected_ids"] == ["22"]
    assert payload["status"] is True
    assert session.calls[0][1].endswith("/question-topic/course")
    assert session.calls[0][2]["params"]["qid"] == "question-1"
    assert session.calls[1][1].endswith("/qbank/update-topic")
    assert session.calls[1][2]["params"]["topicIds"] == "22,23,"
    assert session.calls[1][2]["data"] == {
        "qids": "question-1",
        "updateExamWord": "true",
        "retainOldTopicRelation": "false",
    }


def test_parse_and_resolve_question_bank_inactive_items() -> None:
    payload = {
        "total": 2,
        "pageInfo": {"currentPageNo": 1, "totalPage": 1, "pagesize": 10},
        "dirPathList": [{"id": 10, "dirName": "Unit 1"}],
        "list": [
            {
                "id": 100,
                "type": 0,
                "createrName": "张三",
                "createTime": 1788000000000,
                "questionBankRelation": {
                    "id": 10,
                    "pid": 0,
                    "courseId": 20,
                    "dirName": "Unit 1",
                },
            },
            {
                "id": 101,
                "type": 1,
                "createrName": "张三",
                "createTime": 1788000001000,
                "questionBank": {
                    "id": "question-1",
                    "pid": 10,
                    "courseId": 20,
                    "content": "<p>Which is correct?</p>",
                    "courseQuestionTypeName": "单选题",
                    "originType": 0,
                    "easy": 1,
                },
            },
        ],
    }
    parsed = parse_question_bank_inactive_items(payload, state="recycle")
    assert parsed["items"][0]["item_type"] == "directory"
    assert parsed["items"][1]["name"] == "Which is correct?"
    assert parsed["items"][1]["difficulty"] == "中"
    assert parsed["path"] == [{"directory_id": "10", "name": "Unit 1"}]
    assert resolve_question_bank_inactive_item(parsed["items"], "question-1")["recycle_id"] == "101"


def test_question_bank_inactive_and_status_endpoint_contracts() -> None:
    class InactiveSession(RecordingJSONSession):
        def get(self, url: str, **kwargs):
            self.calls.append(("GET", url, kwargs))
            return self._response({"status": True, "msg": "ok"})

        def post(self, url: str, **kwargs):
            self.calls.append(("POST", url, kwargs))
            if url.endswith("/lock-search"):
                return self._response({"total": 0, "pageInfo": {}, "list": []})
            return self._response({"status": True, "msg": "ok"})

    api = ChaoxingAPI(Path("unused-cookies.json"))
    session = InactiveSession()
    course = {"course_id": "course-1", "cpi": "cpi-1"}
    listing = api._question_bank_inactive_page(
        session,
        course,
        referer="https://qbank/1",
        state="locked",
        page=2,
        search="topic",
        lock_time_filters=["today"],
    )
    api._question_bank_batch_status_request(
        session,
        course,
        question_ids=["question-1"],
        directory_ids=["dir-1"],
        status="3",
        referer="https://qbank/1",
        lock_from_active=True,
    )
    api._question_bank_batch_status_request(
        session,
        course,
        question_ids=["question-1"],
        directory_ids=[],
        status="0",
        referer="https://qbank/1",
    )
    assert listing["state"] == "locked"
    assert session.calls[0][1].endswith("/qbank/lock-search")
    assert session.calls[0][2]["data"]["pageNum"] == "2"
    assert session.calls[0][2]["data"]["lockTimeArr"] == "today"
    assert session.calls[1][0] == "POST"
    assert session.calls[1][2]["data"]["curStatus"] == "0"
    assert session.calls[2][0] == "GET"
    assert session.calls[2][2]["params"]["status"] == "0"


def test_question_bank_batch_type_update_contract() -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    session = RecordingJSONSession()
    before = {
        "question_id": "question-1",
        "index": 1,
        "origin_type": "0",
        "question_type": "单选题",
    }
    after = {**before, "origin_type": "4", "question_type": "简答题"}
    item_reads = iter(
        [
            {"questions": [before]},
            {"questions": [after]},
        ]
    )
    api._list_all_question_bank_items = lambda *args, **kwargs: next(item_reads)
    api._question_bank_landing_context = lambda *args, **kwargs: {
        "session": session,
        "landing_url": "https://qbank/1",
    }
    api._question_bank_question_types = lambda *args, **kwargs: [
        {
            "index": 1,
            "type_id": "type-4",
            "name": "简答题",
            "origin_type": "4",
            "system_type": "1",
        }
    ]
    result = api.update_question_bank_questions_type(
        {"course_id": "course-1", "course_name": "Course", "cpi": "cpi-1"},
        {"clazz_id": "class-1", "clazz_name": "Class"},
        ["question-1"],
        "简答题",
    )
    assert result["question_count"] == 1
    assert session.calls[0][1].endswith("/qbank/update-que-type")
    assert session.calls[0][2]["params"] == {
        "courseid": "course-1",
        "cpi": "cpi-1",
        "newQtype": "4",
        "typeId": "0",
    }
    assert session.calls[0][2]["data"] == {"qids": "question-1"}


def test_question_bank_batch_difficulty_update_contract() -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    session = RecordingJSONSession()
    before = [
        {"question_id": "question-1", "index": 1, "difficulty": "0.5（中）"},
        {"question_id": "question-2", "index": 2, "difficulty": "0.5（中）"},
    ]
    after = [
        {"question_id": "question-1", "index": 1, "difficulty": "0.8（易）"},
        {"question_id": "question-2", "index": 2, "difficulty": "0.8（易）"},
    ]
    item_reads = iter([{"questions": before}, {"questions": after}])
    api._list_all_question_bank_items = lambda *args, **kwargs: next(item_reads)
    api._question_bank_landing_context = lambda *args, **kwargs: {
        "session": session,
        "landing_url": "https://qbank/1",
        "landing_html": '<input type="hidden" id="openDifficulty" value="true">',
    }
    result = api.update_question_bank_questions_difficulty(
        {"course_id": "course-1", "course_name": "Course", "cpi": "cpi-1"},
        {"clazz_id": "class-1", "clazz_name": "Class"},
        ["question-1", "question-2"],
        0.8,
    )
    assert result["question_count"] == 2
    assert session.calls[0][1].endswith("/qbank/update-easy")
    assert session.calls[0][2]["data"] == {
        "courseid": "course-1",
        "cpi": "cpi-1",
        "qids": "question-1,question-2,",
        "easy": 0.8,
    }


def test_question_bank_copy_contract_and_readback() -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    session = RecordingJSONSession()
    source = {
        "question_id": "question-1",
        "index": 1,
        "stem": "Which is correct?",
        "origin_type": "0",
    }
    copied = {**source, "question_id": "question-2"}
    item_reads = iter(
        [
            {"questions": [source]},
            {"questions": []},
            {"questions": [copied]},
        ]
    )
    tree_reads = iter([[], []])
    api._list_all_question_bank_items = lambda *args, **kwargs: next(item_reads)
    api._question_bank_landing_context = lambda *args, **kwargs: {
        "session": session,
        "landing_url": "https://qbank/1",
    }
    api._question_bank_directory_tree = lambda *args, **kwargs: next(tree_reads)
    result = api.copy_question_bank_items(
        {"course_id": "course-1", "course_name": "Course", "cpi": "cpi-1"},
        {"clazz_id": "class-1", "clazz_name": "Class"},
        questions=["question-1"],
        target_directory="0",
    )
    assert result["copied_questions"][0]["question_id"] == "question-2"
    assert session.calls[0][1].endswith("/qbank/questionCopy")
    assert session.calls[0][2]["params"]["newPid"] == "0"
    assert session.calls[0][2]["params"]["pids"] == ""
    assert session.calls[0][2]["data"] == {"qids": "question-1,"}


def test_parse_and_normalize_question_bank_smart_import() -> None:
    context = parse_question_bank_smart_import_context(
        """
        <input type="hidden" id="moocImportExportUrl"
               value="https://mooc1.chaoxing.com/import-export-ans">
        <input type="hidden" id="importQuestionEnc" value="enc-1">
        <input type="hidden" id="courseQueNum" value="1522">
        <input type="hidden" id="queNumMaxSize" value="20000">
        <input type="hidden" id="allowImportTopic" value="true">
        """
    )
    assert context["import_endpoint"] == (
        "https://mooc1.chaoxing.com/import-export-ans/import/import-question"
    )
    assert context["course_question_count"] == 1522
    assert context["course_question_limit"] == 20000
    assert context["allow_import_topics"] is True

    normalized = normalize_question_bank_smart_import_paper(
        [
            {
                "type": "QuestionChoice",
                "content": "Which is correct?",
                "options": [
                    {"name": "A", "value": "First"},
                    {"name": "B", "value": "Second"},
                ],
                "answer": ["B"],
            },
            {
                "type": "QuestionGapFilling",
                "content": "Complete it.",
                "answer": ["one", "two"],
                "isMutex": 1,
            },
            {
                "type": "QuestionYesNo",
                "content": "The statement is true.",
                "answerValue": True,
            },
            {
                "type": "QuestionCommon",
                "typeAlias": "论述题",
                "content": "Explain the result.",
                "answer": ["Because ..."],
            },
            {
                "type": "QuestionWriting",
                "content": "English writing: describe the graph.",
                "answer": ["Model answer"],
            },
        ]
    )
    assert normalized["question_count"] == 5
    assert normalized["warnings"] == []
    single = normalized["questions"][0]
    assert single["type"] == 0
    assert single["answer"][1] == {"content": "Second", "name": "B", "isanswer": True}
    assert normalized["questions"][1]["answer"] == [
        {"content": "one", "name": "1"},
        {"content": "two", "name": "2"},
    ]
    assert normalized["questions"][2]["answer"] == [{"answer": True}]
    assert normalized["questions"][3]["type"] == 6
    writing_answer = normalized["questions"][4]["answer"][0]
    assert writing_answer["subject"] == "0"
    assert writing_answer["grade"] == "cet4"


def test_question_bank_smart_import_preview_and_commit_contracts() -> None:
    class SmartImportSession(RecordingJSONSession):
        def __init__(self) -> None:
            super().__init__()
            self.post_payloads = [
                {
                    "status": True,
                    "paper": [
                        {
                            "type": "QuestionChoice",
                            "typeAlias": "单选题",
                            "content": "Which is correct?",
                            "options": [
                                {"name": "A", "value": "First"},
                                {"name": "B", "value": "Second"},
                            ],
                            "answer": ["B"],
                        }
                    ],
                },
                {"status": True, "needCreate": False},
                {
                    "totalNum": 1,
                    "insertSuccessNum": 1,
                    "insertFailedNum": 0,
                    "ignoreNum": 0,
                },
            ]

        def post(self, url: str, **kwargs):
            self.calls.append(("POST", url, kwargs))
            return self._response(self.post_payloads.pop(0))

    api = ChaoxingAPI(Path("unused-cookies.json"))
    session = SmartImportSession()
    course = {"course_id": "course-1", "course_name": "Course", "cpi": "cpi-1"}
    clazz = {"clazz_id": "class-1", "clazz_name": "Class"}
    context = {
        "session": session,
        "smart_import_url": "https://mooc2-ans.chaoxing.com/mooc2-ans/qbank/smartimport",
        "import_endpoint": ("https://mooc1.chaoxing.com/import-export-ans/import/import-question"),
        "import_token": "enc-1",
        "paper_library_id": "",
        "work_library_id": "",
        "micro_topic_id": "0",
        "group_id": "0",
        "initial_status": "",
        "need_question_ids": False,
        "course_question_count": 10,
        "course_question_limit": 20000,
        "allow_import_topics": True,
    }
    api._question_bank_smart_import_context = lambda *args, **kwargs: context

    preview = api.preview_question_bank_smart_import(
        course,
        clazz,
        source_text="1. Which is correct?\nA. First\nB. Second\n答案：B",
    )
    assert preview["question_count"] == 1
    assert preview["questions"][0]["type"] == 0
    parse_call = session.calls[0]
    assert parse_call[1].endswith("/sqp/api/parse")
    assert "<p>1. Which is correct?</p>" in parse_call[2]["data"]["html"]

    before_after = iter(
        [
            {"questions": []},
            {
                "questions": [
                    {
                        "question_id": "question-1",
                        "stem": "Which is correct?",
                        "origin_type": "0",
                    }
                ]
            },
        ]
    )
    api._question_bank_directory_tree = lambda *args, **kwargs: []
    api._list_all_question_bank_items = lambda *args, **kwargs: next(before_after)
    result = api.import_question_bank_smart(
        course,
        clazz,
        questions=preview["questions"],
        target_directory="0",
    )
    assert result["outcome"] == "complete"
    assert result["inserted_count"] == 1
    type_check_call = session.calls[1]
    assert type_check_call[1].endswith("/qbank/check-qtype-create")
    assert json.loads(type_check_call[2]["data"]["data"]) == [{"type": 0, "name": "单选题"}]
    import_call = session.calls[2]
    assert import_call[1].endswith("/import/import-question")
    assert import_call[2]["data"]["courseId"] == "course-1"
    assert import_call[2]["data"]["pid"] == "0"
    assert json.loads(import_call[2]["data"]["qjson"])[0]["content"] == "Which is correct?"


def test_parse_question_bank_export_and_download_center_contexts() -> None:
    html = """
    <input type="hidden" id="moocImportExportUrl"
           value="https://mooc1.chaoxing.com/import-export-ans">
    <input type="hidden" id="exportQuestionEnc" value="export-token">
    <input type="hidden" id="qbankExcelExportVersion" value="v2">
    <input type="hidden" id="microTopicId" value="0">
    <script>
      $('.downloadCenter').attr('src',
        "/mooc2-ans/mycourse/downloadcenter?courseid=course-1&amp;cpi=cpi-1");
    </script>
    """
    context = parse_question_bank_export_context(html)
    assert context["export_endpoint"] == (
        "https://mooc1.chaoxing.com/import-export-ans/export-questions"
    )
    assert context["export_token"] == "export-token"
    assert context["version"] == "v2"
    assert context["download_center_url"].endswith("courseid=course-1&cpi=cpi-1")

    listing = parse_question_bank_download_center(
        """
        <input type="hidden" id="downcenterorder" value="down">
        <input type="hidden" id="downcenterpage" value="1">
        <input type="hidden" id="totalPage" value="2">
        <div id="downloadBody">
          <ul class="dataBody_td" data="record-1" data-status="1">
            <li class="dataBody_down"><span class="nameText">Unit 1.xlsx</span>
              <i class="editName"></i></li>
            <li class="dataBody_size">2026-08-31 16:00</li>
            <li class="dataBody_status">已完成</li>
            <li class="handles">
              <a class="checkSafe download_ic" id="record-1"
                 data="{&quot;relationId&quot;:&quot;relation-1&quot;,
                 &quot;clazzId&quot;:&quot;class-1&quot;,
                 &quot;libraryId&quot;:&quot;paper-1&quot;}">下载</a>
              <a class="deleteOrCancel">删除</a>
            </li>
          </ul>
        </div>
        """
    )
    assert listing["page_count"] == 2
    assert listing["records"][0]["status"] == "completed"
    assert listing["records"][0]["file_name"] == "Unit 1.xlsx"
    assert listing["records"][0]["relation_id"] == "relation-1"
    assert listing["records"][0]["can_download"] is True
    assert (
        resolve_question_bank_download_record(listing["records"], "Unit 1.xlsx")["record_id"]
        == "record-1"
    )
    assert content_disposition_filename("attachment; filename*=UTF-8''Unit%201.xlsx") == (
        "Unit 1.xlsx"
    )
    assert (
        content_disposition_filename(
            "attachment; filename=" + "文体写作示例-题库.xls".encode().decode("latin-1")
        )
        == "文体写作示例-题库.xls"
    )


def test_question_bank_synchronous_export_contract(tmp_path: Path) -> None:
    class ExportResponse:
        content = b"spreadsheet-bytes"
        encoding = "utf-8"
        apparent_encoding = "utf-8"
        headers = {
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "Content-Disposition": "attachment; filename*=UTF-8''questions.xlsx",
        }
        url = "https://mooc1.chaoxing.com/import-export-ans/export-questions"

        @staticmethod
        def raise_for_status() -> None:
            return None

        @staticmethod
        def iter_content(chunk_size: int):
            assert chunk_size > 0
            yield b"spreadsheet-"
            yield b"bytes"

    class ExportSession:
        def __init__(self) -> None:
            self.calls: list[tuple[str, str, dict]] = []

        def post(self, url: str, **kwargs):
            self.calls.append(("POST", url, kwargs))
            return ExportResponse()

    api = ChaoxingAPI(Path("unused-cookies.json"))
    session = ExportSession()
    landing_html = """
      <input type="hidden" id="moocImportExportUrl"
             value="https://mooc1.chaoxing.com/import-export-ans">
      <input type="hidden" id="exportQuestionEnc" value="export-token">
      <input type="hidden" id="qbankExcelExportVersion" value="v2">
      <input type="hidden" id="microTopicId" value="0">
    """
    api._question_bank_landing_context = lambda *args, **kwargs: {
        "session": session,
        "landing_url": "https://qbank/1",
        "landing_html": landing_html,
    }
    api._question_bank_export_selection = lambda *args, **kwargs: (
        [{"question_id": "question-1", "stem": "Which is correct?"}],
        [],
    )
    result = api.export_question_bank(
        {"course_id": "course-1", "course_name": "Course", "cpi": "cpi-1"},
        {"clazz_id": "class-1", "clazz_name": "Class"},
        export_type="excel",
        questions=["question-1"],
        output_path=tmp_path,
        include_correct_rate=True,
    )
    assert result["mode"] == "synchronous"
    assert result["file"]["file_name"] == "questions.xlsx"
    assert (tmp_path / "questions.xlsx").read_bytes() == b"spreadsheet-bytes"
    call = session.calls[0]
    assert call[1].endswith("/export-questions")
    assert call[2]["params"]["exportType"] == "excel"
    assert call[2]["params"]["exportRightPercent"] == "true"
    assert call[2]["params"]["saveAs"] == "true"
    assert call[2]["data"] == {"questionIds": "question-1", "directoryids": ""}


def test_question_bank_sync_export_json_success_becomes_download_task(monkeypatch) -> None:
    class QueuedResponse:
        content = b'{"status":true,"msg":"queued"}'
        encoding = "utf-8"
        apparent_encoding = "utf-8"
        headers = {"Content-Type": "application/json;charset=UTF-8"}
        url = "https://mooc1.chaoxing.com/import-export-ans/export-questions"

        @staticmethod
        def raise_for_status() -> None:
            return None

        @staticmethod
        def json() -> dict:
            return {"status": True, "msg": "queued"}

    class QueuedSession:
        @staticmethod
        def post(url: str, **kwargs):
            return QueuedResponse()

    api = ChaoxingAPI(Path("unused-cookies.json"))
    api._question_bank_landing_context = lambda *args, **kwargs: {
        "session": QueuedSession(),
        "landing_url": "https://qbank/1",
        "landing_html": """
          <input type="hidden" id="moocImportExportUrl"
                 value="https://mooc1.chaoxing.com/import-export-ans">
          <input type="hidden" id="exportQuestionEnc" value="export-token">
          <input type="hidden" id="qbankExcelExportVersion" value="v2">
          <input type="hidden" id="microTopicId" value="0">
        """,
    }
    api._question_bank_export_selection = lambda *args, **kwargs: (
        [{"question_id": "question-1", "stem": "Question"}],
        [],
    )
    monkeypatch.setattr(
        api,
        "list_question_bank_download_center",
        lambda *args, **kwargs: {"record_count": 1},
    )
    result = api.export_question_bank(
        {"course_id": "course-1", "course_name": "Course", "cpi": "cpi-1"},
        {"clazz_id": "class-1", "clazz_name": "Class"},
        export_type="excel",
        questions=["question-1"],
        output_path=Path("unused.xlsx"),
    )
    assert result["mode"] == "asynchronous"
    assert result["queued"] is True
    assert result["download_center"] == {"record_count": 1}


def test_question_bank_download_center_list_and_download_contract(tmp_path: Path) -> None:
    center_html = """
      <input type="hidden" id="downcenterpage" value="1">
      <input type="hidden" id="totalPage" value="1">
      <ul class="dataBody_td" data="record-1" data-status="1">
        <li><span class="nameText">questions.xlsx</span></li>
        <li>2026-08-31 16:00</li><li class="status">已完成</li>
        <li><a class="checkSafe" id="record-1"
          data="{&quot;relationId&quot;:&quot;relation-1&quot;,
          &quot;clazzId&quot;:&quot;class-1&quot;,&quot;libraryId&quot;:&quot;paper-1&quot;}">
          下载</a></li>
      </ul>
    """

    class Response:
        def __init__(self, content: bytes, content_type: str, url: str) -> None:
            self.content = content
            self.encoding = "utf-8"
            self.apparent_encoding = "utf-8"
            self.headers = {"Content-Type": content_type}
            self.url = url

        @staticmethod
        def raise_for_status() -> None:
            return None

        def iter_content(self, chunk_size: int):
            assert chunk_size > 0
            yield self.content

    class DownloadSession:
        def __init__(self) -> None:
            self.calls: list[tuple[str, str, dict]] = []

        def get(self, url: str, **kwargs):
            self.calls.append(("GET", url, kwargs))
            if url.endswith("/tcm/downloadcenter"):
                return Response(center_html.encode(), "text/html", url)
            if url.endswith("/tcm/check-download-record"):
                return Response(
                    json.dumps(
                        {"downloadUrl": "https://files.chaoxing.com/questions.xlsx"}
                    ).encode(),
                    "application/json",
                    url,
                )
            return Response(b"file-bytes", "application/octet-stream", url)

    api = ChaoxingAPI(Path("unused-cookies.json"))
    session = DownloadSession()
    api._question_bank_landing_context = lambda *args, **kwargs: {
        "session": session,
        "landing_url": "https://qbank/1",
        "landing_html": "",
    }
    course = {"course_id": "course-1", "course_name": "Course", "cpi": "cpi-1"}
    clazz = {"clazz_id": "class-1", "clazz_name": "Class"}
    listing = api.list_question_bank_download_center(course, clazz)
    assert listing["record_count"] == 1
    result = api.get_question_bank_download(
        course,
        clazz,
        "record-1",
        output_path=tmp_path / "saved.xlsx",
    )
    assert (tmp_path / "saved.xlsx").read_bytes() == b"file-bytes"
    assert result["file"]["byte_count"] == 10
    check_call = next(call for call in session.calls if call[1].endswith("check-download-record"))
    assert check_call[2]["params"]["relationId"] == "relation-1"
    assert check_call[2]["params"]["paperid"] == "paper-1"


def test_parse_question_bank_cross_course_picker_and_import_contract() -> None:
    courses = parse_question_bank_source_courses(
        """
        <div class="select-down-box" id="course-select"><div><ul>
          <li courseid="source-1" cenc="token-1" class="active">Source Course</li>
          <li courseid="source-2">另一门课程</li>
        </ul></div></div>
        """
    )
    assert courses == [
        {
            "index": 1,
            "course_id": "source-1",
            "course_name": "Source Course",
            "course_token": "token-1",
            "selected_by_default": True,
        },
        {
            "index": 2,
            "course_id": "source-2",
            "course_name": "另一门课程",
            "course_token": "",
            "selected_by_default": False,
        },
    ]
    listing = parse_question_bank_source_questions(
        """
        <input id="totalPage" value="1"><input id="currentPageNo" value="1">
        <input id="totalResult" value="1">
        <table><tr class="question-item" data-id="source-question-1"
          courseid="source-1" qtype="0" coursequestiontypeid="0">
          <td><p>1</p></td>
          <td><p class="table-question-title">Which is correct?</p></td>
          <td><div onclick="qListDirSearch('dir-1')">Unit 1</div></td>
          <td><p>单选题</p></td><td><p>90%</p></td><td><p>0.8（易）</p></td>
          <td><p>12</p></td><td><p>Teacher</p></td><td><p>2026-08-31</p></td>
        </tr></table>
        """
    )
    source_question = listing["questions"][0]
    assert source_question["question_id"] == "source-question-1"
    assert source_question["stem"] == "Which is correct?"
    assert source_question["directory_id"] == "dir-1"
    assert source_question["use_count"] == 12

    api = ChaoxingAPI(Path("unused-cookies.json"))
    session = RecordingJSONSession()
    course = {"course_id": "target-1", "course_name": "Target", "cpi": "cpi-1"}
    clazz = {"clazz_id": "class-1", "clazz_name": "Class"}
    api._question_bank_source_context = lambda *args, **kwargs: {
        "session": session,
        "picker_url": "https://picker/1",
        "source_courses": courses,
    }
    api._question_bank_source_security_state = lambda *args, **kwargs: {"status": True}
    api._question_bank_source_search = lambda *args, **kwargs: {
        "page": 1,
        "page_count": 1,
        "total": 1,
        "questions": [source_question],
    }
    api._question_bank_directory_tree = lambda *args, **kwargs: []
    before_after = iter(
        [
            {"questions": []},
            {
                "questions": [
                    {
                        "question_id": "target-question-1",
                        "stem": "Which is correct?",
                        "origin_type": "0",
                    }
                ]
            },
        ]
    )
    api._list_all_question_bank_items = lambda *args, **kwargs: next(before_after)
    result = api.import_question_bank_questions_from_course(
        course,
        clazz,
        "Source Course",
        ["source-question-1"],
    )
    assert result["imported_questions"][0]["question_id"] == "target-question-1"
    call = session.calls[0]
    assert call[1].endswith("/qbank/appendQuestionToQbank")
    grouped = json.loads(call[2]["data"]["questionBankParam"])
    assert grouped["0--0"] == {
        "type": "0",
        "courseQuestionTypeId": "0",
        "qNum": 1,
        "data": [
            {
                "cid": "source-1",
                "cenc": "token-1",
                "qid": "source-question-1",
                "qbankType": "personalQbank",
            }
        ],
    }


def test_question_bank_permission_endpoint_and_state_contract() -> None:
    class PermissionSession(RecordingJSONSession):
        def get(self, url: str, **kwargs):
            self.calls.append(("GET", url, kwargs))
            return self._response({"status": True, "permissionList": [{"personId": "person-2"}]})

    api = ChaoxingAPI(Path("unused-cookies.json"))
    session = PermissionSession()
    course = {"course_id": "course-1"}
    directory = {
        "directory_id": "dir-1",
        "course_id": "course-1",
        "is_open": "-1",
        "share_state": "2",
    }
    payload = api._question_bank_directory_permission_payload(
        session,
        course,
        directory,
        referer="https://qbank/1",
    )
    state = api._question_bank_permission_state(
        directory,
        payload,
        [{"index": 1, "person_id": "person-2", "teacher_name": "张三"}],
    )
    assert session.calls[0][1].endswith("/dir-permission/list")
    assert session.calls[0][2]["params"] == {"courseid": "course-1", "dirId": "dir-1"}
    assert state["student_self_practice_allowed"] is False
    assert state["share_scope"] == "selected_teachers"
    assert state["selected_teachers"][0]["teacher_name"] == "张三"


def test_update_question_bank_permissions_posts_exact_contract(monkeypatch) -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    session = RecordingJSONSession()
    course = {"course_id": "course-1", "course_name": "Course", "cpi": "cpi-1"}
    clazz = {"clazz_id": "class-1", "clazz_name": "Class"}
    before = {
        "directory_id": "dir-1",
        "course_id": "course-1",
        "is_open": "1",
        "share_state": "0",
    }
    after = {**before, "is_open": "-1", "share_state": "2"}
    trees = iter([[before], [after]])
    permission_payloads = iter(
        [
            {"accessible": True, "selected_person_ids": [], "message": ""},
            {"accessible": True, "selected_person_ids": ["person-2"], "message": ""},
        ]
    )
    posted: dict = {}
    landing_html = """
    <div id="teacherList">
      <span class="ipt-checkbox" data="person-2"></span>
      <span class="ipt-txt">张三</span>
    </div>
    """
    monkeypatch.setattr(
        api,
        "_question_bank_landing_context",
        lambda *args, **kwargs: {
            "session": session,
            "landing_url": "https://qbank/1",
            "landing_html": landing_html,
        },
    )
    monkeypatch.setattr(api, "_question_bank_directory_tree", lambda *args, **kwargs: next(trees))
    monkeypatch.setattr(
        api,
        "_question_bank_directory_permission_payload",
        lambda *args, **kwargs: next(permission_payloads),
    )

    def record_mutation(_session, path, data, **kwargs):
        posted.update({"path": path, "data": data})
        return {"status": True}

    monkeypatch.setattr(api, "_question_bank_mutation_request", record_mutation)
    result = api.update_question_bank_directory_permissions(
        course,
        clazz,
        "dir-1",
        allow_student_self_practice=False,
        share_scope="selected_teachers",
        selected_teachers=["张三"],
    )
    assert posted == {
        "path": "/mooc2-ans/qbank/update-permission",
        "data": {
            "courseid": "course-1",
            "dirid": "dir-1",
            "isopen": "-1",
            "isShare": "2",
            "personIdArr": "person-2,",
        },
    }
    assert result["after"]["selected_person_ids"] == ["person-2"]


def test_question_bank_directory_and_question_reorder_contracts(monkeypatch) -> None:
    course = {"course_id": "course-1", "course_name": "Course", "cpi": "cpi-1"}
    clazz = {"clazz_id": "class-1", "clazz_name": "Class"}
    landing = {
        "session": RecordingJSONSession(),
        "landing_url": "https://qbank/1",
        "landing_html": "",
    }
    d1 = {
        "directory_id": "d1",
        "parent_id": "0",
        "name": "One",
        "path": "One",
        "is_top": False,
        "index": 1,
    }
    d2 = {
        "directory_id": "d2",
        "parent_id": "0",
        "name": "Two",
        "path": "Two",
        "is_top": False,
        "index": 2,
    }
    directory_api = ChaoxingAPI(Path("unused-cookies.json"))
    directory_items = iter(
        [
            {"directories": [d1, d2], "questions": [], "allow_sort": True},
            {"directories": [d2, d1], "questions": [], "allow_sort": True},
        ]
    )
    directory_posted: dict = {}
    monkeypatch.setattr(directory_api, "_question_bank_landing_context", lambda *args: landing)
    monkeypatch.setattr(
        directory_api, "_question_bank_directory_tree", lambda *args, **kw: [d1, d2]
    )
    monkeypatch.setattr(
        directory_api,
        "_list_all_question_bank_items",
        lambda *args, **kw: next(directory_items),
    )

    def record_directory(_session, path, data, **kwargs):
        directory_posted.update({"path": path, "data": data})
        return {"status": True}

    monkeypatch.setattr(
        directory_api,
        "_question_bank_mutation_request",
        record_directory,
    )
    moved_directory = directory_api.reorder_question_bank_directory(course, clazz, "d2", 1)
    assert moved_directory["after_order"] == ["d2", "d1"]
    assert directory_posted["data"] == {
        "courseid": "course-1",
        "cpi": "cpi-1",
        "idStr": "d2,d1",
        "type": "0",
    }

    question_api = ChaoxingAPI(Path("unused-cookies.json"))
    q1 = {"question_id": "q1", "index": 1, "stem": "One"}
    q2 = {"question_id": "q2", "index": 2, "stem": "Two"}
    question_items = iter(
        [
            {"directories": [], "questions": [q1, q2], "allow_sort": True},
            {"directories": [], "questions": [q2, q1], "allow_sort": True},
        ]
    )
    question_posted: dict = {}
    monkeypatch.setattr(question_api, "_question_bank_landing_context", lambda *args: landing)
    monkeypatch.setattr(
        question_api,
        "_list_all_question_bank_items",
        lambda *args, **kw: next(question_items),
    )

    def record_question(_session, path, data, **kwargs):
        question_posted.update({"path": path, "data": data})
        return {"status": True}

    monkeypatch.setattr(
        question_api,
        "_question_bank_mutation_request",
        record_question,
    )
    moved_question = question_api.reorder_question_bank_question(
        course, clazz, "q2", 1, directory_id="0"
    )
    assert moved_question["after_order"] == ["q2", "q1"]
    assert question_posted["path"].endswith("batchUpdateSort")
    assert question_posted["data"]["idStr"] == "q2,q1"
    assert question_posted["data"]["type"] == "1"


def test_compose_question_bank_core_question_forms() -> None:
    api = ChaoxingAPI(Path("unused-cookies.json"))
    shell = {
        "html": """
          <input name="courseid" value="course-1"><input name="cpi" value="cpi-1">
          <input name="questionBankId" value=""><input name="originType" value="0">
          <input name="qType" value="0"><input name="answerForTF" value="true">
        """,
        "hidden": {"questionBankId": ""},
    }
    detail = """
      <textarea name="content"></textarea><textarea name="A"></textarea>
      <textarea name="B"></textarea><textarea name="answerAnalysis"></textarea>
      <input name="difficulty" value="0.8"><input name="easy" value="0">
      <input name="topicId" value="0"><input name="schoolTopicIds" value="">
      <input name="labelIdArr" value="">
    """
    choice, expected = api._compose_question_bank_question_form(
        shell,
        detail,
        "0",
        stem="Choose one.",
        options=["Alpha", "Beta"],
        correct_answer="B",
        creating=True,
    )
    assert choice["A"] == "<p>Alpha</p>"
    assert choice["B"] == "<p>Beta</p>"
    assert choice["defAnswer"] == "B"
    assert expected["answer"] == "B"

    fill, fill_expected = api._compose_question_bank_question_form(
        shell,
        detail.replace('name="A"', 'name="1"').replace('name="B"', 'name="isMutex"'),
        "2",
        stem="Complete both.",
        answers=["first", "second"],
        creating=True,
    )
    assert fill["answer"] == "<p>first</p>★<p>second</p>"
    assert fill["2"] == "<p>second</p>"
    assert fill_expected["answer"][0]["text"] == "first"

    true_false, tf_expected = api._compose_question_bank_question_form(
        shell,
        detail,
        "3",
        stem="This is true.",
        answer=True,
        creating=True,
    )
    assert true_false["answerForTF"] == "true"
    assert tf_expected["answer"] is True


def test_parse_class_student_table() -> None:
    html = """
    <input type="hidden" id="pageNum" value="1">
    <p>全部学生，共&nbsp;31&nbsp;人</p>
    <table id="studentTable">
      <thead><tr>
        <th lay-data="{field:'checkedbox',type:'checkbox'}"></th>
        <th lay-data="{field:'personid',hide:true}"></th>
        <th lay-data="{field:'userName'}">姓名</th>
        <th lay-data="{field:'studentNumber'}">学号</th>
        <th lay-data="{field:'schoolName'}">学校</th>
        <th lay-data="{field:'group1'}">院系</th>
        <th lay-data="{field:'group2'}">专业</th>
        <th lay-data="{field:'group3'}">班级</th>
        <th lay-data="{field:'createTime'}">加入时间</th>
        <th lay-data="{field:'operation'}">操作</th>
      </tr></thead>
      <tbody><tr>
        <td></td><td>410890414</td><td>赵英竹</td><td>2024001686</td>
        <td>吉林华侨外国语学院</td><td>英语学院</td><td>英语</td>
        <td>英语2401</td><td>2025-09-04</td>
        <td><a href="/mooc2-ans/moocanalysis/accesslog?stucpi=410890414">访问日志</a></td>
      </tr></tbody>
    </table>
    """
    students, total, page = parse_class_student_table(
        html, "https://mooc2-ans.chaoxing.com/mooc2-ans/tcm/clazz-student"
    )
    assert total == 31
    assert page == 1
    assert students[0]["person_id"] == "410890414"
    assert students[0]["student_name"] == "赵英竹"
    assert students[0]["student_no"] == "2024001686"
    assert students[0]["access_log_url"].endswith("stucpi=410890414")
    students[0]["index"] = 1
    assert resolve_class_student(students, "2024001686")["person_id"] == "410890414"


def test_parse_course_operation_logs() -> None:
    html = """
    <span id="modules">[{"name":"全部","id":0},{"name":"作业","id":3}]</span>
    <div>共 1 条</div>
    <ul class="dataBody_td">
      <li title="张三">张三</li><li>2025800218</li>
      <li title="发布作业第1周作业">发布作业第1周作业</li>
      <li>36.48.94.250</li><li>2026-08-27 16:51:56</li>
    </ul>
    """
    rows, total, modules = parse_course_operation_log_rows(html)
    assert total == 1
    assert modules[1] == {"name": "作业", "id": 3}
    assert rows[0]["operator_name"] == "张三"
    assert rows[0]["operation"] == "发布作业第1周作业"


def test_parse_student_join_and_leave_logs() -> None:
    join_html = """
    <p>共 1 条</p>
    <table>
      <tr><th>姓名</th><th>学号</th><th>班级</th><th>加班方式</th><th>加班时间</th></tr>
      <tr><td>洪莺芮</td><td>2023001227</td><td>英日2301</td>
          <td>学生自主加班</td><td>08-25</td></tr>
    </table>
    """
    joins, join_total = parse_student_join_log_rows(join_html)
    assert join_total == 1
    assert joins[0]["student_no"] == "2023001227"
    assert joins[0]["join_method"] == "学生自主加班"

    leave_html = """
    <p>共 1 条</p>
    <ul class="dataBody_td">
      <li class="dataBody_check" data="221067883"><input type="checkbox"></li>
      <li>杨子昂</li><li>英韩2402</li><li>退出课程</li>
      <li>123.173.240.31</li><li>2025-09-02 10:10:32</li>
      <li data="221067883" class="recoverystudy">恢复</li>
    </ul>
    """
    leaves, leave_total = parse_student_leave_log_rows(leave_html)
    assert leave_total == 1
    assert leaves[0]["person_drop_id"] == "221067883"
    assert leaves[0]["restorable"] is True
    leaves[0]["index"] = 1
    assert resolve_student_leave_log(leaves, "杨子昂")["clazz_name"] == "英韩2402"


def test_parse_student_access_summary_and_logs() -> None:
    summary = parse_student_access_summary(
        """
        <p>0 章节学习次数</p><p>89 小时 20 分钟 课程访问时长</p>
        <script>stuExportUrl = "https://example.com/api/export-stu-visit-log?x=1";</script>
        """
    )
    assert summary["chapter_study_count"] == 0
    assert summary["course_access_hours"] == 89
    assert summary["course_access_minutes"] == 20
    logs, page_info = parse_student_access_log_payload(
        {
            "array": [
                {
                    "time": "11-08 14:31",
                    "eventType": "ceyaanswer",
                    "eventName": "提交章节测验",
                    "message": "提交章节测验",
                    "relationName": "Description",
                    "clientip": "36.49.67.56",
                    "ipCity": "吉林长春",
                }
            ],
            "pageInfo": {
                "currentPageNo": 1,
                "pagesize": 100,
                "totalPage": 1,
                "totalResult": 1,
            },
        },
        2025,
    )
    assert logs[0]["timestamp"] == "2025-11-08 14:31"
    assert logs[0]["relation_name"] == "Description"
    assert page_info["total_count"] == 1


def test_parse_teacher_team() -> None:
    html = """
    <span id="allTeacherNum">2</span>
    <ul class="dataBody_td" uid="79371038">
      <li class="dataBody_name">邹红</li><li class="dataBody_read">创建者</li>
      <li class="dataBody_down">2014800132</li>
      <li class="dataBody_size">吉林外国语大学</li>
      <li class="dataBody_depart">英语学院</li><li class="dataBody_time">2025-01-01
        <ul class="operate" personid="112855604"><li>班级分配</li></ul>
      </li>
    </ul>
    <ul class="dataBody_td" personId="485781386" teamTeachId="39092316"
        role="1" uid="405017213">
      <li class="dataBody_name">张三</li><li class="dataBody_read">教师</li>
      <li class="dataBody_down">2025800218</li>
      <li class="dataBody_size">吉林外国语大学</li>
      <li class="dataBody_depart">英语学院</li><li class="dataBody_time"></li>
    </ul>
    """
    teachers, total = parse_teacher_team(html)
    assert total == 2
    assert teachers[0]["teacher_name"] == "邹红"
    assert teachers[0]["role"] == "创建者"
    assert teachers[0]["person_id"] == "112855604"
    assert teachers[1]["person_id"] == "485781386"
    assert teachers[1]["teacher_no"] == "2025800218"


def test_parse_and_resolve_teacher_bank_candidates() -> None:
    html = """
    <div>全部教师 共 2 人</div>
    <ul class="dataBody_td dataBody_addtea" personId="126027814" enc="token-a">
      <li><span>邹红</span></li><li>201480012</li><li>英语学院</li>
    </ul>
    <ul class="dataBody_td dataBody_addtea" personId="112855604" enc="token-b">
      <li><span>邹红</span></li><li>2014800132</li><li>英语学院</li>
    </ul>
    """
    candidates, total = parse_teacher_bank_candidates(html)
    assert total == 2
    assert candidates[1]["teacher_no"] == "2014800132"
    assert resolve_teacher_bank_candidate(candidates, "2014800132")["person_id"] == "112855604"


def test_parse_discussion_payload() -> None:
    topics, folders = parse_discussion_payload(
        {
            "datas": [
                {
                    "id": 708097963,
                    "uuid": "topic-uuid",
                    "bbsid": "bbs-1",
                    "title": "Describing people",
                    "content": "Describe your favorite athlete.",
                    "createrName": "邹红",
                    "reply_count": 3,
                    "readPersonCount": 4,
                    "praise_count": 0,
                    "top": 1,
                    "lastReply": {"replyId": 9, "name": "学生", "content": "My answer"},
                }
            ],
            "folder_list": [{"id": 1, "folder_uuid": "folder-1", "pid": 0, "name": "讨论区"}],
        }
    )
    assert topics[0]["topic_id"] == "708097963"
    assert topics[0]["is_top"] is True
    assert topics[0]["last_reply"]["name"] == "学生"
    assert folders[0]["folder_uuid"] == "folder-1"


def test_parse_discussion_replies_preserves_nested_replies() -> None:
    replies = parse_discussion_replies(
        {
            "datas": [
                {
                    "id": 20,
                    "uuid": "reply-1",
                    "content": "First answer",
                    "creater_name": "学生甲",
                    "top": 1,
                    "second_data": [
                        {
                            "id": 21,
                            "uuid": "reply-2",
                            "content": "Follow-up",
                            "creater_name": "教师",
                        }
                    ],
                }
            ]
        },
        is_top=False,
    )
    assert replies[0]["reply_id"] == "20"
    assert replies[0]["is_top"] is True
    assert replies[0]["replies"][0]["content"] == "Follow-up"


def test_resolve_discussion_reply_includes_nested_replies() -> None:
    replies = [
        {
            "reply_id": "20",
            "uuid": "reply-1",
            "content": "First answer",
            "replies": [
                {
                    "reply_id": "21",
                    "uuid": "reply-2",
                    "content": "Teacher follow-up",
                    "replies": [],
                }
            ],
        }
    ]
    assert resolve_discussion_reply(replies, "2")["uuid"] == "reply-2"
    assert resolve_discussion_reply(replies, "Teacher follow")["reply_id"] == "21"


def test_parse_chapter_items_preserves_hierarchy() -> None:
    html = """
    <div class="chapter_unit"><div class="chapter_item">
      <input class="firstNodeId" value="100"><div class="catalog_num"><em>1</em></div>
      <a class="clicktitle" title="Introduction"></a>
      <div class="catalog_ressbar_width" style="width:25%;"></div></div>
      <!-- 第二级开始 -->
      <div onclick="toNew('200', '101', '300')">
        <span class="catalog_sbar">1.1</span><a class="clicktitle" title="Guide"></a>
        <span class="catalog_points_yi">2</span><span class="state_text">开放</span>
        <div onclick="setOpenStatus('open', '101', '', '', '0', '0')"></div>
        <div class="catalog_ressbar_width" style="width:50%;"></div>
      </div>
    </div>
    """
    chapters = parse_chapter_items(html)
    assert chapters[0]["chapter_id"] == "100"
    assert chapters[0]["task_point_count"] == 2
    assert chapters[0]["children"][0]["title"] == "Guide"
    assert chapters[0]["children"][0]["progress_percent"] == 50.0
    assert chapters[0]["children"][0]["configured_open_status"] == "open"


def test_parse_chapter_editor_tree_and_cards() -> None:
    tree = parse_chapter_editor_tree(
        """
        <script>
        ans_config = {courseid:900000002,root:{"expanded":true,"children":[
          {"id":100,"text":"Unit 1","children":[
            {"id":101,"text":"Learning Guide"}
          ]},
          {"id":200,"text":"Unit 2"}
        ],"id":0},cname:'Course'};
        </script>
        """
    )
    assert tree["course_id"] == "900000002"
    assert tree["chapter_count"] == 3
    assert tree["max_depth"] == 2
    guide = resolve_chapter_editor_item(tree["flat_chapters"], "Learning Guide")
    assert guide["chapter_id"] == "101"
    assert guide["parent_id"] == "100"
    assert guide["number"] == "1.1"

    cards = parse_chapter_cards(
        {
            "data": [
                {
                    "id": 900,
                    "nodeid": 101,
                    "title": "Learning goals",
                    "description": (
                        '<p>Read the guide.</p><img src="https://files/image.png">'
                        '<iframe class="ans-module ans-insertdoc-module" module="insertdoc" '
                        'data="{&quot;objectid&quot;:&quot;object-1&quot;,'
                        '&quot;name&quot;:&quot;guide.docx&quot;,&quot;type&quot;:&quot;.docx&quot;}">'
                        "</iframe>"
                    ),
                }
            ]
        }
    )
    assert cards[0]["card_id"] == "900"
    assert cards[0]["content"] == "Read the guide."
    assert cards[0]["images"] == ["https://files/image.png"]
    assert cards[0]["attachments"][0]["filename"] == "guide.docx"
    assert cards[0]["attachments"][0]["objectid"] == "object-1"


def test_chapter_create_and_rename_post_exact_editor_contracts(monkeypatch) -> None:
    course = {"course_id": "course-1", "course_name": "Course", "cpi": "cpi-1"}
    clazz = {"clazz_id": "class-1", "clazz_name": "Class"}

    create_session = RecordingJSONSession()
    parent = {
        "index": 1,
        "chapter_id": "100",
        "title": "Unit 1",
        "parent_id": "0",
        "depth": 1,
        "position": 1,
        "has_children": False,
        "children": [],
    }
    child = {
        "index": 2,
        "chapter_id": "101",
        "title": "Learning Guide",
        "parent_id": "100",
        "depth": 2,
        "position": 1,
        "has_children": False,
        "children": [],
    }
    parent_after = {**parent, "has_children": True, "children": [child]}
    create_contexts = iter(
        [
            {
                "session": create_session,
                "editor_url": "https://mooc1/edit/chapters/course-1/0",
                "flat_chapters": [parent],
            },
            {
                "session": create_session,
                "editor_url": "https://mooc1/edit/chapters/course-1/0",
                "flat_chapters": [parent_after, child],
            },
        ]
    )
    api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        api, "_chapter_editor_context", lambda *args, **kwargs: next(create_contexts)
    )
    created = api.create_chapter(course, clazz, "Learning Guide", parent="Unit 1")
    assert created["chapter"]["chapter_id"] == "101"
    create_call = create_session.calls[0]
    assert create_call[1].endswith("/edit/createchapter")
    assert create_call[2]["data"] == {
        "name": "Learning Guide",
        "courseid": "course-1",
        "parentid": "100",
        "layer": "2",
        "mooc2": "1",
    }

    rename_session = RecordingJSONSession()
    renamed = {**child, "title": "Guide and goals"}
    rename_contexts = iter(
        [
            {
                "session": rename_session,
                "editor_url": "https://mooc1/edit/chapters/course-1/0",
                "flat_chapters": [child],
            },
            {
                "session": rename_session,
                "editor_url": "https://mooc1/edit/chapters/course-1/0",
                "flat_chapters": [renamed],
            },
        ]
    )
    rename_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        rename_api, "_chapter_editor_context", lambda *args, **kwargs: next(rename_contexts)
    )
    result = rename_api.rename_chapter(course, clazz, "101", "Guide and goals")
    assert result["chapter"]["title"] == "Guide and goals"
    assert rename_session.calls[0][2]["data"]["nodeid"] == "101"


def test_chapter_move_delete_and_status_contracts(monkeypatch) -> None:
    course = {"course_id": "course-1", "course_name": "Course", "cpi": "cpi-1"}
    clazz = {"clazz_id": "class-1", "clazz_name": "Class"}
    first = {
        "index": 1,
        "chapter_id": "101",
        "title": "First",
        "parent_id": "100",
        "depth": 2,
        "position": 1,
        "has_children": False,
        "children": [],
    }
    second = {**first, "index": 2, "chapter_id": "102", "title": "Second", "position": 2}

    move_session = RecordingJSONSession()
    moved_first = {**first, "position": 2}
    moved_second = {**second, "position": 1}
    move_contexts = iter(
        [
            {
                "session": move_session,
                "editor_url": "https://mooc1/edit/chapters/course-1/0",
                "flat_chapters": [first, second],
            },
            {
                "session": move_session,
                "editor_url": "https://mooc1/edit/chapters/course-1/0",
                "flat_chapters": [moved_second, moved_first],
            },
        ]
    )
    api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(api, "_chapter_editor_context", lambda *args, **kwargs: next(move_contexts))
    moved = api.move_chapter(course, clazz, "Second", relative_to="First", position="before")
    assert moved["chapter"]["position"] == 1
    assert move_session.calls[0][1].endswith("/edit/movechapter")
    assert move_session.calls[0][2]["data"]["position"] == "before"

    delete_session = RecordingJSONSession()
    parent = {
        "index": 1,
        "chapter_id": "100",
        "title": "Unit 1",
        "parent_id": "0",
        "depth": 1,
        "position": 1,
        "has_children": True,
        "children": [first],
    }
    delete_contexts = iter(
        [
            {
                "session": delete_session,
                "editor_url": "https://mooc1/edit/chapters/course-1/0",
                "flat_chapters": [parent, first],
            },
            {
                "session": delete_session,
                "editor_url": "https://mooc1/edit/chapters/course-1/0",
                "flat_chapters": [],
            },
        ]
    )
    delete_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        delete_api, "_chapter_editor_context", lambda *args, **kwargs: next(delete_contexts)
    )
    deleted = delete_api.delete_chapters(course, clazz, ["Unit 1"])
    assert deleted["deleted_ids"] == ["100", "101"]
    assert delete_session.calls[0][2]["data"]["knowledgeids"] == "100,101"

    status_session = RecordingJSONSession()
    status_context = {
        "session": status_session,
        "editor_url": "https://mooc1/edit/chapters/course-1/0",
        "flat_chapters": [parent, first],
    }
    status_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        status_api, "_chapter_editor_context", lambda *args, **kwargs: status_context
    )
    monkeypatch.setattr(
        status_api,
        "list_chapters",
        lambda *args, **kwargs: {
            "chapters": [
                {"chapter_id": "100", "children": [{**first, "configured_open_status": "close"}]}
            ]
        },
    )
    updated = status_api.set_chapter_open_status(course, clazz, ["Unit 1"], "close")
    assert updated["status"] == "close"
    assert status_session.calls[0][1].endswith("/mycourse/changestatus")
    assert status_session.calls[0][2]["data"]["chapterids"] == "100,101"
    assert status_session.calls[0][2]["data"]["clazzids"] == "class-1"


def test_chapter_card_create_update_move_and_delete_contracts(monkeypatch) -> None:
    class CardSession(RecordingJSONSession):
        def post(self, url: str, **kwargs):
            self.calls.append(("POST", url, kwargs))
            if url.endswith("/edit/savecard"):
                return self._response({"id": "card-1", "status": True})
            return self._response({"status": True})

    course = {"course_id": "course-1", "course_name": "Course", "cpi": "cpi-1"}
    clazz = {"clazz_id": "class-1", "clazz_name": "Class"}
    chapter = {
        "index": 1,
        "chapter_id": "chapter-1",
        "title": "Learning Guide",
        "parent_id": "100",
        "depth": 2,
        "position": 1,
        "has_children": False,
        "children": [],
    }
    created_card = parse_chapter_cards(
        {
            "data": [
                {
                    "id": "card-1",
                    "nodeid": "chapter-1",
                    "title": "Goals",
                    "description": "<p>Read this page.</p>",
                }
            ]
        }
    )[0]
    session = CardSession()
    api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        api,
        "_chapter_editor_context",
        lambda *args, **kwargs: {
            "session": session,
            "editor_url": "https://mooc1/edit/chapters/course-1/0",
            "flat_chapters": [chapter],
        },
    )
    card_lists = iter([[], [created_card]])
    monkeypatch.setattr(api, "_chapter_cards_request", lambda *args, **kwargs: next(card_lists))
    created = api.create_chapter_card(
        course,
        clazz,
        "Learning Guide",
        "Goals",
        content="Read this page.",
    )
    assert created["card"]["card_id"] == "card-1"
    save_call = session.calls[0]
    assert save_call[1].endswith("/edit/savecard")
    assert save_call[2]["data"]["description"] == "<p>Read this page.</p>"
    assert save_call[2]["data"]["attachments"] == "[]"

    updated_card = {**created_card, "title": "Learning goals"}
    update_session = CardSession()
    update_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        update_api,
        "_chapter_editor_context",
        lambda *args, **kwargs: {
            "session": update_session,
            "editor_url": "https://mooc1/edit/chapters/course-1/0",
            "flat_chapters": [chapter],
        },
    )
    update_lists = iter([[created_card], [updated_card]])
    monkeypatch.setattr(
        update_api, "_chapter_cards_request", lambda *args, **kwargs: next(update_lists)
    )
    updated = update_api.update_chapter_card(
        course,
        clazz,
        "chapter-1",
        "card-1",
        title="Learning goals",
    )
    assert updated["card"]["title"] == "Learning goals"
    assert update_session.calls[0][2]["data"]["id"] == "card-1"

    other_card = {**created_card, "index": 2, "card_id": "card-2", "title": "Examples"}
    moved_card = {**other_card, "index": 1}
    first_after = {**created_card, "index": 2}
    move_session = CardSession()
    move_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        move_api,
        "_chapter_editor_context",
        lambda *args, **kwargs: {
            "session": move_session,
            "editor_url": "https://mooc1/edit/chapters/course-1/0",
            "flat_chapters": [chapter],
        },
    )
    move_lists = iter([[created_card, other_card], [moved_card, first_after]])
    monkeypatch.setattr(
        move_api, "_chapter_cards_request", lambda *args, **kwargs: next(move_lists)
    )
    moved = move_api.move_chapter_card(course, clazz, "chapter-1", "card-2", 1)
    assert moved["card"]["index"] == 1
    assert move_session.calls[0][1].endswith("/edit/movecard")
    assert move_session.calls[0][2]["data"]["othid"] == "card-1"

    delete_session = CardSession()
    delete_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        delete_api,
        "_chapter_editor_context",
        lambda *args, **kwargs: {
            "session": delete_session,
            "editor_url": "https://mooc1/edit/chapters/course-1/0",
            "flat_chapters": [chapter],
        },
    )
    delete_lists = iter([[created_card], []])
    monkeypatch.setattr(
        delete_api, "_chapter_cards_request", lambda *args, **kwargs: next(delete_lists)
    )
    deleted = delete_api.delete_chapter_card(course, clazz, "chapter-1", "card-1")
    assert deleted["remaining_card_count"] == 0
    assert delete_session.calls[0][1].endswith("/edit/deletecard")
    assert delete_session.calls[0][2]["data"] == {"id": "card-1", "courseId": "course-1"}


def test_parse_course_data_items_extracts_download_metadata() -> None:
    html = """
    <ul class="dataBody_td" dataName="Guide.pdf" type="pdf" id="9" isdown="1"
        objectId="object-9" url="" loadurl="">
      <a class="rename_title" title="Guide.pdf"></a>
      <a id="reader_9">4</a>
      <a href="/coursedata/downloadData?dataId=9">下载</a>
      <a onclick="cancelTopSetting('9')">取消置顶</a>
      <li class="dataBody_down"><div class="dataBody_read_select">2</div></li>
      <li class="dataBody_size">397KB</li>
      <li class="dataBody_creater">教师</li>
    </ul>
    """
    items = parse_course_data_items(html)
    assert items[0]["data_id"] == "9"
    assert items[0]["name"] == "Guide.pdf"
    assert items[0]["reader_count"] == 4
    assert items[0]["download_count"] == 2
    assert items[0]["download_url"].endswith("dataId=9")
    assert items[0]["is_top"] is True

    folder = parse_course_data_items(
        """
        <ul class="dataBody_td" dataName="Unit 1" type="afolder" id="10">
          <a class="rename_title" title="Unit 1"></a>
          <a onclick="toppingButton('10','afolder','1','0')">置顶</a>
        </ul>
        """
    )[0]
    assert folder["is_top"] is False
    assert folder["root_id"] == "0"


def test_parse_resource_import_courses_and_items() -> None:
    courses = parse_resource_import_courses(
        """
        <ul><li data="200" data-cpi="300" onclick="intoCourseDataPop('200',300,'Old')">
          <span>Previous Course</span>
        </li></ul>
        """
    )
    assert courses == [
        {
            "index": 1,
            "course_id": "200",
            "cpi": "300",
            "course_name": "Previous Course",
            "title": "Previous Course",
        }
    ]
    parsed = parse_resource_import_items(
        {
            "data": {
                "total": 2,
                "courseDatas": [
                    {"id": 1, "name": "Unit 1", "xtype": "dir", "type": ".afolder"},
                    {
                        "id": 2,
                        "name": "Guide.pdf",
                        "xtype": "file",
                        "type": ".pdf",
                        "objectid": "object-2",
                        "hsize": "12KB",
                    },
                ],
            }
        }
    )
    assert parsed["total_pages"] == 2
    assert parsed["items"][0]["is_folder"] is True
    assert parsed["items"][1]["object_id"] == "object-2"


def test_parse_resource_labels_extracts_assignment_and_permissions() -> None:
    labels = parse_resource_labels(
        """
        <ul>
          <li data="22382217" class="topiclabelli">
            <input class="topicLabelCheckBox" checked="checked" />
            <div class="tree_text topicname">期末复习</div>
            <a class="edittopiclabel">编辑</a>
            <a class="deletetopiclabel">删除</a>
          </li>
          <li data="22382218" class="topiclabelli">
            <input class="topicLabelCheckBox" />
            <div class="tree_text topicname">写作</div>
          </li>
        </ul>
        """
    )
    assert labels == [
        {
            "index": 1,
            "label_id": "22382217",
            "name": "期末复习",
            "title": "期末复习",
            "assigned": True,
            "editable": True,
            "deletable": True,
        },
        {
            "index": 2,
            "label_id": "22382218",
            "name": "写作",
            "title": "写作",
            "assigned": False,
            "editable": False,
            "deletable": False,
        },
    ]


def test_resolve_resource_item_supports_id_name_and_path() -> None:
    items = [
        {
            "index": 1,
            "data_id": "10",
            "name": "Guide.pdf",
            "path": "Unit 1/Guide.pdf",
            "is_folder": False,
        },
        {
            "index": 2,
            "data_id": "20",
            "name": "Unit 1",
            "path": "Unit 1",
            "is_folder": True,
        },
    ]
    assert resolve_resource_item(items, "10")["name"] == "Guide.pdf"
    assert resolve_resource_item(items, "Unit 1/Guide.pdf")["data_id"] == "10"
    assert resolve_resource_item(items, "Unit 1", require_folder=True)["data_id"] == "20"


class ResourceResponse:
    def __init__(
        self,
        payload: dict | str | bytes,
        *,
        url: str = "https://mooc2-ans.chaoxing.com/result",
        headers: dict[str, str] | None = None,
        chunks: list[bytes] | None = None,
    ) -> None:
        if isinstance(payload, bytes):
            self.content = payload
        elif isinstance(payload, str):
            self.content = payload.encode("utf-8")
        else:
            self.content = json.dumps(payload).encode("utf-8")
        self.encoding = "utf-8"
        self.apparent_encoding = "utf-8"
        self.url = url
        self.headers = headers or {"Content-Type": "application/json"}
        self._chunks = chunks if chunks is not None else [self.content]

    @staticmethod
    def raise_for_status() -> None:
        return None

    def json(self):
        return json.loads(self.content.decode("utf-8"))

    def iter_content(self, chunk_size: int):
        del chunk_size
        yield from self._chunks


class ResourceSession:
    def __init__(self, responses: list[ResourceResponse]) -> None:
        self.responses = iter(responses)
        self.calls: list[tuple[str, str, dict]] = []

    def get(self, url: str, **kwargs):
        self.calls.append(("GET", url, kwargs))
        return next(self.responses)

    def post(self, url: str, **kwargs):
        self.calls.append(("POST", url, kwargs))
        return next(self.responses)


def resource_context(session: ResourceSession) -> dict:
    return {
        "session": session,
        "root_url": "https://mooc2-ans.chaoxing.com/mooc2-ans/coursedata?courseid=1",
        "root_html": "",
        "hidden": {"source": "1", "isOpen": "0", "microTopicId": "0"},
    }


def cloud_context(session: ResourceSession) -> dict:
    return {
        "session": session,
        "root_url": "https://pan-yz.chaoxing.com/pcuserpan/index",
        "current_puid": "405017213",
        "root_id": "1167495992583606272",
        "enc": "enc-1",
        "auth_header": "",
        "request_token": "request-token",
        "client_token": "client-token",
    }


def course_asset_context(session: ResourceSession, kind: str = "courseware") -> dict:
    return {
        "session": session,
        "kind": kind,
        "config": COURSE_ASSET_KINDS[kind],
        "root_url": "https://mobilelearn.chaoxing.com/page/ppt/coursewareList",
    }


def test_resource_folder_create_rename_move_and_delete_contracts(monkeypatch) -> None:
    course = {"course_id": "course-1", "course_name": "Course", "cpi": "cpi-1"}
    clazz = {"clazz_id": "class-1", "clazz_name": "Class"}
    created = {
        "index": 1,
        "data_id": "folder-1",
        "name": "Unit 1",
        "title": "Unit 1",
        "is_folder": True,
        "parent_id": "0",
    }

    create_session = ResourceSession([ResourceResponse("folder-1")])
    create_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(create_api, "_session", lambda: create_session)
    monkeypatch.setattr(
        create_api, "_resource_context", lambda *args: resource_context(create_session)
    )
    folder_lists = iter([[], [created]])
    monkeypatch.setattr(
        create_api, "_resource_folder_items", lambda *args, **kwargs: next(folder_lists)
    )
    result = create_api.create_resource_folder(course, clazz, "Unit 1")
    assert result["folder"]["data_id"] == "folder-1"
    assert create_session.calls[0][1].endswith("/coursedata/add-folder")
    assert create_session.calls[0][2]["data"]["rootId"] == "0"

    renamed = {**created, "name": "Unit One", "title": "Unit One"}
    rename_session = ResourceSession([ResourceResponse("ok")])
    rename_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(rename_api, "_session", lambda: rename_session)
    monkeypatch.setattr(
        rename_api, "_resource_context", lambda *args: resource_context(rename_session)
    )
    rename_trees = iter([[created], [renamed]])
    monkeypatch.setattr(
        rename_api, "_resource_tree_from_context", lambda *args, **kwargs: next(rename_trees)
    )
    rename_result = rename_api.rename_resource(course, clazz, "folder-1", "Unit One")
    assert rename_result["resource"]["name"] == "Unit One"
    assert rename_session.calls[0][2]["data"]["dataId"] == "folder-1"

    file_item = {
        "index": 1,
        "data_id": "file-1",
        "name": "Guide.pdf",
        "title": "Guide.pdf",
        "is_folder": False,
        "parent_id": "0",
        "path": "Guide.pdf",
    }
    destination = {
        "index": 2,
        "data_id": "folder-1",
        "name": "Unit One",
        "title": "Unit One",
        "is_folder": True,
        "parent_id": "0",
        "path": "Unit One",
    }
    moved = {**file_item, "parent_id": "folder-1", "path": "Unit One/Guide.pdf"}
    move_session = ResourceSession([ResourceResponse("ok")])
    move_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(move_api, "_session", lambda: move_session)
    monkeypatch.setattr(move_api, "_resource_context", lambda *args: resource_context(move_session))
    move_trees = iter([[file_item, destination], [moved, destination]])
    monkeypatch.setattr(
        move_api, "_resource_tree_from_context", lambda *args, **kwargs: next(move_trees)
    )
    monkeypatch.setattr(move_api, "_resolve_resource_parent", lambda *args: destination)
    move_result = move_api.move_resources(course, clazz, ["file-1"], destination="folder-1")
    assert move_result["moved"][0]["parent_id"] == "folder-1"
    assert move_session.calls[0][2]["data"]["dataId"] == "file-1--"

    delete_session = ResourceSession([ResourceResponse({"status": True})])
    delete_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(delete_api, "_session", lambda: delete_session)
    monkeypatch.setattr(
        delete_api, "_resource_context", lambda *args: resource_context(delete_session)
    )
    monkeypatch.setattr(
        delete_api, "_resource_tree_from_context", lambda *args, **kwargs: [file_item]
    )
    monkeypatch.setattr(delete_api, "_resource_folder_items", lambda *args, **kwargs: [])
    deleted = delete_api.delete_resources(course, clazz, ["file-1"])
    assert deleted["affected_parent_remaining_count"] == 0
    assert "1 affected parent folders" in deleted["verification"]
    assert delete_session.calls[0][2]["params"]["dataId"] == "file-1"


def test_resource_delete_numeric_id_uses_direct_resolution_and_parent_refresh(
    monkeypatch,
) -> None:
    course = {"course_id": "course-1", "course_name": "Course", "cpi": "cpi-1"}
    clazz = {"clazz_id": "class-1", "clazz_name": "Class"}
    file_item = {
        "index": 1,
        "data_id": "123",
        "name": "Guide.pdf",
        "title": "Guide.pdf",
        "is_folder": False,
        "parent_id": "0",
        "parent_name": "根目录",
        "path": "Guide.pdf",
    }
    delete_session = ResourceSession([ResourceResponse({"status": True})])
    delete_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(delete_api, "_session", lambda: delete_session)
    monkeypatch.setattr(
        delete_api, "_resource_context", lambda *args: resource_context(delete_session)
    )
    monkeypatch.setattr(
        delete_api,
        "_resolve_resource_from_context",
        lambda *args, **kwargs: file_item,
    )

    def unexpected_tree(*args, **kwargs):
        raise AssertionError("numeric ID should not build the full tree")

    monkeypatch.setattr(
        delete_api,
        "_resource_tree_from_context",
        unexpected_tree,
    )
    folder_calls: list[dict] = []

    def folder_items(*args, **kwargs):
        folder_calls.append(kwargs)
        return []

    monkeypatch.setattr(delete_api, "_resource_folder_items", folder_items)
    result = delete_api.delete_resources(course, clazz, ["123"])
    assert result["affected_parent_remaining_count"] == 0
    assert folder_calls == [{"folder_id": "0", "folder_name": "根目录"}]


def test_resource_top_and_copy_contracts(monkeypatch) -> None:
    course = {"course_id": "course-1", "course_name": "Course", "cpi": "cpi-1"}
    clazz = {"clazz_id": "class-1", "clazz_name": "Class"}
    source = {
        "index": 1,
        "data_id": "10",
        "name": "Unit 1",
        "title": "Unit 1",
        "data_type": "afolder",
        "is_folder": True,
        "is_top": False,
        "parent_id": "0",
        "parent_name": "根目录",
        "path": "Unit 1",
    }
    topped = {**source, "is_top": True}
    top_session = ResourceSession([ResourceResponse({"status": True})])
    top_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(top_api, "_session", lambda: top_session)
    monkeypatch.setattr(top_api, "_resource_context", lambda *args: resource_context(top_session))
    monkeypatch.setattr(top_api, "_resolve_resource_from_context", lambda *args, **kwargs: source)
    monkeypatch.setattr(top_api, "_resource_folder_items", lambda *args, **kwargs: [topped])
    top_result = top_api.set_resource_top_status(course, clazz, "10", top=True)
    assert top_result["resource"]["is_top"] is True
    assert top_session.calls[0][1].endswith("/coursedata/set-top")
    assert top_session.calls[0][2]["data"]["rootId"] == "0"

    copied = {**source, "data_id": "11", "name": "Unit 1 (1)", "title": "Unit 1 (1)"}
    copy_session = ResourceSession([ResourceResponse({"status": True})])
    copy_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(copy_api, "_session", lambda: copy_session)
    monkeypatch.setattr(copy_api, "_resource_context", lambda *args: resource_context(copy_session))
    monkeypatch.setattr(copy_api, "_resolve_resource_from_context", lambda *args, **kwargs: source)
    sibling_lists = iter([[source], [source, copied]])
    monkeypatch.setattr(
        copy_api, "_resource_folder_items", lambda *args, **kwargs: next(sibling_lists)
    )
    copy_result = copy_api.copy_resource(course, clazz, "10")
    assert copy_result["resource"]["data_id"] == "11"
    assert copy_session.calls[0][1].endswith("/coursedata/copyCourseDataByResId")

    file_source = {
        **source,
        "data_id": "20",
        "name": "Guide.pdf",
        "title": "Guide.pdf",
        "data_type": "pdf",
        "is_folder": False,
        "object_id": "object-20",
    }
    cloud_destination = {
        "resource_id": "cloud-folder-1",
        "name": "Archive",
        "is_file": False,
        "is_folder": True,
        "owner_puid": "405017213",
        "parent_id": "cloud-root",
    }
    cloud_copy = {
        "resource_id": "cloud-file-1",
        "name": "Guide.pdf",
        "object_id": "object-20",
        "is_file": True,
        "is_folder": False,
    }
    cloud_copy_session = ResourceSession([ResourceResponse("true")])
    cloud_copy_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(cloud_copy_api, "_session", lambda: cloud_copy_session)
    monkeypatch.setattr(
        cloud_copy_api,
        "_resource_context",
        lambda *args: resource_context(cloud_copy_session),
    )
    monkeypatch.setattr(
        cloud_copy_api,
        "_resolve_resource_from_context",
        lambda *args, **kwargs: file_source,
    )
    monkeypatch.setattr(
        cloud_copy_api,
        "_cloud_disk_context",
        lambda *args: cloud_context(cloud_copy_session),
    )
    monkeypatch.setattr(
        cloud_copy_api,
        "_resolve_cloud_disk_folder",
        lambda *args: cloud_destination,
    )
    cloud_lists = iter([{"items": []}, {"items": [cloud_copy]}])
    monkeypatch.setattr(
        cloud_copy_api,
        "_cloud_disk_listing",
        lambda *args, **kwargs: next(cloud_lists),
    )
    cloud_result = cloud_copy_api.copy_resource_to_cloud_disk(
        course,
        clazz,
        "20",
        destination="Archive",
    )
    assert cloud_result["cloud_item"]["resource_id"] == "cloud-file-1"
    assert cloud_copy_session.calls[0][1].endswith("/coursedata/copy-to-cloud-disk")
    assert cloud_copy_session.calls[0][2]["data"]["fldid"] == "cloud-folder-1"


def test_resource_link_upload_download_and_permission_contracts(
    monkeypatch, tmp_path: Path
) -> None:
    course = {"course_id": "course-1", "course_name": "Course", "cpi": "cpi-1"}
    clazz = {"clazz_id": "class-1", "clazz_name": "Class"}
    link = {
        "index": 1,
        "data_id": "link-1",
        "name": "Reference",
        "title": "Reference",
        "data_type": "url",
        "is_folder": False,
        "parent_id": "0",
    }
    link_session = ResourceSession([ResourceResponse({"status": True, "key": "key-1"})])
    link_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(link_api, "_session", lambda: link_session)
    monkeypatch.setattr(link_api, "_resource_context", lambda *args: resource_context(link_session))
    link_lists = iter([[], [link]])
    monkeypatch.setattr(
        link_api, "_resource_folder_items", lambda *args, **kwargs: next(link_lists)
    )
    created_link = link_api.create_resource_link(course, clazz, "Reference", "https://example.com")
    assert created_link["resource"]["data_id"] == "link-1"
    record = json.loads(link_session.calls[0][2]["data"]["jsonData"])[0]
    assert record["url"] == "https://example.com"
    assert record["dataType"] == "url"

    upload_path = tmp_path / "test.txt"
    upload_path.write_text("browser-free upload", encoding="utf-8")
    uploaded_item = {
        "index": 1,
        "data_id": "file-1",
        "name": "test.txt",
        "title": "test.txt",
        "data_type": "txt",
        "is_folder": False,
        "object_id": "object-1",
        "parent_id": "0",
    }
    upload_session = ResourceSession(
        [
            ResourceResponse(
                {
                    "state": "SUCCESS",
                    "url": "object-1",
                    "fileSize": upload_path.stat().st_size,
                    "fileType": "txt",
                    "fileRealType": "text/plain",
                }
            ),
            ResourceResponse({"status": True, "key": "key-2"}),
        ]
    )
    upload_context = resource_context(upload_session)
    upload_context["root_html"] = (
        "var commonUploadUrl = ServerHost.uploadDomain + '/upload/uploadNew?t=1&enc2=abc&userId=2';"
    )
    upload_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(upload_api, "_session", lambda: upload_session)
    monkeypatch.setattr(upload_api, "_resource_context", lambda *args: upload_context)
    monkeypatch.setattr(
        upload_api,
        "_find_active_cloud_disk_item_by_object_id",
        lambda *args, **kwargs: None,
    )
    upload_lists = iter([[], [uploaded_item]])
    monkeypatch.setattr(
        upload_api, "_resource_folder_items", lambda *args, **kwargs: next(upload_lists)
    )
    uploaded = upload_api.upload_resource_file(course, clazz, upload_path)
    assert uploaded["resource"]["object_id"] == "object-1"
    assert uploaded["cloud_resource"] is None
    assert "cloud disk" in uploaded["cloud_side_effect"]
    assert upload_session.calls[0][1].startswith(
        "https://mooc1.chaoxing.com/upload-ans/upload/uploadNew"
    )
    assert "files" in upload_session.calls[0][2]
    upload_record = json.loads(upload_session.calls[1][2]["data"]["jsonData"])[0]
    assert upload_record["objectId"] == "object-1"

    download_item = {
        **uploaded_item,
        "download_url": "https://mooc1.chaoxing.com/coursedata/downloadData?dataId=file-1",
    }
    download_session = ResourceSession(
        [
            ResourceResponse(
                b"downloaded bytes",
                url=download_item["download_url"],
                headers={
                    "Content-Type": "text/plain",
                    "Content-Disposition": "attachment; filename=test.txt",
                },
                chunks=[b"downloaded ", b"bytes"],
            )
        ]
    )
    download_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(download_api, "_session", lambda: download_session)
    monkeypatch.setattr(
        download_api, "_resource_context", lambda *args: resource_context(download_session)
    )
    monkeypatch.setattr(
        download_api,
        "_resource_tree_from_context",
        lambda *args, **kwargs: [download_item],
    )
    downloaded = download_api.download_resource_file(
        course, clazz, "file-1", tmp_path / "downloads"
    )
    assert Path(downloaded["output_path"]).read_bytes() == b"downloaded bytes"

    permitted = {**download_item, "can_download": False}
    permission_session = ResourceSession([ResourceResponse({"status": True})])
    permission_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(permission_api, "_session", lambda: permission_session)
    monkeypatch.setattr(
        permission_api,
        "_resource_context",
        lambda *args: resource_context(permission_session),
    )
    permission_trees = iter([[download_item], [permitted]])
    monkeypatch.setattr(
        permission_api,
        "_resource_tree_from_context",
        lambda *args, **kwargs: next(permission_trees),
    )
    permission = permission_api.set_resource_download_permission(
        course, clazz, ["file-1"], allow_download=False
    )
    assert permission["resources"][0]["can_download"] is False
    assert permission_session.calls[0][2]["data"]["isDownload"] == "0"


def test_resource_folder_download_builds_local_zip_without_client(
    monkeypatch, tmp_path: Path
) -> None:
    course = {"course_id": "course-1", "course_name": "Course", "cpi": "cpi-1"}
    clazz = {"clazz_id": "class-1", "clazz_name": "Class"}
    folder = {
        "index": 1,
        "data_id": "folder-1",
        "name": "Unit 1",
        "title": "Unit 1",
        "data_type": "afolder",
        "is_folder": True,
        "parent_id": "0",
        "path": "Unit 1",
    }
    file_item = {
        "index": 2,
        "data_id": "file-1",
        "name": "Guide.txt",
        "title": "Guide.txt",
        "data_type": "txt",
        "is_folder": False,
        "parent_id": "folder-1",
        "path": "Unit 1/Guide.txt",
        "source_url": "",
    }
    link_item = {
        "index": 3,
        "data_id": "link-1",
        "name": "Reference",
        "title": "Reference",
        "data_type": "url",
        "is_folder": False,
        "parent_id": "folder-1",
        "path": "Unit 1/Reference",
        "source_url": "https://example.com/",
    }
    empty_folder = {
        "index": 4,
        "data_id": "folder-2",
        "name": "Empty",
        "title": "Empty",
        "data_type": "afolder",
        "is_folder": True,
        "parent_id": "folder-1",
        "path": "Unit 1/Empty",
    }
    api = ChaoxingAPI(Path("unused-cookies.json"))
    session = ResourceSession([])
    monkeypatch.setattr(api, "_session", lambda: session)
    monkeypatch.setattr(api, "_resource_context", lambda *args: resource_context(session))
    monkeypatch.setattr(
        api,
        "_resource_tree_from_context",
        lambda *args, **kwargs: [folder, file_item, link_item, empty_folder],
    )
    monkeypatch.setattr(
        api,
        "_resource_file_response",
        lambda *args: (
            ResourceResponse(b"course file", headers={"Content-Type": "text/plain"}),
            "text/plain",
        ),
    )
    output_directory = tmp_path / "downloads"
    output_directory.mkdir()
    result = api.download_resource_items(course, clazz, ["folder-1"], output_directory)
    assert result["archive"] is True
    assert result["file_count"] == 1
    assert result["link_count"] == 1
    with zipfile.ZipFile(result["output_path"]) as archive:
        assert set(archive.namelist()) == {
            "Unit 1/Guide.txt",
            "Unit 1/Reference.url",
            "Unit 1/Empty/",
        }
        assert archive.read("Unit 1/Guide.txt") == b"course file"
        assert b"URL=https://example.com/" in archive.read("Unit 1/Reference.url")


def test_course_cloud_source_list_and_import_contracts(monkeypatch) -> None:
    course = {"course_id": "course-1", "course_name": "Course", "cpi": "cpi-1"}
    clazz = {"clazz_id": "class-1", "clazz_name": "Class"}
    source_path = "/0/100"
    source_raw = {
        "path": "/0/100/200",
        "xtype": "file",
        "size": 2048,
        "uploadDate": "2026-08-31 10:00",
        "name": "Guide.pdf",
        "suffix": "pdf",
        "resid": "200",
        "objectid": "object-200",
    }
    list_session = ResourceSession(
        [
            ResourceResponse(
                [
                    {"path": "/0", "xtype": "back", "name": "返回上一级"},
                    source_raw,
                ]
            )
        ]
    )
    list_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(list_api, "_session", lambda: list_session)
    monkeypatch.setattr(
        list_api,
        "_resource_context",
        lambda *args: resource_context(list_session),
    )
    listing = list_api.list_course_cloud_sources(
        course,
        clazz,
        path=source_path,
    )
    assert listing["parent_path"] == "/0"
    assert listing["items"][0]["object_id"] == "object-200"
    assert list_session.calls[0][1].endswith("/coursedata/file-list")

    source = listing["items"][0]
    destination = {
        "data_id": "folder-1",
        "name": "Unit 1",
        "path": "Unit 1",
        "depth": 1,
        "is_folder": True,
    }
    imported = {
        "index": 1,
        "data_id": "resource-1",
        "name": "Guide.pdf",
        "title": "Guide.pdf",
        "data_type": "pdf",
        "is_folder": False,
        "parent_id": "folder-1",
    }
    import_session = ResourceSession([ResourceResponse({"result": True, "exist": False})])
    import_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(import_api, "_session", lambda: import_session)
    monkeypatch.setattr(
        import_api,
        "_resource_context",
        lambda *args: resource_context(import_session),
    )
    monkeypatch.setattr(import_api, "_resolve_resource_parent", lambda *args: destination)
    monkeypatch.setattr(
        import_api,
        "_course_cloud_source_page",
        lambda *args, **kwargs: {"items": [source]},
    )
    folder_lists = iter([[], [imported]])
    monkeypatch.setattr(
        import_api,
        "_resource_folder_items",
        lambda *args, **kwargs: next(folder_lists),
    )
    result = import_api.import_cloud_files_to_resources(
        course,
        clazz,
        ["200"],
        source_path=source_path,
        destination="Unit 1",
    )
    assert result["resources"][0]["data_id"] == "resource-1"
    import_call = import_session.calls[0]
    assert import_call[1].endswith("/coursedata/addYunPan")
    record = json.loads(import_call[2]["data"]["f"])[0]
    assert record == {
        "objectid": "object-200",
        "name": "Guide.pdf",
        "size": 2048,
        "hsize": "2 KB",
        "type": ".pdf",
    }


def test_course_cloud_folder_import_contract(monkeypatch) -> None:
    course = {"course_id": "course-1", "course_name": "Course", "cpi": "cpi-1"}
    clazz = {"clazz_id": "class-1", "clazz_name": "Class"}
    source = {
        "index": 1,
        "resource_id": "cloud-folder-1",
        "name": "Review",
        "title": "Review",
        "path": "/0/cloud-folder-1",
        "is_file": False,
        "is_folder": True,
        "suffix": "",
        "byte_count": 0,
        "object_id": "",
        "upload_time": None,
        "catalog_id": None,
        "file_path": "",
        "extra_info": None,
        "share_id": "0",
    }
    destination = {
        "data_id": "folder-1",
        "name": "Unit 1",
        "path": "Unit 1",
        "depth": 1,
        "is_folder": True,
    }
    imported = {
        "index": 1,
        "data_id": "resource-folder-1",
        "name": "Review",
        "title": "Review",
        "data_type": "afolder",
        "is_folder": True,
        "parent_id": "folder-1",
    }
    session = ResourceSession([ResourceResponse({"result": True, "exist": False})])
    api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(api, "_session", lambda: session)
    monkeypatch.setattr(api, "_resource_context", lambda *args: resource_context(session))
    monkeypatch.setattr(api, "_resolve_resource_parent", lambda *args: destination)
    source_pages = iter([{"items": [source]}, {"items": []}])
    monkeypatch.setattr(
        api,
        "_course_cloud_source_page",
        lambda *args, **kwargs: next(source_pages),
    )
    resource_pages = iter([[], [imported], []])
    monkeypatch.setattr(
        api,
        "_resource_folder_items",
        lambda *args, **kwargs: next(resource_pages),
    )
    result = api.import_cloud_folder_to_resources(
        course,
        clazz,
        "cloud-folder-1",
        destination="Unit 1",
    )
    assert result["folder"]["data_id"] == "resource-folder-1"
    assert result["direct_child_count"] == 0
    assert session.calls[0][1].endswith("/coursedata/addYunPanFolder")
    assert session.calls[0][2]["data"]["yunPanFolderId"] == "cloud-folder-1"


def test_resource_label_http_contracts(monkeypatch) -> None:
    course = {"course_id": "course-1", "course_name": "Course", "cpi": "cpi-1"}
    clazz = {"clazz_id": "class-1", "clazz_name": "Class"}
    resource = {
        "index": 1,
        "data_id": "resource-1",
        "name": "Guide.pdf",
        "title": "Guide.pdf",
        "path": "Guide.pdf",
        "is_folder": False,
    }
    initial = {
        "index": 1,
        "label_id": "label-1",
        "name": "Review",
        "title": "Review",
        "assigned": False,
        "editable": True,
        "deletable": True,
    }
    renamed = {**initial, "name": "Final review", "title": "Final review"}

    list_session = ResourceSession(
        [
            ResourceResponse(
                """
                <li data="label-1" class="topiclabelli">
                  <input class="topicLabelCheckBox" checked />
                  <div class="tree_text topicname">Review</div>
                  <a class="edittopiclabel"></a><a class="deletetopiclabel"></a>
                </li>
                """
            )
        ]
    )
    list_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(list_api, "_session", lambda: list_session)
    monkeypatch.setattr(list_api, "_resource_context", lambda *args: resource_context(list_session))
    monkeypatch.setattr(list_api, "_resolve_resource_from_context", lambda *args: resource)
    listing = list_api.list_resource_labels(course, clazz, "resource-1", search="Rev")
    assert listing["assigned_count"] == 1
    assert list_session.calls[0][1].endswith("/coursedata/getCourseDataLabelList")
    assert list_session.calls[0][2]["params"] == {
        "courseId": "course-1",
        "dataId": "resource-1",
        "query": "Rev",
    }

    create_session = ResourceSession(
        [ResourceResponse({"status": True, "saveTopiclabelId": "label-1"})]
    )
    create_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(create_api, "_session", lambda: create_session)
    monkeypatch.setattr(
        create_api, "_resource_context", lambda *args: resource_context(create_session)
    )
    monkeypatch.setattr(create_api, "_resolve_resource_from_context", lambda *args: resource)
    monkeypatch.setattr(
        create_api, "_resource_labels_from_context", lambda *args, **kwargs: [initial]
    )
    created = create_api.create_resource_label(course, clazz, "resource-1", "Review")
    assert created["label"]["label_id"] == "label-1"
    assert create_session.calls[0][1].endswith("/questionBankTopic/addtopiclable")
    assert create_session.calls[0][2]["params"]["name"] == "Review"

    rename_session = ResourceSession([ResourceResponse({"status": True})])
    rename_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(rename_api, "_session", lambda: rename_session)
    monkeypatch.setattr(
        rename_api, "_resource_context", lambda *args: resource_context(rename_session)
    )
    monkeypatch.setattr(rename_api, "_resolve_resource_from_context", lambda *args: resource)
    rename_reads = iter([[initial], [renamed]])
    monkeypatch.setattr(
        rename_api,
        "_resource_labels_from_context",
        lambda *args, **kwargs: next(rename_reads),
    )
    updated = rename_api.rename_resource_label(
        course, clazz, "resource-1", "label-1", "Final review"
    )
    assert updated["label"]["name"] == "Final review"
    assert rename_session.calls[0][1].endswith("/questionBankTopic/updatetopiclabel")
    assert rename_session.calls[0][2]["params"]["topicLabelId"] == "label-1"

    delete_session = ResourceSession([ResourceResponse({"status": True})])
    delete_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(delete_api, "_session", lambda: delete_session)
    monkeypatch.setattr(
        delete_api, "_resource_context", lambda *args: resource_context(delete_session)
    )
    monkeypatch.setattr(delete_api, "_resolve_resource_from_context", lambda *args: resource)
    delete_reads = iter([[renamed], []])
    monkeypatch.setattr(
        delete_api,
        "_resource_labels_from_context",
        lambda *args, **kwargs: next(delete_reads),
    )
    deleted = delete_api.delete_resource_label(course, clazz, "resource-1", "label-1")
    assert deleted["label"]["label_id"] == "label-1"
    assert delete_session.calls[0][1].endswith("/questionBankTopic/deletetopiclabel")

    assignment_session = ResourceSession([ResourceResponse({"status": True})])
    assignment_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(assignment_api, "_session", lambda: assignment_session)
    monkeypatch.setattr(
        assignment_api,
        "_resource_context",
        lambda *args: resource_context(assignment_session),
    )
    monkeypatch.setattr(assignment_api, "_resource_tree_from_context", lambda *args: [resource])
    assignment_reads = iter([[initial], [{**initial, "assigned": True}]])
    monkeypatch.setattr(
        assignment_api,
        "_resource_labels_from_context",
        lambda *args, **kwargs: next(assignment_reads),
    )
    assigned = assignment_api.update_resource_labels(course, clazz, ["resource-1"], ["label-1"])
    assert assigned["verified"][0]["assigned_label_ids"] == ["label-1"]
    assert assignment_session.calls[0][1].endswith("/coursedata/saveCourseDataLabelRelation")
    assert assignment_session.calls[0][2]["data"]["labelIds"] == "label-1,"

    clear_session = ResourceSession([ResourceResponse({"status": True})])
    clear_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(clear_api, "_session", lambda: clear_session)
    monkeypatch.setattr(
        clear_api, "_resource_context", lambda *args: resource_context(clear_session)
    )
    monkeypatch.setattr(clear_api, "_resource_tree_from_context", lambda *args: [resource])
    clear_reads = iter([[initial], [{**initial, "assigned": False}]])
    monkeypatch.setattr(
        clear_api,
        "_resource_labels_from_context",
        lambda *args, **kwargs: next(clear_reads),
    )
    cleared = clear_api.update_resource_labels(course, clazz, ["resource-1"], [])
    assert cleared["verified"][0]["assigned_label_ids"] == []
    assert clear_session.calls[0][2]["data"]["labelIds"] == ""


def test_course_asset_list_normalizes_courseware_and_teaching_plan(monkeypatch) -> None:
    course = {"course_id": "course-1", "course_name": "Course", "cpi": "cpi-1"}
    clazz = {"clazz_id": "class-1", "clazz_name": "Class"}
    payload = {
        "result": 1,
        "data": {
            "page": 1,
            "pageSize": 1000,
            "totalPage": 1,
            "totalCount": 2,
            "allCount": 2,
            "hasManagePermission": 1,
            "list": [
                {
                    "aid": 100,
                    "title": "Unit 1",
                    "type": 4,
                    "paid": 0,
                    "topsign": 1,
                    "childFileNum": 1,
                    "createName": "Teacher",
                },
                {
                    "aid": 101,
                    "title": "Slides",
                    "type": 1,
                    "paid": 0,
                    "suffix": "pptx",
                    "pptObjectId": "object-101",
                    "size": "1 MB",
                },
            ],
        },
    }
    session = ResourceSession([ResourceResponse(payload)])
    api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(api, "_course_asset_context", lambda *args: course_asset_context(session))
    listing = api.list_course_assets(course, clazz, "courseware")
    assert listing["items"][0]["is_folder"] is True
    assert listing["items"][0]["is_top"] is True
    assert listing["items"][1]["object_id"] == "object-101"
    assert listing["items"][1]["path"] == "Slides"
    assert session.calls[0][1].endswith("/v2/apis/activePlan/getCourseWareList")
    assert session.calls[0][2]["params"]["courseId"] == "course-1"

    teaching_session = ResourceSession([ResourceResponse({"result": 1, "data": {"list": []}})])
    teaching_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        teaching_api,
        "_course_asset_context",
        lambda *args: course_asset_context(teaching_session, "teaching_plan"),
    )
    teaching = teaching_api.list_course_assets(course, clazz, "teaching_plan")
    assert teaching["kind"] == "teaching_plan"
    assert teaching_session.calls[0][1].endswith("/v2/apis/activePlan/getTeachingPlanList")

    teaching_folder = ChaoxingAPI._normalize_course_asset(
        {
            "aid": 200,
            "title": "Teaching plans",
            "type": 7,
            "childFileNum": "unknown",
            "pptChildActiveNum": "",
            "pptEditUidList": " 101, 202,",
        },
        1,
        kind="teaching_plan",
        parent_id="0",
        parent_name="根目录",
        parent_path="",
        depth=1,
    )
    assert teaching_folder["is_folder"] is True
    assert teaching_folder["asset_type"] == "folder"
    assert teaching_folder["child_count"] == 0
    assert teaching_folder["activity_count"] == 0
    assert teaching_folder["teacher_edit_ids"] == ["101", "202"]

    duplicate_folder = payload["data"]["list"][0]
    duplicate_session = ResourceSession(
        [
            ResourceResponse({"result": 1, "data": {"totalPage": 1, "list": [duplicate_folder]}}),
            ResourceResponse({"result": 1, "data": {"totalPage": 1, "list": [duplicate_folder]}}),
        ]
    )
    duplicate_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        duplicate_api,
        "_course_asset_context",
        lambda *args: course_asset_context(duplicate_session),
    )
    deduplicated = duplicate_api.list_course_asset_tree(course, clazz, "courseware")
    assert deduplicated["count"] == 1


def test_course_asset_folder_and_mutation_http_contracts(monkeypatch) -> None:
    course = {"course_id": "course-1", "course_name": "Course", "cpi": "cpi-1"}
    clazz = {"clazz_id": "class-1", "clazz_name": "Class"}
    folder = {
        "index": 1,
        "asset_id": "100",
        "name": "Unit 1",
        "title": "Unit 1",
        "kind": "courseware",
        "type_code": 4,
        "asset_type": "folder",
        "is_folder": True,
        "parent_id": "0",
        "parent_name": "根目录",
        "path": "Unit 1",
        "depth": 1,
        "is_top": False,
    }
    renamed = {**folder, "name": "Unit One", "title": "Unit One", "path": "Unit One"}
    topped = {**renamed, "is_top": True}
    destination = {
        **folder,
        "asset_id": "200",
        "name": "Archive",
        "title": "Archive",
        "path": "Archive",
    }
    moved = {
        **renamed,
        "parent_id": "200",
        "parent_name": "Archive",
        "path": "Archive/Unit One",
        "depth": 2,
    }

    create_session = ResourceSession([ResourceResponse({"result": 1, "data": {"id": 100}})])
    create_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        create_api, "_course_asset_context", lambda *args: course_asset_context(create_session)
    )
    direct_reads = iter([[], [folder]])
    monkeypatch.setattr(
        create_api,
        "_course_asset_direct_items",
        lambda *args, **kwargs: next(direct_reads),
    )
    created = create_api.create_course_asset_folder(course, clazz, "courseware", "Unit 1")
    assert created["folder"]["asset_id"] == "100"
    assert create_session.calls[0][1].endswith("/widget/teachingPlan/createPPTFolder")
    assert create_session.calls[0][2]["data"]["parentFolderId"] == "0"

    rename_session = ResourceSession([ResourceResponse({"result": 1})])
    rename_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        rename_api, "_course_asset_context", lambda *args: course_asset_context(rename_session)
    )
    rename_reads = iter([[folder], [renamed]])
    monkeypatch.setattr(
        rename_api,
        "_course_asset_tree_from_context",
        lambda *args, **kwargs: next(rename_reads),
    )
    rename_result = rename_api.rename_course_asset(course, clazz, "courseware", "100", "Unit One")
    assert rename_result["asset"]["name"] == "Unit One"
    assert rename_session.calls[0][1].endswith("/widget/coursewareActive/changeActiveName")

    top_session = ResourceSession([ResourceResponse({"result": 1})])
    top_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        top_api, "_course_asset_context", lambda *args: course_asset_context(top_session)
    )
    top_reads = iter([[renamed], [topped]])
    monkeypatch.setattr(
        top_api,
        "_course_asset_tree_from_context",
        lambda *args, **kwargs: next(top_reads),
    )
    top_result = top_api.set_course_asset_top_status(course, clazz, "courseware", "100", top=True)
    assert top_result["asset"]["is_top"] is True
    assert top_session.calls[0][2]["params"]["topsign"] == 1

    move_session = ResourceSession([ResourceResponse({"result": 1})])
    move_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        move_api, "_course_asset_context", lambda *args: course_asset_context(move_session)
    )
    move_reads = iter([[renamed, destination], [moved, destination]])
    monkeypatch.setattr(
        move_api,
        "_course_asset_tree_from_context",
        lambda *args, **kwargs: next(move_reads),
    )
    move_result = move_api.move_course_assets(
        course, clazz, "courseware", ["100"], destination="200"
    )
    assert move_result["assets"][0]["parent_id"] == "200"
    assert move_session.calls[0][2]["params"]["activeIds"] == "100,"

    delete_session = ResourceSession([ResourceResponse({"result": 1})])
    delete_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        delete_api, "_course_asset_context", lambda *args: course_asset_context(delete_session)
    )
    delete_reads = iter([[moved, destination], [destination]])
    monkeypatch.setattr(
        delete_api,
        "_course_asset_tree_from_context",
        lambda *args, **kwargs: next(delete_reads),
    )
    deleted = delete_api.delete_course_assets(course, clazz, "courseware", ["100"])
    assert deleted["recoverable"] is True
    assert delete_session.calls[0][1].endswith("/widget/CWareDataController/deleteCPlansById")
    assert delete_session.calls[0][2]["params"]["cPlanIds"] == "100"


def test_course_asset_copy_download_and_recycle_contracts(monkeypatch, tmp_path) -> None:
    course = {"course_id": "course-1", "course_name": "Course", "cpi": "cpi-1"}
    clazz = {"clazz_id": "class-1", "clazz_name": "Class"}
    source = {
        "index": 1,
        "asset_id": "101",
        "name": "Slides",
        "title": "Slides",
        "kind": "courseware",
        "type_code": 1,
        "asset_type": "presentation",
        "is_folder": False,
        "parent_id": "0",
        "parent_name": "根目录",
        "path": "Slides",
        "depth": 1,
        "suffix": "pptx",
        "is_top": False,
    }
    copied = {**source, "asset_id": "102", "index": 2}
    copy_session = ResourceSession([ResourceResponse({"result": 1})])
    copy_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        copy_api, "_course_asset_context", lambda *args: course_asset_context(copy_session)
    )
    monkeypatch.setattr(copy_api, "_course_asset_tree_from_context", lambda *args: [source])
    copy_direct = iter([[source], [source, copied]])
    monkeypatch.setattr(
        copy_api,
        "_course_asset_direct_items",
        lambda *args, **kwargs: next(copy_direct),
    )
    copy_result = copy_api.copy_course_asset(course, clazz, "courseware", "101")
    assert copy_result["asset"]["asset_id"] == "102"
    assert copy_session.calls[0][1].endswith("/widget/teachingPlan/clonePPT")

    download_session = ResourceSession(
        [
            ResourceResponse(
                {
                    "result": 1,
                    "data": {
                        "name": "Slides",
                        "suffix": "pptx",
                        "objectId": "object-101",
                    },
                }
            ),
            ResourceResponse(
                b"presentation-bytes",
                headers={"Content-Type": "application/vnd.ms-powerpoint"},
            ),
        ]
    )
    download_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        download_api,
        "_course_asset_context",
        lambda *args: course_asset_context(download_session),
    )
    monkeypatch.setattr(download_api, "_course_asset_tree_from_context", lambda *args: [source])
    output = tmp_path / "Slides.pptx"
    downloaded = download_api.download_course_asset(course, clazz, "courseware", "101", output)
    assert output.read_bytes() == b"presentation-bytes"
    assert downloaded["byte_count"] == 18
    assert download_session.calls[0][1].endswith("/v2/apis/ppt/getPptInfo")
    assert "objectid=object-101" in download_session.calls[1][1]

    recycled = {**source, "recycled": True}
    restore_session = ResourceSession([ResourceResponse({"result": 1})])
    restore_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        restore_api,
        "_course_asset_context",
        lambda *args: course_asset_context(restore_session),
    )
    restore_reads = iter([[recycled], [], [source]])
    monkeypatch.setattr(
        restore_api,
        "_course_asset_tree_from_context",
        lambda *args, **kwargs: next(restore_reads),
    )
    restored = restore_api.restore_course_asset_recycle_items(course, clazz, "courseware", ["101"])
    assert restored["restored"][0]["asset_id"] == "101"
    assert restore_session.calls[0][1].endswith("/v2/apis/recycleBinPpt/recyclePptById")

    permanent_session = ResourceSession([ResourceResponse({"result": 1})])
    permanent_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        permanent_api,
        "_course_asset_context",
        lambda *args: course_asset_context(permanent_session),
    )
    permanent_reads = iter([[recycled], []])
    monkeypatch.setattr(
        permanent_api,
        "_course_asset_tree_from_context",
        lambda *args, **kwargs: next(permanent_reads),
    )
    permanently_deleted = permanent_api.permanently_delete_course_asset_recycle_items(
        course, clazz, "courseware", ["101"]
    )
    assert permanently_deleted["deleted"][0]["asset_id"] == "101"
    assert permanent_session.calls[0][1].endswith("/v2/apis/recycleBinPpt/deleteCompletely")


def test_course_asset_cloud_import_http_contract(monkeypatch) -> None:
    course = {"course_id": "course-1", "course_name": "Course", "cpi": "cpi-1"}
    clazz = {"clazz_id": "class-1", "clazz_name": "Class"}
    cloud_file = {
        "resource_id": "9001",
        "name": "Week 2.pdf",
        "title": "Week 2.pdf",
        "is_file": True,
        "is_folder": False,
        "suffix": "pdf",
        "byte_count": 407006,
        "object_id": "object-9001",
        "operations_disabled": False,
        "_encrypted_id": "encrypted-9001",
    }
    imported = {
        "index": 1,
        "asset_id": "101",
        "name": "Week 2.pdf",
        "title": "Week 2.pdf",
        "kind": "courseware",
        "type_code": 8,
        "asset_type": "pdf",
        "is_folder": False,
        "parent_id": "0",
        "parent_name": "根目录",
        "path": "Week 2.pdf",
        "depth": 1,
        "object_id": "object-9001",
        "suffix": "pdf",
    }
    session = ResourceSession([ResourceResponse({"result": 1, "data": [{"id": 101}]})])
    api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(api, "_course_asset_context", lambda *args: course_asset_context(session))
    monkeypatch.setattr(api, "_course_asset_tree_from_context", lambda *args: [])
    monkeypatch.setattr(api, "_cloud_disk_context", lambda *args: cloud_context(session))
    monkeypatch.setattr(api, "_resolve_active_cloud_disk_item", lambda *args: cloud_file)
    direct_reads = iter([[], [imported]])
    monkeypatch.setattr(
        api,
        "_course_asset_direct_items",
        lambda *args, **kwargs: next(direct_reads),
    )

    result = api.import_cloud_files_to_course_assets(
        course,
        clazz,
        "courseware",
        ["9001"],
    )
    assert result["imported"][0]["asset_id"] == "101"
    assert "_encrypted_id" not in result["selected"][0]
    assert session.calls[0][1].endswith("/widget/teachingPlan/createPPT")
    request_data = session.calls[0][2]["data"]
    assert request_data["parentFolderId"] == "0"
    assert json.loads(request_data["pptData"]) == [
        {
            "suffix": "pdf",
            "objectId": "object-9001",
            "name": "Week 2.pdf",
            "size": 407006,
        }
    ]

    teaching_session = ResourceSession([ResourceResponse({"result": 1})])
    teaching_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        teaching_api,
        "_course_asset_context",
        lambda *args: course_asset_context(teaching_session, "teaching_plan"),
    )
    monkeypatch.setattr(teaching_api, "_course_asset_tree_from_context", lambda *args: [])
    monkeypatch.setattr(
        teaching_api, "_cloud_disk_context", lambda *args: cloud_context(teaching_session)
    )
    monkeypatch.setattr(teaching_api, "_resolve_active_cloud_disk_item", lambda *args: cloud_file)
    teaching_imported = {**imported, "kind": "teaching_plan", "type_code": 8}
    teaching_reads = iter([[], [teaching_imported]])
    monkeypatch.setattr(
        teaching_api,
        "_course_asset_direct_items",
        lambda *args, **kwargs: next(teaching_reads),
    )
    teaching_api.import_cloud_files_to_course_assets(
        course,
        clazz,
        "teaching_plan",
        ["9001"],
    )
    assert teaching_session.calls[0][1].endswith("/widget/teachingPlan/createTeachPlanFileCommon")
    assert teaching_session.calls[0][2]["params"] == {
        "DB_STRATEGY": "COURSEID",
        "STRATEGY_PARA": "courseId",
    }


def test_cloud_disk_list_and_delete_http_contracts(monkeypatch) -> None:
    context_html = """
    <script>
      var currentPuid = "405017213";
      var rootdir = "1167495992583606272";
      var encstr = "enc-1";
      var p_auth_token = "";
    </script>
    """
    raw_item = {
        "id": "1301297178171625472",
        "name": "verification.txt",
        "puid": 405017213,
        "isfile": True,
        "filesize": 103,
        "objectId": "object-1",
        "encryptedId": "encrypted-1",
        "parentFolderId": "1170626147074138112",
        "parentFolderName": "Recent uploads",
    }

    list_session = ResourceSession(
        [
            ResourceResponse(
                context_html,
                url="https://pan-yz.chaoxing.com/pcuserpan/index",
            ),
            ResourceResponse({"totalCount": 1, "list": [raw_item]}),
        ]
    )
    list_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(list_api, "_session", lambda: list_session)
    listing = list_api.list_cloud_disk_items(search="verification")
    assert listing["items"][0]["resource_id"] == "1301297178171625472"
    assert listing["items"][0]["byte_count"] == 103
    assert "_encrypted_id" not in listing["items"][0]
    assert list_session.calls[1][1].endswith("/opt/listres")
    assert list_session.calls[1][2]["params"]["searchValue"] == "verification"

    file_info = {
        "result": True,
        "data": [
            {
                "resid": raw_item["id"],
                "name": raw_item["name"],
                "puid": raw_item["puid"],
                "isfile": True,
                "size": raw_item["filesize"],
                "objectId": raw_item["objectId"],
                "encryptedId": raw_item["encryptedId"],
            }
        ],
    }
    delete_session = ResourceSession(
        [
            ResourceResponse(
                context_html,
                url="https://pan-yz.chaoxing.com/pcuserpan/index",
            ),
            ResourceResponse(file_info),
            ResourceResponse({"totalCount": 1, "list": [raw_item]}),
            ResourceResponse({"success": True}),
            ResourceResponse({"totalCount": 0, "list": []}),
        ]
    )
    delete_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(delete_api, "_session", lambda: delete_session)
    deleted = delete_api.delete_cloud_disk_items([raw_item["id"]])
    assert deleted["count"] == 1
    delete_call = next(call for call in delete_session.calls if call[0] == "POST")
    assert delete_call[1].endswith("/opt/delres")
    assert delete_call[2]["data"] == {
        "resids": raw_item["id"],
        "resourcetype": "0",
        "puids": "405017213",
        "encryptedids": "encrypted-1",
    }


def test_cloud_disk_context_prefers_literal_client_token_over_cookie_expression(
    monkeypatch,
) -> None:
    context_html = """
    <script>
      var currentPuid = 405017213;
      var rootdir = "1167495992583606272";
      var encstr = "enc-1";
      var cx_p_token = getCookie("cx_p_token");
      var cx_p_token = "0123456789abcdef0123456789abcdef";
    </script>
    """
    session = ResourceSession(
        [
            ResourceResponse(
                context_html,
                url="https://pan-yz.chaoxing.com/pcuserpan/index",
            )
        ]
    )
    api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(api, "_session", lambda: session)
    context = api._cloud_disk_context()
    assert context["current_puid"] == "405017213"
    assert context["request_token"] == ""
    assert context["client_token"] == "0123456789abcdef0123456789abcdef"


def test_cloud_disk_create_rename_move_top_and_download_contracts(
    monkeypatch, tmp_path: Path
) -> None:
    root = {
        "resource_id": "1167495992583606272",
        "name": "根目录",
        "is_file": False,
        "is_folder": True,
        "owner_puid": "405017213",
        "parent_id": "",
    }
    folder = {
        "index": 1,
        "resource_id": "200",
        "name": "Unit 1",
        "is_file": False,
        "is_folder": True,
        "suffix": "",
        "resource_type": 2,
        "byte_count": 0,
        "object_id": "",
        "owner_puid": "405017213",
        "parent_id": root["resource_id"],
        "parent_name": "根目录",
        "path": "",
        "upload_time": None,
        "modified_time": None,
        "deleted_time": None,
        "expires_time": None,
        "is_top": False,
        "is_shared": False,
        "shared_to_me": False,
        "operations_disabled": False,
        "_encrypted_id": "encrypted-folder",
    }
    create_session = ResourceSession([ResourceResponse({"success": True, "data": {}})])
    create_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(create_api, "_session", lambda: create_session)
    monkeypatch.setattr(
        create_api, "_cloud_disk_context", lambda *args: cloud_context(create_session)
    )
    monkeypatch.setattr(create_api, "_resolve_cloud_disk_folder", lambda *args: root)
    create_lists = iter([{"items": []}, {"items": [folder]}])
    monkeypatch.setattr(
        create_api, "_cloud_disk_listing", lambda *args, **kwargs: next(create_lists)
    )
    created = create_api.create_cloud_disk_folder("Unit 1")
    assert created["folder"]["resource_id"] == "200"
    assert create_session.calls[0][1].endswith("/opt/newRootfolder")
    assert create_session.calls[0][2]["data"]["selectDlid"] == "onlyme"

    file_item = {
        **folder,
        "resource_id": "300",
        "name": "Guide.pdf",
        "is_file": True,
        "is_folder": False,
        "suffix": "pdf",
        "resource_type": 1,
        "byte_count": 16,
        "object_id": "object-1",
        "_encrypted_id": "encrypted-file",
    }
    renamed_item = {**file_item, "name": "Handout.pdf"}
    rename_session = ResourceSession(
        [ResourceResponse({"success": True, "data": {"name": "Handout.pdf"}})]
    )
    rename_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        rename_api, "_cloud_disk_context", lambda *args: cloud_context(rename_session)
    )
    rename_items = iter([file_item, renamed_item])
    monkeypatch.setattr(
        rename_api,
        "_resolve_active_cloud_disk_item",
        lambda *args, **kwargs: next(rename_items),
    )
    renamed = rename_api.rename_cloud_disk_item("300", "Handout")
    assert renamed["item"]["name"] == "Handout.pdf"
    assert rename_session.calls[0][2]["data"]["name"] == "Handout.pdf"

    moved_item = {**file_item, "parent_id": folder["resource_id"], "parent_name": folder["name"]}
    move_session = ResourceSession([ResourceResponse({"success": True})])
    move_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(move_api, "_cloud_disk_context", lambda *args: cloud_context(move_session))
    move_items = iter([file_item, moved_item])
    monkeypatch.setattr(
        move_api,
        "_resolve_active_cloud_disk_item",
        lambda *args, **kwargs: next(move_items),
    )
    monkeypatch.setattr(move_api, "_resolve_cloud_disk_folder", lambda *args: folder)
    moved = move_api.move_cloud_disk_items(["300"], destination="200")
    assert moved["moved"][0]["parent_id"] == "200"
    assert move_session.calls[0][2]["data"]["folderid"] == "200_405017213"

    topped_item = {**file_item, "is_top": True}
    top_session = ResourceSession([ResourceResponse({"result": True, "msg": "操作成功"})])
    top_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(top_api, "_cloud_disk_context", lambda *args: cloud_context(top_session))
    monkeypatch.setattr(top_api, "_resolve_active_cloud_disk_item", lambda *args: file_item)
    monkeypatch.setattr(
        top_api, "_cloud_disk_listing", lambda *args, **kwargs: {"items": [topped_item]}
    )
    topped = top_api.set_cloud_disk_top_status("300", top=True)
    assert topped["item"]["is_top"] is True
    assert top_session.calls[0][1].endswith("/opt/setupTop")

    download_session = ResourceSession(
        [
            ResourceResponse(
                b"cloud file bytes",
                headers={
                    "Content-Type": "application/pdf",
                    "Content-Disposition": 'attachment; filename="Guide.pdf"',
                },
            )
        ]
    )
    download_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        download_api, "_cloud_disk_context", lambda *args: cloud_context(download_session)
    )
    monkeypatch.setattr(download_api, "_resolve_active_cloud_disk_item", lambda *args: file_item)
    output = tmp_path / "cloud.pdf"
    downloaded = download_api.download_cloud_disk_item("300", output)
    assert downloaded["byte_count"] == len(b"cloud file bytes")
    assert output.read_bytes() == b"cloud file bytes"
    assert download_session.calls[0][1].endswith("/download/downloadFileV2")


def test_cloud_disk_folder_download_builds_local_zip_without_client(
    monkeypatch, tmp_path: Path
) -> None:
    folder = {
        "index": 1,
        "resource_id": "200",
        "name": "Unit 1",
        "title": "Unit 1",
        "is_file": False,
        "is_folder": True,
        "suffix": "",
        "resource_type": 2,
        "byte_count": 0,
        "object_id": "",
        "owner_puid": "405017213",
        "parent_id": "1167495992583606272",
        "parent_name": "根目录",
        "path": "",
        "upload_time": None,
        "modified_time": None,
        "deleted_time": None,
        "expires_time": None,
        "is_top": False,
        "is_shared": False,
        "shared_to_me": False,
        "operations_disabled": False,
        "_encrypted_id": "encrypted-folder",
    }
    child = {
        **folder,
        "resource_id": "201",
        "name": "Guide.txt",
        "title": "Guide.txt",
        "is_file": True,
        "is_folder": False,
        "suffix": "txt",
        "resource_type": 1,
        "byte_count": 12,
        "object_id": "object-1",
        "parent_id": "200",
        "parent_name": "Unit 1",
        "_encrypted_id": "encrypted-file",
    }
    session = ResourceSession(
        [ResourceResponse(b"folder content", headers={"Content-Type": "text/plain"})]
    )
    api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(api, "_cloud_disk_context", lambda *args: cloud_context(session))
    monkeypatch.setattr(api, "_resolve_active_cloud_disk_item", lambda *args: folder)
    monkeypatch.setattr(api, "_cloud_disk_listing", lambda *args, **kwargs: {"items": [child]})
    output = tmp_path / "unit.zip"
    result = api.download_cloud_disk_items(["200"], output)
    assert result["archive"] is True
    assert result["file_count"] == 1
    with zipfile.ZipFile(output) as archive:
        assert archive.read("Unit 1/Guide.txt") == b"folder content"


def test_cloud_disk_recycle_list_restore_delete_and_empty_contracts(monkeypatch) -> None:
    raw_recycle = {
        "id": "400",
        "name": "Recovered.txt",
        "puid": "405017213",
        "isfile": True,
        "filesize": 12,
        "encryptedId": "encrypted-recycle",
        "parentFolderId": "1167495992583606272",
        "validtimestr": "6 days",
    }
    list_session = ResourceSession([ResourceResponse({"totalCount": 1, "data": [raw_recycle]})])
    list_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(list_api, "_cloud_disk_context", lambda *args: cloud_context(list_session))
    recycle = list_api.list_cloud_disk_recycle_items()
    assert recycle["items"][0]["resource_id"] == "400"
    assert recycle["items"][0]["expires_time"] == "6 days"
    assert list_session.calls[0][1].endswith("/recycle")

    item = list_api._normalize_cloud_disk_item(raw_recycle, 1)
    restore_session = ResourceSession(
        [
            ResourceResponse(
                {
                    "result": True,
                    "data": [{"resid": "400", "code": -2, "success": False}],
                }
            ),
            ResourceResponse({"result": True}),
        ]
    )
    restore_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        restore_api, "_cloud_disk_context", lambda *args: cloud_context(restore_session)
    )
    restore_lists = iter([[item], []])
    monkeypatch.setattr(
        restore_api,
        "_all_cloud_disk_recycle_items",
        lambda *args, **kwargs: next(restore_lists),
    )
    monkeypatch.setattr(
        restore_api, "_cloud_disk_listing", lambda *args, **kwargs: {"items": [item]}
    )
    restored = restore_api.restore_cloud_disk_recycle_items(["400"], conflict_policy="keep_both")
    assert restored["conflict_count"] == 1
    assert restore_session.calls[1][2]["data"] == {"resids": "400", "t": "1"}

    delete_session = ResourceSession([ResourceResponse({"success": True})])
    delete_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        delete_api, "_cloud_disk_context", lambda *args: cloud_context(delete_session)
    )
    delete_lists = iter([[item], []])
    monkeypatch.setattr(
        delete_api,
        "_all_cloud_disk_recycle_items",
        lambda *args, **kwargs: next(delete_lists),
    )
    deleted = delete_api.permanently_delete_cloud_disk_recycle_items(["400"])
    assert deleted["count"] == 1
    assert delete_session.calls[0][1].endswith("/recycle/delres")

    empty_session = ResourceSession([ResourceResponse({"success": True})])
    empty_api = ChaoxingAPI(Path("unused-cookies.json"))
    monkeypatch.setattr(
        empty_api, "_cloud_disk_context", lambda *args: cloud_context(empty_session)
    )
    empty_lists = iter(
        [
            {"total_count": 3, "items": []},
            {"total_count": 0, "items": []},
        ]
    )
    monkeypatch.setattr(
        empty_api, "_cloud_disk_recycle_listing", lambda *args, **kwargs: next(empty_lists)
    )
    emptied = empty_api.empty_cloud_disk_recycle()
    assert emptied["previous_count"] == 3
    assert empty_session.calls[0][1].endswith("/recycle/empty")
