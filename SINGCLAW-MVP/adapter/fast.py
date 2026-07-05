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

# S9.5.2-B — Tool dispatcher gate. Default OFF so model tool_call doesn't hang SSE.
# MVP_TOOLS_ENABLED=1  → 二次 LLM 接 tool_result (S9.5.2-A dispatcher live)
# MVP_TOOLS_ENABLED=0  → tool_call 被识别 → SSE 立即 done, model 文本回复"工具暂未启用"
TOOLS_ENABLED = os.environ.get("MVP_TOOLS_ENABLED", "0") == "1"
# S9.5.2-B — tool_call 后等待 tool_result 最大秒数. 超时强制 done, 防 SSE 空等.
TOOL_WAIT_TIMEOUT_S = float(os.environ.get("MVP_TOOL_WAIT_TIMEOUT_S", "8"))

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


# ============================================================
# S9.5.2-A — Tool dispatcher (web_search / python_exec)
# ============================================================
# 协议同 parser: ALLOWED_TOOLS 白名单, 每个 dispatcher 返回 str (贴进 <tool_result>)
# 安全限制: python_exec 走 subprocess, 显式 timeout + 空 stdin + 受限 env.
import subprocess as _subprocess

MAX_TOOL_ROUNDS = int(os.environ.get("MVP_MAX_TOOL_ROUNDS", "3"))
TOOL_EXEC_TIMEOUT_S = float(os.environ.get("MVP_TOOL_EXEC_TIMEOUT_S", "15"))
WEB_SEARCH_MAX_RESULTS = int(os.environ.get("MVP_WEB_MAX_RESULTS", "5"))
WEB_SEARCH_TIMEOUT_S = float(os.environ.get("MVP_WEB_TIMEOUT_S", "10"))


async def _dispatch_web_search(args: dict) -> str:
    """duckduckgo HTML 抓取, 返回最多 5 条 (title / snippet / url). 零 API key 依赖."""
    query = (args or {}).get("query", "").strip()
    if not query:
        return "[web_search error] missing query"
    if len(query) > 200:
        query = query[:200]
    url = "https://html.duckduckgo.com/html/?q=" + httpx.QueryParams(q=query).get("q")
    try:
        async with httpx.AsyncClient(
            timeout=WEB_SEARCH_TIMEOUT_S,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; SingClaw/1.0)"},
        ) as client:
            r = await client.post(url, data={"q": query, "kl": "us-en"})
            if r.status_code != 200:
                return f"[web_search error] status={r.status_code}"
            html = r.text
    except Exception as e:
        return f"[web_search error] {type(e).__name__}: {str(e)[:200]}"
    # 解析 duckduckgo HTML: .result__a (title) + .result__snippet (text) + .result__url (href)
    results: list[str] = []
    # title + href
    title_re = re.compile(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL)
    snippet_re = re.compile(r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', re.DOTALL)
    titles = [(m.group(1), m.group(2)) for m in title_re.finditer(html)]
    snippets = [m.group(1) for m in snippet_re.finditer(html)]
    for i, (href, title_html) in enumerate(titles[:WEB_SEARCH_MAX_RESULTS]):
        title = re.sub(r"<[^>]+>", "", title_html).strip()
        title = re.sub(r"\s+", " ", title)[:200]
        snippet_raw = snippets[i] if i < len(snippets) else ""
        snippet = re.sub(r"<[^>]+>", "", snippet_raw).strip()
        snippet = re.sub(r"\s+", " ", snippet)[:400]
        # ddg redirect 解密 (uddg= 包裹真实 URL)
        if "uddg=" in href:
            try:
                href = httpx.QueryParams(href.split("?", 1)[-1]).get("uddg") or href
            except Exception:
                pass
        results.append(f"[{i+1}] {title}\n    {snippet}\n    {href[:200]}")
    if not results:
        return f"[web_search] no results for query={query!r}"
    return "[web_search results]\n" + "\n\n".join(results)


async def _dispatch_python_exec(args: dict) -> str:
    """受限 python3 -c 执行. 限制: timeout / 空 stdin / 清环境 / 不允许网络库名 (仅做静态 filter).
    Returns: stdout[:2000] + stderr[:1000] + 退出码. 复杂需求上 docker 不存在, 接受此粒度."""
    code = (args or {}).get("code", "")
    if not isinstance(code, str) or not code.strip():
        return "[python_exec error] missing code"
    if len(code) > 4000:
        return "[python_exec error] code too long (>4000 chars)"
    # 简易静态黑名单: import os/sys/subprocess/socket/urllib/requests → 拒绝
    blacklist = re.search(r"\b(import\s+(os|sys|subprocess|socket|urllib|requests|httpx|http|shutil|ctypes)|__import__\s*\(|open\s*\(|eval\s*\(|exec\s*\()", code)
    if blacklist:
        return f"[python_exec denied] blacklisted token: {blacklist.group(0)}"
    # 清干净环境, 只留 PATH/LANG
    safe_env = {k: v for k, v in os.environ.items() if k in ("PATH", "LANG", "LC_ALL", "TZ", "HOME")}
    try:
        proc = await asyncio.create_subprocess_exec(
            "python3", "-I", "-c", code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.DEVNULL,
            env=safe_env,
            cwd="/tmp",
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=TOOL_EXEC_TIMEOUT_S)
        except asyncio.TimeoutError:
            try: proc.kill()
            except Exception: pass
            return f"[python_exec timeout] killed after {TOOL_EXEC_TIMEOUT_S}s"
        out = (stdout or b"").decode("utf-8", errors="replace")[:2000]
        err = (stderr or b"").decode("utf-8", errors="replace")[:1000]
        rc = proc.returncode
        parts = []
        if out: parts.append(f"stdout:\n{out}")
        if err: parts.append(f"stderr:\n{err}")
        parts.append(f"exit_code: {rc}")
        return "\n".join(parts)
    except Exception as e:
        return f"[python_exec error] {type(e).__name__}: {str(e)[:200]}"


TOOL_DISPATCHERS: dict[str, "callable"] = {
    "web_search": _dispatch_web_search,
    "python_exec": _dispatch_python_exec,
}


async def execute_tool_call(call: dict) -> dict:
    """调度一个 tool_call, 返回 {name, args, result, error?, elapsed}."""
    name = call.get("name", "")
    args = call.get("args", {}) or {}
    fn = TOOL_DISPATCHERS.get(name)
    t0 = time.time()
    if not fn:
        return {"name": name, "args": args, "result": "", "error": f"unknown_tool:{name}", "elapsed": 0.0}
    try:
        result = await fn(args)
        return {"name": name, "args": args, "result": result, "elapsed": round(time.time() - t0, 2)}
    except Exception as e:
        return {"name": name, "args": args, "result": "", "error": f"{type(e).__name__}: {str(e)[:200]}", "elapsed": round(time.time() - t0, 2)}


# ============================================================
# S9.5.1 — Tool call parser (prompt-based, XML-tag ReAct)
# ============================================================
# 协议：模型输出 <tool_call>\n{json}\n</tool_call> 单行/多行均可,
# 可同段多 tool_call. 半截 tag 也尝试 best-effort 救回.

TOOL_CALL_RE = re.compile(
    r"<tool_call>\s*(\{.*?\})\s*</tool_call>",
    re.DOTALL,
)
# 半截 fallback: 模型写完 <tool_call>{...} 但忘了闭合 (实测 1/20 turn 会发生)
TOOL_CALL_HALF_RE = re.compile(
    r"<tool_call>\s*(\{[^\{\}]*(?:\{[^\{\}]*\}[^\{\}]*)*\})\s*$",
    re.DOTALL,
)

# Allowed tools whitelist (S9.5.2 dispatcher 会用同一个白名单, 防止 LLM 幻觉新 tool)
ALLOWED_TOOLS = {"web_search", "python_exec"}


def parse_tool_calls(raw: str) -> tuple[list[dict], str]:
    """从 raw 流式 buffer 里抽取所有 tool_call JSON, 剥离后返回 (calls, cleaned_text).

    返回:
      calls: [{"name": "web_search", "args": {...}, "raw": "..."}, ...]
      cleaned_text: 原始 text 去掉 tool_call 段 + tag 本身, 给用户当 visible 输出

    失败容错:
      - JSON 不合法 → 跳过该段, 留在 cleaned_text 原样
      - 字段不全 → 跳过
      - tool 名不在白名单 → 跳过
    """
    calls: list[dict] = []
    if not raw:
        return calls, raw

    # 1) 完整匹配
    matches = list(TOOL_CALL_RE.finditer(raw))
    if matches:
        # 收集所有 call, 然后从 raw 中按位置删
        for m in matches:
            payload_str = m.group(1)
            try:
                obj = json.loads(payload_str)
            except json.JSONDecodeError:
                continue
            name = obj.get("name")
            args = obj.get("args", {})
            if not isinstance(name, str) or name not in ALLOWED_TOOLS:
                continue
            if not isinstance(args, dict):
                args = {}
            calls.append({"name": name, "args": args, "raw": payload_str})
        # 完整段全部剥离
        cleaned = TOOL_CALL_RE.sub("", raw).strip()
        return calls, cleaned

    # 2) 半截 fallback: 末尾有 <tool_call>{... 但没闭合
    #    只在 raw 末尾尝试, 不要 greedy 全局匹配 (会误伤正常文字)
    half = TOOL_CALL_HALF_RE.search(raw)
    if half:
        payload_str = half.group(1)
        try:
            obj = json.loads(payload_str)
            name = obj.get("name")
            args = obj.get("args", {})
            if isinstance(name, str) and name in ALLOWED_TOOLS and isinstance(args, dict):
                calls.append({"name": name, "args": args, "raw": payload_str, "half": True})
                cleaned = raw[: half.start()].rstrip()
                return calls, cleaned
        except json.JSONDecodeError:
            pass

    return calls, raw


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
                # S9.5.2-B fix: provider 关 stream 不一定发 [DONE], 加 inactive timeout
                INACTIVE_TIMEOUT_S = float(os.environ.get("MVP_STREAM_INACTIVE_S", "2.0"))
                line_iter = resp.aiter_lines()
                last_event_at = time.time()
                while True:
                    if signal.is_set():
                        yield "error", {"reason": "aborted", "provider": label}
                        return
                    try:
                        anext_task = asyncio.create_task(line_iter.__anext__())
                        raw_line = await asyncio.wait_for(anext_task, timeout=INACTIVE_TIMEOUT_S)
                    except asyncio.TimeoutError:
                        # 2s 没新内容 → 推断 provider 静音
                        yield "done", {"reason": "inactive_timeout"}
                        return
                    except StopAsyncIteration:
                        # stream 收完
                        yield "done", {"reason": "stream_end"}
                        return
                    except httpx.HTTPError as e:
                        yield "error", {"reason": "http_error", "detail": str(e)[:300], "provider": label}
                        return
                    last_event_at = time.time()
                    if not raw_line:
                        continue
                    if not raw_line.startswith("data:"):
                        continue
                    payload_str = raw_line[len("data:"):].strip()
                    if payload_str == "[DONE]":
                        yield "done", {"reason": "data_done"}
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

    # S9.5.2-B — tool_call 等待超时守护 (gates TOOLS_ENABLED=0 场景)
    tool_wait_timed_out = False
    tool_call_pending_since_ref = {"v": None}  # 用 dict 容器避 nonlocal

    async def tool_wait_guard():
        while not signal.is_set():
            ts = tool_call_pending_since_ref["v"]
            if ts is not None and (time.time() - ts) > TOOL_WAIT_TIMEOUT_S:
                nonlocal_timed_out[0] = True
                signal.set()
                return
            await asyncio.sleep(0.3)

    nonlocal_timed_out = [False]
    tool_guard_task = asyncio.create_task(tool_wait_guard())

    raw_buffer = ""
    visible_buffer = ""
    # thinking_open=True means expect <think>...</think> wrap (minimax style).
    # thinking_open=False means content is direct text (deepseek style, no wrap).
    thinking_open = True
    thinking_closed = False
    chunk_idx = 0
    first_token_at = None
    chosen_provider = ""
    # S9.5.1 — 累积 tool_call, 每命中一次 emit SSE tool_call 事件
    pending_tool_calls: list[dict] = []
    emitted_call_signatures: set[str] = set()  # 去重, 避免重复事件
    # S9.5.2-B — tool_call 检测时间戳; 超时强制收尾
    tool_call_pending_since: float | None = None
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

                # S9.5.1 — scan raw_buffer for tool_call tags
                # 注意: 只在 thinking_closed 之后才允许出现 tool_call (避免 thinking 块被误解析)
                if thinking_closed:
                    calls, cleaned = parse_tool_calls(raw_buffer)
                    new_calls = []
                    for c in calls:
                        sig = f"{c['name']}::{json.dumps(c['args'], sort_keys=True)}"
                        if sig not in emitted_call_signatures:
                            emitted_call_signatures.add(sig)
                            new_calls.append(c)
                    if new_calls:
                        pending_tool_calls.extend(new_calls)
                        for c in new_calls:
                            # S9.5.1: 只 emit, 不执行 (dispatcher 在 S9.5.2 接入)
                            yield f"event: tool_call\ndata: {json.dumps({'name': c['name'], 'args': c['args'], 'elapsed': round(time.time() - t0, 2), 'half': c.get('half', False)})}\n\n".encode()
                        # S9.5.2-B — gate: 记时间戳; 若 dispatcher 没接 (TOOLS_ENABLED=0), 用后续 timeout 强制收尾
                        if tool_call_pending_since_ref["v"] is None:
                            tool_call_pending_since_ref["v"] = time.time()
                        # 把 raw_buffer 削到 cleaned (剥掉 tool_call 段), 避免重复解析
                        raw_buffer = cleaned
                        # visible_buffer 也同步削掉 tool_call 段 (tool_call 不应被用户当文本看到)
                        # 简化: 由于 cleaned 已经是 raw 的 tool_call-剥离版,
                        # 而 visible_buffer = raw_buffer 去 think 段, 这里只对增量清理.
                        # 实际处理: visible_buffer 始终是"已 emit 给用户的文本",
                        # tool_call 段因为没在 delta 里 emit 给用户, 所以 visible_buffer 里本就没有,
                        # 但保守起见, 重新跑一遍 strip.
                        visible_buffer = strip_tool_calls_visible(visible_buffer)
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
        if tool_guard_task:
            tool_guard_task.cancel()

    elapsed = time.time() - t0
    # S9.5.2-B — tool_wait_timed_out 标记 → 在 done 前补一个 tool_skipped 事件
    wait_was_timed_out = nonlocal_timed_out[0]
    if wait_was_timed_out:
        yield f"event: tool_skipped\ndata: {json.dumps({'reason': 'tools_disabled' if not TOOLS_ENABLED else 'timeout', 'pending': pending_tool_calls, 'waited_sec': round(elapsed, 2)})}\n\n".encode()
    final_reply = visible_buffer.strip()
    if not final_reply and thinking_open and not thinking_closed:
        # model never closed </think> — fall back to stripping raw
        final_reply = strip_thinking(raw_buffer).strip()
    # S9.5.1 — 防御性: final_reply 也剥一次 tool_call 段
    if final_reply:
        _, final_reply = parse_tool_calls(final_reply)
        final_reply = final_reply.strip()
    # S9.5.2-B — tool_call detected 但 dispatcher 未接 → final_reply 为空 → 补上 fallback reply
    # 这样 done 事件一定会发出, SSE 不会在 model 全部输出 tool_call 后藏起来
    if not final_reply:
        if pending_tool_calls and not TOOLS_ENABLED:
            final_reply = f"⚠️ 模型尝试调用工具 `{', '.join(set(c['name'] for c in pending_tool_calls))}` 但当前未启用 dispatcher。S9.5.2 开启 `MVP_TOOLS_ENABLED=1` 后可执行。"
        elif thinking_open and not thinking_closed:
            final_reply = strip_thinking(raw_buffer).strip() or "(空响应)"
        else:
            final_reply = "(空响应)"

    # ============================================================
    # S9.5.2-A — Round 2 (tool execution + second LLM)
    # ============================================================
    # 触发条件: TOOLS_ENABLED + 有 pending_tool_calls + 限轮数未超
    round_idx = 1
    # S9.5.2-A — client_disconnected 仅用于 skip persist_turn, 不干预 tool loop.
    # 避免 watch_disconnect fake signal 提前 break round2.
    client_disconnected = signal.is_set()
    while TOOLS_ENABLED and pending_tool_calls and round_idx <= MAX_TOOL_ROUNDS:
        if client_disconnected and not pending_tool_calls:
            break
        # 1) 并行执行 dispatcher
        tool_results: list[dict] = []
        results = await asyncio.gather(
            *[execute_tool_call(c) for c in pending_tool_calls],
            return_exceptions=True,
        )
        for r in results:
            if isinstance(r, Exception):
                tool_results.append({"name": "?", "result": "", "error": str(r)[:200], "elapsed": 0.0})
            else:
                tool_results.append(r)
        # S9.5.2-C — 持久化每条 tool_call (audit + 对话回放, 与 client 是否断开无关)
        if deps.get("persist_tool_call"):
            for call, res in zip(pending_tool_calls, tool_results):
                try:
                    deps["persist_tool_call"](
                        session_id,
                        round_idx,
                        call.get("name") or res.get("name") or "?",
                        call.get("args") or {},
                        res.get("result", "") or "",
                        res.get("error", "") or "",
                        float(res.get("elapsed", 0.0) or 0.0),
                    )
                except Exception as _e:
                    print(f"[warn] persist_tool_call failed: {_e}", flush=True)
        # 2) emit tool_result events
        for r in tool_results:
            yield f"event: tool_result\ndata: {json.dumps(r)}\n\n".encode()
        # 3) 构造回灌 messages: 把所有 tool_call + tool_result 拼成 user message
        #    使用 <tool_result> 协议块让模型识别
        tool_msg_parts: list[str] = []
        for call, res in zip(pending_tool_calls, tool_results):
            tool_msg_parts.append(
                f"<tool_result name=\"{call['name']}\">\n{res.get('result') or res.get('error') or '(空)'}\n</tool_result>"
            )
        tool_msg = "\n\n".join(tool_msg_parts)
        round2_messages = list(messages) + [{"role": "user", "content": tool_msg}]
        # 4) Round-2 二次 LLM 流 (复用 _stream_with_fallback)
        #    第二轮 thinking 用 deepseek 风格 (无 <think> wrap), 所以默认 thinking_open=False
        #    用新 signal 避免 round1 watch_disconnect fake signal 干扰 round2
        round2_signal = asyncio.Event()
        async def round2_watch_disconnect():
            while not round2_signal.is_set():
                if await request.is_disconnected():
                    round2_signal.set()
                    client_disconnected = True
                    return
                await asyncio.sleep(0.3)
        round2_abort_task = asyncio.create_task(round2_watch_disconnect())
        raw_buffer2 = ""
        visible_buffer2 = ""
        chunk_idx2 = 0
        round2_first_token_at = None
        round2_done = False
        round2_error = None
        round2_calls: list[dict] = []
        round2_reply = ""
        try:
            async for event_type, data in _stream_with_fallback(round2_messages, round2_signal):
                if event_type == "provider":
                    pass
                elif event_type == "delta":
                    content = data.get("content", "")
                    raw_buffer2 += content
                    if round2_first_token_at is None:
                        round2_first_token_at = time.time() - t0
                        yield f"event: first_token\ndata: {json.dumps({'at': round(round2_first_token_at, 3), 'round': round_idx + 1})}\n\n".encode()
                    visible_buffer2 += content
                    yield f"event: delta\ndata: {json.dumps({'i': chunk_idx2, 'text': content, 'elapsed': round(time.time() - t0, 2), 'round': round_idx + 1})}\n\n".encode()
                    chunk_idx2 += 1
                elif event_type == "error":
                    round2_error = data
                    yield f"event: error\ndata: {json.dumps({'round': round_idx + 1, **data})}\n\n".encode()
                    break
                elif event_type == "done":
                    round2_done = True
                    break
        finally:
            round2_signal.set()
            round2_abort_task.cancel()
                # 5) 取 round2 reply, 准备下一轮 / 结束
        #    使用 raw_buffer2 (包含 thinking 段), 不再用 visible_buffer2 (可能被重置)
        #    先剥 thinking, 再扫 tool_call (顺序很重要: thinking 包含 <think> 跟 tool_call tag 可能冲突)
        no_think = strip_thinking(raw_buffer2)
        round2_calls, round2_cleaned = parse_tool_calls(no_think)
        round2_reply = round2_cleaned.strip()
        if round2_calls:
            final_reply = round2_cleaned
            pending_tool_calls = round2_calls
        else:
            final_reply = round2_reply or visible_buffer2.strip() or final_reply
            pending_tool_calls = []  # 退出 while
            final_reply = round2_reply or visible_buffer2.strip() or final_reply
            pending_tool_calls = []  # 退出 while
        if round2_error and not final_reply:
            final_reply = f"(round2 错误: {round2_error.get('reason', 'unknown')})"
        round_idx += 1
        # 超轮保护: 超过 MAX_TOOL_ROUNDS 强制退出
        if round_idx > MAX_TOOL_ROUNDS and pending_tool_calls:
            final_reply = (final_reply or "").rstrip() + f"\n\n⚠️ 超过最大工具调用轮数 ({MAX_TOOL_ROUNDS})。"
            pending_tool_calls = []

    # S9.5.2-B — done event 永远 yield (signal 不跳过)
    if final_reply:
        # S9.5.2-D — 先 persist 拿 turn_id, 再 emit done event 带 turn_id 供前端 reload 关联
        # S9.5.2-D fix — 总是 persist (后端审计职责), 不受 client_disconnected 阻断
        agent_turn_id = 0
        try:
            persist_turn(session_id, "user", message, {"mode": "fast"})
            agent_turn_id = persist_turn(session_id, "agent", final_reply, {"mode": "fast", "elapsed_sec": round(elapsed, 2), "first_token_at": round(first_token_at or elapsed, 3), "chunks": chunk_idx, "pending_tool_calls": pending_tool_calls, "tools_enabled": TOOLS_ENABLED, "tool_skipped": wait_was_timed_out or (bool(pending_tool_calls) and not TOOLS_ENABLED), "rounds": round_idx})
        except Exception as _e:
            print(f"[warn] persist_turn failed: {_e}", flush=True)
        # S9.5.2-D — 回填最近 60s 内未关联的 tool_calls
        if agent_turn_id and deps.get("link_tool_calls_to_turn"):
            try:
                linked = deps["link_tool_calls_to_turn"](session_id, agent_turn_id)
                if linked:
                    print(f"[S9.5.2-D] linked {linked} tool_calls → agent_turn_id={agent_turn_id}", flush=True)
            except Exception as _e:
                print(f"[warn] link_tool_calls_to_turn failed: {_e}", flush=True)
        yield f"event: done\ndata: {json.dumps({'reply': final_reply, 'elapsed_sec': round(elapsed, 2), 'first_token_at': round(first_token_at or elapsed, 3), 'chunks': chunk_idx, 'session_id': session_id, 'mode': 'fast', 'pending_tool_calls': pending_tool_calls, 'tools_enabled': TOOLS_ENABLED, 'tool_skipped': wait_was_timed_out or (bool(pending_tool_calls) and not TOOLS_ENABLED), 'rounds': round_idx, 'turn_id': agent_turn_id})}\n\n".encode()


def strip_tool_calls_visible(text: str) -> str:
    """只剥完整 tool_call 段, 保留半截 fallback (避免误删用户文本).
    used by S9.5.1 防御性清理 visible_buffer."""
    return TOOL_CALL_RE.sub("", text).strip()


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
        "persist_tool_call": server.persist_tool_call,  # S9.5.2-C
        "link_tool_calls_to_turn": server.link_tool_calls_to_turn,  # S9.5.2-D
        "fetch_history": server.fetch_history,
        "fetch_tool_calls": server.fetch_tool_calls,  # S9.5.2-C
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