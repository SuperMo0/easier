# Tailoring rules

Instructions the scheduled Routine follows when turning a job description into a tailored CV.
Edit this file to change how tailoring behaves — the Routine reads it fresh on every run.

## Inputs

- `jobs/incoming/*.json` — discovered postings awaiting processing
- `profile/MASTER-PROFILE.md` — the only permitted source of claims
- `profile/CV-master.md` — the full base CV, for structure and wording reference

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

3. **Skip if the fit is below 40.** Move the posting to `jobs/processed/` with the score
   recorded and send nothing — a flood of weak matches makes the whole pipeline ignorable.

   **Do not treat years of experience as a gate.** A posting asking for 3–5 years is worth
   applying to; those numbers are wish-lists and screening on them rules out most of the
   market. Score on skills and domain overlap, not tenure. Only genuinely senior-only roles
   (8+ years, or a title like Principal or Head of) should lose points for seniority.

   Internships, graduate schemes and trainee roles are wanted, not filtered out — score them
   on the same basis.

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

   **Cloud provider follows the JD.** Sync ran on AWS before being migrated to GCP, so either
   is true. For an AWS-oriented job present the AWS deployment; for a GCP one present GCP.
   Do not narrate the migration — a CV is selective, not a history.

   This applies only to providers the platform genuinely ran on. It is not licence to name a
   provider it never used: an Azure job gets Azure from the projects that actually used Azure,
   not from Sync.

   - Pick at most 4 projects. Drop the rest entirely.
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

7. **Write the output:**
   - `applications/<company>-<job-id>/cv.md` — the tailored CV
   - `applications/<company>-<job-id>/notes.md` — fit score, matched requirements, unmatched
     requirements, apply URL

8. **Commit** both files.

9. **Notify** by dispatching the `Notify` workflow with:
   - `message`: `<Job title> at <Company> — <score>% match. Apply: <url>`
   - `cv_path`: the path to `cv.md`

10. **Move the posting** to `jobs/processed/`.

## Gaps

When a posting requires something the profile doesn't contain, put it in `notes.md` under
"Unmatched requirements". Never paper over it in the CV. If the same gap appears across many
postings, that's a signal worth raising — it means a genuine skill worth acquiring, not a
sentence worth inventing.

## Batching

Process at most 10 postings per run. If more are waiting, leave them for the next wake-up
rather than sending a burst of notifications.
