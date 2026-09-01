from chaoxing_agent.router import route_command


def test_route_login_status() -> None:
    plan = route_command("检查一下现在登录的是哪个账号")
    assert plan.action == "session.check"
    assert not plan.missing_fields


def test_route_http_login_with_and_without_credentials() -> None:
    incomplete = route_command("重新登录学习通")
    complete = route_command("登录学习通账号《13800138000》密码《secret-value》")
    assert incomplete.action == "session.login"
    assert incomplete.missing_fields == ["username", "password"]
    assert complete.action == "session.login"
    assert complete.parameters == {"username": "13800138000", "password": "secret-value"}
    assert complete.missing_fields == []


def test_route_job_ability_public_search_catalog_and_industry_actions() -> None:
    status = route_command("查看岗位能力状态和学校岗位库权限")
    opening = route_command("打开岗位能力")
    search = route_command("搜索招聘岗位《英语教师》，学历本科，第2页，每页30条")
    details = route_command("查看招聘岗位《job-42》详情，搜索《英语教师》")
    popular = route_command("查看本科热门岗位和高薪岗位")
    catalog = route_command("查看本科职业百科目录")
    occupations = route_command("在职业百科中搜索《教师》")
    types = route_command("列出行业分类")
    industries = route_command("列出行业类型《互联网技术》下的分类")
    industry_jobs = route_command("查看行业岗位《人工智能》")

    assert status.action == "job_ability.status.read"
    assert opening.action == "space.module.open" and opening.parameters["module"] == "岗位能力"
    assert search.action == "job_ability.jobs.search"
    assert search.parameters["keyword"] == "英语教师"
    assert search.parameters["education_level"] == "本科"
    assert search.parameters["page"] == 2 and search.parameters["page_size"] == 30
    assert details.action == "job_ability.job_ad.read"
    assert details.parameters == {"job": "job-42", "search": "英语教师"}
    assert popular.action == "job_ability.popular_jobs.list"
    assert catalog.action == "job_ability.occupation_catalog.read"
    assert occupations.action == "job_ability.occupations.search"
    assert occupations.parameters["keyword"] == "教师"
    assert types.action == "job_ability.industry_types.list"
    assert industries.action == "job_ability.industries.list"
    assert industries.parameters["industry_type"] == "互联网技术"
    assert industry_jobs.action == "job_ability.industry_jobs.list"
    assert industry_jobs.parameters["industry"] == "人工智能"


def test_route_subject_creation_operations() -> None:
    status = route_command("检查我能否创建专题")
    tree = route_command("查看完整专题目录树")
    create = route_command("在专题文件夹《课程》中新建专题文件夹《资料》")
    rename = route_command("把专题文件夹《资料》重命名为《教学资料》")
    move = route_command("把专题《写作》移动到专题文件夹《课程》")
    publish = route_command("发布专题《写作》")
    restore = route_command("从专题回收站恢复《写作》")
    permanent = route_command("从专题回收站永久删除《写作》")
    assert status.action == "subjects.creation.status"
    assert tree.action == "subjects.tree.list"
    assert create.action == "subjects.folder.create"
    assert create.parameters == {"name": "资料", "parent_folder": "课程"}
    assert rename.action == "subjects.folder.rename"
    assert rename.parameters == {"folder": "资料", "name": "教学资料"}
    assert move.action == "subjects.move"
    assert move.parameters == {"subject": "写作", "target_folder": "课程"}
    assert publish.action == "subjects.publish_status.update"
    assert publish.parameters["published"] is True
    assert restore.action == "subjects.recycle.restore"
    assert permanent.action == "subjects.recycle.delete"


def test_route_detection_operations() -> None:
    channels = route_command("查看相似度检测的比对库")
    records = route_command("列出AIGC检测记录")
    submit = route_command("提交AIGC检测《论文》《这是一段足够长的正文内容》")
    similarity = route_command(r"提交查重文档《论文》《作者》《D:\Documents\paper.docx》")
    compare = route_command(r"提交两两比对《文档一》《D:\one.docx》《文档二》《D:\two.docx》")
    download = route_command(r"下载AIGC检测报告《record-1》到《D:\Reports》并覆盖")
    free = route_command("使用AIGC检测免费额度解锁《record-1》")
    delete = route_command("永久删除AIGC检测记录《record-1》")
    assert channels.action == "detection.channels.list"
    assert records.action == "detection.records.list" and records.parameters["type"] == "aigc"
    assert submit.action == "detection.submit" and submit.parameters["content"].startswith("这是")
    assert similarity.action == "detection.submit"
    assert similarity.parameters["author"] == "作者"
    assert similarity.parameters["file"] == r"D:\Documents\paper.docx"
    assert compare.action == "detection.comparison.submit"
    assert compare.parameters["file_2"] == r"D:\two.docx"
    assert download.action == "detection.report.download"
    assert download.parameters["overwrite"] is True
    assert free.action == "detection.free_entitlement.use"
    assert delete.action == "detection.record.delete"


def test_route_personal_live_room_and_theme_operations() -> None:
    listing = route_command("查看个人直播间")
    create = route_command("创建直播间《公开课》，时间2026-09-03 11:00，简介《课程介绍》")
    update = route_command("把直播间《公开课》重命名为《公开课第二场》")
    settings = route_command(
        "把直播间《公开课》的观看密码设置为《1234》，开启回看，"
        "回看开始偏移5秒，仅允许单位23080、43870"
    )
    stream = route_command("读取直播间《公开课》的RTMP推流凭据")
    recycle = route_command("从直播回收站恢复《公开课》")
    theme_create = route_command("创建主题直播《系列公开课》《主题说明》")
    add_room = route_command("把个人直播《公开课》加入主题直播《系列公开课》")
    create_child = route_command("在主题直播《系列公开课》中新建子直播《第二场》")
    theme_settings = route_command("把主题直播《系列公开课》的单位限制设为23080、43870")

    assert listing.action == "live.rooms.list"
    assert create.action == "live.room.create"
    assert create.parameters["scheduled_time"] == "2026-09-03 11:00"
    assert update.action == "live.room.update" and update.parameters["title"] == "公开课第二场"
    assert settings.action == "live.room.settings.update"
    assert settings.parameters["access_password"] == "1234"
    assert settings.parameters["replay_enabled"] is True
    assert settings.parameters["replay_start_offset_seconds"] == 5
    assert settings.parameters["allowed_unit_ids"] == ["23080", "43870"]
    assert stream.action == "live.stream.credentials"
    assert recycle.action == "live.recycle.restore"
    assert theme_create.action == "live.theme.create"
    assert add_room.parameters == {"room": "公开课", "theme": "系列公开课"}
    assert create_child.action == "live.theme.room.create"
    assert theme_settings.parameters["allowed_unit_ids"] == ["23080", "43870"]


def test_personal_live_router_does_not_hijack_course_live_module() -> None:
    plan = route_command("查看《文体写作示例》的直播课")
    assert plan.action == "course.module.open"
    assert plan.parameters["course"] == "文体写作示例"


def test_route_ai_workbench_group_and_command_operations() -> None:
    groups = route_command("查看课程《文体写作示例》的AI指令分组")
    group_create = route_command("在课程《文体写作示例》中新建AI指令分组《备课》")
    command_create = route_command(
        "在课程《文体写作示例》的AI指令分组《备课》中创建AI指令《生成提纲》"
        "，指令内容《主题为：请输入主题》，说明《生成结构清楚的提纲》"
        "，提示词《保持准确》，教师和学生两端开放"
    )
    update = route_command(
        "修改课程《文体写作示例》的AI指令《生成提纲》的提示词为《只使用课程资料》并改为学生端"
    )
    move = route_command("把课程《文体写作示例》的AI指令《生成提纲》移动到指令分组《复习》")
    publish = route_command("发布课程《文体写作示例》的AI指令《生成提纲》")
    delete = route_command("删除课程《文体写作示例》的AI指令《生成提纲》")

    assert groups.action == "ai_workbench.groups.list"
    assert group_create.action == "ai_workbench.group.create"
    assert group_create.parameters["name"] == "备课"
    assert command_create.action == "ai_workbench.command.create"
    assert command_create.parameters["group"] == "备课"
    assert command_create.parameters["name"] == "生成提纲"
    assert command_create.parameters["prompt_words"] == "保持准确"
    assert command_create.parameters["role_type"] == 2
    assert update.action == "ai_workbench.command.update"
    assert update.parameters["prompt_words"] == "只使用课程资料"
    assert update.parameters["role_type"] == 1
    assert move.action == "ai_workbench.command.move"
    assert move.parameters["target_group"] == "复习"
    assert publish.action == "ai_workbench.command.publish_status.update"
    assert publish.parameters["published"] is True
    assert delete.action == "ai_workbench.command.delete"


def test_route_ai_workbench_recommendations_and_role_order() -> None:
    recommendations = route_command("查看课程《文体写作示例》第2页AI指令推荐")
    add = route_command("把课程《文体写作示例》的推荐指令《教学设计》引用到分组《备课》")
    reorder = route_command(
        "把课程《文体写作示例》分组《备课》的学生端AI指令顺序调整为《知识讲解》《案例讲解》"
    )

    assert recommendations.action == "ai_workbench.recommendations.list"
    assert recommendations.parameters["page"] == 2
    assert add.action == "ai_workbench.recommendation.add"
    assert add.parameters["recommendation"] == "教学设计"
    assert add.parameters["group"] == "备课"
    assert reorder.action == "ai_workbench.command.reorder"
    assert reorder.parameters["role_type"] == 1
    assert reorder.parameters["commands"] == ["知识讲解", "案例讲解"]


def test_route_knowledge_hub_base_and_document_lifecycle() -> None:
    listing = route_command("查看课程《语言与测试》的AI知识库")
    details = route_command("查看课程《语言与测试》的知识库《默认知识库》详情")
    create = route_command("在课程《语言与测试》新建AI知识库《期末复习库》《期末复习资料》")
    share = route_command("共享课程《语言与测试》的知识库《期末复习库》")
    documents = route_command("查看课程《语言与测试》的知识库《默认知识库》文档")
    upload = route_command(
        r"把文件《D:\资料\复习.pdf》上传到课程《语言与测试》的知识库《默认知识库》"
    )
    deletion = route_command("删除课程《语言与测试》的知识库《默认知识库》文档《旧资料.pdf》")

    assert listing.action == "knowledge_hub.bases.list"
    assert listing.parameters["course"] == "语言与测试"
    assert details.action == "knowledge_hub.base.read"
    assert details.parameters["base"] == "默认知识库"
    assert create.action == "knowledge_hub.base.create"
    assert create.parameters["name"] == "期末复习库"
    assert create.parameters["description"] == "期末复习资料"
    assert share.action == "knowledge_hub.base.share.update"
    assert share.parameters["shared"] is True
    assert documents.action == "knowledge_hub.documents.list"
    assert documents.parameters["base"] == "默认知识库"
    assert upload.action == "knowledge_hub.document.upload"
    assert upload.parameters["base"] == "默认知识库"
    assert upload.parameters["file"] == r"D:\资料\复习.pdf"
    assert deletion.action == "knowledge_hub.document.delete"
    assert deletion.parameters["document"] == "旧资料.pdf"


def test_route_task_engine_read_create_move_recycle_and_publish() -> None:
    folders = route_command("查看课程《文体写作示例》的任务引擎文件夹")
    create_folder = route_command("给课程《文体写作示例》新建任务文件夹《单元一》")
    create_task = route_command("给课程《文体写作示例》创建教学任务《过程分析》")
    details = route_command("查看课程《文体写作示例》的教学任务《过程分析》详情")
    move = route_command("把课程《文体写作示例》的教学任务《过程分析》移动到文件夹《单元一》")
    deletion = route_command("删除课程《文体写作示例》的教学任务《过程分析》")
    recycle = route_command("查看课程《文体写作示例》的任务回收站")
    restore = route_command("从课程《文体写作示例》的任务回收站恢复《过程分析》")
    publish = route_command("发布课程《文体写作示例》的教学任务《过程分析》")

    assert folders.action == "task_engine.folders.list"
    assert create_folder.action == "task_engine.folder.create"
    assert create_folder.parameters["name"] == "单元一"
    assert create_task.action == "task_engine.task.create"
    assert create_task.parameters["name"] == "过程分析"
    assert details.action == "task_engine.task.read"
    assert details.parameters["task"] == "过程分析"
    assert move.action == "task_engine.task.move"
    assert move.parameters["folder"] == "单元一"
    assert deletion.action == "task_engine.task.delete"
    assert recycle.action == "task_engine.recycle.list"
    assert restore.action == "task_engine.task.restore"
    assert publish.action == "task_engine.publish_status.update"
    assert publish.parameters["published"] is True


def test_route_task_engine_labels_export_update_and_complete_order() -> None:
    label = route_command("给课程《文体写作示例》新建任务标签《复习》")
    rename = route_command("把课程《文体写作示例》的任务标签《复习》改名为《期末复习》")
    export = route_command("导出课程《文体写作示例》的教学任务《任务一》《任务二》")
    update = route_command("修改课程《文体写作示例》的教学任务《任务一》，目标《完成比较分析》")
    order = route_command("把课程《文体写作示例》的教学任务顺序调整为《任务二》《任务一》")

    assert label.action == "task_engine.label.create"
    assert label.parameters["name"] == "复习"
    assert rename.action == "task_engine.label.rename"
    assert rename.parameters["label"] == "复习" and rename.parameters["name"] == "期末复习"
    assert export.action == "task_engine.export.request"
    assert export.parameters["tasks"] == ["任务一", "任务二"]
    assert update.action == "task_engine.task.update"
    assert update.parameters["target"] == "完成比较分析"
    assert order.action == "task_engine.order.update"
    assert order.parameters["task_order"] == ["任务二", "任务一"]


def test_route_knowledge_graph_read_category_and_node_lifecycle() -> None:
    listing = route_command("查看课程《文体写作示例》的课程图谱第2级节点")
    details = route_command("查看课程《文体写作示例》的图谱节点《Punctuation》详情")
    create = route_command("给课程《文体写作示例》的课程图谱新建一级分类《语言基础》")
    update = route_command("把课程《文体写作示例》的课程图谱分类《语言基础》改名为《写作基础》")
    deletion = route_command("删除课程《文体写作示例》的课程图谱节点《写作基础》")

    assert listing.action == "knowledge_graph.graph.read"
    assert listing.parameters["course"] == "文体写作示例" and listing.parameters["level"] == 2
    assert details.action == "knowledge_graph.node.read"
    assert details.parameters["node"] == "Punctuation"
    assert create.action == "knowledge_graph.category.create"
    assert create.parameters["name"] == "语言基础"
    assert update.action == "knowledge_graph.category.update"
    assert update.parameters["node"] == "语言基础" and update.parameters["name"] == "写作基础"
    assert deletion.action == "knowledge_graph.node.delete"
    assert deletion.parameters["node"] == "写作基础"


def test_route_generic_graph_nodes_and_actual_node_relations() -> None:
    create = route_command("在课程《文体写作示例》的图谱节点《第一单元》下新建技能点《标点运用》")
    update = route_command("把课程《文体写作示例》的图谱节点《标点运用》改名为《标点选择》")
    reading = route_command("查看课程图谱《文体写作示例》中《标点选择》的节点关系")
    adding = route_command("给课程图谱《文体写作示例》的《标点选择》添加后置关系到《句子写作》")
    removing = route_command("删除课程图谱《文体写作示例》中《标点选择》到《句子写作》的后置关系")

    assert create.action == "knowledge_graph.node.create"
    assert create.parameters["node_type"] == "ability"
    assert create.parameters["parent"] == "第一单元"
    assert create.parameters["name"] == "标点运用"
    assert update.action == "knowledge_graph.node.update"
    assert update.parameters["node"] == "标点运用"
    assert update.parameters["name"] == "标点选择"
    assert reading.action == "knowledge_graph.node.relations.read"
    assert reading.parameters["node"] == "标点选择"
    assert adding.action == "knowledge_graph.node.relation.add"
    assert adding.parameters["relation"] == "successor"
    assert adding.parameters["target"] == "句子写作"
    assert removing.action == "knowledge_graph.node.relation.remove"
    assert removing.parameters["relation"] == "successor"


def test_route_knowledge_graph_custom_relation_definitions() -> None:
    listing = route_command("查看课程《文体写作示例》的课程图谱关系定义")
    create = route_command(
        "给课程《文体写作示例》的课程图谱新建关联类自定义关系《支持关系》《A支持B》"
    )
    update = route_command("把课程《文体写作示例》的图谱关系定义《支持关系》改名为《促进关系》")
    deletion = route_command("删除课程《文体写作示例》的图谱关系定义《促进关系》")

    assert listing.action == "knowledge_graph.relation_types.list"
    assert create.action == "knowledge_graph.relation_type.create"
    assert create.parameters["name"] == "支持关系"
    assert create.parameters["meaning"] == "A支持B"
    assert create.parameters["relation_types"] == [0]
    assert update.action == "knowledge_graph.relation_type.update"
    assert update.parameters["relation"] == "支持关系"
    assert update.parameters["name"] == "促进关系"
    assert deletion.action == "knowledge_graph.relation_type.delete"


def test_route_knowledge_graph_display_settings_read_and_update() -> None:
    reading = route_command("查看课程《文体写作示例》的课程图谱显示设置")
    update = route_command("把课程《文体写作示例》的课程图谱显示全部关系打开，导航节点缩放关闭")

    assert reading.action == "knowledge_graph.settings.read"
    assert update.action == "knowledge_graph.settings.update"
    assert update.parameters["show_all_relations"] is True
    assert update.parameters["navigation_node_scale"] is False
    assert update.missing_fields == []


def test_route_knowledge_graph_advanced_settings_read_and_update() -> None:
    reading = route_command("查看课程《文体写作示例》的课程图谱高级设置")
    update = route_command("把课程《文体写作示例》的知识点卡片和微课预览打开，教学目标关闭")

    assert reading.action == "knowledge_graph.advanced_settings.read"
    assert update.action == "knowledge_graph.advanced_settings.update"
    assert update.parameters["topic_card"] is True
    assert update.parameters["teach_target"] is False
    assert update.parameters["micro_preview"] is True
    assert update.missing_fields == []


def test_route_knowledge_graph_model_lifecycle_visibility_and_classes() -> None:
    listing = route_command("查看课程《文体写作示例》的课程图谱模型")
    create = route_command("给课程《文体写作示例》新建自定义图谱《期末复习》")
    visibility = route_command("把课程《文体写作示例》的学习地图打开")
    classes = route_command("把课程《文体写作示例》的知识图谱只开放给班级《一班》《二班》")
    data = route_command("查看课程《文体写作示例》的学习地图内容")

    assert listing.action == "knowledge_graph.models.list"
    assert create.action == "knowledge_graph.model.create"
    assert create.parameters["name"] == "期末复习"
    assert visibility.action == "knowledge_graph.model.visibility.update"
    assert visibility.parameters["model"] == "学习地图"
    assert visibility.parameters["visible"] is True
    assert classes.action == "knowledge_graph.model.classes.update"
    assert classes.parameters["model"] == "知识图谱"
    assert classes.parameters["visible_classes"] == ["一班", "二班"]
    assert data.action == "knowledge_graph.model.data.read"
    assert data.parameters["model"] == "学习地图"


def test_route_knowledge_graph_task_event_lifecycle() -> None:
    listing = route_command("查看课程《文体写作示例》的图谱任务事件")
    create = route_command(
        "给课程《文体写作示例》新建图谱任务事件《完成事件》："
        "知识点完成率大于等于80%时，在学习路径显示标签《重点》"
    )
    rename = route_command("把课程《文体写作示例》的图谱任务事件《完成事件》改名为《复习事件》")
    deletion = route_command("删除课程《文体写作示例》的图谱任务事件《复习事件》")

    assert listing.action == "knowledge_graph.events.list"
    assert create.action == "knowledge_graph.event.create"
    assert create.parameters["topic_condition"] == 1
    assert create.parameters["set_condition"] == 3
    assert create.parameters["percent1"] == 80
    assert create.parameters["executions"] == [{"label": "重点", "execute_module": 0}]
    assert not create.missing_fields
    assert rename.action == "knowledge_graph.event.update"
    assert rename.parameters["event"] == "完成事件"
    assert rename.parameters["name"] == "复习事件"
    assert deletion.action == "knowledge_graph.event.delete"


def test_route_knowledge_graph_export_format_model_and_path() -> None:
    export = route_command(r"把课程《文体写作示例》的知识图谱导出为 RDF 到 D:\Exports 并覆盖")

    assert export.action == "knowledge_graph.export.download"
    assert export.parameters["course"] == "文体写作示例"
    assert export.parameters["model"] == "知识图谱"
    assert export.parameters["format"] == "rdf"
    assert export.parameters["output_path"] == r"D:\Exports"
    assert export.parameters["overwrite"] is True
    assert not export.missing_fields


def test_route_knowledge_graph_label_group_and_label_management() -> None:
    group = route_command("给课程《文体写作示例》的课程图谱新建标签组《复习》")
    group_order = route_command(
        "把课程《文体写作示例》的图谱标签组顺序调整为《复习》《默认标签组》"
    )
    label = route_command("给课程《文体写作示例》的图谱标签组《复习》新建标签《重点》")
    rename = route_command("把课程《文体写作示例》的图谱标签《重点》改名为《必学》")
    move = route_command("把课程《文体写作示例》的图谱标签《必学》移到《默认标签组》")
    deletion = route_command("删除课程《文体写作示例》的图谱标签《必学》")

    assert group.action == "knowledge_graph.label_group.create"
    assert group.parameters["name"] == "复习"
    assert group_order.action == "knowledge_graph.label_groups.reorder"
    assert group_order.parameters["groups"] == ["复习", "默认标签组"]
    assert label.action == "knowledge_graph.label.create"
    assert label.parameters["group"] == "复习" and label.parameters["name"] == "重点"
    assert rename.action == "knowledge_graph.label.rename"
    assert rename.parameters["label"] == "重点" and rename.parameters["name"] == "必学"
    assert move.action == "knowledge_graph.label.move"
    assert move.parameters["label"] == "必学" and move.parameters["group"] == "默认标签组"
    assert deletion.action == "knowledge_graph.label.delete"


def test_route_class_activity_types_groups_and_filtered_list() -> None:
    types = route_command("查看课程《文体写作示例》的班级活动类型")
    create = route_command("给课程《文体写作示例》新建活动分组《随堂练习》")
    rename = route_command("把课程《文体写作示例》的活动分组《随堂练习》改名为《课堂练习》")
    reorder = route_command("把课程《文体写作示例》的活动分组顺序调整为《课堂练习》《通知》")
    listing = route_command("查看课程《文体写作示例》班级《示例一班》的已结束班级活动，类型45")

    assert types.action == "class_activities.types.list"
    assert create.action == "class_activities.group.create"
    assert create.parameters["name"] == "随堂练习"
    assert rename.action == "class_activities.group.rename"
    assert rename.parameters["group"] == "随堂练习"
    assert rename.parameters["name"] == "课堂练习"
    assert reorder.action == "class_activities.groups.reorder"
    assert reorder.parameters["groups"] == ["课堂练习", "通知"]
    assert listing.action == "class_activities.activities.list"
    assert listing.parameters["clazz"] == "示例一班"
    assert listing.parameters["status"] == "ended"
    assert listing.parameters["activity_type"] == 45


def test_route_class_activity_details_move_lifecycle_and_recycle() -> None:
    details = route_command("查看课程《文体写作示例》的班级活动《第一节课签到》详情")
    move = route_command("把课程《文体写作示例》的班级活动《第一节课签到》移到活动分组《课堂练习》")
    order = route_command(
        "把课程《文体写作示例》分组《课堂练习》的班级活动顺序调整为《签到》《抢答》"
    )
    start = route_command("开始课程《文体写作示例》的班级活动《第一节课签到》")
    end = route_command("结束课程《文体写作示例》的班级活动《第一节课签到》")
    recycle = route_command("查看课程《文体写作示例》的活动回收站")
    restore = route_command("从课程《文体写作示例》的活动回收站恢复《第一节课签到》")
    permanent = route_command("从课程《文体写作示例》的活动回收站永久删除《签到一》《签到二》")

    assert details.action == "class_activities.activity.read"
    assert details.parameters["activity"] == "第一节课签到"
    assert move.action == "class_activities.activity.move"
    assert move.parameters["group"] == "课堂练习"
    assert order.action == "class_activities.activities.reorder"
    assert order.parameters["group"] == "课堂练习"
    assert order.parameters["activities"] == ["签到", "抢答"]
    assert start.action == "class_activities.activity.start"
    assert end.action == "class_activities.activity.end"
    assert recycle.action == "class_activities.recycle.list"
    assert restore.action == "class_activities.recycle.restore"
    assert permanent.action == "class_activities.recycle.items.delete"
    assert permanent.parameters["activities"] == ["签到一", "签到二"]


def test_route_course_list() -> None:
    plan = route_command("列出我教的课")
    assert plan.action == "courses.list_teaching"


def test_route_learning_course_list_modules_open_and_integrity() -> None:
    listing = route_command("列出我学的课")
    searched = route_command("搜索我学的课程《心理学》")
    modules = route_command("查看我学课程《英语文体与写作》的功能入口")
    opened = route_command("打开我学课程《英语文体与写作》的《章节》")
    integrity = route_command("查看我学课程《英语文体与写作》的在线学习诚信承诺书状态")
    accept = route_command("同意我学课程《英语文体与写作》的在线学习诚信承诺书")

    assert listing.action == "learning.courses.list"
    assert searched.action == "learning.courses.list"
    assert searched.parameters == {"search": "心理学"}
    assert modules.action == "learning.course.modules.discover"
    assert modules.parameters == {"course": "英语文体与写作"}
    assert opened.action == "learning.course.module.open"
    assert opened.parameters == {"course": "英语文体与写作", "module": "章节"}
    assert integrity.action == "learning.course.integrity.read"
    assert accept.action == "learning.course.integrity.accept"


def test_route_course_classes_with_quoted_course() -> None:
    plan = route_command("查看《语言测试示例》的班级")
    assert plan.action == "courses.list_classes"
    assert plan.parameters["course"] == "语言测试示例"


def test_route_class_students_command() -> None:
    plan = route_command("列出《文体写作示例》《英语2401》的学生名单")
    assert plan.action == "class.students.list"
    assert plan.parameters["clazz"] == "英语2401"


def test_route_student_access_logs_command() -> None:
    plan = route_command("查看《文体写作示例》《英语2401》《2024001686》的2025年11月访问日志")
    assert plan.action == "class.student.access_logs.list"
    assert plan.parameters["student"] == "2024001686"
    assert plan.parameters["year"] == 2025
    assert plan.parameters["month"] == 11


def test_route_course_and_student_change_logs() -> None:
    operation = route_command("查看《文体写作示例》的《作业》操作日志")
    joins = route_command("查看《文体写作示例》《英语2401》的教师手动加班日志")
    leaves = route_command("查看《文体写作示例》《英语2401》的学生退课日志")
    assert operation.action == "course.operation_logs.list"
    assert operation.parameters["module"] == "作业"
    assert joins.action == "class.student_join_logs.list"
    assert joins.parameters["join_type"] == 1
    assert leaves.action == "class.student_leave_logs.list"


def test_route_restore_student_from_leave_log() -> None:
    plan = route_command("恢复《文体写作示例》《英语2401》《杨子昂》的退课学生")
    assert plan.action == "class.student.restore"
    assert plan.parameters["student"] == "杨子昂"


def test_route_course_teachers_command() -> None:
    plan = route_command("查看《文体写作示例》的教师团队")
    assert plan.action == "course.teachers.list"
    assert plan.parameters["course"] == "文体写作示例"


def test_route_teacher_team_management_commands() -> None:
    search = route_command("在《文体写作示例》教师库搜索《2014800132》")
    bank_add = route_command("从《文体写作示例》的教师库添加《2014800132》为助教")
    manual_add = route_command("向《文体写作示例》添加教师《李老师》，工号《2001800001》")
    remove = route_command("从《文体写作示例》教学团队移除《2001800001》")
    permissions = route_command("查看《文体写作示例》中教师《2025800218》的教师权限")
    permission_update = route_command(
        "给《文体写作示例》的教师《2025800218》开启作业权限、关闭考试权限"
    )
    assert search.action == "course.teacher_candidates.search"
    assert search.parameters["query"] == "2014800132"
    assert bank_add.action == "course.teacher.add_from_bank"
    assert bank_add.parameters["role"] == "assistant"
    assert manual_add.action == "course.teacher.add_by_identity"
    assert manual_add.parameters["identity"] == "2001800001"
    assert remove.action == "course.teacher.remove"
    assert permissions.action == "course.teacher.permissions.read"
    assert permission_update.action == "course.teacher.permissions.update"
    assert permission_update.parameters == {
        "course": "文体写作示例",
        "teacher": "2025800218",
        "changes": {"homework": True, "examine": False},
    }


def test_route_teacher_permission_update_with_canonical_field() -> None:
    plan = route_command("把《900000002》的助教《2025800218》的《piyuework》权限设为开启")
    assert plan.action == "course.teacher.permissions.update"
    assert plan.parameters["changes"] == {"piyuework": True}
    assert not plan.missing_fields


def test_route_grade_weights_command() -> None:
    plan = route_command("查看《文体写作示例》《英语2401》的成绩权重")
    assert plan.action == "course.grade_weights.read"
    assert plan.parameters == {"course": "文体写作示例", "clazz": "英语2401"}


def test_route_homework_library_and_draft_commands() -> None:
    library = route_command("查看《900000002》的作业库")
    drafts = route_command("列出《900000002》的作业草稿箱")
    create = route_command("在《900000002》中创建作业草稿《Unit 1 draft》")
    update = route_command("将《900000002》的作业草稿《Unit 1 draft》改名为《Unit 1 homework》")
    delete = route_command("删除《900000002》的作业草稿《Unit 1 homework》")
    assert library.action == "homework.library.list"
    assert drafts.action == "homework.drafts.list"
    assert create.action == "homework.draft.create"
    assert create.parameters["title"] == "Unit 1 draft"
    assert update.action == "homework.draft.update"
    assert update.parameters["title"] == "Unit 1 homework"
    assert delete.action == "homework.draft.delete"
    assert delete.parameters["draft"] == "Unit 1 homework"


def test_route_homework_question_commands() -> None:
    read = route_command("查看《900000002》作业《Process analysis》的第1题")
    add = route_command(
        "在《900000002》的作业《Unit 1 draft》中添加单选题《Which is correct?》，"
        "选项 A=《Alpha》、B=《Beta》，答案 B，分值 5，难度 0.8"
    )
    update = route_command("将《900000002》作业《Unit 1》的第2题分值改为10，答案改为A")
    delete = route_command("删除《900000002》作业《Unit 1》的第3题")

    assert read.action == "homework.library.item.read"
    assert read.parameters["question"] == "1"
    assert add.action == "homework.question.add"
    assert add.parameters["question_type"] == "single_choice"
    assert add.parameters["stem"] == "Which is correct?"
    assert add.parameters["options"] == ["Alpha", "Beta"]
    assert add.parameters["correct_answer"] == "B"
    assert not add.missing_fields
    assert update.action == "homework.question.update"
    assert update.parameters["question"] == "2"
    assert update.parameters["score"] == 10
    assert update.parameters["correct_answer"] == "A"
    assert delete.action == "homework.question.delete"
    assert delete.parameters["question"] == "3"


def test_route_exam_paper_library_and_paper_question() -> None:
    listing = route_command("查看《900000002》的试卷库")
    read = route_command("查看《900000002》试卷《Process Analysis Test》的第1题")
    assert listing.action == "exam.paper_library.list"
    assert listing.parameters == {"course": "900000002"}
    assert read.action == "exam.paper.read"
    assert read.parameters == {
        "course": "900000002",
        "paper": "Process Analysis Test",
        "question": "1",
    }


def test_route_exam_question_mutations() -> None:
    add = route_command(
        "在《900000002》的试卷《Unit 1 Test》中新增单选题《Which is correct?》，"
        "选项 A=《Alpha》、B=《Beta》，答案 B，分值 5，难度 0.8"
    )
    update = route_command("将《900000002》的试卷《Unit 1 Test》第2题分值改为10，答案改为A")
    delete = route_command("删除《900000002》的试卷《Unit 1 Test》第3题")

    assert add.action == "exam.question.add"
    assert add.parameters["question_type"] == "single_choice"
    assert add.parameters["stem"] == "Which is correct?"
    assert add.parameters["options"] == ["Alpha", "Beta"]
    assert add.parameters["correct_answer"] == "B"
    assert not add.missing_fields
    assert update.action == "exam.question.update"
    assert update.parameters["question"] == "2"
    assert update.parameters["score"] == 10
    assert update.parameters["correct_answer"] == "A"
    assert delete.action == "exam.question.delete"
    assert delete.parameters["question"] == "3"


def test_route_exam_question_and_type_ordering() -> None:
    move_question = route_command("将《900000002》的试卷《Unit 1 Test》第2题移到第1题")
    move_type = route_command("把《900000002》的试卷《Unit 1 Test》的题型《判断题》移到第1位")
    update_type = route_command(
        "修改《900000002》的试卷《Unit 1 Test》的题型《单选题》，"
        "题型说明改为《Choose one.》，题型总分改为20"
    )
    delete_type = route_command("删除《900000002》的试卷《Unit 1 Test》的题型《判断题》")

    assert move_question.action == "exam.question.move"
    assert move_question.parameters["question"] == "2"
    assert move_question.parameters["target_position"] == 1
    assert move_type.action == "exam.question_type.move"
    assert move_type.parameters["question_type"] == "判断题"
    assert move_type.parameters["target_position"] == 1
    assert update_type.action == "exam.question_type.update"
    assert update_type.parameters["question_type"] == "单选题"
    assert update_type.parameters["description"] == "Choose one."
    assert update_type.parameters["total_score"] == 20
    assert delete_type.action == "exam.question_type.delete"
    assert delete_type.parameters["question_type"] == "判断题"


def test_route_exam_paper_settings() -> None:
    read = route_command("查看《900000002》试卷《Unit 1 Test》的试卷设置")
    update = route_command(
        "将《900000002》试卷《Unit 1 Test》的难度改为难，按题型编号，不按题型归类，小题同级编号"
    )
    assert read.action == "exam.paper.settings.read"
    assert read.parameters == {"course": "900000002", "paper": "Unit 1 Test"}
    assert update.action == "exam.paper.settings.update"
    assert update.parameters["difficulty"] == "难"
    assert update.parameters["numbering"] == "by_type"
    assert update.parameters["grouping"] == "ungrouped"
    assert update.parameters["subquestion_numbering"] == "continuous"
    assert not update.missing_fields


def test_route_exam_paper_and_folder_management() -> None:
    create_paper = route_command("在《900000002》中创建试卷《Unit 1 Test》")
    rename_paper = route_command("将《900000002》的试卷《Unit 1 Test》重命名为《Unit 1 Review》")
    copy_paper = route_command("复制《900000002》的试卷《Unit 1 Review》")
    move_paper = route_command("将《900000002》的试卷《Unit 1 Review》移动到《Argumentation》")
    delete_paper = route_command("删除《900000002》的试卷《Unit 1 Review》")
    create_folder = route_command("在《900000002》试卷库创建文件夹《Review Papers》")
    rename_folder = route_command(
        "将《900000002》的试卷库文件夹《Review Papers》改名为《Final Review》"
    )
    move_folder = route_command(
        "将《900000002》的试卷库文件夹《Final Review》移动到《Argumentation》"
    )
    delete_folder = route_command("删除《900000002》的试卷库文件夹《Final Review》")

    assert create_paper.action == "exam.paper.create"
    assert create_paper.parameters["title"] == "Unit 1 Test"
    assert rename_paper.action == "exam.paper.rename"
    assert rename_paper.parameters["title"] == "Unit 1 Review"
    assert copy_paper.action == "exam.paper.copy"
    assert move_paper.action == "exam.paper.move"
    assert move_paper.parameters["target_directory_id"] == "Argumentation"
    assert delete_paper.action == "exam.paper.delete"
    assert create_folder.action == "exam.paper_folder.create"
    assert rename_folder.action == "exam.paper_folder.rename"
    assert move_folder.action == "exam.paper_folder.move"
    assert delete_folder.action == "exam.paper_folder.delete"


def test_route_question_bank_management() -> None:
    tree = route_command("查看《900000002》题库的全部目录树")
    create_folder = route_command("在《900000002》题库创建目录《Review》")
    rename_folder = route_command("将《900000002》题库目录《Review》重命名为《Final Review》")
    reorder_folder = route_command("将《900000002》题库目录《Review》移动到第2位")
    move_question = route_command("将《900000002》题库题目《question-1》移动到目录《Final Review》")
    reorder_question = route_command("将《900000002》题库题目《question-1》移动到第3位")
    difficulty = route_command("将《900000002》题库题目《question-1》的难度设置为0.7")
    delete_question = route_command("删除《900000002》题库题目《question-1》")
    add = route_command(
        "在《900000002》题库新增单选题《Which is correct?》，选项 A=《Alpha》、B=《Beta》，答案 B"
    )

    assert tree.action == "question_bank.directories.list"
    assert create_folder.action == "question_bank.directory.create"
    assert create_folder.parameters["name"] == "Review"
    assert rename_folder.action == "question_bank.directory.rename"
    assert rename_folder.parameters["name"] == "Final Review"
    assert reorder_folder.action == "question_bank.directory.reorder"
    assert reorder_folder.parameters["target_position"] == 2
    assert move_question.action == "question_bank.question.move"
    assert move_question.parameters["target_directory"] == "Final Review"
    assert reorder_question.action == "question_bank.question.reorder"
    assert reorder_question.parameters["target_position"] == 3
    assert difficulty.action == "question_bank.question.difficulty.update"
    assert difficulty.parameters["difficulty"] == 0.7
    assert delete_question.action == "question_bank.question.delete"
    assert add.action == "question_bank.question.add"
    assert add.parameters["correct_answer"] == "B"
    assert not add.missing_fields


def test_route_question_bank_directory_permissions() -> None:
    read = route_command("查看《文体写作示例》题库目录《Unit 1》的权限")
    update = route_command(
        "把《文体写作示例》题库目录《Unit 1》共享给指定教师《张三》并关闭学生抽题自测"
    )
    private = route_command("把《文体写作示例》题库目录《Unit 2》设为私有")
    assert read.action == "question_bank.directory.permissions.read"
    assert read.parameters == {"course": "文体写作示例", "directory": "Unit 1"}
    assert update.action == "question_bank.directory.permissions.update"
    assert update.parameters == {
        "course": "文体写作示例",
        "directory": "Unit 1",
        "allow_student_self_practice": False,
        "share_scope": "selected_teachers",
        "selected_teachers": ["张三"],
    }
    assert private.action == "question_bank.directory.permissions.update"
    assert private.parameters["share_scope"] == "private"


def test_route_question_bank_question_type_management() -> None:
    listing = route_command("查看《文体写作示例》的题库题型列表")
    create = route_command("在《文体写作示例》题库新建题型《术语解释》，基础题型为简答题")
    rename = route_command("把《文体写作示例》题库题型《术语解释》重命名为《概念解释》")
    move = route_command("把《文体写作示例》题库题型《概念解释》移到第3位")
    delete = route_command("删除《文体写作示例》题库题型《概念解释》")
    assert listing.action == "question_bank.question_types.list"
    assert create.action == "question_bank.question_type.add"
    assert create.parameters["base_type"] == "short_answer"
    assert rename.action == "question_bank.question_type.rename"
    assert rename.parameters["name"] == "概念解释"
    assert move.action == "question_bank.question_type.move"
    assert move.parameters["target_position"] == 3
    assert delete.action == "question_bank.question_type.delete"


def test_route_question_bank_label_management() -> None:
    listing = route_command("查看《文体写作示例》的题库标签树")
    selected = route_command("查看《文体写作示例》题库题目《question-1》的标签")
    create = route_command("在《文体写作示例》题库标签《写作》下新建《求职信》")
    rename = route_command("把《文体写作示例》题库标签《求职信》重命名为《申请信》")
    delete = route_command("删除《文体写作示例》题库标签《申请信》")
    assign = route_command("给《文体写作示例》题库题目《question-1》添加标签《写作》《求职信》")
    clear_and_sync = route_command(
        "清空《文体写作示例》题库题目《question-1》的标签并同步到引用它的作业和考试"
    )
    assert listing.action == "question_bank.labels.list"
    assert selected.action == "question_bank.labels.list"
    assert selected.parameters["question"] == "question-1"
    assert create.action == "question_bank.label.create"
    assert create.parameters == {
        "course": "文体写作示例",
        "name": "求职信",
        "parent_label": "写作",
    }
    assert rename.action == "question_bank.label.rename"
    assert rename.parameters["name"] == "申请信"
    assert delete.action == "question_bank.label.delete"
    assert assign.action == "question_bank.question.labels.set"
    assert assign.parameters["questions"] == ["question-1"]
    assert assign.parameters["labels"] == ["写作", "求职信"]
    assert assign.parameters["mode"] == "add"
    assert clear_and_sync.action == "question_bank.question.labels.sync"
    assert clear_and_sync.parameters["labels"] == []
    assert clear_and_sync.parameters["mode"] == "replace"


def test_route_question_bank_topic_management() -> None:
    listing = route_command("查看《文体写作示例》的题库知识点树")
    selected = route_command("查看《文体写作示例》题库题目《question-1》的知识点")
    create = route_command(
        "在《文体写作示例》题库知识点分类《Paragraph Writing》下新建知识点《Topic Sentence》"
    )
    create_category = route_command("在《文体写作示例》题库新建知识点分类《Writing》")
    rename = route_command(
        "把《文体写作示例》题库知识点《Topic Sentence》重命名为《Controlling Idea》"
    )
    delete = route_command("删除《文体写作示例》题库知识点《Controlling Idea》")
    assign = route_command("给《文体写作示例》题库题目《question-1》添加知识点《Topic Sentence》")
    clear_and_sync = route_command(
        "清空《文体写作示例》题库题目《question-1》的知识点并同步到引用它的作业和考试"
    )
    assert listing.action == "question_bank.topics.list"
    assert selected.action == "question_bank.topics.list"
    assert selected.parameters["question"] == "question-1"
    assert create.action == "question_bank.topic.create"
    assert create.parameters == {
        "course": "文体写作示例",
        "name": "Topic Sentence",
        "parent_topic": "Paragraph Writing",
        "kind": "knowledge_point",
    }
    assert create_category.action == "question_bank.topic.create"
    assert create_category.parameters["kind"] == "category"
    assert rename.action == "question_bank.topic.rename"
    assert rename.parameters["name"] == "Controlling Idea"
    assert delete.action == "question_bank.topic.delete"
    assert assign.action == "question_bank.question.topics.set"
    assert assign.parameters["topics"] == ["Topic Sentence"]
    assert assign.parameters["mode"] == "add"
    assert clear_and_sync.action == "question_bank.question.topics.sync"
    assert clear_and_sync.parameters["topics"] == []
    assert clear_and_sync.parameters["mode"] == "replace"


def test_route_question_bank_recycle_and_lock_management() -> None:
    recycle = route_command("查看《文体写作示例》的题库回收站")
    search = route_command("搜索《文体写作示例》题库回收站中的《Topic Sentence》")
    restore = route_command("从《文体写作示例》题库回收站还原《question-1》")
    permanent_delete = route_command("从《文体写作示例》题库回收站永久删除《question-1》")
    empty = route_command("清空《文体写作示例》的题库回收站")
    locked = route_command("查看《文体写作示例》题库已锁定内容")
    lock = route_command("锁定《文体写作示例》题库目录《Unit 1》")
    unlock = route_command("解锁《文体写作示例》题库项目《Unit 1》")
    assert recycle.action == "question_bank.recycle.list"
    assert search.parameters["search"] == "Topic Sentence"
    assert restore.action == "question_bank.recycle.restore"
    assert restore.parameters["items"] == ["question-1"]
    assert permanent_delete.action == "question_bank.recycle.delete"
    assert empty.action == "question_bank.recycle.empty"
    assert locked.action == "question_bank.locked.list"
    assert lock.action == "question_bank.items.lock"
    assert lock.parameters["directories"] == ["Unit 1"]
    assert unlock.action == "question_bank.items.unlock"
    assert unlock.parameters["items"] == ["Unit 1"]


def test_route_question_bank_batch_type_and_copy() -> None:
    type_update = route_command(
        "把《文体写作示例》题库题目《question-1》《question-2》改为题型《简答题》"
    )
    copy_question = route_command("复制《文体写作示例》题库题目《question-1》到目录《Review》")
    copy_directory = route_command("复制《文体写作示例》题库目录《Unit 1》到目录《Review》")
    assert type_update.action == "question_bank.questions.type.update"
    assert type_update.parameters["questions"] == ["question-1", "question-2"]
    assert type_update.parameters["question_type"] == "简答题"
    assert copy_question.action == "question_bank.items.copy"
    assert copy_question.parameters["questions"] == ["question-1"]
    assert copy_question.parameters["target_directory"] == "Review"
    assert copy_directory.action == "question_bank.items.copy"
    assert copy_directory.parameters["directories"] == ["Unit 1"]

    difficulty = route_command("把《文体写作示例》题库题目《question-1》《question-2》难度改为 0.8")
    assert difficulty.action == "question_bank.questions.difficulty.update"
    assert difficulty.parameters["questions"] == ["question-1", "question-2"]
    assert difficulty.parameters["difficulty"] == 0.8


def test_route_question_bank_smart_import() -> None:
    preview = route_command(r"预览《文体写作示例》题库智能导入 D:\Materials\unit1.docx")
    commit = route_command(r"把 D:\Materials\unit1.docx 智能导入《文体写作示例》题库目录《Review》")
    assert preview.action == "question_bank.smart_import.preview"
    assert preview.parameters["file_path"] == r"D:\Materials\unit1.docx"
    assert commit.action == "question_bank.smart_import.commit"
    assert commit.parameters["target_directory"] == "Review"


def test_route_question_bank_exports_and_download_center() -> None:
    exporting = route_command(
        r"把《文体写作示例》题库题目《question-1》《question-2》导出为 Excel "
        r"并保存到 D:\Exports\questions.xlsx"
    )
    assert exporting.action == "question_bank.export.create"
    assert exporting.parameters["questions"] == ["question-1", "question-2"]
    assert exporting.parameters["export_type"] == "excel"
    assert exporting.parameters["output_path"] == r"D:\Exports\questions.xlsx"

    listing = route_command("查看《文体写作示例》题库下载中心")
    assert listing.action == "question_bank.downloads.list"

    downloading = route_command(
        r"下载《文体写作示例》题库下载中心的《record-1》到 D:\Exports\questions.xlsx"
    )
    assert downloading.action == "question_bank.downloads.get"
    assert downloading.parameters["record"] == "record-1"
    assert downloading.parameters["output_path"] == r"D:\Exports\questions.xlsx"

    renaming = route_command("把《文体写作示例》题库下载记录《record-1》重命名为《Unit 1.xlsx》")
    assert renaming.action == "question_bank.downloads.rename"
    assert renaming.parameters["name"] == "Unit 1.xlsx"

    deleting = route_command("删除《文体写作示例》题库下载记录《record-1》")
    assert deleting.action == "question_bank.downloads.delete"


def test_route_question_bank_cross_course_import() -> None:
    courses = route_command("查看《目标课》题库来源课程")
    listing = route_command("查看《目标课》其他课程《来源课》题库，搜索《process》")
    importing = route_command(
        "从《来源课》课程题库导入《question-1》《question-2》到《目标课》目录《Review》"
    )
    assert courses.action == "question_bank.source_courses.list"
    assert listing.action == "question_bank.source_questions.list"
    assert listing.parameters["source_course"] == "来源课"
    assert listing.parameters["search"] == "process"
    assert importing.action == "question_bank.questions.import_from_course"
    assert importing.parameters["source_course"] == "来源课"
    assert importing.parameters["questions"] == ["question-1", "question-2"]
    assert importing.parameters["course"] == "目标课"
    assert importing.parameters["target_directory"] == "Review"


def test_route_publish_homework_from_library() -> None:
    plan = route_command(
        "将《900000002》作业库中的《Process analysis》发放给《示例一班》，"
        "立即开始，截止时间 2026-09-10 23:59，允许补交，禁止粘贴，题目乱序"
    )
    assert plan.action == "homework.library.publish"
    assert plan.parameters["target_classes"] == ["示例一班"]
    assert plan.parameters["start_time"] == "now"
    assert plan.parameters["end_time"] == "2026-09-10 23:59"
    assert plan.parameters["allow_late_submission"] is True
    assert plan.parameters["allow_paste"] is False
    assert plan.parameters["randomize_questions"] is True


def test_route_course_grades_command() -> None:
    plan = route_command("按成绩降序查看《文体写作示例》《英语2401》的学生成绩")
    assert plan.action == "course.grades.list"
    assert plan.parameters == {
        "course": "文体写作示例",
        "clazz": "英语2401",
        "raw_scores": False,
        "sort": "score",
        "descending": True,
    }


def test_route_raw_course_grades_for_one_student() -> None:
    plan = route_command("查看《文体写作示例》《英语2401》《2024001686》的原始分数")
    assert plan.action == "course.grades.list"
    assert plan.parameters["search"] == "2024001686"
    assert plan.parameters["raw_scores"] is True


def test_route_read_grade_visibility() -> None:
    plan = route_command("查看《文体写作示例》《英语2401》的学生查看成绩设置")
    assert plan.action == "course.grade_visibility.read"
    assert plan.parameters == {"course": "文体写作示例", "clazz": "英语2401"}


def test_route_set_grade_visibility_is_full_class_list() -> None:
    plan = route_command("设置《文体写作示例》的成绩可见班级为《英语2401》《英语2402》，显示排名")
    assert plan.action == "course.grade_visibility.set"
    assert plan.parameters["visible_classes"] == ["英语2401", "英语2402"]
    assert plan.parameters["students_can_view_rank"] is True


def test_route_grade_override() -> None:
    plan = route_command("将《文体写作示例》《英语2401》《2024001686》的综合成绩改为85分")
    assert plan.action == "course.grade_override.set"
    assert plan.parameters["student"] == "2024001686"
    assert plan.parameters["score"] == 85.0


def test_route_learning_progress_for_one_student() -> None:
    plan = route_command("查看《文体写作示例》《英语2401》《2024001686》的学习进度")
    assert plan.action == "course.learning_progress.list"
    assert plan.parameters == {
        "course": "文体写作示例",
        "clazz": "英语2401",
        "search": "2024001686",
    }


def test_route_exam_anomaly_monitor() -> None:
    plan = route_command("查看《文体写作示例》《英语2401》的考试异常学习记录")
    assert plan.action == "course.study_monitor.list"
    assert plan.parameters == {
        "course": "文体写作示例",
        "clazz": "英语2401",
        "only_abnormal": True,
        "anomaly_type": 4,
    }


def test_route_study_monitor_reminder() -> None:
    plan = route_command(
        "发送异常学习提醒给《文体写作示例》《英语2401》《2024002794》"
        "，标题《学习异常提醒》，正文《请查看考试异常记录。》"
    )
    assert plan.action == "course.study_monitor.remind"
    assert plan.parameters["student"] == "2024002794"
    assert plan.parameters["title"] == "学习异常提醒"


def test_route_clear_study_anomaly() -> None:
    plan = route_command("清除《文体写作示例》《英语2401》《2024002794》的异常学习记录")
    assert plan.action == "course.study_monitor.clear"
    assert plan.parameters["student"] == "2024002794"


def test_route_open_homework() -> None:
    plan = route_command("打开《语言测试示例》的作业")
    assert plan.action == "course.module.open"
    assert plan.parameters == {"course": "语言测试示例", "module": "作业"}


def test_route_open_module_requests_course_when_missing() -> None:
    plan = route_command("打开考试")
    assert plan.action == "course.module.open"
    assert plan.missing_fields == ["course"]


def test_route_ungraded_homework_command() -> None:
    plan = route_command("列出《语言测试示例》的未批改作业")
    assert plan.action == "homework.list_ungraded"
    assert plan.parameters == {"course": "语言测试示例"}

    explicit_course_label = route_command("查看课程《语言测试示例》的未批改作业")
    assert explicit_course_label.action == "homework.list_ungraded"
    assert explicit_course_label.parameters == {"course": "语言测试示例"}
    assert not plan.missing_fields


def test_route_chapter_list_command() -> None:
    plan = route_command("查看《文体写作示例》的章节目录")
    assert plan.action == "chapters.list"


def test_route_chapter_management_commands() -> None:
    creating = route_command("在《文体写作示例》的章节《Unit 1》下新建子目录《Review》")
    renaming = route_command("把《文体写作示例》的章节《Review》重命名为《Revision》")
    moving = route_command("把《文体写作示例》的章节《Revision》移动到《Learning Guide》之前")
    status = route_command("把《文体写作示例》的章节《Learning Guide》在班级《示例一班》设为关闭")
    deleting = route_command("删除《文体写作示例》的章节《Revision》")
    cards = route_command("查看《文体写作示例》的章节《Learning Guide》内容")
    tree = route_command("查看《文体写作示例》的完整章节树")
    card_create = route_command(
        "在《文体写作示例》的章节《Learning Guide》中新增页面《Goals》，内容《Read this page.》"
    )
    card_update = route_command(
        "把《文体写作示例》章节《Learning Guide》的页面《Goals》重命名为《Learning goals》"
    )
    card_move = route_command(
        "把《文体写作示例》章节《Learning Guide》的页面《Learning goals》移动到第1页"
    )
    card_delete = route_command(
        "删除《文体写作示例》章节《Learning Guide》的页面《Learning goals》"
    )

    assert creating.action == "chapters.create"
    assert creating.parameters["parent"] == "Unit 1"
    assert creating.parameters["title"] == "Review"
    assert renaming.action == "chapters.rename"
    assert renaming.parameters["title"] == "Revision"
    assert moving.action == "chapters.move"
    assert moving.parameters["relative_to"] == "Learning Guide"
    assert moving.parameters["position"] == "before"
    assert status.action == "chapters.open_status.update"
    assert status.parameters["chapters"] == ["Learning Guide"]
    assert status.parameters["classes"] == ["示例一班"]
    assert status.parameters["status"] == "close"
    assert deleting.action == "chapters.delete"
    assert cards.action == "chapters.cards.list"
    assert tree.action == "chapters.tree.list"
    assert card_create.action == "chapters.card.create"
    assert card_create.parameters["content"] == "Read this page."
    assert card_update.action == "chapters.card.update"
    assert card_update.parameters["title"] == "Learning goals"
    assert card_move.action == "chapters.card.move"
    assert card_move.parameters["target_position"] == 1
    assert card_delete.action == "chapters.card.delete"


def test_route_resource_folder_command() -> None:
    plan = route_command("查看《文体写作示例》的资料《Description》")
    assert plan.action == "resources.list"
    assert plan.parameters["folder"] == "Description"


def test_route_resource_management_commands() -> None:
    tree = route_command("查看《文体写作示例》的完整资料树")
    downloading = route_command(
        "下载《文体写作示例》的资料《Guide.pdf》到《D:\\Downloads\\Guide.pdf》"
    )
    folder = route_command("在《文体写作示例》的资料目录《Unit 1》中新建文件夹《Review》")
    renaming = route_command("把《文体写作示例》的资料《Guide.pdf》重命名为《Guide 2.pdf》")
    moving = route_command("把《文体写作示例》的资料《Guide.pdf》《Slides.pptx》移动到《Unit 1》")
    uploading = route_command(
        "上传《文体写作示例》的资料文件《D:\\Materials\\Guide.pdf》到《Unit 1》"
    )
    permission = route_command("禁止《文体写作示例》的资料《Guide.pdf》下载")
    visibility = route_command(
        "设置《文体写作示例》的资料《Unit 1》对指定班级《示例一班》《英语2505》可见"
    )
    readers = route_command("查看《文体写作示例》的资料《Guide.pdf》未读名单")
    downloaders = route_command("查看《文体写作示例》的资料《Guide.pdf》下载记录")
    sources = route_command("查看《文体写作示例》可导入资料的课程")
    share = route_command("分享《文体写作示例》的资料《Guide.pdf》")
    topping = route_command("置顶《文体写作示例》的资料《Guide.pdf》")
    copying = route_command("复制《文体写作示例》的资料《Guide.pdf》")
    copy_to_cloud = route_command("把《文体写作示例》的资料《Guide.pdf》保存到云盘《Archive》")
    cloud_sources = route_command("查看《文体写作示例》可导入的云盘文件")
    cloud_import = route_command(
        "把《文体写作示例》的云盘文件《Guide.pdf》《Slides.pptx》导入资料目录《Unit 1》"
    )
    cloud_folder_import = route_command(
        "把《文体写作示例》的云盘文件夹《Review》导入资料目录《Unit 1》"
    )
    labels = route_command("查看《文体写作示例》的资料《Guide.pdf》的标签")
    label_create = route_command("在《文体写作示例》的资料《Guide.pdf》中创建资料标签《Review》")
    label_rename = route_command(
        "把《文体写作示例》的资料《Guide.pdf》的标签《Review》重命名为《Final》"
    )
    label_delete = route_command("删除《文体写作示例》的资料《Guide.pdf》的标签《Final》")
    labels_update = route_command(
        "给《文体写作示例》的资料《Guide.pdf》《Slides.pptx》设置标签《Review》《Final》"
    )
    labels_clear = route_command("清除《文体写作示例》的资料《Guide.pdf》《Slides.pptx》的全部标签")

    assert tree.action == "resources.tree.list"
    assert downloading.action == "resources.file.download"
    assert downloading.parameters["resource"] == "Guide.pdf"
    assert downloading.parameters["output_path"].endswith("Guide.pdf")
    assert folder.action == "resources.folder.create"
    assert folder.parameters["parent"] == "Unit 1"
    assert folder.parameters["name"] == "Review"
    assert renaming.action == "resources.rename"
    assert moving.action == "resources.move"
    assert moving.parameters["resources"] == ["Guide.pdf", "Slides.pptx"]
    assert uploading.action == "resources.file.upload"
    assert uploading.parameters["parent"] == "Unit 1"
    assert permission.action == "resources.download_permission.update"
    assert permission.parameters["allow_download"] is False
    assert visibility.action == "resources.folder.visibility.update"
    assert visibility.parameters["classes"] == ["示例一班", "英语2505"]
    assert readers.action == "resources.readers.list"
    assert downloaders.action == "resources.downloaders.list"
    assert sources.action == "resources.import_courses.list"
    assert share.action == "resources.share_link.create"
    assert topping.action == "resources.top_status.update"
    assert topping.parameters["top"] is True
    assert copying.action == "resources.copy"
    assert copy_to_cloud.action == "resources.cloud_disk.copy"
    assert copy_to_cloud.parameters["destination"] == "Archive"
    assert cloud_sources.action == "resources.cloud_sources.list"
    assert cloud_import.action == "resources.cloud_files.import"
    assert cloud_import.parameters["resources"] == ["Guide.pdf", "Slides.pptx"]
    assert cloud_import.parameters["destination"] == "Unit 1"
    assert cloud_folder_import.action == "resources.cloud_folder.import"
    assert cloud_folder_import.parameters["resource"] == "Review"
    assert cloud_folder_import.parameters["destination"] == "Unit 1"
    assert labels.action == "resources.labels.list"
    assert labels.parameters["resource"] == "Guide.pdf"
    assert label_create.action == "resources.label.create"
    assert label_create.parameters["name"] == "Review"
    assert label_rename.action == "resources.label.rename"
    assert label_rename.parameters["label"] == "Review"
    assert label_rename.parameters["name"] == "Final"
    assert label_delete.action == "resources.label.delete"
    assert label_delete.parameters["label"] == "Final"
    assert labels_update.action == "resources.labels.update"
    assert labels_update.parameters["resources"] == ["Guide.pdf", "Slides.pptx"]
    assert labels_update.parameters["labels"] == ["Review", "Final"]
    assert labels_clear.action == "resources.labels.update"
    assert labels_clear.parameters["resources"] == ["Guide.pdf", "Slides.pptx"]
    assert labels_clear.parameters["labels"] == []


def test_route_cloud_disk_commands() -> None:
    listing = route_command("查看我的云盘")
    searching = route_command("搜索云盘里的《Guide.pdf》")
    detail = route_command("查看云盘文件《Guide.pdf》的详情")
    deleting = route_command("删除云盘文件《Guide.pdf》《Slides.pptx》")
    folder = route_command("在云盘《Unit 1》里创建协作文件夹《Review》")
    renaming = route_command("把云盘文件《Guide.pdf》重命名为《Handout》")
    moving = route_command("把云盘文件《Guide.pdf》《Slides.pptx》移动到《Archive》")
    topping = route_command("置顶云盘文件《Guide.pdf》")
    downloading = route_command(
        r"下载云盘文件《Guide.pdf》《Slides.pptx》到《D:\Downloads\materials.zip》"
    )
    recycle = route_command("查看云盘回收站")
    restore = route_command("从云盘回收站恢复《Guide.pdf》，同名时替换")
    permanent_delete = route_command("从云盘回收站永久删除《Guide.pdf》")
    empty = route_command("清空云盘回收站")

    assert listing.action == "cloud_disk.items.list"
    assert searching.action == "cloud_disk.items.list"
    assert searching.parameters["search"] == "Guide.pdf"
    assert detail.action == "cloud_disk.item.read"
    assert detail.parameters["resource"] == "Guide.pdf"
    assert deleting.action == "cloud_disk.items.delete"
    assert deleting.parameters["resources"] == ["Guide.pdf", "Slides.pptx"]
    assert folder.action == "cloud_disk.folder.create"
    assert folder.parameters == {"shared": True, "parent": "Unit 1", "name": "Review"}
    assert renaming.action == "cloud_disk.item.rename"
    assert renaming.parameters == {"resource": "Guide.pdf", "name": "Handout"}
    assert moving.action == "cloud_disk.items.move"
    assert moving.parameters["destination"] == "Archive"
    assert topping.action == "cloud_disk.item.top_status.update"
    assert topping.parameters["top"] is True
    assert downloading.action == "cloud_disk.items.download"
    assert downloading.parameters["resources"] == ["Guide.pdf", "Slides.pptx"]
    assert downloading.parameters["output_path"] == r"D:\Downloads\materials.zip"
    assert recycle.action == "cloud_disk.recycle.list"
    assert restore.action == "cloud_disk.recycle.restore"
    assert restore.parameters["conflict_policy"] == "replace"
    assert permanent_delete.action == "cloud_disk.recycle.items.delete"
    assert empty.action == "cloud_disk.recycle.empty"


def test_route_homework_submissions_command() -> None:
    plan = route_command("列出《语言测试示例》的《第1周作业：语境词汇基础题》已批提交")
    assert plan.action == "homework.submissions.list"
    assert plan.parameters == {
        "course": "语言测试示例",
        "homework": "第1周作业：语境词汇基础题",
        "status": 4,
    }


def test_route_homework_submission_read_command() -> None:
    plan = route_command("查看《语言测试示例》的《第1周作业》里《20230001》的作答")
    assert plan.action == "homework.submission.read"
    assert plan.parameters["submission"] == "20230001"


def test_route_homework_score_command() -> None:
    plan = route_command("给《语言测试示例》的《第1周作业》中《20230001》打95分")
    assert plan.action == "homework.score.set"
    assert plan.parameters["score"] == "95"


def test_route_notice_list_command() -> None:
    plan = route_command("查看《语言测试示例》的通知")
    assert plan.action == "notices.list"
    assert plan.parameters == {"course": "语言测试示例"}


def test_route_notice_draft_commands() -> None:
    listing = route_command("查看《语言测试示例》的通知草稿")
    saving = route_command("为《语言测试示例》保存通知草稿《第2周安排》《请预习第二章。》")
    deleting = route_command("删除《语言测试示例》的通知草稿《第2周安排》")
    assert listing.action == "notices.drafts.list"
    assert saving.action == "notices.draft.save"
    assert saving.parameters["title"] == "第2周安排"
    assert deleting.action == "notices.draft.delete"
    assert deleting.parameters["draft"] == "第2周安排"


def test_route_scheduled_notice_command() -> None:
    plan = route_command(
        "向《语言测试示例》《英日2301-2302》定时发送通知"
        "《第2周安排》《请预习第二章。》《2099-01-02 03:04》"
    )
    assert plan.action == "notices.schedule"
    assert plan.parameters["recipient_classes"] == ["英日2301-2302"]
    assert plan.parameters["send_at"] == "2099-01-02 03:04"


def test_route_send_notice_command() -> None:
    plan = route_command(
        "向《语言测试示例》《英日2301-2302》发送通知《第1周安排》《请按时完成作业。》"
    )
    assert plan.action == "notices.send"
    assert plan.parameters["recipient_classes"] == ["英日2301-2302"]
    assert plan.parameters["title"] == "第1周安排"


def test_route_edit_notice_command() -> None:
    plan = route_command(
        "修改《语言测试示例》的通知《第1周安排》为《第1周安排更新》《截止时间改为周日。》"
    )
    assert plan.action == "notices.edit"
    assert plan.parameters["notice"] == "第1周安排"
    assert plan.parameters["content"] == "截止时间改为周日。"


def test_route_notice_top_and_delete_commands() -> None:
    top = route_command("置顶《语言测试示例》的通知《第1周安排》")
    delete = route_command("删除《语言测试示例》的通知《第1周安排》")
    assert top.action == "notices.top.set"
    assert top.parameters["top"] is True
    assert delete.action == "notices.delete"


def test_route_ended_exam_list_command() -> None:
    plan = route_command("查看《文体写作示例》的已结束考试")
    assert plan.action == "exams.list"
    assert plan.parameters["status"] == 2


def test_route_exam_submissions_command() -> None:
    plan = route_command("列出《文体写作示例》的考试《期中测试——2024级——终稿》已交学生")
    assert plan.action == "exams.submissions.list"
    assert plan.parameters["exam"] == "期中测试——2024级——终稿"
    assert plan.parameters["state"] == 1


def test_route_exam_answer_command() -> None:
    plan = route_command(
        "查看《文体写作示例》的考试《期中测试——2024级——终稿》中《2024001686》的答卷"
    )
    assert plan.action == "exams.submission.read"
    assert plan.parameters["submission"] == "2024001686"


def test_route_question_bank_command() -> None:
    plan = route_command("浏览《文体写作示例》的题库")
    assert plan.action == "question_bank.list"
    assert plan.parameters["page"] == 1


def test_route_question_bank_question_command() -> None:
    plan = route_command("查看《文体写作示例》的题库题目《How should you write a number》的答案")
    assert plan.action == "question_bank.question.read"
    assert plan.parameters["question"] == "How should you write a number"


def test_route_discussion_command() -> None:
    plan = route_command("查看《文体写作示例》的本班讨论")
    assert plan.action == "discussions.list"
    assert plan.parameters["class_only"] is True


def test_route_discussion_topic_replies_command() -> None:
    plan = route_command("查看《文体写作示例》的讨论《Describing people》的回复")
    assert plan.action == "discussions.topic.read"
    assert plan.parameters["topic"] == "Describing people"
    assert plan.parameters["order"] == 2


def test_route_discussion_topic_mutations() -> None:
    create = route_command(
        "在《文体写作示例》的本班发布讨论《Writing process》正文《Describe your process.》"
    )
    edit = route_command(
        "修改《文体写作示例》的讨论《Writing process》正文为《Describe your own process.》"
    )
    top = route_command("置顶《文体写作示例》的讨论《Writing process》")
    delete = route_command("删除《文体写作示例》的讨论《Writing process》")
    assert create.action == "discussions.topic.create"
    assert create.parameters["class_only"] is True
    assert create.parameters["content"] == "Describe your process."
    assert edit.action == "discussions.topic.edit"
    assert edit.parameters["content"] == "Describe your own process."
    assert top.action == "discussions.topic.top.set"
    assert top.parameters["top"] is True
    assert delete.action == "discussions.topic.delete"


def test_route_discussion_reply_mutations() -> None:
    create = route_command("回复《文体写作示例》的讨论《Writing process》：《Thanks for sharing.》")
    edit = route_command(
        "修改《文体写作示例》的讨论《Writing process》中回复《Thanks》为《Thank you.》"
    )
    delete = route_command("删除《文体写作示例》的讨论《Writing process》中回复《Thank you.》")
    assert create.action == "discussions.reply.create"
    assert create.parameters["content"] == "Thanks for sharing."
    assert edit.action == "discussions.reply.edit"
    assert edit.parameters["reply"] == "Thanks"
    assert delete.action == "discussions.reply.delete"
    assert delete.parameters["reply"] == "Thank you."


def test_route_class_lifecycle_commands() -> None:
    create = route_command("在《文体写作示例》创建班级《临时班》")
    rename = route_command("将《文体写作示例》的班级《临时班》重命名为《验证班》")
    read = route_command("查看《文体写作示例》的班级《验证班》的班级设置")
    update = route_command("把《文体写作示例》的班级《验证班》人数上限设置为120")
    delete = route_command("删除《文体写作示例》的班级《验证班》")
    assert create.action == "classes.create"
    assert create.parameters["name"] == "临时班"
    assert rename.action == "class.rename"
    assert rename.parameters["name"] == "验证班"
    assert read.action == "class.settings.read"
    assert update.action == "class.settings.update"
    assert update.parameters["student_limit"] == 120
    assert delete.action == "class.delete"


def test_route_class_invitation_read() -> None:
    plan = route_command("查看《文体写作示例》的班级《英语2401》邀请码")
    assert plan.action == "class.invitation.read"
    assert plan.parameters == {"course": "文体写作示例", "clazz": "英语2401"}


def test_route_student_membership_commands() -> None:
    search = route_command("在《文体写作示例》的班级《英语2401》学生库搜索《2024000273》")
    bank_add = route_command(
        "把《文体写作示例》的班级《英语2401》学生库中的《2024000273》添加进班级"
    )
    manual_add = route_command(
        "向《文体写作示例》的班级《英语2401》添加学生《张三》，学号《2024000001》"
    )
    remove = route_command("从《文体写作示例》的班级《英语2401》移除学生《2024000273》")
    assert search.action == "class.student_candidates.search"
    assert search.parameters["query"] == "2024000273"
    assert bank_add.action == "class.student.add_from_bank"
    assert bank_add.parameters["student"] == "2024000273"
    assert manual_add.action == "class.student.add_by_identity"
    assert manual_add.parameters["identity_type"] == "student_no"
    assert remove.action == "class.student.remove"


def test_route_join_application_and_student_move() -> None:
    listing = route_command("查看《文体写作示例》的班级《英语2401》入班申请")
    approve = route_command("批准《文体写作示例》的班级《英语2401》入班申请《2024001234》")
    move = route_command(
        "将《文体写作示例》班级《英语2401》的学生《2024001234》移动到班级《英语2402》"
    )
    assert listing.action == "class.join_applications.list"
    assert approve.action == "class.join_application.decide"
    assert approve.parameters["decision"] == "approve"
    assert move.action == "class.student.move"
    assert move.parameters["target_clazz"] == "英语2402"


def test_unknown_command_is_not_guessed() -> None:
    plan = route_command("替我完成所有事情")
    assert plan.action is None
    assert plan.confidence == 0


def test_route_personal_space_discovery_and_open() -> None:
    discovery = route_command("列出个人空间功能菜单")
    opening = route_command("打开我的笔记")
    assert discovery.action == "space.modules.discover"
    assert opening.action == "space.module.open"
    assert opening.parameters["module"] == "笔记"


def test_route_personal_note_crud() -> None:
    listing = route_command("列出我的笔记")
    search = route_command("搜索笔记《考试》")
    reading = route_command("查看笔记《复习计划》的内容")
    creation = route_command("新建笔记《复习计划》，内容《第一周》")
    title_update = route_command("把笔记《复习计划》重命名为《期末复习计划》")
    content_update = route_command("把笔记《期末复习计划》的正文改为《完成第一周》")
    deletion = route_command("删除笔记《期末复习计划》")
    assert listing.action == "notes.list"
    assert search.action == "notes.list" and search.parameters["search"] == "考试"
    assert reading.action == "notes.read" and reading.parameters["note"] == "复习计划"
    assert creation.action == "notes.create"
    assert creation.parameters == {"title": "复习计划", "content": "第一周"}
    assert title_update.action == "notes.update"
    assert title_update.parameters["title"] == "期末复习计划"
    assert content_update.parameters["content"] == "完成第一周"
    assert deletion.action == "notes.delete"


def test_route_personal_inbox_operations() -> None:
    listing = route_command("查看收件箱")
    sent = route_command("查看已发送通知")
    search = route_command("搜索收件箱《课程通知》")
    reading = route_command("查看收件箱通知《课程通知》的内容")
    unread = route_command("将收到的通知《课程通知》标为未读")
    top = route_command("置顶收件箱通知《课程通知》")
    uncollect = route_command("取消收藏收件箱通知《课程通知》")
    deletion = route_command("删除收件箱通知《课程通知》")
    assert listing.action == "inbox.notices.list"
    assert sent.action == "inbox.notices.list" and sent.parameters["scope"] == "sent"
    assert search.parameters["search"] == "课程通知"
    assert reading.action == "inbox.notice.read"
    assert unread.action == "inbox.notice.mark_unread"
    assert top.parameters["top"] is True
    assert uncollect.parameters["collect"] is False
    assert deletion.action == "inbox.notice.delete"


def test_route_personal_inbox_send_and_drafts() -> None:
    send = route_command("给《本人》发送个人通知《验证标题》《验证正文》")
    draft_save = route_command("新建个人通知草稿《草稿标题》《草稿正文》《本人》")
    draft_list = route_command("查看个人通知草稿")
    draft_search = route_command("搜索个人通知草稿《测试》")
    draft_delete = route_command("删除个人通知草稿《草稿标题》")
    assert send.action == "inbox.notice.send"
    assert send.parameters == {
        "recipients": ["本人"],
        "title": "验证标题",
        "content": "验证正文",
    }
    assert draft_save.action == "inbox.draft.save"
    assert draft_save.parameters["recipients"] == ["本人"]
    assert draft_list.action == "inbox.drafts.list"
    assert draft_search.parameters["search"] == "测试"
    assert draft_delete.action == "inbox.draft.delete"


def test_route_personal_inbox_folder_and_recycle_operations() -> None:
    folders = route_command("查看收件箱文件夹")
    create = route_command("新建通知文件夹《重要》")
    rename = route_command("把通知文件夹《重要》重命名为《待办》")
    rules = route_command("查看通知文件夹《待办》的收纳规则")
    notices = route_command("查看通知文件夹《待办》里的通知")
    move = route_command("把收件箱通知《课程通知》移动到通知文件夹《待办》")
    move_root = route_command("把通知文件夹里的通知《课程通知》移回收件箱根目录")
    reorder = route_command("按《待办》《重要》的顺序排列收件箱文件夹")
    delete = route_command("删除通知文件夹《待办》")
    recycle = route_command("查看通知回收站")
    restore = route_command("从通知回收站恢复《课程通知》")
    permanent = route_command("从通知回收站永久删除《课程通知》")
    empty = route_command("清空通知回收站")
    assert folders.action == "inbox.folders.list"
    assert create.action == "inbox.folder.create" and create.parameters["name"] == "重要"
    assert rename.action == "inbox.folder.update" and rename.parameters["name"] == "待办"
    assert rules.action == "inbox.folder.filters.read"
    assert notices.action == "inbox.folder.notices.list"
    assert move.action == "inbox.notices.move"
    assert move.parameters["notices"] == ["课程通知"]
    assert move.parameters["destination_folder"] == "待办"
    assert move_root.parameters["destination_folder"] == "root"
    assert reorder.action == "inbox.folders.reorder"
    assert reorder.parameters["folders"] == ["待办", "重要"]
    assert delete.action == "inbox.folder.delete"
    assert recycle.action == "inbox.recycle.list"
    assert restore.action == "inbox.recycle.restore"
    assert permanent.action == "inbox.recycle.items.delete"
    assert empty.action == "inbox.recycle.empty"


def test_route_personal_contacts_operations() -> None:
    units = route_command("列出通讯录单位")
    searching = route_command("在通讯录搜索联系人《张三》")
    followers = route_command("查看关注我的人")
    following = route_command("查看我关注的联系人")
    groups = route_command("查看通讯录小组")
    group_members = route_command("查看通讯录小组《教师发展小组》的成员")
    chatgroups = route_command("查看我加入的群聊")
    chat_members = route_command("查看群聊《张三、李四》的成员")
    teams = route_command("查看自建团队列表")
    team_create = route_command("创建通讯录团队《项目组》《张三》《李四》")
    team_rename = route_command("把通讯录团队《项目组》重命名为《课程组》")
    team_add = route_command("向通讯录团队《课程组》添加成员《王五》")
    team_remove = route_command("从通讯录团队《课程组》移除成员《王五》")
    team_delete = route_command("删除通讯录团队《课程组》")
    assert units.action == "contacts.units.list"
    assert searching.action == "contacts.people.search"
    assert searching.parameters["search"] == "张三"
    assert followers.parameters["relation"] == "followers"
    assert following.parameters["relation"] == "following"
    assert groups.action == "contacts.groups.list"
    assert group_members.action == "contacts.group.members.list"
    assert chatgroups.action == "contacts.chatgroups.list"
    assert chat_members.action == "contacts.chatgroup.members.list"
    assert teams.action == "contacts.teams.list"
    assert team_create.parameters["members"] == ["张三", "李四"]
    assert team_rename.parameters["name"] == "课程组"
    assert team_add.action == "contacts.team.members.add"
    assert team_remove.action == "contacts.team.member.remove"
    assert team_delete.action == "contacts.team.delete"


def test_route_personal_group_operations() -> None:
    listing = route_command("查看我的小组")
    searching = route_command("搜索个人小组《写作》")
    reading = route_command("查看小组《写作小组》详情")
    creation = route_command("创建个人小组《课程小组》《课程交流》")
    update = route_command("把个人小组《课程小组》重命名为《写作课程小组》")
    description = route_command("修改个人小组《课程小组》简介为《课程交流区》")
    logo_update = route_command(r"更换个人小组《课程小组》的头像《D:\Images\logo.png》")
    modules = route_command("查看个人小组《课程小组》的模块配置")
    modules_update = route_command("设置个人小组《课程小组》的模块配置为只保留视频模块")
    levels = route_command("查看个人小组《课程小组》的等级头衔")
    level_series = route_command("把个人小组《课程小组》的等级系列切换为默认系列")
    custom_levels = route_command(
        '设置个人小组《课程小组》的自定义等级头衔 [{"level":1,"title":"起步","growth_value":5}]'
    )
    growth_rules = route_command("查看个人小组《课程小组》的成长值规则")
    growth_rule_series = route_command("把个人小组《课程小组》的成长值规则恢复为默认系列")
    growth_rules_update = route_command("把个人小组《课程小组》的发表话题成长值规则设为6")
    settings_update = route_command("开启个人小组《课程小组》的话题审核")
    speaking_rules = route_command("把个人小组《课程小组》的话题最少字数设为30")
    notice_send = route_command("向个人小组《课程小组》发送通知《开课通知》《周一开始上课。》")
    review_reminders = route_command("查看个人小组《课程小组》的审核提醒")
    review_reminder_create = route_command(
        "在个人小组《课程小组》创建审核提醒，星期日 23:58 到 23:59，审核人 PUID《405017213》"
    )
    review_reminder_update = route_command(
        "修改个人小组《课程小组》的审核提醒《reminder-1》为星期六 23:57 到 23:59"
    )
    review_reminders_delete = route_command("删除个人小组《课程小组》的审核提醒《reminder-1》")
    top = route_command("置顶个人小组《课程小组》")
    move = route_command("把个人小组《课程小组》移动到《教学》")
    move_root = route_command("把个人小组《课程小组》移动到根目录")
    quit_group = route_command("退出个人小组《课程小组》")
    dismiss_group = route_command("解散个人小组《课程小组》")
    members = route_command("查看个人小组《课程小组》的成员")
    bulk_import_status = route_command("查看个人小组《课程小组》的成员批量导入状态")
    bulk_import_template = route_command(
        r"下载个人小组《课程小组》的成员批量导入模板到《D:\Temp\template.xlsx》"
    )
    bulk_import = route_command(r"向个人小组《课程小组》批量导入成员，文件《D:\Temp\members.xlsx》")
    member_read = route_command("查看个人小组《课程小组》的成员《张三》详情")
    member_permissions = route_command("查看个人小组《课程小组》的管理员《张三》权限")
    member_permissions_update = route_command(
        "开启个人小组《课程小组》的管理员《张三》权限《showBarcode》"
    )
    member_sources = route_command("查看个人小组《课程小组》的可添加成员来源")
    member_candidates = route_command(
        "搜索个人小组《课程小组》从已有小组来源《71506605》的候选成员《张三》"
    )
    members_add = route_command("向个人小组《课程小组》添加成员 PUID《101》《102》")
    manager_add = route_command("把个人小组《课程小组》的成员《张三》设为管理员")
    manager_remove = route_command("取消个人小组《课程小组》的成员《张三》管理员")
    member_remove = route_command("从个人小组《课程小组》移除成员《张三》")
    creator_transfer = route_command("把个人小组《课程小组》的创建者转让给成员《张三》")
    clear_external = route_command("清除个人小组《课程小组》的全部非学习通成员")
    folders = route_command("查看小组文件夹")
    tree = route_command("查看个人小组文件夹树")
    folder_create = route_command("创建小组文件夹《教学》")
    folder_rename = route_command("把小组文件夹《教学》重命名为《课程》")
    folder_move = route_command("把小组文件夹《课程》移动到《归档》")
    folder_top = route_command("取消置顶小组文件夹《课程》")
    folder_delete = route_command("删除小组文件夹《课程》")
    topics = route_command("查看个人小组《课程小组》的话题")
    topic_search = route_command("搜索个人小组《课程小组》的话题《写作》")
    topic_read = route_command("查看个人小组《课程小组》的话题《如何修改论文》详情")
    topic_create = route_command("在个人小组《课程小组》发布话题《如何修改论文》《先判断问题。》")
    topic_delete = route_command("删除个人小组《课程小组》的话题《如何修改论文》")
    topic_choice = route_command("把个人小组《课程小组》的话题《如何修改论文》设为精华")
    topic_choice_cancel = route_command("取消个人小组《课程小组》的话题《如何修改论文》的精华")
    topic_praise = route_command("点赞个人小组《课程小组》的话题《如何修改论文》")
    topic_praise_cancel = route_command("取消点赞个人小组《课程小组》的话题《如何修改论文》")
    topics_score = route_command("给个人小组《课程小组》的话题《问题一》《问题二》批量评分85分")
    topics_move = route_command(
        "把个人小组《课程小组》的话题《问题一》《问题二》批量移动到话题文件夹《讨论》"
    )
    topics_move_root = route_command(
        "把个人小组《课程小组》的话题《问题一》《问题二》批量移动到话题根目录"
    )
    topics_delete = route_command("批量删除个人小组《课程小组》的话题《问题一》《问题二》")
    topic_update = route_command(
        "把个人小组《课程小组》的话题《如何修改论文》重命名为《如何修改课程论文》"
    )
    topic_content = route_command(
        "修改个人小组《课程小组》的话题《如何修改论文》正文为《先判断问题，再修改。》"
    )
    topic_reply = route_command("回复个人小组《课程小组》的话题《如何修改论文》《先看论点。》")
    nested_reply = route_command(
        "回复个人小组《课程小组》的话题《如何修改论文》中的《先判断问题》《先看论点。》"
    )
    reply_delete = route_command(
        "删除个人小组《课程小组》的话题《如何修改论文》中的回复《先看论点》"
    )
    reply_update = route_command(
        "修改个人小组《课程小组》的话题《如何修改论文》中的回复《先看论点》为《先看中心论点。》"
    )
    topic_folders = route_command("查看个人小组《课程小组》的话题文件夹树")
    topic_top = route_command("取消置顶个人小组《课程小组》的话题《如何修改论文》")
    topic_move = route_command(
        "把个人小组《课程小组》的话题《如何修改论文》移动到话题文件夹《讨论》"
    )
    topic_move_root = route_command("把个人小组《课程小组》的话题《如何修改论文》移动到话题根目录")
    topic_folder_create = route_command(
        "在个人小组《课程小组》的话题文件夹《讨论》中创建子文件夹《论文》"
    )
    topic_folder_rename = route_command(
        "把个人小组《课程小组》的话题文件夹《论文》重命名为《课程论文》"
    )
    topic_folder_move = route_command(
        "把个人小组《课程小组》的话题文件夹《课程论文》移动到《讨论》"
    )
    topic_folder_delete = route_command("删除个人小组《课程小组》的话题文件夹《课程论文》")
    topic_folders_move = route_command(
        "把个人小组《课程小组》的话题文件夹《论文》《读书会》批量移动到《讨论》"
    )
    topic_folders_move_root = route_command(
        "把个人小组《课程小组》的话题文件夹《论文》《读书会》批量移动到根目录"
    )
    topic_folders_delete = route_command(
        "批量删除个人小组《课程小组》的话题文件夹《论文》《读书会》"
    )
    topic_drafts = route_command("查看个人小组《课程小组》的话题草稿")
    topic_draft_read = route_command("查看个人小组《课程小组》的话题草稿《draft-uuid》详情")
    topic_draft_save = route_command(
        "保存个人小组《课程小组》的话题草稿《论文讨论》《先判断问题。》"
    )
    topic_draft_update = route_command(
        "修改个人小组《课程小组》的话题草稿《draft-uuid》《课程论文讨论》《先修改论点。》"
    )
    topic_draft_publish = route_command("发布个人小组《课程小组》的话题草稿《draft-uuid》")

    assert listing.action == "groups.list"
    assert searching.action == "groups.list" and searching.parameters["search"] == "写作"
    assert reading.action == "groups.read" and reading.parameters["group"] == "写作小组"
    assert creation.action == "groups.create" and creation.parameters["description"] == "课程交流"
    assert update.action == "groups.update" and update.parameters["name"] == "写作课程小组"
    assert description.action == "groups.update"
    assert description.parameters["description"] == "课程交流区"
    assert logo_update.action == "groups.logo.update"
    assert logo_update.parameters["file"] == r"D:\Images\logo.png"
    assert modules.action == "groups.modules.list"
    assert modules_update.action == "groups.modules.update"
    assert modules_update.parameters["enabled_type_ids"] == []
    assert levels.action == "groups.levels.list"
    assert level_series.action == "groups.levels.series.update"
    assert level_series.parameters["series"] == "default"
    assert custom_levels.action == "groups.levels.custom.update"
    assert custom_levels.parameters["levels"][0]["title"] == "起步"
    assert growth_rules.action == "groups.growth_rules.list"
    assert growth_rule_series.action == "groups.growth_rules.series.update"
    assert growth_rule_series.parameters["series"] == "default"
    assert growth_rules_update.action == "groups.growth_rules.update"
    assert growth_rules_update.parameters["changes"] == {"2": 6}
    assert settings_update.action == "groups.settings.update"
    assert settings_update.parameters["changes"] == {"topicNeedCheck": True}
    assert speaking_rules.action == "groups.speaking_rules.update"
    assert speaking_rules.parameters["changes"] == {"leastTopicWord": 30}
    assert notice_send.action == "groups.notice.send"
    assert notice_send.parameters["title"] == "开课通知"
    assert notice_send.parameters["content"] == "周一开始上课。"
    assert review_reminders.action == "groups.review_reminders.list"
    assert review_reminder_create.action == "groups.review_reminder.create"
    assert review_reminder_create.parameters["start_time"] == "23:58"
    assert review_reminder_create.parameters["weeks"] == ["星期日"]
    assert review_reminder_create.parameters["puids"] == ["405017213"]
    assert review_reminder_update.action == "groups.review_reminder.update"
    assert review_reminder_update.parameters["reminder"] == "reminder-1"
    assert review_reminder_update.parameters["start_time"] == "23:57"
    assert review_reminders_delete.action == "groups.review_reminders.delete"
    assert review_reminders_delete.parameters["reminders"] == ["reminder-1"]
    assert top.action == "groups.top_status.update" and top.parameters["top"] is True
    assert move.action == "groups.move" and move.parameters["destination_folder"] == "教学"
    assert move_root.parameters["destination_folder"] == "root"
    assert quit_group.action == "groups.quit"
    assert dismiss_group.action == "groups.dismiss"
    assert members.action == "groups.members.list"
    assert bulk_import_status.action == "groups.members.bulk_import.status"
    assert bulk_import_template.action == "groups.members.bulk_import.template.download"
    assert bulk_import_template.parameters["output_path"] == r"D:\Temp\template.xlsx"
    assert bulk_import.action == "groups.members.bulk_import"
    assert bulk_import.parameters["file"] == r"D:\Temp\members.xlsx"
    assert member_read.action == "groups.member.read"
    assert member_read.parameters["member"] == "张三"
    assert member_permissions.action == "groups.member.permissions.read"
    assert member_permissions_update.action == "groups.member.permissions.update"
    assert member_permissions_update.parameters["changes"] == {"showBarcode": True}
    assert member_sources.action == "groups.member.sources.list"
    assert member_candidates.action == "groups.member.candidates.list"
    assert member_candidates.parameters["source"] == "71506605"
    assert member_candidates.parameters["search"] == "张三"
    assert members_add.action == "groups.members.add"
    assert members_add.parameters["puids"] == ["101", "102"]
    assert manager_add.action == "groups.member.manager_status.update"
    assert manager_add.parameters["manager"] is True
    assert manager_remove.parameters["manager"] is False
    assert member_remove.action == "groups.member.remove"
    assert creator_transfer.action == "groups.creator.transfer"
    assert clear_external.action == "groups.members.external.clear"
    assert folders.action == "groups.folders.list"
    assert tree.action == "groups.folders.tree"
    assert folder_create.action == "groups.folder.create"
    assert (
        folder_rename.action == "groups.folder.rename"
        and folder_rename.parameters["name"] == "课程"
    )
    assert folder_move.action == "groups.folder.move"
    assert (
        folder_top.action == "groups.folder.top_status.update"
        and folder_top.parameters["top"] is False
    )
    assert folder_delete.action == "groups.folder.delete"
    assert topics.action == "groups.topics.list" and topics.parameters["group"] == "课程小组"
    assert topic_search.parameters["search"] == "写作"
    assert topic_read.action == "groups.topic.read"
    assert topic_read.parameters["topic"] == "如何修改论文"
    assert topic_create.action == "groups.topic.create"
    assert topic_create.parameters["content"] == "先判断问题。"
    assert topic_delete.action == "groups.topic.delete"
    assert topic_choice.action == "groups.topic.choice_status.update"
    assert topic_choice.parameters["choice"] is True
    assert topic_choice_cancel.parameters["choice"] is False
    assert topic_praise.action == "groups.topic.praise_status.update"
    assert topic_praise.parameters["praised"] is True
    assert topic_praise_cancel.parameters["praised"] is False
    assert topics_score.action == "groups.topics.score.set"
    assert topics_score.parameters["topics"] == ["问题一", "问题二"]
    assert topics_score.parameters["score"] == 85
    assert topics_move.action == "groups.topics.move"
    assert topics_move.parameters["destination_folder"] == "讨论"
    assert topics_move.parameters["topics"] == ["问题一", "问题二"]
    assert topics_move_root.parameters["destination_folder"] == "root"
    assert topics_delete.action == "groups.topics.delete"
    assert topics_delete.parameters["topics"] == ["问题一", "问题二"]
    assert topic_update.action == "groups.topic.update"
    assert topic_update.parameters["title"] == "如何修改课程论文"
    assert topic_content.parameters["content"] == "先判断问题，再修改。"
    assert topic_reply.action == "groups.topic.reply.create"
    assert topic_reply.parameters["content"] == "先看论点。"
    assert nested_reply.parameters["reply_to"] == "先判断问题"
    assert reply_delete.action == "groups.topic.reply.delete"
    assert reply_delete.parameters["reply"] == "先看论点"
    assert reply_update.action == "groups.topic.reply.update"
    assert reply_update.parameters["content"] == "先看中心论点。"
    assert topic_folders.action == "groups.topic.folders.tree"
    assert topic_top.action == "groups.topic.top_status.update"
    assert topic_top.parameters["top"] is False
    assert topic_move.action == "groups.topic.move"
    assert topic_move.parameters["destination_folder"] == "讨论"
    assert topic_move_root.parameters["destination_folder"] == "root"
    assert topic_folder_create.action == "groups.topic.folder.create"
    assert topic_folder_create.parameters["parent_folder"] == "讨论"
    assert topic_folder_create.parameters["name"] == "论文"
    assert topic_folder_rename.action == "groups.topic.folder.rename"
    assert topic_folder_rename.parameters["name"] == "课程论文"
    assert topic_folder_move.action == "groups.topic.folder.move"
    assert topic_folder_move.parameters["destination_folder"] == "讨论"
    assert topic_folder_delete.action == "groups.topic.folder.delete"
    assert topic_folders_move.action == "groups.topic.folders.move"
    assert topic_folders_move.parameters["folders"] == ["论文", "读书会"]
    assert topic_folders_move.parameters["destination_folder"] == "讨论"
    assert topic_folders_move_root.parameters["destination_folder"] == "root"
    assert topic_folders_delete.action == "groups.topic.folders.delete"
    assert topic_folders_delete.parameters["folders"] == ["论文", "读书会"]
    assert topic_drafts.action == "groups.topic.drafts.list"
    assert topic_draft_read.action == "groups.topic.draft.read"
    assert topic_draft_read.parameters["draft"] == "draft-uuid"
    assert topic_draft_save.action == "groups.topic.draft.save"
    assert topic_draft_save.parameters["title"] == "论文讨论"
    assert topic_draft_update.parameters["draft"] == "draft-uuid"
    assert topic_draft_update.parameters["content"] == "先修改论点。"
    assert topic_draft_publish.action == "groups.topic.draft.publish"


def test_route_courseware_and_teaching_plan_operations() -> None:
    listing = route_command("查看《文体写作示例》的课件目录《Unit 1》")
    tree = route_command("查看《文体写作示例》的完整教案目录树")
    folder = route_command("在《文体写作示例》的课件目录《Unit 1》新建文件夹《Review》")
    cloud_import = route_command("将《文体写作示例》的云盘文件《Week 2.pdf》导入课件")
    rename = route_command("把《文体写作示例》的教案《Week 1》重命名为《Week One》")
    top = route_command("置顶《文体写作示例》的课件《Slides》")
    move = route_command("把《文体写作示例》的课件《Slides》《Guide》移动到《Archive》")
    copy = route_command("复制《文体写作示例》的教案《Week One》")
    delete = route_command("删除《文体写作示例》的课件《Slides》《Guide》")
    download = route_command(r"下载《文体写作示例》的课件《Slides》到《D:\Downloads\Slides.pptx》")
    recycle = route_command("查看《文体写作示例》的课件回收站")
    restore = route_command("从《文体写作示例》的课件回收站恢复《Slides》")
    permanent = route_command("从《文体写作示例》的教案回收站永久删除《Week One》")
    assert listing.action == "course_assets.items.list"
    assert listing.parameters["folder"] == "Unit 1"
    assert tree.action == "course_assets.tree.list"
    assert tree.parameters["kind"] == "teaching_plan"
    assert folder.action == "course_assets.folder.create"
    assert folder.parameters["parent"] == "Unit 1"
    assert cloud_import.action == "course_assets.cloud_files.import"
    assert cloud_import.parameters["resources"] == ["Week 2.pdf"]
    assert rename.action == "course_assets.item.rename"
    assert rename.parameters["name"] == "Week One"
    assert top.action == "course_assets.item.top_status.update"
    assert top.parameters["top"] is True
    assert move.action == "course_assets.items.move"
    assert move.parameters["assets"] == ["Slides", "Guide"]
    assert copy.action == "course_assets.item.copy"
    assert delete.action == "course_assets.items.delete"
    assert download.action == "course_assets.item.download"
    assert download.parameters["output_path"].endswith("Slides.pptx")
    assert recycle.action == "course_assets.recycle.list"
    assert restore.action == "course_assets.recycle.restore"
    assert permanent.action == "course_assets.recycle.items.delete"


def test_route_personal_group_label_reason_and_recycle_operations() -> None:
    labels = route_command("查看个人小组《课程小组》的标签")
    label_create = route_command("给个人小组《课程小组》添加标签《重点》")
    label_rename = route_command("把个人小组《课程小组》的标签《重点》重命名为《精华》")
    label_reorder = route_command("调整个人小组《课程小组》标签顺序为《精华》《复习》")
    label_delete = route_command("删除个人小组《课程小组》的标签《精华》")
    reasons = route_command("查看个人小组《课程小组》的删除原因")
    reason_create = route_command("给个人小组《课程小组》添加删除原因《内容重复》")
    reason_rename = route_command("把个人小组《课程小组》的删除原因《内容重复》改为《重复内容》")
    reason_delete = route_command("删除个人小组《课程小组》的删除原因《重复内容》")
    recycle = route_command("查看个人小组《课程小组》的回收站")
    restore = route_command("从个人小组《课程小组》回收站还原《10》《11》")
    permanent = route_command("从个人小组《课程小组》回收站永久删除《10》")
    empty = route_command("清空个人小组《课程小组》的回收站")
    assert labels.action == "groups.labels.list"
    assert label_create.action == "groups.label.create"
    assert label_create.parameters["name"] == "重点"
    assert label_rename.action == "groups.label.rename"
    assert label_reorder.parameters["labels"] == ["精华", "复习"]
    assert label_delete.action == "groups.labels.delete"
    assert reasons.action == "groups.deletion_reasons.list"
    assert reason_create.action == "groups.deletion_reason.create"
    assert reason_rename.action == "groups.deletion_reason.rename"
    assert reason_rename.parameters["name"] == "重复内容"
    assert reason_delete.action == "groups.deletion_reasons.delete"
    assert recycle.action == "groups.recycle.list"
    assert restore.action == "groups.recycle.restore"
    assert restore.parameters["items"] == ["10", "11"]
    assert permanent.action == "groups.recycle.items.delete"
    assert empty.action == "groups.recycle.empty"


def test_route_personal_group_export_operations() -> None:
    listing = route_command("查看个人小组《课程小组》的下载中心")
    create = route_command("导出个人小组《课程小组》的成员名单")
    download = route_command(r"下载个人小组《课程小组》的导出任务《21203》到《D:\Exports》并覆盖")
    retry = route_command("重新导出个人小组《课程小组》的任务《21203》")
    wait = route_command("等待个人小组《课程小组》的导出任务《21203》最多180秒")
    cancel = route_command("取消个人小组《课程小组》的导出任务《21203》")

    assert listing.action == "groups.exports.list"
    assert create.action == "groups.members.export.create"
    assert download.action == "groups.export.download"
    assert download.parameters["export"] == "21203"
    assert download.parameters["output_path"] == r"D:\Exports"
    assert download.parameters["overwrite"] is True
    assert retry.action == "groups.export.retry"
    assert wait.action == "groups.export.wait"
    assert wait.parameters["timeout_seconds"] == 180
    assert cancel.action == "groups.export.cancel"


def test_route_personal_group_activity_operations() -> None:
    listing = route_command("查看个人小组《课程小组》的未上线活动图")
    upload = route_command(r"上传小组活动图片《D:\Images\banner.png》")
    create = route_command("给个人小组《课程小组》新建未上线活动图《课程入口》")
    online_create = route_command(
        "给个人小组《课程小组》新建并上线活动图《课程入口》"
        "《https://example.com/app》《https://example.com/pc》"
        "《https://example.com/app.png》《https://example.com/pc.png》"
    )
    update = route_command("把个人小组《课程小组》的活动图《课程入口》修改为《新入口》")
    status = route_command("下线个人小组《课程小组》的活动图《课程入口》")
    reorder = route_command("调整个人小组《课程小组》活动图顺序为《入口二》《入口一》")
    delete = route_command("删除个人小组《课程小组》的活动图《课程入口》")
    assert listing.action == "groups.activities.list"
    assert listing.parameters["status"] == "offline"
    assert upload.action == "groups.activity.image.upload"
    assert upload.parameters["file"] == r"D:\Images\banner.png"
    assert create.action == "groups.activity.create" and create.parameters["online"] is False
    assert online_create.action == "groups.activity.create"
    assert online_create.parameters["pc_image_url"] == "https://example.com/pc.png"
    assert online_create.missing_fields == []
    assert update.action == "groups.activity.update"
    assert update.parameters["title"] == "新入口"
    assert status.action == "groups.activity.online_status.update"
    assert status.parameters["online"] is False
    assert reorder.action == "groups.activities.reorder"
    assert reorder.parameters["activities"] == ["入口二", "入口一"]
    assert delete.action == "groups.activity.delete"


def test_routes_capabilities_contact_departments_and_single_resource_download() -> None:
    capabilities = route_command("查看能力覆盖")
    assert capabilities.action == "capabilities.list"

    departments = route_command("列出单位通讯录《20001》的部门")
    assert departments.action == "contacts.departments.list"
    assert departments.parameters == {"fid": "20001", "department_type": "unit"}

    members = route_command("列出单位通讯录《20001》的部门《dept-8》成员")
    assert members.action == "contacts.department.members.list"
    assert members.parameters == {"fid": "20001", "department_id": "dept-8"}

    download = route_command(
        r"下载《英语写作示例》的资料文件《Unit 1.pdf》到《D:\Exports\Unit 1.pdf》"
    )
    assert download.action == "resources.file.download"
    assert download.parameters == {
        "course": "英语写作示例",
        "resource": "Unit 1.pdf",
        "output_path": r"D:\Exports\Unit 1.pdf",
    }
