"""ABI 品牌 & 营销 Agent 多项目管理网站 —— 初始数据（严格对齐附件1思维导图 + /reports 实测成果）。

文案规范（执行附件2）：
- 格赖斯准则：数字带出处，缺数据直接写「方案中」或留空，不编造
- ste-zh 规范：已完成（代码交付）与已验证（实测跑通）分开表述
- lieflat 去 AI 味：禁用「不是A而是B」、禁用「赋能/抓手/闭环/心智/沉淀」、不写宣告式冒号开头
"""
from datetime import datetime, timezone

from sqlmodel import Session, SQLModel, select

from .db import engine
from .models import CapabilityItem, GoalGroup, ProductProject, StrategyGroup

OBJECTIVE_TEXT = "【O】以品牌 Agent 全链路自动化，让声量有增长、口碑有防线、人效有提升。"

GOALS = [
    dict(
        code="G1",
        title="【G1】加速品牌多渠道声量增长",
        subtitle="覆盖社媒趋势、爆款脚本、公关媒体、AI 搜索可见度与 IP 名人合作，共 5 个产品项目",
        sort=1,
    ),
    dict(
        code="G2",
        title="【G2】敏捷响应品牌声量所带来的影响和机会",
        subtitle="覆盖消费者声音（VOC）、市场选品洞察、70 平台统一数据采集与全网声量异动监控，共 4 个产品项目",
        sort=2,
    ),
    dict(
        code="G3",
        title="【G3】推进品牌数据资产AI数字化运营",
        subtitle="覆盖内容合规审查、多智能体统一门户、全栈研发评测、独立站智能运营与 OGSM 项目管理，共 5 个产品项目",
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
        status_summary="已上线",
        owner="社媒组",
        verified_summary=(
            "飞书群智能体与 Web 工作台（14 个路由页面）已上线运行。系统注册了 41 项社媒能力，其中 28 项已上线实测、8 项受限运行、5 项待开发。"
            "已打通 TikTok、Instagram、YouTube、Reddit 热门趋势抓取，支持 TikTok 视频画面/转写/总结四维解析，以及评论区 5 档情绪与主题拆解。"
            "每周五早 9:30 自动向交付群推送 6 维度社媒周报；飞书社媒 Base 的 4 张表（888 条记录）已做行级实时镜像。"
        ),
        metrics_highlights=(
            "已上线能力|28 / 41 项|Emily 报告 10-31\n"
            "飞书 Base 镜像|4 表 888 行|社媒 Base 报告 10-31\n"
            "自动化定时作业|34 个|launchd 实测\n"
            "测试与决策档案|270 测试 / 126 ADR|仓库实测"
        ),
        pending_gaps=(
            "TikTok 达人库筛选、KOL 报价区间、品牌官号互动统计等 5 项能力尚未开发\n"
            "社媒飞书 Base 已有指标公式，但缺少分月目标值与各平台统一的互动率口径\n"
            "内容策略生成与批量投放脚本生成仍在开发中"
        ),
        report_links=(
            "Emily 项目成果总结 (10-31)|/reports-view/Emily/Emily-项目成果总结-20261031.html\n"
            "全球社媒 Base OGSM 分析报告|/reports-view/Emily/OGSM分析报告_社媒Base.html"
        ),
        extra_sites="",
        support_notes=(
            "与 Clone 配合分工：Emily 负责定选题方向、受众人群与核心卖点；Clone 负责把爆款视频拆成可拍的分镜脚本。\n"
            "9 月社媒实测参考：TikTok 涨粉 58,766（完成率 106.8%，单粉成本 $1.44）；Facebook 涨粉 25,390（完成率 126.3%）；Instagram 涨粉 14,709（完成率 86.5%）。"
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
        owner="内容制作组",
        verified_summary=(
            "工作台站点（video.luteos.com）已上线。核心复刻引擎（对应 Main 报告中的 Recipe Agent）已完成开发与单案验证："
            "输入一条 TikTok 爆款视频，自动拆出开头钩子、画面节拍、口播词、字幕公式和音乐版权说明，重绑到目标品牌生成可拍摄脚本，供编导和摄影师直接执行。"
            "内置 15 条确定性校验规则与预算双保险机制。"
        ),
        metrics_highlights=(
            "评测案例通过|13 / 14 案例|Main 报告 11-01\n"
            "单案修复验证|已通过 ($0.43)|10-30 复验记录\n"
            "确定性规则|15 条|packages/evals\n"
            "预置种子品牌|4 个|SQLite 实测"
        ),
        pending_gaps=(
            "14 个评测案例的全量基线重跑尚未执行，当前基线快照还停留在 10-30 旧版本\n"
            "思维导图中 Clone 下的细分能力项尚未单独拆行，目前与 Emily 共用脚本生成链路"
        ),
        report_links=(
            "Main & Recipe Agent 成果总结 (11-01)|/reports-view/Main/Main-项目成果总结-20261101.html"
        ),
        extra_sites="",
        support_notes=(
            "执行边界：系统产出拍摄配方（Recipe），由人工编导审阅、摄影师实拍。二创或跨账号使用达人原片前，需先核对达人授权范围与有效期。"
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
        status_summary="已上线",
        owner="公关组",
        verified_summary=(
            "工作台（pr.luteos.com）已上线。飞书「品牌 PR All-in-One」业务库的 7 张表（666 条记录）已接入每日自动重算（早 9:50 定时跑），"
            "其中媒体资源库（246 家）与上线报道表（347 条）已和 Vicky 工作台双向同步。"
            "2026 年已收录 347 条报道，自然报道（Earned）267 条占 77.2%，S 级权威报道 100 条；吸奶器核心榜单 12 家目标媒体已进榜 5 家。"
        ),
        metrics_highlights=(
            "上线报道总数|347 条 (Earned 77%)|Vicky 报告 10-31\n"
            "媒体资源库|246 家 (激活 31%)|跨表匹配实测\n"
            "S 级权威报道|100 条 (19 家媒体)|Tracker 实测\n"
            "Vicky 能力承接度|56% (核心表 70%)|7表×16能力矩阵"
        ),
        pending_gaps=(
            "上线报道表的「品线」字段 347 条全部为空（覆盖率 0%），无法按产品线统计 PR 贡献\n"
            "缺少战役排期日历（Pitching Calendar）功能，23 条排期里有 12 条未填具体产品\n"
            "付费媒体合作表目前是空表（0 条记录），39 条付费报道无成本与 ROI 记录"
        ),
        report_links=(
            "Vicky 项目成果总结 (10-31)|/reports-view/Vicky/Vicky-项目成果总结-20261031.html\n"
            "品牌 PR 七表 × 16 能力 GAP 分析主报告|/reports-view/Vicky/主报告_GAP矩阵版_品牌PR_All-in-One分析.html\n"
            "Momcozy 北美 PR OGSM 战略分析副报告|/reports-view/Vicky/副报告_OGSM战略版_Momcozy北美PR分析.html"
        ),
        extra_sites="",
        support_notes=(
            "30/60/90 天补齐重点：先给媒体库加上统一编号（解决 100 条报道关联不上媒体库的问题），再补齐报道表的产品品线字段与付费合作成本记录。"
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
        status_summary="方案中",
        owner="搜索与内容组",
        verified_summary=(
            "工作台站点（geo.luteos.com）已部署在线。项目按 6 步流程规划：建立品牌标准问句库、用探针真实采集 ChatGPT/Perplexity/Google AI Overview/Amazon Rufus 的回答快照、"
            "解析品牌提及率与排位、找出可见度缺口、生成权威事实内容、定期复测产出月报。目前 6 个功能模块均在方案设计阶段，排期 11–12 月交付。"
        ),
        metrics_highlights=(
            "工作台站点|200 在线|geo.luteos.com\n"
            "规划功能模块|6 项 (全部方案中)|OGSM 骨架定义\n"
            "计划交付周期|2026 年 11–12 月|排期表记录"
        ),
        pending_gaps=(
            "采集探针与问句库尚未落库运行，暂无各 AI 引擎的品牌提及率实测基线\n"
            "需新增 Amazon Rufus 与 TikTok 站内 AI 搜索问答的专项问句集"
        ),
        report_links="",
        extra_sites="",
        support_notes=(
            "核心价值在于测量与复测：固定每个核心品类 20 个真实购买问题，每月对比 AI 回答里有没有推荐我们、引用的事实准不准。内容生产可复用 Emily 与 Vicky 的权威报道。"
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
        status_summary="方案中",
        owner="达人与IP组",
        verified_summary=(
            "工作台站点（magpie.luteos.com）已部署在线。围绕 IP 与名人合作规划了 3 项核心能力："
            "分析 IP 粉丝结构与声量制定合作计划、跨平台追踪 IP 动态并聚类关键事件、识别合作机会信号并给出推荐理由。目前处于方案设计阶段。"
        ),
        metrics_highlights=(
            "工作台站点|200 在线|magpie.luteos.com\n"
            "规划能力项|3 项 (全部方案中)|OGSM 骨架定义"
        ),
        pending_gaps=(
            "缺少跨平台统一的达人/IP 档案表与视频二次剪辑、广告投流授权到期台账\n"
            "寄样回收率与合作结案复盘数据尚未接入系统"
        ),
        report_links="",
        extra_sites="",
        support_notes=(
            "后续推进时建议明确区分两类合作：一类是高预算的 IP/名人联名（重品牌形象与排他期），另一类是带货达人日常寄样分销（重出片率与授权合规）。"
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
        status_summary="已上线",
        owner="VOC 与洞察组",
        verified_summary=(
            "主工作台（radar.luteos.com）及品类洞察平台（business.luteos.com）、品类报告站（report.luteos.com）均已上线。"
            "Reddit 消费者之声（VOC）日报流水线已连续 2 天无人值守全绿运行（每日早 7:05 自动执行采集、LLM 分析、衍生重算、代际发布、飞书推送共 10 个步骤，全程 11.1 分钟）。"
            "累计沉淀 26,154 条帖子、102,182 条评论；重算性能从优化前的 22 分钟（1,324 秒）压缩到 10.29 秒（提速 86 倍）；每日自动产出内容选题、研发痛点线索和竞品对比。"
        ),
        metrics_highlights=(
            "Reddit 语料库|26,154 帖 / 102,182 评|Echo 报告 11-02\n"
            "无人值守日更|10 步全绿 (11.1 分钟)|连续 2/14 天实测\n"
            "重算耗时优化|1,324s → 10.29s (86×)|生产实测\n"
            "单日洞察产出|18 选题 / 7 研发 / 12 竞品|11-02 晨报回执"
        ),
        pending_gaps=(
            "帖子自动绑定到具体产品型号（SPU）的覆盖率还很低（今日新增 56 帖中仅绑上 2 帖）\n"
            "每日 3 次的新鲜度定时监控有构建回执缺失告警（exit 2），需补齐回执文件\n"
            "V2.0 规划的 105 张工票目前已落地 7 张，拖拽式多维分析与自动化品类报告仍在开发中"
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
            "Echo 的核心产出是统一的用户痛点与反对意见分类表（Taxonomy）。后续客服工单（售后退货原因）和社媒评论统一挂到这套分类上，就能避免各部门各算各的账。"
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
        owner="市场与选品组",
        verified_summary=(
            "市场洞察工作台（mkt.luteos.com）已上线。与之配套的 Sage 跨境电商专家桌面端已完成 D20–D30 共 11 个批次的交付："
            "建成四大跨境电商确定性核算合规引擎（不靠大模型估算财务数字）与 53 位跨境专家专属交付物工作流，通过 284 个测试文件、3,088 项用例验证。"
        ),
        metrics_highlights=(
            "工作台站点|200 在线|mkt.luteos.com\n"
            "跨境专家工作流|53 位专家已落地|Sage 报告 11-02\n"
            "确定性核算引擎|4 大引擎已验证|提交 ad8a205b\n"
            "自动化测试基线|3,088 通过 / 51 门禁全过|Sage 实测"
        ),
        pending_gaps=(
            "思维导图中 Market 节点下尚未展开具体子能力行，需将 Echo 侧的「品类洞察平台（business.luteos.com）」与「品类洞察报告（report.luteos.com）」正式并入联动\n"
            "选品结论卡片需要明确下游接收方（产品开发与合规团队），建立新品上市后的动销跟踪"
        ),
        report_links=(
            "Sage 项目成果总结 (11-02)|/reports-view/Sage/Sage-项目成果总结-20261102.html"
        ),
        extra_sites="",
        support_notes=(
            "定位说明：Market 聚焦新品立项前的市场容量、价格带与竞品格局判断；日常消费者原声监控由 Echo 负责。"
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
        status_summary="已上线",
        owner="数据底座组",
        verified_summary=(
            "多平台数据采集工作台（Data Intelligence Hub，scrapy.luteos.com）双生产环境在线，是支撑 GEO、Vicky、Echo、Signal、Emily、Radar 六个项目的上游数据底座。"
            "目前已覆盖 70 个平台、284 个唯一采集端点（其中 200 个已实测跑通并返回真实数据，57 个待配账号凭据，12 个受上游限制）；"
            "注册了 39 个 MCP 工具，拥有 55 个前端页面路由（控制台 26 页 + 洞察应用 29 页），飞书「数说」机器人已通过生产验收。"
        ),
        metrics_highlights=(
            "覆盖平台与端点|70 平台 / 284 端点 (200 已实测)|Source 报告 10-31\n"
            "注册 MCP 工具|39 个|生产代码实测\n"
            "前端页面路由|55 页 (控制台26+洞察29)|仓库清点\n"
            "测试与工程规模|2,807 测试 / 928 提交|CI 7 job 全绿"
        ),
        pending_gaps=(
            "VOC 自动报告管线前 6 步（G0–G6）已跑通，最后一步 G7 发布仍阻塞\n"
            "ABI 数据中心已手工推送 17 张表（1.2 GB、72.6 万行），但 48 张表的 abi schema 与生产看板尚未正式部署\n"
            "57 个受凭据限制的采集端点需按业务优先级逐步补齐账号配置"
        ),
        report_links=(
            "Source 项目成果总结 (10-31)|/reports-view/Source/Source-项目成果总结-20261031.html"
        ),
        extra_sites="",
        support_notes=(
            "作为全链路底座，Source 下一步最关键的协同任务是统一「产品 SKU 编号」与「平台内容唯一 ID」，避免下游 6 个 Agent 各自重复抓取和清洗。"
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
        status_summary="方案中",
        owner="品牌分析组",
        verified_summary=(
            "品牌声量工作台（signal.luteos.com）已部署在线。规划了 3 项核心能力：监控品牌曝光与搜索热度日趋势、"
            "识别声量异常波动并分析原因、追踪竞品动作与新品发布节奏。上游数据由 Source 采集底座提供，目前 3 项能力均在方案设计阶段。"
        ),
        metrics_highlights=(
            "工作台站点|200 在线|signal.luteos.com\n"
            "规划能力项|3 项 (全部方案中)|OGSM 骨架定义"
        ),
        pending_gaps=(
            "需建立跨渠道统一的事件去重规则，避免同一条 Reddit 差评或媒体报道在 Echo、Vicky、Signal 三个群里重复发告警\n"
            "需接入 Google Search Console 与 Amazon 品牌词搜索量数据，建立品牌声量（SOV）计算基线"
        ),
        report_links="",
        extra_sites="",
        support_notes=(
            "分工边界：Signal 负责算清全网品牌声量份额（SOV）、搜索热度趋势和突发异动告警；具体媒体的公关跟进交由 Vicky，产品缺陷原声拆解交由 Echo。"
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
        status_summary="已上线",
        owner="内容合规组",
        verified_summary=(
            "内容合规审查工作台（ca.luteos.com，14 个页面覆盖队列、案件、申诉、放行、下线、名单、报告）已上线生产，全面启用飞书扫码登录。"
            "「词表命中 + 语境守卫」两段式判定引擎已完成 227 项契约自证（PASS / REVIEW / BLOCK 三级处置）；"
            "规则词典（36 条）、控制点（24 条）、路由（24 条）已冻结投产；11-01 刚完成图片/视频签发指纹、上传接口、待放行队列（25 条）等 8 项生产修复。"
        ),
        metrics_highlights=(
            "引擎契约自证|227 / 227 通过|守衡报告 11-01\n"
            "自证检查器|141 个 (验收 127 通过)|仓库实测\n"
            "上线规则与控制点|36 规则 / 24 控制点|生产投影实测\n"
            "Web 审核工作台|14 个功能页在线|ca.luteos.com"
        ),
        pending_gaps=(
            "视频模态目前尚未接入语音转文字（ASR）与音画对齐，系统如实标为「未审查（DP0）」而不假装通过，正在按 T-430~T-435 顺序推进补齐\n"
            "守衡飞书机器人于 10-26 按委托方要求暂停运行，待指令恢复"
        ),
        report_links=(
            "守衡 内容合规审查成果总结 (11-01)|/reports-view/守衡/守衡-项目成果总结-20261101.html"
        ),
        extra_sites="",
        support_notes=(
            "核心原则：Agent 只负责找出风险依据与违规位置，最终放行签字权在人工审核员手上。Shopify 侧整理的 84 条母婴 FDA/FTC 合规规则后续可并入守衡统一管理。"
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
        owner="平台与知识工程组",
        verified_summary=(
            "多智能体门户（mas.luteos.com）及关联的品牌知识库平台（asset.luteos.com）、业务平台（brand.luteos.com）、技能平台（skills.luteos.com）4 个站点全部在线。"
            "配套的 Know（any2skills）知识转化管线已走通两本完整专业书的全链路验证：把书籍/SOP 自动转成带逐字引文出处的 Agent 技能，"
            "建成契约验证、280 次触发盲测、A/B 效用实测三道门禁（曾主动检出并下架 2 个负向技能），已产出 17 个可用技能和 1,089 条知识对象。"
        ),
        metrics_highlights=(
            "在线平台矩阵|4 个站点全部 200 在线|实测验证\n"
            "已投产任务技能|17 个 (273 处原文引用)|Know 报告 10-31\n"
            "结构化知识对象|1,089 条 (带逐字引文)|any2skills 实测\n"
            "质量门禁与测试|3 道门禁 / 577 测试 0 失败|仓库实测"
        ),
        pending_gaps=(
            "把部门 9 个专家 Agent 通过统一适配层收拢到一个入口的方案仍在设计中\n"
            "对话式 CLI 标准交互界面正在开发中"
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
            "Daisy 承担两个核心角色：一是把散落在各处的品牌卖点、检测报告、SOP 文档收拢成可溯源的知识库与技能包；二是作为多智能体的统一调度入口。"
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
        owner="全栈研发组",
        verified_summary=(
            "全栈开发工作台（main.luteos.com）与模型选型评测站（llm.luteos.com）均已上线，飞书机器人（v1.0.5）保持长连接在线。"
            "确立了「shared ← core ← apps」单向依赖架构与 10 篇核心 ADR 规范；"
            "Main Agent 的 150 个真实问答评测案例 100% 通过（评分均值 0.99），全仓 264 个单元与集成测试全部跑通，并交付了 Lody × Magpie × Nowledge Mem 全栈工具链一页纸。"
        ),
        metrics_highlights=(
            "Main 问答评测|150 / 150 通过 (均分 0.99)|Main 报告 11-01\n"
            "单元与集成测试|264 个全部通过|pnpm test 实测\n"
            "架构决策档案|10 篇 ADR (0001–0010)|docs/adr\n"
            "真实模型评测花费|$5.63|evals/runs 账本"
        ),
        pending_gaps=(
            "需协助各业务 Agent 团队统一接入评测门禁（Eval Harness）与发布前自检脚本"
        ),
        report_links=(
            "Main 项目成果总结 (11-01)|/reports-view/Main/Main-项目成果总结-20261101.html"
        ),
        extra_sites=(
            "模型选型与评测平台|https://llm.luteos.com/|online"
        ),
        support_notes=(
            "Main 是部门的研发生产力底座，提供统一的 Agent SDK 运行时、模型成本预算控制、失败重试契约与真实模型评测框架。"
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
        status_summary="已上线",
        owner="独立站智能组",
        verified_summary=(
            "独立站 360 审计站（shopify.luteos.com）、知识站（platform-shopify.luteos.com）与 AI 选品站（product.luteos.com）均已上线。"
            "建成覆盖选品、建站、上架、CRO、归因、履约等 14 个领域的 178 篇正式文档库（795 个 RAG 检索块，检索评测通过率 100%）。"
            "多智能体控制台已上线 5 个岗位 Agent（Listing 上架、商品结构体检、SEO 审计、重复商品排查、建站就绪度检查），"
            "严格执行「Agent 只生成草稿（DRAFT），人工点击发布」的安全边界；内置 84 条 FDA/FTC/CPSC 母婴合规预检规则，已修复 5 款商品的违规宣称。"
        ),
        metrics_highlights=(
            "独立站知识库|14 领域 / 178 篇 / 795 块|Shopify 报告 11-02\n"
            "已上线岗位 Agent|5 个 (Listing 契约 3/3 通过)|src/mas 实测\n"
            "母婴合规预检规则|84 条 (39 强阻断 + 45 提示)|法条核对 10-30\n"
            "RAG 检索评测门禁|100% 通过 (pass-rate 1.0)|部署硬门禁"
        ),
        pending_gaps=(
            "Listing 上架首岗「连续 2 周返工率 <20% 且日均审批 <15 分钟」的验收统计尚未正式启动\n"
            "前端展示的 Agent 运行数据目前是构建时静态快照，需打通 /mas/* 同域反向代理实现实时刷新\n"
            "袜子类目还有 3 处合规措辞待最终确认"
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
            "注：原思维导图中的 platform.shopify.luteos.com 因二级子域证书限制，线上实际可用地址为 https://platform-shopify.luteos.com/，本平台已自动修正链接。"
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
        owner="PMO 组",
        verified_summary=(
            "即为当前网站（pmo.luteos.com）。严格按照《ABIOGSM-品牌Agent》思维导图构建，"
            "将部门愿景（O）、三大目标（G1–G3）、六条专家融合策略（S1–S6）、14 个产品项目、23 个工作台/子站入口、49 项细分能力进度，以及 /reports 目录下的全部实测成果收拢到同一门户，"
            "支持全景导图浏览、项目卡片管理、原始报告在线查阅、汇报投屏演示与后台状态更新。"
        ),
        metrics_highlights=(
            "纳管产品项目|14 个专家产品|OGSM 思维导图\n"
            "联通线上站点|20 / 23 个在线可达|实时探测\n"
            "细分能力图谱|49 项能力点跟踪|全量入库\n"
            "实测报告归档|9 个专家目录 / 12 份报告|在线直读"
        ),
        pending_gaps=(
            "后续可按周自动拉取各专家仓库生成的最新日报 HTML，实现成果数据的自动刷新"
        ),
        report_links=(
            "部门项目汇报 PPT 执行方案 v2|/docs/PPT汇报方案v2-部门项目汇报.md"
        ),
        extra_sites="",
        support_notes=(
            "管理原则：以产品名称作为独立项目管理单元；文案遵循格赖斯准则与去 AI 味规范，如实区分「代码已完成」与「生产已验证」。"
        ),
        sort=14,
    ),
]

CAPABILITIES = [
    # ─── 1. Emily (4 items) ───
    dict(project_slug="emily", scenario_line="社媒趋势洞察 → 内容策略 → 脚本生成",
         name="爆款/趋势洞察", description="发现社媒爆款与趋势，输出可复刻的内容结构",
         status="已完成", verify_state="已验证", sort=1),
    dict(project_slug="emily", scenario_line="社媒趋势洞察 → 内容策略 → 脚本生成",
         name="互动追踪&评论解析", description="追踪社媒互动并解析粉丝真实反馈（情绪5档+主题×情绪）",
         status="已完成", verify_state="已验证", sort=2),
    dict(project_slug="emily", scenario_line="社媒趋势洞察 → 内容策略 → 脚本生成",
         name="内容策略生成", description="按趋势与品牌定位生成社媒内容策略",
         status="进行中", verify_state="部分验证", sort=3),
    dict(project_slug="emily", scenario_line="社媒趋势洞察 → 内容策略 → 脚本生成",
         name="脚本生成", description="按爆款结构批量生成品牌投放脚本",
         status="进行中", verify_state="部分验证", sort=4),

    # ─── 2. Clone (2 items from Recipe Agent report) ───
    dict(project_slug="clone", scenario_line="爆款视频拆解 → 品牌脚本复刻",
         name="TikTok 爆款视频结构拆解", description="提取开头钩子、画面节拍、口播、字幕公式与音乐版权说明",
         status="已完成", verify_state="已验证", sort=5),
    dict(project_slug="clone", scenario_line="爆款视频拆解 → 品牌脚本复刻",
         name="品牌定制 Recipe 脚本生成", description="将爆款结构重绑到目标品牌，生成编导与摄影可直接执行的脚本（13/14 评测通过）",
         status="进行中", verify_state="已验证", sort=6),

    # ─── 3. Vicky (4 items) ───
    dict(project_slug="vicky", scenario_line="PR 线：竞品监测 → 风险预警 → 工作台协同",
         name="线索管理", description="PR 媒体&编辑线索管理（246 家媒体库与 347 条报道双向同步）",
         status="已完成", verify_state="已验证", sort=7),
    dict(project_slug="vicky", scenario_line="PR 线：竞品监测 → 风险预警 → 工作台协同",
         name="线索推荐", description="行业话题推荐、编辑匹配",
         status="已完成", verify_state="已验证", sort=8),
    dict(project_slug="vicky", scenario_line="舆情线：看板对话化 → 自动分类 → 工单闭环",
         name="舆情预警", description="品牌舆情监控与预警分发",
         status="已完成", verify_state="已验证", sort=9),
    dict(project_slug="vicky", scenario_line="舆情线：看板对话化 → 自动分类 → 工单闭环",
         name="数据查询与分析", description="舆情、核心媒体&编辑查询与分析（每日 09:50 自动重算）",
         status="已完成", verify_state="已验证", sort=10),

    # ─── 4. GEO (6 items) ───
    dict(project_slug="geo", scenario_line="问句库 → 采集探针 → 解析与指标 → 诊断洞察 → 内容生成 → 复测报告",
         name="配置与问句库", description="建立品牌问句库并版本化管理",
         status="方案中", verify_state="待验证", sort=11),
    dict(project_slug="geo", scenario_line="问句库 → 采集探针 → 解析与指标 → 诊断洞察 → 内容生成 → 复测报告",
         name="采集探针", description="真实采集 AI 引擎回答并留存快照",
         status="方案中", verify_state="待验证", sort=12),
    dict(project_slug="geo", scenario_line="问句库 → 采集探针 → 解析与指标 → 诊断洞察 → 内容生成 → 复测报告",
         name="解析与指标", description="解析品牌提及与排位，算出五项可见度指标",
         status="方案中", verify_state="待验证", sort=13),
    dict(project_slug="geo", scenario_line="问句库 → 采集探针 → 解析与指标 → 诊断洞察 → 内容生成 → 复测报告",
         name="诊断洞察", description="定位可见度缺口并排出优先攻占主题",
         status="方案中", verify_state="待验证", sort=14),
    dict(project_slug="geo", scenario_line="问句库 → 采集探针 → 解析与指标 → 诊断洞察 → 内容生成 → 复测报告",
         name="内容生成", description="基于事实库生成可被 AI 引用的权威内容",
         status="方案中", verify_state="待验证", sort=15),
    dict(project_slug="geo", scenario_line="问句库 → 采集探针 → 解析与指标 → 诊断洞察 → 内容生成 → 复测报告",
         name="复测与报告", description="复测效果并产出可交付月报",
         status="方案中", verify_state="待验证", sort=16),

    # ─── 5. Radar (3 items) ───
    dict(project_slug="radar", scenario_line="粉丝分析 → 合作计划 → 动态监测 → 机会推荐",
         name="IP 合作计划制定", description="分析 IP 粉丝结构与声量，输出合作计划",
         status="方案中", verify_state="待验证", sort=17),
    dict(project_slug="radar", scenario_line="粉丝分析 → 合作计划 → 动态监测 → 机会推荐",
         name="全渠道动态监测", description="跨平台追踪 IP 动态并聚类关键事件",
         status="方案中", verify_state="待验证", sort=18),
    dict(project_slug="radar", scenario_line="粉丝分析 → 合作计划 → 动态监测 → 机会推荐",
         name="合作机会识别", description="识别合作机会信号并给出推荐理由",
         status="方案中", verify_state="待验证", sort=19),

    # ─── 6. Echo (4 items) ───
    dict(project_slug="echo", scenario_line="舆情线：品牌/品类/SPU舆情预警",
         name="多渠道数据查询", description="售前、售后、独立站、Reddit 等用户反馈（已入库 2.6 万帖 / 10.2 万评）",
         status="已完成", verify_state="已验证",
         integration_name="数据采集插件", integration_url="https://plugin.luteos.com/", sort=20),
    dict(project_slug="echo", scenario_line="舆情线：品牌/品类/SPU舆情预警",
         name="风险指数&机会洞察", description="量化用户风险指数并挖掘产品机会（每日自动生成选题/研发/竞品日报）",
         status="进行中", verify_state="已验证", sort=21),
    dict(project_slug="echo", scenario_line="话题线：高质量内容机会挖掘",
         name="拖拉式多维分析", description="拖拽式多维分析用户声音",
         status="进行中", verify_state="部分验证", sort=22),
    dict(project_slug="echo", scenario_line="产品机会线：品类机会挖掘",
         name="自动化品类洞察报告", description="结合品类洞察平台与报告站自动生成品类机会分析",
         status="进行中", verify_state="已验证",
         integration_name="品类洞察平台 / 品类洞察报告", integration_url="https://business.luteos.com/", sort=23),

    # ─── 7. Market (2 items) ───
    dict(project_slug="market", scenario_line="市场洞察与跨境专家核算",
         name="市场洞察工作台", description="品类容量、价格带与竞品格局分析（mkt.luteos.com）",
         status="进行中", verify_state="已验证", sort=24),
    dict(project_slug="market", scenario_line="市场洞察与跨境专家核算",
         name="跨境电商核算引擎与专家工作流", description="四大确定性核算合规引擎 + 53 位跨境专家交付工作流（Sage 实测通过）",
         status="已完成", verify_state="已验证", sort=25),

    # ─── 8. Source (8 items) ───
    dict(project_slug="source", scenario_line="统一采集平台与 monitor 层 → 分渠道采集器 → 统一表结构 → 采集工具 → 洞察工具",
         name="统一采集平台与 monitor 层", description="统一采集调度、降级链路与多表建模（70 平台 / 284 端点，200 已实测）",
         status="进行中", verify_state="已验证", sort=26),
    dict(project_slug="source", scenario_line="统一采集平台与 monitor 层 → 分渠道采集器 → 统一表结构 → 采集工具 → 洞察工具",
         name="TikTok 采集MCP/skill", description="采集 TikTok 榜单、视频、评论（16 工具 / 21 表已建）",
         status="进行中", verify_state="已验证", sort=27),
    dict(project_slug="source", scenario_line="统一采集平台与 monitor 层 → 分渠道采集器 → 统一表结构 → 采集工具 → 洞察工具",
         name="Reddit 采集MCP/skill", description="采集 Reddit 帖子与评论树",
         status="进行中", verify_state="已验证", sort=28),
    dict(project_slug="source", scenario_line="统一采集平台与 monitor 层 → 分渠道采集器 → 统一表结构 → 采集工具 → 洞察工具",
         name="YouTube 采集MCP/skill", description="采集 YouTube 视频、频道、字幕",
         status="进行中", verify_state="已验证", sort=29),
    dict(project_slug="source", scenario_line="统一采集平台与 monitor 层 → 分渠道采集器 → 统一表结构 → 采集工具 → 洞察工具",
         name="Instagram 采集MCP/skill", description="采集 Instagram 媒体与评论",
         status="进行中", verify_state="已验证", sort=30),
    dict(project_slug="source", scenario_line="统一采集平台与 monitor 层 → 分渠道采集器 → 统一表结构 → 采集工具 → 洞察工具",
         name="Facebook 采集MCP/skill", description="采集 Facebook 页面与互动快照",
         status="进行中", verify_state="已验证", sort=31),
    dict(project_slug="source", scenario_line="统一采集平台与 monitor 层 → 分渠道采集器 → 统一表结构 → 采集工具 → 洞察工具",
         name="Google Trends 采集MCP/skill", description="采集 Google 趋势指数与关联查询",
         status="进行中", verify_state="已验证", sort=32),
    dict(project_slug="source", scenario_line="统一采集平台与 monitor 层 → 分渠道采集器 → 统一表结构 → 采集工具 → 洞察工具",
         name="上游数据底座支撑", description="支撑 GEO、Vicky、Echo、Signal、Emily、Radar 六方数据供给",
         status="进行中", verify_state="部分验证", sort=33),

    # ─── 9. Signal (3 items) ───
    dict(project_slug="signal", scenario_line="多源采集 → 异动检测 → 归因分析 → 告警",
         name="品牌曝光&热度监控", description="监控品牌曝光与搜索热度日趋势",
         status="方案中", verify_state="待验证", sort=34),
    dict(project_slug="signal", scenario_line="多源采集 → 异动检测 → 归因分析 → 告警",
         name="声量异动识别", description="识别声量异常波动并归因",
         status="方案中", verify_state="待验证", sort=35),
    dict(project_slug="signal", scenario_line="多源采集 → 异动检测 → 归因分析 → 告警",
         name="竞品动作&发布监测", description="追踪竞品动作与新品发布节奏",
         status="方案中", verify_state="待验证", sort=36),

    # ─── 10. 守衡 (3 items) ───
    dict(project_slug="shouheng", scenario_line="内容上传 → 模型审核 → 审计判定 → 整改推送",
         name="内容审计规则引擎", description="按品牌规则自动审计内容合规风险（两段式判定，227/227 契约自证通过）",
         status="已完成", verify_state="已验证", sort=37),
    dict(project_slug="shouheng", scenario_line="内容上传 → 模型审核 → 审计判定 → 整改推送",
         name="经营动作与结论复核", description="复核经营结论是否有证据支撑（文档/图片OCR/结构化已跑通，视频待接ASR）",
         status="已完成", verify_state="已验证", sort=38),
    dict(project_slug="shouheng", scenario_line="内容上传 → 模型审核 → 审计判定 → 整改推送",
         name="复核结论与整改清单", description="输出整改清单并推送（14 页 Web 审核工作台在线，支持签发与申诉）",
         status="已完成", verify_state="已验证", sort=39),

    # ─── 11. Daisy (3 items) ───
    dict(project_slug="daisy", scenario_line="知识库 → MAS → CLI",
         name="各 Agent 统一接入", description="九个 Agent 通过适配层统一接入",
         status="方案中", verify_state="待验证", sort=40),
    dict(project_slug="daisy", scenario_line="知识库 → MAS → CLI",
         name="统一入口与品牌知识库", description="把九个 Agent 收成一个入口，沉淀品牌知识资产与 17 个可溯源技能（Know）",
         status="方案中", verify_state="部分验证",
         integration_name="品牌知识库平台 (asset.luteos.com)", integration_url="https://asset.luteos.com/", sort=41),
    dict(project_slug="daisy", scenario_line="知识库 → MAS → CLI",
         name="对话式 CLI 界面", description="提供对话式 CLI 标准交互，联通业务 skills 平台",
         status="进行中", verify_state="已验证",
         integration_name="业务skills平台 (brand / skills)", integration_url="https://skills.luteos.com/", sort=42),

    # ─── 12. Main (2 items) ───
    dict(project_slug="main", scenario_line="全栈研发工作台与模型评测",
         name="全栈开发 Agent 与飞书机器人", description="单向依赖架构 runtime + 飞书长连接机器人（150/150 真实问答评测通过）",
         status="已完成", verify_state="已验证", sort=43),
    dict(project_slug="main", scenario_line="全栈研发工作台与模型评测",
         name="模型选型与评测平台", description="多模型对比评测与成本核算（llm.luteos.com）",
         status="已完成", verify_state="已验证",
         integration_name="模型选型与评测", integration_url="https://llm.luteos.com/", sort=44),

    # ─── 13. Shopify (3 items) ───
    dict(project_slug="shopify", scenario_line="ABI独立站 → 独立站360审计 → AI选品",
         name="ABI 独立站知识平台", description="14 领域 178 篇正式文档与 795 个 RAG 检索块（评测 100% 通过）",
         status="已完成", verify_state="已验证",
         integration_name="ABI独立站", integration_url="https://platform-shopify.luteos.com/", sort=45),
    dict(project_slug="shopify", scenario_line="ABI独立站 → 独立站360审计 → AI选品",
         name="独立站 360 审计与 Listing 上架", description="5 个岗位 Agent（Listing 草稿上架、结构体检、SEO、去重、就绪度）+ 84 条母婴合规预检",
         status="已完成", verify_state="已验证",
         integration_name="独立站360审计", integration_url="https://shopify.luteos.com/", sort=46),
    dict(project_slug="shopify", scenario_line="ABI独立站 → 独立站360审计 → AI选品",
         name="AI 选品平台", description="独立站智能选品辅助工具",
         status="进行中", verify_state="已验证",
         integration_name="AI选品", integration_url="https://product.luteos.com/", sort=47),

    # ─── 14. PMO (2 items) ───
    dict(project_slug="pmo", scenario_line="OGSM 全景导图 → 14 大项目管理 → 汇报演示",
         name="OGSM 全景思维导图与项目矩阵", description="还原附件1思维导图结构，纳管 14 个产品项目、23 个站点入口与 49 项能力进度",
         status="已完成", verify_state="已验证", sort=48),
    dict(project_slug="pmo", scenario_line="OGSM 全景导图 → 14 大项目管理 → 汇报演示",
         name="专家实测成果汇总与汇报模式", description="集成 /reports 全部实测报告，提供去 AI 味的部门汇报投屏视图",
         status="已完成", verify_state="已验证", sort=49),
]


def seed(force_reset: bool = True) -> None:
    """初始化或重置为 V2 思维导图完整数据。"""
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        existing = s.exec(select(ProductProject)).all()
        if existing and not force_reset:
            print(f"[seed] 已存在 {len(existing)} 个产品项目，跳过")
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
        print(
            f"[seed] V2 写入完成：{len(GOALS)} 个目标(G)、{len(STRATEGIES)} 条策略(S)、"
            f"{len(PROJECTS)} 个产品项目、{len(CAPABILITIES)} 项能力点"
        )


def migrate() -> None:
    seed(force_reset=False)


if __name__ == "__main__":
    seed(force_reset=True)
