"""Render a standalone HTML Liuyao chart from runtime JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chart", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    data = json.loads(args.chart.read_text(encoding="utf-8"))
    template_path = Path(__file__).resolve().parents[1] / "assets" / "liuyao-viewer.html"
    template = template_path.read_text(encoding="utf-8")
    # Escape for embedding inside a <script> string literal. JSON dumps escapes
    # quotes/backslashes but NOT "<" or ">", so a "script"-ending sequence in
    # user text (e.g. the question) would break out of the script tag. Replace
    # those two with their hex escapes so the literal stays well-formed.
    embedded = json.dumps(json.dumps(data, ensure_ascii=False), ensure_ascii=False)[1:-1]
    embedded = embedded.replace("<", "\\u003c").replace(">", "\\u003e")
    args.output.write_text(template.replace("__LIUYAO_DATA__", embedded), encoding="utf-8")


if __name__ == "__main__":
    main()
