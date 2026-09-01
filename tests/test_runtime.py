from pathlib import Path

import pytest

from chaoxing_agent.api import ChaoxingLoginVerificationRequired
from chaoxing_agent.config import Settings
from chaoxing_agent.runtime import ActionRuntime, ActionRuntimeError


class LoginAPI:
    def __init__(self) -> None:
        self.parameters: tuple[str, str, str] | None = None

    def login(self, username: str, password: str, *, fid: str) -> dict[str, object]:
        self.parameters = (username, password, fid)
        return {"logged_in": True, "cookies_saved": 2}


@pytest.mark.asyncio
async def test_runtime_dispatches_http_login_without_echoing_parameters(monkeypatch) -> None:
    runtime = ActionRuntime(Settings(cookie_file=Path("session.json"), request_timeout=20.0))
    api = LoginAPI()
    monkeypatch.setattr(runtime, "_api", lambda: api)

    result = await runtime.execute(
        "session.login",
        {"username": "account", "password": "private-password", "fid": "23080"},
    )

    assert api.parameters == ("account", "private-password", "23080")
    assert result["result"] == {"logged_in": True, "cookies_saved": 2}
    assert "private-password" not in str(result)


@pytest.mark.asyncio
async def test_runtime_exposes_observable_postconditions_for_reads_and_confirmed_writes(
    tmp_path, monkeypatch
) -> None:
    runtime = ActionRuntime(
        Settings(
            cookie_file=tmp_path / "session.json",
            request_timeout=20.0,
            confirmation_file=tmp_path / "confirmations.json",
        )
    )

    async def dispatch(action, _parameters):
        if action == "courses.list_teaching":
            return {"courses": [{"course_name": "英语写作"}]}
        assert action == "homework.score.set"
        return {"score": 85, "verification": "fresh submission read showed score 85"}

    monkeypatch.setattr(runtime, "_dispatch", dispatch)

    read_result = await runtime.execute("courses.list_teaching")
    parameters = {
        "course": "英语写作",
        "homework": "第二次作业",
        "submission": "张三",
        "score": 85,
    }
    preview = await runtime.execute("homework.score.set", parameters)
    write_result = await runtime.execute(
        "homework.score.set",
        parameters,
        preview["confirmation"]["token"],
    )

    assert read_result["postcondition"] == {
        "observed": True,
        "kind": "read_result_returned",
        "summary": "当前读取动作返回了结构化结果。",
    }
    assert write_result["postcondition"] == {
        "observed": True,
        "kind": "runtime_verification",
        "summary": "fresh submission read showed score 85",
    }
    assert (
        ActionRuntime._observable_postcondition("publish", {"accepted": True})["observed"] is False
    )


@pytest.mark.asyncio
async def test_runtime_returns_structured_login_verification_state(monkeypatch) -> None:
    class VerificationAPI:
        @staticmethod
        def login(username: str, password: str, *, fid: str):
            raise ChaoxingLoginVerificationRequired(
                "two_factor",
                "学习通要求完成二次验证。",
                "https://passport2.chaoxing.com/twofactor/check?id=1",
            )

    runtime = ActionRuntime(Settings(cookie_file=Path("session.json"), request_timeout=20.0))
    monkeypatch.setattr(runtime, "_api", VerificationAPI)

    result = await runtime.execute(
        "session.login",
        {"username": "account", "password": "private-password", "fid": "-1"},
    )

    assert result["status"] == "verification_required"
    assert result["verification"]["kind"] == "two_factor"
    assert result["verification"]["retry"] == "login"
    assert "private-password" not in str(result)


@pytest.mark.asyncio
async def test_runtime_dispatches_cross_application_login_target(monkeypatch) -> None:
    class TargetLoginAPI:
        def __init__(self) -> None:
            self.parameters: tuple[str, str, str, str] | None = None

        def login(
            self,
            username: str,
            password: str,
            *,
            fid: str,
            target_url: str,
        ) -> dict[str, object]:
            self.parameters = (username, password, fid, target_url)
            return {
                "logged_in": True,
                "target": {"target_reached": True},
                "cookies_saved": 2,
            }

    runtime = ActionRuntime(Settings(cookie_file=Path("session.json"), request_timeout=20.0))
    api = TargetLoginAPI()
    monkeypatch.setattr(runtime, "_api", lambda: api)
    target_url = "https://xueyinonline.chaoxing.com/livecoursenew?stuenc=secret-value"

    result = await runtime.execute(
        "session.login",
        {
            "username": "account",
            "password": "private-password",
            "fid": "23080",
            "target_url": target_url,
        },
    )

    assert api.parameters == ("account", "private-password", "23080", target_url)
    assert result["result"]["target"]["target_reached"] is True
    assert "private-password" not in str(result)


@pytest.mark.asyncio
async def test_runtime_resolves_learning_module_login_target_without_exposing_url(
    monkeypatch,
) -> None:
    class LearningTargetLoginAPI:
        def __init__(self) -> None:
            self.target_url = ""

        @staticmethod
        def resolve_learning_course_module_login_target(course: str, module: str):
            assert course == "测试课程"
            assert module == "直播课/见面课"
            return (
                {
                    "course_id": "265813684",
                    "course_name": "测试课程",
                    "clazz_id": "123456789",
                },
                {"module": "zb_jm", "label": "直播课/见面课"},
                "https://xueyinonline.chaoxing.com/livecoursenew?stuenc=secret-value",
            )

        def login(self, _username: str, _password: str, **kwargs):
            self.target_url = kwargs["target_url"]
            return {
                "logged_in": True,
                "target": {"target_reached": True},
                "cookies_saved": 2,
            }

    runtime = ActionRuntime(Settings(cookie_file=Path("session.json"), request_timeout=20.0))
    api = LearningTargetLoginAPI()
    monkeypatch.setattr(runtime, "_api", lambda: api)

    result = await runtime.execute(
        "session.login",
        {
            "username": "account",
            "password": "private-password",
            "learning_course": "测试课程",
            "learning_module": "直播课/见面课",
        },
    )

    assert "stuenc=secret-value" in api.target_url
    assert result["result"]["target_context"] == {
        "course_id": "265813684",
        "course_name": "测试课程",
        "clazz_id": "123456789",
        "module": "zb_jm",
        "module_label": "直播课/见面课",
    }
    assert "secret-value" not in str(result)


@pytest.mark.asyncio
async def test_runtime_rejects_raw_and_semantic_login_targets_together(monkeypatch) -> None:
    runtime = ActionRuntime(Settings(cookie_file=Path("session.json"), request_timeout=20.0))
    monkeypatch.setattr(runtime, "_api", LoginAPI)

    with pytest.raises(ActionRuntimeError, match="cannot be used together"):
        await runtime.execute(
            "session.login",
            {
                "username": "account",
                "password": "private-password",
                "target_url": "https://xueyinonline.chaoxing.com/livecoursenew",
                "learning_course": "测试课程",
            },
        )


@pytest.mark.asyncio
async def test_runtime_dispatches_learning_reads_and_confirms_integrity(monkeypatch) -> None:
    class LearningAPI:
        def __init__(self) -> None:
            self.accepted = False

        @staticmethod
        def list_learning_courses(**kwargs):
            return [{"course_id": "254641935", "course_name": "英语文体与写作", **kwargs}]

        @staticmethod
        def get_learning_course(course):
            return {
                "course_id": "254641935",
                "course_name": course,
                "clazz_id": "125867890",
            }

        @staticmethod
        def discover_learning_course_modules(course):
            return {"course": course, "modules": [{"label": "章节"}]}

        @staticmethod
        def inspect_learning_course_module(course, module):
            return {"course": course, "module": module, "title": "章节学习"}

        @staticmethod
        def list_learning_activities(course, **kwargs):
            return {"course": course, "activities": [], **kwargs}

        @staticmethod
        def list_learning_chapters(course, **kwargs):
            return {"course": course, "chapters": [{"title": "第一章"}], **kwargs}

        @staticmethod
        def list_learning_discussions(course, **kwargs):
            return {"course": course, "topics": [], **kwargs}

        @staticmethod
        def read_learning_discussion_topic(course, topic, **kwargs):
            return {"course": course, "topic": {"title": topic}, **kwargs}

        @staticmethod
        def create_learning_discussion_topic(course, title, content, **kwargs):
            return {"course": course, "topic": {"title": title, "content": content}, **kwargs}

        @staticmethod
        def update_learning_discussion_topic(course, topic, **kwargs):
            return {"course": course, "topic": {"title": topic}, **kwargs}

        @staticmethod
        def delete_learning_discussion_topic(course, topic):
            return {"course": course, "deleted_topic": {"title": topic}}

        @staticmethod
        def create_learning_discussion_reply(course, topic, content, **kwargs):
            return {"course": course, "topic": topic, "reply": {"content": content}, **kwargs}

        @staticmethod
        def update_learning_discussion_reply(course, topic, reply, content):
            return {
                "course": course,
                "topic": topic,
                "reply": {"before": reply, "content": content},
            }

        @staticmethod
        def delete_learning_discussion_reply(course, topic, reply):
            return {"course": course, "topic": topic, "deleted_reply": {"content": reply}}

        @staticmethod
        def list_learning_homeworks(course, **kwargs):
            return {"course": course, "homeworks": [], **kwargs}

        @staticmethod
        def read_learning_homework(course, homework):
            return {
                "course": course,
                "homework": {"title": homework},
                "questions": [{"stem": "说明课堂导入。"}],
            }

        @staticmethod
        def enter_learning_homework_answer(course, homework):
            return {
                "course": course,
                "homework": {"title": homework},
                "form": {"answer_form_detected": True},
            }

        @staticmethod
        def save_learning_homework_answers(course, homework, updates):
            return {
                "course": course,
                "homework": {"title": homework},
                "updated_questions": updates,
                "postcondition": {"submitted": False},
            }

        @staticmethod
        def submit_learning_homework(course, homework):
            return {
                "course": course,
                "homework": {"title": homework},
                "postcondition": {"submitted": True},
            }

        @staticmethod
        def redo_learning_homework(course, homework):
            return {
                "course": course,
                "homework": {"title": homework},
                "answer": {"form": {"answer_form_detected": True}},
            }

        @staticmethod
        def list_learning_homework_attempts(course, homework):
            return {
                "course": course,
                "homework": {"title": homework},
                "attempts": [{"attempt_id": "1"}],
            }

        @staticmethod
        def read_learning_homework_attempt(course, homework, attempt):
            return {
                "course": course,
                "homework": {"title": homework},
                "attempt": {"attempt_id": attempt},
            }

        @staticmethod
        def list_learning_exams(course, **kwargs):
            return {"course": course, "exams": [], **kwargs}

        @staticmethod
        def list_learning_self_tests(course, **kwargs):
            return {"course": course, "self_tests": [], **kwargs}

        @staticmethod
        def list_learning_materials(course, **kwargs):
            return {"course": course, "items": [], **kwargs}

        @staticmethod
        def list_learning_ai_tools(course):
            return {"course": course, "tools": [{"name": "写作AI助教"}]}

        @staticmethod
        def read_learning_wrong_questions(course):
            return {"course": course, "summary": {"group_count": 0}}

        @staticmethod
        def read_learning_records(course):
            return {"course": course, "records": {"points": 0}}

        @staticmethod
        def list_learning_knowledge_graph(course, **kwargs):
            return {"course": course, "nodes": [{"name": "写作"}], **kwargs}

        @staticmethod
        def read_learning_knowledge_graph_node(course, node):
            return {"course": course, "node": {"name": node}}

        @staticmethod
        def list_learning_knowledge_graph_models(course, **kwargs):
            return {"course": course, "models": [{"name": "知识图谱"}], **kwargs}

        @staticmethod
        def read_learning_knowledge_graph_model(course, model):
            return {"course": course, "model": {"name": model}}

        @staticmethod
        def read_learning_integrity(course):
            return {"course": course, "commitment": {"required": True}}

        def accept_learning_integrity(self, course):
            self.accepted = True
            return {"course": course, "changed": True}

    runtime = ActionRuntime(Settings(cookie_file=Path("session.json"), request_timeout=20.0))
    api = LearningAPI()
    monkeypatch.setattr(runtime, "_api", lambda: api)

    listing = await runtime.execute("learning.courses.list", {"search": "英语"})
    modules = await runtime.execute(
        "learning.course.modules.discover", {"course": "英语文体与写作"}
    )
    opened = await runtime.execute(
        "learning.course.module.open",
        {"course": "英语文体与写作", "module": "章节"},
    )
    activities = await runtime.execute(
        "learning.course.activities.list",
        {"course": "英语文体与写作", "search": "讨论", "status": "ended"},
    )
    chapters = await runtime.execute(
        "learning.course.chapters.list", {"course": "英语文体与写作", "search": "第一"}
    )
    discussions = await runtime.execute(
        "learning.course.discussions.list",
        {"course": "英语文体与写作", "class_only": True},
    )
    discussion = await runtime.execute(
        "learning.course.discussions.topic.read",
        {
            "course": "英语文体与写作",
            "topic": "环境问题",
            "order": "1",
            "reply_search": "pollution",
        },
    )
    mutation_parameters = {
        "learning.course.discussions.topic.create": {
            "course": "英语文体与写作",
            "title": "环境问题",
            "content": "正文",
        },
        "learning.course.discussions.topic.update": {
            "course": "英语文体与写作",
            "topic": "环境问题",
            "content": "新正文",
        },
        "learning.course.discussions.topic.delete": {
            "course": "英语文体与写作",
            "topic": "环境问题",
        },
        "learning.course.discussions.reply.create": {
            "course": "英语文体与写作",
            "topic": "环境问题",
            "content": "回复",
        },
        "learning.course.discussions.reply.update": {
            "course": "英语文体与写作",
            "topic": "环境问题",
            "reply": "回复",
            "content": "新回复",
        },
        "learning.course.discussions.reply.delete": {
            "course": "英语文体与写作",
            "topic": "环境问题",
            "reply": "回复",
        },
    }
    discussion_mutations = {}
    for action, parameters in mutation_parameters.items():
        mutation_preview = await runtime.execute(action, parameters)
        assert mutation_preview["status"] == "confirmation_required"
        discussion_mutations[action] = await runtime.execute(
            action,
            parameters,
            mutation_preview["confirmation"]["token"],
        )
    homeworks = await runtime.execute(
        "learning.course.homeworks.list", {"course": "英语文体与写作"}
    )
    homework = await runtime.execute(
        "learning.course.homework.read",
        {"course": "英语文体与写作", "homework": "BOPPPS 设计"},
    )
    homework_answer = await runtime.execute(
        "learning.course.homework.answer.enter",
        {"course": "英语文体与写作", "homework": "BOPPPS 设计"},
    )
    homework_saved = await runtime.execute(
        "learning.course.homework.answers.save",
        {
            "course": "英语文体与写作",
            "homework": "BOPPPS 设计",
            "updates": [{"question": "1", "answer": "真实问题"}],
        },
    )
    submit_preview = await runtime.execute(
        "learning.course.homework.submit",
        {"course": "英语文体与写作", "homework": "BOPPPS 设计"},
    )
    submit_confirmed = await runtime.execute(
        "learning.course.homework.submit",
        {"course": "英语文体与写作", "homework": "BOPPPS 设计"},
        submit_preview["confirmation"]["token"],
    )
    redo_preview = await runtime.execute(
        "learning.course.homework.redo",
        {"course": "英语文体与写作", "homework": "BOPPPS 设计"},
    )
    redo_confirmed = await runtime.execute(
        "learning.course.homework.redo",
        {"course": "英语文体与写作", "homework": "BOPPPS 设计"},
        redo_preview["confirmation"]["token"],
    )
    homework_attempts = await runtime.execute(
        "learning.course.homework.attempts.list",
        {"course": "英语文体与写作", "homework": "BOPPPS 设计"},
    )
    homework_attempt = await runtime.execute(
        "learning.course.homework.attempt.read",
        {"course": "英语文体与写作", "homework": "BOPPPS 设计", "attempt": "1"},
    )
    exams = await runtime.execute("learning.course.exams.list", {"course": "英语文体与写作"})
    self_tests = await runtime.execute(
        "learning.course.self_tests.list", {"course": "英语文体与写作"}
    )
    materials = await runtime.execute(
        "learning.course.materials.list",
        {"course": "英语文体与写作", "folder": "Week 1"},
    )
    ai_tools = await runtime.execute("learning.course.ai_tools.list", {"course": "英语文体与写作"})
    wrong = await runtime.execute(
        "learning.course.wrong_questions.summary", {"course": "英语文体与写作"}
    )
    records = await runtime.execute("learning.course.records.read", {"course": "英语文体与写作"})
    graph = await runtime.execute(
        "learning.course.knowledge_graph.list",
        {"course": "英语文体与写作", "search": "写作", "level": "2"},
    )
    graph_node = await runtime.execute(
        "learning.course.knowledge_graph.node.read",
        {"course": "英语文体与写作", "node": "Punctuation"},
    )
    graph_models = await runtime.execute(
        "learning.course.knowledge_graph.models.list",
        {"course": "英语文体与写作", "search": "知识"},
    )
    graph_model = await runtime.execute(
        "learning.course.knowledge_graph.model.read",
        {"course": "英语文体与写作", "model": "知识图谱"},
    )
    integrity = await runtime.execute(
        "learning.course.integrity.read", {"course": "英语文体与写作"}
    )
    preview = await runtime.execute(
        "learning.course.integrity.accept", {"course": "英语文体与写作"}
    )
    confirmed = await runtime.execute(
        "learning.course.integrity.accept",
        {"course": "英语文体与写作"},
        preview["confirmation"]["token"],
    )

    assert listing["result"]["count"] == 1
    assert modules["result"]["modules"][0]["label"] == "章节"
    assert opened["result"]["title"] == "章节学习"
    assert activities["result"]["status"] == "ended"
    assert chapters["result"]["chapters"][0]["title"] == "第一章"
    assert discussions["result"]["class_only"] is True
    assert discussion["result"]["topic"]["title"] == "环境问题"
    assert discussion["result"]["order"] == 1
    assert discussion["result"]["reply_search"] == "pollution"
    assert all(result["status"] == "ok" for result in discussion_mutations.values())
    assert (
        discussion_mutations["learning.course.discussions.topic.create"]["result"]["topic"][
            "content"
        ]
        == "正文"
    )
    assert (
        discussion_mutations["learning.course.discussions.reply.update"]["result"]["reply"][
            "content"
        ]
        == "新回复"
    )
    assert homeworks["result"]["homeworks"] == []
    assert homework["result"]["homework"]["title"] == "BOPPPS 设计"
    assert homework_answer["result"]["form"]["answer_form_detected"] is True
    assert homework_saved["result"]["postcondition"]["submitted"] is False
    assert homework_saved["result"]["updated_questions"][0]["question"] == "1"
    assert submit_preview["status"] == "confirmation_required"
    assert "已交" in submit_preview["confirmation"]["summary"]
    assert submit_confirmed["result"]["postcondition"]["submitted"] is True
    assert redo_preview["status"] == "confirmation_required"
    assert "覆盖" in redo_preview["confirmation"]["summary"]
    assert redo_confirmed["result"]["answer"]["form"]["answer_form_detected"] is True
    assert homework_attempts["result"]["attempts"][0]["attempt_id"] == "1"
    assert homework_attempt["result"]["attempt"]["attempt_id"] == "1"
    assert exams["result"]["exams"] == []
    assert self_tests["result"]["self_tests"] == []
    assert materials["result"]["folder"] == "Week 1"
    assert ai_tools["result"]["tools"][0]["name"] == "写作AI助教"
    assert wrong["result"]["summary"]["group_count"] == 0
    assert records["result"]["records"]["points"] == 0
    assert graph["result"]["level"] == 2 and graph["result"]["search"] == "写作"
    assert graph_node["result"]["node"]["name"] == "Punctuation"
    assert graph_models["result"]["models"][0]["name"] == "知识图谱"
    assert graph_model["result"]["model"]["name"] == "知识图谱"
    assert integrity["result"]["commitment"]["required"] is True
    assert preview["status"] == "confirmation_required"
    assert "签署" in preview["confirmation"]["summary"]
    assert confirmed["status"] == "ok" and api.accepted is True


@pytest.mark.asyncio
async def test_runtime_dispatches_job_ability_search_catalog_and_industry(monkeypatch) -> None:
    class JobAbilityAPI:
        @staticmethod
        def search_job_ability_jobs(keyword, **kwargs):
            return {"keyword": keyword, **kwargs}

        @staticmethod
        def read_job_ability_occupation_catalog(**kwargs):
            return {"counts": {"level_1": 1}, **kwargs}

        @staticmethod
        def list_job_ability_industry_jobs(industry, **kwargs):
            return {"industry": industry, **kwargs}

    runtime = ActionRuntime(Settings(cookie_file=Path("session.json"), request_timeout=20.0))
    monkeypatch.setattr(runtime, "_api", lambda: JobAbilityAPI())

    search = await runtime.execute(
        "job_ability.jobs.search",
        {
            "keyword": "英语教师",
            "page": "2",
            "page_size": "30",
            "education_level": "本科",
        },
    )
    catalog = await runtime.execute(
        "job_ability.occupation_catalog.read", {"education_level": "硕士"}
    )
    industry = await runtime.execute(
        "job_ability.industry_jobs.list",
        {"industry": "教学人员", "page": "3", "page_size": "40"},
    )

    assert search["result"] == {
        "keyword": "英语教师",
        "page": 2,
        "page_size": 30,
        "education_level": "本科",
    }
    assert catalog["result"]["education_level"] == "硕士"
    assert industry["result"]["industry"] == "教学人员"
    assert industry["result"]["page"] == 3 and industry["result"]["page_size"] == 40


@pytest.mark.asyncio
async def test_runtime_dispatches_live_reads_and_confirmed_settings(monkeypatch) -> None:
    class LiveAPI:
        def __init__(self) -> None:
            self.settings: dict[str, object] | None = None

        @staticmethod
        def list_live_rooms(**kwargs):
            return {"rooms": [], **kwargs}

        def update_live_room_settings(self, room, **kwargs):
            self.settings = {"room": room, **kwargs}
            return self.settings

    runtime = ActionRuntime(Settings(cookie_file=Path("session.json"), request_timeout=20.0))
    api = LiveAPI()
    monkeypatch.setattr(runtime, "_api", lambda: api)

    listing = await runtime.execute(
        "live.rooms.list", {"search": "课程", "sort_key": "2", "max_items": "20"}
    )
    preview = await runtime.execute(
        "live.room.settings.update",
        {
            "room": "公开课",
            "replay_enabled": "true",
            "allowed_unit_ids": ["23080"],
            "replay_start_offset_seconds": "5",
        },
    )
    confirmed = await runtime.execute(
        "live.room.settings.update",
        {
            "room": "公开课",
            "replay_enabled": "true",
            "allowed_unit_ids": ["23080"],
            "replay_start_offset_seconds": "5",
        },
        preview["confirmation"]["token"],
    )

    assert listing["result"]["sort_key"] == 2 and listing["result"]["max_items"] == 20
    assert preview["status"] == "confirmation_required"
    assert confirmed["status"] == "ok"
    assert api.settings is not None
    assert api.settings["room"] == "公开课"
    assert api.settings["replay_enabled"] is True
    assert api.settings["allowed_unit_ids"] == ["23080"]
    assert api.settings["replay_start_offset_seconds"] == 5


@pytest.mark.asyncio
async def test_detection_download_rejects_non_numeric_timeout_before_http(monkeypatch) -> None:
    runtime = ActionRuntime(Settings(cookie_file=Path("session.json"), request_timeout=20.0))
    monkeypatch.setattr(runtime, "_api", lambda: pytest.fail("HTTP API must not be constructed"))

    with pytest.raises(ActionRuntimeError, match="timeout_seconds must be a finite number"):
        await runtime.execute(
            "detection.report.download",
            {
                "type": "aigc",
                "record": "record-1",
                "output_path": "report.pdf",
                "timeout_seconds": "not-a-number",
            },
        )


@pytest.mark.asyncio
async def test_runtime_dispatches_ai_workbench_reads_and_confirmed_creation(monkeypatch) -> None:
    class AIWorkbenchAPI:
        def __init__(self) -> None:
            self.created: dict[str, object] | None = None

        @staticmethod
        def get_course(_query):
            return {
                "course_id": "900000002",
                "course_name": "文体写作示例",
                "classes": [{"clazz_id": "800000002", "clazz_name": "示例一班"}],
            }

        @staticmethod
        def list_ai_workbench_groups(_course, _clazz):
            return {"count": 1, "groups": [{"group_id": "0", "name": "系统指令"}]}

        def create_ai_workbench_command(
            self, course, clazz, group, name, content, explanation, **kwargs
        ):
            self.created = {
                "course": course["course_id"],
                "clazz": clazz["clazz_id"],
                "group": group,
                "name": name,
                "content": content,
                "explanation": explanation,
                **kwargs,
            }
            return {"command": {"command_id": "99", "name": name}}

    runtime = ActionRuntime(Settings(cookie_file=Path("session.json"), request_timeout=20.0))
    api = AIWorkbenchAPI()
    monkeypatch.setattr(runtime, "_api", lambda: api)

    listing = await runtime.execute(
        "ai_workbench.groups.list", {"course": "900000002", "clazz": "800000002"}
    )
    preview = await runtime.execute(
        "ai_workbench.command.create",
        {
            "course": "900000002",
            "clazz": "800000002",
            "group": "备课",
            "name": "生成提纲",
            "content": "主题为：{请输入主题}",
            "explanation": "生成结构清楚的提纲",
            "role_type": "2",
        },
    )
    confirmed = await runtime.execute(
        "ai_workbench.command.create",
        {
            "course": "900000002",
            "clazz": "800000002",
            "group": "备课",
            "name": "生成提纲",
            "content": "主题为：{请输入主题}",
            "explanation": "生成结构清楚的提纲",
            "role_type": "2",
        },
        preview["confirmation"]["token"],
    )

    assert listing["result"]["groups"][0]["group_id"] == "0"
    assert preview["status"] == "confirmation_required"
    assert confirmed["status"] == "ok"
    assert api.created is not None
    assert api.created["role_type"] == 2


@pytest.mark.asyncio
async def test_runtime_dispatches_knowledge_hub_reads_writes_and_confirmed_share(
    monkeypatch,
) -> None:
    class KnowledgeHubAPI:
        def __init__(self) -> None:
            self.availability: tuple[str, bool] | None = None
            self.share: tuple[str, bool] | None = None

        @staticmethod
        def get_course(_query):
            return {
                "course_id": "900000001",
                "course_name": "语言与测试",
                "classes": [{"clazz_id": "800000001", "clazz_name": "默认班级"}],
            }

        @staticmethod
        def read_knowledge_hub_status(_course, _clazz):
            return {"modules": [{"module": "NORMAL_BASE", "enabled": True}]}

        def set_knowledge_hub_base_availability(self, _course, _clazz, base, enabled):
            self.availability = (base, enabled)
            return {"base": {"base_id": "1", "enabled": enabled}}

        def set_knowledge_hub_base_share(self, _course, _clazz, base, shared):
            self.share = (base, shared)
            return {"base": {"base_id": "1", "shared": shared}}

    runtime = ActionRuntime(Settings(cookie_file=Path("session.json"), request_timeout=20.0))
    api = KnowledgeHubAPI()
    monkeypatch.setattr(runtime, "_api", lambda: api)
    parameters = {
        "course": "900000001",
        "clazz": "800000001",
        "base": "默认知识库",
    }

    status = await runtime.execute(
        "knowledge_hub.status.read",
        {"course": "900000001", "clazz": "800000001"},
    )
    availability = await runtime.execute(
        "knowledge_hub.base.availability.update",
        {**parameters, "enabled": "false"},
    )
    preview = await runtime.execute(
        "knowledge_hub.base.share.update",
        {**parameters, "shared": True},
    )
    confirmed = await runtime.execute(
        "knowledge_hub.base.share.update",
        {**parameters, "shared": True},
        preview["confirmation"]["token"],
    )

    assert status["result"]["modules"][0]["module"] == "NORMAL_BASE"
    assert availability["status"] == "ok" and api.availability == ("默认知识库", False)
    assert preview["status"] == "confirmation_required"
    assert confirmed["status"] == "ok" and api.share == ("默认知识库", True)


@pytest.mark.asyncio
async def test_runtime_dispatches_task_engine_reads_creation_and_confirmed_publish(
    monkeypatch,
) -> None:
    class TaskEngineAPI:
        def __init__(self) -> None:
            self.created: dict[str, object] | None = None
            self.published: dict[str, object] | None = None

        @staticmethod
        def get_course(_query):
            return {
                "course_id": "900000002",
                "course_name": "文体写作示例",
                "classes": [{"clazz_id": "800000002", "clazz_name": "示例一班"}],
            }

        @staticmethod
        def list_task_engine_tasks(_course, _clazz, **kwargs):
            return {"count": 1, "tasks": [{"task_id": "task-1"}], **kwargs}

        def create_task_engine_task(self, course, clazz, name, **kwargs):
            self.created = {
                "course": course["course_id"],
                "clazz": clazz["clazz_id"],
                "name": name,
                **kwargs,
            }
            return {"task": {"task_id": "task-2", "name": name}}

        def set_task_engine_publish_status(self, course, clazz, task, **kwargs):
            self.published = {
                "course": course["course_id"],
                "clazz": clazz["clazz_id"],
                "task": task,
                **kwargs,
            }
            return {"task_id": task, "published": kwargs["publish"]}

    runtime = ActionRuntime(Settings(cookie_file=Path("session.json"), request_timeout=20.0))
    api = TaskEngineAPI()
    monkeypatch.setattr(runtime, "_api", lambda: api)

    listing = await runtime.execute(
        "task_engine.tasks.list",
        {
            "course": "900000002",
            "clazz": "800000002",
            "recycled": "true",
            "max_items": "50",
        },
    )
    created = await runtime.execute(
        "task_engine.task.create",
        {
            "course": "900000002",
            "clazz": "800000002",
            "name": "过程分析",
            "selected_modes": ["list", "frame"],
        },
    )
    parameters = {
        "course": "900000002",
        "clazz": "800000002",
        "task": "task-1",
        "published": True,
        "course_publish_param": [{"courseId": "900000002"}],
        "task_publish_param": [{"clazzId": "800000002"}],
    }
    preview = await runtime.execute("task_engine.publish_status.update", parameters)
    confirmed = await runtime.execute(
        "task_engine.publish_status.update",
        parameters,
        preview["confirmation"]["token"],
    )

    assert listing["result"]["recycled"] is True and listing["result"]["max_items"] == 50
    assert created["status"] == "ok"
    assert api.created is not None and api.created["selected_modes"] == ["list", "frame"]
    assert preview["status"] == "confirmation_required"
    assert confirmed["status"] == "ok"
    assert api.published is not None
    assert api.published["publish"] is True
    assert api.published["course_publish_param"] == [{"courseId": "900000002"}]


@pytest.mark.asyncio
async def test_runtime_dispatches_knowledge_graph_filters_and_confirmed_delete(
    monkeypatch,
) -> None:
    class KnowledgeGraphAPI:
        def __init__(self) -> None:
            self.listed: dict[str, object] | None = None
            self.relation_created: dict[str, object] | None = None
            self.settings_updated: dict[str, object] | None = None
            self.advanced_settings_updated: dict[str, object] | None = None
            self.model_visibility: dict[str, object] | None = None
            self.model_classes: dict[str, object] | None = None
            self.event_created: dict[str, object] | None = None
            self.exported: dict[str, object] | None = None
            self.deleted: dict[str, object] | None = None

        @staticmethod
        def get_course(_query):
            return {
                "course_id": "900000002",
                "course_name": "文体写作示例",
                "cpi": "485781386",
                "classes": [{"clazz_id": "800000002", "clazz_name": "示例一班"}],
            }

        def list_knowledge_graph(self, course, clazz, **kwargs):
            self.listed = {
                "course": course["course_id"],
                "clazz": clazz["clazz_id"],
                **kwargs,
            }
            return {"count": 1, **kwargs}

        def create_knowledge_graph_relation_type(self, course, clazz, name, **kwargs):
            self.relation_created = {
                "course": course["course_id"],
                "clazz": clazz["clazz_id"],
                "name": name,
                **kwargs,
            }
            return {"relation": {"relation_id": "88", "name": name}}

        def update_knowledge_graph_settings(self, course, clazz, **kwargs):
            self.settings_updated = {
                "course": course["course_id"],
                "clazz": clazz["clazz_id"],
                **kwargs,
            }
            return {"settings": kwargs}

        def update_knowledge_graph_advanced_settings(self, course, clazz, **kwargs):
            self.advanced_settings_updated = {
                "course": course["course_id"],
                "clazz": clazz["clazz_id"],
                **kwargs,
            }
            return {"settings": kwargs}

        def set_knowledge_graph_model_visibility(self, course, clazz, model, **kwargs):
            self.model_visibility = {
                "course": course["course_id"],
                "clazz": clazz["clazz_id"],
                "model": model,
                **kwargs,
            }
            return {"model": {"model_id": model, "visible": kwargs["visible"]}}

        def update_knowledge_graph_model_classes(self, course, clazz, model, visible_classes):
            self.model_classes = {
                "course": course["course_id"],
                "clazz": clazz["clazz_id"],
                "model": model,
                "visible_classes": visible_classes,
            }
            return {"classes": visible_classes}

        def create_knowledge_graph_event(self, course, clazz, name, **kwargs):
            self.event_created = {
                "course": course["course_id"],
                "clazz": clazz["clazz_id"],
                "name": name,
                **kwargs,
            }
            return {"event": {"event_id": "677", "name": name}}

        def download_knowledge_graph_export(
            self, course, clazz, export_format, output_path, **kwargs
        ):
            self.exported = {
                "course": course["course_id"],
                "clazz": clazz["clazz_id"],
                "format": export_format,
                "output_path": output_path,
                **kwargs,
            }
            return {"format": export_format, "output_path": output_path}

        def delete_knowledge_graph_node(self, course, clazz, node):
            self.deleted = {
                "course": course["course_id"],
                "clazz": clazz["clazz_id"],
                "node": node,
            }
            return {"deleted_node": {"node_id": node}}

    runtime = ActionRuntime(Settings(cookie_file=Path("session.json"), request_timeout=20.0))
    api = KnowledgeGraphAPI()
    monkeypatch.setattr(runtime, "_api", lambda: api)

    listing = await runtime.execute(
        "knowledge_graph.graph.read",
        {
            "course": "900000002",
            "clazz": "800000002",
            "search": "概念",
            "level": "2",
        },
    )
    relation = await runtime.execute(
        "knowledge_graph.relation_type.create",
        {
            "course": "900000002",
            "clazz": "800000002",
            "name": "支持关系",
            "relation_types": ["0", "2"],
        },
    )
    settings_parameters = {
        "course": "900000002",
        "clazz": "800000002",
        "show_all_relations": "true",
        "navigation_node_scale": "false",
    }
    settings_preview = await runtime.execute("knowledge_graph.settings.update", settings_parameters)
    settings_result = await runtime.execute(
        "knowledge_graph.settings.update",
        settings_parameters,
        settings_preview["confirmation"]["token"],
    )
    advanced_parameters = {
        "course": "900000002",
        "clazz": "800000002",
        "topic_card": "true",
        "teach_target": "false",
        "selftest_included": "true",
    }
    advanced_preview = await runtime.execute(
        "knowledge_graph.advanced_settings.update", advanced_parameters
    )
    advanced_result = await runtime.execute(
        "knowledge_graph.advanced_settings.update",
        advanced_parameters,
        advanced_preview["confirmation"]["token"],
    )
    visibility_parameters = {
        "course": "900000002",
        "clazz": "800000002",
        "model": "学习地图",
        "visible": "true",
    }
    visibility_preview = await runtime.execute(
        "knowledge_graph.model.visibility.update", visibility_parameters
    )
    visibility_result = await runtime.execute(
        "knowledge_graph.model.visibility.update",
        visibility_parameters,
        visibility_preview["confirmation"]["token"],
    )
    class_parameters = {
        "course": "900000002",
        "clazz": "800000002",
        "model": "知识图谱",
        "visible_classes": ["示例一班"],
    }
    class_preview = await runtime.execute("knowledge_graph.model.classes.update", class_parameters)
    class_result = await runtime.execute(
        "knowledge_graph.model.classes.update",
        class_parameters,
        class_preview["confirmation"]["token"],
    )
    event_parameters = {
        "course": "900000002",
        "clazz": "800000002",
        "name": "完成事件",
        "topic_condition": "completion",
        "set_condition": "greater_than_or_equal",
        "percent1": 80,
        "executions": [{"label": "重点", "execute_module": 0}],
    }
    event_preview = await runtime.execute("knowledge_graph.event.create", event_parameters)
    event_result = await runtime.execute(
        "knowledge_graph.event.create",
        event_parameters,
        event_preview["confirmation"]["token"],
    )
    export_result = await runtime.execute(
        "knowledge_graph.export.download",
        {
            "course": "900000002",
            "clazz": "800000002",
            "format": "rdf",
            "output_path": r"D:\Exports",
            "model": "知识图谱",
            "overwrite": "true",
        },
    )
    parameters = {
        "course": "900000002",
        "clazz": "800000002",
        "node": "240240246",
    }
    preview = await runtime.execute("knowledge_graph.node.delete", parameters)
    confirmed = await runtime.execute(
        "knowledge_graph.node.delete", parameters, preview["confirmation"]["token"]
    )

    assert listing["status"] == "ok"
    assert api.listed is not None and api.listed["level"] == 2
    assert relation["status"] == "ok"
    assert api.relation_created is not None
    assert api.relation_created["relation_types"] == [0, 2]
    assert settings_result["status"] == "ok"
    assert api.settings_updated is not None
    assert api.settings_updated["show_all_relations"] is True
    assert api.settings_updated["navigation_node_scale"] is False
    assert advanced_result["status"] == "ok"
    assert api.advanced_settings_updated is not None
    assert api.advanced_settings_updated["topic_card"] is True
    assert api.advanced_settings_updated["teach_target"] is False
    assert api.advanced_settings_updated["selftest_included"] is True
    assert visibility_result["status"] == "ok"
    assert api.model_visibility is not None and api.model_visibility["visible"] is True
    assert class_result["status"] == "ok"
    assert api.model_classes is not None
    assert api.model_classes["visible_classes"] == ["示例一班"]
    assert event_result["status"] == "ok"
    assert api.event_created is not None
    assert api.event_created["percent1"] == 80
    assert api.event_created["percent2"] == 100
    assert export_result["status"] == "ok"
    assert api.exported is not None
    assert api.exported["format"] == "rdf" and api.exported["overwrite"] is True
    assert preview["status"] == "confirmation_required"
    assert confirmed["status"] == "ok"
    assert api.deleted == {
        "course": "900000002",
        "clazz": "800000002",
        "node": "240240246",
    }


@pytest.mark.asyncio
async def test_runtime_dispatches_generic_graph_nodes_and_confirmed_relations(
    monkeypatch,
) -> None:
    class API:
        def __init__(self) -> None:
            self.created = None
            self.added = None
            self.removed = None

        @staticmethod
        def get_course(_query):
            return {
                "course_id": "900000002",
                "course_name": "文体写作示例",
                "classes": [{"clazz_id": "800000002", "clazz_name": "示例一班"}],
            }

        def create_knowledge_graph_node(self, course, clazz, name, **kwargs):
            self.created = {"name": name, **kwargs}
            return {"node": {"topic_id": "101", "name": name}}

        @staticmethod
        def read_knowledge_graph_node_relations(course, clazz, node):
            return {"node": {"name": node}, "relation_count": 0}

        def add_knowledge_graph_node_relation(
            self, course, clazz, node, relation, target, **kwargs
        ):
            self.added = {
                "node": node,
                "relation": relation,
                "target": target,
                **kwargs,
            }
            return {"changed": True}

        def remove_knowledge_graph_node_relation(self, course, clazz, node, relation, target):
            self.removed = {"node": node, "relation": relation, "target": target}
            return {"changed": True}

    runtime = ActionRuntime(Settings(cookie_file=Path("session.json"), request_timeout=20.0))
    api = API()
    monkeypatch.setattr(runtime, "_api", lambda: api)
    base = {"course": "900000002", "clazz": "800000002"}

    created = await runtime.execute(
        "knowledge_graph.node.create",
        {
            **base,
            "name": "技能点",
            "node_type": "ability",
            "parent": "第一单元",
        },
    )
    reading = await runtime.execute(
        "knowledge_graph.node.relations.read", {**base, "node": "技能点"}
    )
    add_parameters = {
        **base,
        "node": "技能点",
        "relation": "successor",
        "target": "写作",
        "description": "",
    }
    add_preview = await runtime.execute("knowledge_graph.node.relation.add", add_parameters)
    added = await runtime.execute(
        "knowledge_graph.node.relation.add",
        add_parameters,
        add_preview["confirmation"]["token"],
    )
    remove_parameters = {
        **base,
        "node": "技能点",
        "relation": "successor",
        "target": "写作",
    }
    remove_preview = await runtime.execute(
        "knowledge_graph.node.relation.remove", remove_parameters
    )
    removed = await runtime.execute(
        "knowledge_graph.node.relation.remove",
        remove_parameters,
        remove_preview["confirmation"]["token"],
    )

    assert created["status"] == "ok" and api.created["node_type"] == "ability"
    assert reading["result"]["relation_count"] == 0
    assert add_preview["status"] == "confirmation_required" and added["status"] == "ok"
    assert api.added == {
        "node": "技能点",
        "relation": "successor",
        "target": "写作",
        "description": "",
    }
    assert remove_preview["status"] == "confirmation_required"
    assert removed["status"] == "ok" and api.removed["target"] == "写作"


@pytest.mark.asyncio
async def test_runtime_dispatches_class_activity_filters_and_confirmed_start(monkeypatch) -> None:
    class ClassActivityAPI:
        def __init__(self) -> None:
            self.listed: dict[str, object] | None = None
            self.started: dict[str, object] | None = None

        @staticmethod
        def get_course(_query):
            return {
                "course_id": "900000002",
                "course_name": "文体写作示例",
                "classes": [{"clazz_id": "800000002", "clazz_name": "示例一班"}],
            }

        def list_class_activities(self, course, clazz, **kwargs):
            self.listed = {
                "course": course["course_id"],
                "clazz": clazz["clazz_id"],
                **kwargs,
            }
            return {"count": 0, **kwargs}

        def set_class_activity_status(self, course, clazz, activity, **kwargs):
            self.started = {
                "course": course["course_id"],
                "clazz": clazz["clazz_id"],
                "activity": activity,
                **kwargs,
            }
            return {"activity": {"activity_id": activity, "status": 1}}

    runtime = ActionRuntime(Settings(cookie_file=Path("session.json"), request_timeout=20.0))
    api = ClassActivityAPI()
    monkeypatch.setattr(runtime, "_api", lambda: api)

    listing = await runtime.execute(
        "class_activities.activities.list",
        {
            "course": "900000002",
            "clazz": "800000002",
            "status": "ongoing",
            "activity_type": "45",
        },
    )
    parameters = {
        "course": "900000002",
        "clazz": "800000002",
        "activity": "activity-1",
    }
    preview = await runtime.execute("class_activities.activity.start", parameters)
    confirmed = await runtime.execute(
        "class_activities.activity.start",
        parameters,
        preview["confirmation"]["token"],
    )

    assert listing["status"] == "ok"
    assert api.listed is not None and api.listed["activity_type"] == 45
    assert preview["status"] == "confirmation_required"
    assert confirmed["status"] == "ok"
    assert api.started is not None and api.started["started"] is True
