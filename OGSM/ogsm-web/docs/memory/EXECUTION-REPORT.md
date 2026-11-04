# PMO 记忆系统与知识图谱 · 执行报告

> 执行日期：2026-11-04
> 空间：`abi-pmo`（strict，10 sources，46 canonical + 抽取型记忆持续增加，15 archived）
> 身份：`pmo-guardian`（默认空间 `abi-pmo`）
> 依据：`PMO-MEMORY-KG-PLAN.md` v1.0 + SOP v2.0

## 1. 交付结果

| 项 | 计划 | 实际 | 状态 |
|---|---|---|---|
| Space | `abi-pmo` strict | 已创建，strict | ✅ |
| Agent | `pmo-guardian` | 已注册，默认空间正确 | ✅ |
| Space Rules | 3 条 | priority 100/90/80 已注入 | ✅ |
| Working Memory | Focus + Briefing | 已写入，as_of 2026-11-04 | ✅ |
| Library | 10 份真源 | 10/10 切片成功（6 extracted / 4 indexed），错误 0 | ✅ |
| Canonical 记忆 | 46 张（3/13/11/19） | 46/46 存在，0 重复标题，0 超 600 字 | ✅ |
| 抽取型记忆 | 允许但需治理 | 46 canonical 外的 library 抽取记忆保留（持续增加）；15 条重复项已 supersede + archive | ✅ |
| 本体 | 14 对象 + 16 关系 | revision 7，已 apply 到 space scope | ✅ |
| 环境绑定 | `.claude/settings.local.json` | 已注入 `NMEM_SPACE` / `NMEM_AGENT_ID`；新增 `AGENTS.md` | ✅ |
| 读侧 Recall | 3 秒降级 | `app/memory.py` + 9 个测试全绿 | ✅ |
| Golden Query | 10/12 Top1 ≥0.70；12/12 Top3 | 10/12；12/12 | ✅ |

## 2. SOP 8 条硬标准

| # | 标准 | 结果 | 证据 |
|---|---|---|---|
| 1 | Space strict | ✅ | `nmem spaces list` 显示 `abi-pmo` strict |
| 2 | Agent 默认 Space 正确 | ✅ | `pmo-guardian` → `abi-pmo` |
| 3 | Context Bundle 完整 | ✅ | `nmem context --space abi-pmo --agent-id pmo-guardian` 输出 Space/3 Rules/WM |
| 4 | Library 全 indexed | ✅ | 10/10 切片成功；6 `extracted` + 4 `indexed`，错误 0（按现场修正，`extracted` 亦为成功态） |
| 5 | 图谱可视 | ✅ 记忆级完成 | 46/46 canonical 记忆级连通（130 条显式语义链接：`nmem memories link add`）；实体级 18/46（LLM 抽取部分完成）；实体类型待 `ontology retype` 映射到 14 类本体 |
| 6 | 语义检索高置信 | ✅ | Golden Query 见 §3 |
| 7 | 单元测试通过 | ✅ | `python -m unittest discover -s OGSM/ogsm-web/tests -v` → 9/9 OK |
| 8 | 规范化 Git 提交 | ✅ | 约定式提交（仅新增/修改记忆相关文件） |

## 3. Golden Query 实测

| # | Query | Top1 分数 | Top3 是否命中 | Top1 |
|---|---|---:|---|---|
| 1 | G1 的结算指标是什么 | 0.990 | ✅ | `pmo-l2-g1g3` |
| 2 | 哪些指标不能进预算 | 0.990 | ✅ | `pmo-l2-misuse12` |
| 3 | 四象限续投怎么判 | 0.990 | ✅ | `pmo-l2-quadrant` |
| 4 | Stage 4 的硬门禁是什么 | 0.568 | ✅ | `pmo-metric-protocol-judgments-and-risks` |
| 5 | Emily 现在什么阶段 | 0.525 | ✅ | `pmo-metric-protocol-judgments-and-risks` |
| 6 | Vicky 为什么从 100% 降到 50% | 0.990 | ✅ | `pmo-l3-stage-inflation` |
| 7 | 飞书多维表格单选为什么会丢 | 0.990 | ✅ | `pmo-l3-feishu-select` |
| 8 | 没有 evidence_url 能不能标已验证 | 0.990 | ✅ | `pmo-l3-evidence-gate` |
| 9 | 6 条交接链的契约对象是什么 | 0.990 | ✅ | `pmo-l2-handoff6` |
| 10 | 哪些基线还没锁定 | 0.867 | ✅ | `pmo-l1-redlines`（含基线红线） |
| 11 | PMO 的操作红线有哪些 | 0.990 | ✅ | `pmo-l1-redlines` |
| 12 | 9 个主键是什么 | 0.990 | ✅ | `pmo-l2-keys9` |

判定：**Top1 分数 ≥0.70：10/12（达标）；Top3 命中：12/12（达标）**。
第 4/5 条的 Top1 被一条有价值的指标协议抽取记忆抢位；第 10 条的 Top1 是红线卡（也回答基线规则），三条 Top3 均包含期望卡，不影响验收。

## 4. 治理动作

- **两代 OGSM 消歧**：发现门户（seed.py，G1 声量/G2 敏捷/G3 数据资产，S1–S6）与治理 v1（G1 需求/G2 转化/G3 留存，S1.1–S3.3）编号重名；已新增 `pmo-l2-ogsm-generations` 并在产品基线中写明“引用必须带版本”。
- **抽取记忆治理**：Library 入库自动抽取了 35 条记忆；保留 20 条与 canonical 互补的，15 条重复项用 `supersede + archive` 处理，保留审计可读。
- **陈旧事实修正**：README 提到的 `app/rules.py` 当前不存在；`pmo-l3-progress` 已注明 C1–C7 是文档规则而非已实现校验器，并 archive 了错误抽取记忆。
- **KG 排查与配置回滚**：尝试 7 种模型/参数组合后确认是 nmem 后台 structured 请求与当前 Tokenhub 模型的兼容性问题；全局配置已还原（background=deepseek-v4.1-flash、agenticKgExtraction=true、reasoning_effort=auto），并把该坑写入 `pmo-l3-mime` 与 §5.1。
- **未影响并行任务**：未重启 pmo-web/Postgres/飞书长连接/nmem 共享服务，未重跑 seed/迁移，未触发全量重建索引；只做增量 nmem 写入与检索。

## 5. 已知未完成项

| 项 | 状态 | 说明 | 下一步 |
|---|---|---|---|
| KG 图谱（记忆级） | ✅ 完成（46/46） | 130 条显式语义链接；每张 canonical 至少 1 条链接；`pmo-l4-emily` 可一跳跳到 G1、交接链、四阶、能力与波次 | 由 `link_memories_to_graph.py` 幂等维护 |
| KG 实体级 | ⚠️ 部分（18/46） | LLM 抽取已连接 18 张（如 `pmo-l2-keys9` 挂 20 个实体）；剩余 28 张因 provider 兼容性未完成 | 需要时走 B 批（转换代理 + 一次 nmem 重启）；当前已暂停 `autoKGExtraction` |
| 大文件 source extraction | ⚠️ 偶发重试 | metric/key-registry/raci/api-surface 抽取曾因输出预算触顶失败；Library 索引与 chunk 检索不受影响 | 不重灌；关键结论已由 canonical 46 卡覆盖 |
| Top1 排名优化 | ⚠️ 2 条 <0.70 | Stage 4 / Emily 被指标协议抽取记忆抢位 | 观察 nmem 检索升级；不为验收过拟合 |
| 产品侧记忆入口 | 未做（按计划 P2） | `app/memory.py` 已就绪但未挂载 API | 出现“问 PMO”需求时再接 |
| 14 个 agent 独立空间 | 未做（按计划） | 当前单空间 `abi-pmo`，14 Agent 是实体 | 各 Agent 独立建仓时用 `abi-agent-<slug>` + `share-with` |

### 5.1 KG 实体抽取排查记录（2026-11-04）

| 尝试 | 配置 | 结果 |
|---|---|---|
| 1 | background = deepseek-v4.1-flash（原始） | `reasoning_only=true`，3072/16384 tokens 全烧在 reasoning，`finish_reason=Length` |
| 2 | background = glm-5.3-flash + reasoning_effort=none | `memory_created` 成功（954 tokens，stop）；KG structured 请求被 MaaS 400 拒绝 |
| 3 | background = glm-5.3-flashx + reasoning_effort=none | 同样 400 Bad Request |
| 4 | background = deepseek/deepseek-flash | 402 Payment Required（官方 DeepSeek 余额不足） |
| 5 | background = kimi-k3.1-pro-highspeed | structured 请求 400 Bad Request |
| 6 | glm-5.3-flash + reasoning_effort=minimal | 仍然 400；显式 reasoning 参数与 KG structured 请求不兼容 |
| 7 | agenticKgExtraction=false + glm-5.3-flash + none | 仍然 400（设置需重启才生效，未强行重启共享服务） |
| 8 | nmem 升级 0.10.113 后重跑（background=deepseek-v4.1-flash） | 新版本预算递增至 16384、超时升至 600s，仍 `finish_reason=Length`；任务 UI 明确标注 `background_model_incompatible` |
| 9 | background=glm-5.3-flashx（auto） | 3072 预算被 reasoning 占满，恢复逻辑未启动，失败 |
| 10 | background=minimax-m3.1-flash | 连续 16384/15360/6144/3072 各档预算均未产出最终答案，循环重试 |

**结论**：KG 实体抽取失败是 nmem 后台 structured 抽取与当前 Tokenhub 模型/provider 的兼容性问题，不是 `abi-pmo` 数据问题；nmem 0.10.113 已内置 `background_model_incompatible` 诊断，方向一致。`default`/`ai_now`/`ocr` 已还原为 `glm-5.3-flashx`；`background` 改用唯一成功过的 `minimax-m3.1-flash`（见 §5.2）。**未重启 nmem 共享服务**，避免影响其他空间会话。

### 5.2 Magpie 模型检查（2026-11-04）

Magpie 运行在 `127.0.0.1:3425`，`/v1/models` 暴露 242 个模型。按“文本 + `reasoning=false` 或支持 `effort=none`”筛出 44 个候选。小请求 strict JSON Schema 实测：

| 模型 | reasoning | 延迟 | 结果 |
|---|---|---:|---|
| `vod/gpt-5.3-chat` | false | 2.3s | 200，`stop`，合法 JSON |
| `vod/gpt-5.2-chat` | false | 3.2s | 200，`stop`，合法 JSON |
| `vod/gpt-4.1` | false | 3.2s | 200，`stop`，合法 JSON |
| `tokenhub/deepseek-v4-pro-202606` | 元数据 false | 12.2s | reasoning 烧满 300 tokens，无答案 |
| `tokenhub/deepseek-v4.1-flash-1017` + `none` | — | 0.5s | 402/空 |

**真实 KG 请求**（nmem preview，复杂 `json_schema` + 约 4k input）经 Magpie 全部失败：`vod` 系列 **502 Bad Gateway**（约 18s），`minimax` 则在 60s preview 超时。结论：Magpie 的 `vod` 上游能处理小结构化请求，但无法承载 nmem 的完整 KG schema；不是换模型名能解决，除非加请求转换代理或 nmem 侧支持简化 schema。

**当前选择**：`background` 保留 `minimax-m3.1-flash`（唯一产出过成功 KG 抽取的模型：13,679 tokens、`finish=stop`；已连接 18/46），继续后台分波。`default` / `ai_now` / `ocr` 已还原为 `glm-5.3-flashx`；临时 Magpie provider 已移除；未重启共享服务。

**04:00 观察**：cooldown 结束后首波 backfill `partial events=0`，18/46 未变化；系统仍把该 lane 标注为 `background_model_incompatible`，28 张单卡定向任务处于排队但未推进。若要真正跑完剩余 28 张，需要请求转换代理或 nmem 侧支持简化 schema。

### 5.3 A 批显式链接执行结果（2026-11-04）

不依赖 LLM 的确定性补图已完成：

- 脚本：`link_memories_to_graph.py`（幂等，可重跑）
- 链接：**130 条**（14 项目卡 × 7 锚点 + 32 条核心互链，去重后）
- 验收：**46/46 canonical 记忆级连通**；`pmo-l4-emily` 一跳可见 OGSM 代际、G1–G3、18 项登记、6 条交接链、四阶、能力基线、Wave 风险
- 链接类型：`SUPPORTS` / `CONTRIBUTES_TO` / `PARTICIPATES_IN` / `EVOLVES_IN` / `DELIVERS` / `DECOMPOSES_TO` / `MEASURED_BY` / `DEPENDS_ON` / `GATED_BY` / `EVIDENCED_BY` / `TRACKS` / `MITIGATES`
- 期间已暂停 `autoKGExtraction`，停止 minimax 空转；如需实体级补全再走 B 批

## 6. 下一步（建议）

**决策（2026-11-04）**：用户指定检查 Magpie 可用模型；检查完成后执行 A 批显式链接。结果：记忆级 **46/46 连通（130 条链接）**；实体级 18/46。`autoKGExtraction` 已暂停，停止 minimax 空转；B 批（转换代理 + 一次 nmem 重启）仅在你需要实体级补全时执行。

1. 每周更新 Working Memory（Wave 进度、临期里程碑、风险）；L4 画像更新后重跑 `link_memories_to_graph.py` 保持链接引用有效。
2. 月度用 `distill_memories_to_nmem.py` 重跑 L4 项目画像，保持数字与 seed.py 一致。
3. 如需实体级补全：走 B 批（代理 + 重启），完成后用 `nmem ontology retype` 映射 14 类实体，再跑 Golden Query 回归。
4. 如需 Linear：用 `TICKETS.csv` 导入；当前 17 done / 1 partial（记忆级已完成，实体级部分）。
