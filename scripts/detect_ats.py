"""Detect which job board a company's careers page runs on.

Careers pages almost always embed or link their applicant tracking system, so fetching the
page and looking for the board's fingerprint identifies it without guessing slugs one at a
time. Runs on GitHub Actions, which can reach these sites; the Claude sandbox cannot.

Usage:
    python detect_ats.py                       # every unverified company in the target list
    python detect_ats.py https://careers.x.com # a single careers page
"""

import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
TARGETS = ROOT / "companies" / "uae-targets.yaml"
TIMEOUT = 20
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; easier-job-discovery/1.0)"}

# Ordered: the first match wins, so put the unambiguous patterns first.
SIGNATURES = [
    ("greenhouse",      r"(?:job-)?boards(?:-api)?\.greenhouse\.io/(?:embed/job_board\?for=)?([a-z0-9_-]+)"),
    ("lever",           r"jobs\.lever\.co/([a-z0-9-]+)"),
    ("ashby",           r"jobs\.ashbyhq\.com/([a-z0-9-]+)"),
    ("workable",        r"apply\.workable\.com/([a-z0-9-]+)"),
    ("smartrecruiters", r"(?:careers|jobs)\.smartrecruiters\.com/([A-Za-z0-9_-]+)"),
    ("recruitee",       r"([a-z0-9-]+)\.recruitee\.com"),
    ("teamtailor",      r"([a-z0-9-]+)\.teamtailor\.com"),
    ("personio",        r"([a-z0-9-]+)\.jobs\.personio\.(?:de|com)"),
    ("workday",         r"([a-z0-9-]+)\.(wd\d+)\.myworkdayjobs\.com"),
]

CANDIDATE_PATHS = ["", "/careers", "/en/careers", "/jobs", "/careers/jobs", "/en-ae/careers"]


def detect(url: str) -> tuple[str, str] | None:
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
    except Exception:
        return None
    if response.status_code >= 400:
        return None
    html = response.text
    for ats, pattern in SIGNATURES:
        if m := re.search(pattern, html, re.I):
            slug = m.group(1)
            # Generic path segments are false positives, not board identifiers.
            if slug.lower() in {"embed", "www", "api", "app", "apply", "job", "jobs", "careers", "career", "search", "static", "cdn", "assets"}:
                continue
            return ats, slug
    return None


def candidate_urls(company: str, careers_url: str | None) -> list[str]:
    if careers_url:
        return [careers_url]
    base = re.sub(r"[^a-z0-9]", "", company.lower())
    return [f"https://{base}.com{p}" for p in CANDIDATE_PATHS] + \
           [f"https://careers.{base}.com", f"https://{base}.ae/careers"]


def main() -> None:
    if len(sys.argv) > 1:
        for url in sys.argv[1:]:
            print(f"{url} -> {detect(url) or 'no board detected'}")
        return

    config = yaml.safe_load(TARGETS.read_text())
    pending = [c for c in config.get("companies", []) if not c.get("verified")]
    print(f"detecting boards for {len(pending)} unverified companies\n")

    def probe(entry: dict):
        for url in candidate_urls(entry["name"], entry.get("careers_url")):
            if found := detect(url):
                return url, found
        return None

    hits = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(probe, entry): entry for entry in pending}
        for future in as_completed(futures):
            entry = futures[future]
            try:
                result = future.result()
            except Exception:
                result = None
            if not result:
                print(f"  \u00b7 {entry['name']:<22} no board detected")
                continue
            url, (ats, slug) = result
            entry["ats"], entry["slug"], entry["verified"] = ats, slug, True
            entry["careers_url"] = url
            hits += 1
            print(f"  \u2713 {entry['name']:<22} {ats}/{slug}   (via {url})")

    TARGETS.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True))
    print(f"\n{hits} board(s) detected.")


if __name__ == "__main__":
    main()
