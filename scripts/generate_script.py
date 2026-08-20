#!/usr/bin/env python3
"""
Generates the daily "Politics in 60" script for South African youth (16-35).

Runs via GitHub Actions every day at 17:00 SAST (15:00 UTC).
Calls the Claude API with the web_search tool so every fact is sourced
live rather than from the model's training data, writes the result to
docs/data/latest.json, archives it under docs/data/archive/, and updates
docs/data/archive-index.json so the hosted page can list past scripts.

Requires env var: ANTHROPIC_API_KEY
"""

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta

import requests

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-5"  # current Sonnet-tier model at time of writing
SAST = timezone(timedelta(hours=2))

APPROVED_SOURCES = [
    "sanews.gov.za", "gov.za", "parliament.gov.za", "elections.org.za",
    "news24.com", "iol.co.za", "timeslive.co.za", "citizen.co.za",
    "polity.org.za", "politicsweb.co.za", "dailymaverick.co.za",
    "ewn.co.za", "sabcnews.com", "businesslive.co.za",
]

SYSTEM_PROMPT = f"""You are a research + scriptwriting assistant for a young South African
political commentator whose audience is 16-35 year olds. Produce ONE daily short-form
video script (spoken length 30-60 seconds, ~90-150 words) covering the most relevant
current South African political story, event, or piece of legislation/by-law for that
audience.

HARD RULES:
1. Every factual claim MUST be verifiable in today's web search results. Do not use
   prior knowledge for facts, dates, names, or figures. If you are not sure, search again
   or leave it out.
2. Only cite these source domains (or their direct reporting): {", ".join(APPROVED_SOURCES)}.
   Do not use unnamed blogs, aggregators without bylines, or social media posts as sources.
3. Tone: energetic, plain-spoken, informative, never inflammatory. Explain WHY it matters
   to a young South African specifically (jobs, voting, cost of living, safety, opportunity).
4. Stay factually neutral on contested party politics: report what happened and its
   real-world implications/advantages/disadvantages; do not editorialize about which
   party is right.
5. Output STRICT JSON ONLY, no markdown fences, no commentary, matching this schema:
{{
  "date": "YYYY-MM-DD",
  "headline": "short punchy headline, under 10 words",
  "script": "the full spoken script, 90-150 words",
  "estimated_seconds": integer,
  "why_it_matters": "one sentence, youth-framed",
  "sources": [{{"title": "...", "url": "...", "publisher": "..."}}]
}}
"""


def call_claude():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    today_sast = datetime.now(SAST).strftime("%Y-%m-%d")

    resp = requests.post(
        API_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": MODEL,
            "max_tokens": 1500,
            "system": SYSTEM_PROMPT,
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Today's date is {today_sast} (South Africa). "
                        "Search for the most relevant, credible South African political "
                        "news from today, and write today's script per your instructions."
                    ),
                }
            ],
            "tools": [{"type": "web_search_20250305", "name": "web_search"}],
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()

    # Concatenate all text blocks (search results produce interleaved tool blocks)
    text = "".join(
        block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
    )

    # Strip accidental code fences and grab the JSON object
    text = text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        print("ERROR: could not find JSON in model output:\n" + text, file=sys.stderr)
        sys.exit(1)

    payload = json.loads(match.group(0))
    payload.setdefault("date", today_sast)
    payload["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    return payload


def write_outputs(payload):
    base = os.path.join(os.path.dirname(__file__), "..", "docs", "data")
    base = os.path.abspath(base)
    os.makedirs(os.path.join(base, "archive"), exist_ok=True)

    latest_path = os.path.join(base, "latest.json")
    archive_path = os.path.join(base, "archive", f"{payload['date']}.json")

    with open(latest_path, "w") as f:
        json.dump(payload, f, indent=2)
    with open(archive_path, "w") as f:
        json.dump(payload, f, indent=2)

    # Update archive index
    index_path = os.path.join(base, "archive-index.json")
    if os.path.exists(index_path):
        with open(index_path) as f:
            index = json.load(f)
    else:
        index = []

    entry = {"date": payload["date"], "headline": payload.get("headline", "")}
    index = [e for e in index if e["date"] != payload["date"]]  # dedupe
    index.append(entry)
    index.sort(key=lambda e: e["date"], reverse=True)

    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)

    print(f"Wrote {latest_path} and {archive_path}")


if __name__ == "__main__":
    result = call_claude()
    write_outputs(result)
