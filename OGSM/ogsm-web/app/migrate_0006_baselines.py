"""迁移 0006：把 B1–B6 / D 从文档里的文字变成可填的结构。

背景：C5 警告「G 基线未锁定」在 T0（2026-11-30）前无法消失，因为缺的是真实数据。
但如果基线只写在 md 里，锁定这件事就永远没有执行点——谁锁、锁了什么、什么时候锁的，都查不到。

本迁移建立 `baseline` 表：每个基线键一行，带口径、窗口、数值、锁定状态与锁定人。
校验器 C5 从此不再只看 Goal.baseline_locked 这个 bool，而是看这张表里是否真有一行非空的数值。
"""
from datetime import datetime, timezone

from sqlmodel import Field, Session, SQLModel, select

from .db import engine, init_db


class Baseline(SQLModel, table=True):
    """基线。一个 OGSM 周期内每个键一行。

    设计要点：`value` 为空 = 未锁定。不允许用「0」或「N/A」冒充——
    那会让 C5 永远显示通过，而这正是最危险的一种通过。
    """

    __tablename__ = "baseline"

    id: int | None = Field(default=None, primary_key=True)
    key: str = Field(unique=True)  # B1..B6 / D
    name: str
    metric_id: str
    formula_note: str = ""  # 口径说明：怎么算的
    window: str = ""  # 观察窗口
    unit: str = ""
    value: str | None = None  # 空 = 未锁定
    locked_at: datetime | None = None
    locked_by: str = ""
    source_system: str = ""  # 数据从哪来
    note: str = ""
    sort: int = 0


SPECS = [
    dict(key="B1", name="品牌自然需求新客数", metric_id="m-l1-cac@2",
         formula_note="branded + organic NTB，同一自然人 12 个月去重",
         window="2026-08-01 ~ 2026-10-31 十二周中位数", unit="人", sort=1,
         source_system="订单侧 NTB 标记"),
    dict(key="B2", name="品牌自然需求新客的 fully-loaded CAC", metric_id="m-l1-cac@2",
         formula_note="（广告+工具分摊+达人费用+人力分摊）÷ 同期品牌自然需求新客数",
         window="2026-08-01 ~ 2026-10-31 十二周中位数", unit="USD", sort=2,
         source_system="财务分摊 + ad_id 花费快照"),
    dict(key="B3", name="MER", metric_id="m-l1-mer@1",
         formula_note="净营收（全渠道）÷ 总营销费用",
         window="上一完整季度（2026Q3）", unit="ratio", sort=3,
         source_system="财务总账 ÷ 营销费用科目"),
    dict(key="B4", name="90 天同品类复购率", metric_id="m-l1-rp90@1",
         formula_note="90 天内第 2 单且同品类客户数 ÷ 同期首单 cohort，按品类分列",
         window="最近 4 个完整 cohort", unit="%", sort=4,
         source_system="订单 cohort + category_map@version"),
    dict(key="B5", name="12 个月贡献毛利 LTV", metric_id="m-l1-ltv@1",
         formula_note="首单 cohort 12 个月累计贡献毛利 ÷ cohort 新客数；不足 12 个月标 partial",
         window="最近 4 个完整季度 cohort 加权中位数", unit="USD", sort=5,
         source_system="订单 cohort + 贡献毛利明细"),
    dict(key="B6", name="单位 GMV 内容+运营人力成本", metric_id="m-l5-laborpergmv@1",
         formula_note="内容+运营人力成本（含外包）÷ 同期净 GMV",
         window="上一季度（2026Q3）", unit="USD per 1M GMV", sort=6,
         source_system="财务人力分摊 + m-l1-gmv"),
    dict(key="D", name="CAC payback 天数", metric_id="m-l1-payback@1",
         formula_note="累计首单贡献毛利 ≥ CAC 所需天数，日粒度插值；分渠道",
         window="近 2 个季度", unit="天", sort=7,
         source_system="同 B2 与 m-l1-cm"),
]


def migrate() -> None:
    init_db()
    # Baseline 定义在本模块内，需要注册到 metadata 才能建表
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        added = 0
        for spec in SPECS:
            row = s.exec(select(Baseline).where(Baseline.key == spec["key"])).first()
            if row is None:
                s.add(Baseline(**spec))
                added += 1
        s.commit()
        total = len(s.exec(select(Baseline)).all())
        print(f"[migrate] 基线表：新增 {added} 行，共 {total} 行")
        locked = [b.key for b in s.exec(select(Baseline)).all() if b.value]
        print(f"[migrate] 已锁定：{', '.join(locked) if locked else '无（全部待填）'}")


if __name__ == "__main__":
    migrate()
