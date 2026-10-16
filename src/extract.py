"""Extract the listing data embedded in the 'Turbo.az Qiymət Radarı' HTML page into a tidy CSV.

Usage: python src/extract.py "<path to Turbo.az Qiymət Radarı.html>"
"""
from pathlib import Path
import json
import re
import sys

import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "data" / "listings.csv"
COLS = ["slug", "brand", "model", "price_azn", "year", "engine_l", "km", "city", "updated",
        "tags", "is_dealer", "seller", "official", "price_estimated"]


def main(html_path: str) -> None:
    html = Path(html_path).read_text(encoding="utf-8")
    raw = re.search(r"const D = (\{.*?\});\n", html, re.S).group(1)
    d = json.loads(raw)
    rows = []
    for r in d["rows"]:
        rows.append([r[0], d["brands"][r[1]], r[2], r[3], r[4], r[5], r[6], d["cities"][r[7]], r[8],
                     r[9], r[10], d["sellers"][r[11]], r[12], r[13]])
    df = pd.DataFrame(rows, columns=COLS)
    df.to_csv(OUT, index=False)
    print(f"{len(df):,} listings, {df.brand.nunique()} brands, scraped {d['scraped']}, "
          f"{len(d['gone'])} removed listings skipped -> {OUT}")


if __name__ == "__main__":
    main(sys.argv[1])
