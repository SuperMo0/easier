"""Regenerate jobs/INDEX.md — one table of every job folder, newest and best first.

Run after anything that adds, tailors or prunes jobs, so browsing the repo always starts
from an accurate list.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JOBS = ROOT / "jobs"

ORDER = ["applied", "needs-you", "review-first", "tailored", "new"]
LABEL = {
    "applied": "Applied",
    "needs-you": "Needs you",
    "review-first": "Review first",
    "tailored": "Tailored, not sent",
    "new": "New",
}


def score_of(folder: Path) -> int | None:
    notes = folder / "notes.md"
    if notes.is_file():
        if m := re.search(r"Fit score:\s*\**\s*(\d+)", notes.read_text()):
            return int(m.group(1))
    return None


def main() -> None:
    rows = []
    for job_file in JOBS.glob("*/job.json"):
        folder = job_file.parent
        try:
            job = json.loads(job_file.read_text())
        except json.JSONDecodeError:
            continue
        rows.append({
            "folder": folder.name,
            "date": job.get("discovered", ""),
            "company": job.get("company", ""),
            "title": job.get("title", ""),
            "status": job.get("status", "new"),
            "url": job.get("url", ""),
            "score": score_of(folder),
        })

    rows.sort(key=lambda r: (r["date"], r["score"] or 0), reverse=True)
    counts = {s: sum(1 for r in rows if r["status"] == s) for s in ORDER}

    lines = [
        "# Jobs",
        "",
        "Every job has its own folder holding the posting (`job.json`), the tailored CV (`cv.md`),",
        "the cover letter (`cover-letter.md`) and the fit notes (`notes.md`).",
        "",
        " · ".join(f"**{LABEL[s]}:** {counts[s]}" for s in ORDER if counts[s]) or "No jobs yet.",
        "",
        "| Date | Company | Role | Score | Status | Folder | Apply |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        score = f"{r['score']}" if r["score"] is not None else "—"
        title = r["title"].replace("|", "/")
        lines.append(
            f"| {r['date']} | {r['company']} | {title} | {score} | {LABEL.get(r['status'], r['status'])} "
            f"| [open](./{r['folder']}/) | [link]({r['url']}) |"
        )
    (JOBS / "INDEX.md").write_text("\n".join(lines) + "\n")
    print(f"INDEX.md: {len(rows)} job(s)")


if __name__ == "__main__":
    main()
