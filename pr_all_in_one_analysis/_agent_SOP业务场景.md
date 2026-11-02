# Momcozy 北美 PR 核心业务场景与运营 SOP

> 数据范围：飞书多维表格「品牌PR All-in-One」7 张表快照（截至 2026-10-31）。报道 Tracker 覆盖 2026-01 至 2026-10，共 347 条记录、336 条有发布日期。本文从业务视角还原「场景—SOP—节奏—角色」，数字均来自 `_bundle.json` 与 `_profile.json`。

## 0. 数据基线

| 表 | 记录数 | 在业务中的角色 | 关键完整度 |
|---|---:|---|---|
| 媒体资源库 | 246 | 目标媒体主数据与评级 | 评级 96%、GEO 91%、SEO 94%、媒体类别 90%；28 个字段中仅 8 个是有效业务字段，19 个为「字段 N」占位 |
| 媒体报道上线Tracker (2026) | 347 | 已上线 coverage 明细 | 日期 97%、项目 79%、产品 75%、媒体评级 60%、品线 0% |
| Pitching Calendar | 23 | 未来 12 个月 campaign 节奏 | 日期 100%；Key Product 具体率仅 48%（9 条「/」+3 条「TBD」）；无 Owner/Status 字段 |
| Editorial Opportunities | 20 | 选题、Pitch Angle、目标媒体库 | Pitch Angle 70%、Pitch Timing 80%、Media Examples 70%、Key Product 65%；无 Owner/Status 字段 |
| 吸奶器榜单媒体进展跟踪 | 12 | 吸奶器品类榜单渗透 | Editor 联系历史 58%、Agency Notes 33%、Media owner 58% |
| PR资源库 | 18 | PR 文档/资产索引 | Owner 68%、文档类型 63%、附件 79% |
| 付费媒体合作数据 | 0 | 付费合作台账 | 空表，仅 1 个「文本」字段 |

三个全局判断：

1. **声量高度集中于大促与品牌节点。** 2026 年 1-10 月 336 条有日期 coverage 中，10 月 68 条（20%）、6 月 51 条（15%）、9 月 42 条（13%），Top 3 月占 48%；2 月仅 11 条、8 月 16 条，淡旺季差异极大。
2. **Earned 是绝对主力，付费是补位。** 合作类型 Earned 267 条（77%）、Paid 39 条（11%）、Awards 18 条（5%）、Press Release 17 条（5%）、Organic 4 条、调研/白皮书 1 条。
3. **媒体结构「中间大、两头小」。** 媒体资源库 A 级 138 家（57%）、S 级 35 家（14%）、B 级 46 家（19%）、C 级 23 家（9%）；但 2026 年实际 coverage 高度偏向 S/A（S 100 条、A 103 条、B 仅 5 条）。资源库利用率仅 24%（59/246），S 级 57%、A 级 25%、B 级 11%、C 级 0%。

---

## 一、核心业务场景清单

### 1.1 场景总览

| # | 场景 | 业务目的 | 触发时机（来自 Pitching Calendar / Editorial Opportunities） | 驱动表 |
|---|---|---|---|---|
| S1 | 日常 Earned 媒体 Pitch | 维持品牌在母婴/生活方式媒体的常态声量与长尾覆盖 | Always-on，无固定日历条目；2026 年 26 条「日常推广」+73 条未标注项目，实际是最大工作流 | 媒体资源库、报道Tracker、Editorial Opportunities、PR资源库 |
| S2 | 新品上市媒体首发 | 用 editorial 首发/评测建立新品认知与权威背书 | EO 11 条 New Product Launch（55%），窗口 2026-10-12 至 2027-01-10；Calendar 的 M5 Ultra Launch 9/1-10/15、Nursery Recliner 2027/2 | Pitching Calendar、Editorial Opportunities、媒体资源库、报道Tracker、PR资源库 |
| S3 | 电商大促 Deal 投放 | 在大促窗口用 deal/listicle 抢占转化型流量 | 26FPD 59 条（10 月）、Prime Day 42 条（6 月）；Calendar 的 Fall Prime Day 9/1-10/9、BFCM 11/1-11/30；EO 的 Prime Big Deal Days 10/7-8、BFCM 11/19-11/30 | Pitching Calendar、Editorial Opportunities、报道Tracker、媒体资源库 |
| S4 | 品类榜单渗透与奖项 | 进入第三方权威榜单/获奖，形成信任状与 GEO/SEO 资产 | 奖项内容 38 条，7 月 13 条、8 月 8 条项目提及；吸奶器榜单 12 家媒体，W1 pitch 集中在 8 月初（Update 8.01-8.04） | 吸奶器榜单媒体进展跟踪、报道Tracker、媒体资源库、PR资源库 |
| S5 | Editorial 选题 / Cultural Moment 营销 | 借文化、健康、公益议题进入母亲叙事，获取高质量 editorial | EO Cultural 6 条：9 月 Baby Safety、10 月 Breast Cancer/World Mental Health/Rainbow Baby、11/17 Prematurity、2027/2-3 IWD；Pitch Timing 从 Early Aug 到 Late Nov | Editorial Opportunities、Pitching Calendar、报道Tracker、PR资源库 |
| S6 | 品牌事件与线下 Showroom | 制造可报道的新闻点，深化媒体关系与体验 | Calendar：Momcozy x Babylist NYC 9/17-9/28、Try Before You Buy 11/1-11/30、LA Showroom Opening 2027/2/1-2/28；历史 ABC Kids Expo 2026/5 | Pitching Calendar、报道Tracker、媒体资源库、PR资源库 |
| S7 | 品牌 Campaign / 品牌叙事 | 围绕「Mom, and More」建立品牌心智，而非单品卖点 | Brand Day 9/1-9/30（Calendar 11 条 Brand Campaign 中最大一块）；NIQ 报告 9/10、Mom, and More 发布 9/14、600 Hours 7/27；2027/1 吸奶器创新故事、2027/2 IWD/护肤指南 | Pitching Calendar、Editorial Opportunities、报道Tracker、PR资源库 |
| S8 | 付费媒体合作 | 补齐可控曝光、测评与时效 coverage | Paid 39 条（11%），10 月 12、5 月 8、6 月 6、1 月 6；主要跟随大促（26FPD 12、Prime Day 5）与产品评测（Product Introduction/Review 14 条中 9 条为 Paid） | 付费媒体合作数据（空）、报道Tracker、媒体资源库 |
| S9 | PR 资产沉淀与复用 | 把媒体关系、素材、奖项授权、洞察变成可复用资产 | 持续；PR资源库 18 份文档、5 位 Owner；建议 3/6/9/12 月季度盘点 | PR资源库、媒体资源库、报道Tracker、吸奶器榜单 |

### 1.2 场景拆解

**S1 日常 Earned 媒体 Pitch**
- 业务目的：在没有大促/新品节点的月份维持声量，覆盖 evergreen 选题、产品 roundup、buying guide 与长尾媒体。
- 触发时机：Always-on。2026 年「日常推广」26 条，加上 73 条未标注项目的记录，构成实际最大工作流；但 Pitching Calendar 只有 23 条 campaign 级记录，没有承接日常 pitch 的条目。
- 数据信号：Earned 267 条（77%）；Product Roundup/Listicle 59 条（17%）、Buying Guide/Gift Guide 40 条（12%）；150 家媒体中仅 64 家（43%）能精确映射回媒体资源库，说明「Pitch 对象」与「媒体主数据」没有闭环。
- 产品角色：全品类长尾 + hero 产品（BuzzFeed 36 条、Parents 16 条、Good Housekeeping 14 条、The Bump 13 条）。

**S2 新品上市媒体首发**
- 业务目的：用新品首发、独立评测、roundup 收录建立「新品值得买」的第三方认知。
- 触发时机：EO 11 条 New Product Launch（20 条中的 55%），时间窗 2026-10-12 至 2027-01-10；Pitching Calendar 另有 M5 Ultra Launch（9/1-10/15）与 Nursery Recliner Launch（2027/2）。Pitch Timing 集中在 Mid Sep - Early Oct，即上市前 2-4 周。
- 数据信号：2026 年新品相关记录包括 D8（1/4 通稿）、ChangeGo stroller（9 条产品露出）、KleanPal（7 条）、D8（4 条）、Wellness 1（4 条）、RB001（4 条）；新品首发通常伴随 Product Introduction/Product Review（14 条）与 Product Roundup（59 条）。
- 产品角色：M5 Ultra、V3、V3 Pro、M8、BN09、WN08、MW08、CB004、AirMesh Nursing Bra、Multi-functional Light Therapy Device、Nursery Recliners。
- 关键矛盾：EO 中 7 条 New Product Launch 缺 Key Product 或 Pitch Angle；「M5 Ultra Breast Pump」的 Key Product 写成「M8 Breast Pump」，与 Calendar 的「M5 Ultra」冲突。

**S3 电商大促 Deal 投放**
- 业务目的：在大促窗口用 deal 清单、比价、折扣码、gift guide 抢占电商转化型媒体的版面。
- 触发时机：26FPD 59 条（10 月，46 Earned + 12 Paid + 1 PR）、Prime Day 42 条（6 月，34 Earned + 5 Paid + 1 PR）；Calendar 的 Fall Prime Day 9/1-10/9、BFCM 11/1-11/30；EO 的 Prime Big Deal Days 10/7-8、BFCM 11/19-11/30、Amazon Baby Sale 2027/1/1-2/28、Valentine's 2027/1/1-2/14。
- 数据信号：Promotion/Deal/Event 117 条（34%），是最大内容类型；10 月 68 条中 47 条是 Promotion/Deal/Event；6 月 51 条中 38 条是 Promotion/Deal/Event。
- 产品角色：W1、D8、KleanPal、ChangeGo、M5、M5 Pinky、Portable Breast Milk Cooler、On-the-Go Bundle。
- 关键矛盾：大促是全年最大场景，但付费媒体表 0 条，无法核算 Paid 39 条的投入产出。

**S4 品类榜单渗透与奖项**
- 业务目的：进入「Best Breast Pump / Best Wearable / Best of the Bump / Nappa Awards」等第三方榜单，形成可复用的信任状。
- 触发时机：奖项内容 38 条，7 月项目提及 13 条、8 月 8 条；吸奶器榜单表 12 家媒体，W1 pitch 集中在 8 月初（Update 8.01-8.04）；The Bump 年度榜单 2026 已公布。
- 数据信号：Nappaawards 11 条、The Bump 13 条（其中 7 条 Awards）、Good Housekeeping 14 条（5 条 Awards）；吸奶器榜单中 11/12 媒体已出现 Momcozy，5 篇入选、5 篇未入选、2 篇空白；报道角度以「性价比」4 条、「便携」2 条为主。
- 产品角色：W1、S12 Pro、M5、M9、S9 Pro、M6、Air1、V1 Pro。

**S5 Editorial 选题 / Cultural Moment 营销**
- 业务目的：把产品放进更大的母亲叙事（安全睡眠、心理健康、母乳喂养、乳腺癌意识、早产儿、IWD），获取深度 editorial 与品牌好感。
- 触发时机：EO Cultural 6 条（National Baby Safety Month 9 月、Breast Cancer Awareness Month 10 月、World Mental Health Day 10/10、Rainbow Baby 10 月、World Prematurity Day 11/17、IWD 2027/2-3）；Calendar Cultural 4 条（PSI Donation 11 月、Wellness Cold & Flu 2027/1、IWD Campaign/Event 2027/2）。
- 数据信号：Brand Storytelling 48 条（14%）；Pitch Angle 已写得较成熟，例如 AAP 安全睡眠/SIDS、PPD/隐形劳动、Rainbow Baby CSR「不做商业推销」；PSI 合作贯穿 2026 Mother's Day 与 2026/11。
- 产品角色：Baby Monitors/Sound Machines/Sleep Sacks、The Pink Collection、吸奶器/暖奶器、Nasal Aspirator/Air Purifier、Pro Collagen/Nipple Care Pen。
- 关键矛盾：Pitch Timing 仍是「Early Aug / Mid Sep / Late Nov」这类相对时间，没有绝对日期与 Owner，无法直接排期。

**S6 品牌事件与线下 Showroom**
- 业务目的：用线下体验、Showroom、展会制造「可报道的新闻」，同时完成媒体关系维护。
- 触发时机：Calendar 三个事件——Momcozy x Babylist NYC（9/17-9/28）、Try Before You Buy at Babylist NYC（11/1-11/30）、LA Showroom Opening（2027/2/1-2/28）；历史 ABC Kids Expo（2026/5）与 Grand Opening（2026/9）已在 Tracker 留下 6 条与 7 条同题报道。
- 数据信号：Event promotion 9 条；「Grand Opening of Momcozy's Space at Babylist New York City Showroom」重复 7 次，是全年重复度最高的标题，说明事件报道角度高度同质化。
- 产品角色：全品类体验（W1、D8、BM08、PureHug、ChangeGo 等），以场景化体验为主。

**S7 品牌 Campaign / 品牌叙事**
- 业务目的：围绕「Mom, and More」建立品牌主张，输出品牌故事、研究报告、创始人/妈妈故事，而不是单品卖点。
- 触发时机：Brand Day 9/1-9/30（Calendar 的 11 条 Brand Campaign 中最大一块）；NIQ 报告 9/10、Mom, and More 发布 9/14、600 Hours of Support 7/27；2027/1 吸奶器创新故事、2027/2 孕产护肤/IWD。
- 数据信号：Brand Storytelling 48 条（14%）；重复标题包括 Working Motherhood 5 条、Breastfeeding study 5 条、Allyson Felix 4 条；PR Newswire 10 条是通稿主渠道。
- 产品角色：W1、M5 Ultra、V3、D8、PureHug、护肤线（Pro Collagen、Nipple Care Pen）。
- 关键矛盾：Campaign 与 coverage 的项目名不统一——「Mom, and More」分散在「品牌日2026」「Brand day」「“Mom, and More” campaign / Brand Day」三个项目名下。

**S8 付费媒体合作**
- 业务目的：用付费合作补齐不可控的测评、Deal、时效曝光，尤其在高价值媒体与大促节点。
- 触发时机：Paid 39 条，10 月 12、5 月 8、6 月 6、1 月 6；26FPD 12 条、Prime Day 5 条；Product Introduction/Product Review 14 条中 9 条为 Paid。
- 数据信号：付费媒体约 24 家（去重后），Scary Mommy 3、USA Today 3、SheKnows 2、New York Post 2、What to Expect 2、US Weekly 2、Healthline 2、Romper 2、KTLA 5 2、Bustle 2、Your baby club 2。
- 产品角色：测评型产品（吸奶器、监护器、推车）与大促 SKU。
- 关键矛盾：付费媒体表 0 条、仅 1 个「文本」字段；39 条 Paid 只有媒体/项目/类型，没有金额、形式、KPI、ROI，无法判断 11% 的付费投入是否有效。

**S9 PR 资产沉淀与复用**
- 业务目的：把媒体关系、Media Kit、奖项授权、洞察分析、通稿日历变成可复用资产，降低重复劳动与人员依赖。
- 触发时机：持续；PR资源库 18 份文档、5 位 Owner；建议季度盘点（3/6/9/12 月）。
- 数据信号：文档类型 Trackers 2、PR资源 4、工作文档 4、洞察分析 2，另有 6 份具名文档无类型；4 份具名文档无 Owner + 1 条空记录；核心资产包括 Media Coverage Tracker、Media Core List、PR Media Kit、MuckRack、2026 奖项申报与授权、Momcozy 词云分析、通稿发布日历。
- 关键矛盾：PR资源库与媒体资源库、报道Tracker 没有关联字段（只有 Parent items 自关联），资产无法自动挂到具体场景或媒体。

---

## 二、每个场景的 SOP

> 角色定义：**PR Manager** = 内部 PR 负责人（郭薇/庄宇铃/肖熠君/高雅静/邓苇）；**Agency** = 外部公关代理（Co-Op 及 Media owner 记录中的 Gabrielle Zollner、Giulia Corbella、Eden Cali）；**Editor** = 外部媒体编辑/奖项通道；**Vicky** = AI PR Agent（监测、研究、初稿、风险复核、知识库）。

### S1 日常 Earned 媒体 Pitch

| # | 步骤（动词开头） | 责任角色 | 工具 / 表 | 产出物 |
|---|---|---|---|---|
| 1 | 建立/更新周度 pitch 主题池 | PR Manager | Editorial Opportunities + Pitching Calendar | 未来 4 周 Pitch 主题池 |
| 2 | 按媒体类别、评级、GEO/SEO、历史覆盖筛选目标媒体 | PR Manager | 媒体资源库 + 报道Tracker | 目标媒体清单（含排除项） |
| 3 | 查找 Editor 与联系历史，判断 cold/warm 路径 | Agency | PR资源库（MuckRack）+ 吸奶器表 Editor 联系历史 | 联系人清单 |
| 4 | 撰写个性化 pitch（角度/产品/证据/样品） | Agency（Vicky 初稿） | Editorial Opportunities Pitch Angle + PR Media Kit | Pitch 邮件/话术 |
| 5 | 发送并登记媒体、日期、角度、负责人 | Agency | Pitching Calendar 或独立 Pitch Log | Pitch 记录 |
| 6 | T+3 / T+7 follow up，记录拒绝原因与下一步 | Agency | 吸奶器表 Pitching Status / Agency Notes | 状态更新 |
| 7 | 上线 48 小时内回收链接、标题、产品、类型 | PR Manager | 报道Tracker | Coverage 记录 |
| 8 | 月度复盘命中率与角度，调整评级/优先级 | PR Manager | 报道Tracker + 媒体资源库 | 月报 + 评级调整 |

**关键控制点**：T+7 无回复转下一家；同一媒体 90 天内不重复同题；pitch 必须带 1 个可验证数据/样品/独家角度；所有上线必须回写 Tracker，否则不计入月度产出。

**当前缺口**：日常 pitch 没有独立状态表，Pitching Calendar 只有 23 条 campaign 级记录，承接不了 26 条「日常推广」+73 条未标注；媒体资源库 28 字段中 19 个为占位字段；B/C 级媒体利用率仅 11%/0%。

### S2 新品上市媒体首发

| # | 步骤（动词开头） | 责任角色 | 工具 / 表 | 产出物 |
|---|---|---|---|---|
| 1 | 上市前 8-10 周锁定 launch brief（产品/卖点/价格/上市日/样品量） | PR Manager + Product | Pitching Calendar | Launch Brief |
| 2 | 建立 Editorial Opportunity（类型/角度/目标媒体/媒体样例） | PR Manager | Editorial Opportunities | 选题卡 |
| 3 | 确定首发媒体组合：1-2 家独家/embargo + 5-10 家 roundup + 品类榜单 | PR Manager | 媒体资源库 | 首发媒体名单 |
| 4 | 准备 Media Kit、产品图、样品、FAQ、claims 证据 | PR Manager（Vicky 校验） | PR资源库 | Media Kit + 样品清单 |
| 5 | 寄样并登记物流/编辑反馈 | Agency | 吸奶器表 / PR资源库 | 寄样记录 |
| 6 | 首发日发 embargo 稿/通稿（如需） | PR Manager | PR资源库 + 报道Tracker | 通稿/首发稿 |
| 7 | 上线追踪收录、标题、角度、产品、链接 | PR Manager | 报道Tracker | 新品 coverage 清单 |
| 8 | 30/60/90 天复盘首发命中、评测转化、榜单承接 | PR Manager | 报道Tracker + 媒体资源库 | 新品 PR 复盘 |

**关键控制点**：所有 claim 必须有证据；首发名单至少含 3 家 S/A 媒体；样品签收后 5 个工作日内跟进；首发媒体与 roundup 媒体分开管理，避免独家冲突。

**当前缺口**：EO 11 条 New Product Launch 中，V3、V3 Pro、BN09、光疗仪、AirMesh、CB004 等 7 条缺 Key Product 或 Pitch Angle；「M5 Ultra Breast Pump」的 Key Product 写成「M8」，与 Pitching Calendar「M5 Ultra」冲突；「Bottle Washer (D8)」的 Pitch Angle 写成劳工节折扣，产品与角度错配。

### S3 电商大促 Deal 投放

| # | 步骤（动词开头） | 责任角色 | 工具 / 表 | 产出物 |
|---|---|---|---|---|
| 1 | 大促前 6-8 周获取机制、价格、折扣码、库存/时效 | PR Manager + Ecommerce | Pitching Calendar | Deal 信息包 |
| 2 | 建立 Promotion 条目与 deal 角度 | PR Manager | Pitching Calendar + Editorial Opportunities | 大促选题卡 |
| 3 | 按 Deal/Commerce Editor 清单分发（News/Lifestyle 为主） | Agency | 媒体资源库 | Deal pitch 名单 |
| 4 | 提供 deal 清单、比价信息、产品组合、图片 | PR Manager | PR资源库 | Deal 素材包 |
| 5 | 上线追踪 deal 文章、折扣码、产品露出 | PR Manager | 报道Tracker | Deal coverage 记录 |
| 6 | 大促中补量：高转化媒体二次 pitch / 付费补位 | PR Manager + Agency | 付费媒体合作数据（当前空） | 补量记录 |
| 7 | 大促后复盘收录数、S/A 占比、付费/自然比例 | PR Manager | 报道Tracker | 大促 PR 复盘 |

**关键控制点**：价格/折扣码必须由电商确认；付费内容必须披露；大促结束后 7 天内完成复盘；deal 文章必须核对折扣码有效期。

**当前缺口**：26FPD 59 条中 12 条 Paid，但付费表 0 条，无法算 ROI；Calendar 的 Fall Prime Day 是 9/1-10/9，而实际 26FPD 集中 10 月，planning 与 release 有 3-5 周错位；BFCM 的「Broadcast Blitz」结束日期写成 2027-10-31，疑似笔误。

### S4 品类榜单渗透与奖项

| # | 步骤（动词开头） | 责任角色 | 工具 / 表 | 产出物 |
|---|---|---|---|---|
| 1 | 锁定年度榜单/奖项日历（Best of、Nappaawards、The Bump、GH、Wirecutter 等） | PR Manager | 吸奶器表 + 报道Tracker | 榜单/奖项清单 |
| 2 | 调研目标媒体现有榜单、评选维度、Momcozy 是否已出现 | PR Manager | 吸奶器表 Breast Pump 品类词相关报道 | 榜单 gap 分析 |
| 3 | 找到 Editor/申报通道与联系历史 | Agency / PR Manager | Editor Name / 联系历史 / MuckRack | 联系人 + 申报通道 |
| 4 | 提交申报/寄样（W1、S12 Pro、M5、M9 等） | Agency | 吸奶器表 Pitching Status | 申报记录 |
| 5 | 跟进评审、补充材料、样品 | Agency | Agency Notes | 评审状态 |
| 6 | 公布后回写入选/获奖 | PR Manager | 吸奶器表「本篇报道是否有入选」+ 报道Tracker | 获奖/入选记录 |
| 7 | 管理报道角度（Best Value / Best Hands-Free / Best for Beginners） | PR Manager | 吸奶器表「媒体报道角度」 | 角度矩阵 |
| 8 | 将获奖/入选转为信任状（Brand Trust Letter、License、Media Kit） | PR Manager | PR资源库 | 信任状资产 |
| 9 | 回写媒体评级升降 | PR Manager | 媒体资源库 | 评级更新 |

**关键控制点**：申报截止前 2 周完成材料；同一产品在不同榜单使用差异化角度；获奖后 30 天内完成 License 登记；未入选媒体必须记录原因与下次窗口。

**当前缺口**：12 家榜单媒体中仅 7 家有 Editor 联系历史（58%），Agency Notes 仅 4 条（33%）；The Independent 是唯一「Momcozy 未出现」的媒体，属于明确 white space；The Bump 状态写「W1 入围但没获奖」，但角度写「Air1 获奖/V1 PRO Overall Best」，状态与角度冲突；Wirecutter、Women's Health、Wired 在榜单表中被跟踪，但 2026 报道 Tracker 无上线记录，说明「榜单跟踪」与「coverage 回写」脱节。

### S5 Editorial 选题 / Cultural Moment 营销

| # | 步骤（动词开头） | 责任角色 | 工具 / 表 | 产出物 |
|---|---|---|---|---|
| 1 | 建立年度 cultural calendar（月份/议题/目标媒体类型） | PR Manager | Editorial Opportunities | Cultural Calendar |
| 2 | 选题本地化：把全球议题转成美国妈妈语境 + 产品角色 | PR Manager + Vicky | Editorial Opportunities Pitch Angle | 选题卡 |
| 3 | 准备证据：研究/数据/专家/公益伙伴（PSI、NIQ、AAP） | Vicky + PR Manager | PR资源库 | Evidence Pack |
| 4 | 匹配媒体类型（Mother&baby / News / Lifestyle / Women / Health） | PR Manager | 媒体资源库 | 目标名单 |
| 5 | Pitch + 独家/访谈安排 | Agency | Editorial Opportunities Media Examples | Pitch 记录 |
| 6 | 风险复核：claim、医疗/心理议题、公益边界 | Vicky | 知识库/红线 | 风险审阅记录 |
| 7 | 上线追踪 + 议题声量复盘 | PR Manager | 报道Tracker | Coverage + 复盘 |

**关键控制点**：医疗/心理/公益议题必须走证据与合规复核；Rainbow Baby 类议题不做商业推销；pitch 提前 3-6 周；文化议题必须有一个「品牌为什么有资格说」的理由。

**当前缺口**：Pitch Timing 是相对时间（Early Aug / Mid Sep / Late Nov），没有绝对日期和 Owner；6 条 Cultural 中 3 条没有 Key Product，难以追踪产品关联；2027/2 IWD 在 Pitching Calendar 有 2 条，但 Editorial Opportunities 没有对应选题卡，2 月是「有日历、无角度」的空窗。

### S6 品牌事件与线下 Showroom

| # | 步骤（动词开头） | 责任角色 | 工具 / 表 | 产出物 |
|---|---|---|---|---|
| 1 | 事件立项：目标、场地、日期、预算、KPI | PR Manager | Pitching Calendar | 事件 brief |
| 2 | 建立事件条目与报道角度 | PR Manager | Pitching Calendar + Editorial Opportunities | 事件选题卡 |
| 3 | 媒体名单：S/A + 本地 + 母婴/生活方式 + 嘉宾 | PR Manager | 媒体资源库 | 邀请名单 |
| 4 | 邀请/RSVP/行程/样品 | Agency | 媒体资源库 + PR资源库 | RSVP 表 |
| 5 | 现场素材：新闻稿、图、视频、Media Kit | PR Manager（Vicky 辅助） | PR资源库 | 事件素材包 |
| 6 | 事件当天/次日发稿与二次传播 | PR Manager | 报道Tracker | 事件报道 |
| 7 | 追踪 Event promotion 报道 | PR Manager | 报道Tracker | Coverage 记录 |
| 8 | 复盘到场率、报道数、S/A 占比、关系深化 | PR Manager | 报道Tracker + 媒体资源库 | 事件复盘 |

**关键控制点**：活动前 4 周发邀请、前 1 周确认；现场 24 小时内出图；事件报道统一标题/话题；每个事件至少准备 3 个差异化角度，避免所有媒体写同一篇。

**当前缺口**：Pitching Calendar 没有预算、场地、KPI、RSVP 字段；事件类 coverage 只有 9 条 Event promotion，且 7 条是同一 Showroom 标题，说明事件报道高度同质化、缺少差异化角度。

### S7 品牌 Campaign / 品牌叙事

| # | 步骤（动词开头） | 责任角色 | 工具 / 表 | 产出物 |
|---|---|---|---|---|
| 1 | 定义 campaign 主张与证据 | PR Manager + Brand | Pitching Calendar | Campaign brief |
| 2 | 研究/白皮书/调研（NIQ、Talker Research） | Vicky + PR Manager | PR资源库 | 研究报告 |
| 3 | 建立 campaign 条目与传播节奏 | PR Manager | Pitching Calendar | Campaign 日历 |
| 4 | 媒体分层：独家/深度/快讯/榜单 | PR Manager | 媒体资源库 | 媒体矩阵 |
| 5 | 生产资产：新闻稿、hero story、妈妈故事、社媒素材 | PR Manager（Vicky 初稿） | PR资源库 | Campaign Kit |
| 6 | Pitch + 通稿发布 | Agency + PR Manager | 报道Tracker | Pitch/通稿记录 |
| 7 | 上线追踪品牌故事/深度稿/重复标题 | PR Manager | 报道Tracker | Coverage 记录 |
| 8 | 复盘品牌故事占比、S/A 媒体、信息一致性 | PR Manager | 报道Tracker + 媒体资源库 | Campaign 复盘 |

**关键控制点**：一个 campaign 一个核心信息 + 3 个证据点；通稿与 pitch 角度必须一致；Brand Day 类 campaign 提前 6-8 周；所有媒体必须使用同一版 brand boilerplate。

**当前缺口**：Brand Campaign 是 Pitching Calendar 最大类型（11/23），但 Tracker 的「品牌日2026」只有 22 条（+Brand day 2），campaign 与 coverage 的映射不唯一；「Mom, and More」相关记录分散在三个项目名；NIQ 研究报告没有在 PR资源库中单独登记为「洞察分析」资产。

### S8 付费媒体合作

| # | 步骤（动词开头） | 责任角色 | 工具 / 表 | 产出物 |
|---|---|---|---|---|
| 1 | 明确付费目标（测评/Deal/曝光/榜单补位） | PR Manager | 付费媒体合作数据 | 付费 brief |
| 2 | 选媒体与报价（S/A + 垂直 + 时效节点） | PR Manager | 媒体资源库 + 付费媒体表 | 媒体/报价清单 |
| 3 | 合同/授权/合规（FTC 披露、素材授权） | PR Manager | PR资源库 | 合同/授权 |
| 4 | 内容 brief 与样品 | PR Manager | PR资源库 | Brief + 样品 |
| 5 | 上线验收：链接、披露、产品、日期 | PR Manager | 报道Tracker | 验收记录 |
| 6 | 效果回收：曝光/点击/转化（如可得） | PR Manager | 付费媒体表 | 效果数据 |
| 7 | 预算/ROI 复盘与下季度计划 | PR Manager | 付费媒体表 + 报道Tracker | ROI 复盘 |

**关键控制点**：付费内容必须披露；同一媒体付费/自然比例设上限；季度复盘；付费媒体必须与 earned 媒体分开评估，避免「用付费量掩盖 earned 质量」。

**当前缺口**：付费媒体表 0 条、仅 1 个「文本」字段；39 条 Paid 记录只有媒体/项目/类型，没有金额、形式、KPI、ROI；无法判断 11% 的付费投入是否有效，也无法做「付费 vs 自然」的边际分析。

### S9 PR 资产沉淀与复用

| # | 步骤（动词开头） | 责任角色 | 工具 / 表 | 产出物 |
|---|---|---|---|---|
| 1 | 识别资产需求（Media Kit/联系人/奖项/洞察/模板） | PR Manager | PR资源库 | 资产清单 |
| 2 | 收集与清洗（文档/链接/截图/数据） | Owner | PR资源库 | 原始资产 |
| 3 | 分类/命名/权限/版本 | Owner | PR资源库 | 结构化资产 |
| 4 | 关联场景：媒体关系/新品/大促/榜单/事件 | PR Manager | PR资源库 + 媒体资源库 | 资产地图 |
| 5 | 复用：pitch/通稿/申报/事件 | PR Manager / Agency | PR资源库 | 复用记录 |
| 6 | 季度盘点：过期/缺失/重复 | PR Manager | PR资源库 | 盘点报告 |
| 7 | 更新与交接 | Owner | PR资源库 | 最新版本 |

**关键控制点**：每份资产必须有 Owner、类型、更新日期、适用场景；季度清理过期链接；新员工入职 1 周内能通过资产库找到 Media Kit、MuckRack、奖项授权与历史 coverage。

**当前缺口**：18 条中 4 份具名文档无 Owner + 1 条空记录；6 份具名文档无类型；文档类型只有 4 类，缺「模板/案例/危机」等；PR资源库与媒体资源库、Tracker 没有关联字段，资产无法自动挂到场景。

### SOP 成熟度与优先级

| 场景 | 数据完备度 | SOP 成熟度 | 优先级 | 理由 |
|---|---|---|---|---|
| S1 日常 Earned | 中 | 中 | P1 | 量最大、复用性最高，但缺 pitch 状态表与媒体映射 |
| S2 新品首发 | 中 | 中 | P0 | 2026 Q4-2027 Q1 新品密集，EO 字段缺口直接影响首发 |
| S3 大促 Deal | 高 | 高 | P0 | 26FPD/BFCM 临近，数据最丰富，但付费/ROI 缺口 |
| S4 榜单/奖项 | 中 | 中 | P0 | 5/10 入选，50% 提升空间；联系历史仅 58% |
| S5 Editorial/Cultural | 中 | 中 | P1 | 角度库已成型，缺绝对排期与 Owner |
| S6 品牌事件 | 低 | 低-中 | P1 | 事件报道同质化，缺 KPI/RSVP 字段 |
| S7 品牌 Campaign | 中 | 中 | P0 | Brand Day 已跑通，但 campaign 与 coverage 映射不唯一 |
| S8 付费媒体 | 低 | 低 | P1 | 11% 篇数但 0 条台账，无法算 ROI |
| S9 资产沉淀 | 中 | 中 | P1 | 18 份文档已起步，缺 Owner/类型/场景关联 |

---

## 三、节奏与日历

### 3.1 2026 年 1-10 月历史节奏

| 月份 | 上线篇数 | 主导内容类型 | 主导项目 | 解读 |
|---|---:|---|---|---|
| 2026-01 | 24 | Product Roundup 9、Product Review 6 | 日常推广 17 | 开年评测/榜单，CES 节点 |
| 2026-02 | 11 | Roundup 4、Review 4 | 日常推广 6 | 全年最低，淡季 |
| 2026-03 | 31 | Promotion/Deal/Event 18 | 未标注 13、单品推广 9 | 春季促销 |
| 2026-04 | 26 | Gift Guide 10、Awards 9 | 未标注 20 | 母亲节礼物指南 + 奖项启动 |
| 2026-05 | 31 | Brand Storytelling 14 | Mother's Day 15、ABC Kids Expo 4 | 母亲节 + 展会 |
| 2026-06 | 51 | Promotion/Deal/Event 38 | Prime Day 39 | 夏促峰值 |
| 2026-07 | 36 | Brand Storytelling 13、Roundup 10、Awards 7 | Breastfeeding Month 16、奖项 13 | 母乳月 + 奖项 |
| 2026-08 | 16 | Awards 6 | 奖项 8 | 奖项淡季 |
| 2026-09 | 42 | Roundup 9、Brand Storytelling 9、Event 8 | 品牌日 23 | Brand Day + 事件 |
| 2026-10 | 68 | Promotion/Deal/Event 47 | 26FPD 53 | 秋促峰值，全年最高 |

**节奏规律**：

- **双峰结构**：6 月（Prime Day）与 10 月（26FPD）是两大峰值，合计 119 条，占 1-10 月的 35%。
- **品牌节点补充**：5 月母亲节、7 月母乳月、9 月 Brand Day 形成三个次级峰值。
- **淡季明显**：2 月 11 条、8 月 16 条，适合做资产盘点、榜单申报、SOP 复盘，而不是硬推声量。
- **大促月内容类型单一**：6 月 75% 是 Promotion/Deal/Event，10 月 69% 是 Promotion/Deal/Event，说明大促月品牌故事/深度内容被挤压。

### 3.2 2026-09 至 2027-03 关键日历

| 月份 | Pitching Calendar 关键节点 | Editorial Opportunities 选题 | 核心产品 | 类型 | PR 动作重点 |
|---|---|---|---|---|---|
| 2026-09（Calendar 5 / EO 4） | Brand Day Core Products 9/1-9/30；Continued Elite Moms Pitching 9/1-9/30；M5 Ultra Launch 9/1-10/15；Fall Prime Day 9/1-10/9；Momcozy x Babylist NYC Event 9/17-9/28 | National Baby Safety Month 9/1-9/30；Bottle Washer D8 9/1-11/1；Ergonest Belly Band 9/1-9/30；Institutional Course Partnership 9/25-11/30 | W1、BirthEase、D8、Triple-Seal Diaper Pail、2-in-1 Swing、Sound Machine、Nasal Aspirator、BM08、PureHug、M5 Ultra、Ergonest | Brand Campaign + Product Launch + Promotion + Cultural | Brand Day 通稿 + Elite Moms；M5 Ultra 首发；Fall Prime Day deal；Babylist 事件；Baby Safety Month 监护仪角度 |
| 2026-10（Calendar 2 / EO 6） | Liv Lee Artist Gift Box 10/1-10/31；Broadcast Blitz for BFCM 10/1-2027/10/31（疑似笔误） | Breast Cancer Awareness Month 10/1-10/31；Rainbow Baby 10/1-10/31；Amazon Prime Big Deal Days 10/7-10/8；World Mental Health Day 10/10；M5 Ultra Breast Pump 10/12-1/3；Baby Nasal Aspirator BN09 10/12-1/3 | The Pink Collection、M5 Ultra/M8、BN09、Liv Lee gift box | Cultural + Promotion + Launch | Pink Collection 乳腺癌月；Rainbow Baby CSR（不做商业推销）；Prime Big Deal Days deal；心理健康日；M5 Ultra/BN09 评测寄样 |
| 2026-11（Calendar 4 / EO 7） | Try Before You Buy Event at Babylist NYC 11/1-11/30；Black Friday/Cyber Monday 11/1-11/30；PSI Donation Initiative 11/1-11/30；PSI x Babylist Event 11/1-11/30 | Multi-functional Light Therapy Device 11/1-1/10；AirMesh Nursing Bra FB095/96 11/1-12/27；V3 Pro 11/2-1/3；V3 11/2-1/3；World Prematurity Day 11/17；Black Friday/Cyber Monday 11/19-11/30；Sound Machine WN08 11/23-1/10 | V3/V3 Pro、WN08、Nursing Bra、Light Therapy、PSI、BFCM 全品类 | Promotion + Launch + Cultural + Event | BFCM deal 清单；PSI 公益/捐赠；早产儿日 NICU 角度；V3 系列首发；护理内衣礼物指南 |
| 2026-12（Calendar 3 / EO 3） | Last Minute Gifts from Amazon 12/1-12/31；Holiday Travel Products 12/1-12/31；Time Savers During Holiday Season 12/1-12/31 | Milk Warmer MW08 12/1-1/10；Muslin Baby Carrier CB004 12/1-1/10；Christmas & New Year 12/25-1/3 | Nursing Shawl、Stroller Organizer、On-the-Go Bundle、Portable Sound Machine、7-in-1 Bottle Cleaning Set、DeepClean、PureHug、MW08、CB004、Gift Box | Promotion + Brand Campaign + Launch | 节日礼物指南；出行场景；时间节省；最后一分钟礼物；圣诞/新年 |
| 2027-01（Calendar 4 / EO 0 新） | Valentine's Day Gift Guides 1/1-2/14；Wellness Products for Cold and Flu 1/1-1/31；Breast Pump Innovation Story 1/1-1/31；Amazon Baby Sale 1/1-2/28 | 仅 10-12 月新品的尾波（M5 Ultra、V3、BN09、WN08、MW08、CB004 到 1/3-1/10） | W1、M5 Ultra、V3、Nasal Aspirator、Air Purifier、Valentine's gift | Promotion + Cultural + Brand Campaign | 情人节礼物指南；冷流感季；吸奶器创新故事；Amazon Baby Sale；承接 Q4 新品尾波 |
| 2027-02（Calendar 5 / EO 0 新） | Breast and Belly Skincare Guide 2/1-2/28；IWD Campaign 2/1-3/8；IWD Event 2/1-3/8；Nursery Recliner Launch 2/1-2/28；LA Showroom Opening 2/1-2/28 | 无新选题；Valentine's 到 2/14、Amazon Baby Sale 到 2/28 | Pro Collagen Belly Firming Moisturizer、Nipple Care Pen、Nursery Recliners、IWD、LA Showroom | Brand Campaign + Product Launch + Cultural + Event | 孕产护肤；IWD 内容/事件；躺椅首发；LA Showroom；2 月 Calendar 最密但 EO 空窗，需补选题卡 |
| 2027-03 | IWD 收口 3/8 | 无新选题 | IWD 相关 | Cultural | IWD 收口 + Q1 复盘 |

**季度主题**：

- **2026 Q3**：Brand Day + M5 Ultra + Babylist 事件 + National Baby Safety Month，品牌、新品、事件三线并行。
- **2026 Q4**：26FPD + BFCM + Holiday + V3/WN08/MW08/CB004 四个新品 + PSI/World Prematurity，大促、新品、公益并行，是全年最拥挤的季度。
- **2027 Q1**：Valentine's + Amazon Baby Sale + 冷流感季 + 吸奶器创新故事 + IWD + 孕产护肤 + Nursery Recliner + LA Showroom，礼物、健康、品牌、新品、事件五线并行。

### 3.3 周度/月度运营节拍（建议，基于数据节奏推断）

| 时点 | 动作 | 责任角色 | 产出 |
|---|---|---|---|
| 周一 | Pipeline review：未来 4 周 Calendar/EO、上周 coverage、待 follow up | PR Manager | 周度 Pipeline 表 |
| 周二-周三 | Pitch wave、follow up、寄样、RSVP | Agency | Pitch/寄样记录 |
| 周四 | Coverage 回收、Tracker 回写、链接核验 | PR Manager | 更新后的 Tracker |
| 周五 | 周报 + Vicky 舆情/风险摘要 + 下周优先级 | PR Manager + Vicky | 周报 |
| 月末 | 月度复盘：篇数、S/A 占比、项目密度、角度命中 | PR Manager | 月报 |
| 季末 | 媒体评级复核、资源库盘点、奖项/榜单 calendar 更新 | PR Manager | 季度复盘 + 资产盘点 |

### 3.4 日历与数据风险

1. **两套类型体系不统一。** Pitching Calendar 只有 Brand Campaign、Product Pitching、Cultural/Awareness Moment、Promotion 四类；Editorial Opportunities 有 New Product Launch（11/20，55%），两表无法直接 join，导致「日历上的 campaign」与「选题上的 launch」对不上。
2. **10 月 Calendar 少、EO 多。** Calendar 只有 2 条（Liv Lee、Broadcast Blitz），EO 有 6 条（乳腺癌月、Rainbow Baby、Prime Big Deal、心理健康日、M5 Ultra、BN09）；而 10 月实际 53 条 26FPD coverage，说明 Calendar 没有完整承接 10 月。
3. **2 月 Calendar 多、EO 空。** Calendar 有 5 条（护肤、IWD x2、躺椅、LA Showroom），EO 没有新选题卡，意味着 2 月有「要做什么」，但没有「怎么 pitch、找谁、什么角度」。
4. **M5 Ultra 产品名冲突。** Calendar 写「M5 Ultra」，EO 的 Opportunity Name 写「M5 Ultra Breast Pump」，但 Key Product 写「M8 Breast Pump」。
5. **D8 类型与角度错配。** EO「Bottle Washer (D8)」类型是 New Product Launch，Pitch Angle 却是「劳工节母婴品类折扣清单及比价信息」，更像 Promotion。
6. **Broadcast Blitz 日期异常。** 2026-10-01 至 2027-10-31，跨度 13 个月，疑似应为 2026-10-31。
7. **Pitch Timing 不是日期。** EO 的 Pitch Timing 是 Early Aug / Mid Sep / Late Nov 等相对时间，没有绝对日期与 Owner，无法直接生成任务。
8. **Q4 空白不是无 coverage。** Tracker 11-12 月为空是因为分析时点为 10/31，不代表 Q4 没有计划；Calendar 已排到 2027-03，属于「计划在前、结果在后」的正常状态。

---

## 四、资源与角色矩阵

### 4.1 项目/活动投入密度

> 347 条记录中，274 条有「需求|项目」；同一记录可挂多个项目，以下为多标签计数。

| 项目/活动 | 篇数 | 占 347 条 | 合作类型（主） | 代表媒体 | 业务含义 |
|---|---:|---:|---|---|---|
| 26FPD（秋季 Prime Day） | 59 | 17.0% | Earned 46 / Paid 12 / PR 1 | The Bump、Babylist、New York Post、Yahoo Shopping | 全年最大单点，10 月峰值 |
| Prime Day（夏促） | 42 | 12.1% | Earned 34 / Paid 5 / PR 1 | BuzzFeed、The Bump、USA Today | 6 月峰值 |
| 奖项/榜单申报 | 33 | 9.5% | Awards 18 + Earned | Nappaawards、The Bump、Good Housekeeping | 信任状与 GEO/SEO 资产 |
| 日常推广 | 26 | 7.5% | Earned 24 / Paid 2 | BuzzFeed、MSN、SheKnows | Always-on 基本盘 |
| 品牌日 2026 / Mom, and More | 25 | 7.2% | Earned 15 / Paid 3 / PR 4 | PR Newswire、MSN、Parents | 品牌叙事主 campaign |
| Mother's Day 2026 | 23 | 6.6% | Earned 主导 | Parents、The Bump、Motherly | 5 月节点 |
| Breastfeeding Month | 19 | 5.5% | Earned 16 / PR 2 | PR Newswire、Parents、BabyCenter | 7-8 月公益/教育 |
| IWD 2026 | 11 | 3.2% | Earned 主导 | Parents、SheKnows、Bustle | 2-3 月女性议题 |
| ABC Kids Expo | 6 | 1.7% | Earned 3 / Paid 2 / PR 1 | 行业/新闻媒体 | 展会 |
| Father's Day 2026 | 4 | 1.2% | Earned | Parents、SheKnows | 6 月节点 |
| 公益/捐赠 | 2 | 0.6% | Earned / PR | PR Newswire | 信任/ESG |
| 未标注 | 73 | 21.0% | Earned 67 / Paid 2 / Awards 1 | 长尾 | 数据治理缺口，无法归因 |

**观察**：

- 前五个具名项目（26FPD、Prime Day、奖项、日常、品牌日）合计 185 条，占 53%，项目集中度高。
- 21% 的记录没有项目归属，是投入产出分析的最大障碍；这部分很可能是日常 pitch 与长尾 coverage。
- 奖项/榜单 33 条、Mother's Day 23 条、Breastfeeding Month 19 条，说明「节点型项目」是 PR 的主要工作单元，而不是「产品线」。

### 4.2 Owner 与文档/表

| Owner | 文档数 | 负责文档 | 覆盖环节 | 关联表 |
|---|---:|---|---|---|
| 庄宇铃（Zoe） | 4 | 媒体关系管理/Media Core List；PR Media Kit；2026 Brand Day；2026 Father's Day | 媒体关系、资产、品牌节点 | 媒体资源库、PR资源库、吸奶器表（The Bump） |
| 郭薇 | 3 | PR核心媒体现状分析（吸奶器）；2026 BFCM；Momcozy 词云分析 | 洞察、核心媒体、大促 | 吸奶器表（Babylist）、PR资源库、报道Tracker |
| 肖熠君 | 3 | 2026 PSI 专业课程合作；2026 BFCM（co-owner）；通稿发布日历 | 公益、通稿、大促 | PR资源库、报道Tracker |
| 高雅静 | 2 | 媒体文章上线汇总（Media Coverage Tracker）；MuckRack 账户信息 | 数据底座、媒体工具 | 报道Tracker、PR资源库 |
| 邓苇 | 2 | 2026 年奖项申报 Awards；2026 BFM | 奖项、品牌月 | PR资源库、报道Tracker |
| 未分配 | 4 + 1 空记录 | 奖项申请管理；奖项授权需求登记；已授权奖项汇总；品牌Campaigns PR 工作文档汇总 | 奖项/资产治理 | PR资源库 |

> Owner 单元格 13 个非空，覆盖 13 份文档（BFCM 为郭薇/肖熠君双 Owner）；18 份文档中 4 份具名文档无 Owner，另有 1 条空记录。

### 4.3 场景 × 角色 RACI

> A = 最终负责，R = 执行，C = 协作/评审，I = 知会。

| 场景 | PR Manager | Agency | Editor | Vicky |
|---|---|---|---|---|
| S1 日常 Earned | A/R | R | C | C（选题雷达/初稿） |
| S2 新品首发 | A/R | R | C | C（brief/claims 校验） |
| S3 大促 Deal | A/R | R | C | I（deal 监测） |
| S4 榜单/奖项 | A/R | R | C | C（榜单监测） |
| S5 Editorial/Cultural | A/R | R | C | R（议题雷达/风险复核） |
| S6 品牌事件 | A/R | R | C | C（素材/传播） |
| S7 品牌 Campaign | A/R | R | C | R（研究/初稿） |
| S8 付费媒体 | A/R | C | C | I |
| S9 资产沉淀 | A/R | I | I | R（知识库/索引） |

### 4.4 外部 Agency / Editor 资源

| 类型 | 名称 | 关联媒体/项目 | 数据来源 |
|---|---|---|---|
| Agency | Co-Op | W1/D8/BFAM pitch；ABC Expo 邀请；Babylist follow up | 吸奶器表 Agency Notes |
| Agency | Gabrielle Zollner | Wired、The Strategist | Media owner |
| Agency | Giulia Nazzarena Corbella | Made for Mums、The Independent | Media owner |
| Agency | Eden Cali | Parents | Media owner |
| Internal | 郭薇 | Babylist | Media owner |
| Internal | 庄宇铃 | The Bump | Media owner |
| Editor | Alicia Betz | Forbes | Editor Name |
| Editor | Angela Lashbrook | Consumer Reports | Editor Name |
| Editor | Madeleine Evans | Good Housekeeping | Editor Name |
| Editor | Caitlin Giddings | Wirecutter (The New York Times) | Editor Name |
| Editor | Marguerite Williams Kypreos | Women's Health | Editor Name |
| Editor | Chaunie Brusie | Parents | Editor Name |
| Editor | Nena Farrell | Wired | Editor Name |
| Editor | Liza Corsillo | The Strategist (New York Magazine) | Editor Name |
| Editor | Sara Conway | Made for Mums | Editor Name |
| Editor | Rebecca Moore | The Independent | Editor Name |
| Editor | Madeline Weinfield | The Bump（奖项申报通道） | Editor Name |

**资源结构判断**：

- 榜单表 12 家媒体中，11 家有 Editor Name（92%），但只有 7 家有联系历史（58%），4 家没有 Agency Notes（33%），说明「知道找谁」但「不知道怎么找/找过没有」。
- Agency 明确出现在 4 条 Agency Notes 中，均围绕 W1/D8/BFAM，说明 Co-Op 的职责集中在吸奶器新品与母乳月，其他品类/项目主要靠内部。
- Media owner 中 Agency 占 5/7，内部占 2/7（郭薇-Babylist、庄宇铃-The Bump），核心媒体关系仍由内部兜底。

### 4.5 表的所有权与更新责任

| 表 | 记录数 | 主责角色 | 数据中的 Owner | 建议更新频率 | 当前完备度 |
|---|---:|---|---|---|---|
| 媒体资源库 | 246 | PR Manager | 未设 Owner 字段 | 月度/季度 | 评级 96%、GEO 91%、SEO 94%；28 字段中 19 个占位 |
| 报道Tracker | 347 | 高雅静（文档 Owner）+ 全员录入 | 高雅静（媒体文章上线汇总） | 每周 | 项目 79%、产品 75%、评级 60%、品线 0% |
| Pitching Calendar | 23 | PR Manager | 未设 Owner 字段 | 月度 | 日期 100%；Key Product 具体率 48%；无 Status |
| Editorial Opportunities | 20 | PR Manager | 未设 Owner 字段 | 月度/季度 | Angle 70%、Timing 80%、Media Examples 70% |
| 吸奶器榜单 | 12 | 郭薇/庄宇铃 + Agency | 郭薇、庄宇铃、Gabrielle/Giulia/Eden | 双周 | 联系历史 58%、Agency Notes 33% |
| PR资源库 | 18 | 5 位 Owner | 庄宇铃 4、郭薇 3、肖熠君 3、高雅静 2、邓苇 2 | 季度 | Owner 68%、类型 63% |
| 付费媒体合作数据 | 0 | 未定 | 无 | — | 0% |

### 4.6 负载与风险观察

- **庄宇铃是文档负载最重的人**：4 份文档，覆盖 Media Core List、PR Media Kit、Brand Day、Father's Day，同时是 The Bump 的 Media owner；媒体关系与品牌节点双负载，存在单点风险。
- **郭薇承担最多战略洞察**：3 份文档（吸奶器核心媒体分析、BFCM、词云分析）+ Babylist Media owner，属于「洞察 + 核心媒体 + 大促」三重角色，认知负荷高。
- **肖熠君聚焦公益/通稿**：PSI 课程合作、BFCM（co-owner）、通稿发布日历，适合承接 S5/S7 的公益与通稿主线。
- **高雅静是数据底座**：Media Coverage Tracker + MuckRack；但 Tracker 项目 79%、产品 75%、评级 60%，数据治理是当前瓶颈，直接影响到所有场景的复盘质量。
- **邓苇聚焦奖项/品牌月**：Awards + BFM，与 S4 的奖项申报高度匹配；奖项 bucket 33 条、Awards 合作 18 条，职责清晰。
- **4 份具名文档无 Owner + 1 条空记录**：尤其「奖项申请管理」「奖项授权需求登记」「已授权奖项汇总」三项属于授权/合规资产，无 Owner 是明显风险。
- **Agency 数据偏薄**：Agency Notes 仅 4/12，Media owner 7/12，联系历史 7/12；Agency 的执行过程没有被完整记录，难以评估 agency 绩效。
- **Editor 覆盖 11/12，但有 1 家 white space**：The Independent 是唯一「Momcozy 未出现」的媒体；5 篇入选、5 篇未入选，榜单渗透的 win rate 约 50%，仍有提升空间。

### 4.7 SOP 落地优先级（供 GAP 汇总）

| 优先级 | 动作 | 直接解决的 GAP | 责任角色 |
|---|---|---|---|
| P0 | 把 Pitching Calendar 与 Editorial Opportunities 合成一张「战役-选题-媒体-产品-日期-Owner-Status」主表 | 两套类型体系不统一、2 月 EO 空窗、10 月 Calendar 少 | PR Manager |
| P0 | 补齐报道Tracker 的「品线 / 项目 / 产品」三个维度，统一项目命名 | 21% 未标注、品线 0%、campaign 与 coverage 映射不唯一 | 高雅静 + 全员 |
| P0 | 付费媒体表从 0 到 1：至少记录媒体、形式、金额、KPI、链接、披露 | 39 条 Paid 无 ROI、无法做付费/自然边际分析 | PR Manager |
| P1 | 榜单表补 Editor 联系历史、Agency Notes、状态、未入选原因 | 联系历史 58%、Agency Notes 33%、white space 未管理 | 郭薇/庄宇铃 + Agency |
| P1 | 媒体资源库清理 19 个占位字段，补 Owner/更新日期/适用场景 | 28 字段中仅 8 个有效、利用率 24% | PR Manager |
| P1 | PR资源库补 Owner/类型/适用场景，季度盘点 | 4 份无 Owner、6 份无类型、无场景关联 | 5 位 Owner |
| P2 | 事件类 SOP 增加 KPI/RSVP/差异化角度模板 | 7 条同题 Showroom 报道、事件报道同质化 | PR Manager |

---

**总体判断**：Momcozy 北美 PR 已经形成「大促 + 品牌节点 + 新品 + 榜单」四类稳定场景，Earned 占 77%，说明团队的核心能力在媒体关系与 editorial pitch，而不是付费投放。当前最大的 SOP 断点不在「做什么」，而在「计划表与结果表没有打通」——Pitching Calendar/Editorial Opportunities 是计划语言，报道Tracker 是结果语言，媒体资源库是主数据语言，三套语言之间缺少统一的项目、产品、媒体、Owner 键。把这三个键补齐，9 个场景的 SOP 才能从「经验驱动」变成「可复用、可衡量、可交接」的运营系统。