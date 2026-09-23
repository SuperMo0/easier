"""Send a Telegram message, optionally with a document attached, through a bot.

No templates, no 24-hour window and no per-day limits for messages to someone who has pressed
Start in the bot, which is why this is the reliable channel; WhatsApp from a test number is
best-effort (see send_whatsapp.py).

Environment: TELEGRAM_BOT_TOKEN (from @BotFather) and TELEGRAM_CHAT_ID (his chat with the bot).

Usage:
    python send_telegram.py --message "APPLIED · Backend Engineer at Careem" --document /tmp/cv.pdf
    python send_telegram.py --find-chat     # after pressing Start: print the chat ids the bot has seen
"""

import argparse
import os
import sys
from pathlib import Path

import requests

CAPTION_LIMIT = 1024   # Telegram's limit for a document caption
TEXT_LIMIT = 4096      # and for a message


def call(token: str, method: str, **kwargs) -> dict:
    response = requests.post(f"https://api.telegram.org/bot{token}/{method}", timeout=120, **kwargs)
    body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
    if not body.get("ok"):
        hint = ""
        if "chat not found" in str(body.get("description", "")):
            hint = " (open the bot in Telegram and press Start first, then check TELEGRAM_CHAT_ID)"
        sys.exit(f"telegram {method} failed ({response.status_code}): {body.get('description', response.text[:300])}{hint}")
    return body["result"]


def find_chat(token: str) -> None:
    updates = call(token, "getUpdates")
    chats = {}
    for update in updates:
        message = update.get("message") or update.get("my_chat_member") or {}
        chat = message.get("chat") or {}
        if chat.get("id"):
            chats[chat["id"]] = chat.get("username") or chat.get("first_name") or chat.get("title") or ""
    if not chats:
        sys.exit("no chats yet: open the bot in Telegram, press Start (or send it any message), then run this again")
    for chat_id, name in chats.items():
        print(f"chat id {chat_id}  ({name})")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--message")
    parser.add_argument("--document", type=Path, help="file to attach, e.g. the tailored CV")
    parser.add_argument("--find-chat", action="store_true")
    args = parser.parse_args()

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        sys.exit("TELEGRAM_BOT_TOKEN is not set")
    if args.find_chat:
        find_chat(token)
        return
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not chat or not args.message:
        sys.exit("TELEGRAM_CHAT_ID and --message are required")
    if args.document and not args.document.is_file():
        sys.exit(f"document not found: {args.document}")

    text = args.message.strip()
    if args.document:
        # One message when the text fits as the document's caption; otherwise the document
        # first, then the full text right after it.
        caption = text if len(text) <= CAPTION_LIMIT else None
        with args.document.open("rb") as fh:
            call(token, "sendDocument", data={"chat_id": chat, **({"caption": caption} if caption else {})},
                 files={"document": (args.document.name, fh)})
        print(f"telegram document sent: {args.document.name}")
        if caption:
            return
    call(token, "sendMessage", data={"chat_id": chat, "text": text[:TEXT_LIMIT], "disable_web_page_preview": "true"})
    print("telegram message sent")


if __name__ == "__main__":
    main()
