"""OGSM 数据模型。

设计原则：schema 即 OGSM 结构。字段的可为空与否，直接编码「哪一层允许缺什么」。
- G 的结算主指标只有一个 → 由 rules.py 校验，不靠应用层约定。
- 进度（状态三态）不进 Result，单独落在 WorkItem。
"""
from datetime import date, datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel, UniqueConstraint


class Objective(SQLModel, table=True):
    """O 层：整个周期只有一条，改需重发版本。"""

    __tablename__ = "objective"

    id: Optional[int] = Field(default=None, primary_key=True)
    version: str = Field(default="v1.0")
    statement: str = Field(description="一句话 O")
    cycle_start: date = Field(default=date(2026, 12, 1))
    cycle_end: date = Field(default=date(2027, 12, 31))
    base_window: str = Field(default="2026-08-01~2026-10-31 十二周中位数")
    contraindications: str = Field(
        default="", description="O 不写哪三件事（换行分隔）"
    )
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ResultVariable(SQLModel, table=True):
    """O 下的结果变量 R1–R4，每个都有基线/目标/判定时点。"""

    __tablename__ = "result_variable"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True)  # R1..R4
    name: str  # 需求效率 / 转化效率 ...
    metric_id: str  # m-l1-cac@2
    baseline_key: str  # B2
    baseline_note: str = ""
    target: str
    judge_at: date
    goal_code: Optional[str] = None  # R4 为 None（跨 G 约束）
    sort: int = 0


class Goal(SQLModel, table=True):
    """G 层。三条准入规则由 rules.py 强制。"""

    __tablename__ = "goal"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True)  # G1
    name: str  # 需求
    one_liner: str  # 让人找到你并相信你
    main_metric_id: str = Field(description="唯一结算主指标，必须 T1 层")
    window_start: date = date(2026, 12, 1)
    window_end: date
    ga: str = Field(description="G-A 负责人")
    leading: str = Field(default="", description="领先指标，只解释不结算，逗号分隔")
    baseline_locked: bool = Field(default=False)
    sort: int = 0


class Strategy(SQLModel, table=True):
    """S 层。反证条件必填——这是唯一能自我纠错的机制。"""

    __tablename__ = "strategy"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True)  # S1.1
    goal_code: str = Field(description="挂到哪个 G；支撑层写 S0")
    title: str
    one_liner: str
    falsification: str = Field(description="反证条件：出现即撤回，必填")
    owner: str = ""
    sort: int = 0


class Line(SQLModel, table=True):
    """载体：18 项登记。"""

    __tablename__ = "line"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    layer: str = Field(description="G1/G2/G3/support/governance/out")
    kind: str = Field(default="business")  # business / support / governance / out
    seg_a: Optional[str] = None  # 段 A
    object_a: Optional[str] = None  # 对象级 A（主键写入口）
    object_a_key: Optional[str] = None  # claim_id / variant_id ...
    strategy_code: Optional[str] = None
    maturity: str = Field(default="M0")  # M0..M4
    consumer: Optional[str] = None  # 实际消费的非 owner 产线
    status: str = Field(default="active")  # active / watch / retire / out
    is_p0: bool = Field(default=False)
    note: str = ""


class Metric(SQLModel, table=True):
    """指标字典。五层 T1–T5，decision_use 决定能否进 OGSM 结算。"""

    __tablename__ = "metric"

    id: Optional[int] = Field(default=None, primary_key=True)
    metric_id: str = Field(index=True)  # m-l1-cac
    version: int = Field(default=1)
    layer: str  # T1..T5
    name: str
    formula: str = ""
    decision_use: str = "explain_only"  # budget/explain_only/gate_only/settlement
    owner: str = ""
    source_system: str = ""

    __table_args__ = (UniqueConstraint("metric_id", "version"),)


class MetricSnapshot(SQLModel, table=True):
    """结算快照。只追加不覆盖。"""

    __tablename__ = "metric_snapshot"

    id: Optional[int] = Field(default=None, primary_key=True)
    line_name: str
    metric_id: str
    period: str  # 2026Q4
    baseline: Optional[str] = None
    target: Optional[str] = None
    actual: Optional[str] = None
    note: str = ""
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Baseline(SQLModel, table=True):
    """基线。一个 OGSM 周期内每个键一行。

    `value` 为空 = 未锁定。不允许用 0 或 N/A 冒充——那会让 C5 永远显示通过，
    而这是最危险的一种通过：看起来有数，实际没人认账。
    """

    __tablename__ = "baseline"

    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(unique=True)  # B1..B6 / D
    name: str
    metric_id: str
    formula_note: str = ""
    window: str = ""
    unit: str = ""
    value: Optional[str] = None
    locked_at: Optional[datetime] = None
    locked_by: str = ""
    source_system: str = ""
    note: str = ""
    sort: int = 0


class Expert(SQLModel, table=True):
    """专家 × OGSM 映射。

    这张表回答一个 OGSM 自身回答不了的问题：**承诺与资源是否对齐**。
    - 有 OGSM 线、无建设证据 → OGSM 承诺了没做（C9 抓）
    - 有建设证据、无 OGSM 线 → 做了没承诺（C10 抓）

    成熟度双栏：报告自报（claimed）与 OGSM 授予（granted）分开。
    按 OGSM 规则，自报不构成授予，granted 默认不高于 M1，除非有非 owner 消费方证据。
    """

    __tablename__ = "expert"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    line_name: Optional[str] = None  # 映射到的 OGSM 产线；空 = 游离
    evidence_doc: str = ""  # 报告文件名，可追溯
    report_date: str = ""
    key_reading: str = ""  # 报告里的关键读数
    maturity_claimed: str = Field(default="M1")
    maturity_granted: str = Field(default="M1")
    gap: str = ""  # 报告自指或分析识别的缺口
    action: str = ""  # 结合动作
    status: str = Field(default="aligned")
    # aligned / has_real_no_name / name_no_build / orphan / excluded
    note: str = ""
    sort: int = 0


class WorkItem(SQLModel, table=True):
    """交付台账。状态三态只允许出现在这里，永不进 M 栏。"""

    __tablename__ = "work_item"

    id: Optional[int] = Field(default=None, primary_key=True)
    line_name: str
    title: str
    status: str = Field(default="进行中")  # 已完成 / 进行中 / 方案中
    evidence: str = ""
    blocker: str = ""
    due: Optional[date] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CheckRun(SQLModel, table=True):
    """校验器的历史结果——让「规则有没有真的在跑」可查。"""

    __tablename__ = "check_run"

    id: Optional[int] = Field(default=None, primary_key=True)
    ran_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    passed: bool = False
    summary: str = ""
