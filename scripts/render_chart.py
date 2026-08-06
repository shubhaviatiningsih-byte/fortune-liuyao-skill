"""Render a standalone HTML Liuyao chart from runtime JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from render_chart_text import render as render_markdown


def render_html(data: dict[str, object]) -> str:
    """Render either a chart response or the unified {result, prompt} wrapper."""
    source = data.get("result") or data
    if not isinstance(source, dict) or not isinstance(source.get("chart"), dict):
        raise ValueError("input must contain a chart response or an object at 'result'")
    template_path = Path(__file__).resolve().parents[1] / "assets" / "liuyao-viewer.html"
    template = template_path.read_text(encoding="utf-8")
    embedded = json.dumps(json.dumps(source, ensure_ascii=False), ensure_ascii=False)[1:-1]
    embedded = embedded.replace("<", "\\u003c").replace(">", "\\u003e")
    return template.replace("__LIUYAO_DATA__", embedded)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chart", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()
    data = json.loads(args.chart.read_text(encoding="utf-8"))
    args.output.write_text(render_html(data), encoding="utf-8")
    markdown_output = args.markdown_output or args.output.with_suffix(".md")
    markdown_output.write_text(render_markdown(data), encoding="utf-8")


if __name__ == "__main__":
    main()
