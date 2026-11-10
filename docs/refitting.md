# Independent refitting

Refits do not overwrite the saved reference fits or manuscript. Use a separate output directory:

```sh
python reproduce.py fit --model primary --phase point --output outputs/refit
python reproduce.py fit --model primary --phase cv --workers 4 --output outputs/refit
python reproduce.py fit --model primary --phase bootstrap --workers 4 --output outputs/refit

python reproduce.py fit --model saturating --phase point --output outputs/refit
python reproduce.py fit --model saturating --phase cv --workers 4 --output outputs/refit
python reproduce.py fit --model saturating --phase bootstrap --workers 4 --output outputs/refit

python reproduce.py fit --model benchmarks --phase point --output outputs/refit
python reproduce.py fit --model benchmarks --phase cv --workers 4 --output outputs/refit

python reproduce.py fit --model drift --phase point --output outputs/refit
python reproduce.py fit --model drift --phase cv --workers 4 --output outputs/refit
python reproduce.py fit --model drift --phase bootstrap --workers 4 --output outputs/refit

python reproduce.py fit --model slowing --phase point --output outputs/refit
python reproduce.py fit --model slowing --phase cv --workers 3 --output outputs/refit
python reproduce.py fit --model slowing --phase bootstrap --workers 4 --output outputs/refit

python reproduce.py all --results outputs/refit/fits --output outputs/refit/report --comparisons --audit-bootstrap
```

The primary, saturation, aging and slowing-decay models use the same 500 saved participant bootstrap seeds. Predictive benchmarks are compared using the matched cross-validation folds and have no parameter bootstrap. Folds use seed 291029. Fit files save completed jobs and resume; a source/input/runtime manifest prevents silently mixing different runs. Failed fits are errors, never silently dropped. Independent refits can differ slightly numerically from saved fits; compare objectives and reporting precision, not bitwise parameter equality.

For a smoke run, `--fold 0` fits one CV fold and `--draws 1` fits one bootstrap draw after the point fit. A partial run is deliberately rejected for full paper reporting. Each worker loads the approximately 230 MB model input; choose workers for available memory.
