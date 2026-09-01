from __future__ import annotations

import hashlib
import json
import os
import secrets
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ConfirmationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ConfirmationChallenge:
    token: str
    action: str
    summary: str
    expires_at: str

    def to_dict(self) -> dict[str, str]:
        return {
            "token": self.token,
            "action": self.action,
            "summary": self.summary,
            "expires_at": self.expires_at,
        }


@dataclass(slots=True)
class _Pending:
    action: str
    fingerprint: str
    summary: str
    expires_at: float


class ConfirmationGate:
    """One-time confirmations bound to an exact action and parameter payload."""

    def __init__(
        self,
        ttl_seconds: int = 300,
        storage_path: Path | None = None,
    ) -> None:
        self.ttl_seconds = ttl_seconds
        self.storage_path = storage_path.expanduser().resolve() if storage_path else None
        self._pending: dict[str, _Pending] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _fingerprint(action: str, parameters: dict[str, Any]) -> str:
        canonical = json.dumps(
            {"action": action, "parameters": parameters},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def issue(self, action: str, parameters: dict[str, Any], summary: str) -> ConfirmationChallenge:
        now = time.time()
        expires_at = now + self.ttl_seconds
        token = secrets.token_urlsafe(24)
        pending = _Pending(
            action=action,
            fingerprint=self._fingerprint(action, parameters),
            summary=summary,
            expires_at=expires_at,
        )
        with self._lock:
            self._load()
            self._prune(now)
            self._pending[token] = pending
            self._save()
        return ConfirmationChallenge(
            token=token,
            action=action,
            summary=summary,
            expires_at=datetime.fromtimestamp(expires_at, tz=UTC).isoformat(),
        )

    def consume(self, token: str, action: str, parameters: dict[str, Any]) -> None:
        now = time.time()
        with self._lock:
            self._load()
            self._prune(now)
            pending = self._pending.pop(token, None)
            self._save()
        if pending is None:
            raise ConfirmationError("confirmation token is missing, expired, or already used")
        if pending.action != action:
            raise ConfirmationError("confirmation token belongs to a different action")
        if pending.fingerprint != self._fingerprint(action, parameters):
            raise ConfirmationError("confirmation token parameters do not match")

    def _prune(self, now: float) -> None:
        expired = [token for token, item in self._pending.items() if item.expires_at <= now]
        for token in expired:
            self._pending.pop(token, None)

    def _load(self) -> None:
        if self.storage_path is None:
            return
        try:
            raw = self.storage_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            self._pending = {}
            return
        except OSError as exc:
            raise ConfirmationError(f"cannot read confirmation store: {exc}") from exc
        try:
            payload = json.loads(raw)
            records = payload["pending"]
            if payload.get("version") != 1 or not isinstance(records, dict):
                raise ValueError("unsupported confirmation store format")
            pending: dict[str, _Pending] = {}
            for token, record in records.items():
                if not isinstance(token, str) or not isinstance(record, dict):
                    raise ValueError("invalid confirmation record")
                action = record["action"]
                fingerprint = record["fingerprint"]
                summary = record["summary"]
                expires_at = record["expires_at"]
                if not all(isinstance(value, str) for value in (action, fingerprint, summary)):
                    raise ValueError("invalid confirmation record")
                if not isinstance(expires_at, (int, float)):
                    raise ValueError("invalid confirmation expiry")
                pending[token] = _Pending(
                    action=action,
                    fingerprint=fingerprint,
                    summary=summary,
                    expires_at=float(expires_at),
                )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ConfirmationError(f"invalid confirmation store: {exc}") from exc
        self._pending = pending

    def _save(self) -> None:
        if self.storage_path is None:
            return
        payload = {
            "version": 1,
            "pending": {
                token: {
                    "action": item.action,
                    "fingerprint": item.fingerprint,
                    "summary": item.summary,
                    "expires_at": item.expires_at,
                }
                for token, item in self._pending.items()
            },
        }
        temporary = self.storage_path.with_name(
            f".{self.storage_path.name}.{os.getpid()}.{secrets.token_hex(4)}.tmp"
        )
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_text(
                json.dumps(payload, ensure_ascii=False, sort_keys=True),
                encoding="utf-8",
            )
            temporary.replace(self.storage_path)
        except OSError as exc:
            raise ConfirmationError(f"cannot write confirmation store: {exc}") from exc
        finally:
            temporary.unlink(missing_ok=True)
