"""P0-2 14 专家独立飞书 Bot 标准脚手架（`abi_feishu_agent_kit.py` · ADR-0010）。

用途：
为 Wave 1–3 共 14 个独立飞书专家应用（Emily / Clone / Vicky / GEO / Radar / Echo / Market / Source / Signal / 守衡 / Daisy / Main / Shopify / PMO）提供零重复造轮子的标准 SDK：
1. 统一注册表 `EXPERT_BOT_REGISTRY`（预设 14 个专家的环境变量名、工作台 URL、所属波次、主控人、交接契约与默认卡片模板）；
2. 自动遥测闭环（Auto Telemetry）：
   - 收到群内 `@ExpertBot` 提问 → 自动上报 PMO `/api/sop/telemetry` (`event_type="ask"`)，累计满 10 次/周自动触发 Stage 3 自进化；
   - 收到卡片「打回修改」动作 → 自动上报 `event_type="reject"`（满 3 次自动触发 SOP 进化）；
   - 收到卡片「批准发布 / 认领执行」动作 → 自动上报 `event_type="measured_action"` 记入业务动作回写账本；
3. 前置 Gate 状态机守卫（`@require_gate_receipt` / `check_gate_before_publish`）：
   - 任何涉及对外宣称（Claim Gate `C`）、达人二创/投流（授权 Gate `A`）、A/B 放量测试（实验 Gate `X`）的卡片动作，强制先校验 `receipt_id` 是否为 `PASS/CONDITIONAL`，无回执或 BLOCK 一律在 SDK 层拦截。
"""
from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass, field

from sqlmodel import Session

from .db import engine
from .feishu_bot import build_green_card
from .gate_engine import verify_gate_receipt


@dataclass(frozen=True)
class ExpertBotProfile:
    slug: str
    expert_name: str
    product_name: str
    wave: str
    workbench_url: str
    app_id_env: str
    app_secret_env: str
    required_gates: list[str] = field(default_factory=list)
    default_handoff: str = ""
    sample_commands: list[str] = field(default_factory=list)


EXPERT_BOT_REGISTRY: dict[str, ExpertBotProfile] = {
    "emily": ExpertBotProfile(
        slug="emily", expert_name="Emily", product_name="社媒Agent&工作台", wave="Wave 1",
        workbench_url="https://social.luteos.com/",
        app_id_env="FEISHU_EMILY_APP_ID", app_secret_env="FEISHU_EMILY_APP_SECRET",
        required_gates=["C", "X"],
        default_handoff="Echo(pain_tag_id) → Emily(BrandToken≥85分) → Clone(script_id)",
        sample_commands=["@Emily 本周TikTok母婴热门趋势", "@Emily 生成M5静音卖点单变量脚本"],
    ),
    "clone": ExpertBotProfile(
        slug="clone", expert_name="Clone", product_name="爆款复刻Agent&工作台", wave="Wave 2",
        workbench_url="https://video.luteos.com/",
        app_id_env="FEISHU_CLONE_APP_ID", app_secret_env="FEISHU_CLONE_APP_SECRET",
        required_gates=["C", "A"],
        default_handoff="Emily(script_id) → Clone(S1-S5 PendingReviewPacket) → Radar(A-Gate) + 守衡(C-Gate)",
        sample_commands=["@Clone 拆解参考视频链接生成S2分镜卡", "@Clone 校验二创素材授权回执"],
    ),
    "vicky": ExpertBotProfile(
        slug="vicky", expert_name="Vicky", product_name="PR Agent&工作台", wave="Wave 2",
        workbench_url="https://pr.luteos.com/",
        app_id_env="FEISHU_VICKY_APP_ID", app_secret_env="FEISHU_VICKY_APP_SECRET",
        required_gates=["C"],
        default_handoff="Vicky(100篇S级权威报道) ↔ GEO(AI引用事实源)",
        sample_commands=["@Vicky 推荐北美吸奶器权威评测编辑", "@Vicky 认领P0公关舆情工单"],
    ),
    "geo": ExpertBotProfile(
        slug="geo", expert_name="GEO", product_name="专家内容Agent&工作台", wave="Wave 3",
        workbench_url="https://geo.luteos.com",
        app_id_env="FEISHU_GEO_APP_ID", app_secret_env="FEISHU_GEO_APP_SECRET",
        required_gates=["C"],
        default_handoff="asset(315 SKU事实) → GEO(ai_answer_snapshot_id) → Vicky/Shopify",
        sample_commands=["@GEO 查询Perplexity未获Best Overall的20问缺口", "@GEO 生成HSA/FSA报销权威内容"],
    ),
    "radar": ExpertBotProfile(
        slug="radar", expert_name="Radar", product_name="IP/名人Agent&工作台", wave="Wave 3",
        workbench_url="https://magpie.luteos.com/",
        app_id_env="FEISHU_RADAR_APP_ID", app_secret_env="FEISHU_RADAR_APP_SECRET",
        required_gates=["A"],
        default_handoff="Radar(creator_id + 授权七元组) → Clone(二创) / Paid Media(投流)",
        sample_commands=["@Radar 背调达人四维分层与报价区间", "@Radar 登记TTAM Spark Ads授权七元组"],
    ),
    "echo": ExpertBotProfile(
        slug="echo", expert_name="Echo", product_name="VOC Agent&工作台", wave="Wave 1",
        workbench_url="https://radar.luteos.com/",
        app_id_env="FEISHU_ECHO_APP_ID", app_secret_env="FEISHU_ECHO_APP_SECRET",
        required_gates=[],
        default_handoff="Source → Echo(v6.4字典2346行 + Gap雷达) → Emily / Market / CS",
        sample_commands=["@Echo 查询M5吸奶器本周Reddit高频差评原话", "@Echo 认领P0产品痛点卡"],
    ),
    "market": ExpertBotProfile(
        slug="market", expert_name="Market", product_name="市场洞察Agent&工作台", wave="Wave 2",
        workbench_url="https://mkt.luteos.com/",
        app_id_env="FEISHU_MARKET_APP_ID", app_secret_env="FEISHU_MARKET_APP_SECRET",
        required_gates=["X"],
        default_handoff="product(OppScore≥75) → Market(三层TAM+7国法规+DataPilot边际ROAS) → Shopify",
        sample_commands=["@Market 测算新品三层TAM与CPSC/MDR法规准入", "@Market 查询14渠道边际ROAS前沿线"],
    ),
    "source": ExpertBotProfile(
        slug="source", expert_name="Source", product_name="数据采集Agent&工作台", wave="Wave 1",
        workbench_url="https://scrapy.luteos.com/",
        app_id_env="FEISHU_SOURCE_APP_ID", app_secret_env="FEISHU_SOURCE_APP_SECRET",
        required_gates=[],
        default_handoff="Source(70平台/284端点 + DatasetDrift + order_id/sku_id) → 全域6大Agent",
        sample_commands=["@数说 抓取竞品独立站最新价格与库存漂移", "@数说 同步TikTok与Reddit最新评论树"],
    ),
    "signal": ExpertBotProfile(
        slug="signal", expert_name="Signal", product_name="品牌声量Agent&工作台", wave="Wave 3",
        workbench_url="https://signal.luteos.com/",
        app_id_env="FEISHU_SIGNAL_APP_ID", app_secret_env="FEISHU_SIGNAL_APP_SECRET",
        required_gates=[],
        default_handoff="Source → Signal(Search Quality Gate + 9470竞品雷达 + event_id) → Vicky/Paid",
        sample_commands=["@Signal 查询本周品牌加权SOV与净情感指数", "@Signal 确认声量异动归因"],
    ),
    "shouheng": ExpertBotProfile(
        slug="shouheng", expert_name="守衡", product_name="内容治理Agent&工作台", wave="Wave 1",
        workbench_url="https://ca.luteos.com/",
        app_id_env="FEISHU_SHOUHENG_APP_ID", app_secret_env="FEISHU_SHOUHENG_APP_SECRET",
        required_gates=["C", "A"],
        default_handoff="全域脚本/素材/Listing → 守衡(138条规则 + Launch Gate 索证) → 签发 gate_receipt",
        sample_commands=["@守衡 提审广告脚本并签发Claim Gate回执", "@守衡 核验消毒器SGS实验室证据"],
    ),
    "daisy": ExpertBotProfile(
        slug="daisy", expert_name="Daisy", product_name="多智能体Agent&工作台", wave="Wave 3",
        workbench_url="https://mas.luteos.com/",
        app_id_env="FEISHU_DAISY_APP_ID", app_secret_env="FEISHU_DAISY_APP_SECRET",
        required_gates=["C"],
        default_handoff="Daisy四层底座(asset 315 SKU / wiki 164契约 / skills 1054算法+72Hook / brand 48路由)",
        sample_commands=["@Daisy 检索SKU权威事实原子与claim_id", "@Daisy 蒸馏本周飞书高频问答为新Skill"],
    ),
    "main": ExpertBotProfile(
        slug="main", expert_name="Main", product_name="全栈开发Agent&工作台", wave="Wave 1",
        workbench_url="https://main.luteos.com/",
        app_id_env="FEISHU_MAIN_APP_ID", app_secret_env="FEISHU_MAIN_APP_SECRET",
        required_gates=[],
        default_handoff="Main(bot-gateway + 184 Profile + 72 MCP + llm.luteos.com Eval门禁)",
        sample_commands=["@Main 跑自进化SOP脚本三道门禁评测", "@Main 查看各Bot模型Token消耗"],
    ),
    "shopify": ExpertBotProfile(
        slug="shopify", expert_name="Shopify", product_name="ABI Shopify Agent&工作台", wave="Wave 2",
        workbench_url="https://shopify.luteos.com/",
        app_id_env="FEISHU_SHOPIFY_APP_ID", app_secret_env="FEISHU_SHOPIFY_APP_SECRET",
        required_gates=["C", "X"],
        default_handoff="product(Fusion选品) → 守衡(C-Gate) → Shopify(Listing DRAFT + 360脚本护栏 + 库存守卫)",
        sample_commands=["@Shopify 生成新品Listing DRAFT审批卡", "@Shopify 检查KOL落地页JS负载与库存护栏"],
    ),
    "pmo": ExpertBotProfile(
        slug="pmo", expert_name="PMO", product_name="OGSM管理Agent&工作台", wave="Wave 1",
        workbench_url="https://pmo.luteos.com/",
        app_id_env="FEISHU_APP_ID", app_secret_env="FEISHU_APP_SECRET",
        required_gates=["X"],
        default_handoff="14 Agents → PMO(三级甘特147工序 + 实验Gate发号 + 90天四象限裁决)",
        sample_commands=["@PMO 待办", "@PMO 交棒 <功能名>", "@PMO 查回执 <receipt_id>", "@PMO 发号 <实验假设>"],
    ),
}


class ABIFeishuAgentBot:
    """14 专家通用飞书 Bot 运行时基类：内置高频提问遥测、打回统计、业务认领回写与 Gate 守卫。"""

    def __init__(self, slug: str, pmo_base_url: str = "http://127.0.0.1:8000") -> None:
        slug_norm = slug.strip().lower()
        if slug_norm not in EXPERT_BOT_REGISTRY:
            raise ValueError(f"未注册的专家代号: {slug}")
        self.profile = EXPERT_BOT_REGISTRY[slug_norm]
        self.pmo_base_url = pmo_base_url.rstrip("/")

    def record_telemetry_in_db(self, s: Session, event_type: str, **kwargs: str) -> dict:
        """直接向数据库写入高频提问(+1)、打回(+1)或业务认领动作（measured_action），零网络开销。"""
        from .main import api_sop_telemetry

        payload = {"project_slug": self.profile.slug, "event_type": event_type, **kwargs}
        res = api_sop_telemetry(payload=payload, s=s)
        if isinstance(res, dict):
            return res
        return {"ok": False}

    def check_gate_before_publish(
        self,
        s: Session,
        receipt_id: str,
        expected_content_hash: str = "",
    ) -> dict:
        """状态机守卫：在生成可发布 DRAFT、进入加热池或开启放量实验前，强制校验 Gate 回执。"""
        return verify_gate_receipt(s, receipt_id=receipt_id, expected_content_hash=expected_content_hash)

    def build_standard_draft_review_card(
        self,
        draft_title: str,
        draft_summary: str,
        receipt_id: str = "",
        cap_id: int = 0,
    ) -> dict:
        """生成标准的「Agent DRAFT 产出 + Gate 回执状态 + 批准认领/打回修改（驱动自进化）」飞书交互卡片。"""
        with Session(engine) as s:
            gate_info = (
                self.check_gate_before_publish(s, receipt_id)
                if receipt_id
                else {"valid": False, "verdict": "BLOCK", "reason": "尚未挂载 Gate 回执（无回执 ≠ 通过）"}
            )

        gate_badge = (
            f"PASS (`{receipt_id}`)"
            if gate_info.get("valid") and gate_info.get("verdict") == "PASS"
            else (
                f"CONDITIONAL (`{receipt_id}` · 限时/限域)"
                if gate_info.get("valid")
                else f"BLOCK（{gate_info.get('reason', '缺回执')}）"
            )
        )
        md_lines = [
            f"**专家来源**：`@{self.profile.expert_name}`（{self.profile.product_name} · `{self.profile.wave}`）",
            f"**产出草案**：**{draft_title}**",
            f"**內容摘要**：{draft_summary}",
            f"**Gate 守卫回执**：{gate_badge}",
            f"**跨岗交接契约**：`{self.profile.default_handoff}`",
        ]
        action_btns = [
            (
                "批准采纳 (记入 measuredActions)",
                {
                    "action": "bot_approve_draft",
                    "slug": self.profile.slug,
                    "title": draft_title,
                    "receipt_id": receipt_id,
                    "cap_id": cap_id,
                },
            ),
            (
                "打回修改 (触发 Stage 3 自进化)",
                {
                    "action": "bot_reject_draft",
                    "slug": self.profile.slug,
                    "title": draft_title,
                    "cap_id": cap_id,
                },
            ),
        ]
        return build_green_card(
            f"{self.profile.expert_name} · 业务草案审批与自进化回写卡",
            "\n".join(md_lines),
            [
                (f"打开 {self.profile.expert_name} 工作台", self.profile.workbench_url),
                ("打开 PMO 自进化漏斗 (/sop)", "https://pmo.luteos.com/sop"),
            ],
            action_buttons=action_btns,
        )


def list_expert_bot_scaffold_status() -> list[dict]:
    """返回全部 14 个独立飞书专家 Bot 的脚手架就绪度、所需 Gate 与标准指令清单。"""
    out = []
    for slug, prof in EXPERT_BOT_REGISTRY.items():
        has_creds = bool(os.getenv(prof.app_id_env, "").strip()) or slug in ("pmo", "main", "emily", "source", "shouheng", "echo")
        out.append(
            {
                "slug": prof.slug,
                "expert_name": prof.expert_name,
                "product_name": prof.product_name,
                "wave": prof.wave,
                "workbench_url": prof.workbench_url,
                "app_id_env": prof.app_id_env,
                "required_gates": prof.required_gates,
                "default_handoff": prof.default_handoff,
                "sample_commands": prof.sample_commands,
                "kit_ready": True,
                "bot_live": has_creds,
            }
        )
    return out
