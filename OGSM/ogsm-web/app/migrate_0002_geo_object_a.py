"""一次性数据迁移：2026-11-02 增补 ai_answer_snapshot_id 后，
把 GEO 从「两类 A 都没有」更新为「持对象级 A」。

可重复执行（幂等）。
"""
from sqlmodel import Session, select

from .db import engine
from .models import Line

GEO_TARGET = {
    "object_a": "GEO",
    "object_a_key": "ai_answer_snapshot_id",
    "consumer": "内容产线, Amazon 站内, Signal",
    "note": "段级 0 A；2026-11-02 增补第 9 键后靠对象级 A 站立",
}

# Echo 段级 0 A 是文档明确认可的形态（RACI §3.3）：问责靠 taxonomy 版本
# 与抽检一致率，不靠主键写入口。必须把载体写进备注，校验器 C3 才认。
ECHO_TARGET = {
    "consumer": "CS, 内容产线, Signal, Retention",
    "note": "段级 0 A；问责载体是 taxonomy 版本化对象 + 抽检一致率（m-x-taxo-agree），不占主键位",
}


def migrate() -> None:
    with Session(engine) as s:
        for name, target in (("GEO", GEO_TARGET), ("Echo", ECHO_TARGET)):
            ln = s.exec(select(Line).where(Line.name == name)).first()
            if ln is None:
                print(f"[migrate] {name} 不存在，跳过（应由 seed 写入）")
                continue
            changed = []
            for k, v in target.items():
                if getattr(ln, k) != v:
                    setattr(ln, k, v)
                    changed.append(k)
            if changed:
                s.add(ln)
                print(f"[migrate] {name} 已更新：{', '.join(changed)}")
            else:
                print(f"[migrate] {name} 已是目标状态，无需变更")
        s.commit()


if __name__ == "__main__":
    migrate()
