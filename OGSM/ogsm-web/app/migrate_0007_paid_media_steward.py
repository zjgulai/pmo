"""迁移 0007：落实 2026-11-02 Paid Media 三项决定。

决定（业务负责人确认）：
1. S5-A 走 B 方案：PMO steward 过渡 90 天，具体人选待定
2. G2-A 与 S5-A 拆开：G2-A 不再由 Paid Media 担任
3. steward 权限边界：只出规则与数据，不签预算

为什么拆开 G2-A / S5-A：
G2 的结算主指标是 MER（全渠道净营收 ÷ 总营销费用），包含自然流量与品牌词，
不全是投放能控制的结果。让 Paid Media 对 MER 负全责，会出现「自然流量下滑也算
投放没做好」的错配——这是 OGSM §1.1 批判的「用中间变量冒充结果」的镜像版本。

同时修正 RACI §3.2「一人一段一 A，最高为 1」的规则冲突：原 OGSM 让 Paid Media
同时持 G2-A 与 S5-A，是唯一一人两 A 的位置。

幂等：逐条比对目标值。
"""
from sqlmodel import Session, select

from .db import engine, init_db
from .models import Goal, Line, WorkItem

G2_A_TARGET = "业务负责人（直管）"

# S5-A 由 PMO steward 代持。Line.seg_a 是字符串，直接写 steward 表述。
PAID_MEDIA_TARGET = {
    "seg_a": "PMO steward（过渡 90 天，不签预算）",
    "note": "P0 新增。S5-A 由 PMO steward 代持至 2026-12-02 前后；"
            "steward 权限边界：只出规则与数据，不签预算。G2-A 不由本条产线担任（已拆开）",
}

WORKITEM = {
    "line_name": "Paid Media",
    "title": "S5-A 转正：确定 90 天后的正式负责人",
    "status": "方案中",
    "blocker": "人选未定。steward 到期未转正即升级到季度评审，不允许自动续期",
    "evidence": "决议 2026-11-02：走 B 方案（PMO steward 过渡 90 天）",
}


def migrate() -> None:
    init_db()
    with Session(engine) as s:
        # ① G2-A 拆开
        g2 = s.exec(select(Goal).where(Goal.code == "G2")).first()
        if g2:
            if g2.ga != G2_A_TARGET:
                print(f"[migrate] G2-A：{g2.ga} → {G2_A_TARGET}")
                g2.ga = G2_A_TARGET
                s.add(g2)
            else:
                print("[migrate] G2-A 已是目标状态")
        else:
            print("[migrate] 警告：未找到 G2")

        # ② S5-A 由 steward 代持
        pm = s.exec(select(Line).where(Line.name == "Paid Media")).first()
        if pm:
            changed = []
            for k, v in PAID_MEDIA_TARGET.items():
                if getattr(pm, k) != v:
                    setattr(pm, k, v)
                    changed.append(k)
            if changed:
                s.add(pm)
                print(f"[migrate] Paid Media 已更新：{', '.join(changed)}")
            else:
                print("[migrate] Paid Media 已是目标状态")
        else:
            print("[migrate] 警告：未找到 Paid Media 产线")

        # ③ 登记转正跟踪项
        exists = s.exec(
            select(WorkItem).where(WorkItem.title.contains("S5-A 转正"))
        ).first()
        if exists is None:
            s.add(WorkItem(**WORKITEM))
            print("[migrate] 新增交付项：S5-A 转正")
        else:
            print("[migrate] 转正跟踪项已存在")

        s.commit()
        print("[migrate] 0007 完成")


if __name__ == "__main__":
    migrate()
