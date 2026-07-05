# Secrets Handbook — SingClaw MVP
**目的**: 让接手者**不踩坑**——知道哪个变量从哪来、什么值、怎么拿、丢了怎么办。
**生成时间**: 2026-07-05 13:05 UTC

---

## 🛑 第一个警告
1. **never commit .env into git**（已在 `.gitignore` 排除，但偶尔误 commit 出现）
2. **never share via chat / email**（用 scp / 1Password / age 加密）
3. **轮换期 = 90 天**，到期会换

---

## 1. 必需的 env 文件清单

| 文件 | 用途 | **最小集** |
|---|---|---|
| `singclaw-dynamic/.env.local` | Next.js chat page | ✅ 必须 |
| `crypto/.env` | 加密 agent + Telegram | ✅ 必须 |
| `linkedin-agent/.env` | LinkedIn 发帖 agent | ❌ 只 LinkedIn 功能才需要 |
| `worldx-demo/.env` | OpenRouter + NVIDIA NIM keys | ❌ 只 worldx 功能才需要 |
| `singclaw-react/.env.local` | 老 supabase client | ❌ 旧代码，新 MVP 不用 |
| `singclaw-site/contracts/.env` | ETH 合约部署 | ❌ 部署合约才需要 |

---

## 2. `singclaw-dynamic/.env.local` (核心)

```bash
# === Next.js / Clerk ===
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_...   # Clerk 前端
CLERK_SECRET_KEY=sk_...                    # Clerk 后端
NEXT_PUBLIC_SUPABASE_URL=https://...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=sb_service_role_... # ⚠️ 提权，慎传

# === MVP Bridge ===
MVP_DEFAULT_CODE=mvp-dev-bypass-2026        # bypass code, currently public, see ISS-006
MVP_CODES=mvp-singclaw-hsing-2026,mvp-dev-bypass-2026

# === Cron / Output ===
CRON_OUTPUT_TOKEN=replace_with_strong_token
```

**申请方式**:
- Clerk: 创 https://dashboard.clerk.com → API Keys → 选 "Production"
- Supabase: 创 https://supabase.com → New project → Settings → API
- MVP codes: **H Sing 手动发一次性，生成方式见下面 §6**

## 3. `crypto/.env`

```bash
# === Telegram bot (B path MVP Adapter) ===
TELEGRAM_BOT_TOKEN=...           # @BotFather /newtoken → /revoke 重生
TELEGRAM_CHAT_ID=6509109244      # H Sing 个人 chat ID

# === ETH 私钥 ===
PRIVATE_KEY=0x...                # ⚠️ 真以太坊钱包钥匙！0 ETH 时无害，有 ETH 时 100% 控制权

# === Optional CG Pro ===
CG_API_KEY=...                   # coingecko pro key，可选
```

**轮换 SPO**: Telegram token 是**最高优先级**——任何机器只能有"只发"权限 (via bot chat id allowlist)。

## 4. `linkedin-agent/.env`

```bash
LINKEDIN_EMAIL=...
LINKEDIN_PASSWORD=...             # ⚠️ 真实密码，能登 LinkedIn 任何时候
LINKEDIN_POST_TIME=14:00          # HH:MM Asia/Shanghai
REVIEW_DEADLINE=12:00             # review 截止
```

**强建议**:
- LinkedIn 账号**要开 2FA**（OTP 短信），避免密码泄漏直通
- H Sing 临时给破解 agent 时，先把 2FA 关；结束后再开

## 5. `worldx-demo/.env` (third-party LLM)

```bash
ORCHESTRATOR_API_KEY=...
ORCHESTRATOR_BASE_URL=https://openrouter.ai/api/v1
ORCHESTRATOR_MODEL=...
IMAGE_GEN_API_KEY=nvapi-...
IMAGE_GEN_BASE_URL=https://integrate.api.nvidia.com/v1
IMAGE_GEN_MODEL=...
VISION_API_KEY=...
SIMULATION_API_KEY=...
```

**轮换 SO**: NVIDIA / OpenRouter 配额到上限后自动 fail，不用手动 revoke。

## 6. 怎么生成强 code

```bash
# 32 位 hex 一次性 code
openssl rand -hex 16
# 输出: 0a1b2c3d4e5f6789...  (32 chars)
```
H Sing 决定后:
```bash
echo "MVP_CODES=$(openssl rand -hex 16),$(openssl rand -hex 16)" \
  >> singclaw-dynamic/.env.local
chmod 600 singclaw-dynamic/.env.local
pm2 restart singclaw-dynamic
```

## 7. 怎么传 secrets 给新人（推荐流程）

**❌ 不要**:
- 用 Telegram 发（明文落 history）
- 用 GitHub PR / commit（泄漏到 git）
- 用 email（多备份）

**✅ 应该**:
1. **SCP** (内网):
   ```bash
   scp /root/.openclaw/workspace/singclaw-dynamic/.env.local \
       user@other-host:/root/.openclaw/workspace/singclaw-dynamic/.env.local
   ```
2. **Age 加密** (跨网/不信任通道):
   ```bash
   # H Sing 端:
   tar czf - -C /root/.openclaw/workspace singclaw-dynamic/.env.local crypto/.env \
     | age -r <recipient-age-pubkey> -o /tmp/secrets-$(date +%F).age
   # 通过 Telegram 发 .age 文件（加密体，不会泄漏）
   
   # 接收端:
   age -d -i recipient-key /tmp/secrets-2026-07-05.age | tar xzf - -C /path/
   chmod 600 /path/.env*
   shred -u /tmp/secrets-2026-07-05.age
   ```
3. **1Password share link** (商业 SSO)
4. **H Sing 临时口头给（不记录）**，新人手动写进文件

## 8. 验证 secrets 是否正确

```bash
# 装完后必跑:
cd /root/.openclaw/workspace/singclaw-dynamic

# Clerk OK?
node -e "console.log(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.slice(0,15) || 'MISSING')"

# MVP code OK?
node -e "console.log(process.env.MVP_CODES?.split(',').length || 'MISSING')"

# Supabase OK?
curl -fsS -H "apikey: $NEXT_PUBLIC_SUPABASE_ANON_KEY" \
  "$NEXT_PUBLIC_SUPABASE_URL/rest/v1/" -o /dev/null -w "%{http_code}\n"
```

## 9. 漏 secrets 时紧急处理

| Key | 紧急动作 |
|---|---|
| CLERK_SECRET_KEY 泄漏 | Clerk dashboard → "Rotate key"（立即 revoke 旧） |
| SUPABASE_SERVICE_ROLE_KEY | Supabase dashboard → Settings → API → "Generate new service role" |
| TELEGRAM_BOT_TOKEN | @BotFather → /revoke → /newtoken |
| ETH PRIVATE_KEY | 立即 transfer 资产 + 重生成 |
| LINKEDIN_PASSWORD | 修改密码 + 检查登录会话 |
| VERCEL_OIDC_TOKEN | Vercel dashboard → Settings → Tokens → Revoke |
| MVP codes | `openssl rand -hex 16` 替换 + pm2 restart |

---

## 10. 当前**已知未轮换**的 secrets（TODO 优先级 P0）

按 [RISK_REGISTER.md R-05](./SINGCLAW_MVP_RISK_REGISTER.md)：

| Secret | 现状 | H Sing 责任 |
|---|---|---|
| TELEGRAM_BOT_TOKEN | 6 周未轮换 | revoke + new |
| LINKEDIN_PASSWORD | 不明（可能 1 月没动） | 改 + 启 2FA |
| VERCEL_OIDC_TOKEN | 不明 | 查 → revoke |
| ETH PRIVATE_KEY | 不明余额，先查 | transfer + 重生成 |

— End of Secrets Handbook —
