# Environment — SingClaw MVP
**生成时间**: 2026-07-05 13:08 UTC

---

## 生产服务器

| 项 | 值 |
|---|---|
| **Host** | VM-0-9-opencloudos (Tencent Cloud) |
| **OS** | opencloudos 9 kernel 6.6.117 x86_64 |
| **Internal IP** | 10.3.0.9 |
| **Public IP** | 43.156.239.53 |
| **Region** | Tencent Cloud (ap-shanghai 假定) |
| **Resources (估)** | 4 vCPU / 8 GB / 100 GB |

## 安装工具版本

### 系统层

| Tool | Version | Verify |
|---|---|---|
| nginx | 1.26.3 | `nginx -v` |
| node | v22.22.0 | `node --version` |
| pnpm | 10.x | `pnpm --version` |
| python | 3.11+ | `python3 --version` |
| fastapi | 0.139.0 | `pip show fastapi` |
| uvicorn[standard] | latest | `pip show uvicorn` |
| pm2 | latest | `pm2 --version` |
| sqlite3 | 3.x | `sqlite3 --version` |
| git | 2.x | `git --version` |
| ssh | 8.x | `ssh -V` |

### 应用层（仅供参考）

- singclaw-dynamic: Next.js 14.2.35 / React 18 / TypeScript 5
- SINGCLAW-MVP/adapter: FastAPI 0.139.0 + uvicorn[standard]
- pm2 apps:
  - `singclaw-dynamic` (id=2)
  - `umami` (id=1)
  - `singclaw-mvp-adapter` (TBD, 见 ISS-004)

### 端口保留

```
22     sshd
80     nginx (HTTP)
443    nginx (HTTPS)
3001   singclaw-dynamic (Next.js)
3002   umami
5432   postgres (loopback)
8000   singclaw-mvp-adapter (loopback only)
8443   nginx (alternative listen, 历史遗留)
9222   chrome devtools (H Sing 浏览 devtools)
24135  openclaw gateway
```

## 文件系统布局

```
/root/.openclaw/                        # OpenClaw / Maxink 根
  ├── openclaw.json                     # 主配置（持有所有 secrets）
  ├── workspace/                        # 项目根（= git workspace）
  │   ├── singclaw-dynamic/             # Next.js chat page
  │   │   ├── .env.local                # secrets (mode 600)
  │   │   ├── ecosystem.config.js       # pm2 entry
  │   │   ├── src/app/                  # pages + api routes
  │   │   ├── public/downloads/         # 静态文件
  │   │   └── .next/                    # build artifact
  │   ├── SINGCLAW-MVP/                 # FastAPI Adapter + Docs
  │   │   └── adapter/
  │   │       ├── server.py             # main
  │   │       ├── fast.py               # fast-path LLM
  │   │       ├── db.sqlite3            # persists turns (mode 600 待改)
  │   │       └── logs/                 # uvicorn 日志
  │   ├── crypto/                       # crypto agent (含 .env)
  │   ├── linkedin-agent/               # LinkedIn agent
  │   ├── docs/                         # 本项目文档包
  │   ├── memory/                       # daily notes + PMO 日报
  │   ├── HANDOFF.md
  │   ├── README.md
  │   └── QUICK_START.md
  ├── skills/                           # OpenClaw skill 注册
  ├── cron-data/                        # cron 产出
  ├── logs/                             # gateway logs
  └── ...

/etc/nginx/conf.d/
  ├── app-singclaw.conf                 # nginx 反代 (主)
  ├── singclaw-mvp.conf                 # 8443 alt listen (历史)
  ├── oa-singclaw.conf
  ├── oa-starclaw.conf
  └── umami.conf

/var/www/singclaw/
  └── downloads/                        # 静态资源
```

## 时间约束

| 项 | 时间 |
|---|---|
| H Sing 时区 | Asia/Shanghai (UTC+8) |
| 工作时间 | 06:00 - 23:00 (preferred) |
| 主动联系窗口 | 07:00 - 23:00 (除 P0) |
| cron 时区 | 默认 UTC，按 cron tz 配置 |
| db / 日志时区 | epoch seconds (UTC) |

## 网络依赖

| 服务 | 访问方式 |
|---|---|
| github.com | SSH (deploy key) |
| miniMax | API (apiKey) |
| DeepSeek | API (apiKey) |
| OpenAI | API (apiKey) |
| Binance | public API (no key) |
| Hyperliquid | public API (no key) |
| CoinGecko | API (apiKey, optional) |
| LinkedIn | session cookie + cred |
| Telegram | Bot API (bot token) |

— End of Environment —
