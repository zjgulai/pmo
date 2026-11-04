"""ABI 品牌 & 营销 Agent 多项目管理网站 —— 初始数据（V8：严格执行「14独立飞书Bot + 四阶自进化进度标尺(25/50/75/100%) + 3人核心铁三角唯一主责制 + Wave 1-3排期」）。

四阶真实进度标尺（用户拍板定案）：
- Stage 1 (0% → 25%)：工作台基座与历史 SOP 初版就绪（*.luteos.com 200 在线 + 核心数据表建模）
- Stage 2 (25% → 50%)：独立飞书应用（14个专属Bot）双向回调与卡片执行跑通（群内/私聊 @Agent 提需求 → 工具执行 → 交互卡片回调产生任务）
  * 硬门禁：未接通独立飞书应用双向回调的能力，进度最高封顶 50%，状态不得标为「已完成」。
- Stage 3 (50% → 75%)：业务高频问答统计与 SOP 自进化（统计飞书提问 ≥10次/周或人工纠正 ≥3次 → 蒸馏提炼为确定性脚本并通过三道门禁，返工率 <20%）
- Stage 4 (75% → 100%)：自进化脚本迁移固化为工作台自动化能力（稳定运行 ≥2周后固化为工作台自动化工位/定时流水线，释放Agent算力）

核心团队与协作边界（唯一真实编制）：
1. 周健：负责所有产品的全栈开发、所有产品项目管理、所有数据算法研发（唯一主责 18 项）
2. 刘华丽：负责所有产品的测试、各Agent运营、各Agent控制台管理（唯一主责 16 项）
3. 吴雨宁：负责所有产品的需求调研、前端设计、数据架构设计、产品推广（唯一主责 15 项）
4. 需求协作方：品牌市场部相关部门人员（在飞书向 14 个专属 Agent 提问触发需求、点卡片确认、认领 P0 动作）
5. 自建干活 Agent（14 个独立飞书 Bot + 后台执行引擎）：替代缺编执行人力，执行对话应答、高频问题聚类与 SOP 自进化。
"""
from datetime import datetime, timezone

from sqlmodel import Session, SQLModel, select

from .db import engine
from .models import (
    BusinessActionLedger,
    CapabilityItem,
    GoalGroup,
    ProductProject,
    SopEvolutionCandidate,
    StrategyGroup,
)

OBJECTIVE_TEXT = "【O】以品牌 Agent 全链路自动化，让声量有增长、口碑有防线、人效有提升。"

GOALS = [
    dict(
        code="G1",
        title="【G1】加速品牌多渠道声量增长",
        subtitle="覆盖社媒趋势、爆款脚本、公关媒体、AI 搜索可见度与 IP 名人合作，共 5 个专家 Agent（独立飞书 Bot + 工作台）",
        sort=1,
    ),
    dict(
        code="G2",
        title="【G2】敏捷响应品牌声量所带来的影响和机会",
        subtitle="覆盖消费者声音（VOC）、市场选品洞察、70 平台统一数据采集与全网声量异动监控，共 4 个专家 Agent（独立飞书 Bot + 工作台）",
        sort=2,
    ),
    dict(
        code="G3",
        title="【G3】推进品牌数据资产AI数字化运营",
        subtitle="覆盖内容合规审查、多智能体统一门户、全栈研发评测、独立站智能运营与 OGSM 项目管理，共 5 个专家 Agent（独立飞书 Bot + 工作台）",
        sort=3,
    ),
]

STRATEGIES = [
    dict(
        code="S1",
        goal_code="G1",
        title="社媒专家 + 爆款复刻专家 融合，为社媒趋势把控、爆款选题、拍摄脚本、AI素材生成提供辅助决策类和生产力工具",
        sort=1,
    ),
    dict(
        code="S2",
        goal_code="G1",
        title="媒体公关专家 + GEO专家 + IP/名人专家 融合，为品牌公共关系从核心媒体编辑跟踪、声量洞察、专家挖掘助力",
        sort=2,
    ),
    dict(
        code="S3",
        goal_code="G2",
        title="VOC专家 + 市场洞察专家 融合，为品牌消费者舆情监控、品牌声量机会识别、竞品洞察提供辅助决策",
        sort=3,
    ),
    dict(
        code="S4",
        goal_code="G2",
        title="品牌声量专家 + 多平台数据采集专家 融合，为品牌知识库构建、声量建模、声量分析提供辅助决策",
        sort=4,
    ),
    dict(
        code="S5",
        goal_code="G3",
        title="内容审核专家 + 多智能体平台 融合，为品牌内容资产审核、知识库沉淀以及多智能体协作提供品牌资产与协作平台",
        sort=5,
    ),
    dict(
        code="S6",
        goal_code="G3",
        title="Agent全栈专家 + 项目管理专家 + 独立站智能化专家融合，沉淀研发、运营、协作三类AI生产力工具",
        sort=6,
    ),
]

PROJECTS = [
    # ─────────────────────────── G1 / S1 ───────────────────────────
    dict(
        slug="emily",
        expert_name="Emily",
        product_name="社媒Agent&工作台",
        goal_code="G1",
        strategy_code="S1",
        workbench_url="https://social.luteos.com/",
        workbench_online=True,
        scenarios="社媒趋势洞察 → 内容策略 → 脚本生成",
        status_summary="进行中",
        owner="吴雨宁（需求&推广） / 刘华丽（Agent运营） / 周健（全栈&算法）",
        verified_summary=(
            "【Wave 1 · 四阶真实进度 72%（已通 Stage 1 工作台 + Stage 2 独立飞书 Bot，正推进 Stage 3 高频问题自进化）】"
            "Emily 独立飞书群智能体与 Web 工作台（14 个路由页面）均已在线运行；注册 41 项社媒能力（28 项已上线、8 项受限、5 项待开发），"
            "每周五早 9:30 自动向交付群推送 6 维度社媒周报，飞书社媒 Base（4 表 888 行）实时镜像，并已整合 BrandOS 10 品牌 Token 语调护栏（均分 88）。"
        ),
        metrics_highlights=(
            "飞书Bot与工作台|Stage 2→3 自进化 (72%)|独立Bot在线+14路由\n"
            "已上线社媒能力|28 / 41 项|Emily 报告 10-31\n"
            "飞书 Base 镜像|4 表 888 行|社媒 Base 报告 10-31\n"
            "品牌 Token 护栏|10 品牌 / 均分 88|BrandOS 实测"
        ),
        pending_gaps=(
            "【Stage 3 自进化缺口】需统计品牌市场部在飞书群提问 ≥10次/周的高频选题/脚本问题，自动蒸馏为标准脚本模板\n"
            "【Stage 4 固化缺口】内容策略生成与批量脚本生成需从飞书问答态迁移固化为 social.luteos.com 工作台自动化流水线"
        ),
        report_links=(
            "Emily 项目成果总结 (10-31)|/reports-view/Emily/Emily-项目成果总结-20261031.html\n"
            "全球社媒 Base OGSM 分析报告|/reports-view/Emily/OGSM分析报告_社媒Base.html"
        ),
        extra_sites="",
        support_notes=(
            "【Wave 1｜当前 Stage 2→3 自进化 (72%)｜甘特收口：2026-09-08 ~ 2026-11-15】\n"
            "飞书Agent→工作台自进化交接链：品牌市场部社媒运营在飞书 @Emily 提问趋势与脚本 → 刘华丽在控制台统计周触发 ≥10次的高频问题（#02 截止 11-11） → 周健通过自进化管线提炼为确定性脚本（#04 截止 11-15） → 吴雨宁将其迁移固化为 social.luteos.com 工作台标准SOP工位（#01/#03 截止 11-08/11-13）。\n"
            "跨 Agent 交接协议（Echo → Emily → Clone）：接收 Echo 产出的高频痛点卡（pain_tag_id + 用户原话），注入 asset.luteos.com 的 Brand Token 参数，向 Clone 输出带 claim_id 的策略 Brief。"
        ),
        sort=1,
    ),
    dict(
        slug="clone",
        expert_name="Clone",
        product_name="爆款复刻Agent&工作台",
        goal_code="G1",
        strategy_code="S1",
        workbench_url="https://video.luteos.com/",
        workbench_online=True,
        scenarios="参考视频输入 → 结构拆解（钩子/节拍/口播/字幕/音乐） → 品牌脚本复刻",
        status_summary="进行中",
        owner="周健（算法&全栈） / 刘华丽（评测&控制台） / 吴雨宁（前端&推广）",
        verified_summary=(
            "【Wave 2 · 四阶真实进度 45%（已通 Stage 1 工作台与复刻算法底座，待接通 Stage 2 独立飞书 Bot 回调）】"
            "工作台（video.luteos.com）、Recipe 爆款拆解引擎（13/14 评测通过，15 条确定性规则）及 AI Video 16 节点流水线（S1–S5 场景 + PendingReviewPacket 权利门禁）已就绪；"
            "按四阶新标尺，因尚未上线独立 @Clone 飞书机器人接收参考视频链接并回调拆片卡片，当前封顶在 Stage 1~2 过渡态（45%）。"
        ),
        metrics_highlights=(
            "四阶真实进度|Stage 1 已通 (45%)|Wave 2 接入独立Bot\n"
            "Recipe 评测通过|13 / 14 案例|Main 报告 11-01\n"
            "视频生产流水线|16 节点 / S1-S5 场景|Video 报告 06-30\n"
            "确定性校验规则|15 条 + 商业权利门禁|packages/evals"
        ),
        pending_gaps=(
            "【Stage 2 飞书回调缺口】需在 Wave 2（11月第3–4周）上线独立 @Clone 飞书应用，支持编导在飞书发参考视频链接直接回调生成分镜卡片\n"
            "【Stage 3-4 自进化缺口】统计编导对拆片卡片的高频修改项（≥3次纠正），自进化更新 S1–S5 镜头配方并固化至 video.luteos.com"
        ),
        report_links=(
            "Main & Recipe Agent 成果总结 (11-01)|/reports-view/Main/Main-项目成果总结-20261101.html"
        ),
        extra_sites="",
        support_notes=(
            "【Wave 2｜当前 Stage 1→2 过渡 (45%)｜甘特收口：2026-11-10 ~ 2026-11-28】\n"
            "飞书Agent→工作台自进化交接链：周健于 11-21 前上线独立 @Clone 飞书Bot（#05），品牌市场部编导在飞书发送 TikTok 爆款链接 → Clone 回调返回钩子/节拍/口播卡片 → 刘华丽于 11-28 前统计高频修改意见（≥3次纠正）沉淀为 S1–S5 镜头配方并迁入 video.luteos.com（#06）。\n"
            "跨 Agent 交接协议（Clone → Radar / 守衡）：产出待审资产包（PendingReviewAssetPacket），强制关联 Radar 的达人二创授权凭证（rights_ref）与守衡的宣称证据（claim_evidence_refs），未获双签前禁止进入广告投流。"
        ),
        sort=2,
    ),

    # ─────────────────────────── G1 / S2 ───────────────────────────
    dict(
        slug="vicky",
        expert_name="Vicky",
        product_name="PR Agent&工作台",
        goal_code="G1",
        strategy_code="S2",
        workbench_url="https://pr.luteos.com/",
        workbench_online=True,
        scenarios="PR 线：竞品监测 → 风险预警 → 工作台协同\n舆情线：看板对话化 → 自动分类 → 工单闭环",
        status_summary="进行中",
        owner="刘华丽（Agent运营&控制台） / 吴雨宁（数据架构&推广） / 周健（全栈研发）",
        verified_summary=(
            "【Wave 2 · 四阶真实进度 50%（Stage 1 工作台与 7 表 666 条每日 09:50 重算已稳，待补 Stage 2 独立飞书 Bot 双向派单回调）】"
            "工作台（pr.luteos.com）已与飞书 PR 业务库（246 家媒体库 / 347 条报道，S级权威报道 100 条）双向同步，并整合了 Melwater 57 条 Action Register；"
            "按四阶标尺挤干水分（原 100% 下调为 50%）：需补齐独立 @Vicky 飞书应用，让公关媒介人员在群内通过卡片直接认领舆情工单与 Pitching 任务。"
        ),
        metrics_highlights=(
            "四阶真实进度|Stage 1-2 过渡 (50%)|Wave 2 补齐Bot回调\n"
            "上线报道总数|347 条 (Earned 77%)|Vicky 报告 10-31\n"
            "媒体资源库|246 家 (S级报道 100条)|跨表匹配实测\n"
            "Vicky 能力承接度|56% (核心表 70%)|7表×16能力矩阵"
        ),
        pending_gaps=(
            "【Stage 2 飞书回调缺口】需在 Wave 2 上线独立 @Vicky 飞书应用，支持群内 @Vicky 查媒体背书、点卡片一键认领公关危机工单\n"
            "【Stage 3-4 自进化缺口】用 BrandOS 315 SKU 字典自动回填 347 条报道的品线字段，并将高频媒介匹配规则固化为工作台 Pitching Calendar"
        ),
        report_links=(
            "Vicky 项目成果总结 (10-31)|/reports-view/Vicky/Vicky-项目成果总结-20261031.html\n"
            "品牌 PR 七表 × 16 能力 GAP 分析主报告|/reports-view/Vicky/主报告_GAP矩阵版_品牌PR_All-in-One分析.html\n"
            "Momcozy 北美 PR OGSM 战略分析副报告|/reports-view/Vicky/副报告_OGSM战略版_Momcozy北美PR分析.html"
        ),
        extra_sites="",
        support_notes=(
            "【Wave 2｜当前 Stage 1-2 过渡 (50%)｜甘特收口：2026-11-10 ~ 2026-11-27】\n"
            "飞书Agent→工作台自进化交接链：吴雨宁/周健于 11-19 ~ 11-24 接入独立 @Vicky 飞书Bot线索查询与编辑推荐回调（#07/#08） → 刘华丽于 11-22 ~ 11-27 打通舆情预警卡片认领并统计 PR 专员高频查询（≥10次/周）自进化固化为 pr.luteos.com 报表（#09/#10）。\n"
            "跨 Agent 交接协议（Vicky ↔ GEO）：Vicky 收录的 100 条 S 级权威媒体评测报道自动同步至 GEO 作为 AI 引擎高权重引用源；GEO 检出的「未获 Best Overall 问句缺口」反推 Vicky 定向攻关目标榜单编辑。"
        ),
        sort=3,
    ),
    dict(
        slug="geo",
        expert_name="GEO",
        product_name="专家内容Agent&工作台",
        goal_code="G1",
        strategy_code="S2",
        workbench_url="https://geo.luteos.com",
        workbench_online=True,
        scenarios="问句库 → 采集探针 → 解析与指标 → 诊断洞察 → 内容生成 → 复测报告",
        status_summary="进行中",
        owner="吴雨宁（问句架构&推广） / 周健（探针&算法） / 刘华丽（复测运营）",
        verified_summary=(
            "【Wave 3 · 四阶真实进度 22%（处于 Stage 1 基座整合期）】"
            "工作台站点（geo.luteos.com）在线，第 9 主键 ai_answer_snapshot_id 已定稿，并已收编 Momcozy 审计的 Perplexity 5/5 提及（0/5 Best Overall）基线快照与 BrandOS 315 SKU×16 类事实文件；"
            "按四阶标尺，独立 @GEO 飞书机器人回调、高频购买问句自进化及 6 步工作台流水线将于 Wave 3（12月）交付。"
        ),
        metrics_highlights=(
            "四阶真实进度|Stage 1 基座期 (22%)|Wave 3 接入独立Bot\n"
            "Perplexity 基线|5/5 提及 (0/5 最佳)|Momcozy 审计实测\n"
            "SKU 权威事实原子|315 SKU × 16 类文件|BrandOS 数据湖\n"
            "主键契约规格|ai_answer_snapshot_id|11-02 主键字典定稿"
        ),
        pending_gaps=(
            "【Stage 1-2 缺口】30 天内落库 ai_answer_snapshot_id，上线独立 @GEO 飞书应用供搜索/内容团队查询 AI 引用缺口并回调派单\n"
            "【Stage 3-4 缺口】将飞书群内高频追问的购买场景问句自动并入 20问/ASIN 标准库，并固化为 geo.luteos.com 月度自动复测流水线"
        ),
        report_links="",
        extra_sites="",
        support_notes=(
            "【Wave 3｜当前 Stage 1 基座期 (22%)｜甘特收口：2026-11-24 ~ 2026-12-26】\n"
            "飞书Agent→工作台自进化交接链：吴雨宁/周健于 12-04 ~ 12-15 上线 @GEO 飞书Bot问句库、探针采样与缺口诊断派单卡（#11~#14） → 周健/刘华丽于 12-20 ~ 12-26 完成 315 SKU 权威内容生成与月度自动复测 SOP 固化（#15/#16）。\n"
            "跨 Agent 交接协议（asset / Vicky → GEO → Shopify）：从 asset.luteos.com 读取 315 个 SKU 的合规参数与 USP，发现 AI 回答缺口后，分派 Vicky 攻关外部权威媒体榜单、分派 Shopify 补齐独立站 PDP 的 FAQ/Review Schema。"
        ),
        sort=4,
    ),
    dict(
        slug="radar",
        expert_name="Radar",
        product_name="IP/名人Agent&工作台",
        goal_code="G1",
        strategy_code="S2",
        workbench_url="https://magpie.luteos.com/",
        workbench_online=True,
        scenarios="粉丝分析 → 合作计划 → 动态监测 → 机会推荐",
        status_summary="进行中",
        owner="吴雨宁（需求&数据架构） / 刘华丽（监测运营） / 周健（算法研发）",
        verified_summary=(
            "【Wave 3 · 四阶真实进度 20%（处于 Stage 1 基座与 SOP 导入期）】"
            "工作台（magpie.luteos.com）在线，已导入 wiki 四维达人分层工作流（Expert/Editorial/Affiliate/Sponsored）与 Shopify 站外增长 SOP 的「creator_id + 授权七元组」风控模型；"
            "按四阶标尺，独立 @Radar 飞书应用回调（BD 在飞书查达人背调、点卡片登记寄样与二创授权到期）排在 Wave 3 交付。"
        ),
        metrics_highlights=(
            "四阶真实进度|Stage 1 基座期 (20%)|Wave 3 接入独立Bot\n"
            "工作台站点|200 在线|magpie.luteos.com\n"
            "达人分层工作流|4 类模型 / Wave-1 排序|wiki 仓库 pytest 通过\n"
            "授权前置闸门|creator_id + 授权七元组|Shopify 站外增长 SOP"
        ),
        pending_gaps=(
            "【Stage 2 缺口】上线独立 @Radar 飞书应用，支持达人 BD 在飞书发主页链接直接回调生成粉丝/声量背调卡片与授权登记按钮\n"
            "【Stage 3-4 缺口】统计 BD 高频询价与违约场景，自进化出达人筛选与到期催办 SOP 并固化至 magpie.luteos.com"
        ),
        report_links="",
        extra_sites="",
        support_notes=(
            "【Wave 3｜当前 Stage 1 基座期 (20%)｜甘特收口：2026-11-24 ~ 2026-12-23】\n"
            "飞书Agent→工作台自进化交接链：吴雨宁于 12-05 前完成达人四维分层与 @Radar 飞书背调卡设计（#17 里程碑） → 刘华丽于 12-16 前打通寄样回收(≥60%)与授权到期(<5%)飞书催办卡（#18） → 周健于 12-23 前将高频筛选条件自进化为合作推荐算法并迁入 magpie.luteos.com（#19）。\n"
            "跨 Agent 交接协议（Radar → Clone / Paid Media）：Radar 是 creator_id 与达人授权七元组的唯一登记源；任何达人素材进入 Clone 二次剪辑或进入 Paid Media 广告投流前，必须校验 Radar 签发的有效授权状态。"
        ),
        sort=5,
    ),

    # ─────────────────────────── G2 / S3 ───────────────────────────
    dict(
        slug="echo",
        expert_name="Echo",
        product_name="VOC Agent&工作台",
        goal_code="G2",
        strategy_code="S3",
        workbench_url="https://radar.luteos.com/",
        workbench_online=True,
        scenarios="舆情线：品牌/品类/SPU舆情预警\n话题线：高质量内容机会挖掘\n产品机会线：品类机会挖掘",
        status_summary="进行中",
        owner="吴雨宁（v6.4标签架构&前端） / 刘华丽（日报运营） / 周健（重算&NLP引擎）",
        verified_summary=(
            "【Wave 1 · 四阶真实进度 72%（Stage 1 工作台与 10 步无人值守晨报已固化，Wave 1 升级独立飞书 Bot 双向问数回调与新痛点自进化）】"
            "主工作台（radar.luteos.com）及 business/report/plugin 子站均在线；Reddit 10 步日更管线（86倍提速，10.29s重算）每日早 07:05 自动推送飞书晨报；"
            "已整合 ai_nlp_voc 712.2 万全渠道语料 + v6.4 标准标签字典（2,346 行零重复）+ BrandOS 社媒独有 765 类沉默痛点 Gap 雷达 + VOA 机会卡。"
        ),
        metrics_highlights=(
            "四阶真实进度|Stage 2→3 自进化 (72%)|Wave 1 升级双向回调\n"
            "全渠道 VOC 资产池|712.2 万条 + 2,346 标签|ai_nlp_voc 实测\n"
            "Reddit 无人值守日更|2.6万帖 / 重算 10.29s (86×)|Echo 报告 11-02\n"
            "跨渠道痛点 Gap 雷达|社媒独有 765 类痛点|BrandOS 交叉报告"
        ),
        pending_gaps=(
            "【Stage 2 双向回调补齐】当前早 07:05 飞书日报为单向推送，Wave 1 需打通群内 @Echo 追问具体 SPU 差评原话与点卡片认领 P0 Action 回写\n"
            "【Stage 3-4 自进化缺口】统计业务对新产品型号的高频追问（≥10次/周），自动进化 SpuBinding 规则（将 SPU 绑定率从 2/56 提升至 ≥80%）并固化为工作台品类报告"
        ),
        report_links=(
            "Echo 项目成果总结 (11-02)|/reports-view/Echo/Echo-项目成果总结-20261102.html"
        ),
        extra_sites=(
            "品类洞察平台|https://business.luteos.com/|online\n"
            "品类洞察报告|https://report.luteos.com/|online\n"
            "数据采集插件|https://plugin.luteos.com/|internal"
        ),
        support_notes=(
            "【Wave 1｜当前 Stage 2→3 自进化 (72%)｜甘特收口：2026-10-15 ~ 2026-11-16】\n"
            "飞书Agent→工作台自进化交接链：吴雨宁于 11-09 前打通 @Echo 按 SPU 实时问数回调（#20） → 刘华丽于 11-13 前为早 07:05 晨报卡增加「认领痛点/追问原话」回调并统计高频问题进化 SpuBinding（#21 里程碑） → 吴雨宁/周健于 11-15 ~ 11-16 将高频维度固化为拖拽分析台与自动品类报告（#22/#23）。\n"
            "跨 Agent 交接协议（Echo → Emily / Market / CS）：Echo 统一采用 v6.4（2,346 行）标签字典作为全组织唯一 VOC 分类标准；向 Emily 输出高赞用户原话（quote_locator），向 Market 输出未满足痛点与 Bundle 机会卡，向售后客服输出退货四层归因。"
        ),
        sort=6,
    ),
    dict(
        slug="market",
        expert_name="Market",
        product_name="市场洞察Agent&工作台",
        goal_code="G2",
        strategy_code="S3",
        workbench_url="https://mkt.luteos.com/",
        workbench_online=True,
        scenarios="市场容量与价格带分析 → 竞品格局拆解 → 品类准入与选品辅助决策",
        status_summary="进行中",
        owner="吴雨宁（TAM架构&推广） / 周健（DataPilot&Sage引擎） / 刘华丽（测试验证）",
        verified_summary=(
            "【Wave 2 · 四阶真实进度 50%（Stage 1 工作台 43 页 + DataPilot 122 万行核算 + Sage 53 专家流已就绪，待 Wave 2 接通独立飞书 Bot 回调）】"
            "mkt.luteos.com（107 表 / 53 证据源 / 三层 TAM 模型 / 7 国法规时间线）、DataPilot（年化 87M 止血 / 635M 造血 / 14 渠道边际 ROAS）与 Sage 四大确定性核算引擎均已验证；"
            "按四阶标尺（原 92% 挤水分至 50%）：目前核算能力在桌面/Web 端，Wave 2 需上线独立 @Market 飞书应用，让业务在群内直接发起新品 Go/No-Go 准入测算回调。"
        ),
        metrics_highlights=(
            "四阶真实进度|Stage 1 已通 (50%)|Wave 2 接入独立Bot\n"
            "全渠道经营核算底座|24个月 122万行 (止血87M)|DataPilot 实测\n"
            "市场洞察与证据源|43 页 / 107 表 / 53 源|mkt53 审计全过\n"
            "确定性核算与专家流|4 大引擎 / 53 位专家|Sage 3,088 测试通过"
        ),
        pending_gaps=(
            "【Stage 2 飞书回调缺口】Wave 2 上线独立 @Market 飞书应用，支持市场/选品人员在飞书输入目标品类/价格带直接回调返回三层 TAM 与毛利测算卡片\n"
            "【Stage 3-4 自进化缺口】统计飞书高频选品测算问题，自动沉淀为新品 Go/No-Go 准入脚本并固化至 mkt.luteos.com 半月自动刷新管线"
        ),
        report_links=(
            "Sage 项目成果总结 (11-02)|/reports-view/Sage/Sage-项目成果总结-20261102.html"
        ),
        extra_sites="",
        support_notes=(
            "【Wave 2｜当前 Stage 1→2 过渡 (50%)｜甘特收口：2026-11-10 ~ 2026-11-29】\n"
            "飞书Agent→工作台自进化交接链：吴雨宁于 11-23 前设计 @Market 飞书准入测算卡片（#24） → 周健于 11-29 前打通飞书调用 Sage/DataPilot 122万行引擎返回三层 TAM 与边际 ROAS 核算卡，并将高频选品测算沉淀为工作台 Go/No-Go 标准模板（#25 里程碑）。\n"
            "跨 Agent 交接协议（product / Echo → Market → Shopify / Paid Media）：Market 承接 G2 上游选品准入 Gate，用三层 TAM、7 国法规与 DataPilot 毛利模型对候选新品做 Go/No-Go 裁决，并输出 14 渠道边际 ROAS 前沿线指导预算分配。"
        ),
        sort=7,
    ),

    # ─────────────────────────── G2 / S4 ───────────────────────────
    dict(
        slug="source",
        expert_name="Source",
        product_name="数据采集Agent&工作台",
        goal_code="G2",
        strategy_code="S4",
        workbench_url="https://scrapy.luteos.com/",
        workbench_online=True,
        scenarios="统一采集平台与 monitor 层 → 分渠道采集器 → 统一表结构 → 采集工具 → 洞察工具",
        status_summary="进行中",
        owner="周健（采集中台研发） / 刘华丽（284端点控制台运营） / 吴雨宁（12表建模架构）",
        verified_summary=(
            "【Wave 1 · 四阶真实进度 78%（Stage 1 采集中台 55 页 + Stage 2「数说」独立飞书 Bot 已通过生产验收，正推进 Stage 3 临时补采自进化为常驻平台包）】"
            "scrapy.luteos.com 双生产在线，覆盖 70 平台 / 284 端点（200 实测跑通）、39 个 MCP 工具、L2–L4 授权门禁与 DatasetDriftEvent 漂移告警；"
            "飞书「数说」机器人已实现群内精确 @ 提及闸门、3 秒回执与后台异步采集回调。"
        ),
        metrics_highlights=(
            "飞书Bot与工作台|Stage 3 自进化 (78%)|「数说」Bot已验收\n"
            "覆盖平台与端点|70 平台 / 284 端点 (200 实测)|Source 报告 10-31\n"
            "注册 MCP 工具|39 个 + 4 类平台包|生产代码实测\n"
            "测试与工程规模|2,807 测试 / 928 提交|CI 7 job 全绿"
        ),
        pending_gaps=(
            "【Stage 2 深化】补齐「数说」飞书 Bot 的文件消息（CSV/Excel 导入）处理能力与 App Secret 轮换\n"
            "【Stage 3-4 自进化缺口】统计各业务群向 @数说 发起的高频临时抓数请求（≥10次/周），自动生成 CleaningPlan 与常驻 PlatformPackage 固化至 scrapy.luteos.com，并落库 order_id/sku_id 主键"
        ),
        report_links=(
            "Source 项目成果总结 (10-31)|/reports-view/Source/Source-项目成果总结-20261031.html"
        ),
        extra_sites="",
        support_notes=(
            "【Wave 1｜当前 Stage 3→4 自进化 (78%)｜甘特收口：2026-10-01 ~ 2026-11-15】\n"
            "飞书Agent→工作台自进化交接链：周健于 11-07 ~ 11-08 完成统一采集层及 TikTok/Reddit 常驻平台包固化（#26~#28） → 刘华丽于 11-09 ~ 11-14 统计 @数说 飞书Bot高频抓数请求并固化 YT/IG/FB/Trends 定时采集任务（#29~#32） → 吴雨宁于 11-15 前完成 order_id/sku_id 主键落库（#33 里程碑）。\n"
            "跨 Agent 交接协议（Source → 全域 6 大 Agent）：统一走「RawRecord → EntitySnapshot → DatasetVersion → DatasetDriftEvent」契约；高风控平台结合 plugin.luteos.com 浏览器插件与官方授权导入，禁止无授权盲爬。"
        ),
        sort=8,
    ),
    dict(
        slug="signal",
        expert_name="Signal",
        product_name="品牌声量Agent&工作台",
        goal_code="G2",
        strategy_code="S4",
        workbench_url="https://signal.luteos.com/",
        workbench_online=True,
        scenarios="多源采集 → 异动检测 → 归因分析 → 告警",
        status_summary="进行中",
        owner="吴雨宁（SOV口径&推广） / 周健（异动归因算法） / 刘华丽（告警运营）",
        verified_summary=(
            "【Wave 3 · 四阶真实进度 25%（已完成 Stage 1 历史声量与竞品雷达底座整合，待 Wave 3 接入独立飞书 Bot）】"
            "工作台（signal.luteos.com）在线，已整合 Melwater 7 源 34.7 万文档 ETL + Search Quality Gate（过滤 query_noise 噪音）以及 BrandOS 10 品牌 9,470 个竞品 ASIN 雷达；"
            "按四阶标尺（原 57% 回调至 25%）：尚未上线独立 @Signal 飞书应用推送异动卡片并接收业务归因确认回调。"
        ),
        metrics_highlights=(
            "四阶真实进度|Stage 1 已通 (25%)|Wave 3 接入独立Bot\n"
            "历史声量底座|7 源 / 34.7 万条唯一文档|Melwater ETL PASS\n"
            "竞品雷达建模|10 品牌 / 9,470 个竞品 ASIN|BrandOS 竞品雷达\n"
            "噪音阻断门禁|Search Quality Gate|阻断 query_noise"
        ),
        pending_gaps=(
            "【Stage 2 飞书回调缺口】Wave 3 上线独立 @Signal 飞书应用，当 SOV 或竞品价格发生异常波动时向飞书群推送卡片，支持业务点按钮确认归因或标记误报\n"
            "【Stage 3-4 自进化缺口】基于业务在飞书卡片上的「误报/真实异动」反馈回调，自进化优化 Search Quality Gate 降噪规则并固化至 signal.luteos.com"
        ),
        report_links="",
        extra_sites="",
        support_notes=(
            "【Wave 3｜当前 Stage 1 基座期 (25%)｜甘特收口：2026-11-24 ~ 2026-12-16】\n"
            "飞书Agent→工作台自进化交接链：吴雨宁于 12-05 前完成加权 SOV 飞书查询卡片设计（#34） → 周健于 12-12 前上线 @Signal 异动归因回调并基于「真异动/误报」点击反馈自进化 Search Quality Gate（#35 里程碑） → 刘华丽于 12-16 前固化 9,470 竞品雷达告警运营（#36）。\n"
            "跨 Agent 交接协议（Source → Signal → Vicky / Echo / Paid Media）：Signal 通过 Search Quality Gate 过滤噪音后计算加权 SOV 与搜索热度异动；发现竞品降价/上新推给 Paid Media 与 Shopify，发现权威媒体异动推给 Vicky。"
        ),
        sort=9,
    ),

    # ─────────────────────────── G3 / S5 ───────────────────────────
    dict(
        slug="shouheng",
        expert_name="守衡",
        product_name="内容治理Agent&工作台",
        goal_code="G3",
        strategy_code="S5",
        workbench_url="https://ca.luteos.com/",
        workbench_online=True,
        scenarios="内容上传 → 模型审核 → 审计判定 → 整改推送",
        status_summary="进行中",
        owner="刘华丽（审核台管理&测试） / 周健（判定引擎&ASR研发） / 吴雨宁（规则库架构）",
        verified_summary=(
            "【Wave 1 · 四阶真实进度 75%（Stage 1 审核台 14 页与 138 条规则引擎已投产；飞书 Bot 于 10-26 暂停待 Wave 1 恢复并接通申诉自进化）】"
            "ca.luteos.com（启用飞书扫码登录）与两段式判定引擎（227/227 契约自证）已上线，并收编了守衡 36 条 + Shopify 84 条母婴 + wiki 18 张规则卡及消毒器 Launch Gate 104 个 COS 证据；"
            "按四阶标尺（原 100% 实事求是回调至 75%）：需在 Wave 1 恢复守衡飞书 Bot 双向提审回调、完成视频 ASR 冷启动（T-430~T-435），并打通「高频申诉案例自动进化为新规则卡」。"
        ),
        metrics_highlights=(
            "四阶真实进度|Stage 2→3 自进化 (75%)|Wave 1 恢复飞书Bot\n"
            "引擎契约自证|227 / 227 通过 (141 检查器)|守衡报告 11-01\n"
            "跨库合规规则池|36 守衡 + 84 母婴 + 18 平台卡|三库合一收编\n"
            "Launch Gate 证据|104 COS 对象 / 120 校验全过|Workspace 实测"
        ),
        pending_gaps=(
            "【Stage 2 飞书恢复】恢复守衡独立飞书 Bot 运行，支持业务在飞书直接发图文/视频/文案触发预审卡片回调（PASS/REVIEW/BLOCK）\n"
            "【Stage 3-4 自进化与视频补齐】统计飞书提审中高频触发 REVIEW/申诉的边界表述（≥3次人工复核），自进化生成新语境守卫规则并迁入 ca.luteos.com；按 T-430~T-435 补齐视频 ASR"
        ),
        report_links=(
            "守衡 内容合规审查成果总结 (11-01)|/reports-view/守衡/守衡-项目成果总结-20261101.html"
        ),
        extra_sites="",
        support_notes=(
            "【Wave 1｜当前 Stage 2→3 自进化 (75%)｜甘特收口：2026-09-01 ~ 2026-11-14】\n"
            "飞书Agent→工作台自进化交接链：周健于 11-09 前恢复 @守衡 飞书Bot双向提审并统一三库 138 条 rule_id（#37） → 刘华丽于 11-12 前打通飞书整改卡片「申诉/已整改」回调并统计 ≥3 次争议判例自进化为新规则卡（#39 里程碑） → 11-14 前完成视频 ASR（T-430~T-435）冷启动验收（#38 里程碑）。\n"
            "跨 Agent 交接协议（全域内容/选品 → 守衡）：守衡是全组织唯一的 Claim Gate 与 Launch Gate 裁决源；未绑定实验室证据（claim_evidence_refs）的卖点（如 99.9% 杀菌率、医疗级）或未通过对抗性数字复核（M01–M12）的经营结论一律 BLOCK。"
        ),
        sort=10,
    ),
    dict(
        slug="daisy",
        expert_name="Daisy",
        product_name="多智能体Agent&工作台",
        goal_code="G3",
        strategy_code="S5",
        workbench_url="https://mas.luteos.com/",
        workbench_online=True,
        scenarios="知识库 → MAS → CLI",
        status_summary="进行中",
        owner="周健（MAS路由研发） / 吴雨宁（四层知识架构&CLI设计） / 刘华丽（门禁测试）",
        verified_summary=(
            "【Wave 3 · 四阶真实进度 60%（Stage 1 四大知识/技能站点在线 + Stage 3 Know/KB 自进化蒸馏底座已建成，待补齐独立飞书 Bot 与 9 Agent 统一适配）】"
            "mas / asset / brand / skills 四个站点全部在线；已建成全组织「高频问答 → SOP 自进化」的核心发动机：KB 平台 Lane B（交互数据反哺候选卡）与 Know（any2skills，三道门禁 577 测试通过，产出 17 技能 / 1,089 引文对象），"
            "以及 BrandOS 315 SKU 事实原子、路特星链 81 正式 Skill / 48 路由、Paper2Skills 1,054 算法 Skill 与灵词 72 个业务 Hook。"
        ),
        metrics_highlights=(
            "四阶真实进度|自进化引擎已建 (60%)|Lane B + Know 三道门禁\n"
            "星链工作流与路由|4 主链路 / 81 正式Skill / 48 路由|Starlink 250 测试通过\n"
            "算法图谱与资产池|1,054 算法Skill / 803 灵词资产|Paper2Skills & 灵词\n"
            "源引文验证技能|17 个技能 / 1,089 引文对象|Know 三道门禁实测"
        ),
        pending_gaps=(
            "【Stage 2 飞书回调缺口】上线独立 @Daisy 飞书应用，作为跨 Agent 知识检索与复杂长链路编排的飞书交互入口\n"
            "【Stage 3-4 全域赋能】将 Daisy 的「Lane B 飞书高频问答采集 → Know 三道门禁生成新 Skill → 固化至各专家工作台」流水线接通其余 13 个专家 Agent"
        ),
        report_links=(
            "Know (any2skills) 项目成果总结 (10-31)|/reports-view/Know/Know-项目成果总结-20261031.html"
        ),
        extra_sites=(
            "品牌知识库平台|https://asset.luteos.com/|online\n"
            "业务 Skills 平台 (Brand)|https://brand.luteos.com/|online\n"
            "业务 Skills 平台 (Skills)|https://skills.luteos.com/|online"
        ),
        support_notes=(
            "【Wave 3｜当前 Stage 2→3 自进化引擎底座 (60%)｜甘特收口：2026-11-25 ~ 2026-12-20】\n"
            "飞书Agent→工作台自进化总枢纽：吴雨宁于 12-13 前上线 @Daisy 飞书Bot与对话式 CLI（#42） → 周健于 12-18 前将 14 个独立飞书Bot的交互日志接入 Daisy 统一适配层与 48 条路由（#40 里程碑） → 12-20 前通过 Lane B + Know 三道门禁将全组高频问答编译为工作台标准 Skill（#41 里程碑）。\n"
            "跨 Agent 交接协议（Daisy 四层底座 → 全域 Agent）：asset.luteos.com 唯一签发 claim_id / evidence_id 与 Brand Token；skills.luteos.com 提供 72 个业务 Hook 触发器；brand.luteos.com 按 48 条路由规则将复杂经营问题分发至各专职 Agent。"
        ),
        sort=11,
    ),

    # ─────────────────────────── G3 / S6 ───────────────────────────
    dict(
        slug="main",
        expert_name="Main",
        product_name="全栈开发Agent&工作台",
        goal_code="G3",
        strategy_code="S6",
        workbench_url="https://main.luteos.com/",
        workbench_online=True,
        scenarios="研发需求定义 → 单向依赖架构与工具契约 → 自动化评测 (Eval) → 生产交付",
        status_summary="已上线",
        owner="周健（全栈底座研发） / 刘华丽（llm.luteos.com评测运营）",
        verified_summary=(
            "【Wave 1 · 四阶真实进度 100%（Stage 1 工作台 + Stage 2 独立飞书 Bot v1.0.5 长连接 + Stage 3-4 150 案例 Eval 门禁已固化）】"
            "main.luteos.com 与 llm.luteos.com 在线，独立飞书机器人（apps/bot-gateway，WS 长连接 + POST /events 双模式）已稳定运行；"
            "150 个真实问答评测 100% 通过（均分 0.99），264 个单测全过，并整合 184 个 Agent Profile 分发与 72 个 MCP 连接器蓝图。"
        ),
        metrics_highlights=(
            "飞书Bot与工作台|Stage 4 已固化 (100%)|Bot v1.0.5 长连接在线\n"
            "Main 问答评测|150 / 150 通过 (均分 0.99)|Main 报告 11-01\n"
            "可部署 Agent 档案|184 个 Profile / 72 MCP 蓝图|control-plane & 灵词\n"
            "单元与集成测试|264 个全部通过|pnpm test 实测"
        ),
        pending_gaps=(
            "【Stage 4 持续赋能】将 Main 的 apps/bot-gateway（飞书长连接+卡片回调+高频问题统计埋点）作为标准脚手架，支撑 Wave 2/3 其余独立飞书 Bot 快速复制"
        ),
        report_links=(
            "Main 项目成果总结 (11-01)|/reports-view/Main/Main-项目成果总结-20261101.html"
        ),
        extra_sites=(
            "模型选型与评测平台|https://llm.luteos.com/|online"
        ),
        support_notes=(
            "【Wave 1 标杆｜当前 Stage 4 已交付固化 (100%)｜甘特收口：2026-09-10 ~ 2026-11-01】\n"
            "飞书Agent→工作台自进化交接链：周健已于 11-01 交付独立飞书 Bot v1.0.5 与 bot-gateway 脚手架（#43 里程碑），刘华丽已在 llm.luteos.com 固化 264 项单测与各 Agent 自进化脚本回归门禁（#44）。\n"
            "定位边界：按 OGSM v1.0 规范，Main 作为纯工程研发底座提供 Agent SDK 运行时、模型路由评测（llm.luteos.com）、MCP 网关与容器沙箱，不占用业务 G 结算名额。"
        ),
        sort=12,
    ),
    dict(
        slug="shopify",
        expert_name="Shopify",
        product_name="ABI Shopify Agent&工作台",
        goal_code="G3",
        strategy_code="S6",
        workbench_url="https://shopify.luteos.com/",
        workbench_online=True,
        scenarios="ABI 独立站知识导航 → 独立站 360 审计 → AI 选品与 Listing 草稿上架",
        status_summary="进行中",
        owner="吴雨宁（独立站架构&推广） / 刘华丽（5岗Agent运营） / 周健（Fusion选品算法）",
        verified_summary=(
            "【Wave 2 · 四阶真实进度 53%（Stage 1 三大工作台、178 篇 RAG、5 岗 Agent 与 Fusion 选品已通，待 Wave 2 接通独立飞书 Bot 卡片审批回调）】"
            "shopify.luteos.com（360 审计定位 2.2MB JS 卡点 + 弃单追回）、platform-shopify.luteos.com（178 篇文档 RAG 100% 通过 + 5 岗 Agent 生成 DRAFT + 84 条母婴规则）与 product.luteos.com（Fusion SHI×CVI 选品 + 80+ 表数仓）均已上线；"
            "按四阶标尺（原 95% 挤水分至 53%）：需在 Wave 2 上线独立 @Shopify 飞书应用，支持运营在飞书直接收 Listing DRAFT 审批卡片并回写修改原因以驱动 SOP 自进化。"
        ),
        metrics_highlights=(
            "四阶真实进度|Stage 1-2 过渡 (53%)|Wave 2 接入独立Bot\n"
            "独立站 RAG 与 KG|178 篇 / 795 块 / 785 关系|pass-rate 1.00\n"
            "360 审计与竞品对标|10 竞品对标 / 5 岗位 Agent|定位 2.2MB JS 卡点\n"
            "Fusion 双平台选品|SHI×CVI 引擎 / 80+ 数仓表|23 页面 / 38 接口"
        ),
        pending_gaps=(
            "【Stage 2 飞书回调缺口】Wave 2 上线独立 @Shopify 飞书应用，当 5 岗 Agent 生成 Listing DRAFT 或检出 360 性能异常时推送飞书卡片，支持运营点按钮「批准发布 / 打回修改」\n"
            "【Stage 3-4 自进化缺口】自动统计飞书卡片上的打回修改原因（目标连续 2 周返工率 <20%），自进化更新 Listing 生成模板并固化至工作台"
        ),
        report_links=(
            "Shopify 项目成果总结 (11-02)|/reports-view/Shopify/Shopify-项目成果总结-20261102.html"
        ),
        extra_sites=(
            "ABI 独立站知识平台|https://platform-shopify.luteos.com/|online\n"
            "独立站 360 审计台|https://shopify.luteos.com/|online\n"
            "AI 选品平台|https://product.luteos.com/|online"
        ),
        support_notes=(
            "【Wave 2｜当前 Stage 1-2 过渡 (53%)｜甘特收口：2026-11-10 ~ 2026-11-28】\n"
            "飞书Agent→工作台自进化交接链：吴雨宁/刘华丽于 11-20 ~ 11-21 接入独立 @Shopify 飞书Bot，推送 5岗Agent 生成的 Listing DRAFT 审批卡并统计打回修改原因（#45/#46 里程碑，返工率<20%即进化固化） → 周健于 11-28 前打通 @Shopify 飞书触发 Fusion(SHI×CVI) 选品评分与 accio_to_shopify 一键转 Draft CSV 回调（#47）。\n"
            "跨 Agent 交接协议：Paid Media 与 Radar 投流前，强制校验 shopify.luteos.com 的落地页 JS 负载与 SCM 的 activity_stock_guard 库存护栏。"
        ),
        sort=13,
    ),
    dict(
        slug="pmo",
        expert_name="PMO",
        product_name="OGSM管理Agent&工作台",
        goal_code="G3",
        strategy_code="S6",
        workbench_url="https://pmo.luteos.com/",
        workbench_online=True,
        scenarios="OGSM 目标与策略对齐 → 14 大产品项目进度追踪 → 验收工作台总控导航 → 阶段成果汇报",
        status_summary="已上线",
        owner="周健（项目总控&全栈） / 吴雨宁（前端设计&推广） / 刘华丽（巡检&验收测试）",
        verified_summary=(
            "【Wave 1 · 四阶真实进度 100%（Stage 1 门户 + Stage 2 独立飞书 Bot 双向卡片回写 + Stage 4 每日 08:30 自动巡检与飞书表主从同步已固化）】"
            "pmo.luteos.com 与独立飞书应用（cli_aa187cc667b8dbea，WS 长连接 + Webhook 双通道 + 免打字卡片按钮回写）已全面投产；"
            "现已发布《3人核心铁三角 × 14独立飞书Agent × 品牌市场部岗位说明书与四阶自进化标准》（/sop），并上线「高频问题自进化漏斗（P0-1）」与「业务动作回写账本 measuredActions（P0-3）」。"
        ),
        metrics_highlights=(
            "四阶真实进度|Stage 4 已固化 (100%)|独立Bot+免打字卡片回写\n"
            "飞书Bot矩阵规划|14 个独立专家飞书应用|Wave 1-3 分批贯通\n"
            "核心团队唯一主责|周健18 / 刘华丽16 / 吴雨宁15|49项能力 MECE 锁定\n"
            "自进化晋升阈值|提问≥10次/周 & 返工<20%|固化入工作台 SOP"
        ),
        pending_gaps=(
            "在 T0（2026-11-30）前联合 Market（DataPilot）锁定 R1–R4 真实财务基线，并督办 Wave 1–3 共 14 个独立飞书 Bot 全部跑通四阶闭环"
        ),
        report_links=(
            "部门项目汇报 PPT 执行方案 v2|/docs/PPT汇报方案v2-部门项目汇报.md"
        ),
        extra_sites=(
            "岗位说明书与自进化标准|https://pmo.luteos.com/sop|online"
        ),
        support_notes=(
            "【Wave 1 标杆｜当前 Stage 4 已交付固化 (100%)｜甘特收口：2026-10-25 ~ 2026-11-03】\n"
            "飞书Agent→工作台自进化交接链：周健/吴雨宁已于 11-03 交付 @PMO 飞书双向卡片回写、Wave 1–3 无冲突甘特排期（#48/#49）及 /sop 页面的「高频问题自进化实时漏斗 + 业务动作回写账本（measuredActions）」。"
        ),
        sort=14,
    ),
]

CAPABILITIES = [
    # ─── 1. Emily (Wave 1 · 11月第1–2周收口 · 独立飞书Bot已通，均值 72%) ───
    dict(project_slug="emily", scenario_line="社媒趋势洞察 → 内容策略 → 脚本生成",
         name="爆款/趋势洞察", description="【吴雨宁｜Stage 3→4 固化收口(85%)｜Wave 1】social.luteos.com 工作台 + @Emily 飞书Bot已打通跨平台趋势抓取与周五自动周报卡片；本周将群内高频趋势追问固化为工作台SOP",
         status="进行中", verify_state="已验证", progress_pct=85,
         start_date="2026-09-08", end_date="2026-11-08", owner="吴雨宁", is_milestone=False, sort=1),
    dict(project_slug="emily", scenario_line="社媒趋势洞察 → 内容策略 → 脚本生成",
         name="互动追踪&评论解析", description="【刘华丽｜Stage 3 自进化中(75%)｜Wave 1】@Emily 飞书Bot支持群内回调查询评论5档情绪与主题拆解；刘华丽统计社媒组高频提问(≥10次/周)于 11-11 完成SOP进化",
         status="进行中", verify_state="已验证", progress_pct=75,
         start_date="2026-09-08", end_date="2026-11-11", owner="刘华丽", is_milestone=True, sort=2),
    dict(project_slug="emily", scenario_line="社媒趋势洞察 → 内容策略 → 脚本生成",
         name="内容策略生成", description="【吴雨宁｜Stage 2→3 自进化中(65%)｜Wave 1】已注入10品牌Brand Token护栏(均分88)，支持在飞书 @Emily 触发策略卡片；11-13 前沉淀稳定迁入工作台自动化工位",
         status="进行中", verify_state="部分验证", progress_pct=65,
         start_date="2026-09-21", end_date="2026-11-13", owner="吴雨宁", is_milestone=False, sort=3),
    dict(project_slug="emily", scenario_line="社媒趋势洞察 → 内容策略 → 脚本生成",
         name="脚本生成", description="【周健｜Stage 2→3 自进化中(65%)｜Wave 1】支持飞书群内 @Emily 生成带 claim_id 的投放脚本初稿；11-15 前完成高频修改项自进化模板并固化至工作台",
         status="进行中", verify_state="部分验证", progress_pct=65,
         start_date="2026-09-21", end_date="2026-11-15", owner="周健", is_milestone=True, sort=4),

    # ─── 2. Clone (Wave 2 · 11月第3–4周收口 · 工作台与算法已通，接入独立飞书Bot，均值 45%) ───
    dict(project_slug="clone", scenario_line="爆款视频拆解 → 品牌脚本复刻",
         name="TikTok 爆款视频结构拆解", description="【周健｜Stage 1 已通/接入飞书Bot(50%)｜Wave 2】video.luteos.com 与 Recipe 拆解引擎已验证；11-21 前上线独立 @Clone 飞书Bot，支持编导发视频链接直接回调拆片卡片",
         status="进行中", verify_state="已验证", progress_pct=50,
         start_date="2026-11-10", end_date="2026-11-21", owner="周健", is_milestone=False, sort=5),
    dict(project_slug="clone", scenario_line="爆款视频拆解 → 品牌脚本复刻",
         name="品牌定制 Recipe 脚本生成", description="【刘华丽｜Stage 1 已通/接入飞书Bot(40%)｜Wave 2】13/14 Eval 通过 + S1-S5 权利门禁已建；11-28 前打通飞书卡片点按钮生成复刻脚本并统计编导高频修改项自进化",
         status="进行中", verify_state="已验证", progress_pct=40,
         start_date="2026-11-14", end_date="2026-11-28", owner="刘华丽", is_milestone=True, sort=6),

    # ─── 3. Vicky (Wave 2 · 11月第3–4周收口 · 7表重算已通，接入独立飞书Bot双向派单，均值 50%) ───
    dict(project_slug="vicky", scenario_line="PR 线：竞品监测 → 风险预警 → 工作台协同",
         name="线索管理", description="【吴雨宁｜Stage 1-2 过渡(50%)｜Wave 2】pr.luteos.com 与 246 家媒体/347 条报道双向同步已通；11-19 前接入独立 @Vicky 飞书Bot支持媒介在群内回调录入与查询线索",
         status="进行中", verify_state="已验证", progress_pct=50,
         start_date="2026-11-10", end_date="2026-11-19", owner="吴雨宁", is_milestone=False, sort=7),
    dict(project_slug="vicky", scenario_line="PR 线：竞品监测 → 风险预警 → 工作台协同",
         name="线索推荐", description="【周健｜Stage 1 已通/接入飞书Bot(45%)｜Wave 2】话题推荐与编辑匹配算法已建；11-24 前支持在飞书 @Vicky 提新品需求自动回调推荐目标榜单编辑卡片并统计高频匹配规则",
         status="进行中", verify_state="已验证", progress_pct=45,
         start_date="2026-11-12", end_date="2026-11-24", owner="周健", is_milestone=False, sort=8),
    dict(project_slug="vicky", scenario_line="舆情线：看板对话化 → 自动分类 → 工单闭环",
         name="舆情预警", description="【刘华丽｜Stage 1-2 过渡(50%)｜Wave 2】舆情分级与 57 条 Action Register 已建；11-22 前打通 @Vicky 飞书预警卡片按钮一键认领工单并回写处置结果",
         status="进行中", verify_state="已验证", progress_pct=50,
         start_date="2026-11-10", end_date="2026-11-22", owner="刘华丽", is_milestone=False, sort=9),
    dict(project_slug="vicky", scenario_line="舆情线：看板对话化 → 自动分类 → 工单闭环",
         name="数据查询与分析", description="【刘华丽｜Stage 2 定时重算已通(55%)｜Wave 2】飞书 7 表每日 09:50 自动重算已稳；11-27 前通过 @Vicky 飞书Bot统计 PR 团队高频查询(≥10次/周)自进化固化为工作台报表",
         status="进行中", verify_state="已验证", progress_pct=55,
         start_date="2026-11-14", end_date="2026-11-27", owner="刘华丽", is_milestone=True, sort=10),

    # ─── 4. GEO (Wave 3 · 12月第1–4周收口 · Stage 1 基座期，均值 22%) ───
    dict(project_slug="geo", scenario_line="问句库 → 采集探针 → 解析与指标 → 诊断洞察 → 内容生成 → 复测报告",
         name="配置与问句库", description="【吴雨宁｜Stage 1 基座就绪(30%)｜Wave 3】已整合 HSA/FSA 报销、职场妈妈等初始问句库；12-04 前接入独立 @GEO 飞书Bot收集业务高频提问自动扩充 20问/ASIN",
         status="进行中", verify_state="部分验证", progress_pct=30,
         start_date="2026-11-24", end_date="2026-12-04", owner="吴雨宁", is_milestone=False, sort=11),
    dict(project_slug="geo", scenario_line="问句库 → 采集探针 → 解析与指标 → 诊断洞察 → 内容生成 → 复测报告",
         name="采集探针", description="【周健｜Stage 1 基座就绪(30%)｜Wave 3】Perplexity 5/5 基线与第 9 主键 ai_answer_snapshot_id 已定稿；12-06 前支持在飞书 @GEO 触发实时探针采样卡片",
         status="进行中", verify_state="部分验证", progress_pct=30,
         start_date="2026-11-24", end_date="2026-12-06", owner="周健", is_milestone=True, sort=12),
    dict(project_slug="geo", scenario_line="问句库 → 采集探针 → 解析与指标 → 诊断洞察 → 内容生成 → 复测报告",
         name="解析与指标", description="【周健｜Stage 1 基座就绪(25%)｜Wave 3】品牌提及与 Best Overall 排位解析逻辑已验证；12-11 前接通飞书卡片问答与工作台指标自动化",
         status="进行中", verify_state="部分验证", progress_pct=25,
         start_date="2026-12-01", end_date="2026-12-11", owner="周健", is_milestone=False, sort=13),
    dict(project_slug="geo", scenario_line="问句库 → 采集探针 → 解析与指标 → 诊断洞察 → 内容生成 → 复测报告",
         name="诊断洞察", description="【吴雨宁｜Stage 1 基座就绪(20%)｜Wave 3】定位可见度缺口（保险渠道/Schema缺失），12-15 前上线飞书诊断卡片一键派单给 Vicky 与 Shopify",
         status="进行中", verify_state="部分验证", progress_pct=20,
         start_date="2026-12-03", end_date="2026-12-15", owner="吴雨宁", is_milestone=False, sort=14),
    dict(project_slug="geo", scenario_line="问句库 → 采集探针 → 解析与指标 → 诊断洞察 → 内容生成 → 复测报告",
         name="内容生成", description="【周健｜Stage 1 事实源就绪(15%)｜Wave 3】基于 BrandOS 315 SKU 的 16 类事实文件生成权威内容；12-20 前接入 @GEO 飞书生成回调与自进化模板",
         status="方案中", verify_state="待验证", progress_pct=15,
         start_date="2026-12-08", end_date="2026-12-20", owner="周健", is_milestone=False, sort=15),
    dict(project_slug="geo", scenario_line="问句库 → 采集探针 → 解析与指标 → 诊断洞察 → 内容生成 → 复测报告",
         name="复测与报告", description="【刘华丽｜Stage 1 方案就绪(10%)｜Wave 3】刘华丽负责 @GEO 控制台月度复测调度、高频问题沉淀审核与 12-26 月报卡片签发",
         status="方案中", verify_state="待验证", progress_pct=10,
         start_date="2026-12-15", end_date="2026-12-26", owner="刘华丽", is_milestone=True, sort=16),

    # ─── 5. Radar (Wave 3 · 12月第1–4周收口 · 彻底消除 11-06 旧日期矛盾，均值 20%) ───
    dict(project_slug="radar", scenario_line="粉丝分析 → 合作计划 → 动态监测 → 机会推荐",
         name="IP 合作计划制定", description="【吴雨宁｜Stage 1 基座就绪(25%)｜Wave 3】已导入 wiki 四维达人分层与 creator_id 授权七元组架构；12-05 前接入独立 @Radar 飞书Bot供 BD 发起背调回调（已从原11-06调入Wave 3）",
         status="进行中", verify_state="部分验证", progress_pct=25,
         start_date="2026-11-24", end_date="2026-12-05", owner="吴雨宁", is_milestone=True, sort=17),
    dict(project_slug="radar", scenario_line="粉丝分析 → 合作计划 → 动态监测 → 机会推荐",
         name="全渠道动态监测", description="【刘华丽｜Stage 1 方案就绪(20%)｜Wave 3】刘华丽负责 @Radar 控制台运营，12-16 前打通飞书卡片催办寄样回收(≥60%)与二创授权到期预警(<5%)",
         status="进行中", verify_state="部分验证", progress_pct=20,
         start_date="2026-12-01", end_date="2026-12-16", owner="刘华丽", is_milestone=False, sort=18),
    dict(project_slug="radar", scenario_line="粉丝分析 → 合作计划 → 动态监测 → 机会推荐",
         name="合作机会识别", description="【周健｜Stage 1 方案就绪(15%)｜Wave 3】结合 TikTok Affiliate 准入预检研发合作信号识别算法，12-23 前将 BD 飞书高频筛选条件自进化为工作台 SOP",
         status="方案中", verify_state="待验证", progress_pct=15,
         start_date="2026-12-08", end_date="2026-12-23", owner="周健", is_milestone=False, sort=19),

    # ─── 6. Echo (Wave 1 · 11月第1–2周收口 · 10步日更已固化，升级飞书双向回调与自进化，均值 72%) ───
    dict(project_slug="echo", scenario_line="舆情线：品牌/品类/SPU舆情预警",
         name="多渠道数据查询", description="【吴雨宁｜Stage 3→4 固化收口(85%)｜Wave 1】radar.luteos.com 已汇聚 Reddit 日更与 712.2 万条全渠道 VOC（v6.4 字典 2,346 行），11-09 前完成飞书群内 @Echo 按 SPU 实时问数回调",
         status="进行中", verify_state="已验证", progress_pct=85,
         start_date="2026-10-15", end_date="2026-11-09", owner="吴雨宁", is_milestone=False,
         integration_name="数据采集插件", integration_url="https://plugin.luteos.com/", sort=20),
    dict(project_slug="echo", scenario_line="舆情线：品牌/品类/SPU舆情预警",
         name="风险指数&机会洞察", description="【刘华丽｜Stage 3 自进化中(75%)｜Wave 1】早 07:05 10步无人值守飞书晨报已运行；11-13 前增加晨报卡片按钮回调（点按钮认领痛点/追问原话）并统计高频问题进化 SpuBinding",
         status="进行中", verify_state="已验证", progress_pct=75,
         start_date="2026-10-20", end_date="2026-11-13", owner="刘华丽", is_milestone=True, sort=21),
    dict(project_slug="echo", scenario_line="话题线：高质量内容机会挖掘",
         name="拖拉式多维分析", description="【吴雨宁｜Stage 2→3 自进化中(65%)｜Wave 1】已建成标签治理工作台 v1 与 29 张 Superset 看板；11-15 前将飞书群内高频交叉查询维度（≥10次/周）迁移固化至拖拽分析台",
         status="进行中", verify_state="已验证", progress_pct=65,
         start_date="2026-10-25", end_date="2026-11-15", owner="吴雨宁", is_milestone=False, sort=22),
    dict(project_slug="echo", scenario_line="产品机会线：品类机会挖掘",
         name="自动化品类洞察报告", description="【周健｜Stage 2→3 自进化中(65%)｜Wave 1】86倍重算与 VOA ProductOpportunityCard 已打通；11-16 前将飞书回调确认的品类痛点自动编译为 report.luteos.com 标准报告模板",
         status="进行中", verify_state="已验证", progress_pct=65,
         start_date="2026-10-20", end_date="2026-11-16", owner="周健", is_milestone=True,
         integration_name="品类洞察平台 / 品类洞察报告", integration_url="https://business.luteos.com/", sort=23),

    # ─── 7. Market (Wave 2 · 11月第3–4周收口 · 工作台与核算引擎已就绪，接入独立飞书Bot，均值 50%) ───
    dict(project_slug="market", scenario_line="市场洞察与跨境专家核算",
         name="市场洞察工作台", description="【吴雨宁｜Stage 1 已通/接入飞书Bot(50%)｜Wave 2】mkt.luteos.com（43页/53证据源/三层TAM）已上线；11-23 前接入独立 @Market 飞书Bot，支持业务在飞书查询容量与法规准入卡片",
         status="进行中", verify_state="已验证", progress_pct=50,
         start_date="2026-11-10", end_date="2026-11-23", owner="吴雨宁", is_milestone=False, sort=24),
    dict(project_slug="market", scenario_line="市场洞察与跨境专家核算",
         name="跨境电商核算引擎与专家工作流", description="【周健｜Stage 1 已通/接入飞书Bot(50%)｜Wave 2】Sage 4大核算引擎与 DataPilot 122万行诊断（止血87M/造血635M）已验证；11-29 前打通飞书 @Market 触发新品毛利核算回调并自进化SOP",
         status="进行中", verify_state="已验证", progress_pct=50,
         start_date="2026-11-14", end_date="2026-11-29", owner="周健", is_milestone=True, sort=25),

    # ─── 8. Source (Wave 1 · 11月第1–2周收口 ·「数说」独立飞书Bot已验收，均值 76%) ───
    dict(project_slug="source", scenario_line="统一采集平台与 monitor 层 → 分渠道采集器 → 统一表结构 → 采集工具 → 洞察工具",
         name="统一采集平台与 monitor 层", description="【周健｜Stage 3→4 固化收口(85%)｜Wave 1】scrapy.luteos.com 284 端点（200 实测）与飞书「数说」Bot（3秒回执+异步采集卡片回调）已投产；11-07 完成高频临时采集自动转常驻包",
         status="进行中", verify_state="已验证", progress_pct=85,
         start_date="2026-10-01", end_date="2026-11-07", owner="周健", is_milestone=True, sort=26),
    dict(project_slug="source", scenario_line="统一采集平台与 monitor 层 → 分渠道采集器 → 统一表结构 → 采集工具 → 洞察工具",
         name="TikTok 采集MCP/skill", description="【周健｜Stage 3→4 固化收口(85%)｜Wave 1】16工具/21表已固化并在「数说」飞书Bot开放调用，11-08 完成 Emily/Clone 高频抓数字段自进化固化",
         status="进行中", verify_state="已验证", progress_pct=85,
         start_date="2026-10-01", end_date="2026-11-08", owner="周健", is_milestone=False, sort=27),
    dict(project_slug="source", scenario_line="统一采集平台与 monitor 层 → 分渠道采集器 → 统一表结构 → 采集工具 → 洞察工具",
         name="Reddit 采集MCP/skill", description="【周健｜Stage 3→4 固化收口(85%)｜Wave 1】JSON/DOM双通道采集与置信度标记已固化至早07:05流水线及「数说」飞书回调（11-08 收口）",
         status="进行中", verify_state="已验证", progress_pct=85,
         start_date="2026-10-05", end_date="2026-11-08", owner="周健", is_milestone=False, sort=28),
    dict(project_slug="source", scenario_line="统一采集平台与 monitor 层 → 分渠道采集器 → 统一表结构 → 采集工具 → 洞察工具",
         name="YouTube 采集MCP/skill", description="【刘华丽｜Stage 3 自进化中(75%)｜Wave 1】已接入「数说」飞书Bot回调与控制台配额监控；11-09 前统计业务高频频道/字幕抓取需求并固化为工作台定时任务",
         status="进行中", verify_state="已验证", progress_pct=75,
         start_date="2026-10-15", end_date="2026-11-09", owner="刘华丽", is_milestone=False, sort=29),
    dict(project_slug="source", scenario_line="统一采集平台与 monitor 层 → 分渠道采集器 → 统一表结构 → 采集工具 → 洞察工具",
         name="Instagram 采集MCP/skill", description="【刘华丽｜Stage 3 自进化中(75%)｜Wave 1】IG Graph授权门控与「数说」飞书回调已通；11-11 前统计高频达人/竞品帖采集需求迁入工作台",
         status="进行中", verify_state="已验证", progress_pct=75,
         start_date="2026-10-20", end_date="2026-11-11", owner="刘华丽", is_milestone=False, sort=30),
    dict(project_slug="source", scenario_line="统一采集平台与 monitor 层 → 分渠道采集器 → 统一表结构 → 采集工具 → 洞察工具",
         name="Facebook 采集MCP/skill", description="【刘华丽｜Stage 2→3 自进化中(70%)｜Wave 1】FB 页面互动快照已接入「数说」Bot，11-13 前根据社媒组高频查询自进化沉淀常驻任务",
         status="进行中", verify_state="已验证", progress_pct=70,
         start_date="2026-10-25", end_date="2026-11-13", owner="刘华丽", is_milestone=False, sort=31),
    dict(project_slug="source", scenario_line="统一采集平台与 monitor 层 → 分渠道采集器 → 统一表结构 → 采集工具 → 洞察工具",
         name="Google Trends 采集MCP/skill", description="【刘华丽｜Stage 3 自进化中(70%)｜Wave 1】趋势词表与关联查询已接入「数说」飞书回调，11-14 前统计高频搜索词并入工作台日常监控池",
         status="进行中", verify_state="已验证", progress_pct=70,
         start_date="2026-10-25", end_date="2026-11-14", owner="刘华丽", is_milestone=False, sort=32),
    dict(project_slug="source", scenario_line="统一采集平台与 monitor 层 → 分渠道采集器 → 统一表结构 → 采集工具 → 洞察工具",
         name="上游数据底座支撑", description="【吴雨宁｜Stage 3 自进化中(75%)｜Wave 1】11-15 前完成 order_id/sku_id 主键（含468品类漂移修正）与 48 张 abi schema 落库，支撑 6 大 Agent 飞书与工作台同源取数",
         status="进行中", verify_state="部分验证", progress_pct=75,
         start_date="2026-10-15", end_date="2026-11-15", owner="吴雨宁", is_milestone=True, sort=33),

    # ─── 9. Signal (Wave 3 · 12月第1–3周收口 · Stage 1 基座期，均值 25%) ───
    dict(project_slug="signal", scenario_line="多源采集 → 异动检测 → 归因分析 → 告警",
         name="品牌曝光&热度监控", description="【吴雨宁｜Stage 1 基座就绪(25%)｜Wave 3】signal.luteos.com 与 Melwater 34.7 万文档 ETL 已就绪；12-05 前接入独立 @Signal 飞书Bot支持群内查询加权 SOV 与净情感卡片",
         status="进行中", verify_state="部分验证", progress_pct=25,
         start_date="2026-11-24", end_date="2026-12-05", owner="吴雨宁", is_milestone=False, sort=34),
    dict(project_slug="signal", scenario_line="多源采集 → 异动检测 → 归因分析 → 告警",
         name="声量异动识别", description="【周健｜Stage 1 基座就绪(25%)｜Wave 3】Search Quality Gate 降噪算法已建；12-12 前打通飞书异动告警卡片回调（业务点按钮标记真危机/误报噪音以驱动规则自进化）",
         status="进行中", verify_state="部分验证", progress_pct=25,
         start_date="2026-11-28", end_date="2026-12-12", owner="周健", is_milestone=True, sort=35),
    dict(project_slug="signal", scenario_line="多源采集 → 异动检测 → 归因分析 → 告警",
         name="竞品动作&发布监测", description="【刘华丽｜Stage 1 基座就绪(25%)｜Wave 3】BrandOS 10 品牌 9,470 个竞品 ASIN 雷达已导入；12-16 前接通 @Signal 飞书竞品降价/上新卡片推送与控制台运营",
         status="进行中", verify_state="已验证", progress_pct=25,
         start_date="2026-12-01", end_date="2026-12-16", owner="刘华丽", is_milestone=False, sort=36),

    # ─── 10. 守衡 (Wave 1 · 11月第1–2周收口 · 恢复独立飞书Bot并接通申诉自进化，均值 73%) ───
    dict(project_slug="shouheng", scenario_line="内容上传 → 模型审核 → 审计判定 → 整改推送",
         name="内容审计规则引擎", description="【周健｜Stage 3→4 固化收口(85%)｜Wave 1】两段式判定引擎（227/227 自证）与三库 138 条规则已投产；11-09 前恢复 @守衡 飞书Bot双向提审并把高频申诉判例自动编译为新规则",
         status="进行中", verify_state="已验证", progress_pct=85,
         start_date="2026-09-01", end_date="2026-11-09", owner="周健", is_milestone=False, sort=37),
    dict(project_slug="shouheng", scenario_line="内容上传 → 模型审核 → 审计判定 → 整改推送",
         name="经营动作与结论复核", description="【刘华丽｜Stage 2→3 自进化中(70%)｜Wave 1】文档/图片OCR/消毒器 Launch Gate（104 COS证据）已跑通；11-14 前完成视频 ASR（T-430~T-435）冷启动与飞书提审验收",
         status="进行中", verify_state="已验证", progress_pct=70,
         start_date="2026-09-15", end_date="2026-11-14", owner="刘华丽", is_milestone=True, sort=38),
    dict(project_slug="shouheng", scenario_line="内容上传 → 模型审核 → 审计判定 → 整改推送",
         name="复核结论与整改清单", description="【刘华丽｜Stage 2→3 自进化中(70%)｜Wave 1】ca.luteos.com 14页审核台在线；11-12 前恢复飞书整改卡片一键推送与「申诉/已整改」按钮回调，统计高频违规点反哺前置培训SOP",
         status="进行中", verify_state="已验证", progress_pct=70,
         start_date="2026-09-20", end_date="2026-11-12", owner="刘华丽", is_milestone=True, sort=39),

    # ─── 11. Daisy (Wave 3 · 12月第2–3周收口 · 自进化蒸馏底座已建，接入独立飞书Bot与14 Agent适配，均值 60%) ───
    dict(project_slug="daisy", scenario_line="知识库 → MAS → CLI",
         name="各 Agent 统一接入", description="【周健｜Stage 2 建设中(50%)｜Wave 3】12-18 前将 14 个独立专家 Agent 的飞书高频问答日志统一接入 Daisy 适配层与 48 条星链路由",
         status="进行中", verify_state="部分验证", progress_pct=50,
         start_date="2026-12-01", end_date="2026-12-18", owner="周健", is_milestone=True, sort=40),
    dict(project_slug="daisy", scenario_line="知识库 → MAS → CLI",
         name="统一入口与品牌知识库", description="【吴雨宁｜Stage 3 自进化引擎已通(70%)｜Wave 3】已建成 KB 平台 Lane B（飞书交互数据自动蒸馏候选卡）+ Know 三道门禁（17技能/577测试）+ 315 SKU 事实原子（12-20 终验）",
         status="进行中", verify_state="已验证", progress_pct=70,
         start_date="2026-11-25", end_date="2026-12-20", owner="吴雨宁", is_milestone=True,
         integration_name="品牌知识库平台 (asset.luteos.com)", integration_url="https://asset.luteos.com/", sort=41),
    dict(project_slug="daisy", scenario_line="知识库 → MAS → CLI",
         name="对话式 CLI 界面", description="【吴雨宁｜Stage 2→3 演进(60%)｜Wave 3】联通 Starlink（81 Skill）、Paper2Skills（1,054 算法 Skill）与灵词（72 Hook），12-13 前接入独立 @Daisy 飞书Bot与 Web CLI",
         status="进行中", verify_state="已验证", progress_pct=60,
         start_date="2026-11-25", end_date="2026-12-13", owner="吴雨宁", is_milestone=False,
         integration_name="业务skills平台 (brand / skills)", integration_url="https://skills.luteos.com/", sort=42),

    # ─── 12. Main (Wave 1 标杆已交付 · 独立飞书Bot v1.0.5 + Eval 门禁 100%) ───
    dict(project_slug="main", scenario_line="全栈研发工作台与模型评测",
         name="全栈开发 Agent 与飞书机器人", description="【周健｜Stage 4 已交付固化(100%)｜Wave 1】独立飞书 Bot（v1.0.5，WS长连接+Webhook）与 main.luteos.com 已投产（150/150 评测通过），提供全组标准 bot-gateway 模板",
         status="已完成", verify_state="已验证", progress_pct=100,
         start_date="2026-09-10", end_date="2026-11-01", owner="周健", is_milestone=True, sort=43),
    dict(project_slug="main", scenario_line="全栈研发工作台与模型评测",
         name="模型选型与评测平台", description="【刘华丽｜Stage 4 已交付固化(100%)｜Wave 1】llm.luteos.com（264单测全过）已固化对各 Agent 自进化 SOP 脚本的门禁回归测试与 Token 成本监控",
         status="已完成", verify_state="已验证", progress_pct=100,
         start_date="2026-09-20", end_date="2026-11-01", owner="刘华丽", is_milestone=False,
         integration_name="模型选型与评测", integration_url="https://llm.luteos.com/", sort=44),

    # ─── 13. Shopify (Wave 2 · 11月第3–4周收口 · 三站点与5岗Agent已通，接入独立飞书Bot卡片审批回调，均值 53%) ───
    dict(project_slug="shopify", scenario_line="ABI独立站 → 独立站360审计 → AI选品",
         name="ABI 独立站知识平台", description="【吴雨宁｜Stage 2 过渡(55%)｜Wave 2】platform-shopify.luteos.com（178篇文档/795块RAG 100%通过）已上线；11-20 前接入独立 @Shopify 飞书Bot统计运营高频问答并自动扩充SOP库",
         status="进行中", verify_state="已验证", progress_pct=55,
         start_date="2026-11-10", end_date="2026-11-20", owner="吴雨宁", is_milestone=False,
         integration_name="ABI独立站", integration_url="https://platform-shopify.luteos.com/", sort=45),
    dict(project_slug="shopify", scenario_line="ABI独立站 → 独立站360审计 → AI选品",
         name="独立站 360 审计与 Listing 上架", description="【刘华丽｜Stage 2 过渡(55%)｜Wave 2】5岗Agent（只写DRAFT）与360审计（定位2.2MB JS卡点）已上线；11-21 前打通飞书卡片审批 DRAFT 并统计打回原因（连续2周返工率<20%即进化固化）",
         status="进行中", verify_state="已验证", progress_pct=55,
         start_date="2026-11-10", end_date="2026-11-21", owner="刘华丽", is_milestone=True,
         integration_name="独立站360审计", integration_url="https://shopify.luteos.com/", sort=46),
    dict(project_slug="shopify", scenario_line="ABI独立站 → 独立站360审计 → AI选品",
         name="AI 选品平台", description="【周健｜Stage 1 已通/接入飞书Bot(50%)｜Wave 2】product.luteos.com（Fusion SHI×CVI 选品 + 80+表数仓 + accio_to_shopify）已上线；11-28 前支持在飞书 @Shopify 触发选品评分卡片回调",
         status="进行中", verify_state="已验证", progress_pct=50,
         start_date="2026-11-14", end_date="2026-11-28", owner="周健", is_milestone=False,
         integration_name="AI选品", integration_url="https://product.luteos.com/", sort=47),

    # ─── 14. PMO (Wave 1 标杆已交付 · 独立飞书Bot双向卡片回写+自动巡检 100%) ───
    dict(project_slug="pmo", scenario_line="OGSM 全景导图 → 14 大项目管理 → 汇报演示",
         name="OGSM 全景思维导图与项目矩阵", description="【周健｜Stage 4 已交付固化(100%)｜Wave 1】pmo.luteos.com 与独立 @PMO 飞书Bot（WS长连接+免打字卡片按钮回写）已投产，落地四阶自进化标尺与 Wave 1-3 无冲突甘特统筹",
         status="已完成", verify_state="已验证", progress_pct=100,
         start_date="2026-10-25", end_date="2026-11-03", owner="周健", is_milestone=True, sort=48),
    dict(project_slug="pmo", scenario_line="OGSM 全景导图 → 14 大项目管理 → 汇报演示",
         name="跨项目甘特图、看板与里程碑汇报", description="【吴雨宁｜Stage 4 已交付固化(100%)｜Wave 1】已发布《岗位说明书与自进化标准》(/sop)，集成飞书表主从同步、08:30巡检催办与10页PPTX导出",
         status="已完成", verify_state="已验证", progress_pct=100,
         start_date="2026-10-30", end_date="2026-11-03", owner="吴雨宁", is_milestone=True, sort=49),
]

SOP_CANDIDATES = [
    dict(project_slug="pmo", expert_name="PMO", wave="Wave 1",
         topic="群内高频催办临期里程碑与飞书表排期对账", weekly_ask_count=18, reject_count=0, rework_rate_pct=5,
         current_stage="Stage 4", target_workbench_sop="pmo.luteos.com 每日08:30自动巡检催办 + 飞书表主从同步",
         owner="周健", due_date="2026-11-03"),
    dict(project_slug="main", expert_name="Main", wave="Wave 1",
         topic="各专家飞书Bot长连接回调与失败Trace回归评测", weekly_ask_count=15, reject_count=1, rework_rate_pct=8,
         current_stage="Stage 4", target_workbench_sop="main/llm.luteos.com 标准 bot-gateway 脚手架与 Eval 门禁",
         owner="刘华丽", due_date="2026-11-01"),
    dict(project_slug="source", expert_name="Source", wave="Wave 1",
         topic="业务群临时请求抓取竞品独立站商品价格与TikTok/Reddit热帖", weekly_ask_count=22, reject_count=2, rework_rate_pct=12,
         current_stage="Stage 3", target_workbench_sop="scrapy.luteos.com 常驻 PlatformPackage 与 Drift 漂移告警",
         owner="周健", due_date="2026-11-07"),
    dict(project_slug="shouheng", expert_name="守衡", wave="Wave 1",
         topic="母婴消毒率/静音/医疗级等高风险宣称边界申诉复核", weekly_ask_count=14, reject_count=4, rework_rate_pct=15,
         current_stage="Stage 3", target_workbench_sop="ca.luteos.com 两段式语境守卫新控制点规则与 Launch Gate",
         owner="刘华丽", due_date="2026-11-12"),
    dict(project_slug="emily", expert_name="Emily", wave="Wave 1",
         topic="社媒运营高频询问TikTok本周爆款钩子与Brand Token合规脚本", weekly_ask_count=16, reject_count=3, rework_rate_pct=18,
         current_stage="Stage 3", target_workbench_sop="social.luteos.com 品牌Token策略与单变量批量脚本工位",
         owner="吴雨宁", due_date="2026-11-15"),
    dict(project_slug="echo", expert_name="Echo", wave="Wave 1",
         topic="产品与客服追问特定SPU（M5/清洗机）差评原话与退货四层归因", weekly_ask_count=19, reject_count=3, rework_rate_pct=16,
         current_stage="Stage 3", target_workbench_sop="radar/business.luteos.com SpuBinding 自动映射与品类机会报告",
         owner="刘华丽", due_date="2026-11-16"),
    dict(project_slug="shopify", expert_name="Shopify", wave="Wave 2",
         topic="独立站新品Listing DRAFT五点描述合规修改与KOL落地页卡顿排查", weekly_ask_count=9, reject_count=3, rework_rate_pct=22,
         current_stage="Stage 2", target_workbench_sop="shopify.luteos.com 5岗Agent一键DRAFT流水线与360脚本预算门禁",
         owner="刘华丽", due_date="2026-11-21"),
    dict(project_slug="vicky", expert_name="Vicky", wave="Wave 2",
         topic="PR专员查询吸奶器/温奶器品线S级权威媒体编辑匹配与舆情派单", weekly_ask_count=8, reject_count=2, rework_rate_pct=25,
         current_stage="Stage 2", target_workbench_sop="pr.luteos.com 品线×权威编辑推荐引擎与 Pitching Calendar",
         owner="吴雨宁", due_date="2026-11-27"),
    dict(project_slug="clone", expert_name="Clone", wave="Wave 2",
         topic="编导发TikTok参考视频链接要求拆解S1-S5分镜脚本与二创授权核验", weekly_ask_count=7, reject_count=3, rework_rate_pct=24,
         current_stage="Stage 2", target_workbench_sop="video.luteos.com S1-S5 场景分镜配方与 PendingReview 签发台",
         owner="周健", due_date="2026-11-28"),
    dict(project_slug="market", expert_name="Market", wave="Wave 2",
         topic="选品会查询新品三层TAM容量、7国法规准入与渠道边际ROAS测算", weekly_ask_count=8, reject_count=1, rework_rate_pct=20,
         current_stage="Stage 2", target_workbench_sop="mkt.luteos.com 新品 Go/No-Go 准入决策合同与止血/造血看板",
         owner="周健", due_date="2026-11-29"),
    dict(project_slug="radar", expert_name="Radar", wave="Wave 3",
         topic="达人BD查询候选IP四维分层背调、报价区间与二创投流授权七元组", weekly_ask_count=4, reject_count=1, rework_rate_pct=35,
         current_stage="Stage 1", target_workbench_sop="magpie.luteos.com Wave-1 达人背调台账与寄样/授权到期监控",
         owner="吴雨宁", due_date="2026-12-05"),
    dict(project_slug="signal", expert_name="Signal", wave="Wave 3",
         topic="品牌分析追问声量突变是真实舆情危机还是搜索噪音(query_noise)", weekly_ask_count=5, reject_count=2, rework_rate_pct=30,
         current_stage="Stage 1", target_workbench_sop="signal.luteos.com 加权SOV净情感同报看板与 9,470 竞品雷达",
         owner="周健", due_date="2026-12-12"),
    dict(project_slug="daisy", expert_name="Daisy", wave="Wave 3",
         topic="跨部门复杂经营问题路由分发与书籍/SOP自动蒸馏为可执行Skill", weekly_ask_count=11, reject_count=2, rework_rate_pct=18,
         current_stage="Stage 3", target_workbench_sop="mas/skills.luteos.com Lane B 交互蒸馏 + Know 三道门禁流水线",
         owner="吴雨宁", due_date="2026-12-20"),
    dict(project_slug="geo", expert_name="GEO", wave="Wave 3",
         topic="内容组查询核心ASIN在Perplexity/Rufus未获Best Overall的缺口问句", weekly_ask_count=4, reject_count=1, rework_rate_pct=35,
         current_stage="Stage 1", target_workbench_sop="geo.luteos.com 20问/ASIN 标准探针与 315 SKU 权威内容生成",
         owner="刘华丽", due_date="2026-12-26"),
]

BUSINESS_ACTIONS = [
    dict(project_slug="echo", expert_name="Echo", action_type="认领痛点卡",
         action_title="认领 Reddit 晨报检出的 M5 穿戴吸奶器马达噪音与法兰贴合痛点卡，转入改款与 FAQ 话术",
         dept_actor="品牌市场部 · 产品与客服组", receipt_ref="voc-v64-spu-m5#0012",
         outcome_metric="已关联 SPU 词典并更新 DTC 客服应答 SOP", status="已回写"),
    dict(project_slug="shouheng", expert_name="守衡", action_type="完成合规整改",
         action_title="拦截并修复 5 款母婴商品详情页中的无证据医疗级与绝对化杀菌率宣称（84条FDA/FTC规则命中）",
         dept_actor="品牌市场部 · 合规与独立站组", receipt_ref="ca-rule-fda-0039#C-0005",
         outcome_metric="5 款违规 Listing 草稿已完成合规替换并签发 PASS 回执", status="已回写"),
    dict(project_slug="shopify", expert_name="Shopify", action_type="批准Listing草稿",
         action_title="采纳 360 审计定位的 KOL M5 落地页 JS 减载方案与 Klaviyo 3 封弃单追回战单",
         dept_actor="品牌市场部 · DTC 独立站运营", receipt_ref="shopify-360-p3#A-0008",
         outcome_metric="已进入 P3 执行队列（目标月挽回弃单 $13k–$27k）", status="已回写"),
    dict(project_slug="emily", expert_name="Emily", action_type="采纳投放脚本",
         action_title="采纳 Emily 基于 Brand Token (88分) 与周五社媒周报生成的 TikTok 素人爆款复刻脚本",
         dept_actor="品牌市场部 · 社媒内容组", receipt_ref="emily-scr-tiktok#S-0019",
         outcome_metric="9月实测 TikTok 涨粉 58,766（完成率 106.8%，单粉成本 $1.44）", status="已回写"),
    dict(project_slug="vicky", expert_name="Vicky", action_type="认领公关工单",
         action_title="认领北美母婴核心媒体榜单攻关任务，将 100 条 S 级权威报道同步注入 GEO 事实库",
         dept_actor="品牌市场部 · 北美 PR 媒介组", receipt_ref="vicky-pr-s100#M-0005",
         outcome_metric="吸奶器核心榜单 12 家目标权威媒体已成功进榜 5 家", status="已回写"),
    dict(project_slug="market", expert_name="Market", action_type="采纳预算与止血清单",
         action_title="采纳 DataPilot 识别的清洗机第二增长曲线（配件比 26.8%）与 764 个亏损长尾 SKU 分批下架清单",
         dept_actor="品牌市场部 · 品类策略与投放组", receipt_ref="mkt-datapilot-zx1#B-0003",
         outcome_metric="锁定年化 87M CNY 止血空间与 T0 渠道边际 ROAS 基线", status="已回写"),
]


def _ensure_v3_columns() -> None:
    """兼容已有 PostgreSQL 表，自动补齐新增的排期、甘特图与验收证据列。"""
    from sqlalchemy import text

    alter_stmts = [
        "ALTER TABLE capability_item ADD COLUMN IF NOT EXISTS progress_pct INTEGER DEFAULT 0",
        "ALTER TABLE capability_item ADD COLUMN IF NOT EXISTS start_date VARCHAR DEFAULT ''",
        "ALTER TABLE capability_item ADD COLUMN IF NOT EXISTS end_date VARCHAR DEFAULT ''",
        "ALTER TABLE capability_item ADD COLUMN IF NOT EXISTS owner VARCHAR DEFAULT ''",
        "ALTER TABLE capability_item ADD COLUMN IF NOT EXISTS is_milestone BOOLEAN DEFAULT FALSE",
        "ALTER TABLE capability_item ADD COLUMN IF NOT EXISTS evidence_url VARCHAR DEFAULT ''",
    ]
    with engine.begin() as conn:
        for stmt in alter_stmts:
            try:
                conn.execute(text(stmt))
            except Exception:
                pass


def backfill_evidence_urls(s: Session) -> int:
    """为所有 verify_state=='已验证' 但尚未挂载 evidence_url 的能力自动绑定对应项目的实测报告或工作台 URL。"""
    projs = {p.slug: p for p in s.exec(select(ProductProject)).all()}
    caps = s.exec(select(CapabilityItem)).all()
    filled = 0
    for c in caps:
        if c.verify_state == "已验证" and not (c.evidence_url or "").strip():
            p = projs.get(c.project_slug)
            if not p:
                continue
            first_rep = ""
            for line in (p.report_links or "").splitlines():
                if "|" in line:
                    first_rep = line.split("|", 1)[1].strip()
                    break
            c.evidence_url = first_rep or c.integration_url or p.workbench_url or ""
            if c.evidence_url:
                s.add(c)
                filled += 1
    if filled:
        s.commit()
    return filled


def sync_enriched_content(s: Session) -> dict:
    """将 V8 四阶真实进度标尺（25/50/75/100%）、14独立飞书Bot Wave 1-3排期与3人铁三角唯一主责制强制同步至现有数据库。"""
    proj_map = {p.slug: p for p in s.exec(select(ProductProject)).all()}
    updated_projs = 0
    for p_def in PROJECTS:
        p_obj = proj_map.get(p_def["slug"])
        if not p_obj:
            continue
        p_obj.status_summary = p_def["status_summary"]
        p_obj.owner = p_def["owner"]
        p_obj.verified_summary = p_def["verified_summary"]
        p_obj.metrics_highlights = p_def["metrics_highlights"]
        p_obj.pending_gaps = p_def["pending_gaps"]
        p_obj.extra_sites = p_def["extra_sites"]
        p_obj.support_notes = p_def["support_notes"]
        p_obj.updated_at = datetime.now(timezone.utc)
        s.add(p_obj)
        updated_projs += 1

    all_caps = s.exec(select(CapabilityItem)).all()
    cap_by_key = {(c.project_slug, c.name.strip()): c for c in all_caps}
    updated_caps = 0
    for c_def in CAPABILITIES:
        key = (c_def["project_slug"], c_def["name"].strip())
        c_obj = cap_by_key.get(key)
        if not c_obj:
            continue
        c_obj.description = c_def["description"]
        c_obj.is_milestone = bool(c_def.get("is_milestone", c_obj.is_milestone))
        c_obj.owner = c_def["owner"]
        # 严格对齐四阶真实进度标尺（挤干未接通飞书双向回调与自进化SOP的水分）
        c_obj.progress_pct = c_def["progress_pct"]
        c_obj.status = c_def["status"]
        c_obj.verify_state = c_def["verify_state"]
        c_obj.start_date = c_def["start_date"]
        c_obj.end_date = c_def["end_date"]
        s.add(c_obj)
        updated_caps += 1

    s.commit()
    backfill_evidence_urls(s)

    # 同步 P0-1 高频问题自进化候选池与 P0-3 业务动作回写账本初始种子
    existing_sops = {x.project_slug: x for x in s.exec(select(SopEvolutionCandidate)).all()}
    for sc in SOP_CANDIDATES:
        obj = existing_sops.get(sc["project_slug"])
        if obj:
            obj.wave = sc["wave"]
            obj.topic = sc["topic"]
            obj.current_stage = sc["current_stage"]
            obj.target_workbench_sop = sc["target_workbench_sop"]
            obj.owner = sc["owner"]
            obj.due_date = sc["due_date"]
            if sc["weekly_ask_count"] > obj.weekly_ask_count:
                obj.weekly_ask_count = sc["weekly_ask_count"]
            s.add(obj)
        else:
            s.add(SopEvolutionCandidate(**sc))

    if not s.exec(select(BusinessActionLedger)).all():
        for ba in BUSINESS_ACTIONS:
            s.add(BusinessActionLedger(**ba))

    s.commit()
    try:
        from .gate_engine import seed_initial_gate_receipts

        seed_initial_gate_receipts(s)
    except Exception:
        pass
    return {"updated_projects": updated_projs, "updated_capabilities": updated_caps}


def seed(force_reset: bool = True) -> None:
    """初始化或重置为 V8 完整数据（含四阶真实进度标尺、Wave 1-3 甘特排期与 3 人唯一主责制）。"""
    SQLModel.metadata.create_all(engine)
    _ensure_v3_columns()
    with Session(engine) as s:
        existing = s.exec(select(CapabilityItem)).all()
        has_schedule = any(getattr(c, "start_date", "") for c in existing)
        if existing and has_schedule and not force_reset:
            print(f"[seed] 已存在 {len(existing)} 项能力数据，同步 V8 四阶真实进度标尺与岗位分工")
            sync_enriched_content(s)
            return

        for row in s.exec(select(CapabilityItem)).all():
            s.delete(row)
        for row in s.exec(select(ProductProject)).all():
            s.delete(row)
        for row in s.exec(select(StrategyGroup)).all():
            s.delete(row)
        for row in s.exec(select(GoalGroup)).all():
            s.delete(row)
        s.commit()

        for g in GOALS:
            s.add(GoalGroup(**g))
        for st in STRATEGIES:
            s.add(StrategyGroup(**st))
        for p in PROJECTS:
            s.add(ProductProject(**p, updated_at=datetime.now(timezone.utc)))
        for c in CAPABILITIES:
            s.add(CapabilityItem(**c))

        s.commit()
        sync_enriched_content(s)
        print(
            f"[seed] V8 写入完成：{len(GOALS)} 个目标(G)、{len(STRATEGIES)} 条策略(S)、"
            f"{len(PROJECTS)} 个产品项目、{len(CAPABILITIES)} 项能力点"
        )


def migrate() -> None:
    seed(force_reset=False)


if __name__ == "__main__":
    seed(force_reset=True)
