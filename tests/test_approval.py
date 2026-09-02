import pytest

from chaoxing_agent.approval import ConfirmationError, ConfirmationGate
from chaoxing_agent.models import ActionRisk
from chaoxing_agent.runtime import ActionRuntime


def test_purchase_risk_requires_confirmation() -> None:
    assert ActionRisk.PURCHASE.requires_confirmation is True


def test_confirmation_is_bound_to_action_and_parameters() -> None:
    gate = ConfirmationGate()
    challenge = gate.issue("scores.submit", {"class": "1", "score": 90}, "submit score")
    with pytest.raises(ConfirmationError, match="parameters"):
        gate.consume(challenge.token, "scores.submit", {"class": "1", "score": 91})


def test_confirmation_is_single_use() -> None:
    gate = ConfirmationGate()
    params = {"notice": "hello"}
    challenge = gate.issue("notice.publish", params, "publish notice")
    gate.consume(challenge.token, "notice.publish", params)
    with pytest.raises(ConfirmationError, match="already used"):
        gate.consume(challenge.token, "notice.publish", params)


def test_expired_confirmation_is_rejected() -> None:
    gate = ConfirmationGate(ttl_seconds=-1)
    params = {"paper": "1"}
    challenge = gate.issue("exam.publish", params, "publish exam")
    with pytest.raises(ConfirmationError, match="expired"):
        gate.consume(challenge.token, "exam.publish", params)


def test_confirmation_persists_across_process_instances(tmp_path) -> None:
    storage = tmp_path / "confirmations.json"
    params = {"course": "900000002", "resource": "verification.txt"}
    challenge = ConfirmationGate(storage_path=storage).issue(
        "resources.file.upload",
        params,
        "upload verification resource",
    )

    ConfirmationGate(storage_path=storage).consume(
        challenge.token,
        "resources.file.upload",
        params,
    )

    with pytest.raises(ConfirmationError, match="already used"):
        ConfirmationGate(storage_path=storage).consume(
            challenge.token,
            "resources.file.upload",
            params,
        )


@pytest.mark.asyncio
async def test_score_action_stops_before_http_until_confirmed() -> None:
    result = await ActionRuntime().execute(
        "homework.score.set",
        {
            "course": "课程",
            "homework": "作业",
            "submission": "20230001",
            "score": "95",
        },
    )
    assert result["status"] == "confirmation_required"
    assert "提交分数 95" in result["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_contact_mutations_stop_before_http_until_confirmed() -> None:
    runtime = ActionRuntime()
    cases = (
        (
            "contacts.follow_status.update",
            {"person": "张三", "followed": True},
        ),
        (
            "contacts.team.create",
            {"name": "项目组", "members": ["张三"]},
        ),
        (
            "contacts.team.rename",
            {"team": "项目组", "name": "课程组"},
        ),
        (
            "contacts.team.members.add",
            {"team": "课程组", "members": ["李四"]},
        ),
        (
            "contacts.team.member.remove",
            {"team": "课程组", "member": "李四"},
        ),
        ("contacts.team.delete", {"team": "课程组"}),
        ("contacts.team.exit", {"team": "他人团队"}),
    )
    for action, parameters in cases:
        result = await runtime.execute(action, parameters)
        assert result["status"] == "confirmation_required"
        assert result["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_monitor_mutations_stop_before_http_until_confirmed() -> None:
    runtime = ActionRuntime()
    reminder = await runtime.execute(
        "course.study_monitor.remind",
        {
            "course": "课程",
            "student": "20240001",
            "title": "学习异常提醒",
            "content": "请查看考试异常记录。",
        },
    )
    clear = await runtime.execute(
        "course.study_monitor.clear",
        {"course": "课程", "student": "20240001"},
    )
    assert reminder["status"] == "confirmation_required"
    assert "学习异常提醒" in reminder["confirmation"]["summary"]
    assert clear["status"] == "confirmation_required"
    assert "清除" in clear["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_student_restore_stops_before_http_until_confirmed() -> None:
    result = await ActionRuntime().execute(
        "class.student.restore",
        {"course": "课程", "clazz": "班级", "student": "杨子昂"},
    )
    assert result["status"] == "confirmation_required"
    assert "杨子昂" in result["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_student_membership_mutations_stop_before_http_until_confirmed() -> None:
    runtime = ActionRuntime()
    cases = (
        (
            "class.student.add_from_bank",
            {"course": "课程", "clazz": "班级", "student": "2024000273"},
        ),
        (
            "class.student.add_by_identity",
            {
                "course": "课程",
                "clazz": "班级",
                "name": "张三",
                "identity": "2024000001",
                "identity_type": "student_no",
            },
        ),
        (
            "class.student.remove",
            {"course": "课程", "clazz": "班级", "student": "2024000273"},
        ),
        (
            "class.join_application.decide",
            {
                "course": "课程",
                "clazz": "班级",
                "application": "99123",
                "decision": "approve",
            },
        ),
        (
            "class.student.move",
            {
                "course": "课程",
                "clazz": "原班级",
                "target_clazz": "目标班级",
                "student": "2024000273",
            },
        ),
    )
    for action, parameters in cases:
        result = await runtime.execute(action, parameters)
        assert result["status"] == "confirmation_required"
        target = (
            parameters.get("student") or parameters.get("name") or parameters.get("application")
        )
        assert target in result["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_class_mutations_stop_before_http_until_confirmed() -> None:
    runtime = ActionRuntime()
    cases = (
        ("classes.create", {"course": "课程", "name": "新班级"}),
        (
            "class.rename",
            {"course": "课程", "clazz": "原班级", "name": "新班级"},
        ),
        (
            "class.settings.update",
            {"course": "课程", "clazz": "班级", "student_limit": 120},
        ),
        ("class.delete", {"course": "课程", "clazz": "班级"}),
    )
    for action, parameters in cases:
        result = await runtime.execute(action, parameters)
        assert result["status"] == "confirmation_required"


@pytest.mark.asyncio
async def test_teacher_team_mutations_stop_before_http_until_confirmed() -> None:
    runtime = ActionRuntime()
    cases = (
        (
            "course.teacher.add_from_bank",
            {"course": "课程", "teacher": "2014800132", "role": "assistant"},
        ),
        (
            "course.teacher.add_by_identity",
            {
                "course": "课程",
                "name": "李老师",
                "identity": "2001800001",
                "identity_type": "employee_no",
                "role": "teacher",
            },
        ),
        ("course.teacher.remove", {"course": "课程", "teacher": "2001800001"}),
        (
            "course.teacher.permissions.update",
            {
                "course": "课程",
                "teacher": "2001800001",
                "changes": {"homework": True, "examine": False},
            },
        ),
    )
    for action, parameters in cases:
        result = await runtime.execute(action, parameters)
        assert result["status"] == "confirmation_required"


@pytest.mark.asyncio
async def test_grade_mutations_stop_before_http_until_confirmed() -> None:
    runtime = ActionRuntime()
    visibility = await runtime.execute(
        "course.grade_visibility.set",
        {
            "course": "课程",
            "visible_classes": ["英语2401"],
            "students_can_view_rank": True,
        },
    )
    override = await runtime.execute(
        "course.grade_override.set",
        {"course": "课程", "student": "20240001", "score": 85},
    )
    assert visibility["status"] == "confirmation_required"
    assert "英语2401" in visibility["confirmation"]["summary"]
    assert override["status"] == "confirmation_required"
    assert "85" in override["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_homework_draft_deletion_stops_before_http_until_confirmed() -> None:
    runtime = ActionRuntime()
    cases = (
        ("homework.draft.delete", {"course": "课程", "draft": "待删除草稿"}),
        (
            "homework.question.delete",
            {"course": "课程", "homework": "Unit 1", "question": "3"},
        ),
        (
            "homework.library.publish",
            {
                "course": "课程",
                "homework": "Unit 1",
                "target_classes": ["示例一班"],
                "start_time": "now",
            },
        ),
    )
    for action, parameters in cases:
        result = await runtime.execute(action, parameters)
        assert result["status"] == "confirmation_required"


@pytest.mark.asyncio
async def test_notice_mutations_stop_before_http_until_confirmed() -> None:
    runtime = ActionRuntime()
    cases = (
        (
            "notices.send",
            {"course": "课程", "title": "标题", "content": "正文"},
        ),
        (
            "notices.edit",
            {
                "course": "课程",
                "notice": "原通知",
                "title": "新标题",
                "content": "新正文",
            },
        ),
        (
            "notices.schedule",
            {
                "course": "课程",
                "title": "定时通知",
                "content": "定时正文",
                "send_at": "2099-01-02 03:04",
            },
        ),
        ("notices.draft.delete", {"course": "课程", "draft": "通知草稿"}),
        ("notices.top.set", {"course": "课程", "notice": "通知", "top": True}),
        ("notices.recall", {"course": "课程", "notice": "通知"}),
        ("notices.delete", {"course": "课程", "notice": "通知"}),
    )
    for action, parameters in cases:
        result = await runtime.execute(action, parameters)
        assert result["status"] == "confirmation_required"


@pytest.mark.asyncio
async def test_exam_library_deletions_stop_before_http_until_confirmed() -> None:
    runtime = ActionRuntime()
    cases = (
        ("exam.paper.delete", {"course": "课程", "paper": "试卷一"}),
        (
            "exam.paper_folder.delete",
            {"course": "课程", "folder": "复习试卷"},
        ),
    )
    for action, parameters in cases:
        result = await runtime.execute(action, parameters)
        assert result["status"] == "confirmation_required"
        assert "回收站" in result["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_exam_question_deletion_stops_before_http_until_confirmed() -> None:
    runtime = ActionRuntime()
    result = await runtime.execute(
        "exam.question.delete",
        {"course": "课程", "paper": "试卷一", "question": "3"},
    )
    assert result["status"] == "confirmation_required"
    assert "永久删除" in result["confirmation"]["summary"]
    assert "试卷一" in result["confirmation"]["summary"]

    type_result = await runtime.execute(
        "exam.question_type.delete",
        {"course": "课程", "paper": "试卷一", "question_type": "判断题"},
    )
    assert type_result["status"] == "confirmation_required"
    assert "全部题目" in type_result["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_question_bank_deletions_stop_before_http_until_confirmed() -> None:
    runtime = ActionRuntime()
    cases = (
        (
            "question_bank.directory.delete",
            {"course": "课程", "directory": "复习题"},
        ),
        (
            "question_bank.question.delete",
            {"course": "课程", "question": "question-1"},
        ),
    )
    for action, parameters in cases:
        result = await runtime.execute(action, parameters)
        assert result["status"] == "confirmation_required"
        assert "回收站" in result["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_question_bank_permission_update_stops_before_http_until_confirmed() -> None:
    result = await ActionRuntime().execute(
        "question_bank.directory.permissions.update",
        {
            "course": "课程",
            "directory": "复习题",
            "share_scope": "private",
            "allow_student_self_practice": False,
        },
    )
    assert result["status"] == "confirmation_required"
    assert "私有" in result["confirmation"]["summary"]
    assert "非本人创建" in result["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_question_bank_question_type_delete_stops_before_http_until_confirmed() -> None:
    result = await ActionRuntime().execute(
        "question_bank.question_type.delete",
        {"course": "课程", "question_type": "术语解释"},
    )
    assert result["status"] == "confirmation_required"
    assert "术语解释" in result["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_question_bank_label_destructive_and_sync_actions_require_confirmation() -> None:
    runtime = ActionRuntime()
    deletion = await runtime.execute(
        "question_bank.label.delete",
        {"course": "课程", "label": "写作"},
    )
    sync = await runtime.execute(
        "question_bank.question.labels.sync",
        {
            "course": "课程",
            "questions": ["question-1"],
            "labels": ["求职信"],
            "mode": "replace",
        },
    )
    assert deletion["status"] == "confirmation_required"
    assert "全部子标签" in deletion["confirmation"]["summary"]
    assert sync["status"] == "confirmation_required"
    assert "作业和考试" in sync["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_question_bank_topic_destructive_and_sync_actions_require_confirmation() -> None:
    runtime = ActionRuntime()
    deletion = await runtime.execute(
        "question_bank.topic.delete",
        {"course": "课程", "topic": "Paragraph Writing"},
    )
    sync = await runtime.execute(
        "question_bank.question.topics.sync",
        {
            "course": "课程",
            "questions": ["question-1"],
            "topics": ["Topic Sentence"],
            "mode": "replace",
        },
    )
    assert deletion["status"] == "confirmation_required"
    assert "全部后代节点" in deletion["confirmation"]["summary"]
    assert sync["status"] == "confirmation_required"
    assert "作业和考试" in sync["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_question_bank_recycle_and_lock_risks_require_confirmation() -> None:
    runtime = ActionRuntime()
    cases = (
        (
            "question_bank.items.lock",
            {"course": "课程", "questions": ["question-1"]},
            "锁定",
        ),
        (
            "question_bank.items.unlock",
            {"course": "课程", "items": ["question-1"]},
            "解锁",
        ),
        (
            "question_bank.recycle.delete",
            {"course": "课程", "items": ["question-1"]},
            "无法恢复",
        ),
        ("question_bank.recycle.empty", {"course": "课程"}, "永久清空"),
    )
    for action, parameters, expected in cases:
        result = await runtime.execute(action, parameters)
        assert result["status"] == "confirmation_required"
        assert expected in result["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_discussion_mutations_stop_before_http_until_confirmed() -> None:
    runtime = ActionRuntime()
    cases = (
        (
            "discussions.topic.create",
            {"course": "课程", "title": "标题", "content": "正文"},
        ),
        (
            "discussions.topic.edit",
            {"course": "课程", "topic": "原话题", "content": "新正文"},
        ),
        (
            "discussions.topic.top.set",
            {"course": "课程", "topic": "话题", "top": True},
        ),
        ("discussions.topic.delete", {"course": "课程", "topic": "话题"}),
        (
            "discussions.reply.create",
            {"course": "课程", "topic": "话题", "content": "回复"},
        ),
        (
            "discussions.reply.edit",
            {"course": "课程", "topic": "话题", "reply": "原回复", "content": "新回复"},
        ),
        (
            "discussions.reply.delete",
            {"course": "课程", "topic": "话题", "reply": "回复"},
        ),
    )
    for action, parameters in cases:
        result = await runtime.execute(action, parameters)
        assert result["status"] == "confirmation_required"


@pytest.mark.asyncio
async def test_cloud_disk_deletion_stops_before_http_until_confirmed() -> None:
    result = await ActionRuntime().execute(
        "cloud_disk.items.delete",
        {"resources": ["verification.txt"]},
    )
    assert result["status"] == "confirmation_required"
    assert "verification.txt" in result["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_personal_note_deletion_stops_before_http_until_confirmed() -> None:
    result = await ActionRuntime().execute("notes.delete", {"note": "复习计划"})
    assert result["status"] == "confirmation_required"
    assert "复习计划" in result["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_personal_inbox_deletion_stops_before_http_until_confirmed() -> None:
    result = await ActionRuntime().execute(
        "inbox.notice.delete",
        {"notice": "课程通知", "scope": "received"},
    )
    assert result["status"] == "confirmation_required"
    assert "课程通知" in result["confirmation"]["summary"]

    send = await ActionRuntime().execute(
        "inbox.notice.send",
        {"recipients": ["本人"], "title": "测试通知", "content": "正文"},
    )
    assert send["status"] == "confirmation_required"
    assert "本人" in send["confirmation"]["summary"]
    assert "测试通知" in send["confirmation"]["summary"]

    draft_delete = await ActionRuntime().execute(
        "inbox.draft.delete",
        {"draft": "个人草稿"},
    )
    assert draft_delete["status"] == "confirmation_required"
    assert "个人草稿" in draft_delete["confirmation"]["summary"]

    folder_delete = await ActionRuntime().execute(
        "inbox.folder.delete",
        {"folder": "待办"},
    )
    assert folder_delete["status"] == "confirmation_required"
    assert "待办" in folder_delete["confirmation"]["summary"]

    permanent = await ActionRuntime().execute(
        "inbox.recycle.items.delete",
        {"notices": ["旧通知"]},
    )
    assert permanent["status"] == "confirmation_required"
    assert "旧通知" in permanent["confirmation"]["summary"]

    empty = await ActionRuntime().execute("inbox.recycle.empty", {})
    assert empty["status"] == "confirmation_required"
    assert "无法恢复" in empty["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_personal_group_publish_and_delete_actions_require_confirmation() -> None:
    runtime = ActionRuntime()
    cases = (
        (
            "groups.create",
            {"name": "课程小组", "description": "课程交流"},
            "课程小组",
        ),
        (
            "groups.update",
            {"group": "课程小组", "name": "写作课程小组"},
            "写作课程小组",
        ),
        (
            "groups.logo.update",
            {"group": "课程小组", "file": r"D:\Images\logo.png"},
            r"D:\Images\logo.png",
        ),
        (
            "groups.modules.update",
            {"group": "课程小组", "enabled_type_ids": ["2", "3"]},
            "2",
        ),
        (
            "groups.levels.series.update",
            {"group": "课程小组", "series": "default"},
            "default",
        ),
        (
            "groups.levels.custom.update",
            {"group": "课程小组", "levels": [{"level": 1}] * 15},
            "完整 15 级",
        ),
        (
            "groups.growth_rules.update",
            {"group": "课程小组", "changes": {"2": 6}},
            "2",
        ),
        (
            "groups.growth_rules.series.update",
            {"group": "课程小组", "series": "default"},
            "default",
        ),
        (
            "groups.settings.update",
            {"group": "课程小组", "changes": {"topicNeedCheck": True}},
            "topicNeedCheck",
        ),
        (
            "groups.speaking_rules.update",
            {"group": "课程小组", "changes": {"leastTopicWord": 30}},
            "leastTopicWord",
        ),
        (
            "groups.notice.send",
            {"group": "课程小组", "title": "开课通知", "content": "周一开始上课。"},
            "开课通知",
        ),
        (
            "groups.review_reminder.create",
            {
                "group": "课程小组",
                "start_time": "23:58",
                "end_time": "23:59",
                "weeks": ["星期日"],
                "puids": ["405017213"],
            },
            "23:58",
        ),
        (
            "groups.review_reminder.update",
            {
                "group": "课程小组",
                "reminder": "reminder-1",
                "start_time": "23:57",
            },
            "reminder-1",
        ),
        (
            "groups.review_reminders.delete",
            {"group": "课程小组", "reminders": ["reminder-1"]},
            "reminder-1",
        ),
        (
            "groups.labels.delete",
            {"group": "课程小组", "labels": ["重点"]},
            "重点",
        ),
        (
            "groups.deletion_reasons.delete",
            {"group": "课程小组", "reasons": ["内容重复"]},
            "内容重复",
        ),
        (
            "groups.recycle.items.delete",
            {"group": "课程小组", "items": ["10"]},
            "无法恢复",
        ),
        (
            "groups.recycle.empty",
            {"group": "课程小组"},
            "无法恢复",
        ),
        (
            "groups.export.cancel",
            {"group": "课程小组", "export": "21203"},
            "21203",
        ),
        (
            "groups.activity.create",
            {"group": "课程小组", "title": "课程入口", "online": False},
            "课程入口",
        ),
        (
            "groups.activity.update",
            {"group": "课程小组", "activity": "课程入口", "title": "新入口"},
            "新入口",
        ),
        (
            "groups.activity.online_status.update",
            {"group": "课程小组", "activity": "课程入口", "online": True},
            "上线",
        ),
        (
            "groups.activities.reorder",
            {"group": "课程小组", "activities": ["入口二", "入口一"]},
            "入口二",
        ),
        (
            "groups.activity.delete",
            {"group": "课程小组", "activity": "课程入口"},
            "课程入口",
        ),
        ("groups.quit", {"group": "他人小组"}, "他人小组"),
        ("groups.dismiss", {"group": "本人小组"}, "本人小组"),
        (
            "groups.members.add",
            {"group": "课程小组", "puids": ["101", "102"]},
            "101",
        ),
        (
            "groups.members.bulk_import",
            {"group": "课程小组", "file": r"D:\Temp\members.xlsx"},
            "members.xlsx",
        ),
        (
            "groups.member.manager_status.update",
            {"group": "课程小组", "member": "张三", "manager": True},
            "设为管理员",
        ),
        (
            "groups.member.permissions.update",
            {"group": "课程小组", "member": "张三", "changes": {"showBarcode": True}},
            "showBarcode",
        ),
        (
            "groups.member.remove",
            {"group": "课程小组", "member": "张三"},
            "张三",
        ),
        (
            "groups.creator.transfer",
            {"group": "课程小组", "member": "张三"},
            "失去创建者身份",
        ),
        (
            "groups.members.external.clear",
            {"group": "课程小组"},
            "非学习通成员",
        ),
        ("groups.folder.delete", {"folder": "归档"}, "归档"),
        (
            "groups.topic.create",
            {"group": "课程小组", "title": "写作问题", "content": "先判断问题。"},
            "写作问题",
        ),
        (
            "groups.topic.delete",
            {"group": "课程小组", "topic": "写作问题"},
            "写作问题",
        ),
        (
            "groups.topic.choice_status.update",
            {"group": "课程小组", "topic": "写作问题", "choice": True},
            "精华",
        ),
        (
            "groups.topic.praise_status.update",
            {"group": "课程小组", "topic": "写作问题", "praised": True},
            "点赞",
        ),
        (
            "groups.topics.score.set",
            {"group": "课程小组", "topics": ["问题一", "问题二"], "score": 85},
            "85",
        ),
        (
            "groups.topics.delete",
            {"group": "课程小组", "topics": ["问题一", "问题二"]},
            "问题二",
        ),
        (
            "groups.topic.update",
            {"group": "课程小组", "topic": "写作问题", "title": "课程写作问题"},
            "课程写作问题",
        ),
        (
            "groups.topic.reply.create",
            {"group": "课程小组", "topic": "写作问题", "content": "先看论点。"},
            "先看论点",
        ),
        (
            "groups.topic.reply.delete",
            {"group": "课程小组", "topic": "写作问题", "reply": "先看论点"},
            "先看论点",
        ),
        (
            "groups.topic.reply.update",
            {
                "group": "课程小组",
                "topic": "写作问题",
                "reply": "先看论点",
                "content": "先看中心论点。",
            },
            "先看中心论点",
        ),
        (
            "groups.topic.folder.delete",
            {"group": "课程小组", "folder": "课程论文"},
            "课程论文",
        ),
        (
            "groups.topic.folders.delete",
            {"group": "课程小组", "folders": ["论文", "读书会"]},
            "读书会",
        ),
        (
            "groups.topic.draft.publish",
            {"group": "课程小组", "draft": "draft-uuid"},
            "draft-uuid",
        ),
    )
    for action, parameters, expected in cases:
        result = await runtime.execute(action, parameters)
        assert result["status"] == "confirmation_required"
        assert expected in result["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_new_resource_and_cloud_publish_or_delete_actions_require_confirmation() -> None:
    runtime = ActionRuntime()
    cases = (
        (
            "resources.copy",
            {"course": "课程", "resource": "Guide.pdf"},
        ),
        (
            "course_assets.folder.create",
            {"course": "课程", "kind": "courseware", "name": "Unit 1"},
        ),
        (
            "course_assets.cloud_files.import",
            {
                "course": "课程",
                "kind": "courseware",
                "resources": ["Week 2.pdf"],
            },
        ),
        (
            "course_assets.file.upload",
            {
                "course": "课程",
                "kind": "teaching_plan",
                "file_path": r"C:\教案\第二单元.docx",
            },
        ),
        (
            "course_assets.item.copy",
            {"course": "课程", "kind": "courseware", "asset": "Slides"},
        ),
        (
            "course_assets.items.delete",
            {"course": "课程", "kind": "courseware", "assets": ["Slides"]},
        ),
        (
            "course_assets.recycle.restore",
            {"course": "课程", "kind": "courseware", "assets": ["Slides"]},
        ),
        (
            "course_assets.recycle.items.delete",
            {"course": "课程", "kind": "courseware", "assets": ["Slides"]},
        ),
        (
            "resources.cloud_disk.copy",
            {"course": "课程", "resource": "Guide.pdf", "destination": "Archive"},
        ),
        (
            "resources.cloud_files.import",
            {
                "course": "课程",
                "resources": ["Guide.pdf"],
                "destination": "Unit 1",
            },
        ),
        (
            "resources.cloud_folder.import",
            {"course": "课程", "resource": "Review", "destination": "Unit 1"},
        ),
        (
            "resources.label.delete",
            {"course": "课程", "resource": "Guide.pdf", "label": "Review"},
        ),
        (
            "resources.labels.update",
            {"course": "课程", "resources": ["Guide.pdf"], "labels": ["Review"]},
        ),
        (
            "cloud_disk.folder.create",
            {"name": "Review", "parent": "", "shared": False},
        ),
        (
            "cloud_disk.recycle.restore",
            {"resources": ["Guide.pdf"], "conflict_policy": "keep_both"},
        ),
        (
            "cloud_disk.recycle.items.delete",
            {"resources": ["Guide.pdf"]},
        ),
        ("cloud_disk.recycle.empty", {}),
    )
    for action, parameters in cases:
        result = await runtime.execute(action, parameters)
        assert result["status"] == "confirmation_required"


@pytest.mark.asyncio
async def test_task_engine_delete_and_publish_actions_require_confirmation() -> None:
    runtime = ActionRuntime()
    cases = (
        (
            "task_engine.folder.delete",
            {"course": "课程", "folder": "单元一", "allow_nonempty": True},
            "单元一",
        ),
        (
            "task_engine.task.delete",
            {"course": "课程", "task": "过程分析"},
            "过程分析",
        ),
        (
            "task_engine.label.delete",
            {"course": "课程", "label": "复习"},
            "复习",
        ),
        (
            "task_engine.publish_status.update",
            {"course": "课程", "task": "过程分析", "published": True},
            "学生是否可学习",
        ),
    )
    for action, parameters, expected in cases:
        result = await runtime.execute(action, parameters)
        assert result["status"] == "confirmation_required"
        assert expected in result["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_knowledge_graph_delete_actions_require_confirmation() -> None:
    runtime = ActionRuntime()
    cases = (
        (
            "knowledge_graph.node.delete",
            {"course": "课程", "node": "第一单元"},
            "全部父子关系后代",
        ),
        (
            "knowledge_graph.node.relation.remove",
            {
                "course": "课程",
                "node": "标点",
                "relation": "后置关系",
                "target": "句子写作",
            },
            "将不再显示",
        ),
        (
            "knowledge_graph.relation_type.delete",
            {"course": "课程", "relation": "支持关系"},
            "使用该定义的关系将受影响",
        ),
        (
            "knowledge_graph.label_group.delete",
            {"course": "课程", "group": "复习"},
            "其中全部标签",
        ),
        (
            "knowledge_graph.label.delete",
            {"course": "课程", "label": "难点"},
            "相关节点将失去该标签",
        ),
        (
            "knowledge_graph.model.delete",
            {"course": "课程", "model": "复习图谱"},
            "专属配置",
        ),
    )
    for action, parameters, expected in cases:
        result = await runtime.execute(action, parameters)
        assert result["status"] == "confirmation_required"
        assert expected in result["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_knowledge_graph_student_visible_settings_require_confirmation() -> None:
    runtime = ActionRuntime()
    result = await runtime.execute(
        "knowledge_graph.settings.update",
        {"course": "课程", "show_all_relations": True},
    )

    assert result["status"] == "confirmation_required"
    assert "学生端图谱外观" in result["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_knowledge_graph_advanced_settings_require_confirmation() -> None:
    runtime = ActionRuntime()
    result = await runtime.execute(
        "knowledge_graph.advanced_settings.update",
        {"course": "课程", "topic_card": True, "selftest_included": False},
    )

    assert result["status"] == "confirmation_required"
    assert "知识点卡片" in result["confirmation"]["summary"]
    assert "纳入自测" in result["confirmation"]["summary"]
    assert "学生端课程图谱" in result["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_knowledge_graph_node_relation_add_requires_confirmation() -> None:
    runtime = ActionRuntime()
    result = await runtime.execute(
        "knowledge_graph.node.relation.add",
        {
            "course": "课程",
            "node": "标点",
            "relation": "后置关系",
            "target": "句子写作",
        },
    )

    assert result["status"] == "confirmation_required"
    assert "学生端图谱关系会立即变化" in result["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_knowledge_graph_model_visibility_actions_require_confirmation() -> None:
    runtime = ActionRuntime()
    cases = (
        (
            "knowledge_graph.model.visibility.update",
            {"course": "课程", "model": "学习地图", "visible": True},
            "学生端可见性",
        ),
        (
            "knowledge_graph.model.classes.update",
            {"course": "课程", "model": "知识图谱", "visible_classes": ["一班"]},
            "其他班级将看不到",
        ),
    )
    for action, parameters, expected in cases:
        result = await runtime.execute(action, parameters)
        assert result["status"] == "confirmation_required"
        assert expected in result["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_knowledge_graph_event_actions_require_confirmation() -> None:
    runtime = ActionRuntime()
    cases = (
        (
            "knowledge_graph.event.create",
            {"course": "课程", "name": "完成事件"},
            "自动改变学生端显示内容",
        ),
        (
            "knowledge_graph.event.update",
            {"course": "课程", "event": "完成事件"},
            "立即生效",
        ),
        (
            "knowledge_graph.event.delete",
            {"course": "课程", "event": "完成事件"},
            "无法恢复",
        ),
    )
    for action, parameters, expected in cases:
        result = await runtime.execute(action, parameters)
        assert result["status"] == "confirmation_required"
        assert expected in result["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_class_activity_publish_and_delete_actions_require_confirmation() -> None:
    runtime = ActionRuntime()
    cases = (
        (
            "class_activities.group.delete",
            {"course": "课程", "group": "课堂练习", "allow_nonempty": True},
            "课堂练习",
        ),
        (
            "class_activities.activity.start",
            {"course": "课程", "activity": "第一节课签到"},
            "学生将可以参与",
        ),
        (
            "class_activities.attendance.create",
            {"course": "课程", "title": "课堂签到", "duration_minutes": 10},
            "课堂签到",
        ),
        (
            "class_activities.activity.end",
            {"course": "课程", "activity": "第一节课签到"},
            "学生将不能继续参与",
        ),
        (
            "class_activities.activity.delete",
            {"course": "课程", "activity": "第一节课签到"},
            "回收站",
        ),
        (
            "class_activities.recycle.items.delete",
            {"course": "课程", "activities": ["第一节课签到"]},
            "无法恢复",
        ),
    )
    for action, parameters, expected in cases:
        result = await runtime.execute(action, parameters)
        assert result["status"] == "confirmation_required"
        assert expected in result["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_knowledge_hub_share_and_delete_actions_require_confirmation() -> None:
    runtime = ActionRuntime()
    cases = (
        (
            "knowledge_hub.base.share.update",
            {"course": "课程", "base": "复习库", "shared": True},
            "共享",
        ),
        (
            "knowledge_hub.base.delete",
            {"course": "课程", "base": "复习库"},
            "永久删除",
        ),
        (
            "knowledge_hub.document.delete",
            {"course": "课程", "base": "复习库", "document": "旧资料.pdf"},
            "旧资料.pdf",
        ),
    )
    for action, parameters, expected in cases:
        result = await runtime.execute(action, parameters)
        assert result["status"] == "confirmation_required"
        assert expected in result["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_live_publish_permission_and_delete_actions_require_confirmation() -> None:
    runtime = ActionRuntime()
    cases = (
        ("live.room.create", {"title": "公开课"}, "公开课"),
        ("live.room.settings.update", {"room": "公开课", "replay_enabled": True}, "回看"),
        ("live.stream.credentials", {"room": "公开课"}, "推流"),
        ("live.room.delete", {"room": "公开课"}, "公开课"),
        ("live.recycle.delete", {"room": "公开课"}, "公开课"),
        ("live.theme.create", {"name": "系列直播"}, "系列直播"),
        ("live.theme.room.add", {"theme": "系列直播", "room": "公开课"}, "公开课"),
        ("live.theme.delete", {"theme": "系列直播"}, "系列直播"),
    )
    for action, parameters, expected in cases:
        result = await runtime.execute(action, parameters)
        assert result["status"] == "confirmation_required"
        assert expected in result["confirmation"]["summary"]


@pytest.mark.asyncio
async def test_cloud_source_runtime_dispatch_converts_integer_strings(monkeypatch) -> None:
    class FakeAPI:
        @staticmethod
        def get_course(query):
            assert query == "课程"
            return {
                "course_id": "course-1",
                "course_name": "课程",
                "cpi": "cpi-1",
                "classes": [{"clazz_id": "class-1", "clazz_name": "班级"}],
            }

        @staticmethod
        def list_course_cloud_sources(course, clazz, **kwargs):
            return {"course": course["course_id"], "clazz": clazz["clazz_id"], **kwargs}

    runtime = ActionRuntime()
    monkeypatch.setattr(runtime, "_api", lambda: FakeAPI())
    result = await runtime.execute(
        "resources.cloud_sources.list",
        {"course": "课程", "page": "2", "page_size": "50"},
    )
    assert result["status"] == "ok"
    assert result["result"]["page"] == 2
    assert result["result"]["page_size"] == 50


def test_optional_label_list_allows_clearing_every_resource_label() -> None:
    assert ActionRuntime._optional_string_list(None) == []
    assert ActionRuntime._optional_string_list("") == []
    assert ActionRuntime._optional_string_list(["Review", " Final "]) == [
        "Review",
        "Final",
    ]
