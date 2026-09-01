$ErrorActionPreference = "Stop"
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$operation = if ($args.Count -gt 0) { [string]$args[0] } else { "" }
$arguments = if ($args.Count -gt 1) { @($args[1..($args.Count - 1)]) } else { @() }
$statePath = Join-Path $PSScriptRoot ".eval-login.json"
$logPath = Join-Path $PSScriptRoot ".eval-log.jsonl"

function Get-ArgumentValue([string]$prefix) {
    foreach ($argument in $arguments) {
        $text = [string]$argument
        if ($text.StartsWith($prefix, [System.StringComparison]::Ordinal)) {
            return $text.Substring($prefix.Length)
        }
    }
    return $null
}

function Get-InputPayload {
    $raw = Get-ArgumentValue "--input-json="
    if ($null -eq $raw) { return @{} }
    return $raw | ConvertFrom-Json -AsHashtable
}

function Write-Result($value) {
    [Console]::WriteLine(
        ($value | ConvertTo-Json -Compress -Depth 12 -EscapeHandling EscapeNonAscii)
    )
}

function Write-EvalLog($value) {
    $line = ($value | ConvertTo-Json -Compress -Depth 12) + [Environment]::NewLine
    [System.IO.File]::AppendAllText($logPath, $line, [System.Text.UTF8Encoding]::new($false))
}

Write-EvalLog @{ operation = $operation; arguments = $arguments }

switch ($operation) {
    "session" {
        if (Test-Path -LiteralPath $statePath) {
            Write-Result @{
                status = "ok"
                action = "session.check"
                result = @{ logged_in = $true; account_name = "端到端验收教师" }
            }
        } else {
            Write-Result @{
                status = "login_required"
                action = "session.check"
                result = @{ logged_in = $false; reason = "no_saved_session" }
                next_prompt = "请输入学习通账号。"
            }
        }
        break
    }
    "login" {
        $username = Get-ArgumentValue "--username="
        $password = Get-ArgumentValue "--password="
        if ($username -cne $env:CHAOXING_EVAL_USERNAME) {
            Write-EvalLog @{ operation = "invalid_login"; field = "username"; value = $username }
            Write-Result @{
                status = "invalid_credentials"
                invalid_field = "username"
                next_prompt = "请输入学习通账号。"
            }
            break
        }
        if ($password -cne $env:CHAOXING_EVAL_PASSWORD) {
            Write-EvalLog @{ operation = "invalid_login"; field = "password"; value = $password }
            Write-Result @{
                status = "invalid_credentials"
                invalid_field = "password"
                next_prompt = "请输入学习通密码。"
            }
            break
        }
        @{ username = $username; password = $password } |
            ConvertTo-Json -Compress |
            Set-Content -LiteralPath $statePath -Encoding utf8NoBOM
        Write-EvalLog @{ operation = "login_values"; username = $username; password = $password }
        Write-Result @{
            status = "ok"
            action = "session.login"
            result = @{ logged_in = $true; account_name = "端到端验收教师" }
            account = @{ username_hint = "***验收"; account_name = "端到端验收教师" }
        }
        break
    }
    "domains" {
        Write-Result @{
            status = "ok"
            domains = @(@{ domain = "homework"; label = "作业"; description = "教师端作业" })
        }
        break
    }
    "intent" {
        $payload = Get-InputPayload
        if ([string]::IsNullOrWhiteSpace([string]$payload.action_id)) {
            Write-Result @{
                status = "candidates"
                protocol_version = "2"
                intent = $payload
                selection_status = "requires_model_choice"
                safe_to_auto_select = $false
                candidates = @(
                    @{
                        action = @{
                            name = "homework.list_ungraded"
                            label = "列出待批作业"
                            domain = "homework"
                            risk = "read"
                            state = "implemented"
                            live_verified = $true
                            description = "返回仍有学生提交待批阅的作业及待批数量。"
                            aliases = @("未批改作业", "待批作业")
                        }
                        matched_terms = @("未批改", "待批")
                    }
                )
            }
        } else {
            Write-Result @{
                status = "selected"
                protocol_version = "2"
                selection_basis = "exact_action_id"
                intent = $payload
                action = @{
                    name = "homework.list_ungraded"
                    label = "列出待批作业"
                    domain = "homework"
                    risk = "read"
                    state = "implemented"
                    live_verified = $true
                    description = "返回仍有学生提交待批阅的作业及待批数量。"
                }
                execution = @{
                    operation = "action"
                    payload = @{
                        action = "homework.list_ungraded"
                        parameters = $payload.parameters
                    }
                }
            }
        }
        break
    }
    "action" {
        $payload = Get-InputPayload
        if ([string]$payload.action -eq "courses.list_teaching") {
            Write-Result @{
                status = "ok"
                action = "courses.list_teaching"
                result = @{ courses = @(@{ name = "英语写作"; classes = @("二班") }) }
                postcondition = @{ observed = $true; kind = "current_account_readback" }
            }
        } else {
            Write-EvalLog @{ operation = "original_task_completed"; payload = $payload }
            Write-Result @{
                status = "ok"
                action = "homework.list_ungraded"
                result = @{
                    course = "英语写作"
                    clazz = "二班"
                    assignments = @(
                        @{ title = "Unit 2 Argument Revision"; ungraded_submissions = 3 }
                    )
                }
                postcondition = @{
                    observed = $true
                    kind = "current_account_readback"
                    summary = "已读回 1 项待批作业，共 3 份待批提交。"
                }
            }
        }
        break
    }
    "invoke" {
        Write-EvalLog @{ operation = "original_task_completed"; via = "invoke" }
        Write-Result @{
            status = "ok"
            result = @{
                course = "英语写作"
                clazz = "二班"
                assignments = @(@{ title = "Unit 2 Argument Revision"; ungraded_submissions = 3 })
            }
            postcondition = @{ observed = $true; kind = "current_account_readback" }
        }
        break
    }
    default {
        Write-Result @{ status = "error"; error = "unsupported eval operation: $operation" }
        exit 2
    }
}
