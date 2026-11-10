# Output map

All generated files go under the chosen output directory; no manuscript files change.

| Paper item | Generated output |
| --- | --- |
| Cohort totals and observed SD denominators | `tables/cohort.json` |
| Main Table 1, grouped coefficients and derived half-lives | `tables/table_1.csv` |
| Supplementary Tables 1, 2, 3 | `tables/supplement_table_1.csv`, `supplement_table_2.csv`, `supplement_table_3.csv`, `supplement_table_3_later_followup.csv` |
| Benchmark values introducing Supplementary Table 4 | `tables/supplement_table_4.csv`, `prediction_metrics.json` |
| Supplementary Table 4 / selected alternatives | `tables/supplement_table_5.csv`, `slowing_400.json`, `retest_saturation.json` |
| Coefficient correlations and baseline age-reference coefficients (retained analysis outputs) | `tables/supplement_table_6.csv`, `age_reference.json` |
| Within-person association | `tables/within_person.json` |
| GI contrast and standardized companions | `tables/effect_size.json` |
| Maintenance dose targets | `tables/maintenance.json` |
| Figure 1 | `figures/Figure_1.png` and `.svg`; illustrative, not participant data |
| Figure 2 | `figures/Figure_2.png` and `.svg`; cohort/interval distributions |
| Figure 3 | `figures/Figure_3.png` and `.svg`; rebuilt aggregate held-out predictions |
| Figure 4 | `figures/Figure_4.png` and `.svg`, `booster_comparison.json`, `illustrative_trajectories.csv` |
| Supplementary Figure 1 / Table 5 | `figures/Supplementary_Figure_1.png`, `.svg`, `supplementary_schedule_comparison.json`, `supplementary_schedule_trajectories.csv` |
| Fixed-amount timing contrast | `tables/timing_contrast.json` |
| Audit | `input_validation.json`, `replay_audit.json`, run/replay manifests |

Table S4's slowing-decay training half-retention is history-dependent and comes from `slowing_400.json` (400 gameplays over 90 days), not the isolated-input half-time. The aging comparator's retest decay reaches its lower bound; `report_as_bound` flags that numerical result so it is not reported as a finite biological half-life. Comparisons omitted from a run have blank RMSE entries. Saved reference values never substitute silently for an unrun prediction check.

Paper tables contain editorial grouping, labels and rounding. The CSV/JSON files provide numerical source values rather than regenerating the prose/Word documents. Manuscript sources, current figure exports and references are tracked together; Word export is a separate publishing step.

Output filenames retain their existing numeric labels for compatibility. In the current paper, Supplementary Table 4 combines the benchmark prose (`supplement_table_4.csv`) and alternative-model table (`supplement_table_5.csv`); Supplementary Table 5 uses the six-schedule figure summaries. Coefficient correlations (`supplement_table_6.csv`) and baseline age-reference estimates (`age_reference.json`) remain available as analysis outputs but are not presented as a manuscript table. The detailed later-follow-up counts remain an analysis output but are not a separate block in the supplement.
