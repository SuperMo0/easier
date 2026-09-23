"""Why aren't WhatsApp messages arriving? Ask Meta, read-only.

Meta accepts a send (and returns a message id) before it knows whether the message can be
delivered; a message that later fails — charged outside the 24-hour window with no payment
method, a marketing template throttled for this user, a paused template — only fails
afterwards. This prints what Meta says about the pieces involved, without sending anything:

- the sender phone number (status, quality rating, messaging tier),
- the WhatsApp Business Account the token manages,
- every message template (status, category, language, quality),
- sent vs delivered counts per day over the last week.

Usage (on a runner, with the same secrets as notify.yml):
    python whatsapp_check.py
"""

import os
import sys
import time
from datetime import datetime, timezone

import requests

BASE = "https://graph.facebook.com/v25.0"


def get(path: str, token: str, **params) -> dict:
    response = requests.get(f"{BASE}/{path}", params={**params, "access_token": token}, timeout=60)
    body = response.json() if response.headers.get("content-type", "").startswith(("application/json", "text/javascript")) else {}
    if not response.ok:
        error = body.get("error", {})
        return {"_error": f"{response.status_code} {error.get('code', '')} {error.get('message', response.text[:300])}"}
    return body


def main() -> None:
    token, phone_id = os.environ.get("META_TOKEN"), os.environ.get("PHONE_NUMBER_ID")
    template = os.environ.get("WHATSAPP_TEMPLATE", "")
    if not token or not phone_id:
        sys.exit("META_TOKEN and PHONE_NUMBER_ID are required")

    print("== Sender phone number")
    phone = get(phone_id, token, fields="display_phone_number,verified_name,status,quality_rating,"
                                        "messaging_limit_tier,name_status,code_verification_status,platform_type")
    for key, value in phone.items():
        print(f"  {key}: {value}")

    print("\n== WhatsApp Business Accounts this token manages")
    debug = get("debug_token", token, input_token=token).get("data", {})
    wabas = sorted({t for scope in debug.get("granular_scopes", [])
                    if scope.get("scope") in ("whatsapp_business_management", "whatsapp_business_messaging")
                    for t in scope.get("target_ids", [])})
    print(f"  token type: {debug.get('type')}, expires: {debug.get('expires_at') or 'never'}, valid: {debug.get('is_valid')}")
    print(f"  scopes: {', '.join(debug.get('scopes', [])) or '(none listed)'}")
    # A token with access to every account lists no target ids; find the accounts other ways.
    if os.environ.get("WABA_ID"):
        wabas.append(os.environ["WABA_ID"])
    for edge in ("me/assigned_whatsapp_business_accounts", "me/businesses"):
        found = get(edge, token, fields="id,name", limit=25)
        if "_error" in found:
            print(f"  {edge}: {found['_error']}")
            continue
        for item in found.get("data", []):
            if edge.endswith("businesses"):
                for sub in ("owned_whatsapp_business_accounts", "client_whatsapp_business_accounts"):
                    wabas += [w["id"] for w in get(f"{item['id']}/{sub}", token, fields="id").get("data", [])]
            else:
                wabas.append(item["id"])
    wabas = sorted(set(wabas))
    if not wabas:
        print("  no WhatsApp Business Account found; set a WABA_ID secret (WhatsApp Manager → API setup) to check templates")

    now = int(time.time())
    week_ago = now - 7 * 86400
    for waba in wabas:
        info = get(waba, token, fields="name,currency,account_review_status,business_verification_status,"
                                       "message_template_namespace")
        if "_error" in info:
            continue  # a target id that isn't a WhatsApp Business Account
        print(f"\n== WhatsApp Business Account {waba}")
        for key, value in info.items():
            if key != "id":
                print(f"  {key}: {value}")
        funding = get(waba, token, fields="primary_funding_id")
        print(f"  payment method (primary_funding_id): {funding.get('primary_funding_id') or funding.get('_error') or 'NONE'}")

        print("  templates:")
        templates = get(f"{waba}/message_templates", token,
                        fields="name,status,category,language,quality_score,rejected_reason", limit=100)
        for t in templates.get("data", []):
            mark = "  <- the one easier sends" if template and t.get("name") == template else ""
            quality = (t.get("quality_score") or {}).get("score", "")
            print(f"    {t.get('name')} [{t.get('language')}] status={t.get('status')} "
                  f"category={t.get('category')} quality={quality}{mark}")
        if "_error" in templates:
            print(f"    could not list templates: {templates['_error']}")

        print("  sent vs delivered, last 7 days (UTC):")
        analytics = get(waba, token, fields=f"analytics.start({week_ago}).end({now}).granularity(DAY)")
        points = (analytics.get("analytics") or {}).get("data_points", [])
        for p in sorted(points, key=lambda p: p.get("start", 0)):
            day = datetime.fromtimestamp(p.get("start", 0), timezone.utc).strftime("%a %d %b")
            print(f"    {day}: sent {p.get('sent', 0)}, delivered {p.get('delivered', 0)}")
        if "_error" in analytics:
            print(f"    could not read analytics: {analytics['_error']}")
        elif not points:
            print("    no data points returned")


if __name__ == "__main__":
    main()
