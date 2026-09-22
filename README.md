# easier

Automated job-application pipeline for the UAE market. Discovers openings, tailors a CV to each
job description, and delivers the result over WhatsApp.

## How it runs

Nothing runs on a local machine. Three pieces, in two environments:

| Piece | Runs on | Purpose |
|---|---|---|
| **Discovery** (`.github/workflows/discover.yml`) | GitHub Actions, cron | Fetches job postings from target companies, commits new ones to `jobs/incoming/` |
| **Tailoring** (a Claude Code Routine) | Anthropic cloud, cron | Reads new JDs, selects matching material from `profile/MASTER-PROFILE.md`, writes a tailored CV to `applications/` |
| **Delivery** (`.github/workflows/notify.yml`) | GitHub Actions, dispatch | Renders the CV to PDF and sends it over WhatsApp with the apply link |

The Claude sandbox has no general internet access, so the two environments communicate through
git commits rather than HTTP. GitHub Actions runners have full network access and handle
everything that touches the outside world.

## Layout

```
profile/
  MASTER-PROFILE.md    internal source of truth — never sent to anyone
  CV-master.md         the full base CV; tailoring selects a subset
companies/
  uae-targets.yaml     target companies and their ATS endpoints
jobs/
  incoming/            discovered JDs awaiting tailoring
  processed/           JDs already handled
applications/          tailored CVs, one directory per job
scripts/
  send_whatsapp.py     Meta WhatsApp Cloud API client
  render_pdf.py        markdown CV -> PDF
```

## Required secrets

Set these in the repository's Actions secrets (Settings → Secrets and variables → Actions):

| Secret | Value |
|---|---|
| `META_TOKEN` | Permanent System User access token with `whatsapp_business_messaging` |
| `PHONE_NUMBER_ID` | WhatsApp sender phone number ID |
| `WHATSAPP_RECIPIENT` | Destination number in international format, no `+` |
| `WHATSAPP_TEMPLATE` | *(optional)* Approved template name for proactive sends |

## The 24-hour window

Meta only permits free-form text messages within 24 hours of the recipient last messaging the
business number. Outside that window, sends must use a pre-approved template. For scheduled
alerts this means either:

- Approve a template with a body variable and set `WHATSAPP_TEMPLATE`, or
- Reply to the business number periodically to keep the window open.

`scripts/send_whatsapp.py` handles both: it uses the template when one is configured and falls
back to plain text otherwise.
