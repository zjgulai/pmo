"""V3 数据初始化与平滑迁移入口。

生产容器启动时执行 `python -m app.migrate`：
- 自动补齐 V3 新增的排期与甘特图列（progress_pct, start_date, end_date, owner, is_milestone）
- 若数据库中尚无排期日期数据，自动写入 V3 完整 14 个产品项目与 49 项带排期能力点
- 若已有排期数据，则保留 PMO 在前台或后台修改过的最新记录
"""
from sqlmodel import Session, SQLModel, select

from .db import engine
from .models import CapabilityItem, ProductProject
from .seed import _ensure_v3_columns, backfill_evidence_urls, seed


def main() -> None:
    SQLModel.metadata.create_all(engine)
    _ensure_v3_columns()
    with Session(engine) as s:
        projs = s.exec(select(ProductProject)).all()
        caps = s.exec(select(CapabilityItem)).all()
        has_dates = any(getattr(c, "start_date", "") for c in caps)

    if len(projs) < 14 or not has_dates:
        print(f"[migrate] 检测到项目数={len(projs)} 或尚未初始化甘特图排期，执行初始化")
        seed(force_reset=True)
    else:
        print(f"[migrate] 已存在 {len(projs)} 个项目与排期数据，保留现有状态")

    with Session(engine) as s:
        n = backfill_evidence_urls(s)
        if n:
            print(f"[migrate] 自动回填 {n} 项已验证能力的实测报告证据链接")


if __name__ == "__main__":
    main()
