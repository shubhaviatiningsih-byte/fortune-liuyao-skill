"""Render a portable Markdown Liuyao chart when HTML artifacts cannot be shown."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _line_glyph(line: dict[str, object]) -> str:
    return "━━━━━━" if line.get("yinYang") == "阳" else "━━　━━"


def _relation_name(value: object) -> str:
    return {
        "generates_original": "回头生",
        "controls_original": "回头克",
        "advance": "化进",
        "retreat": "化退",
        "other": "动变",
        "none": "",
    }.get(str(value), str(value or ""))


def _hexagram_pair(chart: dict[str, object]) -> list[str]:
    original = chart["originalHexagram"]["name"]
    changed = chart["changedHexagram"]["name"]
    result = ["```text", f"本卦 · {original}          变卦 · {changed}"]
    for line in reversed(chart.get("lines", [])):
        changed_line = line.get("changedLine") or line
        result.append(f"{_line_glyph(line):<12}    {_line_glyph(changed_line)}")
    result.append("```")
    return result


def render(data: dict[str, object]) -> str:
    source = data.get("result") or data
    chart = source.get("chart", source)
    analysis = source.get("analysis") or source.get("deterministicRuleFacts") or {}
    question = (analysis.get("questionContext") or {}).get("question") or "未记录"
    rows = [
        "# Fortune 六爻卦盘",
        "",
        f"**所问：** {question}",
        "",
        f"**本卦：** {chart['originalHexagram']['name']}　→　**变卦：** {chart['changedHexagram']['name']}",
        *_hexagram_pair(chart),
        f"**卦宫：** {chart['palace']}宫 · {chart['palaceElement']}　　**世应：** 世{chart['shiPosition']} · 应{chart['yingPosition']}",
        f"**月日：** 月建{chart['monthBranch']} · {chart['dayGanzhi']}日　　**旬空：** {'、'.join(chart['voidBranches'])}",
        "",
        "| 爻位 | 六神 | 六亲纳甲 | 爻象 | 标记 | 变爻 |",
        "|---:|---|---|---|---|---|",
    ]
    for line in reversed(chart.get("lines", [])):
        marks = " ".join(filter(None, ["世" if line.get("isShi") else "", "应" if line.get("isYing") else "", "动" if line.get("moving") else "", "空" if line.get("isVoid") else "", "月破" if line.get("isMonthBreak") else ""])) or "—"
        changed = line.get("changedLine")
        changed_text = "—" if not changed else f"{changed['sixRelative']}{changed['najiaStem']}{changed['najiaBranch']} · {_relation_name(changed['returnRelation'])}"
        rows.append(f"| {line['position']} | {line['sixSpirit']} | {line['sixRelative']}{line['najiaStem']}{line['najiaBranch']} | {_line_glyph(line)} | {marks} | {changed_text} |")
    hidden_lines = chart.get("hiddenLines") or []
    if hidden_lines:
        rows.extend(["", "**伏神：**"])
        for hidden in hidden_lines:
            states = " ".join(filter(None, ["空" if hidden.get("isVoid") else "", "月破" if hidden.get("isMonthBreak") else "", "日冲" if hidden.get("isDayClash") else ""]))
            rows.append(
                f"- 第{hidden['position']}爻伏神：{hidden['sixRelative']}{hidden['najiaStem']}{hidden['najiaBranch']} · "
                f"飞神{hidden['flyingSixRelative']}{hidden['flyingStem']}{hidden['flyingBranch']}"
                f"{' · '+states if states else ''}"
            )
    candidates = analysis.get("candidates") or []
    candidate_text = "；".join(f"{'伏神' if row.get('hidden') else '第'+str(row.get('position'))+'爻'} {row.get('sixRelative')}{row.get('najiaBranch')}" for row in candidates) or "待结合问题确认"
    rows.extend(["", f"**用神主线：** {analysis.get('yongshenRelative') or '待确认'}", f"**用神候选：** {candidate_text}", "", "> 本内容基于玄学体系生成，仅供文化爱好与思维参考，不构成任何重大人生决策的专业建议。"])
    return "\n".join(rows) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chart", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    text = render(json.loads(args.chart.read_text(encoding="utf-8")))
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
