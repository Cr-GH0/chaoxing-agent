import { readFileSync } from "node:fs";

function skipSpace(value, index) {
  while (index < value.length && (value[index] === " " || value[index] === "\t")) {
    index += 1;
  }
  return index;
}

function readQuoted(value, index) {
  const quote = value[index];
  if (quote !== "'" && quote !== '"') return null;
  let result = "";
  index += 1;
  while (index < value.length) {
    const character = value[index];
    if (character === "\r" || character === "\n") return null;
    if (character === quote) {
      if (quote === "'" && value[index + 1] === "'") {
        result += "'";
        index += 2;
        continue;
      }
      return { value: result, next: index + 1 };
    }
    if (quote === '"' && (character === "$" || character === "`")) return null;
    result += character;
    index += 1;
  }
  return null;
}

function hasRunnerPath(path) {
  const segments = path.replaceAll("\\", "/").split("/").filter(Boolean);
  if (segments.length < 3) return false;
  const end = segments.slice(-2).map((part) => part.toLowerCase());
  if (end[0] !== "scripts" || end[1] !== "run.ps1") return false;
  const possibleRoots = [segments.at(-3), segments.at(-4)]
    .filter(Boolean)
    .map((part) => part.toLowerCase());
  return possibleRoots.includes("chaoxing-teacher");
}

function hasSafeArguments(value, index) {
  const unsafeBare = /[\s'";&|<>`$(){}\[\]#]/u;
  while (true) {
    index = skipSpace(value, index);
    if (index === value.length) return true;
    let consumed = false;
    while (index < value.length && value[index] !== " " && value[index] !== "\t") {
      if (value[index] === "'") {
        const quoted = readQuoted(value, index);
        if (!quoted) return false;
        consumed = true;
        index = quoted.next;
        continue;
      }
      if (unsafeBare.test(value[index])) return false;
      consumed = true;
      index += 1;
    }
    if (!consumed) return false;
  }
}

export function isDirectRunnerCommand(command) {
  if (typeof command !== "string" || /[\r\n]/.test(command)) return false;
  let index = skipSpace(command, 0);
  if (command[index] !== "&") return false;
  index = skipSpace(command, index + 1);
  const runner = readQuoted(command, index);
  if (!runner || !hasRunnerPath(runner.value)) return false;
  return hasSafeArguments(command, runner.next);
}

function response(decision, reason) {
  if (decision !== "allow") return { continue: true };
  return {
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "allow",
      permissionDecisionReason: reason,
    },
  };
}

let input = {};
try {
  const raw = readFileSync(0, "utf8");
  input = JSON.parse(raw || "{}");
} catch {
  input = {};
}

const toolName = input.tool_name ?? input.toolName;
const toolInput = input.tool_input ?? input.toolInput ?? {};
const allowed = toolName === "PowerShell" && isDirectRunnerCommand(toolInput.command);
process.stdout.write(
  JSON.stringify(
    response(allowed ? "allow" : undefined, "Direct call to the bundled Chaoxing runner."),
  ),
);
