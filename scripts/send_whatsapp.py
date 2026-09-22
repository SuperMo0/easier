"""Send a WhatsApp message, optionally with a document attached, via Meta's Cloud API.

Runs on GitHub Actions runners, which have the outbound network access the Claude sandbox lacks.

Meta allows free-form text and standalone documents ONLY within 24 hours of the recipient last
messaging the business number. Outside that window nothing but an approved template is
delivered, so a scheduled alert must be a template — and the CV has to travel as the template's
document header rather than as a separate message.

Usage:
    python send_whatsapp.py --message "Backend Engineer at Careem" --document /tmp/cv.pdf
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
        # An unset Actions secret arrives as an empty string rather than an absent key, so a
        # `get` default would not fire and the language would be sent blank.
        "language": os.environ.get("WHATSAPP_TEMPLATE_LANG") or "en_US",
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
    if not response.ok:
        sys.exit(f"media upload failed ({response.status_code}): {response.text}")
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
        hint = ""
        if '"code":131047' in response.text or "24" in response.text:
            hint = (
                "\n\nThis is the 24-hour window rule: free-form messages are only delivered "
                "within 24h of the recipient last messaging the business number. Set "
                "WHATSAPP_TEMPLATE to an approved template name to send at any time."
            )
        sys.exit(f"send failed ({response.status_code}): {response.text}{hint}")
    return response.json()


def template_payload(cfg: dict[str, str], message: str, media_id: str | None, filename: str) -> dict:
    components: list[dict] = []
    if media_id:
        components.append(
            {
                "type": "header",
                "parameters": [
                    {"type": "document", "document": {"id": media_id, "filename": filename}}
                ],
            }
        )
    components.append(
        {"type": "body", "parameters": [{"type": "text", "text": message[:1024]}]}
    )
    return {
        "type": "template",
        "template": {
            "name": cfg["template"],
            "language": {"code": cfg["language"]},
            "components": components,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--message", required=True)
    parser.add_argument("--document", type=Path, help="file to attach, e.g. the tailored CV")
    args = parser.parse_args()

    cfg = _config()

    if args.document and not args.document.is_file():
        sys.exit(f"document not found: {args.document}")

    media_id = upload_media(cfg, args.document) if args.document else None

    if cfg["template"]:
        # One message carrying both the CV and the text. Works regardless of the 24h window.
        filename = args.document.name if args.document else ""
        result = send(cfg, template_payload(cfg, args.message, media_id, filename))
        print(f"template sent: {result['messages'][0]['id']}")
        return

    # No template configured: free-form, which only lands inside the 24h window.
    result = send(cfg, {"type": "text", "text": {"body": args.message[:4096]}})
    print(f"message sent: {result['messages'][0]['id']}")

    if media_id:
        result = send(
            cfg,
            {"type": "document", "document": {"id": media_id, "filename": args.document.name}},
        )
        print(f"document sent: {result['messages'][0]['id']}")


if __name__ == "__main__":
    main()
