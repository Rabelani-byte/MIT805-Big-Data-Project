"""Generate report figures from the executed Part 1 Spark aggregations."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FIGURES = Path(__file__).resolve().parents[1] / "figures"
FIGURES.mkdir(exist_ok=True)
FONT = ImageFont.truetype("arial.ttf", 26)
SMALL = ImageFont.truetype("arial.ttf", 20)
BOLD = ImageFont.truetype("arialbd.ttf", 28)
BLUE = "#3569b7"
GRID = "#d7dde5"


def canvas(title, xlabel, ylabel):
    image = Image.new("RGB", (1500, 720), "white")
    draw = ImageDraw.Draw(image)
    draw.text((750, 22), title, font=BOLD, fill="#182433", anchor="ma")
    draw.line((125, 90, 125, 620), fill="#333333", width=3)
    draw.line((125, 620, 1430, 620), fill="#333333", width=3)
    draw.text((780, 680), xlabel, font=FONT, fill="#333333", anchor="mm")
    # Keep the horizontal y-axis label fully inside the exported bitmap.
    draw.text((12, 355), ylabel, font=FONT, fill="#333333", anchor="lm")
    return image, draw


ratings = [1, 2, 3, 4, 5]
counts = [472381, 376802, 649147, 1085590, 4647623]
image, draw = canvas("Review rating distribution", "Rating (stars)", "Reviews")
max_y = 5_000_000
for tick in range(0, max_y + 1, 1_000_000):
    y = 620 - tick / max_y * 500
    draw.line((125, y, 1430, y), fill=GRID, width=2)
    draw.text((110, y), f"{tick/1e6:.0f}M", font=SMALL, fill="#444444", anchor="rm")
for i, (rating, value) in enumerate(zip(ratings, counts)):
    x0 = 205 + i * 245
    height = value / max_y * 500
    draw.rectangle((x0, 620 - height, x0 + 145, 620), fill=BLUE)
    draw.text((x0 + 72, 635), str(rating), font=SMALL, fill="#333333", anchor="ma")
    draw.text((x0 + 72, 605 - height), f"{value/1e6:.2f}M", font=SMALL, fill="#333333", anchor="ms")
image.save(FIGURES / "rating_distribution.png")

years = [1999, 2000, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009,
         2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019,
         2020, 2021, 2022, 2023]
values = [1, 3, 3, 7, 20, 112, 334, 1320, 2237, 3631, 7085, 15169,
          35864, 106455, 221415, 375728, 539145, 616925, 777115,
          1078297, 1025346, 1133095, 1054750, 237486]
image, draw = canvas("Review volume over time", "Year", "Reviews")
max_y = 1_200_000
for tick in range(0, max_y + 1, 200_000):
    y = 620 - tick / max_y * 500
    draw.line((125, y, 1430, y), fill=GRID, width=2)
    draw.text((110, y), f"{tick/1e6:.1f}M", font=SMALL, fill="#444444", anchor="rm")
points = []
for year, value in zip(years, values):
    x = 125 + (year - 1999) / 24 * 1305
    y = 620 - value / max_y * 500
    points.append((x, y))
draw.line(points, fill=BLUE, width=6, joint="curve")
for x, y in points:
    draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=BLUE)
for year in range(2000, 2024, 4):
    x = 125 + (year - 1999) / 24 * 1305
    draw.text((x, 635), str(year), font=SMALL, fill="#333333", anchor="ma")
x, y = points[-1]
draw.text((x - 10, y - 30), "2023 partial year", font=SMALL, fill="#9a6410", anchor="rs")
image.save(FIGURES / "review_volume_by_year.png")
