import json

import pytest

from chaoxing_agent.cli import _parse_permission_changes, _run_action, build_parser


def test_personal_space_cli_parses_discovery_and_open() -> None:
    discovery = build_parser().parse_args(["space-modules"])
    opening = build_parser().parse_args(["space-open", "笔记"])
    assert discovery.command == "space-modules"
    assert opening.module == "笔记"


def test_learning_cli_parses_list_modules_open_and_integrity() -> None:
    listing = build_parser().parse_args(["learning-courses", "--search", "英语"])
    modules = build_parser().parse_args(["learning-modules", "英语文体与写作"])
    opened = build_parser().parse_args(["learning-open", "英语文体与写作", "章节"])
    integrity = build_parser().parse_args(["learning-integrity", "英语文体与写作"])
    accepted = build_parser().parse_args(
        [
            "learning-integrity-accept",
            "英语文体与写作",
            "--confirmation-token",
            "token-1",
        ]
    )

    assert listing.search == "英语"
    assert modules.course == "英语文体与写作"
    assert opened.module == "章节"
    assert integrity.command == "learning-integrity"
    assert accepted.confirmation_token == "token-1"


def test_learning_cli_parses_semantic_read_commands() -> None:
    activities = build_parser().parse_args(
        ["learning-activities", "新教师入职培训", "--status", "ended", "--search", "讨论"]
    )
    chapters = build_parser().parse_args(["learning-chapters", "英语文体与写作", "--search", "1.1"])
    discussions = build_parser().parse_args(
        ["learning-discussions", "英语文体与写作", "--class-only", "--search", "环境"]
    )
    discussion = build_parser().parse_args(
        [
            "learning-discussion-read",
            "英语文体与写作",
            "环境问题",
            "--order",
            "1",
            "--reply-search",
            "pollution",
        ]
    )
    discussion_create = build_parser().parse_args(
        ["learning-discussion-create", "英语文体与写作", "标题", "正文"]
    )
    discussion_update = build_parser().parse_args(
        ["learning-discussion-update", "英语文体与写作", "标题", "--content", "新正文"]
    )
    discussion_delete = build_parser().parse_args(
        ["learning-discussion-delete", "英语文体与写作", "标题"]
    )
    reply_create = build_parser().parse_args(
        ["learning-discussion-reply-create", "英语文体与写作", "标题", "回复"]
    )
    reply_update = build_parser().parse_args(
        [
            "learning-discussion-reply-update",
            "英语文体与写作",
            "标题",
            "原回复",
            "新回复",
        ]
    )
    reply_delete = build_parser().parse_args(
        ["learning-discussion-reply-delete", "英语文体与写作", "标题", "回复"]
    )
    homeworks = build_parser().parse_args(
        ["learning-homeworks", "英语文体与写作", "--status", "unsubmitted"]
    )
    homework = build_parser().parse_args(
        ["learning-homework-read", "新教师入职培训", "BOPPPS设计小讨论"]
    )
    homework_answer = build_parser().parse_args(
        ["learning-homework-answer-enter", "新教师入职培训", "BOPPPPS设计小讨论"]
    )
    homework_save = build_parser().parse_args(
        [
            "learning-homework-answer-save",
            "新教师入职培训",
            "BOPPPPS设计小讨论",
            "--updates-json",
            '[{"question":"1","answer":"真实问题"}]',
        ]
    )
    homework_submit = build_parser().parse_args(
        [
            "learning-homework-submit",
            "新教师入职培训",
            "BOPPPPS设计小讨论",
            "--confirmation-token",
            "submit-token",
        ]
    )
    homework_redo = build_parser().parse_args(
        [
            "learning-homework-redo",
            "新教师入职培训",
            "BOPPPPS设计小讨论",
            "--confirmation-token",
            "redo-token",
        ]
    )
    homework_attempts = build_parser().parse_args(
        ["learning-homework-attempts", "新教师入职培训", "BOPPPPS设计小讨论"]
    )
    homework_attempt = build_parser().parse_args(
        [
            "learning-homework-attempt-read",
            "新教师入职培训",
            "BOPPPPS设计小讨论",
            "1",
        ]
    )
    exams = build_parser().parse_args(["learning-exams", "英语文体与写作"])
    self_tests = build_parser().parse_args(["learning-self-tests", "英语文体与写作"])
    materials = build_parser().parse_args(
        ["learning-materials", "英语文体与写作", "--folder", "Week 1"]
    )
    ai_tools = build_parser().parse_args(["learning-ai-tools", "英语文体与写作"])
    wrong = build_parser().parse_args(["learning-wrong-questions", "英语文体与写作"])
    records = build_parser().parse_args(["learning-records", "英语文体与写作"])
    graph = build_parser().parse_args(
        ["learning-graph", "英语文体与写作", "--search", "写作", "--level", "2"]
    )
    graph_node = build_parser().parse_args(["learning-graph-node", "英语文体与写作", "Punctuation"])
    graph_models = build_parser().parse_args(
        ["learning-graph-models", "英语文体与写作", "--search", "知识"]
    )
    graph_model = build_parser().parse_args(["learning-graph-model", "英语文体与写作", "知识图谱"])

    assert activities.status == "ended" and activities.search == "讨论"
    assert chapters.search == "1.1"
    assert discussions.class_only is True and discussions.search == "环境"
    assert discussion.topic == "环境问题"
    assert discussion.order == 1 and discussion.reply_search == "pollution"
    assert discussion_create.title == "标题" and discussion_create.content == "正文"
    assert discussion_update.content == "新正文"
    assert discussion_delete.topic == "标题"
    assert reply_create.content == "回复"
    assert reply_update.reply == "原回复" and reply_update.content == "新回复"
    assert reply_delete.reply == "回复"
    assert homeworks.status == "unsubmitted"
    assert homework.homework == "BOPPPS设计小讨论"
    assert homework_answer.command == "learning-homework-answer-enter"
    assert homework_save.command == "learning-homework-answer-save"
    assert json.loads(homework_save.updates_json)[0]["question"] == "1"
    assert homework_submit.confirmation_token == "submit-token"
    assert homework_redo.confirmation_token == "redo-token"
    assert homework_attempts.command == "learning-homework-attempts"
    assert homework_attempt.attempt == "1"
    assert exams.command == "learning-exams"
    assert self_tests.command == "learning-self-tests"
    assert materials.folder == "Week 1"
    assert ai_tools.command == "learning-ai-tools"
    assert wrong.command == "learning-wrong-questions"
    assert records.command == "learning-records"
    assert graph.search == "写作" and graph.level == 2
    assert graph_node.node == "Punctuation"
    assert graph_models.search == "知识"
    assert graph_model.model == "知识图谱"


@pytest.mark.asyncio
async def test_learning_homework_mutation_cli_dispatches_updates_and_confirmation() -> None:
    class Runtime:
        def __init__(self) -> None:
            self.calls = []

        async def execute(self, action, parameters, confirmation_token=None):
            self.calls.append((action, parameters, confirmation_token))
            return {"status": "ok"}

    runtime = Runtime()
    save = build_parser().parse_args(
        [
            "learning-homework-answer-save",
            "英语文体与写作",
            "期中调查",
            "--updates-json",
            '[{"question":"2","answer":"正文"}]',
        ]
    )
    submit = build_parser().parse_args(
        [
            "learning-homework-submit",
            "英语文体与写作",
            "期中调查",
            "--confirmation-token",
            "submit-token",
        ]
    )

    await _run_action(save, runtime)
    await _run_action(submit, runtime)

    assert runtime.calls[0] == (
        "learning.course.homework.answers.save",
        {
            "course": "英语文体与写作",
            "homework": "期中调查",
            "updates": [{"question": "2", "answer": "正文"}],
        },
        None,
    )
    assert runtime.calls[1] == (
        "learning.course.homework.submit",
        {"course": "英语文体与写作", "homework": "期中调查"},
        "submit-token",
    )


def test_job_ability_cli_parses_search_catalog_and_industry_commands() -> None:
    search = build_parser().parse_args(
        ["job-search", "英语教师", "--education", "本科", "--page", "2", "--page-size", "30"]
    )
    details = build_parser().parse_args(
        ["job-read", "job-42", "--search", "英语教师", "--education", "本科"]
    )
    catalog = build_parser().parse_args(["occupation-catalog", "--education", "硕士"])
    industries = build_parser().parse_args(["industries", "互联网技术", "--page-size", "80"])
    jobs = build_parser().parse_args(["industry-jobs", "人工智能", "--page", "3"])

    assert search.keyword == "英语教师" and search.page == 2 and search.page_size == 30
    assert details.job == "job-42" and details.search == "英语教师"
    assert catalog.education == "硕士"
    assert industries.industry_type == "互联网技术" and industries.page_size == 80
    assert jobs.industry == "人工智能" and jobs.page == 3


def test_login_cli_accepts_username_and_fid_without_password_argument() -> None:
    parser = build_parser()
    target_url = "https://xueyinonline.chaoxing.com/livecoursenew"
    login = parser.parse_args(
        [
            "login",
            "--username",
            "13800138000",
            "--fid",
            "23080",
            "--target-url",
            target_url,
        ]
    )
    assert login.command == "login"
    assert login.username == "13800138000"
    assert login.fid == "23080"
    assert login.target_url == target_url
    learning_login = parser.parse_args(
        [
            "login",
            "--username",
            "13800138000",
            "--learning-course",
            "测试课程",
            "--learning-module",
            "直播课/见面课",
        ]
    )
    assert learning_login.learning_course == "测试课程"
    assert learning_login.learning_module == "直播课/见面课"
    dialog_login = parser.parse_args(
        [
            "login",
            "--windows-dialog",
            "--learning-course",
            "测试课程",
        ]
    )
    assert dialog_login.windows_dialog is True
    assert dialog_login.learning_module == "直播课/见面课"
    login_action = next(action for action in parser._actions if action.dest == "command")
    login_parser = login_action.choices["login"]
    assert all(action.dest != "password" for action in login_parser._actions)


@pytest.mark.asyncio
async def test_login_windows_dialog_does_not_read_from_terminal(monkeypatch) -> None:
    class Runtime:
        def __init__(self) -> None:
            self.call = None

        async def execute(self, action, parameters, confirmation_token=None):
            self.call = (action, dict(parameters), confirmation_token)
            return {"status": "ok", "logged_in": True}

    def fail_terminal_prompt(*_args, **_kwargs):
        raise AssertionError("terminal credential prompt must not run")

    monkeypatch.setattr(
        "chaoxing_agent.windows_credentials.prompt_windows_credentials",
        lambda: ("dialog-user", "dialog-secret"),
    )
    monkeypatch.setattr("builtins.input", fail_terminal_prompt)
    monkeypatch.setattr("chaoxing_agent.cli.getpass.getpass", fail_terminal_prompt)
    args = build_parser().parse_args(
        [
            "login",
            "--windows-dialog",
            "--learning-course",
            "测试课程",
            "--learning-module",
            "直播课/见面课",
        ]
    )
    runtime = Runtime()

    result = await _run_action(args, runtime)

    action, parameters, token = runtime.call
    assert action == "session.login"
    assert parameters["username"] == "dialog-user"
    assert parameters["password"] == "dialog-secret"
    assert parameters["learning_course"] == "测试课程"
    assert token is None
    assert "dialog-secret" not in str(result)


def test_subject_creation_cli_parses_read_folder_and_subject_commands() -> None:
    listing = build_parser().parse_args(["subjects", "--folder", "课程", "--search", "写作"])
    tree = build_parser().parse_args(["subject-tree", "--max-folders", "30"])
    create = build_parser().parse_args(["subject-folder-create", "资料", "--parent-folder", "课程"])
    move = build_parser().parse_args(["subject-folder-move", "资料", "--target-folder", "归档"])
    delete = build_parser().parse_args(
        [
            "subject-folder-delete",
            "资料",
            "--allow-nonempty",
            "--confirmation-token",
            "token-1",
        ]
    )
    publish = build_parser().parse_args(
        ["subject-publish", "写作专题", "--off", "--confirmation-token", "token-2"]
    )
    recycle = build_parser().parse_args(["subject-recycle", "--search", "旧专题"])
    permanent = build_parser().parse_args(
        ["subject-recycle-delete", "旧专题", "--confirmation-token", "token-3"]
    )
    assert listing.folder == "课程" and listing.search == "写作"
    assert tree.max_folders == 30
    assert create.parent_folder == "课程"
    assert move.target_folder == "归档"
    assert delete.allow_nonempty is True and delete.confirmation_token == "token-1"
    assert publish.off is True and publish.confirmation_token == "token-2"
    assert recycle.search == "旧专题"
    assert permanent.confirmation_token == "token-3"


def test_detection_cli_parses_records_submissions_payment_and_report() -> None:
    records = build_parser().parse_args(["detections", "aigc", "--status", "6", "--search", "论文"])
    submit = build_parser().parse_args(
        [
            "detection-submit",
            "similarity",
            "论文",
            "--author",
            "作者",
            "--file",
            r"D:\paper.docx",
            "--channel-id",
            "11",
            "--confirmation-token",
            "token-1",
        ]
    )
    compare = build_parser().parse_args(
        [
            "detection-compare",
            "文档一",
            r"D:\one.docx",
            "文档二",
            r"D:\two.docx",
        ]
    )
    free = build_parser().parse_args(
        ["detection-use-free", "aigc", "record-1", "--confirmation-token", "token-2"]
    )
    report = build_parser().parse_args(
        ["detection-report", "aigc", "record-1", r"D:\Reports", "--overwrite"]
    )
    assert records.type == "aigc" and records.status == 6 and records.search == "论文"
    assert submit.file == r"D:\paper.docx" and submit.channel_ids == ["11"]
    assert submit.confirmation_token == "token-1"
    assert compare.file_2 == r"D:\two.docx"
    assert free.confirmation_token == "token-2"
    assert report.output_path == r"D:\Reports" and report.overwrite is True


def test_live_cli_parses_room_theme_and_recycle_commands() -> None:
    create = build_parser().parse_args(
        [
            "live-create",
            "公开课",
            "--scheduled-time",
            "2026-09-03 11:00",
            "--introduction",
            "课程介绍",
            "--confirmation-token",
            "token-1",
        ]
    )
    settings = build_parser().parse_args(
        [
            "live-settings",
            "公开课",
            "--replay-enabled",
            "--no-comments-enabled",
            "--access-password",
            "1234",
            "--allowed-unit-id",
            "23080",
            "--replay-start-offset-seconds",
            "5",
        ]
    )
    restore = build_parser().parse_args(["live-restore", "公开课"])
    theme_add = build_parser().parse_args(
        ["live-theme-add-room", "系列公开课", "公开课", "--confirmation-token", "token-2"]
    )
    theme_settings = build_parser().parse_args(
        [
            "live-theme-settings",
            "系列公开课",
            "--no-forwarding-enabled",
            "--allowed-unit-id",
            "23080",
        ]
    )

    assert create.scheduled_time == "2026-09-03 11:00"
    assert create.confirmation_token == "token-1"
    assert settings.replay_enabled is True and settings.comments_enabled is False
    assert settings.access_password == "1234"
    assert settings.allowed_unit_ids == ["23080"]
    assert settings.replay_start_offset_seconds == 5
    assert restore.room == "公开课"
    assert theme_add.theme == "系列公开课" and theme_add.room == "公开课"
    assert theme_add.confirmation_token == "token-2"
    assert theme_settings.forwarding_enabled is False
    assert theme_settings.allowed_unit_ids == ["23080"]


def test_ai_workbench_cli_parses_groups_commands_and_recommendations() -> None:
    group = build_parser().parse_args(
        [
            "ai-group-create",
            "900000002",
            "备课",
            "--class",
            "800000002",
            "--confirmation-token",
            "token-1",
        ]
    )
    create = build_parser().parse_args(
        [
            "ai-command-create",
            "900000002",
            "备课",
            "生成提纲",
            "主题为：请输入主题",
            "生成结构清楚的提纲",
            "--prompt-words",
            "保持准确",
            "--role-type",
            "2",
        ]
    )
    update = build_parser().parse_args(
        [
            "ai-command-update",
            "900000002",
            "99",
            "--prompt-words",
            "只使用课程资料",
            "--role-type",
            "1",
        ]
    )
    order = build_parser().parse_args(["ai-command-reorder", "900000002", "备课", "0", "99", "1"])
    publish = build_parser().parse_args(["ai-command-publish", "900000002", "99", "--off"])
    recommendation = build_parser().parse_args(
        ["ai-recommendation-add", "900000002", "教学设计", "备课"]
    )

    assert group.clazz == "800000002" and group.confirmation_token == "token-1"
    assert create.prompt_words == "保持准确" and create.role_type == 2
    assert update.command == "ai-command-update" and update.ai_command == "99"
    assert update.prompt_words == "只使用课程资料" and update.role_type == 1
    assert order.role_type == 0 and order.commands == ["99", "1"]
    assert publish.command == "ai-command-publish" and publish.ai_command == "99"
    assert publish.off is True
    assert recommendation.recommendation == "教学设计" and recommendation.group == "备课"


def test_knowledge_hub_cli_parses_base_document_and_confirmation_commands() -> None:
    listing = build_parser().parse_args(
        [
            "knowledge-hub-bases",
            "900000001",
            "--search",
            "复习",
            "--category",
            "0",
        ]
    )
    create = build_parser().parse_args(
        [
            "knowledge-hub-base-create",
            "900000001",
            "期末复习库",
            "期末复习资料",
            "--split-rule-json",
            '{"splitStrategy":0,"enableOcr":true}',
        ]
    )
    share = build_parser().parse_args(
        [
            "knowledge-hub-base-share",
            "900000001",
            "期末复习库",
            "--off",
            "--confirmation-token",
            "token-1",
        ]
    )
    upload = build_parser().parse_args(
        [
            "knowledge-hub-document-upload",
            "900000001",
            "期末复习库",
            r"D:\资料\复习.pdf",
            "--classify-id",
            "2",
        ]
    )
    deletion = build_parser().parse_args(
        [
            "knowledge-hub-document-delete",
            "900000001",
            "期末复习库",
            "复习.pdf",
            "--confirmation-token",
            "token-2",
        ]
    )

    assert listing.search == "复习" and listing.category == 0
    assert create.name == "期末复习库" and create.split_rule_json
    assert share.off is True and share.confirmation_token == "token-1"
    assert upload.file == r"D:\资料\复习.pdf" and upload.classify_id == "2"
    assert deletion.document == "复习.pdf" and deletion.confirmation_token == "token-2"


def test_task_engine_cli_parses_crud_export_and_publish_commands() -> None:
    listing = build_parser().parse_args(
        ["task-list", "900000002", "--folder", "单元一", "--search", "导入", "--recycled"]
    )
    create = build_parser().parse_args(
        [
            "task-create",
            "900000002",
            "过程分析",
            "--folder",
            "单元一",
            "--introduce",
            "完成阅读",
            "--mode",
            "list",
            "--mode",
            "frame",
        ]
    )
    update = build_parser().parse_args(
        ["task-update", "900000002", "task-1", "--name", "过程分析二", "--target", "目标一"]
    )
    reorder = build_parser().parse_args(
        [
            "task-reorder",
            "900000002",
            "task-2",
            "task-1",
            "--folder-order",
            "folder-2",
            "folder-1",
        ]
    )
    deletion = build_parser().parse_args(
        ["task-delete", "900000002", "task-1", "--confirmation-token", "token-delete"]
    )
    export = build_parser().parse_args(
        ["task-export", "900000002", "task-1", "task-2", "--folder", "单元一"]
    )
    publish = build_parser().parse_args(
        [
            "task-publish",
            "900000002",
            "task-1",
            "--course-publish-json",
            '[{"courseId":"1"}]',
            "--task-publish-json",
            '[{"clazzId":"2"}]',
            "--confirmation-token",
            "token-publish",
        ]
    )

    assert listing.folder == "单元一" and listing.recycled is True
    assert create.selected_modes == ["list", "frame"] and create.introduce == "完成阅读"
    assert update.task == "task-1" and update.target == "目标一"
    assert reorder.task_order == ["task-2", "task-1"]
    assert reorder.folder_order == ["folder-2", "folder-1"]
    assert deletion.confirmation_token == "token-delete"
    assert export.tasks == ["task-1", "task-2"]
    assert publish.course_publish_json == '[{"courseId":"1"}]'
    assert publish.task_publish_json == '[{"clazzId":"2"}]'
    assert publish.confirmation_token == "token-publish"


@pytest.mark.asyncio
async def test_task_engine_publish_cli_dispatches_decoded_recipient_lists() -> None:
    class Runtime:
        def __init__(self) -> None:
            self.call = None

        async def execute(self, action, parameters, confirmation_token=None):
            self.call = (action, parameters, confirmation_token)
            return {"status": "ok"}

    args = build_parser().parse_args(
        [
            "task-publish",
            "900000002",
            "task-1",
            "--course-publish-json",
            '[{"courseId":"900000002"}]',
            "--task-publish-json",
            '[{"clazzId":"800000002"}]',
            "--confirmation-token",
            "token-publish",
        ]
    )
    runtime = Runtime()

    await _run_action(args, runtime)

    action, parameters, token = runtime.call
    assert action == "task_engine.publish_status.update"
    assert parameters["course_publish_param"] == [{"courseId": "900000002"}]
    assert parameters["task_publish_param"] == [{"clazzId": "800000002"}]
    assert token == "token-publish"


def test_knowledge_graph_cli_parses_nodes_labels_and_complete_orders() -> None:
    graph = build_parser().parse_args(
        ["graph", "900000002", "--class", "800000002", "--search", "概念", "--level", "2"]
    )
    category = build_parser().parse_args(
        ["graph-category-create", "900000002", "第一单元", "--description", "基础概念"]
    )
    node_create = build_parser().parse_args(
        [
            "graph-node-create",
            "900000002",
            "标点运用",
            "--type",
            "ability",
            "--parent",
            "第一单元",
            "--model",
            "知识图谱",
        ]
    )
    node_relation = build_parser().parse_args(
        [
            "graph-node-relation-add",
            "900000002",
            "标点运用",
            "association",
            "句子写作",
            "--description",
            "相关概念",
            "--confirmation-token",
            "token-relation",
        ]
    )
    relation = build_parser().parse_args(
        [
            "graph-relation-update",
            "900000002",
            "relation-1",
            "--name",
            "促进关系",
            "--relation-type",
            "0",
            "--relation-type",
            "2",
            "--arrow-size",
            "7",
        ]
    )
    settings = build_parser().parse_args(
        [
            "graph-settings-update",
            "900000002",
            "--show-all-relations",
            "--no-navigation-node-scale",
            "--confirmation-token",
            "token-settings",
        ]
    )
    advanced_settings = build_parser().parse_args(
        [
            "graph-advanced-settings-update",
            "900000002",
            "--topic-card",
            "--no-teach-target",
            "--micro-preview",
            "--confirmation-token",
            "token-advanced-settings",
        ]
    )
    model_visibility = build_parser().parse_args(
        [
            "graph-model-visibility",
            "900000002",
            "学习地图",
            "show",
            "--confirmation-token",
            "token-model",
        ]
    )
    model_classes = build_parser().parse_args(
        [
            "graph-model-classes-update",
            "900000002",
            "知识图谱",
            "一班",
            "二班",
            "--confirmation-token",
            "token-classes",
        ]
    )
    event = build_parser().parse_args(
        [
            "graph-event-create",
            "900000002",
            "完成事件",
            "completion",
            "greater_than_or_equal",
            "80",
            '[{"label":"重点","execute_module":"learning_path"}]',
            "--confirmation-token",
            "token-event",
        ]
    )
    export = build_parser().parse_args(
        [
            "graph-export",
            "900000002",
            "rdf",
            r"D:\Exports",
            "--model",
            "知识图谱",
            "--overwrite",
        ]
    )
    groups = build_parser().parse_args(
        ["graph-label-group-reorder", "900000002", "group-2", "group-1"]
    )
    labels = build_parser().parse_args(
        ["graph-label-reorder", "900000002", "group-2", "label-2", "label-1"]
    )
    deletion = build_parser().parse_args(
        [
            "graph-node-delete",
            "900000002",
            "node-1",
            "--confirmation-token",
            "token-delete",
        ]
    )

    assert graph.clazz == "800000002" and graph.level == 2 and graph.search == "概念"
    assert category.name == "第一单元" and category.description == "基础概念"
    assert node_create.node_type == "ability" and node_create.parent == "第一单元"
    assert node_create.model == "知识图谱"
    assert node_relation.relation == "association"
    assert node_relation.target == "句子写作"
    assert node_relation.confirmation_token == "token-relation"
    assert relation.relation_types == [0, 2] and relation.arrow_size == 7
    assert settings.show_all_relations is True
    assert settings.navigation_node_scale is False
    assert settings.confirmation_token == "token-settings"
    assert advanced_settings.topic_card is True
    assert advanced_settings.teach_target is False
    assert advanced_settings.micro_preview is True
    assert advanced_settings.confirmation_token == "token-advanced-settings"
    assert model_visibility.status == "show"
    assert model_visibility.confirmation_token == "token-model"
    assert model_classes.visible_classes == ["一班", "二班"]
    assert model_classes.confirmation_token == "token-classes"
    assert event.percent1 == 80 and event.confirmation_token == "token-event"
    assert export.format == "rdf" and export.output_path == r"D:\Exports"
    assert export.model == "知识图谱" and export.overwrite is True
    assert groups.groups == ["group-2", "group-1"]
    assert labels.group == "group-2" and labels.labels == ["label-2", "label-1"]
    assert deletion.node == "node-1" and deletion.confirmation_token == "token-delete"


@pytest.mark.asyncio
async def test_knowledge_graph_node_delete_cli_dispatches_confirmation() -> None:
    class Runtime:
        def __init__(self) -> None:
            self.call = None

        async def execute(self, action, parameters, confirmation_token=None):
            self.call = (action, parameters, confirmation_token)
            return {"status": "ok"}

    args = build_parser().parse_args(
        [
            "graph-node-delete",
            "900000002",
            "node-1",
            "--class",
            "800000002",
            "--confirmation-token",
            "token-delete",
        ]
    )
    runtime = Runtime()

    await _run_action(args, runtime)

    assert runtime.call == (
        "knowledge_graph.node.delete",
        {"course": "900000002", "node": "node-1", "clazz": "800000002"},
        "token-delete",
    )


@pytest.mark.asyncio
async def test_knowledge_graph_node_relation_cli_dispatches_confirmation() -> None:
    class Runtime:
        def __init__(self) -> None:
            self.call = None

        async def execute(self, action, parameters, confirmation_token=None):
            self.call = (action, parameters, confirmation_token)
            return {"status": "ok"}

    args = build_parser().parse_args(
        [
            "graph-node-relation-add",
            "900000002",
            "source-1",
            "successor",
            "target-1",
            "--description",
            "",
            "--class",
            "800000002",
            "--confirmation-token",
            "token-relation",
        ]
    )
    runtime = Runtime()

    await _run_action(args, runtime)

    assert runtime.call == (
        "knowledge_graph.node.relation.add",
        {
            "course": "900000002",
            "node": "source-1",
            "relation": "successor",
            "target": "target-1",
            "description": "",
            "clazz": "800000002",
        },
        "token-relation",
    )


@pytest.mark.asyncio
async def test_knowledge_graph_event_create_cli_parses_json_and_confirmation() -> None:
    class Runtime:
        def __init__(self) -> None:
            self.call = None

        async def execute(self, action, parameters, confirmation_token=None):
            self.call = (action, parameters, confirmation_token)
            return {"status": "ok"}

    args = build_parser().parse_args(
        [
            "graph-event-create",
            "900000002",
            "完成事件",
            "completion",
            "greater_than_or_equal",
            "80",
            '[{"label":"重点","execute_module":0}]',
            "--confirmation-token",
            "token-event",
        ]
    )
    runtime = Runtime()

    await _run_action(args, runtime)

    action, parameters, token = runtime.call
    assert action == "knowledge_graph.event.create"
    assert parameters["executions"] == [{"label": "重点", "execute_module": 0}]
    assert parameters["percent2"] == 100
    assert token == "token-event"


def test_class_activity_cli_parses_groups_filters_lifecycle_and_recycle() -> None:
    groups = build_parser().parse_args(
        ["class-activity-group-reorder", "900000002", "group-2", "group-1"]
    )
    listing = build_parser().parse_args(
        [
            "class-activities",
            "900000002",
            "--class",
            "800000002",
            "--group",
            "通知",
            "--status",
            "ended",
            "--activity-type",
            "45",
        ]
    )
    start = build_parser().parse_args(
        [
            "class-activity-start",
            "900000002",
            "activity-1",
            "--confirmation-token",
            "token-start",
        ]
    )
    permanent = build_parser().parse_args(
        [
            "class-activity-recycle-delete",
            "900000002",
            "activity-1",
            "activity-2",
            "--confirmation-token",
            "token-delete",
        ]
    )

    assert groups.groups == ["group-2", "group-1"]
    assert listing.clazz == "800000002" and listing.activity_type == 45
    assert listing.status == "ended" and listing.group == "通知"
    assert start.activity == "activity-1" and start.confirmation_token == "token-start"
    assert permanent.activities == ["activity-1", "activity-2"]


@pytest.mark.asyncio
async def test_class_activity_recycle_delete_cli_dispatches_confirmation() -> None:
    class Runtime:
        def __init__(self) -> None:
            self.call = None

        async def execute(self, action, parameters, confirmation_token=None):
            self.call = (action, parameters, confirmation_token)
            return {"status": "ok"}

    args = build_parser().parse_args(
        [
            "class-activity-recycle-delete",
            "900000002",
            "activity-1",
            "activity-2",
            "--class",
            "800000002",
            "--confirmation-token",
            "token-delete",
        ]
    )
    runtime = Runtime()

    await _run_action(args, runtime)

    assert runtime.call == (
        "class_activities.recycle.items.delete",
        {
            "course": "900000002",
            "activities": ["activity-1", "activity-2"],
            "clazz": "800000002",
        },
        "token-delete",
    )


def test_personal_note_cli_parses_crud_commands() -> None:
    listing = build_parser().parse_args(["notes", "--search", "考试", "--max-items", "20"])
    reading = build_parser().parse_args(["note-read", "复习计划"])
    creation = build_parser().parse_args(
        ["note-create", "复习计划", "--content", "第一周", "--content-format", "plain"]
    )
    update = build_parser().parse_args(["note-update", "复习计划", "--title", "期末复习计划"])
    deletion = build_parser().parse_args(
        ["note-delete", "期末复习计划", "--confirmation-token", "token-1"]
    )
    assert listing.search == "考试" and listing.max_items == 20
    assert reading.note == "复习计划"
    assert creation.content == "第一周"
    assert update.title == "期末复习计划"
    assert deletion.confirmation_token == "token-1"


def test_personal_inbox_cli_parses_list_read_and_state_commands() -> None:
    listing = build_parser().parse_args(
        ["inbox", "--scope", "sent", "--search", "课程", "--max-items", "30"]
    )
    reading = build_parser().parse_args(["inbox-read", "notice-1"])
    unread = build_parser().parse_args(["inbox-unread", "notice-1"])
    top = build_parser().parse_args(["inbox-top", "notice-1", "--off"])
    collect = build_parser().parse_args(["inbox-collect", "notice-1"])
    deletion = build_parser().parse_args(
        ["inbox-delete", "notice-1", "--confirmation-token", "token-1"]
    )
    assert listing.scope == "sent" and listing.search == "课程" and listing.max_items == 30
    assert reading.notice == "notice-1"
    assert unread.command == "inbox-unread"
    assert top.off is True
    assert collect.off is False
    assert deletion.confirmation_token == "token-1"


def test_personal_inbox_cli_parses_send_and_draft_commands() -> None:
    send = build_parser().parse_args(
        [
            "inbox-send",
            "测试通知",
            "仅发给本人",
            "--recipient",
            "本人",
            "--hide-read-status",
            "--permission-password",
            "permission-code",
            "--confirmation-token",
            "token-1",
        ]
    )
    drafts = build_parser().parse_args(["inbox-drafts", "--search", "测试", "--max-items", "20"])
    save = build_parser().parse_args(
        [
            "inbox-draft-save",
            "个人草稿",
            "草稿正文",
            "--recipient",
            "405017213",
        ]
    )
    delete = build_parser().parse_args(
        ["inbox-draft-delete", "个人草稿", "--confirmation-token", "token-2"]
    )
    assert send.recipients == ["本人"] and send.hide_read_status is True
    assert send.permission_password == "permission-code"
    assert send.confirmation_token == "token-1"
    assert drafts.search == "测试" and drafts.max_items == 20
    assert save.recipients == ["405017213"]
    assert delete.confirmation_token == "token-2"


def test_personal_inbox_cli_parses_folder_and_recycle_commands() -> None:
    folders = build_parser().parse_args(["inbox-folders"])
    rules = build_parser().parse_args(["inbox-folder-rules", "重要"])
    folder_notices = build_parser().parse_args(
        ["inbox-folder-notices", "重要", "--search", "课程", "--max-items", "20"]
    )
    create = build_parser().parse_args(
        [
            "inbox-folder-create",
            "重要",
            "--sender-rules-json",
            '[{"puid":"405017213","name":"本人"}]',
            "--keywords-json",
            '["课程"]',
        ]
    )
    update = build_parser().parse_args(
        ["inbox-folder-update", "重要", "--name", "待办", "--keywords-json", "[]"]
    )
    delete = build_parser().parse_args(
        ["inbox-folder-delete", "待办", "--confirmation-token", "token-3"]
    )
    reorder = build_parser().parse_args(["inbox-folder-reorder", "待办", "重要"])
    move = build_parser().parse_args(["inbox-move", "重要", "课程通知", "--source-folder", "待办"])
    recycle = build_parser().parse_args(["inbox-recycle", "--search", "旧通知"])
    restore = build_parser().parse_args(["inbox-recycle-restore", "旧通知"])
    permanent = build_parser().parse_args(
        ["inbox-recycle-delete", "旧通知", "--confirmation-token", "token-4"]
    )
    empty = build_parser().parse_args(["inbox-recycle-empty", "--confirmation-token", "token-5"])
    assert folders.command == "inbox-folders"
    assert rules.folder == "重要"
    assert folder_notices.search == "课程" and folder_notices.max_items == 20
    assert create.sender_rules_json.startswith("[")
    assert update.name == "待办" and update.keywords_json == "[]"
    assert delete.confirmation_token == "token-3"
    assert reorder.folders == ["待办", "重要"]
    assert move.destination_folder == "重要" and move.source_folder == "待办"
    assert recycle.search == "旧通知"
    assert restore.notices == ["旧通知"]
    assert permanent.confirmation_token == "token-4"
    assert empty.confirmation_token == "token-5"


def test_personal_contacts_cli_parses_read_and_team_commands() -> None:
    searching = build_parser().parse_args(
        ["contact-search", "张三", "--fid", "23080", "--max-items", "20"]
    )
    followers = build_parser().parse_args(["contacts", "--relation", "followers"])
    group_members = build_parser().parse_args(
        ["contact-group-members", "教师发展小组", "--max-items", "50"]
    )
    team_create = build_parser().parse_args(
        [
            "contact-team-create",
            "项目组",
            "张三",
            "李四",
            "--confirmation-token",
            "token-1",
        ]
    )
    team_remove = build_parser().parse_args(
        ["contact-team-remove", "项目组", "张三", "--confirmation-token", "token-2"]
    )
    assert searching.fid == "23080" and searching.max_items == 20
    assert followers.relation == "followers"
    assert group_members.group == "教师发展小组"
    assert team_create.members == ["张三", "李四"]
    assert team_create.confirmation_token == "token-1"
    assert team_remove.member == "张三"


def test_personal_group_cli_parses_group_and_folder_commands() -> None:
    listing = build_parser().parse_args(["groups", "--folder", "教学", "--search", "写作"])
    reading = build_parser().parse_args(["group-read", "写作小组"])
    creation = build_parser().parse_args(
        [
            "group-create",
            "课程小组",
            "--description",
            "课程交流",
            "--folder",
            "教学",
            "--confirmation-token",
            "token-create",
        ]
    )
    update = build_parser().parse_args(
        [
            "group-update",
            "课程小组",
            "--name",
            "写作课程小组",
            "--confirmation-token",
            "token-update",
        ]
    )
    logo_update = build_parser().parse_args(
        [
            "group-logo-update",
            "课程小组",
            r"D:\Images\logo.png",
            "--confirmation-token",
            "token-logo",
        ]
    )
    modules = build_parser().parse_args(["group-modules", "课程小组"])
    modules_update = build_parser().parse_args(
        [
            "group-modules-update",
            "课程小组",
            "2",
            "3",
            "--confirmation-token",
            "token-modules",
        ]
    )
    levels = build_parser().parse_args(["group-levels", "课程小组"])
    level_series = build_parser().parse_args(
        [
            "group-level-series",
            "课程小组",
            "default",
            "--confirmation-token",
            "token-level-series",
        ]
    )
    custom_levels = build_parser().parse_args(
        [
            "group-levels-custom",
            "课程小组",
            '[{"level":1,"title":"起步","growth_value":5}]',
            "--confirmation-token",
            "token-custom-levels",
        ]
    )
    growth_rules = build_parser().parse_args(["group-growth-rules", "课程小组"])
    growth_rule_series = build_parser().parse_args(
        [
            "group-growth-rule-series",
            "课程小组",
            "default",
            "--confirmation-token",
            "token-growth-series",
        ]
    )
    growth_rules_update = build_parser().parse_args(
        [
            "group-growth-rules-update",
            "课程小组",
            "--set",
            "2=6",
            "--confirmation-token",
            "token-growth",
        ]
    )
    settings_update = build_parser().parse_args(
        [
            "group-settings-update",
            "课程小组",
            "--set",
            "isCheck=false",
            "--set",
            "showManager=true",
            "--confirmation-token",
            "token-settings",
        ]
    )
    speaking_rules = build_parser().parse_args(
        [
            "group-speaking-rules-update",
            "课程小组",
            "--set",
            "leastTopicWord=30",
            "--attachment-rules",
            '{"image":true}',
            "--confirmation-token",
            "token-speaking",
        ]
    )
    notice_send = build_parser().parse_args(
        [
            "group-notice-send",
            "课程小组",
            "开课通知",
            "周一开始上课。",
            "--confirmation-token",
            "token-notice",
        ]
    )
    review_reminders = build_parser().parse_args(["group-review-reminders", "课程小组"])
    review_reminder_create = build_parser().parse_args(
        [
            "group-review-reminder-create",
            "课程小组",
            "23:58",
            "23:59",
            "星期日",
            "--puid",
            "405017213",
            "--confirmation-token",
            "token-review-create",
        ]
    )
    review_reminder_update = build_parser().parse_args(
        [
            "group-review-reminder-update",
            "课程小组",
            "reminder-1",
            "--start-time",
            "23:57",
            "--week",
            "星期六",
            "--confirmation-token",
            "token-review-update",
        ]
    )
    review_reminders_delete = build_parser().parse_args(
        [
            "group-review-reminders-delete",
            "课程小组",
            "reminder-1",
            "--confirmation-token",
            "token-review-delete",
        ]
    )
    top = build_parser().parse_args(["group-top", "课程小组", "--off"])
    move = build_parser().parse_args(["group-move", "课程小组", "教学"])
    quit_group = build_parser().parse_args(
        ["group-quit", "课程小组", "--confirmation-token", "token-quit"]
    )
    dismiss_group = build_parser().parse_args(
        ["group-dismiss", "课程小组", "--confirmation-token", "token-dismiss"]
    )
    members = build_parser().parse_args(["group-members", "课程小组", "--search", "张三"])
    bulk_import_status = build_parser().parse_args(["group-member-bulk-import-status", "课程小组"])
    bulk_import_template = build_parser().parse_args(
        ["group-member-bulk-import-template", "课程小组", r"D:\Temp\template.xlsx"]
    )
    bulk_import = build_parser().parse_args(
        [
            "group-members-bulk-import",
            "课程小组",
            r"D:\Temp\members.xlsx",
            "--confirmation-token",
            "token-bulk-import",
        ]
    )
    member_read = build_parser().parse_args(["group-member-read", "课程小组", "张三"])
    member_permissions = build_parser().parse_args(["group-member-permissions", "课程小组", "张三"])
    member_permissions_update = build_parser().parse_args(
        [
            "group-member-permissions-update",
            "课程小组",
            "张三",
            "--set",
            "showBarcode=true",
            "--confirmation-token",
            "token-member-permissions",
        ]
    )
    member_sources = build_parser().parse_args(["group-member-sources", "课程小组"])
    member_candidates = build_parser().parse_args(
        [
            "group-member-candidates",
            "课程小组",
            "circle",
            "71506605",
            "--search",
            "张三",
        ]
    )
    members_add = build_parser().parse_args(
        [
            "group-members-add",
            "课程小组",
            "101",
            "102",
            "--confirmation-token",
            "token-add-members",
        ]
    )
    member_manager = build_parser().parse_args(
        [
            "group-member-manager",
            "课程小组",
            "张三",
            "--off",
            "--confirmation-token",
            "token-manager",
        ]
    )
    member_remove = build_parser().parse_args(
        [
            "group-member-remove",
            "课程小组",
            "张三",
            "--confirmation-token",
            "token-remove-member",
        ]
    )
    group_transfer = build_parser().parse_args(
        [
            "group-transfer",
            "课程小组",
            "张三",
            "--confirmation-token",
            "token-transfer",
        ]
    )
    clear_external = build_parser().parse_args(
        [
            "group-members-clear-external",
            "课程小组",
            "--confirmation-token",
            "token-clear",
        ]
    )
    folders = build_parser().parse_args(
        ["group-folders", "--parent-folder", "教学", "--search", "写作"]
    )
    tree = build_parser().parse_args(["group-folder-tree"])
    folder_create = build_parser().parse_args(
        ["group-folder-create", "写作", "--parent-folder", "教学"]
    )
    folder_rename = build_parser().parse_args(["group-folder-rename", "写作", "论文写作"])
    folder_move = build_parser().parse_args(["group-folder-move", "论文写作", "root"])
    folder_top = build_parser().parse_args(["group-folder-top", "论文写作", "--off"])
    folder_delete = build_parser().parse_args(
        ["group-folder-delete", "论文写作", "--confirmation-token", "token-folder"]
    )
    topics = build_parser().parse_args(
        ["group-topics", "课程小组", "--folder", "讨论", "--search", "写作"]
    )
    topic_read = build_parser().parse_args(
        [
            "group-topic-read",
            "课程小组",
            "如何修改论文",
            "--order",
            "1",
            "--reply-search",
            "结构",
        ]
    )
    topic_create = build_parser().parse_args(
        [
            "group-topic-create",
            "课程小组",
            "如何修改论文",
            "先判断问题。",
            "--anonymous",
            "--confirmation-token",
            "token-topic",
        ]
    )
    topic_delete = build_parser().parse_args(
        [
            "group-topic-delete",
            "课程小组",
            "如何修改论文",
            "--confirmation-token",
            "token-topic-delete",
        ]
    )
    topic_choice = build_parser().parse_args(
        [
            "group-topic-choice",
            "课程小组",
            "如何修改论文",
            "--off",
            "--confirmation-token",
            "token-choice",
        ]
    )
    topic_praise = build_parser().parse_args(
        ["group-topic-praise", "课程小组", "如何修改论文", "--confirmation-token", "token-praise"]
    )
    topics_score = build_parser().parse_args(
        [
            "group-topics-score",
            "课程小组",
            "85",
            "话题一",
            "话题二",
            "--confirmation-token",
            "token-score",
        ]
    )
    topics_move = build_parser().parse_args(
        ["group-topics-move", "课程小组", "讨论", "话题一", "话题二"]
    )
    topics_delete = build_parser().parse_args(
        [
            "group-topics-delete",
            "课程小组",
            "话题一",
            "话题二",
            "--confirmation-token",
            "token-batch-delete",
        ]
    )
    topic_update = build_parser().parse_args(
        [
            "group-topic-update",
            "课程小组",
            "如何修改论文",
            "--title",
            "如何修改课程论文",
            "--confirmation-token",
            "token-topic-update",
        ]
    )
    topic_reply = build_parser().parse_args(
        [
            "group-topic-reply",
            "课程小组",
            "如何修改论文",
            "先看论点。",
            "--reply-to",
            "先判断问题",
            "--confirmation-token",
            "token-reply",
        ]
    )
    topic_reply_delete = build_parser().parse_args(
        [
            "group-topic-reply-delete",
            "课程小组",
            "如何修改论文",
            "先看论点",
            "--confirmation-token",
            "token-reply-delete",
        ]
    )
    topic_reply_update = build_parser().parse_args(
        [
            "group-topic-reply-update",
            "课程小组",
            "如何修改论文",
            "先看论点",
            "先看中心论点。",
            "--confirmation-token",
            "token-reply-update",
        ]
    )
    topic_folders = build_parser().parse_args(["group-topic-folder-tree", "课程小组"])
    topic_top = build_parser().parse_args(["group-topic-top", "课程小组", "如何修改论文", "--off"])
    topic_move = build_parser().parse_args(["group-topic-move", "课程小组", "如何修改论文", "讨论"])
    topic_folder_create = build_parser().parse_args(
        ["group-topic-folder-create", "课程小组", "论文", "--parent-folder", "讨论"]
    )
    topic_folder_rename = build_parser().parse_args(
        ["group-topic-folder-rename", "课程小组", "论文", "课程论文"]
    )
    topic_folder_move = build_parser().parse_args(
        ["group-topic-folder-move", "课程小组", "课程论文", "root"]
    )
    topic_folder_delete = build_parser().parse_args(
        [
            "group-topic-folder-delete",
            "课程小组",
            "课程论文",
            "--confirmation-token",
            "token-topic-folder",
        ]
    )
    topic_folders_move = build_parser().parse_args(
        ["group-topic-folders-move", "课程小组", "root", "论文", "读书会"]
    )
    topic_folders_delete = build_parser().parse_args(
        [
            "group-topic-folders-delete",
            "课程小组",
            "论文",
            "读书会",
            "--confirmation-token",
            "token-folders-delete",
        ]
    )
    topic_drafts = build_parser().parse_args(["group-topic-drafts", "课程小组", "--search", "论文"])
    topic_draft_read = build_parser().parse_args(
        ["group-topic-draft-read", "课程小组", "draft-uuid"]
    )
    topic_draft_save = build_parser().parse_args(
        [
            "group-topic-draft-save",
            "课程小组",
            "论文讨论",
            "先判断问题。",
            "--draft",
            "draft-uuid",
            "--folder",
            "讨论",
        ]
    )
    topic_draft_publish = build_parser().parse_args(
        [
            "group-topic-draft-publish",
            "课程小组",
            "draft-uuid",
            "--confirmation-token",
            "token-draft",
        ]
    )

    assert listing.folder == "教学" and listing.search == "写作"
    assert reading.group == "写作小组"
    assert creation.description == "课程交流" and creation.confirmation_token == "token-create"
    assert update.name == "写作课程小组" and update.confirmation_token == "token-update"
    assert logo_update.file == r"D:\Images\logo.png"
    assert logo_update.confirmation_token == "token-logo"
    assert modules.group == "课程小组"
    assert modules_update.enabled_type_ids == ["2", "3"]
    assert modules_update.confirmation_token == "token-modules"
    assert levels.group == "课程小组"
    assert level_series.series == "default"
    assert level_series.confirmation_token == "token-level-series"
    assert custom_levels.levels_json.startswith("[")
    assert growth_rules.group == "课程小组"
    assert growth_rule_series.series == "default"
    assert growth_rule_series.confirmation_token == "token-growth-series"
    assert growth_rules_update.growth_rule_changes == ["2=6"]
    assert settings_update.setting_changes == ["isCheck=false", "showManager=true"]
    assert settings_update.confirmation_token == "token-settings"
    assert speaking_rules.rule_changes == ["leastTopicWord=30"]
    assert speaking_rules.attachment_rules == '{"image":true}'
    assert notice_send.title == "开课通知"
    assert notice_send.content == "周一开始上课。"
    assert notice_send.confirmation_token == "token-notice"
    assert review_reminders.group == "课程小组"
    assert review_reminder_create.weeks == ["星期日"]
    assert review_reminder_create.puids == ["405017213"]
    assert review_reminder_create.confirmation_token == "token-review-create"
    assert review_reminder_update.start_time == "23:57"
    assert review_reminder_update.weeks == ["星期六"]
    assert review_reminders_delete.reminders == ["reminder-1"]
    assert review_reminders_delete.confirmation_token == "token-review-delete"
    assert top.off is True
    assert move.destination_folder == "教学"
    assert quit_group.confirmation_token == "token-quit"
    assert dismiss_group.confirmation_token == "token-dismiss"
    assert members.search == "张三"
    assert bulk_import_status.group == "课程小组"
    assert bulk_import_template.output_path == r"D:\Temp\template.xlsx"
    assert bulk_import.file == r"D:\Temp\members.xlsx"
    assert bulk_import.confirmation_token == "token-bulk-import"
    assert member_read.member == "张三"
    assert member_permissions.member == "张三"
    assert member_permissions_update.permission_changes == ["showBarcode=true"]
    assert member_permissions_update.confirmation_token == "token-member-permissions"
    assert member_sources.group == "课程小组"
    assert member_candidates.source_type == "circle" and member_candidates.source == "71506605"
    assert members_add.puids == ["101", "102"]
    assert members_add.confirmation_token == "token-add-members"
    assert member_manager.off is True and member_manager.confirmation_token == "token-manager"
    assert member_remove.confirmation_token == "token-remove-member"
    assert group_transfer.confirmation_token == "token-transfer"
    assert clear_external.confirmation_token == "token-clear"
    assert folders.parent_folder == "教学" and folders.search == "写作"
    assert tree.command == "group-folder-tree"
    assert folder_create.parent_folder == "教学"
    assert folder_rename.name == "论文写作"
    assert folder_move.destination_folder == "root"
    assert folder_top.off is True
    assert folder_delete.confirmation_token == "token-folder"
    assert topics.folder == "讨论" and topics.search == "写作"
    assert topic_read.order == 1 and topic_read.reply_search == "结构"
    assert topic_create.anonymous is True and topic_create.confirmation_token == "token-topic"
    assert topic_delete.confirmation_token == "token-topic-delete"
    assert topic_choice.off is True and topic_choice.confirmation_token == "token-choice"
    assert topic_praise.off is False and topic_praise.confirmation_token == "token-praise"
    assert topics_score.score == 85 and topics_score.topics == ["话题一", "话题二"]
    assert topics_score.confirmation_token == "token-score"
    assert topics_move.destination_folder == "讨论" and topics_move.topics == ["话题一", "话题二"]
    assert topics_delete.topics == ["话题一", "话题二"]
    assert topics_delete.confirmation_token == "token-batch-delete"
    assert topic_update.title == "如何修改课程论文"
    assert topic_update.confirmation_token == "token-topic-update"
    assert topic_reply.reply_to == "先判断问题" and topic_reply.confirmation_token == "token-reply"
    assert topic_reply_delete.confirmation_token == "token-reply-delete"
    assert topic_reply_update.content == "先看中心论点。"
    assert topic_reply_update.confirmation_token == "token-reply-update"
    assert topic_folders.group == "课程小组"
    assert topic_top.off is True and topic_top.topic == "如何修改论文"
    assert topic_move.destination_folder == "讨论"
    assert topic_folder_create.parent_folder == "讨论"
    assert topic_folder_rename.name == "课程论文"
    assert topic_folder_move.destination_folder == "root"
    assert topic_folder_delete.confirmation_token == "token-topic-folder"
    assert topic_folders_move.destination_folder == "root"
    assert topic_folders_move.folders == ["论文", "读书会"]
    assert topic_folders_delete.folders == ["论文", "读书会"]
    assert topic_folders_delete.confirmation_token == "token-folders-delete"
    assert topic_drafts.search == "论文"
    assert topic_draft_read.draft == "draft-uuid"
    assert topic_draft_save.draft == "draft-uuid" and topic_draft_save.folder == "讨论"
    assert topic_draft_publish.confirmation_token == "token-draft"


def test_teacher_permission_update_cli_parses_repeatable_changes() -> None:
    args = build_parser().parse_args(
        [
            "teacher-permissions-update",
            "900000002",
            "2025800218",
            "--set",
            "homework=true",
            "--set",
            "allowedChapterOpenStatus=2",
        ]
    )
    assert args.permission_changes == ["homework=true", "allowedChapterOpenStatus=2"]
    assert _parse_permission_changes(args.permission_changes) == {
        "homework": True,
        "allowedChapterOpenStatus": 2,
    }


def test_chapter_management_cli_parses_targets_and_confirmation() -> None:
    create = build_parser().parse_args(
        ["chapter-create", "900000002", "Learning Guide", "--parent", "Unit 1"]
    )
    move = build_parser().parse_args(
        [
            "chapter-move",
            "900000002",
            "Learning Guide",
            "--relative-to",
            "Overview",
            "--position",
            "before",
        ]
    )
    status = build_parser().parse_args(
        [
            "chapter-status",
            "900000002",
            "time",
            "Learning Guide",
            "--target-class",
            "示例一班",
            "--begin",
            "2026.09.01 08:00",
            "--end",
            "2026.09.30 23:59",
            "--confirmation-token",
            "token-1",
        ]
    )
    assert create.parent == "Unit 1"
    assert move.relative_to == "Overview"
    assert move.position == "before"
    assert status.chapters == ["Learning Guide"]
    assert status.classes == ["示例一班"]
    assert status.confirmation_token == "token-1"

    card_create = build_parser().parse_args(
        [
            "chapter-card-create",
            "900000002",
            "Learning Guide",
            "Goals",
            "--content",
            "Read this page.",
        ]
    )
    card_update = build_parser().parse_args(
        [
            "chapter-card-update",
            "900000002",
            "Learning Guide",
            "Goals",
            "--title",
            "Learning goals",
        ]
    )
    card_delete = build_parser().parse_args(
        [
            "chapter-card-delete",
            "900000002",
            "Learning Guide",
            "Goals",
            "--confirmation-token",
            "token-2",
        ]
    )
    assert card_create.content == "Read this page."
    assert card_update.title == "Learning goals"
    assert card_delete.confirmation_token == "token-2"


def test_resource_management_cli_parses_http_operations_and_confirmations() -> None:
    download_items = build_parser().parse_args(
        [
            "resource-download-items",
            "900000002",
            r"D:\Downloads\materials.zip",
            "Unit 1",
            "Guide.pdf",
            "--class",
            "800000002",
        ]
    )
    upload = build_parser().parse_args(
        [
            "resource-upload",
            "900000002",
            r"D:\Materials\guide.pdf",
            "--parent",
            "Unit 1",
            "--confirmation-token",
            "token-1",
        ]
    )
    permission = build_parser().parse_args(
        [
            "resource-download-permission",
            "900000002",
            "deny",
            "Guide.pdf",
            "Slides.pptx",
            "--confirmation-token",
            "token-2",
        ]
    )
    visibility = build_parser().parse_args(
        [
            "resource-visibility-update",
            "900000002",
            "Unit 1",
            "selected_classes",
            "--visible-class",
            "示例一班",
            "--no-all-teachers",
            "--confirmation-token",
            "token-3",
        ]
    )
    importing = build_parser().parse_args(
        [
            "resource-import",
            "900000002",
            "254641935",
            "1200632090",
            "--destination",
            "Archive",
        ]
    )
    assert download_items.resources == ["Unit 1", "Guide.pdf"]
    assert download_items.output_path == r"D:\Downloads\materials.zip"
    assert download_items.clazz == "800000002"
    assert upload.file_path == r"D:\Materials\guide.pdf"
    assert upload.parent == "Unit 1"
    assert upload.confirmation_token == "token-1"
    assert permission.permission == "deny"
    assert permission.resources == ["Guide.pdf", "Slides.pptx"]
    assert visibility.classes == ["示例一班"]
    assert visibility.all_teachers is False
    assert importing.source_course == "254641935"
    assert importing.destination == "Archive"

    top = build_parser().parse_args(["resource-top", "900000002", "Guide.pdf", "untop"])
    copying = build_parser().parse_args(
        [
            "resource-copy",
            "900000002",
            "Guide.pdf",
            "--confirmation-token",
            "token-copy",
        ]
    )
    assert top.status == "untop"
    assert copying.resource == "Guide.pdf"
    assert copying.confirmation_token == "token-copy"
    copy_to_cloud = build_parser().parse_args(
        [
            "resource-copy-to-cloud",
            "900000002",
            "Guide.pdf",
            "--destination",
            "Archive",
            "--confirmation-token",
            "token-cloud-copy",
        ]
    )
    assert copy_to_cloud.destination == "Archive"
    assert copy_to_cloud.confirmation_token == "token-cloud-copy"
    cloud_sources = build_parser().parse_args(
        [
            "resource-cloud-sources",
            "900000002",
            "--path",
            "/0/1170626147074138112",
            "--search",
            "Guide",
        ]
    )
    cloud_import = build_parser().parse_args(
        [
            "resource-cloud-import",
            "900000002",
            "Guide.pdf",
            "Slides.pptx",
            "--destination",
            "Unit 1",
            "--confirmation-token",
            "token-cloud-import",
        ]
    )
    assert cloud_sources.path == "/0/1170626147074138112"
    assert cloud_sources.search == "Guide"
    assert cloud_import.resources == ["Guide.pdf", "Slides.pptx"]
    assert cloud_import.destination == "Unit 1"
    assert cloud_import.confirmation_token == "token-cloud-import"
    cloud_folder_import = build_parser().parse_args(
        [
            "resource-cloud-folder-import",
            "900000002",
            "Review",
            "--destination",
            "Unit 1",
            "--confirmation-token",
            "token-cloud-folder-import",
        ]
    )
    assert cloud_folder_import.resource == "Review"
    assert cloud_folder_import.destination == "Unit 1"
    assert cloud_folder_import.confirmation_token == "token-cloud-folder-import"

    labels = build_parser().parse_args(
        ["resource-labels", "900000002", "Guide.pdf", "--search", "Review"]
    )
    label_create = build_parser().parse_args(
        ["resource-label-create", "900000002", "Guide.pdf", "Review"]
    )
    label_rename = build_parser().parse_args(
        [
            "resource-label-rename",
            "900000002",
            "Guide.pdf",
            "Review",
            "Final review",
        ]
    )
    label_delete = build_parser().parse_args(
        [
            "resource-label-delete",
            "900000002",
            "Guide.pdf",
            "Review",
            "--confirmation-token",
            "token-label-delete",
        ]
    )
    labels_update = build_parser().parse_args(
        [
            "resource-labels-update",
            "900000002",
            "Guide.pdf",
            "Slides.pptx",
            "--label",
            "Review",
            "--label",
            "Final",
            "--confirmation-token",
            "token-labels-update",
        ]
    )
    labels_clear = build_parser().parse_args(["resource-labels-update", "900000002", "Guide.pdf"])
    assert labels.search == "Review"
    assert label_create.name == "Review"
    assert label_rename.label == "Review"
    assert label_rename.name == "Final review"
    assert label_delete.confirmation_token == "token-label-delete"
    assert labels_update.resources == ["Guide.pdf", "Slides.pptx"]
    assert labels_update.labels == ["Review", "Final"]
    assert labels_update.confirmation_token == "token-labels-update"
    assert labels_clear.labels == []

    cloud_list = build_parser().parse_args(
        ["cloud-list", "--search", "Guide.pdf", "--page-size", "50"]
    )
    cloud_delete = build_parser().parse_args(
        ["cloud-delete", "1301297178171625472", "--confirmation-token", "token-4"]
    )
    assert cloud_list.search == "Guide.pdf"
    assert cloud_list.page_size == 50
    assert cloud_delete.resources == ["1301297178171625472"]
    assert cloud_delete.confirmation_token == "token-4"

    cloud_folder = build_parser().parse_args(
        [
            "cloud-folder-create",
            "Review",
            "--parent",
            "Unit 1",
            "--shared",
            "--confirmation-token",
            "token-5",
        ]
    )
    cloud_rename = build_parser().parse_args(["cloud-rename", "Guide.pdf", "Handout"])
    cloud_move = build_parser().parse_args(["cloud-move", "Archive", "Guide.pdf", "Slides.pptx"])
    cloud_top = build_parser().parse_args(["cloud-top", "Guide.pdf", "top"])
    cloud_download = build_parser().parse_args(
        ["cloud-download", r"D:\Downloads\materials.zip", "Unit 1", "Review"]
    )
    cloud_recycle = build_parser().parse_args(["cloud-recycle", "--page-size", "25"])
    cloud_restore = build_parser().parse_args(
        [
            "cloud-restore",
            "Guide.pdf",
            "--conflict-policy",
            "replace",
            "--confirmation-token",
            "token-6",
        ]
    )
    cloud_permanent_delete = build_parser().parse_args(
        ["cloud-recycle-delete", "Guide.pdf", "--confirmation-token", "token-7"]
    )
    cloud_empty = build_parser().parse_args(
        ["cloud-recycle-empty", "--confirmation-token", "token-8"]
    )
    assert cloud_folder.parent == "Unit 1"
    assert cloud_folder.shared is True
    assert cloud_rename.name == "Handout"
    assert cloud_move.resources == ["Guide.pdf", "Slides.pptx"]
    assert cloud_top.status == "top"
    assert cloud_download.output_path == r"D:\Downloads\materials.zip"
    assert cloud_download.resources == ["Unit 1", "Review"]
    assert cloud_recycle.page_size == 25
    assert cloud_restore.conflict_policy == "replace"
    assert cloud_permanent_delete.confirmation_token == "token-7"
    assert cloud_empty.confirmation_token == "token-8"


def test_exam_question_cli_parses_core_question_fields() -> None:
    args = build_parser().parse_args(
        [
            "exam-question-add",
            "900000002",
            "Unit 1 Test",
            "single_choice",
            "Which is correct?",
            "--option",
            "Alpha",
            "--option",
            "Beta",
            "--correct-answer",
            "B",
            "--score",
            "5",
        ]
    )
    assert args.options == ["Alpha", "Beta"]
    assert args.correct_answer == "B"
    assert args.score == 5

    delete = build_parser().parse_args(["exam-question-delete", "900000002", "Unit 1 Test", "3"])
    assert delete.paper == "Unit 1 Test"
    assert delete.question == "3"

    settings = build_parser().parse_args(
        [
            "exam-paper-settings-update",
            "900000002",
            "Unit 1 Test",
            "--difficulty",
            "hard",
            "--numbering",
            "by_type",
        ]
    )
    assert settings.difficulty == "hard"
    assert settings.numbering == "by_type"

    move = build_parser().parse_args(["exam-question-move", "900000002", "Unit 1 Test", "3", "1"])
    assert move.question == "3"
    assert move.target_position == 1

    type_update = build_parser().parse_args(
        [
            "exam-question-type-update",
            "900000002",
            "Unit 1 Test",
            "single_choice",
            "--description",
            "Choose one.",
            "--total-score",
            "20",
        ]
    )
    assert type_update.description == "Choose one."
    assert type_update.total_score == 20

    type_delete = build_parser().parse_args(
        ["exam-question-type-delete", "900000002", "Unit 1 Test", "true_false"]
    )
    assert type_delete.question_type == "true_false"


def test_question_bank_management_cli_parses_arguments() -> None:
    create = build_parser().parse_args(
        [
            "qbank-question-add",
            "900000002",
            "single_choice",
            "Which is correct?",
            "--directory",
            "Unit 1",
            "--option",
            "Alpha",
            "--option",
            "Beta",
            "--correct-answer",
            "B",
        ]
    )
    assert create.directory == "Unit 1"
    assert create.options == ["Alpha", "Beta"]
    assert create.correct_answer == "B"

    move = build_parser().parse_args(["qbank-question-move", "900000002", "question-1", "Review"])
    assert move.target_directory == "Review"

    question_reorder = build_parser().parse_args(
        ["qbank-question-reorder", "900000002", "question-1", "3"]
    )
    assert question_reorder.target_position == 3

    folder = build_parser().parse_args(
        ["qbank-folder-create", "900000002", "Review", "--parent-directory", "Unit 1"]
    )
    assert folder.name == "Review"
    assert folder.parent_directory == "Unit 1"

    folder_reorder = build_parser().parse_args(["qbank-folder-reorder", "900000002", "Review", "2"])
    assert folder_reorder.target_position == 2

    permissions = build_parser().parse_args(
        [
            "qbank-folder-permissions-update",
            "900000002",
            "Review",
            "--self-practice",
            "false",
            "--share-scope",
            "selected_teachers",
            "--teacher",
            "张三",
            "--teacher",
            "485781386",
        ]
    )
    assert permissions.allow_student_self_practice == "false"
    assert permissions.share_scope == "selected_teachers"
    assert permissions.selected_teachers == ["张三", "485781386"]


def test_question_bank_smart_import_cli_parses_sources() -> None:
    preview = build_parser().parse_args(
        ["qbank-smart-preview", "900000002", "--file", r"D:\Materials\unit1.docx"]
    )
    assert preview.file_path == r"D:\Materials\unit1.docx"
    assert preview.source_text is None

    commit = build_parser().parse_args(
        [
            "qbank-smart-import",
            "900000002",
            "--text",
            "1. Which is correct?\nA. First\nB. Second\n答案：B",
            "--target-directory",
            "Review",
        ]
    )
    assert commit.source_text.startswith("1. Which")
    assert commit.target_directory == "Review"


def test_question_bank_cross_course_cli_parses_arguments() -> None:
    listing = build_parser().parse_args(
        [
            "qbank-source-questions",
            "900000002",
            "254641935",
            "--search",
            "Process analysis",
        ]
    )
    assert listing.source_course == "254641935"
    assert listing.search == "Process analysis"

    importing = build_parser().parse_args(
        [
            "qbank-import-from-course",
            "900000002",
            "254641935",
            "question-1",
            "question-2",
            "--target-directory",
            "Review",
        ]
    )
    assert importing.questions == ["question-1", "question-2"]
    assert importing.target_directory == "Review"

    difficulty = build_parser().parse_args(
        [
            "qbank-questions-difficulty",
            "900000002",
            "0.8",
            "question-1",
            "question-2",
        ]
    )
    assert difficulty.difficulty == "0.8"
    assert difficulty.questions == ["question-1", "question-2"]

    qtype_add = build_parser().parse_args(
        ["qbank-question-type-add", "900000002", "术语解释", "short_answer"]
    )
    qtype_move = build_parser().parse_args(
        ["qbank-question-type-move", "900000002", "术语解释", "3"]
    )
    qtype_delete = build_parser().parse_args(
        ["qbank-question-type-delete", "900000002", "术语解释"]
    )
    assert qtype_add.base_type == "short_answer"
    assert qtype_move.target_position == 3
    assert qtype_delete.question_type == "术语解释"

    exporting = build_parser().parse_args(
        [
            "qbank-export",
            "900000002",
            "excel",
            "--question",
            "question-1",
            "--question",
            "question-2",
            "--output",
            r"D:\Exports",
            "--include-correct-rate",
        ]
    )
    assert exporting.questions == ["question-1", "question-2"]
    assert exporting.output_path == r"D:\Exports"
    assert exporting.include_correct_rate is True

    downloading = build_parser().parse_args(
        ["qbank-download", "900000002", "record-1", "--output", r"D:\Exports\q.xlsx"]
    )
    assert downloading.record == "record-1"
    assert downloading.output_path == r"D:\Exports\q.xlsx"

    label_create = build_parser().parse_args(
        ["qbank-label-create", "900000002", "求职信", "--parent-label", "写作"]
    )
    labels_set = build_parser().parse_args(
        [
            "qbank-question-labels-set",
            "900000002",
            "question-1",
            "question-2",
            "--label",
            "求职信",
            "--label",
            "precise writing",
            "--mode",
            "add",
            "--sync-references",
        ]
    )
    assert label_create.parent_label == "写作"
    assert labels_set.questions == ["question-1", "question-2"]
    assert labels_set.labels == ["求职信", "precise writing"]
    assert labels_set.mode == "add"
    assert labels_set.sync_references is True

    topic_create = build_parser().parse_args(
        [
            "qbank-topic-create",
            "900000002",
            "Topic Sentence",
            "--kind",
            "knowledge_point",
            "--parent-topic",
            "Paragraph Writing",
        ]
    )
    topics_set = build_parser().parse_args(
        [
            "qbank-question-topics-set",
            "900000002",
            "question-1",
            "question-2",
            "--topic",
            "Topic Sentence",
            "--mode",
            "remove",
            "--sync-references",
        ]
    )
    assert topic_create.kind == "knowledge_point"
    assert topic_create.parent_topic == "Paragraph Writing"
    assert topics_set.questions == ["question-1", "question-2"]
    assert topics_set.topics == ["Topic Sentence"]
    assert topics_set.mode == "remove"
    assert topics_set.sync_references is True

    recycle = build_parser().parse_args(
        ["qbank-recycle", "900000002", "--search", "Unit 1", "--order", "asc"]
    )
    lock = build_parser().parse_args(
        [
            "qbank-lock",
            "900000002",
            "--question",
            "question-1",
            "--directory",
            "Unit 1",
            "--directory-id",
            "253795142",
        ]
    )
    permanent_delete = build_parser().parse_args(
        ["qbank-recycle-delete", "900000002", "question-1", "Unit 1"]
    )
    assert recycle.search == "Unit 1"
    assert recycle.order == "asc"
    assert lock.questions == ["question-1"]
    assert lock.directories == ["Unit 1"]
    assert lock.directory_id == "253795142"
    assert permanent_delete.items == ["question-1", "Unit 1"]

    type_update = build_parser().parse_args(
        [
            "qbank-questions-type",
            "900000002",
            "简答题",
            "question-1",
            "question-2",
            "--directory-id",
            "253795142",
        ]
    )
    copy_items = build_parser().parse_args(
        [
            "qbank-copy",
            "900000002",
            "Review",
            "--question",
            "question-1",
            "--directory",
            "Unit 1",
            "--source-directory-id",
            "253795142",
        ]
    )
    assert type_update.question_type == "简答题"
    assert type_update.questions == ["question-1", "question-2"]
    assert copy_items.target_directory == "Review"
    assert copy_items.questions == ["question-1"]
    assert copy_items.directories == ["Unit 1"]


def test_course_asset_cli_parses_courseware_and_teaching_plan_operations() -> None:
    listing = build_parser().parse_args(
        ["course-assets", "900000002", "courseware", "--folder", "Unit 1"]
    )
    folder = build_parser().parse_args(
        [
            "course-asset-folder-create",
            "900000002",
            "teaching_plan",
            "Review",
            "--confirmation-token",
            "token-folder",
        ]
    )
    moving = build_parser().parse_args(
        [
            "course-asset-move",
            "900000002",
            "courseware",
            "Archive",
            "Slides",
            "Guide",
        ]
    )
    cloud_import = build_parser().parse_args(
        [
            "course-asset-cloud-import",
            "900000002",
            "courseware",
            "1173876256092155904",
            "Week 3.pdf",
            "--destination",
            "Unit 1",
            "--confirmation-token",
            "token-import",
        ]
    )
    download = build_parser().parse_args(
        [
            "course-asset-download",
            "900000002",
            "courseware",
            "Slides",
            r"D:\Downloads\Slides.pptx",
        ]
    )
    recycle_delete = build_parser().parse_args(
        [
            "course-asset-recycle-delete",
            "900000002",
            "teaching_plan",
            "Old plan",
            "--confirmation-token",
            "token-delete",
        ]
    )
    assert listing.kind == "courseware"
    assert listing.folder == "Unit 1"
    assert folder.kind == "teaching_plan"
    assert folder.confirmation_token == "token-folder"
    assert moving.destination == "Archive"
    assert moving.assets == ["Slides", "Guide"]
    assert cloud_import.resources == ["1173876256092155904", "Week 3.pdf"]
    assert cloud_import.destination == "Unit 1"
    assert cloud_import.confirmation_token == "token-import"
    assert download.output_path == r"D:\Downloads\Slides.pptx"
    assert recycle_delete.assets == ["Old plan"]
    assert recycle_delete.confirmation_token == "token-delete"


def test_personal_group_label_reason_and_recycle_cli() -> None:
    labels = build_parser().parse_args(["group-labels", "课程小组"])
    label_create = build_parser().parse_args(["group-label-create", "课程小组", "重点"])
    label_rename = build_parser().parse_args(["group-label-rename", "课程小组", "重点", "精华"])
    label_reorder = build_parser().parse_args(["group-labels-reorder", "课程小组", "精华", "复习"])
    label_delete = build_parser().parse_args(
        [
            "group-labels-delete",
            "课程小组",
            "精华",
            "--confirmation-token",
            "token-label",
        ]
    )
    reasons = build_parser().parse_args(["group-deletion-reasons", "课程小组"])
    reason_create = build_parser().parse_args(
        ["group-deletion-reason-create", "课程小组", "内容重复"]
    )
    reason_delete = build_parser().parse_args(
        [
            "group-deletion-reasons-delete",
            "课程小组",
            "内容重复",
            "--confirmation-token",
            "token-reason",
        ]
    )
    recycle = build_parser().parse_args(["group-recycle", "课程小组"])
    restore = build_parser().parse_args(["group-recycle-restore", "课程小组", "10", "11"])
    permanent = build_parser().parse_args(
        [
            "group-recycle-delete",
            "课程小组",
            "10",
            "--confirmation-token",
            "token-recycle",
        ]
    )
    empty = build_parser().parse_args(
        ["group-recycle-empty", "课程小组", "--confirmation-token", "token-empty"]
    )
    assert labels.group == "课程小组"
    assert label_create.name == "重点"
    assert label_rename.label == "重点" and label_rename.name == "精华"
    assert label_reorder.labels == ["精华", "复习"]
    assert label_delete.confirmation_token == "token-label"
    assert reasons.group == "课程小组"
    assert reason_create.name == "内容重复"
    assert reason_delete.confirmation_token == "token-reason"
    assert recycle.group == "课程小组"
    assert restore.items == ["10", "11"]
    assert permanent.confirmation_token == "token-recycle"
    assert empty.confirmation_token == "token-empty"


def test_personal_group_export_cli() -> None:
    listing = build_parser().parse_args(["group-exports", "课程小组"])
    create = build_parser().parse_args(["group-member-export", "课程小组"])
    download = build_parser().parse_args(
        [
            "group-export-download",
            "课程小组",
            "21203",
            r"D:\Exports",
            "--overwrite",
            "--wait-seconds",
            "180",
        ]
    )
    wait = build_parser().parse_args(
        [
            "group-export-wait",
            "课程小组",
            "21203",
            "--timeout-seconds",
            "180",
            "--poll-seconds",
            "3",
        ]
    )
    retry = build_parser().parse_args(["group-export-retry", "课程小组", "21203"])
    cancel = build_parser().parse_args(
        [
            "group-export-cancel",
            "课程小组",
            "21203",
            "--confirmation-token",
            "token-export",
        ]
    )

    assert listing.group == "课程小组"
    assert create.command == "group-member-export"
    assert download.export == "21203" and download.overwrite is True
    assert download.output_path == r"D:\Exports"
    assert download.wait_seconds == 180
    assert wait.timeout_seconds == 180 and wait.poll_seconds == 3
    assert retry.export == "21203"
    assert cancel.confirmation_token == "token-export"


def test_personal_group_activity_cli() -> None:
    listing = build_parser().parse_args(
        ["group-activities", "课程小组", "--status", "offline", "--max-items", "50"]
    )
    upload = build_parser().parse_args(["group-activity-image-upload", r"D:\Images\banner.png"])
    create = build_parser().parse_args(
        [
            "group-activity-create",
            "课程小组",
            "课程入口",
            "--online",
            "--app-image-url",
            "https://example.com/app.png",
            "--pc-image-url",
            "https://example.com/pc.png",
            "--confirmation-token",
            "token-create",
        ]
    )
    update = build_parser().parse_args(
        [
            "group-activity-update",
            "课程小组",
            "课程入口",
            "--title",
            "新课程入口",
            "--confirmation-token",
            "token-update",
        ]
    )
    status = build_parser().parse_args(
        [
            "group-activity-status",
            "课程小组",
            "课程入口",
            "offline",
            "--confirmation-token",
            "token-status",
        ]
    )
    reorder = build_parser().parse_args(
        [
            "group-activities-reorder",
            "课程小组",
            "入口二",
            "入口一",
            "--confirmation-token",
            "token-order",
        ]
    )
    delete = build_parser().parse_args(
        [
            "group-activity-delete",
            "课程小组",
            "课程入口",
            "--confirmation-token",
            "token-delete",
        ]
    )
    assert listing.status == "offline" and listing.max_items == 50
    assert upload.file == r"D:\Images\banner.png"
    assert create.online is True and create.confirmation_token == "token-create"
    assert update.title == "新课程入口"
    assert status.status == "offline"
    assert reorder.activities == ["入口二", "入口一"]
    assert delete.confirmation_token == "token-delete"
