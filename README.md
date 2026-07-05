# Singclaw-chat

> **Personal PMO AI assistant for H Sing** — archived private repo
> 原本在 `s791400458-code/Hyperliquip-Maxink`（work repo），private 副本在 `Parsons791400458/Singclaw-chat`。

**What is this**: Production-grade chat frontend (Next.js 14) backed by self-hosted FastAPI Adapter, multi-provider LLM chain (miniMax → DeepSeek → OpenAI fallback), running at `app.singclaw.xyz/chat`.

**Repo purpose**: 把原本散落在 work repo 里的 SingClaw MVP 部分**单独 private 化**，方便 H Sing 长期积累 + 接手文档化。

---

## 立即访问
- **Production chat**: https://app.singclaw.xyz/chat

---

## 📚 必须读

按顺序读，否则不知道这是什么：

1. **[QUICK_START.md](./QUICK_START.md)** — 5 步上手（clone → 起服务 → 验证）
2. **[docs/SECRETS_HANDBOOK.md](./docs/SECRETS_HANDBOOK.md)** — 没这个跑不起来
3. **[docs/PROJECT_CHARTER.md](./docs/SINGCLAW_MVP_PROJECT_CHARTER.md)** — 项目章程
4. **[docs/SINGCLAW_MVP_DELIVERABLES.md](./docs/SINGCLAW_MVP_DELIVERABLES.md)** — 当前活什么
5. **[HANDOFF.md](./HANDOFF.md)** — 跨机/跨 agent 协同

## 📋 其他文档

| 主题 | 文件 |
|---|---|
| 项目章程 / 范围 / 干系人 | docs/SINGCLAW_MVP_PROJECT_CHARTER.md |
| 开发记录 / 时间线 | docs/SINGCLAW_MVP_DEVELOPMENT_RECORD.md |
| 产出清单 | docs/SINGCLAW_MVP_DELIVERABLES.md |
| Issue Log | docs/SINGCLAW_MVP_ISSUES_LOG.md |
| 风险登记 | docs/SINGCLAW_MVP_RISK_REGISTER.md |
| 资源计划 | docs/SINGCLAW_MVP_RESOURCE_PLAN.md |
| 经验教训 | docs/SINGCLAW_MVP_LESSONS_LEARNED.md |
| Handoff Bundle | docs/SINGCLAW_MVP_HANDOFF_BUNDLE.md |
| Adapter schema | docs/SCHEMA.md |
| Agent 风格 + 上下文 | SOUL.md / MEMORY.md / AGENTS.md / IDENTITY.md (在仓库根) |

---

## ⚠️ 接手者必看

| # | 陷阱 | 文档 |
|---|---|---|
| 1 | Adapter 进程在 nohup，没守护 — 重启 host 全网 5xx | ISS-004 / R-01 |
| 2 | 源码 HEAD 跟 build 脱节 + 无 deploy 验证门 | ISS-005 / R-02 |
| 3 | `/v1/mvp/*` 公网裸奔 — 任何 IP POST 都消耗 LLM 配额 | ISS-006 / R-03 |
| 4 | `.env*` mode 0644 + 部分 git tracked 含明文 key | ISS-007 / R-04 / R-07 |
| 5 | 5+ 个 keys 未 revoke (Telegram / LinkedIn / Vercel / ETH) | ISS-008 / R-05 |

---

## 联系方式

- **H Sing** (project owner): Telegram DM 6509109244 (`@syberh`)
- **Maxink** (PMO assistant): 在同 Telegram DM 内

— End of README —
