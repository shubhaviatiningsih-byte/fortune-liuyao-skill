"""Deterministic pre-chart safety routing for the standalone Skill."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class SensitiveDecision:
    category: str
    allowed: bool
    urgent: bool
    message: str


TERMS = {
    "self_harm_or_violence": ("想自杀", "不想活", "自残", "伤害自己", "杀人", "伤害别人"),
    "pregnancy_or_child_health": ("怀孕", "有孕", "胎儿", "母婴", "保胎", "流产", "预产期", "男胎", "女胎", "胎儿性别"),
    "medical_or_safety": ("重病", "癌症", "疾病", "确诊", "手术", "病情", "能活多久", "生死", "康复", "用药", "治疗方案", "健康风险"),
    "missing_person_or_crime": ("失踪", "下落", "被绑架", "凶手", "犯罪", "是否还活着"),
    "high_stakes_financial_or_legal": ("倾家荡产", "全部身家", "借高利贷", "官司一定赢", "逃税"),
}
URGENT = ("大出血", "出血不止", "剧烈腹痛", "呼吸困难", "昏迷", "失去意识", "想自杀", "自残")
MESSAGES = {
    "self_harm_or_violence": "请先不要独自处理，也不要用占卜判断后果；立即联系当地急救或危机支持，并请可信赖的人陪在身边。",
    "pregnancy_or_child_health": "不能用卦象判断怀孕、胎儿性别或母婴安危，请联系产科或正规医疗机构。",
    "medical_or_safety": "疾病、治疗效果和生死不能由卦象可靠判断，请联系正规医疗机构。",
    "missing_person_or_crime": "卦象不能确认失踪者下落、生死或犯罪事实，请尽快联系警方或救援机构。",
    "high_stakes_financial_or_legal": "涉及全部身家、借贷或诉讼的重大决定不应由卦象替代，请咨询专业人士。",
}


def classify(question: str) -> SensitiveDecision:
    text = question.strip()
    urgent = any(term in text for term in URGENT)
    for category, terms in TERMS.items():
        if any(term in text for term in terms):
            prefix = "你描述的情况可能需要立即处理。" if urgent else ""
            return SensitiveDecision(category, False, urgent, prefix + MESSAGES[category])
    return SensitiveDecision("not_sensitive", True, False, "")


def classify_dict(question: str) -> dict[str, object]:
    return asdict(classify(question))
