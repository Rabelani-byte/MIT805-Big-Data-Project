# Data directory

Raw data is not committed to GitHub.

The Part 1 notebook retrieves:

`raw/review_categories/Clothing_Shoes_and_Jewelry.jsonl`

from the McAuley Lab Amazon Reviews 2023 Hugging Face repository. The hosted file is listed as 27.8 GB. The notebook must record the exact downloaded size and create a line-safe processing subset of at least 3 GiB.

Expected local layout after running the notebook:

```text
/content/mit805_part1/data/
|-- raw/raw/review_categories/Clothing_Shoes_and_Jewelry.jsonl
`-- processed/Clothing_Shoes_and_Jewelry_3GiB.jsonl
```

The repeated `raw/raw` component results from passing the repository-relative Hugging
Face filename to `hf_hub_download()` beneath the notebook's `RAW_DIR`.


