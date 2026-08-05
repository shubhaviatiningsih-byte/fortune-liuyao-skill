"""Standalone Wenwang Najia Liuyao chart and rule-fact engine.

It accepts bottom-up 6/7/8/9 line values and explicit calendar facts, and
returns plain JSON-compatible dictionaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Iterable


STEMS = tuple("甲乙丙丁戊己庚辛壬癸")
BRANCHES = tuple("子丑寅卯辰巳午未申酉戌亥")

TRIGRAMS = {
    (1, 1, 1): ("乾", "金"), (1, 1, 0): ("兑", "金"),
    (1, 0, 1): ("离", "火"), (1, 0, 0): ("震", "木"),
    (0, 1, 1): ("巽", "木"), (0, 1, 0): ("坎", "水"),
    (0, 0, 1): ("艮", "土"), (0, 0, 0): ("坤", "土"),
}

HEXAGRAM_NAMES = {
    "乾": {"乾": "乾为天", "兑": "天泽履", "离": "天火同人", "震": "天雷无妄", "巽": "天风姤", "坎": "天水讼", "艮": "天山遁", "坤": "天地否"},
    "兑": {"乾": "泽天夬", "兑": "兑为泽", "离": "泽火革", "震": "泽雷随", "巽": "泽风大过", "坎": "泽水困", "艮": "泽山咸", "坤": "泽地萃"},
    "离": {"乾": "火天大有", "兑": "火泽睽", "离": "离为火", "震": "火雷噬嗑", "巽": "火风鼎", "坎": "火水未济", "艮": "火山旅", "坤": "火地晋"},
    "震": {"乾": "雷天大壮", "兑": "雷泽归妹", "离": "雷火丰", "震": "震为雷", "巽": "雷风恒", "坎": "雷水解", "艮": "雷山小过", "坤": "雷地豫"},
    "巽": {"乾": "风天小畜", "兑": "风泽中孚", "离": "风火家人", "震": "风雷益", "巽": "巽为风", "坎": "风水涣", "艮": "风山渐", "坤": "风地观"},
    "坎": {"乾": "水天需", "兑": "水泽节", "离": "水火既济", "震": "水雷屯", "巽": "水风井", "坎": "坎为水", "艮": "水山蹇", "坤": "水地比"},
    "艮": {"乾": "山天大畜", "兑": "山泽损", "离": "山火贲", "震": "山雷颐", "巽": "山风蛊", "坎": "山水蒙", "艮": "艮为山", "坤": "山地剥"},
    "坤": {"乾": "地天泰", "兑": "地泽临", "离": "地火明夷", "震": "地雷复", "巽": "地风升", "坎": "地水师", "艮": "地山谦", "坤": "坤为地"},
}

NAJIA = {
    "乾": (("甲", ("子", "寅", "辰")), ("壬", ("午", "申", "戌"))),
    "坤": (("乙", ("未", "巳", "卯")), ("癸", ("丑", "亥", "酉"))),
    "震": (("庚", ("子", "寅", "辰")), ("庚", ("午", "申", "戌"))),
    "巽": (("辛", ("丑", "亥", "酉")), ("辛", ("未", "巳", "卯"))),
    "坎": (("戊", ("寅", "辰", "午")), ("戊", ("申", "戌", "子"))),
    "离": (("己", ("卯", "丑", "亥")), ("己", ("酉", "未", "巳"))),
    "艮": (("丙", ("辰", "午", "申")), ("丙", ("戌", "子", "寅"))),
    "兑": (("丁", ("巳", "卯", "丑")), ("丁", ("亥", "酉", "未"))),
}

BRANCH_ELEMENTS = {
    "子": "水", "亥": "水", "寅": "木", "卯": "木", "巳": "火", "午": "火",
    "申": "金", "酉": "金", "辰": "土", "戌": "土", "丑": "土", "未": "土",
}
GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
SIX_SPIRITS = ("青龙", "朱雀", "勾陈", "腾蛇", "白虎", "玄武")
SPIRIT_START = {"甲": 0, "乙": 0, "丙": 1, "丁": 1, "戊": 2, "己": 3, "庚": 4, "辛": 4, "壬": 5, "癸": 5}

PALACE_PATTERNS = {
    (0, 0, 0, 0, 0, 0): ("本宫", 6),
    (1, 0, 0, 0, 0, 0): ("一世", 1),
    (1, 1, 0, 0, 0, 0): ("二世", 2),
    (1, 1, 1, 0, 0, 0): ("三世", 3),
    (1, 1, 1, 1, 0, 0): ("四世", 4),
    (1, 1, 1, 1, 1, 0): ("五世", 5),
    (1, 1, 1, 0, 1, 0): ("游魂", 4),
    (0, 0, 0, 0, 1, 0): ("归魂", 3),
}

ADVANCE_BRANCH = {"亥": "子", "寅": "卯", "巳": "午", "申": "酉", "丑": "辰", "辰": "未", "未": "戌", "戌": "丑"}
RETREAT_BRANCH = {target: source for source, target in ADVANCE_BRANCH.items()}
CLASH = {"子": "午", "午": "子", "丑": "未", "未": "丑", "寅": "申", "申": "寅", "卯": "酉", "酉": "卯", "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳"}
HARMONY = {"子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯", "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午"}
HARM = {"子": "未", "未": "子", "丑": "午", "午": "丑", "寅": "巳", "巳": "寅", "卯": "辰", "辰": "卯", "申": "亥", "亥": "申", "酉": "戌", "戌": "酉"}
PUNISH_GROUPS = (("寅", "巳", "申"), ("丑", "戌", "未"), ("子", "卯"))
SELF_PUNISH = {"辰", "午", "酉", "亥"}
THREE_HARMONY = {
    "water": ("申", "子", "辰"), "wood": ("亥", "卯", "未"),
    "fire": ("寅", "午", "戌"), "metal": ("巳", "酉", "丑"),
}
SIX_CLASH_HEXAGRAMS = {"乾为天", "兑为泽", "离为火", "震为雷", "巽为风", "坎为水", "艮为山", "坤为地", "天雷无妄", "雷天大壮"}
SIX_HARMONY_HEXAGRAMS = {"天地否", "地天泰", "水泽节", "泽水困", "山火贲", "火山旅", "雷地豫", "地雷复"}

DOMAIN_YONGSHEN = {
    "career": "官鬼", "wealth": "妻财", "academic": "父母", "exam": "父母",
    "travel": "世爻", "home": "父母", "legal_risk": "官鬼",
}


def validate_lines(values: Iterable[int]) -> list[int]:
    lines = [int(value) for value in values]
    if len(lines) != 6 or any(value not in (6, 7, 8, 9) for value in lines):
        raise ValueError("linesBottomUp must contain exactly six values from 6, 7, 8, 9")
    return lines


def derive_calendar(moment: datetime, day_boundary_policy: str = "zi_hour") -> dict[str, str]:
    try:
        from lunar_python import Solar
    except ImportError as exc:
        raise RuntimeError("calendar conversion requires lunar_python==1.4.8") from exc
    day_moment = moment + timedelta(days=1) if day_boundary_policy == "zi_hour" and moment.hour >= 23 else moment
    day_lunar = Solar.fromYmdHms(day_moment.year, day_moment.month, day_moment.day, day_moment.hour, day_moment.minute, day_moment.second).getLunar()
    month_lunar = Solar.fromYmdHms(moment.year, moment.month, moment.day, moment.hour, moment.minute, moment.second).getLunar()
    previous_jieqi = month_lunar.getPrevJieQi()
    next_jieqi = month_lunar.getNextJieQi()
    return {
        "localWallClock": moment.replace(tzinfo=None).isoformat(),
        "timezone": getattr(moment.tzinfo, "key", None) or str(moment.tzinfo),
        "dayGanzhi": day_lunar.getEightChar().getDay(),
        "monthBranch": month_lunar.getEightChar().getMonthZhi(),
        "monthGanzhi": month_lunar.getEightChar().getMonth(),
        "yearGanzhi": month_lunar.getEightChar().getYear(),
        "timeGanzhi": month_lunar.getEightChar().getTime(),
        "lunarDateText": f"农历{month_lunar.getYearInChinese()}年{month_lunar.getMonthInChinese()}月{month_lunar.getDayInChinese()}",
        "solarTermWindow": {
            "previous": {"name": previous_jieqi.getName(), "date": str(previous_jieqi.getSolar())},
            "next": {"name": next_jieqi.getName(), "date": str(next_jieqi.getSolar())},
        },
        "dayBoundaryPolicy": day_boundary_policy,
        "calendarLibrary": "lunar_python",
        "calendarLibraryVersion": "1.4.8",
    }


def _hexagram(bits: tuple[int, ...]) -> dict[str, Any]:
    lower_name, lower_element = TRIGRAMS[bits[:3]]
    upper_name, upper_element = TRIGRAMS[bits[3:]]
    return {
        "name": HEXAGRAM_NAMES[upper_name][lower_name],
        "upperTrigram": {"name": upper_name, "element": upper_element},
        "lowerTrigram": {"name": lower_name, "element": lower_element},
    }


def _palace(bits: tuple[int, ...]) -> tuple[str, str, str, int]:
    for pure_bits, (name, element) in TRIGRAMS.items():
        difference = tuple(left ^ right for left, right in zip(bits, pure_bits + pure_bits))
        if difference in PALACE_PATTERNS:
            stage, shi = PALACE_PATTERNS[difference]
            return name, element, stage, shi
    raise ValueError("hexagram does not match a Jing Fang eight-palace pattern")


def _six_relative(palace_element: str, line_element: str) -> str:
    if line_element == palace_element:
        return "兄弟"
    if GENERATES[line_element] == palace_element:
        return "父母"
    if GENERATES[palace_element] == line_element:
        return "子孙"
    if CONTROLS[line_element] == palace_element:
        return "官鬼"
    return "妻财"


def _najia(hexagram: dict[str, Any], position: int) -> tuple[str, str, str]:
    trigram = hexagram["lowerTrigram"]["name"] if position <= 3 else hexagram["upperTrigram"]["name"]
    side = 0 if position <= 3 else 1
    index = position - 1 if position <= 3 else position - 4
    stem, branches = NAJIA[trigram][side]
    branch = branches[index]
    return stem, branch, BRANCH_ELEMENTS[branch]


def _void_branches(day_ganzhi: str) -> list[str]:
    if len(day_ganzhi) != 2 or day_ganzhi[0] not in STEMS or day_ganzhi[1] not in BRANCHES:
        raise ValueError("dayGanzhi must be a valid stem-branch pair")
    start = (BRANCHES.index(day_ganzhi[1]) - STEMS.index(day_ganzhi[0])) % 12
    return [BRANCHES[(start - 2) % 12], BRANCHES[(start - 1) % 12]]


def _element_relation(actor: str, target: str) -> str:
    if actor == target:
        return "same_element"
    if GENERATES[actor] == target:
        return "generates"
    if CONTROLS[actor] == target:
        return "controls"
    if GENERATES[target] == actor:
        return "generated_by"
    return "controlled_by"


def _return_relation(changed: str, original: str) -> str:
    if changed == original:
        return "same_element"
    if GENERATES[changed] == original:
        return "generates_original"
    if CONTROLS[changed] == original:
        return "controls_original"
    return "other"


def _flying_hidden_relation(flying: str, hidden: str) -> str:
    if flying == hidden:
        return "same_element"
    if GENERATES[flying] == hidden:
        return "generates_hidden"
    if CONTROLS[flying] == hidden:
        return "controls_hidden"
    if GENERATES[hidden] == flying:
        return "generated_by_hidden"
    return "controlled_by_hidden"


def _branch_relations(left: str, right: str) -> list[str]:
    result: list[str] = []
    if CLASH[left] == right:
        result.append("clash")
    if HARMONY[left] == right:
        result.append("harmony")
    if HARM[left] == right:
        result.append("harm")
    if left == right and left in SELF_PUNISH:
        result.append("self_punishment")
    if any(left in group and right in group and left != right for group in PUNISH_GROUPS):
        result.append("punishment_component")
    return result


def _pattern(name: str) -> str:
    if name in SIX_CLASH_HEXAGRAMS:
        return "six_clash"
    if name in SIX_HARMONY_HEXAGRAMS:
        return "six_harmony"
    return "ordinary"


def _strength_status(signals: list[dict[str, str]]) -> str:
    support = sum(item["direction"] == "support" for item in signals)
    pressure = sum(item["direction"] == "pressure" for item in signals)
    if support and pressure:
        return "contested"
    if support:
        return "supported"
    if pressure:
        return "weakened"
    return "neutral"


def _timing_candidates(candidate: dict[str, Any], month_branch: str) -> list[dict[str, Any]]:
    branch = candidate["najiaBranch"]
    result: list[dict[str, Any]] = []
    if candidate.get("isVoid"):
        result.extend([
            {"mechanism": "void_fill", "triggerBranch": branch, "meaning": "用神填实候选"},
            {"mechanism": "void_clash", "triggerBranch": CLASH[branch], "meaning": "冲空候选"},
        ])
    if candidate.get("isMonthBreak"):
        result.extend([
            {"mechanism": "month_break_value", "triggerBranch": branch, "meaning": "月破逢值候选"},
            {"mechanism": "month_break_harmony", "triggerBranch": HARMONY[branch], "meaning": "月破逢合候选"},
            {"mechanism": "month_break_exit", "triggerBranch": CLASH[month_branch], "meaning": "出当前月令候选"},
        ])
    if candidate.get("moving"):
        result.extend([
            {"mechanism": "moving_value", "triggerBranch": branch, "meaning": "动爻逢值候选"},
            {"mechanism": "moving_harmony", "triggerBranch": HARMONY[branch], "meaning": "动爻逢合候选"},
        ])
    if candidate.get("hidden"):
        flying = candidate.get("flyingBranch")
        if flying:
            result.append({"mechanism": "hidden_release", "triggerBranch": CLASH[flying], "meaning": "冲飞出伏候选"})
    dedup: dict[tuple[str, str], dict[str, Any]] = {}
    for item in result:
        dedup[(item["mechanism"], item["triggerBranch"])] = item
    return list(dedup.values())


def build_chart(
    lines_bottom_up: Iterable[int],
    *,
    day_ganzhi: str,
    month_branch: str,
    cast_at: str,
    question_category: str = "general",
    question_subtype: str | None = None,
    question_text: str | None = None,
    question_perspective: str | None = None,
) -> dict[str, Any]:
    values = validate_lines(lines_bottom_up)
    if month_branch not in BRANCHES:
        raise ValueError("monthBranch must be a valid earthly branch")
    original_bits = tuple(1 if value in (7, 9) else 0 for value in values)
    changed_bits = tuple(bit ^ int(value in (6, 9)) for bit, value in zip(original_bits, values))
    original = _hexagram(original_bits)
    changed = _hexagram(changed_bits)
    palace, palace_element, palace_stage, shi_position = _palace(original_bits)
    ying_position = ((shi_position + 2) % 6) + 1
    void_branches = _void_branches(day_ganzhi)
    day_branch = day_ganzhi[1]

    lines: list[dict[str, Any]] = []
    for index, (value, bit, changed_bit) in enumerate(zip(values, original_bits, changed_bits)):
        position = index + 1
        stem, branch, element = _najia(original, position)
        month_relation = _element_relation(BRANCH_ELEMENTS[month_branch], element)
        day_relation = _element_relation(BRANCH_ELEMENTS[day_branch], element)
        signals: list[dict[str, str]] = []
        for source, relation in (("month", month_relation), ("day", day_relation)):
            if relation in ("same_element", "generates"):
                signals.append({"source": source, "relation": relation, "direction": "support"})
            elif relation == "controls":
                signals.append({"source": source, "relation": relation, "direction": "pressure"})
        changed_line = None
        if value in (6, 9):
            c_stem, c_branch, c_element = _najia(changed, position)
            return_relation = _return_relation(c_element, element)
            advance_retreat = "advance" if ADVANCE_BRANCH.get(branch) == c_branch else "retreat" if RETREAT_BRANCH.get(branch) == c_branch else "none"
            changed_line = {
                "yinYang": "阳" if changed_bit else "阴",
                "najiaStem": c_stem, "najiaBranch": c_branch, "najiaElement": c_element,
                "sixRelative": _six_relative(palace_element, c_element),
                "returnRelation": return_relation,
                "advanceRetreat": advance_retreat,
                "isVoid": c_branch in void_branches,
            }
        lines.append({
            "position": position, "value": value, "yinYang": "阳" if bit else "阴",
            "moving": value in (6, 9), "changedYinYang": "阳" if changed_bit else "阴",
            "isShi": position == shi_position, "isYing": position == ying_position,
            "najiaStem": stem, "najiaBranch": branch, "najiaElement": element,
            "sixRelative": _six_relative(palace_element, element),
            "sixSpirit": SIX_SPIRITS[(SPIRIT_START[day_ganzhi[0]] + index) % 6],
            "isVoid": branch in void_branches,
            "isMonthBreak": CLASH[month_branch] == branch,
            "isDayClash": CLASH[day_branch] == branch,
            "monthRelation": month_relation, "dayRelation": day_relation,
            "strengthEvidence": {"status": _strength_status(signals), "signals": signals},
            "changedLine": changed_line,
        })

    pure_bits = next(bits for bits, values_ in TRIGRAMS.items() if values_[0] == palace)
    pure = _hexagram(pure_bits + pure_bits)
    visible_relatives = {line["sixRelative"] for line in lines}
    hidden_lines: list[dict[str, Any]] = []
    for position in range(1, 7):
        stem, branch, element = _najia(pure, position)
        relative = _six_relative(palace_element, element)
        if relative in visible_relatives:
            continue
        flying = lines[position - 1]
        hidden_lines.append({
            "position": position, "hidden": True,
            "najiaStem": stem, "najiaBranch": branch, "najiaElement": element,
            "sixRelative": relative,
            "flyingStem": flying["najiaStem"], "flyingBranch": flying["najiaBranch"],
            "flyingElement": flying["najiaElement"], "flyingSixRelative": flying["sixRelative"],
            "flyingToHiddenRelation": _flying_hidden_relation(flying["najiaElement"], element),
            "isVoid": branch in void_branches,
            "isMonthBreak": CLASH[month_branch] == branch,
            "isDayClash": CLASH[day_branch] == branch,
        })

    relations: list[dict[str, Any]] = []
    for left_index in range(6):
        for right_index in range(left_index + 1, 6):
            for relation in _branch_relations(lines[left_index]["najiaBranch"], lines[right_index]["najiaBranch"]):
                relations.append({"leftPosition": left_index + 1, "rightPosition": right_index + 1, "relation": relation})

    branch_sources: dict[str, list[dict[str, Any]]] = {branch: [] for branch in BRANCHES}
    for line in lines:
        branch_sources[line["najiaBranch"]].append({"source": "line", "position": line["position"], "moving": line["moving"]})
    branch_sources[day_branch].append({"source": "day"})
    branch_sources[month_branch].append({"source": "month"})
    harmony_facts: list[dict[str, Any]] = []
    for group_name, group in THREE_HARMONY.items():
        present = [branch for branch in group if branch_sources[branch]]
        if len(present) >= 2:
            harmony_facts.append({
                "group": group_name, "branches": list(group), "presentBranches": present,
                "missingBranches": [branch for branch in group if branch not in present],
                "complete": len(present) == 3,
                "sources": {branch: branch_sources[branch] for branch in present},
                "conclusionScope": "structure_candidate_only",
            })
    punishment_facts = [item for item in relations if "punishment" in item["relation"]]

    original_pattern = _pattern(original["name"])
    changed_pattern = _pattern(changed["name"])
    transition = {
        ("six_clash", "six_harmony"): "six_clash_to_six_harmony",
        ("six_harmony", "six_clash"): "six_harmony_to_six_clash",
        ("six_clash", "six_clash"): "six_clash_to_six_clash",
        ("six_harmony", "six_harmony"): "six_harmony_to_six_harmony",
    }.get((original_pattern, changed_pattern), "other")

    if question_category == "relationship":
        yongshen = "官鬼" if question_perspective in ("female", "woman", "女") else "妻财" if question_perspective in ("male", "man", "男") else None
    else:
        yongshen = DOMAIN_YONGSHEN.get(question_category)
    candidates: list[dict[str, Any]] = []
    if yongshen and yongshen != "世爻":
        candidates.extend({**line, "hidden": False} for line in lines if line["sixRelative"] == yongshen)
        candidates.extend(line for line in hidden_lines if line["sixRelative"] == yongshen)
    elif yongshen == "世爻":
        candidates.append({**lines[shi_position - 1], "hidden": False})
    for candidate in candidates:
        candidate["timingCandidates"] = _timing_candidates(candidate, month_branch)

    candidate_arguments: list[dict[str, Any]] = []
    for candidate in candidates:
        strengths = (candidate.get("strengthEvidence") or {}).get("signals", [])
        supports = [item for item in strengths if item.get("direction") == "support"]
        limitations: list[str] = []
        if candidate.get("hidden"):
            limitations.append("hidden")
        if candidate.get("isVoid"):
            limitations.append("void")
        if candidate.get("isMonthBreak"):
            limitations.append("month_break")
        if candidate.get("isDayClash"):
            limitations.append("day_clash")
        candidate_arguments.append({
            "candidateRef": f"{'hidden' if candidate.get('hidden') else 'line'}:{candidate['position']}",
            "position": candidate["position"], "hidden": bool(candidate.get("hidden")),
            "moving": bool(candidate.get("moving")),
            "strengthStatus": (candidate.get("strengthEvidence") or {}).get("status", "not_computed_for_hidden"),
            "supportingSignals": supports, "limitingStates": limitations,
            "conclusionScope": "candidate_comparison_only_not_outcome",
        })

    context_arguments = {
        "shi": {"position": shi_position, "line": lines[shi_position - 1]},
        "ying": {"position": ying_position, "line": lines[ying_position - 1]},
        "shiYingBranchRelations": _branch_relations(lines[shi_position - 1]["najiaBranch"], lines[ying_position - 1]["najiaBranch"]),
    }

    chart = {
        "schemaVersion": "fortune-liuyao-chart.v1",
        "schoolProfile": "wenwang_najia_v1",
        "transformationRuleVersion": "standalone-transformations.v1",
        "castAt": cast_at, "dayGanzhi": day_ganzhi, "monthBranch": month_branch,
        "voidBranches": void_branches,
        "originalHexagram": original, "changedHexagram": changed,
        "originalHexagramPattern": original_pattern, "changedHexagramPattern": changed_pattern,
        "hexagramPatternTransition": transition,
        "palace": palace, "palaceElement": palace_element, "palaceStage": palace_stage,
        "shiPosition": shi_position, "yingPosition": ying_position,
        "hiddenLines": hidden_lines, "lines": lines,
    }
    analysis = {
        "schemaVersion": "fortune-liuyao-rule-facts.v1",
        "questionCategory": question_category,
        "questionContext": {"domain": question_category, "subtype": question_subtype, "question": question_text, "perspective": question_perspective},
        "schoolProfile": "wenwang_najia_v1",
        "yongshenRelative": yongshen,
        "selectionStatus": "candidates_identified" if candidates else "route_requires_context",
        "selectionCompleteness": "complete" if yongshen else "needs_clarification",
        "candidates": candidates,
        "shiPosition": shi_position, "yingPosition": ying_position,
        "lineFacts": lines, "hiddenLineFacts": hidden_lines,
        "branchRelationFacts": relations,
        "threeHarmonyFacts": harmony_facts,
        "punishmentFacts": punishment_facts,
        "candidateArguments": candidate_arguments,
        "contextArguments": context_arguments,
        "ruleDecisions": [
            {"ruleId": "role-route", "assertion": f"question target relative: {yongshen}", "conclusionScope": "role_mapping_only"}
        ] if yongshen else [],
        "timingCandidates": [item for candidate in candidates for item in candidate.get("timingCandidates", [])],
        "timingAnalysis": {
            "candidateCount": sum(len(candidate.get("timingCandidates", [])) for candidate in candidates),
            "calendarConversionBoundary": "branch_candidates_only",
            "conclusionScope": "conditional_timing_candidates_not_guaranteed_dates",
        },
    }
    return {
        "schemaVersion": "fortune-liuyao-runtime.v1",
        "castingAudit": {"linesBottomUp": values, "order": "bottom_up", "movingValues": [6, 9]},
        "chart": chart,
        "analysis": analysis,
        "deterministicRuleFacts": analysis,
    }
