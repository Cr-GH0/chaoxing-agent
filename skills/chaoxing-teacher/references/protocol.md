# 执行协议

所有命令都由宿主 Agent 运行，教师不运行命令。Windows 下 `<runner>` 是通过 PowerShell 调用的本 Skill `scripts/run.ps1`；它固定使用安装包内的官方 CPython，不检查或调用系统 Python。账号和密码分别作为参数传入；PowerShell 中用单引号包住参数值，并把值内的单引号写成两个单引号。非 Windows 下 `<runner>` 是 `python3 -S scripts/chaoxing_teacher.py`，宿主须有 Python 3.11+。脚本输出 UTF-8 JSON。HTTP 组件已随 Skill 打包，运行时不下载依赖，不读取或修改教师的全局 pip/uv 配置。账号会话按账号隔离，首选状态目录不可写时自动改用可写目录。

## 无输入操作

- `doctor`：无状态检查内置 HTTP 运行时和离线依赖；不会要求或创建可写状态目录。
- `session`：检查已保存会话。
- `logout`：退出当前账号并删除该账号的本地会话、确认令牌和临时状态。
- `domains --query "教师完整原话" --limit 20`：检索教师端领域。结果只帮助宿主缩小范围，排序不授权执行。
- `catalog --query "关键词" --limit 50`：旧命令检索兼容入口。`safe_to_auto_select` 固定为 `false`，不得据此执行。
- `describe homework-list`：根据内部 `command_id` 返回中文语义及完整参数结构。
- `capabilities --query 作业 --limit 50`：查看对应语义动作的 `observed`、`implemented` 和 `live_verified` 状态。

`domains`、`catalog` 与 `capabilities` 支持 `--offset` 和 `--limit`；单页最多 200 项。

## 登录操作

`session` 返回 `login_required` 时，宿主 Agent 先在聊天中询问“请输入学习通账号。”，收到回复后再询问“请输入学习通密码。”。教师直接以明文回复。拿到两项后，宿主立即运行：

```text
<runner> login '--username=教师原样输入的账号' '--password=教师原样输入的密码' '--fid=-1'
```

宿主按自身命令行的普通引号规则传入两个值，不改写账号或密码；账号、密码都使用带 `=` 的单参数形式，使以 `-` 开头的值不会被解析成选项。登录成功后保存会话 Cookie、再次检查会话，并继续教师登录前提出的原任务。`login` 也保留标准输入 JSON 兼容方式：

```json
{"username":"教师输入的账号","password":"教师输入的密码","fid":"-1"}
```

## JSON 参数操作

正式教师流程把一行 JSON 作为单独的 `--input-json=<JSON>` 参数传给相应操作；PowerShell 中用单引号包住整个参数，并把 JSON 内容已有的单引号写成两个单引号。这样命令始终直接调用本 Skill 入口，不需要管道、临时文件或额外终端命令。标准输入方式仅为旧客户端保留。

执行精确命令：

```json
{"command_id":"courses","arguments":[]}
```

```json
{"command_id":"homeworks","arguments":["--course","课程名称","--clazz","班级名称"]}
```

对应调用为 `<runner> invoke '--input-json={...}'`。`arguments` 必须使用 `describe` 返回的选项和位置参数，每一项均为字符串。不要把多个参数合并成一个字符串。

提交宿主已经理解的结构化意图：

```json
{
  "request":"看看英语写作二班还有哪些作业没改",
  "domain":"homework",
  "operation":["查看","列出"],
  "keywords":["未批改"],
  "entities":{"course":"英语写作","clazz":"二班"},
  "values":{}
}
```

对应调用为 `<runner> intent '--input-json={...}'`。`request` 保存教师原话用于追溯；脚本不再从中猜动作。`domain` 是 `domains` 返回的准确领域；`operation` 和 `keywords` 只用于在该领域内召回候选；`entities` 与 `values` 保存宿主从原话中读出的对象和值，但不会自动变成执行参数。候选结果固定返回 `selection_status: requires_model_choice`，不得把第一候选当作选择结果。若结果为 `not_implemented` 并带有 `known_gap`，说明当前请求命中了已知缺口；不得改选相近动作代替。

选定准确动作并完成真实对象解析后，再次运行 `intent`：

```json
{
  "request":"看看英语写作二班还有哪些作业没改",
  "domain":"homework",
  "operation":["查看","列出"],
  "keywords":["未批改"],
  "entities":{"course":"英语写作","clazz":"二班"},
  "values":{},
  "action_id":"homework.list_ungraded",
  "parameters":{"course":"英语写作","clazz":"二班"}
}
```

只有 `status: selected` 表示 action 已由准确 ID 选定；把返回的 `execution.payload` 原样交给 `action`。这一步只验证动作属于当前教师端目录且已经实现，不替代参数完整性、真实对象解析、风险确认或执行后验证。

执行已知语义动作：

```json
{"action":"homework.assignments.list","parameters":{"course":"课程名称","clazz":"班级名称"}}
```

对应调用为 `<runner> action '--input-json={...}'`。仅在动作名和参数已经从当前能力目录确定时使用。控制动作、学生端动作、目录外动作和仅观察未实现的动作不能从该入口执行。结果中的 `capability` 固定给出动作的风险、实现状态和发布包既往 `live_verified` 状态；本次是否完成仍以返回的回读或其他可观察后置条件为准。

`status: selected` 结果中的 `parameter_adapters` 是现有精确 CLI 适配器及参数结构。只有无法直接确定 typed action 参数名称时才使用 `describe` 和 `invoke`。该路径不解析自然语言，只把已确定参数转换为同一动作运行时的调用。

`plan` 和 `execute` 仍保留给旧客户端和路由器回归测试，不属于教师请求的正式执行协议。

## 登录与确认状态

- `login_required` 或会话检查结果中的 `logged_in: false`：先询问“请输入学习通账号。”，收到后再询问“请输入学习通密码。”；用两项明文运行 `login`，登录后继续原请求。
- `needs_input`：只询问会改变真实对象或结果的缺失字段。
- `confirmation_required`：展示 `confirmation.summary`，等待教师确认；不得提前执行。
- `verification_required`：学习通平台要求验证码或二次验证；展示平台验证入口，完成后重试登录，不得继续原操作或使用旧账号代替。
- `busy`：按 `retry_after_seconds` 自动重试，不询问教师。
- `out_of_scope`：学生端请求，不执行。
- `not_implemented`：只报告已观察但未实现，不能改称已完成。
- `ok`：仍需读取返回结果中的后置条件，确认实际对象和状态。

确认后的 typed action 必须保持原 action 和 parameters 不变，只增加：

```json
{"action":"原动作标识","parameters":{"原参数":"原值"},"confirmation_token":"返回的单次令牌"}
```

若使用精确命令适配器，则保持原来的 `command_id` 与 `arguments`，只追加 `--confirmation-token` 和返回令牌。令牌过期、已使用或参数变化时，重新获取确认。
