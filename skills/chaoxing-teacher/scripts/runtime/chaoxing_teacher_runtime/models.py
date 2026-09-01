from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class ActionRisk(StrEnum):
    READ = "read"
    NAVIGATE = "navigate"
    DRAFT = "draft"
    WRITE = "write"
    PERMISSION = "permission"
    PURCHASE = "purchase"
    PUBLISH = "publish"
    DELETE = "delete"

    @property
    def requires_confirmation(self) -> bool:
        return self in {self.PERMISSION, self.PURCHASE, self.PUBLISH, self.DELETE}


class CapabilityState(StrEnum):
    OBSERVED = "observed"
    IMPLEMENTED = "implemented"


@dataclass(frozen=True, slots=True)
class ActionSpec:
    name: str
    label: str
    domain: str
    risk: ActionRisk
    state: CapabilityState
    implementation: str
    live_verified: bool = False
    description: str = ""
    aliases: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["risk"] = self.risk.value
        payload["state"] = self.state.value
        payload["aliases"] = list(self.aliases)
        return payload


@dataclass(slots=True)
class CommandPlan:
    command: str
    action: str | None
    parameters: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    missing_fields: list[str] = field(default_factory=list)
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
