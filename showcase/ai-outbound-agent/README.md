# AI Outbound Agent Showcase

Sanitized excerpt from a local outbound experiment: find businesses with weak but existing websites, generate a personalized redesign demo, and prepare a low-volume, legally cautious outreach workflow.

## Flow

```text
public lead discovery
  -> company-level fact sheet
  -> weak-site scoring
  -> demo generation brief
  -> QA / visual review
  -> human-approved outreach draft
  -> inbox monitor for warm replies
```

The private folder contains real lead lists, company names, deployed demos, email logs, and CRM state. Those are intentionally omitted here. This showcase keeps the architecture and scoring logic only.

## Included Files

- [`lead_scoring.py`](./lead_scoring.py) - generic scoring model for website/outbound fit.
- [`agent_roster.json`](./agent_roster.json) - role split for a small multi-agent outbound workflow.

## Safety Rules

- company-level public data only;
- no mass messaging without legal review;
- no personal contacts unless there is a legitimate public business context;
- human review before any real outbound send;
- clear opt-out / do-not-contact hygiene.
