"""Build the MIT805 Part 2 Colab notebook.

The generated notebook is intentionally unexecuted. Run it in Colab against the
same 3 GiB JSONL processing dataset used for Part 1, then download the executed
copy and version the generated evidence and figures.
"""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = REPO_ROOT / "notebooks" / "Part_2_PySpark_MapReduce_Analysis.ipynb"


def markdown(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(keepends=True)}


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


cells = [
    markdown("""# MIT 805 Part 2 — PySpark MapReduce and Visualisation

**Dataset:** Amazon Reviews 2023 — Clothing, Shoes and Jewelry  
**Processing dataset:** the same line-safe 3 GiB JSONL subset used in Part 1  
**Central analytical question:** *Which sufficiently reviewed parent products show the greatest customer-experience risk when review volume, low-rating prevalence, helpful negative feedback, and recent rating change are considered together?*

The analysis uses PySpark for all substantive processing. Pandas receives only small aggregated result tables for final plotting."""),
    markdown("""## Objectives and rationale

The analysis has five linked objectives:

1. transform raw review records into analysis features such as negative-review indicators, verified-purchase indicators, time periods, and bounded helpfulness measures;
2. aggregate millions of reviews by parent product using distributed key-based operations;
3. compare historical (up to 2020) and recent (2021–2023) mean ratings;
4. rank sufficiently reviewed products using an explicit, interpretable risk score; and
5. translate the results into quality-monitoring actions while documenting sampling, causal, identity, and review-manipulation limitations.

A minimum of 50 reviews is required for ranking. Part 1 found that the 99th percentile was 48 reviews per product, so this threshold focuses the risk analysis on unusually well-observed products and reduces instability from products with only one or two reviews. It is a prioritisation rule, not a claim of statistical significance."""),
    code("""!pip -q install pyspark==4.0.0 huggingface-hub matplotlib seaborn"""),
    code("""from pathlib import Path
from datetime import datetime, timezone
import json, math, os, platform

from huggingface_hub import HfApi, hf_hub_download
from pyspark.sql import SparkSession, functions as F, types as T, Window
import matplotlib.pyplot as plt
import seaborn as sns

spark = (SparkSession.builder
         .appName("MIT805-Part2-Amazon-Review-Risk")
         .config("spark.sql.shuffle.partitions", "64")
         .config("spark.driver.memory", "10g")
         .getOrCreate())
spark.sparkContext.setLogLevel("WARN")

ROOT = Path("/content/mit805_part2")
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_DIR = ROOT / "output"
FIGURE_DIR = ROOT / "figures"
for folder in (RAW_DIR, PROCESSED_DIR, OUTPUT_DIR, FIGURE_DIR):
    folder.mkdir(parents=True, exist_ok=True)

print("Run time (UTC):", datetime.now(timezone.utc).isoformat())
print("Python:", platform.python_version())
print("Spark:", spark.version)
print("Spark UI:", spark.sparkContext.uiWebUrl)
print("Storage:", ROOT)"""),
    markdown("""## Recreate or reuse the processing dataset

The notebook uses the same public source and the same line-safe minimum of 3 GiB as Part 1. If the processing JSONL file is already stored in Google Drive, set `PROCESSING_PATH` to that file and skip the download/subset cells. Otherwise, the cells below verify the hosted size, download the complete working file, and copy complete JSONL records until the processing threshold is met."""),
    code("""REPO_ID = "McAuley-Lab/Amazon-Reviews-2023"
HF_FILENAME = "raw/review_categories/Clothing_Shoes_and_Jewelry.jsonl"
MIN_PROCESSING_BYTES = 3 * 1024**3

api = HfApi()
info = api.dataset_info(REPO_ID, files_metadata=True)
entry = next(s for s in info.siblings if s.rfilename == HF_FILENAME)
hosted_bytes = entry.size
assert 25 <= hosted_bytes / 1e9 <= 40
print(f"Hosted raw file: {hosted_bytes:,} bytes ({hosted_bytes/1e9:.3f} GB)")"""),
    code("""downloaded = hf_hub_download(
    repo_id=REPO_ID,
    repo_type="dataset",
    filename=HF_FILENAME,
    local_dir=RAW_DIR,
)
RAW_PATH = Path(downloaded)
raw_bytes = RAW_PATH.stat().st_size
assert raw_bytes >= 12e9
print(f"Working file: {raw_bytes:,} bytes ({raw_bytes/1e9:.3f} GB)")"""),
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
assert processing_bytes >= MIN_PROCESSING_BYTES
print(f"Processing file: {processing_bytes:,} bytes ({processing_bytes/1e9:.3f} GB; {processing_bytes/1024**3:.3f} GiB)")"""),
    markdown("""## Mapping and transformation

Spark lazily maps each input review to typed and derived fields. The transformation stage casts ratings, votes, and timestamps; removes structurally invalid records; and creates Boolean/numeric indicators used by the aggregations. `log1p_helpful` limits the leverage of the extremely right-skewed helpful-vote count without discarding genuine popular reviews.

The dataset is repartitioned and cached because several downstream actions reuse it. No full-data conversion to Pandas occurs."""),
    code("""reviews_raw = spark.read.json(str(PROCESSING_PATH))

reviews = (reviews_raw
    .select("parent_asin", "user_id", "rating", "helpful_vote", "verified_purchase", "timestamp", "text")
    .withColumn("rating", F.col("rating").cast("double"))
    .withColumn("helpful_vote", F.col("helpful_vote").cast("long"))
    .withColumn("timestamp", F.col("timestamp").cast("long"))
    .withColumn("review_time", F.to_timestamp(F.from_unixtime(F.col("timestamp") / 1000)))
    .withColumn("review_year", F.year("review_time"))
    .filter(F.col("parent_asin").isNotNull() & F.col("rating").between(1, 5))
    .withColumn("is_negative", (F.col("rating") <= 2).cast("long"))
    .withColumn("is_positive", (F.col("rating") >= 4).cast("long"))
    .withColumn("verified_flag", F.col("verified_purchase").cast("long"))
    .withColumn("negative_helpful", F.when(F.col("rating") <= 2, F.col("helpful_vote")).otherwise(F.lit(0)))
    .withColumn("log1p_helpful", F.log1p(F.greatest(F.col("helpful_vote"), F.lit(0))))
    .withColumn("period", F.when(F.col("review_year") <= 2020, F.lit("historical")).otherwise(F.lit("recent")))
    .repartition(64, "parent_asin")
    .cache())

processing_rows = reviews.count()
print(f"Valid processing rows: {processing_rows:,}")
reviews.printSchema()"""),
    markdown("""## Explicit Map → Shuffle → Reduce demonstration

The following RDD operation makes the MapReduce logic visible:

- **Map:** emit `(parent_asin, metrics)` for every valid review;
- **Shuffle/group:** `reduceByKey` hashes the key and moves partial records so values for the same parent product meet;
- **Reduce:** associative element-wise addition produces product totals.

The explicit RDD result is used as a validation check against the optimised DataFrame aggregation. The substantive full-data analysis below uses Spark SQL/DataFrames, whose physical plan applies the same map–shuffle–reduce pattern with JVM execution and partial hash aggregation."""),
    code("""mapped_pairs = reviews.select(
    "parent_asin", "rating", "is_negative", "negative_helpful", "verified_flag"
).rdd.map(lambda r: (
    r.parent_asin,
    (1, float(r.rating), int(r.is_negative), int(r.negative_helpful or 0), int(r.verified_flag or 0))
))

reduced_pairs = mapped_pairs.reduceByKey(
    lambda a, b: tuple(x + y for x, y in zip(a, b)),
    numPartitions=64,
)

mapreduce_schema = T.StructType([
    T.StructField("parent_asin", T.StringType(), False),
    T.StructField("metrics", T.StructType([
        T.StructField("review_count", T.LongType(), False),
        T.StructField("rating_sum", T.DoubleType(), False),
        T.StructField("negative_count", T.LongType(), False),
        T.StructField("negative_helpful_votes", T.LongType(), False),
        T.StructField("verified_count", T.LongType(), False),
    ]), False),
])

mapreduce_products = spark.createDataFrame(
    reduced_pairs.map(lambda kv: (kv[0], tuple(kv[1]))),
    schema=mapreduce_schema,
).select("parent_asin", "metrics.*").cache()

print("Products produced by explicit reduceByKey:", f"{mapreduce_products.count():,}")
mapreduce_products.orderBy(F.desc("review_count")).show(10, truncate=False)"""),
    markdown("""## Full-data grouping, shuffle, reduction, and join

`groupBy(parent_asin)` requires a wide dependency: Spark must shuffle records across executors so all reviews for a product are co-located. Spark performs partial aggregation before the exchange where possible, then reduces the shuffled partial results. A second aggregation computes period-level means. The two compact product tables are joined by key to connect overall risk indicators with temporal change."""),
    code("""product_metrics = (reviews
    .groupBy("parent_asin")
    .agg(
        F.count("*").alias("review_count"),
        F.avg("rating").alias("mean_rating"),
        F.sum("is_negative").alias("negative_count"),
        F.avg("is_negative").alias("negative_share"),
        F.sum("is_positive").alias("positive_count"),
        F.sum("negative_helpful").alias("negative_helpful_votes"),
        F.avg("verified_flag").alias("verified_share"),
        F.avg("log1p_helpful").alias("mean_log1p_helpful"),
        F.min("review_year").alias("first_year"),
        F.max("review_year").alias("last_year"),
    ))

period_metrics = (reviews
    .groupBy("parent_asin")
    .pivot("period", ["historical", "recent"])
    .agg(F.avg("rating")))

eligible_products = (product_metrics
    .filter(F.col("review_count") >= 50)
    .join(period_metrics, "parent_asin", "left")
    .withColumn("rating_change", F.col("recent") - F.col("historical"))
    .withColumn(
        "risk_score",
        F.col("negative_share")
        * F.log1p(F.col("review_count"))
        * (F.lit(1.0) + F.log1p(F.col("negative_helpful_votes")))
        * (F.lit(1.0) + F.greatest(-F.coalesce(F.col("rating_change"), F.lit(0.0)), F.lit(0.0)))
    )
    .cache())

eligible_count = eligible_products.count()
print(f"Eligible products (>=50 reviews): {eligible_count:,}")
eligible_products.orderBy(F.desc("risk_score")).show(20, truncate=False)"""),
    markdown("""### Validation of the reduction

The independent RDD and DataFrame implementations must agree on product count, rating sum, negative count, negative helpful votes, and verified count. A zero-row mismatch result provides an auditable correctness check."""),
    code("""df_check = product_metrics.select(
    "parent_asin", "review_count",
    (F.col("mean_rating") * F.col("review_count")).alias("rating_sum"),
    "negative_count", "negative_helpful_votes",
    (F.col("verified_share") * F.col("review_count")).alias("verified_count"),
)

mismatches = (df_check.alias("d")
    .join(mapreduce_products.alias("r"), "parent_asin", "full")
    .filter(
        (F.coalesce(F.col("d.review_count"), F.lit(-1)) != F.coalesce(F.col("r.review_count"), F.lit(-1))) |
        (F.abs(F.coalesce(F.col("d.rating_sum"), F.lit(-1.0)) - F.coalesce(F.col("r.rating_sum"), F.lit(-1.0))) > 1e-8) |
        (F.coalesce(F.col("d.negative_count"), F.lit(-1)) != F.coalesce(F.col("r.negative_count"), F.lit(-1))) |
        (F.coalesce(F.col("d.negative_helpful_votes"), F.lit(-1)) != F.coalesce(F.col("r.negative_helpful_votes"), F.lit(-1))) |
        (F.abs(F.coalesce(F.col("d.verified_count"), F.lit(-1.0)) - F.coalesce(F.col("r.verified_count"), F.lit(-1.0))) > 1e-8)
    ))

mismatch_count = mismatches.count()
print("RDD/DataFrame aggregation mismatches:", mismatch_count)
assert mismatch_count == 0"""),
    markdown("""## Spark execution evidence and DAG interpretation

`explain("formatted")` is retained as execution evidence. In the physical plan:

- scans, filters, projections, and derived columns are narrow mapping transformations;
- `Exchange` nodes show shuffle boundaries created by grouping, pivoting, joining, or repartitioning;
- `HashAggregate` partial stages reduce data locally before the shuffle, and final stages reduce shuffled values;
- the join connects product-level aggregates rather than moving raw reviews into Pandas;
- actions such as `count`, `show`, and `write` cause Spark to materialise the lazy DAG as jobs, stages, and tasks.

Unlike traditional Hadoop MapReduce, which materialises a rigid Map → Shuffle → Reduce sequence between jobs, Spark builds a DAG of transformations, pipelines compatible narrow operations within stages, inserts stage boundaries at wide dependencies, and can retain cached intermediate data for reuse."""),
    code("""eligible_products.explain(mode="formatted")

executed_plan = eligible_products._jdf.queryExecution().executedPlan().toString()
(OUTPUT_DIR / "part2_executed_plan.txt").write_text(executed_plan, encoding="utf-8")
print(executed_plan[:12000])"""),
    code("""tracker = spark.sparkContext.statusTracker()
executor_info = spark.sparkContext._jsc.sc().getExecutorMemoryStatus().size()
execution_evidence = {
    "spark_version": spark.version,
    "spark_ui_url": spark.sparkContext.uiWebUrl,
    "default_parallelism": spark.sparkContext.defaultParallelism,
    "shuffle_partitions": spark.conf.get("spark.sql.shuffle.partitions"),
    "cached_review_partitions": reviews.rdd.getNumPartitions(),
    "executors_reported": int(executor_info),
    "active_job_ids_after_actions": list(tracker.getActiveJobIds()),
    "active_stage_ids_after_actions": list(tracker.getActiveStageIds()),
}
print(json.dumps(execution_evidence, indent=2))
(OUTPUT_DIR / "part2_execution_evidence.json").write_text(
    json.dumps(execution_evidence, indent=2), encoding="utf-8"
)"""),
    markdown("""## Results

The following compact outputs answer the analytical question. The top-risk table reports transparent components rather than only the composite score. A distribution summary shows how strongly risk is concentrated, while rating bands describe how many sufficiently reviewed products fall below operationally relevant thresholds."""),
    code("""top_risk = (eligible_products
    .orderBy(F.desc("risk_score"))
    .select(
        "parent_asin", "review_count", "mean_rating", "negative_share",
        "negative_helpful_votes", "historical", "recent", "rating_change",
        "verified_share", "risk_score"
    )
    .limit(25))

risk_summary = eligible_products.select(
    "review_count", "mean_rating", "negative_share", "negative_helpful_votes",
    "rating_change", "risk_score"
).summary("count", "mean", "stddev", "min", "25%", "50%", "75%", "max")

rating_bands = (eligible_products
    .withColumn(
        "rating_band",
        F.when(F.col("mean_rating") < 3.0, "Below 3.0")
         .when(F.col("mean_rating") < 3.5, "3.0–3.49")
         .when(F.col("mean_rating") < 4.0, "3.5–3.99")
         .otherwise("4.0 or higher"))
    .groupBy("rating_band")
    .agg(F.count("*").alias("products"), F.sum("review_count").alias("reviews"))
    .orderBy("rating_band"))

top_risk.show(25, truncate=False)
risk_summary.show(truncate=False)
rating_bands.show(truncate=False)"""),
    markdown("""## Visualisation

Only the bounded aggregate tables below are converted to Pandas. The raw processing DataFrame and full product-level tables remain distributed in Spark."""),
    code("""sns.set_theme(style="whitegrid")

top15_pd = top_risk.limit(15).toPandas().sort_values("risk_score")
fig, ax = plt.subplots(figsize=(9, 6))
bars = ax.barh(top15_pd["parent_asin"], top15_pd["risk_score"], color="#b3473d")
ax.set(title="Highest-priority product risk signals", xlabel="Composite risk score", ylabel="Parent ASIN")
fig.tight_layout()
fig.savefig(FIGURE_DIR / "part2_top_risk_products.png", dpi=200, bbox_inches="tight")
plt.show()"""),
    code("""scatter_pd = (eligible_products
    .select("parent_asin", "review_count", "mean_rating", "negative_share", "risk_score")
    .orderBy(F.desc("review_count"))
    .limit(5000)
    .toPandas())

fig, ax = plt.subplots(figsize=(8, 5))
points = ax.scatter(
    scatter_pd["review_count"], scatter_pd["mean_rating"],
    c=scatter_pd["negative_share"], cmap="YlOrRd", alpha=0.6, s=18
)
ax.set_xscale("log")
ax.set(title="Rating, review volume, and negative-review share", xlabel="Review count (log scale)", ylabel="Mean rating")
fig.colorbar(points, ax=ax, label="Negative-review share")
fig.tight_layout()
fig.savefig(FIGURE_DIR / "part2_volume_rating_risk.png", dpi=200, bbox_inches="tight")
plt.show()"""),
    code("""trend_pd = (eligible_products
    .filter(F.col("historical").isNotNull() & F.col("recent").isNotNull())
    .orderBy(F.desc("review_count"))
    .limit(5000)
    .select("rating_change")
    .toPandas())

fig, ax = plt.subplots(figsize=(8, 4.5))
sns.histplot(data=trend_pd, x="rating_change", bins=40, color="#3569b7", ax=ax)
ax.axvline(0, color="black", linewidth=1, linestyle="--")
ax.set(title="Recent minus historical mean rating", xlabel="Rating change (stars)", ylabel="Products")
fig.tight_layout()
fig.savefig(FIGURE_DIR / "part2_rating_change_distribution.png", dpi=200, bbox_inches="tight")
plt.show()"""),
    markdown("""## Technical and business interpretation

After execution, interpret the measured output rather than assuming every high score represents a defective product:

- **Technical meaning:** the ranking is driven by the conjunction of negative-review share, evidence volume, helpful negative feedback, and recent deterioration. Each component remains visible for auditability.
- **Retail/manufacturer value:** quality teams can review the highest-ranked products first, compare recent and historical feedback, and allocate investigation capacity to issues affecting many customers.
- **Consumer/societal value:** earlier identification of persistent product concerns can improve transparency and reduce repeated negative experiences.
- **Not causal:** the score prioritises signals; it does not prove product defects or that any product caused a reported outcome.
- **Selection and coverage:** reviews are voluntary, the data contain pseudonymous users, and the 3 GiB sequential prefix may differ from the full category file.
- **Identity limitation:** parent ASINs may reflect product variants or listing merges; repeated or coordinated reviews may distort aggregates.
- **Temporal limitation:** 2023 is partial, and products need observations in both periods for a meaningful rating-change comparison.
- **Operational safeguard:** human review of review text, product metadata, return rates, and safety/quality records is required before action."""),
    markdown("""## Export reproducibility evidence

The small JSON/CSV outputs and figures can be committed to GitHub. The raw and processing JSONL files must remain excluded because of size and redistribution considerations."""),
    code("""top_risk_pd = top_risk.toPandas()
top_risk_pd.to_csv(OUTPUT_DIR / "part2_top_risk_products.csv", index=False)
rating_bands.toPandas().to_csv(OUTPUT_DIR / "part2_rating_bands.csv", index=False)

part2_evidence = {
    "central_question": "Which sufficiently reviewed parent products show the greatest customer-experience risk when review volume, low-rating prevalence, helpful negative feedback, and recent rating change are considered together?",
    "processing_file_bytes": processing_bytes,
    "processing_rows": processing_rows,
    "minimum_reviews_for_ranking": 50,
    "eligible_products": eligible_count,
    "mapreduce_validation_mismatches": mismatch_count,
    "risk_score_definition": "negative_share * log1p(review_count) * (1 + log1p(negative_helpful_votes)) * (1 + max(-rating_change, 0))",
    "period_definition": {"historical": "review_year <= 2020", "recent": "2021 <= review_year <= 2023 (partial 2023)"},
    "execution": execution_evidence,
    "limitations": [
        "Observational review data cannot establish causation.",
        "Voluntary reviews are not representative of all purchasers.",
        "The 3 GiB sequential prefix may not represent the complete category file.",
        "Parent-product identifiers can be affected by variants or listing merges.",
        "Helpful votes and ratings may be affected by platform incentives or manipulation.",
        "The 2023 period is incomplete in the processing data.",
    ],
}
(OUTPUT_DIR / "part2_evidence.json").write_text(
    json.dumps(part2_evidence, indent=2, default=str), encoding="utf-8"
)
print(json.dumps(part2_evidence, indent=2, default=str))"""),
    markdown("""## Report and video checklist

The 5–7 page report should include the central question and rationale, mapping transformations, shuffle explanation, reduction formulas, join and risk-score definition, formatted physical-plan evidence, technical results, the three figures, stakeholder value, and limitations. Up to two additional appendix pages may contain the longer plan or result tables.

For the ≤10-minute demonstration, show: dataset scale; transformed schema; map/reduce code; `Exchange` and `HashAggregate` in the plan; the validation result; top-risk results; all three figures; business interpretation; limitations; and the GitHub reproduction instructions."""),
]

notebook = {
    "cells": cells,
    "metadata": {
        "colab": {"provenance": []},
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.x"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

OUTPUT.write_text(json.dumps(notebook, indent=1), encoding="utf-8")
print(f"Wrote {OUTPUT} ({len(cells)} cells)")
