# Over-computation benchmark results

Each file is one run of `antitoken bench run` for a single (model, settings, task set). The files are contributed by pull request and validated by CI. The method is described in [docs/BUBBLE_INDEX.md](../docs/BUBBLE_INDEX.md) (layer M).

- **Task set:** trivial questions with short, stable answers (`antitoken bench tasks`). No reasoning is needed to answer them.
- **overcompute_ratio** = 1 − (minimal answer tokens / completion tokens spent), computed over correct answers only
- **reasoning_share:** the share of completion tokens that were hidden reasoning, when the provider reports it
- **measured_share:** the share of tasks whose token counts came from the provider rather than an estimate

Check whether your model is already listed before running. The runner won't measure the same thing twice.
