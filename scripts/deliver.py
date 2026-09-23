"""Send one notification (Telegram and/or WhatsApp) per application in apply-manifest.json, CV attached.

Each send runs in its own process so one failure never stops the rest.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    manifest = ROOT / "apply-manifest.json"
    if not manifest.is_file():
        print("no manifest; nothing to deliver")
        return
    failures = 0
    for entry in json.loads(manifest.read_text()):
        args = [sys.executable, str(ROOT / "scripts" / "send.py"), "--message", entry["message"]]
        if Path(entry.get("cv_pdf", "")).is_file():
            args += ["--document", entry["cv_pdf"]]
        if subprocess.run(args).returncode != 0:
            failures += 1
    print(f"delivered {len(json.loads(manifest.read_text())) - failures}, failed {failures}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
