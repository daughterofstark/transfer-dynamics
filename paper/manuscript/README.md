# Manuscript source

`manuscript.md` and `supplement.md` are the paper sources. Figures 1–4 and Supplementary Figure 1 are in `figures/`, with editable scripts in `figures/src/`. The analysis CLI regenerates tables and figures in its output directory. It does not modify the manuscript or build Word documents.

The target journal is PLOS Digital Health. The model uses observed daily game counts, calendar-day forgetting, separate training and retest decay, an age-dependent retest input and an age-referenced baseline correction. Point estimates, intervals and plotted predictions are supplied by `paper/reference` and the reproducible analysis workflow.
