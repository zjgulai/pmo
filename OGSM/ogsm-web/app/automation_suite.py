"""ABI PMO 门户四大高阶自动化引擎 (V6)。

包含：
1. collect_live_metrics(s): 自动探测线上各专家生产服务 API 与 /reports 最新 HTML 报告，刷新项目实测时间戳与在线状态。
2. sync_feishu_spreadsheet(s, direction): 通过飞书 Sheets OpenAPI 直接与《ABI OGSM 总览表》(FHQ0soq8ghbMQUtZOfYcWetUnIh) 的 XhJUya / 5UK051 页签双向同步（拉取真实负责人与排期 / 写回最新状态与进度%）。
3. run_patrol_and_催办(s, push_to_feishu): 巡检 24 个站点连通性 + 扫描距截止日 <= 7 天（或已逾期）的关键能力，自动生成巡检催办卡并可直推「ABI智能应用与算法组」群。
4. generate_executive_pptx(s): 使用 python-pptx 动态生成 10 页深林绿品牌母版、原生可编辑表格与高清架构图的部门汇报 PPTX。
"""
import io
import json
import ssl
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

from sqlmodel import Session, select

from . import models
from .feishu_bot import build_green_card, get_tenant_access_token, send_card_to_chat

FEISHU_SPREADSHEET_TOKEN = "FHQ0soq8ghbMQUtZOfYcWetUnIh"
SHEET_OGSM_OVERVIEW = "XhJUya"  # OGSM总览 (64行)
SHEET_TASK_PLAN = "5UK051"      # 任务计划（最新）


def _http_json(req: urllib.request.Request, retries: int = 3) -> dict:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    last_err = None
    for _ in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=12, context=ctx) as r:
                return json.loads(r.read().decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            try:
                return json.loads(body)
            except Exception:
                raise RuntimeError(f"HTTP {e.code}: {body[:300]}") from e
        except Exception as e:
            last_err = e
            time.sleep(0.8)
    raise RuntimeError(f"请求失败: {last_err}")


# ─────────────────── 1. 生产端点与实测日报自动采集刷新 ───────────────────


def collect_live_metrics(s: Session) -> dict:
    """探测线上各专家生产服务健康接口与 /reports 最新报告，自动更新项目在线状态与时间戳。"""
    from .main import _probe_single_url, _scan_latest_reports

    projects = s.exec(select(models.ProductProject).order_by(models.ProductProject.sort)).all()
    proj_by_slug = {p.slug: p for p in projects}

    # 1. 探测全部 14 个主工作台实时在线状态
    probed_workbenches = {}
    for p in projects:
        if p.workbench_url:
            res = _probe_single_url(p.workbench_url)
            p.workbench_online = bool(res["ok"])
            probed_workbenches[p.slug] = res

    # 2. 探测特定生产 JSON 端点（Source / Shopify KB）更新实时技术读数
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    live_probes = {}
    try:
        req = urllib.request.Request("https://scrapy.luteos.com/api/health", headers={"User-Agent": "ABI-PMO/6.0"})
        with urllib.request.urlopen(req, timeout=5, context=ctx) as r:
            src_data = json.loads(r.read().decode("utf-8"))
            live_probes["source"] = src_data
    except Exception:
        pass

    try:
        req = urllib.request.Request("https://platform-shopify.luteos.com/api/health", headers={"User-Agent": "ABI-PMO/6.0"})
        with urllib.request.urlopen(req, timeout=5, context=ctx) as r:
            sp_data = json.loads(r.read().decode("utf-8"))
            live_probes["shopify"] = sp_data
    except Exception:
        pass

    # 3. 扫描 /reports 最新报告并绑定
    dir_to_slug = {
        "emily": "emily",
        "vicky": "vicky",
        "echo": "echo",
        "source": "source",
        "守衡": "shouheng",
        "shopify": "shopify",
        "main": "main",
        "know": "daisy",
        "sage": "market",
    }
    scanned = _scan_latest_reports()
    newly_bound = 0
    for item in scanned:
        slug = dir_to_slug.get(item["expert"].lower())
        if not slug or slug not in proj_by_slug:
            continue
        p = proj_by_slug[slug]
        existing = [x.strip() for x in (p.report_links or "").splitlines() if x.strip()]
        if not any(item["url"] in line for line in existing):
            existing.insert(0, f"{item['name']}|{item['url']}")
            p.report_links = "\n".join(existing[:6])
            newly_bound += 1
        p.updated_at = datetime.now(timezone.utc)
        s.add(p)

    s.commit()
    online_cnt = sum(1 for r in probed_workbenches.values() if r["ok"])
    return {
        "ok": True,
        "collected_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "workbenches_total": len(probed_workbenches),
        "workbenches_online": online_cnt,
        "reports_scanned": len(scanned),
        "reports_newly_bound": newly_bound,
        "live_probes": live_probes,
    }


# ─────────────────── 2. 飞书在线表格 (FHQ0soq8ghbMQUtZOfYcWetUnIh) OpenAPI 双向同步 ───────────────────


def sync_feishu_spreadsheet(s: Session, direction: str = "both") -> dict:
    """与飞书在线表格《ABI OGSM 总览表》(FHQ0soq8ghbMQUtZOfYcWetUnIh) 直接双向同步。

    - pull: 从 5UK051（任务计划最新）与 XhJUya（OGSM总览）读取具体负责人（周健/吴雨宁/刘华丽）与未排期项，补齐到数据库。
    - push: 将数据库中 49 项能力的最新状态、进度百分比、起止日期与唯一主责人写回飞书表 XhJUya 对应行（I~N列）。
    """
    token = get_tenant_access_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"}

    all_caps = s.exec(select(models.CapabilityItem)).all()
    cap_by_name = {c.name.strip(): c for c in all_caps}

    # 别名映射（飞书表名称 -> 网站思维导图能力名称）
    alias_map = {
        "TikTok采集": "TikTok 采集MCP/skill",
        "Reddit采集": "Reddit 采集MCP/skill",
        "YouTube采集": "YouTube 采集MCP/skill",
        "Instagram采集": "Instagram 采集MCP/skill",
        "Facebook采集": "Facebook 采集MCP/skill",
        "Google Trends采集": "Google Trends 采集MCP/skill",
        "多渠道数据整合": "多渠道数据查询",
        "PR工作台搭建": "线索管理",
        "竞品洞察监测&风险预警": "舆情预警",
        "IP合作计划制定": "IP 合作计划制定",
        "Agent化改造": "数据查询与分析",
        "Meltwater数据源替代": "线索推荐",
        "对话式CLI界面": "对话式 CLI 界面",
        "各Agent统一接入": "各 Agent 统一接入",
    }

    def _norm(s_val: str) -> str:
        return (s_val or "").strip().replace(" ", "").lower()

    def _find_cap(raw_name: str) -> models.CapabilityItem | None:
        n = (raw_name or "").strip()
        if not n:
            return None
        if n in cap_by_name:
            return cap_by_name[n]
        mapped = alias_map.get(n)
        if mapped and mapped in cap_by_name:
            return cap_by_name[mapped]
        n_norm = _norm(n)
        for k, c_obj in cap_by_name.items():
            k_norm = _norm(k)
            if n_norm == k_norm or n_norm in k_norm or k_norm in n_norm:
                return c_obj
        return None

    pulled_owners = 0
    pulled_dates = 0
    pushed_rows = 0

    # Step A: 从 5UK051（任务计划最新）拉取真实个人负责人（如 吴雨宁 / 周健）
    if direction in ("pull", "both"):
        req_plan = urllib.request.Request(
            f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{FEISHU_SPREADSHEET_TOKEN}/values/{SHEET_TASK_PLAN}!A1:L120?valueRenderOption=FormattedValue",
            headers=headers,
        )
        plan_data = _http_json(req_plan)
        rows_plan = plan_data.get("data", {}).get("valueRange", {}).get("values", [])
        cur_func_name = ""
        owners_by_func: dict[str, list[str]] = {}
        dates_by_func: dict[str, list[str]] = {}

        for row in rows_plan[1:]:
            if not row or not any(row):
                continue
            func_cell = str(row[2] or "").strip() if len(row) > 2 else ""
            if func_cell:
                cur_func_name = func_cell
            if not cur_func_name:
                continue
            s_d = str(row[7] or "").strip()[:10] if len(row) > 7 else ""
            e_d = str(row[8] or "").strip()[:10] if len(row) > 8 else ""
            person = str(row[10] or "").strip() if len(row) > 10 else ""
            if person and person not in owners_by_func.setdefault(cur_func_name, []):
                owners_by_func[cur_func_name].append(person)
            if s_d and len(s_d) == 10:
                dates_by_func.setdefault(cur_func_name, []).append(s_d)
            if e_d and len(e_d) == 10:
                dates_by_func.setdefault(cur_func_name, []).append(e_d)

        VALID_CORE_OWNERS = {"周健", "吴雨宁", "刘华丽"}
        for fname, plist in owners_by_func.items():
            c_obj = _find_cap(fname)
            if not c_obj or not plist:
                continue
            # 若当前能力已绑定 3 人核心团队的唯一主责人（周健/吴雨宁/刘华丽），不再被飞书表的双人混签或外部人员名覆盖
            if (c_obj.owner or "").strip() in VALID_CORE_OWNERS:
                continue
            valid_persons = [p for p in plist if p in VALID_CORE_OWNERS]
            if valid_persons:
                new_owner = valid_persons[0]
                if c_obj.owner != new_owner:
                    old_ow = c_obj.owner
                    c_obj.owner = new_owner
                    s.add(c_obj)
                    s.add(
                        models.ChangeAuditLog(
                            cap_id=c_obj.id or 0,
                            project_slug=c_obj.project_slug,
                            expert_name=c_obj.project_slug.upper(),
                            cap_name=c_obj.name,
                            source="sheet_sync",
                            actor="飞书表 5UK051",
                            summary=f"负责人 {old_ow or '待定'} -> {new_owner}",
                        )
                    )
                    pulled_owners += 1

        for fname, dlist in dates_by_func.items():
            c_obj = _find_cap(fname)
            # 仅当能力尚未设置排期（start_date/end_date 为空）时才从飞书旧表 5UK051 补齐，绝不覆盖 pmo.luteos.com 已校准的 Wave 1-3 甘特排期
            if c_obj and dlist and (not c_obj.start_date or not c_obj.end_date):
                new_sd, new_ed = min(dlist), max(dlist)
                old_ed = c_obj.end_date or "待排期"
                c_obj.start_date = new_sd
                c_obj.end_date = new_ed
                s.add(c_obj)
                s.add(
                    models.ChangeAuditLog(
                        cap_id=c_obj.id or 0,
                        project_slug=c_obj.project_slug,
                        expert_name=c_obj.project_slug.upper(),
                        cap_name=c_obj.name,
                        source="sheet_sync",
                        actor="飞书表 5UK051",
                        summary=f"排期截止 {old_ed} -> {new_ed}",
                    )
                )
                pulled_dates += 1

        s.commit()

    # Step B: 读取 XhJUya（OGSM总览）并将网站最新状态、进度、校准后的起止日期与唯一主责人写回 XhJUya
    req_ov = urllib.request.Request(
        f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{FEISHU_SPREADSHEET_TOKEN}/values/{SHEET_OGSM_OVERVIEW}!A1:N70?valueRenderOption=FormattedValue",
        headers=headers,
    )
    ov_data = _http_json(req_ov)
    rows_ov = ov_data.get("data", {}).get("valueRange", {}).get("values", [])

    value_ranges_to_write = []
    for row_idx, row in enumerate(rows_ov, start=1):
        if row_idx == 1 or not row or len(row) < 3:
            continue
        seq_code = str(row[0] or "").strip()
        node_name = str(row[2] or "").strip()
        # 只处理三级能力叶节点（如 G1.1.1, G3.1.1 等）
        if seq_code.count(".") < 2:
            continue
        c_obj = _find_cap(node_name)
        if not c_obj:
            continue

        if direction in ("pull", "both") and not c_obj.start_date and len(row) >= 13:
            sd = str(row[11] or "").strip()[:10]
            ed = str(row[12] or "").strip()[:10]
            if len(sd) == 10 and len(ed) == 10:
                c_obj.start_date = sd
                c_obj.end_date = ed
                s.add(c_obj)
                pulled_dates += 1

        if direction in ("push", "both"):
            from .main import _compute_cap_relay

            rel = _compute_cap_relay(c_obj, date.today())
            # XhJUya 的 I列(需求状态)、J列(开发/上线状态)、K列(进度)、L列(计划开始)、M列(计划结束)、N列(需求负责人:吴雨宁)、O列(开发&测试闭环:周健/刘华丽)
            feishu_st = "已完成" if c_obj.status == "已完成" else ("进行中" if c_obj.status == "进行中" else "待启动")
            req_st = "已完成" if c_obj.status in ("已完成", "进行中") else "待启动"
            pct_str = f"{c_obj.progress_pct}%"
            req_owner_col = f"吴雨宁 (当前接棒:{rel['active_owner']})" if c_obj.status != "已完成" else "吴雨宁 (已闭环)"
            dev_qa_col = "周健 (开发) / 刘华丽 (测试&运营)"
            value_ranges_to_write.append(
                {
                    "range": f"{SHEET_OGSM_OVERVIEW}!I{row_idx}:O{row_idx}",
                    "values": [[req_st, feishu_st, pct_str, c_obj.start_date or "", c_obj.end_date or "", req_owner_col, dev_qa_col]],
                }
            )
            pushed_rows += 1

    s.commit()

    # Step C: 将全部 49 项功能 × 3 棒 = 147 道成员接力工序完整写回飞书表 5UK051（每一行均填满项目名、产品名与功能点名，零空缺）
    pushed_plan_rows = 0
    if direction in ("push", "both"):
        from .main import build_tree_data

        tree_d = build_tree_data(s)
        plan_matrix = [
            ["项目名称（产品名称）", "产品名称", "功能点", "阶段（三棒工序）", "任务说明（准出交接物）", "当前状态", "完成进度(%)", "计划开始日期", "计划结束日期", "持续天数", "负责人", "备注（当前接棒状态）"]
        ]
        for pv in tree_d["proj_views"]:
            p = pv["proj"]
            for cv in pv["cap_views"]:
                c = cv["cap"]
                rel = cv["relay"]
                for st_item in rel["steps"]:
                    sd_d = date.fromisoformat(st_item["start_date"])
                    ed_d = date.fromisoformat(st_item["end_date"])
                    dur_days = max(1, (ed_d - sd_d).days + 1)
                    plan_matrix.append(
                        [
                            f"{p.product_name}（{p.expert_name}）",
                            p.expert_name,
                            c.name,
                            f"{st_item['step_code']} · {st_item['step_title']}",
                            st_item["deliverable"],
                            "已完成" if st_item["status"] == "已完成" else ("进行中" if st_item["status"] == "进行中" else "待启动"),
                            f"{st_item['pct']}%",
                            st_item["start_date"],
                            st_item["end_date"],
                            str(dur_days),
                            st_item["owner"],
                            "★ 当期在手接棒" if st_item["is_active"] else st_item["collab"],
                        ]
                    )
                    pushed_plan_rows += 1

        try:
            unmerge_req = urllib.request.Request(
                f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{FEISHU_SPREADSHEET_TOKEN}/unmerge_cells",
                data=json.dumps({"range": f"{SHEET_TASK_PLAN}!A2:C160"}).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            _http_json(unmerge_req)
        except Exception:
            pass

        value_ranges_to_write.append(
            {
                "range": f"{SHEET_TASK_PLAN}!A1:L{len(plan_matrix)}",
                "values": plan_matrix,
            }
        )

    write_res = None
    if value_ranges_to_write and direction in ("push", "both"):
        w_req = urllib.request.Request(
            f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{FEISHU_SPREADSHEET_TOKEN}/values_batch_update",
            data=json.dumps({"valueRanges": value_ranges_to_write}).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        write_res = _http_json(w_req)

    return {
        "ok": True,
        "spreadsheet_token": FEISHU_SPREADSHEET_TOKEN,
        "direction": direction,
        "pulled_owners": pulled_owners,
        "pulled_dates": pulled_dates,
        "pushed_rows": pushed_rows,
        "pushed_plan_rows": pushed_plan_rows,
        "feishu_write_code": write_res.get("code") if isinstance(write_res, dict) else 0,
    }


def push_member_baton_todos(s: Session, push_to_feishu: bool = True) -> dict:
    """每周一、周三定时（或手动点击）向飞书群推送 @吴雨宁 @周健 @刘华丽 个人当期在手接棒（Active Baton）待办任务卡片。"""
    from .feishu_bot import _build_cap_quick_actions
    from .main import build_tree_data

    data = build_tree_data(s)
    today_d = date.today()
    weekday_cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][today_d.weekday()]

    md_lines = [
        f"**点名提醒**：**@吴雨宁**（P1 需求/前端/架构 & 终棒推广） · **@周健**（P2 全栈/飞书Bot/算法） · **@刘华丽**（P3 测试/Agent控制台运营）",
        f"**播报基准**：{today_d.isoformat()}（{weekday_cn}例行三棒接力待办清点）｜全站总进度 **{data['stats']['overall_pct']}%**（147 道工序）",
    ]

    urgent_cap_objs = []
    role_order = [
        ("吴雨宁", "P1 需求/前端/数据架构 (+终棒推广)"),
        ("周健", "P2 全栈开发/独立飞书Bot/算法研发"),
        ("刘华丽", "P3 测试验收/Agent控制台运营/高频统计"),
    ]

    for person, role_label in role_order:
        active_items = []
        for pv in data["proj_views"]:
            p = pv["proj"]
            for cv in pv["cap_views"]:
                c = cv["cap"]
                rel = cv["relay"]
                for st_item in rel["steps"]:
                    if st_item["owner"] == person and st_item["is_active"]:
                        ed_d = date.fromisoformat(st_item["end_date"])
                        days_left = (ed_d - today_d).days
                        active_items.append((days_left, p.expert_name, c, st_item))

        active_items.sort(key=lambda x: x[0])
        md_lines.append("")
        md_lines.append(f"**@{person}｜{role_label}（当期在手接棒 {len(active_items)} 项）**：")
        if active_items:
            for dl, exp_name, c_obj, st_item in active_items[:6]:
                if len(urgent_cap_objs) < 3:
                    urgent_cap_objs.append(c_obj)
                dl_tag = f"剩 {dl} 天" if dl >= 0 else f"已超 {-dl} 天"
                ms_tag = "[里程碑] " if c_obj.is_milestone else ""
                md_lines.append(
                    f"- **{st_item['end_date']}**（{dl_tag}）｜{ms_tag}**[{exp_name}] {c_obj.name}** → `{st_item['step_code']}:{st_item['pct']}%`（总进度 {c_obj.progress_pct}%）\n"
                    f"  └ 准出交接物：{st_item['deliverable']}"
                )
            if len(active_items) > 6:
                md_lines.append(f"- *…其余 {len(active_items) - 6} 项远期接棒任务见甘特图个人筛选视图*")
        else:
            md_lines.append("- 当前无阻塞在手接棒项。")

    md_lines.append("")
    md_lines.append("完成本棒工序后，请直接点击下方按钮推进进度（满 30% 自动从吴雨宁交棒给周健，满 70% 自动从周健交棒给刘华丽）。")

    act_btns = _build_cap_quick_actions(urgent_cap_objs, max_caps=3)
    card_title = f"ABI 三棒接力当期待办点名 (@吴雨宁 @周健 @刘华丽 · {today_d.isoformat()} {weekday_cn})"
    markdown_body = "\n".join(md_lines)
    pushed_msg_id = None

    if push_to_feishu:
        card = build_green_card(
            card_title,
            markdown_body,
            [
                ("打开三级串联甘特图按人筛选", "https://pmo.luteos.com/roadmap"),
                ("岗位说明书与自进化漏斗", "https://pmo.luteos.com/sop"),
            ],
            action_buttons=act_btns,
        )
        res = send_card_to_chat(card)
        pushed_msg_id = res.get("data", {}).get("message_id")

    return {
        "ok": True,
        "pushed": bool(pushed_msg_id),
        "message_id": pushed_msg_id,
        "markdown": markdown_body,
    }


# ─────────────────── 3. 24 站点掉线告警 + 临期里程碑飞书群主动催办 ───────────────────


def run_patrol_and_reminder(s: Session, push_to_feishu: bool = False, days_threshold: int = 14) -> dict:
    """执行全站巡检与近期里程碑扫描；若 push_to_feishu=True 则发送提醒卡片到 ABI智能应用与算法组 群。"""
    from .main import api_ping_sites, build_tree_data

    ping_res = api_ping_sites(s)
    data = build_tree_data(s)
    today_d = date.today()

    # 找出公网应当在线但探测失败的站点（排除已知 internal 的 plugin.luteos.com）
    down_sites = []
    for item in data["all_sites"]:
        if item["net"] == "online":
            info = ping_res["results"].get(item["url"])
            if info and not info["ok"]:
                down_sites.append({"expert": item["expert"], "title": item["title"], "url": item["url"], "info": info})

    # 找出距离截止日 <= days_threshold 天且未完成的能力项
    due_soon_caps = []
    due_cap_objs = []
    for pv in data["proj_views"]:
        p = pv["proj"]
        for cv in pv["cap_views"]:
            c = cv["cap"]
            if c.status == "已完成" or not c.end_date:
                continue
            try:
                ed = date.fromisoformat(c.end_date[:10])
            except ValueError:
                continue
            days_left = (ed - today_d).days
            if days_left <= days_threshold:
                due_soon_caps.append(
                    {
                        "cap_obj": c,
                        "expert": p.expert_name,
                        "goal": p.goal_code,
                        "name": c.name,
                        "pct": c.progress_pct,
                        "end_date": c.end_date,
                        "days_left": days_left,
                        "owner": c.owner or p.owner,
                        "is_milestone": c.is_milestone,
                    }
                )
    due_soon_caps.sort(key=lambda x: x["days_left"])
    due_cap_objs = [x["cap_obj"] for x in due_soon_caps]

    md_lines = [
        f"**巡检时间**：{ping_res['checked_at']}",
        f"**站点在线率**：**{ping_res['online']} / {ping_res['total']}** 个站点在线可达",
    ]
    if down_sites:
        md_lines.append("")
        md_lines.append("**站点异常告警（请相关负责人排查）**：")
        for ds in down_sites:
            md_lines.append(f"- **{ds['expert']} · {ds['title']}** (`{ds['url']}`)：探测不可达 ({ds['info'].get('err') or ds['info'].get('code')})")
    else:
        md_lines.append("- 全部 23 个公网工作台与子站均 200 OK 正常在线。")

    md_lines.append("")
    md_lines.append(f"**近 {days_threshold} 天内到期能力与里程碑催办（共 {len(due_soon_caps)} 项）**：")
    if due_soon_caps:
        for item in due_soon_caps[:10]:
            ms_mark = "[里程碑] " if item["is_milestone"] else ""
            day_tag = f"已逾期 {-item['days_left']} 天" if item["days_left"] < 0 else f"剩 {item['days_left']} 天"
            md_lines.append(
                f"- **{item['end_date']}**（{day_tag}）｜{ms_mark}**{item['expert']} · {item['name']}**：当前 **{item['pct']}%**（负责：{item['owner']}）"
            )
    else:
        md_lines.append(f"- 近 {days_threshold} 天内无未完成的临期能力项。")

    md_lines.append("")
    md_lines.append("可直接点击下方卡片按钮免打字更新进度/上报阻塞，或在群内回复 `@PMO 更新 <能力名> <进度%>`。")

    from .feishu_bot import _build_cap_quick_actions

    act_btns = _build_cap_quick_actions(due_cap_objs, max_caps=3)
    card_title = f"ABI PMO 每日站点巡检与里程碑到期提醒 ({today_d.isoformat()})"
    markdown_body = "\n".join(md_lines)
    pushed_msg_id = None

    if push_to_feishu:
        card = build_green_card(
            card_title,
            markdown_body,
            [
                ("打开甘特图与四列看板更新进度", "https://pmo.luteos.com/roadmap"),
                ("打开战略全景导图", "https://pmo.luteos.com/"),
            ],
            action_buttons=act_btns,
        )
        res = send_card_to_chat(card)
        pushed_msg_id = res.get("data", {}).get("message_id")

    return {
        "ok": True,
        "down_sites_count": len(down_sites),
        "due_soon_count": len(due_soon_caps),
        "pushed": bool(pushed_msg_id),
        "message_id": pushed_msg_id,
        "markdown": markdown_body,
        "action_buttons": act_btns,
    }


# ─────────────────── 4. 10 页可编辑部门汇报 PPTX 动态生成器 ───────────────────


def generate_executive_pptx(s: Session) -> bytes:
    """使用 python-pptx 生成 10 页深林绿品牌母版、原生可编辑表格与高清架构图的汇报 PPTX。"""
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import PP_ALIGN
    from pptx.util import Inches, Pt

    from .main import BASE, build_tree_data

    data = build_tree_data(s)
    st = data["stats"]

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # 绿色系品牌色板
    C_FOREST = RGBColor(11, 46, 34)      # #0B2E22
    C_PRIMARY = RGBColor(20, 83, 60)     # #14533C
    C_SAGE_BG = RGBColor(244, 247, 245)  # #F4F7F5
    C_SUBTLE = RGBColor(235, 241, 237)   # #EBF1ED
    C_INK = RGBColor(10, 31, 23)         # #0A1F17
    C_MUTED = RGBColor(82, 102, 91)      # #52665B
    C_WHITE = RGBColor(255, 255, 255)
    C_MINT = RGBColor(167, 243, 208)

    def _add_slide_header(slide, page_tag: str, title_text: str, sub_text: str = ""):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = C_SAGE_BG
        bg.line.fill.background()

        top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.05))
        top_bar.fill.solid()
        top_bar.fill.fore_color.rgb = C_FOREST
        top_bar.line.fill.background()

        tb = slide.shapes.add_textbox(Inches(0.6), Inches(0.18), Inches(12.1), Inches(0.75))
        tf = tb.text_frame
        tf.word_wrap = True
        p0 = tf.paragraphs[0]
        p0.text = f"{page_tag}  |  {title_text}"
        p0.font.size = Pt(20)
        p0.font.bold = True
        p0.font.color.rgb = C_WHITE

        if sub_text:
            p1 = tf.add_paragraph()
            p1.text = sub_text
            p1.font.size = Pt(11)
            p1.font.color.rgb = C_MINT

    def _style_table(table, col_widths: list[float]):
        for idx, w in enumerate(col_widths):
            table.columns[idx].width = Inches(w)
        for r_idx, row in enumerate(table.rows):
            for cell in row.cells:
                cell.fill.solid()
                if r_idx == 0:
                    cell.fill.fore_color.rgb = C_PRIMARY
                elif r_idx % 2 == 1:
                    cell.fill.fore_color.rgb = C_WHITE
                else:
                    cell.fill.fore_color.rgb = C_SUBTLE
                for p in cell.text_frame.paragraphs:
                    p.font.size = Pt(10.5 if r_idx > 0 else 11)
                    p.font.bold = (r_idx == 0)
                    p.font.color.rgb = C_WHITE if r_idx == 0 else C_INK

    # ── Page 1: 封面 ──
    s1 = prs.slides.add_slide(blank_layout)
    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = C_FOREST
    bg1.line.fill.background()

    tb1 = s1.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.3), Inches(4.2))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "ABI 应用与算法组 · 2026Q4 部门项目汇报"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_MINT

    p2 = tf1.add_paragraph()
    p2.text = "品牌 & 营销 Agent 全景统筹与实测成果报告"
    p2.font.size = Pt(36)
    p2.font.bold = True
    p2.font.color.rgb = C_WHITE
    p2.space_before = Pt(16)

    p3 = tf1.add_paragraph()
    p3.text = data["objective"]
    p3.font.size = Pt(16)
    p3.font.color.rgb = C_MINT
    p3.space_before = Pt(20)

    p4 = tf1.add_paragraph()
    p4.text = f"架构基线：1个愿景(O) / 3大业务目标(G) / 6条融合策略(S) / 14个Agent产品工作台 / 49项能力图谱\n生成日期：{date.today().isoformat()}  |  线上门户：https://pmo.luteos.com"
    p4.font.size = Pt(12)
    p4.font.color.rgb = C_WHITE
    p4.space_before = Pt(36)

    # ── Page 2: 总体目标与进展仪表盘 ──
    s2 = prs.slides.add_slide(blank_layout)
    _add_slide_header(s2, "PAGE 02 / 10", "部门定位与本期总体进展仪表盘", data["objective"])

    kpis = [
        ("纳管产品项目", f"{st['project_total']} 个专家 Agent", f"已上线 {st['project_live']} / 进行中 {st['project_doing']} / 方案中 {st['project_plan']}"),
        ("能力图谱总进度", f"{st['overall_pct']}% ({st['cap_done']}/{st['cap_total']})", f"已完成 {st['cap_done']} / 进行中 {st['cap_doing']} / 方案中 {st['cap_plan']}"),
        ("生产实测验证 (ste-zh)", f"{st['cap_verified']} / {st['cap_total']} 已验证", f"关键里程碑 {st['milestone_count']} 个 · 12 份实测报告支撑"),
        ("线上验收工作台", f"{st['site_online']} / {st['site_total']} 在线可达", "全部接入 luteos.com 统一证书与实时探活"),
    ]
    for i, (k_lbl, k_val, k_sub) in enumerate(kpis):
        left = Inches(0.6 + i * 3.08)
        card = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, Inches(1.35), Inches(2.92), Inches(1.65))
        card.fill.solid()
        card.fill.fore_color.rgb = C_WHITE
        card.line.color.rgb = C_PRIMARY
        ctf = card.text_frame
        ctf.word_wrap = True
        cp0 = ctf.paragraphs[0]
        cp0.text = k_lbl
        cp0.font.size = Pt(11)
        cp0.font.color.rgb = C_MUTED
        cp1 = ctf.add_paragraph()
        cp1.text = k_val
        cp1.font.size = Pt(20)
        cp1.font.bold = True
        cp1.font.color.rgb = C_FOREST
        cp1.space_before = Pt(6)
        cp2 = ctf.add_paragraph()
        cp2.text = k_sub
        cp2.font.size = Pt(10)
        cp2.font.color.rgb = C_INK
        cp2.space_before = Pt(6)

    # 三大目标汇总表
    t_shape2 = s2.shapes.add_table(4, 6, Inches(0.6), Inches(3.35), Inches(12.1), Inches(3.5))
    t2 = t_shape2.table
    headers2 = ["目标代号", "业务目标名称", "覆盖产品项目", "能力点数", "已验证数", "综合进度"]
    for c_i, h_txt in enumerate(headers2):
        t2.cell(0, c_i).text = h_txt
    for r_i, gnode in enumerate(data["goal_tree"], start=1):
        g = gnode["goal"]
        p_names = "、".join(pv["proj"].expert_name for pv in gnode["projects"])
        row_vals = [
            g.code,
            g.title,
            p_names,
            f"{gnode['cap_total']} 项 (完成 {gnode['cap_done']})",
            f"{gnode['cap_verified']} / {gnode['cap_total']}",
            f"{gnode['pct']}%",
        ]
        for c_i, val in enumerate(row_vals):
            t2.cell(r_i, c_i).text = val
    _style_table(t2, [1.1, 3.6, 3.2, 1.6, 1.4, 1.2])

    # ── Page 3: 14大产品系统架构与数据流向全景图 ──
    s3 = prs.slides.add_slide(blank_layout)
    _add_slide_header(
        s3,
        "PAGE 03 / 10",
        "产品核心架构：14 大 Agent 与数据流向全景图",
        "顶层统筹与知识门户 → G2 敏捷洞察层 → G1 内容声量层 → G3 合规与独立站 → 底层 70 平台采集中台与研发底座",
    )
    arch_png = BASE / "static" / "abi-arch-diagram.png"
    if arch_png.exists():
        s3.shapes.add_picture(str(arch_png), Inches(0.6), Inches(1.2), height=Inches(5.95))

    # ── Page 4-6: G1 / G2 / G3 三大产品群矩阵 ──
    for idx, gnode in enumerate(data["goal_tree"]):
        g = gnode["goal"]
        sl = prs.slides.add_slide(blank_layout)
        _add_slide_header(
            sl,
            f"PAGE 0{idx + 4} / 10",
            f"产品矩阵与实测成果 · {g.title}",
            f"{g.subtitle}（目标综合进度：{gnode['pct']}%）",
        )
        projs = gnode["projects"]
        t_sh = sl.shapes.add_table(len(projs) + 1, 5, Inches(0.6), Inches(1.25), Inches(12.1), Inches(5.7))
        tb = t_sh.table
        for c_i, h_txt in enumerate(["产品项目 (Agent)", "验收工作台", "状态与进度", "生产实测成果与核心指标 (/reports)", "下一阶段待补齐项"]):
            tb.cell(0, c_i).text = h_txt
        for r_i, pv in enumerate(projs, start=1):
            p = pv["proj"]
            gap_first = pv["gaps_list"][0] if pv["gaps_list"] else "—"
            tb.cell(r_i, 0).text = f"{p.expert_name}\n{p.product_name}"
            tb.cell(r_i, 1).text = (p.workbench_url or "—").replace("https://", "").replace("/", "")
            tb.cell(r_i, 2).text = f"{p.status_summary}\n进度 {pv['pct']}%\n({pv['done_n']}/{pv['total_n']}完成)"
            tb.cell(r_i, 3).text = p.verified_summary[:150] + ("..." if len(p.verified_summary) > 150 else "")
            tb.cell(r_i, 4).text = gap_first[:85]
        _style_table(tb, [1.8, 1.9, 1.3, 4.7, 2.4])

    # ── Page 7: 重点已投产系统实测读数对标 ──
    s7 = prs.slides.add_slide(blank_layout)
    _add_slide_header(s7, "PAGE 07 / 10", "重点专家系统生产实测数据对标（已验证事实）", "所有数字均溯源至 /reports 目录下各专家实测报告")
    t_sh7 = s7.shapes.add_table(8, 4, Inches(0.6), Inches(1.3), Inches(12.1), Inches(5.6))
    tb7 = t_sh7.table
    for c_i, h_txt in enumerate(["专家系统", "线上工作台", "核心实测指标读数", "工程与验证基线"]):
        tb7.cell(0, c_i).text = h_txt
    highlights_rows = [
        ("Source 数据采集中台", "scrapy.luteos.com", "70 平台 / 284 端点 (200 实测) + L2-L4 授权门禁", "39 个 MCP 工具，独立站发现包 + DatasetDrift 漂移告警，2,807 测试"),
        ("Echo VOC 情报系统", "radar.luteos.com", "712.2 万全渠道语料 + v6.4 标签字典 (2,346 行零重复)", "Reddit 10 步全绿日更 (86×提速)，社媒独有 765 类沉默痛点 Gap 雷达"),
        ("Market 市场与经营诊断", "mkt.luteos.com", "DataPilot 24 个月 122 万行核算 (止血 87M / 造血 635M)", "mkt53 三层 TAM (53 证据源) + Sage 53 位跨境专家流 (3,088 测试)"),
        ("Emily + Clone 内容产线", "social / video.luteos.com", "Emily 28/41 能力 + 10 品牌 Token (88分)；Clone 16 节点流水线", "Recipe (13/14 通过) + S1-S5 视频场景 + PendingReview 权利门禁"),
        ("Vicky + GEO + Radar", "pr / geo / magpie.luteos.com", "347 条报道 (S级 100 条) + Perplexity 5/5 基线 + 315 SKU 事实", "Radar 四维达人分层 (Wave-1) + creator_id 授权七元组前置闸门"),
        ("守衡 内容合规与索证", "ca.luteos.com", "两段式引擎 227/227 自证 + 三库 138 条合规规则收编", "集成消毒器 AI Launch Gate (工厂索证 + B1-H 外发门禁 + 104 COS 证据)"),
        ("Daisy + Shopify + Main", "mas / shopify / main.luteos.com", "四层底座 (1,054 算法 Skill / 81 星链 Skill / 72 Hook / 48 路由)", "Shopify 360 审计 (2.2MB 卡点/弃单追回) + Fusion 选品 + 184 Agent 档案"),
    ]
    for r_i, r_vals in enumerate(highlights_rows, start=1):
        for c_i, val in enumerate(r_vals):
            tb7.cell(r_i, c_i).text = val
    _style_table(tb7, [2.2, 2.2, 4.0, 3.7])

    # ── Page 8: 2026Q4 关键里程碑排期表 ──
    s8 = prs.slides.add_slide(blank_layout)
    _add_slide_header(s8, "PAGE 08 / 10", "2026Q4 关键里程碑节点排期与达成表", f"共设置 {len(data['milestones'])} 个关键里程碑节点")
    ms_slice = data["milestones"][:10]
    t_sh8 = s8.shapes.add_table(len(ms_slice) + 1, 6, Inches(0.6), Inches(1.3), Inches(12.1), Inches(5.6))
    tb8 = t_sh8.table
    for c_i, h_txt in enumerate(["计划截止日", "目标", "专家项目", "关键里程碑能力名称", "负责团队", "当前状态与进度"]):
        tb8.cell(0, c_i).text = h_txt
    for r_i, mv in enumerate(ms_slice, start=1):
        c = mv["cap"]
        tb8.cell(r_i, 0).text = c.end_date or "待排期"
        tb8.cell(r_i, 1).text = mv["goal_code"]
        tb8.cell(r_i, 2).text = mv["proj_expert"]
        tb8.cell(r_i, 3).text = f"{c.name}：{c.description[:42]}"
        tb8.cell(r_i, 4).text = c.owner
        tb8.cell(r_i, 5).text = f"{c.status} ({c.progress_pct}%) · {c.verify_state}"
    _style_table(tb8, [1.5, 0.9, 1.4, 4.7, 1.6, 2.0])

    # ── Page 9: 风险敞口与跨项目待补齐卡点 ──
    s9 = prs.slides.add_slide(blank_layout)
    _add_slide_header(s9, "PAGE 09 / 10", "跨项目核心待补齐卡点与所需支持", "如实披露当前未完成项与跨组数据依赖")
    blockers = data["radar_focus"]["top_blockers"]
    t_sh9 = s9.shapes.add_table(len(blockers) + 1, 3, Inches(0.6), Inches(1.35), Inches(12.1), Inches(5.3))
    tb9 = t_sh9.table
    for c_i, h_txt in enumerate(["所属目标", "产品项目", "当前首要待补齐卡点与协同需求"]):
        tb9.cell(0, c_i).text = h_txt
    for r_i, b in enumerate(blockers, start=1):
        tb9.cell(r_i, 0).text = b["goal"]
        tb9.cell(r_i, 1).text = b["expert"]
        tb9.cell(r_i, 2).text = b["gap"]
    _style_table(tb9, [1.3, 1.8, 9.0])

    # ── Page 10: 总结与 11-12 月行动计划 ──
    s10 = prs.slides.add_slide(blank_layout)
    _add_slide_header(s10, "PAGE 10 / 10", "2026Q4 (11–12月) 三大收口行动项", "以 PMO 门户与飞书机器人为常态化统筹抓手，每周五 09:00 自动出报对账")
    actions_data = [
        ("行动 1：推进方案中项目按期交付 (GEO / Radar / Signal)", "GEO 按 6 步链路在 11–12 月完成问句库、采集探针与可见度月报交付；Signal 基于 Source 采集底座在 11 月底前上线品牌曝光热度日趋势与异动归因；Radar 完成 IP 合作计划与动态监测。"),
        ("行动 2：打通跨项目产品主数据 (SPU/SKU) 关联", "解决当前 Vicky 报道表「品线字段 0% 覆盖」与 Echo 帖子「产品型号绑定率低 (2/56)」的共性断点，由 Source 统一提供标准产品型号字典供各 Agent 引用。"),
        ("行动 3：补齐视频语音审查与多智能体统一入口", "守衡按 T-430~T-435 顺序完成视频抽帧与语音转文字 (ASR) 接入，解除视频「未审查」状态；Daisy 在 12 月完成 9 个专家 Agent 的适配层接入与对话式 CLI 统一交互界面。"),
    ]
    for i, (act_title, act_desc) in enumerate(actions_data):
        top = Inches(1.45 + i * 1.85)
        box = s10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), top, Inches(12.1), Inches(1.6))
        box.fill.solid()
        box.fill.fore_color.rgb = C_WHITE
        box.line.color.rgb = C_PRIMARY
        btf = box.text_frame
        btf.word_wrap = True
        bp0 = btf.paragraphs[0]
        bp0.text = act_title
        bp0.font.size = Pt(15)
        bp0.font.bold = True
        bp0.font.color.rgb = C_FOREST
        bp1 = btf.add_paragraph()
        bp1.text = act_desc
        bp1.font.size = Pt(12)
        bp1.font.color.rgb = C_INK
        bp1.space_before = Pt(8)

    out_stream = io.BytesIO()
    prs.save(out_stream)
    return out_stream.getvalue()
