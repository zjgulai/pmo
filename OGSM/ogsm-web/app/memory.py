"""PMO 持久记忆检索（读侧轻量 Recall）。

设计约束（SOP §一.4 / §五.4）：
- 严格 3 秒超时；失败、离线、无匹配时静默返回空串，绝不阻塞主链路。
- 只读取指定 Space（默认 abi-pmo），不做任何写入。
- 可通过环境变量覆盖：NMEM_CLI_PATH、NMEM_SPACE。
"""
from __future__ import annotations

import json
import os
import subprocess

DEFAULT_SPACE = "abi-pmo"


def recall_durable_memories(query: str, limit: int = 2, min_score: float = 0.5,
                            space: str | None = None,
                            timeout_seconds: float = 3.0) -> str:
    """从 Nowledge Mem 检索与问题强相关的 PMO 口径、红线与避坑经验。

    失败、离线或无匹配时返回空串（优雅降级，不抛异常）。
    """
    if not query or not query.strip():
        return ""
    try:
        cli = os.environ.get("NMEM_CLI_PATH", "nmem")
        target = space or os.environ.get("NMEM_SPACE", DEFAULT_SPACE)
        cmd = [cli, "--json", "memories", "search", query.strip()[:100],
               "--space", target, "-n", str(max(1, int(limit)))]
        res = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=timeout_seconds)
        if res.returncode != 0:
            return ""
        data = json.loads(res.stdout)
        if isinstance(data, list):
            items = data
        else:
            items = data.get("items") or data.get("memories") or []
        blocks = []
        for m in items:
            score = float(m.get("score") or 0.0)
            if score < min_score:
                continue
            title = (m.get("title") or "").strip()
            content = (m.get("content") or m.get("snippet") or "").strip()
            if title and content:
                blocks.append(f"• 【{title}】(匹配度 {score:.2f})\n{content}")
        if not blocks:
            return ""
        return "【PMO 持久记忆（口径/红线/避坑）】\n" + "\n\n".join(blocks)
    except Exception:  # noqa: BLE001 - 读侧生命线：任何异常都必须静默降级
        return ""
