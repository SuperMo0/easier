"""Application stats by level: internship, junior and mid-level roles he has applied to.

Counts every application: the ones easier made (jobs/<folder>/job.json with status
`applied`) and the ones he made himself outside it (jobs/outside.json). Nothing is ever
removed; rejections are counted, just hidden from the lists unless asked for.

Usage (through `easier`, or directly):
    easier --stats                  counts per level and stage
    easier --stats junior           the junior applications (also: intern, mid, unknown, all)
    easier --stats junior --rejected    include rejected ones in the list
"""

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JOBS = ROOT / "jobs"
OUTSIDE = JOBS / "outside.json"

LEVELS = ["Internship", "Junior", "Mid-level", "Unknown"]
STAGES = ["applied", "assessment", "interview", "offer", "rejected"]
# `easier --stats <word>` accepts a few spellings for each level.
LEVEL_ARGS = {"intern": "Internship", "internship": "Internship", "internships": "Internship",
              "junior": "Junior", "juniors": "Junior", "entry": "Junior", "graduate": "Junior",
              "mid": "Mid-level", "mid-level": "Mid-level", "midlevel": "Mid-level",
              "unknown": "Unknown", "all": None}

# The Notion table's "Level" formula uses the same rules, so both always agree.
INTERN = re.compile(r"intern( |$|,|ship|\))|fellowship|residen")
JUNIOR = re.compile(r"junior|(^| )jr[ .]|entry|graduate|trainee|new grad|associate|early career|program|ypp| (i|1)( |$)")


def level_of(title: str) -> str:
    t = " ".join(title.lower().split())
    if "not named" in t:
        return "Unknown"
    if INTERN.search(t):
        return "Internship"
    if JUNIOR.search(t):
        return "Junior"
    return "Mid-level"


def stage_of(status: str, stage: str | None = None) -> str:
    """Where an application stands; `stage` (set by the email check) wins over plain 'applied'."""
    stage = (stage or "").lower()
    if stage in ("assessment", "interview", "offer", "rejected"):
        return stage
    return status.lower() if status.lower() in STAGES else "applied"


def load() -> tuple[list[dict], int]:
    """Every application (easier's and his own), plus how many easier jobs still wait on him."""
    apps, waiting = [], 0
    for job_file in sorted(JOBS.glob("*/job.json")):
        job = json.loads(job_file.read_text())
        if job.get("status") in ("needs-you", "tailored"):
            waiting += 1
        if job.get("status") != "applied":
            continue
        apps.append({"company": job.get("company", ""), "title": job.get("title", ""),
                     "stage": stage_of("applied", job.get("stage")),
                     "applied": job.get("applied_at") or job_file.parent.name[:10],
                     "url": job.get("url"), "by": "easier"})
    if OUTSIDE.is_file():
        for row in json.loads(OUTSIDE.read_text()):
            apps.append({"company": row.get("company", ""), "title": row.get("title", ""),
                         "stage": stage_of(row.get("status", "applied")),
                         "applied": row.get("applied"), "url": row.get("url"), "by": "you"})
    for app in apps:
        app["level"] = level_of(app["title"])
    return apps, waiting


def print_counts(apps: list[dict], waiting: int) -> None:
    dates = sorted(a["applied"] for a in apps if a["applied"])
    since = f" since {dates[0]}" if dates else ""
    print(f"{len(apps)} applications{since}" + (f" · {waiting} more waiting to be sent (see Notion → Pending)" if waiting else ""))
    print()
    width = max(len(l) for l in LEVELS) + 2
    print("".ljust(width) + "".join(s.rjust(12) for s in STAGES) + "total".rjust(8))
    for level in LEVELS + ["Total"]:
        rows = apps if level == "Total" else [a for a in apps if a["level"] == level]
        if not rows and level == "Unknown":
            continue
        cells = [sum(1 for a in rows if a["stage"] == s) for s in STAGES]
        print(level.ljust(width) + "".join(str(c).rjust(12) for c in cells) + str(len(rows)).rjust(8))
    print()
    print("Lists: easier --stats intern | junior | mid | all   (add --rejected to include rejections)")


def print_list(apps: list[dict], level: str | None, rejected: bool) -> None:
    rows = [a for a in apps if (level is None or a["level"] == level) and (rejected or a["stage"] != "rejected")]
    rows.sort(key=lambda a: a["applied"] or "", reverse=True)
    title = level or "All"
    print(f"{title} applications: {len(rows)}" + ("" if rejected else " (rejections hidden; add --rejected)"))
    for a in rows:
        mark = "" if a["stage"] == "applied" else f" [{a['stage'].upper()}]"
        print(f"  {a['applied'] or '          '}  {a['company']} — {a['title']}{mark}")
        if a["url"]:
            print(f"              {a['url']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Application stats by level")
    parser.add_argument("level", nargs="?", help="intern, junior, mid, unknown or all")
    parser.add_argument("--rejected", action="store_true", help="include rejected applications in the list")
    args = parser.parse_args()
    apps, waiting = load()
    if not args.level:
        print_counts(apps, waiting)
        return
    key = args.level.lower()
    if key not in LEVEL_ARGS:
        parser.error(f"unknown level {args.level!r}: use intern, junior, mid, unknown or all")
    print_list(apps, LEVEL_ARGS[key], args.rejected)


if __name__ == "__main__":
    main()
