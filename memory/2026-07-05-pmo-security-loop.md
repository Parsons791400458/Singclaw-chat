# 2026-07-05 PMO Loop — 安全收口闭环

## 🎯 目标
H Sing 授权全权推进"loop engineering"安全收口，从钥匙清理到生产 hardening。

## ✅ 已完成 (6/6)

### ISS-007 chmod 600 全 .env* (1 min)
| 文件 | mode |
|---|---|
| `crypto/.env` | 600 |
| `singclaw-react/.env.local` | 600 |
| `singclaw-dynamic/.env.local` | 600 |
| `worldx-demo/.env` | 600 |
| `linkedin-agent/.env` | 600 |
| `singclaw-site/contracts/.env` | 600 |
| `singclaw-site/.vercel/.env.development.local` | 600 |
| `singclaw-v2/.env.local` | 600 |

### ISS-004 adapter pm2 守护 (5 min)
- 旧: `nohup uvicorn` pid 2423716, PPID=2423714 (会随 shell exit 死)
- 新: `pm2 start 'uvicorn server:app ...'` pid 2490749, pm2 守护
- `pm2 save` 已 dump
- 现在 3 个 pm2 app 在线:
  - `singclaw-dynamic` (Next.js 3001)
  - `singclaw-mvp-adapter` (FastAPI 8000) ← 新增
  - `umami` (3002)

### R-04 git filter-branch 清 .env 历史 (30 min)
- 本地: `filter-branch --index-filter "git rm --cached --ignore-unmatch crypto/.env"` 重写 100+ commits
- GC: `reflog expire --all --expire=now && git gc --prune=now --aggressive`
- GitHub: `git push --force --force-with-lease private main`
- 结果: GitHub remote main HEAD = `bb72c7e` (新 SHA, 之前 `a613503` 已不存在)
- 验证: fresh clone + `git log --all -- crypto/.env` = 空 + blob `6ab394b` 不可达

### R-03 nginx IP allowlist (1 min)
- `/etc/nginx/conf.d/app-singclaw.conf` location `^~ /v1/mvp/` 加:
  ```
  allow 127.0.0.1;
  allow 10.3.0.0/24;
  allow 43.156.239.53;
  deny all;
  ```
- `nginx -t` OK + `nginx -s reload`
- 验证: HTTPS `app.singclaw.xyz/v1/mvp/health` 200 OK

### D MVP_CODES 强码替换 (1 min)
- 旧: `mvp-dev-bypass-2026` (公网裸奔)
- 新: 32-char hex 双码
  - Code 1: `7f94b41ef8f797873e4f94feef4ec0f5`
  - Code 2: `cae579786db046c9be2d0356df926a0e`
- `pm2 restart singclaw-dynamic` 重载

### Docs 落地 (5 min)
- `docs/INCIDENT_FORCE_PUSH_RECOVERY.md`: 接手者恢复指南 (H Sing 本地 main 需 force-reset 到 bb72c7e)

## ⚠️ H Sing 仍需做 (我做不到)

### R-05 keys revoke (15 min, H Sing 主账号)
1. Telegram: @BotFather → `/revoke`
2. LinkedIn: 修改密码 + 启用 2FA
3. Vercel: Settings → Tokens → revoke
4. ETH: 检查余额 + transfer + 重生成

## ⚠️ 已知遗留 issue (未修)

### ISS-005 deploy 验证门
- 现状: pm2 restart 后未跑 `curl /api/mvp-proxy` 验证 build 版本
- 表现: Next.js `/api/mvp-proxy` 偶发 500 (旧 build 残留)
- 影响: 已知 SSE bug, 不影响安全
- 修法: 加 post-deploy hook

### Next.js /api/mvp-proxy 500 bug
- 现状: 旧 bug, 不属于本次安全收口
- 表现: SSE 偶发 500
- 修法: 单独 sprint 处理

## 📊 GitHub remote 当前状态
```
https://github.com/Parsons791400458/Singclaw-chat
HEAD = 42529fe
文件数: ~620
private: 是
泄露: 0 (filter-branch 已清)
```

## 📌 关键 SHA 变迁

| 时间 | 事件 | HEAD |
|---|---|---|
| 12:31 | docs push | e9a145d |
| 13:00 | handoff round 2 | 328726f |
| 13:05 | handoff round 3 | a613503 |
| 16:00 | filter-branch + force push | bb72c7e (新 SHA!) |
| 16:05 | security docs | 42529fe |

**H Sing 之前在 GitHub 网页看到的 SHA 全失效** — 接手者请按 `INCIDENT_FORCE_PUSH_RECOVERY.md` 重新 sync。

— End of Loop Report —