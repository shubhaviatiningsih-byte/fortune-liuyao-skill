"""CLI for the standalone Liuyao chart and rule-fact engine."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from liuyao_core import build_chart, derive_calendar, validate_lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a deterministic Wenwang Najia Liuyao chart")
    parser.add_argument("--lines", required=True, help="Six bottom-up values, for example 7,8,8,6,7,8")
    parser.add_argument("--cast-at", required=True, help="ISO-8601 timestamp")
    parser.add_argument("--timezone", default="Asia/Shanghai", help="IANA timezone")
    parser.add_argument("--day-boundary", default="zi_hour", choices=("zi_hour", "midnight"))
    parser.add_argument("--day-ganzhi", help="Optional verified day stem-branch; skips calendar derivation for this field")
    parser.add_argument("--month-branch", help="Optional verified month branch; skips calendar derivation for this field")
    parser.add_argument("--category", default="general")
    parser.add_argument("--subtype")
    parser.add_argument("--question")
    parser.add_argument("--perspective")
    parser.add_argument(
        "--casting-method",
        default="specified_lines",
        choices=("specified_lines", "auto", "manual_coins", "agent_recorded"),
        help="How the six bottom-up line values were obtained",
    )
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    moment = datetime.fromisoformat(args.cast_at)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=ZoneInfo(args.timezone))
    else:
        moment = moment.astimezone(ZoneInfo(args.timezone))
    calendar = None
    # Both day-ganzhi and month-branch must be provided together to skip the
    # calendar; a partially verified input would silently mix an external value
    # with a derived value from a different provenance.
    if not (args.day_ganzhi and args.month_branch):
        calendar = derive_calendar(moment, args.day_boundary)
        if args.day_ganzhi or args.month_branch:
            raise ValueError(
                "--day-ganzhi and --month-branch must be provided together; "
                "use both to skip calendar derivation, or neither to derive both"
            )
    day_ganzhi = args.day_ganzhi or calendar["dayGanzhi"]
    month_branch = args.month_branch or calendar["monthBranch"]
    result = build_chart(
        validate_lines(part.strip() for part in args.lines.split(",")),
        day_ganzhi=day_ganzhi,
        month_branch=month_branch,
        cast_at=moment.isoformat(),
        question_category=args.category,
        question_subtype=args.subtype,
        question_text=args.question,
        question_perspective=args.perspective,
    )
    result["castingAudit"]["method"] = args.casting_method
    result["calendar"] = calendar or {
        "dayGanzhi": day_ganzhi, "monthBranch": month_branch,
        "timezone": args.timezone, "localWallClock": moment.replace(tzinfo=None).isoformat(),
        "dayBoundaryPolicy": args.day_boundary, "calendarLibrary": "externally_verified",
    }
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
