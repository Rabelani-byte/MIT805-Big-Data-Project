"""Synchronize reproducible Part 1 artifacts from the executed notebook."""

from __future__ import annotations

import base64
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "Data_Collection_and_Analysis_.ipynb"
FIGURES = ROOT / "figures"
RESULTS = ROOT / "results"

FIGURE_CELLS = {
    15: "rating_distribution.png",
    16: "review_volume_by_year.png",
    18: "mean_rating_by_year.png",
    19: "verified_purchase_comparison.png",
    20: "rating_length_helpfulness.png",
    21: "top_products.png",
}


def output_text(cell: dict) -> str:
    chunks: list[str] = []
    for output in cell.get("outputs", []):
        text = output.get("text", "")
        chunks.append("".join(text) if isinstance(text, list) else text)
    return "".join(chunks)


def printed_json(cell: dict) -> dict:
    text = output_text(cell)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("Expected printed JSON was not found")
    return json.loads(text[start : end + 1])


def main() -> None:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = notebook["cells"]
    FIGURES.mkdir(exist_ok=True)
    RESULTS.mkdir(exist_ok=True)

    for index, filename in FIGURE_CELLS.items():
        images = [
            output.get("data", {}).get("image/png")
            for output in cells[index].get("outputs", [])
        ]
        images = [image for image in images if image]
        if len(images) != 1:
            raise ValueError(f"Cell {index} must contain exactly one PNG output")
        payload = "".join(images[0]) if isinstance(images[0], list) else images[0]
        (FIGURES / filename).write_bytes(base64.b64decode(payload))

    evidence = printed_json(cells[23])
    volume = evidence["volume"]
    scale_keys = (
        "raw_dataset_definition", "hosted_file_bytes", "hosted_file_GB_decimal",
        "displayed_source_size_GB", "retrieved_utc", "working_file_bytes",
        "working_file_GB_decimal", "processing_file_bytes",
        "processing_file_GB_decimal",
    )
    scale = {key: volume[key] for key in scale_keys}

    artifacts = {
        "dataset_scale.json": scale,
        "quality_summary.json": evidence["veracity"],
        "part1_evidence.json": evidence,
    }
    for filename, artifact in artifacts.items():
        (RESULTS / filename).write_text(
            json.dumps(artifact, indent=2) + "\n", encoding="utf-8"
        )

    print(f"Synchronized {len(FIGURE_CELLS)} figures and {len(artifacts)} JSON files")


if __name__ == "__main__":
    main()
