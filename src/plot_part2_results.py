"""Create a dependency-free SVG ranking figure from committed Part 2 results."""

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
with (ROOT / "results" / "part2_top_risk_products.csv").open(encoding="utf-8") as source:
    rows = list(csv.DictReader(source))

width, height = 1000, 650
left, right, top, bottom = 150, 40, 70, 70
plot_width = width - left - right
plot_height = height - top - bottom
bar_height = plot_height / len(rows) * 0.66

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
    '<rect width="100%" height="100%" fill="white"/>',
    '<style>text{font-family:Arial,sans-serif;fill:#222}.title{font-size:24px;font-weight:700}.axis{font-size:14px}.label{font-size:13px}</style>',
    f'<text class="title" x="{width/2}" y="35" text-anchor="middle">Highest-priority product risk signals</text>',
]

for tick in range(0, 31, 5):
    x = left + tick / 30 * plot_width
    parts.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{height-bottom}" stroke="#dddddd"/>')
    parts.append(f'<text class="axis" x="{x:.1f}" y="{height-bottom+24}" text-anchor="middle">{tick}</text>')

for index, row in enumerate(reversed(rows)):
    centre = top + (index + 0.5) * plot_height / len(rows)
    score = float(row["risk_score"])
    bar_width = score / 30 * plot_width
    parts.append(f'<text class="label" x="{left-10}" y="{centre+5:.1f}" text-anchor="end">{row["parent_asin"]}</text>')
    parts.append(f'<rect x="{left}" y="{centre-bar_height/2:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" fill="#b3473d"/>')
    parts.append(f'<text class="label" x="{left+bar_width+7:.1f}" y="{centre+5:.1f}">{score:.2f}</text>')

parts.extend([
    f'<text class="axis" x="{left+plot_width/2}" y="{height-15}" text-anchor="middle">Composite risk score</text>',
    '</svg>',
])

output = ROOT / "figures" / "part2_top_risk_products.svg"
output.write_text("\n".join(parts), encoding="utf-8")
print(output)
