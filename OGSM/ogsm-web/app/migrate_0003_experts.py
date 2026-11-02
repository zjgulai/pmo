"""一次性数据迁移 0003：写入专家 × OGSM 映射。

来源：reports/ 九份专家成果总结（2026-10-31 ~ 11-02）。
幂等：已存在的专家不覆盖，缺失的补齐。
"""
from sqlmodel import Session, select

from .db import engine, init_db
from .models import Expert


def migrate() -> None:
    from .seed import seed_experts

    # 专家表是 2026-11-02 新增的；先建表（create_all 幂等，不动已有表）
    init_db()
    with Session(engine) as s:
        existing = {e.name for e in s.exec(select(Expert)).all()}
        added = seed_experts(s, skip=existing)
        s.commit()
        print(f"[migrate] 专家映射：新增 {added} 条，已存在 {len(existing)} 条跳过")


if __name__ == "__main__":
    migrate()
