"""Audit only explicit deterministic chart claims; never grade divination."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


POSITION = {"初": 1, "二": 2, "三": 3, "四": 4, "五": 5, "上": 6}
RELATIVES = ("父母", "兄弟", "子孙", "妻财", "官鬼")


def verify_report(text: str, response: dict[str, Any]) -> dict[str, Any]:
    """Return explicit fact conflicts without judging吉凶、应期 or traditional inference."""
    chart = response.get("chart", response)
    errors: list[dict[str, object]] = []
    for match in re.finditer(r"([初二三四五上])爻(?:为|是|临)?(父母|兄弟|子孙|妻财|官鬼)", text):
        position = POSITION[match.group(1)]
        actual = chart.get("lines", [])[position - 1].get("sixRelative")
        if actual != match.group(2):
            errors.append({"type": "line_relative", "position": position, "claimed": match.group(2), "actual": actual})
    for label, field in (("世", "shiPosition"), ("应", "yingPosition")):
        for match in re.finditer(rf"{label}爻(?:在|居|临)([初二三四五上])爻", text):
            claimed = POSITION[match.group(1)]
            actual = chart.get(field)
            if claimed != actual:
                errors.append({"type": f"{field}", "claimed": claimed, "actual": actual})
    original = (chart.get("originalHexagram") or {}).get("name")
    changed = (chart.get("changedHexagram") or {}).get("name")
    for label, actual in (("本卦", original), ("变卦", changed)):
        match = re.search(rf"{label}(?:为|是|：)\s*([^，。；\s]+)", text)
        if match and actual and match.group(1) != actual:
            errors.append({"type": label, "claimed": match.group(1), "actual": actual})
    return {
        "schemaVersion": "fortune-liuyao-fact-audit.v1",
        "accepted": not errors,
        "errors": errors,
        "scope": "explicit_deterministic_chart_claims_only",
        "unrestricted": ["吉凶判断", "应期推断", "传统取象", "作用链主次"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit explicit chart facts in a completed interpretation")
    parser.add_argument("--chart", required=True, type=Path, help="Unified run JSON or raw chart JSON")
    parser.add_argument("--report", required=True, type=Path, help="Completed Markdown or text interpretation")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    response = json.loads(args.chart.read_text(encoding="utf-8"))
    result = verify_report(args.report.read_text(encoding="utf-8"), response.get("result", response))
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    raise SystemExit(0 if result["accepted"] else 2)


if __name__ == "__main__":
    main()
