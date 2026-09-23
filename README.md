# easier

Automated job-application pipeline for the UAE market. Discovers openings, tailors a CV to each
job description, and delivers the result over WhatsApp.

## How it runs

Everything runs in the cloud; the one optional local step is assisted applying for CAPTCHA
jobs (below). Three pieces, in two environments:

| Piece | Runs on | Purpose |
|---|---|---|
| **Discovery** (`.github/workflows/discover.yml`) | GitHub Actions, twice daily | Pulls postings from every verified company board and from leads Claude found by searching; each new posting gets its own folder under `jobs/` |
| **Tailoring** (a Claude Code Routine) | Anthropic cloud, daily 10:00 Dubai | Searches the web for new openings, scores every new posting, writes a tailored CV, cover letter and notes into the job's folder, and picks the day's top ten |
| **Delivery** (`.github/workflows/notify.yml`) | GitHub Actions, dispatch | Renders the CV to PDF and sends it over WhatsApp with the apply link and the application status |

The Claude sandbox has no general internet access, so the two environments communicate through
git commits rather than HTTP. GitHub Actions runners have full network access and handle
everything that touches the outside world.

## Layout

```
jobs/
  INDEX.md                                        every job, newest and best first — start here
  2026-09-23_careem_software-engineer-backend/    one folder per job:
    job.json                                        the posting and its status
    cv.md                                           tailored CV
    cover-letter.md                                 tailored cover letter
    notes.md                                        fit score, gaps, apply link
  .seen                                           every job id ever seen, so nothing returns
  leads.json                                      URLs Claude found by searching, awaiting fetch
profile/
  MASTER-PROFILE.md    source of truth for every claim a CV makes
  CV-master.md         the full base CV; tailoring selects a subset
  TAILORING.md         the rules the daily run follows
  applicant.yaml       standard answers for application forms
companies/
  uae-targets.yaml     target companies, their boards, and the title filters
scripts/
  discover.py          board fetching, filtering, pruning
  detect_ats.py        identifies a company's job board from its careers page
  fetch_leads.py       fetches full postings for search-found leads
  index.py             rebuilds jobs/INDEX.md
  render_pdf.py        markdown CV -> PDF
  send_whatsapp.py     Meta WhatsApp Cloud API client
```

Job statuses: `new` → `tailored` → one of `applied`, `needs-you`, `review-first`. Folders that
never get tailored are pruned after 30 days, handled ones after 90.

## Jobs that need you: CAPTCHA

Some boards (Lever: Binance, Palantir, 1inch…) show a CAPTCHA after submit, and the pipeline
never solves or bypasses one. For those, run the applier on your own PC. It opens a visible
browser, fills the whole form with the tailored CV, cover letter and answers, and waits for
you to tick the CAPTCHA and press Submit. From a home connection the CAPTCHA is often just a
single click. It then records the outcome in the job folder.

Run it with one command from the repo folder. The first run creates a `.venv` and installs
Playwright and Chromium into it:

```
git clone https://github.com/SuperMo0/easier.git
cd easier
git checkout claude/nifty-keller-7wmtge
./assist.sh
```

Workable jobs are different: Cloudflare's bot check there fails any automated browser, even
when you click it yourself. For those, `easier` opens the application in your normal browser
next to an answer sheet with a copy button for every answer, the cover letter and the PDF
paths. Submit in your browser, then answer `y` in the terminal.

After that, `./assist.sh` is all you need. It pulls, opens each waiting job, and pushes the
outcomes. `./assist.sh jobs/<folder>` does a single job. If the first run says venv is
missing, run `sudo apt install -y python3-venv` once and try again.

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
