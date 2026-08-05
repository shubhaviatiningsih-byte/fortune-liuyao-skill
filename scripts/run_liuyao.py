"""One-shot Skill entry: deterministic chart plus prompt for the current Agent."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_model_packet import build_packet
from cast_lines import _automatic_cast, _manual_cast
from classify_sensitive import classify_dict
from liuyao_core import build_chart, derive_calendar, validate_lines


DOMAINS = (
    "general", "career", "wealth", "relationship", "academic",
    "travel", "home", "legal_risk", "relationship_family",
)


def infer_deadline(question: str) -> str | None:
    deadline = re.search(r"(?:未来|接下来)?\s*([一二三四五六七八九十两\d]+(?:天|周|个月|月|年)(?:内|之内)?)", question)
    return deadline.group(1) if deadline else None


def parse_lines(raw: str) -> list[int]:
    return validate_lines([int(item) for item in re.split(r"[,，\s]+", raw.strip()) if item])


def run(
    question: str,
    category: str,
    method: str,
    timezone: str,
    raw_lines: str | None,
    coins: str | None,
    perspective: str | None = None,
) -> dict[str, object]:
    safety = classify_dict(question)
    if not safety["allowed"]:
        return {"ok": False, "blocked": True, "safety": safety}
    if method == "auto":
        rounds = _automatic_cast()
        lines = [int(row["value"]) for row in rounds]
    elif method == "coins":
        if not coins:
            raise ValueError("coins method requires --coins with six rounds from bottom to top")
        rounds = _manual_cast(coins)
        lines = [int(row["value"]) for row in rounds]
    else:
        if not raw_lines:
            raise ValueError("lines method requires --lines with six values from bottom to top")
        lines = parse_lines(raw_lines)
        rounds = [{"round": index, "value": value} for index, value in enumerate(lines, 1)]
    moment = datetime.now(ZoneInfo(timezone))
    calendar = derive_calendar(moment)
    if category not in DOMAINS:
        raise ValueError(f"unsupported category: {category}")
    result = build_chart(
        lines,
        day_ganzhi=calendar["dayGanzhi"],
        month_branch=calendar["monthBranch"],
        cast_at=moment.isoformat(),
        question_category=category,
        question_text=question,
        question_perspective=perspective,
    )
    result["calendar"] = calendar
    result["castingAudit"]["method"] = method
    result["castingAudit"]["rounds"] = rounds
    result["analysis"]["questionContext"]["deadline"] = infer_deadline(question)
    packet = build_packet(result)
    prompt = "\n\n".join(str(message["content"]) for message in packet["messages"])
    return {"ok": True, "blocked": False, "result": result, "prompt": prompt}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Liuyao chart and Agent-ready interpretation prompt")
    parser.add_argument("--question", required=True)
    parser.add_argument("--category", choices=DOMAINS, default="general", help="Semantic route selected by the current Agent")
    parser.add_argument("--method", choices=("auto", "lines", "coins"), default="auto")
    parser.add_argument("--lines", help="Six 6/7/8/9 values from bottom line to top line")
    parser.add_argument("--coins", help="Six slash-separated three-coin rounds from bottom to top")
    parser.add_argument("--timezone", default="Asia/Shanghai")
    parser.add_argument(
        "--perspective",
        choices=("male", "female", "unspecified"),
        default="unspecified",
        help="Optional relationship perspective; do not request for unrelated domains",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    perspective = None if args.perspective == "unspecified" else args.perspective
    value = run(args.question, args.category, args.method, args.timezone, args.lines, args.coins, perspective)
    text = json.dumps(value, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
