# SingClaw MVP — 问题记录 (Issue Log)
**最后更新**: 2026-07-05 12:30 UTC

## 格式
```
ID | 标题 | 优先级 | 状态 | 报告日 | 解决日 | 根因 | 解决方案
```

---

## 已解决 (Resolved)

### ISS-001 · Chat 发送按钮卡"取消"
- **优先级**: P0 (production outage)
- **状态**: ✅ 已解决
- **报告日**: 2026-07-05 03:00+ UTC
- **解决日**: 2026-07-05 04:08 UTC
- **根因 (复合)**:
  1. FastAPI Adapter 未在 pm2 守护 (nohup 进程死掉)
  2. Next.js production build 是 7h 前的 S8 旧版 (源码 HEAD 09e934c 含 bugfix2 但未 rebuild)
- **诊断路径**:
  - 第一轮误判 → chat page 自身 bug
  - 第二轮正确诊断 → adapter 死 + build 旧 → chat page 实际从未用过 fix
- **解决方案**:
  1. nohup restart adapter: `python3 -m uvicorn server:app --host 127.0.0.1 --port 8000 --app-dir SINGCLAW-MVP/adapter`
  2. `pnpm run build` (in singclaw-dynamic/)
  3. `pm2 restart singclaw-dynamic`
  4. 验证 `/api/mvp-proxy` stage = `S9.5.2-C-BFF-mvp-proxy`
- **影响**: 4 个小时左右部分用户的流式聊天
- **教训**: 见 `LESSONS_LEARNED.md` L-01

### ISS-002 · Clerk middleware 配置缺失导致 MIDDLEWARE_INVOCATION_FAILED
- **优先级**: P2
- **状态**: ✅ 已解决
- **报告日**: 2026-06-末
- **解决日**: 2026-06-末
- **根因**: Clerk 未配置 publishable key 而 middleware 仍走 Clerk auth
- **解决方案**: middleware 绕开 Clerk 路径（commit `de3a0b1`）
- **影响**: 个别首次访问页面报 500
- **教训**: middleware 应优先 fail-open, fail-closed 仅对已配置路径

### ISS-003 · npm clawfi 工具 import 错误
- **优先级**: P3
- **状态**: ⚠️ 部分解决（clawfi 项目独立）
- **详细**: 不在本 MVP 范围

---

## 进行中 / 待办 (Open)

### ISS-004 · Adapter 进程未守护 (P0.1)
- **状态**: 📋 待办
- **描述**: nohup python 进程 PPID 是 shell，shell 一死进程成孤儿
- **阻塞**: 重启 host 后 5xx 全网（包括 H Sing 当时用的 chat）
- **解决路径**:
  ```bash
  pm2 start 'python3 -m uvicorn server:app --host 127.0.0.1 --port 8000 --app-dir /root/.openclaw/workspace/SINGCLAW-MVP/adapter' \
    --name singclaw-mvp-adapter
  pm2 save && pm2 startup
  ```
- **估计工作量**: 5 分钟
- **接受者**: 未来接手者

### ISS-005 · 源码 HEAD 跟 build 脱节，无验证门
- **状态**: 📋 待办
- **描述**: `.next/server/app/api/mvp-proxy/route.js` 时戳可落后源码 7h，pm2 跑的是旧 build
- **解决路径**:
  - 写 `scripts/deploy-with-verify.sh`:
    ```bash
    cd singclaw-dynamic
    pnpm run build
    pm2 restart singclaw-dynamic
    sleep 5
    curl -fsS http://127.0.0.1:3001/api/mvp-proxy | grep -q S9.5.2 || (
      echo "BUILD/DEPLOY MISMATCH"
      pm2 restart singclaw-dynamic
      exit 1
    )
    ```
  - 或在 `ecosystem.config.js` 加 post_deploy curl gate
- **估计工作量**: 10 分钟

### ISS-006 · `/api/mvp-proxy` 与 `/v1/mvp/*` 公网无鉴权
- **状态**: 📋 待办
- **描述**: 任何人在公网 POST 都会调 LLM，消耗 H Sing 的 token 配额
- **解决路径**:
  ```nginx
  # /etc/nginx/conf.d/app-singclaw.conf, 在 location ^~ /v1/mvp/ 内
  allow 43.156.239.53/32;     # H Sing 公网 IP
  allow 10.0.0.0/8;            # 内网/VPN
  deny all;
  ```
- **辅助**: `MVP_CODES` 改强码 + `MVP_DEFAULT_CODE` 留空
- **估计工作量**: 15 分钟

### ISS-007 · `.env*` 文件 mode 644 全员可读
- **状态**: 📋 待办
- **描述**: 6 个 .env 文件目前 mode 644，包括 Bot Token、ETH 私钥
- **解决路径**:
  ```bash
  chmod 600 /root/.openclaw/workspace/{crypto,singclaw-dynamic,singclaw-site,worldx-demo,linkedin-agent}/.env*
  ```
- **估计工作量**: 1 秒

### ISS-008 · 多个 key 未 revoke（需 H Sing 主账号操作）
- **状态**: 📋 待办
- **详细 key**:
  | Key | 位置 | 操作 |
  |---|---|---|
  | Telegram Bot | `crypto/.env` | @BotFather /revoke |
  | LinkedIn 密码 | `linkedin-agent/.env` | 修改 + 启 2FA |
  | Vercel OIDC | `.vercel/.env.development.local` | Settings → Tokens |
  | ETH 私钥 | `crypto/.env` + `singclaw-site/contracts/.env` | 检查余额，转移，regenerate |

### ISS-009 · git 落后 origin/master 14 commit
- **状态**: 📋 待办
- **解决**:
  ```bash
  git push origin main
  ```
- **风险**: host 盘坏，新 commit 全丢（adapter/server.py / S9.5.2-D）
- **估计工作量**: 30 秒

### ISS-010 · `crypto/.env` 在 git 中 tracked
- **状态**: ⚠️ 危险
- **描述**: `crypto/.env` (含 TELEGRAM_BOT_TOKEN + ETH PRIVATE_KEY) 已 commit 进 git
- **解决**:
  ```bash
  cd /root/.openclaw/workspace
  git rm --cached crypto/.env
  # 同时清历史（BFG Repo-Cleaner 或 git filter-branch），但破坏性大
  # 实际止损: revoke 旧 key 后新建 secret，truncate history 是可选升级
  echo "crypto/.env" >> .gitignore
  git add .gitignore
  git commit -m "security: untrack crypto/.env from git"
  ```
- **估计工作量**: 5 分钟（不含 history rewrite）

### ISS-011 · fast-path 不支持 tools
- **状态**: 📋 待办
- **描述**: `/v1/mvp/chat/fast` 不支持 OpenAI/Anthropic function calling，模型尝试 `web_search` 报"工具暂不可用"
- **影响**: 用户问 "BTC 价格" 走 fallback 到模型记忆（不可信）
- **Sprint**: S9.5.3
- **估计工作量**: 1 day

### ISS-012 · db.sqlite3 无清理策略
- **状态**: 📋 待办
- **描述**: turns/audit 单库无 expire，无 VACUUM
- **解决**: 加 `v1/mvp/admin/purge?older_than_days=N` endpoint + cron vacuum

### ISS-013 · Clerk test key 在 production
- **状态**: 📋 待办
- **描述**: `pk_test_*` 在 bundle，限制多
- **解决**: 换 production key 或彻底删 Clerk（单租户不需要）

---

## Backlog for next sprint
- ISS-014 · S9.5.2-E export endpoint + UI 按钮
- ISS-015 · S9.5.2-F tool_call CSV/UI 强化
- ISS-016 · S9.5.3 Function Calling
- ISS-017 · Adapter 加 watchdog 自愈（健康失败 3 次自动 nohup 起）
- ISS-018 · 部署 SOP 文档化
- ISS-019 · cron-job 日志聚合分析

— End of Issue Log —
