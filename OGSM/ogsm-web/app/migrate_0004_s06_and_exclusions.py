"""迁移 0004：应用 2026-11-02 两项决议。

1. 新增支撑层 S0.6 知识生产（Know），支撑 5→6 条，登记项 18→19
2. Sage 确认范围排除（status=excluded，已写理由）
3. 把「8 主键」统一为「9 主键」（第 9 键 ai_answer_snapshot_id 已于本日增补）

幂等：逐条比对目标值，只改不一致的字段。
"""
from sqlmodel import Session, select

from .db import engine, init_db
from .models import Expert, Line, Strategy

S06 = {
    "code": "S0.6",
    "goal_code": "S0",
    "title": "知识生产：把资料变成可执行、可溯源的技能",
    "one_liner": "每条技能规则都能反查回原文位置；发布或降级必须过独立门禁并留痕",
    "falsification": "抽检 30 条技能规则，出处反查失败 >1 条；或门禁三（效用 A/B）连续两季未检出任何负迁移",
    "owner": "Know",
    "sort": 17,
}

KNOW_LINE = {
    "name": "Know（知识生产）",
    "layer": "support",
    "kind": "support",
    "seg_a": None,
    "object_a": "Know",
    "object_a_key": "IR 对象 + 技能发布门禁",
    "strategy_code": "S0.6",
    "maturity": "M1",
    "consumer": "内容产线, 守衡, Paid Media, CS, Shopify-DTC 转化, Source",
    "note": "2026-11-02 新增支撑层。问责靠 IR 对象逐字引文 + 三道门禁留痕，不占主键位",
}

KNOW_EXPERT = {
    "line_name": "Know（知识生产）",
    "status": "aligned",
    "gap": "门禁三（效用 A/B）只在技术书场景验证过，未在品牌营销 SOP 上验证",
    "action": "立为支撑层 S0.6 知识生产；其门禁三「装上比不装好」是全库最缺的机制，可反哺其他产线",
    "note": "2026-11-02 决议：新增 S0.6，支撑层 5→6 条，登记项 18→19",
}

SAGE_EXPERT = {
    "status": "excluded",
    "action": "明确范围排除，作为独立产品线管理；不塞进任何 G 或支撑层",
    "note": "2026-11-02 决议：范围排除。Sage 服务 53 位跨境专家的核算工作台，不满足「服务 ≥3 条品牌营销业务线」",
}

EIGHT_TO_NINE = [
    ("Line", "Source", "object_a_key", "8 主键落库", "9 主键落库"),
]


def _apply(obj, target: dict, label: str) -> list[str]:
    changed = []
    for k, v in target.items():
        if getattr(obj, k) != v:
            setattr(obj, k, v)
            changed.append(k)
    if changed:
        print(f"[migrate] {label} 已更新：{', '.join(changed)}")
    return changed


def migrate() -> None:
    init_db()
    with Session(engine) as s:
        # ① S0.6 战略
        st = s.exec(select(Strategy).where(Strategy.code == "S0.6")).first()
        if st is None:
            s.add(Strategy(**S06))
            print("[migrate] 新增战略 S0.6")
        else:
            _apply(st, S06, "战略 S0.6")

        # ② Know 产线（支撑层第 6 条）
        ln = s.exec(select(Line).where(Line.name == KNOW_LINE["name"])).first()
        if ln is None:
            s.add(Line(**KNOW_LINE))
            print("[migrate] 新增产线「Know（知识生产）」")
        else:
            _apply(ln, KNOW_LINE, "产线 Know")

        # ③ Know 专家：从游离改为已归位
        ko = s.exec(select(Expert).where(Expert.name.like("Know%"))).first()
        if ko:
            _apply(ko, KNOW_EXPERT, "专家 Know")
        else:
            print("[migrate] 警告：未找到专家 Know")

        # ④ Sage 确认排除
        sg = s.exec(select(Expert).where(Expert.name == "Sage")).first()
        if sg:
            _apply(sg, SAGE_EXPERT, "专家 Sage")
        else:
            print("[migrate] 警告：未找到专家 Sage")

        # ⑤ 8 主键 → 9 主键
        for model_name, key, field, old, new in EIGHT_TO_NINE:
            model = {"Line": Line}[model_name]
            row = s.exec(select(model).where(model.name == key)).first()
            if row and getattr(row, field) == old:
                setattr(row, field, new)
                s.add(row)
                print(f"[migrate] {model_name} {key}.{field}：{old} → {new}")

        s.commit()
        print("[migrate] 0004 完成")


if __name__ == "__main__":
    migrate()
