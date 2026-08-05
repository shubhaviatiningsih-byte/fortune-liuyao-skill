---
name: fortune-liuyao
description: 当用户提出六爻占卜、六爻排盘、文王纳甲、三枚硬币起卦、手动输入六次爻值，或询问事业、感情、财富、学业等六爻问题时使用。完成确定性排盘、领域方法加载、综合解读、HTML/Markdown 卦盘交付与事实一致性检查；对高风险医疗、生死、胎儿性别、失踪定位等问题只提供现实帮助。
---

# Fortune 六爻

只执行以下主流程：

**理解问题与语义路由 → 选择起卦方式 → 运行统一入口 → 展示卦盘并完整解读 → 审计明确盘面事实**

确定性脚本负责起卦、历法、排盘、规则事实和展示文件；当前 Agent 负责理解问题、选择领域、调用宿主交互控件，以及依据返回的 `prompt` 完成传统综合判断。锁定盘面事实，不限制无法确定性验证的吉凶、应期和传统推断。

## 1. 理解问题并选择领域

完整阅读 [domain-routing.md](references/domain-routing.md)，根据用户原问题的语义选择以下一个领域，传给统一入口的 `--category`：

`general`、`career`、`wealth`、`relationship`、`academic`、`travel`、`home`、`legal_risk`、`relationship_family`

不要用关键词表代替语义理解。领域只决定加载哪套分析方法，不属于确定性盘面事实。

- 能识别核心事项和用户希望判断的结果：直接继续，不追问可合理留空的信息。
- 问题包含多个需要不同判断主线的独立事项：只问用户本次最想判断哪一个。
- 无法识别所问事项、判断对象或目标结果：暂停起卦，只问一个最必要的澄清问题。
- 问题清晰但领域边界不明确：使用 `general`，不要为了分类追问。

问题清晰度、敏感分流放行、领域路由、脚本状态和校验通过都属于内部过程，成功时不要展示给用户。排盘前不要发送“我会使用本 Skill”“问题已归入某领域”“现在开始运行”等前言；直接执行所需工具。首次面向用户的成功消息从卦盘和解读开始。

### 性别或关系视角

排盘以及事业、财富、学业、出行、住宅、纠纷等领域不需要性别。家庭或代占问题优先理解提问者与被问者的实际关系。

仅当问题属于恋爱或婚姻、用户没有说明视角，并且准备采用“男问妻财、女问官鬼”的传统异性婚恋取用时，才用一个可跳过的问题询问男方、女方或不按性别取用。分别传入 `--perspective male`、`female` 或 `unspecified`。同性关系、非二元身份或用户不愿提供时使用 `unspecified`，结合关系角色与世应分析。

胎儿性别、母婴安危和怀孕结果不是可澄清字段，按安全边界处理。

## 2. 选择并完成起卦

先按 [safety-boundaries.md](references/safety-boundaries.md) 判断；统一入口还会执行确定性分流。被阻止时不排盘，友好转向就医、报警、求助热线或专业咨询等现实帮助。

用户尚未指定起卦方式时，立即使用宿主 Agent 的单选控件提供：

1. 自动起卦
2. 逐爻弹窗
3. 输入硬币或爻值

宿主不支持选择控件时，只发一条简短文字选项。用户选定后立即执行，不再追加“是否开始”。不要另建网页或本地服务模拟弹窗。

### 逐爻弹窗状态机

第一次弹窗显示“生成初爻”。用户点击后运行：

```powershell
python scripts/cast_one_line.py --position 1
```

保存该结果，立即在下一弹窗显示已生成的初爻及“生成二爻”。依次把 `--position` 增加到 6。

- 两次弹窗之间不发送说明、路由、分析或阶段总结。
- 每个位置只运行一次；保存并复用已生成结果，禁止重摇。
- 第六爻完成后不再询问确认，直接把六个值按初爻至上爻传给 `--method lines`。
- 宿主每次提交都要恢复 Agent，允许短暂延迟，但恢复后立即调用下一弹窗。
- 宿主不支持选择控件时，不模拟六轮文字确认；改为让用户一次输入六轮硬币或六个爻值。

硬币换算与顺序完整阅读 [manual-coin-casting.md](references/manual-coin-casting.md)。

## 3. 运行唯一生成入口

先在后台探测当前宿主可用的 Python 命令：Windows 依次尝试 `python`、`py -3`，再检查 Codex 常见内置运行时 `$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`；macOS/Linux 依次尝试 `python3`、`python`。使用第一个能返回 Python 3.10+ 的命令继续，并把后续示例中的 `python` 全部替换成该命令；不向用户展示成功的环境探测过程。

如果所有命令都不存在，停止排盘并只提示：“当前 Agent 环境缺少运行排盘引擎所需的 Python 3.10+。请安装 Python 后重试，或换用自带 Python 运行环境的 Agent。”不要让模型临时心算排盘。

再用已探测到的命令运行一次自检，例如：

```powershell
python scripts/run_liuyao.py --selfcheck
```

只有返回 `READY` 才继续。返回 `NOT_READY` 时，只说明缺少的运行条件，不生成半张盘，也不让 Agent 临时重算历法或纳甲。`lunar_python` 已随 Skill 内置，不要求用户执行 `pip install`；若自检仍报告内置依赖缺失，说明安装包不完整，应重新安装 Skill。

自动起卦示例：

```powershell
python scripts/run_liuyao.py `
  --question "未来三个月能否找到合适工作" `
  --category career `
  --method auto `
  --output session.json
```

逐爻或已知爻值使用：

```powershell
python scripts/run_liuyao.py --question "用户原问题" --category general --method lines --lines "7,8,8,6,7,8" --output session.json
```

用户提供六轮硬币时使用 `--method coins --coins "正反反/正正反/反反反/正反反/正正正/正正反"`。

统一入口一次返回：

- `result`：确定性卦盘、规则事实、问题上下文和起卦审计；
- `prompt`：当前 Agent 应直接使用的完整解读上下文；
- `artifacts.html` 与 `artifacts.markdown`：从同一份结果同步生成的展示文件路径；
- `schemaVersion`：输出契约版本。

JSON 是脚本与 Agent 之间用于保存、复核和事实审计的内部契约。不要向用户粘贴 `session.json`、原始 JSON 或 `prompt`；最终用户只看卦盘文件、可读文字盘和完整解读。只有用户明确要求导出原始排盘数据时才交付 JSON。

不要再依次调用 `build_chart.py`、`build_model_packet.py` 和 `render_chart.py` 拼接默认流程。它们只作为内部组件和诊断工具。

## 4. 展示并完整解读

先展示卦盘，再给出解读：

- 宿主支持文件交付时，把 `artifacts.html` 作为可打开文件链接或附件；不要粘贴 HTML 源码，不要用代码编辑器打开它。
- 同时可在文字回答中使用 `artifacts.markdown`。
- HTML 无法交付或打开时，立即使用 Markdown；不要反复排查桌面文件关联。
- 展示降级只影响卦盘载体，不得中断或缩短解读。

完整阅读 [interpretation-modes.md](references/interpretation-modes.md)，直接使用返回的 `prompt` 在当前对话中完成综合解读。不要把 `prompt` 发送给另一个模型，不要求用户提供模型 API 密钥。不要把已经完成的解读替换成“解读核心”、一句话总结或几条压缩结论，除非用户明确要求简版。

传统健康、吉凶、应期和取象可以作为传统推断表达，但不得伪装成确定性盘面字段、医疗诊断或现实专业意见。

## 5. 解读后审计事实

把完整解读保存为 Markdown 或文本后运行：

```powershell
python scripts/verify_facts.py --chart session.json --report report.md --output fact-audit.json
```

校验器只检查报告中明确声称的本卦、变卦、世应、爻位和六亲等确定性字段。发现冲突时修正对应事实；不要删除或压缩无法确定性验证的传统判断。校验通过时保持静默，不向用户展示 `accepted=true` 或内部清单。

最终原样附上：

> 本内容基于玄学体系生成，仅供文化爱好与思维参考，不构成任何重大人生决策的专业建议。

## 按需读取

- 本地运行与错误边界：[runtime-contract.md](references/runtime-contract.md)
- 领域分类：[domain-routing.md](references/domain-routing.md)
- 领域分析方法：[interpretation-modes.md](references/interpretation-modes.md)
- 硬币起卦：[manual-coin-casting.md](references/manual-coin-casting.md)
- 安全边界：[safety-boundaries.md](references/safety-boundaries.md)
- 展示规则：[frontend-contract.md](references/frontend-contract.md)
