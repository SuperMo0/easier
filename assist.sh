#!/usr/bin/env bash
# Finish the jobs waiting on you from this PC. Each one opens in your own Chrome, where the easier
# extension fills it in; you upload the CV, press Submit, and the outcomes are pushed back.
#
#   ./assist.sh                 every job waiting on you (CAPTCHA, error, questions)
#   ./assist.sh jobs/<folder>   just that one
#   ./assist.sh --playwright jobs/<folder>   in the automated Chrome instead (not Workable/Lever)
#   ./assist.sh --stats         how many internship / junior / mid-level roles you've applied to
#   ./assist.sh --stats junior  the junior ones (also intern, mid, all; --rejected includes rejections)
set -euo pipefail
cd "$(dirname "$0")"

# System Python on Debian/Ubuntu refuses pip installs (PEP 668), so everything lives in .venv.
if [ ! -x .venv/bin/python ]; then
  echo "First run: setting up .venv (needs python3-venv; installs Chromium's system libraries with sudo)"
  python3 -m venv .venv || { echo "Run: sudo apt install -y python3-venv   then try again"; exit 1; }
  .venv/bin/pip install --quiet --upgrade pip
  .venv/bin/pip install --quiet playwright playwright-stealth pyyaml markdown
  .venv/bin/python -m playwright install --with-deps chromium chrome
fi

# --autostash: a run stopped with Ctrl+C leaves outcome files uncommitted.
git pull --quiet --rebase --autostash

# Application stats by level, no browser: easier --stats [intern|junior|mid|all] [--rejected]
if [ "${1:-}" = "--stats" ]; then
  shift
  exec .venv/bin/python scripts/stats.py "$@"
fi

if [ "$#" -gt 0 ]; then
  .venv/bin/python scripts/apply.py --assist "$@"
else
  .venv/bin/python scripts/apply.py --assist --waiting
fi
.venv/bin/python scripts/index.py >/dev/null

git add jobs
if ! git diff --cached --quiet; then
  git commit --quiet -m "Assist: record outcomes"
  git push --quiet || echo "Push failed: the outcomes are committed locally; run 'git push' once GitHub access is set up."
fi
