"""Sanitized portfolio sample: async job routing for Telegram-like feeds.

The production version connects to MTProto clients, persistent storage, and
operator channels. This excerpt keeps only the core decision loop: normalize an
incoming post, deduplicate it, score relevance, and route strong candidates for
human review.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import AsyncIterator, Protocol


@dataclass(frozen=True)
class IncomingPost:
    chat_id: str
    message_id: str
    text: str
    url: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class JobLead:
    title: str
    score: int
    reason: str
    source_url: str | None
    fingerprint: str


class SeenStore(Protocol):
    async def contains(self, fingerprint: str) -> bool:
        ...

    async def add(self, fingerprint: str) -> None:
        ...


class MemorySeenStore:
    def __init__(self) -> None:
        self._seen: set[str] = set()

    async def contains(self, fingerprint: str) -> bool:
        return fingerprint in self._seen

    async def add(self, fingerprint: str) -> None:
        self._seen.add(fingerprint)


class OperatorQueue(Protocol):
    async def send(self, lead: JobLead) -> None:
        ...


class PrintQueue:
    async def send(self, lead: JobLead) -> None:
        print(f"[{lead.score}] {lead.title} - {lead.reason}")


AI_TERMS = {
    "ai",
    "llm",
    "agent",
    "agents",
    "automation",
    "openai",
    "python",
    "n8n",
    "telegram",
    "playwright",
}

NEGATIVE_TERMS = {
    "unpaid",
    "internship",
    "crypto shill",
    "casino",
}


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fingerprint(post: IncomingPost) -> str:
    stable = f"{post.chat_id}:{normalize(post.text)[:400]}"
    return sha256(stable.encode("utf-8")).hexdigest()


def score_post(post: IncomingPost) -> JobLead | None:
    text = normalize(post.text)

    if any(term in text for term in NEGATIVE_TERMS):
        return None

    matches = sorted(term for term in AI_TERMS if term in text)
    if not matches:
        return None

    score = min(100, 35 + len(matches) * 12)
    if "full-time" in text or "contract" in text or "freelance" in text:
        score += 10
    if "remote" in text:
        score += 5

    title = extract_title(post.text)
    reason = "matched: " + ", ".join(matches[:5])
    return JobLead(
        title=title,
        score=min(score, 100),
        reason=reason,
        source_url=post.url,
        fingerprint=fingerprint(post),
    )


def extract_title(text: str) -> str:
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "Job lead")
    return first_line[:90]


class JobRouter:
    def __init__(self, seen: SeenStore, queue: OperatorQueue, threshold: int = 65) -> None:
        self.seen = seen
        self.queue = queue
        self.threshold = threshold

    async def process(self, posts: AsyncIterator[IncomingPost]) -> int:
        routed = 0
        async for post in posts:
            lead = score_post(post)
            if lead is None or lead.score < self.threshold:
                continue
            if await self.seen.contains(lead.fingerprint):
                continue

            await self.seen.add(lead.fingerprint)
            await self.queue.send(lead)
            routed += 1
        return routed


async def demo_feed() -> AsyncIterator[IncomingPost]:
    samples = [
        "Looking for a Python AI agent engineer, remote contract, OpenAI + Playwright.",
        "Unpaid internship for crypto shill campaign.",
        "Need n8n automation for Telegram lead routing and LLM summarization.",
    ]
    for index, text in enumerate(samples, start=1):
        yield IncomingPost(chat_id="jobs", message_id=str(index), text=text)
        await asyncio.sleep(0)


if __name__ == "__main__":
    routed_count = asyncio.run(JobRouter(MemorySeenStore(), PrintQueue()).process(demo_feed()))
    print(f"routed: {routed_count}")
