#!/usr/bin/env bash
# Build the static site and deploy it to the gh-pages branch (GitHub Pages).
# Run from the repo root:  ./deploy.sh
# Requires: the backend venv active (for the data export) and Node/npm.
set -euo pipefail

REPO_URL="https://github.com/shreyas463/2026-fifa-world-cup-final-predictor.git"
BASE="/2026-fifa-world-cup-final-predictor/"
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "→ Exporting pre-computed data…"
( cd "$ROOT/backend" && python -m scripts.export_static )

echo "→ Building static site…"
( cd "$ROOT/frontend" && VITE_STATIC=true VITE_BASE="$BASE" npm run build && touch dist/.nojekyll )

echo "→ Publishing to gh-pages…"
cd "$ROOT/frontend/dist"
rm -rf .git
git init -q -b gh-pages
git add -A
git commit -q -m "Deploy static site"
git push -f "$REPO_URL" gh-pages
rm -rf .git

echo "✅ Deployed → https://shreyas463.github.io/2026-fifa-world-cup-final-predictor/"
