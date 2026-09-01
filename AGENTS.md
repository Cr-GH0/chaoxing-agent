# Project rules

This repository exists to make Chaoxing operations callable by MCP-capable agents from natural-language requests.

- Treat the current Chaoxing UI and responses from the current account as the authority. Do not invent selectors, endpoints, fields, success states, or coverage.
- The shipped runtime is HTTP-only: it must never launch or require a browser, browser extension, WebDriver, or Chaoxing client. A browser may be used only during development to observe requests and postconditions.
- Add every operation to the capability catalog before exposing it. Keep `observed`, `implemented`, and `live_verified` distinct.
- Route operations through the action runtime. A successful tool result must include the observable postcondition used to verify it.
- Reads may run directly. Publishing, sending, score submission, permission changes, and deletion require an action-bound confirmation immediately before execution.
- Never commit cookies, passwords, downloaded submissions, grade plans, or other account runtime data.
- Preserve Chinese text as UTF-8 and add a focused fixture or test for every parsed page/API shape.
- Keep the project agent-neutral: MCP is the primary interface; the CLI exercises the same runtime rather than implementing a second behavior path.
