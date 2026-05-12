"""Sanitized portfolio sample: local-first agent orchestration.

This is a compact excerpt of the control-plane pattern I use for AI agent
workflows: role-scoped agents, explicit tool permissions, human approval gates,
and append-only execution events. It intentionally omits provider calls,
secrets, storage adapters, and customer-specific prompts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable, Protocol
from uuid import uuid4


class Risk(str, Enum):
    LOW = "low"
    NEEDS_APPROVAL = "needs_approval"


@dataclass(frozen=True)
class ToolCall:
    name: str
    args: dict[str, str]
    risk: Risk = Risk.LOW


@dataclass(frozen=True)
class AgentRole:
    name: str
    system_prompt: str
    allowed_tools: frozenset[str]


@dataclass
class Task:
    title: str
    objective: str
    context: dict[str, str] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid4().hex)


@dataclass(frozen=True)
class Event:
    task_id: str
    actor: str
    message: str
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class Tool(Protocol):
    name: str

    def __call__(self, **kwargs: str) -> str:
        ...


class ApprovalQueue:
    def __init__(self) -> None:
        self.pending: list[tuple[Task, AgentRole, ToolCall]] = []

    def request(self, task: Task, role: AgentRole, call: ToolCall) -> str:
        self.pending.append((task, role, call))
        return f"Approval required for {role.name}:{call.name} on task {task.id}"


class AgentOrchestrator:
    def __init__(
        self,
        tools: Iterable[Tool],
        approvals: ApprovalQueue | None = None,
    ) -> None:
        self.tools: dict[str, Tool] = {tool.name: tool for tool in tools}
        self.approvals = approvals or ApprovalQueue()
        self.events: list[Event] = []

    def run_plan(self, task: Task, role: AgentRole, plan: Iterable[ToolCall]) -> list[str]:
        outputs: list[str] = []
        self._log(task, role.name, f"started: {task.title}")

        for call in plan:
            self._ensure_allowed(role, call)

            if call.risk is Risk.NEEDS_APPROVAL:
                outputs.append(self.approvals.request(task, role, call))
                self._log(task, role.name, f"paused for approval: {call.name}")
                continue

            result = self.tools[call.name](**call.args)
            outputs.append(result)
            self._log(task, role.name, f"tool completed: {call.name}")

        self._log(task, role.name, "finished")
        return outputs

    def _ensure_allowed(self, role: AgentRole, call: ToolCall) -> None:
        if call.name not in role.allowed_tools:
            raise PermissionError(f"{role.name} cannot call {call.name}")
        if call.name not in self.tools:
            raise LookupError(f"Tool is not registered: {call.name}")

    def _log(self, task: Task, actor: str, message: str) -> None:
        self.events.append(Event(task_id=task.id, actor=actor, message=message))


class WebSearchTool:
    name = "web_search"

    def __call__(self, **kwargs: str) -> str:
        return f"searched: {kwargs['query']}"


class TelegramNotifyTool:
    name = "telegram_notify"

    def __call__(self, **kwargs: str) -> str:
        return f"queued telegram alert to {kwargs['channel']}"


def build_research_plan(company: str) -> list[ToolCall]:
    return [
        ToolCall("web_search", {"query": f"{company} hiring AI automation"}),
        ToolCall(
            "telegram_notify",
            {"channel": "operator-review", "text": f"Review lead: {company}"},
            risk=Risk.NEEDS_APPROVAL,
        ),
    ]


if __name__ == "__main__":
    researcher = AgentRole(
        name="researcher",
        system_prompt="Find useful signals, cite sources, and stop before outreach.",
        allowed_tools=frozenset({"web_search", "telegram_notify"}),
    )
    orchestrator = AgentOrchestrator([WebSearchTool(), TelegramNotifyTool()])
    task = Task(title="Qualify lead", objective="Find evidence that the lead needs AI ops")

    for line in orchestrator.run_plan(task, researcher, build_research_plan("Example Co")):
        print(line)
