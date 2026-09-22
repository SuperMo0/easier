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

4. **Select material.** Choose the experience and projects that match, in relevance order:
   - Sync NGO always appears; adjust which of its facets lead (backend / AI / cloud / CI).
   - Pick at most 4 projects. Drop the rest entirely.
   - For an infra-heavy JD lead with the Terraform and Cloud Run work; for a data JD lead with
     Kafka, Spark and Airflow; for an AI JD lead with the RAG pipeline.

5. **Reword into the JD's vocabulary** — same facts, their terminology. This is the whole point
   of tailoring and it's where the match rate comes from.

6. **Keep it scannable.** One line per bullet. Business outcome plus the stack on each line —
   HR screens for impact, the engineer after them screens for keywords. Two pages maximum.

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
