"""Fetch job postings from company ATS boards and write new ones to jobs/incoming/.

Runs on GitHub Actions runners. Most companies host their careers page on one of a handful of
applicant tracking systems, each of which exposes a public JSON board API — far more reliable
than scraping rendered HTML.

Modes:
    python discover.py fetch            # pull postings for every verified company
    python discover.py probe careem     # find which ATS a company uses
"""

import argparse
import hashlib
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
TARGETS = ROOT / "companies" / "uae-targets.yaml"
INCOMING = ROOT / "jobs" / "incoming"
PROCESSED = ROOT / "jobs" / "processed"

TIMEOUT = 10
HEADERS = {"User-Agent": "easier-job-discovery/1.0"}

ATS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true",
    "lever": "https://api.lever.co/v0/postings/{slug}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true",
    "smartrecruiters": "https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100",
    "recruitee": "https://{slug}.recruitee.com/api/offers/",
    "teamtailor": "https://{slug}.teamtailor.com/jobs.json",
    "personio": "https://{slug}.jobs.personio.de/search.json",
}


def _strip_html(raw: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw or "", flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = (
        text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        .replace("&nbsp;", " ").replace("&#39;", "'").replace("&quot;", '"')
    )
    return re.sub(r"\s+", " ", text).strip()


def _normalise(ats: str, company: str, raw: dict) -> dict | None:
    """Flatten one ATS's posting shape into the common record we store."""
    if ats == "greenhouse":
        title, url = raw.get("title"), raw.get("absolute_url")
        location = (raw.get("location") or {}).get("name", "")
        body = _strip_html(raw.get("content", ""))
    elif ats == "lever":
        title, url = raw.get("text"), raw.get("hostedUrl")
        location = (raw.get("categories") or {}).get("location", "")
        body = _strip_html(raw.get("descriptionPlain") or raw.get("description", ""))
    elif ats == "ashby":
        title, url = raw.get("title"), raw.get("jobUrl")
        location = raw.get("location", "")
        body = _strip_html(raw.get("descriptionHtml") or raw.get("descriptionPlain", ""))
    elif ats == "smartrecruiters":
        title = raw.get("name")
        uuid = raw.get("id", "")
        url = f"https://jobs.smartrecruiters.com/{raw.get('company', {}).get('identifier', '')}/{uuid}"
        loc = raw.get("location") or {}
        location = ", ".join(filter(None, [loc.get("city"), loc.get("country")]))
        body = ""  # SmartRecruiters needs a second call per posting for the body
    elif ats == "recruitee":
        title, url = raw.get("title"), raw.get("careers_url")
        location = raw.get("location", "")
        body = _strip_html(raw.get("description", ""))
    elif ats == "teamtailor":
        title, url = raw.get("title"), raw.get("careersite-job-url")
        location = raw.get("location", "")
        body = _strip_html(raw.get("body", ""))
    elif ats == "personio":
        title, url = raw.get("name"), raw.get("url")
        location = raw.get("office", "")
        body = _strip_html(raw.get("description", ""))
    else:
        return None

    if not title or not url:
        return None

    return {
        "company": company,
        "ats": ats,
        "title": title.strip(),
        "location": (location or "").strip(),
        "url": url,
        "description": body,
        "discovered": date.today().isoformat(),
    }


def _wanted(record: dict, filters: dict) -> bool:
    """Boards serve every role in every country; keep only what's worth tailoring for."""
    title = record["title"].lower()
    location = record["location"].lower()

    locations = [s.lower() for s in filters.get("locations", [])]
    if locations and not any(s in location for s in locations):
        return False

    excluded = [s.lower() for s in filters.get("title_exclude", [])]
    if any(s in title for s in excluded):
        return False

    included = [s.lower() for s in filters.get("title_include", [])]
    return not included or any(s in title for s in included)


def _postings(ats: str, payload) -> list:
    """Each ATS buries its posting list somewhere different."""
    if isinstance(payload, list):
        return payload
    for key in ("jobs", "content", "offers", "data", "postings"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return []


def fetch_board(ats: str, slug: str) -> list:
    response = requests.get(ATS[ats].format(slug=slug), headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    return _postings(ats, response.json())


def job_id(record: dict) -> str:
    return hashlib.sha256(record["url"].encode()).hexdigest()[:16]


def seen_ids() -> set[str]:
    return {p.stem for p in list(INCOMING.glob("*.json")) + list(PROCESSED.glob("*.json"))}


def cmd_fetch() -> None:
    config = yaml.safe_load(TARGETS.read_text())
    filters = config.get("filters", {})
    INCOMING.mkdir(parents=True, exist_ok=True)
    already = seen_ids()
    added = skipped = 0

    for entry in config.get("companies", []):
        if not entry.get("verified") or entry.get("ats") not in ATS:
            continue
        name, ats, slug = entry["name"], entry["ats"], entry["slug"]
        try:
            postings = fetch_board(ats, slug)
        except Exception as exc:  # a single dead board must not stop the run
            print(f"  !! {name} ({ats}/{slug}): {exc}")
            continue

        kept = 0
        for raw in postings:
            record = _normalise(ats, name, raw)
            if not record:
                continue
            if not _wanted(record, filters):
                skipped += 1
                continue
            ident = job_id(record)
            if ident in already:
                continue
            (INCOMING / f"{ident}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False))
            already.add(ident)
            added += 1
            kept += 1

        print(f"  {name}: {len(postings)} on the board, {kept} kept")

    print(f"\n{added} new job(s) written to jobs/incoming/ ({skipped} filtered out)")


def cmd_probe(slug: str) -> None:
    """Try every ATS for a slug and report which one answers with real postings."""
    print(f"probing '{slug}':\n")
    for ats in ATS:
        try:
            postings = fetch_board(ats, slug)
        except Exception as exc:
            print(f"  {ats:<16} —  {type(exc).__name__}")
            continue
        if postings:
            sample = _normalise(ats, slug, postings[0])
            title = sample["title"] if sample else "?"
            print(f"  {ats:<16} ✓  {len(postings)} postings (e.g. {title!r})")
        else:
            print(f"  {ats:<16} .  reachable, no postings")


def _find_board(slug: str, preferred: str | None) -> tuple[str, int] | None:
    """Return the ATS serving this slug and how many postings it has, trying the declared one first."""
    order = ([preferred] if preferred in ATS else []) + [a for a in ATS if a != preferred]
    for ats in order:
        try:
            postings = fetch_board(ats, slug)
        except Exception:
            continue
        if postings:
            return ats, len(postings)
    return None


def cmd_verify() -> None:
    """Probe every company in the target list and record which ATS actually serves it.

    Probes run concurrently: sequentially this is 36 companies x 7 systems x the timeout,
    which runs to over an hour of mostly waiting on hosts that will never answer.
    """
    config = yaml.safe_load(TARGETS.read_text())
    companies = config.get("companies", [])
    found = 0

    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = {
            pool.submit(_find_board, entry["slug"], entry.get("ats")): entry
            for entry in companies
        }
        for future in as_completed(futures):
            entry = futures[future]
            name, slug = entry["name"], entry["slug"]
            try:
                result = future.result()
            except Exception as exc:
                result = None
                print(f"  ! {name:<24} probe error: {exc}")
            if result:
                ats, count = result
                entry["ats"], entry["verified"] = ats, True
                found += 1
                print(f"  ✓ {name:<24} {ats}/{slug} — {count} postings")
            else:
                entry["verified"] = False
                print(f"  · {name:<24} no board found for slug '{slug}'")

    TARGETS.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True))
    print(f"\n{found}/{len(companies)} companies verified.")
    print("Unverified ones need a different slug, or sit on Workday / a bespoke careers page.")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("fetch")
    sub.add_parser("verify")
    probe = sub.add_parser("probe")
    probe.add_argument("slug")
    args = parser.parse_args()

    if args.command == "fetch":
        cmd_fetch()
    elif args.command == "verify":
        cmd_verify()
    else:
        cmd_probe(args.slug)


if __name__ == "__main__":
    main()
