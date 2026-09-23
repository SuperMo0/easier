# Tailoring rules

Instructions the scheduled Routine follows when turning a job description into a tailored CV.
Edit this file to change how tailoring behaves — the Routine reads it fresh on every run.

## Inputs

- `jobs/<folder>/job.json` — one folder per job. `status` says where it is:
  `new` (untailored), `tailored` (CV written, not yet delivered), `needs-you`, `review-first`,
  `applied`. This run works on `new` and `tailored`.
- `profile/MASTER-PROFILE.md` — the only permitted source of claims
- `profile/CV-master.md` — the full base CV, for structure and wording reference
- `profile/applicant.yaml` — standard answers for application forms

## Layout

Everything about one job lives in its folder, so it can be found and acted on by browsing:

    jobs/2026-09-23_careem_software-engineer-backend/
      job.json          the posting, plus its status
      cv.md             the tailored CV
      cover-letter.md   the tailored cover letter
      notes.md          fit score, matched and unmatched requirements, apply link

`jobs/INDEX.md` lists every folder. Regenerate it with `python scripts/index.py` whenever a
run changes anything.

## Every job has a link

No job folder exists without a working apply URL in `job.json`. Discovery can't produce one,
and `write_job` refuses. When a job description arrives some other way — pasted into a
conversation, forwarded — search for the posting first and store its real link. If the posting
genuinely can't be found, tailor the CV in the conversation but do not create a folder: a job
nobody can apply to from the repo is clutter, not a lead.

## The one hard rule

**Every claim in a generated CV must trace to `MASTER-PROFILE.md`.** Reword freely, reorder
freely, drop freely. Never add a technology, employer, metric, or responsibility that isn't in
the master profile. If a job requires something not in the profile, that's a gap to report, not
a gap to fill.

## Procedure, per posting

1. **Read the posting.** Extract required skills, preferred skills, seniority, and the
   vocabulary the company uses for each concept.

2. **Score the fit** 0–100, weighting required skills far above preferred. Record:
   - which requirements the profile genuinely satisfies
   - which it doesn't
   - the vocabulary mapping applied (e.g. profile says "background worker", JD says "async task
     processing" → use the JD's phrasing for the same true work)

3. **Skip if the fit is below 40** — delete the job's folder and send nothing. Its id is already
   in `jobs/.seen`, so it will not be rediscovered. A flood of weak matches makes the whole
   pipeline ignorable, and a repo full of rejected folders makes it unbrowsable.

   **Target band: internship, graduate, junior and mid-level.** Roles titled Senior, Staff,
   Lead or Principal are filtered out before they reach you; if one slips through, skip it.

   **Years of experience in the body is not a gate.** A posting asking for 3–5 years is worth
   applying to — those numbers are wish-lists and screening on them rules out most of the
   market. Score on skills and domain overlap, not tenure.

   But read the body for seniority the title hides. Skip when the role is senior in substance
   whatever it is called:
   - 7+ years stated as a requirement
   - owning architecture strategy for an organisation, not a service
   - managing, mentoring or leading a team as a core responsibility
   - "define how X is done across the company", "set the standard", "technical leader"

   Internships, graduate schemes and trainee roles are wanted — score them on the same basis
   as any other role.

4. **Select material.**

   **Sync NGO is rebuilt for every job description, never copied.** The master profile holds
   it as five pools — Backend, AI/RAG, Cloud/DevOps, CI/CD & quality, Frontend — totalling far
   more bullets than any CV should carry. Take **4–5 bullets**, chosen and ordered by what the
   JD is hiring for. The first bullet is the one the reviewer reads; make it the thing they
   asked for.

   | JD type | Pool order |
   |---|---|
   | AI / ML / LLM | AI-RAG → Backend → one CI/CD |
   | Backend / platform | Backend → Cloud-DevOps → CI/CD |
   | DevOps / SRE / infrastructure | Cloud-DevOps → CI/CD → Backend |
   | Data / streaming | AI-RAG (embedding + extraction pipelines) → Backend → Cloud-DevOps |
   | Full-stack | Backend → Frontend → one AI-RAG |
   | Frontend | Frontend → Backend → one AI-RAG |

   Whatever the order, one bullet should always establish that the platform is real and in
   production with enterprise users — that is the part most junior candidates cannot claim.

   **Stack follows the JD.** Sync exists in several implementations — Python/FastAPI, Java/
   Spring Boot and .NET on the backend, AWS and GCP on the infrastructure. Pick the variant
   the JD calls for and write it as that stack's own work, in its native vocabulary and
   tooling. One variant per CV, never blended, and never carry one variant's specifics into
   another.

   This applies only to providers the platform genuinely ran on. It is not licence to name a
   provider it never used: an Azure job gets Azure from the projects that actually used Azure,
   not from Sync.

   - Pick at most 4 projects. Drop the rest entirely.
   - **The Last-Mile Delivery Platform leads** for backend, platform, NestJS, Kafka, geospatial,
     logistics and payments-adjacent roles — it is the most complex and most current project.
     Its idempotency work is the lead detail for payments and fintech. It is in progress: say
     "building", never "launched", "live" or "in production".
   - For an infra-heavy JD lead with the Terraform and Cloud Run work; for a data JD lead with
     Kafka, Spark and Airflow; for an AI JD lead with the RAG pipeline.

5. **Reword into the JD's vocabulary** — same facts, their terminology. This is the whole point
   of tailoring and it's where the match rate comes from.

6. **Keep it scannable.** One line per bullet. Business outcome plus the stack on each line —
   HR screens for impact, the engineer after them screens for keywords. Two pages maximum.

   **Describe engineering, not features.** Features say what the app does; engineering says
   what had to be solved. Reviewers hire for the second. For every project, reach past the
   feature list for the concerns underneath:

   - access control — auth model, RBAC, tenant isolation
   - type safety and validation boundaries
   - security posture — rate limiting, headers, sanitization, secret handling
   - data modelling — schema design, relations, indexing, migrations
   - scale work — pagination, virtualization, caching, concurrency
   - infrastructure — deployment, CI/CD, monitoring, IaC
   - testing strategy

   "Blog with a rich text editor" is a feature. "RBAC over JWT with DOMPurify sanitization on
   user-generated HTML" is engineering. Same project; only the second earns an interview.

   **At most two lines per project, regardless of how much the master profile holds on it.**
   Pick the one or two details that are actually memorable — "virtualized message lists",
   "outbox pattern so no order is lost", "streams multi-gigabyte CSVs without loading them
   into memory" — and drop the rest. A project described in four dense bullets reads as
   padding next to one described in two sharp ones.

7. **Write the output into the job's own folder:**
   - `cv.md` — the tailored CV
   - `cover-letter.md` — 150–200 words, specific to this role and company, drawn from the same
     true profile as the CV. No generic openers; the first sentence names what they are building
     and why this candidate has built something like it.
   - `notes.md` — must start with `Fit score: <n> / 100`, then matched requirements, unmatched
     requirements, and the apply URL.
   - set `status` in `job.json` to `tailored`.

8. **Commit** the folder, and regenerate `jobs/INDEX.md`.

9. **Notify** — only for the day's top ten (see below) — by dispatching the `Notify` workflow:
   - `message`: `<STATUS> · <Job title> at <Company> — <score>% match` then the reason if the
     status is `NEEDS YOU`, then `Apply: <url>`
   - `cv_path`: `jobs/<folder>/cv.md`

   Afterwards set `status` in `job.json` to what actually happened — `applied`, `needs-you` or
   `review-first` — and regenerate the index.

10. **Leave the folder in place.** It is the record of the application and the place to act
    from if something needs doing by hand. Pruning removes old folders on its own schedule.

## Custom questions — `answers.json`

The apply script answers standard form questions from `profile/applicant.yaml`. It stops at any
required question it can't answer, and the job comes back as `NEEDS YOU · custom questions: …`
with every such question listed under `unanswered` in `apply-result.json`.

On the next run, answer those questions for that job in `jobs/<folder>/answers.json`. Key each
answer by a short phrase that appears in the question. Then include the folder in that day's
Apply dispatch.

    {"why ziina": "…two or three sentences drawn from the cover letter…",
     "kotlin": "No",
     "notice period": "20 days"}

- Yes/No questions need the answer `"Yes"` or `"No"`.
- An answer can be a list of acceptable values in order of preference. The first one the
  field's options contain is used, e.g. `"language 1": ["Python Advanced", "Arabic"]` when
  one label covers both a programming-language field and a spoken-language field. Read
  `unanswered_detail` in apply-result.json: it lists each field's real options and what was
  tried.
- Every answer must be true to the master profile and applicant.yaml, the same rule as the CV.
- A question asking for more years than the profile has gets the true number, or "No". Never
  claim years he doesn't have. The application still goes in, and the reviewer decides.
- "Why us" and motivation questions get two or three plain sentences taken from the cover
  letter.
- Questions only he can answer (references, a portfolio password, an assessment) stay
  unanswered. Leave that job as `NEEDS YOU`.

## What the boards allow

- **Ashby and Teamtailor** accept automated submissions once every required question is
  answered (confirmed: Brain Co., Property Finder).
- **Lever** (Binance, Palantir, 1inch…) raises an hCaptcha challenge after submit, and
  **Workable** (Flatgigs, dubizzle, Deeplight…) holds the submit behind Cloudflare Turnstile.
  Those jobs come back `NEEDS YOU · CAPTCHA` with every answer ready; he finishes them with
  `python scripts/apply.py --assist --captcha-jobs` on his own PC. Never solve or get around
  a CAPTCHA.
- Greenhouse is not yet confirmed either way.
- A status reason that says the submission *may* have gone through means exactly that. Don't
  re-submit that job until the email inbox shows whether it went through.

## Gaps

When a posting requires something the profile doesn't contain, put it in `notes.md` under
"Unmatched requirements". Never paper over it in the CV. If the same gap appears across many
postings, that's a signal worth raising — it means a genuine skill worth acquiring, not a
sentence worth inventing.

## Refresh before delivering

A folder tailored on an earlier day was written against an older master profile. Before
delivering it, re-tailor its CV and cover letter against the current profile.

## Daily selection — the best ten

Score every `new` posting, then **rank by score together with older `tailored` folders not yet
delivered, and deliver only the top ten**. Postings that clear the threshold but miss the top ten
keep their folder, with a `notes.md` recording the score, and compete again tomorrow.
Below-threshold ones are deleted.

The point is a shortlist worth reading, not a feed. Ten strong matches a day get opened; forty
mediocre ones get ignored, and then the good ones get ignored with them.

If fewer than ten clear the threshold, send fewer. Never pad the list.

## Application status — say what actually happened

Every notification states plainly whether the application was submitted. There are three cases
and the message must name the right one:

- `APPLIED` — the application was actually submitted end to end.
- `NEEDS YOU` — could not submit; the CV is attached and the apply link is in the message.
  Give the reason in three or four words: login required, CAPTCHA, custom questions,
  file upload only, account needed.
- `REVIEW FIRST` — submission was possible but held for approval per the review-before-submit
  setting.

Never imply an application was sent when it was not. A message that reads as "done" when
nothing was submitted is worse than no message, because the job gets crossed off mentally and
the deadline passes.

Message format:

    <STATUS> · <Job title> at <Company> — <score>% match
    <reason, only when NEEDS YOU>
    Apply: <url>
