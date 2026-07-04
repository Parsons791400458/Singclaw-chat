"""
SINGCLAW-MVP Fast Path (S7) — direct LLM provider streaming
============================================================
跳过 OpenClaw CLI，直接调 minimax 的 OpenAI 兼容 chat/completions 端点。
目标: 首 token ≤ 1s (用户体感 3s 内), 真 token-by-token SSE。

注意: 这个文件被 server.py 在末尾 import, 所以不能从 server 顶部 import 顶层对象
(循环依赖). register_routes 内部用 import server 模块 + 直接引用 server.app / 等。
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import time

import httpx

# Import Request directly so FastAPI's annotation resolution works.
# (Avoiding the server.Request indirection because of PEP 563 string annotations
# making type lookup brittle.)
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

# Provider chain (S9.1): primary + fallbacks
# Format: (base_url, api_key, model_id, label)
DEFAULT_PROVIDERS = [
    ("https://api.minimaxi.com/v1", "sk-cp-TabsfUSfco3P4JMR2sfD7voaQR-HTAUEt6xQuw_ArzHtZc2P1X2Ga5QodgK1ShWGFeLjM5oi_XjsHY1p26H_OTR3XLvCjsSLkHCKA_e7cL2IA8dCGIccwLQ", "MiniMax-M3", "minimax-M3"),
    ("https://api.deepseek.com/v1", "<REDACTED-KEY>", "deepseek-v4-pro", "deepseek-v4-pro"),
]

def _load_providers() -> list:
    """Load provider chain from env MVP_PROVIDER_CHAIN (JSON) or default."""
    raw = os.environ.get("MVP_PROVIDER_CHAIN", "").strip()
    if raw:
        try:
            arr = json.loads(raw)
            return [(p["base_url"], p["api_key"], p["model"], p.get("label", p["model"])) for p in arr]
        except Exception:
            pass
    return DEFAULT_PROVIDERS

PROVIDERS = _load_providers()
FAST_TIMEOUT_S = int(os.environ.get("MVP_FAST_TIMEOUT_S", "60"))

# thinking block regex (server-side strip)
THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)

# SingClaw MVP system prompt — loaded from file at import time
def _load_system_prompt() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, "prompts", "singclaw-mvp-system.md"),
        os.environ.get("MVP_SYSTEM_PROMPT_FILE", ""),
    ]
    for path in candidates:
        if path and os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if content:
                return content
    # Fallback if file missing
    return "你是 SingClaw MVP 助手。专业、数据驱动、决断。用中文回复。"

SYSTEM_PROMPT = _load_system_prompt()


def strip_thinking(text: str) -> str:
    return THINK_RE.sub("", text).strip()


async def _stream_provider(provider, messages, signal):
    """Stream from one provider. Yields (event_type, data_dict, provider_label).
    provider: (base_url, api_key, model, label) tuple.
    """
    base_url, api_key, model, label = provider
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 4096,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=FAST_TIMEOUT_S) as client:
            async with client.stream(
                "POST",
                f"{base_url}/chat/completions",
                json=payload,
                headers=headers,
            ) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    yield "error", {"status": resp.status_code, "body": body.decode("utf-8", errors="replace")[:400], "provider": label}
                    return
                async for raw_line in resp.aiter_lines():
                    if signal.is_set():
                        yield "error", {"reason": "aborted", "provider": label}
                        return
                    if not raw_line:
                        continue
                    if not raw_line.startswith("data:"):
                        continue
                    payload_str = raw_line[len("data:"):].strip()
                    if payload_str == "[DONE]":
                        yield "done", {}
                        return
                    try:
                        obj = json.loads(payload_str)
                    except json.JSONDecodeError:
                        continue
                    choices = obj.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    # Some providers (deepseek-v4-pro) put text in reasoning_content; others (minimax) in content
                    content = delta.get("content") or delta.get("reasoning_content")
                    if content:
                        yield "delta", {"content": content}
    except httpx.HTTPError as e:
        yield "error", {"reason": "http_error", "detail": str(e)[:300], "provider": label}
    except asyncio.TimeoutError:
        yield "error", {"reason": "timeout", "provider": label}


async def _stream_with_fallback(messages, signal):
    """Try each provider in chain; on first content delta, commit to that provider.
    On pre-stream errors (auth/4xx/timeout/network), silently try next provider.
    Yields ('provider', label) before first delta of the chosen provider.
    """
    last_error = None
    for provider in PROVIDERS:
        label = provider[3]
        got_any_chunk = False
        first_event = True
        try:
            async for event_type, data in _stream_provider(provider, messages, signal):
                if first_event and event_type == "error":
                    # Pre-stream error: try next provider, don't expose to caller
                    last_error = data
                    first_event = False
                    break
                first_event = False
                if event_type == "delta" and not got_any_chunk:
                    got_any_chunk = True
                    yield "provider", {"label": label}
                yield event_type, data
                if event_type == "done":
                    return
            else:
                # async for completed without break — provider finished cleanly
                if got_any_chunk:
                    return
        except Exception as e:
            last_error = {"reason": "exception", "detail": str(e)[:200], "provider": label}
            continue
        # If we get here without 'done' but got chunks, return
        if got_any_chunk:
            return
        # No chunks: try next provider
    yield "error", {"reason": "all_providers_failed", "last_error": last_error}


def _build_messages(history, user_msg):
    """从 SQLite turns 表读历史, 转 OpenAI messages 格式."""
    msgs = []
    for h in history:
        role = h["role"]
        if role == "system":
            msgs.append({"role": "system", "content": h["content"]})
        elif role == "user":
            msgs.append({"role": "user", "content": h["content"]})
        elif role == "agent":
            msgs.append({"role": "assistant", "content": strip_thinking(h["content"])})
    msgs.append({"role": "user", "content": user_msg})
    return msgs


async def _sse_fast(session_id, message, request, deps):
    """Fast-path SSE stream from minimax directly."""
    persist_turn = deps["persist_turn"]
    fetch_history = deps["fetch_history"]

    t0 = time.time()
    yield f"event: start\ndata: {json.dumps({'session_id': session_id, 'ts': t0, 'mode': 'fast'})}\n\n".encode()

    history = fetch_history(session_id, limit=20)
    messages = _build_messages(history, message)
    if not any(m["role"] == "system" for m in messages):
        messages.insert(0, {
            "role": "system",
            "content": SYSTEM_PROMPT,
        })

    signal = asyncio.Event()

    async def watch_disconnect():
        while not signal.is_set():
            if await request.is_disconnected():
                signal.set()
                return
            await asyncio.sleep(0.3)

    abort_task = asyncio.create_task(watch_disconnect())

    raw_buffer = ""
    visible_buffer = ""
    # thinking_open=True means expect <think>...</think> wrap (minimax style).
    # thinking_open=False means content is direct text (deepseek style, no wrap).
    thinking_open = True
    thinking_closed = False
    chunk_idx = 0
    first_token_at = None
    chosen_provider = ""
    try:
        async for event_type, data in _stream_with_fallback(messages, signal):
            if event_type == "provider":
                # S9.1: notify which model is actually serving this turn
                chosen_provider = data.get("label", "")
                yield f"event: provider\ndata: {json.dumps(data)}\n\n".encode()
                # deepseek-v4-pro streams reasoning_content without <think> wrapper,
                # so we switch to direct emit mode (no thinking strip)
                if "deepseek" in chosen_provider.lower() or "v4-pro" in chosen_provider.lower():
                    thinking_open = False
                    thinking_closed = True
            elif event_type == "delta":
                content = data.get("content", "")
                raw_buffer += content
                # Try to find </think> closing tag
                if thinking_open and "</think>" in raw_buffer:
                    thinking_closed = True
                    thinking_open = False
                    # take everything after first </think>
                    after = raw_buffer.split("</think>", 1)[1]
                    if after:
                        if first_token_at is None:
                            first_token_at = time.time() - t0
                            yield f"event: first_token\ndata: {json.dumps({'at': round(first_token_at, 3)})}\n\n".encode()
                        visible_buffer += after
                        yield f"event: delta\ndata: {json.dumps({'i': chunk_idx, 'text': after, 'elapsed': round(time.time() - t0, 2)})}\n\n".encode()
                        chunk_idx += 1
                elif thinking_closed:
                    # normal visible content
                    if first_token_at is None:
                        first_token_at = time.time() - t0
                        yield f"event: first_token\ndata: {json.dumps({'at': round(first_token_at, 3)})}\n\n".encode()
                    visible_buffer += content
                    yield f"event: delta\ndata: {json.dumps({'i': chunk_idx, 'text': content, 'elapsed': round(time.time() - t0, 2)})}\n\n".encode()
                    chunk_idx += 1
                # else: still in <think>...</think>, buffer but don't emit
            elif event_type == "error":
                yield f"event: error\ndata: {json.dumps(data)}\n\n".encode()
                signal.set()
                break
            elif event_type == "done":
                break
    finally:
        signal.set()
        if abort_task:
            abort_task.cancel()

    elapsed = time.time() - t0
    final_reply = visible_buffer.strip()
    if not final_reply and thinking_open and not thinking_closed:
        # model never closed </think> — fall back to stripping raw
        final_reply = strip_thinking(raw_buffer).strip()
    if final_reply and not signal.is_set():
        yield f"event: done\ndata: {json.dumps({'reply': final_reply, 'elapsed_sec': round(elapsed, 2), 'first_token_at': round(first_token_at or elapsed, 3), 'chunks': chunk_idx, 'session_id': session_id, 'mode': 'fast'})}\n\n".encode()
        persist_turn(session_id, "user", message, {"mode": "fast"})
        persist_turn(session_id, "agent", final_reply, {"mode": "fast", "elapsed_sec": round(elapsed, 2), "first_token_at": round(first_token_at or elapsed, 3), "chunks": chunk_idx})


# ---- Routes ----
def register_routes(app):
    """Mount fast-path routes onto the given FastAPI app."""
    # Late imports to avoid circular import at module load time
    import server

    FastAPI = server.FastAPI
    Request = server.Request
    HTTPException = server.HTTPException
    JSONResponse = server.JSONResponse
    StreamingResponse = server.StreamingResponse

    deps = {
        "persist_turn": server.persist_turn,
        "fetch_history": server.fetch_history,
        "_new_session_id": server._new_session_id,
        "check_access": server.check_access,
        "audit_access": server.audit_access,
        "check_rate": server.check_rate,
    }

    @app.get("/v1/mvp/chat/fast/health")
    async def fast_health():
        """Probe all providers in chain, report each."""
        results = []
        for base_url, api_key, model, label in PROVIDERS:
            t0 = time.time()
            try:
                async with httpx.AsyncClient(timeout=10) as c:
                    r = await c.post(
                        f"{base_url}/chat/completions",
                        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                        json={"model": model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5, "stream": False},
                    )
                    latency = time.time() - t0
                    ok = r.status_code == 200
                    snippet = (r.json().get("choices", [{}])[0].get("message", {}).get("content", ""))[:80] if ok else None
                    results.append({"label": label, "model": model, "ok": ok, "status": r.status_code, "latency_sec": round(latency, 3), "snippet": snippet})
            except Exception as e:
                results.append({"label": label, "model": model, "ok": False, "error": str(e)[:200]})
        any_ok = any(r.get("ok") for r in results)
        return JSONResponse({
            "ok": any_ok,
            "mode": "fast",
            "chain_size": len(PROVIDERS),
            "providers": results,
        })

    @app.post("/v1/mvp/chat/fast")
    async def chat_fast(request: Request):
        ip = request.client.host if request.client else "unknown"
        body_bytes = await request.body()
        try:
            body = json.loads(body_bytes) if body_bytes else {}
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="invalid_json")
        message = (body or {}).get("message")
        session_id = (body or {}).get("session_id") or deps["_new_session_id"]()
        if not isinstance(message, str) or not message:
            raise HTTPException(status_code=400, detail="message_required")

        ok, reason = deps["check_access"](request)
        if not ok:
            deps["audit_access"](ip, session_id, request.headers.get("authorization", "").replace("Bearer ", ""), False, reason)
            raise HTTPException(status_code=401, detail={"error": "access_denied", "reason": reason})

        rl = deps["check_rate"](ip, session_id)
        if rl:
            return rl

        return StreamingResponse(
            _sse_fast(session_id, message, request, deps),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "X-Accel-Buffering": "no",
            },
        )

    @app.post("/v1/mvp/chat/fast/nonstream")
    async def chat_fast_nonstream(request: Request):
        ip = request.client.host if request.client else "unknown"
        body_bytes = await request.body()
        try:
            body = json.loads(body_bytes) if body_bytes else {}
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="invalid_json")
        message = (body or {}).get("message")
        session_id = (body or {}).get("session_id") or deps["_new_session_id"]()
        if not isinstance(message, str) or not message:
            raise HTTPException(status_code=400, detail="message_required")

        ok, reason = deps["check_access"](request)
        if not ok:
            deps["audit_access"](ip, session_id, request.headers.get("authorization", "").replace("Bearer ", ""), False, reason)
            raise HTTPException(status_code=401, detail={"error": "access_denied", "reason": reason})
        rl = deps["check_rate"](ip, session_id)
        if rl:
            return rl

        history = deps["fetch_history"](session_id, limit=20)
        messages = _build_messages(history, message)
        if not any(m["role"] == "system" for m in messages):
            messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

        t0 = time.time()
        chosen = None
        r = None
        last_err = None
        for base_url, api_key, model, label in PROVIDERS:
            try:
                async with httpx.AsyncClient(timeout=FAST_TIMEOUT_S) as c:
                    r = await c.post(
                        f"{base_url}/chat/completions",
                        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                        json={"model": model, "messages": messages, "stream": False, "temperature": 0.7, "max_tokens": 4096},
                    )
                if r.status_code == 200:
                    chosen = (base_url, model, label)
                    break
                last_err = f"{label} status={r.status_code}"
            except Exception as e:
                last_err = f"{label}: {str(e)[:200]}"
                continue
        if r is None or chosen is None:
            raise HTTPException(status_code=502, detail=f"all_providers_failed: {last_err}")
        elapsed = time.time() - t0
        body = r.json()
        choices = body.get("choices") or []
        if not choices:
            raise HTTPException(status_code=502, detail="no_choices")
        msg = choices[0].get("message") or {}
        raw = msg.get("content") or msg.get("reasoning_content") or ""
        reply = strip_thinking(raw)
        deps["persist_turn"](session_id, "user", message, {"mode": "fast_nonstream"})
        deps["persist_turn"](session_id, "agent", reply, {"mode": "fast_nonstream", "elapsed_sec": round(elapsed, 2), "provider": chosen[2]})
        return JSONResponse({
            "session_id": session_id,
            "reply": reply,
            "elapsed_sec": round(elapsed, 2),
            "mode": "fast_nonstream",
            "model": chosen[1],
            "provider": chosen[2],
            "first_token_at": round(elapsed, 3),
        })