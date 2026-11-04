# PMO 记忆与知识图谱 · 执行包

本目录是《ABI PMO 管理站 · 记忆系统与知识图谱建设方案 v1.0》的执行包。当前状态：**已执行（2026-11-04）**，结果见 `EXECUTION-REPORT.md`。

## 文件

| 文件 | 用途 |
|---|---|
| `PMO-MEMORY-KG-PLAN.md` | 完整方案：基线、四层记忆、Library、本体、运行时、执行计划、验收 |
| `EXECUTION-REPORT.md` | 执行报告：交付结果、SOP 8 条、Golden Query 实测、治理动作、未完成项 |
| `memory_cards.csv` | 46 张 canonical 记忆卡目录（已全部写入 `abi-pmo`） |
| `TICKETS.csv` | 18 个 Ticket + status/evidence（17 done，1 partial） |
| `ontology_patch.draft.json` | 14 类对象 + 16 类关系（已 apply，revision 7） |
| `sources.yaml` | 10 份 Library 真源、排除项、解析检查 |
| `distill_memories_to_nmem.py` | 幂等蒸馏脚本；改内容后重跑即可 upsert |
| `link_memories_to_graph.py` | A 批显式语义链接脚本（幂等）；已写入 130 条链接，46/46 记忆级连通 |

## 运行态

- Space：`abi-pmo`（strict，10 sources）
- Agent：`pmo-guardian`（默认空间 `abi-pmo`）
- Rules：`pmo_core_persona`(100) / `pmo_repo_boundary`(90) / `pmo_memory_write_discipline`(80)
- 记忆：46 canonical + library 抽取记忆（持续增加）；15 条重复抽取已 supersede + archive
- Library：10/10 切片成功（6 extracted / 4 indexed，错误 0；`extracted` 按现场修正亦为成功态）
- 图谱：46/46 记忆级连通（130 条显式链接）；实体级 18/46（LLM 抽取部分完成，`autoKGExtraction` 暂停）
- 读侧：`OGSM/ogsm-web/app/memory.py`，3 秒超时 + 静默降级；测试 `OGSM/ogsm-web/tests/test_pmo_nmem_recall.py` 9/9

## 常用命令

```bash
# 开机上下文
nmem context --space abi-pmo --agent-id pmo-guardian

# 检索
nmem memories search "G1 的结算指标是什么" --space abi-pmo -n 3

# 重新蒸馏（幂等）
OGSM/ogsm-web/.venv/bin/python OGSM/ogsm-web/docs/memory/distill_memories_to_nmem.py --run

# 单元测试
OGSM/ogsm-web/.venv/bin/python -m unittest discover -s OGSM/ogsm-web/tests -v
```

## 硬约束

1. 只建一个 `abi-pmo` Space，14 个 Agent 是实体，不是 14 个空间。
2. 所有 `.md` 入库前复制为 `.markdown`，避免 MIME 误判。
3. 不把草稿、日志、聊天、表格行、报告 HTML 直接写进记忆。
4. 每条记忆必须带来源；同主题只保留一个 canonical ID，更新用 upsert。
5. 记忆检索必须 3 秒超时 + 全捕获降级；产品主链路不得依赖 nmem。
6. 本体优先 space scope；apply 前先校验 JSON。
7. 不重启 pmo-web/Postgres/飞书长连接；不重跑 seed/迁移/全量 reindex，不影响并行后台任务。
