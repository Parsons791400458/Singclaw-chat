# SingClaw MVP Adapter — Database Schema
**生成时间**: 2026-07-05 13:05 UTC
**Location**: `/root/.openclaw/workspace/SINGCLAW-MVP/adapter/`

---

## Overview

Adapter 用 SQLite (`db.sqlite3`) 持久化三个东西：

| Table | Purpose |
|---|---|
| `turns` | Chat 历史 (user / agent / system) |
| `tool_calls` | Tool 调用审计 |
| `access_audit` | 鉴权 / 限流事件 |

---

## 1. `turns` 表

```sql
CREATE TABLE IF NOT EXISTS turns (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id  TEXT    NOT NULL,
  role        TEXT    NOT NULL,         -- 'user' / 'agent' / 'system'
  content     TEXT    NOT NULL,
  created_at  REAL    DEFAULT (strftime('%s','now')),
  meta_json   TEXT                        -- JSON: 速率 / elapsed_sec / mode 等
);
CREATE INDEX IF NOT EXISTS idx_turns_session_id ON turns(session_id);
```

**字段含义**:
- `id`: DB rowid，也是 frontend 用的 turn_id
- `session_id`: 客户端给的 UUID
- `role`: 必须是 `'user'`, `'agent'`, `'system'` 之一
- `content`: 完整文字（thinking block 在写入前已被 `strip_thinking` regex 剥除）
- `created_at`: epoch seconds（REAL 类型）
- `meta_json`: JSON 字符串，含 `mode=fast`, `elapsed_sec=X`, `first_token_at=X` 等

**访问模式**:
- GET `/v1/mvp/sessions/{session_id}/history?limit=20` → ORDER BY id DESC LIMIT N
- POST `/v1/mvp/chat` (legacy) → INSERT 两条 (user + agent)
- POST `/v1/mvp/chat/stream` (SSE) → INSERT 同上
- POST `/v1/mvp/chat/fast` → 同上（fast-path）

## 2. `tool_calls` 表

```sql
CREATE TABLE IF NOT EXISTS tool_calls (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id    TEXT    NOT NULL,
  turn_id       INTEGER REFERENCES turns(id),    -- NULL = 尚未挂 agent turn
  round_idx     INTEGER NOT NULL,
  name          TEXT    NOT NULL,                -- e.g. 'web_search', 'coin_price'
  args_json     TEXT,
  result        TEXT    DEFAULT '',
  error         TEXT    DEFAULT '',
  elapsed_sec   REAL    DEFAULT 0.0,
  created_at    REAL    DEFAULT (strftime('%s','now'))
);
CREATE INDEX IF NOT EXISTS idx_tool_calls_session_id ON tool_calls(session_id);
CREATE INDEX IF NOT EXISTS idx_tool_calls_turn_id    ON tool_calls(turn_id);
```

**字段含义**:
- `turn_id`: 关联产生此 tool_call 的 agent turn。**先 persist tool_call 时 turn_id=0**，agent turn 创建后回填（`link_tool_calls_to_turn` 函数）
- `name`: Tool 注册名（OpenClaw plugin manifest）
- `elapsed_sec`: Tool 执行耗时
- `error`: 非空表示 tool 执行失败

## 3. `access_audit` 表

```sql
CREATE TABLE IF NOT EXISTS access_audit (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  ts          REAL    DEFAULT (strftime('%s','now')),
  session_id  TEXT,
  ip          TEXT,
  event       TEXT    NOT NULL,         -- 'allowed', 'rate_limit', 'invalid_code', etc.
  detail      TEXT
);
```

**访问**: 仅当 `MVP_DEBUG=1` 时通过 `/v1/mvp/admin/audit?limit=N` 查看。

## 4. Backup / 迁移

```bash
# 整库备份（adapter 在跑也能做）
sqlite3 db.sqlite3 ".backup '/tmp/backup-$(date +%F).sqlite3'"

# 导出特定 session
sqlite3 db.sqlite3 "SELECT id, role, content, created_at FROM turns WHERE session_id='X' ORDER BY id;"

# VACUUM (缩小文件)
sqlite3 db.sqlite3 "VACUUM;"
```

## 5. 清理策略（未实现）

ISS-012 待办：
- `/v1/mvp/admin/purge?older_than_days=N` endpoint
- cron daily：VACUUM + 删除 90 天前 turns
- 备份到 `~/backups/db.YYYY-MM-DD.sqlite3` (7-day rolling)

## 6. 注意事项

- **WAL 模式**: db 还有 `db.sqlite3-shm` 和 `db.sqlite3-wal` — 备份时必须 -checkpoint
- **路径**: 写在 `DB_PATH = ADAPTER_DIR / "db.sqlite3"` (server.py 顶部)
- **删库重建**: 直接 `rm db.sqlite3 db.sqlite3-*`，adapter 启动时会 recreate schema (`CREATE TABLE IF NOT EXISTS`)
- **mode**: 默认 -rw-r--r-- (644)，建议改 600（含聊天历史）

— End of Schema —
