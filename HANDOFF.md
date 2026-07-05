# SingClaw MVP — Handoff to Other Codex / Other Machine

> 这是 SingClaw-MVP codebase 的协同入口。其他电脑、其他 Codex 实例、其他 agent 开工前 **先读这个文件**，再读 MEMORY.md，再读当晚 PMO 日报。

**Generated**: 2026-07-05 04:10 UTC (after the Chat-Cancel hidden-bug fix)
**Origin machine**: VM-0-9-opencloudos (opencloudos 9 kernel 6.6.117)
**Coordination**: H Sing (Telegram id 6509109244, username syberh), 中文优先

---

## 0. Who you are talking to

You are running on H Sing's behalf. He wears multiple hats:
- P&G-style professional manager
- Crypto/AI 项目 PMO (Hyperliquid / MVP / Adapter / Tools)
- Knowledge engineer (DIKIW)

**Identity rules** (from SOUL.md / IDENTITY.md):
- Reply style: 结论先行、短句、给证据、给下一步
- DO NOT claim P&G background if asked, just do PMO tasks
- DO NOT break P0 deadlines — if blocked >30min, escalate

---

## 1. Read these in order (mandatory)

| File | Why |
|---|---|
| `MEMORY.md` | 长期记忆锚点 (2026-02 / 2026-07 decisions) |
| `SOUL.md` | 人格 / 回复风格 |
| `IDENTITY.md` | 身份边界 |
| `AGENTS.md` | 工作原则 / web 工具策略 / 心跳机制 |
| `memory/2026-07-05-pmo-s9.5.2-loop.md` | **今晚 PMO 锚点** — chat 卡取消的真根因 / 修法 / Loop 测试 |
| `memory/SSOT-SPRINT-PROGRESS.md` (if exists) | 当前 Sprint 状态 |

If you can't find MEMORY.md: STOP. Ask H Sing to provide it. Don't guess.

---

## 2. Active Sprint Backlog (as of 2026-07-05 04:10 UTC)

### 🔥 P0 — Do these immediately

#### 2.1 Adapter 加 pm2 守护 (CRITICAL — 防再掉)
- Adapter currently: `nohup python3 -m uvicorn ... &` → not in pm2/systemd
- Will die on host reboot. Already died once tonight.
- **Action**:
  ```bash
  cd /root/.openclaw/workspace
  pm2 start 'python3 -m uvicorn server:app --host 127.0.0.1 --port 8000 --app-dir SINGCLAW-MVP/adapter' \
    --name singclaw-mvp-adapter --cwd /root/.openclaw/workspace/SINGCLAW-MVP/adapter
  pm2 save && pm2 startup
  ```
- Verify: `pm2 ls` shows `singclaw-mvp-adapter` with `online` status.
- Add `/v1/mvp/health` to `openclaw_gateway_watchdog.py` (existing, runs every 30s).

#### 2.2 Production 部署验证门 (build/deploy 缺校验)
- Tonight's bug: source HEAD was correct (`09e934c`), but `pm2` ran a 7h-old build.
- **Action**: in `/root/.openclaw/workspace/singclaw-dynamic/ecosystem.config.js`, add post-deploy:
  ```js
  post_deploy: ['curl -fsS http://127.0.0.1:3001/api/mvp-proxy | grep -q S9.5.2 || exit 1']
  ```
- Or write `scripts/deploy-with-verify.sh`: build → restart → wait 5s → curl → fail = rollback `.next`.
- Verify after: `pnpm run build && pm2 restart singclaw-dynamic && sleep 5 && curl localhost:3001/api/mvp-proxy`

#### 2.3 安全 chmod + IP allowlist (H Sing: 避免被动用 key)
- All `.env*` files in workspace are mode `0644` — readable by any user on the box.
- **Action**:
  ```bash
  chmod 600 /root/.openclaw/workspace/{crypto,singclaw-dynamic,singclaw-site,worldx-demo,linkedin-agent}/.env*
  chmod 600 /root/.openclaw/workspace/clawfi_account.json /root/.openclaw/workspace/*.bak*.tgz
  ```
- Nginx location `/v1/mvp/*` has no auth. **Action**:
  ```nginx
  # /etc/nginx/conf.d/app-singclaw.conf, inside location ^~ /v1/mvp/
  allow 43.156.239.53/32;     # H Sing public IP (current at handoff time)
  allow 10.0.0.0/8;            # home/VPN range (adjust)
  deny all;
  ```
  Then `nginx -t && nginx -s reload`.

#### 2.4 Keys to revoke on H Sing's account (NOT your job, list for him)
- Telegram bot token (file: `crypto/.env`): `H Sing goes to @BotFather /revoke`
- LinkedIn password (file: `linkedin-agent/.env`): `H Sing changes password + enables 2FA`
- Vercel OIDC token (file: `singclaw-site/.vercel/.env.development.local`): `H Sing revokes in Vercel Settings`
- ETH private key (file: `crypto/.env` and `singclaw-site/contracts/.env`): `H Sing checks balance, transfers out if non-zero, regenerates`

**DO NOT** autonomously do 2.4 — these are interactive revocations, may trigger 2FA / SMS. Tell H Sing.

### 📋 P2 — backlog, schedule later
- S9.5.2-E: `action=export` endpoint + chat page `📥` button (1 day)
- S9.5.2-F: tool_call CSV/UI enhancement
- S9.5.3: real OpenAI/Anthropic function calling (1 day, unblocks BTC price etc.)

---

## 3. Active production state (TOUCH CAREFULLY)

### Running processes (verify before touching)
| Process | Where | How to check |
|---|---|---|
| FastAPI Adapter | `127.0.0.1:8000` (loopback only) | `ss -tlnp \| grep 8000` should show `python3` |
| singclaw-dynamic (Next.js) | `127.0.0.1:3001` | `pm2 ls` (process 2) |
| umami | `127.0.0.1:3002` | `pm2 ls` (process 1) |
| nginx | `0.0.0.0:80/443/8443` | `ss -tlnp \| grep -E ':(80\|443\|8443)\b'` |
| OpenClaw Gateway | `0.0.0.0:24135` | `ss -tlnp \| grep 24135` |
| postgres | `127.0.0.1:5432` | `ss -tlnp \| grep 5432` |

### File paths (opencloudos / debianish layout)
- App source: `/root/.openclaw/workspace/singclaw-dynamic/` (HEAD = commit 09e934c)
- Adapter source: `/root/.openclaw/workspace/SINGCLAW-MVP/adapter/` (FastAPI)
- Logs: `/root/.openclaw/workspace/SINGCLAW-MVP/adapter/logs/uvicorn-*.log`
- Nginx configs: `/etc/nginx/conf.d/{app-singclaw,singclaw-mvp,oa-singclaw,oa-starclaw,umami}.conf`
- Vercel configs (singclaw-site): `/var/www/singclaw/` + GitHub vercel deploy

### Chat page entry points (public)
- `https://app.singclaw.xyz/chat` (Next.js) → `/api/mvp-proxy` → `https://app.singclaw.xyz/v1/mvp/chat/fast`
- For now: `MVP_CODES=mvp-dev-bypass-2026` is public — only safe because app is single-tenant for H Sing.

### mvp-proxy stage string
- After rebuild at 04:08 UTC: `S9.5.2-C-BFF-mvp-proxy` 
- If you see `S8-BFF-mvp-proxy` → build is stale → `pnpm run build && pm2 restart singclaw-dynamic`

---

## 4. Tech-stack conventions (so you don't fight the codebase)

### Frontend (Next.js 14, singclaw-dynamic/)
- **App Router** under `src/app/` (NOT `app/` at root — that's stale from earlier generate).
- API routes: `src/app/api/<name>/route.ts`, exports `POST`/`GET`.
- **Server-side only** env (no `NEXT_PUBLIC_`): server-only keys like `CLERK_SECRET_KEY`, `MVP_*`.
- **Client-side visible** env (must have `NEXT_PUBLIC_`): like `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`.
- Streaming responses for chat: see `src/app/api/mvp-proxy/route.ts` (S9.5.2-D-bugfix2 = wrap upstream ReadableStream in TransformStream; without wrapping, SSE hangs).

### Backend (Python FastAPI, SINGCLAW-MVP/adapter/)
- **Loopback only**: bind to `127.0.0.1:8000`. External access goes through nginx `location ^~ /v1/mvp/`.
- SSE-friendly: `proxy_buffering off;` in nginx for the whole location.
- Persistence: `db.sqlite3` (turns table). Schema is simple — look at `server.py` top half.
- Fast-path: `fast.py` registers routes via `register_routes(app)` at adapter startup.

### Build / deploy
- `pnpm run build` (NOT `pnpm next build` — uses the script in package.json).
- `pm2 restart singclaw-dynamic` after rebuild (NO `next build` while pm2 running).
- Source vs build: `src/app/api/mvp-proxy/route.ts` (might be 00:50) ≠ `.next/server/app/api/mvp-proxy/route.js` (might be 22:22). Always rebuild before restart.

---

## 5. Hand-off checklist (run these before declaring "I'm done")

```bash
# A. Verify ports
ss -tlnp | grep -E ':(3001|8000|24135)\b' | head -5

# B. Verify health
curl -fsS http://127.0.0.1:8000/v1/mvp/health
curl -fsS http://127.0.0.1:3001/api/mvp-proxy
curl -fsS -X POST https://app.singclaw.xyz/api/mvp-proxy \
    -H "Content-Type: application/json" -H "X-MVP-Code: mvp-dev-bypass-2026" \
    -d '{"message":"hi","session_id":"handoff-check","stream":true}' \
    | grep -E "^event:|^data: " | head -5

# C. Verify git clean (or commit + push)
git status -sb | head -10
# If "ahead of origin/master N": commit + push before signing off

# D. Verify PMO memo exists
ls -la /root/.openclaw/workspace/memory/2026-07-05-*.md
```

Pass all 4 = safe to write next PMO memo and sign off.

---

## 6. Multi-machine / multi-agent coordination

If you run multiple Codex agents (this box + others):

### Option A: Git as lock
- Branch per agent: `git checkout -b codex-other-laptop`
- Push every green test. Don't rebase master unless coordinated.
- Conflict resolution: PMO memo + this file are merge-friendly (markdown prose).

### Option B: OpenClaw multi-node (heavier, real-time)
- Install OpenClaw on other laptop, register as a `node` against this box's gateway at `:24135`.
- Each node sees the same `MEMORY.md` (sync via git pull every 5min).
- cross-node messaging via `sessions_send(sessionKey=…)` (OpenClaw native).
- See `openclaw_gateway_watchdog.py` for how this box already supervises OpenClaw.

### Option C: Codex Cloud
- ChatGPT Codex (cloud) can `cd /root/.openclaw/workspace` if mounted as project.
- Won't see your live conversation history, but sees file state and PMO memo.
- Round-trip latency higher but no install.

---

## 7. Failure modes (don't shoot yourself)

1. **If you don't see MEMORY.md**: STOP. Ask H Sing. He's currently using bot mediation (Telegram) and missing context = wrong actions.
2. **If `pnpm run build` fails with `ENOENT` for `singclaw-dynamic/.next`**: it's already gone, that's fine; `pnpm run build` recreates.
3. **If `pnpm run build` fails with TypeScript error**: read `tsconfig.json` errors, don't `next build --skip-lint` (it's set to strict).
4. **If you rebuild but `/api/mvp-proxy` returns old stage**: pm2 hasn't restarted. `pm2 restart singclaw-dynamic` then retry.
5. **If adapter is dead (`Connection refused :8000`)**: that's the entire stack. Diagnose:
   ```bash
   tail -50 /root/.openclaw/workspace/SINGCLAW-MVP/adapter/logs/uvicorn-*.log | tail -30
   ss -tlnp | grep 8000
   ```
   Restart: see §2.1.
6. **If git remote fails (auth)**: this is `Hyperliquip-Maxink.git` — H Sing has the SSH key configured on this box. New machine needs the same key (or PAT).
7. **If you see `token0` in config**: that's ZHIPU legacy model — ignore, already removed from defaults (see MEMORY.md 2026-07-02 entry).

---

## 8. How to reach H Sing

- Telegram DM: bot mediated (this conversation). One-way latency ≈ 2s.
- Voice note: H Sing rarely shares audio. Text is preferred.
- Style: 结论先行, 短句, 给证据, 给下一步. He reads on phone screen.
- If task will take >30min of compute, leave a brief progress update every 5 min.

**Do NOT** DM him during 23:00–07:00 Asia/Shanghai unless production is on fire.

---

## 9. Pre-existing limitations (so you don't try and fail)

- `/v1/mvp/chat/fast` is **tools-disabled** by design (S9.5.3 pending). Model says "tools unavailable" if you ask for `web_search` etc. This is known.
- Adapter has no `purge older than N days` endpoint. DB will grow unbounded. PMO has flagged.
- HTTP 502 from `/v1/mvp/*` means adapter dead. Run §2.1.
- HTTP 200 with old `S8-BFF-mvp-proxy` means build is stale. Run §2.2.
- DB is `db.sqlite3` in adapter cwd. Backup = copy while adapter is running (WAL is fine for SQLite).

— End of handoff —
