# 本地运行契约

## 运行条件

当前源码发行版需要：

- Python 3.10 或更高版本；
- Skill 内置的 `lunar_python==1.4.8`；
- Skill 包内的 `scripts/`、`references/` 和 `assets/`。

由当前 Agent 在后台依次探测 `python` / `py -3`（Windows）或 `python3` / `python`（macOS/Linux）。Windows 上两者不可用时，再检查 Codex 常见内置路径 `$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`。使用第一个 Python 3.10+ 运行时，并以其替换后续命令中的 `python`。探测成功时保持静默；全部不可用时才向用户说明当前宿主缺少 Python，停止排盘，并建议安装 Python 或换用自带 Python 的 Agent。

找到解释器后在 Skill 目录运行：

```powershell
python scripts/run_liuyao.py --selfcheck
```

`READY` 表示历法依赖、确定性金标盘和 HTML/Markdown 渲染均正常。`NOT_READY` 时读取失败检查项并停止排盘；不得用模型心算替代缺失的历法或排盘引擎。

内置 `lunar_python` 缺失时视为安装包不完整，提示重新安装 Skill，不要求用户自行拼装依赖。默认 `Asia/Shanghai` 在缺少系统 IANA 时区库时使用固定 UTC+8 后备；其他 IANA 时区仍以宿主环境数据为准。环境检查和依赖齐全状态不作为正常回答内容展示。

完全没有 Python 解释器的系统不能直接运行当前源码版 Skill。宿主 Agent 自带且允许调用的 Python 运行时可以满足要求；否则需要先安装 Python，或使用未来单独提供的对应平台可执行发行物。

## 唯一生成入口

默认只调用 `scripts/run_liuyao.py`。它负责敏感分流、起卦输入、历法、排盘、规则事实、解读上下文，以及 HTML/Markdown 同步输出。

成功输出使用 `fortune-liuyao-run.v2` 契约：

- `ok` / `blocked`：运行状态；
- `result`：确定性结果；
- `prompt`：当前 Agent 的完整解读上下文；
- `artifacts.html` / `artifacts.markdown`：同源卦盘文件的绝对路径；HTML 可作为用户附件，Markdown 仅供内部复核；
- `schemaVersion`：契约版本。

统一 JSON 是脚本、Agent、渲染器和事实审计之间的内部数据合同，用于避免重复计算和字段错位。默认不向最终用户展示原始 JSON、`prompt` 或 Markdown；用户在当前对话中直接接收完整报告，HTML 仅作为可选卦盘附件，除非明确要求导出机器可读数据。

`build_chart.py`、`build_model_packet.py`、`render_chart.py` 和 `render_chart_text.py` 是内部组件与诊断入口，不用于默认编排。

## 解读后事实审计

模型完成报告后运行：

```powershell
python scripts/verify_facts.py --chart session.json --report report.md --output fact-audit.json
```

退出码 `0` 表示未发现明确盘面冲突，退出码 `2` 表示报告中的确定性字段需要修正。吉凶、应期、传统取象和作用链主次不属于程序裁决范围。

## 错误处理

- 输入无效：指出缺少或冲突字段，修正后重新运行。
- Python 或依赖缺失：说明缺少的运行条件，不生成半张盘。
- 历法失败：停止排盘和解读。
- HTML 交付失败：只省略可视化卦盘附件；聊天中的完整文字解读照常输出，不向用户交付 Markdown。
- 解读失败：保留并交付已经生成的确定性卦盘。

## 版本审计

每次输出保留运行契约、chart schema、规则版本、school profile、起卦审计和日历库版本。调用方只依赖公开的统一输出字段，不依赖内部组件的中间结构。
