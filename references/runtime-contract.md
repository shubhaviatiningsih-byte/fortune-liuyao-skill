# 本地运行契约

排盘、规则整理和上下文组装均在本地执行。

## 本地命令

- `scripts/build_chart.py`：从六次爻值、起卦时间和问题上下文生成盘面及规则事实；
- `scripts/cast_lines.py`：使用密码学随机源自动起卦，或把六轮手动硬币记录换算为爻值；
- `scripts/build_model_packet.py`：把盘面、规则事实和领域方法组装为解读上下文；
- `scripts/render_chart.py` / `scripts/render_chart_text.py`：分别输出 HTML 与 Markdown 卦盘；
- `scripts/test_standalone.py`：验证固定盘例的卦名、宫位、世应、旬空、伏神和用神候选。

## 排盘输入核心字段

- `linesBottomUp`：从初爻到上爻的六个整数，每个只能是 6、7、8、9；
- `castingMode`：`guided`、`auto` 或 `manual`；
- `randomSource`：`client_web_crypto` 或 `external_manual`；
- `questionCategory`、`questionSubtype`、`questionText`；
- `castAt`：带时区的 ISO-8601 时间；
- `timezone`：优先使用 IANA 时区。

感情问题按需增加 `questionPerspective`，时间问题增加 `questionDeadline`。保留用户选择的 `judgmentTargets`，不要从一段话无限扩张目标。

## 错误处理

- 输入校验失败：指出缺少或冲突的字段，修正后重新计算；
- 本地依赖缺失：说明缺少的运行库，不生成半张盘；
- 历法失败：停止解读，因为排盘基础不完整。
- 解读失败：继续展示和导出已经完成的排盘。

## 版本审计

每次导出保留 chart schema、变换规则版本、school profile、起卦审计、日历库版本和规则版本。

## 强度信号说明

`strengthEvidence.status` 是简化方向信号，只统计月建/日辰对爻的「同五行、相生（支持）」与「相克（压力）」；**不包含泄（爻生月日）与耗（爻克月日）**，也不等同于完整古典旺衰。它用于辅助比较候选，不是最终旺衰结论。
