from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    cookie_file: Path | None
    request_timeout: float
    confirmation_file: Path | None = None
    state_file: Path | None = None

    @classmethod
    def from_env(cls) -> Settings:
        cookie_value = os.getenv("CHAOXING_COOKIE_FILE", "").strip()
        confirmation_value = os.getenv("CHAOXING_CONFIRMATION_FILE", "").strip()
        state_value = os.getenv("CHAOXING_STATE_FILE", "").strip()
        confirmation_file: Path | None = None
        state_file: Path | None = None
        local_data = os.getenv("LOCALAPPDATA", "").strip() or os.getenv("TEMP", "").strip()
        if confirmation_value:
            confirmation_file = Path(confirmation_value).expanduser().resolve()
        elif cookie_value:
            if local_data:
                confirmation_file = (
                    Path(local_data).expanduser().resolve()
                    / "chaoxing-agent"
                    / "confirmations.json"
                )
        if state_value:
            state_file = Path(state_value).expanduser().resolve()
        elif cookie_value and local_data:
            state_file = Path(local_data).expanduser().resolve() / "chaoxing-agent" / "state.json"
        return cls(
            cookie_file=Path(cookie_value).expanduser().resolve() if cookie_value else None,
            request_timeout=float(os.getenv("CHAOXING_REQUEST_TIMEOUT", "20")),
            confirmation_file=confirmation_file,
            state_file=state_file,
        )
