#!/usr/bin/env python3
"""Magpie transform proxy for nmem KG extraction.

Why: nmem sends a complex `response_format: json_schema`; Magpie's `vod`
upstream rejects the real KG request with 502. This proxy converts that to
`json_object` and injects the original schema into the system prompt, so a
model like `vod/gpt-5.3-chat` can still return the required JSON shape.

Run:
    python3 magpie_transform_proxy.py
Listen: 127.0.0.1:3435
Upstream: http://127.0.0.1:3425/v1/chat/completions
Log: /tmp/magpie_transform_proxy.log
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UPSTREAM = "http://127.0.0.1:3425/v1/chat/completions"
LOG = "/tmp/magpie_transform_proxy.log"


def log(obj: dict) -> None:
    obj = {"t": time.strftime("%H:%M:%S"), **obj}
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False)[:4000] + "\n")


def inject_schema(body: dict, schema: dict) -> None:
    text = ("\n\nReturn ONE JSON object only, no markdown, conforming to this JSON Schema:\n"
            + json.dumps(schema, ensure_ascii=False))
    msgs = body.get("messages") or []
    for m in msgs:
        if isinstance(m, dict) and m.get("role") == "system":
            c = m.get("content")
            if isinstance(c, str):
                m["content"] = c + text
            elif isinstance(c, list):
                c.append({"type": "text", "text": text})
            return
    msgs.insert(0, {"role": "system", "content": text})
    body["messages"] = msgs


def sse_wrap(payload: dict) -> bytes:
    choice = (payload.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    content = msg.get("content") or ""
    chunk = {
        "id": payload.get("id", "chatcmpl-proxy"),
        "object": "chat.completion.chunk",
        "created": payload.get("created", int(time.time())),
        "model": payload.get("model", ""),
        "choices": [{"index": 0, "delta": {"content": content},
                     "finish_reason": choice.get("finish_reason", "stop")}],
    }
    return (f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            "data: [DONE]\n\n").encode()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def do_POST(self):
        if self.path.rstrip("/") != "/v1/chat/completions":
            self.send_error(404)
            return
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n)
        t0 = time.time()
        try:
            body = json.loads(raw)
        except Exception as e:
            self.send_error(400, str(e))
            return

        stream = bool(body.get("stream"))
        rf = body.get("response_format")
        transformed = False
        if isinstance(rf, dict) and rf.get("type") == "json_schema":
            js = rf.get("json_schema") or {}
            schema = js.get("schema")
            if isinstance(schema, dict):
                inject_schema(body, schema)
                body["response_format"] = {"type": "json_object"}
                transformed = True
        body["stream"] = False  # upstream non-stream; we wrap if client asked stream

        log({"phase": "req", "bytes": len(raw), "model": body.get("model"),
             "stream": stream, "transformed": transformed,
             "max_tokens": body.get("max_tokens"),
             "messages": len(body.get("messages") or []),
             "chars": sum(len(str(m.get("content") or "")) for m in body.get("messages") or []),
             "tools": len(body.get("tools") or [])})

        data = json.dumps(body, ensure_ascii=False).encode()
        req = urllib.request.Request(UPSTREAM, data=data, method="POST",
                                     headers={"Content-Type": "application/json"})
        auth = self.headers.get("Authorization")
        if auth:
            req.add_header("Authorization", auth)
        try:
            with urllib.request.urlopen(req, timeout=240) as r:
                resp = r.read()
                status = r.status
        except urllib.error.HTTPError as e:
            resp = e.read()
            status = e.code
        except Exception as e:  # noqa: BLE001
            resp = json.dumps({"error": {"message": str(e)}}).encode()
            status = 599

        log({"phase": "resp", "status": status, "ms": int((time.time() - t0) * 1000),
             "head": resp[:300].decode("utf-8", "replace")})

        if status != 200:
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)
            return

        if stream:
            try:
                payload = json.loads(resp)
                out = sse_wrap(payload)
            except Exception:
                out = resp
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp)))
        self.end_headers()
        self.wfile.write(resp)


if __name__ == "__main__":
    log({"phase": "start"})
    ThreadingHTTPServer(("127.0.0.1", 3435), Handler).serve_forever()
