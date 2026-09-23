// easier — application autofill (Workable, Lever)
//
// Runs in the page itself (a normal content script, not Chrome DevTools Protocol), so their
// bot checks (Cloudflare Turnstile, hCaptcha) have nothing to flag — unlike Playwright, which
// this exists specifically to avoid using on these boards. Fetches this job's already-resolved
// answers from a local server apply.py starts for the duration of one job (see _fill_server in
// scripts/apply.py) and fills every field it can match. File inputs are never touched: browsers
// block scripts from setting them for security, so the CV/cover-letter upload always stays a
// manual click.

(() => {
  const SERVER = "http://127.0.0.1:8765/easier.json";
  const FIELDS_SELECTOR = "input, textarea, select";
  const LABELISH = 'label, legend, [class*="label"], [class*="title"], [class*="question"], [class*="prompt"]';

  const norm = (s) => (s || "").replace(/\s+/g, " ").trim().toLowerCase();
  const text = (n) => norm(n && n.innerText);
  const isChoice = (el) => el.type === "radio" || el.type === "checkbox";

  const shown = (el) => {
    if (!el) return false;
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== "hidden" && s.display !== "none";
  };
  const ownLabel = (el) => (el.id && document.querySelector(`label[for="${CSS.escape(el.id)}"]`)) || el.closest("label");
  const visible = (el) => el.type === "file" || shown(el) || (isChoice(el) && shown(ownLabel(el)));

  // Walk up to the nearest question text, same heuristic as the Playwright-side collector:
  // stop before a block that holds a different field, so one question's label never lands on
  // its neighbour.
  const isOptionLabel = (c) => {
    if (c.querySelector(FIELDS_SELECTOR)) return true;
    const target = c.htmlFor && document.getElementById(c.htmlFor);
    return !!target && isChoice(target);
  };
  const questionLabel = (el) => {
    for (let node = el.parentElement, k = 0; node && node !== document.body && k < 7; node = node.parentElement, k++) {
      const others = [...node.querySelectorAll(FIELDS_SELECTOR)].some(
        (f) => f !== el && f.type !== "hidden" && !(el.name && f.name === el.name) && !(isChoice(el) && isChoice(f) && !el.name)
      );
      if (others) break;
      for (const c of node.querySelectorAll(LABELISH)) {
        if (c.contains(el) || isOptionLabel(c)) continue;
        const t = text(c);
        if (t && t.length < 500) return t;
      }
    }
    return "";
  };

  function labelOf(el) {
    if (!isChoice(el)) {
      const forLabel = el.id && document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
      if (text(forLabel)) return text(forLabel);
    } else {
      const legend = el.closest("fieldset")?.querySelector("legend");
      if (text(legend)) return text(legend);
    }
    if (!isChoice(el) && el.getAttribute("aria-label")) return norm(el.getAttribute("aria-label"));
    const host = isChoice(el) ? el.closest('[role="radiogroup"], [role="group"]') || el : el;
    const by = host.getAttribute("aria-labelledby");
    if (by) {
      const t = by.split(/\s+/).map((i) => (document.getElementById(i)?.innerText) || "").join(" ");
      if (norm(t)) return norm(t);
    }
    const q = questionLabel(el);
    if (q) return q;
    const wrapping = !isChoice(el) && el.closest("label");
    if (wrapping && !wrapping.querySelector("select") && text(wrapping)) return text(wrapping);
    return norm(el.getAttribute("placeholder") || el.name || "");
  }

  function collectFields() {
    const out = [];
    document.querySelectorAll(FIELDS_SELECTOR).forEach((el) => {
      const type = (el.type || el.tagName).toLowerCase();
      if (["hidden", "submit", "button", "image", "reset", "search"].includes(type)) return;
      if (!visible(el)) return;
      out.push({
        el, type,
        label: labelOf(el).replace(/\s*[*✱]*\s*\(?required\)?\s*$/i, "").replace(/\s*[*✱]+\s*$/, "").trim(),
        group: isChoice(el) ? el.name || "q:" + labelOf(el) : "",
        radioLabel: isChoice(el) ? text(ownLabel(el)) || el.value || "" : "",
      });
    });
    return out;
  }

  // The best-matching (label, answer) pair: exact label match first, then the longest known
  // label that's a substring of the field's label or vice versa — same containment idea as
  // answer_for() on the Python side, since these rows are already its resolved output.
  function findAnswer(label, ...pairLists) {
    let best = null;
    for (const pairs of pairLists) {
      for (const [knownLabel, answer] of pairs) {
        const k = norm(knownLabel);
        if (!k || !answer) continue;
        if (label === k || label.includes(k) || k.includes(label)) {
          if (!best || k.length > best.k.length) best = { k, answer };
        }
      }
      if (best) return best.answer; // a form-specific match always wins over a standard one
    }
    return null;
  }

  function pickOption(options, answer) {
    const a = norm(answer);
    const tests = [(o) => norm(o) === a, (o) => norm(o).startsWith(a), (o) => norm(o).includes(a), (o) => a.includes(norm(o))];
    for (const test of tests) {
      const hit = options.find(test);
      if (hit) return hit;
    }
    return null;
  }

  function setNativeValue(el, value) {
    const proto = el.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, "value").set;
    setter.call(el, value);
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
  }

  // The Python server starts before the tab opens, but a slow page or a person switching back
  // to an older tab can still race it — retry a few times before giving up.
  async function fetchData() {
    let lastErr;
    for (let i = 0; i < 5; i++) {
      try {
        const res = await fetch(SERVER, { cache: "no-store" });
        return await res.json();
      } catch (e) {
        lastErr = e;
        await new Promise((r) => setTimeout(r, 1000));
      }
    }
    throw lastErr;
  }

  async function fill() {
    let data;
    try {
      data = await fetchData();
    } catch (e) {
      showBanner(null, `easier's local server isn't reachable (${e.name}: ${e.message}) — is assist.sh's Workable step still open?`);
      return;
    }

    try {
      runFill(data);
    } catch (e) {
      showBanner(null, `easier hit an error while filling (${e.name}: ${e.message}) — see the console for details.`);
      console.error("easier: fill() failed", e);
    }
  }

  function runFill(data) {
    const formRows = data.formRows || [];
    const standardAnswers = data.standardAnswers || [];
    const fields = collectFields();
    const groups = new Map();
    let filled = 0;
    const skipped = [];

    for (const f of fields) {
      if (f.type === "file") continue; // always manual
      if (isChoice(f.el)) {
        if (!groups.has(f.group)) groups.set(f.group, []);
        groups.get(f.group).push(f);
        continue;
      }
      const answer = findAnswer(f.label, formRows, standardAnswers);
      if (!answer) { if (f.label) skipped.push(f.label); continue; }
      if (f.el.tagName === "SELECT") {
        const options = [...f.el.options].map((o) => o.text.trim());
        const choice = pickOption(options, answer);
        if (choice) {
          f.el.value = [...f.el.options].find((o) => o.text.trim() === choice).value;
          f.el.dispatchEvent(new Event("change", { bubbles: true }));
          filled++;
        } else skipped.push(f.label);
      } else {
        setNativeValue(f.el, answer);
        filled++;
      }
    }

    for (const [, options] of groups) {
      const groupLabel = options[0].label;
      const answer = findAnswer(groupLabel, formRows, standardAnswers);
      if (!answer) { if (groupLabel) skipped.push(groupLabel); continue; }
      const labels = options.map((o) => o.radioLabel);
      const choice = pickOption(labels, answer);
      if (choice) {
        const target = options.find((o) => o.radioLabel === choice);
        if (!target.el.checked) target.el.click();
        filled++;
      } else skipped.push(groupLabel);
    }

    showBanner(filled, skipped);
  }

  function showBanner(filled, skipped) {
    document.getElementById("easier-banner")?.remove();
    const box = document.createElement("div");
    box.id = "easier-banner";
    box.style.cssText =
      "position:fixed;right:16px;bottom:16px;z-index:2147483647;max-width:320px;" +
      "font:13px/1.4 system-ui,sans-serif;background:#1b2430;color:#f3f6fb;border-radius:10px;" +
      "padding:12px 14px;box-shadow:0 6px 24px rgba(0,0,0,.3)";
    const skippedList = Array.isArray(skipped) && skipped.length
      ? `<div style="margin-top:6px;opacity:.85">Still needs you: ${skipped.slice(0, 6).map((s) => s || "(unlabelled)").join("; ")}${skipped.length > 6 ? "…" : ""}</div>`
      : "";
    const summary = filled === null
      ? `<div>${skipped}</div>`
      : `<div><b>easier</b> filled ${filled} field${filled === 1 ? "" : "s"}. Upload the CV/cover letter yourself.</div>${skippedList}`;
    box.innerHTML = `${summary}<button id="easier-refill" style="margin-top:8px;cursor:pointer;border:1px solid #4a5566;background:#2a3444;color:#f3f6fb;border-radius:6px;padding:4px 10px">Re-run autofill</button>`;
    document.body.appendChild(box);
    document.getElementById("easier-refill").onclick = fill;
  }

  setTimeout(fill, 1200);
})();
