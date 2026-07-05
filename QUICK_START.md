# Quick Start — SingClaw MVP
> 新人 Codex / 其他 agent / 其他机器接到本仓库后的 **5 步上手**。

**预计时间**: 10~15 分钟（不计 LLM 首次暖机）

---

## 1. Clone 与工具链（先确认）
```bash
git clone git@github.com:Parsons791400458/Singclaw-chat.git /root/.openclaw/workspace
cd /root/.openclaw/workspace

# 工具版本对照 — 见 docs/ENVIRONMENT.md
# 必须: node 22.x, pnpm 10.x, python 3.11+, pm2, nginx
node --version  && pnpm --version && python3 --version && pm2 --version
```

## 2. 拿 secrets（联系 H Sing）
**没 secrets 你跑不动**。详见 [SECRETS_HANDBOOK.md](./docs/SECRETS_HANDBOOK.md) + **[SECRETS_ONBOARDING.md](./SECRETS_ONBOARDING.md)**。

**怎么传**（按场景）：
- 同内网: `scp` 或 `tar` 拷贝
- 跨网: Age 加密 (推荐, 公网安全)
- 临时: 1Password share link
- ❌ 永远别用 Telegram/email/git 公开发送

最小集（必须要有）：
- `singclaw-dynamic/.env.local` ← FastAPI + Clerk + MVP code
- `crypto/.env` ← Telegram bot + ETH private key
- `linkedin-agent/.env` ← LinkedIn 凭据（仅 LinkedIn agent 需要）

**这些不 commit。H Sing 会通过 secure channel 给你**（scp / age / 1Password）。

## 3. 装 deps + build
```bash
cd singclaw-dynamic && pnpm install && pnpm run build && cd ..

# Python deps for adapter
pip install 'fastapi>=0.139' 'uvicorn[standard]>=0.30' pydantic
```

## 4. 起服务
```bash
# 4.1 Adapter (loopback only)
cd /root/.openclaw/workspace
pm2 start 'python3 -m uvicorn server:app --host 127.0.0.1 --port 8000 \
  --app-dir /root/.openclaw/workspace/SINGCLAW-MVP/adapter' \
  --name singclaw-mvp-adapter
pm2 save

# 4.2 Next.js (chat page)
pm2 start singclaw-dynamic/ecosystem.config.js

# 4.3 Nginx reload (if changed)
sudo nginx -t && sudo nginx -s reload
```

## 5. 验证四件套
```bash
ss -tlnp | grep -E ':(3001|8000|24135)\b' | head -5
curl -fsS http://127.0.0.1:8000/v1/mvp/health
curl -fsS http://127.0.0.1:3001/api/mvp-proxy
curl -fsS -X POST https://app.singclaw.xyz/api/mvp-proxy \
  -H "Content-Type: application/json" -H "X-MVP-Code: <from .env.local MVP_DEFAULT_CODE>" \
  -d '{"message":"hi","session_id":"smoke-test","stream":true}' \
  | grep -E '^event:|^data:' | head -5
```

全过 = OK。任何一个不通过 → 查 [docs/SINGCLAW_MVP_ISSUES_LOG.md](./docs/SINGCLAW_MVP_ISSUES_LOG.md)（最近几个 ISS 已有修复方法）。

---

## 6. 上手后**先读**这些（一周内必读）

| 顺序 | 文件 | Why |
|---|---|---|
| 1 | [PROJECT_CHARTER.md](./docs/SINGCLAW_MVP_PROJECT_CHARTER.md) | 整个项目是干嘛 |
| 2 | [DELIVERABLES.md](./docs/SINGCLAW_MVP_DELIVERABLES.md) | 当前活什么服务 |
| 3 | [ISSUES_LOG.md](./docs/SINGCLAW_MVP_ISSUES_LOG.md) | 哪些坑不要踩 |
| 4 | [RISK_REGISTER.md](./docs/SINGCLAW_MVP_RISK_REGISTER.md) | 风险缓解 |
| 5 | [LESSONS_LEARNED.md](./docs/SINGCLAW_MVP_LESSONS_LEARNED.md) | 别人犯过的错 |
| 6 | [HANDOFF_BUNDLE.md](./docs/SINGCLAW_MVP_HANDOFF_BUNDLE.md) | 跟我同一份 worker onboarding |

---

## 🚨 关键注意事项

1. **永远别把 `.env*` commit 进 git**（已经被 gitignore，但 BFG 清历史是另一回事）
2. **adapter 进程要在 pm2，不在 nohup**（详见 ISS-004）
3. **`pnpm run build` 必跑在 pm2 restart 之前**（详见 ISS-005 deploy 验证门）
4. **公网裸奔问题（H Sing 已 pending，未修完）**：见 ISS-006 / RISK_REGISTER R-03
5. **whoami**: Maxink 的 SOUL/MEMORY/AGENTS/IDENTITY.md 是**个人风格 + 上下文**，clone 后自动获得。**改前请看 README + 跟 H Sing 确认**。

— End of Quick Start —
