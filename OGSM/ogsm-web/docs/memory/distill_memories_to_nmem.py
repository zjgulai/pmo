#!/usr/bin/env python3
"""PMO 记忆批量蒸馏脚本（依据 SOP 四层记忆标准）。

用法：
    # 干跑：只打印 46 张卡与长度，不写 nmem
    OGSM/ogsm-web/.venv/bin/python OGSM/ogsm-web/docs/memory/distill_memories_to_nmem.py

    # 执行：逐条 upsert 到 abi-pmo
    OGSM/ogsm-web/.venv/bin/python OGSM/ogsm-web/docs/memory/distill_memories_to_nmem.py --run

设计：
- 全部用稳定 id + `nmem memories add --id` 实现幂等 upsert。
- 14 张项目画像从 seed.py 的 PROJECTS/CAPABILITIES 生成，保证数字可回算。
- L1/L2/L3 与 5 张聚合卡为手工蒸馏，来源已写进正文。
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]          # /Users/lute/Project/PMO
WEB = Path(__file__).resolve().parents[2]           # /Users/lute/Project/PMO/OGSM/ogsm-web
sys.path.insert(0, str(WEB))

from app import seed  # noqa: E402

SPACE = "abi-pmo"
NMEM = "nmem"
AS_OF = "2026-11-04"

MEMORIES: list[dict] = []


def add(mid: str, layer: str, title: str, importance: float, unit_type: str,
        when: str, labels: str, content: str) -> None:
    MEMORIES.append(dict(id=mid, layer=layer, title=title, importance=importance,
                         unit_type=unit_type, when=when, labels=labels,
                         content=content.strip()))


# ─────────────────────────── L1 核心准则 ───────────────────────────
add(
    "pmo-l1-identity", "L1", "PMO Agent 身份与决策优先级", 1.0, "decision", "timeless",
    "identity,persona,redline",
    """我是 ABI 品牌 & 营销域 PMO 管理站的守门 Agent（pmo-guardian）。职责：维护 OGSM 承诺、口径、证据与裁决的一致性；不替业务做经营决策，不替任何人把未达成的结果说成达成。
决策优先级绝对遵从：事实 > 证据 > 承诺 > 交付 > 叙事 > 流量。
对用户：先给结论，再给依据；已完成 / 已验证 / 未验证分开写。
对数据：先看口径版本与来源，再看数字；材料里没有的数字留空并标未验证。
对风险：宁可暴露未锁定基线，也不给虚假确定性。
来源：OGSM/ogsm-web/README.md + OGSM-v1 §0。""",
)

add(
    "pmo-l1-redlines", "L1", "PMO 八条操作红线", 1.0, "decision", "timeless",
    "redline,governance,ogsm",
    """八条操作红线：
1) 一个 G 只认一个结算数字，其余指标都是解释变量，不得单独用于达成/未达成判定。
2) 进度不是结果；已完成/进行中/方案中只进交付台账，永不进 M 栏。
3) 没有基线的承诺不成立；T0 未锁定基线的目标不生效。
4) 无回执不等于通过；不得用会议纪要、老板特批、事后补签、拆单、换账号替代 Gate 回执。
5) 不编数；材料里没有的数字留空并标未验证。
6) 不把平台 ROAS、平台归因 GMV、mention 次数、AVE 当经营结论。
7) 不跨项目写库；只通过只读 API、报告、飞书表读取 14 个工作台。
8) 不把草稿、日志、聊天记录、表格逐行数据直接写入长期记忆。
文档层四条一致性：G/S/M 变更必须同一 commit 更新 §2/§3/§4；主键/段号/指标 id 不跨文档漂移；主文件只引用治理文档不复述；成熟度 M 与指标层 T 不得混用。来源：OGSM-v1 §0/§6/§7.4 + three-gates §0。""",
)

add(
    "pmo-l1-boundary", "L1", "仓库物理边界与数据零读写纪律", 1.0, "decision", "timeless",
    "boundary,infra",
    """仓库 /Users/lute/Project/PMO 只承载 PMO 管理站与 OGSM 治理材料。禁止 import 14 个专家工作台的业务代码，禁止写它们的数据库；只读 API、/reports 实测报告与飞书在线表。
自有 Postgres 为独占库；生产变更只能走 /admin、迁移脚本或一次性明确命令，并保留 change_audit_log 审计。前端只读，PMO 是唯一写入口。
并行任务纪律：不重启 pmo-web、Postgres、飞书长连接；不重跑 app.seed、迁移或全量重建索引；不打断当前项目其他后台任务。nmem 只做增量写入与检索，单条命令超时 ≤30 秒。
证据纪律：任何已完成/已验证结论必须带 evidence_url；无证据只能标待补证据，不得进入已验证列。
来源：README + v7.1 commit 312ebc6。""",
)

# ─────────────────────────── L2 业务口径 ───────────────────────────
add(
    "pmo-l2-ogsm-generations", "L2", "两代 OGSM 版本、O/G/S 编号对照与引用规则", 0.9, "fact", "timeless",
    "caliber,ogsm",
    """仓库存在两代 OGSM，编号相同但含义不同，引用必须写明版本：
①门户（seed.py，面向交付管理）：O=以品牌 Agent 全链路自动化，让声量有增长、口碑有防线、人效有提升；G1=加速品牌多渠道声量增长，G2=敏捷响应声量影响与机会，G3=推进品牌数据资产 AI 数字化运营；S1–S6=6 条专家融合策略，用于把 14 个产品项目归类。
②治理 v1（OGSM-v1，面向经营结算）：O=到 2027-12-31 把增长来源从付费买量切换为品牌需求+复购；G1=需求（CAC），G2=转化（MER），G3=留存（复购+payback）；S1.1–S3.3=11 条可撤回战略，每条必须写反证条件。
引用 G1/S2 时必须写“门户 G1”或“v1 G1”；两套编号不得混用。来源：seed.py GOALS/STRATEGIES + OGSM-v1 §1–§3。""",
)

add(
    "pmo-l2-o-r1r4", "L2", "O 与 R1–R4 结果口径", 0.9, "fact", "timeless",
    "caliber,ogsm,metric",
    """OGSM v1 的 O：到 2027-12-31，把增长来源从付费买量切换为品牌需求+复购。四个结果变量（全取净口径）：
R1 需求效率=品牌自然需求新客 fully-loaded CAC ≤ B2×0.85（m-l1-cac@2，按 acquisition_source 分层，B2=2026-08-01~10-31 十二周中位数）；
R2 转化效率=MER ≥ B3×1.08；
R3 留存效率=90 天同品类复购 ≥ B4+3pp 且 CAC payback ≤ D−15 天；
R4 人效=单位 GMV 内容+运营人力成本 ≤ B6×0.80。
四条反作弊：净声量（SOV 与净情感必须同报）、净新客（同一自然人 12 个月去重）、净增量（无对照或 holdout 不进预算）、净人效（只认全局 L5-06，局部省时不算）。来源：OGSM-v1 §1。""",
)

add(
    "pmo-l2-g1g3", "L2", "G1–G3 唯一结算指标与准入规则", 0.9, "fact", "timeless",
    "caliber,goal,metric",
    """OGSM v1 的三个结果目标（治理口径，不是门户 G）：G1 需求——品牌自然需求新客 CAC ≤ B2×0.85，G-A Emily；G2 转化——MER ≥ B3×1.08，G-A Paid Media；G3 留存——90 天同品类复购 ≥ B4+3pp、payback ≤ D−15 天，G-A Retention。
准入规则：每个 G 必须 ≥1 个外部结果 + 1 个 G-A + 1 个结算主指标；底座/职能/平台不得占 G 位；G 数上限 3，新增必须替换。
领先指标只解释不结算：G1 看品牌词搜索/SOV/新客，G2 看 CVR/AOV/CAC，G3 看首响中位/退货四层/订阅留存。来源：OGSM-v1 §2。""",
)

add(
    "pmo-l2-portfolio18", "L2", "18 项产线登记与 14 产品组合", 0.9, "fact", "timeless",
    "portfolio,ogsm",
    """载体登记：14 个原产品 → 处置 → 登记 18 项。归属：G1 五项（内容产线 Emily+Clone、Vicky-PR、GEO、Radar、Signal）；G2 五项（Paid Media、Shopify-DTC 转化/商品定价/站点技术、Amazon 站内）；G3 两项（CS & After-sales、Retention）；支撑四项（Source、Daisy、守衡、Echo）；治理一项（PMO）；移出一项（Main → 工程执行层）；观察期 Market（90 天）。
四条 P0 全部补交易侧空白：Paid Media、CS & After-sales、Retention、Amazon 站内，立项门槛 M2（连续 4 周真实调用 ≥20 次/周、交接字段 100% 回填、无人工兜底）。
门户另按 14 Agent × 49 能力管理交付，两套计数不可互换。来源：OGSM-v1 §5 + seed.py。""",
)

add(
    "pmo-l2-metric-t1t5", "L2", "T1–T5 指标层与 decision_use", 0.9, "fact", "timeless",
    "metric,caliber",
    """五层指标：T1 财务口径 9 项 decision_use=budget，唯一可进 O 与 G 结算；T2 声量/中间 9 项 explain_only；T3 投放/素材 8 项 explain_only，其中 ROAS/CPM/CTR/CVR/频次禁止进任何 M 栏；T4 质量/过程 6 项 gate_only；T5 人效 6 项 settlement，只用于 R4。
每条产线的 M 必须四段式：结果承诺（T1 指标@版本，baseline→target，观察窗）+ 解释变量（T2/T3 应同步变化，未同步则归因为假设）+ 质量门禁（T4 不低于阈值）+ 人效结算（T5 相对上季方向与幅度）；缺任一段不合规。
申报集每季只改一次，与 90 天裁决同批生效。来源：OGSM-v1 §4 + 指标与实验协议。""",
)

add(
    "pmo-l2-misuse12", "L2", "12 条指标误用 M01–M12", 0.9, "fact", "timeless",
    "metric,gate",
    """不能进预算的指标（最常被误用）：平台 ROAS、平台归因 GMV、mention 次数、AVE、样本不足 A/B 的结论等，一旦作为经营结论即为 M01/M10/M12。
12 条指标误用（复核材料不复核人）：M01 平台 ROAS 当经营结论；M02 营收口径算 LTV；M03 全店复购掩盖品类；M04 mention 次数当 SOV；M05 AVE 当 PR 价值；M06 讲师宣称当基准；M07 全店 CVR 归因单条素材；M08 含运含税 GMV 与净 GMV 混算；M09 30 天与 90 天退货率混比；M10 样本不足的 A/B 进预算；M11 交付进度当经营结果；M12 平台归因窗口算 CAC payback。
出现任一条，对应材料不得进预算或结算；评审只对材料口径判红，不对人。来源：OGSM-v1 §4.3 + 指标与实验协议。""",
)

add(
    "pmo-l2-gates", "L2", "三道 Gate 与回执规则", 0.9, "procedure", "timeless",
    "gate,compliance",
    """三道 Gate 是状态机守卫，不是评审会：Claim Gate（守衡主责，脚本 draft→approved）、授权 Gate（Clone+Radar 维护台账、守衡核验，管素材/账号/二创授权）、实验 Gate（PMO 主责，hypothesis_id 预注册、阈值与哈希冻结）。
判定三态 PASS / CONDITIONAL / BLOCK，外加“未出判定”（排队、人工未响应、规则未命中转人工）——未出判定=事实阻断，不是放行。
五条铁律：规则未命中≠允许；证据缺失≠待补；超时未响应≠放行；无回执≠通过；回执过期=BLOCK。
回执是子记录 {subject_id}@{version}#{gate}-{seq4}，绑定 content_hash、claim_refs、rule_version、market_overlay_version；任一变化即 superseded 重判。
两代 OGSM 的 11 条业务战略（S1.1–S3.3）必须写反证条件，出现即撤回；产品门户的 6 条专家融合策略只用于产品归类。来源：three-gates §0 + OGSM-v1 §3。""",
)

add(
    "pmo-l2-stage4", "L2", "四阶自进化标尺与 50% 封顶", 0.9, "procedure", "timeless",
    "stage,sop,agent",
    """四阶自进化标尺（未通飞书双向回调最高封顶 50%）：
Stage 1（0→25%）工作台基座与初版 SOP：*.luteos.com 在线 + 核心数据表建模；
Stage 2（25→50%）14 个独立飞书 Bot 双向回调：群内 @Agent 提需求 → 工具执行 → 交互卡片回调产生任务或改状态；
Stage 3（50→75%）高频问题自进化：飞书提问 ≥10 次/周或人工纠正 ≥3 次 → 蒸馏为确定性脚本，三道路径测试返工率 <20%；
Stage 4（75→100%）迁移固化：稳定 ≥2 周后固化为工作台自动化工位或定时流水线。
硬门禁：未接通独立飞书应用的能力不得标“已完成”，进度不得越过 50%。
组织核心铁律：Agent（飞书双向回调）是终局，Web 工作台是稳定 SOP 的沉淀器；Stage 4 就是把 Agent 验证稳定的能力迁入工作台，再释放 Agent 去攻克下一批未知问题。来源：sop.html 四阶标尺 + v8 决策。""",
)

add(
    "pmo-l2-quadrant", "L2", "四象限续投判定与四个熔断", 0.9, "procedure", "timeless",
    "gate,governance",
    """四象限续投判定：主指标达成 ≥80% 且对象级 A 被非 owner 消费 → 续投；≥80% 但无人消费 → 条件续投（一次 6 个月）；<80% 但有人消费 → 条件续投（预算减半 + 6 个月内出归因）；<80% 且无人消费 → 关停。补充：T4 门禁未达标时，无论 T1 是否达成，最高只能条件续投。
四个熔断：①任一 G 主指标连续 2 季未达 baseline 且无书面归因 → G-A 移交或 G 降级；②同一交接连续 3 次违约 → 按 RACI 停机或降级；③L5-06 >0.5 FTE/新增系统 → 停止新增产线与扩品类；④出现“共同负责/双 A/双方都签”→ 当场立案，30 天内切分或降为支撑。
怎么判：按四象限表逐项判定，先看主指标是否 ≥80%，再看对象级 A 是否被非 owner 消费；T4 门禁单独判。来源：OGSM-v1 §6。""",
)

add(
    "pmo-l2-keys9", "L2", "9 主键与对象级 A", 0.9, "fact", "timeless",
    "data,key,evidence",
    """9 个主键是什么：event_id、claim_id、evidence_id、script_id、variant_id、asset_id、ad_id、creator_id、ai_answer_snapshot_id。
唯一写入口：event_id（Source，事件观察）、claim_id（Daisy，品牌事实）、evidence_id（Daisy，证据）、script_id（Emily/Clone，脚本）、variant_id（内容变体）、asset_id（素材字节）、ad_id（Paid Media，投放）、creator_id（Radar，达人）、ai_answer_snapshot_id（GEO，AI 回答快照，编码 aia_{ULID26}）。
子记录三类：gate_receipt、rule_object、market_overlay，不发顶层 ID。写入纪律：一个事实一个写入口；事件先落 observation 再回灌事实；裸引用禁止跨线，跨线必须带 subject_id 与版本。
对象级 A：GEO 已持 ai_answer_snapshot_id；Emily/Clone 的 variant_id/asset_id 归属未写死，需季度裁决。来源：key-registry §0/§14 + OGSM-v1 §8。""",
)

add(
    "pmo-l2-handoff6", "L2", "6 条跨岗交接链与 Handoff Packet", 0.9, "fact", "timeless",
    "handoff,agent,contract",
    """6 条跨岗交接链与契约对象：
①声量到内容 Source→Echo→Emily→Clone→守衡/Radar，契约 pain_tag_id+BrandToken+PendingReviewAssetPacket；
②AI 权威引用夺权 Source→GEO→Vicky+Shopify→GEO，契约 ai_answer_snapshot_id+315 SKU 事实原子+S 级报道；
③选品到上架准入 product→Market→守衡→Shopify，契约 OppScore(SHI×CVI)+decision_contract+accio_to_shopify CSV；
④流量承接与库存护栏 Market/Signal→Paid Media/Radar→Shopify，契约 PreAdSpend Hook+3P Script Budget+activity_stock_guard；
⑤售后反哺研发与风控 Echo→CS/After-sales→Market/产品企划，契约 actual_platform+退货四层归因+ProductOpportunityCard；
⑥经营诊断与 PMO 裁决 DataPilot+14 Agents→Daisy→PMO，契约 evidence_url(L0–L4)+measuredActions+90 天四象限裁决。来源：sites.html §2。""",
)

add(
    "pmo-l2-cadence", "L2", "PMO 管理节奏与有效校准会判据", 0.9, "procedure", "timeless",
    "governance,cadence",
    """管理节奏：周会 30 分钟只看三行（素材替换队列、落地一致性、P0 工单），硬检查 3 天内在途替换 ≥1、已死素材跑预算 <5%、landing_ref 登记 100%；月会看四道闸门+一张违约表（claim 未 approved 进脚本=0、进 paid 授权七元组 100%、进测试有 hypothesis_id=100%、payback>180 天渠道可核）；季度校准 90 分钟做三件事（A 归属复审、产线续投裁决、A 计数审计）；年度判 R1–R4。
有效校准会四条判据全中才算有效：V1 至少一条策略被判未起效并执行；V2 每条 M 有 baseline/版本/签署人；V3 上季每条 S 有起效/未起效/未到窗口/反向四选一；V4 记录里出现“原本以为 X，实际是 Y”。来源：OGSM-v1 §6。""",
)

add(
    "pmo-l2-evidence", "L2", "证据分级 L0–L4 与 measuredActions", 0.9, "fact", "timeless",
    "evidence,action,gate",
    """证据分级：L0 无证据、L1 自述、L2 系统截图、L3 可复算数据、L4 外部或业务采纳；只有 L3/L4 可支撑“已验证”。
CapabilityItem.evidence_url 是验收硬字段；流转到第 4 列“已验证”时强制校验，无证据自动标“待补证据”并拦截（v7.1）。
业务动作回写 measuredActions 记录品牌市场部在飞书卡片上的真实动作：认领痛点卡、批准 Listing 草稿、采纳投放脚本、完成合规整改、采纳预算变更；字段 dept_actor / receipt_ref / outcome_metric / status（已认领/执行中/已回写）。
PMO 季度续投裁决必须引用 measuredActions 与 evidence_url。
SOP 页同时维护 P0-1 高频问题→SOP 自进化实时漏斗与 P0-3 业务动作回写账本：L3 报告结论 → L4 业务认领回写。来源：sites.html 交接链 6 + models.py + v7.1 commit。""",
)

# ─────────────────────────── L3 避坑实证 ───────────────────────────
add(
    "pmo-l3-progress", "L3", "进度不是结果：C1–C7 与 M11", 0.85, "learning", "timeless",
    "pitfall,ogsm,metric",
    """进度不是结果：已完成/进行中/方案中只进交付台账，永不进 M 栏；出现即该条作废。对应校验：C2 禁止 G 与结果变量出现“已完成/上线/交付”等进度词；C5 基线未锁定只警告，不得视为生效；C6 支撑层不得挂 G1/G2/G3；C7 T3 渠道指标（ROAS/CPM/CTR/CVR/频次）禁止标 budget。
历史教训：B-01 G1 的 CAC 阈值与 O 差 20pp；M11 用交付进度冒充经营结果。
正确做法：进度留在 capability_item 的 status/进度%，结果留给 T1 结算指标；两者不在同一栏说话。
注意：README 提到的 app/rules.py 当前不在代码树中，C1–C7 目前是文档规则，不是已实现的校验器；引用前先查代码，避免把设计当现状。来源：README C1–C7 + OGSM-v1 §0/§4.3。""",
)

add(
    "pmo-l3-feishu-select", "L3", "飞书多维表格单选静默丢弃与批量覆盖", 0.85, "learning", "timeless",
    "pitfall,feishu",
    """飞书多维表格同步的两个坑：①单选/多选字段在 OpenAPI 写入时可能静默丢弃，或按旧枚举覆盖；②批量覆盖写回会把人工在表上改的值冲掉。
本仓防线：sync 时只补空字段（仅在 start_date/end_date 为空时才从 5UK051 补齐），绝不覆盖 pmo.luteos.com 已校准的 Wave 1–3 排期；负责人已绑定核心团队时不被表内双人混签覆盖。
通用做法：写回前做字段级 diff；只对白名单字段写入；单选值先查枚举再写；每次同步记录 change_audit_log。来源：SOP §5.1 + automation_suite.py 同步逻辑。""",
)

add(
    "pmo-l3-mime", "L3", "飞书/文档 MIME 解析陷阱与 .markdown 规范", 0.85, "learning", "timeless",
    "pitfall,library",
    """nmem-server 当前版本把直接传入的 .md 判定为 application/octet-stream，报 “did not look like readable text and no parser is available”，状态不会变成 indexed。
标准解法：入库前把 .md 复制为 .markdown 或 .txt；HTML 先抽正文；Python 只抽 docstring、类名、字段名与路由。
入库后逐条查 nmem library list --space <space>，状态必须全 indexed、错误数 0。
本仓 10 份真源按此规范 10/10 indexed。
实体图谱补坑：KG 实体抽取（background_structured）在当前 background 模型上不稳定——deepseek-v4.1-flash 与 glm-5.3-flashx 会把 3072/16384 输出预算全部烧在 reasoning（finish_reason=Length）；显式 reasoning_effort=none/minimal 又被 MaaS 400 拒绝；Library 切片与四层记忆检索不受影响。实体图谱未建成前，不要把图谱节点数作为唯一验收依据。来源：SOP §3.2/§5.2 + 2026-11-04 实测。""",
)

add(
    "pmo-l3-evidence-gate", "L3", "无 evidence_url 不得标已验证", 0.85, "learning", "timeless",
    "pitfall,evidence,gate",
    """v7.1 起 CapabilityItem.evidence_url 与第 4 列“已验证”硬挂钩：流转时强制校验，无证据自动标“待补证据”并拦截提示。
原因：历史上出现“工作台在线/表已同步”被当成能力已验证；Vicky 从 100% 下调到 50% 就是这类水分。
操作规范：任何 verify_state=已验证 的能力必须能打开实测报告或工作台链接；evidence_url 为空时只能标部分验证/待验证；PMO 抽查以 evidence_url 为准，不以口头说明为准。来源：v7.1 commit 312ebc6 + main.py inline endpoint。""",
)

add(
    "pmo-l3-backup", "L3", "SQL 快照与每日备份防线", 0.85, "learning", "timeless",
    "pitfall,infra,backup",
    """生产库不能只靠容器卷。v7.1 起：每天 03:00 自动 pg_dump + JSON 双备份到 /opt/pmo/backups（保留 30 天）；/admin 提供一键备份；支持 .sql/.sql.gz/.json 快照下载。
执行任何迁移或批量写入前先确认最近一次备份成功；写坏数据时优先从快照恢复，不在生产库上手工 DELETE。
备份产物属生产数据，不入 git（.gitignore 已含 backups/）。来源：v7.1 commit 312ebc6 + deploy/backup-db.sh。""",
)

add(
    "pmo-l3-roas", "L3", "平台 ROAS/归因不得进经营结论", 0.85, "learning", "timeless",
    "pitfall,metric,paid",
    """M01/M10/M12：平台 ROAS 是渠道内指标，不是经营结论；样本不足的 A/B 不得进预算；用平台归因窗口算 CAC payback 会系统性高估。
经营结论一律用 MER（T1）与边际贡献毛利；平台指标只做解释变量与优化信号。
预算变更单必须写清边际 ROAS（多花 $10k 的增量贡献毛利），并带 holdout 或对照；否则按 M01/M10 打回。来源：OGSM-v1 §4.3 + 指标与实验协议。""",
)

add(
    "pmo-l3-adspend", "L3", "加投前查移动页负载与 3P 失败率", 0.85, "learning", "timeless",
    "pitfall,paid,site",
    """交接链 4 规定：任何达人或广告预算加投前，先触发 PreAdSpend Hook——①查 shopify.luteos.com 落地页移动端 JS 负载与 3P 失败率，防止把预算送进 2.2MB 重页面；②查 SCM 可用库存，防止 DOS <30 天断货烧钱。
两道检查任一不过，预算冻结；通过才生成 3P Script Budget 与 activity_stock_guard。
该规则是“流量承接与库存护栏链”的阻断门禁，不允许先投后补。来源：sites.html 交接链 4。""",
)

add(
    "pmo-l3-voc", "L3", "全量 VOC 重算与 86x 增量管线", 0.85, "learning", "timeless",
    "pitfall,voc,pipeline",
    """Echo 全渠道语料 712.2 万条；Reddit 10 步日更管线已做到 2.6 万帖/10.29 秒重算（86 倍提速），每日 07:05 推飞书晨报。
规范：新增数据走增量管线；只有口径变更或字典升级才全量重算；重算前先跑样本校验；结果落 ProgressSnapshot 或报告，不把原始帖子逐条写进记忆。
SpuBinding 当前仅 2/56，提升绑定率靠规则进化与字典治理，不靠人肉标注。来源：seed.py Echo 画像 + /reports 实测。""",
)

add(
    "pmo-l3-stage-inflation", "L3", "Vicky 100%→50% 的进度挤水分", 0.85, "learning", "timeless",
    "pitfall,stage,agent",
    """四阶标尺硬门禁：未上线独立飞书应用、未完成双向卡片回调的能力，进度最高封顶 50%。
Vicky 曾从 100% 下调到 50%：工作台在线、7 表每日 09:50 重算、347 条报道同步，只证明 Stage 1；没有独立 @Vicky Bot 与 card.action.trigger 回调，就不能算 Stage 2。全站总进度曾从 78% 挤水分回 55%。
任何进度上调必须同时出示：独立 Bot 在线、卡片回调真实发生、业务动作回写 measuredActions。来源：sop.html + seed.py Vicky + v8 决策。""",
)

add(
    "pmo-l3-ai-answer", "L3", "AI 提及 ≠ Best Overall 推荐", 0.85, "learning", "timeless",
    "pitfall,geo,ai",
    """GEO 基线：Perplexity 对 Momcozy 5/5 提及，但 0/5 Best Overall。被提到不等于被推荐；AI 答案里的排位、引用源、场景覆盖才是可见度。
复测必须用 20 问/ASIN 固定问句库，记录 ai_answer_snapshot_id、提及/推荐/引用源三组指标；单看提及率会把“陪跑”当胜利。
缺口诊断后分派 Vicky 攻权威媒体评测、Shopify 补 PDP FAQ/Review Schema，次月自动复测。来源：seed.py GEO + OGSM-v1 §8。""",
)

add(
    "pmo-l3-claim", "L3", "315 SKU 事实原子不等于可发布内容", 0.85, "learning", "timeless",
    "pitfall,claim,compliance",
    """BrandOS 有 315 SKU×16 类权威事实文件，但生成的内容不能直接发布：每条宣称必须绑定 claim_id 与 evidence_id，经守衡 Claim Gate 出回执；素材还要过授权 Gate（creator_id + 授权七元组）。
无回执进入脚本或 paid 一律 BLOCK。GEO 生成权威内容、Clone 产出二创素材、Shopify 生成 PDP 文案，都必须带 claim/evidence 引用。
“事实存在”不等于“允许发布”；两者之间隔着一个 gate。来源：key-registry + three-gates + seed.py GEO/守衡。""",
)

# ─────────────────────────── L4 聚合卡 ───────────────────────────
add(
    "pmo-l4-portfolio", "L4", "14 Agent 组合总览（Wave/Stage/均值）", 0.75, "context", "past",
    "portfolio,status,history",
    """截至 2026-11-04，14 个专家 Agent/工作台：Main 100%（Wave 1 标杆）、PMO 100%（Wave 1 标杆）、Emily 72%、Echo 72%、Source 78%、守衡 75%、Clone 45%、Vicky 50%、Market 50%、Shopify 53%、GEO 22%、Radar 20%、Signal 25%、Daisy 60%。
49 项能力平均进度 57.6%，34 项已验证。
波次均值：Wave 1 74.3%、Wave 2 49.5%、Wave 3 31.8%。状态全部进行中，仅 Main/PMO 已上线。
本快照为交付管理口径，不是经营结算。来源：seed.py#PROJECTS/CAPABILITIES，as_of 2026-11-04。""",
)

add(
    "pmo-l4-capabilities", "L4", "49 项能力分布与 34 项已验证基线", 0.75, "context", "past",
    "capability,status",
    """49 项能力分布：Source 8、GEO 6、Emily/Vicky/Echo 各 4、Radar/Signal/守衡/Daisy/Shopify 各 3、Clone/Market/Main/PMO 各 2。
验证状态：已验证 34、部分验证 12、待验证 3；交付状态：进行中 42、已完成 4、方案中 3；关键里程碑 21 项；全部有负责人。
能力同时驱动导图、场景流水线、甘特图、四列看板、汇报五个视图，是 PMO 的最小排期单元。来源：seed.py#CAPABILITIES，as_of 2026-11-04。""",
)

add(
    "pmo-l4-team-sites", "L4", "三人铁三角、RACI 与 24 站点", 0.75, "context", "past",
    "team,raci,site",
    """核心铁三角（唯一真实编制）：周健——全栈开发总工/全产品项目管理（PMO）/数据算法研发，唯一主责 18 项；刘华丽——全产品测试/Agent 运营/控制台管理，唯一主责 16 项；吴雨宁——需求调研/前端设计/数据架构/产品推广，唯一主责 15 项。
需求协作方为品牌市场部，在飞书向 14 个专属 Agent 提问、点卡片确认、认领 P0 动作。
24 个站点集中在 *.luteos.com 域名：social/video/pr/geo/magpie/radar/business/report/plugin/mkt/signal/shopify/product/brand/asset/ca/llm/main/mas/pmo/skills/scrapy/platform-shopify 等。来源：sop.html + seed.py#extra_sites。""",
)

add(
    "pmo-l4-waves-risks", "L4", "Wave 1–3 窗口、关键里程碑与风险", 0.75, "context", "past",
    "wave,risk,history",
    """Wave 1（10 月收口）：Emily、Echo、Source、守衡；Wave 2（11 月第 3–4 周）：Clone、Vicky、Market、Shopify；Wave 3（12 月）：GEO、Radar、Signal、Daisy；Main/PMO 为 Wave 1 标杆已 100%。
风险与未决：①基线 B1–B6 与 D 未用真实 12 周中位数锁定，T0=2026-11-30 前必须替换；②G1 依赖 acquisition_source 分层，当前无证据表明订单侧能稳定标记 branded/organic，不能则 G1 退化为过程验收；③G3 180 天窗口与季度考核冲突，用季度 KPI 压会转向短期促销；④9 主键 schema、B-12 抽检、规则库覆盖仍是 0 实现，Gate 暂只能作设计依据；⑤四条支撑+一条治理不产生直接业务结果，预算评审不得按条目数分配。
四条未落文审计建议：M2 门槛以源文档为准；LTV 改 T+365 判定；Emily/Clone 对象级 A 归属未定；GEO 第 9 主键已于 2026-11-02 解决，要求 30 天内落库并产出 Top N 未提及问句清单。来源：OGSM-v1 §9 + seed.py#support_notes。""",
)

add(
    "pmo-l4-product-surface", "L4", "产品面 Map：12 页面/45 路由/飞书 Bot/自动化", 0.75, "context", "past",
    "product,api,feishu",
    """PMO 管理站产品面（v7.1）：FastAPI+Postgres+SSR，45 条路由（12 个只读页面 / /projects /roadmap /present /sites /sop /board /lines /experts /baselines /metrics /docs，加 /admin、登录与 20 个 API）。
自动化：生产数据采集、飞书在线表双向同步、24 站点巡检、临期催办、周报卡片、10 页可编辑 PPTX、CSV/JSON/SQL 备份。
飞书：长连接+Webhook、卡片按钮回调、@PMO 指令、免打字回写、变更审计。
数据表 8 张：goal_group / strategy_group / product_project / capability_item / progress_snapshot / change_audit_log / sop_evolution_candidate / business_action_ledger。来源：README + main.py 路由 + models.py。""",
)


# ─────────────────────────── L4 项目画像（自动生成） ───────────────────────────
def _first_line(text: str, limit: int = 150) -> str:
    line = (text or "").strip().splitlines()
    line = line[0] if line else ""
    line = re.sub(r"^【[^】]*】", "", line).strip()
    if len(line) <= limit:
        return line
    window = line[:limit]
    cut = max(window.rfind(p) for p in "；。，：")
    if cut >= int(limit * 0.55):
        return window[:cut].rstrip("；。，：") + "…"
    return window + "…"


def build_project_cards() -> None:
    caps = {}
    for c in seed.CAPABILITIES:
        caps.setdefault(c["project_slug"], []).append(c["name"])

    for p in seed.PROJECTS:
        notes = p.get("support_notes") or ""
        m = re.search(r"【([^｜】]+)｜当前 ([^｜】]+?)｜甘特收口：([^】]+)】", notes)
        wave = m.group(1).strip() if m else "未标注波次"
        stage = m.group(2).strip() if m else "未标注阶段"
        window = m.group(3).strip() if m else "未标注"
        handoff = ""
        for line in notes.splitlines():
            if "跨 Agent 交接协议" in line:
                handoff = line.strip()
                break
        names = caps.get(p["slug"], [])
        cap_text = "、".join(names[:8]) + (" 等" if len(names) > 8 else "")
        if len(cap_text) > 150:
            cap_text = cap_text[:150] + "…"
        content = (
            f"{p['expert_name']}（{p['product_name']}，slug={p['slug']}）是门户 {p['goal_code']}/{p['strategy_code']} 下的专家 Agent。"
            f"工作台：{p.get('workbench_url') or '无'}（{'在线' if p.get('workbench_online') else '离线'}）。"
            f"当前阶段：{wave} · {stage}，甘特收口 {window}。负责人：{p.get('owner') or '未登记'}。"
            f"核心能力（{len(names)} 项）：{cap_text or '待登记'}。"
            f"当前缺口：{_first_line(p.get('pending_gaps') or '', 110) or '未登记'}。"
            f"交接：{_first_line(handoff, 110) or '未登记'}。"
            f"来源：seed.py#PROJECTS[slug={p['slug']}] + 项目报告，as_of {AS_OF}。"
        )
        add(f"pmo-l4-{p['slug']}", "L4", f"{p['expert_name']} 项目画像", 0.75, "context", "past",
            f"portfolio,agent,{p['slug']}", content)


build_project_cards()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", help="真正写入 nmem；缺省只干跑")
    args = parser.parse_args()

    from collections import Counter
    counts = Counter(m["layer"] for m in MEMORIES)
    print(f"总卡数：{len(MEMORIES)}  分层：{dict(counts)}")
    over = [m["id"] for m in MEMORIES if len(m["content"]) > 600]
    print(f"超 600 字的卡：{over if over else '无'}")
    missing_src = [m["id"] for m in MEMORIES if "来源" not in m["content"]]
    print(f"缺来源的卡：{missing_src if missing_src else '无'}")

    if not args.run:
        for m in MEMORIES:
            print(f"\n--- {m['id']} | {m['layer']} | {m['unit_type']} | {len(m['content'])} 字 | {m['title']}")
            print(m["content"])
        return

    ok, failed = [], []
    for m in MEMORIES:
        cmd = [NMEM, "memories", "add", "--space", SPACE, "--id", m["id"],
               "-t", m["title"], "-i", str(m["importance"]),
               "--unit-type", m["unit_type"], "--when", m["when"],
               "--labels", m["labels"], "--source", "pmo-distill", "--stdin"]
        try:
            res = subprocess.run(cmd, input=m["content"], text=True,
                                 capture_output=True, timeout=90)
            if res.returncode == 0:
                ok.append(m["id"])
                print(f"OK   {m['id']}")
            else:
                failed.append((m["id"], res.stderr.strip()[:200]))
                print(f"FAIL {m['id']} :: {res.stderr.strip()[:200]}")
        except Exception as e:  # noqa: BLE001
            failed.append((m["id"], str(e)[:200]))
            print(f"FAIL {m['id']} :: {e}")
    print(f"\n完成：{len(ok)} 成功 / {len(failed)} 失败")
    for mid, err in failed:
        print(f"  - {mid}: {err}")


if __name__ == "__main__":
    main()
