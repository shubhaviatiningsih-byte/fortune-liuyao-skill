"""One-shot Skill entry: deterministic chart plus prompt for the current Agent."""

from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from build_model_packet import build_packet
from cast_lines import _automatic_cast, _manual_cast
from classify_sensitive import classify_dict
from liuyao_core import build_chart, derive_calendar, validate_lines
from render_chart import render_html
from render_chart_text import render as render_markdown


DOMAINS = (
    "general", "career", "wealth", "relationship", "academic",
    "travel", "home", "legal_risk", "relationship_family",
)

OUTPUT_SCHEMA_VERSION = "fortune-liuyao-run.v2"


def resolve_timezone(name: str):
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        if name == "Asia/Shanghai":
            return timezone(timedelta(hours=8), name="Asia/Shanghai")
        raise


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
    artifact_dir: Path | None = None,
    artifact_stem: str = "fortune-liuyao-chart",
) -> dict[str, object]:
    safety = classify_dict(question)
    if not safety["allowed"]:
        return {
            "schemaVersion": OUTPUT_SCHEMA_VERSION,
            "ok": False,
            "blocked": True,
            "safety": safety,
            "artifacts": {"html": None, "markdown": None},
        }
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
    moment = datetime.now(resolve_timezone(timezone))
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
    response: dict[str, object] = {
        "schemaVersion": OUTPUT_SCHEMA_VERSION,
        "ok": True,
        "blocked": False,
        "result": result,
        "prompt": prompt,
        "artifacts": {"html": None, "markdown": None},
    }
    if artifact_dir is not None:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        html_path = (artifact_dir / f"{artifact_stem}.html").resolve()
        markdown_path = (artifact_dir / f"{artifact_stem}.md").resolve()
        html_path.write_text(render_html(response), encoding="utf-8")
        markdown_path.write_text(render_markdown(response), encoding="utf-8")
        response["artifacts"] = {"html": str(html_path), "markdown": str(markdown_path)}
    return response


def selfcheck() -> dict[str, object]:
    """Verify runtime dependencies, deterministic core, templates, and renderers."""
    checks: list[dict[str, object]] = []

    def record(name: str, action) -> None:
        try:
            action()
            checks.append({"name": name, "ok": True})
        except Exception as exc:  # Report every failed prerequisite to the caller.
            checks.append({"name": name, "ok": False, "error": str(exc)})

    def check_python() -> None:
        if sys.version_info < (3, 10):
            raise RuntimeError(f"Python 3.10+ required; found {sys.version.split()[0]}")

    record("python_runtime", check_python)
    record("timezone_support", lambda: resolve_timezone("Asia/Shanghai"))

    def check_vendored_lunar() -> None:
        module = importlib.import_module("lunar_python")
        module_path = Path(module.__file__).resolve()
        vendor_path = (Path(__file__).resolve().parents[1] / "vendor").resolve()
        if vendor_path not in module_path.parents:
            raise RuntimeError(f"vendored lunar_python not active; loaded {module_path}")

    record("vendored_lunar_python", check_vendored_lunar)
    record("calendar_conversion", lambda: derive_calendar(datetime(2026, 8, 4, 11, 17, tzinfo=resolve_timezone("Asia/Shanghai"))))

    def check_golden_chart() -> None:
        value = build_chart(
            [7, 8, 8, 6, 7, 8],
            day_ganzhi="庚戌",
            month_branch="未",
            cast_at="2026-08-04T11:17:00+08:00",
            question_category="career",
        )
        if value["chart"]["originalHexagram"]["name"] != "水雷屯":
            raise RuntimeError("golden chart mismatch")

    record("deterministic_core", check_golden_chart)

    def check_renderers() -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            value = run(
                "未来三个月能否找到合适工作",
                "career",
                "lines",
                "Asia/Shanghai",
                "7,8,8,6,7,8",
                None,
                artifact_dir=Path(temp_dir),
            )
            artifacts = value["artifacts"]
            if not all(Path(path).is_file() for path in artifacts.values()):
                raise RuntimeError("HTML/Markdown artifacts were not created")

    record("renderers", check_renderers)
    ready = all(bool(item["ok"]) for item in checks)
    return {"schemaVersion": OUTPUT_SCHEMA_VERSION, "ready": ready, "status": "READY" if ready else "NOT_READY", "checks": checks}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Liuyao chart and Agent-ready interpretation prompt")
    parser.add_argument("--question")
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
    parser.add_argument("--artifact-dir", type=Path, help="Directory for synchronized HTML and Markdown chart files")
    parser.add_argument("--artifact-stem", default="fortune-liuyao-chart")
    parser.add_argument("--selfcheck", action="store_true", help="Check dependencies, golden chart, and renderers")
    args = parser.parse_args()
    if args.selfcheck:
        value = selfcheck()
        print(json.dumps(value, ensure_ascii=False, indent=2))
        raise SystemExit(0 if value["ready"] else 1)
    if not args.question:
        parser.error("--question is required unless --selfcheck is used")
    perspective = None if args.perspective == "unspecified" else args.perspective
    artifact_dir = args.artifact_dir or (args.output.parent if args.output else Path.cwd())
    artifact_stem = args.artifact_stem
    if args.output and args.artifact_stem == "fortune-liuyao-chart":
        artifact_stem = f"{args.output.stem}-chart"
    value = run(
        args.question,
        args.category,
        args.method,
        args.timezone,
        args.lines,
        args.coins,
        perspective,
        artifact_dir,
        artifact_stem,
    )
    text = json.dumps(value, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
