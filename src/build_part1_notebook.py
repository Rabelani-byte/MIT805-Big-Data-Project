"""Build the Part 1 Colab notebook without requiring Jupyter locally."""

import json
from pathlib import Path


def md(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(True)}


def code(source):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(True),
    }


cells = [
    md("""# MIT 805 Part 1 - Amazon Reviews 2023 EDA with PySpark

**Dataset:** Clothing, Shoes and Jewelry reviews from McAuley Lab's Amazon Reviews 2023 dataset.  
**Purpose:** establish provenance and scale, assess data quality, perform exploratory analysis, and generate dataset-specific evidence for the 7 Vs of Big Data.

> Run every cell in order. Do not copy placeholder or unexecuted values into the report. The full download is large, so use a high-memory Colab runtime and allow sufficient time.
"""),
    md("""## 1. Reproducible environment

The substantive analysis uses Spark. Pandas is used only after aggregation, when results are small enough for plotting.
"""),
    code("""!pip -q install pyspark==4.0.0 huggingface-hub matplotlib seaborn
"""),
    code("""from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, platform

from huggingface_hub import HfApi, hf_hub_download
from pyspark.sql import SparkSession, functions as F, types as T
import matplotlib.pyplot as plt
import seaborn as sns

spark = (SparkSession.builder
         .appName("MIT805-Part1-AmazonReviews")
         .config("spark.sql.shuffle.partitions", "64")
         .config("spark.driver.memory", "10g")
         .getOrCreate())
spark.sparkContext.setLogLevel("WARN")

ROOT = Path("/content/mit805_part1")
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_DIR = ROOT / "output"
FIGURE_DIR = ROOT / "figures"
for folder in (RAW_DIR, PROCESSED_DIR, OUTPUT_DIR, FIGURE_DIR):
    folder.mkdir(parents=True, exist_ok=True)

print("Run time (UTC):", datetime.now(timezone.utc).isoformat())
print("Python:", platform.python_version())
print("Spark:", spark.version)
print("Storage:", ROOT)
"""),
    md("""## 2. Provenance, terms, and scale

- **Publisher:** McAuley Lab, University of California San Diego.
- **Repository:** https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023
- **Paper:** Hou et al. (2024), *Bridging Language and Items for Retrieval and Recommendation*, https://arxiv.org/abs/2403.03952
- **Period represented:** May 1996 to September 2023 (dataset-level description).
- **Terms:** the maintainers state that the dataset is made available primarily for research, but they do not assign a standalone licence. Use is therefore limited here to non-commercial academic analysis, with attribution and ethical safeguards. See https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/discussions/1
- **Privacy/ethics:** reviewer identifiers are pseudonymous but still potentially linkable. Do not attempt re-identification, publish review-level extracts, or redistribute the raw file.

The selected raw review file is listed as **27.8 GB**, which falls inside the assignment's 25-40 GB raw-data requirement. The notebook verifies the hosted byte count and the downloaded byte count rather than relying only on the display label.
"""),
    code("""REPO_ID = "McAuley-Lab/Amazon-Reviews-2023"
HF_FILENAME = "raw/review_categories/Clothing_Shoes_and_Jewelry.jsonl"
DISPLAYED_RAW_SIZE_GB = 27.8
MIN_PROCESSING_BYTES = 3 * 1024**3  # 3 GiB, deliberately conservative

api = HfApi()
info = api.dataset_info(REPO_ID, files_metadata=True)
entry = next(s for s in info.siblings if s.rfilename == HF_FILENAME)
hosted_bytes = entry.size

scale = {
    "raw_dataset_definition": "Amazon Reviews 2023 - Clothing, Shoes and Jewelry raw reviews",
    "hosted_file_bytes": hosted_bytes,
    "hosted_file_GB_decimal": round(hosted_bytes / 1e9, 3),
    "displayed_source_size_GB": DISPLAYED_RAW_SIZE_GB,
    "retrieved_utc": datetime.now(timezone.utc).isoformat(),
}
print(json.dumps(scale, indent=2))
assert 25 <= hosted_bytes / 1e9 <= 40, "Selected raw file is outside the required 25-40 GB range"
"""),
    md("""## 3. Download and prepare the working and processing datasets

The full selected raw file is the working dataset. A line-safe prefix of at least 3 GiB is created for processing so that the final record is not truncated. If the file is already in Google Drive, change `RAW_PATH` to that location and skip the download.
"""),
    code("""downloaded = hf_hub_download(
    repo_id=REPO_ID,
    repo_type="dataset",
    filename=HF_FILENAME,
    local_dir=RAW_DIR,
)
RAW_PATH = Path(downloaded)
raw_bytes = RAW_PATH.stat().st_size
print(f"Working file: {RAW_PATH}")
print(f"Working size: {raw_bytes:,} bytes ({raw_bytes/1e9:.3f} GB; {raw_bytes/1024**3:.3f} GiB)")
assert raw_bytes >= 12e9, "Working dataset must be at least 12 GB"
"""),
    code("""PROCESSING_PATH = PROCESSED_DIR / "Clothing_Shoes_and_Jewelry_3GiB.jsonl"

if not PROCESSING_PATH.exists() or PROCESSING_PATH.stat().st_size < MIN_PROCESSING_BYTES:
    copied = 0
    with RAW_PATH.open("rb") as source, PROCESSING_PATH.open("wb") as target:
        while copied < MIN_PROCESSING_BYTES:
            line = source.readline()
            if not line:
                break
            target.write(line)
            copied += len(line)

processing_bytes = PROCESSING_PATH.stat().st_size
print(f"Processing size: {processing_bytes:,} bytes ({processing_bytes/1e9:.3f} GB; {processing_bytes/1024**3:.3f} GiB)")
assert processing_bytes >= MIN_PROCESSING_BYTES

scale.update({
    "working_file_bytes": raw_bytes,
    "working_file_GB_decimal": round(raw_bytes / 1e9, 3),
    "processing_file_bytes": processing_bytes,
    "processing_file_GB_decimal": round(processing_bytes / 1e9, 3),
})
(OUTPUT_DIR / "dataset_scale.json").write_text(json.dumps(scale, indent=2), encoding="utf-8")
"""),
    md("""## 4. Load with Spark and inspect structure

Amazon review records contain ratings, titles, review text, product and pseudonymous user identifiers, timestamps, helpful-vote counts, verification flags, and image references. Explicit casting below makes invalid values visible instead of silently accepting them.
"""),
    code("""reviews_raw = spark.read.json(str(PROCESSING_PATH))
reviews_raw.printSchema()

reviews = (reviews_raw
    .withColumn("rating", F.col("rating").cast("double"))
    .withColumn("helpful_vote", F.col("helpful_vote").cast("long"))
    .withColumn("timestamp", F.col("timestamp").cast("long"))
    .withColumn("review_time", F.to_timestamp(F.from_unixtime(F.col("timestamp") / 1000)))
    .withColumn("review_year", F.year("review_time"))
    .withColumn("text_length", F.length(F.coalesce(F.col("text"), F.lit(""))))
    .withColumn("title_length", F.length(F.coalesce(F.col("title"), F.lit(""))))
    .repartition(64)
    .cache())

row_count = reviews.count()
column_count = len(reviews.columns)
print(f"Rows: {row_count:,}; columns: {column_count}")
reviews.show(5, truncate=80)
"""),
    md("""## 5. Data quality assessment

We test completeness, duplicates, valid rating ranges, timestamps, helpful-vote values, and unusually short/long text. A repeated `(user_id, parent_asin, timestamp, text)` tuple is treated as a potential duplicate, not automatically deleted: repeated reviews can also arise from merged or variant product listings.
"""),
    code("""null_exprs = [
    F.sum(F.col(c).isNull().cast("long")).alias(c)
    for c in reviews.columns
]
null_counts = reviews.agg(*null_exprs)
null_counts.show(truncate=False)

quality = reviews.agg(
    F.count("*").alias("rows"),
    F.sum((~F.col("rating").between(1, 5) | F.col("rating").isNull()).cast("long")).alias("invalid_or_null_rating"),
    F.sum((F.col("helpful_vote") < 0).cast("long")).alias("negative_helpful_votes"),
    F.sum((F.col("text_length") == 0).cast("long")).alias("empty_review_text"),
    F.sum((F.col("text_length") > 10000).cast("long")).alias("text_over_10000_chars"),
    F.min("review_time").alias("earliest_review"),
    F.max("review_time").alias("latest_review"),
).first().asDict()

duplicate_rows = (reviews
    .groupBy("user_id", "parent_asin", "timestamp", "text")
    .count().filter(F.col("count") > 1)
    .agg(F.sum(F.col("count") - 1).alias("duplicate_rows"))
    .first()[0] or 0)
quality["potential_duplicate_rows"] = duplicate_rows
quality["potential_duplicate_pct"] = round(100 * duplicate_rows / row_count, 4)
print(json.dumps({k: str(v) for k, v in quality.items()}, indent=2))
(OUTPUT_DIR / "quality_summary.json").write_text(json.dumps({k: str(v) for k, v in quality.items()}, indent=2), encoding="utf-8")
"""),
    md("""## 6. Exploratory data analysis

The following aggregations identify rating imbalance, temporal coverage, verified-purchase behaviour, helpfulness, review-length patterns, and heavily reviewed products. Only these compact results are converted to Pandas.
"""),
    code("""numeric_summary = reviews.select("rating", "helpful_vote", "text_length").summary()
numeric_summary.show(truncate=False)

rating_counts = reviews.groupBy("rating").count().orderBy("rating")
yearly = (reviews.filter(F.col("review_year").isNotNull())
          .groupBy("review_year")
          .agg(F.count("*").alias("reviews"), F.avg("rating").alias("mean_rating"))
          .orderBy("review_year"))
verified = (reviews.groupBy("verified_purchase")
            .agg(F.count("*").alias("reviews"),
                 F.avg("rating").alias("mean_rating"),
                 F.avg("helpful_vote").alias("mean_helpful_votes")))
top_products = (reviews.groupBy("parent_asin")
                .agg(F.count("*").alias("reviews"), F.avg("rating").alias("mean_rating"))
                .orderBy(F.desc("reviews")).limit(20))

rating_profile = (reviews.groupBy("rating")
    .agg(F.count("*").alias("reviews"),
         F.avg("text_length").alias("mean_text_length"),
         F.expr("percentile_approx(text_length, 0.5)").alias("median_text_length"),
         F.avg("helpful_vote").alias("mean_helpful_votes"),
         F.avg(F.col("verified_purchase").cast("double")).alias("verified_share"))
    .orderBy("rating"))

verified_ratings = (reviews.groupBy("verified_purchase", "rating")
    .count().orderBy("verified_purchase", "rating"))

product_concentration = (reviews.groupBy("parent_asin").count()
    .agg(F.count("*").alias("distinct_products"),
         F.max("count").alias("largest_product_reviews"),
         F.expr("percentile_approx(count, 0.5)").alias("median_reviews_per_product"),
         F.expr("percentile_approx(count, 0.99)").alias("p99_reviews_per_product")))

rating_counts.show()
yearly.show(50, truncate=False)
verified.show(truncate=False)
top_products.show(20, truncate=False)
rating_profile.show(truncate=False)
verified_ratings.show(truncate=False)
product_concentration.show(truncate=False)
"""),
    code("""sns.set_theme(style="whitegrid")

rating_pd = rating_counts.toPandas()
fig, ax = plt.subplots(figsize=(7, 4))
sns.barplot(data=rating_pd, x="rating", y="count", color="#3569b7", ax=ax)
ax.set(title="Review rating distribution", xlabel="Stars", ylabel="Number of reviews")
fig.tight_layout()
fig.savefig(FIGURE_DIR / "rating_distribution.png", dpi=200)
plt.show()

yearly_pd = yearly.toPandas()
fig, ax1 = plt.subplots(figsize=(9, 4.5))
ax1.plot(yearly_pd["review_year"], yearly_pd["reviews"], color="#3569b7", marker="o", ms=3)
ax1.set(title="Review volume over time", xlabel="Year", ylabel="Number of reviews")
fig.tight_layout()
fig.savefig(FIGURE_DIR / "review_volume_by_year.png", dpi=200)
plt.show()

fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(yearly_pd["review_year"], yearly_pd["mean_rating"], color="#c96b2c", marker="o", ms=3)
ax.set(title="Average rating over time", xlabel="Year", ylabel="Mean rating", ylim=(3.5, 5.05))
fig.tight_layout()
fig.savefig(FIGURE_DIR / "mean_rating_by_year.png", dpi=200)
plt.show()

verified_pd = verified.toPandas().sort_values("verified_purchase")
verified_pd["purchase_status"] = verified_pd["verified_purchase"].map({True: "Verified", False: "Unverified"})
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
sns.barplot(data=verified_pd, x="purchase_status", y="mean_rating", color="#3569b7", ax=axes[0])
axes[0].set(title="Mean rating by purchase status", xlabel="", ylabel="Mean rating", ylim=(4.15, 4.30))
sns.barplot(data=verified_pd, x="purchase_status", y="mean_helpful_votes", color="#c96b2c", ax=axes[1])
axes[1].set(title="Mean helpful votes", xlabel="", ylabel="Votes per review")
fig.tight_layout()
fig.savefig(FIGURE_DIR / "verified_purchase_comparison.png", dpi=200)
plt.show()

profile_pd = rating_profile.toPandas()
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
sns.lineplot(data=profile_pd, x="rating", y="mean_text_length", marker="o", ax=axes[0])
axes[0].set(title="Review length by rating", xlabel="Stars", ylabel="Mean characters")
sns.lineplot(data=profile_pd, x="rating", y="mean_helpful_votes", marker="o", color="#c96b2c", ax=axes[1])
axes[1].set(title="Helpfulness by rating", xlabel="Stars", ylabel="Mean helpful votes")
fig.tight_layout()
fig.savefig(FIGURE_DIR / "rating_length_helpfulness.png", dpi=200)
plt.show()

top_pd = top_products.toPandas().head(10).sort_values("reviews")
fig, ax = plt.subplots(figsize=(8, 5))
ax.barh(top_pd["parent_asin"], top_pd["reviews"], color="#3569b7")
ax.set(title="Ten most-reviewed parent products", xlabel="Reviews", ylabel="Parent ASIN")
fig.tight_layout()
fig.savefig(FIGURE_DIR / "top_products.png", dpi=200)
plt.show()
"""),
    md("""## 7. Dataset-specific evidence for the 7 Vs

The table below creates an evidence framework. Replace no values manually: use the executed measurements and interpret them in the report.

| V | Dataset-specific evidence | Why it matters |
|---|---|---|
| Volume | Hosted raw-file bytes, working bytes, processing bytes, and Spark row count measured above | Requires distributed storage/processing and sampling decisions |
| Velocity | Reviews span many years and arrive as user-generated events; yearly counts quantify changes | Temporal drift means older patterns may not reflect current behaviour |
| Variety | Numeric ratings/votes, text, Boolean verification, arrays/images, IDs, and timestamps | Mixed structures require schema management and different analyses |
| Veracity | Nulls, potential duplicates, invalid values, extremes, and pseudonymous self-reports measured above | Quality problems can bias ratings, sentiment, and product comparisons |
| Value | Rating, demand, verification, and helpfulness patterns can support merchandising and customer-experience decisions | Converts processing into stakeholder-relevant evidence |
| Variability | Review volume, average rating, text length, and helpfulness differ over time and products | Aggregates can conceal seasonal or product-level heterogeneity |
| Visualization | Rating and temporal charts compress millions of records into interpretable patterns | Makes large-scale findings accessible while retaining accurate scales |
"""),
    code("""evidence = {
    "volume": {**scale, "processing_rows": row_count, "columns": column_count},
    "velocity": {
        "earliest_review": str(quality["earliest_review"]),
        "latest_review": str(quality["latest_review"]),
        "years_observed": int(yearly.count()),
    },
    "variety": {"columns": reviews.columns, "schema": reviews.schema.simpleString()},
    "veracity": quality,
    "limitations": [
        "Reviews are voluntary and are not representative of all purchasers or users.",
        "Pseudonymous identifiers and product-page merging complicate duplicate detection.",
        "Ratings and helpful votes can be influenced by platform design, selection effects, or manipulation.",
        "A 3 GiB line-safe prefix may differ temporally or compositionally from the full category file.",
    ],
}
(OUTPUT_DIR / "part1_evidence.json").write_text(json.dumps(evidence, default=str, indent=2), encoding="utf-8")
print(json.dumps(evidence, default=str, indent=2)[:12000])
"""),
    md("""## 8. Part 1 report checklist

- Report exact raw, working, and processing sizes from `dataset_scale.json`.
- Report records, variables, format, source, retrieval date, and temporal coverage.
- Interpret missingness, duplicates, invalid values, outliers, bias, representativeness, and subset limitations.
- Include at least two meaningful EDA results with interpretations, not graphs alone.
- Apply all seven Vs using the measured evidence.
- State business/societal value conservatively and include at least two limitations.
- Cite the dataset paper, repository, and terms discussion.
- Keep the main narrative to two pages; move supporting tables and figures to the appendix.
- Add the GitHub repository URL to the report and do not commit raw data.
"""),
]

notebook = {
    "cells": cells,
    "metadata": {
        "colab": {"name": "MIT805_Part1_Amazon_Reviews_EDA.ipynb", "provenance": []},
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.x"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

target = Path(__file__).resolve().parents[1] / "notebooks" / "part1_amazon_reviews_eda.ipynb"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(notebook, indent=1, ensure_ascii=False), encoding="utf-8")
print(target)
