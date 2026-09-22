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
JOBS = ROOT / "jobs"
# Every job id ever seen, one per line. Folders get pruned and skipped jobs are never given
# one, but the id stays here so neither is rediscovered and rescored.
SEEN = JOBS / ".seen"

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
    "workable": "https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true",
}


def _strip_html(raw: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw or "", flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = (
        text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        .replace("&nbsp;", " ").replace("&#39;", "'").replace("&quot;", '"')
    )
    return re.sub(r"\s+", " ", text).strip()


_LOCATION_KEYS = {
    "location", "locations", "alllocations", "secondarylocations", "city", "country", "region",
    "office", "offices", "additionaloffices", "addresscountry", "addresslocality", "addressregion",
    "locationstext", "locationname", "workplacetype",
}


def _all_locations(primary, raw: dict) -> str:
    """Primary location first, then every other place the posting mentions."""
    found: list[str] = []

    def walk(node, under_location: bool = False) -> None:
        if isinstance(node, str):
            if under_location and node.strip():
                found.append(node.strip())
        elif isinstance(node, dict):
            for key, value in node.items():
                walk(value, under_location or key.lower() in _LOCATION_KEYS or
                     (under_location and key.lower() in {"name", "text", "label"}))
        elif isinstance(node, list):
            for item in node:
                walk(item, under_location)

    walk(raw)
    parts, seen = [], set()
    for item in [primary if isinstance(primary, str) else ""] + found:
        key = item.lower()
        if item and key not in seen and len(item) < 120:
            seen.add(key)
            parts.append(item)
    return " | ".join(parts)


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
    elif ats == "workable":
        title, url = raw.get("title"), raw.get("url") or raw.get("shortlink")
        loc = raw.get("location") or {}
        location = ", ".join(filter(None, [loc.get("city"), loc.get("country")]))
        body = _strip_html(raw.get("description", ""))
    else:
        return None

    if not title or not url:
        return None

    return {
        "company": company,
        "ats": ats,
        "title": title.strip(),
        "location": _all_locations(location, raw),
        "url": url,
        "description": body,
        "discovered": date.today().isoformat(),
    }


def _matches(term: str, text: str) -> bool:
    """Whole-word match. Plain substring matching fires on fragments: 'ml' hits 'AML',
    'ai' hits 'Compliance AI', and non-engineering roles sail through the filter."""
    return re.search(rf"\b{re.escape(term.strip())}\b", text) is not None


def _wanted(record: dict, filters: dict) -> bool:
    """Boards serve every role in every country; keep only what's worth tailoring for."""
    title = record["title"].lower()
    location = record["location"].lower()

    locations = [s.lower() for s in filters.get("locations", [])]
    if locations and not any(s in location for s in locations):
        return False

    excluded = [s.lower() for s in filters.get("title_exclude", [])]
    if any(_matches(s, title) for s in excluded):
        return False

    included = [s.lower() for s in filters.get("title_include", [])]
    return not included or any(_matches(s, title) for s in included)


def _postings(ats: str, payload) -> list:
    """Each ATS buries its posting list somewhere different."""
    if isinstance(payload, list):
        return payload
    for key in ("jobs", "content", "offers", "data", "postings"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return []


def _fetch_smartrecruiters(slug: str) -> list:
    """SmartRecruiters pages at 100, and parent companies like Delivery Hero list thousands of
    postings worldwide — the first page is almost never the UAE's. Ask for the UAE directly and
    page through it; if the country filter comes back empty, crawl the board and filter locally."""
    base = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings"

    def crawl(params: dict, max_pages: int) -> list:
        out, offset = [], 0
        for _ in range(max_pages):
            response = requests.get(base, params={**params, "limit": 100, "offset": offset},
                                    headers=HEADERS, timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()
            page = data.get("content", [])
            out.extend(page)
            offset += len(page)
            if not page or offset >= data.get("totalFound", 0):
                break
        return out

    return crawl({"country": "ae"}, max_pages=20) or crawl({}, max_pages=15)


def fetch_board(ats: str, slug: str) -> list:
    if ats == "smartrecruiters":
        return _fetch_smartrecruiters(slug)
    response = requests.get(ATS[ats].format(slug=slug), headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    return _postings(ats, response.json())


# Workday is not a slug-and-GET board like the others: every tenant has its own hostname,
# a data-centre number, and one or more named sites, and the job list comes from a POST.
WORKDAY_HOST = "https://{tenant}.{dc}.myworkdayjobs.com"
WORKDAY_DCS = ("wd1", "wd3", "wd5", "wd101", "wd103")


def fetch_workday(host: str, site: str, limit: int = 100) -> list:
    response = requests.post(
        f"{host}/wday/cxs/{host.split('//')[1].split('.')[0]}/{site}/jobs",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={"appliedFacets": {}, "limit": limit, "offset": 0, "searchText": ""},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json().get("jobPostings", [])


def _normalise_workday(company: str, host: str, site: str, raw: dict) -> dict | None:
    title = raw.get("title")
    path = raw.get("externalPath")
    if not title or not path:
        return None
    return {
        "company": company,
        "ats": "workday",
        "title": title.strip(),
        "location": (raw.get("locationsText") or "").strip(),
        "url": f"{host}/en-US/{site}{path}",
        "description": "",  # Workday serves the body from a separate per-posting endpoint
        "discovered": date.today().isoformat(),
    }


def cmd_probe_workday(tenant: str) -> None:
    """Sweep the plausible Workday host and site combinations for a tenant.

    The data-centre number and site name can't be derived from the company name, so the
    only way to find a live board without a browser is to try the common shapes.
    """
    sites = [
        f"{tenant}_Careers", f"{tenant.upper()}_Careers", "External", "Careers",
        "External_Careers", f"{tenant}careers", f"{tenant}Careers", "careers",
    ]
    print(f"probing Workday for '{tenant}':\n")
    hits = 0
    for dc in WORKDAY_DCS:
        host = WORKDAY_HOST.format(tenant=tenant, dc=dc)
        for site in sites:
            try:
                postings = fetch_workday(host, site, limit=1)
            except Exception:
                continue
            if postings:
                hits += 1
                print(f"  ✓ {host}/{site}  — postings found")
    if not hits:
        print("  no live board found; the tenant name or site is different")


def job_id(record: dict) -> str:
    return hashlib.sha256(record["url"].encode()).hexdigest()[:16]


def _slugify(text: str, limit: int) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:limit].rstrip("-")


def job_folders() -> list[Path]:
    return sorted(p.parent for p in JOBS.glob("*/job.json"))


def seen_ids() -> set[str]:
    ids = set()
    if SEEN.is_file():
        ids |= {line.strip() for line in SEEN.read_text().splitlines() if line.strip()}
    for folder in job_folders():
        try:
            ids.add(json.loads((folder / "job.json").read_text())["id"])
        except (KeyError, json.JSONDecodeError):
            pass
    return ids


def mark_seen(ident: str) -> None:
    JOBS.mkdir(parents=True, exist_ok=True)
    with SEEN.open("a") as fh:
        fh.write(ident + "\n")


def write_job(record: dict) -> Path:
    """Give a posting its own folder, named so a person browsing the repo can find it.

    Everything about one job — the posting, the tailored CV, the cover letter, the notes —
    lives together in this folder for the rest of its life.
    """
    if not (record.get("url") or "").startswith(("http://", "https://")):
        raise ValueError(f"refusing to store a job without an apply link: {record.get('title')!r}")
    ident = job_id(record)
    record = {"id": ident, "status": "new", **record}
    name = f"{record['discovered']}_{_slugify(record['company'], 24)}_{_slugify(record['title'], 50)}"
    folder = JOBS / name
    if folder.exists():  # same company, title and day but a different posting
        folder = JOBS / f"{name}_{ident[:6]}"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "job.json").write_text(json.dumps(record, indent=2, ensure_ascii=False))
    mark_seen(ident)
    return folder


def _smartrecruiters_body(slug: str, posting_id: str) -> str:
    """SmartRecruiters lists postings without their text, so the body needs its own call."""
    try:
        response = requests.get(
            f"https://api.smartrecruiters.com/v1/companies/{slug}/postings/{posting_id}",
            headers=HEADERS, timeout=TIMEOUT,
        )
        response.raise_for_status()
        sections = (response.json().get("jobAd") or {}).get("sections") or {}
    except Exception:
        return ""
    return " ".join(
        _strip_html((sections.get(k) or {}).get("text", ""))
        for k in ("companyDescription", "jobDescription", "qualifications", "additionalInformation")
    ).strip()


def _role_key(company: str, title: str) -> str:
    return f"{_slugify(company, 40)}::{_slugify(title, 80)}"


def existing_roles() -> set[str]:
    keys = set()
    for folder in job_folders():
        try:
            job = json.loads((folder / "job.json").read_text())
            keys.add(_role_key(job.get("company", ""), job.get("title", "")))
        except json.JSONDecodeError:
            pass
    return keys


def cmd_fetch() -> None:
    config = yaml.safe_load(TARGETS.read_text())
    filters = config.get("filters", {})
    already = seen_ids()
    roles = existing_roles()
    added = skipped = reposts = 0

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
            if job_id(record) in already:
                continue
            key = _role_key(record["company"], record["title"])
            if key in roles:  # same role reposted under a new URL
                mark_seen(job_id(record))
                already.add(job_id(record))
                reposts += 1
                continue
            roles.add(key)
            if ats == "smartrecruiters" and not record["description"]:
                record["description"] = _smartrecruiters_body(slug, raw.get("id", ""))
            write_job(record)
            already.add(job_id(record))
            added += 1
            kept += 1

        if kept:
            print(f"  {name}: {len(postings)} on the board, {kept} new")

    print(f"\n{added} new job folder(s) written ({skipped} filtered out, {reposts} reposts skipped)")


def cmd_prune(untouched_days: int, handled_days: int) -> None:
    """Delete stale job folders so the repo doesn't pile up.

    A job never tailored after a month has almost always been filled. Handled jobs are kept
    longer as a record of what was sent. Ids stay in .seen either way, so nothing returns.
    """
    today = date.today()
    removed = 0
    for folder in job_folders():
        try:
            job = json.loads((folder / "job.json").read_text())
            age = (today - date.fromisoformat(job.get("discovered", ""))).days
        except (ValueError, json.JSONDecodeError):
            continue  # unparseable record: leave it rather than guess
        limit = untouched_days if job.get("status", "new") == "new" else handled_days
        if age > limit:
            for child in folder.iterdir():
                child.unlink()
            folder.rmdir()
            removed += 1
    print(f"pruned {removed} folder(s) (untailored >{untouched_days}d, handled >{handled_days}d)")


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


def _slug_variants(name: str, slug: str) -> list[str]:
    """Plausible board identifiers for a company.

    A board slug rarely matches the trading name: Talabat sits under its parent Delivery Hero,
    Dubizzle under its group, and plenty of companies append 'careers' or drop punctuation.
    """
    base = re.sub(r"[^a-z0-9 ]", "", name.lower()).strip()
    words = base.split()
    joined = "".join(words)
    variants = [
        slug, joined, base.replace(" ", "-"), base.replace(" ", ""),
        words[0] if words else base,
        f"{joined}careers", f"{joined}group", f"{joined}technologies", f"{joined}tech",
        f"{joined}hq", f"{joined}jobs",
    ]
    seen, out = set(), []
    for v in variants:
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    return out


def cmd_find_slugs() -> None:
    """Sweep slug variants for every unverified company and record any live board."""
    config = yaml.safe_load(TARGETS.read_text())
    companies = [c for c in config.get("companies", []) if not c.get("verified")]
    print(f"sweeping {len(companies)} unverified companies\n")

    def probe(entry):
        for slug in _slug_variants(entry["name"], entry["slug"]):
            found = _find_board(slug, entry.get("ats"))
            if found:
                return slug, found[0], found[1]
        return None

    hits = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(probe, e): e for e in companies}
        for future in as_completed(futures):
            entry = futures[future]
            try:
                result = future.result()
            except Exception:
                result = None
            if result:
                slug, ats, count = result
                entry["slug"], entry["ats"], entry["verified"] = slug, ats, True
                hits += 1
                print(f"  ✓ {entry['name']:<24} {ats}/{slug} — {count} postings")
            else:
                print(f"  · {entry['name']:<24} no variant found")

    TARGETS.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True))
    print(f"\n{hits} newly verified.")


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
    sub.add_parser("find-slugs")
    probe = sub.add_parser("probe")
    probe.add_argument("slug")
    prune = sub.add_parser("prune")
    prune.add_argument("--untouched-days", type=int, default=30)
    prune.add_argument("--handled-days", type=int, default=90)
    workday = sub.add_parser("probe-workday")
    workday.add_argument("tenant")
    args = parser.parse_args()

    if args.command == "fetch":
        cmd_fetch()
    elif args.command == "verify":
        cmd_verify()
    elif args.command == "find-slugs":
        cmd_find_slugs()
    elif args.command == "prune":
        cmd_prune(args.untouched_days, args.handled_days)
    elif args.command == "probe-workday":
        cmd_probe_workday(args.tenant)
    else:
        cmd_probe(args.slug)


if __name__ == "__main__":
    main()
