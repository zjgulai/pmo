# ADR-0009：PMO 飞书专家灵魂大脑、四层记忆检索与三棒一键交棒架构

- **状态**：已批准（Approved）
- **日期**：2026-11-04
- **决策人**：周健（PMO 总控 & 全栈研发）
- **适用范围**：`OGSM/ogsm-web/app/feishu_bot.py`、`OGSM/ogsm-web/app/memory.py`（严格遵守零网站污染约束，不改动 `pmo.luteos.com` 任何前端页面模板）

---

## 1. 背景与问题陈述（Context）

当前 `pmo.luteos.com` 已完成 V9 三级串联甘特图（14 产品 → 49 功能项 → 147 道三棒接力工序：`P1 吴雨宁 30% → P2 周健 40% → P3 刘华丽 30%`）与 `abi-pmo` 记忆空间（46 张四层 canonical 记忆卡 + 130 条显式图谱链接）。但在飞书群内 `@PMO` 时仍存在两个核心断层：
1. **缺乏专家大脑与记忆召回**：`app/feishu_bot.py` 仅支持固定关键词匹配（周报/甘特/探活/个人名），一旦群成员询问跨 Agent 交接契约、9 大主键规格、3 道 Gate 放行条件、12 条指标误用红线、业务导诊等开放式问题，直接回退为静态帮助菜单，未调用 `app/memory.py`。
2. **三棒交接缺乏飞书一键传递机制**：当吴雨宁完成 P1 或周健完成 P2 时，缺乏在飞书卡片上一键「完成本棒并 `@下一棒` 交接」的原子动作。

---

## 2. 核心架构决策（Decisions）

### 决策 D1：零网站污染原则（Zero Website Pollution）
- `pmo.luteos.com` 的 7 个 Web 页面保持纯粹、克制的只读管理视图，不挂载任何聊天浮窗或冗余问答组件。
- PMO 作为「垂直 Agent 矩阵产品项目管理专家」的全部交互、诊脉、守门裁决与交棒动作，100% 收敛在飞书机器人（`@PMO` 群聊与私聊）内完成。

### 决策 D2：双层混合大脑路由（Two-Tier Hybrid Brain）
- **Tier 1（毫秒级确定性执行层）**：
  - `@PMO 交棒 <功能名> [交接说明]` 及卡片按钮 `{"action": "pass_baton", "cap_id": ...}`：自动识别当前所处棒次（`P1 吴雨宁 <30%` → 跃迁至 `35% P2 周健`；`P2 周健 30~69%` → 跃迁至 `75% P3 刘华丽`；`P3 刘华丽 70~99%` → 跃迁至 `100% 已闭环`，同時校验 `evidence_url` 硬门禁），写入 `ChangeAuditLog` 并返回点名 `@下一棒` 的交接卡片。
  - `@PMO 自进化` / `@PMO 漏斗` / `@PMO 回写`：直接从数据库读取 `SopEvolutionCandidate`（周提问 `≥10次/周` 或打回 `≥3次`）与 `BusinessActionLedger`（`measuredActions`）实时排行榜。
  - 原有 `@PMO 待办` / `@PMO 周报` / `@PMO 里程碑` / `@PMO 探活` 保持毫秒级响应。
- **Tier 2（PMO 专家灵魂问答层：`Memory + SQL + LLM/Fallback`）**：
  - 当群成员输入任意非固定指令的自然语言问题时，自动执行三源融合诊断：
    1. **记忆召回（Memory Recall，≤2.5s）**：调用 `app/memory.py`（优先走宿主 `nmem` CLI，容器内无缝回退内置 46 张 canonical 四层记忆知识索引），检索与问题最相关的 Top 3 治理准则（八条红线、12 条指标误用 M01–M12、9 大主键、3 道 Gate、6 条交接链、四阶自进化标尺）。
    2. **实时 SQL 上下文注入（Live SQL Context，≤50ms）**：自动提取问题中涉及的产品/功能、三棒接力当前持棒人、起止排期、阻塞卡点与自进化频次。
    3. **双保險回答生成（LLM + Deterministic Structured Fallback）**：优先请求本地/环境变量配置的 OpenAI 兼容网关（如 Magpie `http://127.0.0.1:3425/v1/chat/completions`，超时 4.5s）按 `pmo_core_persona` 生成回答；若 LLM 网关不可达或超时，**0 报错无缝切换为「结构化专家诊断引擎」**，将召回的记忆条款、实时三棒排期与具体建议组装成标准深林绿飞书卡片返回。

### 决策 D3：赋能四类核心角色的专家诊断场景覆盖
1. **赋能吴雨宁（P1 需求/前端/架构 & 终棒推广）**：解答 9 大主键格式、6 条交接链 Handoff Packet 字段、四阶 Stage 4 固化条件。
2. **赋能周健（P2 全栈/飞书Bot/算法）**：解答 22 份历史资产复用路径、三棒上游 P1 交接状态、飞书 API 与多维表避坑指南。
3. **赋能刘华丽（P3 测试/Agent运营/控制台）**：解答 Stage 3 高频问题晋升阈值（`≥10次/周`、打回 `≥3次`、返工率 `<20%`）、`evidence_url` 验收门禁与 3 道 Gate 判定标准。
4. **赋能品牌市场部（需求协作方）**：提供 14 专家业务场景导诊（新品上市/选品/舆情/短视频找哪个 Agent）与 OGSM 指标防作弊守门裁决（拦截 M01–M12 误用）。

---

## 3. 执行与验收计划（Execution Plan）

| 阶段 | 任务项 | 交付物与验证标准 |
|---|---|---|
| **Step 1：记忆底座增强** | 升级 `app/memory.py`，支持 `nmem` CLI 优先 + 内置 canonical 知识库兜底（确保 Docker 容器内无 `nmem` 二进制时仍 100% 命中 46 张核心治理卡） | `test_pmo_nmem_recall.py` 全部通过 |
| **Step 2：飞书专家引擎开发** | 升级 `app/feishu_bot.py`：① 新增 `pass_baton` 一键交棒指令与按钮；② 新增 `@PMO 自进化` 漏斗查询；③ 新增 `answer_as_pmo_expert()` 专家问答主函数 | 单元测试覆盖吴雨宁/周健/刘华丽/品牌市场部 4 类典型提问与一键交棒状态机 |
| **Step 3：自动化测试验证** | 新增 `OGSM/ogsm-web/tests/test_feishu_pmo_expert.py`，执行全量单测 | `unittest discover` 100% 通过（0 failure） |
| **Step 4：生产热更新与真机验收** | 遵守 `AGENTS.md` 不重启容器/不重跑 seed 的硬约束，热更新 `pmo-web` worker 并调用 `/api/feishu/command` 实测推群验收 | 飞书群实测收到专家问答卡片与三棒交棒按钮 |
