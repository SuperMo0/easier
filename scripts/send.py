"""Send one notification on every channel that's configured: Telegram, WhatsApp, or both.

Telegram (send_telegram.py) is the dependable one. WhatsApp (send_whatsapp.py) goes out from
Meta's test number with a Marketing template, which Meta throttles to a few a day; --plain
sends it as plain text instead, delivered only within 24 hours of his last WhatsApp message to
the number. A channel is used when its secrets are set, and the send counts as done when at
least one channel delivered it to Meta or Telegram.

Usage:
    python send.py --message "APPLIED · Backend Engineer at Careem" [--document cv.pdf] [--plain]
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--message", required=True)
    parser.add_argument("--document", type=Path)
    parser.add_argument("--plain", action="store_true", help="WhatsApp only: plain text instead of the template")
    args = parser.parse_args()

    base = ["--message", args.message] + (["--document", str(args.document)] if args.document else [])
    channels = []
    if os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"):
        channels.append(("Telegram", "send_telegram.py", []))
    if os.environ.get("META_TOKEN") and os.environ.get("PHONE_NUMBER_ID") and os.environ.get("WHATSAPP_RECIPIENT"):
        channels.append(("WhatsApp", "send_whatsapp.py", ["--plain"] if args.plain else []))
    if not channels:
        sys.exit("no notification channel configured (Telegram or WhatsApp secrets)")

    delivered = []
    for name, script, extra in channels:
        if subprocess.run([sys.executable, str(SCRIPTS / script), *base, *extra]).returncode == 0:
            delivered.append(name)
        else:
            print(f"{name}: send failed", file=sys.stderr)
    print(f"sent via: {', '.join(delivered) or 'nothing'}")
    sys.exit(0 if delivered else 1)


if __name__ == "__main__":
    main()
