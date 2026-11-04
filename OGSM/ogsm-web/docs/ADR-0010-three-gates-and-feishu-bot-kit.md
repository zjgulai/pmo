# ADR-0010：P0-4 三道 Gate 状态机守卫回执引擎与 P0-2 14 专家飞书 Bot 标准脚手架

- **状态**：已批准（Approved）
- **日期**：2026-11-04
- **决策人**：周健（PMO 总控 & 全栈研发）
- **适用范围**：`OGSM/ogsm-web/app/gate_engine.py`、`OGSM/ogsm-web/app/abi_feishu_agent_kit.py`、`OGSM/ogsm-web/app/models.py`、`OGSM/ogsm-web/app/main.py`、`OGSM/ogsm-web/app/feishu_bot.py`（严格遵守零网站污染约束，不修改任何前端 HTML 模板）

---

## 1. 背景与目标（Context）

依据《品牌 Agent 三个 Gate 规格与 Fail-closed 默认》与《主键字典》，全组织需要把两项关键工程底座从文档落地为可调用、可机器校验的生产代码：
1. **P0-4 三道 Gate 状态机守卫回执引擎（Claim Gate `C` / 授权 Gate `A` / 实验 Gate `X`）**：
   - Gate 是状态机守卫，不是评审会；输出唯一确定性定位串 `{subject_id}@{version}#{gate}-{seq4}`（例如 `scr-bpc-tiktok-00317@2#C-0001`）。
   - 严格执行五条铁律：规则未命中≠允许；证据缺失≠待补；超时未响应≠放行；无回执≠通过；回执过期 = `BLOCK`。
2. **P0-2 14 专家飞书 Bot 标准脚手架（`abi_feishu_agent_kit.py`）**：
   - 为 Wave 1–3 共 14 个独立飞书专家应用提供统一的「WS 长连接 + Webhook 双通道 + 幂等防重 + 自动向 PMO 上报高频提问（`ask+1`）/ 打回（`reject+1`）/ 业务回写（`measured_action`）+ 前置 Gate 回执强校验」单文件 SDK。

---

## 2. 核心设计规格（Specifications）

### 2.1 P0-4 三道 Gate 守卫引擎（`app/gate_engine.py` & `models.GateReceipt`）

1. **数据模型 `GateReceipt`（子记录表 `gate_receipt`）**：
   - `receipt_id`（唯一索引）：严格遵循 `{subject_id}@{version}#{gate}-{seq4}` 正则 `^[a-z0-9][a-z0-9_-]*@\d+#[CAX]-\d{4}$`，禁止裸写 `#C-41` 或省略 `@version`。
   - `subject_id`、`subject_version`、`gate_type`（`C` Claim / `A` 授权 / `X` 实验）、`seq4`（按 `subject_id + gate_type` 独立 4 位补零递增）。
   - `verdict`：`PASS` / `CONDITIONAL` / `BLOCK`。
   - 五项强制绑定指纹（任一变更即 `superseded`）：`content_hash`、`claim_refs_json`、`rule_refs_json`、`market_overlay_version`、`evidence_refs_json`。
   - 生命周期字段：`conditions_json`、`valid_until`（ISO 日期，到期自动视为 `expired` = `BLOCK`）、`invalidate_on_json`（不允许为空）、`judged_by`、`status`（`active` / `superseded` / `overturned` / `expired`）。

2. **三道 Gate 的 Fail-closed 机器判据**：
   - **Claim Gate (`C`，守衡主责)**：
     - 校验 `claim_refs`、`evidence_refs`、`rule_refs`、`market_overlay_version` 非空；
     - 扫描高危红线词（如无器械资质的 medical 越界词 `治疗/治愈/100%杀菌/完全静音`、儿童出镜未披露、缺欧盟 `overlay-eu-gpsr`）→ 命中或少要件直接判 `BLOCK`；第一方证据限时 30 天判 `CONDITIONAL`；第三方有效证据齐全判 `PASS`。
   - **授权 Gate (`A`，Radar 台账 + 守衡核验)**：
     - 校验授权七元组 `(asset_id, creator_id, scope[], account_ids[], territory[], valid_to, credential_type)`；
     - 凭证类型白名单仅认 4 类：`shop_official`（店铺授权号）、`ttam_spark_code`（TTAM Spark Ads Video code）、`aca`（ACA）、`affiliate_auth`（红人联盟授权）；非白名单（如 DM 截图/口头同意）或 `account_ids` 写 `"all"/"全部"` 一律 `BLOCK`；
     - 若 `is_reedit=True`（二次剪辑）但 `scope` 不含 `"reedit"`，严格按 `rule-tiktok-shop-reedit-scope-us` 判 `BLOCK`。
   - **实验 Gate (`X`，PMO 主责)**：
     - 预注册发号 `POST /api/gate/hypothesis` 生成 `hyp-{yyMMdd}-{seq3}` 并计算 `thresholds_frozen_sha`；
     - 校验 `hypothesis_id` 格式、`changed_variable` 单值（同时改 ≥2 个变量不可归因 → `BLOCK`）、对照组 `control_variant_id` 非空、同批 `arm_count > 5` 时强制要求 `correction_method`（如 `bonferroni` / `bh_fdr`）。

3. **对外 API 与飞书指令（零网站 UI 变更）**：
   - `POST /api/gate/evaluate`：提交 `C` / `A` / `X` 门禁评估并签发不可篡改的 `GateReceipt`；
   - `GET /api/gate/verify/{receipt_id}`（或 `POST /api/gate/verify`）：下游 Agent（Clone / Shopify / Paid Media）在发布或投流前校验回执是否 `active`、未过期且五项指纹未变；
   - `POST /api/gate/hypothesis`：PMO 实验预注册发号器（`hyp-{yyMMdd}-{seq3}`）；
   - 飞书群指令：`@PMO 查回执 <receipt_id>`、`@PMO 发号 <实验假设陈述>`、`@PMO 门禁`。

### 2.2 P0-2 标准飞书专家 Bot 脚手架（`app/abi_feishu_agent_kit.py`）

- 内置全部 14 个专家 Agent 的标准配置注册表 `EXPERT_BOT_REGISTRY`（含 `slug`、名称、工作台 URL、所属 Wave、环境变量名 `FEISHU_<SLUG>_APP_ID`、默认三张标准交互卡片模板：查询诊断卡 / DRAFT 审批与打回卡 / 任务认领回写卡）。
- 提供 `ABIFeishuAgentBot` 基类：
  1. **自动遥测上报（Auto Telemetry）**：群成员每次 `@專家Bot` 提问自动调用 PMO `/api/sop/telemetry` (`event_type="ask"`)；点卡片「打回修改」自动上报 `event_type="reject"`；点「认领执行/批准发布」自动上报 `event_type="measured_action"`；
  2. **前置 Gate 守卫装饰器 `@require_gate_receipt(gate="C")`'**：任何生成投放脚本、二创视频或 Shopify DRAFT 的动作，未传入有效 `PASS/CONDITIONAL` 回执一律在 SDK 层自动拦截并返回合规阻断卡片。
