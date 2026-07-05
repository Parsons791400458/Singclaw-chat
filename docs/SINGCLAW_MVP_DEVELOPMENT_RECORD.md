# SingClaw MVP — 项目开发记录 (Development Record)
**项目**: SingClaw MVP (S9 Sprint)
**记录人**: Maxink
**最后更新**: 2026-07-05 12:30 UTC

---

## 1. 完整时间线 (Timeline)

### 阶段 1: 基础搭建 (S6 Sprint)
- **2026-06-中旬**: Sprint S5.5 / S6 — FastAPI Adapter 设计
  - 端口: loopback 127.0.0.1:8000
  - 端点: `/v1/mvp/health`, `/v1/mvp/chat`, `/v1/mvp/chat/stream`
  - 持久化: SQLite (db.sqlite3)
  - 限流: IP/min + session/min
- **2026-07-04 00:24 UTC**: Adapter pid 1988580 启动成功，与 nginx 联调端到端

### 阶段 2: chat page 集成 (S9.5 Sprint)
- **2026-07-04** (UTC+8 白天): Next.js `singclaw-dynamic` 主线推进
  - PMO 接入 BFF: `src/app/api/mvp-proxy/route.ts`
  - 子代理路径: B (subprocess `openclaw agent`)
- **2026-07-04 22:24 UTC**: mvp-proxy S8 build 上线（含 HTM 配置）

### 阶段 3: 工具调用 + 持久化 (S9.5.2 Sprint)
- **2026-07-05 (凌晨)**:
  - **09e934c** `feat(chat): S9.5.2-D 持久化 reload` — fetch tools by turn_id
  - **5c87602** `fix(chat): S9.5.2-D-bugfix` — 发送按钮卡"取消"
  - **09e934c** `fix(mvp-proxy): S9.5.2-D-bugfix2` — 包装 upstream ReadableStream
  - 推出 S9.5.2-C: tool_call UI 卡片

### 阶段 4: 隐藏 bug 翻车 + 修 (本次事件)
- **2026-07-05 03:00+ UTC** (H Sing 报告 chat 卡"取消"):
  - 第一轮诊断失误: maxink 误判 chat page 自身 bug
  - 发现修复: adapter pid 死了 + pm2 不管
- **2026-07-05 04:02 UTC**:
  - nohup 重启 adapter (pid 2423716)
  - `pnpm run build` 刷新 .next
  - `pm2 restart singclaw-dynamic` (新 pid 2426788)
  - 验证 mvp-proxy stage: `S9.5.2-C-BFF-mvp-proxy` (含 bugfix2)
- **2026-07-05 04:14 UTC**: 10/10 Loop 测试通过
- **2026-07-05 12:30 UTC**: 项目文档化收口 (本文档)

---

## 2. 提交记录 (Commit Record)

仓库: `https://github.com/s791400458-code/Hyperliquip-Maxink.git`
**重点 commit**：

| SHA | 说明 | 时间 |
|---|---|---|
| `09e934c` | fix(mvp-proxy): S9.5.2-D-bugfix2 — 包装 upstream ReadableStream | 2026-07-05 (凌晨) |
| `5c87602` | fix(chat): S9.5.2-D-bugfix — 发送按钮卡取消状态 | 2026-07-05 (凌晨) |
| `83feda8` | feat(chat): S9.5.2-D 持久化 reload — switchSession fetch tools by turn_id | 2026-07-05 (凌晨) |
| `de3a0b1` | fix(middleware): 绕开 Clerk 未配置时的 MIDDLEWARE_INVOCATION_FAILED | 2026-06-末 |
| `fcd6998` | feat(mvp): tool_call UI 卡片 + /api/mvp-proxy?action=tools proxy (S9.5.2-C-UI) | 2026-07-04 |
| `12b94ad` | feat(adapter): S9.1 multi-provider chain + silent fallback | 2026-07-04 04:06 CST |
| `4be328e` | fix: 移除 UserButton 已废弃的 afterSignOutUrl 属性 | older (singclaw-v2 only) |
| `2515d00` | feat: SingClaw v2.0 初始化 - Next.js 14 + TypeScript + Tailwind + pnpm | old init |

注: 仓库当前分支 `main` 落后 origin/master 14 个未推送 commit (含上述 S9.5.2-D 系列)。

---

## 3. 代码产出清单 (Code Deliverables)

### 3.1 chat page (Next.js 14 / singclaw-dynamic)
- `src/app/api/mvp-proxy/route.ts` — BFF (S9.5.2-D-bugfix2, 87 行 + tools endpoint)
- `src/app/chat/page.tsx` — Chat UI (848 行, 多轮 + tools 渲染 + streaming)
- `src/app/api/cron-output/route.ts` — cron 公共 endpoint
- `src/app/api/knowledge/*` — knowledge cards / intake / review
- 其它 SaaS 路由 (cron-output, trading-plans)

### 3.2 Adapter (FastAPI / SINGCLAW-MVP/adapter)
- `server.py` (483 行) — 主 app, SQLite, rate limit, access_audit
- `fast.py` (1195 行) — fast-path LLM direct 接入，多 provider 兜底链
- `db.sqlite3` — 74 turns / 44 audit_events (2026-07-05 04:00)
- `prompts/singclaw-mvp-system.md` — system prompt

### 3.3 基础设施
- `/etc/nginx/conf.d/app-singclaw.conf` — 主反代 + /v1/mvp/ 反代至 8000
- `/etc/nginx/conf.d/singclaw-mvp.conf` — 8443 alternative listen (历史)
- `/etc/nginx/conf.d/oa-singclaw.conf` — oa（OA 系统）
- `/etc/nginx/conf.d/umami.conf` — umami 监控
- `ecosystem.config.js` — pm2 (singclaw-dynamic + umami)
- **缺**: adapter 的 pm2 守护 (P0.1)

---

## 4. 文档产出 (Documentation Deliverables)

- `MEMORY.md` — 长期记忆锚点（3 处关键决策 2026-02 / 2026-07-02 / 2026-07-05）
- `SOUL.md` / `IDENTITY.md` / `AGENTS.md`
- `docs/SINGCLAW_MVP_PROJECT_CHARTER.md` — 项目章程
- `docs/SINGCLAW_MVP_DEVELOPMENT_RECORD.md` — 本文件
- `docs/SINGCLAW_MVP_DELIVERABLES.md` — 产出清单
- `docs/SINGCLAW_MVP_ISSUES_LOG.md` — 问题记录
- `docs/SINGCLAW_MVP_RISK_REGISTER.md` — 风险登记
- `docs/SINGCLAW_MVP_RESOURCE_PLAN.md` — 资源
- `docs/SINGCLAW_MVP_LESSONS_LEARNED.md` — 经验
- `docs/SINGCLAW_MVP_HANDOFF_BUNDLE.md` — 接手包
- `HANDOFF.md` — 跨机协同入口
- `memory/2026-07-05-pmo-s9.5.2-loop.md` — 本次 PMO 日报
- `memory/2026-07-05.md` — daily notes
- `memory/2026-07-04-security-audit.log` — 上一轮安全巡检

---

## 5. 关键 Sprint 回顾

### S9.5.2-C (tool_call UI): ✅ done
- 加 `?action=tools&session_id=` endpoint
- chat page 持久化展示工具调用历史
- 表现: 干净集成

### S9.5.2-D (reload 持久化): ✅ done
- turn_id 关联 tool_call
- fetch history + tools by turn_id
- 多轮上下文证明有效: turn2 记住 turn1 名字

### S9.5.2-D-bugfix (发送按钮卡取消): ✅ fixed
- 真根因: adapter 未运行 + build 旧
- 修法: 修 build + 重启 adapter + 验证

— End of Development Record —
