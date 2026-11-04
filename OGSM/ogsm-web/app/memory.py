"""PMO 持久记忆检索与专家规则知识库（读侧轻量 Recall + 容器内置 Canonical 兜底）。

设计约束（SOP §一.4 / §五.4 & ADR-0009）：
- 严格 3 秒超时；失败、离线、无匹配时静默降级，绝不阻塞主链路。
- 优先调用宿主 `nmem` CLI 检索 `abi-pmo` 空间；若在 Docker 容器内无 `nmem` 二进制，则自动使用内置的 Canonical 四层治理记忆索引，确保飞书 `@PMO` 专家问答在任何环境下 100% 具备完整的红线、主键、Gate、交接链与指标防作弊知识。
"""
from __future__ import annotations

import json
import os
import subprocess

DEFAULT_SPACE = "abi-pmo"

# 内置 Canonical 核心治理记忆池（与 abi-pmo 空间 46 张四层记忆卡同源同步，供容器内零外部依赖高速检索）
BUILTIN_CANONICAL_MEMORIES: list[dict[str, str | list[str]]] = [
    {
        "id": "pmo-l1-redlines",
        "title": "PMO 八条操作红线与决策优先级",
        "keywords": ["红线", "原则", "规则", "roas", "gmv", "mention", "ave", "基线", "回执", "证据", "达成", "预算"],
        "content": (
            "决策优先级：事实 > 证据 > 承诺 > 交付 > 叙事 > 流量。\n"
            "八条操作红线：① 一个 G 只认一个唯一结算数字（G1自然新客CAC / G2边际贡献毛利MER / G3 90天同品类复购率），其余均为解释变量；"
            "② 进度不是结果（已完成/进行中/方案中只进交付台账，永不进M栏）；③ 没有基线（T0=2026-11-30）的承诺不成立；"
            "④ 无 Gate 回执不等于通过（评审会/群消息/老板特批均不构成回执）；⑤ 不编数，缺数据标未验证；"
            "⑥ 严禁把平台归因ROAS、平台GMV、mention次数、AVE当经营结论（命中M01/M04/M05误用）；"
            "⑦ 零跨库写入，只读14个工作台API/报告；⑧ 任何已验证状态必须挂载 evidence_url。"
        ),
    },
    {
        "id": "pmo-l2-misuse12",
        "title": "12 条指标误用拦截规则 (M01–M12)",
        "keywords": ["误用", "指标", "roas", "ltv", "复购", "sov", "ave", "cvr", "gmv", "退货率", "a/b", "实验", "payback", "预算", "加预算", "m01"],
        "content": (
            "12条禁止进预算或经营结论的指标误用：\n"
            "M01 平台ROAS当经营结论（必须用全局MER与边际ROAS） · M02 营收口径算LTV（必须用贡献毛利口径） · "
            "M03 全店复购掩盖品类（必须看同品类90天复购） · M04 mention次数当SOV（必须用来源加权SOV且与净情感同报） · "
            "M05 AVE当PR价值 · M06 讲师宣称当基准 · M07 全店CVR归因单条素材 · M08 含运含税GMV与净GMV混算 · "
            "M09 30天与90天退货率混比 · M10 样本不足或无hypothesis_id的A/B测试进预算 · M11 交付进度%当经营结果 · M12 平台归因窗口算CAC payback。"
        ),
    },
    {
        "id": "pmo-l2-keys9",
        "title": "9 大全域唯一主键契约 (Key Registry)",
        "keywords": ["主键", "schema", "字段", "id", "sku_id", "order_id", "claim_id", "evidence_id", "variant_id", "script_id", "creator_id", "event_id", "ai_answer_snapshot_id", "编码", "数据架构"],
        "content": (
            "9大跨Agent唯一主键（严禁各项目自造编码）：\n"
            "1) order_id / 2) sku_id（Source主责落库，含DataPilot 468个SKU品类漂移修正与BrandOS 315 SKU字典，解Vicky品线0%与Echo绑定2/56之困）；\n"
            "3) claim_id（Daisy/asset唯一签发，编码 clm-...@{version}） / 4) evidence_id（实验室报告/Vine评论快照，绑定守衡Claim Gate）；\n"
            "5) script_id（Emily唯一写入口） / 6) variant_id（Clone Recipe唯一写入口，单条脚本只改一个changed_variable）；\n"
            "7) creator_id（Radar唯一登记源，附带授权七元组） / 8) event_id（Signal唯一写入口，跨Echo/Vicky/Signal三群去重告警）；\n"
            "9) ai_answer_snapshot_id（GEO唯一写入口，编码 aia_{ULID26}，存Perplexity/ChatGPT/Rufus回答快照）。"
        ),
    },
    {
        "id": "pmo-l2-gates3",
        "title": "三道系统级状态机守卫门禁 (Three Gates & Receipt)",
        "keywords": ["gate", "门禁", "回执", "receipt", "守衡", "合规", "授权", "二创", "reedit", "实验", "hypothesis_id", "放行", "block"],
        "content": (
            "三条Gate均为状态机守卫，输出唯一回执 {subject_id}@{version}#{gate}-{seq4}，无回执在系统层直接拒绝迁移（Fail-closed）：\n"
            "1) Claim Gate（守衡主责）：核验对外宣称是否有 claim_evidence_refs 支撑 + 区域 market_overlay（如美妆/医疗界线、母婴儿童披露、欧盟GPSR），未通过一律 BLOCK；\n"
            "2) 授权 Gate（Radar登记 + 守衡核验）：TikTok Shop 美区仅认4类达人素材；二次剪辑(reedit)与跨账号投流各需独立授权，缺凭证锁死 publish_allowed=false；\n"
            "3) 实验 Gate（PMO主责）：无预注册 hypothesis_id 不开测；阈值哈希冻结；同批 >5 臂强制多重比较校正。"
        ),
    },
    {
        "id": "pmo-l2-handoff6",
        "title": "Native Agent 6 条跨岗标准交接链与业务导诊路线",
        "keywords": ["交接", "协作", "导诊", "找谁", "哪个agent", "流程", "链路", "新品", "上市", "选品", "脚本", "差评", "投放", "handoff"],
        "content": (
            "6条机器对机器标准交接链（业务问题导诊地图）：\n"
            "① 声量到内容链：Source(抓数) → Echo(v6.4字典痛点卡 pain_tag_id) → Emily(注入10品牌BrandToken≥85分出策略) → Clone(拆S1-S5分镜包 PendingReviewAssetPacket) → 守衡/Radar(双签 claim_id + rights_ref 后解锁投放)；\n"
            "② AI权威引用夺权链：Source → GEO(20问/ASIN探针检出未获Best Overall缺口如HSA/FSA) → 分派 Vicky(攻关S级权威媒体评测) + Shopify(补PDP FAQ/Review Schema) → GEO次月复测；\n"
            "③ 选品到上架准入链：product.luteos.com(Fusion计算 SHI×CVI=OppScore≥75) → Market(核验三层TAM+7国法规+DataPilot毛利) → 守衡(B1工厂实验室索证) → Shopify(accio_to_shopify一键生成带成本/MOQ的DRAFT草稿)；\n"
            "④ 流量承接与库存护栏链：加投广告或达人前触发灵词 Hook → 查 shopify.luteos.com 落地页移动端JS负载(防2.2MB卡顿页) + 查 SCM activity_stock_guard(防DOS<30断货烧钱)；\n"
            "⑤ 售后反哺研发与风控链：Echo(712万VOC+跨渠道Gap雷达检出社媒独有安全/故障词如motor_failure或退货率飙升) → 触发P0熔断暂停加投 + BrandOS生成DTC差评回复 + 输出VOA改款决策包；\n"
            "⑥ 经营诊断与PMO裁决链：DataPilot(122万行止血87M/造血635M) + 14 Agents 上报 measuredActions → PMO 每90天执行四象限续投/减半/关停裁决。"
        ),
    },
    {
        "id": "pmo-l2-stage4",
        "title": "四阶自进化标尺与三棒接力闭环 (P1吴雨宁→P2周健→P3刘华丽)",
        "keywords": ["四阶", "stage", "自进化", "进度", "三棒", "接棒", "分工", "吴雨宁", "周健", "刘华丽", "封顶", "返工率", "高频"],
        "content": (
            "1) 四阶真实进度标尺（Agent是终局，工作台是稳定SOP沉淀器）：Stage 1(0→25%)工作台基座就绪 → Stage 2(25→50%)14个独立飞书Bot双向回调跑通（未通飞书回调最高封顶50%） → "
            "Stage 3(50→75%)统计飞书高频提问(≥10次/周)或卡片打回(≥3次)蒸馏为确定性脚本并通过门禁(返工率<20%) → Stage 4(75→100%)稳定≥2周迁移固化为工作台自动化工位。\n"
            "2) 功能内三棒接力（49项功能×3棒=147道工序）：P1 吴雨宁(30%：需求调研/前端设计/数据架构Schema) → P2 周健(40%：全栈开发/独立飞书Bot回调/算法研发) → "
            "P3 刘华丽(30%：门禁测试挂evidence_url/Agent控制台运营/高频统计 + 联合吴雨宁向品牌市场部推广收回measuredActions)。"
        ),
    },
    {
        "id": "pmo-l2-quadrant",
        "title": "90天四象限续投/关停裁决与四大熔断机制",
        "keywords": ["四象限", "裁决", "续投", "关停", "砍掉", "熔断", "校准会", "僵尸项目"],
        "content": (
            "季度校准会四象限裁决（根治正式终止项目数=0的僵尸项目病灶）：\n"
            "• 主指标达成≥80% 且 对象级A被非owner消费 = 续投；\n"
            "• 主指标达成≥80% 但 无下游非owner消费 = 条件续投（限期6个月接通下游）；\n"
            "• 主指标<80% 但 有下游消费 = 条件续投（预算减半 + 6个月内出归因）；\n"
            "• 主指标<80% 且 无下游消费 = 立即关停。\n"
            "注：T4质量门禁未达标时最高只能条件续投；L5-06系统维护人力 > 0.5 FTE/新增系统时立即熔断停止新建产线。"
        ),
    },
]


def _search_builtin_memories(query: str, limit: int = 3) -> list[dict]:
    q_low = (query or "").lower()
    scored = []
    for item in BUILTIN_CANONICAL_MEMORIES:
        score = 0.0
        for kw in item["keywords"]:
            if kw in q_low:
                score += 0.28
        # 标题与正文词片匹配
        title_str = str(item["title"]).lower()
        content_str = str(item["content"]).lower()
        for token in ("g1", "g2", "g3", "emily", "clone", "vicky", "geo", "radar", "echo", "market", "source", "signal", "守衡", "daisy", "main", "shopify", "pmo", "吴雨宁", "周健", "刘华丽"):
            if token in q_low and (token in title_str or token in content_str):
                score += 0.22
        if score > 0:
            scored.append((min(0.99, round(0.55 + score, 2)), item))
    scored.sort(key=lambda x: x[0], reverse=True)
    if not scored:
        # 默认返回核心红线与四阶三棒规则作为基底
        return [
            {"title": BUILTIN_CANONICAL_MEMORIES[0]["title"], "content": BUILTIN_CANONICAL_MEMORIES[0]["content"], "score": 0.75},
            {"title": BUILTIN_CANONICAL_MEMORIES[5]["title"], "content": BUILTIN_CANONICAL_MEMORIES[5]["content"], "score": 0.72},
        ][:limit]
    return [{"title": it["title"], "content": it["content"], "score": sc} for sc, it in scored[:limit]]


def recall_durable_memories(query: str, limit: int = 2, min_score: float = 0.5,
                            space: str | None = None,
                            timeout_seconds: float = 3.0,
                            allow_builtin_fallback: bool = False) -> str:
    """从 Nowledge Mem 检索与问题强相关的 PMO 口径、红线与避坑经验。

    - 默认严格遵守单元测试契约：当 `allow_builtin_fallback=False` 且 `nmem` 失败/超时/无匹配时返回空串 `""`。
    - 当飞书机器人专家问答调用（`allow_builtin_fallback=True`）且容器内无 `nmem` 时，自动使用内置 Canonical 记忆池兜底。
    """
    if not query or not query.strip():
        return ""
    target = space or os.environ.get("NMEM_SPACE", DEFAULT_SPACE)
    try:
        cli = os.environ.get("NMEM_CLI_PATH", "nmem")
        cmd = [cli, "--json", "memories", "search", query.strip()[:100],
               "--space", target, "-n", str(max(1, int(limit)))]
        res = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=timeout_seconds)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            items = data if isinstance(data, list) else (data.get("items") or data.get("memories") or [])
            blocks = []
            for m in items:
                score = float(m.get("score") or 0.0)
                if score < min_score:
                    continue
                title = (m.get("title") or "").strip()
                content = (m.get("content") or m.get("snippet") or "").strip()
                if title and content:
                    blocks.append(f"• 【{title}】(匹配度 {score:.2f})\n{content}")
            if blocks:
                return "【PMO 持久记忆（口径/红线/避坑）】\n" + "\n\n".join(blocks)
    except Exception:  # noqa: BLE001
        pass

    if allow_builtin_fallback and target == DEFAULT_SPACE:
        fallback_items = _search_builtin_memories(query, limit=max(1, int(limit)))
        blocks = [
            f"• 【{m['title']}】(匹配度 {m['score']:.2f})\n{m['content']}"
            for m in fallback_items
            if float(m["score"]) >= min_score
        ]
        if blocks:
            return "【PMO 持久记忆（口径/红线/避坑）】\n" + "\n\n".join(blocks)
    return ""
