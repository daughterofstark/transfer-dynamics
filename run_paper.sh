#!/usr/bin/env bash
# Full reproduction.  ./run_paper.sh [--quick]
set -euo pipefail
DATA="${DATA:-data/newsubset.csv}"
NICOLE="${NICOLE:-data/short_intervals.csv}"
NBOOT=200; [[ "${1:-}" == "--quick" ]] && NBOOT=20

for f in "$DATA" "$NICOLE"; do
  [[ -f "$f" ]] || { echo "missing input: $f  (see data/README.md)"; exit 1; }
done
mkdir -p out/fig_main out/fig_supp out/logs
LOG="out/logs/pipeline_$(date +%Y%m%d_%H%M%S).log"

echo "==> pipeline (nboot=$NBOOT)"
python paper_pipeline.py --data "$DATA" --nicole "$NICOLE" --nboot "$NBOOT" \
    --main-dir out/fig_main --supp-dir out/fig_supp \
    --merged-csv out/merged_for_fit.csv 2>&1 | tee "$LOG"

echo "==> verification numbers"
python verify_numbers.py --data "$DATA" --nicole "$NICOLE" \
    --only exposure sweep rescale unweighted 2>&1 | tee out/logs/verify.log

echo "==> intercept check"
python intercept_check.py --data "$DATA" --nicole "$NICOLE" 2>&1 | tee out/logs/intercept.log

echo; echo "==> manifest check"
if grep -q "FAIL" "$LOG"; then
  echo "!! FAILURES — do not trust the output:"; grep "FAIL" "$LOG"; exit 1
fi
echo "   clean."
echo; echo "figures: out/fig_main/ out/fig_supp/   logs: out/logs/"
echo "canonical numbers: end of $LOG"
