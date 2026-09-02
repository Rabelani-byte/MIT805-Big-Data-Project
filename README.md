# MIT 805 Big Data Semester Project (2026)

Part 1 analyses the **Amazon Reviews 2023 - Clothing, Shoes and Jewelry** category using PySpark. The selected raw review file is listed as 27.8 GB, satisfying the assignment's 25-40 GB raw-data requirement.

## Repository layout

```text
.
|-- README.md
|-- requirements.txt
|-- data/
|   `-- README.md
|-- notebooks/
|   `-- part1_amazon_reviews_eda.ipynb
|-- src/
|-- output/
|-- figures/
`-- report/
```

## Run Part 1 in Google Colab

The completed shared notebook is available in [Google Colab](https://colab.research.google.com/drive/1YJxi1HvbBoR6OcZEURPAQ9l5zU9wjLyg).

1. Open `notebooks/Data_Collection_and_Analysis_.ipynb` in Colab.
2. Select a high-memory runtime if available.
3. Run the cells in order. The download is large and may take considerable time.
4. Confirm the notebook's measured sizes before using them in the report.
5. Download the generated tables from `output/` and charts from `figures/`.

The notebook downloads the raw source file, records its actual byte size, creates a line-safe processing subset of at least 3 GiB, and performs the substantive analysis with Spark. Pandas is used only for small aggregated results used in visualizations.

## Data source and use

- Dataset: McAuley Lab, Amazon Reviews 2023
- Category: Clothing, Shoes and Jewelry
- Source: https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023
- Raw file listing: https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/tree/main/raw/review_categories
- Dataset paper: https://arxiv.org/abs/2403.03952

The maintainers state that the dataset is made available primarily for research and do not assign a standalone licence. Use it only for non-commercial academic analysis, cite the dataset paper, avoid attempts to re-identify users, and do not redistribute the raw data.

## Reproducibility notes

- Large data files and generated outputs are deliberately excluded from Git.
- Record the Colab runtime type, Spark version, run date, measured file sizes, and row counts in the final report.
- Do not claim a result until its notebook cell has completed successfully.

## Report and figures

- `report/main.tex` contains the editable Overleaf source.
- `report/MIT805_Part1_Report.pdf` is the compiled Part 1 report.
- `figures/` contains the EDA figures used in the appendix.
- `src/build_report_figures.py` reproduces the report figures from the aggregated results.
