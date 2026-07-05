# SingClaw MVP — 项目章程 (Project Charter)
**版本**: 1.0
**编制日期**: 2026-07-05 12:30 UTC (08:30 CST)
**编制人**: Maxink (H Sing's main assistant on Tencent OpenClaw)
**项目发起人**: H Sing (syberh)
**项目经理**: Maxink (P&G-style PMO, not P&G-employed)

---

## 1. 项目概述 (Project Overview)

### 1.1 项目背景 (Background)
H Sing 是一位 P&G 风格的职业经理人，同时是 Crypto / AI 项目 PMO。在 2026 年 4 月，他启动了 **SingClaw MVP** ——一个部署在 `app.singclaw.xyz` 的私域 AI 助手前端，对接自建 FastAPI Adapter 与 LLMs。

### 1.2 项目名称
- 正式名: **SingClaw MVP** (S9 Sprint)
- 简称 / 子代号: **MVP**、**adapter**、**chat page**
- 仓库: `s791400458-code/Hyperliquip-Maxink` (公共 git remote)

### 1.3 实施时间框架 (Time Frame)
- **启动日期**: 2026-04 (Sprint S6 早期)
- **当前 Sprint**: **S9.5.2** (S9.5.2-D 阶段, Bugfix2 active)
- **目标交付**: MVP 进入 production-grade chat 体验 (类似 ChatGPT)，多轮上下文 + 流式 + 工具调用准备
- **不在范围**: 公开 SaaS、多租户、AWS/GCP 部署

---

## 2. 业务案例 (Business Case)

### 2.1 商业需求
1. **个人 PMO 助手**: H Sing 在日常 PMO / Crypto 巡检 / 求职推进 4 类任务中需要一个能记住上下文的 AI 助手
2. **生产级聊天体验**: 流式输出、多轮记忆、context 保留是 ChatGPT 级别的最低门槛
3. **私人可观测**: 自建后端 (FastAPI Adapter) 让 H Sing 看到所有 turn 历史、token 消耗、模型选择
4. **离线 + 不依赖第三方 SaaS**: OpenClaw 提供统一 agent 入口，不绑定 OpenAI / Anthropic

### 2.2 价值衡量
| 价值维度 | 度量 | 目标 |
|---|---|---|
| 实用性 | H Sing 每周主动调用次数 | ≥ 30 次/周 |
| 体验 | 平均流式首 token 延迟 | ≤ 5s |
| 多轮质量 | turn2 能否记住 turn1 关键信息 | ✅ 通过率 ≥ 95% |
| 可靠性 | 月可用率 | ≥ 99% (P0 故障 ≤ 1/月) |

### 2.3 财务可行性
- **开发成本**: H Sing 自有 + Maxink / Codex 协同 (按 token 计费)
- **运营成本**: ~$50/月 (miniMax + DeepSeek 双 provider 兜底)
- **预期收益**: PMO 效率提升 + 副业/求职推进

---

## 3. 范围 (Scope)

### 3.1 in-scope ✅
- Next.js 14 chat page (`/chat`) with markdown 渲染 + 流式输出
- FastAPI Adapter (S5+S6)，绑定 loopback `:8000`
- SQLite 持久化 (turns 表 + tool_calls + access_audit)
- SSE streaming 通过 BFF (`/api/mvp-proxy`)
- multi-provider chain (miniMax → DeepSeek → OpenAI fallback)
- 鉴权 (dev-bypass code + MVP 路径)
- nginx 反代 (`/v1/mvp/*` → `:8000`)
- pm2 守护 singclaw-dynamic (待加 adapter 守护 P0.1)

### 3.2 out-of-scope ❌ (现在不做)
- 公开 multi-tenant 注册
- Stripe / 付费墙
- 移动 app
- 多语言 UI (i18n)
- 真 OpenAI Function Calling (S9.5.3 backlog)
- SOC2 / GDPR 合规

---

## 4. 干系人 (Stakeholders)

| 角色 | 姓名 | 责任 | 影响度 | 介入度 |
|---|---|---|---|---|
| 项目发起人 / 主要用户 | H Sing (syberh) | 决策、PMO 反馈、产品方向 | 高 | 高 |
| 主助手机器人 | Maxink (本助手) | 项目执行、PMO 落地、debug | 高 | 高 |
| 多机协同 / Codex | 其他电脑 Codex 实例 | 接班执行、sprint 推进 | 中 | 低 |
| LLM Provider | miniMax / DeepSeek / OpenAI | 提供 inference | 中 | 低 |
| OpenClaw Platform | Tencent OpenClaw | 平台 / gateway | 中 | 低 |
| 用户支持代理 | clawfi / a-stock / crypto | 协调任务 | 低 | 低 |

**沟通渠道**:
- H Sing ↔ Maxink: Telegram DM (chat 6509109244)
- 跨机协同: git push/pull + HANDOFF.md
- 紧急升级: H Sing 主动联系

---

## 5. 里程碑 (Milestones)

| ID | 里程碑 | 目标日期 | 状态 |
|---|---|---|---|
| M0 | S6 FastAPI Adapter 完成端到端 smoke test | 2026-07-04 | ✅ 完成 |
| M1 | S9.5.2-C chat page 与 adapter 联调 | 2026-07-04 | ✅ 完成 |
| M2 | S9.5.2-D 持久化 + reload + 工具调用 UI | 2026-07-05 | ✅ 完成 (含 bugfix2) |
| **M3** | **生产级 chat 体验验收** (本次修复后) | 2026-07-05 | ✅ 完成 (10/10 场景过) |
| M4 | adapter 加 pm2 守护 | 待办 (P0.1) | 📋 待办 |
| M5 | 生产 build/deploy 验证门 | 待办 (P0.2) | 📋 待办 |
| M6 | 安全整改 (chmod + IP allowlist + keys revoke) | 待办 (P0.3) | 📋 待办 |
| M7 | S9.5.3 真 Function Calling | 待办 | 📋 待办 |

---

## 6. 假设与约束 (Assumptions & Constraints)

### 6.1 假设
1. H Sing 会持续提供 Telegram 反馈与决策
2. miniMax + DeepSeek 模型可用
3. git remote `Hyperliquip-Maxink` 可持续推送
4. OpenClaw gateway 持续运行于 `:24135`

### 6.2 约束
1. **单工程师** (Maxink + 偶尔 Codex)
2. **预算**: $50/月 LLM 配额
3. **基础设施**: 1 台 opencloudos VM (VM-0-9-opencloudos, 10.3.0.9)
4. **开发节奏**: Telegram-led, sprint-led (周为粒度)
5. **合规**: 不涉及公开用户数据，但 secrets 必须 mode `0600`

---

## 7. 风险概览 (Risk Snapshot)
详见 `PROJECT_RISK_REGISTER.md`：
- **R-01**: Adapter 进程未守护，重启 host 即掉 → P0
- **R-02**: 源码 HEAD 跟 build 脱节 + deploy 无验证 → P0
- **R-03**: `/api/mvp-proxy` 公网无鉴权 → P0
- **R-04**: `.env*` 文件 mode 0644 → P0
- **R-05**: keys (Telegram / LinkedIn / Vercel / ETH) 未 revoke → P1
- **R-06**: `/v1/mvp/chat/fast` fast-path 不支持 tools → P2
- **R-07**: db.sqlite3 无清理策略 → P2
- **R-08**: Backend 落后 master 14 commit，未 push → P1

---

## 8. 预算 (Budget)
| 项 | 预期 | 实际 (到 2026-07-05) |
|---|---|---|
| 工程师时间 | ~80h | 不计 (H Sing 自己 + AI 协同) |
| LLM token 月费 | ~$50 | ~$30 (本月) |
| VM 成本 | 已在 Tencent 计费 | 已含在 H Sing 平台 |
| Total | 不限 | ~$30/月 |

---

## 9. 批准 (Approval)

| 角色 | 姓名 | 签字 | 日期 |
|---|---|---|---|
| 项目发起人 | H Sing | _待签_ | _待办_ |
| 项目经理 | Maxink | _已草拟_ | 2026-07-05 12:30 UTC |

— End of Project Charter —
