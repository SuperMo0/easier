"""Send a WhatsApp message, optionally with a document attached, via Meta's Cloud API.

Runs on GitHub Actions runners, which have the outbound network access the Claude sandbox lacks.

Usage:
    python send_whatsapp.py --message "Tailored CV ready for Careem" --document applications/careem/cv.pdf
"""

import argparse
import mimetypes
import os
import sys
from pathlib import Path

import requests

API_VERSION = "v25.0"
BASE = f"https://graph.facebook.com/{API_VERSION}"


def _config() -> dict[str, str]:
    missing = [k for k in ("META_TOKEN", "PHONE_NUMBER_ID", "WHATSAPP_RECIPIENT") if not os.environ.get(k)]
    if missing:
        sys.exit(f"missing required environment variables: {', '.join(missing)}")
    return {
        "token": os.environ["META_TOKEN"],
        "phone_id": os.environ["PHONE_NUMBER_ID"],
        "recipient": os.environ["WHATSAPP_RECIPIENT"],
        "template": os.environ.get("WHATSAPP_TEMPLATE", ""),
    }


def upload_media(cfg: dict[str, str], path: Path) -> str:
    """Upload a file to Meta's media store and return its media ID."""
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    with path.open("rb") as fh:
        response = requests.post(
            f"{BASE}/{cfg['phone_id']}/media",
            headers={"Authorization": f"Bearer {cfg['token']}"},
            data={"messaging_product": "whatsapp", "type": mime},
            files={"file": (path.name, fh, mime)},
            timeout=120,
        )
    response.raise_for_status()
    return response.json()["id"]


def send(cfg: dict[str, str], payload: dict) -> dict:
    response = requests.post(
        f"{BASE}/{cfg['phone_id']}/messages",
        headers={
            "Authorization": f"Bearer {cfg['token']}",
            "Content-Type": "application/json",
        },
        json={"messaging_product": "whatsapp", "to": cfg["recipient"], **payload},
        timeout=60,
    )
    if not response.ok:
        sys.exit(f"send failed ({response.status_code}): {response.text}")
    return response.json()


def text_payload(cfg: dict[str, str], message: str) -> dict:
    # Outside the 24h customer-service window Meta rejects free-form text, so prefer an
    # approved template when one is configured.
    if cfg["template"]:
        return {
            "type": "template",
            "template": {
                "name": cfg["template"],
                "language": {"code": "en_US"},
                "components": [
                    {"type": "body", "parameters": [{"type": "text", "text": message[:1024]}]}
                ],
            },
        }
    return {"type": "text", "text": {"body": message[:4096]}}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--message", required=True)
    parser.add_argument("--document", type=Path, help="file to attach, e.g. the tailored CV")
    args = parser.parse_args()

    cfg = _config()

    result = send(cfg, text_payload(cfg, args.message))
    print(f"message sent: {result['messages'][0]['id']}")

    if args.document:
        if not args.document.is_file():
            sys.exit(f"document not found: {args.document}")
        media_id = upload_media(cfg, args.document)
        result = send(
            cfg,
            {
                "type": "document",
                "document": {"id": media_id, "filename": args.document.name},
            },
        )
        print(f"document sent: {result['messages'][0]['id']}")


if __name__ == "__main__":
    main()
