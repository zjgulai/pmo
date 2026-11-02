"""OGSM 管理站。

形态：Postgres + 单体 FastAPI + 服务端渲染。
写入口：仅 PMO（口令登录），前台全只读。
核心：每次渲染前跑 rules.run_checks()，把结构问题摆在页面顶部。
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
from .rules import run_checks

app = FastAPI(title="ABI OGSM")
BASE = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE / "templates"))
# 本地 Python 3.15 上 jinja2 的 LRU 缓存键不可哈希，关掉缓存即可（模板量小，无性能影响）
templates.env.cache = None

# 静态文件必须挂载，否则 style.css 404，页面退化成无样式纯文本。
# 2026-11-02 生产首版就漏了这一行——只验 HTTP 200 不验资源加载，等于没验。
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")

PMO_PASSWORD = os.getenv("OGSM_PMO_PASSWORD", "pmo")
SECRET = os.getenv("SECRET_KEY", "change-me-in-production")
signer = URLSafeSerializer(SECRET, salt="ogsm-pmo")
DOCS_DIR = Path(os.getenv("OGSM_DOCS_DIR", str(BASE.parent.parent)))


def render(request: Request, name: str, context: dict, status_code: int = 200):
    """统一渲染入口。

    Starlette 新签名是 (request, name, context)；旧的位置参数顺序已被移除。
    集中在这里适配一次，避免每个路由各写一遍。
    """
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


def ctx(request: Request, session: Session, **kw):
    """所有页面共享的上下文：校验结果 + 登录态 + 导航。"""
    checks = run_checks(session)
    base = {
        "request": request,
        "checks": checks,
        "is_pmo": is_pmo(request),
        "today": date.today().isoformat(),
    }
    base.update(kw)
    return base


# ───────────────────────────── 只读视图 ─────────────────────────────


@app.get("/", response_class=HTMLResponse)
def one_pager(request: Request, s: Session = Depends(get_session)):
    """一页纸：O + 三个 G + 十一条 S。给全员和汇报看。"""
    obj = s.exec(select(models.Objective)).first()
    goals = s.exec(select(models.Goal).order_by(models.Goal.sort)).all()
    results = s.exec(select(models.ResultVariable).order_by(models.ResultVariable.sort)).all()
    strategies = s.exec(select(models.Strategy).order_by(models.Strategy.sort)).all()
    by_goal: dict[str, list] = {}
    for st in strategies:
        by_goal.setdefault(st.goal_code, []).append(st)
    return render(request, "onepager.html",
                  ctx(request, s, obj=obj, goals=goals, results=results, by_goal=by_goal))


@app.get("/board", response_class=HTMLResponse)
def board(request: Request, s: Session = Depends(get_session)):
    """结算看板：目标 vs 实际 + 四象限续投判定 + 熔断状态。"""
    goals = s.exec(select(models.Goal).order_by(models.Goal.sort)).all()
    results = s.exec(select(models.ResultVariable).order_by(models.ResultVariable.sort)).all()
    snaps = s.exec(select(models.MetricSnapshot).order_by(models.MetricSnapshot.id.desc())).all()
    latest: dict[str, models.MetricSnapshot] = {}
    for sn in snaps:
        latest.setdefault(f"{sn.line_name}|{sn.metric_id}", sn)

    # 四象限判定
    lines = s.exec(select(models.Line)).all()
    quad = []
    for ln in lines:
        if ln.kind == "out":
            continue
        consumed = bool((ln.consumer or "").strip())
        has_metric = any(k.startswith(f"{ln.name}|") for k in latest)
        actual = next((v for k, v in latest.items() if k.startswith(f"{ln.name}|")), None)
        hit = None
        if actual and actual.actual and actual.target:
            try:
                a, t = float(actual.actual), float(actual.target)
                hit = a >= t * 0.8
            except ValueError:
                hit = None
        if hit is None:
            verdict = "待结算"
        elif hit and consumed:
            verdict = "续投"
        elif hit and not consumed:
            verdict = "条件续投（6 个月）"
        elif not hit and consumed:
            verdict = "条件续投（预算减半）"
        else:
            verdict = "关停"
        quad.append({"line": ln, "verdict": verdict, "consumed": consumed, "has_metric": has_metric})

    return render(request, "board.html",
                  ctx(request, s, goals=goals, results=results, quad=quad, latest=latest))


@app.get("/lines", response_class=HTMLResponse)
def lines(request: Request, s: Session = Depends(get_session)):
    """产线台账：18 项登记 + 成熟度 + 消费方 + work_item。"""
    rows = s.exec(select(models.Line)).all()
    items = s.exec(select(models.WorkItem).order_by(models.WorkItem.id.desc())).all()
    grouped: dict[str, list] = {}
    for ln in rows:
        grouped.setdefault(ln.layer, []).append(ln)
    order = ["G1", "G2", "G3", "support", "governance", "out"]
    grouped = {k: grouped[k] for k in order if k in grouped}
    return render(request, "lines.html", ctx(request, s, grouped=grouped, items=items))


@app.get("/metrics", response_class=HTMLResponse)
def metrics(request: Request, s: Session = Depends(get_session)):
    rows = s.exec(select(models.Metric).order_by(models.Metric.layer, models.Metric.metric_id)).all()
    grouped: dict[str, list] = {}
    for m in rows:
        grouped.setdefault(m.layer, []).append(m)
    return render(request, "metrics.html", ctx(request, s, grouped=grouped))


@app.get("/baselines", response_class=HTMLResponse)
def baselines(request: Request, s: Session = Depends(get_session)):
    """基线台账：B1–B6 / D 的口径、窗口、来源、数值、锁定人。

    这是 T0 唯一必须关闭的清单。C5/C5b 的警告能不能消失，取决于这张表。
    """
    rows = s.exec(select(models.Baseline).order_by(models.Baseline.sort)).all()
    locked = [b for b in rows if b.value]
    return render(request, "baselines.html",
                  ctx(request, s, rows=rows, locked_n=len(locked), total=len(rows)))


@app.post("/admin/baseline")
def lock_baseline(
    request: Request,
    key: str = Form(...),
    value: str = Form(...),
    locked_by: str = Form(...),
    note: str = Form(default=""),
    s: Session = Depends(get_session),
):
    """锁定一条基线。

    强制要求 locked_by：无人认账的基线不能用于考核（对应 C5b）。
    value 为空则拒绝——不允许用空白冒充「已锁定」。
    """
    if not is_pmo(request):
        return RedirectResponse("/login", status_code=303)
    if not value.strip() or not locked_by.strip():
        return RedirectResponse("/baselines", status_code=303)
    b = s.exec(select(models.Baseline).where(models.Baseline.key == key)).first()
    if b:
        b.value = value.strip()
        b.locked_by = locked_by.strip()
        b.locked_at = datetime.now(timezone.utc)
        if note:
            b.note = note
        s.add(b)
        s.commit()
    return RedirectResponse("/baselines", status_code=303)


@app.get("/experts", response_class=HTMLResponse)
def experts(request: Request, s: Session = Depends(get_session)):
    """专家 × OGSM 对齐：承诺与资源是否对齐。

    与 /lines 的区别：/lines 看「每条产线是谁」，/experts 看「每个人挂在哪条线」。
    两个方向都看，才能发现「承诺了没做」与「做了没承诺」。
    """
    rows = s.exec(select(models.Expert).order_by(models.Expert.sort)).all()
    by_status: dict[str, list] = {}
    for e in rows:
        by_status.setdefault(e.status, []).append(e)
    counts = {k: len(v) for k, v in by_status.items()}
    for k in ("aligned", "has_real_no_name", "orphan", "name_no_build", "excluded"):
        counts.setdefault(k, 0)
    return render(request, "experts.html", ctx(request, s, by_status=by_status, counts=counts))


@app.get("/docs", response_class=HTMLResponse)
def docs_index(request: Request, s: Session = Depends(get_session)):
    """治理索引：列出原始 md 文档（只读）。"""
    files = []
    if DOCS_DIR.exists():
        for p in sorted(DOCS_DIR.glob("*.md")):
            files.append({"name": p.name, "size": p.stat().st_size, "mtime": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")})
    return render(request, "docs.html", ctx(request, s, files=files))


@app.get("/docs/{name}", response_class=HTMLResponse)
def docs_view(name: str, request: Request, s: Session = Depends(get_session)):
    p = (DOCS_DIR / name).resolve()
    if not p.exists() or p.suffix != ".md" or DOCS_DIR.resolve() not in p.parents:
        return RedirectResponse("/docs", status_code=303)
    text = p.read_text(encoding="utf-8", errors="replace")
    return render(request, "doc.html", ctx(request, s, name=name, text=text))


# ───────────────────────────── PMO 写入口 ─────────────────────────────


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request, s: Session = Depends(get_session)):
    return render(request, "login.html", ctx(request, s, err=None))


@app.post("/login")
def login(request: Request, password: str = Form(...)):
    if password != PMO_PASSWORD:
        return render(request, "login.html",
                      {"err": "口令不正确", "is_pmo": False, "checks": None,
                       "today": date.today().isoformat()},
                      status_code=401)
    resp = RedirectResponse("/admin", status_code=303)
    resp.set_cookie("ogsm_pmo", signer.dumps("pmo"), httponly=True, samesite="lax", max_age=86400)
    return resp


@app.get("/logout")
def logout():
    resp = RedirectResponse("/", status_code=303)
    resp.delete_cookie("ogsm_pmo")
    return resp


@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request, s: Session = Depends(get_session)):
    if not is_pmo(request):
        return RedirectResponse("/login", status_code=303)
    goals = s.exec(select(models.Goal).order_by(models.Goal.sort)).all()
    lines_rows = s.exec(select(models.Line)).all()
    items = s.exec(select(models.WorkItem).order_by(models.WorkItem.id.desc())).all()
    return render(request, "admin.html", ctx(request, s, goals=goals, lines=lines_rows, items=items))


@app.post("/admin/goal/{goal_id}")
def update_goal(
    goal_id: int,
    request: Request,
    baseline_locked: str = Form(default=""),
    ga: str = Form(default=""),
    s: Session = Depends(get_session),
):
    if not is_pmo(request):
        return RedirectResponse("/login", status_code=303)
    g = s.get(models.Goal, goal_id)
    if g:
        g.ga = ga or g.ga
        g.baseline_locked = baseline_locked == "on"
        s.add(g)
        s.commit()
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/line/{line_id}")
def update_line(
    line_id: int,
    request: Request,
    maturity: str = Form(default=""),
    seg_a: str = Form(default=""),
    consumer: str = Form(default=""),
    status: str = Form(default=""),
    s: Session = Depends(get_session),
):
    if not is_pmo(request):
        return RedirectResponse("/login", status_code=303)
    ln = s.get(models.Line, line_id)
    if ln:
        if maturity:
            ln.maturity = maturity
        if seg_a:
            ln.seg_a = seg_a
        if consumer:
            ln.consumer = consumer
        if status:
            ln.status = status
        s.add(ln)
        s.commit()
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/snapshot")
def add_snapshot(
    request: Request,
    line_name: str = Form(...),
    metric_id: str = Form(...),
    period: str = Form(...),
    baseline: str = Form(default=""),
    target: str = Form(default=""),
    actual: str = Form(default=""),
    note: str = Form(default=""),
    s: Session = Depends(get_session),
):
    if not is_pmo(request):
        return RedirectResponse("/login", status_code=303)
    s.add(models.MetricSnapshot(
        line_name=line_name, metric_id=metric_id, period=period,
        baseline=baseline, target=target, actual=actual, note=note,
    ))
    s.commit()
    return RedirectResponse("/board", status_code=303)


@app.post("/admin/workitem/{item_id}")
def update_workitem(
    item_id: int,
    request: Request,
    status: str = Form(default=""),
    evidence: str = Form(default=""),
    blocker: str = Form(default=""),
    s: Session = Depends(get_session),
):
    if not is_pmo(request):
        return RedirectResponse("/login", status_code=303)
    wi = s.get(models.WorkItem, item_id)
    if wi:
        if status:
            wi.status = status
        wi.evidence = evidence or wi.evidence
        wi.blocker = blocker
        wi.updated_at = datetime.now(timezone.utc)
        s.add(wi)
        s.commit()
    return RedirectResponse("/admin", status_code=303)


@app.get("/health")
def health():
    return {"ok": True}
