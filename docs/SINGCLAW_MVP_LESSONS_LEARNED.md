# SingClaw MVP — 经验教训 (Lessons Learned)
**最后更新**: 2026-07-05 12:30 UTC

---

## L-01 · 致命: "看起来好的部署"≠"真的部署了"

### 现象
2026-07-05 凌晨，H Sing 报告 chat 按钮卡"取消"。
Maxink 第一轮 debug → 误判 chat page bug。
实际情况：源码 `09e934c` 含 bugfix2，但 `.next/server/app/api/mvp-proxy/route.js` 是 7h 前的 S8 旧版。
pm2 跑的 HTML 200 但 SSE 流永远是旧实现的死状态。

### 为什么
1. `git log -1` 没在 deployment 里跑——HEAD 跟实际服务脱节
2. `pnpm run build` 没作为强制动作（commit 不等于 deploy）
3. pm2 没配置 build artifact version 比对

### 教训
1. **必须有 deployment 验证门**：build → pm2 restart → **curl 验证 stage 字符串匹配 HEAD**
2. **不要被 `HTTP 200` 骗**：流式端点 200 不代表流式 OK，必须真 stream
3. **优先怀疑上游而不是前端**：用户卡在按钮，大概率不是按钮的 bug

### 防再发生
- 加 `scripts/deploy-with-verify.sh` (10 min)
- `ecosystem.config.js` 加 post_deploy curl
- `openclaw_gateway_watchdog.py` 加 stage 比对

---

## L-02 · 守护进程必须有，不是 nice-to-have

### 现象
Adapter 用 `nohup python3 -m uvicorn ... &`，shell exit 后进程成孤儿。
host 重启 → 整个 BFF 死，chat 全瘫。
**没人通知**，因为没人在 watch adapter。

### 为什么
- 初版脚本 "能跑就行"，没考虑 host lifecycle
- pm2 已配给 singclaw-dynamic 和 umami，遗漏 adapter
- watchdog 巡检只覆盖 nginx/proxy 端口，没覆盖 `:8000`

### 教训
1. **每个 production 进程都在 pm2 或 systemd**
2. **watchdog health probe 必须包含所有 5xx 入口**
3. **进程列表"看得见"是 P0 hygiene**：每周 audit pm2 ls + ps auxf 跨对一次

### 防再发生
- pm2 start adapter
- watcher 加 `/v1/mvp/health` 巡检 + auto-restart
- 月初 audit

---

## L-03 · 环境变量文件是泄漏面

### 现象
6 个 `.env*` 文件 mode `0644`，含 Bot Token、ETH 私钥、Clerk 测试 key 等。
任何在该 host 有 shell 的用户能直接 cat。
**外加** `crypto/.env` 已被 git tracked，历史也含明文。

### 为什么
1. 默认 mode 是 644，没人在意过
2. `.gitignore` 没含 `.env*`（部分目录漏了）
3. 我自己 2026-07-04 workspace setup 时写过这些 key，半年没管

### 教训
1. **`.env*` 默认 mode 600**，写入时 chmod
2. **`git rm --cached` 不算修，要 rewrite history**
3. **真正方便**: secrets manager（Vault / age / sops），不要明文

### 防再发生
- `chmod 600` 立即
- 全 `.gitignore` 严格
- 改用 openssl age 加密 + gitattributes filter
- revoke 旧 key

---

## L-04 · debug 时第一直觉 vs 第二直觉

### 现象
同一次 ISS-001，Maxink 第一轮诊断是 chat page 自身 bug（错），第二轮才命中真根因。

### 为什么
- 启发式 1: 用户描述"按钮卡" → 假设是前端
- 没验证: 实际是上游 (`/v1/mvp/*` 502 之后，前端 SSE 起不来 → 按钮永远显示"取消中")

### 教训
1. **复杂 bug 三层诊断**: 前端 → BFF → 上游. 缺一不可。
2. **502 vs 200 是关键分界**: 你的页面 200 不代表全部链路 200
3. **第一次不要给最终结论**: 列 3 个候选 hypothesis，依次排除

### 防再发生
- 凡是流式/UI 错误，先 curl 上游
- debug 笔记要列 hypothesized-vs-actual 表格

---

## L-05 · 事件驱动 vs 文档驱动

### 现象
所有 PMO 关键节点（bugfix、sprint 结论、风险）都没结构化文档化，直到 H Sing 主动问"还有什么需要留意的"才盘点。

### 为什么
- Maxink 习惯日常 chat 回顾，但不写文档
- memory/ 目录有 daily notes，但没 hard 化的项目文档
- 一周后我（或接手的 agent）会忘了今晚发生了什么

### 教训
1. **每次故障修复后 30 分钟内写 PMO 日报**（已做：`memory/2026-07-05-pmo-s9.5.2-loop.md`）
2. **每次 Sprint 结束写 project docs**（本次就是：本次结束 + 项目文档化）
3. **用模板而不是自由文本**（已采纳 PROJECT_CHARTER.md）

### 防再发生
- "每次 PMO 结尾必须写 docs" 是 SOUL.md 已声明
- HANDOFF.md 是跨 session 入口

---

## L-06 · 不要假设生产环境无 access

### 现象
2 天前我添加 key 时，以为 server 不会被外人访问。但 `43.156.239.53` 是真公网 IP，`app.singclaw.xyz` 在 Cloudflare 防护下走 https，但没有 IP allowlist。

### 为什么
1. 个人 MVP 项目常被默认为 "只有自己用"
2. H Sing 公网 IP 一旦泄漏就是裸奔
3. dev_bypass 看起来无害（谁都猜中 "mvp-dev-bypass-2026"）

### 教训
1. **永远假设 prod 是公网**: 即使是个人项目，不依赖 IP 信任
2. **任何认证 code 默认私有**: 32 位随机，至少
3. **OLL (open access list) 显式配置**: 而不是 deny-all（容易忘）

### 防再发生
- nginx IP allowlist
- MVP_DEFAULT_CODE 留空强制 header 必传
- 月初 audit auth.log

---

## L-07 · 跨 session / 跨 agent 协同

### 现象
H Sing 切换设备 / 多机器时，session 不共享。今天他提出 "其他电脑 codex 怎么接"，意识到没结构化 handoff 机制。

### 为什么
- 单 agent 项目默认是单点
- 没 HANDOFF.md 时，换设备等于从零开始
- memory/ 是 daily notes，缺 project-level context

### 教训
1. **PROJECT_CHARTER.md + HANDOFF.md 是 onboarding 必备**
2. **配置变化要 commit + push，不能只在 memory/**
3. **多 agent 协同要 RACI**

### 防再发生
- 已加 HANDOFF.md + 本项目文档包
- 跨 session memory_search 之前，先读 HANDOFF

---

## L-08 · 文档也要追溯性

### 现象
有些 daily notes 写了"对接已通"，但没 commit reference，没日期精确度。半年后查无可考。

### 为什么
- 写 memory 时只关心当下共识，没关心未来可审计性
- 没固定模板，导致每篇风格不同

### 教训
1. **每个事件 + commit SHA + 时间戳**
2. **每个决策有 ATTRIBUTION: 谁决定、为何决定、否则如何**

— End of Lessons Learned —
