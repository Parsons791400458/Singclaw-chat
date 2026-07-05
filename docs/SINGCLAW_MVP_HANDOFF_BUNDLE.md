# SingClaw MVP — 项目文档包入口 (Handoff Bundle)
> 给接手者（其他 Codex / 其他机器 / 未来 agent）的完整引导。

**生成时间**: 2026-07-05 12:30 UTC

---

## 0. 顺序读 (Read in order)

1. 📄 **`PROJECT_CHARTER.md`** — 项目立项、范围、干系人
2. 📄 **`DEVELOPMENT_RECORD.md`** — 完整时间线 + commit 记录 + 代码产出
3. 📄 **`DELIVERABLES.md`** — 当前活的服务、公网入口、清单
4. 📄 **`ISSUES_LOG.md`** — 已解决问题 + 待办 issue
5. 📄 **`RISK_REGISTER.md`** — 风险登记 + mitigation
6. 📄 **`RESOURCE_PLAN.md`** — 资源使用 + 财务
7. 📄 **`LESSONS_LEARNED.md`** — 经验教训
8. 📄 **`HANDOFF.md`** (working copy) — 跨机协同入口

---

## 1. 项目一句话总结 (TL;DR)

SingClaw MVP 是 H Sing 的个人 PMO 私域 AI 助手。架构 = Next.js chat page (`singclaw-dynamic`) + FastAPI Adapter (loopback 8000) + multi-provider LLM chain (miniMax → DeepSeek → OpenAI)，通过 nginx 反代在 `app.singclaw.xyz` 对外服务。Sprint S9.5.2 当前处于 production-grade chat（流式 + 多轮），但有 6 个 P0 backlog（adapter 守护、build 验证门、auth、chmod、keys revoke、git push）。

## 2. 当前最紧急 4 件事

| 优先级 | 任务 | 工时 |
|---|---|---|
| P0.1 | Adapter 加 pm2 守护 | 5 min |
| P0.2 | Deployment 验证门 (build → restart → curl stage 比对) | 10 min |
| P0.3 | chmod 600 全 `.env*` + nginx IP allowlist `/v1/mvp/*` | 1 min + 15 min |
| P0.4 | revoke Telegram / LinkedIn / Vercel / ETH 旧 keys | H Sing 主账号 |

## 3. Verification 命令 (接到机器后跑这 4 行)

```bash
# 服务存活
ss -tlnp | grep -E ':(3001|8000|24135)\b' | head -5

# 健康
curl -fsS http://127.0.0.1:8000/v1/mvp/health
curl -fsS http://127.0.0.1:3001/api/mvp-proxy

# 端到端
curl -fsS -X POST https://app.singclaw.xyz/api/mvp-proxy \
    -H "Content-Type: application/json" -H "X-MVP-Code: mvp-dev-bypass-2026" \
    -d '{"message":"hi","session_id":"handoff-check","stream":true}' \
    | grep -E '^event:|^data:' | head -5

# Git 干净
cd /root/.openclaw/workspace
git status -sb
```

全过 = 健康，可以接力。

## 4. 跨机协同 (multimachine coordination)

详见 `HANDOFF.md` §6，主要模式：

| 模式 | 时延 | 用例 |
|---|---|---|
| **A. Git + HANDOFF** | 分钟 | P0 backlog 收尾 |
| B. OpenClaw multi-node | 秒 | 多 agent live |
| C. Codex Cloud | 网络 | 不想装 CLI |

默认推荐 A。

## 5. 接手者 checklist

- [ ] 读完上面 8 个 markdown 文件
- [ ] 跑 §3 verification 4 行命令
- [ ] 跟 H Sing 报到 (`syberh` on Telegram)
- [ ] 看 cron `--list` 把 watchdog 加入日常
- [ ] 第一次 sprint: 接 ISS-004 / ISS-005 / ISS-006 (P0 三连)

— End of Handoff Bundle —
