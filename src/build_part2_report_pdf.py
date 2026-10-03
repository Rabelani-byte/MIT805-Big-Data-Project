"""Build the submission-ready MIT805 Part 2 report PDF."""

from pathlib import Path

from reportlab.graphics.charts.barcharts import HorizontalBarChart, VerticalBarChart
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageBreak, PageTemplate, Paragraph, Spacer,
    Table, TableStyle, KeepTogether,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf"
OUTPUT.mkdir(parents=True, exist_ok=True)
PDF_PATH = OUTPUT / "MIT805_PART2_GROUP_6_REPORT.pdf"

PAGE_W, PAGE_H = A4
MARGIN = 1.65 * cm
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="Title2", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=18, leading=22, alignment=TA_CENTER, textColor=colors.HexColor("#17365D"), spaceAfter=8))
styles.add(ParagraphStyle(name="SubTitle", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=12, leading=15, alignment=TA_CENTER, textColor=colors.HexColor("#365F91"), spaceAfter=10))
styles.add(ParagraphStyle(name="H1x", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=14, leading=17, textColor=colors.HexColor("#17365D"), spaceBefore=5, spaceAfter=6))
styles.add(ParagraphStyle(name="H2x", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=colors.HexColor("#365F91"), spaceBefore=5, spaceAfter=4))
styles.add(ParagraphStyle(name="Bodyx", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.8, leading=11.4, spaceAfter=5, alignment=0))
styles.add(ParagraphStyle(name="Smallx", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.6, leading=9.4, spaceAfter=3))
styles.add(ParagraphStyle(name="Captionx", parent=styles["BodyText"], fontName="Helvetica-Oblique", fontSize=7.5, leading=9, alignment=TA_CENTER, textColor=colors.HexColor("#444444"), spaceBefore=3, spaceAfter=5))


def P(text, style="Bodyx"):
    return Paragraph(text, styles[style])


def styled_table(data, widths, font=7.5):
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), font),
        ("LEADING", (0, 0), (-1, -1), font + 2),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B8C5D6")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F6FA")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#B8C5D6"))
    canvas.line(MARGIN, 1.1 * cm, PAGE_W - MARGIN, 1.1 * cm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(MARGIN, 0.72 * cm, "MIT 805 Part 2 - Group 6")
    canvas.drawRightString(PAGE_W - MARGIN, 0.72 * cm, f"Page {doc.page}")
    canvas.restoreState()


def risk_chart():
    labels = ["B000M85KOQ", "B075ZTS57G", "B0BN9DY5FV", "B075B41Y9Z", "B07V33GN1Q", "B0BS66M37H", "B07KCN4G6T", "B073D254G5", "B074TWL5HV", "B019VM3CPW"]
    values = [19.488, 19.888, 19.934, 20.326, 20.966, 21.542, 22.590, 23.427, 26.980, 28.180]
    d = Drawing(480, 225)
    chart = HorizontalBarChart()
    chart.x, chart.y, chart.width, chart.height = 92, 28, 350, 170
    chart.data = [values]
    chart.categoryAxis.categoryNames = labels
    chart.categoryAxis.labels.fontSize = 6.7
    chart.valueAxis.valueMin, chart.valueAxis.valueMax, chart.valueAxis.valueStep = 0, 30, 5
    chart.valueAxis.labels.fontSize = 7
    chart.bars[0].fillColor = colors.HexColor("#B3473D")
    chart.bars[0].strokeColor = None
    chart.barWidth = 7
    d.add(chart)
    d.add(String(255, 5, "Composite risk score", textAnchor="middle", fontName="Helvetica", fontSize=8))
    return d


def rating_chart():
    labels = ["Below 3.0", "3.0-3.49", "3.5-3.99", "4.0+"]
    values = [22, 239, 2422, 15082]
    d = Drawing(480, 220)
    chart = VerticalBarChart()
    chart.x, chart.y, chart.width, chart.height = 58, 38, 390, 145
    chart.data = [values]
    chart.categoryAxis.categoryNames = labels
    chart.categoryAxis.labels.fontSize = 7
    chart.valueAxis.valueMin, chart.valueAxis.valueMax, chart.valueAxis.valueStep = 0, 16000, 4000
    chart.valueAxis.labels.fontSize = 7
    chart.bars[0].fillColor = colors.HexColor("#4F81BD")
    chart.bars[0].strokeColor = None
    d.add(chart)
    d.add(String(250, 6, "Mean-rating band", textAnchor="middle", fontName="Helvetica", fontSize=8))
    return d


story = []
story += [P("MIT 805: Big Data Semester Project", "Title2"), P("Part 2 - PySpark, MapReduce and Visualisation", "SubTitle"), P("Amazon Reviews 2023: Clothing, Shoes and Jewelry", "SubTitle"), P("<b>Group 6:</b> u26842328 RY Muthadzwi - u16153970 M Ndlovu", "SubTitle")]
story += [P("1. Processing Objective and Analytical Question", "H1x")]
story += [P("This analysis asks: <i>Which sufficiently reviewed parent products show the greatest customer-experience risk when review volume, low-rating prevalence, helpful negative feedback, and recent rating change are considered together?</i> The objective is to convert millions of review events into a transparent product-level prioritisation tool. A high score indicates a combination of signals requiring investigation; it does not prove that a product is defective.")]
story += [P("Five linked objectives are used: transform raw reviews into typed analytical features; demonstrate mapping, shuffle and reduction on the full processing dataset; calculate product-level volume, rating, negative-review and helpfulness measures; compare historical and recent ratings; and rank sufficiently observed products while retaining the component measures for auditability. Products require at least 50 reviews. Part 1 found a 99th percentile of 48 reviews per product, so this rule focuses on unusually well-observed products and reduces instability from tiny groups.")]
story += [P("Dataset scale and subset justification", "H2x")]
story += [P("The public category file contains 27,810,080,533 bytes (27.810 GB; 25.900 GiB). The downloaded working file has the same size because it was not filtered. A line-safe prefix containing 3,221,225,482 bytes (3.221 GB; 3.000 GiB) and 7,231,543 complete JSONL records was processed using PySpark 4.0.0. Copying complete lines prevents a corrupt final record. The subset is computationally manageable in Colab but is sequential and may differ from the complete file in temporal or product composition.")]
story += [styled_table([["Stage", "Measured size", "Role"], ["Raw", "27,810,080,533 bytes (27.810 GB)", "Original public category file"], ["Working", "27,810,080,533 bytes (27.810 GB)", "Complete downloaded JSONL file"], ["Processing", "3,221,225,482 bytes (3.221 GB)", "7,231,543 records processed by Spark"]], [2.5*cm, 6.0*cm, 8.0*cm])]
story += [P("Table 1. Measured data scale used in Part 2.", "Captionx"), PageBreak()]

story += [P("2. Mapping and Transformation", "H1x")]
story += [P("Spark reads JSONL directly, selects the parent product, user, rating, helpful-vote, verified-purchase, timestamp and review-text fields, and applies explicit types. Records without a parent product or with ratings outside 1-5 are excluded. Each valid review is mapped to negative and positive indicators, a verified-purchase flag, negative helpful votes, log-transformed helpfulness, review year, and a historical/recent period. The log transform limits leverage from the highly right-skewed helpful-vote count without discarding genuine popular reviews.")]
mapping = [["Mapped field", "Purpose"], ["parent_asin", "Key used to bring reviews for the same parent product together."], ["rating / is_negative", "Mean rating and prevalence of one- or two-star feedback."], ["negative_helpful", "Strength of customer endorsement for negative feedback."], ["verified_flag", "Descriptive share of verified reviews."], ["period", "Historical (<=2020) versus recent (2021-2023) comparison."]]
story += [styled_table(mapping, [4.1*cm, 12.4*cm]), P("Table 2. Map-stage fields and analytical purpose.", "Captionx")]
story += [P("The transformed DataFrame is repartitioned into 64 partitions by parent ASIN and cached because several aggregations reuse it. These are lazy transformations: Spark records lineage and executes the DAG only when an action such as count, show or write is requested. All substantive operations remain distributed in Spark; Pandas receives only bounded aggregate tables for final plotting.")]
story += [P("Explicit MapReduce validation", "H2x")]
story += [P("An independent RDD pipeline emits <font name='Courier'>(parent_asin, (1, rating, negative, negative_helpful, verified))</font> for every valid review. <font name='Courier'>reduceByKey</font> shuffles by the key and combines tuples using associative element-wise addition. It produced 1,836,721 product keys. The result was compared with the DataFrame aggregation across review count, rating sum, negative count, negative helpful votes and verified count. The mismatch count was zero, providing an independent correctness check.")]
story += [PageBreak()]

story += [P("3. Shuffle, Reduction and Spark Execution", "H1x")]
story += [P("Grouping by parent ASIN creates a wide dependency. Reviews sharing a product key may begin in different partitions, so Spark hashes the key and moves intermediate records across partitions. The physical plan records this as an <font name='Courier'>Exchange</font>. Spark performs partial <font name='Courier'>HashAggregate</font> operations before the exchange where possible, reducing shuffle volume, followed by final reduction once equal keys are co-located.")]
story += [P("The product reduction calculates review count, mean rating, negative count and share, positive count, negative helpful-vote total, verified share, mean log-helpfulness, first year and last year. A second grouped pivot calculates historical and recent mean ratings. A left join connects the compact product tables. Requiring 50 reviews leaves 17,765 eligible products.")]
story += [P("The transparent composite score is <b>negative share x log(1 + review count) x [1 + log(1 + negative helpful votes)] x [1 + max(-rating change, 0)]</b>. Logarithms prevent extremely large counts from overwhelming other components. A decline increases risk, while improvement does not erase the base signal.")]
story += [P("Spark DAG compared with Hadoop MapReduce", "H2x")]
story += [P("The physical plan contains scans, filters and projections (narrow mapping transformations), Exchange nodes (shuffle boundaries), partial and final HashAggregate stages, a pivot and a sort-merge join. Spark represents the work as a DAG and pipelines compatible narrow operations into stages. Wide dependencies create stage boundaries, caching supports reuse, and adaptive query execution can revise the physical plan using runtime statistics. Traditional Hadoop MapReduce uses a comparatively rigid Map -> Shuffle -> Reduce sequence for each job and typically materialises intermediate output to disk between jobs.")]
execution = [["Evidence", "Verified value"], ["Spark / partitioning", "PySpark 4.0.0; 64 shuffle and cached partitions"], ["Processing scale", "7,231,543 valid records"], ["RDD reduction", "1,836,721 parent-product keys"], ["Eligible groups", "17,765 products with at least 50 reviews"], ["Validation", "0 RDD/DataFrame aggregation mismatches"], ["Physical plan", "Exchange, partial/final HashAggregate, pivot, sort-merge join"]]
story += [styled_table(execution, [5.0*cm, 11.5*cm]), P("Table 3. Execution evidence from the verified Colab run.", "Captionx"), PageBreak()]

story += [P("4. Results and Technical Interpretation", "H1x")]
story += [P("Eligible products averaged 149.53 reviews and 4.287 stars. Mean negative-review share was 11.14%, while the median composite risk score was 1.616. Among 16,535 products observed in both periods, recent mean rating was on average 0.118 stars below the historical mean. This is descriptive and does not establish a causal platform-wide decline.")]
story += [P("B019VM3CPW ranked first with a score of 28.18. It combined 408 reviews, a 26.23% negative share, 222 helpful votes on negative reviews and a decline from 3.789 historical stars to 2.000 recent stars. B074TWL5HV ranked second (26.98) because 2,329 reviews, a 37.87% negative share and 452 helpful negative votes outweighed its smaller 0.291-star decline. The ranking therefore exposes products where several risk signals coincide rather than sorting on mean rating alone.")]
top = [["#", "Parent ASIN", "Reviews", "Mean", "Neg. share", "Change", "Score"], [1,"B019VM3CPW",408,"3.784","0.262","-1.789","28.180"], [2,"B074TWL5HV",2329,"3.221","0.379","-0.291","26.980"], [3,"B073D254G5",1163,"3.356","0.360","-0.526","23.427"], [4,"B07KCN4G6T",5844,"3.691","0.266","-0.331","22.590"], [5,"B0BS66M37H",373,"3.375","0.335","-0.565","21.542"], [6,"B07V33GN1Q",726,"3.408","0.332","-0.542","20.966"], [7,"B075B41Y9Z",1451,"3.521","0.290","-0.502","20.326"], [8,"B0BN9DY5FV",4628,"3.790","0.234","-0.520","19.934"], [9,"B075ZTS57G",89,"2.551","0.584","-0.777","19.888"], [10,"B000M85KOQ",51,"2.843","0.471","-1.880","19.488"]]
story += [styled_table(top, [0.7*cm, 3.2*cm, 2.0*cm, 1.7*cm, 2.1*cm, 2.0*cm, 1.8*cm], 6.7), P("Table 4. Ten highest-ranked product-risk signals.", "Captionx"), risk_chart(), P("Figure 1. Highest composite product-risk signals.", "Captionx"), PageBreak()]

story += [P("5. Visualisation and Pattern Interpretation", "H1x")]
story += [P("Three charts were produced from bounded Spark aggregates. The risk bar chart communicates ranking concentration. A second plot uses logarithmic review count against mean rating for the 5,000 most-reviewed eligible products, with colour representing negative-review share; this avoids compression by a few extremely high-volume products. A third chart shows recent-minus-historical rating change for 5,000 high-volume products with valid observations in both periods and includes a zero reference line. Only these compact results are converted to Pandas.")]
story += [rating_chart(), P("Figure 2. Eligible products by mean-rating band.", "Captionx")]
summary = [["Statistic", "Reviews", "Mean rating", "Negative share", "Neg. helpful", "Rating change", "Risk"], ["Mean","149.53","4.287","0.111","22.41","-0.118","2.194"], ["Median","87","4.322","0.100","7","-0.093","1.616"], ["75th pct.","144","4.500","0.145","19","0.120","2.955"], ["Maximum","37409","4.968","0.623","3065","3.523","28.180"]]
story += [styled_table(summary, [2.3*cm,2.0*cm,2.2*cm,2.4*cm,2.2*cm,2.3*cm,1.7*cm], 6.8), P("Table 5. Distribution summary for eligible products.", "Captionx")]
story += [P("The rating-band reduction found 22 eligible products below 3.0 stars, 239 between 3.0 and 3.49, 2,422 between 3.5 and 3.99, and 15,082 at least 4.0. The predominance above four stars agrees with Part 1's positive overall distribution, while the risk model highlights important exceptions with substantial evidence.")]
story += [PageBreak()]

story += [P("6. Business and Societal Value", "H1x")]
story += [P("Retail quality teams can use the ranking as a triage mechanism. High-volume products with unusually high negative share, strongly endorsed negative reviews and recent deterioration can be reviewed before lower-evidence cases. Manufacturers can compare recurring complaints with return, warranty and defect records; merchandising teams can assess listing descriptions, variants or sizing guidance; and platform teams can monitor whether recent changes coincide with seller, fulfilment or product-version changes. Decomposed score components make escalation explainable.")]
story += [P("Potential societal value includes improved transparency and fewer repeated negative experiences. Earlier investigation may identify misleading descriptions, unreliable sizing, durability concerns or safety complaints. Automated removal, seller penalties or safety claims must never be based on the score alone; human review of text and operational evidence is required.")]
story += [P("Limitations and safeguards", "H2x")]
limitations = [
    "<b>Selection bias:</b> reviews are voluntary and do not represent every purchaser.",
    "<b>Subset coverage:</b> the sequential 3 GiB prefix may differ from the complete 27.810 GB file.",
    "<b>Causality:</b> associations do not prove a product or platform change caused an outcome.",
    "<b>Product identity:</b> parent ASINs can combine variants or reflect listing merges.",
    "<b>Platform effects:</b> incentives, moderation, ranking or manipulation can affect ratings and votes.",
    "<b>Temporal comparability:</b> 2023 is partial and some products have few recent observations.",
    "<b>Score sensitivity:</b> the formula is a prioritisation rule, not a validated failure probability.",
]
for i, item in enumerate(limitations, 1):
    story.append(P(f"{i}. {item}"))
story += [P("Operational use should retain component measures, require sufficient recent evidence, inspect review text and metadata, test threshold sensitivity, and document decisions. Pseudonymous identifiers must not be used for re-identification.")]
story += [P("Reproducibility", "H2x"), P("The repository contains the PySpark notebook, dependencies, measured evidence, ranked output and reproduction instructions: <link href='https://github.com/Rabelani-byte/MIT805-Big-Data-Project'>github.com/Rabelani-byte/MIT805-Big-Data-Project</link>. The shared executed Colab notebook is linked from the README. Raw and processing data are excluded; the documented public source and line-safe recreation steps preserve reproducibility without improper redistribution. Commits are attributable to group contributors.")]
story += [PageBreak()]

story += [P("7. Conclusion", "H1x")]
story += [P("The verified PySpark pipeline transformed 7,231,543 reviews, grouped them into 1,836,721 product keys and identified 17,765 sufficiently reviewed products. Explicit RDD MapReduce and the independent DataFrame reduction agreed with zero mismatches. The Spark plan demonstrates mapping, exchange-driven shuffle, partial and final aggregation, pivoting and joining within a DAG-based execution model. Results identify a concentrated set of products where negative prevalence, evidence volume, helpful negative feedback and recent deterioration coincide. The score directs investigation rather than automatic judgement.")]
story += [P("References", "H1x")]
refs = [
    "1. J. Hou et al. (2024), <i>Bridging Language and Items for Retrieval and Recommendation</i>. https://arxiv.org/abs/2403.03952",
    "2. McAuley Lab, <i>Amazon Reviews 2023</i>, Hugging Face dataset repository. https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023",
    "3. Apache Software Foundation, <i>Spark Programming Guide and Spark SQL Performance Tuning</i>. https://spark.apache.org/docs/latest/",
    "4. MIT 805, <i>Big Data Semester Project (2026): Large-Scale Data Analysis and Distributed Processing with PySpark</i>, assignment brief.",
]
for ref in refs:
    story.append(P(ref, "Smallx"))
story += [Spacer(1, 8), P("Appendix: video and evidence checklist", "H2x"), P("The <=10-minute demonstration should show: measured sizes; transformed schema; RDD map and reduceByKey; DataFrame grouping and risk calculation; zero-mismatch validation; Exchange and HashAggregate plan evidence; top-risk results; all three notebook charts; stakeholder interpretation; limitations; and GitHub reproduction steps. The notebook exports evidence JSON, the ranked CSV, rating bands, the executed plan and three figures.")]

doc = BaseDocTemplate(str(PDF_PATH), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=1.35*cm, bottomMargin=1.45*cm, title="MIT805 Part 2 Group 6 Report", author="RY Muthadzwi and M Ndlovu")
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=footer)])
doc.build(story)
print(PDF_PATH)
