"""Small golden regression set for the standalone Skill runtime."""

from cast_lines import _automatic_cast, _manual_cast
from cast_one_line import cast_one
from build_model_packet import ROUTING_POLICY, SYSTEM_PROMPT, _load_method
from classify_sensitive import classify
from liuyao_core import build_chart
from render_chart_text import render
from run_liuyao import run
from verify_facts import verify_report


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    tun = build_chart(
        [7, 8, 8, 6, 7, 8],
        day_ganzhi="庚戌", month_branch="未",
        cast_at="2026-08-04T11:17:00+08:00",
        question_category="career", question_subtype="job_search",
    )
    chart = tun["chart"]
    check(chart["originalHexagram"]["name"] == "水雷屯", "original hexagram mismatch")
    check(chart["changedHexagram"]["name"] == "泽雷随", "changed hexagram mismatch")
    check((chart["palace"], chart["shiPosition"], chart["yingPosition"]) == ("坎", 2, 5), "palace/shi/ying mismatch")
    check(chart["voidBranches"] == ["寅", "卯"], "void branches mismatch")
    check(chart["lines"][3]["changedLine"]["returnRelation"] == "other", "changed relation mismatch")
    check(chart["hiddenLines"][0]["sixRelative"] == "妻财", "hidden relative mismatch")
    check(len(tun["analysis"]["candidates"]) == 2, "career yongshen candidates mismatch")

    qian = build_chart(
        [7, 7, 7, 7, 7, 7],
        day_ganzhi="甲子", month_branch="子",
        cast_at="2026-01-01T12:00:00+08:00",
    )["chart"]
    check(qian["originalHexagram"]["name"] == "乾为天", "pure Qian mismatch")
    check((qian["palace"], qian["shiPosition"], qian["yingPosition"]) == ("乾", 6, 3), "pure Qian palace mismatch")

    kun_change = build_chart(
        [6, 8, 8, 8, 8, 8],
        day_ganzhi="甲子", month_branch="子",
        cast_at="2026-01-01T12:00:00+08:00",
    )["chart"]
    check(kun_change["originalHexagram"]["name"] == "坤为地", "pure Kun mismatch")
    check(kun_change["changedHexagram"]["name"] == "地雷复", "Kun-to-Fu mismatch")

    manual = _manual_cast("正反反/正正反/反反反/正反反/正正正/正正反")
    check([row["value"] for row in manual] == [7, 8, 6, 7, 9, 8], "manual casting mismatch")

    automatic = _automatic_cast()
    check(len(automatic) == 6 and all(row["value"] in (6, 7, 8, 9) for row in automatic), "automatic casting mismatch")

    markdown = render(tun)
    check("水雷屯" in markdown and "泽雷随" in markdown and "| 爻位 |" in markdown and "伏神" in markdown, "Markdown chart mismatch")
    check("本内容基于玄学体系生成" in markdown, "Markdown safety disclaimer mismatch")
    check(_load_method("career")["methodId"] == "liuyao-career-v4", "career method version mismatch")
    check("先审题取用并处理用神多现" in SYSTEM_PROMPT, "interpretation order prompt mismatch")
    check("不可等权计票" in SYSTEM_PROMPT, "evidence priority prompt mismatch")
    check(classify("未来三个月求职是否顺利").allowed, "ordinary question was blocked")
    check(not classify("怀孕后孩子会不会健康").allowed, "sensitive pregnancy question was not blocked")
    check(classify("孩子在学校健康快乐吗").allowed, "ordinary child wellbeing question was over-blocked")
    adversarial = verify_report("本卦为乾为天。世爻在五爻。初爻为官鬼。", tun)
    check(not adversarial["accepted"] and len(adversarial["errors"]) >= 3, "fabricated chart facts escaped audit")
    natural_adversarial = verify_report("二爻妻财卯木静。", tun)
    check(not natural_adversarial["accepted"], "natural no-copula line-relative claim escaped audit")
    inference = verify_report("此事可能先难后易，辰日或有机会，仍需结合现实条件。", tun)
    check(inference["accepted"], "traditional inference was incorrectly constrained")
    one_shot = run("未来三个月能否找到合适工作", "career", "lines", "Asia/Shanghai", "7,8,8,6,7,8", None)
    check(one_shot["result"]["analysis"]["questionContext"]["domain"] == "career", "one-shot Agent route mismatch")
    check(one_shot["result"]["chart"]["originalHexagram"]["name"] == "水雷屯", "one-shot chart mismatch")
    check(len(one_shot["prompt"]) > 1000, "one-shot Agent prompt missing")
    wealth_route = run("我开了个网店，这两个月能不能回本盈利？", "wealth", "lines", "Asia/Shanghai", "7,8,8,6,7,8", None)
    check("liuyao-wealth-v1" in wealth_route["prompt"], "Agent-selected wealth method was not loaded")
    check('"authority": "advisory"' in wealth_route["prompt"], "routing guidance was not marked advisory")
    check('"yongshenRelative"' not in wealth_route["prompt"].split('"routingGuidance"', 1)[0], "routing-derived yongshen leaked into deterministic facts")
    forced_career = run("我开了个网店，这两个月能不能回本盈利？", "career", "lines", "Asia/Shanghai", "7,8,8,6,7,8", None)
    check("liuyao-career-v4" in forced_career["prompt"], "question keywords overrode the Agent-selected route")
    check("不是盘面事实" in ROUTING_POLICY, "routing policy does not distinguish guidance from facts")
    female_relationship = run("我和他还能继续发展吗", "relationship", "lines", "Asia/Shanghai", "7,8,8,6,7,8", None, "female")
    check(female_relationship["result"]["analysis"]["questionContext"]["perspective"] == "female", "relationship perspective was not passed through")
    unspecified_relationship = run("我们还能继续发展吗", "relationship", "lines", "Asia/Shanghai", "7,8,8,6,7,8", None)
    check(unspecified_relationship["result"]["analysis"]["yongshenRelative"] is None, "unspecified relationship perspective was forced into a gender route")
    single = cast_one(1)
    check(single["positionName"] == "初爻" and single["value"] in (6, 7, 8, 9), "single-line casting mismatch")
    print("standalone fortune-liuyao regression: 27/27 passed")


if __name__ == "__main__":
    main()
