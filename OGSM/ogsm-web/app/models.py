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
    sort: int = 0
