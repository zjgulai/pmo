---
title: 品牌 Agent 主键字典（Key Registry）
doc_type: analysis
module: brand-agent
topic: key-registry
status: draft
created: 2026-11-01
updated: 2026-11-01
owner: self
source: human+ai
---

# 品牌 Agent 主键字典（Key Registry）

## 0. 全局契约
**0.1 主键与子记录**：8 个主键是一等对象，有独立编码、状态机、写入口。`claim_rule_binding`、`publish_record`、`event_observation`、`asset_rights`、`metric_snapshot`、`correction_request` 都是挂在主键下的子记录，**不单独发顶层 ID**。前六类用 `(parent_id, seq)` 定位；`gate_receipt`（第七类）、`rule_object`（第八类）、`market_overlay`（第九类）需要被跨线引用，用 §0.9 的确定性定位串。每增加一个顶层 ID，就多一处需要协调的写入口。

三类子记录的唯一写入口：`gate_receipt` 由出判定的 gate 写——Claim Gate → 守衡，授权 Gate → 守衡核验（Radar 提供台账），实验 Gate → PMO；`rule_object` 由合规 owner 写；`market_overlay` 由 PMO 写。三者均不参与跨线裸引用，跨线引用必须带 `subject_id` 与版本。

**0.2 编码三型**

| 型 | 形式 | 用于 | 为什么 |
|---|---|---|---|
| R 可读型 | `{pfx}-{seg}-{seq}` | 会在合同、会议、工单、对外文案里被念出来或逐字核对的对象 | 能读、能从 ID 反推归属 |
| U 单调型 | `{pfx}_{ULID26}` | 机器高并发创建、需按时间排序、不需人念的对象 | 无中心分配，字典序即时间序，多写点不撞号 |
| D 派生型 | `{pfx}-{外部事实}` | 由外部系统字段确定、不能依赖内部注册协调的对象 | 可从导出重建，天然幂等 |

**0.3 三种一律禁用**：纯自增（多写入口冲突、跨环境重号、泄露量级、可被猜测）；纯 UUIDv4（不可读、不可排序、随机写放大、无法人工核对）；哈希即 ID（平台重编码改字节，同一创意被拆成多个身份）。

**0.4 空值三值**：必填字段不接受 NULL。可空字段只允许三个可判定值——`NOT_APPLICABLE`（结构上不需要）、`NOT_YET_OBSERVED`（应观测但未发生，必须同时填 `due_by`，到期转异常）、`ABSENT`（事实上的没有，是一次断言）。禁止「未知」「待定」「TBD」：空值不说明原因，复盘时无法区分「没发生」与「没人填」，这两者的责任归属完全相反。

**0.5 版本与引用**：所有主键带 `version`（整数，从 1 起）与 `supersedes`。跨产线引用必须写成 `{id}@{version}`，禁止裸引用。不可变字段变更 = 新建记录 + version+1 + 旧记录 `status=superseded`；可变字段原地更新并写 `change_log`。

**0.6 写入口判定**：一个主键只有一个写入口，判定标准是「谁有权让对象从不存在变成存在」。追加子记录、改只读字段、提 correction_request、订阅视图，都不构成写入口。两个系统各能创建同一对象即判定主键失效，须在下一次迭代收敛。

**0.7 九键总表**（第 9 键于 2026-11-02 增补，理由与代价见 §14）

| # | 主键 | 前缀 | 型 | 唯一写入口 | 修掉断点 |
|---|---|---|---|---|---|
| 1 | event_id | `evt_` | U | Signal | BP-04 |
| 2 | claim_id | `clm-` | R | Daisy（本体）+ 守衡（规则绑定子表） | BP-02、BP-06 |
| 3 | evidence_id | `evd_` | U | Daisy | BP-02 |
| 4 | script_id | `scr-` | R | Emily | BP-03 |
| 5 | variant_id | `var-` | R | Clone | BP-03、BP-16 |
| 6 | asset_id | `ast_` | U | Clone / Daisy / Vicky（按 asset_class 分域） | BP-06、BP-11、BP-16 |
| 7 | ad_id | `ad-` | D | 投放侧（未建，PMO 过渡 steward） | BP-03、BP-16 |
| 8 | creator_id | `crt-` | R | Radar | BP-11 |
| 9 | ai_answer_snapshot_id | `aia_` | U | GEO | 修掉「AI 可见度不可复测」（§14） |

第 9 键不是第 4 个 G、不动 O、不动段数。它只解决一件具体的事：**GEO 的两个指标（AI 提及率、AI 准确率）此前没有对象宿主，不可计算**。按本段 §0.1「每增加一个顶层 ID，就多一处需要协调的写入口」，这一条必须逐个交代；交代见 §14.1。

**0.8 `asset_rights` 的唯一写入口**：`asset_rights` 的唯一写入口是 Radar。字段为授权七元组 `(asset_id, creator_id, scope[], account_ids[], territory[], valid_to, doc_asset_id)`，另附 `credential_type` 枚举。Clone 只能追加 `asset_ref` 外键，不得修改任何授权字段；守衡只读并出判定——授权 Gate 的 PASS / CONDITIONAL / BLOCK 只引用台账，不回写台账。`asset_rights.status` 随授权撤回或到期变更，变更权同样只在 Radar。

跨线台账不等于双写：Clone / Daisy / Vicky 分域写的是 `asset_id` 本体的 `content_hash`、`distribution_targets`、`status`；授权字段的唯一可写存储在 `asset_rights` 一处，只有 Radar 能对它 INSERT / UPDATE，同一行数据不存在第二个写者。多条产线读同一份台账（授权 Gate、投放侧、PMO 结算）是读扩散，不是写扩散——双写是两个写者各维护一份真相，台账是一处写入、多处只读。`asset.rights` 只是 `asset_rights` 的只读投影（§6），不是第二个写点；投影为空 = 全自有资产、无需第三方授权。

**0.9 Gate 依赖的三类子记录**：`gate_receipt`（第七类）、`rule_object`（第八类）、`market_overlay`（第九类）已登记在 §0.1，写入口见 §0.1。它们不是第 9/10/11 个主键：`gate_receipt` 是某个主体版本的一次判定回执，生命周期完全依附于 `subject_id@version`；`rule_object` 与 `market_overlay` 是单一 owner 维护的判定输入（规则、市场叠加），不参与业务状态机，也不会被多条产线并发创建。三者各只有一个写者，所以不新增需要协调的写点。

但它们必须能被跨线引用：实验 Gate 的 E2 回执要求把 C2 与 A1 的回执号写进 `evidence_refs`，`rule_refs[]` 与 `market_overlay_version` 是任何判定的前提。解法是给三者确定性定位串，但三类性质不同，不能合并论证：`gate_receipt` 是纯子记录——定位串由 `subject_id@version`、gate 码与序号拼成，不是新发 ID；`rule_object` 与 `market_overlay` 是独立对象——`rule_id` / `overlay_id` 是 Gate §1.1 的提案编码，各有独立 ID 空间、独立版本规则与单一 owner，只是不进业务状态机：

| 子记录 | 定位串 | 例 |
|---|---|---|
| `gate_receipt` | `{subject_id}@{version}#{gate}-{seq4}` | `scr-bpc-tiktok-00317@2#C-0041` |
| `rule_object` | `{rule_id}@{rule_version}` | `rule-claim-cosmetic-medical-boundary-us-review@3` |
| `market_overlay` | `{overlay_id}@{overlay_version}` | `overlay-eu-gpsr-reach-eu-review@2` |

「既是子记录又可被引用」的边界：可引用性来自定位串，不来自顶层 ID。三类分两种：`gate_receipt` 是纯子记录，生命周期完全依附 `subject_id@version`，定位串由既有键拼成，不产生新的分配点；`rule_object` 与 `market_overlay` 是独立对象，有独立 ID 空间（`rule_id` / `overlay_id`）、独立版本规则与单一 owner，只是不参与业务状态机、也不会被多条产线并发创建——「不新增协调点」来自单 owner，不来自「由既有主键拼成」。三者都不进 §0.7 八键总表，也不得作为 `parent_id` 的父对象；跨线引用必须写完整定位串（含版本），禁止裸写 `#C-0041`、`rule-claim-…` 或 `overlay-eu`——不带版本的引用等于指向「最新版」，判定不可复现。

**`gate_receipt` 字段规格**（第七类子记录）

| 字段 | 类型 | 必填 | 取值域 | 为空语义 |
|---|---|---|---|---|
| receipt_id | str | Y | `{subject_id}@{version}#{gate}-{seq4}` | — |
| subject_id / subject_version | str / int | Y | 8 主键之一；版本 ≥1，禁止指向「最新版」 | — |
| gate / seq4 | enum / int | Y | `C`（Claim）/ `A`（授权）/ `X`（实验）；seq4 按 (subject_id, gate) 独立递增、4 位补零，`receipt_id` 中不得写裸序号 | — |
| gate_version | int | Y | ≥1；判定表版本，规则内容变更 +1；回执绑定判定时的版本，禁止指向「最新版」 | — |
| judged_at | ts UTC | Y | ISO-8601；晚于 `published_at` 即回执作废 | — |
| verdict | enum | Y | `pass` / `conditional` / `block` | — |
| conditions[] | list | N | CONDITIONAL 的可机检 predicate（渠道 / 账号 / 可播片段 / 到期日） | `ABSENT`：PASS 与 BLOCK 无附带条件 |
| rule_refs[] | list | Y | `[{rule_id}@{rule_version}, source_locator]`，≥1；source_locator 到文件 SHA + 段落 | 不允许为空：无规则引用 = 未判 |
| market_overlay_version | str | Y | `{overlay_id}@{overlay_version}`；多市场写 map | 不允许为空：overlay 缺失 = 未判 |
| judge_identity | obj | Y | `{type: human / agent, id, role}`；agent 须登记模型版本与抽检人 | — |
| evidence_sha | char(64) | Y | sha256(证据包)；asset 类另带 `content_hash` | 无证据类写 `NOT_APPLICABLE` |
| supersedes | str | N | 上一条 `receipt_id` | `ABSENT`：首判 |
| status / valid_until | enum / ts | Y | `active` / `superseded` / `overturned` / `expired`；到期由系统置 `expired` | — |
| invalidate_on[] | list | Y | 失效事件枚举：`bytes_changed` / `claim_version_changed` / `rule_changed` / `rights_revoked` / `expired`，≥1；任一命中即置 `superseded` 重判 | 不允许为空：无失效条件的回执等于永久有效，与 §0.5 版本引用冲突 |
| sla_due_at | ts UTC | Y | 判定时限；`judged_at` 晚于它即 SLA 违约，只升级、不改判定（Gate §0.3 铁律 3） | — |

字段名以本表为准：Gate §0.4 的 `judged_by` / `evidence_refs[].sha256` 是同一字段的分组写法；§0.4 的 `gate_version` / `conditions[]` / `invalidate_on[]` / `sla_due_at` 在本表均有对应列，Gate 不再另立字段。

**`rule_object` 字段规格**（第八类子记录）

| 字段 | 类型 | 必填 | 取值域 | 为空语义 |
|---|---|---|---|---|
| rule_id | str | Y | 沿用 Gate §1.1 的提案编码（`rule-{topic}-{market}-review`），版本不进 ID | — |
| rule_version | int | Y | ≥1；规则内容变更 +1，禁止原地改 | — |
| rule_type | enum | Y | `claim` / `authorization` / `experiment` | — |
| market / category | enum / list | Y | `us` / `eu` / `uk` / `global`；`bmc` / `bpc` / `spo` | — |
| source_locator | obj | Y | `{doc_ref, sha256, section}`，定位到原文文件与段落 | 不允许为空：无原文的规则不得发布 |
| rule_body | text | Y | 可机判条件 + 人判说明；禁止只写「不合规」 | — |
| status | enum | Y | `proposed` / `published` / `superseded` / `retired` | — |
| effective_from / supersedes | date / str | N | — | `NOT_YET_OBSERVED`：发布日期未定；`ABSENT`：首版 |

**`market_overlay` 字段规格**（第九类子记录）

| 字段 | 类型 | 必填 | 取值域 | 为空语义 |
|---|---|---|---|---|
| overlay_id | str | Y | 沿用 Gate §1.1 的提案编码（`overlay-{topic}-{market}`，如 `overlay-eu-gpsr-reach-eu-review`），版本不进 ID | — |
| overlay_version | int | Y | ≥1；overlay 内容变更 +1，禁止原地改 | — |
| market | enum | Y | `us` / `eu` / `uk` | — |
| base_rule_refs[] | list | Y | `[{rule_id}@{rule_version}]`，≥1 | 不允许为空：无 base rule 的 overlay 不得发布 |
| overrides[] | list | Y | `[{rule_id, field, stricter_value}]`；与 base 冲突取更严 | `ABSENT`：仅汇总，不改 base |
| source_locator | obj | Y | `{doc_ref, sha256, section}` | 不允许为空 |
| status / effective_from / effective_to | enum / date / date | Y / Y / N | `proposed` / `published` / `superseded` / `retired`；到期即失效 | `NOT_APPLICABLE`：长期有效 |
| supersedes | str | N | 上一条 `overlay_id@{overlay_version}` | `ABSENT`：首版 |

## 1. event_id
**语义**：现实中一次被观测到的公开信号事件——具体来源、具体时间窗内、围绕一个实体与一个主题，被判定为同一件事。声誉与声量侧的唯一事实单位。

**唯一写入口**：Signal。只有 Signal 的去重与建单引擎可 INSERT，Echo/Vicky/GEO 只能追加 `event_observation`。理由：Signal 的职责前置条件就是「先归一、再算量」；若 Echo 与 Vicky 也能建单，三套告警必然复活，且 Vicky 按「最早命中方」建主单会让 Echo 永远抢先，媒体负面永远无 PR 主单。

**字段规格**

| 字段 | 类型 | 必填 | 取值域 | 示例 | 为空语义 |
|---|---|---|---|---|---|
| event_id | str(30) | Y | `evt_`+ULID26 | evt_01JB7K2M9Q4R8S1T3V5W7X9Y2Z | — |
| entity_id / entity_role | str / enum | Y | `own_brand`/`competitor`/`category`/`creator` | ent_brand_luteos / own_brand | — |
| event_type | enum | Y | `volume_anomaly`/`media_negative`/`product_defect`/`objection_surge`/`regulatory`/`recall`/`viral_positive` | media_negative | — |
| dedup_fingerprint | char(64) | Y | sha256(entity‖topic_cluster‖6h_bucket‖source_cluster) | 9f2c… | — |
| topic_cluster_id | str | Y | Signal taxonomy 版本化簇 | tc_lactation_claim@v3 | — |
| first_seen_at | ts UTC | Y | ISO-8601 | 2026-11-01T03:12:00Z | — |
| severity | enum | Y | `P0`/`P1`/`P2`/`P3` | P1 | — |
| primary_owner / owner_rule | enum / str | Y | `signal`/`vicky`/`echo`/`legal`/`product`；规则 ID+版本 | vicky / evt-route-v3 | — |
| observation_ids | list | N | 子记录引用 | [obs_881] | `NOT_YET_OBSERVED`，仅允许存活 ≤10 分钟 |
| parent_event_id | str | N | 合并目标 | evt_01JB6… | `ABSENT`：独立事件 |
| status / version | enum / int | Y | 见状态机；≥1 | open / 3 | — |

**编码**：`evt_{ULID26}`。事件是机器每秒产生、必须先按时间排序才能算异动的对象，可读型无价值（无人念事件号），自增在多区域采集器并发时必然冲突。

**生产者 → 消费者**

| 产线 | 权限 | 说明 |
|---|---|---|
| Signal | 创建 / 改 status / 改 severity | 唯一 writer |
| Echo、Vicky | 追加 event_observation | 不得改 event_type/severity；Vicky 仅在 primary_owner 是自己时可改 status |
| Source、GEO、PMO | 只读 | 原始帖 / AI 可见度 / 指标口径 |

**状态机**：`open → triaged → assigned → mitigating → resolved → closed`，旁支 `open|triaged → merged`、`any → false_positive`。

1. open→triaged：Signal，去重后 15 分钟内
2. triaged→assigned：Signal，按 owner_rule 落 primary_owner
3. assigned→mitigating：primary_owner
4. mitigating→resolved：primary_owner，必须附回落数据
5. resolved→closed：Signal，72h 无复发
6. →merged / false_positive：Signal + 人工双签

**版本与不可变**：不可变 `event_id`、`entity_id`、`dedup_fingerprint`、`first_seen_at`、`topic_cluster_id`——五项定义「这是哪一件事」，改了就不是同一事件。可追加 `observation_ids`、`severity`、`primary_owner`（须留 `owner_change_log`）。

**关联**：`event_id 1:N event_observation`；`N:1 entity`；`N:1 topic_cluster`；`event_id 1:N claim_id`（regulatory 类事件）；`event_id 0:N ad_id`（投放暂停联动，过渡期不启用）。

## 2. claim_id
**语义**：品牌对外说出的、可被第三方核验或质疑的一句具体宣称（功效、成分、产地、认证、社会证明、比较级）。是事实主张，不是文案句子。

**唯一写入口**：Daisy 写 claim 本体，守衡只在 `claim_rule_binding` 子表追加判定。Emily 的「claim 与证据库」降级为只读缓存（`claim_id@version`，TTL 24h）。理由：claim 三源的根因不是缺表，是三个系统都有 INSERT 权限；收敛写权限是唯一有效手段。

**避免双写的四条硬规则**

1. 库层权限：claim 表只有 Daisy 服务账号有 INSERT/UPDATE；守衡只有 `claim_rule_binding` 的 INSERT。
2. 守衡发现 claim 有误，只能提交 `claim_correction_request`（rule_id、原文、建议改法），由 Daisy 5 个工作日内应用或驳回，回执落库。
3. 判定真相源是守衡子表，claim 真相源是 Daisy 主表，互不写入；同一 claim 多条判定按 `evaluated_at` 排序，最新一条为当前判定。
4. Emily/GEO/Vicky/Clone 一律只读；需要新 claim 走 `claim_request` 给 Daisy。

**字段规格**

| 字段 | 类型 | 必填 | 取值域 | 示例 | 为空语义 |
|---|---|---|---|---|---|
| claim_id | str(24) | Y | `clm-{cat}-{market}-{seq4}` | clm-bpc-us-0142 | — |
| statement | text | Y | ≤280 字符，单一断言 | 含 18% 烟酰胺 | — |
| claim_type | enum | Y | `efficacy`/`ingredient`/`origin`/`certification`/`social_proof`/`comparative`/`sustainability` | ingredient | — |
| category / markets | enum / list | Y | `bmc`/`bpc`/`spo`；`us`/`eu`/`uk`/`global` | bpc / [us, eu] | — |
| substantiation_level | enum | Y | `L1_required`/`L2_required`/`L3_recommended` | L2_required | — |
| evidence_refs | list | Y | `[{evidence_id}@{version}]`，≥1 | [evd_01JB…@2] | 不允许为空：无证据的 claim 不得存在 |
| rule_binding_current | obj | Y | `{rule_id, rule_version, verdict}` | {bpc-claim-v4, 4, conditional} | — |
| allowed_channels | list | Y | `organic`/`paid`/`pdp`/`amazon_aplus`/`pr`/`ai_answer` | [organic, pdp] | — |
| prohibited_phrasing | list | N | 禁用改写清单 | [治疗, 根治] | `ABSENT`：无额外禁用 |
| expires_at / supersedes | date / str | N | — | 2027-03-31 / clm-bpc-us-0131 | `NOT_APPLICABLE`：无时效；`ABSENT`：新建 |
| status / version | enum / int | Y | 见状态机；≥1 | approved / 3 | — |

**编码**：`clm-{category}-{market}-{seq4}`，seq4 按 (category, market) 独立递增、不按年重置。claim 是唯一会被法务、平台审核、外部编辑逐字引用的对象，必须能念、能核对；market 必须进 ID，因为同一句宣称在 US FTC 与 EU 法规下判定不同，不进 ID 就会跨市场误复用——这是「上架后被迫改文案」的机制原因。

**生产者 → 消费者**

| 产线 | 权限 | 说明 |
|---|---|---|
| Daisy | 创建 / 改本体全部字段 / 改 status | 唯一 writer |
| 守衡 | 追加 claim_rule_binding；提交 correction_request | 不可改本体 |
| Emily、Clone、GEO、Vicky、Echo | 只读 | 脚本引用（Emily 缓存 TTL 24h）、AI 答案、coverage、卖点比对 |
| PMO | 只读 | 审计口径 |

**状态机**：`draft → submitted → under_review → approved`，旁支 `under_review → rejected`、`approved → suspended`、`any → superseded`、`approved → expired`。

1. draft→submitted：Daisy
2. submitted→under_review：守衡，自动触发
3. under_review→approved/rejected：守衡出判定 + 合规 owner 双签（规则类裁定权归合规 owner，守衡只有建议权）
4. approved→suspended：守衡，须附新证据
5. →superseded：Daisy；approved→expired：系统按 `expires_at`

**版本与不可变**：不可变 `claim_id`、`statement`、`category`、`markets`。改 statement 必须新建 claim + supersedes 链，否则历史素材引用的文本被静默改写，已有归因全部作废。可追加 `evidence_refs`（只增不删，删除语义 = 新增一条 `retracted` 引用）、`allowed_channels`、`status`。

**关联**：`claim_id 1:N evidence_id`；`1:N claim_rule_binding`；`claim_id 1:N script_id`（经 script.claim_refs）；`1:N asset_id`（经 asset.claim_refs）；`0:1 superseded_by`。

## 3. evidence_id
**语义**：一份能独立支撑某条 claim 的证据物——检测报告、认证证书、成分规格书、临床或人体试验、内部对照实验、第三方媒体引用、达人实测视频。是「凭什么是真的」的最小可核验单位。

**唯一写入口**：Daisy。证据是事实本体的一部分，与 claim 同源；若守衡或 Emily 也能发 evidence_id，claim 三源会以「证据三源」的形式复活，且更难排查。

**字段规格**

| 字段 | 类型 | 必填 | 取值域 | 示例 | 为空语义 |
|---|---|---|---|---|---|
| evidence_id | str(30) | Y | `evd_`+ULID26 | evd_01JB7K4P2Q8R… | — |
| evidence_type | enum | Y | `lab_report`/`certificate`/`spec_sheet`/`clinical`/`internal_test`/`media_quote`/`creator_testimony`/`regulatory_filing` | lab_report | — |
| issuer / issuer_independence | str / enum | Y | 法定名；`third_party`/`second_party`/`first_party` | SGS Japan K.K. / third_party | — |
| issued_at / valid_until | date | Y / N | — | 2026-08-14 / 2027-08-13 | `NOT_APPLICABLE`：无有效期 |
| file_asset_id | str | Y | 指向 asset_id | ast_01JB7M… | — |
| supports_claim_ids | list | Y | ≥1 | [clm-bpc-us-0142] | — |
| scope_limits | list | N | 受试人群/批次/市场边界 | [n=32, JP only] | `ABSENT`：无已知限制，须人工确认后才允许填 |
| status / version | enum / int | Y | `active`/`expired`/`retracted`/`disputed`；≥1 | active / 2 | — |

**编码**：`evd_{ULID26}`。证据物数量大、由上传动作产生、彼此无层级、不需人念；ULID 保证多来源上传不撞号且可按时间排序，便于「最近新增证据」审计。

**生产者 → 消费者**

| 产线 | 权限 | 说明 |
|---|---|---|
| Daisy | 创建 / 改 status | 唯一 writer |
| 守衡 | 只读；可提 disputed 请求 | 不建证据 |
| Emily、Clone、GEO、Vicky | 只读 | — |
| 法务（人工） | 只读 + 离线签署 | 不写库 |

**状态机**：`active → expired`（自动）、`active → retracted`（出具方撤回）、`active → disputed`（守衡提出，双签生效）、`retracted|disputed → active`（仅在出具新版本证据并新建 evidence_id 后）。

**版本与不可变**：不可变 `evidence_id`、`evidence_type`、`issuer`、`issued_at`、`file_asset_id`——证据是对既成事实的记录，改出具方或日期即伪造。可追加 `supports_claim_ids`（只增）、`scope_limits`。

**关联**：`evidence_id N:1 asset_id`（file_asset_id）；`evidence_id N:M claim_id`；`1:N evidence_supersede`。

## 4. script_id
**语义**：一条内容的叙事层单位——锁定「对谁说、说什么 claim、怎么证明、要验证什么假设、CTA 是什么」的母脚本。不含镜头，不含成片。

**唯一写入口**：Emily。Clone 的镜头脚本与分镜不另发 script_id，它是 variant 的执行字段；Clone 要改 claim 必须回 Emily 新建脚本版本。Emily 与 Clone 都写「脚本」是 BP-26/27 的直接来源，从主键层面切断：叙事层有 ID，执行层无独立 ID。

**字段规格**

| 字段 | 类型 | 必填 | 取值域 | 示例 | 为空语义 |
|---|---|---|---|---|---|
| script_id | str(28) | Y | `scr-{cat}-{platform}-{seq5}` | scr-bpc-tiktok-00317 | — |
| claim_refs | list | Y | `[{claim_id}@{version}]`，≥1 | [clm-bpc-us-0142@3] | 不允许为空 |
| hypothesis_id | str | Y | `hyp-{yyMMdd}-{seq3}` | hyp-261101-012 | 不允许为空：无假设不入测试 |
| audience | obj | Y | `{segment_id, funnel_stage}` | {seg_bpc_25_34, consideration} | — |
| proof_method | enum | Y | `demo`/`before_after`/`third_party_citation`/`creator_testimony`/`ingredient_closeup`/`comparison` | creator_testimony | — |
| hook_type | enum | Y | 钩子分类库版本化枚举 | problem_conflict@v2 | — |
| cta / platform_primary | str / enum | Y | ≤60 字符；`tiktok`/`reels`/`shorts`/`amazon`/`pdp`/`pr` | Shop the set / tiktok | — |
| test_thresholds | obj | Y | `{metric, min, window_days}` | {ctr, 0.018, 7} | — |
| status / version | enum / int | Y | 见状态机；≥1 | live / 2 | — |

**编码**：`scr-{cat}-{platform}-{seq5}`。脚本是会议与 brief 的主语（「317 那条」），必须可念；platform 进 ID 因为同一叙事在三平台判据不同，跨平台复用必须显式新建，否则「一稿三平台」被当成同一 object 归因，3 秒留存差异永远说不清。

**生产者 → 消费者**

| 产线 | 权限 | 说明 |
|---|---|---|
| Emily | 创建 / 改全部字段 | 唯一 writer |
| Clone | 只读 + 追加 `clone_acceptance`、`production_feasibility` | 可拒单 |
| 守衡 | 只读 claim_refs + 追加 `precheck_verdict` | 不改脚本 |
| Echo、PMO | 只读 | objection 覆盖 / 假设统计 |

**状态机**：`draft → approved → in_production → live → retired`，旁支 `draft → rejected_by_clone`、`live → superseded`。

1. draft→approved：Emily，前置条件 claim_refs 全部 `status=approved`
2. approved→in_production：Clone 接单
3. in_production→live：Clone，前置条件 ≥1 variant 达 `live`
4. live→retired：Emily 或 Clone（素材疲劳 / 假设已判定）
5. draft→rejected_by_clone：Clone，缺 claim/audience/hypothesis 任一项

**版本与不可变**：不可变 `script_id`、`claim_refs` 的 claim_id 部分、`hypothesis_id`。改 claim 版本 = 新建 script version，旧变体仍指向旧版本，历史归因不被污染。可追加 `cta`、`test_thresholds`（仅 live 前）。

**关联**：`script_id 1:N variant_id`；`N:M claim_id`；`1:1 hypothesis_id`。

## 5. variant_id
**语义**：一个单变量测试变体——相对对照组只改了一个受控变量（钩子、开头画面、CTA、BGM、字幕样式、时长）的一条可独立投放的创意。

**唯一写入口**：Clone。变体是产能产物，只有 Clone 知道实际改了什么；若 Emily 也能建变体，假设与执行混在一个 ID 上，归因再次失效。

**字段规格**

| 字段 | 类型 | 必填 | 取值域 | 示例 | 为空语义 |
|---|---|---|---|---|---|
| variant_id | str(34) | Y | `var-{script 去前缀}-v{nn}` | var-bpc-tiktok-00317-v04 | — |
| script_id | str | Y | 父脚本 | scr-bpc-tiktok-00317 | — |
| changed_variable | enum | Y | `hook`/`opening_frame`/`cta`/`bgm`/`subtitle_style`/`duration`/`none_control` | hook | 不允许为空；`none_control` 表示对照组，不是空 |
| control_variant_id | str | N | 对照组 | var-bpc-tiktok-00317-v00 | `ABSENT`：本批无对照，须 PMO 例外登记 |
| structure_source_id | str | Y | 复刻来源 | struct_tt_20261012_07 | — |
| asset_ids | list | Y | ≥1 当前有效资产 | [ast_01JB…, ast_01JB…] | — |
| rights_status | enum | Y | `cleared`/`partial`/`blocked` | cleared | — |
| publish_record_id | str | N | 发布回执 | pub_20261101_tt_881 | `NOT_YET_OBSERVED`，`due_by`=计划发布时间 |
| status / version | enum / int | Y | 见状态机；≥1 | testing / 1 | — |

**编码**：`var-{script 主体}-v{nn}`。变体天然依附脚本，父 ID 编进子 ID 后「一个脚本出了几条变体」用前缀扫描即可回答，不需 JOIN；1:N 在编码层成立，孤儿变体不可能存在。纯 UUID 会让「v04 属于哪条脚本」必须查表。

**生产者 → 消费者**

| 产线 | 权限 | 说明 |
|---|---|---|
| Clone | 创建 / 改 changed_variable / 追加 asset_ids / 改 status | 唯一 writer |
| Emily | 只读 + 追加 `hypothesis_fit` | — |
| 投放侧（过渡期 PMO 代管） | 只读 + 追加 `ad_refs` | — |
| 守衡、PMO | 只读 rights_status | 授权 gate / 实验统计 |

**状态机**：`draft → rights_checking → ready → testing → scaling → retired`，旁支 `rights_checking → blocked`、`testing → killed`。

1. draft→rights_checking：Clone 提交
2. rights_checking→ready/blocked：授权 gate（守衡 + Radar 台账）
3. ready→testing：投放侧；无 owner 时由 PMO 代签
4. testing→scaling/killed：投放侧，按预注册阈值三分
5. any→retired：Clone

**版本与不可变**：不可变 `variant_id`、`script_id`、`changed_variable`、`control_variant_id`。四项定义「在测什么」，改了实验就换了，必须新建 variant——这是「改 6 版无法归因」的根因修复。可追加 `asset_ids`（重导出）、`rights_status`、`ad_refs`。

**关联**：`variant_id N:1 script_id`；`1:N asset_id`；`1:N ad_id`；`0:1 control_variant_id`。

## 6. asset_id
**语义**：一个实体素材文件——可下载、可播放、可上传的字节实体：成片 mp4、封面图、字幕 srt、BGM 音频、证据 PDF 扫描件、PR 报道截图。

**唯一写入口**：按 `asset_class` 分域，每个 class 只有一个 writer。这是唯一按域分权的主键，因为它的现实来源本来就分域（内容、证据、收录），强行统一会产生一个虚假的中央写入口。分域后仍满足「一个对象一个 writer」。

| asset_class | 唯一 writer |
|---|---|
| content_master / content_rendition / cover / audio | Clone |
| evidence_file | Daisy |
| earned_coverage | Vicky |

**字段规格**

| 字段 | 类型 | 必填 | 取值域 | 示例 | 为空语义 |
|---|---|---|---|---|---|
| asset_id | str(30) | Y | `ast_`+ULID26 | ast_01JB7M9Q… | — |
| asset_class | enum | Y | `content_master`/`content_rendition`/`evidence_file`/`earned_coverage`/`cover`/`audio` | content_rendition | — |
| variant_id | str | N | 内容类必填 | var-bpc-tiktok-00317-v04 | `NOT_APPLICABLE`：证据与 coverage 类 |
| content_hash | char(64) | Y | sha256(bytes) | 3a7f… | — |
| platform_spec / duration_ms | enum / int | N | `9x16`/`4x5`/`1x1`/`16x9`/`pdf`/`none` | 9x16 / 28000 | `NOT_APPLICABLE` |
| claim_refs | list | Y | 该素材实际说出的 claim 版本 | [clm-bpc-us-0142@3] | 不允许为空：未声明宣称的素材禁止进 paid |
| rights | obj（只读投影） | N | 由 `asset_rights` 物化：`{creator_id, scope[], account_ids[], territory[], valid_to, doc_asset_id, credential_type}` | 见 §0.8 | `ABSENT`：无 `asset_rights` 行 = 全自有，无需第三方授权 |
| distribution_targets | list | N | `pdp`/`amazon_aplus`/`tiktok_organic`/`tiktok_paid`/`meta_paid`/`pr`/`ai_answer` | [tiktok_paid] | `NOT_YET_OBSERVED`，须填 `due_by` |
| status / version | enum / int | Y | `ingested`/`validated`/`distributed`/`retired`/`quarantined`；≥1 | validated / 1 | — |

**`rights` 是只读投影，不是存储**：唯一可写存储是 `asset_rights`（§0.8）。物化方是 Radar：视图定义与刷新规则归 Radar，刷新任务只执行 `asset_rights` 按 `asset_id` 的聚合，无业务写权。物化时机：`asset_rights` INSERT / UPDATE 提交后刷新；每日对账兜底，投影与台账差异 >0 即告警。读方（授权 Gate、投放侧、PMO 结算、Emily/GEO/Shopify）只能 SELECT；Clone / Daisy / Vicky 及任何产线对 `asset.rights` 无 INSERT / UPDATE 权限，直接写视为契约违规并记审计。

**编码**：`ast_{ULID26}` + `content_hash` 唯一索引。文件高频、机器产生、无需人念，用 ULID；但只有 ULID 不够——同一文件重复上传会产生两个 ID，因此用 content_hash 做唯一约束保证幂等（先查 hash，命中则复用原 ID）。不采用「哈希即 ID」，因为平台重编码会让同一创意产生新字节，需要保留「同一 asset 的多个字节版本」这一层。

**生产者 → 消费者**

| 产线 | 权限 | 说明 |
|---|---|---|
| Clone / Daisy / Vicky | 按 class 创建与改 status | 分域唯一 writer |
| 投放侧 | 只读 + 追加 `ad_refs` | — |
| 守衡 | 只读 + 置 `quarantined` | 授权撤回 / 合规命中 |
| Emily、GEO、Shopify | 只读 | 内容日历 / AI 答案素材 / PDP 分发 |

**状态机**：`ingested → validated → distributed → retired`，旁支 `validated → quarantined → validated|retired`。

1. ingested→validated：writer，前置条件 content_hash 与 claim_refs 齐备
2. validated→distributed：分发方
3. validated→quarantined：守衡（授权撤回 2h 内）或 Radar（creator 撤权）
4. quarantined→retired：writer

**版本与不可变**：不可变 `asset_id`、`content_hash`、`asset_class`。改字节 = 新建 asset + supersedes，使「终版-2-改」的历史完整可回溯。可追加 `distribution_targets`；`rights.valid_to` 不可由 asset writer 直接改，延期必须由 Radar 改 `asset_rights.valid_to`，投影随后刷新。

**关联**：`asset_id N:1 variant_id`（内容类）；`1:N evidence_id`（反向 file_asset_id）；`1:N asset_rights`；`N:M distribution_targets`。

## 7. ad_id
**语义**：一个投放绑定实例——某个 variant 在某个广告账户、某个 ad group、某段时间窗口内的一次具体投放。是花费、曝光、CTR、CVR 唯一可以挂载的对象。

**唯一写入口**：投放侧。该产线当前不存在（S5 空白），因此规定四条过渡规则：

1. ad_id 采用 D 派生型 `ad-{pf}-{acct}-{ext}`，由平台导出的 (账户短码, 外部 ad id) 确定性生成，不依赖任何内部注册协调。
2. 任何拿到平台导出的一方都可重建同一 ID，重复导入幂等——这是「无人负责」状态下唯一可执行的唯一性方案。
3. 过渡期 owner 记为 `PMO (steward)`，`owner_status=provisional`；S5 建立后 30 天内移交，ID 不变。
4. 过渡期禁止：手工编造 ad_id；没有 ad_id 的花费记录进入归因报表。宁可缺，不可错。

**字段规格**

| 字段 | 类型 | 必填 | 取值域 | 示例 | 为空语义 |
|---|---|---|---|---|---|
| ad_id | str(64) | Y | `ad-{pf}-{acct}-{ext}` | ad-ttUS-A1B2-1798456 | — |
| platform / account_code | enum / str(8) | Y | `tiktok`/`meta`/`google`/`amazon`/`youtube`；短码分配后不可改 | tiktok / ttUS-A1B2 | — |
| external_ad_id | str | Y | 平台原始 ID | 1798456123456789 | — |
| variant_id | str | Y | 绑定变体 | var-bpc-tiktok-00317-v04 | 不允许为空：无变体的投放不得存在 |
| audience_ref / landing_ref | str | N | 受众包 ID+版本；PDP/listing 版本 | aud_lal_bpc_1pct@2 / pdp_bpc_serum@v12 | `NOT_YET_OBSERVED` |
| budget_daily | decimal | N | USD | 250.00 | `NOT_APPLICABLE`：CBO 或账户级预算 |
| flight_start / flight_end | ts | Y | UTC | 2026-11-01 / 2026-11-15 | — |
| spend / impressions / ctr / cvr | decimal | N | 平台口径 | — | `NOT_YET_OBSERVED`，`due_by`=次日 09:00 |
| attribution_window / owner_status / status | enum | Y | `1d_view_7d_click`/`7d_click`/`platform_default`；`provisional`/`assigned`；`draft`/`active`/`paused`/`ended` | 7d_click / provisional / active | — |

**编码**：D 派生型。这是全字典里唯一没有产线 owner 的主键；派生编码是唯一能在无人负责状态下保持唯一性与幂等的方案——ID 完全由外部事实决定，不依赖内部注册流程。代价：`account_code` 变更会产生新 ID，因此账户短码一旦分配不得更改（写入账户主表约束）。

**生产者 → 消费者**

| 产线 | 权限 | 说明 |
|---|---|---|
| 投放侧（未建） | 创建 / 改全部 | 最终 writer |
| PMO（过渡 steward） | 由导出重建 / 只读 | 不手工新建 |
| Clone | 只读 + 追加 `handoff_packet_id` | 素材交接 |
| Emily、Shopify、Signal | 只读 | 假设回写 / 落地页 CVR / 声量关联 |

**状态机**：`draft → active → paused → active`，`active → ended`。迁移权归投放侧；过渡期暂停由 PMO 依合规或授权 gate 执行，`pause_reason` 必须记录来源（守衡/Radar/PMO）。

**版本与不可变**：不可变 `ad_id`、`platform`、`account_code`、`external_ad_id`、`variant_id`——四项为平台侧事实，改了就不是同一次投放；平台改绑变体视为新 ad。可追加指标字段（每日快照追加，不覆盖）、`status`。

**关联**：`ad_id N:1 variant_id`；`N:1 account`；`N:1 audience`；`1:N metric_snapshot`；`0:N event_id`。

## 8. creator_id
**语义**：一个真实合作主体（达人、名人、编辑、联盟客、机构），跨平台、跨改名、跨合同期保持同一身份。解决「同一个人在小红书/TikTok/IG 上是三个 ID」与「改名后历史合作断链」。

**唯一写入口**：Radar。Radar 是唯一持有谈判约束、授权范围与结算关系的产线；授权台账必须以 creator_id 为主键，若 Clone 也能建 creator，授权七元组会分裂成两套。达人供应链（寄样/回收/结算）当前无 owner，过渡期并入 Radar 的一个模块，写入口不变。

**字段规格**

| 字段 | 类型 | 必填 | 取值域 | 示例 | 为空语义 |
|---|---|---|---|---|---|
| creator_id | str(12) | Y | `crt-{seq6}` | crt-000027 | — |
| legal_name | str | Y | 合同主体名 | — | `NOT_YET_OBSERVED`，`due_by`=首份合同签署 |
| handles | list | Y | `[{platform, handle, since, until}]`，≥1 | [{tiktok, @x, 2024-02}] | 不允许为空 |
| creator_tier / content_domain | enum / list | Y | `celebrity`/`s_tier`/`a_tier`/`koc`/`affiliate`/`editor`；类目对齐 | koc / [bpc, bmc] | — |
| market_reach | list | Y | `us`/`eu`/`uk` | [us] | — |
| exclusivity | obj | N | `{competitor_ids[], until}` | {[…], 2027-02-01} | `ABSENT`：无排他 |
| risk_flags | list | N | `controversy`/`disclosure_missing`/`claim_overreach`/`competitor_lock` | [disclosure_missing] | `ABSENT`：无已知风险 |
| rights_template_id | str | N | 标准授权模板版本 | rtpl_spark_v3 | `NOT_YET_OBSERVED` |
| status / version | enum / int | Y | 见状态机；≥1 | active / 2 | — |

**编码**：`crt-{seq6}`，不含平台、类目、档位。creator 的身份问题本身就是「跨平台同一人」，把平台编进 ID 会强迫同一个人拿 3 个 ID——这正是当前授权台账失效的机制原因；档位会变、类目会变，任何业务属性进 ID 都会导致改属性=换 ID=历史断链。序号 + handles 子表是唯一稳定解。

**生产者 → 消费者**

| 产线 | 权限 | 说明 |
|---|---|---|
| Radar | 创建 / 改全部 / 改 status | 唯一 writer |
| Clone | 只读 + 追加 `asset_ref` 外键 | 不改 creator 本体；不得写 `asset_rights` 任何授权字段 |
| Emily、Vicky | 只读 | brief 目标人 / PR 关系（editor 类） |
| 守衡、PMO | 只读 | 授权 gate / 结算口径 |

**状态机**：`prospect → vetted → contracted → active → dormant → blacklisted`，旁支 `vetted → rejected`。

1. prospect→vetted：Radar，尽调完成
2. vetted→contracted：Radar + 人工签署
3. contracted→active：Radar，首条内容发布
4. active→dormant：Radar，180 天无合作
5. any→blacklisted：Radar + 合规双签

**版本与不可变**：不可变 `creator_id`。可追加 `handles`（只增不删，用 `until` 标记失效）——handle 可变、人不可变；删旧 handle 会让历史素材找不到当时的账号归属。

**关联**：`creator_id 1:N creator_handle`；`1:N asset_rights`（与 asset_id 组成授权七元组，写入口见 §0.8）；`N:M ad_id`（经 asset）；`1:N campaign`。

## 9. 主键之间的有向关系

```text
claim_id 1:N evidence_id
claim_id 1:N script_id            (经 script.claim_refs)
claim_id 1:N asset_id             (经 asset.claim_refs)
script_id 1:N variant_id
variant_id 1:N asset_id
variant_id 1:N ad_id
asset_id 1:N asset_rights N:1 creator_id   → 授权七元组 (asset_id, creator_id, scope[], account_ids[], territory[], valid_to, doc_asset_id) + credential_type
event_id 1:N event_observation
event_id 1:N claim_id             (regulatory / 宣称类事件)
event_id 0:N ad_id                (投放暂停联动，过渡期不启用)
evidence_id N:1 asset_id          (file_asset_id)
evidence_id N:M claim_id
```

三条硬约束：① 禁止反向引用，下游写 `parent_id`，上游不写 `children[]`（event 的 observation_ids 为物化视图除外）——双向引用必然产生两份真相，并发写会分叉。② 禁止跨层跳引用，ad 只引用 variant 不直接引用 script，asset 只引用 `claim_id@version` 不复制 statement。③ 过渡期降级的键（§11）必须以 `legacy_` 或裸字符串标记，不得冒充正式 ID。

## 10. 断点修复对照

| 断点 | 现状 | 修复键 | 修复机制 | 判定标准 |
|---|---|---|---|---|
| BP-02 claim 三源 | Emily 引用、Daisy 事实库、守衡规则库各存一份；规则未命中默认放行 | claim_id + evidence_id | claim 表只有 Daisy 有写权限；守衡只 append 规则绑定子表；Emily 降级为只读缓存；未 approved 不得进脚本 | 全库 claim 文本只存在一处；任一内容里的 claim 可反查到唯一 `claim_id@version`；规则未命中时 verdict 必须为 `manual_required`，不得为 `pass` |
| BP-03 素材到投放主键链缺失 | script→variant→ad→asset 无定义，素材表现无法回写脚本 | script_id + variant_id + asset_id + ad_id | 四键构成显式有向链；variant 的 changed_variable 单值约束 | 任一 ad 的花费可沿 ad→variant→script→claim 反查到叙事假设，路径 ≤4 跳且每跳为 1:1 或 1:N |
| BP-04 事件无去重主键 | 三套告警三套分级；主单按最早命中方建，Echo 永远先命中 | event_id | dedup_fingerprint 唯一索引；primary_owner 由 event_type 路由表决定，不看命中先后 | 同一源帖 24h 内只产生 1 个 event_id；`media_negative` 类事件的 primary_owner 100% 为 vicky |
| BP-06 coverage 字段与下游不一致 | 资产卡与 PDP/A+/GEO 字段不一致，授权三态无下游格式 | asset_id（earned_coverage 类）+ claim_id + evidence_id | coverage 不再是独立卡片，改为 asset 的一个 class；下游读同一 record 的同一枚举，不各自转换 | PDP/A+/GEO 三处引用的覆盖率、授权范围、claim 版本字段级 diff = 0 |
| BP-11 授权台账缺 creator_id | Clone 谱系无 creator/到期/撤回；2h 内无法定位关联素材 | creator_id + asset_id | 授权 = (asset_id, creator_id, scope[], account_ids[], territory[], valid_to, doc_asset_id) 七元组 + `credential_type`，唯一写入口是 Radar；撤回时按 creator_id 反查 asset_id | 任一 creator 撤权后 2h 内可列出全部在用 asset；进入 paid 的 asset 100% 有七元组 |
| BP-16 发布记录不回填 | 账号/时间/付费/受众/预算/素材 ID 无人回填内容日历 | variant_id + asset_id + ad_id | publish_record 为 variant 的必填子记录；未填则 variant 不能进 `testing`；付费发布自动带 ad_id | 100% 已发布 variant 有 publish_record；内容日历与平台后台发布条数差异 = 0 |

副带闭合（非本次主目标，但结构上同时成立）：BP-07 事实源版本（强制 `id@version` 引用）、BP-10 brief 授权字段（creator_id + 七元组前置）、BP-14 实验设计（variant 单变量 + control_variant_id）。

## 11. 一次落地：只做 3 个主键

选 **claim_id、variant_id、event_id**。

1. **三个都有活着的 owner**：Daisy+守衡、Clone、Signal 均在运行。不需要先建产线，不需要组织调整，落地不依赖任何未授权动作。
2. **三个都已被现有动作强制触碰**：每篇内容过 claim 预检（雏形已在）、每条素材有文件名（无结构）、每条告警进群（三套）。落地只需把已有动作改写成写主键，不新增流程。
3. **三个合计修掉 BP-02/03/04/06/16 五个**，占已知 6 个中的 5 个。
4. **三个构成其余 5 个的前置**：evidence 是 claim 的子结构；script 是 variant 的父；asset 是 variant 的产出；ad 是 variant 的下游；creator 只有在 asset 存在授权绑定时才有意义。先做 ad_id 会卡在 S5 无 owner，先做 creator_id 会卡在 asset 不存在。
5. **对齐执行顺序第 1 步**：主键字典 → RACI → 三个 gate。claim_id 直接支撑 claim gate，variant_id 直接支撑实验 gate，event_id 直接支撑 RACI 的处置 owner。

**其余 5 个的降级形态**

| 键 | 降级形态 | 撑住什么 | 会漏什么 | 升级触发条件 |
|---|---|---|---|---|
| script_id | variant 上的必填字符串 `script_ref`，Emily 按 `scr-{cat}-{platform}-{seq5}` 手工生成，不入注册表 | 溯源到脚本 | 无脚本状态机与拒单留痕；改脚本无 trace | 出现「同一脚本跨批复用」，或 Clone 拒单需留痕 |
| evidence_id | claim 内嵌 `evidence[]`：{type, issuer, issued_at, url 或 file_hash, valid_until} | claim 有证据可查 | 一份证据支撑多 claim 时重复；证据撤回无法一次传播 | 首例证据撤回事件 |
| asset_id | variant 上的 `file_hash` + `platform_spec` 二元组 | 文件去重与版本回溯 | 无法承载授权七元组与分发目标；无隔离（quarantine） | 首例授权撤回或平台拒审 |
| ad_id | variant 上的 `ad_refs[]`（platform + external_id + account_code 字符串） | 花费能与变体关联 | 无 flight/budget/audience 结构；无指标快照 | S5 产线建立 |
| creator_id | Radar 达人档案表自增主键 + (platform, handle) 唯一约束 | 单平台内可查 | 跨平台同一人重复；改名断链；授权反查漏 | 首例达人改名或多平台签约 |

**落地检查点（可判定）**：① 新内容 100% 带 `clm-…@{version}`，旧内容按批回填、回填率进周报。② 新素材 100% 带 `var-…`，`changed_variable` 非空且单值，文件名不再承担身份。③ 新告警 100% 以 `event_id` 为群内唯一引用，同一帖出现在三个群时三处 ID 相同。

## 12. 反例校验

### 12.1 claim 三源打架
**现状**：「含 20% 烟酰胺」在 Emily 脚本库、Daisy 事实库、守衡规则库各有一份。Emily 写 20%，Daisy 记录供应商给的 18%，守衡按关键词命中判「需检测报告」而报告只覆盖 18%。三处不同步，素材拍完被拒审，返工两周。

**落地后**：① Daisy 建 `clm-bpc-us-0142`，statement 固定为「含 18% 烟酰胺」，evidence_refs 挂 `evd_01JB…@1`（SGS 报告，第三方，有效至 2027-08-13）。② 守衡 append 规则绑定 `rule=bpc-claim-v4@4, verdict=conditional, required=L2_third_party, allowed_channels=[organic,pdp]`，paid 被排除。③ Emily 只读 `clm-bpc-us-0142@1`，脚本存引用不存文本；要写 20% 只能提 `claim_request`，Daisy 不批则写不进去。④ claim gate 校验引用版本 = 当前版本、verdict ≠ rejected、channel ∈ allowed_channels，任一不满足则 `script.status` 无法进 `approved`。

**结果**：三源变一源加两个只读引用。冲突从「三个库不一致」变成「一条 correction_request 有回执」。

### 12.2 素材改 6 版无法归因
**现状**：一条素材文件名 `终版-2-改`，实际改了钩子、开头画面、CTA、BGM、字幕、时长共 6 处。报表只到 campaign 层级。复盘只能得出「新版更好」。

**落地后**：① 原脚本 `scr-bpc-tiktok-00317` 下有 `v00`（对照）+ `v01..v06`，每个只允许一处 `changed_variable`：hook、opening_frame、cta、bgm、subtitle_style、duration。② 想一次改 6 处会被拒绝——`changed_variable` 是单值枚举，上一批胜出值只能在下一批叠加，这是「改 6 个地方一起改，跑出来无法归因」的结构性阻断。③ 每次导出（9:16 与 4:5）产生 2 个 `asset_id`，同 variant 不同 platform_spec；字节不同但变体相同，重导出不产生新 variant。④ 投放产生 3 条 ad（跨 2 个账户），各带 `ad_id`。⑤ 复盘按 variant_id 聚合 ad 指标，输出 6 行，每行一个变量。

**结果**：结论从「新版更好」变成「钩子贡献 +0.4pp CTR，BGM 无显著差异，时长 28s→21s 使 2s 留存 -6pp」。归因单位从「文件」变成「变量」。

### 12.3 三条告警进三个群
**现状**：同一个 Reddit 差评帖，Echo 报产品负面、Signal 报声量异动、Vicky 报舆情预警。三条告警、三个群、三个分级。Vicky 按「最早命中方」建主单，Echo 永远先命中，媒体负面永远无 PR 主单。

**落地后**：① Signal 用 `dedup_fingerprint = sha256(entity ⊕ topic_cluster ⊕ 6h_bucket ⊕ source_cluster)` 建 `evt_01JB…`，唯一索引保证只建一次。② Echo 与 Vicky 各自只 append `event_observation`（来源、原文、自有分类），不改 event 本体。③ `event_type` 由 topic_cluster 映射表判为 `media_negative`（该帖被 2 家行业媒体引用）→ `owner_rule=evt-route-v3` → `primary_owner=vicky`，主单归属不再取决于谁先看到。④ 三个群改为订阅同一 event_id 的三个视图：Signal 看量、Echo 看产品归因、Vicky 看待处置，群里出现的是同一个 ID。⑤ 关闭需 `resolved` 附回落数据（该 topic_cluster 24h 提及量回到基线 ±20%），否则不允许关闭。

**结果**：告警条数不变（三方可各自订阅），事件数从 3 变 1，主单 owner 可预期。

## 13. 未核验与风险
**推断项**

- 各产线实际数据模型未读取（无产品代码与库表可访问），字段规格按业务动作反推最小集，落地前必须与实际 schema 对齐。
- ad_id 的 D 派生型依赖平台导出字段完整性；TikTok GMV Max、Meta Advantage+ 等自动投放层级的外部 ID 稳定性未经实测。
- publish_record 的「未填不得进 testing」以当前无发布 owner（BP-24）为前提；若发布仍由人工多账号操作，回填率是最大落地风险。
- creator_id 的跨平台合并依赖人工判断，自动化只能给候选提示，最终确认权在 Radar。

**需真实系统数据才能确认**：现有 claim 总量、重复率、evidence 覆盖率；素材文件的实际版本数与被投放引用率；三条告警的实际重复率（估计约 60% 重叠，未验证）；授权台账现存条目数与已过期条目数。

**风险**

- 主键落地会立刻暴露历史数据无 ID 的存量问题。回填成本远大于新建，必须给存量数据 `legacy_` 前缀与并行期，不做强制清洗。
- 单写入口在组织上等于拿走别人的写权限。claim_id 从 Emily 收归 Daisy 会遇到直接阻力；若不同步调整 RACI 与考核，主键会被绕过——绕过方式是脚本里硬编码文本、不引用 claim_id。检测手段：发布前做「文本→claim_id 反查」，反查不到即阻断。
- 派生型 ad_id 在 account_code 变更时会分裂，必须在账户主表加不可变约束，否则一年后同一投放出现两个 ID。
- 三键最小方案留下 asset_id 缺口，授权七元组在过渡期无处安放；这期间的 paid 投放授权校验只能靠人工清单，是已知敞口，不能宣称已被治理覆盖。

---

## 14. ai_answer_snapshot_id（第 9 键，2026-11-02 增补）

### 14.1 为什么必须加，而不是把 GEO 并入 Signal

GEO 的两个指标 `m-x-ai-mention@1`（AI 提及率）与 `m-x-ai-accuracy@1`（AI 准确率）在 2026-11-01 版里**没有对象宿主**：RACI §3.2 判定 GEO 为「唯一两类 A 都没有的产线」，指标字典 §14.3 写「无主键宿主，90 天内不补第 9 个主键，GEO 的 M 栏无法绑定对象」。结果是 GEO 的申报集整体不成立，按 §15 会自动进收缩名单。

三个候选处置及否决理由：

| 处置 | 为什么不行 |
|---|---|
| 并入 Signal（复用 `event_id`） | `event_id` 的语义是「一次被观测到的公开信号事件」。AI 回答里**品牌未被提及**是最关键的数据（GEO 的核心是缺口分析），而它没有实体、没有事件、不构成「信号事件」。若强行以「无提及」建事件，会让 Signal 的声量口径被污染，也让 GEO 只能统计命中项、统计不了缺失项 |
| 挂到 `asset_id` 的 `ai_answer` class | `asset_id` 是「可下载、可播放、可上传的字节实体」，`content_hash` 是唯一索引的一部分。AI 回答是**外部系统输出的文本快照**，同一问题每次复测内容不同、无法做字节去重，硬塞进 asset 会让 content_hash 的唯一性约束失效 |
| 不建主键，GEO 只报 work_item | 这是当前状态，等于承认 GEO 不参与 OGSM 结算。但它承担 S1.2「权威可见度」这一条战略，战略不能挂在一个无法结算的产线上 |

**结论：新增第 9 键。** 判定依据是 §0.6 的写入口判据反用——「两个系统各能创建同一对象即判定主键失效」；反过来，**一个对象被 ≥3 条产线同时需要、且当前无任何既有键能承载它的语义，就必须发独立 ID**。

### 14.2 语义

**一次在指定 AI 引擎上、用指定问句、在指定时点发起并留存的回答快照。** 是「AI 现在怎么说我们」的最小可复测单位。

它是**观测记录**，不是事件、不是内容、不是证据：
- 不是事件（`event_id`）——不要求有实体与主题簇，「无提及」也是有效快照；
- 不是内容（`asset_id`）——不对字节负责，只对「问题 + 引擎 + 时点 + 回答原文」这个四元组负责；
- 不是证据（`evidence_id`）——不支撑任何 claim；反过来，claim 是它的输入之一。

### 14.3 唯一写入口

**GEO。** 只有 GEO 的采集探针可 INSERT，理由与 §1 的 Signal 相同：探针是唯一知道「这个问句问的是谁、用的哪个引擎、什么时候问的」的一方。若 Amazon 站内也能建（Rufus 侧），同一问句在 Rufus 与 ChatGPT 上会出现两套 ID 体系，缺口分析无法合并。

Amazon 站内与 Signal 只能**读**，或追加 `observation`（见 §14.5 的 `platform` 字段区分 Rufus）。

### 14.4 字段规格

| 字段 | 类型 | 必填 | 取值域 | 示例 | 为空语义 |
|---|---|---|---|---|---|
| ai_answer_snapshot_id | str(30) | Y | `aia_`+ULID26 | aia_01JD2K9M4Q8R1S3T5V7W9X2YZ | — |
| engine | enum | Y | `chatgpt`/`gemini`/`perplexity`/`copilot`/`amazon_rufus`/`tiktok_search` | chatgpt | — |
| prompt_id | str | Y | 问句库版本化对象 `q-{cat}-{seq4}@{version}` | q-bpc-0142@3 | 不允许为空：无问句的快照不可复测 |
| prompt_text | text | Y | 快照时的问句原文（冗余存，防止问句库改版后历史失真） | 「孕妇可以用烟酰胺吗」 | — |
| asked_at | ts UTC | Y | ISO-8601 | 2026-11-02T08:00:00Z | — |
| answer_text | text | Y | 回答原文全文 | … | 不允许为空：无原文的快照不可复核 |
| answer_sha256 | char(64) | Y | sha256(answer_text 规范化后) | 7c1f… | — |
| brand_mentioned | bool | Y | 是否提及本品牌（可为 false，这是有效值） | true | 不允许为空 |
| mention_position | int | N | 首次提及的段序号（≥1） | 3 | `ABSENT`：未提及 |
| cited_sources | list | N | 回答中引用的 URL/来源域，≥0 条 | [「自家域」, 「竞品域」] | `ABSENT`：无引用 |
| cited_own | bool | Y | 是否引用了品牌自有权威源 | false | 不允许为空：这是「准确率」的分子 |
| competitor_mentions | list | N | 同回答中出现的竞品名 | [竞品 A] | `ABSENT`：无 |
| accuracy_verdict | enum | N | `accurate`/`partial`/`wrong`/`not_applicable` | partial | `NOT_YET_OBSERVED`，`due_by`=快照后 2 工作日：待人工标注 |
| judged_by | obj | N | `{type: human/agent, id}`；agent 须登记模型版本 | {human, pm_01} | `ABSENT`：未标注 |
| market / locale | enum / str | Y | `us`/`eu`/`uk`；`en-US` 等 | us / en-US | — |
| question_set_version | str | Y | 问句集版本（20 问/ASIN 或按类目） | qs-bpc-us@2 | — |
| status / version | enum / int | Y | `captured`/`judged`/`superseded`；≥1 | judged / 1 | — |

**为什么存 `prompt_text` 冗余**：`prompt_id@version` 能定位问句，但问句库改版后旧版本的措辞可能已被覆盖。AI 对措辞极度敏感，差一个词答案就变。历史快照必须能独立复现「当时问的是什么」，所以原文冗余入库。

**为什么 `brand_mentioned=false` 是合法值**：GEO 的核心交付是**缺口**——哪些问句里 AI 不提我们。若把「未提及」当空值处理，缺口分析就永远只有 0 条。

### 14.5 编码

`aia_{ULID26}`。理由与 `event_id`/`evidence_id` 一致：高频、机器产生、按时间排序有价值、无需人念。**不用可读型**，因为它的主键维度是「引擎 × 问句 × 时点」三元组，写进 ID 会很长且绝大多数组合永不出现。

### 14.6 生产者 → 消费者

| 产线 | 权限 | 说明 |
|---|---|---|
| GEO | 创建 / 改 status / 改 accuracy_verdict | 唯一 writer |
| Amazon 站内 | 只读 + 追加 `engine=amazon_rufus` 的采集请求 | 不得改判定；Rufus 侧快照同样由 GEO 落库 |
| Signal | 只读 | AI 回答可作为负面信号源，用于 `event_observation` |
| PMO | 只读 | 指标口径与结算 |
| 内容产线、Radar | 只读 | 缺口 → 选题输入 / 达人 brief |

### 14.7 状态机

`captured → judged → superseded`

1. captured→judged：GEO 或人工标注 `accuracy_verdict` 后
2. judged→superseded：同 `prompt_id` 在同引擎复测出新快照时，旧快照置 `superseded`（**不删除**，缺口趋势需要历史）
3. 无 rejected 态：快照是观测记录，不存在「错答」，只存在「AI 答错了」这一事实

### 14.8 度量（GEO 的申报集从此成立）

| 指标 | 公式 | 分子分母来源 |
|---|---|---|
| `m-x-ai-mention@1` AI 提及率 | `brand_mentioned=true` 的快照数 ÷ 同期 `captured` 且 `judged` 的快照总数 | 按 `question_set_version` 与 `engine` 分层 |
| `m-x-ai-accuracy@1` AI 准确率 | `accuracy_verdict=accurate` 的快照数 ÷ `accuracy_verdict≠not_applicable` 的快照数 | 只统计已标注 |
| `m-x-ai-cited-own@1` 自有源引用率（新增，可选） | `cited_own=true` 的快照数 ÷ 总快照数 | — |

三条硬规则：

1. **分母必须按问句集版本分层。** 换问句集 = 新版本，旧快照不进新分母，否则「加了 10 个不利问句」会被读成「提及率下降」。
2. **`captured` 但未 `judged` 的快照不进准确率分母**，进提及率分母（提及是三值判定，准确率需要人工）。
3. **两个指标都是 `explain_only`。** GEO 是零段 A 产线，它指向的 L1 是「品牌词搜索量 → NTB」，按指标字典 §14.3 R2 必须写明指向——已写明，且不得单独作为预算依据。

### 14.9 这次增补的代价（必须承认的三件事）

| 代价 | 具体是什么 | 缓解 |
|---|---|---|
| 多一个写入口 | §0.1 的原则是每加一个顶层 ID 就多一处协调 | 只有一个 writer（GEO），且它当前只服务 3 条线，协调面小于 `asset_id` 的 3 域分权 |
| 问句库成为新的版本化对象 | `prompt_id@{version}` 之前未登记，现在成了 GEO 的硬依赖 | 与 `competitor_set@{version}`、`sov_weight@1` 同构，复用既有版本化模式，不新增范式 |
| 人工标注成本 | 准确率需要人工 golden set，与 B-12 抽检口径一致 | 首批只标注 20 问 × 3 引擎 = 60 条/月，可控；未标注的快照不影响提及率 |

### 14.10 落地检查点（可判定）

1. 新建快照 100% 带 `prompt_id@{version}` 与 `answer_sha256`；缺一即采集器有 bug。
2. 同一 `prompt_id` 在同一引擎的 `captured` 快照，历史版本必须为 `superseded`，**不允许同版本两条 active**。
3. `brand_mentioned=false` 的快照占比能在页面上单独看到——看不见缺口，就等于没建这个键。
4. 复测闭环：任一季度必须能用该键产出「Top N 未提及问句」清单，且清单被内容产线或 GEO 实际消费 ≥1 次。做不到即该键未成立，按 §11 的降级逻辑回退为 work_item。

---

## 15. order_id 与 sku_id（域外键，2026-11-02 增补）

### 15.1 为什么这两键的优先级高于原三键

原 §11 的落地顺序是 `claim_id` → `variant_id` → `event_id`，选它们的理由是「三个都有活着的 owner」。这个理由仍然成立，但它只回答了**可执行性**，没回答**紧迫性**。

2026-11-02 对齐 `reports/` 九份专家报告后，出现了一个原方案没有预料到的事实：**三个独立建设中的专家，各自用手工方法补同一件事——没有 `sku_id`。**

| 专家 | 报告原话 | 实际在做什么 |
|---|---|---|
| Vicky | 「Tracker 品线覆盖 **0.0%**」（347 条记录该字段全空） | PR 报道无法关联到具体品线，只能用自由文本手打 |
| Echo | 「产品身份解析覆盖率 **2/56**」 | 从 Reddit 帖子里人工推断说的是哪个产品 |
| Shopify | 「Listing 依赖商品主数据」 | MAS 的 5 个 Agent 必须先把 SKU 对上才能工作 |

三个人用三种方法做同一件事，且互不相通。这是**重复建设最贵的形态**：不是多花一次钱，而是三份无法合并的数据。所以 `order_id + sku_id` 的落地优先级应提到三键之前或并行。

差别的性质要说清楚：

| | `claim_id` / `variant_id` / `event_id` | `order_id` / `sku_id` |
|---|---|---|
| 作用 | **建新**：让未来的对象有唯一身份 | **止损**：让已有的重复建设停止 |
| 收益 | 未来可归因 | 现在就有三份数据可合并 |
| 谁在等 | 三个 Gate | 三个已建成的专家 |
| 失败代价 | 归因失效（延后可见） | 重复建设继续（每天可见） |

### 15.2 order_id

**语义**：一笔已完成或已取消的交易的主键。是花费、退货、复购、cohort 唯一可挂载的对象。

**唯一写入口**：**交易系统**，不是任何 Agent。具体是 Shopify orders API、Amazon 订单报表、TikTok Shop order API 三处，各按平台规则产生。这里与 9 主键的根本区别是：**它不由我们创建，只由我们接收。**

| 字段 | 类型 | 必填 | 取值域 | 示例 | 为空语义 |
|---|---|---|---|---|---|
| order_id | str | Y | `ord-{pf}-{external_id}` | ord-shopify-5821304 | — |
| platform | enum | Y | `shopify`/`amazon`/`tiktok_shop` | shopify | — |
| external_order_id | str | Y | 平台原始订单号 | 5821304779123 | — |
| placed_at | ts UTC | Y | ISO-8601 | 2026-11-02T03:14:00Z | — |
| customer_ref | str | Y | 匿名化客户标识（sha256(email‖salt)） | c_9f3a… | `ABSENT`：平台未提供 |
| currency / gross_amount | enum / decimal | Y | ISO-4217 / 币种最小单位 | USD / 12800 | — |
| discount_amount / shipping / tax | decimal | N | 同上 | 1500 / 0 / 1023 | `NOT_APPLICABLE`：平台不单列 |
| refund_amount | decimal | N | 累计退款 | 0 | `NOT_YET_OBSERVED`，`due_by`=+90 天 |
| order_status | enum | Y | `placed`/`fulfilled`/`delivered`/`cancelled`/`refunded` | fulfilled | — |
| is_first_order | bool | Y | 该客户在 12 个月内是否首单 | true | 不允许为空：这是 NTB 的唯一来源 |
| market / locale | enum / str | Y | `us`/`eu`/`uk` | us / en-US | — |
| attribution_source | enum | N | `branded`/`organic`/`paid`/`direct`/`referral`/`unknown` | organic | `NOT_YET_OBSERVED`，`due_by`=T0+30 天 |

**三条硬规则**：

1. **`attribution_source` 是 G1 的生死线。** OGSM §9 已记录：「无证据表明订单侧能稳定标记 branded/organic；若不能，G1 退化为品牌词搜索量 + SOV 两个领先指标」。这个字段能否填，直接决定 G1 是结果验收还是过程验收。
2. **`customer_ref` 必须是匿名哈希，不得存原始邮箱。** 复购率与 NTB 都依赖跨单去重，但这是客户数据，只做 join，不做身份关联。
3. **`is_first_order` 由 12 个月窗口算出，不由平台字段直接读。** 平台的「新客」定义各不相同（Amazon 是 12 个月，Shopify 无内置定义），必须我方统一计算，否则 CAC 分母四个平台四个口径。

### 15.3 sku_id

**语义**：一个可售单元的主数据身份。跨平台、跨改名、跨包装版本保持同一身份。

**唯一写入口**：**PMO 定标准、商品主数据持有方落库**（当前是 Shopify-商品与定价 + Amazon 站内，双写合并）。这是唯一需要「合并两处主数据」的键——因为 DTC 与 Amazon 的商品体系天然分裂。

| 字段 | 类型 | 必填 | 取值域 | 示例 | 为空语义 |
|---|---|---|---|---|---|
| sku_id | str | Y | `sku-{cat}-{seq5}` | sku-bpc-00142 | — |
| display_name | str | Y | 对外名 | 硅胶电动吸奶器 S12 | — |
| product_line | enum | Y | `bmc`/`bpc`/`spo`（母婴/美妆/户外） | bmc | — |
| category_map | obj | Y | `{platform: category_path}`，各平台映射 | {amazon: "Baby>Feeding"} | `NOT_YET_OBSERVED`，`due_by`=T0+60 天 |
| platform_ids | obj | Y | `{shopify: handle, amazon: asin, tiktok: product_id}`，≥1 | {amazon: "B0CXXX"} | 不允许为空 |
| variant_axes | obj | N | 颜色/尺码/规格等区分维 | {color: ["pink","beige"]} | `ABSENT`：单规格 |
| status | enum | Y | `live`/`draft`/`delisted`/`retired` | live | — |
| replaced_by | str | N | 换代关系（旧 SKU → 新 SKU） | sku-bpc-00201 | `ABSENT`：非换代 |
| cost_basis / price_band | decimal / str | N | 用于贡献毛利与选品判断 | 8.40 / mid | `NOT_YET_OBSERVED` |
| version | int | Y | ≥1 | 3 | — |

**四条硬规则**：

1. **`sku_id` 与 `platform_ids` 是 1:N。** 一个 SKU 在三个平台有三个外部 ID，但只有一个 `sku_id`。这是它区别于 `asin_id` 的根本点——`asin_id` 是 Amazon 的视角，`sku_id` 是品牌自己的视角。
2. **`product_line` 必须能对上 OGSM 的三条业务线。** Vicky 报告的「Tracker 品线 0.0%」就是因为没有这个字段，PR 报道无法归类到 bmc/bpc/spo。
3. **`replaced_by` 是复购率的分母修正项。** 90 天同品类复购中，用户从旧 SKU 买到新 SKU 算不算同品类？答案是算，且必须显式建模，否则换代产品会被读成「流失」。
4. **禁止把 `variant_axes` 做成 new SKU。** 粉色与米色是两个 SKU 还是同一 SKU 的两个变体，取决于库存与定价是否独立管理。规则：**库存独立则独立 SKU**。

### 15.4 与 9 主键的关系

这两个键**不进 9 主键表**，理由与 `asset_rights` 相同——它们是**外部事实**，不是内部创建的对象：

- 9 主键的判据是「谁有权让对象从不存在变成存在」（§0.6）；`order_id` 从不存在到存在的权力在买家，`sku_id` 在商品上架动作，都不在我方引擎里。
- 但它们**必须出现在每个交接契约的字段表里**，且**缺失即视为未交接**（RACI §4.2 第 2 条）。

因此它们在 RACI §4.3 的「域外键」清单里，编号为：

| 候选键序 | 键 | 当前状态 |
|---|---|---|
| 第 9 | order_id | **2026-11-02 提级：与三键并行，由 Source 落库** |
| 第 10 | sku_id | **同上** |

原先登记的 9–17 顺延为 11–19，编号一次性重排，不做两套并存（避免重演「两个第 9 候选键」的历史问题）。

### 15.5 落地检查点（可判定）

| # | 检查点 | 判据 |
|---|---|---|
| 1 | 订单覆盖率 | 三个平台导出的订单中，带 `order_id` 的比例 = 100%（含取消单） |
| 2 | NTB 可算 | 任取 30 天窗口，`is_first_order=true` 的订单数 ÷ 全部新客订单数 = 100%（即口径可复现） |
| 3 | `attribution_source` 填充率 | 分层为 branded/organic/paid 的订单占比；**若 <70%，G1 必须降级为过程验收**（OGSM §9 已写死的后果） |
| 4 | SKU 覆盖 | Vicky Tracker 347 条记录中，`sku_id` 非空的比例 ≥90% |
| 5 | Echo 身份解析 | 产品身份解析覆盖率从 2/56 提升到 ≥80% |
| 6 | 跨平台一致性 | 同一 SKU 在 Shopify 与 Amazon 的 `sku_id` 一致率 = 100%（不一致即主数据分叉） |

### 15.6 代价与风险

| 项 | 内容 | 缓解 |
|---|---|---|
| 商品主数据双写 | Shopify 与 Amazon 各有一套，合并必然有冲突（价格、名称、类目路径） | `platform_ids` 分列，不强行统一名称；冲突裁决权归 Shopify-商品与定价（OGSM 已定） |
| 历史订单回填 | 存量订单无 `sku_id`，只能用商品名模糊匹配 | 按 §11 的 `legacy_` 前缀并行，不强制清洗；新建订单 100% 用新契约 |
| `attribution_source` 可能拿不到 | 这是 G1 的生死线，也是最可能失败的一项 | 若 T0+30 天仍 <70%，按 OGSM §9 明确降级，不得用全站 CAC 冒充 |
| 三个平台口径不一 | Amazon 12 个月新客、Shopify 无定义、TikTok 又一套 | 统一由我方计算 `is_first_order`，不读平台字段 |

### 15.7 未核验

- 三平台订单导出字段的实际完整度未验证（`attribution_source` 是否可从 UTM/落地页参数稳定推断，取决于埋点质量）。
- Shopify 与 Amazon 的商品主数据在当前系统中的重合率未知；若两套体系几乎不重叠，`sku_id` 的合并价值需重新评估。
- 「库存独立则独立 SKU」的判定需要读取库存系统，当前无证据表明存在统一库存主数据。
