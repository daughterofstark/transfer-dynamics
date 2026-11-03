# Output map

All generated files go under the chosen output directory; no manuscript files change.

| Paper item | Generated output |
| --- | --- |
| Cohort totals and observed SD denominators | `tables/cohort.json` |
| Main Table 1, grouped coefficients and derived half-lives | `tables/table_1.csv` |
| Supplementary Tables 1, 2, 3 | `tables/supplement_table_1.csv`, `supplement_table_2.csv`, `supplement_table_3.csv`, `supplement_table_3_later_followup.csv` |
| Supplementary Table 4 / held-out benchmark comparison | `tables/supplement_table_4.csv`, `prediction_metrics.json` |
| Supplementary Table 5 | `tables/supplement_table_5.csv`, `slowing_400.json`, `retest_saturation.json` |
| Supplementary Table 6 / reference coefficients | `tables/supplement_table_6.csv`, `age_reference.json` |
| Within-person association | `tables/within_person.json` |
| GI contrast and standardized companions | `tables/effect_size.json` |
| Maintenance dose targets | `tables/maintenance.json` |
| Figure 1 | `figures/Figure_1.png` and `.svg`; illustrative, not participant data |
| Figure 2 | `figures/Figure_2.png` and `.svg`; cohort/interval distributions |
| Figure 3 | `figures/Figure_3.png` and `.svg`; rebuilt aggregate held-out predictions |
| Figure 4 | `figures/Figure_4.png` and `.svg`, `booster_comparison.json`, `illustrative_trajectories.csv` |
| Audit | `input_validation.json`, `replay_audit.json`, run/replay manifests |

Table S5's slowing-decay training half-retention is history-dependent and comes from `slowing_400.json` (400 gameplays over 90 days), not the isolated-input half-time. The aging comparator's retest decay reaches its lower bound; `report_as_bound` flags that numerical result so it is not reported as a finite biological half-life. Comparisons omitted from a run have blank RMSE entries. Saved reference values never substitute silently for an unrun prediction check.

Paper tables contain editorial grouping, labels and rounding. The CSV/JSON files provide numerical source values rather than regenerating the prose/Word documents. Manuscript sources, current figure exports and references are tracked together; Word export is a separate publishing step.
