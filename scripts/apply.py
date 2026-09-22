"""Submit applications for tailored jobs, in a real browser, on a GitHub Actions runner.

For each job folder: open the application form, fill it from profile/applicant.yaml, attach the
tailored CV and cover letter, submit, and record exactly what happened.

Principles:
- A required question that applicant.yaml cannot answer truthfully stops the application.
  It is never guessed — the status becomes NEEDS YOU with the question named.
- APPLIED is only recorded when the site confirms the submission.
- One job failing never stops the rest.

Usage:
    python apply.py jobs/<folder> [jobs/<folder> ...]      # submit
    python apply.py --dry-run jobs/<folder>                  # fill everything, do not submit
"""

import argparse
import json
import re
import sys
import traceback
from pathlib import Path

import yaml
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
APPLICANT = yaml.safe_load((ROOT / "profile" / "applicant.yaml").read_text())
MANIFEST = ROOT / "apply-manifest.json"
SHOTS = ROOT / "apply-screenshots"
CV_NAME = "Mwafak_Almahaini_CV.pdf"
LETTER_NAME = "Mwafak_Almahaini_Cover_Letter.pdf"

CONFIRMATION = re.compile(
    r"thank you for (your )?appl|application (has been |was )?(submitted|received)|"
    r"we('ve| have) received your application|successfully (submitted|applied)|"
    r"thanks for applying|your application is (in|complete)",
    re.I,
)
SUBMIT = re.compile(r"^\s*(submit( application)?|apply( now)?|send application)\s*$", re.I)


# ----------------------------------------------------------------------------- answers

def _a(path: str):
    node = APPLICANT
    for part in path.split("."):
        node = node.get(part) if isinstance(node, dict) else None
    return node


# (pattern on the field's label, answer). First match wins, so specific patterns go first.
# An answer of None means "known question, no truthful answer on file" — required ones stop.
RULES: list[tuple[str, object]] = [
    (r"\bfirst\s*name|given name|forename", _a("first_name")),
    (r"\blast\s*name|surname|family name", _a("last_name")),
    (r"\b(full\s*)?name\b(?!.*(company|employer|school|university|reference|manager))", _a("full_name")),
    (r"e-?mail", _a("email")),
    (r"phone|mobile|contact number", _a("phone")),
    (r"linked\s*in", _a("links.linkedin")),
    (r"git\s*hub", _a("links.github")),
    (r"portfolio|personal (web)?site|website|blog", _a("links.portfolio")),
    (r"current (company|employer)|employer name|organi[sz]ation", _a("current_company")),
    (r"current (job )?title|current (position|role)", _a("current_title")),
    (r"notice period", f"{_a('notice_period_days')} days"),
    (r"(earliest|available|availability).*(start|join)|start date|when can you (start|join)", _a("earliest_start")),
    (r"salary|compensation|pay expectation|expected (ctc|package|pay)", _a("expected_salary.text")),
    (r"(require|need).*(sponsor|visa)|sponsorship", "No"),
    (r"visa status|current visa|type of visa|residency status", _a("work_authorization.visa")),
    (r"(legally )?(authori[sz]ed|eligible|permitted|right) to work|work authori[sz]ation|work permit", "Yes"),
    (r"relocat", "Yes"),
    (r"driv(ing|er'?s?) licen[cs]e", _a("driving_licence")),
    (r"^\s*(total |overall )?(years of )?(professional |relevant |work )?experience\s*(\(years\))?\s*\??\s*$|how many years of (professional |work )?experience do you have\s*\??$",
     str(_a("years_experience"))),
    (r"(highest|level of) (degree|education)|degree", _a("education.degree")),
    (r"university|school|college|institution", _a("education.school")),
    (r"graduat", str(_a("education.graduated") or "")[:4] or None),
    (r"nationality|citizenship", _a("nationality")),
    (r"date of birth|\bdob\b|birth ?date", _a("date_of_birth")),
    (r"^\s*gender|sex\b", _a("gender")),
    (r"\blocation\b|city|where are you (based|located)|current(ly)? (living|residing)", _a("location")),
    (r"language", ", ".join(_a("languages") or [])),
    (r"hear about|how did you (find|learn)|referr?al source|source of application", "Company careers page"),
    (r"remote|hybrid|on-?site|work (arrangement|mode|model)", "Yes"),
]

DECLINE = re.compile(r"decline|prefer not|do not wish|don'?t wish|not to (say|disclose)|rather not", re.I)
EEO = re.compile(r"race|ethnic|veteran|disabilit|gender identity|sexual orientation|pronoun", re.I)
CONSENT = re.compile(r"agree|consent|acknowledge|privacy|terms|accurate|certify|confirm that", re.I)


def answer_for(label: str):
    """Return (known, answer). known=False means nothing on file matches the question."""
    text = " ".join(label.split()).lower()
    for pattern, answer in RULES:
        if re.search(pattern, text):
            return True, answer
    return False, None


# ----------------------------------------------------------------------------- page work

COLLECT_FIELDS = """
() => {
  const labelOf = (el) => {
    if (el.id) {
      const l = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
      if (l && l.innerText.trim()) return l.innerText.trim();
    }
    if (el.getAttribute('aria-label')) return el.getAttribute('aria-label');
    const by = el.getAttribute('aria-labelledby');
    if (by) {
      const t = by.split(/\\s+/).map(i => document.getElementById(i)?.innerText || '').join(' ').trim();
      if (t) return t;
    }
    const wrap = el.closest('label, fieldset, [class*="field"], [class*="question"], div');
    if (wrap) {
      const lab = wrap.querySelector('label, legend, [class*="label"]');
      if (lab && lab.innerText.trim()) return lab.innerText.trim();
    }
    return el.getAttribute('placeholder') || el.name || '';
  };
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return (r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none') || el.type === 'file';
  };
  const out = [];
  document.querySelectorAll('input, textarea, select').forEach((el, i) => {
    const type = (el.type || el.tagName).toLowerCase();
    if (['hidden', 'submit', 'button', 'image', 'reset', 'search'].includes(type)) return;
    if (!visible(el)) return;
    el.setAttribute('data-easier-idx', String(i));
    const label = labelOf(el);
    const required = el.required || el.getAttribute('aria-required') === 'true' || /\\*\\s*$/.test(label);
    const options = el.tagName === 'SELECT' ? [...el.options].map(o => o.text.trim()).filter(Boolean) : [];
    let radioLabel = '';
    if (type === 'radio' || type === 'checkbox') {
      const own = el.id && document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
      radioLabel = (own ? own.innerText : el.closest('label')?.innerText || el.value || '').trim();
    }
    out.push({ idx: String(i), type, name: el.name || '', label: label.replace(/\\*+\\s*$/, '').trim(),
               required, options, radioLabel, role: el.getAttribute('role') || '' });
  });
  return out;
}
"""


def open_form(page, ats: str, url: str) -> None:
    target = url
    if ats == "lever" and not url.rstrip("/").endswith("/apply"):
        target = url.rstrip("/") + "/apply"
    elif ats == "ashby" and not url.rstrip("/").endswith("/application"):
        target = url.rstrip("/") + "/application"
    page.goto(target, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(2_500)
    # Workable, SmartRecruiters and some Greenhouse boards hide the form behind an Apply button.
    if not page.locator("input[type=file]").count():
        for name in (r"apply( for this job| now)?", r"i'?m interested"):
            button = page.get_by_role("button", name=re.compile(name, re.I)).or_(
                page.get_by_role("link", name=re.compile(name, re.I)))
            if button.count():
                button.first.click()
                page.wait_for_timeout(3_000)
                break


def visible_captcha(page) -> bool:
    """True only for a challenge a person would have to solve.

    Most boards run invisible reCAPTCHA, which renders a small badge iframe with
    size=invisible in its URL and never interrupts a normal submission. Only a visible
    checkbox widget, or an image challenge that has actually popped up, blocks.
    """
    for frame in page.locator("iframe").all():
        src = frame.get_attribute("src") or ""
        if not src or "size=invisible" in src:
            continue
        blocking = (
            re.search(r"recaptcha/(api2|enterprise)/anchor", src)            # v2 checkbox widget
            or re.search(r"recaptcha/(api2|enterprise)/bframe", src)         # image challenge
            or ("hcaptcha.com" in src and "frame=checkbox" in src)
            or ("hcaptcha.com" in src and "frame=challenge" in src)
        )
        if not blocking:
            continue
        try:
            box = frame.bounding_box()
        except Exception:
            box = None
        if box and box["width"] > 60 and box["height"] > 60 and frame.is_visible():
            return True
    return False


def describe(page) -> None:
    """Log what the runner actually sees, so a failed run can be diagnosed from the log."""
    try:
        frames = [f.get_attribute("src") or "" for f in page.locator("iframe").all()]
        print(f"    page: {page.title()!r} at {page.url}")
        print(f"    inputs={page.locator('input').count()} textareas={page.locator('textarea').count()} "
              f"selects={page.locator('select').count()} files={page.locator('input[type=file]').count()}")
        for src in frames[:8]:
            print(f"    iframe: {src[:140]}")
    except Exception as exc:
        print(f"    (describe failed: {exc})")


def fill_form(page, cv_pdf: Path, letter_pdf: Path | None, letter_text: str) -> dict:
    fields = page.evaluate(COLLECT_FIELDS)
    filled, unanswered = [], []
    groups: dict[str, list] = {}

    for f in fields:
        sel = f'[data-easier-idx="{f["idx"]}"]'
        el = page.locator(sel)
        label, low = f["label"], f["label"].lower()

        if f["type"] in ("radio", "checkbox") and f["name"]:
            groups.setdefault(f["name"], []).append(f)
            continue

        if f["type"] == "file":
            # Ashby-style "autofill from resume" boxes parse the upload and can overwrite
            # fields already filled; the real resume field comes later in the form.
            if re.search(r"autofill|auto-fill|parse|import", low):
                continue
            if re.search(r"cover", low) and letter_pdf:
                el.set_input_files(str(letter_pdf)); filled.append("cover letter (file)")
            elif re.search(r"resume|cv|curriculum|attach", low) or not filled:
                el.set_input_files(str(cv_pdf)); filled.append("CV (file)")
            continue

        if re.search(r"cover letter|why (do you want|are you interested)|motivation|additional information|anything else", low):
            if letter_text.strip() and (f["type"] == "textarea" or "cover" in low):
                el.fill(letter_text[:4000]); filled.append(label or "cover letter"); continue

        if EEO.search(low) and f["type"] == "select-one":
            choice = next((o for o in f["options"] if DECLINE.search(o)), None)
            if choice:
                el.select_option(label=choice); filled.append(label)
            elif f["required"]:
                unanswered.append(label)
            continue

        known, answer = answer_for(label)
        if not known or answer in (None, "", "None"):
            if f["required"]:
                unanswered.append(label or f["name"] or "unlabelled field")
            continue

        answer = str(answer)
        if f["type"] == "select-one":
            opts = f["options"]
            choice = (next((o for o in opts if o.lower() == answer.lower()), None)
                      or next((o for o in opts if answer.lower() in o.lower() or o.lower() in answer.lower()), None))
            if choice:
                el.select_option(label=choice); filled.append(label)
            elif f["required"]:
                unanswered.append(label)
        elif f["role"] == "combobox":
            el.click(); el.fill(answer); page.wait_for_timeout(700); page.keyboard.press("Enter")
            filled.append(label)
        else:
            el.fill(answer); filled.append(label)

    for name, options in groups.items():
        group_label = options[0]["label"]
        low = group_label.lower()
        required = any(o["required"] for o in options)
        if all(o["type"] == "checkbox" for o in options) and len(options) == 1:
            if CONSENT.search(low + " " + options[0]["radioLabel"].lower()):
                page.locator(f'[data-easier-idx="{options[0]["idx"]}"]').check(); filled.append("consent")
            elif required:
                unanswered.append(group_label)
            continue
        if EEO.search(low):
            pick = next((o for o in options if DECLINE.search(o["radioLabel"])), None)
        else:
            known, answer = answer_for(group_label)
            pick = None
            if known and answer:
                pick = next((o for o in options if o["radioLabel"].lower().startswith(str(answer).lower())), None)
        if pick:
            page.locator(f'[data-easier-idx="{pick["idx"]}"]').check(); filled.append(group_label)
        elif required:
            unanswered.append(group_label)

    return {"filled": filled, "unanswered": unanswered}


def submit(page) -> tuple[str, str]:
    button = page.get_by_role("button", name=SUBMIT)
    if not button.count():
        button = page.locator("button[type=submit], input[type=submit]")
    if not button.count():
        return "needs-you", "no submit button found"
    button.last.click()
    try:
        page.wait_for_function(
            "(re) => new RegExp(re, 'i').test(document.body.innerText)",
            arg=CONFIRMATION.pattern, timeout=25_000,
        )
        return "applied", ""
    except PlaywrightTimeout:
        pass
    if visible_captcha(page):
        return "needs-you", "CAPTCHA"
    invalid = page.locator("[aria-invalid=true]")
    if invalid.count():
        return "needs-you", "form rejected a field"
    return "needs-you", "submission not confirmed"


# ----------------------------------------------------------------------------- per job

def score_of(folder: Path) -> str:
    notes = folder / "notes.md"
    if notes.is_file() and (m := re.search(r"Fit score:\s*\**\s*(\d+)", notes.read_text())):
        return m.group(1)
    return "?"


def apply_one(browser, folder: Path, dry_run: bool) -> dict:
    job = json.loads((folder / "job.json").read_text())
    cv_pdf = folder / CV_NAME
    letter_pdf = folder / LETTER_NAME
    letter_text = (folder / "cover-letter.md").read_text() if (folder / "cover-letter.md").is_file() else ""

    result = {"status": "needs-you", "reason": "", "filled": [], "unanswered": []}
    if not job.get("url"):
        result["reason"] = "no application URL"
    elif job.get("ats") in ("manual", "workday", "custom", "search", "model-search") and not job.get("url"):
        result["reason"] = "unsupported application site"
    else:
        context = browser.new_context(viewport={"width": 1280, "height": 1800})
        page = context.new_page()
        try:
            open_form(page, job.get("ats", ""), job["url"])
            print(f"  {folder.name}")
            describe(page)
            if page.locator("input[type=password]").count():
                result["reason"] = "login required"
            elif visible_captcha(page):
                result["reason"] = "CAPTCHA"
            elif not page.locator("input, textarea").count():
                result["reason"] = "no application form found"
            else:
                outcome = fill_form(page, cv_pdf, letter_pdf if letter_pdf.is_file() else None, letter_text)
                result.update(outcome)
                print(f"    filled: {outcome['filled']}")
                print(f"    unanswered: {outcome['unanswered']}")
                if outcome["unanswered"]:
                    shown = "; ".join(q[:60] for q in outcome["unanswered"][:2])
                    result["reason"] = f"custom questions: {shown}"
                elif dry_run:
                    result["status"], result["reason"] = "dry-run", "filled, not submitted"
                else:
                    result["status"], result["reason"] = submit(page)
            SHOTS.mkdir(exist_ok=True)
            page.screenshot(path=str(SHOTS / f"{folder.name}.png"), full_page=True)
        except Exception as exc:
            result["reason"] = f"automation error: {type(exc).__name__}"
            traceback.print_exc()
        finally:
            context.close()

    if not dry_run:
        job["status"] = result["status"]
        job["status_reason"] = result["reason"]
        (folder / "job.json").write_text(json.dumps(job, indent=2, ensure_ascii=False))
    (folder / "apply-result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))

    label = {"applied": "APPLIED", "needs-you": "NEEDS YOU", "dry-run": "DRY RUN"}.get(result["status"], result["status"].upper())
    parts = [label, f"{job.get('title', '')} at {job.get('company', '')}", f"{score_of(folder)}% match"]
    if result["reason"] and result["status"] != "applied":
        parts.append(f"reason: {result['reason']}")
    if job.get("url"):
        parts.append(job["url"])
    return {"folder": str(folder), "status": result["status"], "message": " · ".join(parts), "cv_pdf": str(cv_pdf)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("folders", nargs="+", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    jobs_root = (ROOT / "jobs").resolve()
    folders = []
    for f in args.folders:
        f = (ROOT / f).resolve() if not f.is_absolute() else f.resolve()
        # Inputs arrive from a workflow dispatch; refuse anything outside jobs/.
        if jobs_root not in f.parents or not (f / "job.json").is_file():
            print(f"skipping invalid job folder: {f}")
            continue
        folders.append(f)

    manifest = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for folder in folders:
            try:
                entry = apply_one(browser, folder, args.dry_run)
            except Exception as exc:
                traceback.print_exc()
                entry = {"folder": str(folder), "status": "needs-you",
                         "message": f"NEEDS YOU · {folder.name} · reason: automation error {type(exc).__name__}",
                         "cv_pdf": str(folder / CV_NAME)}
            print(entry["message"])
            manifest.append(entry)
        browser.close()

    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
