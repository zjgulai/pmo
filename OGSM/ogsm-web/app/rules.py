"""OGSM 结构校验器。

这是这份实现的核心：把 OGSM-v1 文档 §7 的「修改与扩展规则」变成可执行断言。
校验在每次页面渲染前跑；失败项直接显示在页面顶部，不静默。

每条规则都对应一次真实踩过的坑：
- C1 ← B-01（G1 的 CAC 阈值与 O 差 20pp）
- C2 ← M11（「已完成」冒充经营结果）
- C3 ← M-05（8 个段 A 没有指标 / 没有 A）
- C4 ← 战略缺反证条件会一年后全部变成「还在做」
- C5 ← 没有基线的承诺不成立
"""
from dataclasses import dataclass, field

from sqlmodel import Session, select

from .models import (Baseline, Expert, Goal, Line, Metric, ResultVariable,
                     Strategy, WorkItem)

PROGRESS_WORDS = ("已完成", "进行中", "方案中", "上线", "交付")
ALLOWED_DECISION_USE = {"budget", "explain_only", "gate_only", "settlement"}


@dataclass
class Finding:
    code: str
    level: str  # error / warn
    message: str
    where: str = ""


@dataclass
class CheckResult:
    findings: list[Finding] = field(default_factory=list)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "error"]

    @property
    def warns(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "warn"]

    @property
    def passed(self) -> bool:
        return not self.errors

    def summary(self) -> str:
        if self.passed and not self.warns:
            return f"全部通过（{len(self.findings)} 项提示）" if self.findings else "全部通过"
        return f"{len(self.errors)} 错误 / {len(self.warns)} 警告"


def _metric(session: Session, metric_id: str) -> Metric | None:
    base = metric_id.split("@")[0]
    return session.exec(
        select(Metric).where(Metric.metric_id == base).order_by(Metric.version.desc())
    ).first()


def run_checks(session: Session) -> CheckResult:
    r = CheckResult()
    goals = session.exec(select(Goal)).all()
    strategies = session.exec(select(Strategy)).all()
    lines = session.exec(select(Line)).all()
    results = session.exec(select(ResultVariable)).all()

    # ── C1：每个 G 有且仅有 1 个结算主指标，且必须是 T1 层 ─────────────
    seen: dict[str, list[str]] = {}
    for g in goals:
        seen.setdefault(g.main_metric_id, []).append(g.code)
        m = _metric(session, g.main_metric_id)
        if m is None:
            r.findings.append(
                Finding("C1", "error", f"{g.code} 的结算主指标 {g.main_metric_id} 不在指标字典中", g.code)
            )
        elif m.layer != "T1":
            r.findings.append(
                Finding(
                    "C1",
                    "error",
                    f"{g.code} 的结算主指标 {g.main_metric_id} 属于 {m.layer} 层，只有 T1 可进 OGSM 结算",
                    g.code,
                )
            )
        elif m.decision_use != "budget":
            r.findings.append(
                Finding(
                    "C1",
                    "error",
                    f"{g.code} 的结算主指标 {g.main_metric_id} 的 decision_use={m.decision_use}，应为 budget",
                    g.code,
                )
            )
    for mid, codes in seen.items():
        if len(codes) > 1:
            r.findings.append(
                Finding("C1", "error", f"{mid} 被多个 G 共用（{', '.join(codes)}）——一个 G 只认一个数字", mid)
            )

    # ── C2：进度词不得出现在结果层 ─────────────────────────────────
    for g in goals:
        for fname, val in (("main_metric_id", g.main_metric_id), ("one_liner", g.one_liner)):
            if any(w in (val or "") for w in PROGRESS_WORDS):
                r.findings.append(
                    Finding("C2", "error", f"{g.code} 的 {fname} 出现进度词：{val}", g.code)
                )
    for rv in results:
        if any(w in (rv.target or "") for w in PROGRESS_WORDS):
            r.findings.append(
                Finding("C2", "error", f"{rv.code} 的目标值出现进度词：{rv.target}", rv.code)
            )

    # ── C3：每条产线必须有段 A 或对象级 A ──────────────────────────
    # business 层缺两者 = error（无人可问责）
    # support 层缺两者 = warn（文档允许：Echo 靠 taxonomy 版本问责，Daisy 靠对象级 A）
    for ln in lines:
        if ln.kind == "out":
            continue
        if not (ln.seg_a or ln.object_a):
            # 文档允许「段级 0 A + 备注写明问责载体」的支撑层（如 Echo 靠 taxonomy 版本）。
            # 判定必须读备注，而不是只看有没有 A —— 否则规则会把文档认可的形态判成缺失。
            has_carrier = bool((ln.note or "").strip())
            if ln.kind == "business":
                r.findings.append(
                    Finding(
                        "C3",
                        "error",
                        f"产线「{ln.name}」既无段 A 也无对象级 A —— 无法问责，季度裁决时只能进收缩名单",
                        ln.name,
                    )
                )
            elif not has_carrier:
                r.findings.append(
                    Finding(
                        "C3",
                        "warn",
                        f"支撑层「{ln.name}」未登记段 A 与对象级 A —— 需在备注写明问责载体（版本化对象 / 抽检一致率等）",
                        ln.name,
                    )
                )
        if ln.kind == "support" and not ln.consumer:
            r.findings.append(
                Finding("C3", "warn", f"支撑层「{ln.name}」未登记消费方，无法证明服务 ≥3 条业务线", ln.name)
            )
        if ln.kind == "support" and ln.consumer:
            n = len([c for c in ln.consumer.replace("、", ",").split(",") if c.strip()])
            if n < 3:
                r.findings.append(
                    Finding("C3", "warn", f"支撑层「{ln.name}」只登记 {n} 个消费方，规则要求 ≥3", ln.name)
                )

    # ── C4：每条战略必须有反证条件 ────────────────────────────────
    for s in strategies:
        if not (s.falsification or "").strip():
            r.findings.append(
                Finding("C4", "error", f"战略 {s.code}「{s.title}」没有反证条件——出现即撤回的判据缺失", s.code)
            )

    # ── C5：G 未锁基线不得视为已生效 ──────────────────────────────
    # 判据从「Goal.baseline_locked 这个 bool」改为「Baseline 表里是否真有非空数值」。
    # 理由：bool 是自报的，数值是可查的。前者可以被随手勾上，后者必须有人填。
    baselines = session.exec(select(Baseline)).all()
    bmap = {b.key: b for b in baselines}
    for g in goals:
        # 该 G 依赖哪些基线键（由 ResultVariable 的 baseline_key 推出）
        keys = [rv.baseline_key for rv in results if rv.goal_code == g.code]
        flat = [k.strip() for kk in keys for k in kk.replace("/", ",").split(",") if k.strip()]
        missing = [k for k in flat if not (bmap.get(k) and bmap[k].value)]
        if not g.baseline_locked or missing:
            r.findings.append(
                Finding(
                    "C5",
                    "warn",
                    f"{g.code} 基线未锁定"
                    + (f"（缺 {', '.join(missing)} 的数值）" if missing else "")
                    + "——T0 2026-11-30 前须用真实 12 周中位数写入",
                    g.code,
                )
            )

    # ── C5b：所有基线键都必须有值 ─────────────────────────────────
    for b in baselines:
        if not b.value:
            r.findings.append(
                Finding("C5b", "warn",
                        f"基线 {b.key}「{b.name}」未填数值（窗口 {b.window}，来源 {b.source_system or '未定'}）", b.key)
            )
        elif not b.locked_by:
            r.findings.append(
                Finding("C5b", "error",
                        f"基线 {b.key} 有数值但未记录锁定人——无人认账的基线不能用于考核", b.key)
            )

    # ── 附加：支撑层不得占 G 位 ───────────────────────────────────
    for ln in lines:
        if ln.kind == "support" and ln.layer in {"G1", "G2", "G3"}:
            r.findings.append(
                Finding("C6", "error", f"支撑层「{ln.name}」被挂在 {ln.layer} 上——底座不得占 G 位", ln.name)
            )

    # ── 附加：指标 decision_use 合法 ─────────────────────────────
    for m in session.exec(select(Metric)).all():
        if m.decision_use not in ALLOWED_DECISION_USE:
            r.findings.append(
                Finding("C7", "error", f"指标 {m.metric_id} 的 decision_use 非法：{m.decision_use}", m.metric_id)
            )
        if m.layer == "T3" and m.name in {"ROAS", "CPM", "CTR", "CVR", "频次"} and m.decision_use == "budget":
            r.findings.append(
                Finding("C7", "error", f"{m.metric_id}（{m.name}）属渠道内指标，禁止标为 budget", m.metric_id)
            )

    # ── C8：每个零段 A 的产线必须持对象级 A，否则无问责载体 ─────────
    # 文档允许「零段 A」，但要求它靠对象级 A（主键写入口）站立。
    # 判定：段 A 为空的业务产线，必须给出 object_a 与 object_a_key。
    for ln in lines:
        if ln.kind != "business" or ln.status == "out":
            continue
        if not ln.seg_a:
            if not (ln.object_a and ln.object_a_key):
                r.findings.append(
                    Finding(
                        "C8",
                        "error",
                        f"「{ln.name}」零段 A 且未登记对象级 A —— 两条问责线都没有，"
                        f"按 90 天裁决必进收缩名单。要么给段 A，要么点明它持哪个主键的写入口",
                        ln.name,
                    )
                )
            else:
                r.findings.append(
                    Finding(
                        "C8",
                        "warn",
                        f"「{ln.name}」零段 A，靠对象级 A（{ln.object_a_key}）站立 —— "
                        f"需在季度评审中证明该对象被 ≥1 个非 owner 消费",
                        ln.name,
                    )
                )

    # ── C9：业务产线必须有可追溯的建设载体 ─────────────────────────
    # 「有 OGSM 线、无建设证据」= 承诺了没做。这是资源与战略错配的一半。
    experts = session.exec(select(Expert)).all()
    by_line: dict[str, list[Expert]] = {}
    for e in experts:
        if e.line_name:
            by_line.setdefault(e.line_name, []).append(e)

    for ln in lines:
        if ln.kind == "out" or ln.status in {"out", "watch"}:
            continue
        carriers = by_line.get(ln.name, [])
        with_evidence = [e for e in carriers if (e.evidence_doc or "").strip()]
        if with_evidence:
            continue
        # Shopify 拆出的三条共享同一份报告证据：主线有证据时，子线降为警告
        sibling_ok = any(
            ln.name.startswith(sib) and any(
                (e.evidence_doc or "").strip() for e in by_line.get(x, [])
            )
            for sib in ("Shopify-",)
            for x in {"Shopify-DTC 转化", "Shopify-商品与定价", "Shopify-站点技术"}
        )
        if sibling_ok:
            r.findings.append(
                Finding(
                    "C9",
                    "warn",
                    f"产线「{ln.name}」无独立建设证据（与同组 Shopify 主线共用报告，但报告未分别覆盖）",
                    ln.name,
                )
            )
            continue
        r.findings.append(
            Finding(
                "C9",
                "error" if ln.is_p0 else "warn",
                f"产线「{ln.name}」无任何专家建设证据"
                + ("（P0 产线零证据，优先级最高）" if ln.is_p0 else ""),
                ln.name,
            )
        )

    # ── C10：每个专家必须映射到 OGSM 线，或在范围排除声明里点名 ───────
    # 「有建设证据、无 OGSM 线」= 做了没承诺。这是错配的另一半。
    for e in experts:
        if e.status == "excluded":
            if not (e.note or "").strip():
                r.findings.append(
                    Finding("C10", "error", f"专家「{e.name}」标为范围排除但未写理由", e.name)
                )
            continue
        if not e.line_name:
            r.findings.append(
                Finding("C10", "error", f"专家「{e.name}」有建设证据但未映射到任何 OGSM 线", e.name)
            )
        elif e.line_name not in {ln.name for ln in lines}:
            r.findings.append(
                Finding("C10", "error", f"专家「{e.name}」映射到不存在的产线「{e.line_name}」", e.name)
            )

    # ── C11：授予成熟度不得高于自报，且无消费方证据不得越过 M1 ────────
    _order = {"M0": 0, "M1": 1, "M2": 2, "M3": 3, "M4": 4}
    for e in experts:
        c, g = _order.get(e.maturity_claimed, 0), _order.get(e.maturity_granted, 0)
        if g > c:
            r.findings.append(
                Finding("C11", "error",
                        f"专家「{e.name}」授予 {e.maturity_granted} 高于自报 {e.maturity_claimed}", e.name)
            )
        if g >= 2:
            ln = next((x for x in lines if x.name == e.line_name), None)
            if not (ln and (ln.consumer or "").strip()):
                r.findings.append(
                    Finding("C11", "error",
                            f"专家「{e.name}」授予 {e.maturity_granted} 但所属产线无消费方登记——"
                            f"成熟度只能由消费方升级", e.name)
                )

    return r
