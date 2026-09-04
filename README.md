# Chaoxing Agent

Chaoxing Agent 把学习通/超星教师端、学生端与个人空间的操作封装成可验证的 HTTP 动作，供 Codex、其他 MCP Agent 和本地脚本调用。用户可以直接给出中文自然语言命令，也可以调用稳定的语义工具。

交付运行时不打开浏览器，不依赖浏览器扩展、WebDriver 或学习通客户端。开发新动作时可以观察网页请求；进入代码库的正式动作必须能够脱离浏览器独立运行。

## 可直接安装的教师 Skill

[skills/chaoxing-teacher](skills/chaoxing-teacher) 是不含宿主专用注册项的标准 Skill 目录。Windows 安装包已自带官方 Python 运行时；WorkBuddy、ZCode、Codex 或其他支持本地 Skill 的 Agent 宿主可载入同一份包，不需要另外注册服务、安装 Python、配置环境变量、指定 Cookie 文件或运行安装向导。

教师的日常入口只有自然语言：直接说出目的；尚未登录时，Agent 先在对话中问账号，再问密码。教师直接在聊天框中输入明文账号和密码，Agent 随后登录并自动继续原请求。发布、发送、成绩提交或覆盖、权限变化、删除和付费等高影响动作仍在执行前按具体影响确认一次。

Skill 自带当前 HTTP 运行时和离线 HTTP 组件，首次运行不下载或安装依赖。Agent 在内部把教师原话整理为领域、操作、对象和值，再由 Skill 在单一领域内返回 typed action 候选；目录排名只用于召回，不能直接授权执行，英文标识仅留在内部执行字段。学生端入口在 Skill 层拒绝。状态目录不可写时自动降级到宿主可写目录；账号会话相互隔离，并提供退出和并发保护。

运行 `python scripts/build_teacher_skill.py` 会同步内置运行时并在 `dist` 只生成一份 `学习通教师版-版本号.zip`。同一份包用于所有支持标准 Skill 的宿主；构建器拒绝把 Cookie、确认记录、状态文件、MCP 服务或 `__pycache__` 装入发布包。

下文的 CLI 与服务接口是本仓库的开发、维护和其他集成路径，不是教师使用该 Skill 的前置步骤。

## 当前能力

截至 2026-09-04，本仓库包含 566 个已实现动作，覆盖 41 个领域。精确动作名、风险等级、实现状态和实测状态以运行时目录为准：
截至 2026-09-04，本仓库包含 566 个已实现动作，覆盖 41 个领域。精确动作名、风险等级、实现状态和实测状态以运行时目录为准：

```powershell
uv run chaoxing-agent capabilities
```

主要领域包括：

- 登录、教师课程、班级与教学团队；
- 我学的课、学生课程入口、课程活动、章节、讨论、作业、考试、自测、资料、AI 工具、错题概况、学习记录、课程图谱与在线学习诚信承诺状态；
- 章节、课件、教案（含本地文件直接上传）、资料、课程资源与云盘；
- 作业、考试、题库、通知、讨论与成绩统计；
- 班级活动（含普通、手势、位置、二维码和签到码签到）、任务引擎、课程图谱、AI 工作台与 AI 知识库；
- 笔记、收件箱、通讯录、小组、专题创作与个人直播；
- AIGC/相似度检测；
- 岗位能力中的招聘搜索、职业百科和行业岗位库。

完整的领域计数、风险分布和当前平台不可用状态见 [能力地图](docs/capability-map.md)。

## 工作路径

```text
中文自然语言或语义工具调用
          ↓
MCP / CLI
          ↓
动作目录 → 参数解析 → 风险确认
          ↓
已登录的 requests HTTP 会话
          ↓
结构化结果 + 回读/可观察后置条件
```

CLI、MCP 和自然语言路由共用同一个 `ActionRuntime`，不会形成三套行为不同的实现。

## 安装

需要 Python 3.11 或更高版本，并建议使用 [uv](https://docs.astral.sh/uv/)。

```powershell
uv sync --extra dev
```

仓库开发环境依赖 `requests` 和 MCP Python SDK；教师 Skill 已内置运行所需的纯 Python HTTP 组件，正式运行不安装浏览器自动化包或其他 Python 包。

## 开发者 CLI 登录

先指定本地 Cookie 文件位置。该文件可以尚不存在，登录成功后会原子写入：

```powershell
$env:CHAOXING_COOKIE_FILE = "$env:LOCALAPPDATA\chaoxing-agent\cookies.json"
uv run chaoxing-agent login --username "学习通账号"
```

这一节只供仓库开发调试；教师使用 Skill 时直接按前述聊天流程输入账号和密码。开发 CLI 的密码可在随后出现的终端提示中输入，也可设置 `CHAOXING_USERNAME` 与 `CHAOXING_PASSWORD`。

学银在线等超星跨应用页面需要额外 SSO 时，可把当前页面地址作为目标；运行时先完成平台返回的 HTTP 跳转，再分别验证个人空间登录状态与目标主机，且响应不返回目标查询参数或 SSO 票据：

```powershell
uv run chaoxing-agent login --username "学习通账号" --target-url "https://xueyinonline.chaoxing.com/..."
```

对于学生课程模块，优先按课程名解析目标，代理无需读取或传递带签名的地址：

```powershell
uv run chaoxing-agent login --username "学习通账号" --learning-course "课程名" --learning-module "直播课/见面课"
```

该方式需要当前 Cookie 至少仍能读取“我学的课”，以便在内存中选定课程和模块；如果主会话也已过期，先执行一次普通 `login`，再执行上述目标登录。

检查会话：

```powershell
uv run chaoxing-agent doctor --live
uv run chaoxing-agent session
```

也可以把已有的 Cookie JSON 指给 `CHAOXING_COOKIE_FILE`。支持顶层数组或 `{ "cookies": [...] }`，每条记录需要 `name`、`value`、`domain` 和 `path`。

如果平台强制二次验证，HTTP 登录会明确返回二次验证要求；项目不会绕过平台验证。

可选配置：

| 环境变量 | 含义 | 默认值 |
| --- | --- | --- |
| `CHAOXING_COOKIE_FILE` | 登录 Cookie JSON；认证动作必需 | 无 |
| `CHAOXING_REQUEST_TIMEOUT` | HTTP 超时秒数 | `20` |
| `CHAOXING_CONFIRMATION_FILE` | 一次性确认记录 | `%LOCALAPPDATA%\chaoxing-agent\confirmations.json` |
| `CHAOXING_STATE_FILE` | 少量本地草稿映射状态 | `%LOCALAPPDATA%\chaoxing-agent\state.json` |

示例值见 [.env.example](.env.example)。项目不会自动加载 `.env`；请通过 Agent/MCP 配置或系统环境变量注入。

## CLI

读取操作可以直接执行：

```powershell
uv run chaoxing-agent courses
uv run chaoxing-agent learning-courses
uv run chaoxing-agent learning-modules "课程名称"
uv run chaoxing-agent learning-open "课程名称" "章节"
uv run chaoxing-agent learning-chapters "课程名称"
uv run chaoxing-agent learning-discussions "课程名称"
uv run chaoxing-agent learning-discussion-read "课程名称" "讨论标题或ID"
uv run chaoxing-agent learning-homeworks "课程名称"
uv run chaoxing-agent learning-homework-read "课程名称" "作业标题或ID"
uv run chaoxing-agent learning-homework-answer-enter "课程名称" "作业标题或ID"
uv run chaoxing-agent learning-homework-answer-save "课程名称" "作业标题或ID" --updates-json '[{"question":"1","answer":"答案正文"}]'
uv run chaoxing-agent learning-homework-submit "课程名称" "作业标题或ID"
uv run chaoxing-agent learning-homework-redo "课程名称" "作业标题或ID"
uv run chaoxing-agent learning-homework-attempts "课程名称" "作业标题或ID"
uv run chaoxing-agent learning-homework-attempt-read "课程名称" "作业标题或ID" "次数"
uv run chaoxing-agent learning-materials "课程名称"
uv run chaoxing-agent learning-records "课程名称"
uv run chaoxing-agent learning-graph "课程名称"
uv run chaoxing-agent learning-graph-node "课程名称" "节点名称或ID"
uv run chaoxing-agent classes "英语写作示例"
uv run chaoxing-agent modules "英语写作示例"
uv run chaoxing-agent homeworks "英语写作示例"
uv run chaoxing-agent job-search "英语教师" --education "本科"
uv run chaoxing-agent industry-types
```

自然语言入口调用同一运行时：

```powershell
uv run chaoxing-agent run "列出我教的课程"
uv run chaoxing-agent run "列出我学的课程"
uv run chaoxing-agent run "打开我学课程《课程名称》的《章节》"
uv run chaoxing-agent run "列出我学课程《课程名称》的章节"
uv run chaoxing-agent run "查看我学课程《课程名称》的讨论《讨论标题》回复"
uv run chaoxing-agent run "回复我学课程《课程名称》的讨论《讨论标题》：《回复正文》"
uv run chaoxing-agent run "查看我学课程《课程名称》的作业"
uv run chaoxing-agent run "查看我学课程《课程名称》的作业《作业标题》详情"
uv run chaoxing-agent run "进入我学课程《课程名称》的作业《作业标题》开始答题"
uv run chaoxing-agent run "把我学课程《课程名称》的作业《作业标题》第1题答案改为《答案正文》并暂存"
uv run chaoxing-agent run "提交我学课程《课程名称》的作业《作业标题》"
uv run chaoxing-agent run "重做我学课程《课程名称》的作业《作业标题》"
uv run chaoxing-agent run "查看我学课程《课程名称》的作业《作业标题》作答记录"
uv run chaoxing-agent run "查看我学课程《课程名称》的作业《作业标题》第2次作答记录"
uv run chaoxing-agent run "查看我学课程《课程名称》的学习记录"
uv run chaoxing-agent run "查看我学课程《课程名称》的课程图谱"
uv run chaoxing-agent run "读取我学课程《课程名称》的图谱节点《节点名称》"
uv run chaoxing-agent run "列出《英语写作示例》的未批改作业"
uv run chaoxing-agent run "搜索招聘岗位《英语教师》，学历本科"
```

上述 `run` 是 CLI 兼容入口，中文路由器继续用于已有命令和回归测试。
动作目录中的 561 个平台动作都在中文路由器中登记；`command.plan` 和
`command.execute` 是解析与执行自然语言命令本身的两个元动作。对于参数不足的命令，
路由器返回缺失字段和补充提示，不会猜测课程、班级、人员或本地路径。

便携教师 Skill 不再把中文路由器作为自然语言主路径：宿主模型先把教师原话整理成领域、
操作、对象和值，运行器只在一个领域内返回 typed action 候选；准确 `action_id` 确定后
才绑定参数并进入统一动作运行时。旧目录排序只负责检索，永远不能凭排名授权执行。

学生端课程内容使用独立语义动作。列出作业、考试和自测只解析列表页，不进入项目、启动作答、接受诚信承诺或提交内容；资料列表只读取根目录或指定的一级文件夹，不会预览、下载或增加浏览次数。学生作业暂存只修改命令中指定的题目并保留表单其余字段，回读一致且状态仍为未交才报告成功；正式提交需要动作绑定的一次性确认，并在刷新列表显示已交后才报告成功。学生讨论可以读取详情与全部可见回复；发帖、回复、编辑和删除必须经过一次性确认，并受当前页面权限和本人身份校验约束。

查看所有 CLI 子命令：

```powershell
uv run chaoxing-agent --help
```

输出是 UTF-8 JSON。所有资源都使用平台稳定 ID，并在可以唯一解析时同时接受名称或序号。

## 连接 Codex 或其他 MCP Agent

从仓库根目录注册本地 stdio 服务：

```powershell
codex mcp add chaoxing-agent `
  --env "CHAOXING_COOKIE_FILE=$env:LOCALAPPDATA\chaoxing-agent\cookies.json" `
  -- uv run chaoxing-agent-mcp
```

服务也支持 Streamable HTTP：

```powershell
uv run chaoxing-agent mcp --transport streamable-http --host 127.0.0.1 --port 8000
```

不要把该服务直接绑定到公网地址。MCP 工具覆盖精确动作；当 Agent 无法确定能力时，先调用 `chaoxing_capabilities`。

## 风险确认

读取直接执行。以下操作需要在动作发生点进行一次性确认：

- 发布、发送、提交与共享；
- 成绩提交或覆盖；
- 教师、成员和资源权限变更；
- 删除、永久删除、清空回收站；
- 付费或消耗免费检测额度。

第一次调用返回 `confirmation_required`，其中包含具体影响、绑定动作与参数的令牌和过期时间。用户确认后，Agent 必须使用完全相同的动作与参数再次调用。令牌五分钟失效、只能使用一次，参数变化后不能复用。

## 成功判定

HTTP 200 不是完成证据。写操作会尽量执行以下一种或多种验证：

- 回读并比对新状态；
- 确认新增对象出现并取得稳定 ID；
- 确认删除对象从刷新列表消失；
- 在验证失败时恢复原状态或明确报告无法恢复的边界。

页面令牌、上传授权和临时签名只保存在单次请求内存中，不进入工具结果、日志或仓库。

## 平台边界

能力目录区分三种事实：

- `observed`：当前账号页面出现了入口；
- `implemented`：仓库存在可调用的语义动作；
- `live_verified`：该动作已在真实平台上执行并检查后置条件。

平台功能会随账号权限、学校采购、维护状态和超星更新而变化。入口返回“暂无数据”“系统维护中”或没有 HTTP 地址时，项目会如实报告当前不可用状态，不会伪造操作。

## 开发与验收

```powershell
uv run ruff format --check .
uv run ruff check .
uv run pytest
uv build
```

新增动作的最小流程：

1. 从当前网页与响应确认真实入口、请求字段、权限和成功信号；
2. 在 `capabilities.py` 登记动作、风险和实测状态；
3. 在统一 HTTP API 与 `ActionRuntime` 中实现；
4. 暴露 MCP 工具，并在适合时添加中文路由；
5. 添加页面/API 夹具测试、确认门测试和无浏览器实机验证。

项目规则见 [AGENTS.md](AGENTS.md)，运行结构见 [架构说明](docs/architecture.md)，安全边界见 [SECURITY.md](SECURITY.md)。

严禁提交 Cookie、密码、学生作业、成绩、下载的账号数据、浏览器配置或本地确认/状态文件。
