---
title: 品牌 Agent 11×18 RACI 矩阵与交接契约
doc_type: analysis
module: brand-agent
topic: raci-matrix
status: draft
created: 2026-11-01
updated: 2026-11-01
owner: self
source: human+ai
---

# 品牌 Agent 11×18 RACI 矩阵与交接契约

## 0. 硬约束（不满足即废表）

矩阵的判定单位是**问责单元**。11 个段默认等于 11 个单元；S6 因平台级责任分界拆为 S6-DTC 与 S6-AMZ，共 12 个单元。拆分条件写在 §1.3 第 3 条，除此之外任何段不得拆。

| # | 约束 | 判定方式 | 本表结果 |
|---|---|---|---|
| 1 | 每个问责单元有且仅有一个 A | 数矩阵每行的 A 个数 | 12 个单元各 1 个 A，合计 12 |
| 2 | Echo/Source/Daisy/Main/PMO 必须有明确归位 | 查 §3.3 定位表 | Source 持 S10 A，PMO 持 S11 A；Daisy/Echo 段级 0 A（持对象级问责）；Main 裁撤 |
| 3 | 每条产线最多持 1 个段 A | 数矩阵每列的 A 个数 | 12 条各 1 个，6 条 0 个，0 条 ≥2 个 |
| 4 | 无产线在 3 段以上持 A | 同上 | 0 条；最高为 1 |
| 5 | S5 与 S8 必须有 A | 查行 | Paid Media 与 Retention，均为 P0 产线，已写明 |
| 6 | 14 列基线（不含 P0）下无 A 的段必须单列 | 查 §5.1 | 4 个整段 + 3 个子项 |

**S6 必须拆的理由**：不拆时 Shopify 与 Amazon 站内共持一个 A。Shopify 的 A 覆盖 sessions→PDP→ATC→checkout→purchase 与站点主题、支付、订单；Amazon 站内的 A 覆盖 ASIN、Buy Box、Account Health、listing 与 SP/SB/SD 结构。两者的失败方式不同、可杀死主体不同（一个封店、一个关停独立站），共持一个 A 等于两件事都无人问责。这是全表唯一的拆分，也是判定「段是否切干净」的样板：**只有当段内存在独立可杀死的账号或资质主体时才允许拆**。

## 1. 记号与计数规则

### 1.1 五个取值

| 取值 | 定义 | 判据 |
|---|---|---|
| A | 唯一问责。该段主指标未达成时，第一个被问的人 | 只有一个人；不因「多方共管」而分摊 |
| R | 执行。必须在该段交付具体产物 | 有独占动作，不是「参与讨论」 |
| C | 协商。其否决可使交接阻断 | 必须有否决动作；无否决权的一律记 I |
| I | 知会。只读订阅，不参与决策 | 不承担任何交付责任 |
| — | 无关 | 填 — 的产线不得在评审会上就该段发言或指派任务 |

### 1.2 两类 A 不互换

段级 A 对**经营结果**问责；对象级 A 对**对象唯一性与版本**问责。二者不可互相折算：持对象级 A 不自动获得段 A，持段 A 也不得写别人域内的对象。

| 主键 | 对象级 A（唯一写入口） | 是否同时持段 A |
|---|---|---|
| event_id | Signal | 是（S9） |
| claim_id | Daisy | 否 |
| evidence_id | Daisy | 否 |
| script_id | Emily | 是（S3） |
| variant_id | Clone | 否 |
| asset_id | Clone（content_*）、Daisy（evidence_file）、Vicky（earned_coverage） | 部分（Vicky 持 S4） |
| ad_id | 投放侧（过渡期 PMO steward） | 是（Paid Media 持 S5） |
| creator_id | Radar | 否 |
| ai_answer_snapshot_id | GEO | 否（零段 A，靠对象级 A 站立） |
| asset_rights | Radar | 否 |

`asset_rights` 是字典 §0.1 的子记录（挂在 `asset_id` 下），不占主键位；单列一行是因为它是授权 gate 的底层对象，唯一挡住付费花钱的闸门必须点名到人。

`ai_answer_snapshot_id` 是 2026-11-02 增补的第 9 主键（字典 §14）。它解决的是本文件 §7 风险 3 与指标字典 §14.3 末段共同指认的缺口：**GEO 两类 A 都没有**。增补后 GEO 持对象级 A，**段级仍为 0 A**——它不对经营结果问责，只对「AI 快照的完整性与可复测性」问责。这把 GEO 从「必进收缩名单」拉回到「可类比的零段 A 产线」，与 Clone/Radar/Daisy/Echo 同形。

### 1.3 A 的四条判据

1. A 落在主指标落在谁报表上，不落在谁干活最多上。Clone 一条产线出 60% 的素材，但 CTR 的问责在 S3 的 A（Emily）与 S5 的 A（Paid Media）。
2. 一列一段一 A。跨段持 A 说明范围没切清，必须在当季切分。
3. 平台或市场有独立可杀死主体（独立账号、独立资质、独立封店风险）才允许拆子段。当前只有 S6 满足；S4 的三个 sub 渠道（达人/媒体/联盟）共用同一套对外披露与授权规则，不拆。
4. A 可被 90 天裁决。无 A 的产线不进裁决，只做成本核算——这是零 A 产线的真实处境。

### 1.4 列头对照

Em=Emily、Cl=Clone、Vi=Vicky、Ge=GEO、Ra=Radar、Ec=Echo、Mk=Market、So=Source、Sg=Signal、Sh=守衡、Da=Daisy、Mn=Main、Sp=Shopify、Pmo=PMO、Pd=Paid Media、Cs=CS & After-sales、Rt=Retention/Subscription、Az=Amazon 站内。

## 2. 11×18 RACI 矩阵

| 段 | Em | Cl | Vi | Ge | Ra | Ec | Mk | So | Sg | Sh | Da | Mn | Sp | Pmo | Pd | Cs | Rt | Az |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 品类机会与选品 | I | — | I | I | C | R | **A** | R | C | C | I | — | R | C | C | C | I | R |
| S2 产品定义与合规准入 | C | C | I | I | I | C | R | C | I | **A** | R | — | C | C | I | C | I | R |
| S3 内容与素材供给 | **A** | R | C | R | C | R | C | R | C | R | R | C | C | I | R | C | C | R |
| S4 达人·媒体·联盟（earned） | C | C | **A** | C | R | C | I | R | C | C | I | — | I | C | C | I | I | I |
| S5 付费投放 | C | R | I | I | R | I | I | R | C | R | C | C | R | C | **A** | I | R | R |
| S6-DTC 转化承接（独立站） | C | C | I | C | I | R | C | C | I | R | C | R | **A** | I | R | C | C | — |
| S6-AMZ 转化承接（Amazon 店铺） | C | R | I | I | I | R | C | R | I | R | C | C | C | I | R | R | I | **A** |
| S7 履约与售后 | I | I | R | I | I | R | I | I | C | C | I | C | R | C | C | **A** | C | R |
| S8 复购与 LTV | I | I | I | I | I | R | C | C | I | C | I | C | R | C | R | R | **A** | R |
| S9 品牌资产（搜索·心智·AI） | C | I | R | R | C | C | C | R | **A** | C | C | I | C | R | C | C | C | C |
| S10 数据与决策基建 | C | C | C | C | C | C | C | **A** | R | C | R | R | C | R | C | C | C | C |
| S11 组织与治理 | C | I | C | I | I | I | C | R | C | R | R | R | C | **A** | C | C | C | C |

簇密度说明：S10 与 S11 两行 C 密集是横切段的正常形态，判据不是 C 的数量而是 R 的独占动作是否清晰。S10 的 R 只有四个：So 之外的 Sg（声量口径）、Da（事实库与权限台账）、Mn（工程执行）、Pmo（指标字典与实验协议）；S11 的 R 只有三个：So（SLA）、Sh（判定回执）、Da（权限与冲突）、Mn（工具交付）。

## 3. 矩阵自检

### 3.1 每个单元的 A 与其承担的主指标

| 单元 | A | 该 A 承担的主指标（只列一个，其余为解释变量） | 14 列基线是否有 A |
|---|---|---|---|
| S1 | Market | 新品 90d 动销率 | 有 |
| S2 | 守衡 | claim 可证率 | 有（仅内容侧；资质侧无） |
| S3 | Emily | 周素材产出中通过 claim 预检的比例 | 有 |
| S4 | Vicky | buyer guide 收录数 | 有 |
| S5 | Paid Media | MER 与增量 ROAS | **无** |
| S6-DTC | Shopify | 独立站 CVR | 有 |
| S6-AMZ | Amazon 站内 | Amazon 侧 CVR 与 Buy Box 赢得率 | **无** |
| S7 | CS | 首响中位与退货原因四层完成率 | **无** |
| S8 | Retention | 90 天复购率与 CAC payback | **无** |
| S9 | Signal | 品牌搜索占比与 SOV | 有 |
| S10 | Source | 归因覆盖率与数据延迟 | 有（但 6 条线争夺） |
| S11 | PMO | 指标口径一致率与承诺签署率 | 有（但被当成工具而非治理） |

### 3.2 每条产线的 A 计数

| 产线 | 段 A 数 | 对象级 A | 结论 |
|---|---|---|---|
| Market、守衡、Emily、Vicky、Paid Media、Shopify、Amazon 站内、CS、Retention、Signal、Source、PMO | 各 1 | 见 §1.2 | 符合约束 3 与 4 |
| Clone | 0 | variant_id、asset_id（content_*） | 对象级问责成立，段级无 A；续投依据只能是变体质量与产能 |
| Radar | 0 | creator_id | 对象级问责成立；S4 的 R 是达人侧唯一动作，不持 A |
| Daisy | 0 | claim_id、evidence_id、asset_id（evidence_file） | 横切支撑，对象级问责成立 |
| Echo | 0 | 无（taxonomy 为版本化对象，未进 8 主键） | 纯横切支撑，问责靠 taxonomy 版本与抽检一致率 |
| GEO | 0 | ai_answer_snapshot_id（第 9 键，2026-11-02 增补） | 对象级问责成立；段级仍 0 A。见 §1.2 补记与 §7 风险 3（已降级为「可与 Clone/Radar 类比」） |
| Main | 0 | 无 | 裁撤出产线清单，降为工程执行层 |

### 3.3 五条挂不上的产线的定位

| 产线 | 定位 | 依据 | 不接受的后果 |
|---|---|---|---|
| Source | 横切支撑，S10 的 A | 采集、实体对齐、数据契约、断流降级是 S10 主指标的物理来源；且 B-08 落库方 | 若只做 R，S10 变成 6 条线共管的口径战场，归因覆盖率无人负责 |
| PMO | 横切支撑，S11 的 A | 目标下发、承诺签署、跨线仲裁、90 天裁决是 S11 的全部内容 | 若只做 I，PMO 退化为进度表，按 §4.2 应直接砍掉 |
| Daisy | 横切支撑，段级 0 A | 它的问责是对象级的（claim/evidence 唯一写入口）与治理级的（权限台账、冲突裁决） | 若强行给段 A，会与守衡（S2）、Emily（S3）的裁定权冲突，重演 claim 三源 |
| Echo | 横切支撑，段级 0 A | VOC taxonomy 与 objection 主榜是事实层，不是经营结果；S1/S3/S7/S8 都只读它 | 若给 S9 或 S7 的 A，会与 Signal 的声量口径、CS 的工单处置打架 |
| Main | 裁撤（移出产线清单） | 工程职能不是业务产线；模型评测与工具交付并入 S10 的 R，不再单列 | 若保留为产线，S11 会出现第二条工程治理线，与 PMO 争夺「交付进度」的解释权 |

## 4. 逐段交接契约

停机 = 下游该段不得开工、不得进入下一个状态机。降级 = 下游可继续，但必须带降级标记并限期补齐。二选一，无第三种。

| 上游段 | 上游 → 下游 | 交接字段（引用主键字典） | 交接触发条件 | SLA | 验收签字 | 失败模式 |
|---|---|---|---|---|---|---|
| S1 | Market → 守衡（S2 A） | opportunity_id、category_id、price_band、competitor_set[]、compliance_gap[]、Echo 原话样本引用 | 机会卡判定为「进入」，且有 ≥1 个决策消费方书面承接 | 5 个工作日内交输入包；超时机会卡自动失效，重走评审 | 守衡 | **停机**：S2 不开工 |
| S2 | 守衡 → Emily（S3 A） | claim_id@{version}、evidence_id、claim_rule_binding{rule_id, rule_version, verdict}、allowed_channels[]、prohibited_phrasing[]、expires_at | claim.status=approved 且 verdict≠rejected；或任一 claim 版本变更 | 读库实时；版本变更到脚本侧生效 ≤2h；过期前 30 天预警 | Emily | **停机**：引用版本≠当前版本或 verdict=rejected，script 不得进 approved |
| S3 | Emily / Clone → Radar / Vicky（S4） | script_id@{version}、claim_refs[]、rights{asset_id, creator_id, scope[], account_ids[], territory[], valid_to, doc_asset_id, credential_type}、proof_method | script=approved 且 asset=validated 且 rights_status≠blocked | 48h 内交 brief 与素材包；授权到期前 30 天复审 | Radar（creator 侧）+ Vicky（媒体侧）双签 | **停机**：无 creator_id 或授权七元组缺任一项（含 credential_type）的素材不得进 S4 任何分发 |
| S3 | Emily / Clone → Paid Media（S5） | variant_id、script_id、asset_id、changed_variable（单值）、control_variant_id、publish_record_id、rights_status=cleared、test_thresholds{metric,min,window_days} | variant=ready 且 publish_record_id 非空 且 claim gate 通过 | 衰减判定后 3 天内替换素材上线；无衰减按周补片 | Paid Media | **停机**：缺 variant_id 或 rights_status≠cleared 的素材不得进 ad |
| S4 | Radar / Vicky → Paid Media（S5） | creator_id、asset_id、rights{scope=paid, account_ids[], territory[], valid_to, doc_asset_id, credential_type}、variant_id、handoff_packet_id | 达人内容首条付费素材上线，且授权凭证齐、到期日可查 | 48h 内完成授权与放大决策 | Paid Media + Radar 双签 | **停机**：无书面授权凭证一律不进 paid |
| S5 | Paid Media → Shopify / Amazon 站内（S6） | ad_id、variant_id、landing_ref（pdp@{version} 或 asin@{version}）、audience_ref、click_id/UTM、attribution_window | campaign 上线前 24h；或投放结构变更 | 落地页版本冻结 ≥24h；投放数据次日 09:00 前回传 | Shopify / Amazon 站内 | **停机**：landing_ref 未登记不得开投 |
| S6 | Shopify / Amazon 站内 → CS（S7） | order_id、sku_id、publish_record_id、pdp@{version}、claim_id@{version}、promised_delivery_at | 订单创建 / 发货 | 订单创建后 ≤1h 建立承诺快照 | CS | **降级**：订单已发生，停机不成立；承诺比对标 NOT_YET_OBSERVED + due_by=+24h，逾期转异常工单 |
| S7 | CS → Retention（S8） | ticket_id、voice_id、return_reason_code（四层）、refund_cost、satisfaction | 工单关闭 / 退货单完成 | T+1 日 | Retention | **降级**：复购障碍只用行为数据，报告强制标注「无语义证据」，不得据此下产品整改结论 |
| S8 | Retention → Paid Media / PMO | ltv_cohort_id、contribution_margin（口径版本）、cac_payback_days、channel、cohort_size | 月初 cohort 结算完成 | 每月 5 日前 | Paid Media + PMO 双签 | **停机**：无 payback 的渠道不得加预算，只能维持或减 |
| S9 | Signal / GEO / Vicky → PMO（S10 口径层） | sov、brand_search_share、ai_mention_rate、ai_accuracy_rate、event_id 聚合、metric_dict@{version} | 月度复测完成；或口径版本变更 | 月报 T+3；口径变更前 5 工作日通知 | PMO | **降级**：未复测指标进季度校验时标「未复测」，不得进预算决策 |
| S10 | Source → 全体消费者 | 8 主键 schema、id@{version} 引用规则、空值三值（NOT_APPLICABLE / NOT_YET_OBSERVED / ABSENT）、due_by、契约版本 | schema 变更前 5 工作日；断流即时 | 断流 2h 内缺口声明；24h 内恢复或给替代方案 | ≥3 个下游书面确认（Em/Cl/Pd 或对应消费者） | **降级**：最后已知值 + stale_at 标记；>24h 自动转停机 |
| S11 | PMO → 全体 | work_item_id、commitment{metric, baseline, target, window, owner, metric_version}、裁决结论（续投/收缩/关停） | 季度校准；90 天产线裁决 | 会前 5 工作日下发，会后 5 工作日签署 | 各段 A 签字 | **停机**：无签署承诺的产线不得占用下季度预算与人力 |

### 4.1 停机与降级的判定依据

只有 4 条是降级，共同点是**下游对象已经产生，停机无法撤回**：订单已创建（S6→S7）、工单已关闭（S7→S8）、指标已发布（S9→S10）、断流时下游已在跑（S10→全体）。这四条即使停机也拦不住既有损失，只能降级并限期补齐。

其余 8 条停机的理由一致：交接发生在**对象创建之前**。无 claim 不得进脚本、无 variant 不得进 ad、无授权不得进 paid、无 landing_ref 不得开投、无 payback 不得加预算、无签署承诺不得占预算。停机的成本是延迟一天，放行的成本是一条错误归因流进季度复盘且不可回溯——两者不对称，所以选停机。

以上 4 条降级 + 8 条停机是「交接字段都在已登记键内」时的口径。S1→S2、S6→S7、S7→S8、S8→S5、S9→PMO、S11→全体 这 6 条因域外键未登记，登记完成前按 §4.2 第 3 条只计记录，实际按本表执行的只有其余 6 条（S2→S3、S3→S4、S3→S5、S4→S5、S5→S6、S10→全体）。

### 4.2 三条补充规则

1. 交接字段缺失时，缺失语义必须写实：结构性不需要填 NOT_APPLICABLE，应观测未发生填 NOT_YET_OBSERVED 并附 due_by，事实上没有填 ABSENT。禁止「待定」「未知」。
2. 交接不以会议、文档、群消息为载体。字段不入库即视为未交接；口头确认不改变状态机。
3. 无主键覆盖的交接共 6 条：S1→S2（opportunity_id、category_id）、S6→S7（order_id、sku_id）、S7→S8（ticket_id、voice_id）、S8→S5（ltv_cohort_id）、S9→PMO（metric_dict@version）、S11→全体（work_item_id）。S11 计入而非排除的理由：`work_item_id` 是 PMO 下发、全体产线据以排预算与人力并跨线引用的业务对象标识，不在 9 主键、也不在字典 §0.1 的九类子记录内；唯一可能的排除口径是「治理域不属于业务数据流」，但同一口径会连带排除已计入的 `metric_dict@version`（同为 PMO 自持的字典版本），口径自相矛盾，故不成立。这 6 条在对应键登记完成前只作为记录项，不得作为阻断条件；其余 6 条按 §4.1 执行停机或降级。

   **上述 9 个域外键按优先级登记为字典 §11 的候选键，登记顺序：order_id → sku_id → ticket_id/voice_id → ltv_cohort_id → opportunity_id/category_id → metric_dict@version → work_item_id。**

   **2026-11-02 提级说明**：`order_id` 与 `sku_id` 由「记录项」提为**与三键并行落库**。理由是 Vicky（Tracker 品线覆盖 0.0%）、Echo（身份解析 2/56）、Shopify（依赖商品主数据）三方各自用手工方法补同一件事，是重复建设最贵的形态。两键的完整规格见字典 §15。提级不改变本条的其他判定：其余 7 个域外键仍为记录项。

   S11 的 `commitment.metric_version` 复用 `metric_dict@version`，不另计一个域外键。本条只解除停机与阻断计数，不解除 §4.1 已定的降级义务：S6→S7、S7→S8、S9→PMO 仍按原行带降级标记并限期补齐；S11→全体 原判停机，纳入本条后按 S8→S5 的先例降为记录项。明细见 §4.3。

### 4.3 六条无 8 主键覆盖交接的域外键

6 条交接共涉及 9 个域外键。登记标准与落库统一按 P0 §5：PMO 定 B-08 标准、Source 落库；下表的「对象写入方」只负责产生值，不改契约。S11 的 `commitment.metric_version` 指向 `metric_dict@version`，与 S9→PMO 共用同一个域外键，不重复计数。

| 交接 | 域外键 | 代表业务对象 | 对象写入方 | 键登记完成前下游怎么降级 |
|---|---|---|---|---|
| S1→S2 | opportunity_id | 机会卡：一次品类机会的判定记录与决策消费方 | Market（观察期由 PMO steward 代持） | 停机降为记录项：S2 可开工；输入包用「机会卡编号（自由文本）+ 评审日」承载，缺口记 `NOT_YET_OBSERVED` + due_by |
| S1→S2 | category_id | 平台类目节点（Amazon browse node / 独立站品类路径） | Amazon 站内、Shopify | 以「平台类目名 + 类目路径快照」承载，人工核对表随输入包交付，不阻断 S2 |
| S6→S7 | order_id | 成交订单：一笔交易的主键 | Shopify、Amazon 站内 | 降级义务不变：以平台订单号明文 + 下单时间写实记录，承诺快照照常生成，逾期转异常工单 |
| S6→S7 | sku_id | 商品 SKU 主数据（DTC SKU / ASIN-SKU 映射） | Shopify、Amazon 站内 | 以 SKU 明文 + 商品名快照承载；退货原因与 cohort 关联降为按商品名匹配，报告标匹配率 |
| S7→S8 | ticket_id | 客服工单 | CS | 降级义务不变：以工单系统流水号（非契约 ID）承载；复购障碍只用行为数据并标「无语义证据」 |
| S7→S8 | voice_id | 客户原声（VOC 记录） | Echo | VOC 只作解释、不作证据；S8 报告强制标注「无语义证据」，不得据此下产品整改结论 |
| S8→S5 | ltv_cohort_id | 首单 cohort：同月同渠道的首购客群 | Retention | 停机降为记录项：payback 只按「渠道 + 月份」粗口径结算，渠道只能维持或减预算，不得加预算 |
| S9→PMO | metric_dict@{version} | 指标字典版本快照（口径定义集） | PMO | 降级义务不变：标「未复测 / 口径未定版」，不得进预算决策 |
| S11→全体 | work_item_id | 工作项：PMO 下发的一条目标/承诺单元，季度校准与 90 天裁决的最小记账单元 | PMO | 停机降为记录项：产线可进下季度排期；承诺以「work_item 编号（自由文本）+ 下发日 + 承诺口径版本」承载，缺口记 `NOT_YET_OBSERVED` + due_by；未签署承诺的产线在季度评审中不计续投的正面证据，但不再阻断预算占用 |

## 5. 三张补充表

### 5.1 无主段清单（14 列基线，不含 P0）

整段无 A 的 4 个，子项无 A 的 3 个。

| 单元 / 子项 | 现有 14 列中的 A | 现状 | 临时 owner | 临时期限 | 转正判据 |
|---|---|---|---|---|---|
| S5 付费投放 | 无 | 0 条线对「花出去的钱换回什么」负责；ad_id 无产线写入口 | PMO（steward） | 30 天 | Paid Media 建立并签署本条交接契约；ad_id 移交时 ID 不变 |
| S6-AMZ 转化承接（Amazon） | 无 | 覆盖平台写了 Amazon US/Europe，产线为空；无 Account Health 巡检、无 listing 责任 | Shopify（作为交易入口代管） | 30 天 | Amazon 站内上线并持有每日 Account Health 巡检记录 |
| S7 履约与售后 | 无 | Echo 只做语义感知，不接工单；退货原因不回流 | CS（P0） | 30 天 | 统一收件箱 + 原因码 + SLA 看板上线 |
| S8 复购与 LTV | 无 | Shopify 只到「复购与私域」最小闭环，不承担 LTV 口径与 CAC payback | Shopify | 30 天 | Retention 的 12 个月贡献毛利 cohort 表可算 |
| S2-资质（认证/进口/类目准入） | 无 | 守衡只管内容合规，明确不覆盖认证办理；Market 只做门槛核对 | Market | 60 天 | 认证清单、责任人、办理周期落表并进 S2 验收 |
| S4-联盟营销 | 无 A 无 R | 联盟客既不在 Radar 的 IP/名人范围内，也不在 Paid Media 的账户范围内 | Radar（affiliate 属 creator 域） | 60 天 | 佣金台账与 creator_id 绑定，佣金异常可在一个结算周期内发现 |
| S7-履约（承运商/库存） | 无 | CS 明确不做承运商管理与补货；Inventory/Fulfillment 是 P1 | Shopify（订单与物流数据）+ Amazon 站内（FBA） | 90 天 | P1 立项，或明确外包并写入 S7 边界 |

临时 owner 的权限限制：只可执行、不可签长期承诺；不进入 §3.1 的 A 值统计；到期未转正即升级到季度评审，不允许自动续期。

### 5.2 拥挤段清单（3 条以上触达）

「退出」指不再持有该段的独立动作与预算，只保留 R 或 I；不是裁员，也不是把产线关停。

| 段 | 触达 | 名单 | A | 退出方 | 退出理由 | 退出后独立动作数 |
|---|---|---|---|---|---|---|
| S3 内容与素材 | 5 | Emily、Clone、守衡、GEO、Daisy | Emily | GEO、Daisy | GEO 的内容生成与 Emily 的权威内容生产重复，只保留「AI 可引用形态」的规格输出；Daisy 只供 claim/evidence，不产出内容 | 3（Emily 策略、Clone 产能、守衡 gate） |
| S4 达人/媒体/联盟 | 4 | Vicky、Radar、Emily、GEO | Vicky | Emily、GEO | Emily 的 brief 由 Radar 出，Emily 只提供 narrative 引用；GEO 不做 PR 排期，只消费 coverage 作为 AI 引用源 | 2（Vicky 媒体、Radar 达人） |
| S9 品牌资产 | 4 | Signal、GEO、Vicky、Echo | Signal | Echo、Vicky | Echo 只做口碑数据源，不持口径；Vicky 只交 coverage 资产，品牌词 lift 的归因统一由 Signal 算 | 2（Signal 总量与口径、GEO AI 子维度） |
| S10 数据与决策基建 | 6 | Source、Daisy、Main、Echo、Signal、PMO | Source | Echo、Signal、Main | Echo 与 Signal 的声量与 VOC 管道并入 Source，不得自建；Main 只做工程执行，不定义契约 | 3（Source 数据、Daisy 事实与权限、PMO 口径） |
| S11 组织与治理 | 3 | PMO、Main、守衡 | PMO | Main | 工程交付指标归 S10 承载，S11 只保留组织级承诺与裁决 | 2（PMO 治理、守衡 判定回执） |

削不掉的只有一条：S3 的守衡 gate 不退出。它是唯一有权说不的位置，退出就等于把合规判定降级为 R，S3 会在第一个拒审事件上失守。

### 5.3 跨段长链路责任表

方括号内为段级 A，R 只在关键跳标注。

**链 1｜新品上市（S1→S8）**

`S1 机会卡 [Market A]` → `S2 claim/evidence [守衡 A / Daisy R]` → `S2 认证准入 [无 A]` → `S3 脚本 [Emily A]` → `S3/S4 素材与授权 [Clone R / Radar R]` → `S5 投放 [Paid Media A]` → `S6 承接 [Shopify A / Amazon 站内 A]` → `S7 售后 [CS A]` → `S8 复购 [Retention A]`

- 真空跳 1：认证与进口资质。守衡只判内容，Market 只判类目门槛，办证无人。
- 真空跳 2：首批 100 单的转化质量。S5 与 S6 各有 A，跨段无合并 owner；CVR 掉点时分不清是流量问题还是页面问题，两边都能举证自己没错。
- 9 跳中 2 跳无 A，占 22%。

**链 2｜舆情/危机 24h（S9→S4→S7→S5）**

`监听到事件 [Signal A，写 event_id]` → `分级与派单 [Vicky R]` → `买家侧处置 [CS A]` → `产品缺陷判定 [守衡 A / Daisy R]` → `对外口径 [法务签，无列]` → `暂停投放 [Paid Media A]`

- 真空跳 1：「因舆情暂停投放」的触发权。Paid Media 有止损权，但舆情触发不在它的输入契约里；Signal 有 event_id 但不持投放权限。
- 真空跳 2：对外声明的最终签字。法务是自然人，不在 18 列，Vicky 只有草稿权。这条链在 P0 事件上必然出现在表外。
- 同一事件进三处的风险已被 event_id 收敛（Signal 唯一写入口，Echo/Vicky 只 append event_observation），但处置动作仍可能三处重复。

**链 3｜爆款复刻放量（S3→S5→S6→S9）**

`结构拆解 [Clone R]` → `复刻决策 [无 A]` → `脚本与假设 [Emily A]` → `变体生产 [Clone R，variant_id]` → `授权核验 [Radar R，creator_id]` → `投放放量 [Paid Media A]` → `承接 [Shopify A / Az A]` → `品牌搜索验证 [Signal A]`

- 真空跳：「是否值得投入 15 条产能复刻」。Clone 能判可迁移机制，但产能投入需要 Emily 的假设与 Paid Media 的预算双签，当前无单一 owner，结果是「谁声音大谁决定」。
- 授权核验的 A = Radar（对象级，持 `asset_rights` 写入口）；段级仍为 0 A，链路问责按对象级执行。

**链 4｜PR/AI 可见度 → 品牌搜索（S4→S9→S6）**

`pitch 与收录 [Vicky A]` → `coverage 资产化 [Vicky R，earned_coverage]` → `下游分发 [GEO R / Shopify C / Az R]` → `品牌搜索与 SOV [Signal A]` → `归因裁决 [PMO R]`

- 真空跳：「这条 PR 值不值」的因果判定。Vicky 只能给方向性弹性区间，Signal 只能给相关性，PMO 只做口径；三段都只能出 C 级证据，没有一个 A 对单次 PR 的投入产出签字。
- 结论：这条链在结构上只能做到方向性结论，任何「PR 带来 X 个新客」的表述都是越权。

**链 5｜达人供应链（S4→S3→S5→S7）**

`找人 [Radar R]` → `尽调 [Radar R]` → `签约 [人工，无列]` → `寄样 [无 A]` → `内容回收 [Radar R]` → `授权 [Radar R，七元组]` → `付费放大 [Paid Media A]` → `结算与佣金 [无 A]` → `授权到期回收 [Radar R]`

- 真空跳 1：寄样。单季 1-3 万美金寄样成本，无台账、无回收率、无人负责。
- 真空跳 2：结算与佣金冲回。与财务对账差异无 owner，ROI 归因从源头不可信。
- 9 跳中 2 跳无 A，且这两跳恰好是现金与货物流失的位置。

## 6. 这张 RACI 怎么用

### 6.1 周会（30 分钟）：只看三行

| 看哪行 | 看什么 | 硬检查 |
|---|---|---|
| S3→S5 | 素材替换队列 | 3 天内在途替换项 ≥1；已死素材继续跑预算占比 <5% |
| S5→S6 | 落地一致性 | landing_ref 登记率 100%；广告承诺与 PDP 版本一致 |
| S7 | P0 工单 | 每个 P0 有 owner、有关闭时间、有升级记录 |

周会只读 A 列与 R 列。C 列不出现在周会议程；I 列只接收交接失败通知，不发言。周会出现的任何「共同负责」表述，当场记为交接违约一次。

### 6.2 月会：看四道闸门 + 一张违约表

1. claim gate：未 approved 的 claim 进入脚本的数量必须为 0。
2. 授权 gate：进入 paid 的 asset 有授权七元组（含 `credential_type`）的比例必须为 100%。
3. 实验 gate：进入测试的 variant 有 hypothesis_id 与 control_variant_id 的比例必须为 100%。
4. payback gate：payback >180 天的渠道自动进入限制加预算名单，数量必须可核。
5. 交接违约表：按 §4 的 12 条交接统计违约次数与逾期时长；§4.2 第 3 条的 6 条只记记录值、不计违约次数。同一交接连续 3 次违约即触发 §6.4 第 2 条（只对可强制的 6 条成立）。

月会不看「完成度」。「已完成 / 进行中 / 方案中」在本表里没有对应列，出现即视为跑题。

### 6.3 季度评审：只做三件事

1. **A 归属复审**：逐段看主指标是否达成；连续两季未达成的段，A 必须移交或该段降级。
2. **产线续投裁决**：每条产线看两项——段 A 是否持有、对象级 A 的交付是否被至少 1 个非 owner 消费方实际调用。两项皆无的产线进收缩名单。
3. **A 计数审计**：重跑 §3.2。出现任一产线 A 计数 ≥2 即当场冻结其第二个 A 段，30 天内切分。

### 6.4 这张表什么情况下要改（可判定触发）

1. 任一 A 段的主指标连续 2 个季度未达 baseline。
2. 同一交接连续 3 次违约。
3. 新增或裁撤产线——表必须同版本更新，未更新的表不得用于考核。
4. 出现新的可杀死主体（新平台账号、新市场资质），允许拆子段；拆后必须重跑 §3 自检。
5. 任一产线段 A 计数 ≥2。
6. 评审会上出现「共同负责」「双方都签」这类表述。

触发 1、2、4 由 PMO 发起；触发 3 由变更方发起；触发 5、6 由任何参会人当场发起，不需要事先审批即可立案。

### 6.5 改表的审批流程

1. 提案：受影响段的现 A 或 PMO 提交变更单，写明段、现 A、拟 A、依据指标、生效日。
2. 双签：现 A 与拟 A 同时签字。任一方不签即进 PMO 仲裁，不得默认生效。
3. 字段核验：守衡核交接字段是否仍在主键字典内；不在字典内先走 B-08 契约变更，不得先改 RACI 后补字段。
4. 批准：涉及预算与考核的 A 变更由业务负责人批准，PMO 只有提案权。
5. 版本：version+1，旧版进 archive；下游 5 个工作日内切换，切换期双写不双算。
6. 回滚：新版生效 30 天内任一交接失败 2 次，自动回退上一版，回退不需再审批。

### 6.6 三条反滥用规则

1. 不得用「共同 A」「A/B 角」代替唯一 A。存在两个 A 的段，等同于零 A。
2. 不得把 C 当挡箭牌。C 只在有否决动作时成立，无否决动作一律降为 I。
3. 不得用 I 掩盖未交付。I 不承担任何交付责任，把交付挂在 I 上等于没派单。

## 7. 未核验与风险

**推断项**

- A 的归属由产线章程、边界声明与 8 主键写入口推出，未做人力与预算盘点。S4 的 A 归 Vicky 是当前唯一可行解；若达人支出占 earned 预算 >60%，A 应移交 Radar 并同步改写 S4 定义。
- 停机与降级的分界按「对象是否已产生」判定，未验证各段实际的对象创建时点。S6→S7 的承诺快照能否在 1h 内生成，取决于 PDP 版本与订单系统的关联能力，当前无接口证据。
- SLA 数值（2h / 24h / 48h / 3 天 / 5 工作日）是可按当前流程推演的执行起点，不是实测值。落地 4 周后必须用实际交接时长重设。

**需真实系统数据才能确认**

- 各产线的真实调用量与停机成本：停机对 S5 的成本与对 S2 的成本差一个量级，当前只能定性。
- landing_ref 在现有投放系统中是否可强制登记为开投前置条件。
- S10 的断流频率与恢复时长分布，决定 24h 自动转停机是否过松。

**风险**

1. **A 会变成抢权而非担责。** 判定方法是看该产线是否接受「连续两季未达标即移交」条款；只接受 A 不接受移交条款的，视为未接受问责。
2. **S6 拆成两个单元后仍是双头。** Shopify 与 Amazon 站内对同一 SKU 的价差与促销节奏无共同裁决人，Pricing 是 P1 未建；在此之前由 PMO 代裁决，这是已知敞口，不能宣称已被治理覆盖。
3. **6 条产线段级 0 A。** Clone、Radar、Daisy 靠对象级 A 站立，成立；Echo 靠 taxonomy 版本站立，勉强成立；**GEO 已于 2026-11-02 新增第 9 键 `ai_answer_snapshot_id`，从此靠对象级 A 站立**，本风险由「唯一零问责产线」降级为「与 Clone/Radar 同形的零段 A 产线」。剩余条件：该键必须在 30 天内落库并产出「Top N 未提及问句」清单，否则回退为 work_item（字典 §14.10）。
4. **停机规则在落地首月必然引发争议。** 观测期设定为前 4 周：停机项只记录并标红，不实际阻断；第 5 周起按表执行。对应 gate 的阻断生效由「日期 AND 覆盖率」双条件决定（Gate §6.6），不看个案，避免变成「视情况」。
5. **整表建立在主键字典之上。** B-08 与 B-12 仍为「重复 0 次、实现 0 次」；主键未落地前，§4 的 12 条交接里有 6 条（9 个域外键）只能记录、不能强制，仅剩 6 条可作拦截依据，本表只能作为设计与考核依据，不能作为系统拦截依据。
