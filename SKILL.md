---
name: fortune-liuyao
description: 当用户提出六爻占卜、六爻排盘、文王纳甲、三枚硬币起卦、手动输入六次爻值，或询问事业、感情、财富、学业等六爻问题时使用。完成确定性排盘、规则事实整理、领域方法加载、综合解读、卦面 JSON 导出与事实一致性检查。高风险医疗、生死、胎儿性别、失踪定位等问题只返回友善的现实帮助。
---

# Fortune 六爻

本 Skill 只有一条默认链路：

**问题规范化 → 起卦 → 确定性排盘 → 规则事实 → 领域方法引导 → 模型自由综合解读 → 事实一致性检查。**

用户不需要选择“自由”或“引导”模式。方法负责提醒模型看全关键结构，不替模型预设吉凶；模型可以使用自身掌握的京房纳甲和六爻知识形成明确结论。

## 默认入口：一次返回排盘与提示词

先完整阅读 [domain-routing.md](references/domain-routing.md)，先判断问题是否足以起卦，再根据用户原问题的语义选择一个领域，并把枚举值传给统一入口的 `--category`。不要使用关键词表，也不要把可从原问题理解的信息再次做成表单询问。若无法识别用户到底在问什么、判断谁或希望判断哪一种结果，暂停起卦并只问一个最必要的澄清问题；收到回答后再分类和起卦。若问题本身已经明确、只是领域边界无法可靠分类，则直接使用 `general`，不要追问。

只有用户尚未指定起卦方式时，使用宿主 Agent 的选择控件弹出：

- **自动起卦**：一次安全随机生成初爻至上爻；
- **逐爻起卦**：让用户连续确认六次，每次确认后运行一次单爻脚本；
- **输入硬币／爻值**：让用户一次输入六轮硬币或六个 `6/7/8/9`。

宿主不支持选择控件时，仅用一条简短文字列出三个选项。不得为实现弹窗另起 HTML 页面或本地端口。

自动起卦直接运行：

```powershell
python scripts/run_liuyao.py --question "用户原问题" --category career --method auto
```

逐爻起卦从初爻到上爻依次运行，必须等用户确认当前次后再生成：

```powershell
python scripts/cast_one_line.py --position 1
python scripts/cast_one_line.py --position 2
# 依次至 --position 6
```

每次向用户回显爻位、硬币结果、爻值与老少阴阳。收齐六爻后，把六个值按初爻至上爻传给统一入口的 `--method lines`。

参照成熟工具的 `result + prompt` 契约，由当前 Agent 调用统一脚本，不让网页承担模型调用：

```powershell
python scripts/run_liuyao.py `
  --question "未来三个月能否找到合适工作" `
  --category career `
  --method auto
```

脚本先做敏感分流，再确定性起卦和排盘，最后返回：

- `result`：完整卦盘、规则事实、问题上下文和起卦审计；
- `prompt`：可直接交给当前 Agent 默认模型的综合解读提示词。

当前 Agent 必须直接使用 `prompt` 继续作答，不调用项目内部 Fortune API，不向用户索要模型密钥。需要手工爻值时用 `--method lines --lines "7,8,8,6,7,8"`；用户提供六轮硬币时用 `--method coins --coins "正反反/正正反/反反反/正反反/正正正/正正反"`。

采用传统异性婚恋取用且已取得必要视角时，可额外传入 `--perspective male` 或 `--perspective female`；其他情况省略该参数或使用 `--perspective unspecified`。

网页工作台只作为可选的本地交互与卦盘展示实验，不是 Skill 的默认运行入口。无法稳定完成宿主 Agent 回写时，不得声称网页能够独立流式解读。

完整阅读 [interpretation-modes.md](references/interpretation-modes.md) 后再组装解读上下文；执行本地排盘时阅读 [runtime-contract.md](references/runtime-contract.md)；生成可视卦面时阅读 [frontend-contract.md](references/frontend-contract.md)。

## 1. 规范问题

保存一个核心问题、领域、具体目标、时间范围、起卦方式、起卦时刻和 IANA 时区。复合问题保留一个主问题，并把结果、质量、风险、时间拆成子目标。

领域、判断目标、提问视角和期限应优先由当前 Agent 从用户原问题中理解，不要把这些字段拆成表单让用户重复填写。起卦前应用以下门槛：

- 能识别核心事项和用户希望判断的结果：直接继续，不追问措辞、分类或可合理保留为未知的细节；
- 核心事项明确，但同时存在多个彼此独立、会使用不同判断主线的问题：请用户先选本次最想判断的一个；
- 无法识别所问事项、判断对象或目标结果：暂停起卦，只问一个能够解除当前歧义的简短问题；
- 用户回答后立即继续，不连续追加一组资料收集问题。

例如，“看看我最近怎么样”应先问“你这次最想看工作、财务、感情，还是其他具体事项？”；“我和他能不能继续发展”已足以按感情关系处理，不要再询问领域；“这次面试能不能通过”已包含事项和目标，不要再让用户填写职位类别或期限。浏览器可以取得时区时不要要求用户手填。

### 何时询问性别或提问视角

不要默认收集性别。排盘本身以及事业、财富、学业、出行、住宅、纠纷等领域均不依赖性别。家庭或代占问题优先询问提问者与被问者的实际关系，也不以性别代替关系。

只有同时满足以下条件时，才询问一次提问视角：

1. 问题属于恋爱或婚姻；
2. 用户原文没有明确提问者视角；
3. 当前解读准备采用“男问以妻财、女问以官鬼为初始主线”的传统异性婚恋口径，缺少该信息会改变取用。

此时用简短且可跳过的问法：“按传统婚恋取用，需要确认你的提问视角；你是男方、女方，还是希望不按性别口径，直接以双方关系和世应分析？”用户不愿提供、属于同性关系、非二元身份，或该传统口径不适用时，传入 `--perspective unspecified`，结合关系角色、世应和完整问题分析，不得强迫二选一。用户已在原文明确“我是男方／女方”等信息时直接识别，不重复询问。

胎儿性别不属于可澄清字段。凡要求预测胎儿性别、母婴安危或怀孕结果，按敏感分流处理，不起卦。

## 2. 排盘前做敏感问题分流

按 [safety-boundaries.md](references/safety-boundaries.md) 的固定分类和统一响应模板处理。命中紧急信号、怀孕母婴、医疗生死、失踪犯罪或高风险财务时，不排盘、不解读、不输出吉凶日期或概率，改为友善地把用户转向可靠现实帮助（就医、报警、求助热线、专业咨询），并可按需帮用户整理症状或求助信息。

网页工作台和脚本调用都必须先运行 `scripts/classify_sensitive.py` 的确定性分类，不得只依赖模型自行遵守提示词。

## 3. 起卦并确定性排盘

支持脚本自动起卦、Agent 逐次记录，以及用户自己用三枚硬币摇六次后口述结果。读取 [manual-coin-casting.md](references/manual-coin-casting.md)，用其中固定映射把每次正反面换算成 6、7、8、9。六次结果始终按初爻至上爻排列，不得倒序。

自动起卦时运行：

```powershell
python scripts/cast_lines.py --mode auto --output casting.json
```

用户提供六次硬币结果时运行：

```powershell
python scripts/cast_lines.py --mode manual `
  --manual "正反反/正正反/反反反/正反反/正正正/正正反" `
  --output casting.json
```

如果用户已经知道爻值，可直接接收类似 `7,8,8,6,7,8` 的六个数字；如果用户只报告正反面，则先回显六次原始记录和换算后的爻值，请用户核对后再排盘。

依据 Skill 固定规则完成本地排盘。历法、纳甲、八宫世应、六亲、六神、旬空、月破、动爻、变爻、伏神、回头生克、进退神、冲合刑害和规则事实均以排盘结果为准。解读阶段不得重算或静默修改这些字段；发现疑点时保留输入和规则版本供校勘。

使用随 Skill 分发的本地脚本：

```powershell
python scripts/build_chart.py `
  --lines "7,8,8,6,7,8" `
  --cast-at "2026-08-04T11:17:00+08:00" `
  --timezone "Asia/Shanghai" `
  --category "career" `
  --subtype "job_search" `
  --question "两个月内能否找到工作" `
  --output chart.json
```

若环境没有 `lunar_python==1.4.8`，先按 `requirements.txt` 安装；若已有经过核验的日干支和月建，也可用 `--day-ganzhi`、`--month-branch` 显式传入。

## 4. 先展示盘面

先显示本卦、变卦、宫位、世应、月日旬空、六爻、动变、伏神和版本信息，再开始解读。解读失败不能让已完成的盘面消失。

- 环境支持 HTML 或文件产物时，运行 `python scripts/render_chart.py --chart chart.json --output chart.html`，返回可打开的可视卦盘；
- 环境不能展示网页时，运行 `python scripts/render_chart_text.py --chart chart.json --output chart.md`，直接返回完整 Markdown 卦盘；
- 不要声称已经打开网页，除非当前 Agent 确实能够展示或提供该 HTML 文件。

## 5. 组装解读上下文

在 Skill 目录执行：

```powershell
python scripts/build_model_packet.py --chart chart.json --output packet.json
```

脚本读取问题领域并加载 Skill 内的方法说明。解读上下文包含：

- 用户问题、判断目标与期限；
- 完整排盘及日历；
- 用神候选和多现信息；
- 世应、旺衰证据、动变、伏神、爻间关系与组合事实；
- 对应领域的分析主线；
- 要求的报告结构。

解读上下文只包含问题、盘面、规则事实和方法说明，不写入密钥、令牌或其他秘密配置。

## 6. 让模型自由综合解读

模型先给直接判断，再说明决定判断的主线。重点比较：

1. 用神及多现取舍；
2. 世爻承接与应爻环境；
3. 月建、日辰和旺衰证据；
4. 动爻、变爻、回头生克、进退与爻间关系；
5. 伏神、飞神与原神、忌神、仇神作用链；
6. 与用户期限对应的条件性应期；
7. 卦名、整体卦式、爻位和六神的辅助取象。

允许使用 Skill 资料以外的稳定六爻知识。方法是注意力清单，不是正负计票，也不强迫输出中庸结论。

## 7. 只校验事实一致性

生成后运行 `scripts/verify_facts.py`，区分“排盘事实”和“模型推断”。修正不存在的爻、错误的世应/六亲/本卦/变卦，以及把工程状态误写成另一种确定性状态。

校验器只锁定报告中明确声称的确定性盘面字段。吉凶、应期、传统取象、作用链主次等无法确定性验证的内容属于模型推断，可以保留；若依赖特定口径，说明该口径。不要因为某项推断并非程序字段就删除整段推理，也不要把明确判断统一降级成模糊句。原则是：**锁事实，不锁判断；拦编造，不压缩传统推断空间。**

## 报告顺序

1. 问题与起卦信息（含硬币原始记录、换算约定和六爻顺序）
2. 卦盘
3. 直接判断
4. 用神与世应
5. 关键动变与作用链
6. 支持、阻力及主次裁决
7. 应期条件（用户问时间时）
8. 现实建议
9. 事实一致性结果
10. 文末原样附上：`本内容基于玄学体系生成，仅供文化爱好与思维参考，不构成任何重大人生决策的专业建议。`

## Skill 内部组件

- `references/safety-boundaries.md`：高风险问题分类、触发词与统一友善分流模板；
- `references/manual-coin-casting.md`：硬币起卦和六爻顺序；
- `references/runtime-contract.md`：本地执行输入、输出和版本纪律；
- `references/interpretation-modes.md`：各领域分析主线；
- `references/frontend-contract.md`：卦面与报告展示规范；
- `scripts/liuyao_core.py`：文王纳甲、八宫世应、六亲六神、伏神动变和核心规则事实；
- `scripts/cast_lines.py`：自动起卦与手动硬币换算；
- `scripts/build_chart.py`：本地排盘命令；
- `scripts/render_chart.py`：把排盘 JSON 渲染为可独立打开的卦面页面；
- `scripts/render_chart_text.py`：在不能展示 HTML 时输出 Markdown 卦盘；
- `scripts/build_model_packet.py`：把本地盘面、规则事实和方法组装为解读上下文。
- `scripts/classify_sensitive.py`：排盘前的确定性敏感问题分流；
- `scripts/verify_facts.py`：只核对报告中的明确盘面事实；
- `scripts/cast_one_line.py`：宿主逐爻交互时生成一爻；
- `scripts/run_liuyao.py`：统一返回确定性 `result` 与当前 Agent 可直接使用的 `prompt`。
