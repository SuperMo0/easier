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
from discover import (ATS, JOBS, _normalise, _strip_html, _wanted, job_id, lever_body,  # noqa: E402
                      seen_ids, write_job)


def _from_board(url: str, company: str) -> dict | None:
    """Workable and Ashby have no per-job endpoint worth using; read the company's board
    and pick this posting out of it."""
    if m := re.search(r"apply\.workable\.com/([\w-]+)/j/([0-9a-z]+)", url, re.I):
        kind, slug, key = "workable", m[1], m[2].upper()
        match = lambda j: (j.get("shortcode") or "").upper() == key  # noqa: E731
    elif m := re.search(r"jobs\.ashbyhq\.com/([\w.-]+)/([0-9a-f-]{36})", url, re.I):
        kind, slug, key = "ashby", m[1], m[2].lower()
        match = lambda j: (j.get("id") or "").lower() == key or key in (j.get("jobUrl") or "")  # noqa: E731
    else:
        return None
    response = requests.get(ATS[kind].format(slug=slug), headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    raw = next((j for j in response.json().get("jobs", []) if match(j)), None)
    if raw is None:
        raise LookupError("posting no longer on the board")
    record = _normalise(kind, company, raw)
    if record:
        record["via"] = "model-search"
    return record


def _api_url(url: str) -> tuple[str, str] | None:
    """Map an ATS job page to its JSON endpoint — far more reliable than parsing HTML."""
    if m := re.search(r"(\beu\.)?greenhouse\.io/(?:embed/job_app\?for=)?([\w-]+)/jobs/(\d+)", url):
        eu, slug, jid = m.groups()
        host = "boards-api.eu.greenhouse.io" if eu else "boards-api.greenhouse.io"
        return "greenhouse", f"https://{host}/v1/boards/{slug}/jobs/{jid}"
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
                lever_body(payload))
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


def _why(exc: Exception) -> str:
    """HTTP status when there is one (404/410 means the posting is gone, 403/429 a refusal)."""
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        return f"HTTP {exc.response.status_code}"
    return f"{type(exc).__name__}: {exc}" if str(exc) else type(exc).__name__


def fetch_one(lead: dict) -> dict | None:
    url = lead["url"]
    api = _api_url(url)
    try:
        if record := _from_board(url, lead.get("company", "")):
            return record
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
        # Aggregators (Glassdoor, Indeed, Bayt) often refuse a runner. When the search already
        # gave a description, keep the lead on that rather than lose a real opening.
        if lead.get("description") and lead.get("title"):
            print(f"  ~ {url}: {_why(exc)}, kept from search summary")
            title, location, body = lead["title"], lead.get("location", ""), lead["description"]
        else:
            print(f"  !! {url}: {_why(exc)}")
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


def refresh() -> None:
    """Re-read the full posting for every open job folder whose stored description is thin,
    so tailoring works from the whole JD rather than an intro paragraph."""
    updated = 0
    for job_file in sorted(JOBS.glob("*/job.json")):
        job = json.loads(job_file.read_text())
        if job.get("status") not in ("new", "tailored") or not job.get("url"):
            continue
        api = _api_url(job["url"])
        try:
            if record := _from_board(job["url"], job.get("company", "")):
                body = record["description"]
            elif api:
                response = requests.get(api[1], headers=HEADERS, timeout=TIMEOUT)
                response.raise_for_status()
                _, _, body = _from_api(api[0], response.json())
            else:
                continue
        except Exception as exc:
            print(f"  !! {job_file.parent.name}: {_why(exc)}")
            continue
        if len(body) > len(job.get("description", "")) + 200:
            job["description"] = body
            job_file.write_text(json.dumps(job, indent=2, ensure_ascii=False))
            updated += 1
            print(f"  ✓ {job_file.parent.name}: {len(body)} chars")
    print(f"\n{updated} description(s) refreshed")


def main() -> None:
    if "--refresh" in sys.argv:
        refresh(); return
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
