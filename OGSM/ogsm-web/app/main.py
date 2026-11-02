"""ABI 品牌 & 营销 Agent 多项目管理与汇报门户 (V3)。

第一性原理与奥卡姆剃刀架构：
1. 宏观到微观唯一主干：O(愿景) → G1~G3(目标) → S1~S6(专家融合策略) → 14个Agent产品项目 → 49项能力图谱。
2. 49项能力图谱同源驱动五大视图：战略全景导图(/)、产品与场景流水线(/projects)、甘特图与四列看板(/roadmap)、里程碑汇报演示(/present)、PMO行内直改与维护(/admin)。
3. 自动化能力：23个工作台并发实时探活(/api/ping-sites)、甘特/看板行内无刷新修改(/api/cap/{id}/inline)、飞书对齐CSV一键导出(/api/export.csv)。
"""
import concurrent.futures
import csv
import io
import os
import ssl
import time
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

from fastapi import Body, Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import BadSignature, URLSafeSerializer
from sqlmodel import Session, select

from . import models
from .db import get_session
from .seed import OBJECTIVE_TEXT, seed

app = FastAPI(title="ABI 品牌 & 营销 Agent 项目管理门户")
BASE = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE / "templates"))
templates.env.cache = None

app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")

PMO_PASSWORD = os.getenv("OGSM_PMO_PASSWORD", "pmo")
SECRET = os.getenv("SECRET_KEY", "change-me-in-production")
signer = URLSafeSerializer(SECRET, salt="ogsm-pmo")

REPO_ROOT = Path(os.getenv("OGSM_DOCS_DIR", str(BASE.parent.parent)))
OGSM_DOCS_DIR = REPO_ROOT / "OGSM" if (REPO_ROOT / "OGSM").exists() else REPO_ROOT
REPORTS_DIR = REPO_ROOT / "reports"

# 甘特图时间轴范围：2026-08-01 至 2026-12-31（共 153 天）
GANTT_START = date(2026, 8, 1)
GANTT_END = date(2026, 12, 31)
GANTT_TOTAL_DAYS = (GANTT_END - GANTT_START).days + 1


def render(request: Request, name: str, context: dict, status_code: int = 200):
    return templates.TemplateResponse(
        request=request, name=name, context=context, status_code=status_code
    )


def is_pmo(request: Request) -> bool:
    raw = request.cookies.get("ogsm_pmo")
    if not raw:
        return False
    try:
        return signer.loads(raw) == "pmo"
    except BadSignature:
        return False


def _parse_pipe_lines(raw: str, cols: int) -> list[list[str]]:
    out = []
    for line in (raw or "").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split("|")]
        while len(parts) < cols:
            parts.append("")
        out.append(parts[:cols])
    return out


def _parse_date(d_str: str) -> date | None:
    if not d_str or not d_str.strip():
        return None
    try:
        return date.fromisoformat(d_str.strip()[:10])
    except ValueError:
        return None


def _calc_gantt_bar(start_str: str, end_str: str, today_d: date, status: str) -> dict:
    """计算甘特图横条的百分比位置、宽度与逾期状态。"""
    sd = _parse_date(start_str)
    ed = _parse_date(end_str)
    if not sd or not ed or ed < sd:
        return {"has_schedule": False, "left_pct": 0, "width_pct": 0, "is_overdue": False}

    clamped_s = max(GANTT_START, min(GANTT_END, sd))
    clamped_e = max(GANTT_START, min(GANTT_END, ed))
    left_days = (clamped_s - GANTT_START).days
    span_days = max(2, (clamped_e - clamped_s).days + 1)

    left_pct = round(left_days / GANTT_TOTAL_DAYS * 100, 2)
    width_pct = round(min(100 - left_pct, span_days / GANTT_TOTAL_DAYS * 100), 2)
    is_overdue = (ed < today_d) and (status != "已完成")

    return {
        "has_schedule": True,
        "left_pct": left_pct,
        "width_pct": width_pct,
        "is_overdue": is_overdue,
        "start_short": sd.strftime("%m/%d"),
        "end_short": ed.strftime("%m/%d"),
    }


def _kanban_col_for(c: models.CapabilityItem) -> str:
    """四列看板归类：
    1. plan: 方案中
    2. doing: 进行中（研发实现中，进度 < 80%）
    3. pending_verify: 联调收口 / 待最终验收（已完成但未实测验证，或进行中且进度 >= 80%）
    4. verified: 已完成且已验证（生产实测通过）
    """
    if c.status == "已完成":
        return "verified" if c.verify_state == "已验证" else "pending_verify"
    if c.status == "进行中":
        if (c.progress_pct or 0) >= 80:
            return "pending_verify"
        return "doing"
    return "plan"


def build_tree_data(s: Session) -> dict:
    """加载完整 OGSM 树、甘特图坐标、四列看板与统计概览。"""
    today_d = date.today()
    today_clamped = max(GANTT_START, min(GANTT_END, today_d))
    today_pct = round((today_clamped - GANTT_START).days / GANTT_TOTAL_DAYS * 100, 2)

    goals = s.exec(select(models.GoalGroup).order_by(models.GoalGroup.sort)).all()
    strategies = s.exec(select(models.StrategyGroup).order_by(models.StrategyGroup.sort)).all()
    projects = s.exec(select(models.ProductProject).order_by(models.ProductProject.sort)).all()
    caps = s.exec(select(models.CapabilityItem).order_by(models.CapabilityItem.sort)).all()

    proj_map = {p.slug: p for p in projects}
    caps_by_proj: dict[str, list[dict]] = {}

    kanban_cols: dict[str, list[dict]] = {
        "plan": [],
        "doing": [],
        "pending_verify": [],
        "verified": [],
    }
    milestones = []
    overdue_count = 0
    scheduled_count = 0

    for c in caps:
        gbar = _calc_gantt_bar(c.start_date, c.end_date, today_d, c.status)
        if gbar["has_schedule"]:
            scheduled_count += 1
        if gbar["is_overdue"]:
            overdue_count += 1
        kcol = _kanban_col_for(c)
        p_obj = proj_map.get(c.project_slug)

        c_view = {
            "cap": c,
            "gbar": gbar,
            "kcol": kcol,
            "proj_expert": p_obj.expert_name if p_obj else c.project_slug,
            "proj_name": p_obj.product_name if p_obj else "",
            "goal_code": p_obj.goal_code if p_obj else "G1",
            "workbench_url": p_obj.workbench_url if p_obj else "",
        }
        caps_by_proj.setdefault(c.project_slug, []).append(c_view)
        kanban_cols[kcol].append(c_view)
        if c.is_milestone:
            milestones.append(c_view)

    # 按截止日期排序里程碑
    milestones.sort(key=lambda x: x["cap"].end_date or "9999-12-31")

    proj_views = []
    proj_by_strat: dict[str, list[dict]] = {}
    proj_by_goal: dict[str, list[dict]] = {}
    all_sites = []

    for p in projects:
        p_cap_views = caps_by_proj.get(p.slug, [])
        p_caps = [cv["cap"] for cv in p_cap_views]
        done_n = sum(1 for c in p_caps if c.status == "已完成")
        doing_n = sum(1 for c in p_caps if c.status == "进行中")
        plan_n = sum(1 for c in p_caps if c.status == "方案中")
        verified_n = sum(1 for c in p_caps if c.verify_state == "已验证")
        total_n = len(p_caps)
        avg_pct = int(round(sum(c.progress_pct or 0 for c in p_caps) / total_n)) if total_n else 0

        # 计算项目级汇总甘特条（取所有子能力最早 start_date 和最晚 end_date）
        valid_starts = [c.start_date for c in p_caps if _parse_date(c.start_date)]
        valid_ends = [c.end_date for c in p_caps if _parse_date(c.end_date)]
        proj_start = min(valid_starts) if valid_starts else ""
        proj_end = max(valid_ends) if valid_ends else ""
        proj_gbar = _calc_gantt_bar(
            proj_start,
            proj_end,
            today_d,
            "已完成" if done_n == total_n and total_n > 0 else "进行中",
        )

        # 按业务场景分组能力，并拆解场景步骤节点（供自动化流水线图渲染）
        scen_groups: dict[str, dict] = {}
        for cv in p_cap_views:
            c = cv["cap"]
            key = c.scenario_line or "核心业务场景"
            if key not in scen_groups:
                raw_steps = [s.strip() for s in key.replace("->", "→").split("→") if s.strip()]
                scen_groups[key] = {"steps": raw_steps, "cap_views": []}
            scen_groups[key]["cap_views"].append(cv)

        extra_sites = _parse_pipe_lines(p.extra_sites, 3)
        if p.workbench_url:
            all_sites.append(
                {
                    "expert": p.expert_name,
                    "title": p.product_name,
                    "url": p.workbench_url,
                    "kind": "主工作台",
                    "goal": p.goal_code,
                    "net": "online" if p.workbench_online else "internal",
                }
            )
        for es in extra_sites:
            all_sites.append(
                {
                    "expert": p.expert_name,
                    "title": es[0],
                    "url": es[1],
                    "kind": "关联子平台",
                    "goal": p.goal_code,
                    "net": es[2] or "online",
                }
            )

        pv = {
            "proj": p,
            "cap_views": p_cap_views,
            "caps": p_caps,
            "scen_groups": scen_groups,
            "done_n": done_n,
            "doing_n": doing_n,
            "plan_n": plan_n,
            "verified_n": verified_n,
            "total_n": total_n,
            "pct": avg_pct,
            "proj_start": proj_start,
            "proj_end": proj_end,
            "proj_gbar": proj_gbar,
            "scenarios_list": [x.strip() for x in (p.scenarios or "").splitlines() if x.strip()],
            "metrics_list": _parse_pipe_lines(p.metrics_highlights, 3),
            "gaps_list": [x.strip() for x in (p.pending_gaps or "").splitlines() if x.strip()],
            "reports_list": _parse_pipe_lines(p.report_links, 2),
            "extra_sites": extra_sites,
            "support_list": [x.strip() for x in (p.support_notes or "").splitlines() if x.strip()],
        }
        proj_views.append(pv)
        proj_by_strat.setdefault(p.strategy_code, []).append(pv)
        proj_by_goal.setdefault(p.goal_code, []).append(pv)

    strat_by_goal: dict[str, list[dict]] = {}
    for st in strategies:
        s_projs = proj_by_strat.get(st.code, [])
        s_caps = [c for pv in s_projs for c in pv["caps"]]
        s_total = len(s_caps)
        s_pct = int(round(sum(c.progress_pct or 0 for c in s_caps) / s_total)) if s_total else 0
        strat_by_goal.setdefault(st.goal_code, []).append(
            {
                "strat": st,
                "projects": s_projs,
                "cap_total": s_total,
                "cap_done": sum(1 for c in s_caps if c.status == "已完成"),
                "pct": s_pct,
            }
        )

    goal_tree = []
    for g in goals:
        g_projs = proj_by_goal.get(g.code, [])
        g_caps = [c for pv in g_projs for c in pv["caps"]]
        g_total = len(g_caps)
        g_done = sum(1 for c in g_caps if c.status == "已完成")
        g_doing = sum(1 for c in g_caps if c.status == "进行中")
        g_plan = sum(1 for c in g_caps if c.status == "方案中")
        g_verified = sum(1 for c in g_caps if c.verify_state == "已验证")
        g_pct = int(round(sum(c.progress_pct or 0 for c in g_caps) / g_total)) if g_total else 0
        goal_tree.append(
            {
                "goal": g,
                "strategies": strat_by_goal.get(g.code, []),
                "projects": g_projs,
                "proj_count": len(g_projs),
                "cap_done": g_done,
                "cap_doing": g_doing,
                "cap_plan": g_plan,
                "cap_verified": g_verified,
                "cap_total": g_total,
                "pct": g_pct,
                "done_pct": round(g_done / g_total * 100, 1) if g_total else 0,
                "doing_pct": round(g_doing / g_total * 100, 1) if g_total else 0,
                "plan_pct": round(g_plan / g_total * 100, 1) if g_total else 0,
            }
        )

    total_caps = len(caps)
    overall_pct = int(round(sum(c.progress_pct or 0 for c in caps) / total_caps)) if total_caps else 0

    stats = {
        "project_total": len(projects),
        "project_live": sum(1 for p in projects if p.status_summary == "已上线"),
        "project_doing": sum(1 for p in projects if p.status_summary == "进行中"),
        "project_plan": sum(1 for p in projects if p.status_summary == "方案中"),
        "cap_total": total_caps,
        "cap_done": sum(1 for c in caps if c.status == "已完成"),
        "cap_doing": sum(1 for c in caps if c.status == "进行中"),
        "cap_plan": sum(1 for c in caps if c.status == "方案中"),
        "cap_verified": sum(1 for c in caps if c.verify_state == "已验证"),
        "overall_pct": overall_pct,
        "scheduled_count": scheduled_count,
        "unscheduled_count": total_caps - scheduled_count,
        "milestone_count": len(milestones),
        "overdue_count": overdue_count,
        "site_total": len(all_sites),
        "site_online": sum(1 for s_item in all_sites if s_item["net"] == "online"),
        "kanban_counts": {k: len(v) for k, v in kanban_cols.items()},
    }

    # 甘特图顶部月份刻度（2026年8月~12月）
    gantt_months = [
        {"label": "2026年 8月", "sub": "基建与底座铺垫", "width_pct": round(31 / GANTT_TOTAL_DAYS * 100, 2)},
        {"label": "2026年 9月", "sub": "核心引擎开发", "width_pct": round(30 / GANTT_TOTAL_DAYS * 100, 2)},
        {"label": "2026年 10月", "sub": "工作台上线与实测", "width_pct": round(31 / GANTT_TOTAL_DAYS * 100, 2)},
        {"label": "2026年 11月 (当月)", "sub": "二期深化与探针交付", "width_pct": round(30 / GANTT_TOTAL_DAYS * 100, 2)},
        {"label": "2026年 12月", "sub": "全链路收口与复测", "width_pct": round(31 / GANTT_TOTAL_DAYS * 100, 2)},
    ]

    return {
        "objective": OBJECTIVE_TEXT,
        "goal_tree": goal_tree,
        "goals": goals,
        "strategies": strategies,
        "proj_views": proj_views,
        "kanban_cols": kanban_cols,
        "milestones": milestones,
        "gantt_months": gantt_months,
        "today_pct": today_pct,
        "stats": stats,
        "all_sites": all_sites,
    }


def ctx(request: Request, session: Session, active_nav: str = "mindmap", **kw) -> dict:
    data = build_tree_data(session)
    data.update(
        {
            "request": request,
            "is_pmo": is_pmo(request),
            "active_nav": active_nav,
            "today": date.today().isoformat(),
        }
    )
    data.update(kw)
    return data


# ───────────────────────────── 四大核心页面 ─────────────────────────────


@app.get("/", response_class=HTMLResponse)
def overview_mindmap(request: Request, s: Session = Depends(get_session)):
    """页面 1：战略全景导图（宏观到微观战略分解图 + 自动化漏斗 + 9 级交互式思维导图）。"""
    return render(request, "mindmap.html", ctx(request, s, active_nav="mindmap"))


@app.get("/projects", response_class=HTMLResponse)
def projects_matrix(request: Request, goal: str = "", status: str = "", s: Session = Depends(get_session)):
    """页面 2：14 大产品与业务场景自动化流水线矩阵。"""
    return render(
        request,
        "projects.html",
        ctx(request, s, active_nav="projects", filter_goal=goal, filter_status=status),
    )


@app.get("/roadmap", response_class=HTMLResponse)
def roadmap_gantt_kanban(request: Request, view: str = "gantt", s: Session = Depends(get_session)):
    """页面 3：项目甘特图（两级折叠+今日红线+里程碑）与四列敏捷看板（支持行内直改）。"""
    return render(
        request,
        "roadmap.html",
        ctx(request, s, active_nav="roadmap", current_view=view),
    )


@app.get("/present", response_class=HTMLResponse)
def presentation_mode(request: Request, s: Session = Depends(get_session)):
    """页面 4：里程碑汇报演示页（10页汇报法则 + 里程碑时间轴 + 实测报告中心）。"""
    return render(request, "present.html", ctx(request, s, active_nav="present"))


@app.get("/sites", response_class=HTMLResponse)
def workbenches_directory(request: Request, s: Session = Depends(get_session)):
    """23 个线上工作台与子平台实时探活面板。"""
    return render(request, "sites.html", ctx(request, s, active_nav="sites"))


# 兼容旧路由自动跳转
@app.get("/board")
@app.get("/lines")
@app.get("/experts")
@app.get("/baselines")
@app.get("/metrics")
def legacy_redirect():
    return RedirectResponse("/roadmap", status_code=302)


# ───────────────────────────── 自动化 API（行内直改 / 实时探活 / CSV 导出） ─────────────────────────────


@app.post("/api/cap/{cap_id}/inline")
def inline_update_capability(
    cap_id: int,
    request: Request,
    payload: dict = Body(...),
    s: Session = Depends(get_session),
):
    """在甘特图或看板上行内直接修改能力点的状态、验证态、进度百分比、起止日期、负责人与里程碑。"""
    if not is_pmo(request):
        return JSONResponse({"ok": False, "error": "需要先登录 PMO 维护账号"}, status_code=403)

    c = s.get(models.CapabilityItem, cap_id)
    if not c:
        return JSONResponse({"ok": False, "error": "未找到该能力点"}, status_code=404)

    if "status" in payload and payload["status"] in ("已完成", "进行中", "方案中"):
        c.status = payload["status"]
        if c.status == "已完成" and (c.progress_pct or 0) < 100:
            c.progress_pct = 100
    if "verify_state" in payload and payload["verify_state"] in ("已验证", "部分验证", "待验证"):
        c.verify_state = payload["verify_state"]
    if "progress_pct" in payload:
        try:
            c.progress_pct = max(0, min(100, int(payload["progress_pct"])))
        except (ValueError, TypeError):
            pass
    if "start_date" in payload:
        c.start_date = str(payload["start_date"] or "").strip()[:10]
    if "end_date" in payload:
        c.end_date = str(payload["end_date"] or "").strip()[:10]
    if "owner" in payload:
        c.owner = str(payload["owner"] or "").strip()[:40]
    if "is_milestone" in payload:
        c.is_milestone = bool(payload["is_milestone"])

    # 看板四列拖拽快捷映射
    if "kcol" in payload:
        kcol = payload["kcol"]
        if kcol == "plan":
            c.status = "方案中"
            c.verify_state = "待验证"
            if c.progress_pct == 100:
                c.progress_pct = 20
        elif kcol == "doing":
            c.status = "进行中"
            c.verify_state = "部分验证"
            if c.progress_pct in (0, 100):
                c.progress_pct = 60
        elif kcol == "pending_verify":
            c.status = "已完成"
            c.verify_state = "部分验证"
            c.progress_pct = 95
        elif kcol == "verified":
            c.status = "已完成"
            c.verify_state = "已验证"
            c.progress_pct = 100

    s.add(c)
    s.commit()
    s.refresh(c)
    return {
        "ok": True,
        "id": c.id,
        "status": c.status,
        "verify_state": c.verify_state,
        "progress_pct": c.progress_pct,
        "start_date": c.start_date,
        "end_date": c.end_date,
        "owner": c.owner,
        "is_milestone": c.is_milestone,
        "kcol": _kanban_col_for(c),
    }


def _probe_single_url(url: str) -> dict:
    ctx_ssl = ssl.create_default_context()
    ctx_ssl.check_hostname = False
    ctx_ssl.verify_mode = ssl.CERT_NONE
    t0 = time.monotonic()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ABI-PMO-HealthMonitor/3.0"})
        with urllib.request.urlopen(req, timeout=4.5, context=ctx_ssl) as resp:
            ms = int((time.monotonic() - t0) * 1000)
            return {"url": url, "ok": 200 <= resp.status < 400, "code": resp.status, "ms": ms}
    except Exception as e:
        ms = int((time.monotonic() - t0) * 1000)
        code = getattr(e, "code", 0) or 0
        return {"url": url, "ok": False, "code": code, "ms": ms, "err": type(e).__name__}


@app.get("/api/ping-sites")
def api_ping_sites(s: Session = Depends(get_session)):
    """并发实时探测全部 23 个工作台与子平台的 HTTP 状态码与响应延迟。"""
    data = build_tree_data(s)
    urls = sorted({item["url"] for item in data["all_sites"] if item["url"]})
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        futs = {pool.submit(_probe_single_url, u): u for u in urls}
        for fut in concurrent.futures.as_completed(futs):
            res = fut.result()
            results[res["url"]] = res
    online_n = sum(1 for r in results.values() if r["ok"])
    return {
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total": len(results),
        "online": online_n,
        "results": results,
    }


@app.get("/api/export.csv")
def export_ogsm_csv(s: Session = Depends(get_session)):
    """一键导出与飞书 OGSM 总览表结构对齐的 CSV 台账。"""
    data = build_tree_data(s)
    buf = io.StringIO()
    buf.write("﻿")  # UTF-8 BOM for Excel / Feishu
    writer = csv.writer(buf)
    writer.writerow(
        [
            "序号",
            "目标(G)",
            "策略(S)",
            "专家代号",
            "产品项目名称",
            "验收工作台",
            "业务场景线",
            "能力图谱名称",
            "能力说明",
            "开发状态",
            "验证状态",
            "进度%",
            "开始日期",
            "截止日期",
            "负责团队",
            "是否里程碑",
            "待整合子平台",
        ]
    )
    seq = 1
    for gnode in data["goal_tree"]:
        g_code = gnode["goal"].code
        for pv in gnode["projects"]:
            p = pv["proj"]
            for cv in pv["cap_views"]:
                c = cv["cap"]
                writer.writerow(
                    [
                        seq,
                        g_code,
                        p.strategy_code,
                        p.expert_name,
                        p.product_name,
                        p.workbench_url,
                        c.scenario_line,
                        c.name,
                        c.description,
                        c.status,
                        c.verify_state,
                        f"{c.progress_pct}%",
                        c.start_date or "待排期",
                        c.end_date or "待排期",
                        c.owner or p.owner,
                        "是" if c.is_milestone else "否",
                        f"{c.integration_name} ({c.integration_url})" if c.integration_name else "",
                    ]
                )
                seq += 1
    return Response(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="ABI_OGSM_2026Q4_Capabilities.csv"'},
    )


# ───────────────────────────── 实测报告与文档查阅 ─────────────────────────────


@app.get("/docs", response_class=HTMLResponse)
def docs_index(request: Request, s: Session = Depends(get_session)):
    report_files = []
    if REPORTS_DIR.exists():
        for p in sorted(REPORTS_DIR.rglob("*.html")):
            rel = p.relative_to(REPORTS_DIR)
            expert = rel.parts[0] if len(rel.parts) > 1 else "综合"
            report_files.append(
                {
                    "expert": expert,
                    "name": p.name,
                    "rel": str(rel),
                    "size_kb": round(p.stat().st_size / 1024, 1),
                    "mtime": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                }
            )

    doc_files = []
    if OGSM_DOCS_DIR.exists():
        for p in sorted(OGSM_DOCS_DIR.rglob("*.md")):
            if "ogsm-web" in p.parts:
                continue
            rel = p.relative_to(OGSM_DOCS_DIR)
            doc_files.append(
                {
                    "name": str(rel),
                    "size_kb": round(p.stat().st_size / 1024, 1),
                    "mtime": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                }
            )

    return render(
        request,
        "docs.html",
        ctx(request, s, active_nav="docs", report_files=report_files, doc_files=doc_files),
    )


@app.get("/reports-view/{expert}/{filename}", response_class=HTMLResponse)
def view_expert_report(expert: str, filename: str):
    target = (REPORTS_DIR / expert / filename).resolve()
    if not target.exists() or REPORTS_DIR.resolve() not in target.parents:
        return RedirectResponse("/docs", status_code=303)
    return HTMLResponse(target.read_text(encoding="utf-8", errors="replace"))


@app.get("/docs/{name:path}", response_class=HTMLResponse)
def docs_view(name: str, request: Request, s: Session = Depends(get_session)):
    p = (OGSM_DOCS_DIR / name).resolve()
    if not p.exists() or p.suffix != ".md" or OGSM_DOCS_DIR.resolve() not in p.parents:
        return RedirectResponse("/docs", status_code=303)
    text = p.read_text(encoding="utf-8", errors="replace")
    return render(request, "doc.html", ctx(request, s, active_nav="docs", name=name, text=text))


# ───────────────────────────── PMO 管理后台 ─────────────────────────────


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request, s: Session = Depends(get_session)):
    return render(request, "login.html", ctx(request, s, active_nav="admin", err=None))


@app.post("/login")
def login(request: Request, password: str = Form(...), s: Session = Depends(get_session)):
    if password != PMO_PASSWORD:
        return render(
            request,
            "login.html",
            ctx(request, s, active_nav="admin", err="口令不正确"),
            status_code=401,
        )
    resp = RedirectResponse("/roadmap", status_code=303)
    resp.set_cookie("ogsm_pmo", signer.dumps("pmo"), httponly=True, samesite="lax", max_age=86400 * 7)
    return resp


@app.get("/logout")
def logout():
    resp = RedirectResponse("/", status_code=303)
    resp.delete_cookie("ogsm_pmo")
    return resp


@app.get("/admin", response_class=HTMLResponse)
def admin_panel(request: Request, s: Session = Depends(get_session)):
    if not is_pmo(request):
        return RedirectResponse("/login", status_code=303)
    return render(request, "admin.html", ctx(request, s, active_nav="admin"))


@app.post("/admin/project/{project_id}")
def update_project(
    project_id: int,
    request: Request,
    product_name: str = Form(...),
    workbench_url: str = Form(default=""),
    status_summary: str = Form(default="进行中"),
    owner: str = Form(default=""),
    scenarios: str = Form(default=""),
    verified_summary: str = Form(default=""),
    pending_gaps: str = Form(default=""),
    s: Session = Depends(get_session),
):
    if not is_pmo(request):
        return RedirectResponse("/login", status_code=303)
    p = s.get(models.ProductProject, project_id)
    if p:
        p.product_name = product_name.strip() or p.product_name
        p.workbench_url = workbench_url.strip()
        p.status_summary = status_summary
        p.owner = owner.strip()
        p.scenarios = scenarios.strip()
        p.verified_summary = verified_summary.strip()
        p.pending_gaps = pending_gaps.strip()
        p.updated_at = datetime.now(timezone.utc)
        s.add(p)
        s.commit()
    return RedirectResponse("/admin#proj-" + (p.slug if p else ""), status_code=303)


@app.post("/admin/capability/{cap_id}")
def update_capability(
    cap_id: int,
    request: Request,
    name: str = Form(...),
    description: str = Form(default=""),
    status: str = Form(default="进行中"),
    verify_state: str = Form(default="已验证"),
    progress_pct: int = Form(default=0),
    start_date: str = Form(default=""),
    end_date: str = Form(default=""),
    owner: str = Form(default=""),
    is_milestone: str = Form(default=""),
    integration_name: str = Form(default=""),
    integration_url: str = Form(default=""),
    s: Session = Depends(get_session),
):
    if not is_pmo(request):
        return RedirectResponse("/login", status_code=303)
    c = s.get(models.CapabilityItem, cap_id)
    if c:
        c.name = name.strip() or c.name
        c.description = description.strip()
        c.status = status
        c.verify_state = verify_state
        c.progress_pct = max(0, min(100, int(progress_pct or 0)))
        c.start_date = start_date.strip()[:10]
        c.end_date = end_date.strip()[:10]
        c.owner = owner.strip()
        c.is_milestone = is_milestone == "on"
        c.integration_name = integration_name.strip()
        c.integration_url = integration_url.strip()
        s.add(c)
        s.commit()
    return RedirectResponse("/admin#proj-" + (c.project_slug if c else ""), status_code=303)


@app.post("/admin/capability-add")
def add_capability(
    request: Request,
    project_slug: str = Form(...),
    scenario_line: str = Form(default=""),
    name: str = Form(...),
    description: str = Form(default=""),
    status: str = Form(default="方案中"),
    verify_state: str = Form(default="待验证"),
    progress_pct: int = Form(default=0),
    start_date: str = Form(default=""),
    end_date: str = Form(default=""),
    owner: str = Form(default=""),
    s: Session = Depends(get_session),
):
    if not is_pmo(request):
        return RedirectResponse("/login", status_code=303)
    if name.strip():
        s.add(
            models.CapabilityItem(
                project_slug=project_slug,
                scenario_line=scenario_line.strip(),
                name=name.strip(),
                description=description.strip(),
                status=status,
                verify_state=verify_state,
                progress_pct=max(0, min(100, int(progress_pct or 0))),
                start_date=start_date.strip()[:10],
                end_date=end_date.strip()[:10],
                owner=owner.strip(),
                sort=99,
            )
        )
        s.commit()
    return RedirectResponse(f"/admin#proj-{project_slug}", status_code=303)


@app.post("/admin/reset-seed")
def reset_seed_data(request: Request):
    if not is_pmo(request):
        return RedirectResponse("/login", status_code=303)
    seed(force_reset=True)
    return RedirectResponse("/roadmap", status_code=303)


@app.get("/health")
def health():
    return {"ok": True}
