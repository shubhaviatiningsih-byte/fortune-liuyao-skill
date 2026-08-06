"""Build one compact Liuyao interpretation packet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SYSTEM_PROMPT = """你是一名重视纳甲、用神、世应、月日动变与应期条件的六爻研究者。
程序提供的排盘和规则事实不可改写；不要重新计算纳甲、六亲、世应、六神、旬空、动变或伏神。
请在方法引导下自由运用稳定的京房纳甲与六爻知识综合判断。
内部判断按此主次完成：先审题取用并处理用神多现，再察用神与世应受月建、日辰的旺衰生克，继而追踪动爻、变爻及飞伏的实际作用路径，最后才用卦名、卦式、爻位和六神辅助取象。静爻、动爻、日月和辅助类象不可等权计票；没有作用到世、应或用神的结构不得升级为主结论。
对外先给明确倾向，以决定性作用链组织主判断，同时覆盖会实质改变结论的其他结构；区分盘面字面事实、规则事实和你的传统推断，不展示冗长的内部推演过程，也不要逐项堆砌与结论无关的术语。
若某项推断依赖特定传统口径，说明该口径即可，不要用大量空泛限制语削弱结论。
输出顺序：直接判断、用神与世应、关键动变、支持与阻力的主次裁决、应期条件、现实建议、文末统一说明。
最终报告必须直接完整写在当前聊天回复中。不得只给摘要、几条压缩结论或要求用户打开 HTML、Markdown、JSON 等文件才能看到解读；HTML 只可作为卦盘附件，Markdown 与 JSON 仅供内部复核。
文末必须原样附上：本内容基于玄学体系生成，仅供文化爱好与思维参考，不构成任何重大人生决策的专业建议。"""


ROUTING_POLICY = """领域路由由当前 Agent 根据用户完整问题的语义选择，只负责加载对应领域方法和提供初始关注点。routingGuidance 不是盘面事实，其中的用神、候选与应期候选均可在综合原问题和完整卦盘后说明理由并调整。chart 与 deterministicRuleFacts 才是不可改写的确定性事实。不要因为路由标签而忽略用户问题的真实目标，也不要向用户追加领域分类问题。"""


DELIVERY_POLICY = """排盘展示不是最终回答。当前聊天回复才是主要交付物，必须继续完成 analysisMethod 要求的综合解读，不得只复述卦名、六亲、给一段简短概括或把全文放进附件；但不要为了篇幅机械扩写。发送前静默确认已经回答所问，解释用神、世应、月日和关键动变如何支持结论，覆盖会实质改变判断的其他结构，并在适用时回答时间趋势和现实建议。敏感分流放行、领域路由、脚本执行、事实校验通过等过程状态属于内部信息，成功时保持静默；只有问题被阻止或发现必须修正的事实冲突时才对用户说明必要结果。传统健康取象属于模型推断，不得伪装成医学诊断，也不得替代现实就医。"""


METHOD_IDS = {
    "career": "liuyao-career-v4",
    "wealth": "liuyao-wealth-v1",
    "relationship": "liuyao-relationship-v1",
    "academic": "liuyao-academic-v1",
    "travel": "liuyao-travel-v1",
    "home": "liuyao-home-v1",
    "legal_risk": "liuyao-legal-v1",
    "relationship_family": "liuyao-family-v1",
}


FALLBACK_METHOD = (
    "确认问题目标与规则层用神；比较用神、世应和月日支持制约；逐条查看动爻变爻、"
    "回头生克、进退、伏神和爻间关系；完成主线后再用卦名、整体格局、爻位和六神辅助取象；"
    "问题含时间范围时，从成事基础、当前病处、解除条件和落实窗口组织应期。"
)


DETERMINISTIC_FACT_FIELDS = (
    "schemaVersion",
    "schoolProfile",
    "shiPosition",
    "yingPosition",
    "lineFacts",
    "hiddenLineFacts",
    "branchRelationFacts",
    "threeHarmonyFacts",
    "punishmentFacts",
    "contextArguments",
)


ROUTING_GUIDANCE_FIELDS = (
    "questionCategory",
    "questionContext",
    "yongshenRelative",
    "selectionStatus",
    "selectionCompleteness",
    "candidates",
    "candidateArguments",
    "ruleDecisions",
    "timingCandidates",
    "timingAnalysis",
)


def _load_method(category: str) -> dict[str, Any]:
    """Load compact domain guidance from the standalone Skill package."""
    methods_path = Path(__file__).resolve().parents[1] / "references" / "domain-methods.json"
    try:
        methods = json.loads(methods_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        methods = {}
    selected = methods.get(category) or methods.get("general")
    if not isinstance(selected, dict):
        return {"methodId": METHOD_IDS.get(category, "liuyao-general-v1"), "text": FALLBACK_METHOD, "steps": []}
    return {
        "methodId": selected.get("methodId", METHOD_IDS.get(category, "liuyao-general-v1")),
        "text": selected.get("instruction", FALLBACK_METHOD),
        "focus": selected.get("focus", []),
        "steps": [],
    }


def _select_fields(analysis: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    return {key: analysis[key] for key in fields if key in analysis}


def build_packet(chart_response: dict[str, Any]) -> dict[str, Any]:
    chart_response = chart_response.get("result") or chart_response
    if not isinstance(chart_response, dict):
        raise ValueError("chart response must be an object or contain an object at 'result'")
    chart = chart_response.get("chart")
    if not isinstance(chart, dict):
        raise ValueError("chart response must contain an object at 'chart'")
    analysis = chart_response.get("analysis")
    if not isinstance(analysis, dict):
        analysis = chart_response.get("deterministicRuleFacts")
    if not isinstance(analysis, dict):
        analysis = {}

    category = str(
        analysis.get("questionCategory")
        or (analysis.get("questionContext") or {}).get("domain")
        or "general"
    )
    payload = {
        "questionContext": analysis.get("questionContext"),
        "calendar": chart_response.get("calendar"),
        "castingAudit": chart_response.get("castingAudit"),
        "chart": chart,
        "deterministicRuleFacts": _select_fields(analysis, DETERMINISTIC_FACT_FIELDS),
        "routingGuidance": {
            **_select_fields(analysis, ROUTING_GUIDANCE_FIELDS),
            "authority": "advisory",
            "instruction": (
                "领域由当前 Agent 根据用户完整问题作语义分类，只用于选择分析方法和初始关注点。"
                "其中的用神、候选与应期候选不是盘面事实；解读时可依据原问题和完整卦盘说明理由后调整，"
                "但不得改写 chart 与 deterministicRuleFacts。"
            ),
        },
        "analysisMethod": _load_method(category),
    }
    return {
        "schemaVersion": "fortune-liuyao-interpretation-packet.v1",
        "pipeline": [
            "deterministic_chart",
            "deterministic_rule_facts",
            "domain_method_guidance",
            "free_model_interpretation",
            "fact_consistency_review",
        ],
        "chartVersions": {
            "schemaVersion": chart.get("schemaVersion"),
            "transformationRuleVersion": chart.get("transformationRuleVersion"),
            "schoolProfile": chart.get("schoolProfile"),
        },
        "messages": [
            {"role": "system", "content": f"{SYSTEM_PROMPT}\n{ROUTING_POLICY}\n{DELIVERY_POLICY}"},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chart", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    source = json.loads(args.chart.read_text(encoding="utf-8"))
    packet = build_packet(source)
    args.output.write_text(json.dumps(packet, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
