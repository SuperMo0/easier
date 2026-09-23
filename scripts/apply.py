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
import os
import re
import sys
import traceback
from pathlib import Path
from urllib.parse import urljoin

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
ALREADY = re.compile(r"already (applied|submitted|received an application)|you have applied", re.I)
SPAM = re.compile(r"flagged|\bspam\b|suspicious|unusual activity|verify (that )?you('| a)re (a )?human|are you a robot", re.I)
SUBMIT = re.compile(r"^\s*(submit( application)?|apply( now)?|send application)\s*$", re.I)


# ----------------------------------------------------------------------------- answers

def _a(path: str):
    node = APPLICANT
    for part in path.split("."):
        node = node.get(part) if isinstance(node, dict) else None
    return node


# (pattern on the field's label, answer). First match wins, so specific patterns go first.
# An answer of None means "known question, no truthful answer on file" — required ones stop.
RULES: list[tuple] = [
    (r"\bfirst\s*name|given name|forename", _a("first_name"), "short"),
    (r"\blast\s*name|surname|family name", _a("last_name"), "short"),
    (r"preferred name|what would you like us to call you|nickname", _a("first_name"), "short"),
    (r"pronounc", None),
    (r"\b(full\s*)?name\b(?!.*(company|employer|school|university|reference|manager))", _a("full_name"), "short"),
    (r"e-?mail", _a("email"), "short"),
    (r"^\s*(home |street |residential |postal |current )?address\b", _a("location"), "short"),
    (r"referred by|know (someone|anyone)|referral from|employee referral", "No"),
    (r"valid (uae )?(residency|residence) visa|(residency|residence) visa in the uae", "Yes"),
    (r"phone|mobile|contact number", _a("phone"), "short"),
    (r"linked\s*in", _a("links.linkedin")),
    (r"git\s*hub", _a("links.github")),
    (r"portfolio|personal (web)?site|website|blog", _a("links.portfolio"), "short"),
    (r"current (company|employer)|employer name|organi[sz]ation", _a("current_company"), "short"),
    (r"current (job )?title|current (position|role)", _a("current_title")),
    (r"notice period", f"{_a('notice_period_days')} days"),
    (r"join immediately|immediate joiner|start immediately", f"No, available within {_a('notice_period_days')} days"),
    (r"(earliest|available|availability).*(start|join)|start date|when can you (start|join)", _a("earliest_start")),
    (r"current (salary|ctc|compensation|pay|package)|present salary|last drawn", _a("current_salary")),
    (r"(salary|compensation|pay).*(\$|usd|dollar)", _a("expected_salary.usd_text")),
    (r"salary|compensation|pay expectation|expected (ctc|package|pay)", _a("expected_salary.text")),
    (r"(require|need).*(sponsor|visa)|sponsorship", "No"),
    (r"visa status|current visa|type of visa|residency status", _a("work_authorization.visa")),
    (r"(legally )?(authori[sz]ed|eligible|permitted|right) to work|work authori[sz]ation|work permit", "Yes"),
    (r"relocat", "Yes"),
    (r"driv(ing|er'?s?) licen[cs]e", _a("driving_licence")),
    (r"^\s*(total |overall )?(years of )?(professional |relevant |work )?experience\s*(\(years\))?\s*\??\s*$|how many years of (professional |work )?experience do you have\s*\??$",
     str(_a("years_experience"))),
    (r"(highest|level of) (degree|education)|degree",
     [_a("education.degree"), "Bachelor's degree", "Bachelor's", "Bachelor", "BSc", "Undergraduate"]),
    (r"(which|what) (university|school|college)|(university|school|college) (did|do) you attend|university or school",
     [_a("education.school"), "Nile University", "Other (School Not Listed)", "Other"]),
    (r"university|school|college|institution", [_a("education.school"), "Nile University", "Other (School Not Listed)", "Other"], "short"),
    (r"graduat", str(_a("education.graduated") or "")[:4] or None),
    (r"nationality|citizenship", _a("nationality")),
    (r"date of birth|\bdob\b|birth ?date", _a("date_of_birth")),
    (r"^\s*gender|sex\b", _a("gender")),
    (r"\blocation\b|city|where are you (based|located)|where do you (currently )?live|country of residence|current(ly)? (living|residing)",
     [_a("location"), "United Arab Emirates", "UAE", "Dubai"], "short"),
    (r"language.*(check all|all that apply|select all)|(check all|all that apply|select all).*language", ["Arabic", "English"]),
    (r"^\s*language\s*#?\s*1\b", "Arabic", "short"),
    (r"^\s*language\s*#?\s*2\b", "English", "short"),
    (r"^\s*language\s*#?\s*[3-9]\b", None, "short"),
    (r"language", ", ".join(_a("languages") or [])),
    (r"hear about|heard about|how did you (find|learn)|referr?al source|source of application",
     ["Company website", "Company careers", "Careers page", "Careers site", "Website", "Job board", "Online job", "Other"]),
    (r"remote|hybrid|on-?site|work (arrangement|mode|model)", "Yes"),
]

DECLINE = re.compile(r"decline|prefer not|do not wish|don'?t wish|not to (say|disclose)|rather not", re.I)
EEO = re.compile(r"race|ethnic|veteran|disabilit|gender identity|sexual orientation|pronoun", re.I)
CONSENT = re.compile(r"agree|consent|acknowledge|privacy|terms|accurate|certify|confirm that", re.I)


def answer_for(label: str, job_answers: dict | None = None):
    """Return (known, answer). known=False means nothing on file matches the question.

    job_answers comes from the job folder's answers.json: answers the Routine wrote for that
    posting's own questions, keyed by a phrase from the question. They are checked first.
    """
    text = " ".join(label.split()).lower()
    for phrase, answer in (job_answers or {}).items():
        if phrase and " ".join(phrase.split()).lower() in text:
            return True, answer
    for pattern, answer, *flags in RULES:
        # Identity rules (name, school, address…) misfire inside long custom questions such as
        # "…please mention their full name" or "…Parents or University sponsorship". Those
        # belong in answers.json, so these rules only answer short, form-field-like labels.
        if "short" in flags and len(text) > 60:
            continue
        if re.search(pattern, text):
            return True, answer
    return False, None


# ----------------------------------------------------------------------------- page work

COLLECT_FIELDS = r"""
() => {
  const FIELDS = 'input, textarea, select';
  const LABELISH = 'label, legend, [class*="label"], [class*="title"], [class*="question"], [class*="prompt"]';
  const text = (n) => ((n && n.innerText) || '').trim();
  const isChoice = (el) => el.type === 'radio' || el.type === 'checkbox';
  const ownLabel = (el) => (el.id && document.querySelector(`label[for="${CSS.escape(el.id)}"]`)) || el.closest('label');
  // A label that wraps a field, or points at a radio/checkbox, names an option, not a question.
  const isOptionLabel = (c) => {
    if (c.querySelector(FIELDS)) return true;
    const target = c.htmlFor && document.getElementById(c.htmlFor);
    return !!target && isChoice(target);
  };
  // Walk up to the nearest question text. Stop before a block that holds a different field,
  // so one question's label never lands on its neighbour (Lever wraps each custom question
  // in its own card; its field names are opaque ids like cards[uuid][field0]).
  const questionLabel = (el) => {
    for (let node = el.parentElement, k = 0; node && node !== document.body && k < 7; node = node.parentElement, k++) {
      const others = [...node.querySelectorAll(FIELDS)].some(f => f !== el && f.type !== 'hidden'
        && !(el.name && f.name === el.name) && !(isChoice(el) && isChoice(f) && !el.name));
      if (others) break;
      for (const c of node.querySelectorAll(LABELISH)) {
        if (c.contains(el) || isOptionLabel(c)) continue;
        const t = text(c);
        if (t && t.length < 500) return { t, node: c };
      }
    }
    return { t: '', node: null };
  };
  const labelOf = (el) => {
    if (!isChoice(el)) {
      const forLabel = el.id && document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
      if (text(forLabel)) return { t: text(forLabel), node: forLabel };
    } else {
      const legend = el.closest('fieldset')?.querySelector('legend');
      if (text(legend)) return { t: text(legend), node: legend };
    }
    if (!isChoice(el) && el.getAttribute('aria-label')) return { t: el.getAttribute('aria-label'), node: null };
    const host = isChoice(el) ? el.closest('[role="radiogroup"], [role="group"]') || el : el;
    const by = host.getAttribute('aria-labelledby');
    if (by) {
      const t = by.split(/\s+/).map(i => { const n = document.getElementById(i);
        return (n && (n.innerText || n.textContent)) || ''; }).join(' ').trim();
      if (t) return { t, node: document.getElementById(by.split(/\s+/)[0]) };
    }
    const q = questionLabel(el);
    if (q.t) return q;
    const wrapping = !isChoice(el) && el.closest('label');
    if (wrapping && !wrapping.querySelector('select') && text(wrapping)) return { t: text(wrapping), node: wrapping };
    return { t: el.getAttribute('placeholder') || el.name || '', node: null };
  };
  const shown = (el) => {
    if (!el) return false;
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none';
  };
  // Custom-styled radios and checkboxes hide the real input and show its label instead.
  const visible = (el) => el.type === 'file' || shown(el) || (isChoice(el) && shown(ownLabel(el)));
  // Many boards (Ashby among them) mark required fields only with a CSS asterisk or a class.
  const markedRequired = (lab) => !!lab && (/required/i.test(lab.className || '')
    || /[*✱]/.test(getComputedStyle(lab, '::after').content || '')
    || !!lab.querySelector('[class*="required"]'));
  // Text and class names of the block that holds this field and no other, used to spot
  // resume "autofill" boxes that sit next to the real resume field.
  const contextOf = (el) => {
    let t = '';
    for (let node = el.parentElement; node && node !== document.body; node = node.parentElement) {
      if (node.querySelectorAll(FIELDS).length > 1) break;
      t += ' ' + (typeof node.className === 'string' ? node.className : '') + ' ' + (node.innerText || '').slice(0, 200);
    }
    return t.slice(0, 1200);
  };
  const out = [];
  document.querySelectorAll(FIELDS).forEach((el, i) => {
    const type = (el.type || el.tagName).toLowerCase();
    if (['hidden', 'submit', 'button', 'image', 'reset', 'search'].includes(type)) return;
    if (!visible(el)) return;
    el.setAttribute('data-easier-idx', String(i));
    const found = labelOf(el);
    // Teamtailor and others append "* Required" to the label text.
    const label = found.t.replace(/\s*[*✱]*\s*\(?required\)?\s*$/i, '').replace(/\s*[*✱]+\s*$/, '')
      .replace(/^\s*[*✱]\s*/, '').replace(/\s+/g, ' ').trim();
    const required = el.required || el.getAttribute('aria-required') === 'true'
      || !!el.closest('[aria-required="true"]') || /[*✱]\s*(\(?required\)?)?\s*$/i.test(found.t)
      || /^\s*[*✱]/.test(found.t) || /\brequired\s*$/i.test(found.t) || markedRequired(found.node);
    const options = el.tagName === 'SELECT' ? [...el.options].map(o => o.text.trim()).filter(Boolean) : [];
    let radioLabel = '';
    if (isChoice(el)) radioLabel = (text(ownLabel(el)) || el.value || '').trim();
    out.push({ idx: String(i), type, name: el.name || '', label, required, options, radioLabel,
               group: isChoice(el) ? (el.name || 'q:' + label) : '',
               role: el.getAttribute('role') || '', context: type === 'file' ? contextOf(el) : '' });
  });
  return out;
}
"""


COLLECT_BUTTON_GROUPS = """
() => {
  const out = [], seen = new Set();
  document.querySelectorAll('button').forEach(b => {
    const t = (b.innerText || '').trim().toLowerCase();
    if (t !== 'yes' && t !== 'no') return;
    const group = b.parentElement;
    if (!group || seen.has(group)) return;
    const buttons = [...group.querySelectorAll('button')];
    const texts = buttons.map(x => (x.innerText || '').trim().toLowerCase());
    if (buttons.length > 4 || !texts.includes('yes') || !texts.includes('no')) return;
    seen.add(group);
    const gi = out.length;
    buttons.forEach((x, j) => x.setAttribute('data-easier-bg', gi + '-' + j));
    let lab = null;
    for (let node = group.parentElement, k = 0; k < 5 && node && !lab; k++, node = node.parentElement) {
      const found = node.querySelector('label, legend, [class*="title"], [class*="label"], [class*="question"]');
      if (found && !group.contains(found) && found.innerText.trim()) lab = found;
    }
    const label = lab ? lab.innerText.trim() : '';
    const required = /\\*\\s*$/.test(label) || (!!lab && (/required/i.test(lab.className || '')
      || /\\*/.test(getComputedStyle(lab, '::after').content || '')));
    out.push({ gi: String(gi), label: label.replace(/\\*+\\s*$/, '').trim(), required, options: texts });
  });
  return out;
}
"""

# Read after a submit click, so a run that is not confirmed says why.
AFTER_SUBMIT = """
() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const texts = (sel) => [...document.querySelectorAll(sel)].filter(vis)
    .map(e => (e.innerText || '').trim()).filter(t => t && t.length < 300);
  const invalid = [...document.querySelectorAll('[aria-invalid="true"]')].map(e =>
    e.getAttribute('aria-label') || e.name || e.id || e.tagName);
  return {
    url: location.href,
    alerts: texts('[role="alert"], [aria-live="assertive"], [aria-live="polite"]').slice(0, 6),
    errors: texts('[class*="error" i], [class*="invalid" i], [class*="danger" i]').slice(0, 8),
    invalid: invalid.slice(0, 8),
    tail: (document.body.innerText || '').replace(/\\s+/g, ' ').trim().slice(-700),
    // The markup around each question the page says is missing, to see how it is built.
    blocks: [...document.querySelectorAll('[class*="error" i], [role="alert"]')]
      .map(e => ((e.innerText || '').match(/required field:\\s*(.+)/i) || [])[1]).filter(Boolean)
      .slice(0, 3).map(q => {
        const hit = [...document.querySelectorAll('label, legend, [class*="title"], [class*="label"]')]
          .find(n => (n.innerText || '').trim().startsWith(q.trim().slice(0, 40)));
        let box = hit;
        for (let k = 0; box && k < 3; k++) box = box.parentElement;
        return box ? box.outerHTML.slice(0, 5000) : '';
      }),
  };
}
"""


def _pick(options: list[str], answer: str) -> str | None:
    """The option that best matches an answer: exact, then prefix, then containment."""
    norm = lambda t: " ".join(str(t).split()).lower()  # noqa: E731
    within = lambda x, y: bool(x) and re.search(rf"(?<!\w){re.escape(x)}(?!\w)", y) is not None  # noqa: E731
    a = norm(answer)
    for test in (lambda o: o == a, lambda o: o.startswith(a), lambda o: within(o, a), lambda o: within(a, o)):
        for option in options:
            if test(norm(option)):
                return option
    return None


def _first(answer) -> str:
    return str(answer[0] if isinstance(answer, list) else answer)


def _pick_any(options: list[str], answer) -> str | None:
    """Like _pick, but an answer may be a list of acceptable values in order of preference."""
    for a in answer if isinstance(answer, list) else [answer]:
        if a and (choice := _pick(options, str(a))):
            return choice
    return None


def _combobox(page, el, answer) -> tuple[bool, list[str]]:
    """Choose from a custom dropdown (role=combobox). Read-only ones can't be typed into, so
    open the list and click the matching option; typeable ones filter first. Returns whether
    an option was chosen, and the options that were on offer."""
    texts: list[str] = []
    try:
        el.click(timeout=5_000)
        if el.get_attribute("readonly") is None:
            el.fill(_first(answer))
        page.wait_for_timeout(800)
        owns = el.get_attribute("aria-controls") or el.get_attribute("aria-owns")
        scope = page.locator(f"#{owns}") if owns else page
        options = scope.locator('[role="option"]')
        texts = [t.strip() for t in options.all_inner_texts()]
        choice = _pick_any(texts, answer)
        if choice is None:
            page.keyboard.press("Escape")
            return False, texts
        options.nth(texts.index(choice)).click(timeout=5_000)
        return True, texts
    except Exception:
        return False, texts


def _check(page, idx: str) -> None:
    """Tick a radio or checkbox, including custom-styled ones whose real input is hidden."""
    el = page.locator(f'[data-easier-idx="{idx}"]')
    try:
        el.check(timeout=3_000)
        return
    except Exception:
        pass
    ident = el.get_attribute("id")
    label = page.locator(f'label[for="{ident}"]') if ident else None
    if label is not None and label.count():
        label.first.click(timeout=3_000)
    else:
        el.dispatch_event("click")


def dismiss_banners(page) -> None:
    """Cookie and consent dialogs sit over the form and swallow clicks."""
    for name in (r"^\s*(accept|allow)( all)?( cookies)?\s*$", r"^\s*(i agree|agree|got it|ok|okay)\s*$"):
        button = page.get_by_role("button", name=re.compile(name, re.I))
        try:
            if button.count() and button.first.is_visible():
                button.first.click(timeout=3_000)
                page.wait_for_timeout(800)
                return
        except Exception:
            continue


def open_form(page, ats: str, url: str) -> None:
    target = url
    if ats == "lever" and not url.rstrip("/").endswith("/apply"):
        target = url.rstrip("/") + "/apply"
    elif ats == "ashby" and not url.rstrip("/").endswith("/application"):
        target = url.rstrip("/") + "/application"
    page.goto(target, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(2_500)
    dismiss_banners(page)
    # Workable, SmartRecruiters, company careers pages and some Greenhouse boards put the form
    # behind an Apply button. A link is followed by URL: it often opens a new tab or sits
    # under an overlay, and either way a click would leave this page where it was.
    for _ in range(2):
        if page.locator("input[type=file]").count():
            break
        for name in (r"apply( for this (job|role|position)| now)?", r"i'?m interested"):
            button = page.get_by_role("link", name=re.compile(name, re.I)).or_(
                page.get_by_role("button", name=re.compile(name, re.I)))
            if not button.count():
                continue
            href = button.first.get_attribute("href") or ""
            if href and not href.startswith(("#", "javascript:", "mailto:")):
                page.goto(urljoin(page.url, href), wait_until="domcontentloaded", timeout=60_000)
            else:
                button.first.click(timeout=10_000)
            page.wait_for_timeout(3_000)
            dismiss_banners(page)
            break
        else:
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


def fill_form(page, cv_pdf: Path, letter_pdf: Path | None, letter_text: str,
              job_answers: dict | None = None) -> dict:
    fields = page.evaluate(COLLECT_FIELDS)
    filled, unanswered = [], []
    groups: dict[str, list] = {}

    for f in fields:
        sel = f'[data-easier-idx="{f["idx"]}"]'
        el = page.locator(sel)
        label, low = f["label"], f["label"].lower()

        if f["type"] in ("radio", "checkbox"):
            groups.setdefault(f["group"], []).append(f)
            continue

        if f["type"] == "file":
            # Ashby-style "autofill from resume" boxes parse the upload and can overwrite
            # fields already filled; the real resume field comes later in the form.
            if re.search(r"autofill|auto-fill|parse|import", low + " " + f.get("context", "").lower()):
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

        known, answer = answer_for(label, job_answers)
        if not known or answer in (None, "", "None"):
            if f["required"]:
                unanswered.append(label or f["name"] or "unlabelled field")
            continue

        if f["type"] == "select-one":
            choice = _pick_any(f["options"], answer)
            if choice:
                el.select_option(label=choice); filled.append(label)
            elif f["required"]:
                unanswered.append(label)
        elif f["role"] == "combobox":
            ok, seen = _combobox(page, el, answer)
            f["options"] = seen
            if ok:
                filled.append(label)
            elif f["required"]:
                unanswered.append(label)
        else:
            el.fill(_first(answer)); filled.append(label)

    for name, options in groups.items():
        group_label = options[0]["label"]
        low = group_label.lower()
        required = any(o["required"] for o in options)
        if all(o["type"] == "checkbox" for o in options) and len(options) == 1:
            if CONSENT.search(low + " " + options[0]["radioLabel"].lower()):
                _check(page, options[0]["idx"]); filled.append("consent")
            elif required:
                unanswered.append(group_label)
            continue
        labels = [o["radioLabel"] for o in options]
        if EEO.search(low):
            picks = [o for o in options if DECLINE.search(o["radioLabel"])][:1]
        else:
            known, answer = answer_for(group_label, job_answers)
            if known and answer and isinstance(answer, list) and all(o["type"] == "checkbox" for o in options):
                # "Check all that apply": tick every option the answer names.
                chosen = {_pick(labels, a) for a in answer} - {None}
                picks = [o for o in options if o["radioLabel"] in chosen]
            else:
                choice = _pick_any(labels, answer) if known and answer else None
                picks = [o for o in options if o["radioLabel"] == choice][:1]
        if picks:
            for o in picks:
                _check(page, o["idx"])
            filled.append(group_label)
        elif required:
            unanswered.append(group_label)

    for g in page.evaluate(COLLECT_BUTTON_GROUPS):
        known, answer = answer_for(g["label"], job_answers)
        want = str(answer).strip().lower() if known and answer else ""
        want = "yes" if want.startswith("yes") else "no" if want.startswith("no") else ""
        if want in g["options"]:
            page.locator(f'[data-easier-bg="{g["gi"]}-{g["options"].index(want)}"]').click()
            filled.append(f'{g["label"] or "yes/no question"} ({want})')
        elif g["required"]:
            unanswered.append(g["label"] or "unlabelled yes/no question")

    # What each unanswered question offered, so answers.json can be written from the real
    # options rather than guessed.
    offered = {f["label"]: f["options"] for f in fields if f["options"]}
    for key, opts in groups.items():
        offered.setdefault(opts[0]["label"], [o["radioLabel"] for o in opts])
    detail = [{"question": q, "options": offered.get(q, [])[:25]} for q in unanswered]
    return {"filled": filled, "unanswered": unanswered, "unanswered_detail": detail}


def submit(page, result: dict) -> tuple[str, str]:
    button = page.get_by_role("button", name=SUBMIT)
    if not button.count():
        button = page.locator("button[type=submit], input[type=submit]")
    if not button.count():
        return "needs-you", "no submit button found"
    page.wait_for_timeout(2_000)
    button.last.scroll_into_view_if_needed()
    button.last.click()
    either = f"(?:{CONFIRMATION.pattern})|(?:{ALREADY.pattern})"
    for _ in range(3):
        try:
            page.wait_for_function(
                "(re) => new RegExp(re, 'i').test(document.body.innerText)", arg=either, timeout=30_000,
            )
            break
        except PlaywrightTimeout:
            # A slow upload shows "Submitting…"; keep waiting rather than call it failed.
            if not re.search(r"submitting|uploading|please wait", page.inner_text("body"), re.I):
                break
    body = page.inner_text("body")
    if CONFIRMATION.search(body):
        return "applied", ""
    if ALREADY.search(body):
        return "applied", "already applied earlier"

    after = page.evaluate(AFTER_SUBMIT)
    after["frames"] = [f.url[:160] for f in page.frames if f.url and f.url != "about:blank"][:10]
    result["after_submit"] = after
    if re.search(r"submitting|uploading|please wait", body, re.I):
        return "needs-you", "still submitting after 90s — check your email before applying again"
    print(f"    after submit: {json.dumps(after, ensure_ascii=False)[:1500]}")
    if visible_captcha(page):
        return "needs-you", "CAPTCHA"
    said = next((t for t in after["alerts"] + after["errors"] if t), "")
    if SPAM.search(" ".join(after["alerts"] + after["errors"] + [after["tail"]])):
        return "needs-you", "site flagged the automated submission"
    if after["invalid"] or said:
        return "needs-you", f"form rejected the submission: {said[:80] or ', '.join(after['invalid'][:3])}"
    return "needs-you", "submission not confirmed"


# ----------------------------------------------------------------------------- per job

def cv_answers(folder: Path) -> dict:
    """Profile fields some boards ask for (Workable's Headline and Summary), taken from this
    job's tailored CV so they say the same thing it does."""
    cv = folder / "cv.md"
    if not cv.is_file():
        return {}
    lines = [l.strip() for l in cv.read_text().splitlines()]
    out = {}
    if len(lines) > 1 and lines[1].startswith("**"):
        out["headline"] = lines[1].strip("*").strip().title().replace("Ai ", "AI ").replace("Llm", "LLM").replace("Rag", "RAG")
    body = [l for l in lines[4:12] if l and not l.startswith(("#", "[", "-", "+", "*"))]
    if body:
        out["summary"] = body[0]
    return out


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
    answers_file = folder / "answers.json"
    job_answers = {**cv_answers(folder), **(json.loads(answers_file.read_text()) if answers_file.is_file() else {})}

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
                outcome = fill_form(page, cv_pdf, letter_pdf if letter_pdf.is_file() else None, letter_text,
                                    job_answers)
                result.update(outcome)
                print(f"    filled: {outcome['filled']}")
                print(f"    unanswered: {outcome['unanswered']}")
                if outcome["unanswered"]:
                    shown = "; ".join(q[:60] for q in outcome["unanswered"][:2])
                    result["reason"] = f"custom questions: {shown}"
                elif dry_run:
                    result["status"], result["reason"] = "dry-run", "filled, not submitted"
                else:
                    result["status"], result["reason"] = submit(page, result)
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
        # Headed under a virtual display on the runner: the same browser a person would use.
        browser = p.chromium.launch(headless=not os.environ.get("DISPLAY"))
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
