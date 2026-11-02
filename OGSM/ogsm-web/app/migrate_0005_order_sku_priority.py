"""迁移 0005：落实「order_id + sku_id 优先」决议（2026-11-02）。

背景：三份专家报告独立撞上同一面墙——没有 sku_id。
- Vicky Tracker 品线覆盖 0.0%
- Echo 产品身份解析 2/56
- Shopify 依赖商品主数据

决议：order_id + sku_id 由「记录项」提为与三键并行落库，Source 为首交付方。

本迁移只改交付台账的状态与描述，不动主键契约本身（契约在字典 §15）。
"""
from sqlmodel import Session, select

from .db import engine, init_db
from .models import WorkItem

# 按 title 匹配（work_item 无唯一键，用标题定位）
UPDATES = [
    {
        "match": "8 主键 schema 落库",
        "title": "order_id + sku_id 落库（P0 首交付，与三键并行）",
        "status": "进行中",
        "blocker": "PMO 标准已定（字典 §15）；待 Source 落库。attribution_source 填充率 <70% 则 G1 降级",
        "evidence": "契约：brand-agent-ogsm-key-registry §15；决策：专家-OGSM-结合方案 §2.2",
    },
]

# 新增跟踪项
ADD = [
    {
        "line_name": "Source",
        "title": "sku_id 主数据合并（Shopify × Amazon × TikTok）",
        "status": "方案中",
        "blocker": "两套主数据重合率未知；需先做 100 条抽样比对",
        "evidence": "",
    },
    {
        "line_name": "Vicky-PR",
        "title": "Tracker 品线字段回填（当前 0.0%）",
        "status": "方案中",
        "blocker": "依赖 sku_id 落库",
        "evidence": "reports/Vicky 主报告：Tracker 品线覆盖 0.0%（347 条全空）",
    },
    {
        "line_name": "Echo",
        "title": "产品身份解析覆盖率 2/56 → ≥80%",
        "status": "方案中",
        "blocker": "依赖 sku_id 落库",
        "evidence": "reports/Echo 2026-11-02：L1-T05 连续 2 日非零，覆盖率仍低",
    },
]


def migrate() -> None:
    init_db()
    with Session(engine) as s:
        for u in UPDATES:
            wi = s.exec(select(WorkItem).where(WorkItem.title.contains(u["match"]))).first()
            if wi is None:
                print(f"[migrate] 未找到含「{u['match']}」的交付项，跳过")
                continue
            changed = []
            for k, v in u.items():
                if k == "match":
                    continue
                if getattr(wi, k) != v:
                    setattr(wi, k, v)
                    changed.append(k)
            if changed:
                s.add(wi)
                print(f"[migrate] 更新「{u['title']}」：{', '.join(changed)}")

        existing = {w.title for w in s.exec(select(WorkItem)).all()}
        added = 0
        for a in ADD:
            if a["title"] in existing:
                continue
            s.add(WorkItem(**a))
            added += 1
        if added:
            print(f"[migrate] 新增交付项 {added} 条")

        s.commit()
        print("[migrate] 0005 完成")


if __name__ == "__main__":
    migrate()
