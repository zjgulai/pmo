#!/usr/bin/env python3
"""A 批：为 46 张 canonical 记忆建立显式语义链接（不依赖 LLM）。

用法：
    # 干跑：列出链接矩阵
    OGSM/ogsm-web/.venv/bin/python OGSM/ogsm-web/docs/memory/link_memories_to_graph.py

    # 执行：幂等写入 abi-pmo
    OGSM/ogsm-web/.venv/bin/python OGSM/ogsm-web/docs/memory/link_memories_to_graph.py --run
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

WEB = Path(__file__).resolve().parents[2]
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WEB))
from app import seed  # noqa: E402

SPACE = "abi-pmo"

# (source, relation_type, target, reason)
CORE_LINKS = [
    ("pmo-l1-identity", "SUPPORTS", "pmo-l1-redlines", "身份与红线同属核心准则，红线约束身份行为"),
    ("pmo-l1-identity", "SUPPORTS", "pmo-l1-boundary", "身份与仓库边界共同定义 Agent 的活动范围"),
    ("pmo-l3-progress", "DEPENDS_ON", "pmo-l2-misuse12", "进度不是结果的判定依赖 M11 口径"),
    ("pmo-l3-feishu-select", "DEPENDS_ON", "pmo-l3-mime", "飞书表同步与 Library 解析都依赖字段/格式稳定性"),
    ("pmo-l3-mime", "TRACKS", "pmo-l1-boundary", "MIME 解析规范属于仓库数据纪律"),
    ("pmo-l3-evidence-gate", "EVIDENCED_BY", "pmo-l2-evidence", "证据硬门禁由 L0–L4 证据分级支撑"),
    ("pmo-l3-backup", "MITIGATES", "pmo-l1-boundary", "备份防线缓解生产数据被误写的风险"),
    ("pmo-l3-roas", "DEPENDS_ON", "pmo-l2-misuse12", "平台 ROAS 误用对应 M01/M10/M12"),
    ("pmo-l3-adspend", "PARTICIPATES_IN", "pmo-l2-handoff6", "加投前检查属于流量承接与库存护栏链"),
    ("pmo-l3-voc", "PARTICIPATES_IN", "pmo-l2-portfolio18", "VOC 增量管线是 G2 产线能力"),
    ("pmo-l3-stage-inflation", "EVIDENCED_BY", "pmo-l2-stage4", "Vicky 挤水分是四阶标尺 50% 硬门禁的实证"),
    ("pmo-l3-ai-answer", "EVIDENCED_BY", "pmo-l2-keys9", "AI 提及/推荐判定依赖 ai_answer_snapshot_id"),
    ("pmo-l3-claim", "GATED_BY", "pmo-l2-gates", "事实原子发布必须经 Claim/授权 Gate"),
    ("pmo-l2-ogsm-generations", "DECOMPOSES_TO", "pmo-l2-g1g3", "两代 OGSM 卡片解释 G1–G3 的版本边界"),
    ("pmo-l2-ogsm-generations", "DECOMPOSES_TO", "pmo-l2-o-r1r4", "两代 OGSM 卡片解释 O 与 R1–R4 的版本边界"),
    ("pmo-l2-ogsm-generations", "SUPPORTS", "pmo-l2-portfolio18", "两代 OGSM 是 18 项产线登记的上位口径"),
    ("pmo-l2-g1g3", "MEASURED_BY", "pmo-l2-metric-t1t5", "G1–G3 必须由 T1 结算指标度量"),
    ("pmo-l2-g1g3", "DEPENDS_ON", "pmo-l2-misuse12", "G 结算需排除 12 条指标误用"),
    ("pmo-l2-o-r1r4", "MEASURED_BY", "pmo-l2-metric-t1t5", "O 的 R1–R4 结果变量落到 T1–T5 指标层"),
    ("pmo-l2-metric-t1t5", "GATED_BY", "pmo-l2-misuse12", "指标分层受 12 条误用检测约束"),
    ("pmo-l2-portfolio18", "DEPENDS_ON", "pmo-l2-keys9", "18 项产线的对象级 A 依赖 9 主键"),
    ("pmo-l2-handoff6", "GATED_BY", "pmo-l2-gates", "6 条交接链的资产/脚本必须过三道 Gate"),
    ("pmo-l2-handoff6", "EVIDENCED_BY", "pmo-l2-evidence", "交接链验收依赖 L0–L4 证据与 measuredActions"),
    ("pmo-l2-stage4", "GATED_BY", "pmo-l2-gates", "Stage 3/4 的自进化脚本需过三道路径与返工率门禁"),
    ("pmo-l2-stage4", "TRACKS", "pmo-l2-cadence", "四阶进度按 PMO 周/月/季节奏复核"),
    ("pmo-l2-quadrant", "TRACKS", "pmo-l2-cadence", "四象限续投在季度校准会执行"),
    ("pmo-l2-keys9", "EVIDENCED_BY", "pmo-l2-evidence", "主键对象需要 evidence_url 与回执支撑"),
    ("pmo-l2-cadence", "SUPPORTS", "pmo-l2-quadrant", "管理节奏为四象限裁决提供会议与证据节奏"),
    ("pmo-l4-portfolio", "SUPPORTS", "pmo-l2-ogsm-generations", "14 Agent 组合总览是两代 OGSM 的交付侧快照"),
    ("pmo-l4-portfolio", "SUPPORTS", "pmo-l2-portfolio18", "14 Agent 组合总览是 18 项登记的交付侧视图"),
    ("pmo-l4-portfolio", "EVIDENCED_BY", "pmo-l4-capabilities", "组合总览的数字由 49 项能力基线回算"),
    ("pmo-l4-portfolio", "TRACKS", "pmo-l4-waves-risks", "组合总览按 Wave 与风险清单更新"),
]

ANCHORS = [
    ("pmo-l2-ogsm-generations", "SUPPORTS", "属于两代 OGSM 的策略归类"),
    ("pmo-l2-g1g3", "CONTRIBUTES_TO", "服务 OGSM v1 的结果目标"),
    ("pmo-l2-portfolio18", "PARTICIPATES_IN", "是 18 项登记中的产品载体"),
    ("pmo-l2-handoff6", "PARTICIPATES_IN", "参与 6 条跨岗交接链"),
    ("pmo-l2-stage4", "EVOLVES_IN", "按四阶自进化标尺演进"),
    ("pmo-l4-waves-risks", "EVOLVES_IN", "属于 Wave 1–3 排期与风险清单"),
    ("pmo-l4-capabilities", "DELIVERS", "交付 49 项能力中的对应项"),
]


def build_links():
    links = list(CORE_LINKS)
    for p in seed.PROJECTS:
        src = f"pmo-l4-{p['slug']}"
        for target, rel, reason in ANCHORS:
            links.append((src, rel, target, f"{p['expert_name']}：{reason}"))
    # 去重（同 source/target/type 只保留一条）
    seen, out = set(), []
    for s, r, t, why in links:
        key = (s, r, t)
        if key in seen:
            continue
        seen.add(key)
        out.append((s, r, t, why))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    links = build_links()
    print(f"链接总数：{len(links)}（项目卡 {len(seed.PROJECTS)} × {len(ANCHORS)} + 核心 {len(CORE_LINKS)}，去重后）")
    if not args.run:
        for s, r, t, why in links:
            print(f"{s} --{r}--> {t}  # {why}")
        return
    ok, fail = 0, []
    for s, r, t, why in links:
        cmd = ["nmem", "memories", "link", "add", "--space", SPACE,
               "--type", r, "--reason", why, s, t]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if res.returncode == 0:
            ok += 1
        else:
            fail.append((s, r, t, res.stderr.strip()[:160]))
    print(f"完成：{ok} 成功 / {len(fail)} 失败")
    for f in fail[:20]:
        print("FAIL", f)


if __name__ == "__main__":
    main()
