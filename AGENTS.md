# AGENTS.md — ABI PMO 管理站

本仓库是 ABI 品牌 & 营销域 PMO 管理站与 OGSM 治理材料。任何编码 Agent 在开始工作前，先按下面约定加载长期记忆。

## 会话启动

1. 运行 `nmem context --space abi-pmo --agent-id pmo-guardian`，加载 Space Rules 与 Working Memory。
2. 涉及 OGSM 口径、指标、Gate、14 个 Agent 阶段或证据的问题，先检索：
   `nmem memories search "<query>" --space abi-pmo -n 3`
3. 记忆检索失败、离线或超时：不阻塞主任务，把“未检索到”写明，不猜。
4. 会话结束前，只把新产生的决策、口径、避坑、画像写入 `abi-pmo`；原始日志、聊天、表格行、未批准草稿不写。

## 硬约束

- 一个 G 只认一个结算数字；进度不是结果；没有基线的承诺不成立。
- 无回执不等于通过；无 `evidence_url` 不得标“已验证”。
- 不 import 14 个专家工作台业务代码，不写它们的数据库；只读 API/报告/飞书表。
- 不重启 `pmo-web`/Postgres/飞书长连接；不重跑 `app.seed`、迁移或全量重建索引；不影响并行后台任务。
- 生产变更走 `/admin` 或迁移脚本，并留 `change_audit_log`；改动前先确认最近一次备份成功。

## 记忆资产

- 真源：`OGSM/OGSM-v1-整合版-20261102.md`（批准口径）。
- 方案与执行包：`OGSM/ogsm-web/docs/memory/`（46 张记忆卡、18 个 Ticket、本体草案、真源清单）。
- 蒸馏脚本：`OGSM/ogsm-web/docs/memory/distill_memories_to_nmem.py`（幂等 upsert，改内容后重跑即可）。
