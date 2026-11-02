"""ABI 品牌 & 营销 Agent 多项目管理与汇报门户 (V2)。

设计核心：
1. 严格以《ABIOGSM-品牌Agent》思维导图为唯一主骨架（O → G1~G3 → 6条融合策略 → 14个产品项目）
2. 以「产品名称（专家代号 + 产品构成）」为项目管理单元，直连 20+ 个线上验收工作台
3. 深度整合 /reports 目录下的实测成果，遵循附件2（格赖斯准则 + lieflat 去 AI 味 + ste-zh 规范）
"""
import os
from datetime import date, datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
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

# /docs 挂载到仓库根（容器内为 /docs，本地为 /Users/lute/Project/PMO）
REPO_ROOT = Path(os.getenv("OGSM_DOCS_DIR", str(BASE.parent.parent)))
OGSM_DOCS_DIR = REPO_ROOT / "OGSM" if (REPO_ROOT / "OGSM").exists() else REPO_ROOT
REPORTS_DIR = REPO_ROOT / "reports"


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


def build_tree_data(s: Session) -> dict:
    """加载完整 OGSM 树与统计概览。"""
    goals = s.exec(select(models.GoalGroup).order_by(models.GoalGroup.sort)).all()
    strategies = s.exec(select(models.StrategyGroup).order_by(models.StrategyGroup.sort)).all()
    projects = s.exec(select(models.ProductProject).order_by(models.ProductProject.sort)).all()
    caps = s.exec(select(models.CapabilityItem).order_by(models.CapabilityItem.sort)).all()

    caps_by_proj: dict[str, list[models.CapabilityItem]] = {}
    for c in caps:
        caps_by_proj.setdefault(c.project_slug, []).append(c)

    # 为每个项目预解析多字段与能力进度统计
    proj_views = []
    proj_by_strat: dict[str, list[dict]] = {}
    proj_by_goal: dict[str, list[dict]] = {}

    all_sites = []
    for p in projects:
        p_caps = caps_by_proj.get(p.slug, [])
        done_n = sum(1 for c in p_caps if c.status == "已完成")
        doing_n = sum(1 for c in p_caps if c.status == "进行中")
        plan_n = sum(1 for c in p_caps if c.status == "方案中")
        total_n = len(p_caps)
        pct = int(round((done_n + doing_n * 0.5) / total_n * 100)) if total_n else 0

        # 按业务场景分组能力
        scen_groups: dict[str, list[models.CapabilityItem]] = {}
        for c in p_caps:
            key = c.scenario_line or "核心能力"
            scen_groups.setdefault(key, []).append(c)

        extra_sites = _parse_pipe_lines(p.extra_sites, 3)
        if p.workbench_url:
            all_sites.append((p.expert_name, p.product_name, p.workbench_url, "online" if p.workbench_online else "internal"))
        for es in extra_sites:
            all_sites.append((p.expert_name, es[0], es[1], es[2] or "online"))

        pv = {
            "proj": p,
            "caps": p_caps,
            "scen_groups": scen_groups,
            "done_n": done_n,
            "doing_n": doing_n,
            "plan_n": plan_n,
            "total_n": total_n,
            "pct": pct,
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
        strat_by_goal.setdefault(st.goal_code, []).append(
            {"strat": st, "projects": proj_by_strat.get(st.code, [])}
        )

    goal_tree = []
    for g in goals:
        g_projs = proj_by_goal.get(g.code, [])
        g_caps = [c for pv in g_projs for c in pv["caps"]]
        goal_tree.append(
            {
                "goal": g,
                "strategies": strat_by_goal.get(g.code, []),
                "projects": g_projs,
                "proj_count": len(g_projs),
                "cap_done": sum(1 for c in g_caps if c.status == "已完成"),
                "cap_doing": sum(1 for c in g_caps if c.status == "进行中"),
                "cap_plan": sum(1 for c in g_caps if c.status == "方案中"),
                "cap_total": len(g_caps),
            }
        )

    stats = {
        "project_total": len(projects),
        "project_live": sum(1 for p in projects if p.status_summary == "已上线"),
        "project_doing": sum(1 for p in projects if p.status_summary == "进行中"),
        "project_plan": sum(1 for p in projects if p.status_summary == "方案中"),
        "cap_total": len(caps),
        "cap_done": sum(1 for c in caps if c.status == "已完成"),
        "cap_doing": sum(1 for c in caps if c.status == "进行中"),
        "cap_plan": sum(1 for c in caps if c.status == "方案中"),
        "cap_verified": sum(1 for c in caps if c.verify_state == "已验证"),
        "site_total": len(all_sites),
        "site_online": sum(1 for s_item in all_sites if s_item[3] == "online"),
    }

    return {
        "objective": OBJECTIVE_TEXT,
        "goal_tree": goal_tree,
        "goals": goals,
        "strategies": strategies,
        "proj_views": proj_views,
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


# ───────────────────────────── 核心视图 ─────────────────────────────


@app.get("/", response_class=HTMLResponse)
def overview_mindmap(request: Request, s: Session = Depends(get_session)):
    """首页：OGSM 全景思维导图 + 顶部管理总览仪表盘。"""
    return render(request, "mindmap.html", ctx(request, s, active_nav="mindmap"))


@app.get("/projects", response_class=HTMLResponse)
def projects_matrix(request: Request, goal: str = "", status: str = "", s: Session = Depends(get_session)):
    """14 大产品项目管理矩阵（以产品名称为项目名称）。"""
    return render(
        request,
        "projects.html",
        ctx(request, s, active_nav="projects", filter_goal=goal, filter_status=status),
    )


@app.get("/present", response_class=HTMLResponse)
def presentation_mode(request: Request, s: Session = Depends(get_session)):
    """部门项目汇报演示视图（对齐附件2的汇报结构与去 AI 味表达）。"""
    return render(request, "present.html", ctx(request, s, active_nav="present"))


@app.get("/sites", response_class=HTMLResponse)
def workbenches_directory(request: Request, s: Session = Depends(get_session)):
    """全部 23 个线上工作台与子平台直达导航页。"""
    return render(request, "sites.html", ctx(request, s, active_nav="sites"))


# compatibility redirects for old routes
@app.get("/board")
@app.get("/lines")
@app.get("/experts")
@app.get("/baselines")
@app.get("/metrics")
def legacy_redirect():
    return RedirectResponse("/projects", status_code=302)


# ───────────────────────────── 实测报告与文档查阅 ─────────────────────────────


@app.get("/docs", response_class=HTMLResponse)
def docs_index(request: Request, s: Session = Depends(get_session)):
    """实测报告（/reports）与 OGSM 资料库索引。"""
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
    """直接在线打开 /reports 下的专家实测 HTML 报告。"""
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
    resp = RedirectResponse("/admin", status_code=303)
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
                sort=99,
            )
        )
        s.commit()
    return RedirectResponse(f"/admin#proj-{project_slug}", status_code=303)


@app.post("/admin/reset-seed")
def reset_seed_data(request: Request):
    """一键恢复为思维导图与 /reports 的标准初始数据。"""
    if not is_pmo(request):
        return RedirectResponse("/login", status_code=303)
    seed(force_reset=True)
    return RedirectResponse("/admin", status_code=303)


@app.get("/health")
def health():
    return {"ok": True}
