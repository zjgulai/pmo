"""ABI 品牌 & 营销 Agent 多项目管理网站 —— 数据模型 (V3)。

第一性原理与奥卡姆剃刀设计：
1. 宏观到微观唯一主干：愿景(O) → 目标(G1/G2/G3) → 策略(S1~S6) → 14个产品项目(Agent&工作台) → 49项能力图谱(CapabilityItem)。
2. 能力图谱(CapabilityItem)既是思维导图的叶子，也是业务场景自动化的组成模块，同时承载起止日期、进度百分比、负责人与里程碑标记——同一份数据直接驱动「思维导图、场景流水线、甘特图、四列看板、汇报演示」五大视图，零冗余表。
"""
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class GoalGroup(SQLModel, table=True):
    """G 层：G1 加速品牌多渠道声量增长 / G2 敏捷响应... / G3 推进品牌数据资产..."""

    __tablename__ = "goal_group"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True)  # G1 / G2 / G3
    title: str
    subtitle: str = ""
    sort: int = 0


class StrategyGroup(SQLModel, table=True):
    """S 层：6 条专家融合策略。"""

    __tablename__ = "strategy_group"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True)  # S1..S6
    goal_code: str = Field(index=True)  # G1 / G2 / G3
    title: str
    sort: int = 0


class ProductProject(SQLModel, table=True):
    """核心管理单元：14 个专家产品项目（Agent 及其对应的验收工作台）。"""

    __tablename__ = "product_project"

    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True)  # emily, clone, vicky...
    expert_name: str  # 专家昵称：Emily
    product_name: str  # 产品构成：社媒Agent&工作台
    goal_code: str = Field(index=True)  # G1 / G2 / G3
    strategy_code: str = Field(index=True)  # S1..S6
    workbench_url: str = ""  # https://social.luteos.com/
    workbench_online: bool = Field(default=True)
    scenarios: str = ""  # 多条业务场景用 \n 分隔
    status_summary: str = Field(default="进行中")  # 已上线 / 进行中 / 方案中
    owner: str = ""  # 负责团队/负责人

    # /reports 深度总结（格赖斯准则 + ste-zh：已验证能力 / 核心实测数据 / 待补齐项）
    verified_summary: str = ""
    metrics_highlights: str = ""  # 指标名|数值|出处
    pending_gaps: str = ""
    report_links: str = ""  # 标题|路径
    extra_sites: str = ""  # 名称|URL|状态
    support_notes: str = ""
    sort: int = 0
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CapabilityItem(SQLModel, table=True):
    """最小管理与排期单元：49 项产品能力图谱（同源驱动导图、场景流水线、甘特图与四列看板）。"""

    __tablename__ = "capability_item"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_slug: str = Field(index=True)
    scenario_line: str = ""  # 所属业务场景链路
    name: str  # 能力点名称
    description: str = ""  # 解决的具体业务问题
    status: str = Field(default="进行中")  # 已完成 / 进行中 / 方案中
    verify_state: str = Field(default="已验证")  # 已验证 / 部分验证 / 待验证

    # 排期与甘特图字段（对齐飞书 OGSM 总览表 H/I/J/K 列）
    progress_pct: int = Field(default=0)  # 0 ~ 100
    start_date: str = ""  # YYYY-MM-DD，空表示待排期
    end_date: str = ""  # YYYY-MM-DD，空表示待排期
    owner: str = ""  # 负责人
    is_milestone: bool = Field(default=False)  # 关键里程碑标记

    integration_name: str = ""  # 待整合能力名称
    integration_url: str = ""  # 整合来源 URL
    evidence_url: str = ""  # 实测验收证据链接（如 /reports-view/... 或工作台 URL）
    sort: int = 0


class ProgressSnapshot(SQLModel, table=True):
    """进度快照表：用于一键保存某时刻的 49 项能力进度并自动对比生成周报简报。"""

    __tablename__ = "progress_snapshot"

    id: Optional[int] = Field(default=None, primary_key=True)
    label: str = ""  # 如 2026-11-02 周快照
    overall_pct: int = 0
    done_count: int = 0
    verified_count: int = 0
    payload_json: str = ""  # JSON: {cap_id: {name, proj, status, verify_state, pct}}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChangeAuditLog(SQLModel, table=True):
    """进度与状态变更审计流水：记录网页行内修改、飞书群指令修改或表格同步的每一次变动。"""

    __tablename__ = "change_audit_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    cap_id: int = 0
    project_slug: str = ""
    expert_name: str = ""
    cap_name: str = ""
    source: str = "web"  # web / feishu_bot / sheet_sync
    actor: str = "PMO"
    summary: str = ""  # 如 进度 60% -> 80%，状态 进行中 -> 已完成
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SopEvolutionCandidate(SQLModel, table=True):
    """P0-1 飞书高频问题自进化漏斗：记录各专家飞书 Bot 高频提问（≥10次/周）或打回（≥3次）转化为工作台 SOP 的实时状态。"""

    __tablename__ = "sop_evolution_candidate"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_slug: str = Field(index=True)
    expert_name: str = ""
    wave: str = "Wave 1"  # Wave 1 / Wave 2 / Wave 3
    topic: str = ""  # 高频问题聚类主题
    weekly_ask_count: int = 0  # 飞书群周提问/触发次数（阈值 ≥10）
    reject_count: int = 0  # 卡片打回/人工纠正次数（阈值 ≥3）
    rework_rate_pct: int = 100  # 近期脚本返工率%（晋升阈值 <20%）
    current_stage: str = "Stage 2"  # Stage 1 / Stage 2 / Stage 3 / Stage 4
    target_workbench_sop: str = ""  # 迁移固化到的工作台工位名称
    owner: str = "刘华丽"  # 运营/研发/固化主责人
    due_date: str = ""  # 对应甘特图收口日期 YYYY-MM-DD
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BusinessActionLedger(SQLModel, table=True):
    """P0-3 品牌市场部业务动作回写账本（measuredActions）：记录业务人员在飞书卡片点按钮认领/批准发布/完成整改的真实闭环动作。"""

    __tablename__ = "business_action_ledger"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_slug: str = Field(index=True)
    expert_name: str = ""
    action_type: str = ""  # 认领痛点卡 / 批准Listing草稿 / 采纳投放脚本 / 完成合规整改 / 采纳预算变更
    action_title: str = ""  # 具体业务动作说明
    dept_actor: str = "品牌市场部"  # 认领执行的业务子团队
    receipt_ref: str = ""  # 关联的 gate_receipt 或对象主键（如 sku_id / claim_id）
    outcome_metric: str = ""  # 回写的业务结果或验证状态
    status: str = "已回写"  # 已认领 / 执行中 / 已回写
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GateReceipt(SQLModel, table=True):
    """P0-4 三道 Gate 状态机守卫回执（子记录，定位串 {subject_id}@{version}#{gate}-{seq4}）。

    遵循《品牌 Agent 三个 Gate 规格与 Fail-closed 默认》：
    - gate_type: C (Claim Gate 守衡主责) / A (授权 Gate Radar台账+守衡核验) / X (实验 Gate PMO主责)
    - verdict: PASS / CONDITIONAL / BLOCK
    - 五项绑定指纹：subject_id@version, content_hash, claim_refs_json, rule_refs_json, market_overlay_version
    """

    __tablename__ = "gate_receipt"

    id: Optional[int] = Field(default=None, primary_key=True)
    receipt_id: str = Field(unique=True, index=True)  # 如 scr-bpc-tiktok-00317@2#C-0001
    subject_id: str = Field(index=True)  # 如 scr-bpc-tiktok-00317
    subject_version: int = 1
    gate_type: str = Field(index=True)  # C / A / X
    seq4: str = "0001"
    verdict: str = "BLOCK"  # PASS / CONDITIONAL / BLOCK
    content_hash: str = ""  # SHA-256 指纹
    claim_refs_json: str = "[]"  # ["clm-bpc-us-0142@3"]
    rule_refs_json: str = "[]"  # ["rule-claim-cosmetic-medical-boundary-us-review@3"]
    market_overlay_version: str = ""  # 如 overlay-us-ftc-fda@1
    evidence_refs_json: str = "[]"  # ["evd-sgs-2026-009@1"] 或 ["NOT_APPLICABLE"]
    conditions_json: str = "[]"  # CONDITIONAL 限制谓词
    valid_until: str = ""  # YYYY-MM-DD，到期自动视为 expired = BLOCK
    invalidate_on_json: str = '["content_hash_change","claim_version_change","rule_version_change","rights_revoked","expired"]'
    judged_by: str = "守衡-Engine@v2.1 (抽检:刘华丽)"
    status: str = "active"  # active / superseded / overturned / expired
    reason_summary: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


