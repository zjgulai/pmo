---
title: 品牌 Agent 三个 Gate 规格与 Fail-closed 默认
doc_type: analysis
module: brand-agent
topic: three-gates
status: draft
created: 2026-11-01
updated: 2026-11-01
owner: self
source: human+ai
---

# 品牌 Agent 三个 Gate 规格与 Fail-closed 默认

## 0. 总则

### 0.1 形态：状态机守卫，不是评审会

判定对象是 canonical object 的一个版本，不是「这一版感觉行不行」。gate 的输出是一条回执，回执是状态迁移的必要条件；没有回执的迁移在系统层被拒绝，评审会、群消息、邮件批复都不构成回执。gate 能拦住的唯一位置是状态机守卫——状态若能由人手工改，gate 就只是建议。

### 0.2 判定三态与「未出判定」

| 态 | 含义 | 对状态机的作用 |
|---|---|---|
| PASS | 要件齐备、规则命中允许、证据有效且覆盖目标市场与渠道 | 允许迁移 |
| CONDITIONAL | 允许但带可机检限制（渠道 / 账号 / 可播片段 / 有效期） | 允许迁移，带 predicate，到期自动转 BLOCK |
| BLOCK | 命中禁止、要件缺失、证据失效、无法判定 | 拒绝迁移 |
| （未出判定） | 排队、人工未响应、规则未命中转人工中 | 不产生回执；对象停在原状态 = 事实阻断 |

`manual_required` 不是第四种判定，它是「未出判定」的原因码，与主键字典 BP-02 一致。把它实现成放行，是 gate 失效的第一种方式。

### 0.3 五条铁律

1. 规则未命中 ≠ 允许：转人工，未出判定前不得迁移。
2. 证据缺失 ≠ 待补：阻断，不允许「先上后补证据」。
3. 超时未响应 ≠ 放行：停在原状态并升级；超时只产生升级，不产生回执。
4. 无回执 ≠ 通过：系统拒绝迁移，不设人工改状态入口。
5. 回执过期 = BLOCK：`valid_until` 到期由系统置 `expired`，不延续旧判定。

### 0.4 通用回执（子记录，不新增顶层 ID）

回执是子记录，不单独发顶层 ID，引用形式为 `{subject_id}@{version}#{gate}-{seq4}`（`seq4` 为四位补零序号，如 `scr-bpc-tiktok-00317@2#C-0041`；不得写成 `#C-41`）。该形式已登记为字典 §0.1 的第七类子记录 `gate_receipt`；第八类 `rule_object`、第九类 `market_overlay` 同批登记。三类子记录的写入口：`gate_receipt` 由出判定的 gate 写，`rule_object` 由合规 owner 写，`market_overlay` 由 PMO 写；均不参与跨线裸引用，跨线引用必须带 subject_id 与版本。

| 字段 | 说明 |
|---|---|
| subject_id@version#gate-seq4（即 `receipt_id`，是拼成的定位串、不是第 9 个顶层主键） / verdict | 禁止指向「最新版」；asset 类必须带 `content_hash`；pass / conditional / block |
| gate_version / rule_refs[] / market_overlay_version | 判定表版本 + `{rule_id, rule_version, source_locator}`（locator 到文件 SHA + 段落）+ 多市场 overlay map |
| evidence_refs[] | `{evidence_id@version, sha256}`；无证据类写 `NOT_APPLICABLE` |
| conditions[] / valid_until / invalidate_on[] | predicate、失效时间、失效事件（字节变更 / claim 版本 / 规则变更 / 授权撤回 / 到期） |
| judged_by / judged_at / sla_due_at | `{type, id, role}`；agent 判定须登记模型版本与抽检人 |
| supersedes / status | active / superseded / overturned / expired；回执不可改，改判只新建 |

回执绑定五项：`subject_id@version`、`content_hash`、`claim_refs[]` 版本集合、`rule_version`、`market_overlay_version`。任一变化即 `superseded` 重判；五项全不变时后续 gate 可复用，责任仍在原判定人与原规则版本。

## 1. 行业事实与市场叠加

### 1.1 必须固化进规则层的六条事实

| 事实 | 规则对象（提案编码） | 对 gate 的硬要求 |
|---|---|---|
| TikTok Shop 美国区可用达人素材只有四类：店铺授权号、TTAM Spark Ads Video code、ACA、红人联盟授权；营销号与他人广告账户的帖子一律不可用 | `rule-tiktok-shop-creator-asset-sources-us-review` | 凭证白名单；四类覆盖分列；混剪默认无授权 |
| 「混剪不需要授权，投流才需要」是错的：二次剪辑与跨账号复用各需独立授权 | `rule-tiktok-shop-reedit-scope-us-review` | `scope` 缺 `reedit` 即不得剪辑 |
| Amazon 早期评论唯一合规渠道是 Vine；激励评价与 review 操纵是红线 | `rule-amazon-reviews-vine-only-us-review` | `social_proof` 证据必须是 Vine 记录或自然评论快照 |
| 美妆 cosmetic claim 与 medical claim 有法定界线 | `rule-claim-cosmetic-medical-boundary-us-review`、`-eu-review` | 命中 medical 词表须药品/器械资质，否则 BLOCK |
| 母婴内容被理解为面向儿童时触发付费推广披露 | `rule-meta-paid-disclosure-minors-us-review` | 儿童出镜或儿童向表达 → 强制披露 + 禁定向 |
| 运动户外 performance claim 必须有测试证据；EU 叠加 GPSR / REACH | `rule-claim-performance-evidence-sports-outdoor-us-review`、`overlay-eu-gpsr-reach-eu-review` | 证据 `scope_limits` 须覆盖使用条件；缺 overlay 即 BLOCK |

### 1.2 overlay 判定顺序

1. 判定 = base rule 与 market overlay 求交取更严，冲突以 overlay 为准。
2. overlay 缺失或未发布 = BLOCK，不得回退到 base rule 单判。
3. 市场按 `distribution_targets` 与 `ad.flight` 的实际投放地判定；实际市场不在 `claim.markets` 内 = BLOCK。

## 2. Claim Gate（守衡主责）

每条对外宣称，是否能在类目 overlay 允许范围内被证据逐条支撑。

### 2.1 触发点

| # | 精确动作 | 状态迁移 |
|---|---|---|
| C1 | 脚本提交审批 | `script: draft → approved` |
| C2 | 素材入库校验 | `asset: ingested → validated`（带 `content_hash`） |
| C3 | 素材新增分发目标 | `distribution_targets` 追加 `paid`/`pdp`/`amazon_aplus`/`pr`/`ai_answer` |
| C4 | claim 或证据状态变更 | 引用该 claim 的 live 对象 24h 内批量重判（内部草稿、`retired`/`quarantined` 不触发） |

### 2.2 输入要件

| 字段 | 提供方 | 缺一件时的行为 |
|---|---|---|
| `claim_id@version` + `statement`、`claim_type`、`category`、`markets`、`allowed_channels[]` | Daisy | BLOCK；未声明 claim 不得进 paid；`markets` 缺 = 无 overlay 可判；`allowed_channels` 缺视为空集 |
| `evidence_refs[]` + `valid_until` + `scope_limits` | Daisy | 缺失 BLOCK；过期或不覆盖目标市场/使用条件 BLOCK |
| `claim_rule_binding{rule_id, rule_version, verdict}` + `market_overlay_version` | 守衡 | BLOCK：规则未绑定或 overlay 缺失 = 未判 |
| 画面/字幕/口播 claim 抽取结果与置信度 | 守衡抽取器 | 抽取失败或低置信 → 转人工 |
| `audience.segment_id`（是否含儿童向） | Emily / Radar | BLOCK：无法判披露义务 |

### 2.3 判定三态

| 态 | 判据 | 例 |
|---|---|---|
| PASS | 全部 `claim_refs` approved；证据第三方且在效期；`allowed_channels` ⊇ 目标渠道；实际市场 ⊆ `claim.markets`；无未声明 claim | `clm-bpc-us-0142@3`「含 18% 烟酰胺」+ SGS 报告，投 US organic + PDP |
| CONDITIONAL | 证据为第一方需补第三方；仅部分渠道或片段；overlay 给限时例外 | 同一 claim 用内部测试报告 → 「仅 organic，30 天内补第三方」，`valid_until` = 补证截止日 |
| BLOCK | 命中禁止；证据缺失/过期/不覆盖；claim 未 approved 或 superseded；medical 越界；儿童出镜未披露；他牌 logo / 未授权音乐；overlay 缺失；人工超 SLA | 脚本写「治疗湿疹」→ `rule-claim-cosmetic-medical-boundary-us-review@3` 命中，附原文第 12–14 行；只写「不合规」不构成回执 |

### 2.4 Fail-closed 默认行为表

| 情形 | 默认 | 解除条件 |
|---|---|---|
| 规则库无命中 / 抽取置信度低 | 转人工，不出 PASS；同时立 `rule_gap` | 人工出判定；同一 gap 连续 3 次必须补规则 |
| 规则服务不可用或系统故障 | BLOCK，不降级、不复用旧判定 | 服务恢复并出回执 |
| 证据缺失 / 过期 / retracted / disputed | BLOCK；引用该证据的 claim 全 `suspended`，下游 24h 重判 | 新版本证据 |
| 证据 scope 不覆盖市场或使用条件 | BLOCK，记 `scope_gap` | 补覆盖或降渠道/改宣称 |
| claim 未 approved 或引用旧版本 | BLOCK | 引用 `@current` |
| 同一 claim 两条冲突判定 / market overlay 缺失 | BLOCK，按 `evaluated_at` 取最新；不套用他国规则，未裁前不迁移 | 合规 owner 裁定 + 新回执 / overlay 发布 |
| 回执到期 / 人工超 SLA | BLOCK + 升级，不自动放行 | 重判出回执 |

### 2.5 输出与留痕

在 §0.4 上追加：`claim_verdicts[]`（逐 claim 判，不合并）、`extracted_claims[]`（未声明 claim 与时间码，空也写 `[]`）、`channel_matrix`（claim × 渠道允许矩阵）、`required_fix[]`（删哪句/换哪段/补哪份证据）。判定人以个人身份签名，不得签团队名；机器判定记模型版本与抽检人；回执与素材字节 SHA 同时入库。

### 2.6 推翻与回灌

1. 触发源：平台拒审/下架、法务或监管函、客诉、抽检、复盘、媒体或竞品指出；24h 内开单，原回执 `overturned`，新回执 `supersedes`。
2. 根因七选一：R1 规则缺失 / R2 规则错误 / R3 规则过期 / R4 证据问题 / R5 抽取漏检 / R6 人工误判 / R7 流程绕过。
3. 修复按根因定：R1 补规则；R2 规则版本 +1；R3 更新 overlay 并回扫；R4 退 Daisy 处置 evidence；R5 进抽取回归集；R6 判定人降权加抽检；R7 按 §7 立案。
4. 每条推翻至少 1 条负例 `{素材 SHA, 原判定, 正确判定, 根因, 规则版本}` 入回归库，30 天内回扫同规则历史判定；复发率 = 同根因同类误判 90 天内复发数 ÷ 该类判定总数，首年 ≤10%、次年 ≤5%。

### 2.7 SLA 与升级

| 场景 | 时限 | 升级对象 | 超时默认 |
|---|---|---|---|
| C1 单条脚本 / C2 单批素材（≤20 条）/ 规则未命中转人工 | 4 工作小时 / 24 小时 / 1 工作日 | 守衡负责人 → 合规 owner | BLOCK |
| 高风险（medical / 儿童 / 认证 / 召回） | 2 小时出首判 | 直接升级品牌负责人 | BLOCK |

升级只改处理顺序，不改判定标准；加急不减免任何要件。

### 2.8 度量

| 指标 | 公式 | 初始目标 |
|---|---|---|
| 漏检率 / 误杀率 | 事后推翻或外部处罚中本应阻断数 ÷ 应阻断总数；被推翻的 BLOCK ÷ BLOCK 总数 | ≤2%（P0 = 0）/ ≤10% |
| 判定时长 | `judged_at − request_at`，P50 / P95 | P50 ≤2h，P95 ≤24h |
| 回执可追溯率 | 判定人 + 规则版本 + 证据 SHA 齐全 ÷ 全部回执 | 100% |
| 覆盖率 / 到期未复审 | 有回执 ÷ 应判对象；`expired` 后仍在分发数 | 100% / 0 |

目标为初始值，落地 4 周后按实测基线重设。

## 3. 授权 Gate（Clone + Radar 维护台账，守衡核验）

这份字节能不能进 paid、能用在哪些账号、能用到何时、二次剪辑与跨账号复用是否分别被覆盖。台账写域：`asset_rights` 的唯一写入口是 Radar，字段为七元组 `(asset_id, creator_id, scope[], account_ids[], territory[], valid_to, doc_asset_id)`，另附 `credential_type` 枚举；Clone 只能追加 `asset_ref` 外键，不得修改任何授权字段；守衡只读并出判定。跨线台账不等于双写，因为只有一处 INSERT/UPDATE。

### 3.1 触发点

| # | 精确动作 | 状态迁移 |
|---|---|---|
| A1 | 素材进加热池前 | `distribution_targets` 追加 `tiktok_paid` / `meta_paid` |
| A2 | 变体出片入队 | `variant: rights_checking → ready` |
| A3 | 二次剪辑或跨账号复用 | 新 `asset_id` 或新增 `account_ids` 时重判，不得继承父素材判定 |
| A4 | 自有账号 organic 分发 | `asset: validated → distributed` 且目标含 organic（全自有可机器 PASS） |
| A5 | 授权到期或撤回 | `asset_rights.status` 变更 → 2h 内反查并置 `quarantined` |

### 3.2 输入要件

| 字段 | 提供方 | 缺一件时的行为 |
|---|---|---|
| `creator_id@version` + `asset_id` + `content_hash` | Radar / Clone | BLOCK；无 creator 的第三方素材不得进 paid |
| `scope[]` ∈ {organic, paid, reedit, cross_account} + `valid_to` | Radar | BLOCK；缺项不得推断；无到期日 = 无限期，不接受 |
| `account_ids[]` 逐账号枚举 | Radar | BLOCK；「全部账号」「品牌所有号」一律不接收 |
| `doc_asset_id`（书面凭证 + SHA）+ `credential_type` | Radar | 无凭证 BLOCK；类型不在白名单 = BLOCK，不转人工 |
| `territory[]` + 平台侧授权状态快照 | Radar / 守衡 | 缺 territory 按最严市场处理；平台查不到转人工，4h 未判 = BLOCK |

凭证白名单只有四类：店铺授权号、TTAM Spark Ads Video code、ACA、红人联盟授权。DM 截图、口头同意、达人微信确认、第三方转授权、agency 自述不构成凭证。

### 3.3 判定三态

| 态 | 判据 | 例 |
|---|---|---|
| PASS | 四类 `scope` 全覆盖或用例不涉及；账号含目标号；地域含目标市场；`valid_to ≥ flight_end + 7 天`；凭证白名单内且平台可查 | Spark Ads Video code，`scope=[paid]`，账号 `ttUS-A1B2`，有效期 2027-03-31，flight 结束 2027-02-28 |
| CONDITIONAL | 部分覆盖：只能原片直投；只在列明账号；到期早于 flight 结束；仅部分地域 | `scope=[paid]` 缺 `reedit` → 「原片直投，禁二次剪辑」，`rights_status=partial` |
| BLOCK | 无七元组；凭证类型不支持；账号不在清单；`scope` 不含 paid；已过期；creator 撤权或 blacklisted；排他期内；平台不可查且人工未判 | 达人 IG 帖子混剪后投流，仅聊天记录 → `rule-tiktok-shop-reedit-scope-us-review` 命中 |

三态与主键字典固定映射：PASS → `rights_status=cleared`，CONDITIONAL → `partial`，BLOCK → `blocked`。下游只读这三值。

### 3.4 Fail-closed 默认行为表

| 情形 | 默认 | 解除条件 |
|---|---|---|
| 台账无记录 / `scope` 缺失 / `valid_to` 缺失 / `territory` 不含目标市场 | BLOCK，不得推断为 organic 或 paid | Radar 补齐七元组或改投放地 |
| 凭证存在但平台查不到 | 转人工 ≤4h | 平台可查或补新凭证 |
| 凭证类型不在白名单 | BLOCK，不转人工 | 取得白名单内凭证 |
| `account_ids` 为空或写「全部」 | BLOCK | 逐账号枚举完成 |
| 到期日落在 flight 窗口内 | CONDITIONAL 限时至到期日，到期自动停投 | 续期或缩窗 |
| creator dormant / blacklisted | BLOCK，冻结全部关联 asset | 状态恢复 + 复核 |
| 已剪辑但无 `reedit` 授权 | BLOCK + asset 永久不得进 paid，补授权也须新 asset 重判 | 新授权 + 新素材 |
| 撤回传播超 2h / 超时未响应 | 全部关联对象 BLOCK + 事故立案 | 双签复盘并验证传播完成 |

### 3.5 输出与留痕

在 §0.4 上追加：`ledger_ref`（指向 `asset_rights` 行，回执不复制台账字段）、`credential_sha256`（凭证替换即视为新凭证）、`platform_check{checked_at, method, result}`（截图须带抽检人）、`account_matrix`（账号 × 用途）、`reedit_allowed` + `reedit_limits`、`auto_stop_at`（写入投放系统，不靠人记）。

### 3.6 推翻与回灌

1. 触发源：平台拒审或下架、达人投诉、撤权后发现漏挂、竞品举报、抽检；24h 内开单，原回执 `overturned`。
2. 根因：L1 台账缺失 / L2 凭证类型误判 / L3 `scope` 误读（把 paid 当 organic）/ L4 账号清单过期 / L5 到期未复审 / L6 撤回传播失败 / L7 剪辑越界。
3. 修复：L1 补台账约束；L2 更新白名单；L3 加机检谓词；L4 账号主表加有效期；L5 上线到期任务；L6 演练加监控；L7 加剪辑版本指纹。
4. 负例 `{素材 SHA, 授权类型, 误判点, 正确判定, 根因}`，每条推翻至少 1 条；30 天回扫同凭证类型的全部在用素材；复发率口径同 §2.6，授权类目标首年 ≤5%（凭证类型有限可穷举）。

### 3.7 SLA 与升级

| 场景 | 时限 | 升级对象 | 超时默认 |
|---|---|---|---|
| A1 / A2 标准素材（含平台可查性核验） | 4 工作小时 | 守衡负责人 → Radar 授权 owner → 法务 | BLOCK |
| 爆款加急（发布 48h 内放大） | 2 小时 | Radar → 业务负责人 | BLOCK |
| A5 撤回传播 / 到期复审 | 2 小时 / 到期前 30 天 | Radar + 守衡双签 | 全量 `quarantined` |

### 3.8 度量

| 指标 | 公式 | 初始目标 |
|---|---|---|
| 七元组完整率 / 无凭证进 paid 数 | 进 paid 且七元组齐全 ÷ 进 paid 总数；无 PASS/CONDITIONAL 仍投放数 | 100% / 0 |
| 撤回传播时长 | 撤权 → 全部关联对象 `quarantined` | P95 ≤2h |
| 到期未复审在用数 | `valid_to` 已过仍在投放的对象数 | 0 |
| 误杀率 / 漏检率 | 申诉推翻的 BLOCK ÷ BLOCK；平台拒审回溯本应阻断数 ÷ 应阻断数 | ≤5% / ≤1%（P0 = 0） |
| 混剪存量 | 无 `reedit` 授权仍被剪辑使用的 asset 数 | 0 |

## 4. 实验 Gate（PMO 主责）

这次测试有没有编号、有没有对照、样本量够不够、阈值是不是开测前就写死的。15–25 条素材自由组合的核心问题不是「测得多」，而是 α=0.05 下同批 20 次比较期望产生 1 个假阳性；这个 gate 的首要作用是把假爆款挡在放量之前。

### 4.1 触发点

| # | 精确动作 | 状态迁移 |
|---|---|---|
| X1 | 脚本立项 | `script: draft → approved` 前必须有 `hypothesis_id` |
| X2 | 批次开测 | `variant: ready → testing`（批次级） |
| X3 | 放量 | `variant: testing → scaling`，需结果回执 |
| X4 | 页面 / 定价实验 | `pdp@{version}` 上线或 `price_change` 生效前 |
| X5 | 中途变更 | 阈值/样本/对照组任一变更 → 原批次作废，新批次新编号 |

### 4.2 输入要件

| 字段 | 提供方 | 缺一件时的行为 |
|---|---|---|
| `hypothesis_id` `hyp-{yyMMdd}-{seq3}` | PMO 编号池 | BLOCK：无编号不进测试 |
| 假设陈述（「若 X 则 Y」，可证伪） | Emily / Paid Media / Shopify | BLOCK |
| `primary_metric` + `metric_dict@version` + baseline + 窗口 + MDE + `sample_size` | PMO / 数据 | BLOCK；口径版本缺失不得开测；样本按 baseline、MDE、power 计算 |
| `test_thresholds{metric, min, window_days}` 冻结 | 提议方 + PMO 签 | BLOCK |
| `control_variant_id` / holdout / 前后对照窗口 + `stop_rules` + `budget_cap`（paid） | 执行方 + PMO | BLOCK；无对照且无例外登记不得开测 |
| `changed_variable` 单值 + `correction_method` | Clone / PMO | BLOCK；多值不可归因；15 条以上同批必填校正 |

`hypothesis_id` 由 PMO 分配、Emily 在 `script` 上引用；`script_id` 仍只有 Emily 能写，PMO 只发号不碰脚本本体。这是「实验 gate 归 PMO」与「script 单写入口」不冲突的唯一解法。

### 4.3 判定三态

| 态 | 判据 | 例 |
|---|---|---|
| PASS | 预注册齐备、样本达标、对照有效、阈值未变、结论按阈值三分且附样本量与检验方法 | `hyp-261101-012`：CTR baseline 1.2%，MDE 0.3pp，6 臂 Bonferroni，7 天窗口，结论「v04 +0.4pp，显著」 |
| CONDITIONAL | 样本未达只能「待定」；前后对照只能作方向性；窗口内有外部事件；学习期样本被剔除 | 样本达 62% 但方向一致 → 「待定，不得放量」 |
| BLOCK | 无编号；阈值事后改；无对照；同时改 ≥2 个变量；样本 < 预注册；未声明多重比较；窗口未满即判；结果外推 | 一批 15 条各改 2 个变量 → BLOCK，该批不可归因 |

### 4.4 Fail-closed 默认行为表

| 情形 | 默认 | 解除条件 |
|---|---|---|
| 无 `hypothesis_id` | BLOCK，不得进 testing | PMO 发号并登记 |
| 阈值未预注册 / 开测后修改 | BLOCK；改过即批次作废，原结果不得引用 | 重新登记 |
| 无对照组且无例外登记 / 同变体改多变量 | BLOCK；前者例外须写明代价与限域，后者标 `unattributable` 不得进入任何结论 | 补对照或登记例外 / 拆成单变量新变体 |
| 样本量不足 | CONDITIONAL 只能「待定」；要放量 → BLOCK。降级只允许按指标字典 §10.2 的三条合法路径重做预注册，不得降低 α 或事后改 MDE | 补样本 |
| 口径版本缺失或冲突 | BLOCK | PMO 发布口径 |
| 结果窗口未满 / 数据断流 | BLOCK，缺失段不计入样本 | 窗口结束或数据补齐 |
| 多重比较未处理 | BLOCK（放量方向），允许出「待定」 | 声明校正方法并复算 |

### 4.5 输出与留痕

在 §0.4 上追加：`batch_id` + `variant_id[]`（一批一条结果回执）、`thresholds_frozen_sha`（开测后哈希不一致即作废）、`sample_actual / sample_target`（分臂）、`correction_method` + 原始 α、`result`（scale / hold / kill / inconclusive，与 gate 三态分开记）、`scope_limits`（市场、类目、账号、时间窗，外推即失效）、`decision_by`（绑 `ad_id` 或 `pdp@version`）。回执默认有效期 90 天，逾期须复测或重新登记。

### 4.6 推翻与回灌

1. 触发源：复现失败、样本污染、口径变更、外部事件、多重比较未校正、数据错误；24h 内开单，引用该结论的放量决策同时挂复核标记。
2. 根因：E1 编号缺失或事后补 / E2 阈值改动 / E3 样本污染 / E4 口径漂移 / E5 多重比较 / E6 外推越界。
3. 修复：E1 状态机守卫；E2 阈值哈希校验；E3 样本洁净度检查；E4 口径版本化；E5 强制校正声明；E6 写死 `scope_limits`。
4. 负例 `{hypothesis_id, 原结论, 复现结果, 根因}` 每条至少 1 条入实验回归集；30 天内用新口径复算同批次历史结论并公示偏差；复发率口径同 §2.6，实验类目标 ≤5%。

### 4.7 SLA 与升级

| 场景 | 时限 | 升级对象 | 超时默认 |
|---|---|---|---|
| X1 发号与预注册 | 4 工作小时 | PMO → 段 A | 脚本不得 approved |
| X2 批次开测 | 提交后 1 工作日，且不晚于上线前 24h | PMO → 段 A | 不得开测 |
| X3 / X4 结果判定（X5 变更即时作废原批次） | 窗口结束 3 工作日 | PMO → 段 A → 业务负责人 | 不得放量 |

### 4.8 度量

| 指标 | 公式 | 初始目标 |
|---|---|---|
| 预注册覆盖率 | 完整预注册批次 ÷ 全部批次 | 100% |
| 无编号开测数 | 无 `hypothesis_id` 进入 testing 的批次 | 0 |
| 阈值冻结一致率 / 放量与阈值一致率 | 开测后阈值哈希未变的批次 ÷ 全部；按预注册阈值放量 ÷ 全部放量决策 | 100% / 100% |
| 结论可复算率 | 复算一致 ÷ 复算批次 | ≥95% |
| 无效实验率 / 重复试错率 / 外推越界数 | inconclusive ÷ 全部；90 天内同假设重登 ÷ 全部；超 `scope_limits` 使用次数 | 季度下降 / ≤5% / 0 |

## 5. A. 三个 gate 的顺序与依赖

### 5.1 文字流程图

```text
script.draft ─[E1 预注册 · PMO]─┐
             ─[C1 Claim · 守衡]─┴→ script.approved
                                        │
        Clone 出片 → variant.rights_checking → asset.ingested
                                        │
        ┌──────────────┴──────────────┐
        ▼                             ▼
[C2 Claim · 守衡]            [A1 授权 · 守衡核验]
        │                             │
  asset.validated        variant.rights_checking → ready
        └──────────────┬──────────────┘
                       ▼
     [E2 批次开测 · PMO（需 C2 + A1 回执号）] → variant.testing
                       ▼
  ad_id 创建 → 开投 → [E3 结果判定] → scaling / killed → [A2 到期复审/撤回]
```

### 5.2 能不能并行

| 关系 | 判定 | 依据 |
|---|---|---|
| C1 与 E1、C2 与 A1 | 并行 | claim 判内容，授权判字节与账号，E1 判「测什么、怎么判」；字段不重叠，互不为输入 |
| E2 与 C2 / A1 | 串行，E2 最后 | E2 回执须把 C2 与 A1 回执号写进 `evidence_refs`，缺一不接单 |
| E3 与 A2 | 并行 | 测试期跨授权到期时 A2 续期，E3 不等待；A2 转 BLOCK 则该批标 `rights_tainted` |
| 三 gate 与开投 | 串行 | `ad_id` 创建是全链最后动作，三回执齐全才允许 |

### 5.3 一个 gate 阻断后，其他 gate 跑不跑

跑，但回执不生效。

1. 任一 BLOCK：对象停原状态；同主体其他 gate 继续受理并出回执，避免修一处重排三轮。
2. 其他 gate 的回执标 `inactive`，不得用于放行，也不得作为 CONDITIONAL 的条件。
3. 修复后只重跑被推翻的那个 gate，其余按 §0.4 复用。
4. 修复改变 `content_hash`（重导片、删片段、换字幕层）：全部回执 `superseded` 重跑；只改 `claim.statement` 时 C 与 A 可保留，E 若引用旧 claim 则失效——因果对象变了。
5. 禁止用「另一个 gate 已过」抵消当前 BLOCK；禁止用「授权不全所以先投 organic」降级放行，除非 organic 单独过 A4。

死锁只有两条路解：补齐要件，或撤回对象（`retired`）。授权谈不下来、规则补不上时，正确结果是对象不进入下一状态，不是由下游 gate 出 CONDITIONAL 放行；不存在「临时豁免」。

## 6. B. 现状与目标差距、落地步骤

### 6.1 差距性质

| Gate | 现状 | 差距性质 |
|---|---|---|
| Claim | 有雏形（守衡投前放行 + claim 三源），但规则未命中默认放行；无回执、无规则版本绑定、无负例库、无 SLA、无度量（补全稿 §2.10，BP-02） | 有流程、无强制 |
| 授权 | 不存在。只有 Radar 档案与人工清单，`asset_rights` 七元组无载体；混剪绕过授权被当成「省钱」（补全稿 §2.2，BP-11） | 从 0 到 1 |
| 实验 | 不存在。15–25 条自由组合，无编号、无对照、无预注册、无多重比较，阈值复盘时才讨论（variant 字段） | 从 0 到 1 |

### 6.2 Step 0：状态机接入（共同前置）

| 动作 | 完成标志 |
|---|---|
| 对 C1/C2、A1/A2、X1/X2/X3 加守卫，拒绝时留拒绝记录 | 六处「无回执强行迁移」成功次数 = 0；拒绝记录可导出 |
| 移除人工改状态接口，或改为双签 + 原因 | 人工改状态逐条可查，均有原因与双签 |

### 6.3 Claim Gate 落地

| 步 | 动作 | 完成标志 |
|---|---|---|
| 1 | 改默认值：未命中 → `manual_required` | 20 条未命中样本 PASS = 0、MANUAL = 20，且 100% 生成 `rule_gap` |
| 2 | 规则对象化：引用 `rule_id@rule_version` + 原文段落 | 抽 30 条回执，规则引用齐全率 100%，无「凭经验」判定 |
| 3 | 回执落库 + C1/C2 状态机守卫（§0.4 + §2.5） | 判定人 / 规则版本 / 证据 SHA 齐全率 100%；无回执进入 `approved` / `validated` 成功次数 = 0 |
| 4 | 负例库与回灌 | 首例推翻 5 工作日内 `rule_version+1`；回归集含该负例；30 天回扫完成率 100% |
| 5 | market overlay（US / EU）+ 度量上线 | 同一 claim 两地判定不同且各带 overlay 版本；overlay 缺失 100% BLOCK；连续 4 周四项度量有数 |

### 6.4 授权 Gate 落地

| 步 | 动作 | 完成标志 |
|---|---|---|
| 1 | `asset_rights` 七元组落表 + 凭证白名单、四类 `scope` 分列 | 新进 paid 素材完整率 100%；非白名单凭证 100% BLOCK；「全部账号」表述 = 0 |
| 2 | A1/A2 状态机守卫 | 无 `cleared` 进 paid / `variant.ready` 成功次数 = 0 |
| 3 | 平台侧授权状态核验 | 凭证平台可查率 ≥95%；不可查 100% 转人工且 4h 内出判定 |
| 4 | 撤回传播演练 | 撤权后 2h 内清单完整率 100%，留演练记录 |
| 5 | 到期复审 + 混剪存量清理 | 到期前 30 天复审完成率 100%；无 `reedit` 授权已剪辑 asset 全 `quarantined`，再进 paid = 0 |

### 6.5 实验 Gate 落地

| 步 | 动作 | 完成标志 |
|---|---|---|
| 1 | 编号池 + 预注册模板、单变量 + 对照强制 | 新 `script` 100% 带 `hyp-` 编号；批次内单变量比例 100%（对照除外）；无编号 `approved` = 0 |
| 2 | X2 批次开测守卫 + 阈值冻结（登记时算哈希） | 无实验回执进入 `testing` = 0；中途改阈值 = 0，出现即批次作废留档 |
| 3 | 多重比较 + 结果判定与回写 | 批次登记 100% 含 `correction_method`；窗口结束 3 工作日内判定率 100%；放量与预注册阈值一致率 100% |

### 6.6 落地节奏

| 周 | 交付 | 影子期 | 阻断生效（日期条件之一） |
|---|---|---|---|
| W0–W1 | Step 0 状态机；实验编号池 | — | — |
| W1–W4 | Claim gate 全部 5 步 | W1–W4 | W5 起 |
| W5–W8 | 授权 gate 全部 5 步 | W5–W8 | W9 起 |
| W9–W12 | 实验 gate 批次守卫与结果判定 | W9–W12 | W13 起 |

> **阻断生效 = 日期条件 AND 覆盖率条件，两者同时满足才生效。**
> - Claim Gate：生效需同时满足「US/EU overlay 已发布」且「在产 SKU 的 claim 类目 base rule 覆盖率 ≥80%」。覆盖率公式与口径见 §6.7；未达标时按类目白名单逐类放开：每类连续 2 周、20 条抽检 PASS 率 ≥70%，纳入下一类。
> - 授权 Gate：生效需同时满足「凭证白名单四类已落地」且「平台侧可查率 ≥80%」。可查率公式与 L1/L2/L3 三档可查定义见 §6.7；未达标时只阻断「无任何凭证」一类，凭证存在但不可查的走人工 4h。
> - 实验 Gate：生效需同时满足「编号池与预注册模板上线」且「预注册核算达标率 ≥90% 且平均样本量核算时长 ≤2 工作日」。公式与口径见 §6.7；未达标时只要求 `hypothesis_id`，不阻断样本量。
> - 未覆盖对象在阻断期内一律走「人工判定 + 24h SLA + BLOCK 落 `rule_gap`」，不得静默放行。
> - 熔断：任一 gate 连续 5 个工作日人工队列 >50 条，或 SLA 违约率 >30%，自动暂停该 gate 的阻断资格 4 周并上报业务负责人，记 `rule_gap_burst`；已在影子期的 gate 只暂停「进入阻断期」的评估，影子判定与 BLOCK 记录照常。熔断不重置、不顺延复评计时（复评仍按每 4 周固定节拍），但每次熔断必须在 4 周内把覆盖率提升 ≥10pp；未提升的，第 4 周末直接进入下一次复评，不得以「刚熔断过」为由推迟。
> - 影子期上限为 3 次复评（每 4 周一次）；第 3 次仍不达覆盖率门槛，该 gate 转为人工 gate（§6.8）：机器判定停用，改由固定人工 owner 按同一判定表出回执，**BLOCK 照常阻断状态机**。人工 gate 不设退出期限；任一复评时点覆盖率达标的，下一个复评时点恢复机器判定，不设特批通道。

影子期不是放行：判定照出、BLOCK 照记，只不阻断状态机；对象进「已知敞口登记表」（对象 ID、gate、影子判定、敞口类型、段 A 签字、到期日、处置动作），每月进 PMO 月会，不得作为下游依据、不计入覆盖率分母。影子期退出按上述覆盖率条件判定，不按个案审批，也不按日历自动转阻断。

### 6.7 覆盖率门槛的可计算口径

三个门槛的分子、分母、抽取口径固定如下；口径变更走规则变更流程（§7.3），不得在复算时临时调整。

**分母为 0 时的统一规则（三门槛共用，防止除零与「假达标」）**

分母为 0 时覆盖率不写成 0% 也不写成 100%，一律记 `NOT_APPLICABLE`，并按下列规则处理：

- **阻断资格**：`NOT_APPLICABLE` 不构成达标，gate 保持未生效（不阻断）。理由：没有可判对象时，覆盖率无法证明规则库已具备阻断能力。
- **不触发熔断**：分母为 0 不计入人工队列长度与 SLA 违约率统计，避免「无业务即无告警」被误读为健康。
- **三门槛各自的 0 分母判定**：Claim Gate＝当期无在产 SKU；授权 Gate＝当期无 asset 进入 paid；实验 Gate＝当期无预注册提交。
- **恢复条件**：分母由 0 变为非 0 的当周即重新复算，并作为该 gate 的首次达标判定点，不得沿用此前的 `NOT_APPLICABLE` 状态。
- **留痕**：`NOT_APPLICABLE` 须写入 `metric_snapshot`，并在 PMO 月会记录「本期无可判对象」及原因，不得静默略过。

**Claim Gate｜claim 类目 base rule 覆盖率 ≥80%**

- 分子：在产 SKU 实际使用、且同时存在「已发布 base rule」与「已发布 market overlay」的 claim 类目数。
- 分母：在产 SKU 实际使用的 claim 类目总数。
- claim 类目 = (`category`, `claim_type`) 唯一组合；一个类目有规则即覆盖该类目下全部 claim。
- 抽取口径：按 claim 类目去重计数，不按 claim 条数、不按 SKU 计——按条数计会让高频 claim 稀释覆盖率，按 SKU 计会让单 SKU 多类目被重复计入。在产 = SKU `status=live` 且 `distribution_targets` 含对外渠道；内部草稿与 `retired`/`quarantined` 不进分母。
- 数据源：`claim` 表（Daisy，`claim_type` + `category` + 在产 SKU 关联）、`rule_object`（`status=published`）、`market_overlay`（`status=published`）。

**授权 Gate｜平台侧可查率 ≥80%**

- 分子：分母样本中 `platform_check.result=verified` 的 asset 数（含 L1 与 L2 两档）。
- 分母：当期进入 paid 的 asset 总数；全量计算，超过 500 时按月分层抽样 500（层 = 四类凭证，层内按 asset 数等比例）。
- 可查三档：L1 平台 API 可验（自动 PASS）；L2 平台后台可见但需人工截图 + 抽检（记 `verified_manual`）；L3 仅凭证照片、平台无记录（记 `unverifiable`）。分子只含 L1 + L2。L3 的处置按 gate 模式分叉，不得混用：**阻断模式**（覆盖率已达标）下直接 BLOCK；**人工模式**（覆盖率未达标，见 §6.6）下走人工判定 4h，人工确认真实即记 `verified_manual`，否则 BLOCK。
- 抽取口径：按 asset 计，一个 asset 一次计数；同一 asset 覆盖多账号不重复计数。
- 数据源：`asset_rights`（`credential_type`、`doc_asset_id`）、守衡 `platform_check{checked_at, method, result}`。

**实验 Gate｜预注册核算达标率 ≥90% 且平均样本量核算时长 ≤2 工作日**

- 分子：T 周内完成且 `sample_size` 非空的预注册批次数。
- 分母：T 周内提交的预注册批次数（以脚本申请 `approved` 前的预注册请求为准）。
- 平均核算时长 = Σ(`prereg_done_at − prereg_request_at`) ÷ 完成批次数，按 PMO 工作日历计工作日。
- 抽取口径：按批次计；T 周为自然周（周一 00:00–周日 24:00）。两个条件同时满足才算达标，缺一即未达标——只看达标率不看时长，会把「全部拖延但全部完成」判为达标。
- 数据源：PMO 预注册记录（`hypothesis_id`、提交/完成时间戳、`sample_size`、baseline/MDE/power 输入）。

| 门槛名 | 公式 | 数据源 | owner | 复算频率 | 未达标时的行为 |
|---|---|---|---|---|---|
| Claim Gate 覆盖率 | 已覆盖 claim 类目数 ÷ 在产 SKU 的 claim 类目总数 | `claim` + `rule_object` + `market_overlay` | 合规 owner（规则发布）/ 守衡负责人（统计与复算） | 每周一 09:00 自动复算；`rule_object` 发布后 24h 内重算 | 按类目白名单逐类放开：每类连续 2 周、20 条抽检 PASS 率 ≥70% 纳入下一类；未纳入类目走人工判定 + 24h SLA + BLOCK 落 `rule_gap` |
| 授权 Gate 平台侧可查率 | `platform_check=verified` 的 asset 数（L1+L2）÷ 当期进 paid 的 asset 数 | `asset_rights` + `platform_check` | Radar 授权 owner（凭证与平台快照）/ 守衡负责人（复算） | 每周抽样复核；每月首个工作日全量复算 | 只阻断「无任何凭证」一类；凭证存在但不可查（L3）走人工 4h |
| 实验 Gate 预注册核算达标率 | 完成且含 `sample_size` 的预注册批次数 ÷ 提交的预注册批次数 ≥90%，且平均核算时长 ≤2 工作日 | PMO 预注册记录 | PMO | 每周一 09:00 | 只要求 `hypothesis_id`，不阻断样本量 |

### 6.8 人工 gate：定义与可观测标志

机器判定被停用后，gate 不取消判定，只换判定人。

| 项 | 定义 |
|---|---|
| 判定方式 | 固定人工 owner 按同一判定表逐条出回执（§0.4、§2.3 / §3.3 / §4.3 的判据不变）；不新增要件、不改判据、不设「临时豁免」。双签：Claim = 守衡负责人 + 合规 owner；授权 = Radar 授权 owner + 法务；实验 = PMO + 段 A |
| 是否阻断 | **阻断。** 人工回执仍是状态迁移的必要条件，BLOCK 照常拒绝迁移。若人工 gate 不出 BLOCK，「降级」等于制度在 3 次复评后自动失效，人工 gate 会变成事实上的放行通道 |
| 是否计入阻断统计 | 计入。人工 gate 的 BLOCK 进该 gate 的漏检率 / 误杀率与 `rule_gap` 台账，月报单列「人工 gate BLOCK 数」及其按对象类型的分布 |
| 由谁承担 | 判定人个人签名（§2.5）；误判按 §2.6 / §3.6 / §4.6 的根因流程追责；PMO 月会复盘 |
| SLA | 单条 2 工作日；人工队列与 SLA 违约率的熔断阈值同 §6.6，不另设 |
| 区别于影子期 | 影子期：判定照出、BLOCK 记为影子判定、**不阻断**、可进「已知敞口登记表」后放行；人工 gate：BLOCK **阻断**、不得进敞口登记表、无任何放行例外 |

可观测标志：人工 gate 的回执写 `judged_by.type=human_gate`；影子期回执保留原 `judged_by.type`，进入影子期的事实以该对象出现在「已知敞口登记表」为准。月报按判定人类型分列「判定数 / BLOCK 数 / 实际阻断数」三列，BLOCK 数 ≠ 实际阻断数且对象不在敞口登记表内，即为绕过（§7.2）。

## 7. C. 谁有权绕过 Gate

**结论：无人有权绕过。** 不存在加急通道、老板特批、会议决议、法律顾问口头意见、事后补签、agent 代传；任何「这次先放、回头补」按绕过处理。

### 7.1 三类不属于绕过的动作与不存在的通道

| 动作 | 为什么不算 | 约束 |
|---|---|---|
| 撤回类：停投、下架、删帖、`quarantined`、关账户 | gate 只管「放出去」，不管「收回来」 | 2h 内记录原因与执行人 |
| 法务或监管强制动作 | 外部权威源要求，品牌无裁量权 | 可先执行后补记录（≤24h），不得用于发布方向 |
| 机器判定替代人工 | 加速判定，不是跳过判定 | 仍出回执、仍受抽检（抽检率不得为 0）、仍可推翻 |

明确不存在的通道：加急审批 / 老板口头 / 会议决议 / 法务邮件「原则上可以」/ 事后补签 / 拆单 / 换账号 / paid 伪装 organic / 交 agency 用其账户代传 / 改文件名重传 / 手工把 BLOCK 改 CONDITIONAL / 给某条素材临时豁免规则。

### 7.2 反绕过检测

| 绕过方式 | 检测手段 | 后果 |
|---|---|---|
| 拆单规避 | 按 `content_hash` 相似度与上传批次聚类，同源 ≥3 片段无回执即命中 | 全部片段 `quarantined`，该批不得再进 paid |
| 换账号发布 / paid 伪装 organic | `creator_id` + 素材指纹跨账号比对；平台推广标识与 `distribution_targets` 比对 | 违规账号冻结投放权限 90 天；补判不洗白，事件立案 |
| 绕过系统直传平台后台 | `publish_record` 与平台发布记录对账 | 差异即立案；责任人当季考核不合格 |
| 事后补签回执 | 回执 `judged_at` 晚于 `published_at` | 回执作废，按无回执处理 |
| 改规则让某条通过 | 变更单引用具体 `subject_id` 即命中 | 驳回；发起人 90 天内无规则变更权 |
| 把 BLOCK 改 CONDITIONAL 冲误杀率 | 两率联看，误杀降而漏检升即审计；`CONDITIONAL→BLOCK` 到期转化率单列 | 审计不过则 gate 权限收回，PMO 代管 90 天 |

### 7.3 规则变更也是绕过路径

改规则使某条素材通过，等同绕过。约束：①变更单不得引用任何 `subject_id`，引用即驳回；②必须带理由、影响面、回扫计划，`rule_version+1` 后 30 天内回扫在用对象；③审批人固定——claim 规则 = 合规 owner + 守衡负责人，授权白名单 = Radar + 法务，实验协议 = PMO + 段 A；④不得追溯修改历史回执，历史判定只标「按新规则应判 X」。

## 8. 未核验与风险

**推断项**

- 全部 `rule-*` / `overlay-*` 编码为提案，知识库中无同名 canonical 对象；库内 TikTok Shop 与独立站规则类文件为 0（补全稿 §6），Claim Gate 上线首月将大面积 BLOCK。
- TikTok Shop 四类凭证的实际字段、有效期语义、能否跨账号、ACA 的准确覆盖范围未对平台后台核验；本稿按「四类互不覆盖、逐类判定」设计，若实际存在合并覆盖，判定表需收窄。
- 平台是否提供授权状态查询接口未知；若无，「平台可查率 ≥95%」不可达，只能降为人工截图 + 抽检，SLA 与漏检率目标同步上调。`valid_to ≥ flight_end + 7 天`、各处 SLA、样本量公式参数均为推演值，非实测；各产线真实系统未读，六个迁移点是否存在于现有工作台未知。

**需真实系统数据才能确认**

- 现有 claim 总量、重复率、证据覆盖率；素材月产量与进 paid 比例；历史拒审率与原因分布。
- 授权台账现有条目数、已过期条目数、无 `reedit` 授权的剪辑素材存量；每月测试批次数、单批变体数、当前判定人力与工时——人力决定 SLA 是否可达。

**风险**

1. **规则库空洞导致全面阻断、影子期变永久敞口。** 前者是风险首次可见，不是设计缺陷，解法是分批补规则 + 覆盖率门槛而非改回放行；后者靠覆盖率封口不靠审批，覆盖率不达标不得进入阻断，第 3 次复评仍不达门槛即转为人工 gate（§6.8；人工 gate 仍出 BLOCK、仍阻断，只改判定人），不得以日历到期为由强行阻断，也不得把人工 gate 读成放行。规则与 overlay 未发布前，Claim Gate 不具备阻断资格，只能按 §6.6 的分阶段放开规则进入人工队列。
2. **Gate 变橡皮章。** PASS 率 >95% 且平均判定时长 <1 分钟同时出现即触发审计；把 BLOCK 改 CONDITIONAL 可降误杀率、同时抬漏检率，两率必须联看。
3. **授权 gate 单点依赖 Radar。** Clone 可写 asset 侧但不得代写 `scope`；台账缺失即 BLOCK，不允许下游代填。
4. **实验 gate 与投放实操冲突。** 学习期花费不构成有效样本，窗口须从学习期结束起算；测试周期拉长 3–7 天，必须接受，否则归因永不成立。
5. **多重比较是假爆款主因。** 同批 15–25 条在 α=0.05 下期望 1 个假阳性；不校正就会稳定产出「可放量」的错误结论。
6. **Gate 管不到对方账号。** 达人、agency 在自己账号发布时，品牌只能约束「品牌可用素材」；靠合同与事后监测，不在 gate 能力范围内，不能宣称已被治理覆盖。
