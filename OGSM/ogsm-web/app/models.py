"""ABI 品牌 & 营销 Agent 多项目管理网站 —— 数据模型。

严格对齐《ABIOGSM-品牌Agent》思维导图 9 级结构：
愿景(O) → 目标(G1/G2/G3) → 策略(S) → 专家昵称 → 产品构成 → 验收工作台
→ 业务场景 → 能力图谱(含进度与待整合子平台) + /reports 实测成果与支撑补充。
"""
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class GoalGroup(SQLModel, table=True):
    """G 层：G1 加速品牌多渠道声量增长 / G2 敏捷响应... / G3 推进品牌数据资产..."""

    __tablename__ = "goal_group"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True)  # G1 / G2 / G3
    title: str  # 加速品牌多渠道声量增长
    subtitle: str = ""  # 简短说明
    sort: int = 0


class StrategyGroup(SQLModel, table=True):
    """S 层：6 条专家融合策略。"""

    __tablename__ = "strategy_group"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True)  # S1..S6
    goal_code: str = Field(index=True)  # G1 / G2 / G3
    title: str  # 社媒专家 + 爆款复刻专家 融合...
    sort: int = 0


class ProductProject(SQLModel, table=True):
    """核心管理单元：14 个专家产品项目（以产品名称为项目名称）。"""

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
    owner: str = ""  # 负责人

    # /reports 深度总结（格赖斯准则 + ste-zh：已验证能力 / 核心实测数据 / 待补齐项）
    verified_summary: str = ""  # 已验证能力与核心方法
    metrics_highlights: str = ""  # 核心实测指标（用 \n 分隔，每行 指标名|数值|出处）
    pending_gaps: str = ""  # 待补齐项（用 \n 分隔）
    report_links: str = ""  # 关联的 /reports 报告路径（用 \n 分隔，标题|路径）
    extra_sites: str = ""  # 待整合能力/关联子站（用 \n 分隔，名称|URL|状态）

    # 补充文档支撑（折叠展示，不喧宾夺主）
    support_notes: str = ""  # 上下游协作、核心指标口径、演进建议
    sort: int = 0
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CapabilityItem(SQLModel, table=True):
    """能力图谱与进度：挂在具体产品项目下。"""

    __tablename__ = "capability_item"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_slug: str = Field(index=True)
    scenario_line: str = ""  # 所属业务场景线（如 PR 线 / 舆情线）
    name: str  # 爆款/趋势洞察
    description: str = ""  # 发现社媒爆款与趋势，输出可复刻的内容结构
    status: str = Field(default="进行中")  # 已完成 / 进行中 / 方案中
    verify_state: str = Field(default="已验证")  # 已验证 / 部分验证 / 待验证
    integration_name: str = ""  # 待整合能力名称（如 品类洞察平台）
    integration_url: str = ""  # 整合来源 URL（如 https://business.luteos.com/）
    sort: int = 0
