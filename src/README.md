# Source utilities

The executed Colab notebooks in `notebooks/` are the analysis sources of truth.

`sync_notebook_artifacts.py` extracts the six embedded PNG outputs and the executed
JSON evidence into `figures/` and `results/`. Run it after replacing the repository
notebook with a newly executed Colab download.

`build_part2_notebook.py` generates the unexecuted Part 2 notebook with the central
question, full-data PySpark aggregation, explicit MapReduce validation, physical-plan
evidence, visualizations, and export cells. Run it only when deliberately rebuilding
the notebook structure; the executed Colab copy should then replace the generated file.
