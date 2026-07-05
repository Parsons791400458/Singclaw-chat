# SingClaw MVP — 资源计划 (Resource Plan)
**最后更新**: 2026-07-05 12:30 UTC

---

## 1. 人力 (Human Resources)

### 1.1 核心团队
| 角色 | 姓名 | 时间投入 | 当前状态 |
|---|---|---|---|
| 项目发起人 / Sponsor | H Sing (syberh) | ~30% | 在线 (Telegram 全天) |
| 主助手机器人 / PMO | Maxink | ~50% (H Sing 启用时) | 在线 |
| 多机协同 / Codex | 未来接手者 | 不定 | 未上 |

### 1.2 临时资源
- **Codex**: 尚未正式纳入；今晚 PMO 留 HANDOFF.md 给 Codex 拉起
- **小夏 / ClawFi / 等其他 agent**: 不参与 MVP 主线

### 1.3 RACI
| 任务 | R (Responsible) | A (Accountable) | C (Consulted) | I (Informed) |
|---|---|---|---|---|
| adapter pm2 | Maxink | H Sing | - | - |
| 安全 chmod | Maxink | H Sing | - | - |
| keys revoke | H Sing | H Sing | Maxink | - |
| Chat page UI | Maxink + Codex | H Sing | - | - |
| Adapter backend | Maxink | H Sing | - | - |
| Nginx config | Maxink | H Sing | - | - |

---

## 2. 计算资源 (Compute Resources)

### 2.1 生产服务器 (Production)
- **VM 名**: VM-0-9-opencloudos
- **OS**: opencloudos 9 kernel 6.6.117 x86_64
- **网络 IP**: 10.3.0.9 (内网), 43.156.239.53 (公网出)
- **资源 (估算)**: 4 vCPU / 8 GB RAM / 100 GB SSD (待 verify)
- **Tenant**: Tencent Cloud
- **位置**: Tencent Cloud (region 待 verify)

### 2.2 服务占用
| 服务 | 进程 / 端口 | 内存 (估算) | CPU (估算) |
|---|---|---|---|
| FastAPI Adapter | 8000 | 30 MB | <1% idle |
| Next.js singclaw-dynamic | 3001 | 60 MB | <1% idle (尖峰时 20%) |
| Umami | 3002 | 80 MB | <1% idle |
| Nginx | 80/443/8443 | 100 MB | <2% |
| OpenClaw Gateway | 24135 | 50 MB | <1% |
| Postgres | 5432 (本地) | 100 MB | <1% |
| Chrome (H Sing 用) | 9222 | 200 MB | 杂项 |
| **合计峰值** | | **~620 MB** | **~10%** |

### 2.3 端口清单
```
22    sshd
80    nginx (HTTP)
443   nginx (HTTPS)
3001  next-server singclaw-dynamic
3002  next-server umami
5432  postgres
8000  python3 uvicorn adapter (loopback only)
8443  nginx (alternative listen)
9222  chrome debug
24135 openclaw gateway
```

---

## 3. 外部服务 (External Services)

### 3.1 LLM Provider
| Provider | 模型 | 用途 | 月配额估算 |
|---|---|---|---|
| miniMax | M3 | 默认 | ~$25/月 |
| DeepSeek | deepseek-v4-pro | fallback 1 | ~$5/月 |
| OpenAI | gpt-5.5 | fallback 2 | ~$20/月 |
| **合计** | | | **~$50/月** |

### 3.2 第三方 API
| 用途 | 服务 | 备注 |
|---|---|---|
| 加密资产 | CoinGecko API (CG_API_KEY) | demo |
| Crypto 巡检 | Binance Public + Hyperliquid | public (无 key) |
| 监控 | Umami (自托管) | n/a |

### 3.3 待办 / 需要开通
- 邮件发送 (Sendgrid 等) — slack snapshot 太长时用
- Cloudflare Access — 公网鉴权
- **真 OpenAI/Anthropic function calling** — S9.5.3

---

## 4. 软件依赖 (Software Dependencies)

### 4.1 系统层
- nginx 1.26.3
- Python 3.11+ + FastAPI 0.139.0 + uvicorn
- Node 22.22.0
- pnpm 10.x
- pm2
- sqlite3
- Postgres 14+ (本地)

### 4.2 应用
```
singclaw-dynamic/
  next: 14.2.35
  react: ^18
  supabase/ssr: ^0.10.2
  supabase-js: ^2.104.1
  clerk/nextjs: ^6.39.3
  swr: ^2.2.5
  react-markdown: ^10.1.0
SINGCLAW-MVP/adapter/
  fastapi: 0.139.0
  uvicorn[standard]
  pydantic
```

### 4.3 待升级 (Backlog)
- Clerk SDK 升级到 v7+ (singclaw-v2 用的)
- Next.js 14 → 15 (singclaw-v2 已用 Next 16)
- Postgres 版本检查 (TBD)

---

## 5. 数据资产 (Data Assets)

| 类型 | 位置 | 大小 | 备份策略 | 隐私等级 |
|---|---|---|---|---|
| chat turns + audit | db.sqlite3 | 60 KB / 增长 5 KB/h | 无 (待办) | 中 (含 H Sing 个人对话) |
| knowledge base | /shared/knowledge-base (待办) | TBD | TBD | 中 |
| public downloads | singclaw-dynamic/public/downloads/ | 6 PDF/DOCX | git-track? 否 | 高 (HSBC 真实简历/材料) |
| static site | /var/www/singclaw | ~100 MB | cron 每日 backup | n/a |
| OpenClaw skills | /root/.openclaw/skills | TBD | git-tracked | n/a |

---

## 6. 财务资源 (Financial Resources)
- **总预算**: ~$50/月 (LLM 配额)
- **VM**: 含在 Tencent platform 计费
- **Domain**: singclaw.xyz (registrar age 93d)
- **GitHub**: free tier（私有 repo with Pro 账号）

---

## 7. 资源风险 (Resource Risks)
- **R-12 (单兵)**: 见 `RISK_REGISTER.md`
- **R-13 (LLM quota)**: 同
- **R-11 (单点)**: 同

---

## 8. 资源节奏 (Resource Cadence)

| 周期 | 任务 | 负责人 |
|---|---|---|
| 每日 | security audit（key + .env mode + chat 可用性） | Maxink / cron |
| 每周 | git status + 落后推送 + PMO 写入 | Maxink |
| 每周 | LLM 配额审计 | H Sing / Maxink |
| 每月 | db backup + vacuum | 待做 |
| 每季度 | Risk Register 重审 | H Sing |
| 每半年 | 全资源 audit | H Sing |

— End of Resource Plan —
