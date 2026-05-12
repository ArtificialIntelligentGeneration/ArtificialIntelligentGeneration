"""Sanitized lead scoring model for AI-assisted website outbound."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LeadFacts:
    company_name: str
    website_url: str
    niche: str
    has_public_business_contact: bool
    has_existing_website: bool
    mobile_issues: bool
    unclear_offer: bool
    weak_first_screen: bool
    outdated_visuals: bool
    slow_or_broken_pages: bool
    strong_local_intent: bool
    public_proof_points: int
    legal_or_reputation_risk: bool = False


@dataclass(frozen=True)
class LeadScore:
    total: int
    decision: str
    reasons: list[str]
    next_step: str


def score_lead(facts: LeadFacts) -> LeadScore:
    score = 0
    reasons: list[str] = []

    if facts.legal_or_reputation_risk:
        return LeadScore(
            total=0,
            decision="skip",
            reasons=["legal/reputation risk must be resolved first"],
            next_step="do not contact",
        )

    if facts.has_existing_website:
        score += 15
        reasons.append("existing website gives a concrete comparison target")
    if facts.has_public_business_contact:
        score += 10
        reasons.append("public company-level contact path exists")
    if facts.mobile_issues:
        score += 15
        reasons.append("mobile UX likely loses leads")
    if facts.unclear_offer:
        score += 15
        reasons.append("offer is hard to understand quickly")
    if facts.weak_first_screen:
        score += 15
        reasons.append("first screen can be improved for conversion")
    if facts.outdated_visuals:
        score += 10
        reasons.append("visual refresh can create obvious before/after value")
    if facts.slow_or_broken_pages:
        score += 10
        reasons.append("technical quality issue is visible")
    if facts.strong_local_intent:
        score += 10
        reasons.append("local service intent makes conversion improvements valuable")
    if facts.public_proof_points >= 3:
        score += 10
        reasons.append("enough public proof points to personalize demo")

    score = min(score, 100)
    if score >= 75:
        decision = "build-demo"
        next_step = "generate personalized demo and review manually"
    elif score >= 50:
        decision = "research-more"
        next_step = "collect missing public proof points before demo"
    else:
        decision = "skip"
        next_step = "do not spend production time yet"

    return LeadScore(total=score, decision=decision, reasons=reasons, next_step=next_step)


if __name__ == "__main__":
    sample = LeadFacts(
        company_name="Example Local Service",
        website_url="https://example.com",
        niche="window repair",
        has_public_business_contact=True,
        has_existing_website=True,
        mobile_issues=True,
        unclear_offer=True,
        weak_first_screen=True,
        outdated_visuals=True,
        slow_or_broken_pages=False,
        strong_local_intent=True,
        public_proof_points=4,
    )
    print(score_lead(sample))
