#!/usr/bin/env bash
# Reproduce every number, table and figure reported for v17.
#   ./run_paper.sh           full run: 200 bootstrap samples and figures (~50 min)
#   ./run_paper.sh --quick   20 bootstrap samples, no figures (~6 min)
# Both modes write to out/v17/ and rebuild the merged data from the raw inputs.
set -eo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-.venv/bin/python}"
DATA="${DATA:-data/newsubset.csv}"
COMPOSITE="${COMPOSITE:-data/short_intervals.csv}"
OUT="${OUTPUT:-out/v17}"
WORKERS="${WORKERS:-1}"
GI_POLICY="${GI_BATTERY_POLICY:-same-battery}"

if ! "$PY" -c "import numpy, scipy, pandas, matplotlib, seaborn" 2>/dev/null; then
  echo "Python environment not found or incomplete: $PY"
  echo "Set it up with: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi
for f in "$DATA" "$COMPOSITE"; do
  if [ ! -f "$f" ]; then echo "Missing input: $f (see data/README.md)"; exit 1; fi
done

NBOOT=200
SKIP=""
if [ "${1:-}" = "--quick" ]; then NBOOT=20; SKIP="--skip-figures"; fi

"$PY" run_v17.py --data "$DATA" --composite "$COMPOSITE" --nboot "$NBOOT" --workers "$WORKERS" --out "$OUT" --gi-battery-policy "$GI_POLICY" --rebuild $SKIP
"$PY" descriptives_v17.py --data "$DATA" --composite "$COMPOSITE" --out "$OUT" --gi-battery-policy "$GI_POLICY"

echo "Done. Reports: $OUT/report.md and $OUT/descriptives.md"
