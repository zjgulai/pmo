#!/usr/bin/env python3
"""B 批：对缺少实体连接的 canonical 记忆逐张做 KG preview + apply。

前置：
- nmem provider `openai_compatible:magpie-proxy` 指向本机转换代理 3435；
- 代理与 Magpie/`vod/gpt-5.3-chat` 可用。

用法：
    OGSM/ogsm-web/.venv/bin/python OGSM/ogsm-web/docs/memory/batch_extract_entities.py --run
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
import urllib.request

API = "http://127.0.0.1:14242"
SPACE = "abi-pmo"


def http_json(method: str, path: str, body: dict | None = None, timeout: int = 240):
    data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read())


def canonical_ids() -> list[str]:
    res = subprocess.run(["nmem", "memories", "list", "--space", SPACE, "-n", "200", "--json"],
                         capture_output=True, text=True, timeout=60)
    d = json.loads(res.stdout)
    items = d if isinstance(d, list) else d.get("items") or d.get("memories") or []
    return [m["id"] for m in items if m.get("source") == "pmo-distill"]


def has_entities(mid: str) -> bool:
    res = subprocess.run(["nmem", "graph", "expand", mid],
                         capture_output=True, text=True, timeout=30)
    return "Mentions entity" in res.stdout


def extract_one(mid: str) -> tuple[int, str]:
    body = {"extraction_level": "expert", "use_remote_llm": True,
            "preferred_language": "zh", "force_reextraction": True}
    try:
        status, preview = http_json("POST", f"/memories/{mid}/extract-kg/preview", body)
    except Exception as e:  # noqa: BLE001
        return 0, f"preview-error {str(e)[:120]}"
    if status != 200:
        return status, f"preview-http {status} {str(preview)[:120]}"
    entities = preview.get("entities") or []
    rels = preview.get("relationships") or []
    if not entities and not rels:
        return 0, "empty"
    apply_body = {"entities": entities, "relationships": rels,
                  "extraction_confidence": preview.get("extraction_confidence", 0.8)}
    try:
        status2, applied = http_json("POST", f"/memories/{mid}/extract-kg/apply", apply_body)
    except Exception as e:  # noqa: BLE001
        return 0, f"apply-error {str(e)[:120]}"
    ok = status2 == 200 and (applied.get("success") is not False)
    return 0 if ok else status2, f"entities={len(entities)} rels={len(rels)} apply={status2} ok={ok}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    ids = canonical_ids()
    pending = [m for m in ids if not has_entities(m)]
    if args.limit:
        pending = pending[: args.limit]
    print(f"canonical={len(ids)} 待实体抽取={len(pending)}")
    if not args.run:
        print("\n".join(pending))
        return

    ok, fail = [], []
    for i, mid in enumerate(pending, 1):
        t0 = time.time()
        code, msg = extract_one(mid)
        dt = int(time.time() - t0)
        print(f"[{i}/{len(pending)}] {mid} {dt}s code={code} {msg}", flush=True)
        (ok if code == 0 else fail).append(mid)
        time.sleep(1)
    print(f"\n完成：{len(ok)} 成功 / {len(fail)} 失败")
    print("失败：", fail)


if __name__ == "__main__":
    main()
