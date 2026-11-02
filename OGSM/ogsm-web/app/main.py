"""ABI 品牌 & 营销 Agent 多项目管理与汇报门户 (V4)。

核心能力：
1. 紧凑一屏全景导图 (/) + 右侧滑出详情抽屉（点击任意 Agent 或能力胶囊即刻在右侧展开完整详情，无需跳页）。
2. 业务场景-能力图谱可视化装配图 (/projects)：每个场景步骤工位下方直接挂载对应的能力模块与通电进度。
3. 实测报告页内同屏预览器：点击任意 /reports 实测报告直接在页内分屏/浮层渲染 HTML，告别切标签页。
4. PMO 本周焦点与风险雷达栏：自动聚合「近25天到期里程碑 + 核心阻塞卡点 + 最新实测报告动态」。
5. 一键进度快照与周报对比生成 (/api/snapshot/save & /api/weekly-brief)：自动对比上次快照，生成可一键复制到飞书群的 Markdown 简报。
"""
import concurrent.futures
import csv
import io
import json
import os
import ssl
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone
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
    if c.status == "已完成":
        return "verified" if c.verify_state == "已验证" else "pending_verify"
    if c.status == "进行中":
        if (c.progress_pct or 0) >= 80:
            return "pending_verify"
        return "doing"
    return "plan"


def _assemble_scenario_stations(steps: list[str], cap_views: list[dict]) -> list[dict]:
    """将业务场景的步骤条（Step 1 → Step 2...）与该场景下的能力模块精准装配到对应工位。"""
    if not steps:
        steps = ["核心能力工位"]
    stations = [{"step_name": s, "caps": [], "state": "plan", "pct": 0} for s in steps]
    n_st = len(stations)
    n_caps = len(cap_views)

    for idx, cv in enumerate(cap_views):
        c_name = cv["cap"].name
        best_st = None
        best_score = 0
        for st_obj in stations:
            st_clean = st_obj["step_name"].split("：")[-1].strip()
            # 用 2 字词片只在能力标题(c_name)上计算重合度，避免长描述里的通用词误吸
            grams = {st_clean[i : i + 2] for i in range(max(1, len(st_clean) - 1)) if len(st_clean[i : i + 2]) == 2}
            score = sum(2 for g in grams if g in c_name)
            if score > best_score:
                best_score = score
                best_st = st_obj
        if best_st is not None and best_score > 0:
            best_st["caps"].append(cv)
        else:
            # 按顺序均匀落位到空工位或对应比例工位
            empty_sts = [s for s in stations if not s["caps"]]
            if empty_sts and n_caps >= n_st:
                empty_sts[0]["caps"].append(cv)
            else:
                target_idx = min(n_st - 1, int(idx * n_st / max(1, n_caps)))
                stations[target_idx]["caps"].append(cv)

    all_pct = int(round(sum(x["cap"].progress_pct or 0 for x in cap_views) / max(1, n_caps)))
    for i, st_obj in enumerate(stations):
        scaps = st_obj["caps"]
        if scaps:
            pct = int(round(sum(x["cap"].progress_pct or 0 for x in scaps) / len(scaps)))
            st_obj["pct"] = pct
            if all(x["cap"].status == "已完成" for x in scaps):
                st_obj["state"] = "done"
            elif any(x["cap"].status in ("已完成", "进行中") for x in scaps):
                st_obj["state"] = "doing"
            else:
                st_obj["state"] = "plan"
        else:
            threshold = int((i + 1) / n_st * 100)
            st_obj["pct"] = all_pct
            if all_pct >= threshold:
                st_obj["state"] = "done"
            elif all_pct >= max(10, threshold - 45):
                st_obj["state"] = "doing"
            else:
                st_obj["state"] = "plan"
    return stations


def _scan_latest_reports() -> list[dict]:
    """自动扫描 /reports 目录下所有 HTML 报告，按修改时间倒序排列。"""
    items = []
    if REPORTS_DIR.exists():
        for p in REPORTS_DIR.rglob("*.html"):
            rel = p.relative_to(REPORTS_DIR)
            expert = rel.parts[0] if len(rel.parts) > 1 else "综合"
            mtime_ts = p.stat().st_mtime
            items.append(
                {
                    "expert": expert,
                    "name": p.name.replace(".html", ""),
                    "filename": p.name,
                    "url": f"/reports-view/{rel}",
                    "size_kb": round(p.stat().st_size / 1024, 1),
                    "mtime": datetime.fromtimestamp(mtime_ts).strftime("%m-%d %H:%M"),
                    "mtime_ts": mtime_ts,
                }
            )
    items.sort(key=lambda x: x["mtime_ts"], reverse=True)
    return items


def build_tree_data(s: Session) -> dict:
    """加载完整 OGSM 树、场景装配图、PMO 焦点雷达、抽屉 JSON 与甘特看板数据。"""
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
    upcoming_milestones = []
    overdue_count = 0
    scheduled_count = 0
    soon_cutoff = today_d + timedelta(days=28)

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
            ed = _parse_date(c.end_date)
            if ed and today_d <= ed <= soon_cutoff and c.status != "已完成":
                days_left = (ed - today_d).days
                upcoming_milestones.append({**c_view, "days_left": days_left})

    milestones.sort(key=lambda x: x["cap"].end_date or "9999-12-31")
    upcoming_milestones.sort(key=lambda x: x["days_left"])

    proj_views = []
    proj_by_strat: dict[str, list[dict]] = {}
    proj_by_goal: dict[str, list[dict]] = {}
    all_sites = []
    drawer_dict = {}
    top_blockers = []

    for p in projects:
        p_cap_views = caps_by_proj.get(p.slug, [])
        p_caps = [cv["cap"] for cv in p_cap_views]
        done_n = sum(1 for c in p_caps if c.status == "已完成")
        doing_n = sum(1 for c in p_caps if c.status == "进行中")
        plan_n = sum(1 for c in p_caps if c.status == "方案中")
        verified_n = sum(1 for c in p_caps if c.verify_state == "已验证")
        total_n = len(p_caps)
        avg_pct = int(round(sum(c.progress_pct or 0 for c in p_caps) / total_n)) if total_n else 0

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

        scen_groups: dict[str, dict] = {}
        for cv in p_cap_views:
            c = cv["cap"]
            key = c.scenario_line or "核心业务场景"
            if key not in scen_groups:
                raw_steps = [s_step.strip() for s_step in key.replace("->", "→").split("→") if s_step.strip()]
                scen_groups[key] = {"steps": raw_steps, "cap_views": [], "stations": []}
            scen_groups[key]["cap_views"].append(cv)

        for key, sgrp in scen_groups.items():
            sgrp["stations"] = _assemble_scenario_stations(sgrp["steps"], sgrp["cap_views"])

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

        metrics_list = _parse_pipe_lines(p.metrics_highlights, 3)
        gaps_list = [x.strip() for x in (p.pending_gaps or "").splitlines() if x.strip()]
        reports_list = _parse_pipe_lines(p.report_links, 2)
        support_list = [x.strip() for x in (p.support_notes or "").splitlines() if x.strip()]

        if gaps_list:
            top_blockers.append(
                {
                    "slug": p.slug,
                    "expert": p.expert_name,
                    "goal": p.goal_code,
                    "gap": gaps_list[0],
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
            "metrics_list": metrics_list,
            "gaps_list": gaps_list,
            "reports_list": reports_list,
            "extra_sites": extra_sites,
            "support_list": support_list,
        }
        proj_views.append(pv)
        proj_by_strat.setdefault(p.strategy_code, []).append(pv)
        proj_by_goal.setdefault(p.goal_code, []).append(pv)

        # 供前端右侧抽屉零延迟渲染的序列化数据
        drawer_dict[p.slug] = {
            "slug": p.slug,
            "expert": p.expert_name,
            "product_name": p.product_name,
            "goal_code": p.goal_code,
            "strategy_code": p.strategy_code,
            "status_summary": p.status_summary,
            "owner": p.owner,
            "pct": avg_pct,
            "workbench_url": p.workbench_url,
            "extra_sites": extra_sites,
            "verified_summary": p.verified_summary,
            "metrics": metrics_list,
            "gaps": gaps_list,
            "reports": reports_list,
            "support": support_list,
            "caps": [
                {
                    "id": c.id,
                    "name": c.name,
                    "desc": c.description,
                    "scenario": c.scenario_line,
                    "status": c.status,
                    "verify_state": c.verify_state,
                    "pct": c.progress_pct,
                    "start_date": c.start_date,
                    "end_date": c.end_date,
                    "owner": c.owner or p.owner,
                    "is_milestone": c.is_milestone,
                    "integ_name": c.integration_name,
                    "integ_url": c.integration_url,
                }
                for c in p_caps
            ],
        }

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

    latest_reports = _scan_latest_reports()

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
        "upcoming_ms_count": len(upcoming_milestones),
        "overdue_count": overdue_count,
        "site_total": len(all_sites),
        "site_online": sum(1 for s_item in all_sites if s_item["net"] == "online"),
        "kanban_counts": {k: len(v) for k, v in kanban_cols.items()},
    }

    gantt_months = [
        {"label": "2026年 8月", "sub": "基建与底座铺垫", "width_pct": round(31 / GANTT_TOTAL_DAYS * 100, 2)},
        {"label": "2026年 9月", "sub": "核心引擎开发", "width_pct": round(30 / GANTT_TOTAL_DAYS * 100, 2)},
        {"label": "2026年 10月", "sub": "工作台上线与实测", "width_pct": round(31 / GANTT_TOTAL_DAYS * 100, 2)},
        {"label": "2026年 11月 (当月)", "sub": "二期深化与探针交付", "width_pct": round(30 / GANTT_TOTAL_DAYS * 100, 2)},
        {"label": "2026年 12月", "sub": "全链路收口与复测", "width_pct": round(31 / GANTT_TOTAL_DAYS * 100, 2)},
    ]

    radar_focus = {
        "upcoming_milestones": upcoming_milestones[:6],
        "top_blockers": top_blockers[:6],
        "latest_reports": latest_reports[:6],
    }

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
        "radar_focus": radar_focus,
        "drawer_json": json.dumps(drawer_dict, ensure_ascii=False),
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
    """页面 1：紧凑一屏战略全景导图 + PMO 本周焦点雷达 + 右侧滑出详情抽屉。"""
    return render(request, "mindmap.html", ctx(request, s, active_nav="mindmap"))


@app.get("/projects", response_class=HTMLResponse)
def projects_matrix(request: Request, goal: str = "", status: str = "", s: Session = Depends(get_session)):
    """页面 2：14 大产品与「业务场景-能力图谱可视化装配流水线」矩阵。"""
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
    """页面 4：里程碑汇报演示页 + 一键周报快照生成。"""
    return render(request, "present.html", ctx(request, s, active_nav="present"))


@app.get("/sites", response_class=HTMLResponse)
def workbenches_directory(request: Request, s: Session = Depends(get_session)):
    return render(request, "sites.html", ctx(request, s, active_nav="sites"))


@app.get("/board")
@app.get("/lines")
@app.get("/experts")
@app.get("/baselines")
@app.get("/metrics")
def legacy_redirect():
    return RedirectResponse("/roadmap", status_code=302)


# ───────────────────────────── 自动化 API（行内直改 / 探活 / 周报快照对比 / CSV） ─────────────────────────────


@app.post("/api/cap/{cap_id}/inline")
def inline_update_capability(
    cap_id: int,
    request: Request,
    payload: dict = Body(...),
    s: Session = Depends(get_session),
):
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
            c.status = "进行中"
            c.verify_state = "已验证"
            if (c.progress_pct or 0) < 85:
                c.progress_pct = 85
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


def _build_snapshot_payload(data: dict) -> dict:
    out = {}
    for pv in data["proj_views"]:
        p = pv["proj"]
        for c in pv["caps"]:
            out[str(c.id)] = {
                "name": c.name,
                "expert": p.expert_name,
                "goal": p.goal_code,
                "status": c.status,
                "verify_state": c.verify_state,
                "pct": c.progress_pct or 0,
                "end_date": c.end_date or "",
            }
    return out


@app.post("/api/snapshot/save")
def save_progress_snapshot(s: Session = Depends(get_session)):
    """保存当前时刻的 49 项能力进度快照，用于后续周报对比。"""
    data = build_tree_data(s)
    st = data["stats"]
    payload = _build_snapshot_payload(data)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    snap = models.ProgressSnapshot(
        label=f"快照 {now_str}",
        overall_pct=st["overall_pct"],
        done_count=st["cap_done"],
        verified_count=st["cap_verified"],
        payload_json=json.dumps(payload, ensure_ascii=False),
    )
    s.add(snap)
    s.commit()
    s.refresh(snap)
    return {"ok": True, "id": snap.id, "label": snap.label, "overall_pct": snap.overall_pct}


@app.get("/api/weekly-brief")
def generate_weekly_brief(s: Session = Depends(get_session)):
    """自动对比最近一次历史快照，生成无 AI 味的《ABI 品牌 Agent 周度进展与里程碑简报》。"""
    data = build_tree_data(s)
    st = data["stats"]
    cur_map = _build_snapshot_payload(data)

    snaps = s.exec(
        select(models.ProgressSnapshot).order_by(models.ProgressSnapshot.id.desc())
    ).all()
    prev_snap = snaps[0] if snaps else None

    diffs = []
    if prev_snap and prev_snap.payload_json:
        try:
            prev_map = json.loads(prev_snap.payload_json)
            for cid, cur in cur_map.items():
                old = prev_map.get(cid)
                if not old:
                    diffs.append(f"- 新增能力点：**{cur['expert']} · {cur['name']}**（当前 {cur['pct']}%）")
                elif (
                    cur["pct"] != old.get("pct")
                    or cur["status"] != old.get("status")
                    or cur["verify_state"] != old.get("verify_state")
                ):
                    diffs.append(
                        f"- **{cur['expert']} · {cur['name']}**：进度 `{old.get('pct')}% → {cur['pct']}%`，"
                        f"状态 `{old.get('status')} → {cur['status']}`（{cur['verify_state']}）"
                    )
        except Exception:
            pass

    lines = [
        f"# ABI 品牌 & 营销 Agent 周度进展与里程碑简报（{date.today().isoformat()}）",
        "",
        "## 一、 总体进度读数",
        f"- **纳管产品项目**：{st['project_total']} 个专家 Agent（已上线 {st['project_live']} / 进行中 {st['project_doing']} / 方案中 {st['project_plan']}）",
        f"- **能力图谱总进度**：**{st['overall_pct']}%**（共 {st['cap_total']} 项：已完成 {st['cap_done']} 项 / 进行中 {st['cap_doing']} 项 / 方案中 {st['cap_plan']} 项）",
        f"- **生产实测验证（ste-zh 口径）**：**{st['cap_verified']} / {st['cap_total']} 项已验证**",
        f"- **验收工作台连通性**：{st['site_online']} / {st['site_total']} 个站点在线可达",
        "",
    ]

    if prev_snap:
        delta_pct = st["overall_pct"] - prev_snap.overall_pct
        sign = "+" if delta_pct >= 0 else ""
        lines.append(f"## 二、 相比上次快照（{prev_snap.label}）的进度变化（总进度 {sign}{delta_pct}%）")
        if diffs:
            lines.extend(diffs)
        else:
            lines.append("- 本窗口内暂无能力点状态或百分比变动（可在甘特图/看板中直接修改进度后再对比）。")
        lines.append("")
    else:
        lines.append("## 二、 快照对比")
        lines.append("- 当前尚无历史基准快照。点击弹窗左下角「保存当前为基准快照」即可记录基线。")
        lines.append("")

    lines.append("## 三、 近 4 周即将到期的关键里程碑（💎 Milestone）")
    if data["radar_focus"]["upcoming_milestones"]:
        for m in data["radar_focus"]["upcoming_milestones"]:
            c = m["cap"]
            lines.append(
                f"- **{c.end_date}**（剩 {m['days_left']} 天）｜**{m['proj_expert']} · {c.name}**：当前 {c.progress_pct}%（{c.owner}）"
            )
    else:
        lines.append("- 近 4 周内无待交付里程碑。")
    lines.append("")

    lines.append("## 四、 跨项目核心待补齐卡点（需协同支持）")
    for b in data["radar_focus"]["top_blockers"]:
        lines.append(f"- **[{b['goal']} · {b['expert']}]** {b['gap']}")

    return {
        "ok": True,
        "has_prev": prev_snap is not None,
        "prev_label": prev_snap.label if prev_snap else "无历史快照",
        "markdown": "\n".join(lines),
    }


def _probe_single_url(url: str) -> dict:
    ctx_ssl = ssl.create_default_context()
    ctx_ssl.check_hostname = False
    ctx_ssl.verify_mode = ssl.CERT_NONE
    t0 = time.monotonic()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ABI-PMO-HealthMonitor/4.0"})
        with urllib.request.urlopen(req, timeout=4.5, context=ctx_ssl) as resp:
            ms = int((time.monotonic() - t0) * 1000)
            return {"url": url, "ok": 200 <= resp.status < 400, "code": resp.status, "ms": ms}
    except Exception as e:
        ms = int((time.monotonic() - t0) * 1000)
        code = getattr(e, "code", 0) or 0
        return {"url": url, "ok": False, "code": code, "ms": ms, "err": type(e).__name__}


@app.get("/api/ping-sites")
def api_ping_sites(s: Session = Depends(get_session)):
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
    data = build_tree_data(s)
    buf = io.StringIO()
    buf.write("﻿")
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
    report_files = _scan_latest_reports()
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
    resp = RedirectResponse("/", status_code=303)
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
    return RedirectResponse("/", status_code=303)


@app.get("/health")
def health():
    return {"ok": True}
