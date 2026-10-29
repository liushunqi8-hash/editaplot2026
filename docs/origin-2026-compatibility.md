# EditaPlot 的 Origin 2026 兼容说明

这份说明回答一个最常见的问题：**我的 Origin 版本能不能用 EditaPlot？**

先给结论：

- 这个 fork（editaplot2026 / v1.1.0）**唯一针对并实机验证于 Origin / OriginPro 2026（产品号 10.30）**。
- 页大小设置、对象反读和 smoke 门禁都在 Origin 2026 上完成过端到端验证，可生成可编辑 OPJU 并导出 PNG、PDF、TIF。
- 其他 Origin 版本（2021–2025b、2026b 等）**不在本 fork 的支持范围内**；上游仓库的跨版本兼容说明不再适用于这里。
- 默认由 EditaPlot 启动一个隔离的新 Origin 实例，不需要提前打开 Origin 窗口。
- 这里只判断技术可调用性，不收集与绘图无关的信息。

## 产品版本与产品号

| Origin 产品 | 产品号 | 本 fork 口径 |
| --- | ---: | --- |
| **Origin 2026** | **10.30** | **唯一实机验证版本（本 fork 基线）** |
| Origin 2026b | 10.35 | 未验证，不保证可用 |
| 2025 及更早各版本 | 9.80–10.25 | 不在本 fork 支持范围 |

Origin 返回的 `@V` 还可能带有更长的构建后缀。产品号和具体构建号是两层信息，EditaPlot 不会把任意后缀猜成某个官方 Service Release。本 fork 的版本探测只把 10.30 当作已验证基线；读到其他产品号时会照常走握手与探针，但不承诺完整兼容。

## 官方 External Python 边界

OriginLab 的 External Python 文档说明：

- 外部 `originpro` 路线仅适用于 Windows；
- 本机需要安装 Origin 2021 或更高版本；
- `originpro` 通过 Origin Automation Server 与 Origin 交互；
- 使用该包时会启动一个可见或隐藏的 Origin 实例。

因此，macOS 和 Linux 不在当前 Origin Automation 路线内，Origin 2020b 及更早版本也不在本 fork 的目标范围内。

## 为什么不要求提前打开 Origin

EditaPlot 默认采用隔离实例策略：

1. Skill 请求一个新的、由 EditaPlot 管理的 Origin 实例；
2. 在这个实例中创建工作簿、图页和项目；
3. 根据"完成后保留 Origin 窗口"的选择，显示或关闭这个实例；
4. 不触碰其他已打开的、由使用者管理的 Origin 会话。

OriginLab 的 Automation 文档指出，`Application` 总是创建新实例；`ApplicationSI` 则优先连接已有实例。EditaPlot 默认使用前一种生命周期语义，因此不需要先打开 Origin。只有在明确选择 `attach_existing` 时，才进入附加已有会话的路线；该路线不会重置项目，也不会关闭已有会话。

## 一个版本怎样被判定为"可用于当前模板"

EditaPlot 不使用"版本号大于某个值，所以肯定兼容"的捷径。一次真实判断分为五层：

1. **Automation 握手**：能否创建隔离实例、读取就绪状态和必要环境信息。
2. **版本风险优先级**：已知产品或构建风险只决定先跑哪些探针。
3. **模板能力探针**：检查当前模板实际需要的轴、文本、误差棒、分类刻度、填充、参考线或三维等能力。
4. **真实产物**：必须生成非空、可编辑的 OPJU，以及 PNG、PDF、TIF。
5. **对象与视觉证据**：反读轴和文本等对象状态，并完成人工视觉检查。

只有 PNG、只有版本字符串、或者仅仅能导入 Python 包，都不足以证明完整兼容。

## Origin 2026 (10.30) 上的页大小与读回修复

本 fork 相对上游的关键修复集中在 Origin 2026 的 Automation 行为差异上：

- **页大小不再被静默忽略。** 上游使用的 COM `PutWidth` / `PutHeight` 在 Origin 2026 上是静默空操作，`GetWidth()` 也返回错误单位。本 fork 改用 LabTalk 原生 dots 设置页大小：`page.width = (W_cm / 2.54) * page.resx`。
- **不再被整数 cm 取整。** 以 cm 单位设置 `page.width` 时，Origin 2026 会把 23.5 取整成 23.0。dots 路线保留小数 cm（实测读回 23.499 cm，合同值为 23.5 cm）。
- **图层与标签像素级读回降级为诊断。** Origin 2026 的 COM bridge 对部分图层几何和标签裁剪像素的读回单位错乱；这些读回不再作为硬失败，而是记录为诊断。图页物理尺寸和附件相对位置仍严格校验。

这三点已在 Origin 2026 / 10.30 上端到端验证：隔离 smoke 通过，`trend` 模板成功渲染 10 个数据点的 `ln(Rx) vs T/K` 折线，并产出 OPJU、PNG、PDF、TIF。

## 为什么更需要对象反读

Origin 2025b 起，OriginLab 调整了图页比例、边距、字体呈现、轴框、线宽和刻度标签自动旋转等默认值；Origin 2026 又进一步改变了部分 COM 几何读回的单位语义。因此 EditaPlot 对关键尺寸和文本采用显式合同，并以对象反读和最终视觉结果验收，而不是依赖某个版本的默认主题。

## 先区分 Codex 沙箱预检与真实 COM 启动错误

如果新版首先返回 `origin_codex_sandbox_context`，说明当前 Codex 命令运行在隔离账户中，EditaPlot 已在调用 Origin COM 前停止；这不能证明 Origin、版本、Python 包或数据有问题。我让 Codex 只针对原来的精确 `origin-smoke` 或 `render` 命令发起正式、受限的本地执行申请。只有这次精确申请获批后，Codex 才可重跑同一条命令；申请可以由你在提示时确认，也可以由已经配置的 Codex 自动审查评估，但审批不保证通过，自动审查也不等于预先授予所有 Origin 命令权限。

这条路线不是绕过沙箱。无需把命令复制到自己的 PowerShell，也不要使用管理员权限、修改 DCOM/注册表或改走未验证的 Automation 接口。审批被本机或组织策略拒绝时应停止。若报告 `origin_execution_context_unknown`，说明 Windows 执行身份无法验证；它不是一个待审批状态，同样必须在 COM 前停止，不能根据 `USERNAME` 或 `USERPROFILE` 猜测身份。

只有精确申请获批、命令已经处于可验证的当前用户上下文后，仍然发生的 COM 错误才进入下面的启动恢复流程。沙箱预检发生在 COM 之前，不消耗后续"瞬时启动错误自动重试"或"用户批准再试"的次数。

## 获批后仍遇到 0x80080005 等启动错误时会怎样

`0x80080005` 表示 COM Server 没有在规定时间内完成启动注册；它本身不能证明是 Origin 版本、Python 包或数据文件的问题。EditaPlot 会把常见启动错误收敛成短代码：

- `origin_com_unspecified_failure`：对应 `0x80004005`；
- `origin_com_call_rejected` / `origin_com_server_busy`：Origin 暂时拒绝或延后调用；
- `origin_com_disconnected` / `origin_com_server_unavailable`：连接中断或服务暂不可达；
- `origin_com_server_execution_failed`：对应 `0x80080005`；
- `origin_com_class_not_registered`：对应 `0x80040154`；
- `origin_com_activation_access_denied`：对应 `0x80070005`。

对通用或明确可重试的瞬时启动错误，EditaPlot 会先尝试退出可能存在的半启动自有实例；只有清理调用成功，才自动创建一个全新的隔离实例，最多一次。清理失败不会覆盖主激活错误：主激活错误码仍为终端错误，清理细节只作为次要诊断保留，也不会因此自动重试。成功激活后，它执行 `sec -poc 30` 并用 `run.isOCready()` 确认 Origin C 已就绪，未就绪时不会读取版本或新建项目。类别入口不存在和访问被拒绝不会自动循环。

如果最初启动与清理同时失败，我只让报告保留脱敏字段：`primary_activation_code`、`primary_activation_stage`、`cleanup_error_code` 和 `cleanup_error_stage`，以及捕获到的脱敏 HRESULT 十六进制码（`primary_hresult`、`cleanup_hresult`，仅含错误码、不含原始异常文本）。这些字段不包含 Windows 账户名、本地路径或原始 COM 异常文本，也不会因为同时存在两组诊断而继续自动重试。

如果两次自动尝试都失败，EditaPlot 会停止并保留脱敏兼容报告。只有用户同意后，才允许在同一活动 Windows 用户上下文再执行一次；新的 smoke 必须使用新的空白同级输出目录，不能覆盖第一次诊断。它不会切换到 `ApplicationSI`、自动改 DCOM/注册表或把管理员模式作为普通用法。它也不会仅凭经过时间就强杀可能正在管理隐藏 Origin 的 Python worker；长时间无进度时应先保留报告并定位最后阶段。

smoke 或正式绘图失败时，Python 预览以及单独生成的 PNG/PDF/SVG 只能算预览，不能写成"Origin 已完成"。正式完成仍须同时具备 OPJU、PNG、PDF、TIF、对象反读和人工视觉检查。

## 普通用户只需要看什么

运行前不必自己判断构建号。把数据交给 EditaPlot 后，重点看三类结果：

- `verified`：当前环境与路线拥有完整证据；
- `compatible_unverified`：握手和所需能力通过，但尚未成为完整实机基线；
- `unknown`：产品或构建无法可靠归类，正在或需要运行完整探针。

如果探针失败，报告应指出失败阶段和受影响能力；不会用一大段版本术语淹没初次使用者。

## 官方与公开来源

- OriginLab External Python：
  <https://docs.originlab.com/externalpython/>
- OriginLab Automation 实例差异：
  <https://docs.originlab.com/com/difference-of-application-applicationsi-and-applicationcomsi/>
- Origin / OriginPro 官方版本与构建历史：
  <https://www.originlab.com/index.aspx?pid=3325>
- Origin 2025b 图形默认值变化：
  <https://docs.originlab.com/quick-help/why-graph-looks-different-in-2025b/>
- OriginLab Python Samples：
  <https://github.com/originlab/Python-Samples>
