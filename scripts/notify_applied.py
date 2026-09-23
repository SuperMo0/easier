"""WhatsApp him when a job he submitted himself (easier / assist mode) is recorded as applied.

Runs on pushes that change a jobs/*/job.json. The cloud Apply run sends its own messages, and
its commits are pushed with GITHUB_TOKEN, which never triggers another workflow, so nothing is
sent twice.

Usage:
    python notify_applied.py <before-sha> <after-sha>
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path("/tmp/applied-notify")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout


def status_at(rev: str, path: str) -> str | None:
    text = git("show", f"{rev}:{path}")
    try:
        return json.loads(text).get("status") if text else None
    except json.JSONDecodeError:
        return None


def score_of(folder: Path) -> str:
    notes = folder / "notes.md"
    if notes.is_file() and (m := re.search(r"Fit score:\s*\**\s*(\d+)", notes.read_text())):
        return m.group(1)
    return "?"


def main() -> None:
    before, after = sys.argv[1], sys.argv[2]
    if not before or set(before) == {"0"}:          # first push of a branch
        before = f"{after}~1"
    changed = [p for p in git("diff", "--name-only", before, after, "--", "jobs/*/job.json").split() if p]
    sent = 0
    for path in changed:
        job_file = ROOT / path
        if not job_file.is_file():
            continue
        job = json.loads(job_file.read_text())
        if job.get("status") != "applied" or status_at(before, path) == "applied":
            continue
        folder = job_file.parent
        message = " · ".join(filter(None, [
            "APPLIED", f"{job.get('title', '')} at {job.get('company', '')}",
            f"{score_of(folder)}% match", "submitted by you", job.get("url", ""),
        ]))
        args = [sys.executable, str(ROOT / "scripts" / "send_whatsapp.py"), "--message", message]
        if (folder / "cv.md").is_file():
            OUT.mkdir(parents=True, exist_ok=True)
            pdf = OUT / f"{folder.name}_Mwafak_Almahaini_CV.pdf"
            subprocess.run([sys.executable, str(ROOT / "scripts" / "render_pdf.py"), str(folder / "cv.md"), str(pdf)],
                           check=True)
            # The name he sees in WhatsApp is the file's own name.
            final = OUT / folder.name / "Mwafak_Almahaini_CV.pdf"
            final.parent.mkdir(parents=True, exist_ok=True)
            pdf.replace(final)
            args += ["--document", str(final)]
        print(message)
        if subprocess.run(args).returncode == 0:
            sent += 1
    print(f"{sent} message(s) sent")


if __name__ == "__main__":
    main()
