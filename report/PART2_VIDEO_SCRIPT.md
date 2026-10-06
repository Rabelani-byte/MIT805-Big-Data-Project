# MIT 805 Part 2 video script (target: 8:30-9:30)

## 0:00-0:35 - Introduction and question

**Show:** Report title, then the first notebook heading.

**Say:** “We are Group 6. This Part 2 analysis uses the Amazon Reviews 2023 Clothing, Shoes and Jewelry category. Our central question is: which sufficiently reviewed parent products show the greatest customer-experience risk when review volume, low-rating prevalence, helpful negative feedback, and recent rating change are considered together? The purpose is prioritisation for investigation, not automatic proof that a product is defective.”

## 0:35-1:20 - Dataset and scale

**Show:** The hosted-size, working-file and processing-file output cells.

**Say:** “The original and downloaded working file contain 27,810,080,533 bytes, or 27.810 decimal gigabytes. We created a line-safe 3.000 GiB processing file by copying complete JSONL records, so the final record was not truncated. PySpark processed 7,231,543 valid review records. This representative subset is manageable in Colab but is a sequential prefix, which we treat as a limitation.”

## 1:20-2:20 - Mapping and transformation

**Show:** Transformation cell and schema output.

**Say:** “Spark casts ratings, helpful votes and timestamps to appropriate types, validates product identifiers and the 1-to-5 rating range, and derives review year. Each record is mapped to negative and positive indicators, a verified-purchase flag, negative helpful votes, log-transformed helpfulness, and a historical or recent period. We repartition by parent ASIN into 64 partitions and cache the transformed DataFrame because several later actions reuse it. The full data stays in Spark; Pandas is used only for bounded plotting tables.”

## 2:20-3:15 - Explicit MapReduce

**Show:** RDD `map` and `reduceByKey` cell, then its product-count output.

**Say:** “The explicit RDD pipeline demonstrates MapReduce directly. The map emits a parent-ASIN key and a tuple containing one review, rating, negative indicator, negative helpful votes and verified indicator. `reduceByKey` performs the shuffle and combines tuples by associative addition. This produced 1,836,721 parent-product groups.”

## 3:15-4:20 - DataFrame grouping and reduction

**Show:** `groupBy`, pivot, join and risk-score code; then the eligible-count output.

**Say:** “The substantive DataFrame aggregation groups by parent ASIN. Reviews with the same key must move across partitions, so this creates a shuffle. Spark can partially aggregate locally before the exchange and then perform the final reduction. A second aggregation calculates historical and recent mean ratings, and a key-based join connects those results. We require at least 50 reviews, leaving 17,765 eligible products. The risk score multiplies negative share, log review volume, logged helpful negative votes, and a penalty for recent deterioration. Every component remains visible.”

## 4:20-5:15 - Correctness and execution evidence

**Show:** Zero-mismatch cell and the formatted physical plan around `Exchange`, `HashAggregate` and `SortMergeJoin`.

**Say:** “We validate the DataFrame reduction against the independent RDD result. The mismatch count is zero for product count, rating sum, negative count, negative helpful votes and verified count. In the physical plan, scans, filters and projections are narrow mapping transformations. `Exchange` marks shuffle boundaries, while partial and final `HashAggregate` operators show reduction. The sort-merge join combines the product and period summaries.”

## 5:15-5:55 - Spark DAG versus Hadoop MapReduce

**Show:** DAG explanation markdown and execution-evidence JSON.

**Say:** “Traditional Hadoop MapReduce uses a relatively rigid Map, Shuffle, Reduce sequence and generally materialises intermediate results between jobs. Spark constructs a DAG, pipelines compatible narrow transformations within stages, and creates stage boundaries at wide dependencies such as grouping or joining. It can cache intermediate data and adapt the physical plan using runtime statistics.”

## 5:55-7:15 - Results

**Show:** Top-risk table and distribution summary.

**Say:** “The first-ranked product is B019VM3CPW with a risk score of 28.18. It has 408 reviews, a 26.23 percent negative share, 222 helpful votes on negative reviews, and its mean rating declined from 3.789 historically to 2.000 recently. B074TWL5HV ranks second with 2,329 reviews, a 37.87 percent negative share and 452 helpful negative votes. Across eligible products, mean rating is 4.287, mean negative share is 11.14 percent, and the median risk score is 1.616. The average recent-minus-historical change among products with both periods is negative 0.118 stars. These are descriptive results, not causal claims.”

## 7:15-8:05 - Visualisations

**Show:** Each of the three charts in sequence.

**Say:** “The horizontal bar chart communicates the highest priorities. The volume-versus-rating plot uses a log review-count axis and colour for negative share, allowing high- and moderate-volume products to be compared. The rating-change histogram separates improvement from deterioration with a zero reference line. Only small aggregate tables are converted to Pandas for these plots.”

## 8:05-9:00 - Value and limitations

**Show:** Interpretation/limitations markdown cell.

**Say:** “Retailers and manufacturers can use the ranking to prioritise manual review, compare complaints with returns or warranty records, and investigate recent changes. Potential consumer value is earlier identification of persistent concerns. Limitations include voluntary-review selection bias, the sequential subset, incomplete 2023 coverage, possible product-variant or listing merges, manipulation of ratings or helpful votes, and the sensitivity of a composite score. The output should guide human investigation and must not trigger automatic penalties.”

## 9:00-9:30 - Reproducibility and close

**Show:** GitHub repository structure and README.

**Say:** “The GitHub repository provides the notebooks, requirements, measured evidence, result table, figures and reproduction instructions. Raw reviews are excluded and recreated from the documented public source. The verified RDD and DataFrame agreement, Spark plan and exported evidence make the analysis auditable. Thank you.”

## Recording checklist

- Keep the final recording below 10 minutes; aim for 9 minutes.
- Increase Colab browser zoom enough for code and outputs to be readable.
- Collapse long outputs before recording, except the relevant plan fragment.
- Do not wait for cells to execute during the video; use the saved executed notebook.
- Show all three charts and the zero-mismatch line.
- End on the GitHub README and repository structure.
- Export or upload the video and test the final link in a private/incognito window before submitting it through the ClickUP Google Form.
