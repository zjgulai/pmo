# ABI PMO 管理站 · 记忆系统与知识图谱建设方案 v1.0

> 依据：`SOP_Nowledge_Mem_智能体记忆系统与知识图谱构建规范 v2.0`（2026-10-26）
> 对象：ABI 品牌 & 营销域 PMO 管理站（`OGSM/ogsm-web`）
> 日期：2026-11-04
> 状态：**已批准并执行**（2026-11-04；执行结果见 `EXECUTION-REPORT.md`）。
> 配套文件：`memory_cards.csv`、`TICKETS.csv`、`ontology_patch.draft.json`、`sources.yaml`、`distill_memories_to_nmem.py`、`EXECUTION-REPORT.md`

---

## 0. 一页结论

给 PMO 建一个 **strict 隔离空间** `abi-pmo`，绑定一个守门身份 `pmo-guardian`，把当前产品最容易被稀释的四类知识固化下来：

1. **核心准则**：PMO 是谁、先保什么、绝对不做什么。
2. **业务口径**：O/G/S、T1–T5、12 条误用、三道 Gate、四阶标尺、四象限裁决。
3. **避坑实证**：进度虚高、飞书单选丢弃、无证据标已验证、平台 ROAS 当结论等。
4. **组合画像**：14 个 Agent、49 项能力、24 个站点、6 条交接链的当前状态。

**规模**：46 张记忆卡、10 份 Library 真源、14 类实体、16 类关系、3 条常驻规则、1 份 Working Memory。

**不做**：不把 12 份草稿、原始日志、飞书表格行、报告 HTML 直接灌入；不为 14 个 Agent 各建一个空间；不在 MVP 里改产品页面；不重启 pmo-web 容器、不打断当前项目正在跑的后台任务。

**投入**：18 个 Ticket，约 44 小时；单人 5–6 个工作日，两人并行 3–4 天。

**完成判据**：SOP 8 条硬标准全过 + PMO 专项 6 条全过 + 12 条 Golden Query 中 10 条 Top1 ≥ 0.70、12 条 Top3 全命中。

---

## 1. 当前项目产品基线

### 1.1 产品定位

PMO 管理站不是又一个报表页，而是 ABI 品牌 & 营销域的 **OGSM 治理控制面**：

- 形态：**Postgres + 单体 FastAPI + 服务端渲染**；PMO 是唯一写入口，前台只读。
- 主干：愿景 O → G1/G2/G3 → S1–S6 → 14 个专家 Agent/工作台 → 49 项能力。（治理文档 OGSM v1 另有 G1 需求/G2 转化/G3 留存与 11 条战略，两代编号不得混用，详见 `pmo-l2-ogsm-generations`。）
- 作用：把 OGSM v1 从一份文档变成可校验、可结算、可追踪的系统。
- 治理：一个 G 只认一个结算数字；进度不是结果；没有基线的承诺不成立。

### 1.2 产品面与数据面

| 维度 | 当前实现 |
|---|---|
| 只读页面 | `/` 全景导图、`/projects` 场景装配、`/roadmap` 甘特与负载、`/present` 汇报、`/sites` 架构与交接链、`/sop` 岗位与四阶标尺、`/board` 结算看板、`/lines` 产线台账、`/experts` 专家、`/baselines` 基线、`/metrics` 指标字典、`/docs` 治理索引 |
| 写入面 | `/admin` 改项目/能力/交付状态；`/api/cap/{id}/inline` 行内改进度并留审计；`/api/snapshot/save` 存周快照 |
| 自动化 | 生产数据采集、飞书在线表双向同步、24 站点巡检、临期催办、周报卡片、10 页可编辑 PPTX、CSV/JSON/SQL 备份 |
| 飞书 | 长连接 + Webhook、卡片按钮回调、`@PMO` 指令、免打字回写、变更审计 |
| 数据表 | `goal_group`、`strategy_group`、`product_project`、`capability_item`、`progress_snapshot`、`change_audit_log`、`sop_evolution_candidate`、`business_action_ledger` |

### 1.3 当前组合数据（2026-11-04 基线）

| 指标 | 数值 |
|---|---:|
| 专家 Agent/产品 | 14 |
| 能力项 | 49 |
| 已验证能力 | 34 |
| 能力平均进度 | 57.6% |
| 工作台/站点 | 24 |
| 跨岗交接链 | 6 |
| 指标层 | T1–T5 |
| 产线登记 | 18 项 |
| 三道 Gate | Claim / 授权 / 实验 |

**波次分布**：

| 波次 | Agent 数 | 平均进度 | 成员 |
|---|---:|---:|---|
| Wave 1 标杆 | 2 | 100% | Main、PMO |
| Wave 1 | 4 | 74.3% | Emily 72%、Echo 72%、Source 78%、守衡 75% |
| Wave 2 | 4 | 49.5% | Clone 45%、Vicky 50%、Market 50%、Shopify 53% |
| Wave 3 | 4 | 31.8% | GEO 22%、Radar 20%、Signal 25%、Daisy 60% |

### 1.4 知识资产与现状缺口

**已有资产**：

- `OGSM-v1-整合版-20261102.md`：24KB，批准口径。
- 10 份治理草稿：主键、RACI、三道 Gate、指标协议、P0 四条产线、场景能力补全等，合计约 650KB。
- 产品代码：`app/` 约 4,500 行，8 张表，45 条路由（20 个 API + 25 个页面/管理入口）。
- 报告与站点：24 个 `*.luteos.com`，多个 `/reports-view` 实测报告。
- Nowledge Mem 现状：3 个 Space（Default、内容合规审查、MAS Router），全局 1,386 个实体；**没有 PMO Space**。

**缺口**：

1. 产品事实散在 seed.py、模板、报告和飞书表里，开发 Agent 每次都要重新读。
2. OGSM 口径与指标误用没有进入“开机即注入”的硬规则，容易被“进度/声量/ROAS”带偏。
3. 14 个 Agent 的阶段、缺口、负责人没有可多跳检索的实体网络。
4. 没有本体，实体类型靠自动抽取，无法稳定表达 G→S→产线→能力→证据。
5. 没有 3 秒 Recall 与降级，记忆一旦接入主链路就会成为单点故障。

---

## 2. 记忆系统设计

### 2.1 四维治理映射

| SOP 维度 | 本项目落点 |
|---|---|
| 物理隔离 | 单空间 `abi-pmo`，`strict` 检索；与 Default、内容合规、MAS Router 物理隔离 |
| 认知金字塔 | L1 3 条 / L2 13 条 / L3 11 条 / L4 19 条，共 46 条 |
| 实体关系网 | 14 类对象 + 16 类关系；以 14 个 Agent 画像卡承载实体密度 |
| 读写自闭环 | Context Bundle 开机注入；3 秒 Recall + `try/except` 降级；写侧只做蒸馏，不做日志搬运 |

### 2.2 Space 与 Agent

| 项 | 值 | 说明 |
|---|---|---|
| Space ID | `abi-pmo` | 稳定 ID，后续 CLI 全部用它 |
| Space 名称 | `ABI PMO 管理站 Space` | 桌面端显示名 |
| 检索模式 | `strict` | 阻断跨项目记忆污染 |
| Agent ID | `pmo-guardian` | 与现有 `content-guardian`、`mas-router-dev` 命名一致 |
| Agent 角色 | `pmo_guardian` | 守门，不是业务决策者 |
| 默认 Space | `abi-pmo` | Context Bundle 自动加载 |
| 标签 | `pmo,ogsm,repo-guardian,evidence` | 便于跨工具识别 |

**为什么现在只建一个 Space**：

- 当前仓库的产品是 PMO 控制面，14 个 Agent 在这里是**被管理的组合实体**，不是 14 个独立开发仓库。
- 一个 Space 保证 OGSM 口径单一真源；拆 14 个空间会让 G/S/指标重复 14 份，直接违反“真源唯一性”。
- 预留命名：未来各 Agent 独立建仓时使用 `abi-agent-<slug>`（如 `abi-agent-emily`），通过 `share-with` 只读共享 PMO 口径，不复制。

### 2.3 命名、标签与枚举

**记忆 ID**：`pmo-<层>-<主题>`，稳定不变，更新用 upsert。

**受控标签**（每条最多 4 个）：

| 类别 | 标签 |
|---|---|
| 层级 | `identity`、`caliber`、`pitfall`、`history` |
| 域 | `ogsm`、`metric`、`gate`、`portfolio`、`agent`、`handoff`、`feishu`、`evidence`、`stage`、`product`、`risk`、`data` |

**unit_type 映射**（严格使用 8 个合法枚举）：

| 内容 | unit_type |
|---|---|
| 人格、红线、边界 | `decision` |
| O/G/S/指标/误用/主键/交接契约 | `fact` |
| Gate、四阶、四象限、管理节奏 | `procedure` |
| 踩坑与实证 | `learning` |
| 项目画像、组合快照、风险 | `context` |
| 已发生的里程碑 | `event`（本期不用） |

### 2.4 四层记忆卡（46 张）

完整目录见 `memory_cards.csv`。层级与标题如下。

#### L1 核心准则（3 张，importance 1.0，timeless）

| ID | 标题 |
|---|---|
| `pmo-l1-identity` | PMO Agent 身份与决策优先级 |
| `pmo-l1-redlines` | PMO 八条操作红线 |
| `pmo-l1-boundary` | 仓库物理边界与数据零读写纪律 |

#### L2 业务口径（13 张，importance 0.9，timeless）

| ID | 标题 |
|---|---|
| `pmo-l2-o-r1r4` | O 与 R1–R4 结果口径 |
| `pmo-l2-g1g3` | G1–G3 唯一结算指标与准入规则 |
| `pmo-l2-ogsm-generations` | 两代 OGSM 版本、O/G/S 编号对照与引用规则 |
| `pmo-l2-portfolio18` | 18 项产线登记与 14 产品组合 |
| `pmo-l2-metric-t1t5` | T1–T5 指标层与 decision_use |
| `pmo-l2-misuse12` | 12 条指标误用 M01–M12 |
| `pmo-l2-gates` | 三道 Gate 与回执规则 |
| `pmo-l2-stage4` | 四阶自进化标尺与 50% 封顶 |
| `pmo-l2-quadrant` | 四象限续投判定与四个熔断 |
| `pmo-l2-keys9` | 9 主键与对象级 A |
| `pmo-l2-handoff6` | 6 条跨岗交接链与 Handoff Packet |
| `pmo-l2-cadence` | PMO 管理节奏与有效校准会判据 |
| `pmo-l2-evidence` | 证据分级 L0–L4 与 measuredActions |

#### L3 避坑实证（11 张，importance 0.85，timeless）

| ID | 标题 |
|---|---|
| `pmo-l3-progress` | 进度不是结果：C1–C7 与 M11 |
| `pmo-l3-feishu-select` | 飞书多维表格单选静默丢弃与批量覆盖 |
| `pmo-l3-mime` | 飞书/文档 MIME 解析陷阱与 `.markdown` 规范 |
| `pmo-l3-evidence-gate` | 无 `evidence_url` 不得标已验证 |
| `pmo-l3-backup` | SQL 快照与每日备份防线 |
| `pmo-l3-roas` | 平台 ROAS/归因不得进经营结论 |
| `pmo-l3-adspend` | 加投前查移动页负载与 3P 失败率 |
| `pmo-l3-voc` | 全量 VOC 重算与 86x 增量管线 |
| `pmo-l3-stage-inflation` | Vicky 100%→50% 的进度挤水分 |
| `pmo-l3-ai-answer` | AI 提及 ≠ Best Overall 推荐 |
| `pmo-l3-claim` | 315 SKU 事实原子不等于可发布内容 |

#### L4 沉淀纪要（19 张，importance 0.75，past）

| ID | 标题 |
|---|---|
| `pmo-l4-portfolio` | 14 Agent 组合总览（Wave/Stage/均值） |
| `pmo-l4-emily` | Emily 项目画像 |
| `pmo-l4-clone` | Clone 项目画像 |
| `pmo-l4-vicky` | Vicky 项目画像 |
| `pmo-l4-geo` | GEO 项目画像 |
| `pmo-l4-radar` | Radar 项目画像 |
| `pmo-l4-echo` | Echo 项目画像 |
| `pmo-l4-market` | Market 项目画像 |
| `pmo-l4-source` | Source 项目画像 |
| `pmo-l4-signal` | Signal 项目画像 |
| `pmo-l4-shouheng` | 守衡 项目画像 |
| `pmo-l4-daisy` | Daisy 项目画像 |
| `pmo-l4-main` | Main 项目画像 |
| `pmo-l4-shopify` | Shopify 项目画像 |
| `pmo-l4-pmo` | PMO 项目画像 |
| `pmo-l4-capabilities` | 49 项能力分布与 34 项已验证基线 |
| `pmo-l4-team-sites` | 三人铁三角、RACI 与 24 站点 |
| `pmo-l4-waves-risks` | Wave 1–3 窗口、关键里程碑与风险 |
| `pmo-l4-product-surface` | 产品面 Map：12 页面/45 路由/飞书 Bot/自动化 |

### 2.5 记忆卡样例

**L1 示例：`pmo-l1-redlines`**

```text
我是 ABI 品牌 & 营销域的 PMO 守门 Agent。我只对 OGSM 承诺、口径与证据负责，不替业务做经营决策。
决策优先级：事实 > 证据 > 承诺 > 交付 > 叙事 > 流量。
八条红线：
1) 一个 G 只认一个结算数字，其余指标只做解释变量。
2) 进度不是结果；“已完成/进行中/方案中”只进交付台账，永不进 M 栏。
3) 没有基线的承诺不成立；T0 未锁定基线的目标不生效。
4) 无回执不等于通过；三道路径不得用会议纪要、老板特批、事后补签替代。
5) 不编数；材料里没有的数字留空并标“未验证”。
6) 不把平台归因、ROAS、mention 次数当经营结论。
7) 不跨项目写库；只读 14 个工作台的 API/报告/飞书表。
8) 不把草稿、日志、聊天记录直接写入长期记忆。
来源：OGSM-v1 §0/§6、three-gates §0。
```

**L2 示例：`pmo-l2-g1g3`**

```text
G1 需求：品牌自然需求新客 CAC ≤ B2×0.85（m-l1-cac@2，按 acquisition_source 分层；B2=2026-08-01~10-31 十二周中位数）。
G2 转化：MER ≥ B3×1.08（m-l1-mer@1）。
G3 留存：90 天同品类复购率 ≥ B4+3pp，且 CAC payback ≤ D−15 天（T+180 首读）。
每个 G 只能有一个结算主指标；声量、SOV、品牌词搜索、CVR、ROAS 只做领先/解释变量，不能单独判定达成。
若订单侧无法稳定标记 branded/organic，G1 退化为过程验收，不得宣称需求效率提升。
来源：OGSM-v1 §2、§9。
```

**L3 示例：`pmo-l3-stage-inflation`**

```text
四阶标尺有一条硬门禁：未上线独立飞书应用、未完成双向卡片回调的能力，进度最高封顶 50%。
Vicky 曾从 100% 下调到 50%：工作台在线、7 表每日重算、347 条报道同步，只证明 Stage 1；没有独立 @Vicky Bot 与 card.action.trigger 回调，就不能算 Stage 2。
任何进度上调前，必须同时出示三项证据：独立 Bot 在线、卡片回调真实发生、业务动作回写 measuredActions。
来源：templates/sop.html 四阶标尺、seed.py Vicky 画像、v7.1 commit。
```

### 2.6 写入、更新与淘汰

| 规则 | 做法 |
|---|---|
| 单一真源 | 同一主题只保留一个 canonical ID；新结论用同一 ID upsert，不新建平行记忆 |
| 来源可回指 | 每条记忆末尾必须写 `来源：文件 §节 / 路由 / commit` |
| 长度 | 单条 150–600 字；超过 600 字拆成“定义 + 案例”两条 |
| 冲突 | 以 OGSM v1 + 当前代码/数据库为准；草稿只进 Library，不进记忆 |
| 时效 | L4 画像标注 `as_of: 2026-11-04`；每周更新 Working Memory，每月重算 L4 |
| 淘汰 | 被新版本替代的记忆不删除，保留版本链；过期项目画像改为 `archived` |
| 禁入 | 密钥、个人信息、未批准草稿、原始聊天/日志、表格逐行数据 |

---

## 3. Library 真源归档

### 3.1 入库清单（10 份）

| ID | 优先级 | 真源 | 入库文件名 | 标签 | 用途 |
|---|---|---|---|---|---|
| L01 | P0 | `OGSM/OGSM-v1-整合版-20261102.md` | `ogsm-v1.markdown` | `ogsm,caliber,decision` | O/G/S/M/产线/治理唯一口径 |
| L02 | P0 | `OGSM/ogsm-web/README.md` | `pmo-product-readme.markdown` | `product,architecture` | 产品定位、取舍、运行方式 |
| L03 | P0 | `app/templates/sop.html` | `pmo-sop-4stage.txt` | `sop,stage,raci` | 四阶标尺、50% 门禁、岗位边界 |
| L04 | P0 | `app/templates/sites.html` | `pmo-handoff-chains.txt` | `handoff,contract` | 6 条交接链与 Packet |
| L05 | P0 | `app/models.py` | `pmo-data-model.txt` | `data,schema` | 8 张表与字段语义 |
| L06 | P0 | `brand-agent-pmo-metric-and-experiment-protocol-draft-20261101.md` | `pmo-metric-protocol.markdown` | `metric,experiment` | T1–T5、12 条误用、四段式 M |
| L07 | P1 | `brand-agent-ogsm-three-gates-draft-20261101.md` | `pmo-three-gates.markdown` | `gate,compliance` | 状态机、回执、拒绝记录 |
| L08 | P1 | `brand-agent-ogsm-key-registry-draft-20261101.md` | `pmo-key-registry.markdown` | `data,key` | 9 主键、对象级 A |
| L09 | P1 | `brand-agent-ogsm-raci-matrix-draft-20261101.md` | `pmo-raci.markdown` | `raci,governance` | 问责边界与熔断 |
| L10 | P1 | `app/main.py` | `pmo-api-surface.txt` | `product,api,feishu` | 页面/路由/飞书/自动化 |

### 3.2 解析规范（避坑红线）

- **所有 `.md` 必须先复制为 `.markdown`**。`nmem-server` 当前对 `.md` 有 MIME 误判，会报 `did not look like readable text`，状态不会变成 `indexed`。
- HTML 只抽正文（四阶标尺、交接链表、岗位说明），不整页灌入。
- Python 只抽模块 docstring、类名、字段名、路由，不灌全文件。
- 入库后逐条检查 `nmem library list --space abi-pmo`，状态必须全为 `indexed`，错误数 0。
- 不入库：PPT 方案、治理思维导图、场景能力草稿、P0 四条产线草稿、归档历史、报告原始 HTML、`.lody/attachments`、任何密钥文件。

### 3.3 执行命令（Ticket PMO-MEM-006）

```bash
nmem library add --space abi-pmo \
  -c "OGSM v1 唯一批准口径" \
  -l ogsm -l caliber -l decision \
  /tmp/pmo-mem/ogsm-v1.markdown

# 其余 9 份同理；每份单独 comment 与 labels
nmem library list --space abi-pmo
```

---

## 4. 知识图谱本体

### 4.1 对象类型（14 类）

| Key | 显示名 | 说明 |
|---|---|---|
| `Objective` | O 战略意图 | 一年后要变成什么样的一句话总目标 |
| `Goal` | G 结果目标 | G1/G2/G3，每个只认一个结算指标 |
| `Strategy` | S 战略打法 | 怎么赢，必须挂产线并写反证条件 |
| `Metric` | 指标 | T1–T5 与版本化口径 |
| `ProductAgent` | 专家 Agent/产品 | 14 个独立飞书 Agent 与工作台 |
| `Capability` | 能力项 | 49 项可验收能力 |
| `HandoffChain` | 跨岗交接链 | 6 条链与 Handoff Packet |
| `Gate` | 门禁 | Claim/授权/实验，无回执不迁移 |
| `Evidence` | 证据资产 | 实测报告、evidence_url、回执 |
| `Owner` | 责任人或角色 | 段 A、G-A、PMO、铁三角 |
| `Workbench` | 工作台站点 | 24 个 `*.luteos.com` |
| `DeliveryWave` | 交付波次 | Wave 1–3 与 Stage |
| `BusinessAction` | 业务动作 | measuredActions 回写 |
| `Risk` | 风险/未决项 | 未锁基线、口径冲突、依赖缺口 |

### 4.2 关系类型（16 类）

| Key | 显示名 | 典型方向 |
|---|---|---|
| `DECOMPOSES_TO` | 分解为 | O → G |
| `SUPPORTS` | 支撑 | S → G |
| `MEASURED_BY` | 由指标结算 | G/Capability → Metric |
| `OWNS` | 负责 | Owner → ProductAgent/Capability |
| `DELIVERS` | 交付能力 | ProductAgent → Capability |
| `DEPENDS_ON` | 依赖 | Capability → Capability |
| `HANDS_OFF_TO` | 交接给 | ProductAgent → ProductAgent |
| `PARTICIPATES_IN` | 参与交接链 | ProductAgent → HandoffChain |
| `GATED_BY` | 受门禁约束 | Capability/Evidence → Gate |
| `EVIDENCED_BY` | 由证据支撑 | Capability → Evidence |
| `HOSTED_ON` | 部署于工作台 | ProductAgent → Workbench |
| `EVOLVES_IN` | 在波次中演进 | Capability → DeliveryWave |
| `BLOCKS` | 阻断 | Gate → Capability/BusinessAction |
| `CONTRIBUTES_TO` | 贡献于 | Capability → Goal |
| `TRACKS` | 跟踪 | BusinessAction → Capability |
| `MITIGATES` | 缓解风险 | Risk → Goal/Capability |

### 4.3 图谱装配策略

1. **不逐条造 49 个能力记忆**。用 14 张项目画像卡承载 49 个能力名称，避免 49 条低质碎片稀释检索。
2. **每张项目卡固定字段**：Goal、Strategy、Workbench、Owner、Wave/Stage/进度、核心能力、当前缺口、关键交接、`as_of`。
3. **实体别名统一**：`Emily`/`社媒 Agent`/`social.luteos.com` 指向同一 `ProductAgent`；`G1`/`需求`/`CAC` 在同一 `Goal` 下。
4. **本体作用域**：优先 `--scope space --space-id abi-pmo`，避免污染 Default、内容合规、MAS Router 的全局词汇；若 CLI 不支持，退回 global 但所有 key 加 `PMO` 前缀。
5. **应用后检查**：`nmem ontology show` 的 14 类实体覆盖数 > 0；`nmem graph expand` 能从任一项目卡跳到 Goal、Capability、HandoffChain。

### 4.4 本体草案

已生成：`ontology_patch.draft.json`。执行时先校验 JSON，再 apply：

```bash
python3 -m json.tool OGSM/ogsm-web/docs/memory/ontology_patch.draft.json >/dev/null
nmem ontology apply \
  --file OGSM/ogsm-web/docs/memory/ontology_patch.draft.json \
  --scope space --space-id abi-pmo
nmem ontology show
```

---

## 5. Working Memory 与 Rules

### 5.1 Working Memory

```markdown
## Focus Areas
- **当前产品**：ABI PMO 管理站（OGSM/ogsm-web），FastAPI + Postgres + SSR；v7.1 已上线负责人负载矩阵、验收证据硬拦截、飞书卡片回写与 SQL 快照。
- **当前组合**：14 Agent / 49 能力 / 34 已验证 / 能力均值 57.6% / 24 站点；Wave 1 均值 74.3%，Wave 2 49.5%，Wave 3 31.8%。
- **本期收口**：11 月 Wave 1–2 收口（Emily、Echo、Source、守衡、Clone、Vicky、Market、Shopify）；12 月 Wave 3（GEO、Radar、Signal、Daisy）。
- **治理焦点**：基线 B1–B6 未锁、G1 的 acquisition_source 分层未证、G3 180 天窗口与季度考核冲突。

## Briefing
- **项目角色**：PMO 守门 Agent，只对承诺、口径与证据负责，不替业务做决策。
- **核心准则**：一个 G 一个结算数字；进度不是结果；没有基线不承诺；无回执不等于通过。
- **近期动态**：v7.1 把“已验证”与 evidence_url 硬挂钩；无证据自动标“待补证据”并拦截。
```

### 5.2 三条常驻规则

| Rule ID | Priority | Scope | 内容摘要 |
|---|---:|---|---|
| `pmo_core_persona` | 100 | space | 人设、决策优先级、八条红线 |
| `pmo_repo_boundary` | 90 | space | 仓库边界、只读 14 个工作台、自有 Postgres、记忆写入纪律 |
| `pmo_memory_write_discipline` | 80 | space | 每条记忆带来源、单条 ≤600 字、同主题 upsert、禁入清单 |

执行命令：

```bash
nmem rules upsert pmo_core_persona \
  --title "PMO 人格内核与决策优先级" \
  --body-file /tmp/pmo-mem/rule-persona.md \
  --scope space --space abi-pmo --priority 100 \
  --tags "persona,rules,governance"

nmem rules upsert pmo_repo_boundary \
  --title "PMO 仓库物理边界与数据零读写纪律" \
  --body-file /tmp/pmo-mem/rule-boundary.md \
  --scope space --space abi-pmo --priority 90 \
  --tags "boundary,infra"

nmem rules upsert pmo_memory_write_discipline \
  --title "PMO 记忆写入与来源纪律" \
  --body-file /tmp/pmo-mem/rule-memory.md \
  --scope space --space abi-pmo --priority 80 \
  --tags "memory,governance"
```

---

## 6. 运行时集成

### 6.1 开发 Agent 开机唤醒

在 `.claude/settings.local.json` 的 `env` 中固化（该文件已被全局 gitignore）：

```json
{
  "env": {
    "NMEM_SPACE": "abi-pmo",
    "NMEM_AGENT_ID": "pmo-guardian"
  }
}
```

同时新增 `AGENTS.md`（或 `CLAUDE.md`）会话开场约定：

```markdown
## 会话启动
1. 先运行 `nmem context --space abi-pmo --agent-id pmo-guardian`，加载 Rules 与 Working Memory。
2. 涉及 OGSM 口径、指标、Gate、项目阶段的问题，先检索 `nmem memories search "<query>" --space abi-pmo -n 3`。
3. 记忆检索失败或超时，不阻塞主任务；把“未检索到”写明，不猜。
4. 会话结束前，只把新产生的决策、口径、避坑、画像写入 `abi-pmo`；原始日志与草稿不写。
```

### 6.2 3 秒 Recall + 优雅降级

新增 `OGSM/ogsm-web/app/memory.py`（P1，可选但推荐）：

```python
def recall_durable_memories(query: str, limit: int = 2,
                            min_score: float = 0.5,
                            space: str = "abi-pmo") -> str:
    """检索 PMO 口径/红线/避坑；失败、离线或无匹配时静默返回空串。"""
    if not query or not query.strip():
        return ""
    try:
        import json, os, subprocess
        cli = os.environ.get("NMEM_CLI_PATH", "nmem")
        target = os.environ.get("NMEM_SPACE", space)
        cmd = [cli, "--json", "memories", "search", query.strip()[:100],
               "--space", target, "-n", str(limit)]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
        if res.returncode != 0:
            return ""
        data = json.loads(res.stdout)
        items = data if isinstance(data, list) else data.get("items", data.get("memories", []))
        blocks = []
        for m in items:
            score = float(m.get("score") or 0.0)
            if score < min_score:
                continue
            title = (m.get("title") or "").strip()
            content = (m.get("content") or m.get("snippet") or "").strip()
            if title and content:
                blocks.append(f"• 【{title}】(匹配度 {score:.2f})\n{content}")
        return ("【PMO 持久记忆】\n" + "\n\n".join(blocks)) if blocks else ""
    except Exception:
        return ""
```

测试要求：

- 真实检索：`G1 结算指标` 返回非空且 Top1 命中。
- 超时降级：把 `NMEM_CLI_PATH` 指向 `sleep 5` 的假命令，函数在 3 秒内返回空串，不抛异常。
- 离线降级：关闭 nmem 服务或改错 URL，函数返回空串，主链路继续。

### 6.3 产品侧（P2，本期不做）

PMO 管理站目前没有 LLM 对话入口，强行加“记忆搜索页”会增加维护面且没有使用场景。等出现“问 PMO”需求时，再基于 `recall_durable_memories` 增加只读 `/api/memory/recall` 与页面面板。本期只服务开发 Agent 与飞书 Bot 的上下文，不改产品 UI。

---

## 7. 执行计划

### 7.1 阶段与时间

| 阶段 | 工作 | 产出 | 估时 | Gate |
|---|---|---|---:|---|
| P0 冻结 | 真源清单、敏感信息扫描、记忆卡目录 | `sources.yaml`、`memory_cards.csv` | 0.5d | 10 份真源确认、0 密钥 |
| P1 建底座 | Space、Agent、3 条 Rules、Working Memory | Context Bundle 可读 | 0.5d | 4 项全部存在 |
| P2 归档 | 10 份 `.markdown/.txt`、Library 入库 | `indexed` 10/10 | 0.5d | 错误数 0 |
| P3 蒸馏 | L1/L2/L3/L4 共 46 条 | 46 条可检索记忆 | 1.5d | 去重、来源、冲突检查 |
| P4 图谱 | 本体 apply、实体补链、别名治理 | 14 类实体有覆盖 | 0.5d | 项目卡可多跳 |
| P5 运行时 | 环境变量、AGENTS.md、Recall Helper + 测试 | 开机注入、3 秒降级 | 0.5d | 测试全绿 |
| P6 验收 | 12 Golden Query、SOP 8 条、提交与交接 | 验收报告、commit | 0.5d | 10/12 Top1 ≥ 0.70 |

### 7.2 依赖链

```text
P0 冻结
  ├─ P1 建底座 ── P3 蒸馏 ── P4 图谱 ── P6 验收
  ├─ P2 归档 ──── P3 蒸馏
  └─ P5 运行时 ── P6 验收
```

### 7.3 并行策略

- 两人并行：一人做 P1+P2（底座与归档），一人做 P0+P3 的 L1/L2 草稿；P3 后半段合并。
- 单人执行：按 P0→P1→P2→P3→P4→P5→P6 顺序，L4 项目卡最后批量生成。
- 不要在 P3 之前 apply 本体；否则图谱会先按默认 `CONCEPT` 抽取，后续 retype 成本高。
- 全程不与当前项目并行任务争资源：不重启 `pmo-web`/Postgres/飞书长连接；不重跑 `app.seed` 或迁移；不触发全量 `nmem models reindex`；`nmem` 只做增量写入与检索，单次命令超时 30 秒内。

---

## 8. Ticket 拆解

完整可导入版本见 `TICKETS.csv`。默认执行者 `AI Agent`，验收者 `PMO`；涉及口径的 Ticket 需 `刘华丽` 复核，涉及产品事实的需 `吴雨宁` 复核，涉及仓库/环境的需 `周健` 批准。

| ID | Ticket | 估时 | 依赖 | 验收标准 |
|---|---|---|---:|---|---|
| PMO-MEM-001 | 冻结 10 份真源、扫描密钥、确认 46 张卡目录 | 3h | — | `sources.yaml` 与 `memory_cards.csv` 评审通过；密钥扫描 0 命中 |
| PMO-MEM-002 | 创建 `abi-pmo` strict Space 与 `pmo-guardian` Agent | 1h | 001 | `nmem spaces list` 显示 strict；`nmem agents list` 默认 Space 正确 |
| PMO-MEM-003 | 注入 3 条 Space Rules | 1h | 002 | `nmem context` 输出 3 条规则，priority 100/90/80 |
| PMO-MEM-004 | 初始化 Working Memory | 1h | 002 | 含 Focus Areas 与 Briefing，数字与 2026-11-04 基线一致 |
| PMO-MEM-005 | 生成 10 份可解析副本（`.markdown/.txt`） | 3h | 001 | 10 个文件存在、非空；`.md` 已转 `.markdown` |
| PMO-MEM-006 | 批量入库 Library 并校验 `indexed` | 1h | 005 | 10/10 `indexed`，错误 0 |
| PMO-MEM-007 | 蒸馏 L1 核心准则 3 条 | 2h | 002,003,006 | 3 条均为 `decision`/1.0/timeless，含来源 |
| PMO-MEM-008 | 蒸馏 L2 业务口径 13 条 | 4h | 006 | 13 条 `fact/procedure`/0.9，数字与 OGSM v1 一致 |
| PMO-MEM-009 | 蒸馏 L3 避坑实证 11 条 | 4h | 006 | 11 条 `learning`/0.85，每条有实证来源 |
| PMO-MEM-010 | 蒸馏 L4 组合画像 19 条 | 5h | 006 | 14 个项目卡字段齐全；4 张聚合卡数字可回算 |
| PMO-MEM-011 | 去重、冲突、来源、长度校验 | 3h | 007–010 | 46 条、0 重复 ID、100% 来源、单条 ≤600 字 |
| PMO-MEM-012 | 编写并校验 ontology patch | 3h | 002 | JSON 合法；14 对象 + 16 关系；scope 明确 |
| PMO-MEM-013 | apply 本体并检查覆盖率 | 1h | 012 | `ontology show` 14 类实体覆盖 > 0 |
| PMO-MEM-014 | 核心实体补链与别名治理 | 3h | 011,013 | 14 Agent、6 链、G1–G3 可从记忆多跳到达 |
| PMO-MEM-015 | 环境变量与 `AGENTS.md` 开机约定 | 1h | 002 | 新会话能自动加载 Context Bundle |
| PMO-MEM-016 | 3 秒 Recall Helper + 降级测试 | 4h | 002,011 | 真实检索通过；超时/离线返回空串不抛错 |
| PMO-MEM-017 | 12 条 Golden Query 验收 | 2h | 011,013,016 | 10/12 Top1 ≥ 0.70；12/12 Top3 命中 |
| PMO-MEM-018 | SOP 8 条验收、提交与交接 | 2h | 全部 | 8/8 + 6/6；约定式提交；交接摘要落库 |

**总计**：约 44 小时。

---

## 9. 验收标准

### 9.1 SOP 8 条硬标准

| # | 标准 | 本项目验证方式 |
|---|---|---|
| 1 | Space 为 `strict` | `nmem spaces list` 显示 `abi-pmo` strict |
| 2 | Agent 默认 Space 正确 | `nmem agents list` 中 `pmo-guardian` → `abi-pmo` |
| 3 | Context Bundle 完整 | `nmem context --space abi-pmo --agent-id pmo-guardian` 含 Space/Rules/WM |
| 4 | Library 全 `indexed` | `nmem library list --space abi-pmo` 10/10 切片成功；`extracted` 与 `indexed` 均算成功态，错误 0 |
| 5 | 图谱可视 | 桌面端 `⌘5` 选 `ABI PMO 管理站 Space`，可见实体网络 |
| 6 | 语义检索高置信 | 12 条 Golden Query，10 条 Top1 ≥ 0.70 |
| 7 | 单元测试通过 | `test_pmo_nmem_recall.py` 真实检索 + 超时降级全绿 |
| 8 | 规范化提交 | `feat(memory): ...` 或 `docs(memory): ...` |

### 9.2 PMO 专项 6 条

| # | 标准 | 验证 |
|---|---|---|
| 1 | 46 条记忆卡与目录一致 | `memory_cards.csv` 46 行，实际 count 46 |
| 2 | 无平行真源 | 同主题只有一个 canonical ID；冲突项为 0 |
| 3 | L4 画像数字可回算 | 14 Agent 进度、49 能力、34 已验证与 seed.py 一致 |
| 4 | 跨空间隔离 | 从 Default 空间搜 `G1 结算指标` 不返回 `abi-pmo` 记忆 |
| 5 | 产品主链路不受影响 | 停掉 nmem 后，`/`、`/board`、`/roadmap` 正常 |
| 6 | 变更留痕 | 环境变量、AGENTS.md、ontology patch、tickets 均进 git |

### 9.3 Golden Query（12 条）

| # | Query | 期望 Top1 ID |
|---|---|---|
| 1 | G1 的结算指标是什么 | `pmo-l2-g1g3` |
| 2 | 哪些指标不能进预算 | `pmo-l2-misuse12` |
| 3 | 四象限续投怎么判 | `pmo-l2-quadrant` |
| 4 | Stage 4 的硬门禁是什么 | `pmo-l2-stage4` |
| 5 | Emily 现在什么阶段 | `pmo-l4-emily` |
| 6 | Vicky 为什么从 100% 降到 50% | `pmo-l3-stage-inflation` |
| 7 | 飞书多维表格单选为什么会丢 | `pmo-l3-feishu-select` |
| 8 | 没有 evidence_url 能不能标已验证 | `pmo-l3-evidence-gate` |
| 9 | 6 条交接链的契约对象是什么 | `pmo-l2-handoff6` |
| 10 | 哪些基线还没锁定 | `pmo-l4-waves-risks` |
| 11 | PMO 的操作红线有哪些 | `pmo-l1-redlines` |
| 12 | 9 个主键是什么 | `pmo-l2-keys9` |

判定：10/12 Top1 ≥ 0.70；12/12 Top3 命中；跨空间查询 0 命中。

---

## 10. 风险与对策

| # | 风险 | 影响 | 对策 |
|---|---|---|---|
| 1 | `.md` MIME 误判 | Library 不入库 | 统一复制为 `.markdown`，入库后查 `indexed` |
| 2 | 本体作用域污染 | 其他 Space 词汇被改 | 优先 space scope；失败则 global + `PMO` 前缀 |
| 3 | 草稿灌入稀释检索 | Top1 置信度低 | 只入库 10 份；草稿只做 Library，不做记忆 |
| 4 | 46 条仍出现重复 | 检索冲突 | 稳定 ID + upsert + 去重 Ticket |
| 5 | 进度数字过期 | 回答错误 | L4 标 `as_of`；WM 每周更新；月度重算 |
| 6 | 密钥/个人信息入库 | 合规事故 | 入库前扫描；禁入清单；只存摘要 |
| 7 | nmem 离线拖垮主链路 | 产品不可用 | 3 秒超时 + 全捕获；产品不依赖记忆 |
| 8 | 跨空间污染 | 口径串台 | strict + 隔离测试 |
| 9 | 文档与代码不一致 | 记忆写错 | 优先级：代码/数据库 > OGSM v1 > 草稿；冲突记录到 L3 |
| 10 | 图谱实体噪声 | 图谱不可读 | 只用 14 类对象；不逐条造 49 能力 |
| 11 | 影响并行后台任务 | 生产服务抖动 | 不重启容器、不跑 seed/迁移/全量 reindex；nmem 命令 ≤30 秒；失败只回滚本次写入 |

---

## 11. 待确认决策

| # | 决策 | 推荐 | 备选 |
|---|---|---|---|
| 1 | Space ID 与 Agent ID | `abi-pmo` / `pmo-guardian` | 沿用 `pmo` / `pmo-agent` |
| 2 | 单空间还是 14 空间 | 单空间，14 Agent 作为实体 | 14 个 `abi-agent-*` 空间 |
| 3 | Library 范围 | 10 份（6 P0 + 4 P1） | 只入 6 份 P0 |
| 4 | 产品侧记忆入口 | 本期不做，P2 再做 | 本期加 `/api/memory/recall` |
| 5 | Ticket 去向 | 先落 `TICKETS.csv`，批准后再推 Linear | 直接推 Linear `PRA` |
| 6 | 执行时机 | 方案批准后一次性执行 P0–P6 | 先做 P0–P2 试点 |

---

## 12. 交付物

| 文件 | 用途 |
|---|---|
| `OGSM/ogsm-web/docs/memory/PMO-MEMORY-KG-PLAN.md` | 本方案 |
| `OGSM/ogsm-web/docs/memory/memory_cards.csv` | 46 张记忆卡目录，执行时逐条填内容 |
| `OGSM/ogsm-web/docs/memory/TICKETS.csv` | 18 个 Ticket，可导入 Linear/Jira |
| `OGSM/ogsm-web/docs/memory/ontology_patch.draft.json` | 14 对象 + 16 关系本体草案 |
| `OGSM/ogsm-web/docs/memory/sources.yaml` | 10 份真源、排除项、解析检查 |

**下一步**：确认 §11 的 6 个决策后，从 `PMO-MEM-001` 开始执行；先建 Space 与 Rules，再入库 Library，最后蒸馏与图谱。不要在方案未批准前写入 `nmem`，避免把未定口径固化成“记忆真源”。
