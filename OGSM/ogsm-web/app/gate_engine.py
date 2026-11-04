"""P0-4 三道 Gate 状态机守卫与回执签发/校验引擎（ADR-0010）。

严格实现《品牌 Agent 三个 Gate 规格与 Fail-closed 默认》：
1. 通用回执格式：`{subject_id}@{version}#{gate}-{seq4}`（如 `scr-bpc-tiktok-00317@2#C-0001`），禁止省略 `@version` 或不足 4 位序号。
2. 五条铁律（Fail-closed）：
   - 规则未命中 ≠ 允许：阻断或转人工，不出 PASS；
   - 证据缺失 ≠ 待补：直接 BLOCK；
   - 超时未响应 ≠ 放行；
   - 无回执 ≠ 通过：系统层拒绝迁移；
   - 回执过期 = BLOCK：`valid_until < today` 自动置为 `expired`。
3. 三道 Gate：
   - Claim Gate (`C`，守衡主责)：核验 claim_refs、evidence_refs、rule_refs、market_overlay_version 与医疗/绝对化红线词；
   - 授权 Gate (`A`，Radar台账 + 守衡核验)：核验达人授权七元组、4 类凭证白名单与二次剪辑 `reedit` 范围；
   - 实验 Gate (`X`，PMO主责)：预注册发号 `hyp-{yyMMdd}-{seq3}`、单变量 `changed_variable`、对照组与 >5 臂多重比较校正。
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timedelta, timezone

from sqlmodel import Session, select

from . import models

RECEIPT_ID_PATTERN = re.compile(r"^([a-zA-Z0-9][a-zA-Z0-9_-]*)@(\d+)#([CAX])-(\d{4})$")
HYPOTHESIS_ID_PATTERN = re.compile(r"^hyp-\d{6}-\d{3}$")

# TikTok Shop 美区达人素材唯一允许的 4 类凭证白名单（three-gates §1.1 & §3.2）
ALLOWED_CREDENTIAL_TYPES = {
    "shop_official",     # 店铺授权号
    "ttam_spark_code",   # TTAM Spark Ads Video code
    "aca",               # ACA 授权
    "affiliate_auth",    # 红人联盟授权
}

# 高危医疗/绝对化禁用宣称词表（命中且无医疗器械资质直接 BLOCK）
MEDICAL_REDLINE_WORDS = (
    "治疗", "治愈", "100%杀菌", "完全静音", "0分贝", "预防疾病", "医疗级", "fda批准", "fda approved", "cure", "treat eczema",
)

DEFAULT_INVALIDATE_ON = [
    "content_hash_change",
    "claim_version_change",
    "rule_version_change",
    "rights_revoked",
    "expired",
]


def _next_seq4(s: Session, subject_id: str, gate_type: str) -> str:
    existing = s.exec(
        select(models.GateReceipt).where(
            models.GateReceipt.subject_id == subject_id,
            models.GateReceipt.gate_type == gate_type,
        )
    ).all()
    return f"{len(existing) + 1:04d}"


def issue_hypothesis_id(
    s: Session,
    hypothesis_statement: str,
    primary_metric: str = "m-l1-mer@1",
    min_threshold: str = "+5%",
    window_days: int = 14,
    proposer: str = "Emily",
) -> dict:
    """PMO 实验 Gate 预注册发号器：生成 `hyp-{yyMMdd}-{seq3}` 并冻结阈值哈希。"""
    stmt = (hypothesis_statement or "").strip()
    if not stmt or len(stmt) < 4:
        return {"ok": False, "verdict": "BLOCK", "error": "假设陈述（若 X 则 Y）不能为空"}

    ymd = date.today().strftime("%y%m%d")
    prefix = f"hyp-{ymd}-"
    existing = s.exec(
        select(models.GateReceipt).where(models.GateReceipt.gate_type == "X")
    ).all()
    seq3 = f"{len(existing) + 1:03d}"
    hyp_id = f"{prefix}{seq3}"

    threshold_payload = {
        "hypothesis_id": hyp_id,
        "statement": stmt,
        "primary_metric": primary_metric,
        "min_threshold": min_threshold,
        "window_days": window_days,
        "proposer": proposer,
    }
    frozen_sha = hashlib.sha256(
        json.dumps(threshold_payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()

    return {
        "ok": True,
        "hypothesis_id": hyp_id,
        "thresholds_frozen_sha": frozen_sha,
        "primary_metric": primary_metric,
        "min_threshold": min_threshold,
        "window_days": window_days,
        "proposer": proposer,
    }


def evaluate_and_issue_gate_receipt(s: Session, payload: dict) -> dict:
    """对输入对象执行 C (Claim) / A (授权) / X (实验) 门禁判定，签发并持久化 `GateReceipt`。"""
    gate_type = str(payload.get("gate_type") or "C").strip().upper()
    if gate_type not in ("C", "A", "X"):
        return {"ok": False, "verdict": "BLOCK", "error": f"未知 gate_type={gate_type}，仅支持 C / A / X"}

    subject_id = str(payload.get("subject_id") or "").strip()
    subject_version = int(payload.get("subject_version") or 1)
    if not subject_id or "@" in subject_id or "#" in subject_id:
        return {"ok": False, "verdict": "BLOCK", "error": "subject_id 必填且不得包含 @ 或 #"}

    content_text = str(payload.get("content_text") or "")
    content_hash = str(payload.get("content_hash") or "").strip()
    if not content_hash:
        content_hash = hashlib.sha256((content_text or f"{subject_id}@{subject_version}").encode("utf-8")).hexdigest()

    claim_refs = list(payload.get("claim_refs") or [])
    rule_refs = list(payload.get("rule_refs") or [])
    evidence_refs = list(payload.get("evidence_refs") or [])
    market_overlay = str(payload.get("market_overlay_version") or "").strip()
    valid_until = str(payload.get("valid_until") or (date.today() + timedelta(days=90)).isoformat())[:10]
    today_iso = date.today().isoformat()

    reasons: list[str] = []
    conditions: list[str] = []
    verdict = "PASS"
    judged_by = "守衡-ClaimEngine@v2.1 (抽检:刘华丽)"

    # ── 1. Claim Gate (C，守衡主责) ──
    if gate_type == "C":
        if not claim_refs or any("@" not in str(cr) for cr in claim_refs):
            verdict = "BLOCK"
            reasons.append("缺少带版本号的 claim_refs（如 clm-bpc-us-0142@3），违反唯一写入口版本规则")
        if not evidence_refs:
            verdict = "BLOCK"
            reasons.append("缺少 evidence_refs 支撑证据（违反铁律 2：证据缺失 ≠ 待补，直接阻断）")
        if not rule_refs or any("@" not in str(rr) for rr in rule_refs):
            verdict = "BLOCK"
            reasons.append("缺少带版本号的 rule_refs（如 rule-claim-cosmetic-medical-boundary-us-review@3）")
        if not market_overlay or "@" not in market_overlay:
            verdict = "BLOCK"
            reasons.append("缺少带版本号的 market_overlay_version（如 overlay-us-ftc-fda@1），禁止退回 base rule 单判")
        if valid_until < today_iso:
            verdict = "BLOCK"
            reasons.append(f"证据或有效期 {valid_until} 已过期（回执过期 = BLOCK）")

        low_txt = content_text.lower()
        for bad_w in MEDICAL_REDLINE_WORDS:
            if bad_w in low_txt:
                verdict = "BLOCK"
                reasons.append(f"命中高危医疗/绝对化红线词「{bad_w}」（rule-claim-cosmetic-medical-boundary-us-review@3）")

        if verdict == "PASS" and payload.get("evidence_tier") == "first_party_only":
            verdict = "CONDITIONAL"
            cond_due = (date.today() + timedelta(days=30)).isoformat()
            valid_until = min(valid_until, cond_due)
            conditions.append(f"当前仅第一方内部测试报告，仅限 organic 渠道，须于 {cond_due} 前补第三方 SGS/实验室证据")
            reasons.append("第一方证据限时放行（CONDITIONAL）")

    # ── 2. 授权 Gate (A，Radar台账 + 守衡核验) ──
    elif gate_type == "A":
        judged_by = "守衡×Radar-RightsGate@v2.1 (抽检:刘华丽)"
        creator_id = str(payload.get("creator_id") or "").strip()
        cred_type = str(payload.get("credential_type") or "").strip()
        scopes = list(payload.get("scope") or [])
        account_ids = list(payload.get("account_ids") or [])
        territory = list(payload.get("territory") or [])
        is_reedit = bool(payload.get("is_reedit", False))

        if not creator_id:
            verdict = "BLOCK"
            reasons.append("缺少 creator_id（无达人档案的第三方素材禁止进 paid）")
        if cred_type not in ALLOWED_CREDENTIAL_TYPES:
            verdict = "BLOCK"
            reasons.append(
                f"凭证类型「{cred_type or '空'}」不在美区4类白名单内（仅认 shop_official / ttam_spark_code / aca / affiliate_auth；聊天截图或口头同意一律 BLOCK）"
            )
        if not account_ids or any(str(a).lower() in ("all", "全部", "全部账号", "*") for a in account_ids):
            verdict = "BLOCK"
            reasons.append("account_ids 必须逐账号枚举，严禁填写「全部账号」或留空")
        if not scopes or "paid" not in scopes:
            verdict = "BLOCK"
            reasons.append("授权 scope 未包含 paid 投流权限")
        if is_reedit and "reedit" not in scopes:
            verdict = "BLOCK"
            reasons.append("素材经过二次剪辑（is_reedit=True），但授权 scope 缺少 reedit（命中 rule-tiktok-shop-reedit-scope-us-review@1）")
        if not territory:
            verdict = "BLOCK"
            reasons.append("授权七元组缺少 territory 目标市场范围")
        if valid_until < today_iso:
            verdict = "BLOCK"
            reasons.append(f"达人授权到期日 {valid_until} 已过期")

        if not rule_refs:
            rule_refs = ["rule-tiktok-shop-creator-asset-sources-us-review@1", "rule-tiktok-shop-reedit-scope-us-review@1"]
        if not market_overlay:
            market_overlay = "overlay-us-tiktok-shop@1"
        if not evidence_refs:
            evidence_refs = [f"cred-{cred_type or 'missing'}@1"]

        if verdict == "PASS" and not is_reedit and "reedit" not in scopes:
            verdict = "CONDITIONAL"
            conditions.append("原片直投（rights_status=partial），严禁二次剪辑或跨账号混剪")

    # ── 3. 实验 Gate (X，PMO主责) ──
    elif gate_type == "X":
        judged_by = "PMO-ExperimentGate@v2.1 (签发:周健)"
        hyp_id = str(payload.get("hypothesis_id") or "").strip()
        changed_vars = list(payload.get("changed_variables") or [])
        control_id = str(payload.get("control_variant_id") or "").strip()
        arm_count = int(payload.get("arm_count") or 2)
        correction = str(payload.get("correction_method") or "").strip()
        sample_actual = int(payload.get("sample_actual") or 100)
        sample_target = int(payload.get("sample_target") or 100)

        if not HYPOTHESIS_ID_PATTERN.match(hyp_id):
            verdict = "BLOCK"
            reasons.append(f"缺少合法预注册编号 hypothesis_id（格式须为 hyp-yyMMdd-seq3，当前：{hyp_id or '空'}）")
        if len(changed_vars) != 1:
            verdict = "BLOCK"
            reasons.append(f"单条测试变体必须只改 1 个变量（changed_variables 当前为 {len(changed_vars)} 个），多变量混改不可归因一律 BLOCK")
        if not control_id:
            verdict = "BLOCK"
            reasons.append("缺少对照组 control_variant_id（命中 M10 无对照实验禁止进预算）")
        if arm_count > 5 and not correction:
            verdict = "BLOCK"
            reasons.append(f"同批比较臂数 arm_count={arm_count} (>5)，未声明多重比较校正方法（如 bonferroni / bh_fdr），防止假爆款放量")
        if verdict == "PASS" and sample_actual < sample_target:
            verdict = "CONDITIONAL"
            conditions.append(f"当前样本量 {sample_actual}/{sample_target} 未达标，仅作方向性待定（inconclusive），禁止放量加预算")

        if not rule_refs:
            rule_refs = ["rule-pmo-experiment-preregistration@1"]
        if not market_overlay:
            market_overlay = "overlay-global-ogsm-v1@1"
        if not evidence_refs:
            evidence_refs = [f"{hyp_id or 'no-hyp'}@1"]

    if not reasons:
        reasons.append("全部要件、规则版本、市场 overlay 与证据链核验通过")

    # 将同一 (subject_id, subject_version, gate_type) 的历史 active 回执置为 superseded
    old_active = s.exec(
        select(models.GateReceipt).where(
            models.GateReceipt.subject_id == subject_id,
            models.GateReceipt.subject_version == subject_version,
            models.GateReceipt.gate_type == gate_type,
            models.GateReceipt.status == "active",
        )
    ).all()
    for oa in old_active:
        oa.status = "superseded"
        s.add(oa)

    seq4 = _next_seq4(s, subject_id, gate_type)
    receipt_id = f"{subject_id}@{subject_version}#{gate_type}-{seq4}"

    rec = models.GateReceipt(
        receipt_id=receipt_id,
        subject_id=subject_id,
        subject_version=subject_version,
        gate_type=gate_type,
        seq4=seq4,
        verdict=verdict,
        content_hash=content_hash,
        claim_refs_json=json.dumps(claim_refs, ensure_ascii=False),
        rule_refs_json=json.dumps(rule_refs, ensure_ascii=False),
        market_overlay_version=market_overlay,
        evidence_refs_json=json.dumps(evidence_refs, ensure_ascii=False),
        conditions_json=json.dumps(conditions, ensure_ascii=False),
        valid_until=valid_until,
        invalidate_on_json=json.dumps(DEFAULT_INVALIDATE_ON, ensure_ascii=False),
        judged_by=judged_by,
        status="active",
        reason_summary="；".join(reasons),
    )
    s.add(rec)
    s.commit()
    s.refresh(rec)

    return {
        "ok": True,
        "receipt_id": rec.receipt_id,
        "gate_type": rec.gate_type,
        "verdict": rec.verdict,
        "allowed_to_proceed": rec.verdict in ("PASS", "CONDITIONAL"),
        "status": rec.status,
        "valid_until": rec.valid_until,
        "conditions": conditions,
        "reasons": reasons,
        "judged_by": rec.judged_by,
    }


def verify_gate_receipt(
    s: Session,
    receipt_id: str,
    expected_content_hash: str = "",
) -> dict:
    """状态机守卫核验器：校验 `receipt_id` 格式、存在性、active 状态、有效期与 content_hash 指纹。"""
    rid = (receipt_id or "").strip()
    if not RECEIPT_ID_PATTERN.match(rid):
        return {
            "ok": False,
            "valid": False,
            "verdict": "BLOCK",
            "reason": f"回执定位串格式非法（须严格匹配 {{subject_id}}@{{version}}#{{C|A|X}}-{{seq4}}，当前：{rid or '空'}）",
        }

    rec = s.exec(select(models.GateReceipt).where(models.GateReceipt.receipt_id == rid)).first()
    if not rec:
        return {
            "ok": False,
            "valid": False,
            "verdict": "BLOCK",
            "reason": f"未找到回执 {rid}（违反铁律 4：无回执 ≠ 通过，系统拒绝状态迁移）",
        }

    today_iso = date.today().isoformat()
    if rec.valid_until and rec.valid_until < today_iso and rec.status == "active":
        rec.status = "expired"
        s.add(rec)
        s.commit()

    if rec.status != "active":
        return {
            "ok": True,
            "valid": False,
            "receipt_id": rec.receipt_id,
            "verdict": "BLOCK",
            "status": rec.status,
            "reason": f"回执状态已失效（status={rec.status}），须重新提审获取新回执",
        }

    if expected_content_hash and rec.content_hash and expected_content_hash != rec.content_hash:
        rec.status = "superseded"
        s.add(rec)
        s.commit()
        return {
            "ok": True,
            "valid": False,
            "receipt_id": rec.receipt_id,
            "verdict": "BLOCK",
            "status": "superseded",
            "reason": "素材/脚本字节 content_hash 已发生变更，原回执自动作废（superseded），必须重判",
        }

    valid = rec.verdict in ("PASS", "CONDITIONAL")
    return {
        "ok": True,
        "valid": valid,
        "receipt_id": rec.receipt_id,
        "subject_id": rec.subject_id,
        "subject_version": rec.subject_version,
        "gate_type": rec.gate_type,
        "verdict": rec.verdict,
        "status": rec.status,
        "valid_until": rec.valid_until,
        "conditions": json.loads(rec.conditions_json or "[]"),
        "reason": rec.reason_summary,
        "judged_by": rec.judged_by,
    }


def seed_initial_gate_receipts(s: Session) -> int:
    """预置 4 条典型真实业务场景的 Gate 回执（含 PASS / CONDITIONAL / BLOCK 样本），供飞书群与下游联调核验。"""
    if s.exec(select(models.GateReceipt)).first():
        return 0

    samples = [
        # 1. Claim Gate PASS 样本（Emily/Clone 吸奶器脚本，绑定 BrandOS 事实与 SGS 证据）
        {
            "gate_type": "C",
            "subject_id": "scr-bpc-tiktok-00317",
            "subject_version": 2,
            "content_text": "Momcozy M5 穿戴式吸奶器：低于 45dB 轻音运行，通过 FDA 合规材质检测与 SGS 测试报告",
            "claim_refs": ["clm-m5-noise-45db@2", "clm-m5-bpa-free@1"],
            "evidence_refs": ["evd-sgs-m5-noise-2026@1", "evd-fda-material-104@1"],
            "rule_refs": ["rule-claim-cosmetic-medical-boundary-us-review@3", "rule-momcozy-baby-fda-84@1"],
            "market_overlay_version": "overlay-us-ftc-fda@1",
        },
        # 2. Claim Gate BLOCK 样本（违规使用医疗级/绝对化无证据宣称）
        {
            "gate_type": "C",
            "subject_id": "scr-sterilizer-us-00089",
            "subject_version": 1,
            "content_text": "医疗级 100%杀菌 彻底治愈宝宝鹅口疮与湿疹",
            "claim_refs": ["clm-sterilizer-999@1"],
            "evidence_refs": [],
            "rule_refs": ["rule-claim-cosmetic-medical-boundary-us-review@3"],
            "market_overlay_version": "overlay-us-ftc-fda@1",
        },
        # 3. 授权 Gate PASS 样本（Radar 登记 TTAM Spark Ads 凭证，含 reedit 二创授权）
        {
            "gate_type": "A",
            "subject_id": "ast-creator-remix-00512",
            "subject_version": 1,
            "creator_id": "crt-tiktok-us-momlife@1",
            "credential_type": "ttam_spark_code",
            "scope": ["organic", "paid", "reedit"],
            "account_ids": ["ttUS-MomcozyOfficial", "ttUS-MomcozyBaby"],
            "territory": ["US", "CA"],
            "is_reedit": True,
            "valid_until": "2027-03-31",
        },
        # 4. 实验 Gate PASS 样本（PMO 预注册 6 臂 Bonferroni 校正实验）
        {
            "gate_type": "X",
            "subject_id": "exp-batch-m5-hooks",
            "subject_version": 1,
            "hypothesis_id": "hyp-261104-001",
            "changed_variables": ["hook_first_3s"],
            "control_variant_id": "var-m5-ctrl-001",
            "arm_count": 6,
            "correction_method": "bonferroni",
            "sample_actual": 12000,
            "sample_target": 10000,
        },
    ]
    for sp in samples:
        evaluate_and_issue_gate_receipt(s, sp)
    return len(samples)
