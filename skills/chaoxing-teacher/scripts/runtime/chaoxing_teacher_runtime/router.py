from __future__ import annotations

import json
import re
from typing import Any

from .capabilities import COURSE_MODULES, SPACE_MODULES
from .models import CommandPlan

MODULE_ALIASES: dict[str, str] = {
    label.replace("​", ""): label.replace("​", "") for _, label in COURSE_MODULES
}
MODULE_ALIASES.update(
    {
        "课件": "课件",
        "教案": "教案",
        "章节": "章节",
        "资料": "资料",
        "通知": "通知",
        "公告": "通知",
        "讨论": "讨论",
        "话题": "讨论",
        "作业": "作业",
        "考试": "考试",
        "试卷": "考试",
        "题库": "题库",
        "统计": "统计",
        "管理": "管理",
        "直播": "直播课/见面课",
    }
)

SPACE_MODULE_ALIASES: dict[str, str] = {
    label.replace("\u200b", ""): label.replace("\u200b", "") for _, label in SPACE_MODULES
}

TEACHER_PERMISSION_ALIASES: dict[str, tuple[str, ...]] = {
    "activity": ("课堂活动权限",),
    "courseware": ("课件权限",),
    "allowedUsePpt": ("使用PPT权限", "PPT使用权限"),
    "editChapter": ("编辑章节权限", "章节编辑权限"),
    "information": ("课程信息查看权限",),
    "notice": ("通知权限", "公告权限"),
    "discuss": ("讨论权限", "话题权限"),
    "taskEngine": ("任务点权限",),
    "homework": ("作业权限",),
    "worklibrary": ("作业库权限",),
    "examine": ("考试权限",),
    "paperlibrary": ("试卷库权限",),
    "statistics": ("统计权限",),
    "courseset": ("课程设置权限",),
    "allowedExportQuestion": ("导出试题权限",),
    "qbank": ("题库权限",),
    "editwork": ("编辑作业权限",),
    "editWorkRelation": ("关联作业权限",),
    "piyuework": ("批阅作业权限", "批改作业权限"),
    "editexam": ("编辑考试权限",),
    "editExamRelation": ("关联考试权限",),
    "piyueexam": ("批阅考试权限", "批改考试权限"),
    "allowUnpubPaperPreview": ("预览未发布试卷权限",),
    "editQbankQuestion": ("编辑题库试题权限",),
    "fetchQbankQuestion": ("提取题库试题权限",),
    "editCoursedata": ("编辑课程资料权限",),
    "editCoursedataItemAdd": ("添加课程资料权限",),
    "editCoursedataItemEdit": ("修改课程资料权限",),
    "editCoursedataItemDelete": ("删除课程资料权限",),
    "downloadCoursedata": ("下载课程资料权限",),
    "allowedViewTestanswer": ("查看测验答案权限",),
    "allowedChapterOpenStatus": ("设置章节开放状态权限",),
    "clazzManage": ("班级管理权限",),
    "teamteacherManage": ("教学团队管理权限", "教师团队管理权限"),
    "addTeacher": ("添加教师权限",),
    "scoreWeightManage": ("成绩权重管理权限",),
    "courseManage": ("课程管理权限",),
    "clonecourse": ("克隆课程权限",),
    "mapcourse": ("映射课程权限",),
    "operationLogManage": ("操作日志管理权限",),
    "editGraph": ("编辑知识图谱权限",),
    "importCourseStatus": ("导入课程权限",),
    "importChapter": ("导入章节权限",),
    "importCourseGraph": ("导入课程图谱权限",),
    "importWorkLibrary": ("导入作业库权限",),
    "importExamLibrary": ("导入试卷库权限",),
    "importAiAssistantLibrary": ("导入AI助教库权限",),
    "importPracticeLibrary": ("导入练习库权限",),
    "importQBank": ("导入题库权限",),
    "importTeachingCourseware": ("导入教学课件权限",),
    "importResource": ("导入资源权限",),
    "editCoursePortal": ("编辑课程门户权限",),
    "editCourseInfoData": ("编辑课程信息权限",),
    "assignClazz": ("分配班级权限",),
    "editAiKnowledge": ("编辑AI知识权限",),
}

PERSONAL_GROUP_SETTING_ALIASES: dict[str, tuple[str, ...]] = {
    "showQrcode": ("小组二维码", "小组邀请码", "showQrcode"),
    "isCheck": ("加入审核", "成员加入审核", "isCheck"),
    "lock_add": ("只允许管理员发话题", "普通成员发话题", "lock_add"),
    "isShowCircleCloud": ("小组云盘", "isShowCircleCloud"),
    "isShowPrice": ("小组价格", "isShowPrice"),
    "showManager": ("显示管理员身份", "showManager"),
    "growthEnable": ("等级头衔", "成长值", "growthEnable"),
    "topicNeedCheck": ("话题审核", "topicNeedCheck"),
    "replyNeedCheck": ("回复审核", "replyNeedCheck"),
    "showDelReason": ("删除原因", "showDelReason"),
    "onlyMgrDeleteTopic": ("仅管理员删除话题", "onlyMgrDeleteTopic"),
    "onlyManagerReply": ("仅管理员回复", "onlyManagerReply"),
    "onlyMgrScore": ("仅管理员评分", "onlyMgrScore"),
    "onlyMgrShareTopic": ("仅管理员转发话题", "onlyMgrShareTopic"),
    "memberShowRank": ("仅管理员查看统计", "memberShowRank"),
    "sign_ban": ("小组禁言", "sign_ban"),
}

PERSONAL_GROUP_MANAGER_PERMISSION_ALIASES: dict[str, tuple[str, ...]] = {
    "showBarcode": ("管理二维码", "showBarcode"),
    "showLockAddSet": ("设置成员发话题权限", "showLockAddSet"),
    "showOnlyManagerReplySet": ("设置仅管理员回复", "showOnlyManagerReplySet"),
    "onlyMgrScoreSet": ("设置仅管理员评分", "onlyMgrScoreSet"),
    "memberShowRankSet": ("设置统计查看权限", "memberShowRankSet"),
    "modifyExpose": ("设置加入审核", "modifyExpose"),
    "showTopicNeedCheck": ("设置话题审核", "showTopicNeedCheck"),
    "showReplyNeedCheck": ("设置回复审核", "showReplyNeedCheck"),
    "showNeedDelReasonSet": ("设置删除原因", "showNeedDelReasonSet"),
    "showSignbanSet": ("设置禁言", "showSignbanSet"),
    "showGroupSquareSet": ("设置小组广场", "showGroupSquareSet"),
    "modifyShowPic": ("修改小组图片", "modifyShowPic"),
    "showSpeechSet": ("设置发言规则", "showSpeechSet"),
    "isShowCircleCloudButton": ("设置小组云盘", "isShowCircleCloudButton"),
    "isShowCircleChatButton": ("设置小组群聊", "isShowCircleChatButton"),
    "isShowPriceButton": ("设置小组价格", "isShowPriceButton"),
    "showOnlyMgrDeleteTopicSet": ("设置仅管理员删除话题", "showOnlyMgrDeleteTopicSet"),
    "showOnlyMgrShareTopicSet": ("设置仅管理员转发话题", "showOnlyMgrShareTopicSet"),
}

PERSONAL_GROUP_SPEAKING_RULE_ALIASES: dict[str, tuple[str, ...]] = {
    "leastTopicWord": ("话题最少字数", "leastTopicWord"),
    "addTopicNumber": ("累计话题数量", "addTopicNumber"),
    "addTopicNumberOfDay": ("每日话题数量", "addTopicNumberOfDay"),
    "replyInvitationWord": ("回复最少字数", "replyInvitationWord"),
    "replyTopicNumber": ("回复话题数量", "replyTopicNumber"),
}

LIVE_ROOM_SETTING_ALIASES: dict[str, tuple[str, ...]] = {
    "comments_enabled": ("评论", "互动评论"),
    "forwarding_enabled": ("转发",),
    "replay_enabled": ("回看", "回放"),
    "learning_app_only": ("仅学习通观看", "只在学习通观看"),
    "chat_content_review": ("聊天内容审核", "互动内容审核"),
    "login_required": ("登录后观看", "登录观看"),
    "picture_live": ("图片直播",),
    "show_viewer_count": ("观看人数", "在线人数"),
    "reservations_enabled": ("直播预约", "预约功能"),
    "preupload_enabled": ("预上传",),
}

LIVE_THEME_SETTING_ALIASES: dict[str, tuple[str, ...]] = {
    key: LIVE_ROOM_SETTING_ALIASES[key]
    for key in (
        "forwarding_enabled",
        "replay_enabled",
        "learning_app_only",
        "login_required",
    )
}

PERMISSION_TOGGLE_WORDS: tuple[tuple[str, bool], ...] = (
    ("不允许", False),
    ("关闭", False),
    ("禁用", False),
    ("取消", False),
    ("收回", False),
    ("撤销", False),
    ("去掉", False),
    ("开启", True),
    ("启用", True),
    ("打开", True),
    ("允许", True),
    ("授予", True),
    ("赋予", True),
    ("勾选", True),
)


def _extract_quoted(text: str) -> list[str]:
    return [
        match.group(1).strip()
        for match in re.finditer(r"[《“\"']([^》”\"']+)[》”\"']", text)
        if match.group(1).strip()
    ]


def _homework_question_type_from_text(text: str) -> str | None:
    aliases = (
        ("single_choice", ("单选题", "单选")),
        ("multiple_choice", ("多选题", "多选")),
        ("fill_blank", ("填空题", "填空")),
        ("true_false", ("判断题", "判断")),
        ("short_answer", ("简答题", "简答")),
    )
    for question_type, labels in aliases:
        if any(label in text for label in labels):
            return question_type
    return None


def _labeled_question_options(text: str) -> list[str]:
    matches = [
        (match.group(1).upper(), match.group(2).strip())
        for match in re.finditer(
            r"(?<![A-Za-z])([A-Z])\s*[=:：]\s*[《“\"']([^》”\"']+)[》”\"']",
            text,
            flags=re.IGNORECASE,
        )
    ]
    if not matches:
        return []
    expected = [chr(ord("A") + index) for index in range(len(matches))]
    return [
        value
        for (label, value), expected_label in zip(matches, expected, strict=True)
        if label == expected_label
    ]


def _teacher_permission_field(label: str) -> str | None:
    normalized = label.strip().lower()
    for field, aliases in TEACHER_PERMISSION_ALIASES.items():
        if normalized == field.lower() or label.strip() in aliases:
            return field
    return None


def _parse_teacher_permission_changes(text: str) -> dict[str, bool | int]:
    mentions: list[tuple[int, int, str]] = []
    for field, aliases in TEACHER_PERMISSION_ALIASES.items():
        labels = (*aliases, field)
        for label in labels:
            flags = re.IGNORECASE if label.isascii() else 0
            boundary = r"(?<![A-Za-z0-9_]){}(?![A-Za-z0-9_])" if label.isascii() else r"{}"
            for match in re.finditer(boundary.format(re.escape(label)), text, flags):
                mentions.append((match.start(), match.end(), field))

    selected: list[tuple[int, int, str]] = []
    occupied: list[tuple[int, int]] = []
    for start, end, field in sorted(mentions, key=lambda item: (-(item[1] - item[0]), item[0])):
        if any(start < used_end and end > used_start for used_start, used_end in occupied):
            continue
        selected.append((start, end, field))
        occupied.append((start, end))
    selected.sort()

    toggles: list[tuple[int, int, bool]] = []
    toggle_occupied: list[tuple[int, int]] = []
    for word, value in PERMISSION_TOGGLE_WORDS:
        for match in re.finditer(re.escape(word), text):
            start, end = match.span()
            if any(
                start < used_end and end > used_start for used_start, used_end in toggle_occupied
            ):
                continue
            toggles.append((start, end, value))
            toggle_occupied.append((start, end))
    toggles.sort()

    raw_values = [
        int(match.group(1)) for match in re.finditer(r"(?:设为|设置为|改为)\s*(-?\d+)", text)
    ]
    if len(selected) == 1 and raw_values:
        return {selected[0][2]: raw_values[-1]}

    distinct_toggle_values = {value for _, _, value in toggles}
    if re.search(r"全部权限|所有权限", text) and len(distinct_toggle_values) == 1:
        value = distinct_toggle_values.pop()
        return {field: value for field in TEACHER_PERMISSION_ALIASES}
    if len(distinct_toggle_values) == 1:
        value = distinct_toggle_values.pop()
        return {field: value for _, _, field in selected}

    changes: dict[str, bool | int] = {}
    for start, end, field in selected:
        if not toggles:
            continue
        closest = min(
            toggles,
            key=lambda toggle: min(abs(start - toggle[1]), abs(toggle[0] - end)),
        )
        changes[field] = closest[2]
    return changes


def _parse_alias_boolean_changes(
    text: str,
    aliases_by_field: dict[str, tuple[str, ...]],
) -> dict[str, bool]:
    mentions: list[tuple[int, int, str]] = []
    for field, aliases in aliases_by_field.items():
        for label in aliases:
            flags = re.IGNORECASE if label.isascii() else 0
            for match in re.finditer(re.escape(label), text, flags):
                mentions.append((match.start(), match.end(), field))
    toggles: list[tuple[int, int, bool]] = []
    for word, value in PERMISSION_TOGGLE_WORDS:
        toggles.extend((match.start(), match.end(), value) for match in re.finditer(word, text))
    if not toggles:
        return {}
    distinct = {value for _, _, value in toggles}
    if len(distinct) == 1:
        value = distinct.pop()
        return {field: value for _, _, field in mentions}
    changes: dict[str, bool] = {}
    for start, end, field in mentions:
        closest = min(
            toggles,
            key=lambda toggle: min(abs(start - toggle[1]), abs(toggle[0] - end)),
        )
        changes[field] = closest[2]
    return changes


def _parse_personal_group_speaking_rule_changes(text: str) -> dict[str, int]:
    changes: dict[str, int] = {}
    for field, aliases in PERSONAL_GROUP_SPEAKING_RULE_ALIASES.items():
        for label in aliases:
            match = re.search(
                re.escape(label) + r".{0,16}?(?:设为|设置为|改为|为)?\s*[《“\"']?(\d+)",
                text,
                flags=re.IGNORECASE if label.isascii() else 0,
            )
            if match:
                changes[field] = int(match.group(1))
                break
    return changes


def route_command(command: str) -> CommandPlan:
    text = " ".join(command.strip().split())
    if not text:
        return CommandPlan(command, None, message="命令不能为空。")

    if text in {
        "能力清单",
        "能力列表",
        "能力目录",
        "能力覆盖",
        "查看能力覆盖",
        "支持什么",
        "能做什么",
    } or re.fullmatch(
        r"(?:查看|列出|显示)?(?:学习通|超星|代理)?(?:的)?能力(?:清单|列表|目录|覆盖)",
        text,
    ):
        return CommandPlan(text, "capabilities.list", confidence=0.99)

    if re.search(r"(?:重新|再次|立即|现在)?登录(?:学习通|超星)|刷新登录", text) and not re.search(
        r"检查|查看|确认|状态|是谁", text
    ):
        quoted = _extract_quoted(text)
        parameters: dict[str, str] = {}
        account_match = re.search(
            r"(?:账号|用户名|手机号)(?:为|是|：|:)?\s*[《“\"']([^》”\"']+)[》”\"']",
            text,
        )
        password_match = re.search(
            r"密码(?:为|是|：|:)?\s*[《“\"']([^》”\"']+)[》”\"']",
            text,
        )
        course_match = re.search(
            r"(?:课程|课)(?:为|是|：|:)?\s*[《“\"']([^》”\"']+)[》”\"']",
            text,
        )
        if account_match:
            parameters["username"] = account_match.group(1)
        if password_match:
            parameters["password"] = password_match.group(1)
        target_match = re.search(r"https://[^\s》”\"']+", text, flags=re.I)
        if target_match:
            parameters["target_url"] = target_match.group(0).rstrip("，。；;,.)）]")
        elif course_match and re.search(r"直播课|见面课|直播", text):
            parameters["learning_course"] = course_match.group(1)
            parameters["learning_module"] = "直播课/见面课"
        if "username" not in parameters and not course_match and quoted:
            parameters["username"] = quoted[0]
        if "password" not in parameters and not course_match and len(quoted) >= 2:
            parameters["password"] = quoted[1]
        missing = [key for key in ("username", "password") if key not in parameters]
        return CommandPlan(
            text,
            "session.login",
            parameters=parameters,
            confidence=0.99 if not missing else 0.88,
            missing_fields=missing,
            message=(
                "当前未登录；请先询问‘请输入学习通账号。’，收到后再询问‘请输入学习通密码。’，然后直接登录并继续原请求。"
                if missing
                else ""
            ),
        )

    if re.search(r"(检查|查看|确认).*(登录|会话|账号)|(登录|会话|账号).*(状态|是谁)", text):
        return CommandPlan(text, "session.check", confidence=0.98)

    knowledge_hub_intent = bool(
        re.search(r"AI\s*知识库|知识库(?:文档|文件|统计|状态)|课程.{0,20}知识库", text, re.I)
    )
    if knowledge_hub_intent:
        quoted = _extract_quoted(text)
        course_match = re.search(
            r"(?:课程|课)(?:为|是|：|:)?\s*[《“\"']([^》”\"']+)[》”\"']",
            text,
        )
        base: dict[str, Any] = {}
        operands = list(quoted)
        if course_match:
            base["course"] = course_match.group(1)
            if course_match.group(1) in operands:
                operands.remove(course_match.group(1))
        elif operands:
            base["course"] = operands.pop(0)
        clazz_match = re.search(
            r"(?:班级|教学班)(?:为|是|：|:)?\s*[《“\"']([^》”\"']+)[》”\"']",
            text,
        )
        if clazz_match:
            base["clazz"] = clazz_match.group(1)
            if clazz_match.group(1) in operands:
                operands.remove(clazz_match.group(1))

        if "行业库" in text:
            base["module"] = "INDUSTRY_BASE"
        elif "知识图谱库" in text:
            base["module"] = "KNOWLEDGE_GRAPH"
        elif re.search(r"AI库模块|AI基础库", text, re.I):
            base["module"] = "AI_BASE"
        else:
            base["module"] = "NORMAL_BASE"

        def hub_missing(*keys: str) -> list[str]:
            return [key for key in keys if key not in base]

        document_intent = "知识库" in text and ("文档" in text or "文件" in text)
        if document_intent:
            document_operands = list(operands)
            knowledge_base_match = re.search(
                r"知识库(?:为|是|：|:)?\s*[《“\"']([^》”\"']+)[》”\"']",
                text,
            )
            if knowledge_base_match:
                base["base"] = knowledge_base_match.group(1)
                if knowledge_base_match.group(1) in document_operands:
                    document_operands.remove(knowledge_base_match.group(1))
            elif document_operands:
                base["base"] = document_operands.pop(0)
            if re.search(r"上传|导入|添加文件|添加文档", text):
                path_match = re.search(
                    r"(?P<path>[A-Za-z]:\\[^\r\n，,》”\"']+|/[^\r\n，,》”\"']+)",
                    text,
                )
                if document_operands:
                    base["file"] = document_operands[0]
                elif path_match:
                    base["file"] = path_match.group("path").strip().strip("。；;")
                classify_match = re.search(r"分类(?:ID)?\s*[=:：]?\s*(\d+)", text, re.I)
                if classify_match:
                    base["classify_id"] = classify_match.group(1)
                required = hub_missing("course", "base", "file")
                return CommandPlan(
                    text,
                    "knowledge_hub.document.upload",
                    parameters=base,
                    confidence=0.98 if not required else 0.76,
                    missing_fields=required,
                    message="请依次用书名号提供课程、知识库和本地文件路径。" if required else "",
                )
            if re.search(r"下载|保存到本地", text):
                if document_operands:
                    base["document"] = document_operands[0]
                output_match = re.search(
                    r"(?:保存到|下载到|输出到|到)\s*[《“\"']?"
                    r"(?P<path>[A-Za-z]:\\[^\r\n，,》”\"']+|/[^\r\n，,》”\"']+)",
                    text,
                )
                if len(document_operands) >= 2:
                    base["output_path"] = document_operands[1]
                elif output_match:
                    base["output_path"] = output_match.group("path").strip().strip("。；;")
                base["overwrite"] = bool(re.search(r"覆盖|替换已有|允许覆写", text))
                required = hub_missing("course", "base", "document", "output_path")
                return CommandPlan(
                    text,
                    "knowledge_hub.document.download",
                    parameters=base,
                    confidence=0.98 if not required else 0.76,
                    missing_fields=required,
                    message="请依次提供课程、知识库、文档和本地保存路径。" if required else "",
                )
            if re.search(r"删除|移除", text):
                if document_operands:
                    base["document"] = document_operands[0]
                required = hub_missing("course", "base", "document")
                return CommandPlan(
                    text,
                    "knowledge_hub.document.delete",
                    parameters=base,
                    confidence=0.98 if not required else 0.78,
                    missing_fields=required,
                    message="请依次用书名号提供课程、知识库和文档。" if required else "",
                )
            search_match = re.search(r"搜索.{0,6}?[《“\"']([^》”\"']+)[》”\"']", text)
            if search_match:
                base["search"] = search_match.group(1)
            page_match = re.search(r"第\s*(\d+)\s*页", text)
            if page_match:
                base["page"] = int(page_match.group(1))
            required = hub_missing("course", "base")
            return CommandPlan(
                text,
                "knowledge_hub.documents.list",
                parameters=base,
                confidence=0.97 if not required else 0.78,
                missing_fields=required,
                message="请依次用书名号提供课程和知识库。" if required else "",
            )

        if re.search(r"状态|开放情况|模块配置|字典", text):
            required = hub_missing("course")
            return CommandPlan(
                text,
                "knowledge_hub.status.read",
                parameters=base,
                confidence=0.97 if not required else 0.8,
                missing_fields=required,
                message="请用书名号提供课程。" if required else "",
            )
        if re.search(r"统计|文件数|分段字符", text):
            required = hub_missing("course")
            return CommandPlan(
                text,
                "knowledge_hub.statistics.read",
                parameters=base,
                confidence=0.97 if not required else 0.8,
                missing_fields=required,
                message="请用书名号提供课程。" if required else "",
            )
        if re.search(r"新建|创建|新增", text):
            if operands:
                base["name"] = operands[0]
            if len(operands) >= 2:
                base["description"] = operands[1]
            if "表格库" in text:
                base["category"] = 4
            elif "图谱库" in text or "图文库" in text:
                base["category"] = 9
            elif "图片库" in text:
                base["category"] = 10
            else:
                base["category"] = 0
            required = hub_missing("course", "name", "description")
            return CommandPlan(
                text,
                "knowledge_hub.base.create",
                parameters=base,
                confidence=0.98 if not required else 0.76,
                missing_fields=required,
                message="请依次用书名号提供课程、知识库名称和描述。" if required else "",
            )
        if re.search(r"重命名|改名|修改|编辑|更新描述", text):
            if operands:
                base["base"] = operands[0]
            if re.search(r"重命名|改名", text) and len(operands) >= 2:
                base["name"] = operands[1]
            description_match = re.search(
                r"(?:描述|简介)(?:改为|修改为|设为|为)?\s*[《“\"']([^》”\"']*)[》”\"']",
                text,
            )
            if description_match:
                base["description"] = description_match.group(1)
            required = hub_missing("course", "base")
            if not any(key in base for key in ("name", "description", "cover", "split_rule")):
                required.append("changes")
            return CommandPlan(
                text,
                "knowledge_hub.base.update",
                parameters=base,
                confidence=0.97 if not required else 0.76,
                missing_fields=required,
                message="请提供课程、知识库和要修改的字段。" if required else "",
            )
        if re.search(r"共享|取消共享|停止共享", text):
            if operands:
                base["base"] = operands[0]
            base["shared"] = not bool(re.search(r"取消共享|停止共享|不共享", text))
            required = hub_missing("course", "base")
            return CommandPlan(
                text,
                "knowledge_hub.base.share.update",
                parameters=base,
                confidence=0.98 if not required else 0.78,
                missing_fields=required,
                message="请依次用书名号提供课程和知识库。" if required else "",
            )
        if re.search(r"优先", text):
            if operands:
                base["base"] = operands[0]
            base["priority"] = not bool(re.search(r"取消|关闭|移除|不优先", text))
            required = hub_missing("course", "base")
            return CommandPlan(
                text,
                "knowledge_hub.base.priority.update",
                parameters=base,
                confidence=0.98 if not required else 0.78,
                missing_fields=required,
                message="请依次用书名号提供课程和知识库。" if required else "",
            )
        if re.search(r"启用|停用|禁用|可用状态|关闭知识库", text):
            if operands:
                base["base"] = operands[0]
            base["enabled"] = not bool(re.search(r"停用|禁用|关闭", text))
            required = hub_missing("course", "base")
            return CommandPlan(
                text,
                "knowledge_hub.base.availability.update",
                parameters=base,
                confidence=0.98 if not required else 0.78,
                missing_fields=required,
                message="请依次用书名号提供课程和知识库。" if required else "",
            )
        if re.search(r"删除|移除", text):
            if operands:
                base["base"] = operands[0]
            required = hub_missing("course", "base")
            return CommandPlan(
                text,
                "knowledge_hub.base.delete",
                parameters=base,
                confidence=0.98 if not required else 0.78,
                missing_fields=required,
                message="请依次用书名号提供课程和知识库。" if required else "",
            )
        if re.search(r"详情|读取单个|查看单个", text):
            if operands:
                base["base"] = operands[0]
            required = hub_missing("course", "base")
            return CommandPlan(
                text,
                "knowledge_hub.base.read",
                parameters=base,
                confidence=0.98 if not required else 0.78,
                missing_fields=required,
                message="请依次用书名号提供课程和知识库。" if required else "",
            )
        search_match = re.search(r"搜索.{0,6}?[《“\"']([^》”\"']+)[》”\"']", text)
        if search_match:
            base["search"] = search_match.group(1)
        required = hub_missing("course")
        return CommandPlan(
            text,
            "knowledge_hub.bases.list",
            parameters=base,
            confidence=0.96 if not required else 0.8,
            missing_fields=required,
            message="请用书名号提供课程。" if required else "",
        )

    if re.search(r"AI指令|快捷指令|指令分组|指令推荐|推荐指令", text, re.I):
        quoted = _extract_quoted(text)
        base: dict[str, Any] = {"course": quoted[0]} if quoted else {}

        def missing(*keys: str) -> list[str]:
            return [key for key in keys if key not in base]

        def role_type() -> int:
            if re.search(r"均不开放|都不开放|两端关闭|教师和学生都关闭", text):
                return 3
            if re.search(r"教师.{0,6}学生|学生.{0,6}教师|两端|师生", text):
                return 2
            if "学生端" in text or re.search(r"只.{0,3}学生", text):
                return 1
            return 0

        if re.search(r"指令推荐|推荐指令", text):
            if re.search(r"引用|添加|加入", text):
                if len(quoted) >= 2:
                    base["recommendation"] = quoted[1]
                if len(quoted) >= 3:
                    base["group"] = quoted[2]
                required = [key for key in ("course", "recommendation", "group") if key not in base]
                return CommandPlan(
                    text,
                    "ai_workbench.recommendation.add",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请依次用书名号提供课程、推荐指令和目标分组。" if required else "",
                )
            page_match = re.search(r"第\s*(\d+)\s*页", text)
            if page_match:
                base["page"] = int(page_match.group(1))
            required = missing("course")
            return CommandPlan(
                text,
                "ai_workbench.recommendations.list",
                parameters=base,
                confidence=0.97 if not required else 0.8,
                missing_fields=required,
                message="请用书名号提供课程。" if required else "",
            )

        group_contains_command = bool(
            re.search(r"指令分组[《“\"'][^》”\"']+[》”\"'].{0,12}(?:中|内|里的?).*指令", text)
            or re.search(r"(?:AI指令|快捷指令)[《“\"']", text)
        )
        if "指令分组" in text and not group_contains_command:
            if re.search(r"调整|排序|顺序", text):
                if len(quoted) >= 2:
                    base["groups"] = quoted[1:]
                required = [key for key in ("course", "groups") if key not in base]
                return CommandPlan(
                    text,
                    "ai_workbench.group.reorder",
                    parameters=base,
                    confidence=0.97 if not required else 0.78,
                    missing_fields=required,
                    message="请依次用书名号提供课程和包含系统分组在内的完整分组顺序。"
                    if required
                    else "",
                )
            if re.search(r"重命名|改名", text):
                if len(quoted) >= 2:
                    base["group"] = quoted[1]
                if len(quoted) >= 3:
                    base["name"] = quoted[2]
                required = [key for key in ("course", "group", "name") if key not in base]
                return CommandPlan(
                    text,
                    "ai_workbench.group.rename",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请依次用书名号提供课程、原分组和新名称。" if required else "",
                )
            if re.search(r"删除|移除", text):
                if len(quoted) >= 2:
                    base["group"] = quoted[1]
                if re.search(r"允许.{0,4}非空|连同.{0,4}指令", text):
                    base["allow_nonempty"] = True
                required = [key for key in ("course", "group") if key not in base]
                return CommandPlan(
                    text,
                    "ai_workbench.group.delete",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请依次用书名号提供课程和分组。" if required else "",
                )
            if re.search(r"新建|创建", text):
                if len(quoted) >= 2:
                    base["name"] = quoted[1]
                required = [key for key in ("course", "name") if key not in base]
                return CommandPlan(
                    text,
                    "ai_workbench.group.create",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请依次用书名号提供课程和新分组名称。" if required else "",
                )
            required = missing("course")
            return CommandPlan(
                text,
                "ai_workbench.groups.list",
                parameters=base,
                confidence=0.97 if not required else 0.8,
                missing_fields=required,
                message="请用书名号提供课程。" if required else "",
            )

        if re.search(r"发布|公开|取消发布|取消公开", text):
            if len(quoted) >= 2:
                base["command"] = quoted[1]
            base["published"] = not bool(re.search(r"取消|撤销|下线", text))
            required = [key for key in ("course", "command") if key not in base]
            return CommandPlan(
                text,
                "ai_workbench.command.publish_status.update",
                parameters=base,
                confidence=0.99 if not required else 0.8,
                missing_fields=required,
                message="请依次用书名号提供课程和 AI 指令。" if required else "",
            )
        if re.search(r"删除|移除", text):
            if len(quoted) >= 2:
                base["command"] = quoted[1]
            required = [key for key in ("course", "command") if key not in base]
            return CommandPlan(
                text,
                "ai_workbench.command.delete",
                parameters=base,
                confidence=0.98 if not required else 0.8,
                missing_fields=required,
                message="请依次用书名号提供课程和 AI 指令。" if required else "",
            )
        if re.search(r"移动|移到|放入", text):
            if len(quoted) >= 2:
                base["command"] = quoted[1]
            if len(quoted) >= 3:
                base["target_group"] = quoted[2]
            required = [key for key in ("course", "command", "target_group") if key not in base]
            return CommandPlan(
                text,
                "ai_workbench.command.move",
                parameters=base,
                confidence=0.98 if not required else 0.8,
                missing_fields=required,
                message="请依次用书名号提供课程、AI 指令和目标分组。" if required else "",
            )
        if re.search(r"调整|排序|顺序", text):
            if len(quoted) >= 2:
                base["group"] = quoted[1]
            if len(quoted) >= 3:
                base["commands"] = quoted[2:]
            base["role_type"] = 1 if "学生" in text and "教师" not in text else 0
            required = [key for key in ("course", "group", "commands") if key not in base]
            return CommandPlan(
                text,
                "ai_workbench.command.reorder",
                parameters=base,
                confidence=0.97 if not required else 0.78,
                missing_fields=required,
                message="请依次用书名号提供课程、分组和该角色的完整指令顺序。" if required else "",
            )
        if re.search(r"新建|创建", text):
            keys = ("group", "name", "content", "explanation")
            for index, key in enumerate(keys, 1):
                if len(quoted) > index:
                    base[key] = quoted[index]
            if len(quoted) >= 6:
                base["prompt_words"] = quoted[5]
            base["role_type"] = role_type()
            required = [
                key
                for key in ("course", "group", "name", "content", "explanation")
                if key not in base
            ]
            return CommandPlan(
                text,
                "ai_workbench.command.create",
                parameters=base,
                confidence=0.98 if not required else 0.78,
                missing_fields=required,
                message="请依次用书名号提供课程、分组、指令名称、指令内容和说明。"
                if required
                else "",
            )
        if re.search(r"修改|编辑|更新|开放角色", text):
            if len(quoted) >= 2:
                base["command"] = quoted[1]
            labeled_fields = {
                "name": r"(?:名称|改名)",
                "content": r"(?:指令内容|标准问题)",
                "explanation": r"(?:说明|描述)",
                "prompt_words": r"(?:提示词|大模型提示词)",
            }
            for key, label in labeled_fields.items():
                match = re.search(label + r".{0,8}?[《“\"']([^》”\"']*)[》”\"']", text)
                if match:
                    base[key] = match.group(1)
            if re.search(r"教师端|学生端|两端|师生|均不开放|都不开放", text):
                base["role_type"] = role_type()
            required = [key for key in ("course", "command") if key not in base]
            if not any(
                key in base
                for key in (
                    "name",
                    "content",
                    "explanation",
                    "prompt_words",
                    "role_type",
                )
            ):
                required.append("changes")
            return CommandPlan(
                text,
                "ai_workbench.command.update",
                parameters=base,
                confidence=0.97 if not required else 0.78,
                missing_fields=required,
                message="请提供课程、AI 指令及要修改的字段。" if required else "",
            )
        if re.search(r"详情|读取|查看单个", text) and len(quoted) >= 2:
            base["command"] = quoted[1]
            return CommandPlan(
                text,
                "ai_workbench.command.read",
                parameters=base,
                confidence=0.98,
            )
        if len(quoted) >= 2:
            base["group"] = quoted[1]
        search_match = re.search(r"搜索.{0,6}?[《“\"']([^》”\"']+)[》”\"']", text)
        if search_match:
            base["search"] = search_match.group(1)
        required = missing("course")
        return CommandPlan(
            text,
            "ai_workbench.commands.list",
            parameters=base,
            confidence=0.96 if not required else 0.8,
            missing_fields=required,
            message="请用书名号提供课程。" if required else "",
        )

    graph_intent = bool(
        "课程图谱" in text
        or "课程知识图谱" in text
        or ("知识图谱" in text and "题库" not in text)
        or re.search(
            r"图谱标签|图谱节点|图谱分类|图谱关系|图谱模型|图谱模式|图谱任务|自定义图谱|"
            r"学习地图|知识列表|问题图谱|目标图谱|课程思政图谱|岗位能力图谱|"
            r"知识点卡片|教学目标|图谱学时|知识点学时|分类关系|纳入自测|"
            r"图谱自测|微课预览|微课缩放|技能点|能力点",
            text,
        )
    )
    if graph_intent and not re.search(r"我学的课|我学的课程|我学课程|学生课程", text):
        quoted = _extract_quoted(text)
        base: dict[str, Any] = {"course": quoted[0]} if quoted else {}
        operands = quoted[1:]
        clazz_match = re.search(
            r"(?:班级|教学班)(?:为|是|：|:)?\s*[《“\"']([^》”\"']+)[》”\"']",
            text,
        )
        if clazz_match:
            base["clazz"] = clazz_match.group(1)
            if clazz_match.group(1) in operands:
                operands.remove(clazz_match.group(1))

        def graph_missing(*keys: str) -> list[str]:
            return [key for key in keys if key not in base]

        graph_event_intent = bool(
            re.search(r"(?:课程|知识)?图谱.{0,6}(?:任务)?事件|图谱任务|任务事件", text)
        )
        if graph_event_intent:

            def graph_event_conditions() -> None:
                if "知识点掌握率" in text or "掌握率" in text:
                    base["topic_condition"] = 0
                elif "知识点完成率" in text or "完成率" in text:
                    base["topic_condition"] = 1
                for marker, value in (
                    ("大于等于", 3),
                    ("不低于", 3),
                    ("至少", 3),
                    ("小于等于", 4),
                    ("不高于", 4),
                    ("至多", 4),
                    ("大于", 1),
                    ("超过", 1),
                    ("小于", 2),
                    ("低于", 2),
                    ("等于", 0),
                    ("区间", 7),
                    ("介于", 7),
                ):
                    if marker in text:
                        base["set_condition"] = value
                        break
                percentages = [
                    int(round(float(value))) for value in re.findall(r"(\d+(?:\.\d+)?)\s*%", text)
                ]
                if percentages:
                    base["percent1"] = percentages[0]
                    if len(percentages) >= 2:
                        base["percent2"] = percentages[1]

            if re.search(r"删除|移除", text):
                if operands:
                    base["event"] = operands[0]
                required = graph_missing("course", "event")
                return CommandPlan(
                    text,
                    "knowledge_graph.event.delete",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请依次用书名号提供课程和要删除的图谱任务事件。" if required else "",
                )
            if re.search(r"新建|创建|添加", text):
                if operands:
                    base["name"] = operands[0]
                graph_event_conditions()
                labels = operands[1:] if len(operands) >= 2 else []
                if labels:
                    execute_module = 1 if "微课资料" in text else 0
                    base["executions"] = [
                        {"label": label, "execute_module": execute_module} for label in labels[:3]
                    ]
                required = graph_missing(
                    "course",
                    "name",
                    "topic_condition",
                    "set_condition",
                    "percent1",
                    "executions",
                )
                return CommandPlan(
                    text,
                    "knowledge_graph.event.create",
                    parameters=base,
                    confidence=0.97 if not required else 0.76,
                    missing_fields=required,
                    message=(
                        "请提供课程、事件名、完成率或掌握率条件、百分比，"
                        "以及用书名号列出的 1 至 3 个执行标签。"
                        if required
                        else ""
                    ),
                )
            if re.search(r"重命名|改名|修改|编辑|调整", text):
                if operands:
                    base["event"] = operands[0]
                if len(operands) >= 2 and re.search(r"重命名|改名", text):
                    base["name"] = operands[1]
                graph_event_conditions()
                if re.search(r"学习路径|微课资料", text):
                    labels = operands[2:] if "name" in base else operands[1:]
                    if labels:
                        execute_module = 1 if "微课资料" in text else 0
                        base["executions"] = [
                            {"label": label, "execute_module": execute_module}
                            for label in labels[:3]
                        ]
                required = graph_missing("course", "event")
                if not any(
                    key in base
                    for key in (
                        "name",
                        "topic_condition",
                        "set_condition",
                        "percent1",
                        "percent2",
                        "executions",
                    )
                ):
                    required.append("changes")
                return CommandPlan(
                    text,
                    "knowledge_graph.event.update",
                    parameters=base,
                    confidence=0.97 if not required else 0.76,
                    missing_fields=required,
                    message="请提供课程、图谱任务事件及要修改的条件或执行动作。"
                    if required
                    else "",
                )
            search_match = re.search(r"搜索.{0,6}?[《“\"']([^》”\"']+)[》”\"']", text)
            if search_match:
                base["search"] = search_match.group(1)
            required = graph_missing("course")
            return CommandPlan(
                text,
                "knowledge_graph.events.list",
                parameters=base,
                confidence=0.98 if not required else 0.8,
                missing_fields=required,
                message="请用书名号提供课程。" if required else "",
            )

        if re.search(r"导出|下载", text) and re.search(r"图谱|知识点", text):
            format_aliases = (
                ("xmind", "xmind"),
                ("excel", "excel"),
                ("xlsx", "xlsx"),
                ("csv", "csv"),
                ("psg", "psg"),
                ("json", "json"),
                ("pdf", "pdf"),
                ("rdf", "rdf"),
            )
            lowered = text.lower()
            export_format = next(
                (value for marker, value in format_aliases if marker in lowered),
                None,
            )
            if export_format:
                base["format"] = export_format
            output_match = re.search(
                r"(?:保存到|下载到|输出到|导出到|到)\s*[《“\"']?"
                r"(?P<path>[A-Za-z]:\\[^\r\n，,》”\"']+|/[^\r\n，,》”\"']+)",
                text,
            )
            if output_match:
                output_path = output_match.group("path").strip().strip("。；;")
                output_path = re.sub(r"\s+并(?:覆盖|替换已有|允许覆写).*$", "", output_path).strip()
                base["output_path"] = output_path
            elif operands and re.match(r"^(?:[A-Za-z]:\\|/)", operands[-1]):
                base["output_path"] = operands[-1]
            for model_name in (
                "学习地图",
                "知识列表",
                "问题图谱",
                "目标图谱",
                "课程思政图谱",
                "岗位能力图谱",
                "知识图谱",
            ):
                if model_name in text:
                    base["model"] = model_name
                    break
            base["overwrite"] = bool(re.search(r"覆盖|替换已有|允许覆写", text))
            required = graph_missing("course", "format", "output_path")
            return CommandPlan(
                text,
                "knowledge_graph.export.download",
                parameters=base,
                confidence=0.98 if not required else 0.78,
                missing_fields=required,
                message="请提供课程、导出格式及本地保存路径。" if required else "",
            )

        graph_advanced_settings_intent = bool(
            re.search(
                r"图谱高级设置|知识点卡片|教学目标|图谱学时|知识点学时|"
                r"分类关系|纳入自测|图谱自测|微课预览|微课缩放|微课缩放模式",
                text,
            )
        )
        if graph_advanced_settings_intent:
            update_intent = bool(
                re.search(r"修改|调整|设为|开启|打开|启用|关闭|关掉|隐藏|禁用|停用", text)
            ) and not bool(re.search(r"查看|读取|当前|是什么|有哪些", text))
            if update_intent:
                settings = {
                    "topic_card": r"知识点卡片",
                    "teach_target": r"教学目标",
                    "study_hours_enabled": r"(?:图谱|知识点)?学时",
                    "classify_relation_data": r"分类关系",
                    "selftest_included": r"纳入自测|图谱自测|自测",
                    "micro_preview": r"微课预览",
                    "micro_scale_mode": r"微课缩放(?:模式)?|缩放模式",
                }
                off_pattern = r"关闭|关掉|不显示|隐藏|禁用|停用|取消|不纳入|设为关"
                on_pattern = r"开启|打开|启用|显示出来|纳入|设为开"

                def nearest_toggle(field_match: re.Match[str]) -> bool | None:
                    candidates: list[tuple[int, int, bool]] = []
                    for priority, (toggle_pattern, value) in enumerate(
                        ((off_pattern, False), (on_pattern, True))
                    ):
                        for toggle_match in re.finditer(toggle_pattern, text):
                            if toggle_match.end() <= field_match.start():
                                distance = field_match.start() - toggle_match.end()
                            elif toggle_match.start() >= field_match.end():
                                distance = toggle_match.start() - field_match.end()
                            else:
                                distance = 0
                            if distance <= 12:
                                candidates.append((distance, priority, value))
                    return min(candidates)[2] if candidates else None

                for key, pattern in settings.items():
                    match = re.search(pattern, text)
                    if not match:
                        continue
                    value = nearest_toggle(match)
                    if value is not None:
                        base[key] = value
                required = graph_missing("course")
                if not any(key in base for key in settings):
                    required.append("changes")
                return CommandPlan(
                    text,
                    "knowledge_graph.advanced_settings.update",
                    parameters=base,
                    confidence=0.97 if not required else 0.78,
                    missing_fields=required,
                    message="请提供课程及至少一项图谱高级设置的开关值。" if required else "",
                )
            required = graph_missing("course")
            return CommandPlan(
                text,
                "knowledge_graph.advanced_settings.read",
                parameters=base,
                confidence=0.98 if not required else 0.8,
                missing_fields=required,
                message="请用书名号提供课程。" if required else "",
            )

        graph_model_intent = bool(
            re.search(
                r"图谱模型|图谱模式|自定义图谱|学习地图|知识列表|问题图谱|"
                r"目标图谱|课程思政图谱|岗位能力图谱",
                text,
            )
            or (
                "知识图谱" in text
                and re.search(r"开放班级|开放给.{0,4}班级|可见班级|班级范围|对哪些班级", text)
            )
        )
        if graph_model_intent:
            named_modes = (
                "学习地图",
                "知识列表",
                "问题图谱",
                "目标图谱",
                "课程思政图谱",
                "岗位能力图谱",
                "知识图谱",
            )

            def inferred_model() -> str | None:
                named = next((name for name in named_modes if name in text), None)
                if named:
                    return named
                if operands:
                    return operands[0]
                return None

            if re.search(r"开放班级|开放给.{0,4}班级|可见班级|班级范围|对哪些班级", text):
                if clazz_match and re.search(r"(?:只)?开放给\s*$", text[: clazz_match.start()]):
                    target_class = base.pop("clazz", "")
                    if target_class and target_class not in operands:
                        operands.insert(0, target_class)
                model = inferred_model()
                if model:
                    base["model"] = model
                update_classes = bool(
                    re.search(r"修改|设置|调整|开放给|只对|全部班级|任何班级", text)
                ) and not bool(re.search(r"查看|读取|哪些", text))
                if update_classes:
                    if re.search(r"不对任何班级|无班级|全部隐藏", text):
                        base["visible_classes"] = []
                    elif "全部班级" in text:
                        base["visible_classes"] = ["*"]
                    else:
                        class_operands = list(operands)
                        if model and class_operands and class_operands[0] == model:
                            class_operands = class_operands[1:]
                        base["visible_classes"] = class_operands
                    required = graph_missing("course", "model", "visible_classes")
                    return CommandPlan(
                        text,
                        "knowledge_graph.model.classes.update",
                        parameters=base,
                        confidence=0.97 if not required else 0.78,
                        missing_fields=required,
                        message="请提供课程、图谱模型及完整可见班级集合。" if required else "",
                    )
                required = graph_missing("course", "model")
                return CommandPlan(
                    text,
                    "knowledge_graph.model.classes.list",
                    parameters=base,
                    confidence=0.97 if not required else 0.8,
                    missing_fields=required,
                    message="请提供课程和图谱模型。" if required else "",
                )
            if re.search(r"删除|移除", text):
                model = inferred_model()
                if model:
                    base["model"] = model
                required = graph_missing("course", "model")
                return CommandPlan(
                    text,
                    "knowledge_graph.model.delete",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请提供课程和要删除的自定义图谱模型。" if required else "",
                )
            if re.search(r"隐藏|关闭|不显示|显示|开启|打开|启用", text) and not re.search(
                r"设置|外观|显示全部", text
            ):
                model = inferred_model()
                if model:
                    base["model"] = model
                base["visible"] = not bool(re.search(r"隐藏|关闭|不显示|停用", text))
                required = graph_missing("course", "model")
                return CommandPlan(
                    text,
                    "knowledge_graph.model.visibility.update",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请提供课程和要显示或隐藏的图谱模型。" if required else "",
                )
            if re.search(r"排序|顺序|重排", text):
                if operands:
                    base["models"] = operands
                required = graph_missing("course", "models")
                return CommandPlan(
                    text,
                    "knowledge_graph.models.reorder",
                    parameters=base,
                    confidence=0.97 if not required else 0.78,
                    missing_fields=required,
                    message="请按目标顺序用书名号提供课程及全部图谱模型。" if required else "",
                )
            if re.search(r"新建|创建|添加", text):
                if operands:
                    base["name"] = operands[0]
                style_match = re.search(r"样式\s*(\d+)", text)
                if style_match:
                    base["style"] = int(style_match.group(1))
                required = graph_missing("course", "name")
                return CommandPlan(
                    text,
                    "knowledge_graph.model.create",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请依次用书名号提供课程和自定义图谱名称。" if required else "",
                )
            if re.search(r"重命名|改名|修改|编辑", text):
                model = inferred_model()
                if model:
                    base["model"] = model
                if operands:
                    base["name"] = (
                        operands[1] if operands[0] == model and len(operands) >= 2 else operands[0]
                    )
                style_match = re.search(r"样式\s*(\d+)", text)
                if style_match:
                    base["style"] = int(style_match.group(1))
                required = graph_missing("course", "model", "name")
                return CommandPlan(
                    text,
                    "knowledge_graph.model.update",
                    parameters=base,
                    confidence=0.97 if not required else 0.78,
                    missing_fields=required,
                    message="请提供课程、原图谱模型和新名称。" if required else "",
                )
            if re.search(r"数据|内容|节点|详情", text):
                model = inferred_model()
                if model:
                    base["model"] = model
                required = graph_missing("course", "model")
                return CommandPlan(
                    text,
                    "knowledge_graph.model.data.read",
                    parameters=base,
                    confidence=0.97 if not required else 0.8,
                    missing_fields=required,
                    message="请提供课程和图谱模型。" if required else "",
                )
            search_match = re.search(r"搜索.{0,6}?[《“\"']([^》”\"']+)[》”\"']", text)
            if search_match:
                base["search"] = search_match.group(1)
            required = graph_missing("course")
            return CommandPlan(
                text,
                "knowledge_graph.models.list",
                parameters=base,
                confidence=0.97 if not required else 0.8,
                missing_fields=required,
                message="请用书名号提供课程。" if required else "",
            )

        graph_settings_intent = bool(
            re.search(
                r"图谱(?:显示|外观)?设置|显示全部关系|全部关系显示|"
                r"显示全部(?:节点|主题)名称|导航节点缩放|图谱背景色",
                text,
            )
        )
        if graph_settings_intent:
            update_intent = bool(
                re.search(r"修改|调整|设为|开启|打开|启用|关闭|关掉|隐藏|禁用|停用", text)
            ) and not bool(re.search(r"查看|读取|当前|是什么|有哪些", text))
            if update_intent:
                settings = {
                    "show_all_relations": r"显示全部关系|全部关系显示",
                    "show_all_topic_names": r"显示全部(?:节点|主题)名称|全部(?:节点|主题)名称显示",
                    "navigation_node_scale": r"导航节点缩放",
                    "graph_background_color": r"图谱背景色",
                }
                for key, pattern in settings.items():
                    match = re.search(pattern, text)
                    if not match:
                        continue
                    neighborhood = text[max(0, match.start() - 8) : min(len(text), match.end() + 8)]
                    if re.search(r"关闭|关掉|不显示|隐藏|禁用|停用|设为关", neighborhood):
                        base[key] = False
                    elif re.search(r"开启|打开|启用|显示出来|设为开", neighborhood):
                        base[key] = True
                required = graph_missing("course")
                if not any(key in base for key in settings):
                    required.append("changes")
                return CommandPlan(
                    text,
                    "knowledge_graph.settings.update",
                    parameters=base,
                    confidence=0.97 if not required else 0.78,
                    missing_fields=required,
                    message="请提供课程及至少一项图谱显示设置的开关值。" if required else "",
                )
            required = graph_missing("course")
            return CommandPlan(
                text,
                "knowledge_graph.settings.read",
                parameters=base,
                confidence=0.98 if not required else 0.8,
                missing_fields=required,
                message="请用书名号提供课程。" if required else "",
            )

        node_relation_intent = bool(
            re.search(
                r"节点关系|知识点关系|技能点关系|前置关系|后置关系|关联关系|"
                r"(?:添加|建立|创建|移除|删除|取消).{0,18}(?:前置|后置|关联).{0,3}关系",
                text,
            )
        ) and not bool(re.search(r"关系定义|关系类型", text))
        if node_relation_intent:
            relation_alias = None
            for marker, value in (
                (r"前置关系|前置", "predecessor"),
                (r"后置关系|后置", "successor"),
                (r"关联关系|关联", "association"),
            ):
                if re.search(marker, text):
                    relation_alias = value
                    break
            custom_match = re.search(
                r"自定义关系(?:为|是|：|:)?\s*[《“\"']([^》”\"']+)[》”\"']",
                text,
            )
            if custom_match:
                relation_alias = custom_match.group(1)
                if custom_match.group(1) in operands:
                    operands.remove(custom_match.group(1))
            description_match = re.search(
                r"(?:关系说明|说明)(?:为|是|：|:)?\s*[《“\"']([^》”\"']+)[》”\"']",
                text,
            )
            if description_match:
                base["description"] = description_match.group(1)
                if description_match.group(1) in operands:
                    operands.remove(description_match.group(1))
            if operands:
                base["node"] = operands[0]
            if len(operands) >= 2:
                base["target"] = operands[1]
            if relation_alias:
                base["relation"] = relation_alias
            if re.search(r"删除|移除|取消|解除", text):
                required = graph_missing("course", "node", "relation", "target")
                return CommandPlan(
                    text,
                    "knowledge_graph.node.relation.remove",
                    parameters=base,
                    confidence=0.98 if not required else 0.78,
                    missing_fields=required,
                    message="请依次用书名号提供课程、源节点和目标节点，并说明关系类型。"
                    if required
                    else "",
                )
            if re.search(r"添加|建立|创建|关联到|设为", text):
                required = graph_missing("course", "node", "relation", "target")
                return CommandPlan(
                    text,
                    "knowledge_graph.node.relation.add",
                    parameters=base,
                    confidence=0.98 if not required else 0.78,
                    missing_fields=required,
                    message="请依次用书名号提供课程、源节点和目标节点，并说明关系类型。"
                    if required
                    else "",
                )
            required = graph_missing("course", "node")
            return CommandPlan(
                text,
                "knowledge_graph.node.relations.read",
                parameters=base,
                confidence=0.98 if not required else 0.8,
                missing_fields=required,
                message="请依次用书名号提供课程和图谱节点。" if required else "",
            )

        if re.search(r"关系定义|关系类型|自定义关系", text):
            if re.search(r"删除|移除", text):
                if operands:
                    base["relation"] = operands[0]
                required = graph_missing("course", "relation")
                return CommandPlan(
                    text,
                    "knowledge_graph.relation_type.delete",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请依次用书名号提供课程和自定义图谱关系。" if required else "",
                )
            if re.search(r"重命名|改名|修改|编辑", text):
                if operands:
                    base["relation"] = operands[0]
                if len(operands) >= 2:
                    base["name"] = operands[1]
                if len(operands) >= 3:
                    base["meaning"] = operands[2]
                required = graph_missing("course", "relation")
                if not any(
                    key in base
                    for key in (
                        "name",
                        "meaning",
                        "example_html",
                        "color",
                        "arrow_size",
                        "line_thickness",
                    )
                ):
                    required.append("changes")
                return CommandPlan(
                    text,
                    "knowledge_graph.relation_type.update",
                    parameters=base,
                    confidence=0.97 if not required else 0.78,
                    missing_fields=required,
                    message="请提供课程、自定义关系及要修改的字段。" if required else "",
                )
            if re.search(r"新建|创建|添加", text):
                if operands:
                    base["name"] = operands[0]
                if len(operands) >= 2:
                    base["meaning"] = operands[1]
                if len(operands) >= 3:
                    base["example_html"] = operands[2]
                relation_types = [
                    value
                    for marker, value in (
                        ("关联", 0),
                        ("父子", 1),
                        ("前后置", 2),
                    )
                    if marker in text
                ]
                if relation_types:
                    base["relation_types"] = relation_types
                required = graph_missing("course", "name")
                return CommandPlan(
                    text,
                    "knowledge_graph.relation_type.create",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请依次用书名号提供课程和自定义关系名称。" if required else "",
                )
            search_match = re.search(r"搜索.{0,6}?[《“\"']([^》”\"']+)[》”\"']", text)
            if search_match:
                base["search"] = search_match.group(1)
            required = graph_missing("course")
            return CommandPlan(
                text,
                "knowledge_graph.relation_types.list",
                parameters=base,
                confidence=0.97 if not required else 0.8,
                missing_fields=required,
                message="请用书名号提供课程。" if required else "",
            )

        label_member_intent = bool(
            re.search(r"(?:新建|创建|添加).{0,6}标签(?!组)", text)
            or re.search(r"图谱标签.{0,24}(?:重命名|改名|删除|移除|移动|移到|放入|换组)", text)
            or re.search(r"标签组.{0,16}标签(?:顺序|排序|重排)", text)
        )
        if re.search(r"标签组", text) and not label_member_intent:
            if re.search(r"删除|移除", text):
                if operands:
                    base["group"] = operands[0]
                required = graph_missing("course", "group")
                return CommandPlan(
                    text,
                    "knowledge_graph.label_group.delete",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请依次用书名号提供课程和图谱标签组。" if required else "",
                )
            if re.search(r"重命名|改名", text):
                if operands:
                    base["group"] = operands[0]
                if len(operands) >= 2:
                    base["name"] = operands[1]
                required = graph_missing("course", "group", "name")
                return CommandPlan(
                    text,
                    "knowledge_graph.label_group.rename",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请依次用书名号提供课程、原标签组和新名称。" if required else "",
                )
            if re.search(r"新建|创建|添加", text):
                if operands:
                    base["name"] = operands[0]
                if re.search(r"知识类型", text):
                    base["group_type"] = 1
                elif re.search(r"认知维度", text):
                    base["group_type"] = 2
                else:
                    base["group_type"] = 0
                required = graph_missing("course", "name")
                return CommandPlan(
                    text,
                    "knowledge_graph.label_group.create",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请依次用书名号提供课程和新标签组名称。" if required else "",
                )
            if re.search(r"排序|顺序|重排", text):
                if operands:
                    base["groups"] = operands
                required = graph_missing("course", "groups")
                return CommandPlan(
                    text,
                    "knowledge_graph.label_groups.reorder",
                    parameters=base,
                    confidence=0.97 if not required else 0.78,
                    missing_fields=required,
                    message="请按目标顺序用书名号提供课程和全部图谱标签组。" if required else "",
                )
            required = graph_missing("course")
            return CommandPlan(
                text,
                "knowledge_graph.labels.list",
                parameters=base,
                confidence=0.97 if not required else 0.8,
                missing_fields=required,
                message="请用书名号提供课程。" if required else "",
            )

        if re.search(r"(?:图谱|课程图谱|知识图谱).{0,6}标签|标签.{0,6}(?:图谱|课程图谱)", text):
            if re.search(r"删除|移除", text):
                if operands:
                    base["label"] = operands[0]
                required = graph_missing("course", "label")
                return CommandPlan(
                    text,
                    "knowledge_graph.label.delete",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请依次用书名号提供课程和图谱标签。" if required else "",
                )
            if re.search(r"重命名|改名", text):
                if operands:
                    base["label"] = operands[0]
                if len(operands) >= 2:
                    base["name"] = operands[1]
                required = graph_missing("course", "label", "name")
                return CommandPlan(
                    text,
                    "knowledge_graph.label.rename",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请依次用书名号提供课程、原标签和新名称。" if required else "",
                )
            if re.search(r"移动|移到|放入|换组", text):
                if operands:
                    base["label"] = operands[0]
                if len(operands) >= 2:
                    base["group"] = operands[1]
                required = graph_missing("course", "label", "group")
                return CommandPlan(
                    text,
                    "knowledge_graph.label.move",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请依次用书名号提供课程、标签和目标标签组。" if required else "",
                )
            if re.search(r"排序|顺序|重排", text):
                group_match = re.search(r"标签组[《“\"']([^》”\"']+)[》”\"']", text)
                if group_match:
                    base["group"] = group_match.group(1)
                    if group_match.group(1) in operands:
                        operands.remove(group_match.group(1))
                if operands:
                    base["labels"] = operands
                required = graph_missing("course", "group", "labels")
                return CommandPlan(
                    text,
                    "knowledge_graph.labels.reorder",
                    parameters=base,
                    confidence=0.97 if not required else 0.78,
                    missing_fields=required,
                    message="请用书名号提供课程、标签组和组内全部标签的完整顺序。"
                    if required
                    else "",
                )
            if re.search(r"新建|创建|添加", text):
                if operands:
                    base["group"] = operands[0]
                if len(operands) >= 2:
                    base["name"] = operands[1]
                required = graph_missing("course", "group", "name")
                return CommandPlan(
                    text,
                    "knowledge_graph.label.create",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请依次用书名号提供课程、标签组和新标签名称。" if required else "",
                )
            search_match = re.search(r"搜索.{0,6}?[《“\"']([^》”\"']+)[》”\"']", text)
            if search_match:
                base["search"] = search_match.group(1)
            required = graph_missing("course")
            return CommandPlan(
                text,
                "knowledge_graph.labels.list",
                parameters=base,
                confidence=0.97 if not required else 0.8,
                missing_fields=required,
                message="请用书名号提供课程。" if required else "",
            )

        generic_node_create = bool(
            re.search(r"新建|创建|添加", text)
            and re.search(r"知识点|技能点|能力点|图谱节点|分类节点", text)
            and not re.search(r"一级|顶层", text)
        )
        if generic_node_create:
            node_type = "knowledge"
            if re.search(r"技能点|能力点", text):
                node_type = "ability"
            elif re.search(r"分类节点", text):
                node_type = "category"
            base["node_type"] = node_type
            description_match = re.search(
                r"(?:说明|描述)(?:为|是|：|:)?\s*[《“\"']([^》”\"']+)[》”\"']",
                text,
            )
            if description_match:
                base["description"] = description_match.group(1)
                if description_match.group(1) in operands:
                    operands.remove(description_match.group(1))
            if re.search(r"[》”\"']\s*(?:之)?下", text) and len(operands) >= 2:
                base["parent"] = operands[0]
                base["name"] = operands[-1]
            elif operands:
                base["name"] = operands[-1]
            for model_name in (
                "学习地图",
                "知识列表",
                "问题图谱",
                "目标图谱",
                "课程思政图谱",
                "岗位能力图谱",
                "知识图谱",
            ):
                if model_name in text and model_name != "知识图谱":
                    base["model"] = model_name
                    break
            required = graph_missing("course", "name")
            return CommandPlan(
                text,
                "knowledge_graph.node.create",
                parameters=base,
                confidence=0.98 if not required else 0.8,
                missing_fields=required,
                message="请依次用书名号提供课程、新节点名称；有父节点时同时提供父节点。"
                if required
                else "",
            )

        generic_node_update = bool(
            re.search(r"重命名|改名|修改|编辑", text)
            and re.search(r"知识点|技能点|能力点|图谱节点", text)
            and not re.search(r"分类|一级节点", text)
        )
        if generic_node_update:
            if operands:
                base["node"] = operands[0]
            if len(operands) >= 2:
                base["name"] = operands[1]
            if len(operands) >= 3:
                base["description"] = operands[2]
            required = graph_missing("course", "node", "name")
            return CommandPlan(
                text,
                "knowledge_graph.node.update",
                parameters=base,
                confidence=0.98 if not required else 0.8,
                missing_fields=required,
                message="请依次用书名号提供课程、原节点和新名称。" if required else "",
            )

        if re.search(r"新建|创建|添加", text) and re.search(r"一级|分类|顶层", text):
            if operands:
                base["name"] = operands[0]
            if len(operands) >= 2:
                base["description"] = operands[1]
            required = graph_missing("course", "name")
            return CommandPlan(
                text,
                "knowledge_graph.category.create",
                parameters=base,
                confidence=0.98 if not required else 0.8,
                missing_fields=required,
                message="请依次用书名号提供课程和新一级分类名称。" if required else "",
            )
        if re.search(r"重命名|改名|修改|编辑", text) and re.search(r"分类|一级节点", text):
            if operands:
                base["node"] = operands[0]
            if len(operands) >= 2:
                base["name"] = operands[1]
            if len(operands) >= 3:
                base["description"] = operands[2]
            required = graph_missing("course", "node", "name")
            return CommandPlan(
                text,
                "knowledge_graph.category.update",
                parameters=base,
                confidence=0.98 if not required else 0.8,
                missing_fields=required,
                message="请依次用书名号提供课程、原分类和新名称。" if required else "",
            )
        if re.search(r"删除|移除", text) and re.search(r"节点|分类", text):
            if operands:
                base["node"] = operands[0]
            required = graph_missing("course", "node")
            return CommandPlan(
                text,
                "knowledge_graph.node.delete",
                parameters=base,
                confidence=0.98 if not required else 0.8,
                missing_fields=required,
                message="请依次用书名号提供课程和要删除的图谱节点。" if required else "",
            )
        if re.search(r"详情|读取节点|查看节点|节点关系", text):
            if operands:
                base["node"] = operands[0]
            required = graph_missing("course", "node")
            return CommandPlan(
                text,
                "knowledge_graph.node.read",
                parameters=base,
                confidence=0.98 if not required else 0.8,
                missing_fields=required,
                message="请依次用书名号提供课程和图谱节点。" if required else "",
            )
        search_match = re.search(r"搜索.{0,6}?[《“\"']([^》”\"']+)[》”\"']", text)
        if search_match:
            base["search"] = search_match.group(1)
        level_match = re.search(r"(?:第)?(\d+)级", text)
        if level_match:
            base["level"] = int(level_match.group(1))
        required = graph_missing("course")
        return CommandPlan(
            text,
            "knowledge_graph.graph.read",
            parameters=base,
            confidence=0.96 if not required else 0.8,
            missing_fields=required,
            message="请用书名号提供课程。" if required else "",
        )

    if re.search(r"班级活动|课堂活动|活动分组|活动回收站", text):
        quoted = _extract_quoted(text)
        base: dict[str, Any] = {"course": quoted[0]} if quoted else {}
        operands = quoted[1:]
        clazz_match = re.search(
            r"(?:班级|教学班)(?!活动)(?:为|是|：|:)?\s*[《“\"']([^》”\"']+)[》”\"']",
            text,
        )
        if clazz_match:
            base["clazz"] = clazz_match.group(1)
            if clazz_match.group(1) in operands:
                operands.remove(clazz_match.group(1))

        def activity_missing(*keys: str) -> list[str]:
            return [key for key in keys if key not in base]

        if re.search(r"活动类型|可用类型|支持.{0,4}活动", text):
            required = activity_missing("course")
            return CommandPlan(
                text,
                "class_activities.types.list",
                parameters=base,
                confidence=0.98 if not required else 0.8,
                missing_fields=required,
                message="请用书名号提供课程。" if required else "",
            )

        activity_group_intent = bool(
            re.search(r"活动分组|课堂活动.{0,4}分组|班级活动.{0,4}分组", text)
        ) and not bool(
            re.search(r"(?:班级活动|课堂活动).{0,20}(?:移动|移到|放入)", text)
            or re.search(r"(?:班级活动|课堂活动).{0,8}(?:排序|顺序|重排)", text)
        )
        if activity_group_intent:
            if re.search(r"删除|移除", text):
                if operands:
                    base["group"] = operands[0]
                if re.search(r"非空|含有活动|保留.{0,4}活动", text):
                    base["allow_nonempty"] = True
                required = activity_missing("course", "group")
                return CommandPlan(
                    text,
                    "class_activities.group.delete",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请依次用书名号提供课程和活动分组。" if required else "",
                )
            if re.search(r"重命名|改名", text):
                if operands:
                    base["group"] = operands[0]
                if len(operands) >= 2:
                    base["name"] = operands[1]
                required = activity_missing("course", "group", "name")
                return CommandPlan(
                    text,
                    "class_activities.group.rename",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请依次用书名号提供课程、原分组和新名称。" if required else "",
                )
            if re.search(r"新建|创建|添加", text):
                if operands:
                    base["name"] = operands[0]
                required = activity_missing("course", "name")
                return CommandPlan(
                    text,
                    "class_activities.group.create",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请依次用书名号提供课程和新活动分组名称。" if required else "",
                )
            if re.search(r"排序|顺序|重排", text):
                if operands:
                    base["groups"] = operands
                required = activity_missing("course", "groups")
                return CommandPlan(
                    text,
                    "class_activities.groups.reorder",
                    parameters=base,
                    confidence=0.97 if not required else 0.78,
                    missing_fields=required,
                    message="请用书名号依次提供课程和全部自定义活动分组的完整顺序。"
                    if required
                    else "",
                )
            required = activity_missing("course")
            return CommandPlan(
                text,
                "class_activities.groups.list",
                parameters=base,
                confidence=0.97 if not required else 0.8,
                missing_fields=required,
                message="请用书名号提供课程。" if required else "",
            )

        if "回收站" in text:
            if re.search(r"永久删除|彻底删除|完全删除", text):
                if operands:
                    base["activities"] = operands
                required = activity_missing("course", "activities")
                return CommandPlan(
                    text,
                    "class_activities.recycle.items.delete",
                    parameters=base,
                    confidence=0.99 if not required else 0.8,
                    missing_fields=required,
                    message="请依次用书名号提供课程和要永久删除的回收站活动。" if required else "",
                )
            if re.search(r"恢复|还原", text):
                if operands:
                    base["activity"] = operands[0]
                required = activity_missing("course", "activity")
                return CommandPlan(
                    text,
                    "class_activities.recycle.restore",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请依次用书名号提供课程和要恢复的活动。" if required else "",
                )
            search_match = re.search(r"搜索.{0,6}?[《“\"']([^》”\"']+)[》”\"']", text)
            if search_match:
                base["search"] = search_match.group(1)
            required = activity_missing("course")
            return CommandPlan(
                text,
                "class_activities.recycle.list",
                parameters=base,
                confidence=0.97 if not required else 0.8,
                missing_fields=required,
                message="请用书名号提供课程。" if required else "",
            )

        start_intent = bool(
            re.search(r"^(?:请|现在)?\s*(?:开始|启动|发放|开放)", text)
            or re.search(r"(?:班级活动|课堂活动).{0,12}(?:开始|启动|发放|开放)$", text)
        )
        if start_intent:
            if operands:
                base["activity"] = operands[0]
            required = activity_missing("course", "activity")
            return CommandPlan(
                text,
                "class_activities.activity.start",
                parameters=base,
                confidence=0.98 if not required else 0.8,
                missing_fields=required,
                message="请依次用书名号提供课程和要开始的班级活动。" if required else "",
            )
        end_intent = bool(
            re.search(r"^(?:请|现在)?\s*(?:结束|停止|终止|关闭)", text)
            or re.search(r"(?:班级活动|课堂活动).{0,12}(?:结束|停止|终止|关闭)$", text)
        )
        if end_intent:
            if operands:
                base["activity"] = operands[0]
            required = activity_missing("course", "activity")
            return CommandPlan(
                text,
                "class_activities.activity.end",
                parameters=base,
                confidence=0.98 if not required else 0.8,
                missing_fields=required,
                message="请依次用书名号提供课程和要结束的班级活动。" if required else "",
            )
        if re.search(r"删除|移除", text):
            if operands:
                base["activity"] = operands[0]
            required = activity_missing("course", "activity")
            return CommandPlan(
                text,
                "class_activities.activity.delete",
                parameters=base,
                confidence=0.98 if not required else 0.8,
                missing_fields=required,
                message="请依次用书名号提供课程和要移入回收站的活动。" if required else "",
            )
        if re.search(r"重命名|改名", text):
            if operands:
                base["activity"] = operands[0]
            if len(operands) >= 2:
                base["name"] = operands[1]
            required = activity_missing("course", "activity", "name")
            return CommandPlan(
                text,
                "class_activities.activity.rename",
                parameters=base,
                confidence=0.98 if not required else 0.8,
                missing_fields=required,
                message="请依次用书名号提供课程、原活动和新名称。" if required else "",
            )
        if re.search(r"移动|移到|放入", text):
            if operands:
                base["activity"] = operands[0]
            if len(operands) >= 2:
                base["group"] = operands[1]
            required = activity_missing("course", "activity", "group")
            return CommandPlan(
                text,
                "class_activities.activity.move",
                parameters=base,
                confidence=0.98 if not required else 0.8,
                missing_fields=required,
                message="请依次用书名号提供课程、活动和目标分组。" if required else "",
            )
        if re.search(r"排序|顺序|重排", text):
            group_match = re.search(r"(?:分组|组内)[《“\"']([^》”\"']+)[》”\"']", text)
            if group_match:
                base["group"] = group_match.group(1)
                if group_match.group(1) in operands:
                    operands.remove(group_match.group(1))
            if operands:
                base["activities"] = operands
            required = activity_missing("course", "group", "activities")
            return CommandPlan(
                text,
                "class_activities.activities.reorder",
                parameters=base,
                confidence=0.97 if not required else 0.76,
                missing_fields=required,
                message="请用书名号提供课程、分组及组内全部活动的完整顺序。" if required else "",
            )
        if re.search(r"详情|读取|查看单个|元数据", text) and operands:
            base["activity"] = operands[0]
            return CommandPlan(
                text,
                "class_activities.activity.read",
                parameters=base,
                confidence=0.98,
            )

        group_match = re.search(r"分组[《“\"']([^》”\"']+)[》”\"']", text)
        if group_match:
            base["group"] = group_match.group(1)
        search_match = re.search(r"搜索.{0,6}?[《“\"']([^》”\"']+)[》”\"']", text)
        if search_match:
            base["search"] = search_match.group(1)
        for marker, value in (
            ("未开始", "not_started"),
            ("进行中", "ongoing"),
            ("已结束", "ended"),
        ):
            if marker in text:
                base["status"] = value
                break
        type_match = re.search(r"(?:活动)?类型\s*(\d+)", text)
        if type_match:
            base["activity_type"] = int(type_match.group(1))
        required = activity_missing("course")
        return CommandPlan(
            text,
            "class_activities.activities.list",
            parameters=base,
            confidence=0.96 if not required else 0.8,
            missing_fields=required,
            message="请用书名号提供课程。" if required else "",
        )

    if re.search(r"任务引擎|教学任务|任务文件夹|任务回收站|任务标签", text):
        quoted = _extract_quoted(text)
        base: dict[str, Any] = {"course": quoted[0]} if quoted else {}

        def task_missing(*keys: str) -> list[str]:
            return [key for key in keys if key not in base]

        if "文件夹" in text and not re.search(r"任务.{0,8}(?:移动|移到|放入)", text):
            if re.search(r"删除|移除", text):
                if len(quoted) >= 2:
                    base["folder"] = quoted[1]
                if re.search(r"非空|含有任务|连同", text):
                    base["allow_nonempty"] = True
                required = task_missing("course", "folder")
                return CommandPlan(
                    text,
                    "task_engine.folder.delete",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请依次用书名号提供课程和任务文件夹。" if required else "",
                )
            if re.search(r"重命名|改名", text):
                if len(quoted) >= 2:
                    base["folder"] = quoted[1]
                if len(quoted) >= 3:
                    base["name"] = quoted[2]
                required = task_missing("course", "folder", "name")
                return CommandPlan(
                    text,
                    "task_engine.folder.rename",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请依次用书名号提供课程、原文件夹和新名称。" if required else "",
                )
            if re.search(r"新建|创建|添加", text):
                if len(quoted) >= 2:
                    base["name"] = quoted[1]
                required = task_missing("course", "name")
                return CommandPlan(
                    text,
                    "task_engine.folder.create",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请依次用书名号提供课程和新文件夹名称。" if required else "",
                )
            required = task_missing("course")
            return CommandPlan(
                text,
                "task_engine.folders.list",
                parameters=base,
                confidence=0.97 if not required else 0.8,
                missing_fields=required,
                message="请用书名号提供课程。" if required else "",
            )

        if "标签" in text:
            task_match = re.search(r"任务[《“\"']([^》”\"']+)[》”\"']", text)
            if task_match:
                base["task"] = task_match.group(1)
            if re.search(r"删除|移除", text):
                if len(quoted) >= 2:
                    base["label"] = quoted[-1]
                required = task_missing("course", "label")
                return CommandPlan(
                    text,
                    "task_engine.label.delete",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请依次用书名号提供课程和任务标签。" if required else "",
                )
            if re.search(r"重命名|改名", text):
                if len(quoted) >= 2:
                    base["label"] = quoted[1]
                if len(quoted) >= 3:
                    base["name"] = quoted[2]
                required = task_missing("course", "label", "name")
                return CommandPlan(
                    text,
                    "task_engine.label.rename",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请依次用书名号提供课程、原标签和新名称。" if required else "",
                )
            if re.search(r"新建|创建|添加", text):
                if len(quoted) >= 2:
                    base["name"] = quoted[-1]
                required = task_missing("course", "name")
                return CommandPlan(
                    text,
                    "task_engine.label.create",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请依次用书名号提供课程和新标签名称。" if required else "",
                )
            search_match = re.search(r"搜索.{0,6}?[《“\"']([^》”\"']+)[》”\"']", text)
            if search_match:
                base["search"] = search_match.group(1)
            required = task_missing("course")
            return CommandPlan(
                text,
                "task_engine.labels.list",
                parameters=base,
                confidence=0.97 if not required else 0.8,
                missing_fields=required,
                message="请用书名号提供课程。" if required else "",
            )

        if "回收站" in text:
            if re.search(r"恢复|还原", text):
                if len(quoted) >= 2:
                    base["task"] = quoted[1]
                required = task_missing("course", "task")
                return CommandPlan(
                    text,
                    "task_engine.task.restore",
                    parameters=base,
                    confidence=0.98 if not required else 0.8,
                    missing_fields=required,
                    message="请依次用书名号提供课程和要恢复的任务。" if required else "",
                )
            search_match = re.search(r"搜索.{0,6}?[《“\"']([^》”\"']+)[》”\"']", text)
            if search_match:
                base["search"] = search_match.group(1)
            required = task_missing("course")
            return CommandPlan(
                text,
                "task_engine.recycle.list",
                parameters=base,
                confidence=0.97 if not required else 0.8,
                missing_fields=required,
                message="请用书名号提供课程。" if required else "",
            )

        if re.search(r"发布|取消发布|撤销发布|下线", text):
            if len(quoted) >= 2:
                base["task"] = quoted[1]
            base["published"] = not bool(re.search(r"取消|撤销|下线", text))
            required = task_missing("course", "task")
            return CommandPlan(
                text,
                "task_engine.publish_status.update",
                parameters=base,
                confidence=0.99 if not required else 0.8,
                missing_fields=required,
                message="请依次用书名号提供课程和教学任务。" if required else "",
            )
        if re.search(r"导出", text):
            if len(quoted) >= 2:
                base["tasks"] = quoted[1:]
            required = task_missing("course")
            return CommandPlan(
                text,
                "task_engine.export.request",
                parameters=base,
                confidence=0.97 if not required else 0.8,
                missing_fields=required,
                message="请用书名号提供课程；还可继续提供要导出的任务。" if required else "",
            )
        if re.search(r"恢复|还原", text):
            if len(quoted) >= 2:
                base["task"] = quoted[1]
            required = task_missing("course", "task")
            return CommandPlan(
                text,
                "task_engine.task.restore",
                parameters=base,
                confidence=0.98 if not required else 0.8,
                missing_fields=required,
                message="请依次用书名号提供课程和要恢复的任务。" if required else "",
            )
        if re.search(r"删除|移除", text):
            if len(quoted) >= 2:
                base["task"] = quoted[1]
            required = task_missing("course", "task")
            return CommandPlan(
                text,
                "task_engine.task.delete",
                parameters=base,
                confidence=0.98 if not required else 0.8,
                missing_fields=required,
                message="请依次用书名号提供课程和要移入回收站的任务。" if required else "",
            )
        if re.search(r"移动|移到|放入", text):
            if len(quoted) >= 2:
                base["task"] = quoted[1]
            if re.search(r"根目录|根层级", text):
                base["folder"] = ""
            elif len(quoted) >= 3:
                base["folder"] = quoted[2]
            required = task_missing("course", "task", "folder")
            return CommandPlan(
                text,
                "task_engine.task.move",
                parameters=base,
                confidence=0.98 if not required else 0.8,
                missing_fields=required,
                message="请依次用书名号提供课程、任务和目标文件夹，或说明移到根目录。"
                if required
                else "",
            )
        if re.search(r"复制|拷贝", text):
            if len(quoted) >= 2:
                base["task"] = quoted[1]
            if len(quoted) >= 3:
                base["name"] = quoted[2]
            required = task_missing("course", "task")
            return CommandPlan(
                text,
                "task_engine.task.copy",
                parameters=base,
                confidence=0.98 if not required else 0.8,
                missing_fields=required,
                message="请依次用书名号提供课程和要复制的任务。" if required else "",
            )
        if re.search(r"排序|顺序", text):
            if len(quoted) >= 2:
                base["task_order"] = quoted[1:]
            required = task_missing("course", "task_order")
            return CommandPlan(
                text,
                "task_engine.order.update",
                parameters=base,
                confidence=0.96 if not required else 0.76,
                missing_fields=required,
                message="请依次用书名号提供课程和该层级全部任务的完整顺序。" if required else "",
            )
        if re.search(r"新建|创建|添加", text):
            if len(quoted) >= 2:
                base["name"] = quoted[1]
            folder_match = re.search(r"(?:放入|位于|文件夹)[《“\"']([^》”\"']+)[》”\"']", text)
            if folder_match:
                base["folder"] = folder_match.group(1)
            required = task_missing("course", "name")
            return CommandPlan(
                text,
                "task_engine.task.create",
                parameters=base,
                confidence=0.98 if not required else 0.8,
                missing_fields=required,
                message="请依次用书名号提供课程和新任务名称。" if required else "",
            )
        if re.search(r"修改|编辑|更新|改名", text):
            if len(quoted) >= 2:
                base["task"] = quoted[1]
            labeled_fields = {
                "name": r"(?:新名称|改名|名称)",
                "introduce": r"(?:简介|介绍)",
                "rich_text": r"(?:富文本|任务说明|正文)",
                "target": r"(?:任务目标|目标)",
            }
            for key, label in labeled_fields.items():
                match = re.search(label + r".{0,8}?[《“\"']([^》”\"']*)[》”\"']", text)
                if match:
                    base[key] = match.group(1)
            date_matches = re.findall(r"20\d{2}-\d{2}-\d{2}(?:\s+\d{2}:\d{2})?", text)
            if date_matches:
                base["start_date"] = date_matches[0]
            if len(date_matches) >= 2:
                base["end_date"] = date_matches[1]
            required = task_missing("course", "task")
            if not any(
                key in base
                for key in (
                    "name",
                    "introduce",
                    "rich_text",
                    "target",
                    "start_date",
                    "end_date",
                )
            ):
                required.append("changes")
            return CommandPlan(
                text,
                "task_engine.task.update",
                parameters=base,
                confidence=0.97 if not required else 0.78,
                missing_fields=required,
                message="请提供课程、教学任务和要修改的字段。" if required else "",
            )
        if re.search(r"详情|读取|查看单个|任务点", text) and len(quoted) >= 2:
            base["task"] = quoted[1]
            return CommandPlan(text, "task_engine.task.read", parameters=base, confidence=0.98)
        folder_match = re.search(r"文件夹[《“\"']([^》”\"']+)[》”\"']", text)
        if folder_match:
            base["folder"] = folder_match.group(1)
        search_match = re.search(r"搜索.{0,6}?[《“\"']([^》”\"']+)[》”\"']", text)
        if search_match:
            base["search"] = search_match.group(1)
        required = task_missing("course")
        return CommandPlan(
            text,
            "task_engine.tasks.list",
            parameters=base,
            confidence=0.96 if not required else 0.8,
            missing_fields=required,
            message="请用书名号提供课程。" if required else "",
        )

    course_live_intent = bool(
        re.search(
            r"(?:《[^》]+》|课程).{0,12}(?:直播课|见面课|直播模块)|"
            r"(?:打开|进入|查看).{0,20}课程.{0,12}直播",
            text,
        )
    )
    live_intent = "直播" in text and (
        any(
            marker in text
            for marker in (
                "直播间",
                "个人直播",
                "主题直播",
                "推流",
                "直播邀请码",
                "观看地址",
                "直播回收站",
                "预热视频",
                "直播封面",
            )
        )
        or not course_live_intent
    )
    if live_intent:
        quoted = _extract_quoted(text)
        if "主题直播" in text:
            if re.search(r"在.*主题直播.*(?:新建|创建|添加).*子?直播", text):
                parameters: dict[str, Any] = {}
                if quoted:
                    parameters["theme"] = quoted[0]
                if len(quoted) >= 2:
                    parameters["title"] = quoted[1]
                schedule = re.search(r"(20\d{2}-\d{2}-\d{2}\s+\d{2}:\d{2})", text)
                if schedule:
                    parameters["scheduled_time"] = schedule.group(1)
                missing = [key for key in ("theme", "title") if key not in parameters]
                return CommandPlan(
                    text,
                    "live.theme.room.create",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.8,
                    missing_fields=missing,
                    message="请依次用书名号提供主题直播名称和子直播标题。" if missing else "",
                )
            if re.search(r"(?:加入|添加|放入|归入).*主题直播|主题直播.*(?:加入|添加)", text):
                parameters = {}
                if len(quoted) >= 2:
                    if text.find(quoted[0]) < text.find("主题直播"):
                        parameters = {"room": quoted[0], "theme": quoted[1]}
                    else:
                        parameters = {"theme": quoted[0], "room": quoted[1]}
                missing = [key for key in ("theme", "room") if key not in parameters]
                return CommandPlan(
                    text,
                    "live.theme.room.add",
                    parameters=parameters,
                    confidence=0.97 if not missing else 0.78,
                    missing_fields=missing,
                    message="请用书名号提供主题直播名称和个人直播名称。" if missing else "",
                )
            if re.search(r"访问设置|权限|允许|开启|关闭|禁用|单位限制", text):
                parameters = {"theme": quoted[0]} if quoted else {}
                parameters.update(_parse_alias_boolean_changes(text, LIVE_THEME_SETTING_ALIASES))
                if re.search(r"(?:清空|取消|解除).{0,8}单位限制", text):
                    parameters["allowed_unit_ids"] = []
                else:
                    unit_section = text[text.find("单位") :] if "单位" in text else ""
                    unit_ids = re.findall(r"(?<!\d)(\d{2,})(?!\d)", unit_section)
                    if unit_ids:
                        parameters["allowed_unit_ids"] = list(dict.fromkeys(unit_ids))
                missing = [] if quoted else ["theme"]
                if len(parameters) <= int(bool(quoted)):
                    missing.append("setting_changes")
                return CommandPlan(
                    text,
                    "live.theme.settings.update",
                    parameters=parameters,
                    confidence=0.96 if not missing else 0.78,
                    missing_fields=missing,
                    message="请提供主题直播名称和要修改的访问设置。" if missing else "",
                )
            if re.search(r"删除|移除", text):
                parameters = {"theme": quoted[0]} if quoted else {}
                return CommandPlan(
                    text,
                    "live.theme.delete",
                    parameters=parameters,
                    confidence=0.98 if quoted else 0.82,
                    missing_fields=[] if quoted else ["theme"],
                    message="请用书名号提供要删除的主题直播。" if not quoted else "",
                )
            if re.search(r"新建|创建", text):
                parameters = {"name": quoted[0]} if quoted else {}
                if len(quoted) >= 2:
                    parameters["description"] = quoted[1]
                return CommandPlan(
                    text,
                    "live.theme.create",
                    parameters=parameters,
                    confidence=0.98 if quoted else 0.82,
                    missing_fields=[] if quoted else ["name"],
                    message="请用书名号提供主题直播名称。" if not quoted else "",
                )
            if re.search(r"修改|编辑|改名|重命名", text):
                parameters = {"theme": quoted[0]} if quoted else {}
                if len(quoted) >= 2:
                    if re.search(r"说明|描述|简介", text):
                        parameters["description"] = quoted[1]
                    else:
                        parameters["name"] = quoted[1]
                missing = []
                if not quoted:
                    missing.append("theme")
                if len(quoted) < 2:
                    missing.append("name_or_description")
                return CommandPlan(
                    text,
                    "live.theme.update",
                    parameters=parameters,
                    confidence=0.97 if not missing else 0.8,
                    missing_fields=missing,
                    message="请用书名号提供主题直播及新名称或说明。" if missing else "",
                )
            if quoted and re.search(r"读取|查看|详情|打开|子直播", text):
                return CommandPlan(
                    text,
                    "live.theme.read",
                    parameters={"theme": quoted[0]},
                    confidence=0.98,
                )
            parameters = {"search": quoted[0]} if quoted and "搜索" in text else {}
            return CommandPlan(text, "live.themes.list", parameters=parameters, confidence=0.95)

        if "回收站" in text:
            if re.search(r"永久删除|彻底删除", text):
                parameters = {"room": quoted[0]} if quoted else {}
                return CommandPlan(
                    text,
                    "live.recycle.delete",
                    parameters=parameters,
                    confidence=0.98 if quoted else 0.82,
                    missing_fields=[] if quoted else ["room"],
                    message="请用书名号提供要永久删除的直播。" if not quoted else "",
                )
            if re.search(r"恢复|还原", text):
                parameters = {"room": quoted[0]} if quoted else {}
                return CommandPlan(
                    text,
                    "live.recycle.restore",
                    parameters=parameters,
                    confidence=0.98 if quoted else 0.82,
                    missing_fields=[] if quoted else ["room"],
                    message="请用书名号提供要恢复的直播。" if not quoted else "",
                )
            return CommandPlan(
                text,
                "live.recycle.list",
                parameters={"search": quoted[0]} if quoted and "搜索" in text else {},
                confidence=0.97,
            )
        if re.search(r"推流地址|推流凭据|RTMP|无需客户端开播", text, re.I):
            parameters = {"room": quoted[0]} if quoted else {}
            return CommandPlan(
                text,
                "live.stream.credentials",
                parameters=parameters,
                confidence=0.99 if quoted else 0.83,
                missing_fields=[] if quoted else ["room"],
                message="请用书名号提供直播间。" if not quoted else "",
            )
        if re.search(r"观看地址|邀请码|观看链接", text):
            parameters = {"room": quoted[0]} if quoted else {}
            return CommandPlan(
                text,
                "live.room.watch",
                parameters=parameters,
                confidence=0.98 if quoted else 0.82,
                missing_fields=[] if quoted else ["room"],
                message="请用书名号提供直播间。" if not quoted else "",
            )
        if re.search(r"实时状态|是否.*直播|直播状态|正在直播", text):
            parameters = {"room": quoted[0]} if quoted else {}
            return CommandPlan(
                text,
                "live.room.status",
                parameters=parameters,
                confidence=0.98 if quoted else 0.82,
                missing_fields=[] if quoted else ["room"],
                message="请用书名号提供直播间。" if not quoted else "",
            )
        if re.search(r"单位.*(?:列表|选项|有哪些)|可限制单位", text):
            return CommandPlan(text, "live.units.list", confidence=0.98)
        if re.search(r"导出", text):
            parameters = {"search": quoted[0]} if quoted else {}
            return CommandPlan(text, "live.export", parameters=parameters, confidence=0.96)
        if re.search(r"上传.*(?:封面|预热视频)|(?:封面|预热视频).*上传", text):
            parameters = {"kind": "preview_video" if "预热视频" in text else "cover"}
            if quoted:
                parameters["file"] = quoted[0]
            if len(quoted) >= 2:
                parameters["room"] = quoted[1]
            missing = [] if quoted else ["file"]
            return CommandPlan(
                text,
                "live.asset.upload",
                parameters=parameters,
                confidence=0.97 if not missing else 0.8,
                missing_fields=missing,
                message="请用书名号提供本地文件路径。" if missing else "",
            )
        if re.search(
            r"访问设置|互动设置|权限|允许|开启|关闭|禁用|观看密码|访问密码|"
            r"清除密码|回看开始|回放开始|单位限制",
            text,
        ):
            parameters = {"room": quoted[0]} if quoted else {}
            parameters.update(_parse_alias_boolean_changes(text, LIVE_ROOM_SETTING_ALIASES))
            if re.search(r"(?:清除|取消|移除|关闭).{0,6}(?:观看|访问)?密码", text):
                parameters["access_password"] = ""
            else:
                password_match = re.search(
                    r"(?:观看|访问)?密码.{0,8}?[《“\"']([^》”\"']*)[》”\"']",
                    text,
                )
                if password_match:
                    parameters["access_password"] = password_match.group(1)
            offset_match = re.search(
                r"(?:回看|回放).{0,12}?(?:开始|偏移).{0,8}?(\d+)\s*秒",
                text,
            )
            if offset_match:
                parameters["replay_start_offset_seconds"] = int(offset_match.group(1))
            if re.search(r"(?:清空|取消|解除).{0,8}单位限制", text):
                parameters["allowed_unit_ids"] = []
            else:
                unit_section = text[text.find("单位") :] if "单位" in text else ""
                unit_ids = re.findall(r"(?<!\d)(\d{2,})(?!\d)", unit_section)
                if unit_ids:
                    parameters["allowed_unit_ids"] = list(dict.fromkeys(unit_ids))
            missing = [] if quoted else ["room"]
            if len(parameters) <= int(bool(quoted)):
                missing.append("setting_changes")
            return CommandPlan(
                text,
                "live.room.settings.update",
                parameters=parameters,
                confidence=0.96 if not missing else 0.78,
                missing_fields=missing,
                message="请提供直播间名称和要修改的设置。" if missing else "",
            )
        if re.search(r"删除|移除", text):
            parameters = {"room": quoted[0]} if quoted else {}
            return CommandPlan(
                text,
                "live.room.delete",
                parameters=parameters,
                confidence=0.98 if quoted else 0.82,
                missing_fields=[] if quoted else ["room"],
                message="请用书名号提供要删除的直播间。" if not quoted else "",
            )
        if re.search(r"新建|创建", text):
            parameters = {"title": quoted[0]} if quoted else {}
            if len(quoted) >= 2:
                parameters["introduction"] = quoted[1]
            schedule = re.search(r"(20\d{2}-\d{2}-\d{2}\s+\d{2}:\d{2})", text)
            if schedule:
                parameters["scheduled_time"] = schedule.group(1)
            return CommandPlan(
                text,
                "live.room.create",
                parameters=parameters,
                confidence=0.98 if quoted else 0.82,
                missing_fields=[] if quoted else ["title"],
                message="请用书名号提供直播间标题。" if not quoted else "",
            )
        if re.search(r"修改|编辑|更新|改名|重命名", text):
            parameters = {"room": quoted[0]} if quoted else {}
            if len(quoted) >= 2:
                if re.search(r"简介|说明|描述", text):
                    parameters["introduction"] = quoted[1]
                else:
                    parameters["title"] = quoted[1]
            schedule = re.search(r"(20\d{2}-\d{2}-\d{2}\s+\d{2}:\d{2})", text)
            if schedule:
                parameters["scheduled_time"] = schedule.group(1)
            missing = []
            if not quoted:
                missing.append("room")
            if len(parameters) <= int(bool(quoted)):
                missing.append("changes")
            return CommandPlan(
                text,
                "live.room.update",
                parameters=parameters,
                confidence=0.97 if not missing else 0.8,
                missing_fields=missing,
                message="请提供直播间和要修改的标题、简介或时间。" if missing else "",
            )
        if quoted and re.search(r"读取|查看|打开|详情|设置", text):
            return CommandPlan(
                text,
                "live.room.read",
                parameters={"room": quoted[0]},
                confidence=0.98,
            )
        parameters = {"search": quoted[0]} if quoted and "搜索" in text else {}
        return CommandPlan(text, "live.rooms.list", parameters=parameters, confidence=0.94)

    if re.search(r"AIGC检测|相似度检测|查重|两两比对|两两对比|检测记录|检测报告", text, re.I):
        quoted = _extract_quoted(text)
        if re.search(r"两两比对|两两对比", text):
            detection_type = "comparison"
        elif re.search(r"AIGC", text, re.I):
            detection_type = "aigc"
        else:
            detection_type = "similarity"
        if re.search(r"检测库|比对库", text) and re.search(r"列出|查看|有哪些|选择", text):
            return CommandPlan(text, "detection.channels.list", confidence=0.98)
        if re.search(r"永久删除|删除", text) and re.search(r"记录|任务", text):
            parameters = {"type": detection_type}
            if quoted:
                parameters["record"] = quoted[0]
            return CommandPlan(
                text,
                "detection.record.delete",
                parameters=parameters,
                confidence=0.98 if quoted else 0.82,
                missing_fields=[] if quoted else ["record"],
                message="请用书名号提供要删除的检测记录。" if not quoted else "",
            )
        if re.search(r"免费|额度|权益", text) and re.search(r"使用|消耗|获取|解锁", text):
            parameters = {"type": detection_type}
            if quoted:
                parameters["record"] = quoted[0]
            return CommandPlan(
                text,
                "detection.free_entitlement.use",
                parameters=parameters,
                confidence=0.98 if quoted else 0.82,
                missing_fields=[] if quoted else ["record"],
                message="请用书名号提供要解锁的检测记录。" if not quoted else "",
            )
        if re.search(r"支付状态|是否付费|免费额度|免费权限", text):
            parameters = {"type": detection_type}
            if quoted:
                parameters["record"] = quoted[0]
            return CommandPlan(
                text,
                "detection.payment.status",
                parameters=parameters,
                confidence=0.98 if quoted else 0.82,
                missing_fields=[] if quoted else ["record"],
                message="请用书名号提供检测记录。" if not quoted else "",
            )
        if re.search(r"下载|保存", text) and "报告" in text:
            parameters = {"type": detection_type}
            if quoted:
                parameters["record"] = quoted[0]
            if len(quoted) >= 2:
                parameters["output_path"] = quoted[1]
            if re.search(r"覆盖", text):
                parameters["overwrite"] = True
            missing = [key for key in ("record", "output_path") if key not in parameters]
            return CommandPlan(
                text,
                "detection.report.download",
                parameters=parameters,
                confidence=0.98 if not missing else 0.8,
                missing_fields=missing,
                message="请依次用书名号提供检测记录和本地输出路径。" if missing else "",
            )
        if re.search(r"进度|实时状态|解析状态|检测状态", text):
            parameters = {"type": detection_type}
            if quoted:
                parameters["record"] = quoted[0]
            return CommandPlan(
                text,
                "detection.record.status",
                parameters=parameters,
                confidence=0.98 if quoted else 0.82,
                missing_fields=[] if quoted else ["record"],
                message="请用书名号提供检测记录。" if not quoted else "",
            )
        if re.search(r"提交|上传|发起|新建", text):
            if detection_type == "comparison":
                parameters = {}
                keys = ("title_1", "file_1", "title_2", "file_2")
                for key, value in zip(keys, quoted, strict=False):
                    parameters[key] = value
                missing = [key for key in keys if key not in parameters]
                return CommandPlan(
                    text,
                    "detection.comparison.submit",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.78,
                    missing_fields=missing,
                    message=(
                        "请依次用书名号提供文档一标题、路径、文档二标题、路径。" if missing else ""
                    ),
                )
            parameters = {"type": detection_type}
            if quoted:
                parameters["title"] = quoted[0]
            if re.search(r"文件|文档", text) and len(quoted) >= 2:
                parameters["file"] = quoted[-1]
                if detection_type == "similarity" and len(quoted) >= 3:
                    parameters["author"] = quoted[1]
            elif len(quoted) >= 2:
                parameters["content"] = quoted[-1]
                if detection_type == "similarity" and len(quoted) >= 3:
                    parameters["author"] = quoted[1]
            missing = [key for key in ("title",) if key not in parameters]
            if "file" not in parameters and "content" not in parameters:
                missing.append("content_or_file")
            if detection_type == "similarity" and "author" not in parameters:
                missing.append("author")
            return CommandPlan(
                text,
                "detection.submit",
                parameters=parameters,
                confidence=0.97 if not missing else 0.76,
                missing_fields=missing,
                message=(
                    "请用书名号提供标题、作者（相似度检测需要）以及正文或文件路径。"
                    if missing
                    else ""
                ),
            )
        parameters = {"type": detection_type}
        if quoted:
            parameters["search"] = quoted[0]
        return CommandPlan(text, "detection.records.list", parameters=parameters, confidence=0.94)

    if "专题" in text:
        quoted = _extract_quoted(text)
        if re.search(r"能否|是否可以|资格|实名认证|创建状态", text) and re.search(
            r"创建|新建|专题", text
        ):
            return CommandPlan(text, "subjects.creation.status", confidence=0.98)
        if re.search(r"目录树|文件夹树|完整目录", text):
            return CommandPlan(text, "subjects.tree.list", confidence=0.98)
        if re.search(r"回收站", text):
            if re.search(r"永久删除|彻底删除", text):
                parameters = {"subject": quoted[0]} if quoted else {}
                return CommandPlan(
                    text,
                    "subjects.recycle.delete",
                    parameters=parameters,
                    confidence=0.98 if quoted else 0.82,
                    missing_fields=[] if quoted else ["subject"],
                    message="请用书名号提供要永久删除的专题。" if not quoted else "",
                )
            if re.search(r"恢复|还原", text):
                parameters = {"subject": quoted[0]} if quoted else {}
                return CommandPlan(
                    text,
                    "subjects.recycle.restore",
                    parameters=parameters,
                    confidence=0.98 if quoted else 0.82,
                    missing_fields=[] if quoted else ["subject"],
                    message="请用书名号提供要恢复的专题。" if not quoted else "",
                )
            return CommandPlan(
                text,
                "subjects.recycle.list",
                parameters={"search": quoted[0]}
                if quoted and re.search(r"搜索|查找", text)
                else {},
                confidence=0.97,
            )
        subject_is_direct_object = bool(
            re.search(r"(?:把|将|移动|删除|发布|取消发布)\s*专题\s*[《“\"']", text)
        )
        if "文件夹" in text and not subject_is_direct_object:
            if re.search(r"新建|创建", text):
                parameters: dict[str, Any] = {}
                if len(quoted) >= 2 and re.search(r"在.*文件夹.*(?:新建|创建)", text):
                    parameters["parent_folder"] = quoted[0]
                    parameters["name"] = quoted[1]
                elif quoted:
                    parameters["name"] = quoted[0]
                    if len(quoted) >= 2:
                        parameters["parent_folder"] = quoted[1]
                return CommandPlan(
                    text,
                    "subjects.folder.create",
                    parameters=parameters,
                    confidence=0.98 if quoted else 0.8,
                    missing_fields=[] if quoted else ["name"],
                    message="请用书名号提供专题文件夹名称。" if not quoted else "",
                )
            if re.search(r"重命名|改名|改为", text):
                parameters = {}
                if quoted:
                    parameters["folder"] = quoted[0]
                if len(quoted) >= 2:
                    parameters["name"] = quoted[1]
                missing = [key for key in ("folder", "name") if key not in parameters]
                return CommandPlan(
                    text,
                    "subjects.folder.rename",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.8,
                    missing_fields=missing,
                    message="请依次用书名号提供原文件夹和新名称。" if missing else "",
                )
            if re.search(r"移动|移到", text):
                parameters = {"folder": quoted[0]} if quoted else {}
                if len(quoted) >= 2:
                    parameters["target_folder"] = quoted[1]
                elif re.search(r"根目录", text):
                    parameters["target_folder"] = "-1"
                return CommandPlan(
                    text,
                    "subjects.folder.move",
                    parameters=parameters,
                    confidence=0.98 if quoted else 0.8,
                    missing_fields=[] if quoted else ["folder"],
                    message="请用书名号提供要移动的专题文件夹。" if not quoted else "",
                )
            if re.search(r"删除|移除", text):
                parameters = {"folder": quoted[0]} if quoted else {}
                if re.search(r"非空|连同内容|包含内容", text):
                    parameters["allow_nonempty"] = True
                return CommandPlan(
                    text,
                    "subjects.folder.delete",
                    parameters=parameters,
                    confidence=0.98 if quoted else 0.8,
                    missing_fields=[] if quoted else ["folder"],
                    message="请用书名号提供要删除的专题文件夹。" if not quoted else "",
                )
        if re.search(r"取消发布|下线", text):
            parameters = {"subject": quoted[0], "published": False} if quoted else {}
            return CommandPlan(
                text,
                "subjects.publish_status.update",
                parameters=parameters,
                confidence=0.98 if quoted else 0.82,
                missing_fields=[] if quoted else ["subject"],
                message="请用书名号提供要取消发布的专题。" if not quoted else "",
            )
        if re.search(r"发布|上线", text):
            parameters = {"subject": quoted[0], "published": True} if quoted else {}
            return CommandPlan(
                text,
                "subjects.publish_status.update",
                parameters=parameters,
                confidence=0.98 if quoted else 0.82,
                missing_fields=[] if quoted else ["subject"],
                message="请用书名号提供要发布的专题。" if not quoted else "",
            )
        if re.search(r"移动|移到", text):
            parameters = {"subject": quoted[0]} if quoted else {}
            if len(quoted) >= 2:
                parameters["target_folder"] = quoted[1]
            elif re.search(r"根目录", text):
                parameters["target_folder"] = "-1"
            return CommandPlan(
                text,
                "subjects.move",
                parameters=parameters,
                confidence=0.98 if quoted else 0.8,
                missing_fields=[] if quoted else ["subject"],
                message="请用书名号提供要移动的专题。" if not quoted else "",
            )
        if re.search(r"删除|移除", text):
            parameters = {"subject": quoted[0]} if quoted else {}
            return CommandPlan(
                text,
                "subjects.delete",
                parameters=parameters,
                confidence=0.98 if quoted else 0.8,
                missing_fields=[] if quoted else ["subject"],
                message="请用书名号提供要删除的专题。" if not quoted else "",
            )
        parameters = {}
        if quoted:
            if re.search(r"搜索|查找|检索", text):
                parameters["search"] = quoted[0]
            else:
                parameters["folder"] = quoted[0]
        return CommandPlan(text, "subjects.items.list", parameters=parameters, confidence=0.92)

    if re.search(r"个人空间|空间功能", text) and re.search(r"菜单|列出|查看|有哪些|入口", text):
        return CommandPlan(text, "space.modules.discover", confidence=0.97)

    job_ability_status_intent = bool(
        re.search(r"岗位能力.{0,12}(状态|权限|开放|可用)|学校.{0,6}岗位库", text)
    )
    job_ability_intent = job_ability_status_intent or bool(
        re.search(
            r"招聘岗位|岗位搜索|职位搜索|热门岗位|高薪岗位|职业百科|职业目录|"
            r"职业搜索|搜索职业|行业类型|行业分类|行业岗位|岗位库条目",
            text,
        )
    )
    if job_ability_intent:
        quoted = _extract_quoted(text)
        education_match = re.search(
            r"(?:学历|层次|教育程度)?\s*(本科|专科|大专|硕士|研究生|博士|高中|中专)",
            text,
        )
        base: dict[str, Any] = {}
        if education_match:
            base["education_level"] = education_match.group(1)
        page_match = re.search(r"第\s*(\d+)\s*页", text)
        if page_match:
            base["page"] = int(page_match.group(1))
        page_size_match = re.search(r"每页\s*(\d+)\s*(?:条|项|个)?", text)
        if page_size_match:
            base["page_size"] = int(page_size_match.group(1))

        if job_ability_status_intent:
            return CommandPlan(text, "job_ability.status.read", confidence=0.98)
        if re.search(r"热门岗位|高薪岗位", text):
            return CommandPlan(
                text,
                "job_ability.popular_jobs.list",
                parameters=base,
                confidence=0.98,
            )
        if re.search(r"职业百科|职业目录|职业搜索|搜索职业", text):
            if re.search(r"搜索|查找|检索", text):
                if quoted:
                    base["keyword"] = quoted[-1]
                missing = [] if "keyword" in base else ["keyword"]
                return CommandPlan(
                    text,
                    "job_ability.occupations.search",
                    parameters=base,
                    confidence=0.98 if not missing else 0.78,
                    missing_fields=missing,
                    message="请用书名号提供职业搜索关键词。" if missing else "",
                )
            return CommandPlan(
                text,
                "job_ability.occupation_catalog.read",
                parameters=base,
                confidence=0.97,
            )
        if re.search(r"行业类型|行业分类", text) and not re.search(
            r"下的|下面的|中的|对应的|所属", text
        ):
            return CommandPlan(
                text,
                "job_ability.industry_types.list",
                parameters=base,
                confidence=0.97,
            )
        if re.search(r"行业岗位|岗位库条目|行业.{0,8}(岗位|职位)", text):
            if quoted:
                base["industry"] = quoted[-1]
            missing = [] if "industry" in base else ["industry"]
            return CommandPlan(
                text,
                "job_ability.industry_jobs.list",
                parameters=base,
                confidence=0.98 if not missing else 0.78,
                missing_fields=missing,
                message="请用书名号提供岗位分类。" if missing else "",
            )
        if re.search(r"行业", text) and re.search(r"下|分类|目录|包含|有哪些", text):
            if quoted:
                base["industry_type"] = quoted[-1]
            missing = [] if "industry_type" in base else ["industry_type"]
            return CommandPlan(
                text,
                "job_ability.industries.list",
                parameters=base,
                confidence=0.97 if not missing else 0.76,
                missing_fields=missing,
                message="请用书名号提供行业类型。" if missing else "",
            )
        if re.search(r"详情|详细|完整信息|读取岗位", text):
            if quoted:
                base["job"] = quoted[0]
            if len(quoted) >= 2:
                base["search"] = quoted[1]
            missing = [] if "job" in base else ["job"]
            return CommandPlan(
                text,
                "job_ability.job_ad.read",
                parameters=base,
                confidence=0.98 if not missing else 0.78,
                missing_fields=missing,
                message="请用书名号提供岗位 ID、岗位名或企业与岗位组合。" if missing else "",
            )
        if quoted:
            base["keyword"] = quoted[-1]
        missing = [] if "keyword" in base else ["keyword"]
        return CommandPlan(
            text,
            "job_ability.jobs.search",
            parameters=base,
            confidence=0.98 if not missing else 0.76,
            missing_fields=missing,
            message="请用书名号提供招聘岗位搜索关键词。" if missing else "",
        )

    if "笔记" in text:
        quoted = _extract_quoted(text)
        if re.search(r"删除|移除", text):
            parameters = {"note": quoted[0]} if quoted else {}
            return CommandPlan(
                text,
                "notes.delete",
                parameters=parameters,
                confidence=0.98 if quoted else 0.82,
                missing_fields=[] if quoted else ["note"],
                message="请提供要删除的笔记标题、序号或 CID。" if not quoted else "",
            )
        if re.search(r"新建|创建|记一条|写一条|添加", text):
            parameters = {}
            if quoted:
                parameters["title"] = quoted[0]
            if len(quoted) >= 2:
                parameters["content"] = quoted[1]
            return CommandPlan(
                text,
                "notes.create",
                parameters=parameters,
                confidence=0.97 if quoted else 0.8,
                missing_fields=[] if quoted else ["title"],
                message="请用书名号提供新笔记标题。" if not quoted else "",
            )
        if re.search(r"修改|编辑|更新|改名|重命名|改为", text):
            parameters = {"note": quoted[0]} if quoted else {}
            if len(quoted) >= 2:
                if re.search(r"标题|改名|重命名", text):
                    parameters["title"] = quoted[1]
                if re.search(r"内容|正文", text):
                    parameters["content"] = quoted[-1]
            missing = []
            if not quoted:
                missing.append("note")
            if len(quoted) < 2:
                missing.append("title_or_content")
            return CommandPlan(
                text,
                "notes.update",
                parameters=parameters,
                confidence=0.97 if not missing else 0.8,
                missing_fields=missing,
                message=("请用书名号提供原笔记和新的标题或正文。" if missing else ""),
            )
        if re.search(r"搜索|查找|检索", text):
            return CommandPlan(
                text,
                "notes.list",
                parameters={"search": quoted[-1]} if quoted else {},
                confidence=0.96,
            )
        if quoted and re.search(r"读取|查看|打开|详情|内容|正文", text):
            return CommandPlan(
                text,
                "notes.read",
                parameters={"note": quoted[0]},
                confidence=0.98,
            )
        if re.search(r"列出|查看|显示|有哪些|列表", text):
            return CommandPlan(text, "notes.list", confidence=0.96)
        if re.search(r"打开|进入", text):
            return CommandPlan(
                text,
                "space.module.open",
                parameters={"module": "笔记"},
                confidence=0.95,
            )

    if any(
        marker in text
        for marker in (
            "收件箱",
            "已发送通知",
            "收到的通知",
            "个人通知",
            "站内通知",
            "通知文件夹",
            "通知回收站",
        )
    ):
        quoted = _extract_quoted(text)
        scope = "sent" if re.search(r"已发送|发出的|我发的", text) else "received"
        base_parameters: dict[str, object] = {"scope": scope}
        if "回收站" in text:
            if re.search(r"清空", text):
                return CommandPlan(text, "inbox.recycle.empty", confidence=0.99)
            if re.search(r"永久删除|彻底删除|完全删除", text):
                return CommandPlan(
                    text,
                    "inbox.recycle.items.delete",
                    parameters={"notices": quoted} if quoted else {},
                    confidence=0.98 if quoted else 0.82,
                    missing_fields=[] if quoted else ["notices"],
                    message="请用书名号提供要永久删除的回收站通知。" if not quoted else "",
                )
            if re.search(r"恢复|还原", text):
                return CommandPlan(
                    text,
                    "inbox.recycle.restore",
                    parameters={"notices": quoted} if quoted else {},
                    confidence=0.98 if quoted else 0.82,
                    missing_fields=[] if quoted else ["notices"],
                    message="请用书名号提供要恢复的回收站通知。" if not quoted else "",
                )
            parameters = {"search": quoted[-1]} if quoted else {}
            return CommandPlan(
                text,
                "inbox.recycle.list",
                parameters=parameters,
                confidence=0.98,
            )
        if "文件夹" in text:
            if re.search(r"移动|移入|移到|归入|移出|移回", text) and "通知" in text:
                destination_match = re.search(
                    r"(?:到|至|进|入)(?:收件箱)?(?:通知)?文件夹[：:\s]*[《“\"]([^》”\"]+)[》”\"]",
                    text,
                )
                destination = destination_match.group(1).strip() if destination_match else ""
                root_destination = bool(
                    re.search(r"移(?:回|到|至|出).{0,8}收件箱(?:根目录)?", text)
                )
                values = list(quoted)
                if destination and destination in values:
                    values.remove(destination)
                if not destination and not root_destination and values:
                    destination = values.pop()
                parameters: dict[str, object] = {
                    "scope": scope,
                    "destination_folder": "root" if root_destination else destination,
                }
                if values:
                    parameters["notices"] = values
                missing = [
                    key for key in ("notices", "destination_folder") if not parameters.get(key)
                ]
                return CommandPlan(
                    text,
                    "inbox.notices.move",
                    parameters=parameters,
                    confidence=0.97 if not missing else 0.76,
                    missing_fields=missing,
                    message="请说明通知和目标收件箱文件夹。" if missing else "",
                )
            if re.search(r"排序|顺序|排列", text):
                return CommandPlan(
                    text,
                    "inbox.folders.reorder",
                    parameters={
                        "folders": quoted,
                        "top": bool(re.search(r"置顶文件夹|顶部文件夹", text)),
                    }
                    if quoted
                    else {},
                    confidence=0.96 if quoted else 0.78,
                    missing_fields=[] if quoted else ["folders"],
                    message="请按目标顺序用书名号列出同组的全部收件箱文件夹。"
                    if not quoted
                    else "",
                )
            if re.search(r"删除|移除", text):
                return CommandPlan(
                    text,
                    "inbox.folder.delete",
                    parameters={"folder": quoted[0]} if quoted else {},
                    confidence=0.98 if quoted else 0.82,
                    missing_fields=[] if quoted else ["folder"],
                    message="请用书名号提供要删除的收件箱文件夹。" if not quoted else "",
                )
            if re.search(r"重命名|改名|修改名称", text):
                parameters = {}
                if quoted:
                    parameters["folder"] = quoted[0]
                if len(quoted) >= 2:
                    parameters["name"] = quoted[1]
                missing = [key for key in ("folder", "name") if key not in parameters]
                return CommandPlan(
                    text,
                    "inbox.folder.update",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.78,
                    missing_fields=missing,
                    message="请依次用书名号提供原文件夹和新名称。" if missing else "",
                )
            if re.search(r"新建|创建|添加", text):
                return CommandPlan(
                    text,
                    "inbox.folder.create",
                    parameters={"name": quoted[0]} if quoted else {},
                    confidence=0.98 if quoted else 0.82,
                    missing_fields=[] if quoted else ["name"],
                    message="请用书名号提供新收件箱文件夹名称。" if not quoted else "",
                )
            if re.search(r"规则|筛选|收纳", text):
                return CommandPlan(
                    text,
                    "inbox.folder.filters.read",
                    parameters={"folder": quoted[0]} if quoted else {},
                    confidence=0.97 if quoted else 0.8,
                    missing_fields=[] if quoted else ["folder"],
                    message="请用书名号提供收件箱文件夹。" if not quoted else "",
                )
            if "通知" in text and quoted:
                parameters = {"folder": quoted[0], "scope": scope}
                if len(quoted) >= 2:
                    parameters["search"] = quoted[-1]
                return CommandPlan(
                    text,
                    "inbox.folder.notices.list",
                    parameters=parameters,
                    confidence=0.97,
                )
            return CommandPlan(text, "inbox.folders.list", confidence=0.97)
        if "草稿" in text:
            if re.search(r"删除|移除", text):
                return CommandPlan(
                    text,
                    "inbox.draft.delete",
                    parameters={"draft": quoted[0]} if quoted else {},
                    confidence=0.98 if quoted else 0.82,
                    missing_fields=[] if quoted else ["draft"],
                    message="请用书名号提供要删除的个人通知草稿。" if not quoted else "",
                )
            if re.search(r"保存|新建|创建|修改|更新|编辑", text):
                parameters: dict[str, object] = {}
                if quoted:
                    parameters["title"] = quoted[0]
                if len(quoted) >= 2:
                    parameters["content"] = quoted[1]
                if len(quoted) >= 3:
                    parameters["recipients"] = quoted[2:]
                missing = []
                if not quoted:
                    missing.append("title")
                if len(quoted) < 2:
                    missing.append("content")
                return CommandPlan(
                    text,
                    "inbox.draft.save",
                    parameters=parameters,
                    confidence=0.96 if not missing else 0.78,
                    missing_fields=missing,
                    message="请依次用书名号提供草稿标题和正文。" if missing else "",
                )
            parameters = {"search": quoted[-1]} if quoted else {}
            return CommandPlan(
                text,
                "inbox.drafts.list",
                parameters=parameters,
                confidence=0.97,
            )
        if re.search(r"发送|发给|寄给", text) and re.search(r"个人通知|站内通知", text):
            recipient_match = re.search(
                r"(?:给|收件人(?:是|为)?)[：:\s]*[《“\"]([^》”\"]+)[》”\"]",
                text,
            )
            recipient = recipient_match.group(1).strip() if recipient_match else ""
            values = list(quoted)
            if recipient and recipient in values:
                values.remove(recipient)
            parameters = {}
            if recipient:
                parameters["recipients"] = [recipient]
            if values:
                parameters["title"] = values[0]
            if len(values) >= 2:
                parameters["content"] = values[1]
            missing = [key for key in ("recipients", "title", "content") if key not in parameters]
            return CommandPlan(
                text,
                "inbox.notice.send",
                parameters=parameters,
                confidence=0.97 if not missing else 0.76,
                missing_fields=missing,
                message=("请说明个人收件人，并依次用书名号提供通知标题和正文。" if missing else ""),
            )
        if re.search(r"删除|移除", text) and "通知" in text:
            if quoted:
                base_parameters["notice"] = quoted[0]
            return CommandPlan(
                text,
                "inbox.notice.delete",
                parameters=base_parameters,
                confidence=0.98 if quoted else 0.82,
                missing_fields=[] if quoted else ["notice"],
                message="请用书名号提供要删除的通知标题或通知 ID。" if not quoted else "",
            )
        if re.search(r"标为未读|设为未读|改为未读|重新未读", text):
            parameters = {"scope": "received"}
            if quoted:
                parameters["notice"] = quoted[0]
            return CommandPlan(
                text,
                "inbox.notice.mark_unread",
                parameters=parameters,
                confidence=0.98 if quoted else 0.82,
                missing_fields=[] if quoted else ["notice"],
                message="请用书名号提供要标为未读的通知。" if not quoted else "",
            )
        if re.search(r"置顶|取消置顶", text) and "通知" in text:
            if quoted:
                base_parameters["notice"] = quoted[0]
            base_parameters["top"] = "取消置顶" not in text
            return CommandPlan(
                text,
                "inbox.notice.top_status.update",
                parameters=base_parameters,
                confidence=0.98 if quoted else 0.82,
                missing_fields=[] if quoted else ["notice"],
                message="请用书名号提供要设置置顶状态的通知。" if not quoted else "",
            )
        if re.search(r"收藏|取消收藏", text) and "通知" in text:
            if quoted:
                base_parameters["notice"] = quoted[0]
            base_parameters["collect"] = "取消收藏" not in text
            return CommandPlan(
                text,
                "inbox.notice.collect_status.update",
                parameters=base_parameters,
                confidence=0.98 if quoted else 0.82,
                missing_fields=[] if quoted else ["notice"],
                message="请用书名号提供要设置收藏状态的通知。" if not quoted else "",
            )
        if quoted and re.search(r"读取|查看|打开|内容|详情", text):
            base_parameters["notice"] = quoted[0]
            return CommandPlan(
                text,
                "inbox.notice.read",
                parameters=base_parameters,
                confidence=0.98,
            )
        if re.search(r"搜索|查找|检索", text):
            if quoted:
                base_parameters["search"] = quoted[-1]
            return CommandPlan(
                text,
                "inbox.notices.list",
                parameters=base_parameters,
                confidence=0.97,
            )
        if re.search(r"列出|查看|显示|有哪些|列表|已发送", text):
            return CommandPlan(
                text,
                "inbox.notices.list",
                parameters=base_parameters,
                confidence=0.97,
            )

    if re.search(r"通讯录团队|自建团队", text):
        quoted = _extract_quoted(text)
        if re.search(r"删除", text) and "成员" not in text:
            return CommandPlan(
                text,
                "contacts.team.delete",
                parameters={"team": quoted[0]} if quoted else {},
                confidence=0.98 if quoted else 0.8,
                missing_fields=[] if quoted else ["team"],
                message="请用书名号提供要删除的通讯录团队。" if not quoted else "",
            )
        if re.search(r"退出", text):
            return CommandPlan(
                text,
                "contacts.team.exit",
                parameters={"team": quoted[0]} if quoted else {},
                confidence=0.98 if quoted else 0.8,
                missing_fields=[] if quoted else ["team"],
                message="请用书名号提供要退出的通讯录团队。" if not quoted else "",
            )
        if re.search(r"重命名|改名", text):
            parameters = {}
            if quoted:
                parameters["team"] = quoted[0]
            if len(quoted) > 1:
                parameters["name"] = quoted[1]
            missing = []
            if not quoted:
                missing.append("team")
            if len(quoted) < 2:
                missing.append("name")
            return CommandPlan(
                text,
                "contacts.team.rename",
                parameters=parameters,
                confidence=0.98 if not missing else 0.8,
                missing_fields=missing,
                message="请依次用书名号提供原团队和新名称。" if missing else "",
            )
        if re.search(r"新建|创建", text):
            parameters = {}
            if quoted:
                parameters["name"] = quoted[0]
            if len(quoted) > 1:
                parameters["members"] = quoted[1:]
            missing = []
            if not quoted:
                missing.append("name")
            if len(quoted) < 2:
                missing.append("members")
            return CommandPlan(
                text,
                "contacts.team.create",
                parameters=parameters,
                confidence=0.98 if not missing else 0.8,
                missing_fields=missing,
                message="请依次用书名号提供团队名称和至少一名成员。" if missing else "",
            )
        if re.search(r"添加|加入", text) and "成员" in text:
            parameters = {}
            if quoted:
                parameters["team"] = quoted[0]
            if len(quoted) > 1:
                parameters["members"] = quoted[1:]
            missing = []
            if not quoted:
                missing.append("team")
            if len(quoted) < 2:
                missing.append("members")
            return CommandPlan(
                text,
                "contacts.team.members.add",
                parameters=parameters,
                confidence=0.98 if not missing else 0.8,
                missing_fields=missing,
                message="请依次用书名号提供团队和要添加的成员。" if missing else "",
            )
        if re.search(r"移除|删除", text) and "成员" in text:
            parameters = {}
            if quoted:
                parameters["team"] = quoted[0]
            if len(quoted) > 1:
                parameters["member"] = quoted[1]
            missing = []
            if not quoted:
                missing.append("team")
            if len(quoted) < 2:
                missing.append("member")
            return CommandPlan(
                text,
                "contacts.team.member.remove",
                parameters=parameters,
                confidence=0.98 if not missing else 0.8,
                missing_fields=missing,
                message="请依次用书名号提供团队和要移除的成员。" if missing else "",
            )
        if "成员" in text and re.search(r"列出|查看|显示|有哪些|列表", text):
            return CommandPlan(
                text,
                "contacts.team.members.list",
                parameters={"team": quoted[0]} if quoted else {},
                confidence=0.98 if quoted else 0.8,
                missing_fields=[] if quoted else ["team"],
                message="请用书名号提供通讯录团队。" if not quoted else "",
            )
        if re.search(r"列出|查看|显示|有哪些|列表", text):
            return CommandPlan(text, "contacts.teams.list", confidence=0.97)

    if "群聊" in text and re.search(r"通讯录|加入|我的|成员", text):
        quoted = _extract_quoted(text)
        if "成员" in text:
            return CommandPlan(
                text,
                "contacts.chatgroup.members.list",
                parameters={"chatgroup": quoted[0]} if quoted else {},
                confidence=0.98 if quoted else 0.8,
                missing_fields=[] if quoted else ["chatgroup"],
                message="请用书名号提供群聊名称、序号或 ID。" if not quoted else "",
            )
        if re.search(r"列出|查看|显示|有哪些|列表", text):
            return CommandPlan(text, "contacts.chatgroups.list", confidence=0.97)

    if "小组" in text and "通讯录" in text:
        quoted = _extract_quoted(text)
        if "成员" in text:
            return CommandPlan(
                text,
                "contacts.group.members.list",
                parameters={"group": quoted[0]} if quoted else {},
                confidence=0.98 if quoted else 0.8,
                missing_fields=[] if quoted else ["group"],
                message="请用书名号提供小组名称、序号或 ID。" if not quoted else "",
            )
        parameters = {"search": quoted[-1]} if quoted and re.search(r"搜索|查找", text) else {}
        return CommandPlan(text, "contacts.groups.list", parameters=parameters, confidence=0.97)

    if re.search(r"关注我的|我的粉丝|粉丝列表", text):
        return CommandPlan(
            text,
            "contacts.relations.list",
            parameters={"relation": "followers"},
            confidence=0.98,
        )

    if re.search(r"我关注的|关注列表", text) and re.search(r"联系人|通讯录|人员|人", text):
        return CommandPlan(
            text,
            "contacts.relations.list",
            parameters={"relation": "following"},
            confidence=0.98,
        )

    if re.search(r"联系人|通讯录人员", text) and re.search(r"取消关注|关注", text):
        quoted = _extract_quoted(text)
        return CommandPlan(
            text,
            "contacts.follow_status.update",
            parameters={
                **({"person": quoted[0]} if quoted else {}),
                "followed": "取消关注" not in text,
            },
            confidence=0.98 if quoted else 0.8,
            missing_fields=[] if quoted else ["person"],
            message="请用书名号提供联系人姓名或 PUID。" if not quoted else "",
        )

    if re.search(r"通讯录|联系人", text) and re.search(r"搜索|查找|检索", text):
        quoted = _extract_quoted(text)
        return CommandPlan(
            text,
            "contacts.people.search",
            parameters={"search": quoted[0]} if quoted else {},
            confidence=0.98 if quoted else 0.8,
            missing_fields=[] if quoted else ["search"],
            message="请用书名号提供联系人搜索词。" if not quoted else "",
        )

    if (
        re.search(r"通讯录|联系人", text)
        and "部门" in text
        and re.search(r"列出|查看|显示|有哪些|列表", text)
    ):
        quoted = _extract_quoted(text)
        fid_match = re.search(r"(?:FID|单位ID)\s*[=:：]?\s*([A-Za-z0-9_-]+)", text, re.I)
        department_match = re.search(
            r"(?:部门ID|dept(?:artment)?_?id)\s*[=:：]?\s*([A-Za-z0-9_-]+)",
            text,
            re.I,
        )
        parameters: dict[str, Any] = {}
        if fid_match:
            parameters["fid"] = fid_match.group(1)
        elif quoted:
            parameters["fid"] = quoted[0]
        if "成员" in text:
            if department_match:
                parameters["department_id"] = department_match.group(1)
            elif len(quoted) >= 2:
                parameters["department_id"] = quoted[1]
            if len(quoted) >= 3:
                parameters["search"] = quoted[2]
            missing = [key for key in ("fid", "department_id") if key not in parameters]
            return CommandPlan(
                text,
                "contacts.department.members.list",
                parameters=parameters,
                confidence=0.98 if not missing else 0.78,
                missing_fields=missing,
                message=(
                    "请依次提供单位 FID 和部门 ID；需要时再提供成员搜索词。" if missing else ""
                ),
            )
        if len(quoted) >= 2:
            parameters["parent_id"] = quoted[1]
        parameters["department_type"] = "custom" if re.search(r"自建|团队", text) else "unit"
        missing = [] if "fid" in parameters else ["fid"]
        return CommandPlan(
            text,
            "contacts.departments.list",
            parameters=parameters,
            confidence=0.98 if not missing else 0.8,
            missing_fields=missing,
            message="请提供单位 FID；需要读取下级部门时再提供父部门 ID。" if missing else "",
        )

    if "通讯录" in text and "单位" in text and re.search(r"列出|查看|显示|有哪些|列表", text):
        return CommandPlan(text, "contacts.units.list", confidence=0.97)

    personal_group_reference = bool(
        re.search(
            r"我的小组|个人小组|小组文件夹|小组标签|小组回收站|小组删除原因|小组活动|活动图|小组导出|小组下载中心|小组等级|小组头衔|小组成长值|小组积分规则|小组审核提醒|审核提醒|小组模块|功能模块",
            text,
        )
        or (
            "小组" in text
            and re.search(
                r"新建|创建|修改|更换|上传|退出|解散|置顶|取消置顶|移动|重命名|发送|发布|导出|下载",
                text,
            )
        )
        or ("小组" in text and re.search(r"成员|管理员|创建者|所有者|转让|邀请|移除|清除", text))
        or (
            "小组" in text
            and _extract_quoted(text)
            and re.search(r"详情|设置|读取|打开|查看|搜索|查找", text)
        )
    )
    if personal_group_reference and "通讯录" not in text:
        quoted = _extract_quoted(text)
        intent_text = re.sub(r"《[^》]*》|“[^”]*”|\"[^\"]*\"|'[^']*'", "", text)
        if re.search(r"头像|logo|图标", intent_text, re.I) and re.search(
            r"修改|更换|上传|设置", intent_text
        ):
            parameters: dict[str, object] = {}
            if quoted:
                parameters["group"] = quoted[0]
            if len(quoted) >= 2:
                parameters["file"] = quoted[1]
            missing = [key for key in ("group", "file") if key not in parameters]
            return CommandPlan(
                text,
                "groups.logo.update",
                parameters=parameters,
                confidence=0.99 if not missing else 0.76,
                missing_fields=missing,
                message="请依次用书名号提供个人小组和本地图像路径。" if missing else "",
            )
        if re.search(r"模块配置|功能模块|小组模块", intent_text):
            parameters: dict[str, object] = {"group": quoted[0]} if quoted else {}
            if re.search(r"修改|设置|启用|关闭|只保留", intent_text):
                type_ids = list(
                    dict.fromkeys(
                        [value for value in quoted[1:] if value.isdigit()]
                        + re.findall(r"(?:类型|type)\s*(\d+)", intent_text, re.IGNORECASE)
                    )
                )
                if type_ids or "只保留视频" in intent_text:
                    parameters["enabled_type_ids"] = type_ids
                missing = [key for key in ("group", "enabled_type_ids") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.modules.update",
                    parameters=parameters,
                    confidence=0.99 if not missing else 0.74,
                    missing_fields=missing,
                    message="请提供个人小组和管理页实际列出的启用模块类型 ID。" if missing else "",
                )
            return CommandPlan(
                text,
                "groups.modules.list",
                parameters=parameters,
                confidence=0.99 if quoted else 0.78,
                missing_fields=[] if quoted else ["group"],
                message="请用书名号提供个人小组。" if not quoted else "",
            )
        if "审核提醒" in intent_text:
            parameters: dict[str, object] = {"group": quoted[0]} if quoted else {}
            normalized_times = [
                f"{int(hour):02d}:{minute}"
                for hour, minute in re.findall(
                    r"(?<!\d)([01]?\d|2[0-3]):([0-5]\d)(?!\d)", intent_text
                )
            ]
            weeks = list(dict.fromkeys(re.findall(r"(?:星期|周)[一二三四五六日天]", intent_text)))
            puids = list(
                dict.fromkeys(
                    [value for value in quoted[1:] if value.isdigit()]
                    + re.findall(r"(?<![\w:])\d{6,18}(?![\w:])", intent_text)
                )
            )
            if re.search(r"删除|移除|取消", intent_text):
                reminders = quoted[1:]
                if reminders:
                    parameters["reminders"] = reminders
                missing = [key for key in ("group", "reminders") if not parameters.get(key)]
                return CommandPlan(
                    text,
                    "groups.review_reminders.delete",
                    parameters=parameters,
                    confidence=0.99 if not missing else 0.75,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组和一个或多个提醒 UUID 或序号。"
                    if missing
                    else "",
                )
            if re.search(r"新建|创建|添加|设置", intent_text):
                if len(normalized_times) >= 2:
                    parameters["start_time"], parameters["end_time"] = normalized_times[:2]
                if weeks:
                    parameters["weeks"] = weeks
                if puids:
                    parameters["puids"] = puids
                missing = [
                    key
                    for key in ("group", "start_time", "end_time", "weeks", "puids")
                    if not parameters.get(key)
                ]
                return CommandPlan(
                    text,
                    "groups.review_reminder.create",
                    parameters=parameters,
                    confidence=0.99 if not missing else 0.7,
                    missing_fields=missing,
                    message="请提供个人小组、开始和结束时间、重复星期及审核人员 PUID。"
                    if missing
                    else "",
                )
            if re.search(r"修改|更新|编辑|调整|改为", intent_text):
                if len(quoted) >= 2:
                    parameters["reminder"] = quoted[1]
                if normalized_times:
                    parameters["start_time"] = normalized_times[0]
                if len(normalized_times) >= 2:
                    parameters["end_time"] = normalized_times[1]
                if weeks:
                    parameters["weeks"] = weeks
                if puids:
                    parameters["puids"] = puids
                missing = [key for key in ("group", "reminder") if not parameters.get(key)]
                if not any(
                    key in parameters for key in ("start_time", "end_time", "weeks", "puids")
                ):
                    missing.append("changes")
                return CommandPlan(
                    text,
                    "groups.review_reminder.update",
                    parameters=parameters,
                    confidence=0.99 if not missing else 0.72,
                    missing_fields=missing,
                    message=(
                        "请提供个人小组、提醒 UUID 或序号，以及至少一项时间、星期或审核人员修改。"
                    )
                    if missing
                    else "",
                )
            return CommandPlan(
                text,
                "groups.review_reminders.list",
                parameters=parameters,
                confidence=0.99 if quoted else 0.78,
                missing_fields=[] if quoted else ["group"],
                message="请用书名号提供个人小组。" if not quoted else "",
            )
        if re.search(r"成长值规则|积分规则", intent_text):
            parameters: dict[str, object] = {"group": quoted[0]} if quoted else {}
            if re.search(r"切换|恢复|启用|改用", intent_text) and re.search(
                r"默认|自定义", intent_text
            ):
                parameters["series"] = "custom" if "自定义" in intent_text else "default"
                return CommandPlan(
                    text,
                    "groups.growth_rules.series.update",
                    parameters=parameters,
                    confidence=0.99 if quoted else 0.78,
                    missing_fields=[] if quoted else ["group"],
                    message="请用书名号提供个人小组。" if not quoted else "",
                )
            if re.search(r"修改|设置|调整|改为|设为", intent_text):
                growth_type_aliases = {
                    "首次加入": 1,
                    "加入小组": 1,
                    "发表话题": 2,
                    "话题加精": 3,
                    "加精话题": 3,
                    "发表评论": 4,
                    "发布评论": 4,
                    "点赞互动": 5,
                    "被评论": 6,
                    "话题被回复": 6,
                }
                growth_type = 0
                if len(quoted) >= 2 and quoted[1].isdigit():
                    growth_type = int(quoted[1])
                if not growth_type:
                    for alias, type_id in growth_type_aliases.items():
                        if alias in text:
                            growth_type = type_id
                            break
                value_match = re.search(r"(?:设为|改为|调整为|=)\s*(\d+)", intent_text)
                if growth_type:
                    parameters["changes"] = (
                        {str(growth_type): int(value_match.group(1))} if value_match else {}
                    )
                missing = [key for key in ("group", "changes") if not parameters.get(key)]
                return CommandPlan(
                    text,
                    "groups.growth_rules.update",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.72,
                    missing_fields=missing,
                    message="请提供个人小组、成长行为类型和新的成长值。" if missing else "",
                )
            return CommandPlan(
                text,
                "groups.growth_rules.list",
                parameters=parameters,
                confidence=0.98 if quoted else 0.78,
                missing_fields=[] if quoted else ["group"],
                message="请用书名号提供个人小组。" if not quoted else "",
            )
        if re.search(r"等级|头衔", intent_text):
            parameters = {"group": quoted[0]} if quoted else {}
            if re.search(r"切换|恢复|启用|改用", intent_text) and re.search(
                r"默认|自定义", intent_text
            ):
                parameters["series"] = "custom" if "自定义" in intent_text else "default"
                return CommandPlan(
                    text,
                    "groups.levels.series.update",
                    parameters=parameters,
                    confidence=0.99 if quoted else 0.78,
                    missing_fields=[] if quoted else ["group"],
                    message="请用书名号提供个人小组。" if not quoted else "",
                )
            if "自定义" in intent_text and re.search(r"修改|设置|保存|更新", intent_text):
                levels_match = re.search(r"(\[\s*\{.*\}\s*\])", text, re.S)
                if levels_match:
                    try:
                        levels = json.loads(levels_match.group(1))
                    except json.JSONDecodeError:
                        levels = None
                    if isinstance(levels, list):
                        parameters["levels"] = levels
                missing = [key for key in ("group", "levels") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.levels.custom.update",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.72,
                    missing_fields=missing,
                    message="请提供个人小组和包含 15 个等级对象的 JSON 数组。" if missing else "",
                )
            return CommandPlan(
                text,
                "groups.levels.list",
                parameters=parameters,
                confidence=0.98 if quoted else 0.78,
                missing_fields=[] if quoted else ["group"],
                message="请用书名号提供个人小组。" if not quoted else "",
            )
        if re.search(r"导出|下载中心", intent_text):
            parameters: dict[str, object] = {"group": quoted[0]} if quoted else {}
            if (
                re.search(r"成员|成员名单", intent_text)
                and re.search(r"导出|生成", intent_text)
                and not re.search(r"下载|取消|删除|重试|重新", intent_text)
            ):
                return CommandPlan(
                    text,
                    "groups.members.export.create",
                    parameters=parameters,
                    confidence=0.99 if quoted else 0.78,
                    missing_fields=[] if quoted else ["group"],
                    message="请用书名号提供个人小组。" if not quoted else "",
                )
            if re.search(r"取消|删除", intent_text):
                if len(quoted) >= 2:
                    parameters["export"] = quoted[1]
                missing = [key for key in ("group", "export") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.export.cancel",
                    parameters=parameters,
                    confidence=0.99 if not missing else 0.76,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组和导出任务。" if missing else "",
                )
            if re.search(r"重试|重新导出", intent_text):
                if len(quoted) >= 2:
                    parameters["export"] = quoted[1]
                missing = [key for key in ("group", "export") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.export.retry",
                    parameters=parameters,
                    confidence=0.99 if not missing else 0.76,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组和失败的导出任务。" if missing else "",
                )
            if re.search(r"等待|等到|完成状态", intent_text):
                if len(quoted) >= 2:
                    parameters["export"] = quoted[1]
                timeout_match = re.search(r"(?:最多|最长|等待)\s*(\d+)\s*秒", intent_text)
                if timeout_match:
                    parameters["timeout_seconds"] = int(timeout_match.group(1))
                missing = [key for key in ("group", "export") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.export.wait",
                    parameters=parameters,
                    confidence=0.99 if not missing else 0.76,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组和导出任务。" if missing else "",
                )
            if "下载" in intent_text and "下载中心" not in intent_text:
                if len(quoted) >= 2:
                    parameters["export"] = quoted[1]
                if len(quoted) >= 3:
                    parameters["output_path"] = quoted[2]
                if re.search(r"覆盖|替换", intent_text):
                    parameters["overwrite"] = True
                missing = [
                    key for key in ("group", "export", "output_path") if key not in parameters
                ]
                return CommandPlan(
                    text,
                    "groups.export.download",
                    parameters=parameters,
                    confidence=0.99 if not missing else 0.73,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组、导出任务和本地保存路径。"
                    if missing
                    else "",
                )
            return CommandPlan(
                text,
                "groups.exports.list",
                parameters=parameters,
                confidence=0.98 if quoted else 0.78,
                missing_fields=[] if quoted else ["group"],
                message="请用书名号提供个人小组。" if not quoted else "",
            )
        if re.search(r"活动图|小组活动", intent_text):
            if re.search(r"图片|图像|banner", intent_text, re.I) and re.search(
                r"上传", intent_text
            ):
                return CommandPlan(
                    text,
                    "groups.activity.image.upload",
                    parameters={"file": quoted[0]} if quoted else {},
                    confidence=0.99 if quoted else 0.78,
                    missing_fields=[] if quoted else ["file"],
                    message="请用书名号提供本地图片路径。" if not quoted else "",
                )
            parameters: dict[str, object] = {"group": quoted[0]} if quoted else {}
            if re.search(r"排序|调整.*顺序|重新排列", intent_text):
                if len(quoted) >= 2:
                    parameters["activities"] = quoted[1:]
                missing = [key for key in ("group", "activities") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.activities.reorder",
                    parameters=parameters,
                    confidence=0.99 if not missing else 0.76,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组和全部已上线活动图的目标顺序。"
                    if missing
                    else "",
                )
            if (
                re.search(r"上线|下线", intent_text)
                and not re.search(r"新建|创建", intent_text)
                and not re.search(r"查看|列出|显示|有哪些|列表|读取", intent_text)
            ):
                if len(quoted) >= 2:
                    parameters["activity"] = quoted[1]
                parameters["online"] = "下线" not in intent_text
                missing = [key for key in ("group", "activity") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.activity.online_status.update",
                    parameters=parameters,
                    confidence=0.99 if not missing else 0.77,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组和活动图。" if missing else "",
                )
            if re.search(r"删除|移除", intent_text):
                if len(quoted) >= 2:
                    parameters["activity"] = quoted[1]
                missing = [key for key in ("group", "activity") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.activity.delete",
                    parameters=parameters,
                    confidence=0.99 if not missing else 0.77,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组和活动图。" if missing else "",
                )
            if re.search(r"新建|创建|添加", intent_text):
                if len(quoted) >= 2:
                    parameters["title"] = quoted[1]
                optional_fields = ("app_link", "pc_link", "app_image_url", "pc_image_url")
                for field, value in zip(optional_fields, quoted[2:], strict=False):
                    parameters[field] = value
                parameters["online"] = bool(
                    re.search(r"上线|在线", intent_text)
                    and not re.search(r"未上线|下线", intent_text)
                )
                missing = [key for key in ("group", "title") if key not in parameters]
                if parameters["online"]:
                    missing.extend(
                        key for key in ("app_image_url", "pc_image_url") if key not in parameters
                    )
                return CommandPlan(
                    text,
                    "groups.activity.create",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.72,
                    missing_fields=missing,
                    message=(
                        "请依次用书名号提供个人小组、标题；上线时再提供移动端链接、"
                        "PC 链接、移动端图片地址和 PC 图片地址。"
                        if missing
                        else ""
                    ),
                )
            if re.search(r"重命名|修改|编辑|更新", intent_text):
                if len(quoted) >= 2:
                    parameters["activity"] = quoted[1]
                if len(quoted) >= 3:
                    parameters["title"] = quoted[2]
                missing = [key for key in ("group", "activity", "title") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.activity.update",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.74,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组、活动图和新标题。" if missing else "",
                )
            status = (
                "offline"
                if re.search(r"未上线|下线", intent_text)
                else "online"
                if re.search(r"已上线|在线", intent_text)
                else "all"
            )
            parameters["status"] = status
            return CommandPlan(
                text,
                "groups.activities.list",
                parameters=parameters,
                confidence=0.98 if quoted else 0.78,
                missing_fields=[] if quoted else ["group"],
                message="请用书名号提供个人小组。" if not quoted else "",
            )
        member_intent = bool(re.search(r"成员|管理员|创建者|所有者|候选人|可添加人员", intent_text))
        if member_intent and "话题" not in intent_text:
            if re.search(r"批量导入|导入模板", intent_text):
                parameters: dict[str, object] = {"group": quoted[0]} if quoted else {}
                if "模板" in intent_text and re.search(r"下载|保存", intent_text):
                    if len(quoted) >= 2:
                        parameters["output_path"] = quoted[1]
                    if re.search(r"覆盖|替换", intent_text):
                        parameters["overwrite"] = True
                    missing = [key for key in ("group", "output_path") if not parameters.get(key)]
                    return CommandPlan(
                        text,
                        "groups.members.bulk_import.template.download",
                        parameters=parameters,
                        confidence=0.99 if not missing else 0.74,
                        missing_fields=missing,
                        message="请依次用书名号提供个人小组和模板保存路径。" if missing else "",
                    )
                if re.search(r"状态|额度|次数|是否|有效期|查看|读取", intent_text):
                    return CommandPlan(
                        text,
                        "groups.members.bulk_import.status",
                        parameters=parameters,
                        confidence=0.99 if quoted else 0.78,
                        missing_fields=[] if quoted else ["group"],
                        message="请用书名号提供个人小组。" if not quoted else "",
                    )
                if len(quoted) >= 2:
                    parameters["file"] = quoted[1]
                missing = [key for key in ("group", "file") if not parameters.get(key)]
                return CommandPlan(
                    text,
                    "groups.members.bulk_import",
                    parameters=parameters,
                    confidence=0.99 if not missing else 0.74,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组和已填写的 XLSX 文件路径。"
                    if missing
                    else "",
                )
            if re.search(r"清除|清理", intent_text) and re.search(
                r"非(?:学习通|超星)|外部成员", intent_text
            ):
                return CommandPlan(
                    text,
                    "groups.members.external.clear",
                    parameters={"group": quoted[0]} if quoted else {},
                    confidence=0.98 if quoted else 0.8,
                    missing_fields=[] if quoted else ["group"],
                    message="请用书名号提供个人小组。" if not quoted else "",
                )
            if re.search(r"转让|移交", intent_text) and re.search(
                r"创建者|所有者|小组", intent_text
            ):
                parameters = {}
                if quoted:
                    parameters["group"] = quoted[0]
                if len(quoted) >= 2:
                    parameters["member"] = quoted[1]
                missing = [key for key in ("group", "member") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.creator.transfer",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.76,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组和新创建者。" if missing else "",
                )
            if "管理员" in intent_text and "权限" in intent_text:
                parameters = {}
                if quoted:
                    parameters["group"] = quoted[0]
                if len(quoted) >= 2:
                    parameters["member"] = quoted[1]
                updating = bool(
                    re.search(r"修改|设置|开启|启用|允许|关闭|禁用|取消|撤销", intent_text)
                )
                if updating:
                    changes = _parse_alias_boolean_changes(
                        text, PERSONAL_GROUP_MANAGER_PERMISSION_ALIASES
                    )
                    if changes:
                        parameters["changes"] = changes
                    missing = [
                        key for key in ("group", "member", "changes") if key not in parameters
                    ]
                    return CommandPlan(
                        text,
                        "groups.member.permissions.update",
                        parameters=parameters,
                        confidence=0.98 if not missing else 0.72,
                        missing_fields=missing,
                        message="请说明个人小组、管理员和要开启或关闭的权限。" if missing else "",
                    )
                missing = [key for key in ("group", "member") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.member.permissions.read",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.76,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组和管理员。" if missing else "",
                )
            if "管理员" in intent_text and re.search(r"设为|设置|指定|取消|撤销|移除", intent_text):
                parameters = {"manager": not bool(re.search(r"取消|撤销|移除", intent_text))}
                if quoted:
                    parameters["group"] = quoted[0]
                if len(quoted) >= 2:
                    parameters["member"] = quoted[1]
                missing = [key for key in ("group", "member") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.member.manager_status.update",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.76,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组和成员。" if missing else "",
                )
            if re.search(r"添加|邀请|加入", intent_text) and not re.search(
                r"来源|候选|可添加", intent_text
            ):
                parameters = {}
                if quoted:
                    parameters["group"] = quoted[0]
                puids = [value for value in quoted[1:] if re.fullmatch(r"\d+", value)]
                if puids:
                    parameters["puids"] = puids
                missing = [key for key in ("group", "puids") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.members.add",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.74,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组和一个或多个成员 PUID。" if missing else "",
                )
            if re.search(r"删除|移除|移出|踢出", intent_text):
                parameters = {}
                if quoted:
                    parameters["group"] = quoted[0]
                if len(quoted) >= 2:
                    parameters["member"] = quoted[1]
                missing = [key for key in ("group", "member") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.member.remove",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.76,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组和成员。" if missing else "",
                )
            if re.search(r"来源|从哪里", intent_text) and not re.search(
                r"候选|搜索|查找", intent_text
            ):
                return CommandPlan(
                    text,
                    "groups.member.sources.list",
                    parameters={"group": quoted[0]} if quoted else {},
                    confidence=0.98 if quoted else 0.8,
                    missing_fields=[] if quoted else ["group"],
                    message="请用书名号提供个人小组。" if not quoted else "",
                )
            if re.search(r"候选|可添加|搜索|查找", intent_text):
                source_type = (
                    "ibuild"
                    if re.search(r"对建|ibuild", intent_text, re.I)
                    else "unit"
                    if "单位" in intent_text
                    else "circle"
                )
                parameters = {"source_type": source_type}
                if quoted:
                    parameters["group"] = quoted[0]
                if len(quoted) >= 2:
                    parameters["source"] = quoted[1]
                if len(quoted) >= 3:
                    parameters["search"] = quoted[2]
                missing = [key for key in ("group", "source") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.member.candidates.list",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.74,
                    missing_fields=missing,
                    message="请依次用书名号提供目标个人小组和来源 ID。" if missing else "",
                )
            if len(quoted) >= 2 and re.search(r"详情|读取|打开|查看", intent_text):
                return CommandPlan(
                    text,
                    "groups.member.read",
                    parameters={"group": quoted[0], "member": quoted[1]},
                    confidence=0.98,
                )
            parameters = {"group": quoted[0]} if quoted else {}
            if len(quoted) >= 2 and re.search(r"搜索|查找|检索", intent_text):
                parameters["search"] = quoted[1]
            return CommandPlan(
                text,
                "groups.members.list",
                parameters=parameters,
                confidence=0.97 if quoted else 0.8,
                missing_fields=[] if quoted else ["group"],
                message="请用书名号提供个人小组。" if not quoted else "",
            )
        if "回收站" in intent_text:
            parameters = {"group": quoted[0]} if quoted else {}
            if re.search(r"清空", intent_text):
                missing = [] if "group" in parameters else ["group"]
                return CommandPlan(
                    text,
                    "groups.recycle.empty",
                    parameters=parameters,
                    confidence=0.99 if not missing else 0.78,
                    missing_fields=missing,
                    message="请用书名号提供个人小组。" if missing else "",
                )
            if re.search(r"还原|恢复", intent_text):
                if len(quoted) >= 2:
                    parameters["items"] = quoted[1:]
                missing = [key for key in ("group", "items") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.recycle.restore",
                    parameters=parameters,
                    confidence=0.99 if not missing else 0.76,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组和回收站项目。" if missing else "",
                )
            if re.search(r"永久|彻底", intent_text) and re.search(r"删除|清除", intent_text):
                if len(quoted) >= 2:
                    parameters["items"] = quoted[1:]
                missing = [key for key in ("group", "items") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.recycle.items.delete",
                    parameters=parameters,
                    confidence=0.99 if not missing else 0.76,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组和回收站项目。" if missing else "",
                )
            return CommandPlan(
                text,
                "groups.recycle.list",
                parameters=parameters,
                confidence=0.98 if quoted else 0.78,
                missing_fields=[] if quoted else ["group"],
                message="请用书名号提供个人小组。" if not quoted else "",
            )
        if "删除原因" in intent_text:
            parameters = {"group": quoted[0]} if quoted else {}
            reason_intent = intent_text.replace("删除原因", "原因")
            if re.search(r"重命名|修改|编辑|改为|更名", reason_intent):
                if len(quoted) >= 2:
                    parameters["reason"] = quoted[1]
                if len(quoted) >= 3:
                    parameters["name"] = quoted[2]
                missing = [key for key in ("group", "reason", "name") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.deletion_reason.rename",
                    parameters=parameters,
                    confidence=0.99 if not missing else 0.74,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组、原删除原因和新名称。" if missing else "",
                )
            if re.search(r"新建|创建|添加", reason_intent):
                if len(quoted) >= 2:
                    parameters["name"] = quoted[1]
                missing = [key for key in ("group", "name") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.deletion_reason.create",
                    parameters=parameters,
                    confidence=0.99 if not missing else 0.76,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组和删除原因。" if missing else "",
                )
            if re.search(r"删除|移除", reason_intent):
                if len(quoted) >= 2:
                    parameters["reasons"] = quoted[1:]
                missing = [key for key in ("group", "reasons") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.deletion_reasons.delete",
                    parameters=parameters,
                    confidence=0.99 if not missing else 0.76,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组和删除原因。" if missing else "",
                )
            return CommandPlan(
                text,
                "groups.deletion_reasons.list",
                parameters=parameters,
                confidence=0.98 if quoted else 0.78,
                missing_fields=[] if quoted else ["group"],
                message="请用书名号提供个人小组。" if not quoted else "",
            )
        if "标签" in intent_text:
            parameters = {"group": quoted[0]} if quoted else {}
            if re.search(r"排序|调整.*顺序|重新排列", intent_text):
                if len(quoted) >= 2:
                    parameters["labels"] = quoted[1:]
                missing = [key for key in ("group", "labels") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.labels.reorder",
                    parameters=parameters,
                    confidence=0.99 if not missing else 0.76,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组和全部标签的目标顺序。" if missing else "",
                )
            if re.search(r"重命名|修改|编辑", intent_text):
                if len(quoted) >= 2:
                    parameters["label"] = quoted[1]
                if len(quoted) >= 3:
                    parameters["name"] = quoted[2]
                missing = [key for key in ("group", "label", "name") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.label.rename",
                    parameters=parameters,
                    confidence=0.99 if not missing else 0.74,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组、原标签和新名称。" if missing else "",
                )
            if re.search(r"新建|创建|添加", intent_text):
                if len(quoted) >= 2:
                    parameters["name"] = quoted[1]
                missing = [key for key in ("group", "name") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.label.create",
                    parameters=parameters,
                    confidence=0.99 if not missing else 0.76,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组和标签名。" if missing else "",
                )
            if re.search(r"删除|移除", intent_text):
                if len(quoted) >= 2:
                    parameters["labels"] = quoted[1:]
                missing = [key for key in ("group", "labels") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.labels.delete",
                    parameters=parameters,
                    confidence=0.99 if not missing else 0.76,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组和标签。" if missing else "",
                )
            return CommandPlan(
                text,
                "groups.labels.list",
                parameters=parameters,
                confidence=0.98 if quoted else 0.78,
                missing_fields=[] if quoted else ["group"],
                message="请用书名号提供个人小组。" if not quoted else "",
            )
        if re.search(r"通知|公告", intent_text) and re.search(r"发送|发布", intent_text):
            parameters = {}
            if quoted:
                parameters["group"] = quoted[0]
            if len(quoted) >= 2:
                parameters["title"] = quoted[1]
            if len(quoted) >= 3:
                parameters["content"] = quoted[2]
            if len(quoted) >= 4:
                parameters["pcode"] = quoted[3]
            missing = [key for key in ("group", "title", "content") if key not in parameters]
            return CommandPlan(
                text,
                "groups.notice.send",
                parameters=parameters,
                confidence=0.99 if not missing else 0.74,
                missing_fields=missing,
                message="请依次用书名号提供个人小组、通知标题和正文。" if missing else "",
            )
        if "发言规则" in intent_text or any(
            alias in text
            for aliases in PERSONAL_GROUP_SPEAKING_RULE_ALIASES.values()
            for alias in aliases
        ):
            changes = _parse_personal_group_speaking_rule_changes(text)
            parameters: dict[str, object] = {}
            if quoted:
                parameters["group"] = quoted[0]
            if changes:
                parameters["changes"] = changes
            missing = [key for key in ("group", "changes") if key not in parameters]
            return CommandPlan(
                text,
                "groups.speaking_rules.update",
                parameters=parameters,
                confidence=0.98 if not missing else 0.72,
                missing_fields=missing,
                message="请说明个人小组以及要修改的发言规则和整数值。" if missing else "",
            )
        setting_changes = _parse_alias_boolean_changes(text, PERSONAL_GROUP_SETTING_ALIASES)
        if setting_changes:
            parameters = {"changes": setting_changes}
            if quoted:
                parameters["group"] = quoted[0]
            missing = [] if "group" in parameters else ["group"]
            return CommandPlan(
                text,
                "groups.settings.update",
                parameters=parameters,
                confidence=0.98 if not missing else 0.76,
                missing_fields=missing,
                message="请用书名号提供个人小组。" if missing else "",
            )
        if "话题" in intent_text:
            if "草稿" in intent_text:
                if re.search(r"发布|发表", intent_text):
                    parameters = {}
                    if quoted:
                        parameters["group"] = quoted[0]
                    if len(quoted) >= 2:
                        parameters["draft"] = quoted[1]
                    missing = [key for key in ("group", "draft") if key not in parameters]
                    return CommandPlan(
                        text,
                        "groups.topic.draft.publish",
                        parameters=parameters,
                        confidence=0.98 if not missing else 0.76,
                        missing_fields=missing,
                        message="请依次用书名号提供个人小组和话题草稿。" if missing else "",
                    )
                if re.search(r"新建|创建|保存|修改|编辑|更新", intent_text):
                    updating = bool(re.search(r"修改|编辑|更新", intent_text))
                    parameters = {}
                    if quoted:
                        parameters["group"] = quoted[0]
                    if updating and len(quoted) >= 2:
                        parameters["draft"] = quoted[1]
                    value_offset = 2 if updating else 1
                    if len(quoted) > value_offset:
                        parameters["title"] = quoted[value_offset]
                    if len(quoted) > value_offset + 1:
                        parameters["content"] = quoted[value_offset + 1]
                    missing = [
                        key for key in ("group", "title", "content") if key not in parameters
                    ]
                    if updating and "draft" not in parameters:
                        missing.append("draft")
                    return CommandPlan(
                        text,
                        "groups.topic.draft.save",
                        parameters=parameters,
                        confidence=0.98 if not missing else 0.73,
                        missing_fields=missing,
                        message=(
                            "请依次用书名号提供个人小组、草稿（修改时）、标题和正文。"
                            if missing
                            else ""
                        ),
                    )
                if re.search(r"搜索|查找|检索", intent_text):
                    parameters = {}
                    if quoted:
                        parameters["group"] = quoted[0]
                    if len(quoted) >= 2:
                        parameters["search"] = quoted[1]
                    return CommandPlan(
                        text,
                        "groups.topic.drafts.list",
                        parameters=parameters,
                        confidence=0.98 if quoted else 0.8,
                        missing_fields=[] if quoted else ["group"],
                        message="请用书名号提供个人小组。" if not quoted else "",
                    )
                if len(quoted) >= 2 and re.search(r"详情|读取|打开|查看", intent_text):
                    return CommandPlan(
                        text,
                        "groups.topic.draft.read",
                        parameters={"group": quoted[0], "draft": quoted[1]},
                        confidence=0.98,
                    )
                return CommandPlan(
                    text,
                    "groups.topic.drafts.list",
                    parameters={"group": quoted[0]} if quoted else {},
                    confidence=0.97 if quoted else 0.8,
                    missing_fields=[] if quoted else ["group"],
                    message="请用书名号提供个人小组。" if not quoted else "",
                )
            batch_topic_folder_operation = bool(
                "文件夹" in intent_text
                and "批量" in intent_text
                and (
                    re.search(r"删除|移除", intent_text)
                    or (
                        "移动" in intent_text
                        and intent_text.find("文件夹") < intent_text.find("移动")
                    )
                )
            )
            if batch_topic_folder_operation:
                if re.search(r"删除|移除", intent_text):
                    parameters = {}
                    if quoted:
                        parameters["group"] = quoted[0]
                    if len(quoted) >= 2:
                        parameters["folders"] = quoted[1:]
                    missing = [key for key in ("group", "folders") if key not in parameters]
                    return CommandPlan(
                        text,
                        "groups.topic.folders.delete",
                        parameters=parameters,
                        confidence=0.98 if not missing else 0.75,
                        missing_fields=missing,
                        message="请依次用书名号提供个人小组和一个或多个话题文件夹。"
                        if missing
                        else "",
                    )
                if re.search(r"移动", intent_text):
                    parameters = {}
                    if quoted:
                        parameters["group"] = quoted[0]
                    if "根目录" in intent_text:
                        if len(quoted) >= 2:
                            parameters["folders"] = quoted[1:]
                        parameters["destination_folder"] = "root"
                    elif len(quoted) >= 3:
                        parameters["folders"] = quoted[1:-1]
                        parameters["destination_folder"] = quoted[-1]
                    missing = [
                        key
                        for key in ("group", "folders", "destination_folder")
                        if key not in parameters
                    ]
                    return CommandPlan(
                        text,
                        "groups.topic.folders.move",
                        parameters=parameters,
                        confidence=0.98 if not missing else 0.74,
                        missing_fields=missing,
                        message="请说明个人小组、一个或多个话题文件夹和目标目录。"
                        if missing
                        else "",
                    )
            if re.search(r"加精|精华", intent_text):
                parameters = {"choice": not bool(re.search(r"取消|撤销", intent_text))}
                if quoted:
                    parameters["group"] = quoted[0]
                if len(quoted) >= 2:
                    parameters["topic"] = quoted[1]
                missing = [key for key in ("group", "topic") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.topic.choice_status.update",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.76,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组和话题。" if missing else "",
                )
            if re.search(r"点赞|赞", intent_text):
                parameters = {"praised": not bool(re.search(r"取消|撤销", intent_text))}
                if quoted:
                    parameters["group"] = quoted[0]
                if len(quoted) >= 2:
                    parameters["topic"] = quoted[1]
                missing = [key for key in ("group", "topic") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.topic.praise_status.update",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.76,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组和话题。" if missing else "",
                )
            if re.search(r"评分|打分", intent_text):
                parameters = {}
                if quoted:
                    parameters["group"] = quoted[0]
                if len(quoted) >= 2:
                    parameters["topics"] = quoted[1:]
                score_match = re.search(
                    r"(?:评分|打分)(?:设为|设置为|为)?\s*(-?\d+)|(-?\d+)\s*分",
                    intent_text,
                )
                if score_match:
                    parameters["score"] = int(score_match.group(1) or score_match.group(2))
                missing = [key for key in ("group", "topics", "score") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.topics.score.set",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.73,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组、一个或多个话题，并说明分数。"
                    if missing
                    else "",
                )
            if "批量" in intent_text and re.search(r"移动", intent_text):
                parameters = {}
                if quoted:
                    parameters["group"] = quoted[0]
                if "根目录" in intent_text:
                    if len(quoted) >= 2:
                        parameters["topics"] = quoted[1:]
                    parameters["destination_folder"] = "root"
                elif len(quoted) >= 3:
                    parameters["topics"] = quoted[1:-1]
                    parameters["destination_folder"] = quoted[-1]
                missing = [
                    key
                    for key in ("group", "topics", "destination_folder")
                    if key not in parameters
                ]
                return CommandPlan(
                    text,
                    "groups.topics.move",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.74,
                    missing_fields=missing,
                    message="请说明个人小组、一个或多个话题和目标话题文件夹。" if missing else "",
                )
            if "批量" in intent_text and re.search(r"删除|移除", intent_text):
                parameters = {}
                if quoted:
                    parameters["group"] = quoted[0]
                if len(quoted) >= 2:
                    parameters["topics"] = quoted[1:]
                missing = [key for key in ("group", "topics") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.topics.delete",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.75,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组和一个或多个话题。" if missing else "",
                )
            moving_topic_to_folder = bool(re.search(r"话题.*移动到(?:话题)?文件夹", intent_text))
            if "文件夹" in intent_text and not moving_topic_to_folder:
                if re.search(r"文件夹树|完整层级|目录树", intent_text):
                    return CommandPlan(
                        text,
                        "groups.topic.folders.tree",
                        parameters={"group": quoted[0]} if quoted else {},
                        confidence=0.98 if quoted else 0.8,
                        missing_fields=[] if quoted else ["group"],
                        message="请用书名号提供个人小组名称。" if not quoted else "",
                    )
                if re.search(r"删除|移除", intent_text):
                    parameters = {}
                    if quoted:
                        parameters["group"] = quoted[0]
                    if len(quoted) >= 2:
                        parameters["folder"] = quoted[1]
                    missing = [key for key in ("group", "folder") if key not in parameters]
                    return CommandPlan(
                        text,
                        "groups.topic.folder.delete",
                        parameters=parameters,
                        confidence=0.98 if not missing else 0.76,
                        missing_fields=missing,
                        message="请依次用书名号提供个人小组和话题文件夹。" if missing else "",
                    )
                if re.search(r"重命名|改名", intent_text):
                    parameters = {}
                    for key, index in (("group", 0), ("folder", 1), ("name", 2)):
                        if len(quoted) > index:
                            parameters[key] = quoted[index]
                    missing = [key for key in ("group", "folder", "name") if key not in parameters]
                    return CommandPlan(
                        text,
                        "groups.topic.folder.rename",
                        parameters=parameters,
                        confidence=0.98 if not missing else 0.75,
                        missing_fields=missing,
                        message="请依次用书名号提供个人小组、话题文件夹和新名称。"
                        if missing
                        else "",
                    )
                if re.search(r"移动", intent_text):
                    parameters = {}
                    if quoted:
                        parameters["group"] = quoted[0]
                    if len(quoted) >= 2:
                        parameters["folder"] = quoted[1]
                    if len(quoted) >= 3:
                        parameters["destination_folder"] = quoted[2]
                    elif "根目录" in intent_text:
                        parameters["destination_folder"] = "root"
                    missing = [
                        key
                        for key in ("group", "folder", "destination_folder")
                        if key not in parameters
                    ]
                    return CommandPlan(
                        text,
                        "groups.topic.folder.move",
                        parameters=parameters,
                        confidence=0.98 if not missing else 0.75,
                        missing_fields=missing,
                        message="请说明个人小组、话题文件夹和目标目录。" if missing else "",
                    )
                if re.search(r"新建|创建|添加", intent_text):
                    parameters = {}
                    if quoted:
                        parameters["group"] = quoted[0]
                    if len(quoted) >= 2:
                        parameters["name"] = quoted[-1]
                    if len(quoted) >= 3:
                        parameters["parent_folder"] = quoted[1]
                    missing = [key for key in ("group", "name") if key not in parameters]
                    return CommandPlan(
                        text,
                        "groups.topic.folder.create",
                        parameters=parameters,
                        confidence=0.98 if not missing else 0.76,
                        missing_fields=missing,
                        message="请用书名号提供个人小组和新话题文件夹名称。" if missing else "",
                    )
            if "删除" in intent_text and re.search(r"回复|评论", intent_text):
                parameters = {}
                for key, index in (("group", 0), ("topic", 1), ("reply", 2)):
                    if len(quoted) > index:
                        parameters[key] = quoted[index]
                missing = [key for key in ("group", "topic", "reply") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.topic.reply.delete",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.75,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组、话题和回复。" if missing else "",
                )
            if re.search(r"修改|编辑", intent_text) and re.search(r"回复|评论", intent_text):
                parameters = {}
                for key, index in (("group", 0), ("topic", 1), ("reply", 2), ("content", 3)):
                    if len(quoted) > index:
                        parameters[key] = quoted[index]
                missing = [
                    key for key in ("group", "topic", "reply", "content") if key not in parameters
                ]
                return CommandPlan(
                    text,
                    "groups.topic.reply.update",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.74,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组、话题、原回复和新正文。" if missing else "",
                )
            reply_creation = bool(
                re.search(r"发布|发送|新增|添加", intent_text)
                or re.search(r"^(?:请)?(?:匿名)?回复", intent_text)
            )
            if re.search(r"回复|评论", intent_text) and reply_creation:
                parameters = {}
                if quoted:
                    parameters["group"] = quoted[0]
                if len(quoted) >= 2:
                    parameters["topic"] = quoted[1]
                if len(quoted) >= 3:
                    parameters["content"] = quoted[-1]
                if len(quoted) >= 4:
                    parameters["reply_to"] = quoted[2]
                if "匿名" in intent_text:
                    parameters["anonymous"] = True
                missing = [key for key in ("group", "topic", "content") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.topic.reply.create",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.75,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组、话题和回复正文。" if missing else "",
                )
            if re.search(r"置顶|取消置顶", intent_text):
                parameters = {"top": "取消置顶" not in intent_text}
                if quoted:
                    parameters["group"] = quoted[0]
                if len(quoted) >= 2:
                    parameters["topic"] = quoted[1]
                missing = [key for key in ("group", "topic") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.topic.top_status.update",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.76,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组和话题。" if missing else "",
                )
            if re.search(r"移动", intent_text):
                parameters = {}
                if quoted:
                    parameters["group"] = quoted[0]
                if len(quoted) >= 2:
                    parameters["topic"] = quoted[1]
                if len(quoted) >= 3:
                    parameters["destination_folder"] = quoted[2]
                elif "根目录" in intent_text:
                    parameters["destination_folder"] = "root"
                missing = [
                    key for key in ("group", "topic", "destination_folder") if key not in parameters
                ]
                return CommandPlan(
                    text,
                    "groups.topic.move",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.75,
                    missing_fields=missing,
                    message="请说明个人小组、话题和目标话题文件夹。" if missing else "",
                )
            if "删除" in intent_text:
                parameters = {}
                if quoted:
                    parameters["group"] = quoted[0]
                if len(quoted) >= 2:
                    parameters["topic"] = quoted[1]
                missing = [key for key in ("group", "topic") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.topic.delete",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.76,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组和话题。" if missing else "",
                )
            if re.search(r"发布|新建|发起|创建", intent_text):
                parameters = {}
                if quoted:
                    parameters["group"] = quoted[0]
                if len(quoted) >= 2:
                    parameters["title"] = quoted[1]
                if len(quoted) >= 3:
                    parameters["content"] = quoted[2]
                if "匿名" in intent_text:
                    parameters["anonymous"] = True
                missing = [key for key in ("group", "title", "content") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.topic.create",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.75,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组、话题标题和正文。" if missing else "",
                )
            if re.search(r"修改|编辑|重命名|改名", intent_text):
                parameters = {}
                if quoted:
                    parameters["group"] = quoted[0]
                if len(quoted) >= 2:
                    parameters["topic"] = quoted[1]
                if len(quoted) >= 3:
                    key = "content" if re.search(r"正文|内容", intent_text) else "title"
                    parameters[key] = quoted[2]
                missing = [key for key in ("group", "topic") if key not in parameters]
                if "title" not in parameters and "content" not in parameters:
                    missing.append("title_or_content")
                return CommandPlan(
                    text,
                    "groups.topic.update",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.74,
                    missing_fields=missing,
                    message="请依次用书名号提供个人小组、原话题和新标题或正文。" if missing else "",
                )
            if len(quoted) >= 2 and re.search(r"详情|回复|正文|读取|打开|查看", intent_text):
                return CommandPlan(
                    text,
                    "groups.topic.read",
                    parameters={"group": quoted[0], "topic": quoted[1]},
                    confidence=0.98,
                )
            parameters = {}
            if quoted:
                parameters["group"] = quoted[0]
            if len(quoted) >= 2 and re.search(r"搜索|查找|检索", intent_text):
                parameters["search"] = quoted[1]
            return CommandPlan(
                text,
                "groups.topics.list",
                parameters=parameters,
                confidence=0.97 if quoted else 0.8,
                missing_fields=[] if quoted else ["group"],
                message="请用书名号提供个人小组名称。" if not quoted else "",
            )
        if "文件夹" in text:
            if re.search(r"文件夹树|完整层级|目录树", text):
                return CommandPlan(text, "groups.folders.tree", confidence=0.98)
            if re.search(r"删除|移除", text):
                return CommandPlan(
                    text,
                    "groups.folder.delete",
                    parameters={"folder": quoted[0]} if quoted else {},
                    confidence=0.98 if quoted else 0.8,
                    missing_fields=[] if quoted else ["folder"],
                    message="请用书名号提供要删除的小组文件夹。" if not quoted else "",
                )
            if re.search(r"重命名|改名", text):
                parameters = {}
                if quoted:
                    parameters["folder"] = quoted[0]
                if len(quoted) >= 2:
                    parameters["name"] = quoted[1]
                missing = [key for key in ("folder", "name") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.folder.rename",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.78,
                    missing_fields=missing,
                    message="请依次用书名号提供小组文件夹和新名称。" if missing else "",
                )
            if re.search(r"置顶|取消置顶", text):
                return CommandPlan(
                    text,
                    "groups.folder.top_status.update",
                    parameters={
                        **({"folder": quoted[0]} if quoted else {}),
                        "top": "取消置顶" not in text,
                    },
                    confidence=0.98 if quoted else 0.8,
                    missing_fields=[] if quoted else ["folder"],
                    message="请用书名号提供小组文件夹。" if not quoted else "",
                )
            if re.search(r"移动", text):
                parameters = {}
                if quoted:
                    parameters["folder"] = quoted[0]
                if len(quoted) >= 2:
                    parameters["destination_folder"] = quoted[1]
                elif re.search(r"根目录", text):
                    parameters["destination_folder"] = "root"
                missing = [key for key in ("folder", "destination_folder") if key not in parameters]
                return CommandPlan(
                    text,
                    "groups.folder.move",
                    parameters=parameters,
                    confidence=0.97 if not missing else 0.76,
                    missing_fields=missing,
                    message="请说明小组文件夹和目标父目录。" if missing else "",
                )
            if re.search(r"新建|创建|添加", text):
                parameters = {"name": quoted[0]} if quoted else {}
                if len(quoted) >= 2:
                    parameters["parent_folder"] = quoted[1]
                return CommandPlan(
                    text,
                    "groups.folder.create",
                    parameters=parameters,
                    confidence=0.98 if quoted else 0.8,
                    missing_fields=[] if quoted else ["name"],
                    message="请用书名号提供新小组文件夹名称。" if not quoted else "",
                )
            parameters = {}
            if quoted:
                parameters["parent_folder"] = quoted[0]
            if re.search(r"搜索|查找", text) and quoted:
                parameters = {"search": quoted[-1]}
            return CommandPlan(
                text,
                "groups.folders.list",
                parameters=parameters,
                confidence=0.97,
            )
        if re.search(r"解散", text):
            return CommandPlan(
                text,
                "groups.dismiss",
                parameters={"group": quoted[0]} if quoted else {},
                confidence=0.98 if quoted else 0.8,
                missing_fields=[] if quoted else ["group"],
                message="请用书名号提供要解散的小组。" if not quoted else "",
            )
        if re.search(r"退出", text):
            return CommandPlan(
                text,
                "groups.quit",
                parameters={"group": quoted[0]} if quoted else {},
                confidence=0.98 if quoted else 0.8,
                missing_fields=[] if quoted else ["group"],
                message="请用书名号提供要退出的小组。" if not quoted else "",
            )
        if re.search(r"置顶|取消置顶", text):
            return CommandPlan(
                text,
                "groups.top_status.update",
                parameters={
                    **({"group": quoted[0]} if quoted else {}),
                    "top": "取消置顶" not in text,
                },
                confidence=0.98 if quoted else 0.8,
                missing_fields=[] if quoted else ["group"],
                message="请用书名号提供小组。" if not quoted else "",
            )
        if re.search(r"移动", text):
            parameters = {}
            if quoted:
                parameters["group"] = quoted[0]
            if len(quoted) >= 2:
                parameters["destination_folder"] = quoted[1]
            elif re.search(r"根目录", text):
                parameters["destination_folder"] = "root"
            missing = [key for key in ("group", "destination_folder") if key not in parameters]
            return CommandPlan(
                text,
                "groups.move",
                parameters=parameters,
                confidence=0.97 if not missing else 0.76,
                missing_fields=missing,
                message="请说明小组和目标小组文件夹。" if missing else "",
            )
        if re.search(r"新建|创建", text):
            parameters = {}
            if quoted:
                parameters["name"] = quoted[0]
            if len(quoted) >= 2:
                parameters["description"] = quoted[1]
            return CommandPlan(
                text,
                "groups.create",
                parameters=parameters,
                confidence=0.97 if quoted else 0.78,
                missing_fields=[] if quoted else ["name"],
                message="请用书名号提供新小组名称。" if not quoted else "",
            )
        if re.search(r"重命名|改名|修改.*简介|编辑.*简介", text):
            parameters = {}
            if quoted:
                parameters["group"] = quoted[0]
            if len(quoted) >= 2:
                if re.search(r"简介", text):
                    parameters["description"] = quoted[1]
                else:
                    parameters["name"] = quoted[1]
            missing = ["group"] if "group" not in parameters else []
            if "name" not in parameters and "description" not in parameters:
                missing.append("name_or_description")
            return CommandPlan(
                text,
                "groups.update",
                parameters=parameters,
                confidence=0.97 if not missing else 0.76,
                missing_fields=missing,
                message="请用书名号提供小组和新的名称或简介。" if missing else "",
            )
        if quoted and re.search(r"详情|设置|读取|打开|查看", text):
            return CommandPlan(
                text,
                "groups.read",
                parameters={"group": quoted[0]},
                confidence=0.97,
            )
        parameters = {"search": quoted[-1]} if quoted and re.search(r"搜索|查找", text) else {}
        return CommandPlan(text, "groups.list", parameters=parameters, confidence=0.97)

    for alias, module in sorted(
        SPACE_MODULE_ALIASES.items(), key=lambda item: len(item[0]), reverse=True
    ):
        if alias in {"云盘", "笔记"}:
            continue
        if alias in text and re.search(r"打开|进入|读取|查看", text):
            return CommandPlan(
                text,
                "space.module.open",
                parameters={"module": module},
                confidence=0.96,
            )

    learning_context = bool(re.search(r"我学的课|我学的课程|我学课程|学生课程", text))
    if learning_context:
        quoted = _extract_quoted(text)
        integrity_intent = bool(re.search(r"诚信.*承诺|在线学习.*承诺|承诺书", text))
        if integrity_intent and re.search(r"签署|接受|同意|确认签署", text):
            parameters = {"course": quoted[0]} if quoted else {}
            return CommandPlan(
                text,
                "learning.course.integrity.accept",
                parameters=parameters,
                confidence=0.98 if quoted else 0.72,
                missing_fields=[] if quoted else ["course"],
                message="请用书名号提供要签署在线学习诚信承诺书的课程。" if not quoted else "",
            )
        if integrity_intent:
            parameters = {"course": quoted[0]} if quoted else {}
            return CommandPlan(
                text,
                "learning.course.integrity.read",
                parameters=parameters,
                confidence=0.98 if quoted else 0.72,
                missing_fields=[] if quoted else ["course"],
                message="请用书名号提供要查看诚信承诺状态的课程。" if not quoted else "",
            )
        if re.search(r"模块|入口|功能", text):
            parameters = {"course": quoted[0]} if quoted else {}
            return CommandPlan(
                text,
                "learning.course.modules.discover",
                parameters=parameters,
                confidence=0.98 if quoted else 0.72,
                missing_fields=[] if quoted else ["course"],
                message="请用书名号提供要查看学生侧功能入口的课程。" if not quoted else "",
            )
        if re.search(r"课程图谱|知识图谱|学习地图|图谱", text):
            parameters: dict[str, object] = {"course": quoted[0]} if quoted else {}
            operand = quoted[1] if len(quoted) > 1 else ""
            if "模型" in text and re.search(r"读取|查看|打开", text) and operand:
                parameters["model"] = operand
                return CommandPlan(
                    text,
                    "learning.course.knowledge_graph.model.read",
                    parameters=parameters,
                    confidence=0.98,
                )
            if "模型" in text or re.search(r"图谱(视图|类型)", text):
                if operand and re.search(r"搜索|查找", text):
                    parameters["search"] = operand
                return CommandPlan(
                    text,
                    "learning.course.knowledge_graph.models.list",
                    parameters=parameters,
                    confidence=0.98 if quoted else 0.72,
                    missing_fields=[] if quoted else ["course"],
                    message="请用书名号提供要查看图谱模型的课程。" if not quoted else "",
                )
            if re.search(r"节点|知识点", text):
                if operand:
                    parameters["node"] = operand
                missing = ([] if quoted else ["course"]) + ([] if operand else ["node"])
                return CommandPlan(
                    text,
                    "learning.course.knowledge_graph.node.read",
                    parameters=parameters,
                    confidence=0.98 if not missing else 0.72,
                    missing_fields=missing,
                    message="请依次用书名号提供课程和图谱节点。" if missing else "",
                )
            if operand and re.search(r"搜索|查找", text):
                parameters["search"] = operand
            level_match = re.search(r"(?:第\s*)?(\d+)\s*层", text)
            if level_match:
                parameters["level"] = int(level_match.group(1))
            return CommandPlan(
                text,
                "learning.course.knowledge_graph.list",
                parameters=parameters,
                confidence=0.98 if quoted else 0.72,
                missing_fields=[] if quoted else ["course"],
                message="请用书名号提供要查看课程图谱的课程。" if not quoted else "",
            )
        if "学习记录" in text or re.search(r"学习(进度|统计)", text):
            parameters = {"course": quoted[0]} if quoted else {}
            return CommandPlan(
                text,
                "learning.course.records.read",
                parameters=parameters,
                confidence=0.98 if quoted else 0.72,
                missing_fields=[] if quoted else ["course"],
                message="请用书名号提供要读取学习记录的课程。" if not quoted else "",
            )
        if "错题" in text:
            parameters = {"course": quoted[0]} if quoted else {}
            return CommandPlan(
                text,
                "learning.course.wrong_questions.summary",
                parameters=parameters,
                confidence=0.98 if quoted else 0.72,
                missing_fields=[] if quoted else ["course"],
                message="请用书名号提供要查看错题概况的课程。" if not quoted else "",
            )
        if re.search(r"AI\s*(助教|工具|智能体)|资料助手", text, flags=re.I):
            parameters = {"course": quoted[0]} if quoted else {}
            return CommandPlan(
                text,
                "learning.course.ai_tools.list",
                parameters=parameters,
                confidence=0.98 if quoted else 0.72,
                missing_fields=[] if quoted else ["course"],
                message="请用书名号提供要查看 AI 工具的课程。" if not quoted else "",
            )
        if "作业" in text and re.search(r"暂存|保存(?:作业)?草稿", text):
            parameters: dict[str, object] = {}
            operands = list(quoted)
            if operands:
                parameters["course"] = operands.pop(0)
            if operands and operands[0] == "作业":
                operands.pop(0)
            if operands:
                parameters["homework"] = operands.pop(0)
            question_match = re.search(r"第\s*(\d+)\s*题", text)
            if question_match:
                question = question_match.group(1)
                if operands:
                    parameters["updates"] = [{"question": question, "answer": operands[-1]}]
            missing = [key for key in ("course", "homework") if key not in parameters]
            if not question_match:
                missing.append("question")
            if "updates" not in parameters:
                missing.append("answer")
            return CommandPlan(
                text,
                "learning.course.homework.answers.save",
                parameters=parameters,
                confidence=0.98 if not missing else 0.72,
                missing_fields=missing,
                message=("请依次用书名号提供课程、作业和答案，并写明第几题。" if missing else ""),
            )
        if (
            "作业" in text
            and re.search(r"(?<!已)提交|交卷|正式交作业|交作业", text)
            and not re.search(r"查看|读取|列出|显示|已提交|提交记录", text)
        ):
            parameters: dict[str, object] = {}
            operands = list(quoted)
            if operands:
                parameters["course"] = operands.pop(0)
            if operands and operands[0] == "作业":
                operands.pop(0)
            if operands:
                parameters["homework"] = operands[0]
            missing = [key for key in ("course", "homework") if key not in parameters]
            return CommandPlan(
                text,
                "learning.course.homework.submit",
                parameters=parameters,
                confidence=0.98 if not missing else 0.72,
                missing_fields=missing,
                message="请依次用书名号提供课程和要提交的作业。" if missing else "",
            )
        if "作业" in text and re.search(r"重做|重新作答|再次作答", text):
            parameters: dict[str, object] = {}
            if quoted:
                parameters["course"] = quoted[0]
            operands = quoted[1:]
            if operands and operands[0] == "作业":
                operands = operands[1:]
            if operands:
                parameters["homework"] = operands[0]
            missing = [key for key in ("course", "homework") if key not in parameters]
            return CommandPlan(
                text,
                "learning.course.homework.redo",
                parameters=parameters,
                confidence=0.98 if not missing else 0.72,
                missing_fields=missing,
                message="请依次用书名号提供课程和要重做的作业。" if missing else "",
            )
        if "作业" in text and re.search(
            r"(?:进入|开始|继续|修改).{0,10}(?:作答|答题)|(?:开始|继续)作业",
            text,
        ):
            parameters: dict[str, object] = {}
            if quoted:
                parameters["course"] = quoted[0]
            operands = quoted[1:]
            if operands and operands[0] == "作业":
                operands = operands[1:]
            if operands:
                parameters["homework"] = operands[0]
            missing = [key for key in ("course", "homework") if key not in parameters]
            return CommandPlan(
                text,
                "learning.course.homework.answer.enter",
                parameters=parameters,
                confidence=0.98 if not missing else 0.72,
                missing_fields=missing,
                message="请依次用书名号提供课程和要进入答题的作业。" if missing else "",
            )
        if "作业" in text and re.search(
            r"作答记录|答题记录|作答历史|答题历史|历史答案|历次作答",
            text,
        ):
            parameters: dict[str, object] = {}
            if quoted:
                parameters["course"] = quoted[0]
            operands = quoted[1:]
            if operands and operands[0] == "作业":
                operands = operands[1:]
            homework = operands[0] if operands else ""
            if homework:
                parameters["homework"] = homework
            attempt = operands[1] if len(operands) > 1 else ""
            attempt_match = re.search(r"第\s*(\d+)\s*次(?:作答|答题)", text)
            if attempt_match:
                attempt = attempt_match.group(1)
            if attempt:
                parameters["attempt"] = attempt
            required = ("course", "homework", "attempt") if attempt else ("course", "homework")
            missing = [key for key in required if key not in parameters]
            action = (
                "learning.course.homework.attempt.read"
                if attempt
                else "learning.course.homework.attempts.list"
            )
            return CommandPlan(
                text,
                action,
                parameters=parameters,
                confidence=0.98 if not missing else 0.72,
                missing_fields=missing,
                message=(
                    "请依次用书名号提供课程和作业；读取某次记录时再提供次数。" if missing else ""
                ),
            )
        if "作业" in text and re.search(r"详情|题目|题干|我的答案|当前答案", text):
            parameters: dict[str, object] = {}
            if quoted:
                parameters["course"] = quoted[0]
            homework = quoted[1] if len(quoted) > 1 else ""
            if homework == "作业" and len(quoted) > 2:
                homework = quoted[2]
            if homework:
                parameters["homework"] = homework
            missing = [key for key in ("course", "homework") if key not in parameters]
            return CommandPlan(
                text,
                "learning.course.homework.read",
                parameters=parameters,
                confidence=0.98 if not missing else 0.72,
                missing_fields=missing,
                message="请依次用书名号提供课程和作业。" if missing else "",
            )
        if "讨论" in text and re.search(r"删除.*(?:回复|评论)|(?:回复|评论).*删除", text):
            parameters: dict[str, object] = {}
            operands = list(quoted)
            if operands:
                parameters["course"] = operands.pop(0)
            if operands and operands[0] == "讨论":
                operands.pop(0)
            for key, value in zip(("topic", "reply"), operands, strict=False):
                parameters[key] = value
            missing = [key for key in ("course", "topic", "reply") if key not in parameters]
            return CommandPlan(
                text,
                "learning.course.discussions.reply.delete",
                parameters=parameters,
                confidence=0.98 if not missing else 0.72,
                missing_fields=missing,
                message="请依次用书名号提供课程、讨论和回复。" if missing else "",
            )
        if "讨论" in text and re.search(
            r"(?:编辑|修改).*?(?:回复|评论)|(?:回复|评论).*?(?:编辑|修改)", text
        ):
            parameters = {}
            operands = list(quoted)
            if operands:
                parameters["course"] = operands.pop(0)
            if operands and operands[0] == "讨论":
                operands.pop(0)
            for key, value in zip(("topic", "reply", "content"), operands, strict=False):
                parameters[key] = value
            missing = [
                key for key in ("course", "topic", "reply", "content") if key not in parameters
            ]
            return CommandPlan(
                text,
                "learning.course.discussions.reply.update",
                parameters=parameters,
                confidence=0.98 if not missing else 0.72,
                missing_fields=missing,
                message="请依次用书名号提供课程、讨论、原回复和新正文。" if missing else "",
            )
        if (
            "讨论" in text
            and "回复" in text
            and not re.search(r"查看|读取|显示|浏览|删除|编辑|修改", text)
        ):
            parameters = {}
            operands = list(quoted)
            if operands:
                parameters["course"] = operands.pop(0)
            if operands and operands[0] == "讨论":
                operands.pop(0)
            if operands:
                parameters["topic"] = operands[0]
            if len(operands) > 2:
                parameters["reply_to"] = operands[1]
                parameters["content"] = operands[2]
            elif len(operands) > 1:
                parameters["content"] = operands[1]
            parameters["anonymous"] = "匿名" in text
            missing = [key for key in ("course", "topic", "content") if key not in parameters]
            return CommandPlan(
                text,
                "learning.course.discussions.reply.create",
                parameters=parameters,
                confidence=0.98 if not missing else 0.72,
                missing_fields=missing,
                message="请依次用书名号提供课程、讨论和回复正文。" if missing else "",
            )
        if "讨论" in text and "删除" in text:
            parameters = {}
            operands = list(quoted)
            if operands:
                parameters["course"] = operands.pop(0)
            if operands and operands[0] == "讨论":
                operands.pop(0)
            if operands:
                parameters["topic"] = operands[0]
            missing = [key for key in ("course", "topic") if key not in parameters]
            return CommandPlan(
                text,
                "learning.course.discussions.topic.delete",
                parameters=parameters,
                confidence=0.98 if not missing else 0.72,
                missing_fields=missing,
                message="请依次用书名号提供课程和讨论。" if missing else "",
            )
        if "讨论" in text and re.search(r"编辑|修改", text):
            parameters = {}
            operands = list(quoted)
            if operands:
                parameters["course"] = operands.pop(0)
            if operands and operands[0] == "讨论":
                operands.pop(0)
            if operands:
                parameters["topic"] = operands[0]
            if len(operands) > 2:
                parameters["title"] = operands[1]
                parameters["content"] = operands[2]
            elif len(operands) > 1:
                if "标题" in text and not re.search(r"正文|内容", text):
                    parameters["title"] = operands[1]
                else:
                    parameters["content"] = operands[1]
            missing = [key for key in ("course", "topic") if key not in parameters]
            if "title" not in parameters and "content" not in parameters:
                missing.append("content")
            return CommandPlan(
                text,
                "learning.course.discussions.topic.update",
                parameters=parameters,
                confidence=0.98 if not missing else 0.72,
                missing_fields=missing,
                message="请依次用书名号提供课程、原讨论和新标题或正文。" if missing else "",
            )
        if "讨论" in text and re.search(r"发布|新建|发起|创建", text):
            parameters = {}
            operands = list(quoted)
            if operands:
                parameters["course"] = operands.pop(0)
            if operands and operands[0] == "讨论":
                operands.pop(0)
            for key, value in zip(("title", "content"), operands, strict=False):
                parameters[key] = value
            parameters["anonymous"] = "匿名" in text
            missing = [key for key in ("course", "title", "content") if key not in parameters]
            return CommandPlan(
                text,
                "learning.course.discussions.topic.create",
                parameters=parameters,
                confidence=0.98 if not missing else 0.72,
                missing_fields=missing,
                message="请依次用书名号提供课程、讨论标题和正文。" if missing else "",
            )
        if (
            "讨论" in text
            and re.search(r"查看|读取|显示|浏览", text)
            and (
                re.search(r"详情|回复|正文|内容", text)
                or (len(quoted) >= 2 and not re.search(r"列出|列表|有哪些|搜索|查找", text))
            )
        ):
            parameters: dict[str, object] = {}
            if quoted:
                parameters["course"] = quoted[0]
            operands = quoted[1:]
            if operands and operands[0] == "讨论":
                operands = operands[1:]
            if operands:
                parameters["topic"] = operands[0]
            if len(operands) > 1 and re.search(r"搜索|查找", text):
                parameters["reply_search"] = operands[1]
            parameters["class_only"] = bool(re.search(r"本班|当前班|这个班", text))
            parameters["order"] = 1 if re.search(r"正序|最早|从旧到新", text) else 2
            missing = [key for key in ("course", "topic") if key not in parameters]
            return CommandPlan(
                text,
                "learning.course.discussions.topic.read",
                parameters=parameters,
                confidence=0.98 if not missing else 0.72,
                missing_fields=missing,
                message="请依次用书名号提供课程和讨论。" if missing else "",
            )
        semantic_read = bool(re.search(r"列出|列表|有哪些|查看|读取|搜索|查找|浏览", text))
        semantic_actions = (
            ("自测", "learning.course.self_tests.list"),
            ("考试", "learning.course.exams.list"),
            ("作业", "learning.course.homeworks.list"),
            ("讨论", "learning.course.discussions.list"),
            ("资料", "learning.course.materials.list"),
            ("章节", "learning.course.chapters.list"),
            ("任务", "learning.course.activities.list"),
        )
        semantic = next(
            ((marker, action) for marker, action in semantic_actions if marker in text),
            None,
        )
        if semantic_read and semantic:
            marker, action = semantic
            parameters: dict[str, object] = {"course": quoted[0]} if quoted else {}
            extra_quoted = quoted[1:]
            if extra_quoted and extra_quoted[0] == marker:
                extra_quoted = extra_quoted[1:]
            if action == "learning.course.materials.list" and extra_quoted and "文件夹" in text:
                parameters["folder"] = extra_quoted[0]
            elif extra_quoted and re.search(r"搜索|查找", text):
                parameters["search"] = extra_quoted[0]
            if action == "learning.course.discussions.list":
                parameters["class_only"] = bool(re.search(r"本班|当前班|这个班", text))
            if action in {
                "learning.course.activities.list",
                "learning.course.homeworks.list",
                "learning.course.exams.list",
                "learning.course.self_tests.list",
            }:
                if "未开始" in text:
                    parameters["status"] = "not_started"
                elif "进行中" in text:
                    parameters["status"] = "ongoing"
                elif re.search(r"已结束|已完成", text):
                    parameters["status"] = "ended"
                elif "未交" in text:
                    parameters["status"] = "unsubmitted"
                elif "已交" in text:
                    parameters["status"] = "submitted"
            return CommandPlan(
                text,
                action,
                parameters=parameters,
                confidence=0.98 if quoted else 0.72,
                missing_fields=[] if quoted else ["course"],
                message=f"请用书名号提供要查看{marker}的课程。" if not quoted else "",
            )
        module_aliases = (
            "AI助教",
            "任务",
            "章节",
            "讨论",
            "作业",
            "考试",
            "资料",
            "错题集",
            "学习记录",
            "课程图谱",
            "自测",
            "直播课/见面课",
            "直播课",
            "见面课",
        )
        requested_module = quoted[1] if len(quoted) >= 2 else ""
        if not requested_module:
            requested_module = next(
                (module for module in module_aliases if module in text),
                "",
            )
        if requested_module and re.search(r"打开|进入|查看|读取", text):
            parameters: dict[str, object] = {"module": requested_module}
            if quoted:
                parameters["course"] = quoted[0]
            missing = [] if "course" in parameters else ["course"]
            return CommandPlan(
                text,
                "learning.course.module.open",
                parameters=parameters,
                confidence=0.98 if not missing else 0.74,
                missing_fields=missing,
                message="请用书名号提供要进入的我学课程。" if missing else "",
            )
        search = quoted[0] if quoted and re.search(r"搜索|查找", text) else ""
        parameters = {"search": search} if search else {}
        return CommandPlan(text, "learning.courses.list", parameters=parameters, confidence=0.97)

    course_list_intent = bool(
        re.search(
            r"(列出|查看|显示|有哪些).*(我教的课|我教的课程|教师课程)"
            r"|(我教的课|我教的课程|教师课程).*(列表|有哪些)",
            text,
        )
        or re.fullmatch(r"(?:列出|查看|显示)?(?:全部|所有)?课程(?:列表|有哪些)?", text)
    )
    if course_list_intent:
        return CommandPlan(text, "courses.list_teaching", confidence=0.96)

    permission_update = (
        re.search(r"教师|助教|团队成员", text)
        and "权限" in text
        and re.search(
            r"修改|开启|启用|打开|允许|授予|赋予|勾选|关闭|禁用|取消|"
            r"收回|撤销|去掉|设为|设置为|改为",
            text,
        )
    )
    if permission_update:
        quoted = _extract_quoted(text)
        permission_quotes = {
            value for value in quoted if _teacher_permission_field(value) is not None
        }
        identity_quotes = [value for value in quoted if value not in permission_quotes]
        parameters: dict[str, object] = {}
        if identity_quotes:
            parameters["course"] = identity_quotes[0]
        if len(identity_quotes) == 2:
            parameters["teacher"] = identity_quotes[1]
        elif len(identity_quotes) >= 3:
            parameters["clazz"] = identity_quotes[1]
            parameters["teacher"] = identity_quotes[2]
        changes = _parse_teacher_permission_changes(text)
        if changes:
            parameters["changes"] = changes
        missing = [key for key in ("course", "teacher", "changes") if key not in parameters]
        return CommandPlan(
            text,
            "course.teacher.permissions.update",
            parameters=parameters,
            confidence=0.97 if not missing else 0.63,
            missing_fields=missing,
            message=(
                "请给出课程、教师或助教姓名/工号，以及要开启或关闭的权限；"
                "权限可使用中文名称或接口字段名。"
                if missing
                else ""
            ),
        )

    if re.search(r"教师权限|助教权限|团队成员权限", text) and re.search(
        r"读取|查看|显示|是什么", text
    ):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) >= 3:
            parameters["clazz"] = quoted[1]
            parameters["teacher"] = quoted[2]
        elif len(quoted) >= 2:
            parameters["teacher"] = quoted[1]
        missing = [key for key in ("course", "teacher") if key not in parameters]
        return CommandPlan(
            text,
            "course.teacher.permissions.read",
            parameters=parameters,
            confidence=0.97 if not missing else 0.66,
            missing_fields=missing,
            message="请给出课程和教师或助教姓名、工号或人员 ID。" if missing else "",
        )

    if re.search(r"教师库|可添加教师|可添加助教", text) and re.search(r"搜索|查找", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["query"] = quoted[-1]
        if len(quoted) > 2:
            parameters["clazz"] = quoted[1]
        parameters["role"] = "assistant" if "助教" in text else "teacher"
        missing = [key for key in ("course", "query") if key not in parameters]
        return CommandPlan(
            text,
            "course.teacher_candidates.search",
            parameters=parameters,
            confidence=0.97 if not missing else 0.66,
            missing_fields=missing,
            message="请给出课程和要搜索的教师姓名或工号。" if missing else "",
        )

    if "教师库" in text and re.search(r"添加|加入", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["teacher"] = quoted[-1]
        if len(quoted) > 2:
            parameters["clazz"] = quoted[1]
        parameters["role"] = "assistant" if "助教" in text else "teacher"
        missing = [key for key in ("course", "teacher") if key not in parameters]
        return CommandPlan(
            text,
            "course.teacher.add_from_bank",
            parameters=parameters,
            confidence=0.97 if not missing else 0.66,
            missing_fields=missing,
            message="请给出课程和要添加的教师库人员。" if missing else "",
        )

    if re.search(r"添加教师|添加助教|加入教师|加入助教", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int] = {}
        for key, value in zip(("course", "name", "identity"), quoted, strict=False):
            parameters[key] = value
        parameters["role"] = "assistant" if "助教" in text else "teacher"
        parameters["identity_type"] = (
            "mobile"
            if re.search(r"手机|手机号", text)
            else "chaoxing_no"
            if "超星号" in text
            else "employee_no"
        )
        missing = [key for key in ("course", "name", "identity") if key not in parameters]
        return CommandPlan(
            text,
            "course.teacher.add_by_identity",
            parameters=parameters,
            confidence=0.96 if not missing else 0.65,
            missing_fields=missing,
            message="请依次给出课程、姓名和工号、手机号或超星号。" if missing else "",
        )

    if re.search(r"移除教师|移除助教|删除团队成员|从.*教学团队.*移除", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["teacher"] = quoted[-1]
        if len(quoted) > 2:
            parameters["clazz"] = quoted[1]
        missing = [key for key in ("course", "teacher") if key not in parameters]
        return CommandPlan(
            text,
            "course.teacher.remove",
            parameters=parameters,
            confidence=0.97 if not missing else 0.66,
            missing_fields=missing,
            message="请给出课程和要移除的教师或助教。" if missing else "",
        )

    if re.search(r"教师团队|教学团队|课程教师", text) and re.search(
        r"列出|查看|显示|搜索|有哪些", text
    ):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int] = {"course": quoted[0]} if quoted else {}
        if len(quoted) > 1:
            parameters["search"] = quoted[1]
        parameters["role"] = 3 if "助教" in text else 1 if "只看教师" in text else 0
        missing = [] if "course" in parameters else ["course"]
        return CommandPlan(
            text,
            "course.teachers.list",
            parameters=parameters,
            confidence=0.94 if not missing else 0.68,
            missing_fields=missing,
            message="请用书名号或引号给出课程名称。" if missing else "",
        )

    if re.search(
        r"学生成绩|班级成绩|成绩明细|综合成绩(?:列表|明细|排名)|成绩排名|原始分数|原始成绩",
        text,
    ):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int | bool] = {"course": quoted[0]} if quoted else {}
        if len(quoted) > 1:
            parameters["clazz"] = quoted[1]
        if len(quoted) > 2:
            parameters["search"] = quoted[2]
        parameters["raw_scores"] = bool(re.search(r"原始分数|原始成绩|未加权", text))
        if re.search(r"排名|从高到低|降序", text):
            parameters["sort"] = "score"
            parameters["descending"] = True
        missing = [] if "course" in parameters else ["course"]
        return CommandPlan(
            text,
            "course.grades.list",
            parameters=parameters,
            confidence=0.96 if not missing else 0.68,
            missing_fields=missing,
            message="请用书名号或引号给出课程名称。" if missing else "",
        )

    override_match = re.search(
        r"(?:综合成绩|总评).*(?:改为|设为|设置为)\s*(\d+(?:\.\d+)?)\s*分?",
        text,
    )
    restore_override = bool(re.search(r"(?:综合成绩|总评).*(?:恢复自动|取消覆盖)", text))
    if override_match or restore_override:
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int | float | bool | None] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) >= 3:
            parameters["clazz"] = quoted[1]
            parameters["student"] = quoted[2]
        elif len(quoted) >= 2:
            parameters["student"] = quoted[1]
        parameters["score"] = None if restore_override else float(override_match.group(1))
        missing = [key for key in ("course", "student") if key not in parameters]
        return CommandPlan(
            text,
            "course.grade_override.set",
            parameters=parameters,
            confidence=0.97 if not missing else 0.64,
            missing_fields=missing,
            message="请给出课程、学生姓名或学号，以及目标成绩。" if missing else "",
        )

    if re.match(r"(?:请)?(?:把|将)?(?:设置|开放|关闭)", text) and re.search(
        r"成绩可见|查看成绩|成绩开放", text
    ):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int | bool | list[str]] = {}
        if quoted:
            parameters["course"] = quoted[0]
        parameters["visible_classes"] = [] if re.search(r"关闭|全部不可见", text) else quoted[1:]
        parameters["students_can_view_rank"] = "显示排名" in text
        parameters["students_can_view_class_average"] = "显示班级平均分" in text
        missing = [] if "course" in parameters else ["course"]
        if not parameters["visible_classes"] and not re.search(r"关闭|全部不可见", text):
            missing.append("visible_classes")
        return CommandPlan(
            text,
            "course.grade_visibility.set",
            parameters=parameters,
            confidence=0.95 if not missing else 0.62,
            missing_fields=missing,
            message="请给出课程和完整的成绩可见班级列表。" if missing else "",
        )

    if re.search(r"成绩可见性|学生查看成绩设置|成绩开放设置", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int | bool] = {"course": quoted[0]} if quoted else {}
        if len(quoted) > 1:
            parameters["clazz"] = quoted[1]
        missing = [] if "course" in parameters else ["course"]
        return CommandPlan(
            text,
            "course.grade_visibility.read",
            parameters=parameters,
            confidence=0.96 if not missing else 0.68,
            missing_fields=missing,
            message="请用书名号或引号给出课程名称。" if missing else "",
        )

    if re.search(r"学习进度|学生进度|任务点完成情况|学习明细", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int | bool] = {"course": quoted[0]} if quoted else {}
        if len(quoted) > 1:
            parameters["clazz"] = quoted[1]
        if len(quoted) > 2:
            parameters["search"] = quoted[2]
        if re.search(r"按.*(?:视频|观看).*时长", text):
            parameters["sort"] = "totalTime"
        elif re.search(r"按.*任务点", text):
            parameters["sort"] = "job"
        if re.search(r"从高到低|降序|最多|最慢|排名", text):
            parameters["descending"] = True
        missing = [] if "course" in parameters else ["course"]
        return CommandPlan(
            text,
            "course.learning_progress.list",
            parameters=parameters,
            confidence=0.96 if not missing else 0.68,
            missing_fields=missing,
            message="请用书名号或引号给出课程名称。" if missing else "",
        )

    if re.search(r"发送.*(?:异常|学习).*提醒|提醒.*异常.*学生", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int | bool] = {}
        if len(quoted) >= 5:
            parameters.update(
                {
                    "course": quoted[0],
                    "clazz": quoted[1],
                    "student": quoted[2],
                    "title": quoted[3],
                    "content": quoted[4],
                }
            )
        elif len(quoted) >= 4:
            parameters.update(
                {
                    "course": quoted[0],
                    "student": quoted[1],
                    "title": quoted[2],
                    "content": quoted[3],
                }
            )
        missing = [
            key for key in ("course", "student", "title", "content") if key not in parameters
        ]
        return CommandPlan(
            text,
            "course.study_monitor.remind",
            parameters=parameters,
            confidence=0.96 if not missing else 0.62,
            missing_fields=missing,
            message="请给出课程、学生、提醒标题和提醒正文。" if missing else "",
        )

    if re.search(r"清除|删除", text) and re.search(r"异常学习|学习异常|异常记录", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int | bool] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) >= 3:
            parameters["clazz"] = quoted[1]
            parameters["student"] = quoted[2]
        elif len(quoted) >= 2:
            parameters["student"] = quoted[1]
        missing = [key for key in ("course", "student") if key not in parameters]
        return CommandPlan(
            text,
            "course.study_monitor.clear",
            parameters=parameters,
            confidence=0.96 if not missing else 0.64,
            missing_fields=missing,
            message="请给出课程和学生姓名或学号。" if missing else "",
        )

    if re.search(r"学习监控|异常学习|异常学习记录|学习异常", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int | bool] = {"course": quoted[0]} if quoted else {}
        if len(quoted) > 1:
            parameters["clazz"] = quoted[1]
        if len(quoted) > 2:
            parameters["search"] = quoted[2]
        parameters["only_abnormal"] = "异常" in text
        parameters["anomaly_type"] = (
            1 if "视频" in text else 2 if "作业" in text else 4 if "考试" in text else 0
        )
        missing = [] if "course" in parameters else ["course"]
        return CommandPlan(
            text,
            "course.study_monitor.list",
            parameters=parameters,
            confidence=0.96 if not missing else 0.68,
            missing_fields=missing,
            message="请用书名号或引号给出课程名称。" if missing else "",
        )

    if re.search(r"成绩权重|课程权重|考核权重|综合成绩(?:构成|组成)", text) and re.search(
        r"读取|查看|显示|列出|是什么", text
    ):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int] = {"course": quoted[0]} if quoted else {}
        if len(quoted) > 1:
            parameters["clazz"] = quoted[1]
        missing = [] if "course" in parameters else ["course"]
        return CommandPlan(
            text,
            "course.grade_weights.read",
            parameters=parameters,
            confidence=0.96 if not missing else 0.68,
            missing_fields=missing,
            message="请用书名号或引号给出课程名称。" if missing else "",
        )

    if re.search(r"访问日志|访问记录", text) and re.search(r"读取|查看|显示|列出", text):
        quoted = _extract_quoted(text)
        date_match = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月(?:\s*(\d{1,2})\s*日)?", text)
        parameters: dict[str, str | int] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) >= 3:
            parameters["clazz"] = quoted[1]
            parameters["student"] = quoted[2]
        elif len(quoted) >= 2:
            parameters["student"] = quoted[1]
        if date_match:
            parameters["year"] = int(date_match.group(1))
            parameters["month"] = int(date_match.group(2))
            parameters["day"] = int(date_match.group(3) or 0)
        missing = [key for key in ("course", "student", "year", "month") if key not in parameters]
        return CommandPlan(
            text,
            "class.student.access_logs.list",
            parameters=parameters,
            confidence=0.96 if not missing else 0.66,
            missing_fields=missing,
            message=("请给出课程、学生姓名或学号，以及要查询的年月。" if missing else ""),
        )

    if "恢复" in text and re.search(r"退课|退班|移除", text) and "学生" in text:
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) >= 3:
            parameters["clazz"] = quoted[1]
            parameters["student"] = quoted[2]
        elif len(quoted) >= 2:
            parameters["student"] = quoted[1]
        missing = [key for key in ("course", "student") if key not in parameters]
        return CommandPlan(
            text,
            "class.student.restore",
            parameters=parameters,
            confidence=0.97 if not missing else 0.65,
            missing_fields=missing,
            message="请给出课程、班级（如有多个）和学生姓名或退课记录 ID。" if missing else "",
        )

    if re.search(r"批准|通过|同意|拒绝|驳回", text) and re.search(
        r"入班申请|加入申请|学生加入申请", text
    ):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int] = {}
        for key, value in zip(("course", "clazz", "application"), quoted, strict=False):
            parameters[key] = value
        parameters["decision"] = "reject" if re.search(r"拒绝|驳回", text) else "approve"
        missing = [key for key in ("course", "application") if key not in parameters]
        return CommandPlan(
            text,
            "class.join_application.decide",
            parameters=parameters,
            confidence=0.97 if not missing else 0.66,
            missing_fields=missing,
            message="请依次用书名号或引号给出课程、班级和申请人或申请记录 ID。" if missing else "",
        )

    if re.search(r"入班申请|加入申请|待审批学生", text) and re.search(
        r"读取|查看|显示|列出|有哪些", text
    ):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["clazz"] = quoted[1]
        missing = [] if "course" in parameters else ["course"]
        return CommandPlan(
            text,
            "class.join_applications.list",
            parameters=parameters,
            confidence=0.96 if not missing else 0.68,
            missing_fields=missing,
            message="请用书名号或引号给出课程名称。" if missing else "",
        )

    if re.search(r"移动|转移|换班", text) and "学生" in text and "班级" in text:
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["clazz"] = quoted[1]
        if len(quoted) > 2:
            parameters["student"] = quoted[2]
        if len(quoted) > 3:
            parameters["target_clazz"] = quoted[3]
        missing = [
            key for key in ("course", "clazz", "student", "target_clazz") if key not in parameters
        ]
        return CommandPlan(
            text,
            "class.student.move",
            parameters=parameters,
            confidence=0.97 if not missing else 0.64,
            missing_fields=missing,
            message="请依次用书名号或引号给出课程、原班级、学生和目标班级。" if missing else "",
        )

    if re.search(r"退课日志|退班记录|学生移除记录", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int] = {"course": quoted[0]} if quoted else {}
        if len(quoted) > 1:
            parameters["clazz"] = quoted[1]
        if len(quoted) > 2:
            parameters["search"] = quoted[2]
        missing = [] if "course" in parameters else ["course"]
        return CommandPlan(
            text,
            "class.student_leave_logs.list",
            parameters=parameters,
            confidence=0.96 if not missing else 0.68,
            missing_fields=missing,
            message="请用书名号或引号给出课程名称。" if missing else "",
        )

    if re.search(r"加班日志|加入班级记录|学生加入记录", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int] = {"course": quoted[0]} if quoted else {}
        if len(quoted) > 1:
            parameters["clazz"] = quoted[1]
        if len(quoted) > 2:
            parameters["search"] = quoted[2]
        parameters["join_type"] = (
            2
            if "自主" in text
            else 1
            if "教师" in text or "手动" in text
            else 3
            if "教务" in text or "同步" in text
            else 0
            if "其他" in text
            else -1
        )
        missing = [] if "course" in parameters else ["course"]
        return CommandPlan(
            text,
            "class.student_join_logs.list",
            parameters=parameters,
            confidence=0.96 if not missing else 0.68,
            missing_fields=missing,
            message="请用书名号或引号给出课程名称。" if missing else "",
        )

    if re.search(r"操作日志|教师操作记录|课程变更日志", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int] = {"course": quoted[0]} if quoted else {}
        if len(quoted) > 1:
            parameters["module"] = quoted[1]
        dates = re.findall(r"\d{4}-\d{1,2}-\d{1,2}", text)
        if dates:
            parameters["start_date"] = dates[0]
        if len(dates) > 1:
            parameters["end_date"] = dates[1]
        missing = [] if "course" in parameters else ["course"]
        return CommandPlan(
            text,
            "course.operation_logs.list",
            parameters=parameters,
            confidence=0.96 if not missing else 0.68,
            missing_fields=missing,
            message="请用书名号或引号给出课程名称。" if missing else "",
        )

    if re.search(r"学生库|可添加学生", text) and re.search(r"搜索|查找", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int] = {}
        for key, value in zip(("course", "clazz", "query"), quoted, strict=False):
            parameters[key] = value
        missing = [key for key in ("course", "query") if key not in parameters]
        return CommandPlan(
            text,
            "class.student_candidates.search",
            parameters=parameters,
            confidence=0.97 if not missing else 0.66,
            missing_fields=missing,
            message="请依次用书名号或引号给出课程、班级和学生姓名或学号。" if missing else "",
        )

    if "学生库" in text and re.search(r"添加|加入", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int] = {}
        for key, value in zip(("course", "clazz", "student"), quoted, strict=False):
            parameters[key] = value
        missing = [key for key in ("course", "student") if key not in parameters]
        return CommandPlan(
            text,
            "class.student.add_from_bank",
            parameters=parameters,
            confidence=0.97 if not missing else 0.66,
            missing_fields=missing,
            message="请依次用书名号或引号给出课程、班级和要添加的学生。" if missing else "",
        )

    if re.search(r"添加学生|加入学生", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int] = {}
        for key, value in zip(("course", "clazz", "name", "identity"), quoted, strict=False):
            parameters[key] = value
        parameters["identity_type"] = (
            "email"
            if "邮箱" in text
            else "mobile"
            if re.search(r"手机|手机号", text)
            else "employee_no"
            if "工号" in text
            else "student_no"
        )
        missing = [key for key in ("course", "name", "identity") if key not in parameters]
        return CommandPlan(
            text,
            "class.student.add_by_identity",
            parameters=parameters,
            confidence=0.96 if not missing else 0.65,
            missing_fields=missing,
            message="请依次用书名号或引号给出课程、班级、学生姓名和身份号码。" if missing else "",
        )

    if re.search(r"移除学生|删除班级学生|从班级删除.*学生", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int] = {}
        for key, value in zip(("course", "clazz", "student"), quoted, strict=False):
            parameters[key] = value
        missing = [key for key in ("course", "student") if key not in parameters]
        return CommandPlan(
            text,
            "class.student.remove",
            parameters=parameters,
            confidence=0.97 if not missing else 0.66,
            missing_fields=missing,
            message="请依次用书名号或引号给出课程、班级和要移除的学生。" if missing else "",
        )

    if re.search(r"学生名单|班级学生|学生列表", text) and re.search(
        r"列出|查看|显示|搜索|有哪些", text
    ):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["clazz"] = quoted[1]
        if len(quoted) > 2:
            parameters["search"] = quoted[2]
        missing = [] if "course" in parameters else ["course"]
        return CommandPlan(
            text,
            "class.students.list",
            parameters=parameters,
            confidence=0.94 if not missing else 0.68,
            missing_fields=missing,
            message="请用书名号或引号给出课程名称。" if missing else "",
        )

    if "班级" in text and re.search(r"新建|创建", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["name"] = quoted[1]
        missing = [key for key in ("course", "name") if key not in parameters]
        return CommandPlan(
            text,
            "classes.create",
            parameters=parameters,
            confidence=0.96 if not missing else 0.68,
            missing_fields=missing,
            message="请依次用书名号或引号给出课程名称和新班级名称。" if missing else "",
        )

    if "班级" in text and re.search(r"改名|重命名|名称改为", text):
        quoted = _extract_quoted(text)
        parameters = {}
        for key, value in zip(("course", "clazz", "name"), quoted, strict=False):
            parameters[key] = value
        missing = [key for key in ("course", "clazz", "name") if key not in parameters]
        return CommandPlan(
            text,
            "class.rename",
            parameters=parameters,
            confidence=0.97 if not missing else 0.68,
            missing_fields=missing,
            message="请依次用书名号或引号给出课程、原班级和新名称。" if missing else "",
        )

    if "班级" in text and "删除" in text:
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["clazz"] = quoted[1]
        missing = [key for key in ("course", "clazz") if key not in parameters]
        return CommandPlan(
            text,
            "class.delete",
            parameters=parameters,
            confidence=0.97 if not missing else 0.68,
            missing_fields=missing,
            message="请依次用书名号或引号给出课程和班级。" if missing else "",
        )

    if re.search(r"邀请码|加课码|班级二维码", text) and re.search(
        r"读取|查看|显示|是什么|给我", text
    ):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["clazz"] = quoted[1]
        missing = [] if "course" in parameters else ["course"]
        return CommandPlan(
            text,
            "class.invitation.read",
            parameters=parameters,
            confidence=0.97 if not missing else 0.68,
            missing_fields=missing,
            message="请用书名号或引号给出课程名称。" if missing else "",
        )

    if re.search(r"班级设置|班级配置", text) and re.search(r"读取|查看|显示|是什么", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["clazz"] = quoted[1]
        missing = [] if "course" in parameters else ["course"]
        return CommandPlan(
            text,
            "class.settings.read",
            parameters=parameters,
            confidence=0.96 if not missing else 0.68,
            missing_fields=missing,
            message="请用书名号或引号给出课程名称。" if missing else "",
        )

    if (
        "班级" in text
        and "资料" not in text
        and re.search(r"设置|配置|允许|禁止|公开|隐藏|结束|结课|人数上限", text)
    ):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int | bool] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["clazz"] = quoted[1]
        if re.search(r"允许学生(?:加入|加班)|开启.*学生加入", text):
            parameters["allow_student_join"] = True
        elif re.search(r"禁止学生(?:加入|加班)|关闭.*学生加入", text):
            parameters["allow_student_join"] = False
        if re.search(r"加入.*(?:需要|要求).*审批|教师审批", text):
            parameters["join_requires_approval"] = True
        elif re.search(r"加入.*不需要审批|取消.*审批", text):
            parameters["join_requires_approval"] = False
        if re.search(r"允许学生退课", text):
            parameters["allow_student_withdraw"] = True
        elif re.search(r"禁止学生退课", text):
            parameters["allow_student_withdraw"] = False
        if re.search(r"全网公开", text):
            parameters["public_scope"] = "network"
        elif re.search(r"校内公开", text):
            parameters["public_scope"] = "school"
        elif re.search(r"关闭公开|不公开", text):
            parameters["public_scope"] = "closed"
        limit_match = re.search(r"人数上限\D*(\d+)", text)
        if limit_match:
            parameters["student_limit"] = int(limit_match.group(1))
        if re.search(r"取消结课|恢复开课", text):
            parameters["ended"] = False
        elif re.search(r"结束班级|班级结课|结束课程", text):
            parameters["ended"] = True
        if re.search(r"向学生隐藏|隐藏班级", text):
            parameters["hidden_from_students"] = True
        elif re.search(r"取消隐藏|向学生显示", text):
            parameters["hidden_from_students"] = False
        missing = [] if "course" in parameters else ["course"]
        setting_keys = set(parameters) - {"course", "clazz"}
        if not setting_keys:
            missing.append("setting")
        return CommandPlan(
            text,
            "class.settings.update",
            parameters=parameters,
            confidence=0.95 if not missing else 0.65,
            missing_fields=missing,
            message="请给出课程、班级（如有多个）和要修改的具体设置。" if missing else "",
        )

    if "班级" in text and "资料" not in text and re.search(r"列出|查看|显示|有哪些|进入", text):
        quoted = _extract_quoted(text)
        course = quoted[0] if quoted else ""
        return CommandPlan(
            text,
            "courses.list_classes",
            parameters={"course": course} if course else {},
            confidence=0.88 if course else 0.67,
            missing_fields=[] if course else ["course"],
            message="请提供课程名称或课程 ID。" if not course else "",
        )

    quoted = _extract_quoted(text)
    question_reference = re.search(r"第\s*(\d+)\s*题", text)
    refers_to_homework_question = bool(
        re.search(r"作业.*(?:题目|试题|第\s*\d+\s*题)", text)
        or re.search(r"(?:题目|试题|第\s*\d+\s*题).*作业", text)
    )

    if refers_to_homework_question and re.search(r"删除|移除|清除", text):
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["homework"] = quoted[1]
        if len(quoted) > 2:
            parameters["question"] = quoted[2]
        elif question_reference:
            parameters["question"] = question_reference.group(1)
        missing = [key for key in ("course", "homework", "question") if key not in parameters]
        return CommandPlan(
            text,
            "homework.question.delete",
            parameters=parameters,
            confidence=0.97 if not missing else 0.65,
            missing_fields=missing,
            message="请依次给出课程、作业或草稿、题号或题目 ID。" if missing else "",
        )

    if refers_to_homework_question and re.search(r"修改|更新|编辑|改为", text):
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["homework"] = quoted[1]
        if question_reference:
            parameters["question"] = question_reference.group(1)
            content_candidates = quoted[2:]
        elif len(quoted) > 2:
            parameters["question"] = quoted[2]
            content_candidates = quoted[3:]
        else:
            content_candidates = []
        if re.search(r"题干|题目内容", text) and content_candidates:
            parameters["stem"] = content_candidates[0]
        options = _labeled_question_options(text)
        if options:
            parameters["options"] = options
        correct_match = re.search(
            r"(?:正确答案|答案)\s*(?:改为|设为|为|是|[:：])?\s*"
            r"([A-Z](?:\s*[,，、;；]\s*[A-Z])*)",
            text,
            flags=re.IGNORECASE,
        )
        if correct_match:
            parameters["correct_answer"] = correct_match.group(1)
        boolean_match = re.search(
            r"(?:正确答案|答案)\s*(?:改为|设为|为|是|[:：])?\s*"
            r"(正确|错误|对|错|true|false)",
            text,
            flags=re.IGNORECASE,
        )
        if boolean_match:
            parameters["answer"] = boolean_match.group(1)
        score_match = re.search(r"(?:分值|分数)\s*(?:改为|设为|为|[:：])?\s*(\d+(?:\.\d+)?)", text)
        if score_match:
            parameters["score"] = float(score_match.group(1))
        difficulty_match = re.search(r"难度\s*(?:改为|设为|为|[:：])?\s*(0\.\d|1(?:\.0)?)", text)
        if difficulty_match:
            parameters["difficulty"] = float(difficulty_match.group(1))
        analysis_match = re.search(r"(?:解析|答案解析)[^《“\"']*[《“\"']([^》”\"']*)[》”\"']", text)
        if analysis_match:
            parameters["analysis"] = analysis_match.group(1)
        missing = [key for key in ("course", "homework", "question") if key not in parameters]
        has_change = any(
            key in parameters
            for key in (
                "stem",
                "options",
                "correct_answer",
                "answer",
                "score",
                "difficulty",
                "analysis",
            )
        )
        if not has_change:
            missing.append("changed_field")
        return CommandPlan(
            text,
            "homework.question.update",
            parameters=parameters,
            confidence=0.94 if not missing else 0.62,
            missing_fields=missing,
            message="请给出课程、作业、题目以及至少一个要修改的字段。" if missing else "",
        )

    question_type = _homework_question_type_from_text(text)
    if question_type and "作业" in text and re.search(r"添加|新增|加入|加一道|出一道", text):
        parameters: dict[str, object] = {"question_type": question_type}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["homework"] = quoted[1]
        if len(quoted) > 2:
            parameters["stem"] = quoted[2]
        options = _labeled_question_options(text)
        if options:
            parameters["options"] = options
        correct_match = re.search(
            r"(?:正确答案|答案)\s*(?:为|是|[:：])?\s*"
            r"([A-Z](?:\s*[,，、;；]\s*[A-Z])*)",
            text,
            flags=re.IGNORECASE,
        )
        if correct_match:
            parameters["correct_answer"] = correct_match.group(1)
        if question_type == "fill_blank" and len(quoted) > 3:
            parameters["answers"] = quoted[3:]
        answer_match = re.search(
            r"(?:参考答案|答案)[^《“\"']*[《“\"']([^》”\"']*)[》”\"']",
            text,
        )
        if answer_match and question_type == "short_answer":
            parameters["answer"] = answer_match.group(1)
        boolean_match = re.search(
            r"(?:正确答案|答案)\s*(?:为|是|[:：])?\s*(正确|错误|对|错|true|false)",
            text,
            flags=re.IGNORECASE,
        )
        if boolean_match:
            parameters["answer"] = boolean_match.group(1)
        score_match = re.search(r"(?:分值|分数)\s*(?:为|是|[:：])?\s*(\d+(?:\.\d+)?)", text)
        parameters["score"] = float(score_match.group(1)) if score_match else 5
        difficulty_match = re.search(r"难度\s*(?:为|是|[:：])?\s*(0\.\d|1(?:\.0)?)", text)
        parameters["difficulty"] = float(difficulty_match.group(1)) if difficulty_match else 0.8
        analysis_match = re.search(r"(?:解析|答案解析)[^《“\"']*[《“\"']([^》”\"']*)[》”\"']", text)
        if analysis_match:
            parameters["analysis"] = analysis_match.group(1)
        missing = [key for key in ("course", "homework", "stem") if key not in parameters]
        if question_type in {"single_choice", "multiple_choice"}:
            missing.extend(key for key in ("options", "correct_answer") if key not in parameters)
        if question_type == "fill_blank" and "answers" not in parameters:
            missing.append("answers")
        if question_type == "true_false" and "answer" not in parameters:
            missing.append("answer")
        return CommandPlan(
            text,
            "homework.question.add",
            parameters=parameters,
            confidence=0.95 if not missing else 0.61,
            missing_fields=missing,
            message="请给出课程、作业、题型所需题干、选项和答案。" if missing else "",
        )

    if refers_to_homework_question and re.search(r"读取|查看|显示|展开", text):
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["homework"] = quoted[1]
        if len(quoted) > 2:
            parameters["question"] = quoted[2]
        elif question_reference:
            parameters["question"] = question_reference.group(1)
        missing = [key for key in ("course", "homework") if key not in parameters]
        return CommandPlan(
            text,
            "homework.library.item.read",
            parameters=parameters,
            confidence=0.95 if not missing else 0.66,
            missing_fields=missing,
            message="请依次给出课程以及作业库作业或草稿。" if missing else "",
        )

    if "作业草稿" in text and re.search(r"改名|重命名|修改标题", text):
        parameters: dict[str, str] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) == 3:
            parameters["draft"] = quoted[1]
            parameters["title"] = quoted[2]
        elif len(quoted) >= 4:
            parameters["clazz"] = quoted[1]
            parameters["draft"] = quoted[2]
            parameters["title"] = quoted[3]
        missing = [key for key in ("course", "draft", "title") if key not in parameters]
        return CommandPlan(
            text,
            "homework.draft.update",
            parameters=parameters,
            confidence=0.96 if not missing else 0.65,
            missing_fields=missing,
            message="请依次给出课程、原草稿标题或 ID 和新标题。" if missing else "",
        )

    if "作业草稿" in text and re.search(r"删除|清除", text):
        parameters: dict[str, str] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) == 2:
            parameters["draft"] = quoted[1]
        elif len(quoted) >= 3:
            parameters["clazz"] = quoted[1]
            parameters["draft"] = quoted[2]
        missing = [key for key in ("course", "draft") if key not in parameters]
        return CommandPlan(
            text,
            "homework.draft.delete",
            parameters=parameters,
            confidence=0.97 if not missing else 0.66,
            missing_fields=missing,
            message="请给出课程和要永久删除的作业草稿标题或 ID。" if missing else "",
        )

    if "作业草稿" in text and re.search(r"新建|创建|保存", text):
        parameters: dict[str, str] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) == 2:
            parameters["title"] = quoted[1]
        elif len(quoted) >= 3:
            parameters["clazz"] = quoted[1]
            parameters["title"] = quoted[2]
        missing = [key for key in ("course", "title") if key not in parameters]
        return CommandPlan(
            text,
            "homework.draft.create",
            parameters=parameters,
            confidence=0.97 if not missing else 0.66,
            missing_fields=missing,
            message="请给出课程和作业草稿标题。" if missing else "",
        )

    if re.search(r"作业草稿|作业草稿箱", text) and re.search(r"列出|查看|显示|搜索|有哪些", text):
        parameters: dict[str, str] = {"course": quoted[0]} if quoted else {}
        if "搜索" in text and len(quoted) > 1:
            parameters["search"] = quoted[-1]
        missing = [] if "course" in parameters else ["course"]
        return CommandPlan(
            text,
            "homework.drafts.list",
            parameters=parameters,
            confidence=0.95 if not missing else 0.68,
            missing_fields=missing,
            message="请给出课程名称或课程 ID。" if missing else "",
        )

    if "作业库" in text and re.search(r"列出|查看|显示|搜索|有哪些", text):
        parameters: dict[str, str] = {"course": quoted[0]} if quoted else {}
        if "搜索" in text and len(quoted) > 1:
            parameters["search"] = quoted[-1]
        missing = [] if "course" in parameters else ["course"]
        return CommandPlan(
            text,
            "homework.library.list",
            parameters=parameters,
            confidence=0.95 if not missing else 0.68,
            missing_fields=missing,
            message="请给出课程名称或课程 ID。" if missing else "",
        )

    if re.search(r"作业库.*(?:发放|发布|布置)|(?:发放|发布|布置).*作业", text):
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["homework"] = quoted[1]
        date_pattern = r"\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}(?::\d{2})?"
        target_classes = [
            value for value in quoted[2:] if not re.fullmatch(date_pattern, value.strip())
        ]
        if target_classes:
            parameters["target_classes"] = target_classes
        start_match = re.search(rf"(?:开始时间|从)\D*({date_pattern})", text)
        end_match = re.search(rf"(?:结束时间|截止时间|截止|至)\D*({date_pattern})", text)
        parameters["start_time"] = start_match.group(1) if start_match else "now"
        if end_match:
            parameters["end_time"] = end_match.group(1)
        parameters["allow_late_submission"] = bool(re.search(r"允许.*补交|开启.*补交", text))
        deadline_match = re.search(rf"补交截止\D*({date_pattern})", text)
        if deadline_match:
            parameters["late_deadline"] = deadline_match.group(1)
        passing_match = re.search(r"(?:及格|通过)(?:分数|分|线)?\D*(\d+(?:\.\d+)?)", text)
        if passing_match:
            parameters["passing_score"] = float(passing_match.group(1))
        redo_match = re.search(r"(?:允许)?重做\D*(\d+)\s*次", text)
        if redo_match:
            parameters["redo_times"] = int(redo_match.group(1))
        if re.search(r"禁止粘贴|不允许粘贴", text):
            parameters["allow_paste"] = False
        if re.search(r"隐藏分数|不显示分数", text):
            parameters["show_score"] = False
        if re.search(r"隐藏正误|不显示正误", text):
            parameters["show_correctness"] = False
        if re.search(r"题目乱序|随机题序", text):
            parameters["randomize_questions"] = True
        if re.search(r"选项乱序|随机选项", text):
            parameters["randomize_options"] = True
        missing = [key for key in ("course", "homework") if key not in parameters]
        return CommandPlan(
            text,
            "homework.library.publish",
            parameters=parameters,
            confidence=0.96 if not missing else 0.64,
            missing_fields=missing,
            message="请依次给出课程和作业库作业标题或 ID。" if missing else "",
        )

    score_match = re.search(r"(?:打|评分为|设为)\s*(\d+(?:\.\d)?)\s*分", text)
    if "作业" in text and score_match and len(quoted) >= 3:
        return CommandPlan(
            text,
            "homework.score.set",
            parameters={
                "course": quoted[0],
                "homework": quoted[1],
                "submission": quoted[2],
                "score": score_match.group(1),
            },
            confidence=0.96,
        )
    if "作业" in text and re.search(r"作答|答案|批阅详情", text) and len(quoted) >= 3:
        return CommandPlan(
            text,
            "homework.submission.read",
            parameters={
                "course": quoted[0],
                "homework": quoted[1],
                "submission": quoted[2],
            },
            confidence=0.94,
        )

    if "作业" in text and re.search(r"提交|作答", text):
        parameters: dict[str, str | int] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["homework"] = quoted[1]
        parameters["status"] = 3 if re.search(r"待批|未批", text) else 4 if "已批" in text else 0
        missing = [key for key in ("course", "homework") if key not in parameters]
        return CommandPlan(
            text,
            "homework.submissions.list",
            parameters=parameters,
            confidence=0.93 if not missing else 0.68,
            missing_fields=missing,
            message="请依次用书名号或引号给出课程名称和作业名称。" if missing else "",
        )

    if "作业" in text and re.search(r"列出|查看|显示|有哪些|待批|未批", text):
        quoted = _extract_quoted(text)
        course = quoted[0] if quoted else ""
        ungraded = bool(re.search(r"待批|未批|未批改", text))
        return CommandPlan(
            text,
            "homework.list_ungraded" if ungraded else "homework.list",
            parameters={"course": course} if course else {},
            confidence=0.94 if course else 0.7,
            missing_fields=[] if course else ["course"],
            message="请用书名号或引号给出课程名称。" if not course else "",
        )

    if re.search(r"删除|移除", text) and re.search(r"页面|卡片|内容页", text) and "章节" in text:
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["chapter"] = quoted[1]
        if len(quoted) > 2:
            parameters["card"] = quoted[2]
        missing = [key for key in ("course", "chapter", "card") if key not in parameters]
        return CommandPlan(
            text,
            "chapters.card.delete",
            parameters=parameters,
            confidence=0.97 if not missing else 0.62,
            missing_fields=missing,
            message="请依次给出课程、章节和要删除的页面标题或 ID。" if missing else "",
        )

    if (
        re.search(r"移动|移到|排序|调整顺序", text)
        and re.search(r"页面|卡片|内容页", text)
        and "章节" in text
    ):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["chapter"] = quoted[1]
        if len(quoted) > 2:
            parameters["card"] = quoted[2]
        position_match = re.search(r"(?:第|到)\s*(\d+)\s*(?:页|个|位|位置)", text)
        if position_match:
            parameters["target_position"] = int(position_match.group(1))
        missing = [
            key for key in ("course", "chapter", "card", "target_position") if key not in parameters
        ]
        return CommandPlan(
            text,
            "chapters.card.move",
            parameters=parameters,
            confidence=0.96 if not missing else 0.61,
            missing_fields=missing,
            message="请依次给出课程、章节、页面和一基目标位置。" if missing else "",
        )

    if (
        re.search(r"页面|卡片|内容页", text)
        and "章节" in text
        and re.search(r"重命名|改名|修改|编辑|更新|正文.*改为|内容.*改为", text)
    ):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["chapter"] = quoted[1]
        if len(quoted) > 2:
            parameters["card"] = quoted[2]
        if len(quoted) > 3:
            if re.search(r"重命名|改名|标题", text):
                parameters["title"] = quoted[3]
            else:
                parameters["content"] = quoted[3]
        missing = [key for key in ("course", "chapter", "card") if key not in parameters]
        if "title" not in parameters and "content" not in parameters:
            missing.append("title_or_content")
        return CommandPlan(
            text,
            "chapters.card.update",
            parameters=parameters,
            confidence=0.96 if not missing else 0.61,
            missing_fields=missing,
            message="请依次给出课程、章节、页面，以及新标题或新正文。" if missing else "",
        )

    if (
        re.search(r"新建|创建|添加|新增", text)
        and re.search(r"页面|卡片|内容页", text)
        and "章节" in text
    ):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["chapter"] = quoted[1]
        if len(quoted) > 2:
            parameters["title"] = quoted[2]
        if len(quoted) > 3:
            parameters["content"] = quoted[3]
        missing = [key for key in ("course", "chapter", "title") if key not in parameters]
        return CommandPlan(
            text,
            "chapters.card.create",
            parameters=parameters,
            confidence=0.96 if not missing else 0.62,
            missing_fields=missing,
            message="请依次给出课程、章节和新页面标题；正文可选。" if missing else "",
        )

    course_asset_match = re.search(r"课件|教案", text)
    if course_asset_match:
        kind = "teaching_plan" if "教案" in course_asset_match.group(0) else "courseware"
        quoted = _extract_quoted(text)

        if "回收站" in text and re.search(r"永久删除|彻底删除", text):
            parameters = {"kind": kind}
            if quoted:
                parameters["course"] = quoted[0]
            if len(quoted) > 1:
                parameters["assets"] = quoted[1:]
            missing = [key for key in ("course", "assets") if key not in parameters]
            return CommandPlan(
                text,
                "course_assets.recycle.items.delete",
                parameters=parameters,
                confidence=0.98 if not missing else 0.64,
                missing_fields=missing,
                message="请依次给出课程和要永久删除的回收站内容。" if missing else "",
            )

        if "回收站" in text and re.search(r"恢复|还原", text):
            parameters = {"kind": kind}
            if quoted:
                parameters["course"] = quoted[0]
            if len(quoted) > 1:
                parameters["assets"] = quoted[1:]
            missing = [key for key in ("course", "assets") if key not in parameters]
            return CommandPlan(
                text,
                "course_assets.recycle.restore",
                parameters=parameters,
                confidence=0.98 if not missing else 0.64,
                missing_fields=missing,
                message="请依次给出课程和要恢复的回收站内容。" if missing else "",
            )

        if "回收站" in text and re.search(r"查看|列出|搜索|有哪些", text):
            parameters = {"kind": kind}
            if quoted:
                parameters["course"] = quoted[0]
            if len(quoted) > 1:
                parameters["search"] = quoted[1]
            missing = [] if "course" in parameters else ["course"]
            return CommandPlan(
                text,
                "course_assets.recycle.list",
                parameters=parameters,
                confidence=0.97 if not missing else 0.68,
                missing_fields=missing,
                message="请给出课程名称。" if missing else "",
            )

        if "云盘" in text and re.search(r"导入|添加|复制到", text):
            parameters = {"kind": kind}
            if quoted:
                parameters["course"] = quoted[0]
            if len(quoted) >= 3 and re.search(r"目录|文件夹", text):
                parameters["resources"] = quoted[1:-1]
                parameters["destination"] = quoted[-1]
            elif len(quoted) > 1:
                parameters["resources"] = quoted[1:]
            missing = [key for key in ("course", "resources") if key not in parameters]
            return CommandPlan(
                text,
                "course_assets.cloud_files.import",
                parameters=parameters,
                confidence=0.98 if not missing else 0.63,
                missing_fields=missing,
                message="请依次给出课程和一个或多个云盘文件；需要时再给出目标目录。"
                if missing
                else "",
            )

        if re.search(r"下载|保存到本地", text):
            parameters = {"kind": kind}
            if quoted:
                parameters["course"] = quoted[0]
            if len(quoted) > 1:
                parameters["asset"] = quoted[1]
            if len(quoted) > 2:
                parameters["output_path"] = quoted[2]
            missing = [key for key in ("course", "asset", "output_path") if key not in parameters]
            return CommandPlan(
                text,
                "course_assets.item.download",
                parameters=parameters,
                confidence=0.98 if not missing else 0.62,
                missing_fields=missing,
                message="请依次给出课程、文件标题或 ID、本地输出路径。" if missing else "",
            )

        if re.search(r"新建|创建|添加", text) and re.search(r"文件夹|目录", text):
            parameters = {"kind": kind}
            if quoted:
                parameters["course"] = quoted[0]
            if len(quoted) >= 3:
                parameters["parent"] = quoted[1]
                parameters["name"] = quoted[2]
            elif len(quoted) > 1:
                parameters["name"] = quoted[1]
            missing = [key for key in ("course", "name") if key not in parameters]
            return CommandPlan(
                text,
                "course_assets.folder.create",
                parameters=parameters,
                confidence=0.98 if not missing else 0.63,
                missing_fields=missing,
                message="请给出课程和新文件夹名称；需要时再给出父目录。" if missing else "",
            )

        if re.search(r"重命名|改名|修改名称", text):
            parameters = {"kind": kind}
            for key, value in zip(("course", "asset", "name"), quoted, strict=False):
                parameters[key] = value
            missing = [key for key in ("course", "asset", "name") if key not in parameters]
            return CommandPlan(
                text,
                "course_assets.item.rename",
                parameters=parameters,
                confidence=0.98 if not missing else 0.63,
                missing_fields=missing,
                message="请依次给出课程、原内容和新名称。" if missing else "",
            )

        if re.search(r"置顶|取消置顶", text):
            parameters = {"kind": kind, "top": "取消置顶" not in text}
            if quoted:
                parameters["course"] = quoted[0]
            if len(quoted) > 1:
                parameters["asset"] = quoted[1]
            missing = [key for key in ("course", "asset") if key not in parameters]
            return CommandPlan(
                text,
                "course_assets.item.top_status.update",
                parameters=parameters,
                confidence=0.98 if not missing else 0.65,
                missing_fields=missing,
                message="请依次给出课程和内容标题或 ID。" if missing else "",
            )

        if re.search(r"移动|移到|挪到", text):
            parameters = {"kind": kind}
            if quoted:
                parameters["course"] = quoted[0]
            if len(quoted) >= 3:
                parameters["assets"] = quoted[1:-1]
                parameters["destination"] = quoted[-1]
            missing = [key for key in ("course", "assets", "destination") if key not in parameters]
            return CommandPlan(
                text,
                "course_assets.items.move",
                parameters=parameters,
                confidence=0.97 if not missing else 0.62,
                missing_fields=missing,
                message="请依次给出课程、一个或多个内容和目标目录。" if missing else "",
            )

        if re.search(r"复制|克隆|创建副本", text):
            parameters = {"kind": kind}
            if quoted:
                parameters["course"] = quoted[0]
            if len(quoted) > 1:
                parameters["asset"] = quoted[1]
            missing = [key for key in ("course", "asset") if key not in parameters]
            return CommandPlan(
                text,
                "course_assets.item.copy",
                parameters=parameters,
                confidence=0.98 if not missing else 0.65,
                missing_fields=missing,
                message="请依次给出课程和要复制的内容。" if missing else "",
            )

        if re.search(r"删除|移除", text):
            parameters = {"kind": kind}
            if quoted:
                parameters["course"] = quoted[0]
            if len(quoted) > 1:
                parameters["assets"] = quoted[1:]
            missing = [key for key in ("course", "assets") if key not in parameters]
            return CommandPlan(
                text,
                "course_assets.items.delete",
                parameters=parameters,
                confidence=0.98 if not missing else 0.64,
                missing_fields=missing,
                message="请依次给出课程和要删除的一个或多个内容。" if missing else "",
            )

        if re.search(r"完整.*树|目录树|全部.*目录", text):
            parameters = {"kind": kind}
            if quoted:
                parameters["course"] = quoted[0]
            missing = [] if "course" in parameters else ["course"]
            return CommandPlan(
                text,
                "course_assets.tree.list",
                parameters=parameters,
                confidence=0.97 if not missing else 0.68,
                missing_fields=missing,
                message="请给出课程名称。" if missing else "",
            )

        if re.search(r"查看|列出|搜索|有哪些", text):
            parameters = {"kind": kind}
            if quoted:
                parameters["course"] = quoted[0]
            if len(quoted) > 1 and re.search(r"目录|文件夹", text):
                parameters["folder"] = quoted[1]
            elif len(quoted) > 1 and "搜索" in text:
                parameters["search"] = quoted[1]
            missing = [] if "course" in parameters else ["course"]
            return CommandPlan(
                text,
                "course_assets.items.list",
                parameters=parameters,
                confidence=0.97 if not missing else 0.68,
                missing_fields=missing,
                message="请给出课程名称。" if missing else "",
            )

    if re.search(r"删除|移除", text) and re.search(r"章节|子目录|课程目录", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["chapters"] = quoted[1:]
        missing = [key for key in ("course", "chapters") if key not in parameters]
        return CommandPlan(
            text,
            "chapters.delete",
            parameters=parameters,
            confidence=0.97 if not missing else 0.64,
            missing_fields=missing,
            message="请依次给出课程名称和要删除的章节标题或 ID。" if missing else "",
        )

    if re.search(r"章节|子目录|课程目录", text) and re.search(r"重命名|改名|修改名称", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["chapter"] = quoted[1]
        if len(quoted) > 2:
            parameters["title"] = quoted[2]
        missing = [key for key in ("course", "chapter", "title") if key not in parameters]
        return CommandPlan(
            text,
            "chapters.rename",
            parameters=parameters,
            confidence=0.97 if not missing else 0.63,
            missing_fields=missing,
            message="请依次给出课程、原章节和新标题。" if missing else "",
        )

    if re.search(r"章节|子目录|课程目录", text) and re.search(r"移动|移到|挪到|调整顺序", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["chapter"] = quoted[1]
        if len(quoted) > 2:
            if re.search(r"之前|前面", text):
                parameters.update({"relative_to": quoted[2], "position": "before"})
            elif re.search(r"之后|后面", text):
                parameters.update({"relative_to": quoted[2], "position": "after"})
            else:
                parameters["parent"] = quoted[2]
        missing = [key for key in ("course", "chapter") if key not in parameters]
        if "parent" not in parameters and "relative_to" not in parameters:
            missing.append("parent_or_relative_to")
        return CommandPlan(
            text,
            "chapters.move",
            parameters=parameters,
            confidence=0.96 if not missing else 0.62,
            missing_fields=missing,
            message="请依次给出课程、待移动章节和目标父章节或相邻章节。" if missing else "",
        )

    if re.search(r"章节|子目录|课程目录", text) and re.search(
        r"快速导入|按.*大纲.*导入|批量新建", text
    ):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["outline"] = quoted[1]
        missing = [key for key in ("course", "outline") if key not in parameters]
        return CommandPlan(
            text,
            "chapters.outline.import",
            parameters=parameters,
            confidence=0.95 if not missing else 0.61,
            missing_fields=missing,
            message="请依次给出课程名称和保留换行、用前导空格表示层级的目录文本。"
            if missing
            else "",
        )

    if re.search(r"新建|创建|添加", text) and re.search(r"章节|子目录|课程目录", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) >= 3 and re.search(r"下|子目录|子章节", text):
            parameters["parent"] = quoted[1]
            parameters["title"] = quoted[2]
        elif len(quoted) > 1:
            parameters["title"] = quoted[1]
        missing = [key for key in ("course", "title") if key not in parameters]
        return CommandPlan(
            text,
            "chapters.create",
            parameters=parameters,
            confidence=0.96 if not missing else 0.63,
            missing_fields=missing,
            message="请给出课程、章节标题；新建子章节时同时给出父章节。" if missing else "",
        )

    chapter_status_match = re.search(r"开放|闯关|定时|关闭|复习模式", text)
    if (
        chapter_status_match
        and re.search(r"章节|子目录", text)
        and re.search(r"设置|设为|改为|开放|关闭", text)
    ):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        remaining = quoted[1:]
        if "班级" in text and len(remaining) >= 2:
            parameters["classes"] = [remaining[-1]]
            remaining = remaining[:-1]
        if remaining:
            parameters["chapters"] = remaining
        status = (
            "time"
            if "定时" in text
            else "task"
            if "闯关" in text
            else "review"
            if "复习模式" in text
            else "close"
            if "关闭" in text
            else "open"
        )
        parameters["status"] = status
        timestamps = re.findall(r"\d{4}[.-]\d{1,2}[.-]\d{1,2}\s+\d{1,2}:\d{2}", text)
        if timestamps:
            parameters["begin"] = timestamps[0]
        if len(timestamps) > 1:
            parameters["end"] = timestamps[1]
        missing = [key for key in ("course", "chapters") if key not in parameters]
        if status == "time":
            missing.extend(key for key in ("begin", "end") if key not in parameters)
        return CommandPlan(
            text,
            "chapters.open_status.update",
            parameters=parameters,
            confidence=0.96 if not missing else 0.61,
            missing_fields=missing,
            message="请给出课程、章节、开放模式；定时开放还需开始和结束时间。" if missing else "",
        )

    if (
        re.search(r"章节|课程目录", text)
        and re.search(r"内容|页面|卡片", text)
        and re.search(r"读取|查看|显示", text)
    ):
        quoted = _extract_quoted(text)
        parameters = {"course": quoted[0]} if quoted else {}
        if len(quoted) > 1:
            parameters["chapter"] = quoted[1]
        missing = [key for key in ("course", "chapter") if key not in parameters]
        return CommandPlan(
            text,
            "chapters.cards.list",
            parameters=parameters,
            confidence=0.95 if not missing else 0.64,
            missing_fields=missing,
            message="请依次给出课程和章节标题或 ID。" if missing else "",
        )

    if re.search(r"完整章节树|完整目录树|章节编辑树|七级目录", text):
        quoted = _extract_quoted(text)
        return CommandPlan(
            text,
            "chapters.tree.list",
            parameters={"course": quoted[0]} if quoted else {},
            confidence=0.95 if quoted else 0.67,
            missing_fields=[] if quoted else ["course"],
            message="请用书名号或引号给出课程名称。" if not quoted else "",
        )

    if re.search(r"章节|课程目录", text) and re.search(r"列出|查看|显示|搜索|有哪些", text):
        quoted = _extract_quoted(text)
        parameters = {"course": quoted[0]} if quoted else {}
        if len(quoted) > 1:
            parameters["search"] = quoted[1]
        return CommandPlan(
            text,
            "chapters.list",
            parameters=parameters,
            confidence=0.94 if quoted else 0.68,
            missing_fields=[] if quoted else ["course"],
            message="请用书名号或引号给出课程名称。" if not quoted else "",
        )

    if (
        re.search(r"云盘文件夹|云盘目录", text)
        and re.search(r"导入|添加到", text)
        and re.search(r"课程资料|资料目录|资料文件夹", text)
    ):
        quoted = _extract_quoted(text)
        parameters = {"course": quoted[0]} if quoted else {}
        remaining = quoted[1:]
        if re.search(r"资料目录|课程资料文件夹", text) and len(remaining) >= 2:
            parameters["destination"] = remaining[-1]
            remaining = remaining[:-1]
        if remaining:
            parameters["resource"] = remaining[0]
        missing = [key for key in ("course", "resource") if key not in parameters]
        return CommandPlan(
            text,
            "resources.cloud_folder.import",
            parameters=parameters,
            confidence=0.97 if not missing else 0.61,
            missing_fields=missing,
            message=(
                "请按课程、一个云盘文件夹、可选资料目录的顺序给出名称或 ID。" if missing else ""
            ),
        )

    if (
        "云盘" in text
        and re.search(r"导入|添加到", text)
        and re.search(r"课程资料|资料目录|资料文件夹", text)
    ):
        quoted = _extract_quoted(text)
        parameters = {"course": quoted[0]} if quoted else {}
        remaining = quoted[1:]
        if re.search(r"资料目录|资料文件夹", text) and len(remaining) >= 2:
            parameters["destination"] = remaining[-1]
            remaining = remaining[:-1]
        if remaining:
            parameters["resources"] = remaining
        missing = [key for key in ("course", "resources") if key not in parameters]
        return CommandPlan(
            text,
            "resources.cloud_files.import",
            parameters=parameters,
            confidence=0.97 if not missing else 0.61,
            missing_fields=missing,
            message=(
                "请按课程、一个或多个云盘文件、可选资料目录的顺序给出名称或 ID。" if missing else ""
            ),
        )

    if (
        "云盘" in text
        and re.search(r"可导入|来源", text)
        and re.search(r"列出|查看|显示|搜索|有哪些|浏览", text)
    ):
        quoted = _extract_quoted(text)
        parameters = {"course": quoted[0]} if quoted else {}
        if len(quoted) > 1:
            parameters["path"] = quoted[1]
        return CommandPlan(
            text,
            "resources.cloud_sources.list",
            parameters=parameters,
            confidence=0.97 if quoted else 0.65,
            missing_fields=[] if quoted else ["course"],
            message="请先给出课程名称；需要时再给出云盘目录路径。" if not quoted else "",
        )

    if "云盘" in text and "回收站" in text and re.search(r"清空", text):
        return CommandPlan(
            text,
            "cloud_disk.recycle.empty",
            parameters={},
            confidence=0.99,
        )

    if "云盘" in text and "回收站" in text and re.search(r"永久删除|彻底删除", text):
        quoted = _extract_quoted(text)
        return CommandPlan(
            text,
            "cloud_disk.recycle.items.delete",
            parameters={"resources": quoted} if quoted else {},
            confidence=0.99 if quoted else 0.67,
            missing_fields=[] if quoted else ["resources"],
            message="请用书名号或引号给出要永久删除的回收站项目。" if not quoted else "",
        )

    if "云盘" in text and "回收站" in text and re.search(r"恢复|还原", text):
        quoted = _extract_quoted(text)
        parameters = {
            "resources": quoted,
            "conflict_policy": "replace" if "替换" in text else "keep_both",
        }
        if not quoted:
            parameters.pop("resources")
        return CommandPlan(
            text,
            "cloud_disk.recycle.restore",
            parameters=parameters,
            confidence=0.98 if quoted else 0.66,
            missing_fields=[] if quoted else ["resources"],
            message="请用书名号或引号给出要恢复的回收站项目。" if not quoted else "",
        )

    if "云盘" in text and "回收站" in text and re.search(r"列出|查看|显示|有哪些|浏览", text):
        return CommandPlan(
            text,
            "cloud_disk.recycle.list",
            parameters={},
            confidence=0.98,
        )

    if "云盘" in text and re.search(r"下载|保存到本地", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if len(quoted) >= 2:
            parameters["resources"] = quoted[:-1]
            parameters["output_path"] = quoted[-1]
        missing = [key for key in ("resources", "output_path") if key not in parameters]
        return CommandPlan(
            text,
            "cloud_disk.items.download",
            parameters=parameters,
            confidence=0.98 if not missing else 0.62,
            missing_fields=missing,
            message="请依次给出一个或多个云盘项目，以及本地输出路径。" if missing else "",
        )

    if "云盘" in text and re.search(r"新建|创建|添加", text) and re.search(r"文件夹|目录", text):
        quoted = _extract_quoted(text)
        parameters = {"shared": bool(re.search(r"共享|协作", text))}
        if len(quoted) >= 2:
            parameters.update({"parent": quoted[0], "name": quoted[1]})
        elif quoted:
            parameters["name"] = quoted[0]
        missing = [] if "name" in parameters else ["name"]
        return CommandPlan(
            text,
            "cloud_disk.folder.create",
            parameters=parameters,
            confidence=0.98 if not missing else 0.66,
            missing_fields=missing,
            message="请给出云盘新文件夹名称；需要时先给出父目录。" if missing else "",
        )

    if "云盘" in text and re.search(r"重命名|改名|修改名称", text):
        quoted = _extract_quoted(text)
        parameters = {"resource": quoted[0], "name": quoted[1]} if len(quoted) >= 2 else {}
        missing = [key for key in ("resource", "name") if key not in parameters]
        return CommandPlan(
            text,
            "cloud_disk.item.rename",
            parameters=parameters,
            confidence=0.98 if not missing else 0.64,
            missing_fields=missing,
            message="请依次给出原云盘项目名称或 ID，以及新名称。" if missing else "",
        )

    if "云盘" in text and re.search(r"移动|移到|挪到", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if len(quoted) >= 2:
            parameters["resources"] = quoted[:-1]
            parameters["destination"] = quoted[-1]
        missing = [key for key in ("resources", "destination") if key not in parameters]
        return CommandPlan(
            text,
            "cloud_disk.items.move",
            parameters=parameters,
            confidence=0.98 if not missing else 0.62,
            missing_fields=missing,
            message="请依次给出一个或多个云盘项目和目标目录。" if missing else "",
        )

    if "云盘" in text and re.search(r"置顶|取消置顶", text):
        quoted = _extract_quoted(text)
        return CommandPlan(
            text,
            "cloud_disk.item.top_status.update",
            parameters={"resource": quoted[0], "top": "取消置顶" not in text}
            if quoted
            else {"top": "取消置顶" not in text},
            confidence=0.98 if quoted else 0.66,
            missing_fields=[] if quoted else ["resource"],
            message="请用书名号或引号给出云盘项目名称或 ID。" if not quoted else "",
        )

    if "云盘" in text and re.search(r"删除|移除", text):
        quoted = _extract_quoted(text)
        parameters = {"resources": quoted} if quoted else {}
        return CommandPlan(
            text,
            "cloud_disk.items.delete",
            parameters=parameters,
            confidence=0.98 if quoted else 0.66,
            missing_fields=[] if quoted else ["resources"],
            message="请用书名号或引号给出一个或多个云盘文件名称或 ID。" if not quoted else "",
        )

    if "云盘" in text and re.search(r"详情|文件信息|对象信息", text):
        quoted = _extract_quoted(text)
        return CommandPlan(
            text,
            "cloud_disk.item.read",
            parameters={"resource": quoted[0]} if quoted else {},
            confidence=0.97 if quoted else 0.66,
            missing_fields=[] if quoted else ["resource"],
            message="请用书名号或引号给出云盘文件名称或 ID。" if not quoted else "",
        )

    if "云盘" in text and re.search(r"列出|查看|显示|搜索|有哪些|浏览", text):
        quoted = _extract_quoted(text)
        parameters = {"search": quoted[0]} if quoted and "搜索" in text else {}
        return CommandPlan(
            text,
            "cloud_disk.items.list",
            parameters=parameters,
            confidence=0.96,
        )

    if "资料" in text and "标签" in text and re.search(r"删除|移除", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["resource"] = quoted[1]
        if len(quoted) > 2:
            parameters["label"] = quoted[2]
        missing = [key for key in ("course", "resource", "label") if key not in parameters]
        return CommandPlan(
            text,
            "resources.label.delete",
            parameters=parameters,
            confidence=0.98 if not missing else 0.63,
            missing_fields=missing,
            message="请依次给出课程、资料标题或 ID、标签名称或 ID。" if missing else "",
        )

    if "资料" in text and "标签" in text and re.search(r"重命名|改名|修改名称", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["resource"] = quoted[1]
        if len(quoted) > 2:
            parameters["label"] = quoted[2]
        if len(quoted) > 3:
            parameters["name"] = quoted[3]
        missing = [key for key in ("course", "resource", "label", "name") if key not in parameters]
        return CommandPlan(
            text,
            "resources.label.rename",
            parameters=parameters,
            confidence=0.98 if not missing else 0.62,
            missing_fields=missing,
            message="请依次给出课程、资料、原标签、新标签名称。" if missing else "",
        )

    if "资料" in text and "标签" in text and re.search(r"新建|创建|添加", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["resource"] = quoted[1]
        if len(quoted) > 2:
            parameters["name"] = quoted[2]
        missing = [key for key in ("course", "resource", "name") if key not in parameters]
        return CommandPlan(
            text,
            "resources.label.create",
            parameters=parameters,
            confidence=0.98 if not missing else 0.63,
            missing_fields=missing,
            message="请依次给出课程、任一资料、要创建的标签名称。" if missing else "",
        )

    if (
        "资料" in text
        and "标签" in text
        and (
            re.search(r"清除|清空", text)
            or re.search(r"设置|替换|更新|打标签|打上标签|标签.*(?:改|设)为", text)
        )
    ):
        quoted = _extract_quoted(text)
        parameters = {}
        clearing = bool(re.search(r"清除|清空", text))
        if clearing:
            if quoted:
                parameters["course"] = quoted[0]
            if len(quoted) > 1:
                parameters["resources"] = quoted[1:]
            parameters["labels"] = []
        else:
            marker = re.search(
                r"(?:设置|替换|更新|打上?|添加)(?:完整)?(?:资料)?标签(?:集合)?(?:为|成)?"
                r"|(?:完整)?(?:资料)?标签(?:集合)?(?:设置|替换|更新|改|设)(?:为|成)",
                text,
            )
            before = _extract_quoted(text[: marker.start()]) if marker else quoted[:2]
            after = _extract_quoted(text[marker.end() :]) if marker else quoted[2:]
            if before:
                parameters["course"] = before[0]
            if len(before) > 1:
                parameters["resources"] = before[1:]
            if after:
                parameters["labels"] = after
        missing = [key for key in ("course", "resources") if key not in parameters]
        if not clearing and "labels" not in parameters:
            missing.append("labels")
        return CommandPlan(
            text,
            "resources.labels.update",
            parameters=parameters,
            confidence=0.97 if not missing else 0.6,
            missing_fields=missing,
            message="请给出课程、一个或多个资料，以及完整标签集合；清除时无需给标签。"
            if missing
            else "",
        )

    if "资料" in text and "标签" in text and re.search(r"查看|列出|有哪些|当前", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["resource"] = quoted[1]
        missing = [key for key in ("course", "resource") if key not in parameters]
        return CommandPlan(
            text,
            "resources.labels.list",
            parameters=parameters,
            confidence=0.98 if not missing else 0.65,
            missing_fields=missing,
            message="请依次给出课程和资料标题或 ID。" if missing else "",
        )

    if re.search(r"完整资料树|资料目录树|全部资料树", text):
        quoted = _extract_quoted(text)
        return CommandPlan(
            text,
            "resources.tree.list",
            parameters={"course": quoted[0]} if quoted else {},
            confidence=0.96 if quoted else 0.66,
            missing_fields=[] if quoted else ["course"],
            message="请用书名号或引号给出课程名称。" if not quoted else "",
        )

    if (
        re.search(r"下载|保存到本地", text)
        and re.search(r"资料|课程文件", text)
        and not re.search(r"允许|禁止|关闭|开启|谁下载|下载者|下载记录", text)
    ):
        quoted = _extract_quoted(text)
        bulk_intent = bool(re.search(r"批量|多个|这些|全部|所有", text))
        single_intent = not bulk_intent and (
            len(quoted) == 3 or bool(re.search(r"单个|一个|这份|这个|该资料|该文件|资料文件", text))
        )
        if single_intent:
            parameters = {}
            if quoted:
                parameters["course"] = quoted[0]
            if len(quoted) >= 2:
                parameters["resource"] = quoted[1]
            if len(quoted) >= 3:
                parameters["output_path"] = quoted[2]
            if "覆盖" in text:
                parameters["overwrite"] = True
            missing = [
                key for key in ("course", "resource", "output_path") if key not in parameters
            ]
            return CommandPlan(
                text,
                "resources.file.download",
                parameters=parameters,
                confidence=0.98 if not missing else 0.64,
                missing_fields=missing,
                message="请依次给出课程、资料标题或 ID、本地输出路径。" if missing else "",
            )
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 2:
            parameters["resources"] = quoted[1:-1]
            parameters["output_path"] = quoted[-1]
        if "覆盖" in text:
            parameters["overwrite"] = True
        missing = [key for key in ("course", "resources", "output_path") if key not in parameters]
        return CommandPlan(
            text,
            "resources.items.download",
            parameters=parameters,
            confidence=0.97 if not missing else 0.61,
            missing_fields=missing,
            message="请依次给出课程、一个或多个资料标题或 ID、本地输出路径。" if missing else "",
        )

    if (
        re.search(r"新建|创建|添加", text)
        and re.search(r"资料.*文件夹|资料目录", text)
        and not re.search(r"网址|链接", text)
    ):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) >= 3:
            parameters["parent"] = quoted[1]
            parameters["name"] = quoted[2]
        elif len(quoted) > 1:
            parameters["name"] = quoted[1]
        missing = [key for key in ("course", "name") if key not in parameters]
        return CommandPlan(
            text,
            "resources.folder.create",
            parameters=parameters,
            confidence=0.97 if not missing else 0.62,
            missing_fields=missing,
            message="请给出课程、新文件夹名称；需要时同时给出父目录。" if missing else "",
        )

    if re.search(r"资料|课程文件", text) and re.search(r"重命名|改名|修改名称", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["resource"] = quoted[1]
        if len(quoted) > 2:
            parameters["name"] = quoted[2]
        missing = [key for key in ("course", "resource", "name") if key not in parameters]
        return CommandPlan(
            text,
            "resources.rename",
            parameters=parameters,
            confidence=0.97 if not missing else 0.62,
            missing_fields=missing,
            message="请依次给出课程、原资料标题或 ID、新名称。" if missing else "",
        )

    if re.search(r"资料|课程文件", text) and re.search(r"移动|移到|挪到", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) >= 3:
            parameters["resources"] = quoted[1:-1]
            parameters["destination"] = quoted[-1]
        missing = [key for key in ("course", "resources", "destination") if key not in parameters]
        return CommandPlan(
            text,
            "resources.move",
            parameters=parameters,
            confidence=0.96 if not missing else 0.61,
            missing_fields=missing,
            message="请依次给出课程、一个或多个资料、目标目录。" if missing else "",
        )

    if re.search(r"资料|课程文件", text) and re.search(r"排序|调整顺序|顺序设为", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        remaining = quoted[1:]
        if re.search(r"资料目录|文件夹", text) and len(remaining) >= 2:
            parameters["folder"] = remaining[0]
            remaining = remaining[1:]
        if remaining:
            parameters["resources"] = remaining
        missing = [key for key in ("course", "resources") if key not in parameters]
        return CommandPlan(
            text,
            "resources.reorder",
            parameters=parameters,
            confidence=0.95 if not missing else 0.61,
            missing_fields=missing,
            message="请给出课程、所在目录和该目录全部资料的新顺序。" if missing else "",
        )

    if re.search(r"资料|课程文件", text) and re.search(r"置顶|取消置顶", text):
        quoted = _extract_quoted(text)
        parameters = {"course": quoted[0]} if quoted else {}
        if len(quoted) > 1:
            parameters["resource"] = quoted[1]
        parameters["top"] = "取消置顶" not in text
        missing = [key for key in ("course", "resource") if key not in parameters]
        return CommandPlan(
            text,
            "resources.top_status.update",
            parameters=parameters,
            confidence=0.97 if not missing else 0.63,
            missing_fields=missing,
            message="请依次给出课程和资料标题或 ID。" if missing else "",
        )

    if (
        re.search(r"资料|课程文件", text)
        and "云盘" in text
        and re.search(r"保存到|复制到|添加到", text)
        and not re.search(r"从云盘|云盘导入", text)
    ):
        quoted = _extract_quoted(text)
        parameters = {"course": quoted[0]} if quoted else {}
        if len(quoted) > 1:
            parameters["resource"] = quoted[1]
        if len(quoted) > 2:
            parameters["destination"] = quoted[2]
        missing = [key for key in ("course", "resource") if key not in parameters]
        return CommandPlan(
            text,
            "resources.cloud_disk.copy",
            parameters=parameters,
            confidence=0.97 if not missing else 0.63,
            missing_fields=missing,
            message="请依次给出课程、资料标题或 ID；需要时再给出云盘目录。" if missing else "",
        )

    if (
        re.search(r"资料|课程文件", text)
        and re.search(r"复制|创建副本", text)
        and "其他课程" not in text
    ):
        quoted = _extract_quoted(text)
        parameters = {"course": quoted[0]} if quoted else {}
        if len(quoted) > 1:
            parameters["resource"] = quoted[1]
        missing = [key for key in ("course", "resource") if key not in parameters]
        return CommandPlan(
            text,
            "resources.copy",
            parameters=parameters,
            confidence=0.97 if not missing else 0.63,
            missing_fields=missing,
            message="请依次给出课程和要复制的资料标题或 ID。" if missing else "",
        )

    if re.search(r"删除|移除", text) and re.search(r"资料|课程文件", text):
        quoted = _extract_quoted(text)
        parameters = {"course": quoted[0], "resources": quoted[1:]} if quoted else {}
        if not parameters.get("resources"):
            parameters.pop("resources", None)
        missing = [key for key in ("course", "resources") if key not in parameters]
        return CommandPlan(
            text,
            "resources.delete",
            parameters=parameters,
            confidence=0.97 if not missing else 0.62,
            missing_fields=missing,
            message="请依次给出课程和要删除的一个或多个资料标题或 ID。" if missing else "",
        )

    if re.search(r"添加|新建|创建", text) and re.search(r"网址资料|链接资料|资料链接", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) >= 4:
            parameters.update({"parent": quoted[1], "name": quoted[2], "url": quoted[3]})
        elif len(quoted) >= 3:
            parameters.update({"name": quoted[1], "url": quoted[2]})
        missing = [key for key in ("course", "name", "url") if key not in parameters]
        return CommandPlan(
            text,
            "resources.link.create",
            parameters=parameters,
            confidence=0.97 if not missing else 0.61,
            missing_fields=missing,
            message="请给出课程、资料名称、网址；需要时同时给出父目录。" if missing else "",
        )

    if re.search(r"上传", text) and re.search(r"资料|课程文件", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["file_path"] = quoted[1]
        if len(quoted) > 2:
            parameters["parent"] = quoted[2]
        missing = [key for key in ("course", "file_path") if key not in parameters]
        return CommandPlan(
            text,
            "resources.file.upload",
            parameters=parameters,
            confidence=0.97 if not missing else 0.62,
            missing_fields=missing,
            message="请给出课程、本地文件绝对路径；需要时同时给出目标目录。" if missing else "",
        )

    if re.search(r"允许|禁止|关闭|开启", text) and re.search(r"资料.*下载|下载.*资料", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["resources"] = quoted[1:]
        parameters["allow_download"] = not bool(re.search(r"禁止|关闭|不允许", text))
        missing = [key for key in ("course", "resources") if key not in parameters]
        return CommandPlan(
            text,
            "resources.download_permission.update",
            parameters=parameters,
            confidence=0.97 if not missing else 0.62,
            missing_fields=missing,
            message="请给出课程和一个或多个资料标题或 ID。" if missing else "",
        )

    if re.search(r"设置|修改", text) and re.search(r"资料.*可见|资料.*权限", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["folder"] = quoted[1]
        if "全部班级" in text:
            parameters["mode"] = "all_classes"
        elif re.search(r"不对班级|无班级|所有班级不可见", text):
            parameters["mode"] = "no_classes"
        elif "指定班级" in text:
            parameters["mode"] = "selected_classes"
            if len(quoted) > 2:
                parameters["classes"] = quoted[2:]
        missing = [key for key in ("course", "folder", "mode") if key not in parameters]
        if parameters.get("mode") == "selected_classes" and not parameters.get("classes"):
            missing.append("classes")
        return CommandPlan(
            text,
            "resources.folder.visibility.update",
            parameters=parameters,
            confidence=0.96 if not missing else 0.61,
            missing_fields=missing,
            message="请给出课程、资料文件夹和全部/指定/无班级可见范围。" if missing else "",
        )

    if re.search(r"查看|读取|显示", text) and re.search(r"资料.*可见|资料.*权限", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["folder"] = quoted[1]
        missing = [key for key in ("course", "folder") if key not in parameters]
        return CommandPlan(
            text,
            "resources.folder.visibility.read",
            parameters=parameters,
            confidence=0.96 if not missing else 0.63,
            missing_fields=missing,
            message="请依次给出课程和资料文件夹。" if missing else "",
        )

    if re.search(r"资料", text) and re.search(r"谁看了|阅读者|未读名单|已读名单", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["resource"] = quoted[1]
        if len(quoted) > 2 and "班级" in text:
            parameters["reader_class"] = quoted[2]
        missing = [key for key in ("course", "resource") if key not in parameters]
        return CommandPlan(
            text,
            "resources.readers.list",
            parameters=parameters,
            confidence=0.97 if not missing else 0.63,
            missing_fields=missing,
            message="请依次给出课程和资料标题或 ID。" if missing else "",
        )

    if re.search(r"资料", text) and re.search(r"谁下载了|下载者|下载记录", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["resource"] = quoted[1]
        missing = [key for key in ("course", "resource") if key not in parameters]
        return CommandPlan(
            text,
            "resources.downloaders.list",
            parameters=parameters,
            confidence=0.97 if not missing else 0.63,
            missing_fields=missing,
            message="请依次给出课程和资料标题或 ID。" if missing else "",
        )

    if re.search(r"列出|查看|有哪些", text) and re.search(r"可导入.*课程|资料来源课程", text):
        quoted = _extract_quoted(text)
        return CommandPlan(
            text,
            "resources.import_courses.list",
            parameters={"course": quoted[0]} if quoted else {},
            confidence=0.96 if quoted else 0.65,
            missing_fields=[] if quoted else ["course"],
            message="请给出目标课程名称。" if not quoted else "",
        )

    if re.search(r"列出|查看|浏览|搜索", text) and re.search(r"可导入资料|来源课程资料", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["source_course"] = quoted[1]
        if len(quoted) > 2:
            parameters["folder_id"] = quoted[2]
        missing = [key for key in ("course", "source_course") if key not in parameters]
        return CommandPlan(
            text,
            "resources.import_items.list",
            parameters=parameters,
            confidence=0.96 if not missing else 0.62,
            missing_fields=missing,
            message="请依次给出目标课程和来源课程。" if missing else "",
        )

    if re.search(r"导入|复制", text) and re.search(r"课程资料|资料", text) and "其他课程" in text:
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["source_course"] = quoted[1]
        remaining = quoted[2:]
        if re.search(r"目标目录|导入到|复制到", text) and len(remaining) >= 2:
            parameters["destination"] = remaining[-1]
            remaining = remaining[:-1]
        if remaining:
            parameters["resources"] = remaining
        missing = [key for key in ("course", "source_course", "resources") if key not in parameters]
        return CommandPlan(
            text,
            "resources.import.execute",
            parameters=parameters,
            confidence=0.96 if not missing else 0.60,
            missing_fields=missing,
            message="请给出目标课程、来源课程、资料和可选目标目录。" if missing else "",
        )

    if re.search(r"分享|分享链接", text) and re.search(r"资料|课程文件", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["resource"] = quoted[1]
        missing = [key for key in ("course", "resource") if key not in parameters]
        return CommandPlan(
            text,
            "resources.share_link.create",
            parameters=parameters,
            confidence=0.96 if not missing else 0.62,
            missing_fields=missing,
            message="请依次给出课程和资料标题或 ID。" if missing else "",
        )

    if re.search(r"资料|课程文件", text) and re.search(r"列出|查看|显示|浏览|搜索|有哪些", text):
        quoted = _extract_quoted(text)
        parameters = {"course": quoted[0]} if quoted else {}
        if len(quoted) > 1:
            parameters["folder"] = quoted[1]
        return CommandPlan(
            text,
            "resources.list",
            parameters=parameters,
            confidence=0.94 if quoted else 0.68,
            missing_fields=[] if quoted else ["course"],
            message="请用书名号或引号给出课程名称。" if not quoted else "",
        )

    if re.search(r"删除|清除", text) and re.search(r"通知|公告", text) and "草稿" in text:
        parameters: dict[str, str | int | bool] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) >= 2:
            parameters["draft"] = quoted[-1]
        missing = [key for key in ("course", "draft") if key not in parameters]
        return CommandPlan(
            text,
            "notices.draft.delete",
            parameters=parameters,
            confidence=0.97 if not missing else 0.65,
            missing_fields=missing,
            message="请给出课程和通知草稿标题或 ID。" if missing else "",
        )

    if re.search(r"定时(?:发送|发布)|预约(?:发送|发布)", text) and re.search(r"通知|公告", text):
        parameters: dict[str, str | int | bool | list[str]] = {}
        if len(quoted) >= 5:
            parameters.update(
                {
                    "course": quoted[0],
                    "clazz": quoted[1],
                    "recipient_classes": [quoted[1]],
                    "title": quoted[2],
                    "content": quoted[3],
                    "send_at": quoted[4],
                }
            )
        elif len(quoted) >= 4:
            parameters.update(
                {
                    "course": quoted[0],
                    "title": quoted[1],
                    "content": quoted[2],
                    "send_at": quoted[3],
                }
            )
        missing = [
            key for key in ("course", "title", "content", "send_at") if key not in parameters
        ]
        return CommandPlan(
            text,
            "notices.schedule",
            parameters=parameters,
            confidence=0.97 if not missing else 0.63,
            missing_fields=missing,
            message="请给出课程、通知标题、正文和定时发送时间。" if missing else "",
        )

    if re.search(r"保存|新建|修改|编辑", text) and re.search(r"通知|公告", text) and "草稿" in text:
        parameters: dict[str, str | int | bool | list[str]] = {}
        is_update = bool(re.search(r"修改|编辑", text))
        if is_update and len(quoted) >= 4:
            parameters.update(
                {
                    "course": quoted[0],
                    "draft": quoted[1],
                    "title": quoted[2],
                    "content": quoted[3],
                }
            )
        elif len(quoted) >= 4:
            parameters.update(
                {
                    "course": quoted[0],
                    "clazz": quoted[1],
                    "recipient_classes": [quoted[1]],
                    "title": quoted[2],
                    "content": quoted[3],
                }
            )
        elif len(quoted) >= 3:
            parameters.update(
                {
                    "course": quoted[0],
                    "title": quoted[1],
                    "content": quoted[2],
                }
            )
        missing = [key for key in ("course", "title", "content") if key not in parameters]
        return CommandPlan(
            text,
            "notices.draft.save",
            parameters=parameters,
            confidence=0.97 if not missing else 0.63,
            missing_fields=missing,
            message="请给出课程、草稿标题和正文。" if missing else "",
        )

    if (
        re.search(r"通知|公告", text)
        and "草稿" in text
        and re.search(r"列出|查看|显示|有哪些|搜索", text)
    ):
        parameters = {"course": quoted[0]} if quoted else {}
        if len(quoted) > 1:
            parameters["search"] = quoted[1]
        return CommandPlan(
            text,
            "notices.drafts.list",
            parameters=parameters,
            confidence=0.96 if quoted else 0.68,
            missing_fields=[] if quoted else ["course"],
            message="请用书名号或引号给出课程名称。" if not quoted else "",
        )

    if re.search(r"删除", text) and re.search(r"通知|公告", text):
        parameters: dict[str, str | int | bool] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) >= 3:
            parameters["clazz"] = quoted[1]
            parameters["notice"] = quoted[2]
        elif len(quoted) >= 2:
            parameters["notice"] = quoted[1]
        missing = [key for key in ("course", "notice") if key not in parameters]
        return CommandPlan(
            text,
            "notices.delete",
            parameters=parameters,
            confidence=0.96 if not missing else 0.64,
            missing_fields=missing,
            message="请给出课程和通知标题或 ID。" if missing else "",
        )

    if re.search(r"撤回", text) and re.search(r"通知|公告", text):
        parameters: dict[str, str | int | bool] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) >= 3:
            parameters["clazz"] = quoted[1]
            parameters["notice"] = quoted[2]
        elif len(quoted) >= 2:
            parameters["notice"] = quoted[1]
        missing = [key for key in ("course", "notice") if key not in parameters]
        return CommandPlan(
            text,
            "notices.recall",
            parameters=parameters,
            confidence=0.96 if not missing else 0.64,
            missing_fields=missing,
            message="请给出课程和通知标题或 ID。" if missing else "",
        )

    if re.search(r"置顶|取消置顶", text) and re.search(r"通知|公告", text):
        parameters: dict[str, str | int | bool] = {"top": "取消置顶" not in text}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) >= 3:
            parameters["clazz"] = quoted[1]
            parameters["notice"] = quoted[2]
        elif len(quoted) >= 2:
            parameters["notice"] = quoted[1]
        missing = [key for key in ("course", "notice") if key not in parameters]
        return CommandPlan(
            text,
            "notices.top.set",
            parameters=parameters,
            confidence=0.96 if not missing else 0.64,
            missing_fields=missing,
            message="请给出课程和通知标题或 ID。" if missing else "",
        )

    if re.search(r"修改|编辑", text) and re.search(r"通知|公告", text):
        parameters: dict[str, str | int | bool] = {}
        if len(quoted) >= 5:
            parameters.update(
                {
                    "course": quoted[0],
                    "clazz": quoted[1],
                    "notice": quoted[2],
                    "title": quoted[3],
                    "content": quoted[4],
                }
            )
        elif len(quoted) >= 4:
            parameters.update(
                {
                    "course": quoted[0],
                    "notice": quoted[1],
                    "title": quoted[2],
                    "content": quoted[3],
                }
            )
        missing = [key for key in ("course", "notice", "title", "content") if key not in parameters]
        return CommandPlan(
            text,
            "notices.edit",
            parameters=parameters,
            confidence=0.96 if not missing else 0.62,
            missing_fields=missing,
            message="请给出课程、原通知、新标题和新正文。" if missing else "",
        )

    if re.search(r"发送|发布|新建", text) and re.search(r"通知|公告", text):
        parameters: dict[str, str | int | bool | list[str]] = {}
        if len(quoted) >= 4:
            parameters.update(
                {
                    "course": quoted[0],
                    "clazz": quoted[1],
                    "recipient_classes": [quoted[1]],
                    "title": quoted[2],
                    "content": quoted[3],
                }
            )
        elif len(quoted) >= 3:
            parameters.update(
                {
                    "course": quoted[0],
                    "title": quoted[1],
                    "content": quoted[2],
                }
            )
        missing = [key for key in ("course", "title", "content") if key not in parameters]
        return CommandPlan(
            text,
            "notices.send",
            parameters=parameters,
            confidence=0.96 if not missing else 0.62,
            missing_fields=missing,
            message="请给出课程、通知标题和正文。" if missing else "",
        )

    if re.search(r"通知|公告", text) and re.search(r"列出|查看|显示|有哪些|搜索", text):
        quoted = _extract_quoted(text)
        parameters = {"course": quoted[0]} if quoted else {}
        if len(quoted) > 1:
            parameters["search"] = quoted[1]
        return CommandPlan(
            text,
            "notices.list",
            parameters=parameters,
            confidence=0.94 if quoted else 0.68,
            missing_fields=[] if quoted else ["course"],
            message="请用书名号或引号给出课程名称。" if not quoted else "",
        )

    exam_folder_reference = "试卷" in text and re.search(r"文件夹|目录", text)

    if exam_folder_reference and re.search(r"重命名|改名|修改名称", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int] = {}
        for key, value in zip(("course", "folder", "title"), quoted, strict=False):
            parameters[key] = value
        missing = [key for key in ("course", "folder", "title") if key not in parameters]
        return CommandPlan(
            text,
            "exam.paper_folder.rename",
            parameters=parameters,
            confidence=0.96 if not missing else 0.65,
            missing_fields=missing,
            message="请依次给出课程、原文件夹标题或 ID 和新标题。" if missing else "",
        )

    if exam_folder_reference and re.search(r"删除|移入回收站", text):
        quoted = _extract_quoted(text)
        parameters = {}
        for key, value in zip(("course", "folder"), quoted, strict=False):
            parameters[key] = value
        missing = [key for key in ("course", "folder") if key not in parameters]
        return CommandPlan(
            text,
            "exam.paper_folder.delete",
            parameters=parameters,
            confidence=0.97 if not missing else 0.65,
            missing_fields=missing,
            message="请依次给出课程和要移入回收站的试卷库文件夹。" if missing else "",
        )

    if exam_folder_reference and "移动" in text:
        quoted = _extract_quoted(text)
        parameters = {}
        for key, value in zip(("course", "folder", "target_directory_id"), quoted, strict=False):
            parameters[key] = value
        missing = [
            key for key in ("course", "folder", "target_directory_id") if key not in parameters
        ]
        return CommandPlan(
            text,
            "exam.paper_folder.move",
            parameters=parameters,
            confidence=0.95 if not missing else 0.64,
            missing_fields=missing,
            message="请依次给出课程、要移动的文件夹和目标文件夹标题或 ID。" if missing else "",
        )

    if exam_folder_reference and re.search(r"新建|创建|添加", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["title"] = quoted[1]
        missing = [key for key in ("course", "title") if key not in parameters]
        return CommandPlan(
            text,
            "exam.paper_folder.create",
            parameters=parameters,
            confidence=0.96 if not missing else 0.65,
            missing_fields=missing,
            message="请依次给出课程和新试卷库文件夹标题。" if missing else "",
        )

    exam_question_type_reference = bool(
        "试卷" in text and "题型" in text and "题型归类" not in text
    )
    if exam_question_type_reference:
        type_match = re.search(
            r"题型\s*(?:为|是|[:：])?\s*[《“\"']([^》”\"']+)[》”\"']",
            text,
        ) or re.search(r"[《“\"']([^》”\"']+)[》”\"']\s*题型", text)
        type_query = type_match.group(1) if type_match else _homework_question_type_from_text(text)

        if re.search(r"删除|移除|清除", text):
            quoted = _extract_quoted(text)
            parameters: dict[str, object] = {}
            if quoted:
                parameters["course"] = quoted[0]
            if len(quoted) > 1:
                parameters["paper"] = quoted[1]
            if type_query:
                parameters["question_type"] = type_query
            missing = [key for key in ("course", "paper", "question_type") if key not in parameters]
            return CommandPlan(
                text,
                "exam.question_type.delete",
                parameters=parameters,
                confidence=0.97 if not missing else 0.64,
                missing_fields=missing,
                message="请依次给出课程、试卷以及要删除的题型。" if missing else "",
            )

        if re.search(r"移动|移到|移至|调到|调整.*顺序", text):
            quoted = _extract_quoted(text)
            parameters: dict[str, object] = {}
            if quoted:
                parameters["course"] = quoted[0]
            if len(quoted) > 1:
                parameters["paper"] = quoted[1]
            if type_query:
                parameters["question_type"] = type_query
            position_match = re.search(
                r"(?:移动|移|调(?:整)?)(?:到|至)\s*第?\s*(\d+)\s*(?:位|个)?",
                text,
            )
            if position_match:
                parameters["target_position"] = int(position_match.group(1))
            missing = [
                key
                for key in ("course", "paper", "question_type", "target_position")
                if key not in parameters
            ]
            return CommandPlan(
                text,
                "exam.question_type.move",
                parameters=parameters,
                confidence=0.96 if not missing else 0.63,
                missing_fields=missing,
                message="请给出课程、试卷、题型和目标位置。" if missing else "",
            )

        if re.search(r"修改|更新|编辑|设置|改为|设为", text) and re.search(
            r"题型说明|题型总分|总分", text
        ):
            quoted = _extract_quoted(text)
            parameters: dict[str, object] = {}
            if quoted:
                parameters["course"] = quoted[0]
            if len(quoted) > 1:
                parameters["paper"] = quoted[1]
            if type_query:
                parameters["question_type"] = type_query
            description_match = re.search(
                r"题型说明\s*(?:修改为|更新为|编辑为|设置为|改为|设为|为|[:：])?\s*"
                r"[《“\"']([^》”\"']*)[》”\"']",
                text,
            )
            if description_match:
                parameters["description"] = description_match.group(1)
            total_score_match = re.search(
                r"(?:题型)?总分\s*(?:修改为|更新为|设置为|改为|设为|为|[:：])?\s*"
                r"(\d+(?:\.\d+)?)",
                text,
            )
            if total_score_match:
                parameters["total_score"] = float(total_score_match.group(1))
            missing = [key for key in ("course", "paper", "question_type") if key not in parameters]
            if not {"description", "total_score"}.intersection(parameters):
                missing.append("changed_field")
            return CommandPlan(
                text,
                "exam.question_type.update",
                parameters=parameters,
                confidence=0.95 if not missing else 0.62,
                missing_fields=missing,
                message="请给出课程、试卷、题型以及新的题型说明或总分。" if missing else "",
            )

    refers_to_exam_question = bool(
        "试卷" in text
        and "答卷" not in text
        and (
            re.search(r"试卷.*(?:题目|试题|第\s*\d+\s*题)", text)
            or re.search(r"(?:题目|试题|第\s*\d+\s*题).*试卷", text)
            or (
                _homework_question_type_from_text(text)
                and re.search(r"新增|添加|加入|加一道|出一道", text)
            )
        )
    )

    if refers_to_exam_question and re.search(r"移动|移到|移至|调到|调整.*顺序", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["paper"] = quoted[1]
        if question_reference:
            parameters["question"] = question_reference.group(1)
        elif len(quoted) > 2:
            parameters["question"] = quoted[2]
        position_match = re.search(
            r"(?:移动|移|调(?:整)?)(?:到|至)\s*第?\s*(\d+)\s*(?:题|位|个)?",
            text,
        )
        if position_match:
            parameters["target_position"] = int(position_match.group(1))
        missing = [
            key
            for key in ("course", "paper", "question", "target_position")
            if key not in parameters
        ]
        return CommandPlan(
            text,
            "exam.question.move",
            parameters=parameters,
            confidence=0.96 if not missing else 0.63,
            missing_fields=missing,
            message="请给出课程、试卷、题目和目标位置。" if missing else "",
        )

    if refers_to_exam_question and re.search(r"删除|移除|清除", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["paper"] = quoted[1]
        if question_reference:
            parameters["question"] = question_reference.group(1)
        elif len(quoted) > 2:
            parameters["question"] = quoted[2]
        missing = [key for key in ("course", "paper", "question") if key not in parameters]
        return CommandPlan(
            text,
            "exam.question.delete",
            parameters=parameters,
            confidence=0.97 if not missing else 0.65,
            missing_fields=missing,
            message="请依次给出课程、试卷以及题号或题目 ID。" if missing else "",
        )

    if refers_to_exam_question and re.search(r"修改|更新|编辑|改为", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["paper"] = quoted[1]
        if question_reference:
            parameters["question"] = question_reference.group(1)
            content_candidates = quoted[2:]
        elif len(quoted) > 2:
            parameters["question"] = quoted[2]
            content_candidates = quoted[3:]
        else:
            content_candidates = []
        if re.search(r"题干|题目内容", text) and content_candidates:
            parameters["stem"] = content_candidates[0]
        options = _labeled_question_options(text)
        if options:
            parameters["options"] = options
        correct_match = re.search(
            r"(?:正确答案|答案)\s*(?:改为|设为|为|是|[:：])?\s*"
            r"([A-Z](?:\s*[,，、;；]\s*[A-Z])*)",
            text,
            flags=re.IGNORECASE,
        )
        if correct_match:
            parameters["correct_answer"] = correct_match.group(1)
        boolean_match = re.search(
            r"(?:正确答案|答案)\s*(?:改为|设为|为|是|[:：])?\s*"
            r"(正确|错误|对|错|true|false)",
            text,
            flags=re.IGNORECASE,
        )
        if boolean_match:
            parameters["answer"] = boolean_match.group(1)
        reference_answer_match = re.search(
            r"(?:参考答案|答案内容)[^《“\"']*[《“\"']([^》”\"']*)[》”\"']",
            text,
        )
        if reference_answer_match:
            parameters["answer"] = reference_answer_match.group(1)
        blank_answers = [
            match.group(1)
            for match in re.finditer(
                r"(?:第?\s*\d+\s*空|空\s*\d+)\s*(?:改为|设为|为|是|[=:：])?\s*"
                r"[《“\"']([^》”\"']+)[》”\"']",
                text,
            )
        ]
        if blank_answers:
            parameters["answers"] = blank_answers
        score_match = re.search(r"(?:分值|分数)\s*(?:改为|设为|为|[:：])?\s*(\d+(?:\.\d+)?)", text)
        if score_match:
            parameters["score"] = float(score_match.group(1))
        difficulty_match = re.search(r"难度\s*(?:改为|设为|为|[:：])?\s*(0\.\d|1(?:\.0)?)", text)
        if difficulty_match:
            parameters["difficulty"] = float(difficulty_match.group(1))
        analysis_match = re.search(r"(?:解析|答案解析)[^《“\"']*[《“\"']([^》”\"']*)[》”\"']", text)
        if analysis_match:
            parameters["analysis"] = analysis_match.group(1)
        missing = [key for key in ("course", "paper", "question") if key not in parameters]
        changed_fields = {
            "stem",
            "options",
            "correct_answer",
            "answers",
            "answer",
            "score",
            "difficulty",
            "analysis",
        }
        if not changed_fields.intersection(parameters):
            missing.append("changed_field")
        return CommandPlan(
            text,
            "exam.question.update",
            parameters=parameters,
            confidence=0.95 if not missing else 0.62,
            missing_fields=missing,
            message="请给出课程、试卷、题目以及至少一个要修改的字段。" if missing else "",
        )

    exam_question_type = _homework_question_type_from_text(text)
    if (
        refers_to_exam_question
        and exam_question_type
        and re.search(r"添加|新增|加入|加一道|出一道", text)
    ):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {"question_type": exam_question_type}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["paper"] = quoted[1]
        if len(quoted) > 2:
            parameters["stem"] = quoted[2]
        options = _labeled_question_options(text)
        if options:
            parameters["options"] = options
        correct_match = re.search(
            r"(?:正确答案|答案)\s*(?:为|是|[:：])?\s*"
            r"([A-Z](?:\s*[,，、;；]\s*[A-Z])*)",
            text,
            flags=re.IGNORECASE,
        )
        if correct_match:
            parameters["correct_answer"] = correct_match.group(1)
        blank_answers = [
            match.group(1)
            for match in re.finditer(
                r"(?:第?\s*\d+\s*空|空\s*\d+)\s*(?:为|是|[=:：])?\s*"
                r"[《“\"']([^》”\"']+)[》”\"']",
                text,
            )
        ]
        if blank_answers:
            parameters["answers"] = blank_answers
        reference_answer_match = re.search(
            r"(?:参考答案|答案内容)[^《“\"']*[《“\"']([^》”\"']*)[》”\"']",
            text,
        )
        if reference_answer_match:
            parameters["answer"] = reference_answer_match.group(1)
        boolean_match = re.search(
            r"(?:正确答案|答案)\s*(?:为|是|[:：])?\s*(正确|错误|对|错|true|false)",
            text,
            flags=re.IGNORECASE,
        )
        if boolean_match:
            parameters["answer"] = boolean_match.group(1)
        score_match = re.search(r"(?:分值|分数)\s*(?:为|是|[:：])?\s*(\d+(?:\.\d+)?)", text)
        parameters["score"] = float(score_match.group(1)) if score_match else 5
        difficulty_match = re.search(r"难度\s*(?:为|是|[:：])?\s*(0\.\d|1(?:\.0)?)", text)
        parameters["difficulty"] = float(difficulty_match.group(1)) if difficulty_match else 0.8
        analysis_match = re.search(r"(?:解析|答案解析)[^《“\"']*[《“\"']([^》”\"']*)[》”\"']", text)
        if analysis_match:
            parameters["analysis"] = analysis_match.group(1)
        missing = [key for key in ("course", "paper", "stem") if key not in parameters]
        if exam_question_type in {"single_choice", "multiple_choice"}:
            missing.extend(key for key in ("options", "correct_answer") if key not in parameters)
        if exam_question_type == "fill_blank" and "answers" not in parameters:
            missing.append("answers")
        if exam_question_type == "true_false" and "answer" not in parameters:
            missing.append("answer")
        return CommandPlan(
            text,
            "exam.question.add",
            parameters=parameters,
            confidence=0.95 if not missing else 0.61,
            missing_fields=missing,
            message="请给出课程、试卷、题型所需题干、选项和答案。" if missing else "",
        )

    exam_setting_reference = bool(
        "试卷" in text
        and re.search(r"难度|题目序号|题号|题型归类|小题.*编号|试卷设置|编辑设置", text)
    )
    if exam_setting_reference and re.search(
        r"^设置|修改|设为|改为|将.*(?:难度|题号|题型归类|小题)|把.*(?:难度|题号|题型归类|小题)",
        text,
    ):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["paper"] = quoted[1]
        difficulty_match = re.search(
            r"难度\s*(?:设置为|设为|改为|为|是|[:：])?\s*(易|中|难|简单|中等|困难)", text
        )
        if difficulty_match:
            parameters["difficulty"] = difficulty_match.group(1)
        if re.search(r"按题型编号", text):
            parameters["numbering"] = "by_type"
        elif re.search(r"连续编号", text):
            parameters["numbering"] = "continuous"
        if re.search(r"不按题型归类|题型不归类", text):
            parameters["grouping"] = "ungrouped"
        elif re.search(r"按题型归类", text):
            parameters["grouping"] = "by_type"
        if re.search(r"小题同级编号", text):
            parameters["subquestion_numbering"] = "continuous"
        elif re.search(r"小题降级编号", text):
            parameters["subquestion_numbering"] = "nested"
        missing = [key for key in ("course", "paper") if key not in parameters]
        setting_keys = {
            "difficulty",
            "numbering",
            "grouping",
            "subquestion_numbering",
        }
        if not setting_keys.intersection(parameters):
            missing.append("setting")
        return CommandPlan(
            text,
            "exam.paper.settings.update",
            parameters=parameters,
            confidence=0.95 if not missing else 0.63,
            missing_fields=missing,
            message="请给出课程、试卷以及要修改的难度、编号或归类设置。" if missing else "",
        )

    if exam_setting_reference and re.search(r"读取|查看|显示|当前|是什么", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["paper"] = quoted[1]
        missing = [key for key in ("course", "paper") if key not in parameters]
        return CommandPlan(
            text,
            "exam.paper.settings.read",
            parameters=parameters,
            confidence=0.96 if not missing else 0.66,
            missing_fields=missing,
            message="请依次给出课程和试卷标题或 ID。" if missing else "",
        )

    if (
        "试卷" in text
        and not re.search(r"答卷|文件夹|目录", text)
        and re.search(r"重命名|改名|修改名称|修改标题", text)
    ):
        quoted = _extract_quoted(text)
        parameters = {}
        for key, value in zip(("course", "paper", "title"), quoted, strict=False):
            parameters[key] = value
        missing = [key for key in ("course", "paper", "title") if key not in parameters]
        return CommandPlan(
            text,
            "exam.paper.rename",
            parameters=parameters,
            confidence=0.96 if not missing else 0.65,
            missing_fields=missing,
            message="请依次给出课程、原试卷标题或 ID 和新标题。" if missing else "",
        )

    if (
        "试卷" in text
        and not re.search(r"答卷|文件夹|目录", text)
        and re.search(r"删除|移入回收站", text)
    ):
        quoted = _extract_quoted(text)
        parameters = {}
        for key, value in zip(("course", "paper"), quoted, strict=False):
            parameters[key] = value
        missing = [key for key in ("course", "paper") if key not in parameters]
        return CommandPlan(
            text,
            "exam.paper.delete",
            parameters=parameters,
            confidence=0.97 if not missing else 0.65,
            missing_fields=missing,
            message="请依次给出课程和要移入回收站的试卷。" if missing else "",
        )

    if (
        "试卷" in text
        and not re.search(r"答卷|文件夹|目录", text)
        and re.search(r"复制|拷贝|创建副本", text)
    ):
        quoted = _extract_quoted(text)
        parameters = {}
        for key, value in zip(("course", "paper"), quoted, strict=False):
            parameters[key] = value
        missing = [key for key in ("course", "paper") if key not in parameters]
        return CommandPlan(
            text,
            "exam.paper.copy",
            parameters=parameters,
            confidence=0.96 if not missing else 0.65,
            missing_fields=missing,
            message="请依次给出课程和要复制的试卷。" if missing else "",
        )

    if "试卷" in text and not re.search(r"答卷|文件夹|目录", text) and "移动" in text:
        quoted = _extract_quoted(text)
        parameters = {}
        for key, value in zip(("course", "paper", "target_directory_id"), quoted, strict=False):
            parameters[key] = value
        missing = [
            key for key in ("course", "paper", "target_directory_id") if key not in parameters
        ]
        return CommandPlan(
            text,
            "exam.paper.move",
            parameters=parameters,
            confidence=0.95 if not missing else 0.64,
            missing_fields=missing,
            message="请依次给出课程、要移动的试卷和目标文件夹标题或 ID。" if missing else "",
        )

    if (
        "试卷" in text
        and not re.search(r"答卷|文件夹|目录", text)
        and re.search(r"新建|创建|手动创建", text)
    ):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["title"] = quoted[1]
        missing = [] if "course" in parameters else ["course"]
        return CommandPlan(
            text,
            "exam.paper.create",
            parameters=parameters,
            confidence=0.96 if not missing else 0.65,
            missing_fields=missing,
            message="请给出课程；可同时给出新试卷标题。" if missing else "",
        )

    if (
        "试卷" in text
        and "答卷" not in text
        and re.search(r"读取|查看|显示|浏览|展开", text)
        and (len(_extract_quoted(text)) >= 2 or re.search(r"第\s*\d+\s*题", text))
    ):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["paper"] = quoted[1]
        if question_reference:
            parameters["question"] = question_reference.group(1)
        missing = [key for key in ("course", "paper") if key not in parameters]
        return CommandPlan(
            text,
            "exam.paper.read",
            parameters=parameters,
            confidence=0.96 if not missing else 0.66,
            missing_fields=missing,
            message="请依次用书名号或引号给出课程和试卷标题或 ID。" if missing else "",
        )

    if "试卷库" in text and re.search(r"列出|查看|显示|有哪些|搜索|浏览", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int] = {"course": quoted[0]} if quoted else {}
        if "搜索" in text and len(quoted) > 1:
            parameters["search"] = quoted[1]
        missing = [] if "course" in parameters else ["course"]
        return CommandPlan(
            text,
            "exam.paper_library.list",
            parameters=parameters,
            confidence=0.95 if not missing else 0.68,
            missing_fields=missing,
            message="请用书名号或引号给出课程名称。" if missing else "",
        )

    if (
        re.search(r"考试|试卷", text)
        and re.search(r"答卷|考试作答|答题详情", text)
        and re.search(r"读取|查看|显示|浏览", text)
    ):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["exam"] = quoted[1]
        if len(quoted) > 2:
            parameters["submission"] = quoted[2]
        missing = [key for key in ("course", "exam", "submission") if key not in parameters]
        return CommandPlan(
            text,
            "exams.submission.read",
            parameters=parameters,
            confidence=0.96 if not missing else 0.68,
            missing_fields=missing,
            message=(
                "请依次用书名号或引号给出课程名称、考试名称和学生姓名或学号。" if missing else ""
            ),
        )

    if (
        re.search(r"考试|试卷", text)
        and re.search(r"已交|未交|提交|考生", text)
        and re.search(r"列出|查看|显示|有哪些|搜索", text)
    ):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int] = {
            "state": 0 if "未交" in text else 1,
            "status": -1,
        }
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["exam"] = quoted[1]
        if len(quoted) > 2:
            parameters["search"] = quoted[2]
        missing = [key for key in ("course", "exam") if key not in parameters]
        return CommandPlan(
            text,
            "exams.submissions.list",
            parameters=parameters,
            confidence=0.95 if not missing else 0.68,
            missing_fields=missing,
            message=("请依次用书名号或引号给出课程名称和考试名称。" if missing else ""),
        )

    if "考试" in text and re.search(r"列出|查看|显示|有哪些|搜索", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int] = {"course": quoted[0]} if quoted else {}
        if len(quoted) > 1:
            parameters["search"] = quoted[1]
        parameters["status"] = (
            0 if "未开始" in text else 1 if "进行中" in text else 2 if "已结束" in text else -1
        )
        return CommandPlan(
            text,
            "exams.list",
            parameters=parameters,
            confidence=0.94 if quoted else 0.68,
            missing_fields=[] if quoted else ["course"],
            message="请用书名号或引号给出课程名称。" if not quoted else "",
        )

    qbank_label_reference = bool("题库" in text and "标签" in text)
    qbank_label_question_reference = bool(
        qbank_label_reference and re.search(r"题目|试题|第\s*\d+\s*题", text)
    )
    if qbank_label_question_reference and re.search(
        r"设置|关联|添加|增加|移除|取消|删除|替换|清空",
        text,
    ):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if question_reference:
            parameters["questions"] = [question_reference.group(1)]
            label_start = 1
        elif len(quoted) > 1:
            parameters["questions"] = [quoted[1]]
            label_start = 2
        else:
            label_start = len(quoted)
        labels = quoted[label_start:]
        if labels:
            parameters["labels"] = labels
        elif "清空" in text:
            parameters["labels"] = []
        if re.search(r"移除|取消|删除", text):
            parameters["mode"] = "remove"
        elif re.search(r"添加|增加|关联", text):
            parameters["mode"] = "add"
        else:
            parameters["mode"] = "replace"
        sync_references = bool(
            re.search(r"同步.{0,12}(?:作业|考试|引用)|(?:作业|考试).{0,8}同步", text)
        )
        action = (
            "question_bank.question.labels.sync"
            if sync_references
            else "question_bank.question.labels.set"
        )
        missing = [key for key in ("course", "questions") if key not in parameters]
        if parameters["mode"] in {"add", "remove"} and "labels" not in parameters:
            missing.append("labels")
        return CommandPlan(
            text,
            action,
            parameters=parameters,
            confidence=0.97 if not missing else 0.65,
            missing_fields=missing,
            message="请给出课程、题库题目和标签；清空标签时无需给出标签。" if missing else "",
        )

    if (
        qbank_label_reference
        and not qbank_label_question_reference
        and re.search(r"重命名|改名|修改名称", text)
    ):
        quoted = _extract_quoted(text)
        parameters = {}
        for key, value in zip(("course", "label", "name"), quoted, strict=False):
            parameters[key] = value
        missing = [key for key in ("course", "label", "name") if key not in parameters]
        return CommandPlan(
            text,
            "question_bank.label.rename",
            parameters=parameters,
            confidence=0.97 if not missing else 0.65,
            missing_fields=missing,
            message="请依次给出课程、原标签和新名称。" if missing else "",
        )

    if (
        qbank_label_reference
        and not qbank_label_question_reference
        and re.search(r"删除|移除", text)
    ):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["label"] = quoted[1]
        missing = [key for key in ("course", "label") if key not in parameters]
        return CommandPlan(
            text,
            "question_bank.label.delete",
            parameters=parameters,
            confidence=0.97 if not missing else 0.66,
            missing_fields=missing,
            message="请依次给出课程和要删除的题库标签。" if missing else "",
        )

    if (
        qbank_label_reference
        and not qbank_label_question_reference
        and re.search(r"新建|新增|创建|添加", text)
    ):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["name"] = quoted[-1]
        if len(quoted) > 2:
            parameters["parent_label"] = quoted[1]
        missing = [key for key in ("course", "name") if key not in parameters]
        return CommandPlan(
            text,
            "question_bank.label.create",
            parameters=parameters,
            confidence=0.96 if not missing else 0.65,
            missing_fields=missing,
            message="请给出课程和新标签名称；可同时给出父标签。" if missing else "",
        )

    if qbank_label_reference and re.search(r"列出|查看|显示|有哪些|标签树", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if qbank_label_question_reference:
            if question_reference:
                parameters["question"] = question_reference.group(1)
            elif len(quoted) > 1:
                parameters["question"] = quoted[1]
        missing = ["course"] if "course" not in parameters else []
        if qbank_label_question_reference and "question" not in parameters:
            missing.append("question")
        return CommandPlan(
            text,
            "question_bank.labels.list",
            parameters=parameters,
            confidence=0.96 if not missing else 0.68,
            missing_fields=missing,
            message="请给出课程；查看题目标签时还需给出题目。" if missing else "",
        )

    qbank_topic_reference = bool("题库" in text and re.search(r"知识点|知识图谱", text))
    qbank_topic_question_reference = bool(
        qbank_topic_reference and re.search(r"题目|试题|第\s*\d+\s*题", text)
    )
    if qbank_topic_question_reference and re.search(
        r"设置|关联|添加|增加|移除|取消|删除|替换|清空",
        text,
    ):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if question_reference:
            parameters["questions"] = [question_reference.group(1)]
            topic_start = 1
        elif len(quoted) > 1:
            parameters["questions"] = [quoted[1]]
            topic_start = 2
        else:
            topic_start = len(quoted)
        topics = quoted[topic_start:]
        if topics:
            parameters["topics"] = topics
        elif "清空" in text:
            parameters["topics"] = []
        if re.search(r"移除|取消|删除", text):
            parameters["mode"] = "remove"
        elif re.search(r"添加|增加|关联", text):
            parameters["mode"] = "add"
        else:
            parameters["mode"] = "replace"
        sync_references = bool(
            re.search(r"同步.{0,12}(?:作业|考试|引用)|(?:作业|考试).{0,8}同步", text)
        )
        action = (
            "question_bank.question.topics.sync"
            if sync_references
            else "question_bank.question.topics.set"
        )
        missing = [key for key in ("course", "questions") if key not in parameters]
        if parameters["mode"] in {"add", "remove"} and "topics" not in parameters:
            missing.append("topics")
        return CommandPlan(
            text,
            action,
            parameters=parameters,
            confidence=0.97 if not missing else 0.65,
            missing_fields=missing,
            message="请给出课程、题库题目和知识点；清空时无需给出知识点。" if missing else "",
        )

    if (
        qbank_topic_reference
        and not qbank_topic_question_reference
        and re.search(r"重命名|改名|修改名称", text)
    ):
        quoted = _extract_quoted(text)
        parameters = {}
        for key, value in zip(("course", "topic", "name"), quoted, strict=False):
            parameters[key] = value
        missing = [key for key in ("course", "topic", "name") if key not in parameters]
        return CommandPlan(
            text,
            "question_bank.topic.rename",
            parameters=parameters,
            confidence=0.97 if not missing else 0.65,
            missing_fields=missing,
            message="请依次给出课程、原知识点或分类和新名称。" if missing else "",
        )

    if (
        qbank_topic_reference
        and not qbank_topic_question_reference
        and re.search(r"删除|移除", text)
    ):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["topic"] = quoted[1]
        missing = [key for key in ("course", "topic") if key not in parameters]
        return CommandPlan(
            text,
            "question_bank.topic.delete",
            parameters=parameters,
            confidence=0.97 if not missing else 0.66,
            missing_fields=missing,
            message="请依次给出课程和要删除的知识点或分类。" if missing else "",
        )

    if (
        qbank_topic_reference
        and not qbank_topic_question_reference
        and re.search(r"新建|新增|创建|添加", text)
    ):
        quoted = _extract_quoted(text)
        parameters = {
            "kind": (
                "category"
                if re.search(
                    r"(?:新建|新增|创建|添加).{0,8}(?:知识点)?分类|作为.{0,4}分类",
                    text,
                )
                else "knowledge_point"
            )
        }
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["name"] = quoted[-1]
        if len(quoted) > 2:
            parameters["parent_topic"] = quoted[1]
        missing = [key for key in ("course", "name") if key not in parameters]
        return CommandPlan(
            text,
            "question_bank.topic.create",
            parameters=parameters,
            confidence=0.96 if not missing else 0.65,
            missing_fields=missing,
            message="请给出课程和新知识点或分类名称；可同时给出父分类。" if missing else "",
        )

    if qbank_topic_reference and re.search(r"列出|查看|显示|有哪些|知识点树|搜索", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if qbank_topic_question_reference:
            if question_reference:
                parameters["question"] = question_reference.group(1)
            elif len(quoted) > 1:
                parameters["question"] = quoted[1]
        elif "搜索" in text and len(quoted) > 1:
            parameters["search"] = quoted[1]
        missing = ["course"] if "course" not in parameters else []
        if qbank_topic_question_reference and "question" not in parameters:
            missing.append("question")
        return CommandPlan(
            text,
            "question_bank.topics.list",
            parameters=parameters,
            confidence=0.96 if not missing else 0.68,
            missing_fields=missing,
            message="请给出课程；查看题目知识点时还需给出题目。" if missing else "",
        )

    qbank_question_type_reference = bool(
        "题库" in text and "题型" in text and not re.search(r"题目|试题|第\s*\d+\s*题", text)
    )
    if qbank_question_type_reference and re.search(r"删除|移除", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["question_type"] = quoted[1]
        missing = [key for key in ("course", "question_type") if key not in parameters]
        return CommandPlan(
            text,
            "question_bank.question_type.delete",
            parameters=parameters,
            confidence=0.97 if not missing else 0.66,
            missing_fields=missing,
            message="请依次给出课程和要删除的题库题型。" if missing else "",
        )

    if qbank_question_type_reference and re.search(r"重命名|改名|修改名称", text):
        quoted = _extract_quoted(text)
        parameters = {}
        for key, value in zip(("course", "question_type", "name"), quoted, strict=False):
            parameters[key] = value
        missing = [key for key in ("course", "question_type", "name") if key not in parameters]
        return CommandPlan(
            text,
            "question_bank.question_type.rename",
            parameters=parameters,
            confidence=0.97 if not missing else 0.65,
            missing_fields=missing,
            message="请依次给出课程、原题型和新名称。" if missing else "",
        )

    if qbank_question_type_reference and re.search(r"移动|排序|调到|移到", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["question_type"] = quoted[1]
        position = re.search(r"(?:第|到|至|位置)\s*(\d+)|(?<!\d)(\d+)\s*(?:位|位置)", text)
        if position:
            parameters["target_position"] = int(position.group(1) or position.group(2))
        missing = [
            key for key in ("course", "question_type", "target_position") if key not in parameters
        ]
        return CommandPlan(
            text,
            "question_bank.question_type.move",
            parameters=parameters,
            confidence=0.96 if not missing else 0.64,
            missing_fields=missing,
            message="请依次给出课程、题库题型和目标位置。" if missing else "",
        )

    if qbank_question_type_reference and re.search(r"新建|新增|创建|添加", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["name"] = quoted[1]
        base_type = _homework_question_type_from_text(text)
        if base_type:
            parameters["base_type"] = base_type
        elif len(quoted) > 2:
            parameters["base_type"] = quoted[2]
        missing = [key for key in ("course", "name", "base_type") if key not in parameters]
        return CommandPlan(
            text,
            "question_bank.question_type.add",
            parameters=parameters,
            confidence=0.96 if not missing else 0.64,
            missing_fields=missing,
            message="请给出课程、新题型名称和基础题型。" if missing else "",
        )

    if qbank_question_type_reference and re.search(r"列出|查看|显示|有哪些|管理", text):
        quoted = _extract_quoted(text)
        parameters = {"course": quoted[0]} if quoted else {}
        missing = [] if quoted else ["course"]
        return CommandPlan(
            text,
            "question_bank.question_types.list",
            parameters=parameters,
            confidence=0.96 if not missing else 0.68,
            missing_fields=missing,
            message="请给出课程名称或 ID。" if missing else "",
        )

    qbank_recycle_reference = bool("题库" in text and re.search(r"回收站|垃圾箱", text))
    if qbank_recycle_reference and re.search(r"清空", text):
        quoted = _extract_quoted(text)
        parameters = {"course": quoted[0]} if quoted else {}
        missing = [] if quoted else ["course"]
        return CommandPlan(
            text,
            "question_bank.recycle.empty",
            parameters=parameters,
            confidence=0.98 if not missing else 0.68,
            missing_fields=missing,
            message="请给出要清空题库回收站的课程。" if missing else "",
        )

    if qbank_recycle_reference and re.search(r"永久删除|彻底删除|完全删除", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["items"] = quoted[1:]
        missing = [key for key in ("course", "items") if key not in parameters]
        return CommandPlan(
            text,
            "question_bank.recycle.delete",
            parameters=parameters,
            confidence=0.98 if not missing else 0.66,
            missing_fields=missing,
            message="请依次给出课程和要永久删除的回收站项目。" if missing else "",
        )

    if qbank_recycle_reference and re.search(r"还原|恢复", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["items"] = quoted[1:]
        missing = [key for key in ("course", "items") if key not in parameters]
        return CommandPlan(
            text,
            "question_bank.recycle.restore",
            parameters=parameters,
            confidence=0.97 if not missing else 0.66,
            missing_fields=missing,
            message="请依次给出课程和要还原的回收站项目。" if missing else "",
        )

    if qbank_recycle_reference and re.search(r"列出|查看|显示|有哪些|搜索", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if "搜索" in text and len(quoted) > 1:
            parameters["search"] = quoted[1]
        parameters["order"] = "asc" if re.search(r"升序|最早", text) else "desc"
        missing = ["course"] if "course" not in parameters else []
        return CommandPlan(
            text,
            "question_bank.recycle.list",
            parameters=parameters,
            confidence=0.97 if not missing else 0.68,
            missing_fields=missing,
            message="请给出课程名称或 ID。" if missing else "",
        )

    qbank_locked_reference = bool(
        "题库" in text and re.search(r"已锁定|锁定项|锁定内容|锁定列表", text)
    )
    if "题库" in text and re.search(r"解锁|解除锁定", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["items"] = quoted[1:]
        missing = [key for key in ("course", "items") if key not in parameters]
        return CommandPlan(
            text,
            "question_bank.items.unlock",
            parameters=parameters,
            confidence=0.97 if not missing else 0.66,
            missing_fields=missing,
            message="请依次给出课程和要解锁的题库项目。" if missing else "",
        )

    if qbank_locked_reference and re.search(r"列出|查看|显示|有哪些|搜索", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if "搜索" in text and len(quoted) > 1:
            parameters["search"] = quoted[1]
        parameters["order"] = "asc" if re.search(r"升序|最早", text) else "desc"
        missing = ["course"] if "course" not in parameters else []
        return CommandPlan(
            text,
            "question_bank.locked.list",
            parameters=parameters,
            confidence=0.97 if not missing else 0.68,
            missing_fields=missing,
            message="请给出课程名称或 ID。" if missing else "",
        )

    if "题库" in text and re.search(r"锁定", text) and not qbank_locked_reference:
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            key = (
                "directories"
                if re.search(r"目录|文件夹", text)
                and not re.search(r"题目|试题|第\s*\d+\s*题", text)
                else "questions"
            )
            parameters[key] = quoted[1:]
        missing = ["course"] if "course" not in parameters else []
        if "questions" not in parameters and "directories" not in parameters:
            missing.append("items")
        return CommandPlan(
            text,
            "question_bank.items.lock",
            parameters=parameters,
            confidence=0.96 if not missing else 0.65,
            missing_fields=missing,
            message="请依次给出课程和要锁定的题库题目或目录。" if missing else "",
        )

    if "题库" in text and re.search(r"来源课程|可(?:供)?提取题目.*课程|其他课程.*有哪些", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {"course": quoted[0]} if quoted else {}
        missing = ["course"] if "course" not in parameters else []
        return CommandPlan(
            text,
            "question_bank.source_courses.list",
            parameters=parameters,
            confidence=0.96 if not missing else 0.68,
            missing_fields=missing,
            message="请给出要接收题目的目标课程。" if missing else "",
        )

    if "题库" in text and re.search(r"下载中心|(?:导出|下载)(?:记录|任务)", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {"course": quoted[0]} if quoted else {}
        deleting = bool(re.search(r"删除|移除|清除", text))
        renaming = bool(re.search(r"重命名|改名|改为", text))
        getting = len(quoted) > 1 and bool(re.search(r"下载|获取链接|下载地址|保存到", text))
        if deleting or renaming or getting:
            if len(quoted) > 1:
                parameters["record"] = quoted[1]
            if renaming and len(quoted) > 2:
                parameters["name"] = quoted[2]
            output_match = re.search(
                r"(?:保存到|下载到|输出到|到)\s*"
                r"(?P<path>[A-Za-z]:\\[^\r\n，,]+|/[^\r\n，,]+)",
                text,
                flags=re.IGNORECASE,
            )
            if output_match:
                parameters["output_path"] = output_match.group("path").strip().strip("。；;")
            if deleting:
                action = "question_bank.downloads.delete"
                required = ("course", "record")
                message = "请依次给出课程和要删除的题库下载记录。"
            elif renaming:
                action = "question_bank.downloads.rename"
                required = ("course", "record", "name")
                message = "请依次给出课程、下载记录和新文件名。"
            else:
                action = "question_bank.downloads.get"
                required = ("course", "record")
                message = "请依次给出课程和要获取的题库下载记录。"
            missing = [key for key in required if key not in parameters]
            return CommandPlan(
                text,
                action,
                parameters=parameters,
                confidence=0.96 if not missing else 0.64,
                missing_fields=missing,
                message=message if missing else "",
            )
        missing = ["course"] if "course" not in parameters else []
        return CommandPlan(
            text,
            "question_bank.downloads.list",
            parameters=parameters,
            confidence=0.97 if not missing else 0.68,
            missing_fields=missing,
            message="请给出要查看下载中心的课程。" if missing else "",
        )

    if "题库" in text and re.search(r"导出|输出为", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        type_match = re.search(r"\b(ti|word|excel|pdf)\b", text, flags=re.IGNORECASE)
        if type_match:
            parameters["export_type"] = type_match.group(1).lower()
        export_all = bool(re.search(r"导出(?:题库)?全部|全部题目|整个题库|全量", text))
        parameters["export_all"] = export_all
        if not export_all and len(quoted) > 1:
            key = (
                "directories"
                if re.search(r"目录|文件夹", text)
                and not re.search(r"题目|试题|第\s*\d+\s*题", text)
                else "questions"
            )
            parameters[key] = quoted[1:]
        output_match = re.search(
            r"(?:保存到|下载到|输出到|导出到)\s*(?P<path>[A-Za-z]:\\[^\r\n，,]+|/[^\r\n，,]+)",
            text,
            flags=re.IGNORECASE,
        )
        if output_match:
            parameters["output_path"] = output_match.group("path").strip().strip("。；;")
        missing = [key for key in ("course", "export_type") if key not in parameters]
        if not export_all and "questions" not in parameters and "directories" not in parameters:
            missing.append("items")
        if not export_all and "output_path" not in parameters:
            missing.append("output_path")
        return CommandPlan(
            text,
            "question_bank.export.create",
            parameters=parameters,
            confidence=0.96 if not missing else 0.64,
            missing_fields=missing,
            message=(
                "请给出课程、导出格式、要导出的题目或目录，以及同步文件的保存路径。"
                if missing
                else ""
            ),
        )

    if "题库" in text and re.search(r"跨课程|其他课程|从.{0,20}课程", text):
        quoted = _extract_quoted(text)
        importing = bool(re.search(r"导入|提取|复制到", text))
        parameters: dict[str, object] = {}
        if importing:
            if quoted:
                parameters["source_course"] = quoted[0]
            has_target_directory = bool(re.search(r"目录|文件夹", text)) and len(quoted) >= 4
            if has_target_directory:
                parameters["course"] = quoted[-2]
                parameters["target_directory"] = quoted[-1]
                parameters["questions"] = quoted[1:-2]
            elif len(quoted) >= 3:
                parameters["course"] = quoted[-1]
                parameters["questions"] = quoted[1:-1]
            missing = [
                key for key in ("source_course", "questions", "course") if not parameters.get(key)
            ]
            return CommandPlan(
                text,
                "question_bank.questions.import_from_course",
                parameters=parameters,
                confidence=0.95 if not missing else 0.62,
                missing_fields=missing,
                message="请依次给出来源课程、题目、目标课程及可选的目标目录。" if missing else "",
            )
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["source_course"] = quoted[1]
        if len(quoted) > 2:
            parameters["search"] = quoted[2]
        missing = [key for key in ("course", "source_course") if key not in parameters]
        return CommandPlan(
            text,
            "question_bank.source_questions.list",
            parameters=parameters,
            confidence=0.95 if not missing else 0.65,
            missing_fields=missing,
            message="请依次给出目标课程和来源课程。" if missing else "",
        )

    if "题库" in text and re.search(r"智能导入|批量导入|导入试题|识别试题|解析试题", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        file_match = re.search(
            r"(?P<path>[A-Za-z]:\\[^\r\n\"'“”]+\.(?:docx?|pdf|png|jpe?g))",
            text,
            flags=re.IGNORECASE,
        )
        if file_match:
            parameters["file_path"] = file_match.group("path").strip()
        elif re.search(r"文本|文字", text) and len(quoted) > 1:
            parameters["source_text"] = quoted[1]
        preview = bool(re.search(r"预览|识别|解析|检查", text)) and not re.search(
            r"执行|确认导入|加入题库", text
        )
        action = (
            "question_bank.smart_import.preview" if preview else "question_bank.smart_import.commit"
        )
        if not preview and re.search(r"目录|文件夹", text) and len(quoted) > 1:
            parameters["target_directory"] = quoted[-1]
        missing = ["course"] if "course" not in parameters else []
        if "file_path" not in parameters and "source_text" not in parameters:
            missing.append("source")
        return CommandPlan(
            text,
            action,
            parameters=parameters,
            confidence=0.96 if not missing else 0.66,
            missing_fields=missing,
            message="请给出课程以及要解析或导入的文本或本地文件路径。" if missing else "",
        )

    if (
        "题库" in text
        and re.search(r"题目|试题|第\s*\d+\s*题", text)
        and re.search(r"难度|难易度", text)
        and re.search(r"修改|更新|设置|改为|设为", text)
        and (len(_extract_quoted(text)) > 2 or re.search(r"批量|多道|多个|这些|全部|所有", text))
    ):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["questions"] = quoted[1:]
        elif question_reference:
            parameters["questions"] = [question_reference.group(1)]
        difficulty_match = re.search(
            r"(?:难度|难易度)\D*(0\.\d|1(?:\.0)?|易|中|难|easy|medium|hard)",
            text,
            re.IGNORECASE,
        )
        if difficulty_match:
            raw_difficulty = difficulty_match.group(1)
            parameters["difficulty"] = (
                float(raw_difficulty)
                if re.fullmatch(r"\d+(?:\.\d+)?", raw_difficulty)
                else raw_difficulty
            )
        missing = [key for key in ("course", "questions", "difficulty") if key not in parameters]
        return CommandPlan(
            text,
            "question_bank.questions.difficulty.update",
            parameters=parameters,
            confidence=0.96 if not missing else 0.64,
            missing_fields=missing,
            message="请给出课程、一至多道题和目标难度。" if missing else "",
        )

    if (
        "题库" in text
        and re.search(r"题目|试题|第\s*\d+\s*题", text)
        and re.search(r"(?:修改|改为|设为|转换).{0,10}题型|题型.{0,6}(?:修改|改为|设为)", text)
    ):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 2:
            parameters["questions"] = quoted[1:-1]
            parameters["question_type"] = quoted[-1]
        elif question_reference and len(quoted) > 1:
            parameters["questions"] = [question_reference.group(1)]
            parameters["question_type"] = quoted[-1]
        missing = [key for key in ("course", "questions", "question_type") if key not in parameters]
        return CommandPlan(
            text,
            "question_bank.questions.type.update",
            parameters=parameters,
            confidence=0.96 if not missing else 0.64,
            missing_fields=missing,
            message="请依次给出课程、一至多道题和目标题型。" if missing else "",
        )

    if "题库" in text and re.search(r"复制|拷贝|创建副本", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 2:
            parameters["target_directory"] = quoted[-1]
            key = (
                "directories"
                if re.search(r"目录|文件夹", text)
                and not re.search(r"题目|试题|第\s*\d+\s*题", text)
                else "questions"
            )
            parameters[key] = quoted[1:-1]
        missing = ["course"] if "course" not in parameters else []
        if "questions" not in parameters and "directories" not in parameters:
            missing.append("items")
        if "target_directory" not in parameters:
            missing.append("target_directory")
        return CommandPlan(
            text,
            "question_bank.items.copy",
            parameters=parameters,
            confidence=0.96 if not missing else 0.64,
            missing_fields=missing,
            message="请依次给出课程、要复制的题目或目录和目标目录。" if missing else "",
        )

    qbank_directory_reference = bool(
        "题库" in text
        and re.search(r"文件夹|目录", text)
        and not re.search(r"题目|试题|第\s*\d+\s*题", text)
    )
    qbank_permission_reference = bool(
        qbank_directory_reference
        and re.search(r"权限|共享范围|可见范围|学生(?:抽题)?自测|私有|公开|共享给", text)
    )
    if qbank_permission_reference and re.search(
        r"设置|修改|更新|改为|设为|开启|关闭|允许|禁止|不允许|共享给|公开|私有",
        text,
    ):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["directory"] = quoted[1]

        if re.search(r"(?:关闭|禁止|不允许|取消).{0,8}(?:学生)?(?:抽题)?自测", text):
            parameters["allow_student_self_practice"] = False
        elif re.search(r"(?:开启|允许).{0,8}(?:学生)?(?:抽题)?自测", text):
            parameters["allow_student_self_practice"] = True

        if re.search(r"私有|仅自己(?:可见)?", text):
            parameters["share_scope"] = "private"
        elif re.search(r"指定.{0,8}(?:教师|成员)|仅共享给", text):
            parameters["share_scope"] = "selected_teachers"
            if len(quoted) > 2:
                parameters["selected_teachers"] = quoted[2:]
        elif re.search(r"公开|全部教学团队|所有教学团队|全体教师", text):
            parameters["share_scope"] = "all_team"

        missing = [key for key in ("course", "directory") if key not in parameters]
        if not any(
            key in parameters
            for key in (
                "allow_student_self_practice",
                "share_scope",
                "selected_teachers",
            )
        ):
            missing.append("permission_change")
        if parameters.get("share_scope") == "selected_teachers" and not parameters.get(
            "selected_teachers"
        ):
            missing.append("selected_teachers")
        return CommandPlan(
            text,
            "question_bank.directory.permissions.update",
            parameters=parameters,
            confidence=0.97 if not missing else 0.66,
            missing_fields=missing,
            message=(
                "请依次给出课程、题库目录和要修改的共享范围或学生抽题自测状态；"
                "指定成员范围还需给出教师姓名或人员 ID。"
                if missing
                else ""
            ),
        )

    if qbank_permission_reference and re.search(r"查看|读取|显示|当前|是什么", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["directory"] = quoted[1]
        missing = [key for key in ("course", "directory") if key not in parameters]
        return CommandPlan(
            text,
            "question_bank.directory.permissions.read",
            parameters=parameters,
            confidence=0.97 if not missing else 0.68,
            missing_fields=missing,
            message="请依次给出课程和题库目录。" if missing else "",
        )

    if qbank_directory_reference and re.search(r"删除|移入回收站", text):
        quoted = _extract_quoted(text)
        parameters = {}
        for key, value in zip(("course", "directory"), quoted, strict=False):
            parameters[key] = value
        missing = [key for key in ("course", "directory") if key not in parameters]
        return CommandPlan(
            text,
            "question_bank.directory.delete",
            parameters=parameters,
            confidence=0.97 if not missing else 0.65,
            missing_fields=missing,
            message="请依次给出课程和要移入回收站的题库目录。" if missing else "",
        )

    if qbank_directory_reference and re.search(r"重命名|改名|修改名称", text):
        quoted = _extract_quoted(text)
        parameters = {}
        for key, value in zip(("course", "directory", "name"), quoted, strict=False):
            parameters[key] = value
        missing = [key for key in ("course", "directory", "name") if key not in parameters]
        return CommandPlan(
            text,
            "question_bank.directory.rename",
            parameters=parameters,
            confidence=0.96 if not missing else 0.64,
            missing_fields=missing,
            message="请依次给出课程、原题库目录和新名称。" if missing else "",
        )

    if qbank_directory_reference and re.search(r"第\s*\d+\s*位|位置\s*\d+|\d+\s*位", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["directory"] = quoted[1]
        position = re.search(r"第\s*(\d+)\s*位|位置\s*(\d+)|(\d+)\s*位", text)
        if position:
            parameters["target_position"] = int(
                position.group(1) or position.group(2) or position.group(3)
            )
        missing = [
            key for key in ("course", "directory", "target_position") if key not in parameters
        ]
        return CommandPlan(
            text,
            "question_bank.directory.reorder",
            parameters=parameters,
            confidence=0.96 if not missing else 0.64,
            missing_fields=missing,
            message="请依次给出课程、题库目录和同级目标位置。" if missing else "",
        )

    if qbank_directory_reference and re.search(r"移动|移到|移至", text):
        quoted = _extract_quoted(text)
        parameters = {}
        for key, value in zip(("course", "directory", "target_directory"), quoted, strict=False):
            parameters[key] = value
        missing = [
            key for key in ("course", "directory", "target_directory") if key not in parameters
        ]
        return CommandPlan(
            text,
            "question_bank.directory.move",
            parameters=parameters,
            confidence=0.96 if not missing else 0.64,
            missing_fields=missing,
            message="请依次给出课程、要移动的题库目录和目标目录。" if missing else "",
        )

    if qbank_directory_reference and re.search(r"置顶|取消置顶", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {"top": "取消置顶" not in text}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["directory"] = quoted[1]
        missing = [key for key in ("course", "directory") if key not in parameters]
        return CommandPlan(
            text,
            "question_bank.directory.top.set",
            parameters=parameters,
            confidence=0.96 if not missing else 0.65,
            missing_fields=missing,
            message="请依次给出课程和要设置置顶状态的题库目录。" if missing else "",
        )

    if qbank_directory_reference and re.search(r"新建|创建|添加", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["name"] = quoted[-1]
        if len(quoted) > 2:
            parameters["parent_directory"] = quoted[1]
        missing = [key for key in ("course", "name") if key not in parameters]
        return CommandPlan(
            text,
            "question_bank.directory.create",
            parameters=parameters,
            confidence=0.96 if not missing else 0.65,
            missing_fields=missing,
            message="请给出课程和新题库目录名称；可同时给出父目录。" if missing else "",
        )

    if qbank_directory_reference and re.search(r"目录树|文件夹树|全部目录", text):
        quoted = _extract_quoted(text)
        parameters = {"course": quoted[0]} if quoted else {}
        missing = [] if quoted else ["course"]
        return CommandPlan(
            text,
            "question_bank.directories.list",
            parameters=parameters,
            confidence=0.96 if not missing else 0.68,
            missing_fields=missing,
            message="请给出课程名称或 ID。" if missing else "",
        )

    qbank_question_reference = bool("题库" in text and re.search(r"题目|试题|第\s*\d+\s*题", text))
    if qbank_question_reference and re.search(r"删除|移入回收站", text):
        quoted = _extract_quoted(text)
        parameters = {}
        if quoted:
            parameters["course"] = quoted[0]
        if question_reference:
            parameters["question"] = question_reference.group(1)
        elif len(quoted) > 1:
            parameters["question"] = quoted[1]
        missing = [key for key in ("course", "question") if key not in parameters]
        return CommandPlan(
            text,
            "question_bank.question.delete",
            parameters=parameters,
            confidence=0.97 if not missing else 0.65,
            missing_fields=missing,
            message="请依次给出课程和题库题目 ID、题号或题干。" if missing else "",
        )

    if qbank_question_reference and re.search(r"第\s*\d+\s*位|位置\s*\d+|\d+\s*位", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if question_reference:
            parameters["question"] = question_reference.group(1)
        elif len(quoted) > 1:
            parameters["question"] = quoted[1]
        position = re.search(r"第\s*(\d+)\s*位|位置\s*(\d+)|(\d+)\s*位", text)
        if position:
            parameters["target_position"] = int(
                position.group(1) or position.group(2) or position.group(3)
            )
        missing = [
            key for key in ("course", "question", "target_position") if key not in parameters
        ]
        return CommandPlan(
            text,
            "question_bank.question.reorder",
            parameters=parameters,
            confidence=0.96 if not missing else 0.64,
            missing_fields=missing,
            message="请依次给出课程、题库题目和当前目录内的目标位置。" if missing else "",
        )

    if qbank_question_reference and re.search(r"移动|移到|移至", text):
        quoted = _extract_quoted(text)
        parameters = {}
        for key, value in zip(("course", "question", "target_directory"), quoted, strict=False):
            parameters[key] = value
        if question_reference:
            parameters["question"] = question_reference.group(1)
        missing = [
            key for key in ("course", "question", "target_directory") if key not in parameters
        ]
        return CommandPlan(
            text,
            "question_bank.question.move",
            parameters=parameters,
            confidence=0.96 if not missing else 0.64,
            missing_fields=missing,
            message="请依次给出课程、题库题目和目标目录。" if missing else "",
        )

    if (
        qbank_question_reference
        and re.search(r"难度", text)
        and re.search(r"修改|更新|设置|改为|设为", text)
    ):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if question_reference:
            parameters["question"] = question_reference.group(1)
        elif len(quoted) > 1:
            parameters["question"] = quoted[1]
        difficulty_match = re.search(r"难度\D*(0\.\d|1(?:\.0)?)", text)
        if difficulty_match:
            parameters["difficulty"] = float(difficulty_match.group(1))
        missing = [key for key in ("course", "question", "difficulty") if key not in parameters]
        return CommandPlan(
            text,
            "question_bank.question.difficulty.update",
            parameters=parameters,
            confidence=0.95 if not missing else 0.63,
            missing_fields=missing,
            message="请给出课程、题库题目和 0.1 至 1.0 的难度。" if missing else "",
        )

    if qbank_question_reference and re.search(r"修改|更新|编辑|改为", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if question_reference:
            parameters["question"] = question_reference.group(1)
            content_candidates = quoted[1:]
        elif len(quoted) > 1:
            parameters["question"] = quoted[1]
            content_candidates = quoted[2:]
        else:
            content_candidates = []
        if re.search(r"题干|题目内容", text) and content_candidates:
            parameters["stem"] = content_candidates[-1]
        options = _labeled_question_options(text)
        if options:
            parameters["options"] = options
        correct_match = re.search(
            r"(?:正确答案|答案)\s*(?:改为|设为|为|是|[:：])?\s*"
            r"([A-Z](?:\s*[,，、;；]\s*[A-Z])*)",
            text,
            flags=re.IGNORECASE,
        )
        if correct_match:
            parameters["correct_answer"] = correct_match.group(1)
        score_free_difficulty = re.search(r"难度\D*(0\.\d|1(?:\.0)?)", text)
        if score_free_difficulty:
            parameters["difficulty"] = float(score_free_difficulty.group(1))
        analysis_match = re.search(r"(?:解析|答案解析)[^《“\"']*[《“\"']([^》”\"']*)", text)
        if analysis_match:
            parameters["analysis"] = analysis_match.group(1)
        missing = [key for key in ("course", "question") if key not in parameters]
        if not {"stem", "options", "correct_answer", "difficulty", "analysis"}.intersection(
            parameters
        ):
            missing.append("changed_field")
        return CommandPlan(
            text,
            "question_bank.question.update",
            parameters=parameters,
            confidence=0.94 if not missing else 0.61,
            missing_fields=missing,
            message="请给出课程、题库题目和至少一个要修改的字段。" if missing else "",
        )

    qbank_question_type = _homework_question_type_from_text(text)
    if "题库" in text and qbank_question_type and re.search(r"新增|添加|加入|加一道|出一道", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, object] = {"question_type": qbank_question_type}
        if quoted:
            parameters["course"] = quoted[0]
        stem_match = re.search(
            r"(?:单选题|多选题|填空题|判断题|简答题)\s*[《“\"']([^》”\"']+)",
            text,
        )
        if stem_match:
            parameters["stem"] = stem_match.group(1)
        elif len(quoted) > 1:
            parameters["stem"] = quoted[-1]
        directory_match = re.search(r"(?:目录|文件夹)\s*[《“\"']([^》”\"']+)[》”\"']", text)
        if directory_match:
            parameters["directory"] = directory_match.group(1)
        options = _labeled_question_options(text)
        if options:
            parameters["options"] = options
        correct_match = re.search(
            r"(?:正确答案|答案)\s*(?:为|是|[:：])?\s*"
            r"([A-Z](?:\s*[,，、;；]\s*[A-Z])*)",
            text,
            flags=re.IGNORECASE,
        )
        if correct_match:
            parameters["correct_answer"] = correct_match.group(1)
        boolean_match = re.search(
            r"(?:正确答案|答案)\s*(?:为|是|[:：])?\s*(正确|错误|对|错|true|false)",
            text,
            flags=re.IGNORECASE,
        )
        if boolean_match:
            parameters["answer"] = boolean_match.group(1)
        missing = [key for key in ("course", "stem") if key not in parameters]
        if qbank_question_type in {"single_choice", "multiple_choice"}:
            missing.extend(key for key in ("options", "correct_answer") if key not in parameters)
        if qbank_question_type == "true_false" and "answer" not in parameters:
            missing.append("answer")
        return CommandPlan(
            text,
            "question_bank.question.add",
            parameters=parameters,
            confidence=0.94 if not missing else 0.61,
            missing_fields=missing,
            message="请给出课程、题型所需题干、选项和答案。" if missing else "",
        )

    if (
        "题库" in text
        and re.search(r"题目|试题|答案|详情|完整内容", text)
        and re.search(r"读取|查看|显示|浏览", text)
    ):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["question"] = quoted[1]
        missing = [key for key in ("course", "question") if key not in parameters]
        return CommandPlan(
            text,
            "question_bank.question.read",
            parameters=parameters,
            confidence=0.95 if not missing else 0.68,
            missing_fields=missing,
            message=("请依次用书名号或引号给出课程名称和题目 ID 或题干。" if missing else ""),
        )

    if "题库" in text and re.search(r"列出|查看|显示|浏览|搜索", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int] = {"course": quoted[0]} if quoted else {}
        if len(quoted) > 1:
            parameters["search"] = quoted[1]
        parameters["page"] = 1
        return CommandPlan(
            text,
            "question_bank.list",
            parameters=parameters,
            confidence=0.94 if quoted else 0.68,
            missing_fields=[] if quoted else ["course"],
            message="请用书名号或引号给出课程名称。" if not quoted else "",
        )

    if re.search(r"讨论|话题", text) and re.search(
        r"删除.*(?:回复|评论)|(?:回复|评论).*删除", text
    ):
        quoted = _extract_quoted(text)
        parameters: dict[str, str] = {}
        for key, value in zip(("course", "topic", "reply"), quoted, strict=False):
            parameters[key] = value
        missing = [key for key in ("course", "topic", "reply") if key not in parameters]
        return CommandPlan(
            text,
            "discussions.reply.delete",
            parameters=parameters,
            confidence=0.97 if not missing else 0.68,
            missing_fields=missing,
            message="请依次用书名号或引号给出课程、讨论和回复。" if missing else "",
        )

    if re.search(r"讨论|话题", text) and re.search(
        r"(?:编辑|修改).*?(?:回复|评论)|(?:回复|评论).*?(?:编辑|修改)", text
    ):
        quoted = _extract_quoted(text)
        parameters = {}
        for key, value in zip(("course", "topic", "reply", "content"), quoted, strict=False):
            parameters[key] = value
        missing = [key for key in ("course", "topic", "reply", "content") if key not in parameters]
        return CommandPlan(
            text,
            "discussions.reply.edit",
            parameters=parameters,
            confidence=0.97 if not missing else 0.68,
            missing_fields=missing,
            message="请依次用书名号或引号给出课程、讨论、原回复和新正文。" if missing else "",
        )

    if (
        re.search(r"讨论|话题", text)
        and "回复" in text
        and not re.search(r"读取|查看|显示|浏览|删除|编辑|修改", text)
    ):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | bool] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["topic"] = quoted[1]
        if len(quoted) > 3:
            parameters["reply_to"] = quoted[2]
            parameters["content"] = quoted[3]
        elif len(quoted) > 2:
            parameters["content"] = quoted[2]
        parameters["anonymous"] = "匿名" in text
        missing = [key for key in ("course", "topic", "content") if key not in parameters]
        return CommandPlan(
            text,
            "discussions.reply.create",
            parameters=parameters,
            confidence=0.96 if not missing else 0.68,
            missing_fields=missing,
            message="请依次用书名号或引号给出课程、讨论和回复正文。" if missing else "",
        )

    if re.search(r"讨论|话题", text) and "删除" in text:
        quoted = _extract_quoted(text)
        parameters: dict[str, str] = {}
        for key, value in zip(("course", "topic"), quoted, strict=False):
            parameters[key] = value
        missing = [key for key in ("course", "topic") if key not in parameters]
        return CommandPlan(
            text,
            "discussions.topic.delete",
            parameters=parameters,
            confidence=0.97 if not missing else 0.68,
            missing_fields=missing,
            message="请依次用书名号或引号给出课程和讨论。" if missing else "",
        )

    if re.search(r"讨论|话题", text) and "置顶" in text:
        quoted = _extract_quoted(text)
        parameters: dict[str, str | bool] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["topic"] = quoted[1]
        parameters["top"] = not bool(re.search(r"取消置顶|不再置顶", text))
        missing = [key for key in ("course", "topic") if key not in parameters]
        return CommandPlan(
            text,
            "discussions.topic.top.set",
            parameters=parameters,
            confidence=0.97 if not missing else 0.68,
            missing_fields=missing,
            message="请依次用书名号或引号给出课程和讨论。" if missing else "",
        )

    if re.search(r"讨论|话题", text) and re.search(r"编辑|修改", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, str] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["topic"] = quoted[1]
        if len(quoted) > 3:
            parameters["title"] = quoted[2]
            parameters["content"] = quoted[3]
        elif len(quoted) > 2:
            if "标题" in text and not re.search(r"正文|内容", text):
                parameters["title"] = quoted[2]
            else:
                parameters["content"] = quoted[2]
        missing = [key for key in ("course", "topic") if key not in parameters]
        if "title" not in parameters and "content" not in parameters:
            missing.append("content")
        return CommandPlan(
            text,
            "discussions.topic.edit",
            parameters=parameters,
            confidence=0.96 if not missing else 0.68,
            missing_fields=missing,
            message=(
                "请依次用书名号或引号给出课程、原讨论，以及新标题或新正文。" if missing else ""
            ),
        )

    if re.search(r"讨论|话题", text) and re.search(r"发布|新建|发起|创建", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | bool] = {}
        for key, value in zip(("course", "title", "content"), quoted, strict=False):
            parameters[key] = value
        parameters["class_only"] = bool(re.search(r"本班|这个班|当前班", text))
        parameters["anonymous"] = "匿名" in text
        missing = [key for key in ("course", "title", "content") if key not in parameters]
        return CommandPlan(
            text,
            "discussions.topic.create",
            parameters=parameters,
            confidence=0.96 if not missing else 0.68,
            missing_fields=missing,
            message="请依次用书名号或引号给出课程、标题和正文。" if missing else "",
        )

    if (
        re.search(r"讨论|话题", text)
        and re.search(r"回复|正文|详情|内容", text)
        and re.search(r"读取|查看|显示|浏览", text)
    ):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int | bool] = {}
        if quoted:
            parameters["course"] = quoted[0]
        if len(quoted) > 1:
            parameters["topic"] = quoted[1]
        parameters["class_only"] = bool(re.search(r"本班|这个班|当前班", text))
        parameters["order"] = 1 if re.search(r"正序|最早|从旧到新", text) else 2
        missing = [key for key in ("course", "topic") if key not in parameters]
        return CommandPlan(
            text,
            "discussions.topic.read",
            parameters=parameters,
            confidence=0.95 if not missing else 0.68,
            missing_fields=missing,
            message="请依次用书名号或引号给出课程名称和讨论标题。" if missing else "",
        )

    if re.search(r"讨论|话题", text) and re.search(r"列出|查看|显示|浏览|搜索|有哪些", text):
        quoted = _extract_quoted(text)
        parameters: dict[str, str | int | bool] = {"course": quoted[0]} if quoted else {}
        if len(quoted) > 1:
            parameters["search"] = quoted[1]
        parameters["class_only"] = bool(re.search(r"本班|这个班|当前班", text))
        return CommandPlan(
            text,
            "discussions.list",
            parameters=parameters,
            confidence=0.94 if quoted else 0.68,
            missing_fields=[] if quoted else ["course"],
            message="请用书名号或引号给出课程名称。" if not quoted else "",
        )

    module = next((target for alias, target in MODULE_ALIASES.items() if alias in text), None)
    if module and re.search(r"打开|进入|查看|去|切到", text):
        quoted = _extract_quoted(text)
        parameters = {"module": module}
        if quoted:
            parameters["course"] = quoted[0]
        missing = []
        if "course" not in parameters:
            missing.append("course")
        return CommandPlan(
            text,
            "course.module.open",
            parameters=parameters,
            confidence=0.9 if not missing else 0.72,
            missing_fields=missing,
            message="请用书名号或引号给出课程名称。" if missing else "",
        )

    if re.search(r"(课程|这个课).*(功能|菜单|入口)|(功能|菜单).*(课程|这个课)", text):
        quoted = _extract_quoted(text)
        parameters = {"course": quoted[0]} if quoted else {}
        return CommandPlan(
            text,
            "course.modules.discover",
            parameters=parameters,
            confidence=0.86 if quoted else 0.65,
            missing_fields=[] if quoted else ["course"],
            message="请提供课程名称或课程 ID。" if not quoted else "",
        )

    return CommandPlan(
        text,
        None,
        confidence=0.0,
        message="当前路由器还不能确定动作；可先调用 capabilities.list 查看覆盖状态。",
    )
