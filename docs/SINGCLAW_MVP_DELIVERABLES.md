# SingClaw MVP — 当前产出清单 (Deliverables)
**状态日期**: 2026-07-05 12:30 UTC

## 1. 活的服务 (Live Services)

| 服务 | 端点 | PID / status | 验证命令 |
|---|---|---|---|
| FastAPI Adapter | `127.0.0.1:8000` | pid 2423716, online | `curl -fsS http://127.0.0.1:8000/v1/mvp/health` |
| Next.js singclaw-dynamic | `127.0.0.1:3001` | pm2 pid 2426788, online, 4 restarts | `curl -fsS http://127.0.0.1:3001/api/mvp-proxy` |
| Nginx (主) | `0.0.0.0:80/443/8443` | running | `curl -fsS https://app.singclaw.xyz/chat` |
| OpenClaw Gateway | `0.0.0.0:24135` | online | `/health` 200 |
| Postgres | `127.0.0.1:5432` | local only | n/a |
| Umami 监控 | `127.0.0.1:3002` | pm2, online | n/a |

## 2. 公网入口 (Public URLs)

| URL | 用途 | 状态 |
|---|---|---|
| `https://app.singclaw.xyz/chat` | Chat UI 入口 | ✅ 200 |
| `https://app.singclaw.xyz/api/mvp-proxy` | BFF 端点 (chat page → adapter) | ✅ stage S9.5.2-C |
| `https://app.singclaw.xyz/v1/mvp/*` | Adapter 直连 (loopback src) | ✅ 200 (通过 nginx) |
| `https://singclaw-dynamic.vercel.app/chat` | Vercel 镜像 | 备用 |

## 3. 代码仓库 (Repositories)

| 仓库 | URL | 用途 | push 状态 |
|---|---|---|---|
| `Hyperliquip-Maxink` | github.com/s791400458-code/Hyperliquip-Maxink.git | 当前工作仓库 | main 落后 origin/master 14 commit |

## 4. 文档包 (Documentation Set, 本次新建)

| 路径 | 用途 |
|---|---|
| `docs/SINGCLAW_MVP_PROJECT_CHARTER.md` | 项目章程 |
| `docs/SINGCLAW_MVP_DEVELOPMENT_RECORD.md` | 开发记录 |
| `docs/SINGCLAW_MVP_DELIVERABLES.md` | 本文件 |
| `docs/SINGCLAW_MVP_ISSUES_LOG.md` | Issue Log |
| `docs/SINGCLAW_MVP_RISK_REGISTER.md` | Risk Register |
| `docs/SINGCLAW_MVP_RESOURCE_PLAN.md` | Resource Plan |
| `docs/SINGCLAW_MVP_LESSONS_LEARNED.md` | Lessons Learned |
| `docs/SINGCLAW_MVP_HANDOFF_BUNDLE.md` | 接手包 (合并自 HANDOFF.md + PMO 日报) |
| `HANDOFF.md` | 跨机协同入口 (working copy) |

## 5. 数据资产 (Data Assets)

| 项 | 位置 | 数量 |
|---|---|---|
| chat turns | `SINGCLAW-MVP/adapter/db.sqlite3` | 74 turns / 44 audit_events (增长中) |
| tool_calls | 同上 | n/a |
| 下载文件 (HSBC PDF/DOCX) | `singclaw-dynamic/public/downloads/` | 6 个 credentials 文件 (untracked) |
| 日志 | `SINGCLAW-MVP/adapter/logs/` | uvicorn 日志 (按 YYYYMMDD-HHMMSS 命名) |

## 6. Sprint 进展 (Sprint Status)

| Sprint | 主题 | 状态 |
|---|---|---|
| S6 | Adapter 端到端 | ✅ |
| S9.1 | multi-provider chain + silent fallback | ✅ commit 12b94ad |
| S9.5.2-C | tool_call UI 卡片 | ✅ commit fcd6998 |
| S9.5.2-D | 持久化 reload + tool by turn_id | ✅ commit 83feda8 |
| S9.5.2-D-bugfix | 发送按钮卡取消 | ✅ fix 落地 (源码 + build + pm2 restart) |
| S9.5.2-E | export endpoint + UI 下载 | 📋 待办 |
| S9.5.2-F | tool_call CSV/UI 强化 | 📋 待办 |
| S9.5.3 | 真 OpenAI function calling | 📋 待办 |

## 7. 当前生产能力 (Capabilities)

✅ **已具备**:
1. 流式聊天 (ChatGPT-like typing)
2. 多轮上下文（turn-to-turn 记忆）
3. abort 安全（取消按钮可立刻用）
4. 并发隔离（多 session）
5. SQLite 持久化
6. 工具调用持久化展示
7. multi-provider fallback（miniMax → DeepSeek → OpenAI）
8. 系统健康监控（/v1/mvp/health）
9. SSE 友好 nginx 配置

❌ **不具备**:
1. web_search / coin_price 等 fast-path 工具
2. multi-tenant / 鉴权 / 配额管理
3. Adapter 进程守护（nohup 现状）
4. Production build 验证门
5. IP allowlist / 鉴权（公网裸奔）

## 8. 最近一次验证 (Last Verification)

时戳: 2026-07-05 12:10 UTC (08:10 CST)
- ✅ 5 轮连续 send → 100% HTTP 200
- ✅ 多轮上下文 → turn2 正确记住 turn1 名字 (H Sing)
- ✅ 并发 race → DB 隔离 OK
- ✅ abort → 立刻能再 send
- ✅ 5-27 chunks/turn 流式打字
- ✅ 多语言（含俄文 борщ）

— End of Deliverables —
