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


def build_green_card(title: str, markdown_body: str, buttons: list[tuple[str, str]] | None = None) -> dict:
    """构建零 Emoji、深林绿主题的飞书交互卡片。"""
    elements: list[dict] = [{"tag": "markdown", "content": markdown_body}]
    if buttons:
        elements.append({"tag": "hr"})
        actions = []
        for idx, (label, url) in enumerate(buttons):
            actions.append(
                {
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": label},
                    "type": "primary" if idx == 0 else "default",
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


def handle_bot_command(query: str) -> tuple[str, str, list[tuple[str, str]]]:
    """根据群成员 @PMO 的指令生成卡片 (title, markdown_body, buttons)。"""
    from .main import api_ping_sites, build_tree_data, generate_weekly_brief

    q = query.strip()
    q_low = q.lower()
    default_btns = [
        ("打开 PMO 战略全景导图", "https://pmo.luteos.com/"),
        ("甘特图与四列看板", "https://pmo.luteos.com/roadmap"),
        ("14大产品系统架构图", "https://pmo.luteos.com/sites"),
    ]

    with Session(engine) as s:
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
            return (
                f"PMO 能力进度已更新 · {target_cap.name}",
                (
                    f"- **能力名称**：{target_cap.name}（所属项目：`{target_cap.project_slug.upper()}`）\n"
                    f"- **进度变更**：`{old_pct}%` → **`{new_pct}%`**\n"
                    f"- **状态变更**：`{old_status}` → **`{target_cap.status}`**\n"
                    f"- **截止排期**：{target_cap.end_date or '待排期'}（负责：{target_cap.owner or '待定'}）"
                ),
                default_btns,
            )

        # 2. 周报 / 进度 / 汇总
        if any(w in q_low for w in ("周报", "简报", "进度", "汇总", "总览", "ogsm", "report", "status")):
            brief = generate_weekly_brief(s)
            return (
                f"ABI 品牌 & 营销 Agent 周度进展与里程碑简报 ({date.today().isoformat()})",
                brief["markdown"],
                default_btns,
            )

        # 3. 里程碑 / 甘特 / 排期
        if any(w in q_low for w in ("里程碑", "甘特", "排期", "到期", "milestone", "gantt")):
            data = build_tree_data(s)
            lines = [
                f"**总体排期覆盖度**：{data['stats']['scheduled_count']} / {data['stats']['cap_total']} 项已排期（总加权进度 **{data['stats']['overall_pct']}%**）",
                "",
                "**近 4 周待交付关键里程碑 (Milestone)**：",
            ]
            for m in data["radar_focus"]["upcoming_milestones"]:
                c = m["cap"]
                lines.append(
                    f"- **{c.end_date}**（剩 {m['days_left']} 天）｜**{m['proj_expert']} · {c.name}**：当前 **{c.progress_pct}%**（{c.owner}）"
                )
            return ("ABI 2026Q4 关键里程碑与甘特排期", "\n".join(lines), default_btns)

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
            return ("ABI 24 个线上工作台与子站实时探活报告", "\n".join(lines), default_btns)

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
            )

        # 4c. 站点巡检与里程碑催办：@PMO 巡检 / @PMO 催办
        if any(w in q_low for w in ("巡检", "催办", "提醒", "patrol")):
            from .automation_suite import run_patrol_and_reminder

            pat_res = run_patrol_and_reminder(s, push_to_feishu=False, days_threshold=14)
            return ("ABI PMO 站点巡检与临期里程碑催办", pat_res["markdown"], default_btns)

        # 5. 查询特定专家项目（如 @PMO Emily / Echo / 守衡 / Source / Vicky / GEO / Shopify...）
        data = build_tree_data(s)
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
                    "**能力图谱与排期明细**：",
                ]
                for c in pv["caps"]:
                    ms_tag = "[里程碑] " if c.is_milestone else ""
                    lines.append(
                        f"- {ms_tag}**{c.name}**：`{c.status} {c.progress_pct}%`（{c.verify_state}，截止：{c.end_date or '待排期'}）"
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
                return (f"{p.expert_name} · {p.product_name} 项目详情", "\n".join(lines), btns)

        # 5b. 查询特定负责人名下任务（如 @PMO 周健 / @PMO 吴雨宁 / @PMO 李倩怡 / @PMO 刘华丽 / @PMO 负责人）
        for w_item in data.get("owner_workloads", []):
            person_name = w_item["owner"]
            if len(person_name) >= 2 and person_name.lower() in q_low:
                person_caps = [
                    (pv["proj"].expert_name, c)
                    for pv in data["proj_views"]
                    for c in pv["caps"]
                    if person_name in (c.owner or pv["proj"].owner or "")
                ]
                lines = [
                    f"**负责人**：{person_name}｜**名下能力总数**：{w_item['total']} 项（已完成 {w_item['done']} / 进行中 {w_item['doing']} / 方案中 {w_item['plan']}，平均进度 **{w_item['pct']}%**）",
                    "",
                    "**名下能力排期明细**：",
                ]
                for exp_n, c in person_caps:
                    lines.append(
                        f"- **[{exp_n}] {c.name}**：`{c.status} {c.progress_pct}%`（截止：{c.end_date or '待排期'}）"
                    )
                return (f"负责人工作负载与任务清单 · {person_name}", "\n".join(lines), default_btns)

        if any(w in q_low for w in ("负责人", "负载", "分工", "workload", "owner")):
            lines = ["**各负责人工作负载与平均完成度**：", ""]
            for w_item in data.get("owner_workloads", []):
                lines.append(
                    f"- **{w_item['owner']}**：共 **{w_item['total']}** 项（已完成 {w_item['done']} / 进行中 {w_item['doing']} / 方案中 {w_item['plan']}）｜平均进度 **{w_item['pct']}%**"
                )
            lines.append("")
            lines.append("可发送 `@PMO 周健` 或 `@PMO 吴雨宁` 查看个人名下具体能力排期。")
            return ("ABI 品牌 Agent 负责人工作负载矩阵", "\n".join(lines), default_btns)

        # 6. 默认帮助与总览菜单
        st = data["stats"]
        help_lines = [
            f"当前纳管 **14 个专家 Agent 产品项目**、**{st['cap_total']} 项能力图谱**（总进度 **{st['overall_pct']}%**，已实测验证 **{st['cap_verified']} 项**，在线站点 **{st['site_online']}/{st['site_total']}**）。",
            "",
            "**在群内 @PMO 支持以下实时指令**：",
            "- `@PMO 周报` 或 `@PMO 进度`：获取最新周度进展对比与里程碑简报",
            "- `@PMO 里程碑` 或 `@PMO 甘特`：查看近 4 周待交付关键里程碑排期",
            "- `@PMO 探活`：实时并发检测全部 24 个工作台站点 HTTP 状态与延迟",
            "- `@PMO <项目名>`（如 `@PMO Emily`、`@PMO Echo`、`@PMO 守衡`、`@PMO Source`）：查询指定专家项目的能力进度与实测报告",
            "- `@PMO 更新 <能力名> <进度%>`（如 `@PMO 更新 采集探针 50%`）：在群内直接更新能力进度并同步至甘特图与看板",
        ]
        return ("ABI PMO 品牌 & 营销 Agent 统筹助手", "\n".join(help_lines), default_btns)


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
            title, md_body, btns = handle_bot_command(clean_q)
            card = build_green_card(title, md_body, btns)
            reply_card_to_message(msg_id, card, fallback_chat_id=chat_id)
        except Exception as exc:
            print(f"[feishu-bot] 回复异常: {exc}", flush=True)

    threading.Thread(target=_async_reply, daemon=True).start()
    return {"ok": True, "dispatched": True, "query": clean_q}


def start_ws_client_forever() -> None:
    """使用 lark_oapi.ws.Client 启动飞书长连接事件监听（作为独立守护进程运行）。"""
    import lark_oapi as lark
    from lark_oapi.api.im.v1 import P2ImMessageReceiveV1

    app_id, app_secret, _ = get_feishu_creds()

    def _on_p2_message(data: P2ImMessageReceiveV1) -> None:
        try:
            raw_str = lark.JSON.marshal(data)
            ev_dict = json.loads(raw_str) if raw_str else {}
            process_incoming_message_event(ev_dict)
        except Exception as exc:
            print(f"[feishu-ws] 处理消息异常: {exc}", flush=True)

    handler = (
        lark.EventDispatcherHandler.builder("", "")
        .register_p2_im_message_receive_v1(_on_p2_message)
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
