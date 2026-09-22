"""Fetch full job postings from leads the model found by searching.

The Claude sandbox can search the web but cannot open a page; GitHub Actions runners can
open anything but cannot judge what is worth opening. So the model writes leads here and
this script, running on a runner, turns each one into a full posting record.

Usage:
    python fetch_leads.py
"""

import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
LEADS = ROOT / "jobs" / "leads.json"
TARGETS = ROOT / "companies" / "uae-targets.yaml"

TIMEOUT = 20
HEADERS = {"User-Agent": "easier-job-discovery/1.0"}

sys.path.insert(0, str(ROOT / "scripts"))
from discover import _strip_html, _wanted, job_id, seen_ids, write_job  # noqa: E402


def _api_url(url: str) -> tuple[str, str] | None:
    """Map an ATS job page to its JSON endpoint — far more reliable than parsing HTML."""
    if m := re.search(r"greenhouse\.io/(?:embed/job_app\?for=)?([\w-]+)/jobs/(\d+)", url):
        slug, jid = m.groups()
        return "greenhouse", f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs/{jid}"
    if m := re.search(r"jobs\.lever\.co/([\w-]+)/([\w-]+)", url):
        slug, jid = m.groups()
        return "lever", f"https://api.lever.co/v0/postings/{slug}/{jid}"
    if m := re.search(r"jobs\.smartrecruiters\.com/([\w-]+)/(\d+)", url):
        _, jid = m.groups()
        return "smartrecruiters", f"https://api.smartrecruiters.com/v1/postings/{jid}"
    return None


def _from_api(kind: str, payload: dict) -> tuple[str, str, str]:
    if kind == "greenhouse":
        return (payload.get("title", ""),
                (payload.get("location") or {}).get("name", ""),
                _strip_html(payload.get("content", "")))
    if kind == "lever":
        return (payload.get("text", ""),
                (payload.get("categories") or {}).get("location", ""),
                _strip_html(payload.get("descriptionPlain") or payload.get("description", "")))
    # smartrecruiters
    loc = payload.get("location") or {}
    sections = (payload.get("jobAd") or {}).get("sections") or {}
    body = " ".join(
        _strip_html((sections.get(k) or {}).get("text", ""))
        for k in ("jobDescription", "qualifications", "additionalInformation")
    )
    return (payload.get("name", ""),
            ", ".join(filter(None, [loc.get("city"), loc.get("country")])),
            body.strip())


def fetch_one(lead: dict) -> dict | None:
    url = lead["url"]
    api = _api_url(url)
    try:
        if api:
            kind, endpoint = api
            response = requests.get(endpoint, headers=HEADERS, timeout=TIMEOUT)
            response.raise_for_status()
            title, location, body = _from_api(kind, response.json())
        else:
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            response.raise_for_status()
            body = _strip_html(response.text)[:12000]
            title, location = lead.get("title", ""), lead.get("location", "")
    except Exception as exc:
        print(f"  !! {url}: {type(exc).__name__}")
        return None

    return {
        "company": lead.get("company", ""),
        "ats": lead.get("source", "search"),
        "title": (title or lead.get("title", "")).strip(),
        "location": (location or lead.get("location", "")).strip(),
        "url": url,
        "description": body,
        "discovered": date.today().isoformat(),
        "via": "model-search",
    }


def main() -> None:
    if not LEADS.is_file():
        print("no leads file"); return
    leads = json.loads(LEADS.read_text())
    if not leads:
        print("no leads"); return

    filters = yaml.safe_load(TARGETS.read_text()).get("filters", {})
    already = seen_ids()
    added = skipped = 0

    with ThreadPoolExecutor(max_workers=8) as pool:
        for future in as_completed({pool.submit(fetch_one, l): l for l in leads}):
            record = future.result()
            if not record or not record["title"]:
                continue
            if not _wanted(record, filters):
                skipped += 1
                print(f"  · filtered: {record['title'][:60]}")
                continue
            ident = job_id(record)
            if ident in already:
                continue
            write_job(record)
            already.add(ident)
            added += 1
            print(f"  ✓ {record['company']:<16} {record['title'][:56]}")

    print(f"\n{added} posting(s) fetched from leads, {skipped} filtered out")
    LEADS.write_text("[]")  # consumed


if __name__ == "__main__":
    main()
