#!/usr/bin/env python3
"""
Generates the "Politics in 60" script for South African youth (16-35).

Runs via GitHub Actions every 30 minutes. Each run:
  1. Loads the previous story (if any) for context.
  2. Calls the Claude API with the web_search tool so every fact is sourced
     live, and asks the model to decide whether there is a genuinely NEW
     political development since the previous story.
  3. If yes: writes a new timestamped story, updates latest.json and the
     archive index.
  4. If no: does nothing, and the workflow's git step finds no diff, so
     nothing is committed and the site keeps showing the last real story.

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
political commentator whose audience is 16-35 year olds. You are called every 30 minutes.
Your job each time is to check for a genuinely NEW or meaningfully UPDATED South African
political story, event, or piece of legislation/by-law since the previous story you were
told about, and if one exists, write a short-form video script for it (spoken length
30-60 seconds, ~90-150 words).

HARD RULES:
1. Every factual claim MUST be verifiable in this run's web search results. Do not use
   prior knowledge for facts, dates, names, or figures.
2. Only cite these source domains (or their direct reporting): {", ".join(APPROVED_SOURCES)}.
   Do not use unnamed blogs, aggregators without bylines, or social media posts as sources.
3. Tone: energetic, plain-spoken, informative, never inflammatory. Explain WHY it matters
   to a young South African specifically (jobs, voting, cost of living, safety, opportunity).
4. Stay factually neutral on contested party politics: report what happened and its
   real-world implications/advantages/disadvantages; do not editorialize about which
   party is right.
5. Do NOT manufacture a "new" story just to have one. Minor rewording of the same news,
   or routine/no news, is NOT new. Only flag something new if a reasonable person would
   agree it's a distinct development (a bill passing a new stage, a new ruling, a new
   scandal, a new poll, a new policy announcement, etc).
6. Output STRICT JSON ONLY, no markdown fences, no commentary, matching exactly one of
   these two shapes:

   If there IS a new/updated story:
   {{
     "is_new": true,
     "headline": "short punchy headline, under 10 words",
     "script": "the full spoken script, 90-150 words",
     "estimated_seconds": integer,
     "why_it_matters": "one sentence, youth-framed",
     "sources": [{{"title": "...", "url": "...", "publisher": "..."}}]
   }}

   If there is NOT a new/updated story since the previous one:
   {{
     "is_new": false
   }}
"""


def load_previous():
    base = os.path.join(os.path.dirname(__file__), "..", "docs", "data")
    latest_path = os.path.join(os.path.abspath(base), "latest.json")
    if not os.path.exists(latest_path):
        return None
    with open(latest_path) as f:
        return json.load(f)


def call_claude(previous):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    now_sast = datetime.now(SAST)

    if previous:
        prev_context = (
            f"PREVIOUS STORY (published {previous.get('published_at_sast', previous.get('date',''))}):\n"
            f"Headline: {previous.get('headline','')}\n"
            f"Script: {previous.get('script','')}\n"
        )
    else:
        prev_context = "PREVIOUS STORY: none — this is the first run, so any relevant current story counts as new.\n"

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
                        f"Current date/time: {now_sast.strftime('%Y-%m-%d %H:%M')} SAST.\n\n"
                        f"{prev_context}\n"
                        "Search for current South African political news and decide, per your "
                        "instructions, whether there is a genuinely new/updated story since the "
                        "previous one. Respond with the correct JSON shape."
                    ),
                }
            ],
            "tools": [{"type": "web_search_20250305", "name": "web_search"}],
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()

    text = "".join(
        block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
    )
    text = text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        print("ERROR: could not find JSON in model output:\n" + text, file=sys.stderr)
        sys.exit(1)

    payload = json.loads(match.group(0))
    payload["_now_sast"] = now_sast
    return payload


def write_outputs(payload):
    now_sast = payload.pop("_now_sast")
    payload["published_at_sast"] = now_sast.strftime("%Y-%m-%d %H:%M")
    payload["generated_at_utc"] = datetime.now(timezone.utc).isoformat()

    story_id = now_sast.strftime("%Y%m%d-%H%M")

    base = os.path.join(os.path.dirname(__file__), "..", "docs", "data")
    base = os.path.abspath(base)
    os.makedirs(os.path.join(base, "archive"), exist_ok=True)

    latest_path = os.path.join(base, "latest.json")
    archive_path = os.path.join(base, "archive", f"{story_id}.json")

    with open(latest_path, "w") as f:
        json.dump(payload, f, indent=2)
    with open(archive_path, "w") as f:
        json.dump(payload, f, indent=2)

    index_path = os.path.join(base, "archive-index.json")
    if os.path.exists(index_path):
        with open(index_path) as f:
            index = json.load(f)
    else:
        index = []

    entry = {
        "id": story_id,
        "published_at_sast": payload["published_at_sast"],
        "headline": payload.get("headline", ""),
    }
    index = [e for e in index if e["id"] != story_id]  # dedupe
    index.append(entry)
    index.sort(key=lambda e: e["id"], reverse=True)

    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)

    print(f"New story written: {story_id} — {payload.get('headline','')}")


if __name__ == "__main__":
    previous_story = load_previous()
    result = call_claude(previous_story)

    if result.get("is_new"):
        del result["is_new"]
        write_outputs(result)
    else:
        print("No new story this run — leaving latest.json untouched.")
