"""PMO 飞书应用事件回调、长连接守护与群卡片推送模块。

默认连接信息：
- App ID: cli_aa187cc667b8dbea (PMO)
- Bot Open ID: ou_0e2e4adf9d8479b0bdbee9cb19428fcb
- 目标群（ABI智能应用与算法组）: oc_b7b7d26f970f614d018c76d8eb557847

双通道事件接收：
1. WebSocket 长连接（lark_oapi.ws.Client 后台守护进程）：无需配置公网加密 Key 即可实时接收群内 @PMO 与私聊消息。
2. HTTP Webhook（POST /api/feishu/events）：支持 url_verification 握手与标准 v2 事件推送。
"""
import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
from datetime import date

from sqlmodel import Session, select

from . import models
from .db import engine

DEFAULT_APP_ID = "cli_aa187cc667b8dbea"
DEFAULT_APP_SECRET = ""  # 由环境变量 FEISHU_APP_SECRET 提供，不硬编码进仓库
DEFAULT_CHAT_ID = "oc_b7b7d26f970f614d018c76d8eb557847"  # ABI智能应用与算法组
BOT_OPEN_ID = "ou_0e2e4adf9d8479b0bdbee9cb19428fcb"

# 幂等缓存：防止飞书重试或双 worker 重复回复同一条 message_id
_SEEN_MESSAGES: dict[str, float] = {}
_SEEN_LOCK = threading.Lock()


def get_feishu_creds() -> tuple[str, str, str]:
    app_id = os.getenv("FEISHU_APP_ID", DEFAULT_APP_ID).strip() or DEFAULT_APP_ID
    app_secret = os.getenv("FEISHU_APP_SECRET", DEFAULT_APP_SECRET).strip() or DEFAULT_APP_SECRET
    chat_id = os.getenv("FEISHU_DEFAULT_CHAT_ID", DEFAULT_CHAT_ID).strip() or DEFAULT_CHAT_ID
    return app_id, app_secret, chat_id


def get_tenant_access_token() -> str:
    app_id, app_secret, _ = get_feishu_creds()
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data=json.dumps({"app_id": app_id, "app_secret": app_secret}).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read().decode("utf-8"))
    if data.get("code") != 0:
        raise RuntimeError(f"获取 tenant_access_token 失败: {data}")
    return str(data["tenant_access_token"])


def build_green_card(
    title: str,
    markdown_body: str,
    buttons: list[tuple[str, str]] | None = None,
    action_buttons: list[tuple[str, dict]] | None = None,
) -> dict:
    """构建零 Emoji、深林绿主题的飞书交互卡片（同时支持 URL 跳转按钮与免打字交互回写按钮）。"""
    elements: list[dict] = [{"tag": "markdown", "content": markdown_body}]
    if action_buttons:
        elements.append({"tag": "hr"})
        elements.append(
            {
                "tag": "markdown",
                "content": "**免打字快捷操作（点击按钮直接更新数据库并记录审计流水）**：",
            }
        )
        act_items = []
        for idx, (label, val_dict) in enumerate(action_buttons[:12]):
            btn_type = "danger" if val_dict.get("action") == "report_blocker" else ("primary" if idx == 0 else "default")
            act_items.append(
                {
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": label},
                    "type": btn_type,
                    "value": val_dict,
                }
            )
        elements.append({"tag": "action", "actions": act_items})

    if buttons:
        elements.append({"tag": "hr"})
        actions = []
        for idx, (label, url) in enumerate(buttons):
            actions.append(
                {
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": label},
                    "type": "primary" if (idx == 0 and not action_buttons) else "default",
                    "url": url,
                }
            )
        elements.append({"tag": "action", "actions": actions})

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "template": "green",
            "title": {"tag": "plain_text", "content": title},
        },
        "elements": elements,
    }


def send_card_to_chat(card: dict, chat_id: str | None = None) -> dict:
    """使用 PMO 应用身份直接向指定群（默认 ABI智能应用与算法组）发送交互卡片。"""
    _, _, default_cid = get_feishu_creds()
    target_cid = (chat_id or default_cid).strip()
    token = get_tenant_access_token()
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
        data=json.dumps(
            {
                "receive_id": target_cid,
                "msg_type": "interactive",
                "content": json.dumps(card, ensure_ascii=False),
            }
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def reply_card_to_message(message_id: str, card: dict, fallback_chat_id: str = "") -> dict:
    """优先使用 reply 接口回复原消息；若失败则回退为 send_card_to_chat。"""
    token = get_tenant_access_token()
    req = urllib.request.Request(
        f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply",
        data=json.dumps(
            {
                "msg_type": "interactive",
                "content": json.dumps(card, ensure_ascii=False),
            }
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        if fallback_chat_id:
            return send_card_to_chat(card, fallback_chat_id)
        raise


def _mark_seen(msg_id: str) -> bool:
    """返回 True 表示首次处理，返回 False 表示已处理过（幂等拦截）。"""
    if not msg_id:
        return True
    now = time.monotonic()
    with _SEEN_LOCK:
        expired = [k for k, ts in _SEEN_MESSAGES.items() if now - ts > 600]
        for k in expired:
            _SEEN_MESSAGES.pop(k, None)
        if msg_id in _SEEN_MESSAGES:
            return False
        _SEEN_MESSAGES[msg_id] = now
        return True


def _clean_user_query(raw_text: str) -> str:
    txt = re.sub(r"@_user_\d+", "", raw_text or "")
    txt = txt.replace("@PMO", "").replace("@pmo", "").strip()
    return txt


def _build_cap_quick_actions(caps: list[models.CapabilityItem], max_caps: int = 3) -> list[tuple[str, dict]]:
    """为未完成的能力点生成飞书交互卡片免打字快捷按钮（完成本棒交棒 / +25% / 报阻塞）。"""
    actions: list[tuple[str, dict]] = []
    todo = [c for c in caps if c.status != "已完成"]
    for c in todo[:max_caps]:
        short_name = c.name
        pct = c.progress_pct or 0
        if pct < 30:
            baton_label = f"{short_name} · 完成P1交棒@周健"
        elif pct < 70:
            baton_label = f"{short_name} · 完成P2交棒@刘华丽"
        else:
            baton_label = f"{short_name} · 完成P3闭环(100%)"
        actions.append(
            (
                baton_label,
                {"action": "pass_baton", "cap_id": c.id},
            )
        )
        actions.append(
            (
                f"{short_name} · 报阻塞",
                {"action": "report_blocker", "cap_id": c.id},
            )
        )
    return actions


def _execute_baton_pass(s: Session, c: models.CapabilityItem, note: str = "", source: str = "feishu_bot") -> dict:
    """执行三棒接力跃迁：P1(吴雨宁 <30%) -> P2(周健 35%) -> P3(刘华丽 75%) -> 100%(闭环，强制校验 evidence_url)。"""
    p = s.exec(select(models.ProductProject).where(models.ProductProject.slug == c.project_slug)).first()
    exp_name = p.expert_name if p else c.project_slug.upper()
    old_pct = c.progress_pct or 0
    old_status = c.status

    if old_pct < 30:
        from_owner, from_step = "吴雨宁", "P1（需求/前端/Schema）"
        to_owner, to_step = "周健", "P2（全栈开发/独立飞书Bot回调/算法）"
        new_pct = 35
        new_status = "进行中"
        gate_warn = ""
    elif old_pct < 70:
        from_owner, from_step = "周健", "P2（全栈开发/独立飞书Bot回调/算法）"
        to_owner, to_step = "刘华丽", "P3（门禁测试/Agent控制台运营/联合吴雨宁推广）"
        new_pct = 75
        new_status = "进行中"
        gate_warn = ""
    else:
        from_owner, from_step = "刘华丽", "P3（测试验收/Agent运营/工作台推广）"
        to_owner, to_step = "全员闭环", "Stage 4 工作台固化完成"
        new_pct = 100
        new_status = "已完成"
        if (c.evidence_url or "").strip():
            c.verify_state = "已验证"
            gate_warn = ""
        else:
            c.verify_state = "部分验证"
            gate_warn = "（注意：当前尚未挂载 evidence_url 实测证据，按 ste-zh 铁律暂标为「部分验证/待补证据」）"

    c.progress_pct = new_pct
    c.status = new_status
    c.owner = to_owner if to_owner in ("吴雨宁", "周健", "刘华丽") else "刘华丽"
    s.add(c)

    note_suffix = f"｜交接说明：{note}" if note else ""
    summary_txt = f"三棒交接：{from_owner} 完成 {from_step} -> 交棒给 @{to_owner} 进入 {to_step}（{old_pct}% -> {new_pct}%）{note_suffix}"
    s.add(
        models.ChangeAuditLog(
            cap_id=c.id or 0,
            project_slug=c.project_slug,
            expert_name=exp_name,
            cap_name=c.name,
            source=source,
            actor=from_owner,
            summary=summary_txt,
        )
    )
    s.commit()
    return {
        "exp_name": exp_name,
        "cap_name": c.name,
        "from_owner": from_owner,
        "from_step": from_step,
        "to_owner": to_owner,
        "to_step": to_step,
        "old_pct": old_pct,
        "new_pct": new_pct,
        "old_status": old_status,
        "new_status": new_status,
        "end_date": c.end_date or "待排期",
        "gate_warn": gate_warn,
        "note": note,
    }


def process_card_action_event(action_value: dict, operator_open_id: str = "") -> dict:
    """处理飞书卡片按钮点击事件 (card.action.trigger)，免打字直接修改数据库并记录审计流水。"""
    act_type = str(action_value.get("action") or "")
    cap_id = int(action_value.get("cap_id") or 0)
    if not act_type or not cap_id:
        return {
            "toast": {"type": "info", "content": "已收到操作请求"},
        }

    with Session(engine) as s:
        c = s.get(models.CapabilityItem, cap_id)
        if not c:
            return {
                "toast": {"type": "error", "content": f"未找到能力节点 #{cap_id}"},
            }

        p = s.exec(select(models.ProductProject).where(models.ProductProject.slug == c.project_slug)).first()
        exp_name = p.expert_name if p else c.project_slug.upper()

        if act_type == "pass_baton":
            res = _execute_baton_pass(s, c, note="飞书卡片一键交棒", source="feishu_card")
            return {
                "toast": {
                    "type": "success",
                    "content": (
                        f"已交棒「{res['cap_name']}」：{res['from_owner']} -> @{res['to_owner']} "
                        f"({res['old_pct']}% -> {res['new_pct']}%)"
                    ),
                }
            }

        if act_type == "set_pct":
            new_pct = max(0, min(100, int(action_value.get("pct") or 0)))
            old_pct = c.progress_pct
            old_status = c.status
            c.progress_pct = new_pct
            if new_pct == 100:
                c.status = "已完成"
            elif new_pct > 0 and c.status == "方案中":
                c.status = "进行中"
            s.add(c)
            s.add(
                models.ChangeAuditLog(
                    cap_id=c.id or 0,
                    project_slug=c.project_slug,
                    expert_name=exp_name,
                    cap_name=c.name,
                    source="feishu_card",
                    actor="飞书卡片按钮",
                    summary=f"免打字按钮：进度 {old_pct}% -> {new_pct}%，状态 {old_status} -> {c.status}",
                )
            )
            s.commit()
            return {
                "toast": {
                    "type": "success",
                    "content": f"已更新「{c.name}」：{old_pct}% -> {new_pct}% ({c.status})",
                }
            }

        if act_type == "report_blocker":
            if p:
                blocker_line = f"[飞书群报阻塞 {date.today().isoformat()}] {c.name}（当前 {c.progress_pct}%，负责：{c.owner or p.owner}）需协同排障"
                existing_gaps = [x.strip() for x in (p.pending_gaps or "").splitlines() if x.strip()]
                if not any(c.name in g for g in existing_gaps):
                    existing_gaps.insert(0, blocker_line)
                    p.pending_gaps = "\n".join(existing_gaps)
                    s.add(p)
            s.add(
                models.ChangeAuditLog(
                    cap_id=c.id or 0,
                    project_slug=c.project_slug,
                    expert_name=exp_name,
                    cap_name=c.name,
                    source="feishu_card",
                    actor="飞书卡片按钮",
                    summary=f"上报阻塞卡点：{c.name}（当前进度 {c.progress_pct}%）",
                )
            )
            s.commit()
            return {
                "toast": {
                    "type": "warning",
                    "content": f"已登记「{c.name}」阻塞卡点并同步至 PMO 雷达栏",
                }
            }

    return {"toast": {"type": "info", "content": "操作已完成"}}


def answer_as_pmo_expert(
    s: Session,
    query: str,
    data: dict,
    default_btns: list[tuple[str, str]],
) -> tuple[str, str, list[tuple[str, str]], list[tuple[str, dict]]]:
    """Tier 2 · PMO 专家灵魂问答引擎（ADR-0009）：

    融合三源信息回答群成员开放式问题：
    1. Nowledge Mem 读侧 Recall（46张 canonical 治理/红线/主键/Gate/交接链记忆卡 + 内置索引兜底）
    2. 实时 SQL 数据库快照（匹配到的专家项目、三棒接力当期持棒人、排期与自进化漏斗）
    3. LLM 推理（若配置了 PMO_LLM_BASE_URL / Magpie）+ 零延迟确定性专家诊断兜底
    """
    from .memory import recall_durable_memories

    q = query.strip()
    q_low = q.lower()

    # Step 1: 召回长期治理记忆（开启内置 Canonical 兜底，确保容器内 100% 命中）
    recalled_mem = recall_durable_memories(q, limit=3, min_score=0.5, allow_builtin_fallback=True)

    # Step 2: 匹配问题中提及的相关专家项目与功能项（支持别名与业务场景词映射）
    scene_to_slugs = {
        "选品": ["shopify", "market"],
        "上架": ["shopify", "shouheng"],
        "listing": ["shopify", "shouheng"],
        "温奶器": ["shopify", "market", "echo", "shouheng"],
        "吸奶器": ["echo", "vicky", "emily", "shouheng"],
        "消毒": ["shouheng", "clone", "emily"],
        "二创": ["clone", "radar", "shouheng"],
        "脚本": ["emily", "clone", "shouheng"],
        "视频": ["clone", "emily", "shouheng"],
        "达人": ["radar", "clone"],
        "红人": ["radar", "clone"],
        "kol": ["radar", "shopify"],
        "公关": ["vicky", "geo"],
        "媒体": ["vicky", "geo"],
        "差评": ["echo", "shouheng"],
        "评论": ["echo", "emily"],
        "voc": ["echo", "source"],
        "退货": ["echo", "market"],
        "爬虫": ["source"],
        "采集": ["source", "geo"],
        "数说": ["source"],
        "合规": ["shouheng"],
        "审核": ["shouheng"],
        "规则": ["shouheng", "daisy"],
        "知识库": ["daisy", "shopify"],
        "skill": ["daisy", "main"],
        "roas": ["market", "shopify", "emily"],
        "预算": ["market", "pmo"],
        "声量": ["signal", "vicky", "emily"],
        "sov": ["signal", "geo"],
    }
    matched_slugs: list[str] = []
    for pv in data["proj_views"]:
        p = pv["proj"]
        if p.slug in q_low or p.expert_name.lower() in q_low:
            matched_slugs.append(p.slug)
    for kw, slugs in scene_to_slugs.items():
        if kw in q_low:
            for sl in slugs:
                if sl not in matched_slugs:
                    matched_slugs.append(sl)

    matched_pvs = [data["pv_by_slug"][sl] for sl in matched_slugs[:3] if sl in data.get("pv_by_slug", {})]
    matched_caps: list[models.CapabilityItem] = []
    for pv in data["proj_views"]:
        for cv in pv["cap_views"]:
            c = cv["cap"]
            if any(tok in q_low for tok in (c.name.lower(), c.name[:4].lower()) if len(tok) >= 2):
                matched_caps.append(c)

    # Step 3: 若配置了本地/内网 LLM 网关（如 Magpie），尝试用 pmo-guardian 人格合成深度回答
    llm_url = os.getenv("PMO_LLM_BASE_URL", "").strip()
    llm_model = os.getenv("PMO_LLM_MODEL", "vod/gpt-5.3-chat").strip()
    llm_key = os.getenv("PMO_LLM_API_KEY", "sk-no-key-required").strip()
    llm_answer = ""
    if llm_url:
        try:
            proj_ctx = "\n".join(
                f"- {pv['proj'].expert_name}({pv['proj'].workbench_url}): 进度{pv['pct']}%, 收口{pv['proj_end']}, 交接:{(pv['support_list'] or [''])[0]}"
                for pv in (matched_pvs or data["proj_views"][:5])
            )
            sys_prompt = (
                "你是 ABI 品牌 & 营销域 PMO 守门与架构专家 Agent (pmo-guardian)。"
                "严格遵守：事实>证据>承诺>交付；一个G只认一个结算指标；无回执不等于通过；"
                "每个功能由 P1吴雨宁(需求/前端/Schema 30%)→P2周健(全栈/飞书Bot/算法 40%)→P3刘华丽(测试/Agent运营/推广 30%) 三棒串联闭环。"
                "请直接、简练、分点回答群成员问题，指出具体规则编号、涉及的专家Agent、三棒当前持棒人与下一步可执行动作。"
            )
            user_prompt = f"用户问题：{q}\n\n{recalled_mem}\n\n【实时项目排期上下文】\n{proj_ctx}"
            req = urllib.request.Request(
                f"{llm_url.rstrip('/')}/chat/completions",
                data=json.dumps(
                    {
                        "model": llm_model,
                        "messages": [
                            {"role": "system", "content": sys_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "max_tokens": 600,
                        "temperature": 0.2,
                    }
                ).encode("utf-8"),
                headers={"Authorization": f"Bearer {llm_key}", "Content-Type": "application/json; charset=utf-8"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=4.0) as r:
                resp_j = json.loads(r.read().decode("utf-8"))
                llm_answer = (resp_j.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
        except Exception:
            llm_answer = ""

    # Step 4: 组装高密度专家诊断卡片（即使无外部 LLM 也 100% 给出权威记忆裁决 + 三棒协同指路）
    lines = [
        f"**咨询问题**：{q}",
        f"**专家身份**：`pmo-guardian`（ABI 垂直 Agent 矩阵项目管理与治理守门专家）",
    ]
    if llm_answer:
        lines.append("")
        lines.append("**一、 PMO 专家诊断与执行建议**：")
        lines.append(llm_answer)

    if recalled_mem:
        lines.append("")
        lines.append("**一、 命中的 OGSM 治理规范、主键契约与避坑准则（`abi-pmo` 记忆库）**：" if not llm_answer else "**二、 关联的 `abi-pmo` 长期记忆与硬约束出处**：")
        # 去掉首行多余标题，保持卡片紧凑
        clean_mem = "\n".join(recalled_mem.splitlines()[1:]) if recalled_mem.startswith("【PMO") else recalled_mem
        lines.append(clean_mem)

    if matched_pvs:
        lines.append("")
        lines.append("**二、 关联专家 Agent 实时排期与三棒在手接棒状态**：" if not llm_answer else "**三、 关联专家 Agent 实时排期与三棒在手接棒状态**：")
        for pv in matched_pvs:
            p = pv["proj"]
            lines.append(
                f"- **{p.expert_name} · {p.product_name}**（`{p.workbench_url}`）｜综合进度 **{pv['pct']}%**｜收口：**{pv['proj_end']}**"
            )
            for cv in pv["cap_views"][:3]:
                c = cv["cap"]
                rel = cv["relay"]
                if c not in matched_caps:
                    matched_caps.append(c)
                lines.append(
                    f"  └ `{c.name}`（{c.progress_pct}%）：**当前接棒 @{rel['active_owner']}**（{rel['active_step']}，本棒截止 `{rel['active_end_date']}`）"
                )
            if pv["support_list"]:
                lines.append(f"  └ **跨岗交接协议**：{pv['support_list'][-1]}")

    lines.append("")
    lines.append("**三、 三棒铁三角协同动作指引**：")
    lines.append(
        "- **需改 Schema / 飞书卡片交互 / 工作台 SOP 推广** → 找 **@吴雨宁（P1 首棒 & 终棒推广）**\n"
        "- **需写全栈接口 / 接入独立飞书 Bot 回调 / 调算法脚本** → 找 **@周健（P2 研发棒）**\n"
        "- **需跑门禁盲测（挂 `evidence_url`）/ 查高频问题统计（≥10次/周）** → 找 **@刘华丽（P3 测试与控制台运营棒）**\n"
        "- *常用快捷指令*：`@PMO 待办` · `@PMO 交棒 <功能名>` · `@PMO 自进化` · `@PMO 周报`"
    )

    btns = [
        ("打开岗位说明书与自进化漏斗 (/sop)", "https://pmo.luteos.com/sop"),
        ("打开三级串联甘特图 (/roadmap)", "https://pmo.luteos.com/roadmap"),
    ]
    return (
        "ABI PMO 专家诊断与跨 Agent 协同裁决",
        "\n".join(lines),
        btns,
        _build_cap_quick_actions(matched_caps, max_caps=2),
    )


def handle_bot_command(
    query: str,
) -> tuple[str, str, list[tuple[str, str]], list[tuple[str, dict]]]:
    """根据群成员 @PMO 的指令生成卡片 (title, markdown_body, buttons, action_buttons)。"""
    from .main import api_ping_sites, build_tree_data, generate_weekly_brief

    q = query.strip()
    q_low = q.lower()
    default_btns = [
        ("打开 PMO 战略全景导图", "https://pmo.luteos.com/"),
        ("甘特图与四列看板", "https://pmo.luteos.com/roadmap"),
        ("14大产品系统架构图", "https://pmo.luteos.com/sites"),
    ]

    with Session(engine) as s:
        # 1z. 三棒交接指令：@PMO 交棒 <能力名> [交接说明]（支持能力名中含空格，如 "IP 合作计划制定"）
        m_baton = re.match(r"^(?:交棒|完成交棒|转交|移交)\s+(.+)$", q)
        if m_baton:
            rest_txt = m_baton.group(1).strip()
            all_caps = s.exec(select(models.CapabilityItem)).all()
            # 优先匹配完整能力名（忽略空格大小写），其次匹配首个词
            def _norm_c(s_val: str) -> str:
                return s_val.replace(" ", "").lower()

            rest_norm = _norm_c(rest_txt)
            target_cap = None
            best_len = 0
            for c_cand in all_caps:
                cn = _norm_c(c_cand.name)
                if cn and cn in rest_norm and len(cn) > best_len:
                    target_cap = c_cand
                    best_len = len(cn)
            if not target_cap:
                first_tok = rest_txt.split()[0].lower()
                target_cap = next((c for c in all_caps if first_tok in c.name.lower()), None)
            if not target_cap:
                return (
                    "PMO 三棒交接提示",
                    f"未找到包含「**{rest_txt}**」的功能节点，请核对名称后再试。",
                    default_btns,
                    [],
                )
            note = rest_txt.replace(target_cap.name, "", 1).strip()
            if note == rest_txt:
                parts = rest_txt.split(maxsplit=1)
                note = parts[1].strip() if len(parts) > 1 else ""
            res = _execute_baton_pass(s, target_cap, note=note, source="feishu_bot")
            return (
                f"PMO 三棒接力交棒完成 · {res['exp_name']} · {res['cap_name']}",
                (
                    f"- **交出棒次**：**@{res['from_owner']}** 已完成 `{res['from_step']}`\n"
                    f"- **接棒点名**：请 **@{res['to_owner']}** 接棒进入 `{res['to_step']}`\n"
                    f"- **进度跃迁**：`{res['old_pct']}%` → **`{res['new_pct']}%`**（状态：`{res['new_status']}`，收口日：`{res['end_date']}`）\n"
                    + (f"- **交接备注**：{res['note']}\n" if res["note"] else "")
                    + (f"- **门禁提示**：{res['gate_warn']}\n" if res["gate_warn"] else "")
                ),
                default_btns,
                _build_cap_quick_actions([target_cap], max_caps=1),
            )

        # 1a. 报阻塞指令：@PMO 阻塞 <能力名> <原因>
        m_blk = re.match(r"^(?:阻塞|报阻塞|卡点)\s+(\S+)(?:\s+(.+))?$", q)
        if m_blk:
            cap_kw = m_blk.group(1)
            reason = (m_blk.group(2) or "进度受阻需跨团队协同").strip()
            all_caps = s.exec(select(models.CapabilityItem)).all()
            target_cap = next((c for c in all_caps if cap_kw.lower() in c.name.lower()), None)
            if not target_cap:
                return (
                    "PMO 阻塞上报提示",
                    f"未找到包含「**{cap_kw}**」的能力图谱节点，请核对名称后再试。",
                    default_btns,
                    [],
                )
            p = s.exec(
                select(models.ProductProject).where(models.ProductProject.slug == target_cap.project_slug)
            ).first()
            exp_name = p.expert_name if p else target_cap.project_slug.upper()
            if p:
                blocker_line = f"{target_cap.name}：{reason}（{date.today().isoformat()} 群内上报）"
                existing_gaps = [x.strip() for x in (p.pending_gaps or "").splitlines() if x.strip()]
                existing_gaps.insert(0, blocker_line)
                p.pending_gaps = "\n".join(existing_gaps)
                s.add(p)
            s.add(
                models.ChangeAuditLog(
                    cap_id=target_cap.id or 0,
                    project_slug=target_cap.project_slug,
                    expert_name=exp_name,
                    cap_name=target_cap.name,
                    source="feishu_bot",
                    actor="飞书群指令",
                    summary=f"上报阻塞：{reason}",
                )
            )
            s.commit()
            return (
                f"PMO 阻塞卡点已登记 · {target_cap.name}",
                (
                    f"- **能力节点**：{target_cap.name}（所属项目：`{exp_name}`）\n"
                    f"- **阻塞说明**：{reason}\n"
                    f"- **当前进度**：`{target_cap.status} {target_cap.progress_pct}%`（负责：{target_cap.owner or '待定'}）\n"
                    f"- **联动状态**：已写入首页跨项目重点待补齐卡点与变更审计流水"
                ),
                default_btns,
                _build_cap_quick_actions([target_cap], max_caps=1),
            )

        # 1. 更新指令：@PMO 更新 <能力名> <进度%>
        m_upd = re.match(r"^(?:更新|修改|设置)\s+(\S+)\s+(\d{1,3})%?$", q)
        if m_upd:
            cap_kw, new_pct_str = m_upd.group(1), m_upd.group(2)
            new_pct = max(0, min(100, int(new_pct_str)))
            all_caps = s.exec(select(models.CapabilityItem)).all()
            target_cap = next((c for c in all_caps if cap_kw.lower() in c.name.lower()), None)
            if not target_cap:
                return (
                    "PMO 进度更新提示",
                    f"未找到包含「**{cap_kw}**」的能力图谱节点，请核对名称后再试。",
                    default_btns,
                    [],
                )
            old_pct = target_cap.progress_pct
            old_status = target_cap.status
            target_cap.progress_pct = new_pct
            if new_pct == 100:
                target_cap.status = "已完成"
            elif new_pct > 0 and target_cap.status == "方案中":
                target_cap.status = "进行中"
            s.add(target_cap)
            s.add(
                models.ChangeAuditLog(
                    cap_id=target_cap.id or 0,
                    project_slug=target_cap.project_slug,
                    expert_name=target_cap.project_slug.upper(),
                    cap_name=target_cap.name,
                    source="feishu_bot",
                    actor="飞书群指令",
                    summary=f"进度 {old_pct}% -> {new_pct}%，状态 {old_status} -> {target_cap.status}",
                )
            )
            s.commit()
            ev_hint = (
                f"\n- **验收提醒**：当前已完成但未挂载实测证据，请补充证据后再流转至「已验证」。"
                if (new_pct == 100 and not (target_cap.evidence_url or "").strip())
                else ""
            )
            return (
                f"PMO 能力进度已更新 · {target_cap.name}",
                (
                    f"- **能力名称**：{target_cap.name}（所属项目：`{target_cap.project_slug.upper()}`）\n"
                    f"- **进度变更**：`{old_pct}%` → **`{new_pct}%`**\n"
                    f"- **状态变更**：`{old_status}` → **`{target_cap.status}`**\n"
                    f"- **截止排期**：{target_cap.end_date or '待排期'}（负责：{target_cap.owner or '待定'}）{ev_hint}"
                ),
                default_btns,
                _build_cap_quick_actions([target_cap], max_caps=1),
            )

        # 2. 周报 / 进度 / 汇总
        if any(w in q_low for w in ("周报", "简报", "进度", "汇总", "总览", "ogsm", "report", "status")):
            brief = generate_weekly_brief(s)
            return (
                f"ABI 品牌 & 营销 Agent 周度进展与里程碑简报 ({date.today().isoformat()})",
                brief["markdown"],
                default_btns,
                [],
            )

        # 3. 里程碑 / 甘特 / 排期
        if any(w in q_low for w in ("里程碑", "甘特", "排期", "到期", "milestone", "gantt")):
            data = build_tree_data(s)
            lines = [
                f"**总体排期覆盖度**：{data['stats']['scheduled_count']} / {data['stats']['cap_total']} 项已排期（总加权进度 **{data['stats']['overall_pct']}%**）",
                "",
                "**近 4 周待交付关键里程碑 (Milestone)**：",
            ]
            ms_caps = []
            for m in data["radar_focus"]["upcoming_milestones"]:
                c = m["cap"]
                ms_caps.append(c)
                lines.append(
                    f"- **{c.end_date}**（剩 {m['days_left']} 天）｜**{m['proj_expert']} · {c.name}**：当前 **{c.progress_pct}%**（{c.owner}）"
                )
            return (
                "ABI 2026Q4 关键里程碑与甘特排期",
                "\n".join(lines),
                default_btns,
                _build_cap_quick_actions(ms_caps, max_caps=3),
            )

        # 4. 探活 / 站点 / 工作台
        if any(w in q_low for w in ("探活", "站点", "工作台", "健康", "ping", "site")):
            ping_data = api_ping_sites(s)
            lines = [
                f"**检测时间**：{ping_data['checked_at']}",
                f"**在线率**：**{ping_data['online']} / {ping_data['total']}** 个站点在线可达",
                "",
            ]
            for url, info in list(ping_data["results"].items())[:16]:
                short_u = url.replace("https://", "").replace("/", "")
                st_txt = f"200 在线 ({info['ms']}ms)" if info["ok"] else f"受限/内网 ({info.get('err') or info.get('code')})"
                lines.append(f"- `{short_u}`：{st_txt}")
            return ("ABI 24 个线上工作台与子站实时探活报告", "\n".join(lines), default_btns, [])

        # 4b. 飞书在线表格双向同步：@PMO 同步表格
        if any(w in q_low for w in ("同步表格", "飞书表", "同步飞书", "sheet")):
            from .automation_suite import sync_feishu_spreadsheet

            sync_res = sync_feishu_spreadsheet(s, direction="both")
            return (
                "ABI OGSM 飞书在线表格双向同步完成",
                (
                    f"- **绑定飞书表格**：`{sync_res['spreadsheet_token']}`（`XhJUya` 总览页 + `5UK051` 任务计划）\n"
                    f"- **拉取更新负责人**：{sync_res['pulled_owners']} 项\n"
                    f"- **拉取补齐排期日期**：{sync_res['pulled_dates']} 项\n"
                    f"- **写回飞书表最新状态与进度**：{sync_res['pushed_rows']} 行（状态码 `{sync_res['feishu_write_code']}`）"
                ),
                default_btns,
                [],
            )

        # 4c. 站点巡检与里程碑催办：@PMO 巡检 / @PMO 催办
        if any(w in q_low for w in ("巡检", "催办", "提醒", "patrol")):
            from .automation_suite import run_patrol_and_reminder

            pat_res = run_patrol_and_reminder(s, push_to_feishu=False, days_threshold=14)
            return (
                "ABI PMO 站点巡检与临期里程碑催办",
                pat_res["markdown"],
                default_btns,
                pat_res.get("action_buttons", []),
            )

        # 5. 当仅仅输入单个项目名（且非复杂疑问句）时，返回该项目详情卡；若为业务/架构/规范咨询句，则转入 Tier 2 PMO 专家灵魂问答引擎
        data = build_tree_data(s)
        is_expert_question = (
            len(q) >= 12
            or any(
                kw in q_low
                for kw in (
                    "怎么", "如何", "为什么", "什么", "哪些", "找谁", "哪个", "能不能", "可以吗",
                    "主键", "字段", "schema", "gate", "门禁", "回执", "红线", "误用",
                    "roas", "cac", "mer", "sov", "交接", "复用", "避坑", "能否", "算不算", "?", "？",
                )
            )
        )
        if not is_expert_question:
            for pv in data["proj_views"]:
                p = pv["proj"]
                if (
                    p.slug in q_low
                    or p.expert_name.lower() in q_low
                    or p.product_name.lower() in q_low
                ):
                    lines = [
                        f"**所属目标与策略**：{p.goal_code} · {p.strategy_code}｜**状态**：{p.status_summary}（综合进度 **{pv['pct']}%**）",
                        f"**负责团队**：{p.owner}｜**计划收口**：{pv['proj_end'] or '待排期'}",
                        f"**主验收工作台**：{p.workbench_url or '无'}",
                        "",
                        "**能力图谱与三棒接力明细**：",
                    ]
                    for cv in pv["cap_views"]:
                        c = cv["cap"]
                        rel = cv["relay"]
                        ms_tag = "[里程碑] " if c.is_milestone else ""
                        ev_tag = " [已挂证据]" if (c.evidence_url or "").strip() else ""
                        lines.append(
                            f"- {ms_tag}**{c.name}**：`{c.status} {c.progress_pct}%`（当前接棒：**@{rel['active_owner']}** · {rel['active_step']}，截止：{c.end_date or '待排期'}{ev_tag}）"
                        )
                    lines.append("")
                    lines.append(f"**实测成果总结**：\n{p.verified_summary}")
                    if pv["gaps_list"]:
                        lines.append("")
                        lines.append("**下一阶段待补齐项**：")
                        for g in pv["gaps_list"][:3]:
                            lines.append(f"- {g}")

                    btns = []
                    if p.workbench_url:
                        btns.append((f"打开 {p.expert_name} 工作台", p.workbench_url))
                    btns.append(("在 PMO 门户查看详情", f"https://pmo.luteos.com/projects#proj-{p.slug}"))
                    return (
                        f"{p.expert_name} · {p.product_name} 项目详情",
                        "\n".join(lines),
                        btns,
                        _build_cap_quick_actions(pv["caps"], max_caps=3),
                    )

        # 5aa. 查询自进化漏斗与业务动作回写账本：@PMO 自进化 / @PMO 漏斗 / @PMO 回写
        if any(w in q_low for w in ("自进化", "漏斗", "回写", "measured", "sop")):
            sops = data.get("sop_candidates", [])
            acts = data.get("business_actions", [])
            ready_sops = [sc for sc in sops if sc.weekly_ask_count >= 10 or sc.reject_count >= 3]
            lines = [
                f"**Stage 3 自进化达标池**：共 **{len(ready_sops)} / {len(sops)}** 个专家已达触发阈值（周提问 `≥10次/周` 或 卡片打回 `≥3次`）",
                "",
                "**一、 已达标可立项/固化工作台 SOP 的高频问题榜**：",
            ]
            for sc in ready_sops[:8]:
                lines.append(
                    f"- **[{sc.wave} · {sc.expert_name}]** `{sc.current_stage}`｜提问 **{sc.weekly_ask_count}次/周** · 打回 **{sc.reject_count}次** · 返工率 `{sc.rework_rate_pct}%`\n"
                    f"  └ 高频主题：{sc.topic} → 固化目标：`{sc.target_workbench_sop}`（主责：@{sc.owner}，截止：{sc.due_date}）"
                )
            lines.append("")
            lines.append(f"**二、 品牌市场部业务动作回写账本（measuredActions 累计 {len(acts)} 项）**：")
            for ba in acts[:5]:
                lines.append(
                    f"- **[{ba.expert_name} · {ba.action_type}]** {ba.action_title}（`{ba.receipt_ref}`）→ **{ba.outcome_metric}**"
                )
            return (
                "ABI 14专家自进化漏斗与业务回写账本 (P0-1 & P0-3)",
                "\n".join(lines),
                [("打开 /sop 自进化晋升台与回写账本", "https://pmo.luteos.com/sop")] + default_btns[:2],
                [],
            )

        # 5b. 查询特定负责人名下当期在手接棒任务（如 @PMO 我的任务 / @PMO 周健 / @PMO 吴雨宁 / @PMO 刘华丽 / @PMO 待办）
        if not is_expert_question and any(w in q_low for w in ("待办", "点名", "三棒", "接棒", "todos")):
            from .automation_suite import push_member_baton_todos

            todo_res = push_member_baton_todos(s, push_to_feishu=False)
            return (
                f"ABI 三棒接力当期待办清单 (@吴雨宁 @周健 @刘华丽 · {date.today().isoformat()})",
                todo_res["markdown"],
                default_btns,
                [],
            )

        target_person_q = q_low
        if not is_expert_question and any(w in q_low for w in ("我的任务", "我的排期", "我的项目", "my task")):
            target_person_q = "周健"

        if not is_expert_question:
            for w_item in data.get("owner_workloads", []):
                person_name = w_item["owner"]
                if len(person_name) >= 2 and person_name.lower() in target_person_q:
                    active_steps = []
                    for pv in data["proj_views"]:
                        exp_n = pv["proj"].expert_name
                        for cv in pv["cap_views"]:
                            c = cv["cap"]
                            rel = cv["relay"]
                            for st_obj in rel["steps"]:
                                if st_obj["owner"] == person_name and st_obj["is_active"]:
                                    active_steps.append((exp_n, c, st_obj))

                    today_d = date.today()
                    lines = [
                        f"**成员**：@{person_name}（{w_item.get('role_desc', '')}）",
                        f"**全量工序（49道）**：已交棒 {w_item['done']} / **当期在手接棒 {w_item.get('active_baton', len(active_steps))}** / 待上游交棒 {w_item['plan']}｜工序均分 **{w_item['pct']}%**",
                        "",
                        f"**当前球在 @{person_name} 手里的在手接棒任务（共 {len(active_steps)} 项）**：",
                    ]
                    raw_caps_only = []
                    for exp_n, c, st_obj in active_steps:
                        raw_caps_only.append(c)
                        dl = (date.fromisoformat(st_obj["end_date"]) - today_d).days
                        day_info = f"{st_obj['end_date']} (剩 {dl} 天)" if dl >= 0 else f"{st_obj['end_date']} (已超 {-dl} 天)"
                        lines.append(
                            f"- **[{exp_n}] {c.name}**｜本棒 `{st_obj['step_code']}:{st_obj['pct']}%`（功能总进度 {c.progress_pct}%）｜本棒截止：{day_info}\n"
                            f"  └ 准出交接物：{st_obj['deliverable']}"
                        )
                    return (
                        f"三棒接力当期在手任务清单 · @{person_name}",
                        "\n".join(lines),
                        default_btns,
                        _build_cap_quick_actions(raw_caps_only, max_caps=3),
                    )

        if not is_expert_question and any(w in q_low for w in ("负责人", "负载", "分工", "workload", "owner")):
            lines = ["**3 人三棒接力闭环（P1 吴雨宁 → P2 周健 → P3 刘华丽）工作负载矩阵**：", ""]
            for w_item in data.get("owner_workloads", []):
                lines.append(
                    f"- **@{w_item['owner']}**（{w_item.get('step_code', '')}）：49道工序已交棒 {w_item['done']} / **当期在手接棒 {w_item.get('active_baton', 0)}** / 待上游交棒 {w_item['plan']}｜工序总进度 **{w_item['pct']}%**"
                )
            lines.append("")
            lines.append("可发送 `@PMO 待办`、`@PMO 周健`、`@PMO 吴雨宁` 或 `@PMO 刘华丽` 查看个人当期在手接棒任务并直接点按钮推进交棒。")
            return ("ABI 品牌 Agent 三棒接力负载矩阵", "\n".join(lines), default_btns, [])

        # 6. 若用户显式请求「帮助 / 菜单 / help」或空指令，返回总览菜单；否则一律走 Tier 2 PMO 专家灵魂问答引擎
        if not q or q_low in ("帮助", "菜单", "help", "?", "？", "指令"):
            st = data["stats"]
            help_lines = [
                f"当前纳管 **14 个专家 Agent 产品项目**、**{st['cap_total']} 项功能**、**147 道三棒接力工序**（总进度 **{st['overall_pct']}%**，已实测验证 **{st['cap_verified']} 项**，在线站点 **{st['site_online']}/{st['site_total']}**）。",
                "",
                "**三棒接力闭环机制**：每项功能均按 `P1 吴雨宁（需求/前端/架构 30%） → P2 周健（全栈/飞书Bot/算法 40%） → P3 刘华丽（测试/Agent运营 + 联合吴雨宁推广 30%）` 串联交付；每周一、周三 09:00 自动在群内 @三人 播报当期在手待办。",
                "",
                "**在群内 @PMO 支持以下实时能力**：",
                "- **直接向 @PMO 提问任何架构/契约/红线/导诊问题**（如 `@PMO Radar和Clone交接二创视频要带哪些主键？`、`@PMO 单条视频ROAS 9.0能不能直接加预算？`）",
                "- `@PMO 交棒 <功能名> [交接说明]`：完成当前棒次并自动 `@下一棒` 成员接力",
                "- `@PMO 自进化` 或 `@PMO 漏斗`：查看 14 专家高频问题自进化达标榜与 `measuredActions` 账本",
                "- `@PMO 待办` 或 `@PMO 周健` / `@PMO 吴雨宁` / `@PMO 刘华丽`：查询个人当期在手接棒待办并一键点按钮交棒",
                "- `@PMO 周报` / `@PMO 里程碑` / `@PMO 探活` / `@PMO <项目名>`",
                "- `@PMO 更新 <能力名> <进度%>` 或 `@PMO 阻塞 <能力名> <原因>`",
            ]
            return ("ABI PMO 品牌 & 营销 Agent 统筹与治理专家", "\n".join(help_lines), default_btns, [])

        return answer_as_pmo_expert(s, q, data, default_btns)


def process_incoming_message_event(event_dict: dict) -> dict:
    """处理飞书 im.message.receive_v1 事件（同时兼容 HTTP Webhook 与 WebSocket 长连接）。"""
    header = event_dict.get("header") or {}
    event = event_dict.get("event") or {}
    sender = event.get("sender") or {}
    message = event.get("message") or {}

    # 忽略应用自身发送的消息，防止循环触发
    if sender.get("sender_type") == "app":
        return {"ok": True, "skipped": "app_sender"}

    msg_id = str(message.get("message_id") or header.get("event_id") or "")
    if not _mark_seen(msg_id):
        return {"ok": True, "skipped": "duplicate"}

    chat_type = str(message.get("chat_type") or "")
    chat_id = str(message.get("chat_id") or "")
    mentions = message.get("mentions") or []

    # 群聊中仅当 @PMO 机器人（或消息文本显式含 @PMO / /pmo）时才响应，避免打扰正常群聊
    if chat_type == "group":
        mentioned_bot = False
        for m in mentions:
            mid = m.get("id")
            if isinstance(mid, dict) and mid.get("open_id") == BOT_OPEN_ID:
                mentioned_bot = True
            elif isinstance(mid, str) and mid == BOT_OPEN_ID:
                mentioned_bot = True
            if m.get("name") in ("PMO", "pmo"):
                mentioned_bot = True
        raw_content = str(message.get("content") or "")
        if not mentioned_bot and "PMO" not in raw_content and "pmo" not in raw_content:
            return {"ok": True, "skipped": "not_mentioned"}

    try:
        content_obj = json.loads(message.get("content") or "{}")
    except Exception:
        content_obj = {}

    text = str(content_obj.get("text") or "")
    if not text and isinstance(content_obj.get("content"), list):
        # 富文本 post 提取纯文本
        parts = []
        for line in content_obj["content"]:
            if isinstance(line, list):
                for seg in line:
                    if isinstance(seg, dict) and seg.get("text"):
                        parts.append(str(seg["text"]))
        text = " ".join(parts)

    clean_q = _clean_user_query(text)

    def _async_reply():
        try:
            title, md_body, btns, act_btns = handle_bot_command(clean_q)
            card = build_green_card(title, md_body, btns, action_buttons=act_btns)
            reply_card_to_message(msg_id, card, fallback_chat_id=chat_id)
        except Exception as exc:
            print(f"[feishu-bot] 回复异常: {exc}", flush=True)

    threading.Thread(target=_async_reply, daemon=True).start()
    return {"ok": True, "dispatched": True, "query": clean_q}


def start_ws_client_forever() -> None:
    """使用 lark_oapi.ws.Client 启动飞书长连接事件监听（作为独立守护进程运行，同时监听群消息与卡片按钮回调）。"""
    import lark_oapi as lark
    from lark_oapi.api.im.v1 import P2ImMessageReceiveV1
    from lark_oapi.event.callback.model.p2_card_action_trigger import (
        CallBackToast,
        P2CardActionTrigger,
        P2CardActionTriggerResponse,
    )

    app_id, app_secret, _ = get_feishu_creds()

    def _on_p2_message(data: P2ImMessageReceiveV1) -> None:
        try:
            raw_str = lark.JSON.marshal(data)
            ev_dict = json.loads(raw_str) if raw_str else {}
            process_incoming_message_event(ev_dict)
        except Exception as exc:
            print(f"[feishu-ws] 处理消息异常: {exc}", flush=True)

    def _on_p2_card_action(data: P2CardActionTrigger) -> P2CardActionTriggerResponse:
        resp = P2CardActionTriggerResponse()
        try:
            ev = getattr(data, "event", None)
            act = getattr(ev, "action", None) if ev else None
            op = getattr(ev, "operator", None) if ev else None
            val = (getattr(act, "value", None) or {}) if act else {}
            open_id = (getattr(op, "open_id", "") or "") if op else ""
            res_dict = process_card_action_event(val, operator_open_id=open_id)
            toast_info = res_dict.get("toast") or {"type": "success", "content": "已更新"}
            resp.toast = CallBackToast(toast_info)
        except Exception as exc:
            print(f"[feishu-ws] 处理卡片按钮异常: {exc}", flush=True)
            resp.toast = CallBackToast({"type": "error", "content": f"处理失败: {exc}"})
        return resp

    handler = (
        lark.EventDispatcherHandler.builder("", "")
        .register_p2_im_message_receive_v1(_on_p2_message)
        .register_p2_card_action_trigger(_on_p2_card_action)
        .build()
    )
    cli = lark.ws.Client(
        app_id,
        app_secret,
        event_handler=handler,
        log_level=lark.LogLevel.INFO,
    )
    print(f"[feishu-ws] 启动 PMO 飞书长连接监听 (app_id={app_id})...", flush=True)
    cli.start()


if __name__ == "__main__":
    start_ws_client_forever()
