# ABI OGSM 管理站

把 `OGSM-v1-整合版-20261102.md` 变成可管理、可校验、可结算的系统。

形态：**Postgres + 单体 FastAPI + 服务端渲染**。PMO 唯一写入口，前台全只读。

## 为什么这样建

OGSM 死掉最常见的方式不是没人看，是**首页变成一张几个月没更新的海报**。
要避免这个，唯一有效的办法是让页面上的每个数字都来自一个会被其他地方校验的源。

所以设计取舍是：

| 决定 | 理由 |
|---|---|
| 用 Postgres 而不是 YAML | 要多人查、要按周期追加快照、要历史可查 |
| 单体 + 服务端渲染，不做前后端分离 | 页面只有五个视图，SPA 只会增加维护面 |
| **每次渲染前跑结构校验** | 把文档 §7 的规则变成断言。文档靠读，校验器靠跑 |
| 写入口只有 PMO 一方 | 符合 RACI「一个对象一个写入口」，且避免 18 条产线各自维护口径 |
| 进度三态只进交付台账 | 「已完成」等价于成熟度 M1，永不进 M 栏 |

## 结构校验器（`app/rules.py`）

这是整份实现的核心。每条规则都对应一次真实踩过的坑：

| 编号 | 断言 | 对应历史问题 |
|---|---|---|
| C1 | 每个 G 有且仅有 1 个结算主指标，且必须是 T1 层、`decision_use=budget` | B-01：G1 的 CAC 阈值与 O 差 20pp |
| C2 | G 与结果变量中不得出现「已完成/进行中/方案中/上线/交付」 | M11：交付进度冒充经营结果 |
| C3 | 业务产线必须有段 A 或对象级 A（支撑层降为警告） | M-05：8 个段 A 没有指标；Echo/Daisy 走对象级 A |
| C4 | 每条战略必须有反证条件 | 没有反证条件，十一条战略一年后全部变成「还在做」 |
| C5 | G 基线未锁定只警告，不得视为已生效 | T0 前基线必须用真实 12 周中位数替换 |
| C6 | 支撑层不得挂在 G1/G2/G3 上 | 原 G3 把职能当目标 |
| C7 | T3 渠道内指标（ROAS/CPM/CTR/CVR/频次）禁止标为 budget | M01：平台 ROAS 当经营结论 |

当前读数：**1 错误 / 4 警告**。1 个错误是 GEO 既无段 A 也无对象级 A ——
这是文档里点名的结构性缺口（缺 `ai_answer_snapshot_id`），不是实现 bug。

## 五个视图

| 路由 | 受众 | 内容 |
|---|---|---|
| `/` 一页纸 | 全员 / 汇报 | O + 三个 G + 十一条 S + 支撑层 + 三条硬规则 |
| `/board` 结算看板 | 业务负责人 / 财务 | G 结算、四象限续投判定、四个熔断、快照录入 |
| `/lines` 产线台账 | 段 A | 18 项登记、成熟度、对象级 A、消费方、交付台账 |
| `/metrics` 指标字典 | PMO | T1–T5 五层 + `decision_use` + 12 条误用 |
| `/docs` 治理索引 | PMO | 11 份原始 md 的只读浏览 + 文档职责表 |

PMO 后台 `/admin`：改 G-A 与基线锁定、改产线成熟度与消费方、改交付状态、录结算快照。

## 运行

### 方式一：宿主机跑应用 + 容器跑数据库（推荐，已验证）

```bash
cd ogsm-web
docker compose up -d                      # 只起 Postgres，映射到 5433

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
DATABASE_URL="postgresql+psycopg://ogsm:ogsm@localhost:5433/ogsm" .venv/bin/python -m app.seed
DATABASE_URL="postgresql+psycopg://ogsm:ogsm@localhost:5433/ogsm" \
OGSM_DOCS_DIR="/Users/lute/Project/PMO/OGSM" \
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8080
```

打开 http://127.0.0.1:8080 。PMO 口令默认 `pmo`。

### 方式二：全容器

`Dockerfile` 已就绪，但**本机 Docker Desktop 对 `OGSM/` 目录的文件共享索引是坏的**
（挂父目录正常、挂子目录为空或读到损坏字节）。在别的机器上可直接：

```bash
cd ogsm-web
docker compose -f docker-compose.full.yml up -d --build
```

## 环境变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `DATABASE_URL` | `...@localhost:5432/ogsm` | Postgres 连接串 |
| `OGSM_PMO_PASSWORD` | `pmo` | **上线前必须改** |
| `SECRET_KEY` | `change-me-in-production` | 会话签名密钥，**上线前必须改** |
| `OGSM_DOCS_DIR` | `../..` | 治理索引读 md 的目录 |

## 目录

```
ogsm-web/
├── docker-compose.yml      # 只含 Postgres
├── Dockerfile              # 全容器部署用（上下文需为父目录）
├── requirements.txt
└── app/
    ├── models.py           # schema 即 OGSM 结构
    ├── rules.py            # 七个结构断言 ← 核心
    ├── seed.py             # OGSM v1.0 内容，幂等
    ├── main.py             # 路由
    ├── static/style.css
    └── templates/          # base + 五个视图 + 后台 + 登录
```

## 已知取舍

- **改内容目前要改 `seed.py` 或走 `/admin`**。没有通用 CRUD 表单，因为 O/G/S 一年只改一次，
  为低频操作建通用后台不划算。加产线、加指标走 seed 更安全（有 schema 与校验兜底）。
- **`localStorage`/cookie 会话无过期刷新**，24 小时后需重新登录。够用。
- 四象限判定当前用 `actual >= target × 0.8` 的简化规则。文档里的完整规则含
  「T4 门禁未达标则最高只能条件续投」，需接入真实 L4 指标后才能自动算。
