# SI-Agent 产品侧现状简报（2026-10-31 快照）

> 真源：`tools/social/collect/capability_registry.json`（updated 2026-10-30）+ `Web/src/router/config.tsx`

## 能力注册表（40 项 = live 27 / limited 8 / not_built 5）

### live（27 项）
| 能力 | 说明 |
|---|---|
| TikTok 话题趋势 | Creative Center 主腿 + TikHub 备腿，Top100 rank/posts/views |
| TikTok 视频下载 | yt-dlp 落盘 + 媒体台账登记 + D17 权利门禁 |
| TikTok 视频搜索/评论 | Apify actor；评论采集目标条数 100 可配 |
| Reddit 帖子/评论 | TikHub Dynamic 三通道（搜索/子版/评论） |
| IG 达人/账号画像 | TikHub IG 达人搜索 + Exa people |
| YouTube 视频搜索 | — |
| LinkedIn 人物画像 | — |
| 竞品新闻与动态 | 竞品词典驱动 |
| 深度研究 | 通用版 |
| 深度研究（麦肯锡框架） | 结构化报告 |
| 视频四维解析（TK 专用） | 画面/转写/总结/下载 |
| TK 美国热门话题榜（7天） | 7 天窗口 |
| IG 趋势 Reels 采样 | 采样级 |
| TK 母婴垂类趋势榜 | 垂类过滤 |
| TK 音乐反查 | 音乐→视频 |
| hashtag → 视频下钻 | 话题→内容链 |
| 主题簇 → 视频下钻 | 聚类→内容链（JEV 栈 cluster_v2） |
| 竞品官号 → 视频下钻 | 竞品→内容链 |
| 趋势起量榜（池内持续起量） | 池内差分起量 |
| 意图识别层（14 类意图+槽位） | 群 bot 路由 |
| 多轮追问（B 假设确认+C 条件追问） | 群 bot |
| 业务数据管道（In→任务→采集→Out 回写） | 飞书表驱动采集 |
| 每日能力巡检 | 09:00 launchd，四层巡检 |
| 每日收尾编排 | 18:00，总结/待办/镜像同步 |
| 周报卡（6 维度，近 7 天滚动） | 自动生成 |
| 周报卡定时推送 | 周五 09:30 → 交付群 |
| 工作台部署一致性检查 | deploy preflight |

### limited（8 项）
评论主题与情绪解析（JEV 四表已建、回填面极小，仅工作台 /videos/:id 入口）/ Facebook 主页帖 / Threads 搜索 / X·Twitter 搜索 / AnySearch 垂直 / 视频四维解析（通用版，仅 TK 专用版是 live）/ IG hashtag 热度快照 / 变化提示 change-t-v1（shadow 灰度）

### not_built（5 项）
1. **TikTok 达人库**（粉丝量/签约状态筛选）
2. **KOL 画像与报价区间**
3. **品牌官方号互动声量统计**
4. **竞品定价与促销对比**
5. 通用问答兜底（t_general）

## 工作台前端路由（React+Vite，生产 social.luteos.com）
`/insights`（洞察首页）· `/insights/history` · `/analysis` · `/knowledge` · `/metrics` · `/capabilities` · `/reports` · `/trends` + `/trends/:id` · `/framework` · `/videos`（爆款列表）· `/videos/catalog` · `/videos/parse` · `/videos/results` · `/videos/:id`（含评论区洞察面板）· `/thresholds/versions`

## 群内 bot（飞书，Social-Leader/Emily 人格）
14 类意图路由 + 多轮追问 + 每日巡检推送（异常才推，不@）+ 每日收尾 + 周报卡推送 + 知识内化夜间管道（kb_nightly）

## 近期产品方向（用户 2026-10-30 拍板）
产品从「半技术半业务」转向 **业务组织 / 业务场景 / 营销 4P** 视角，以业务问题为导向盘点工作台功能、按奥卡姆剃刀拆分板块。
