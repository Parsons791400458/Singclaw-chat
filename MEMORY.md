# MEMORY.md — 长期记忆核心

## 📌 2026-02-21 关键决策（P&G职业经理人角色确认）
- ✅ 身份定位：**P&G职业经理人**，负责 g-crypto-alpha 与 g-ai 两个 agent 的全生命周期管理  
- ✅ g-crypto-alpha 当前任务：Hyperliquid 自动化交易系统（方案A：API集成）  
- ✅ 已产出：HyperliquidAPI / TrendFollowingStrategy / CryptoBot 三模块代码框架  
- ✅ 交付要求：每日至少 2 个可验证产出（代码/报告/数据文件），阻塞超30分钟必须上报  

> *注：此条为记忆锚点，后续所有 agent 任务均需引用本条 ID*

## 📌 2026-07-02 默认模型切换（M3 上位 → token0 下线）
- ✅ 决策链：
  1. H Sing 指示默认模型从 `token0/glm-5.2` 改为 `minimax/MiniMax-M3`（token0 不通）
  2. H Sing 进一步指示**删除 token0**：从 default fallback 链中移除
- ✅ 最终配置 `agents.defaults.model`：
  ```json
  {
    "primary": "minimax/MiniMax-M3",
    "fallbacks": ["deepseek/deepseek-v4-pro", "openai/gpt-5.5"]
  }
  ```
- ✅ 已清理：原 fallback 链中无效条目 `openai-compatible/mydamoxing/glm-5.2-20260613`（不存在 provider）
- ✅ gateway 已 restart 验证：uptime 重置, /health 200
- ✅ token0 已**全清**（H Sing 2026-07-03 02:35 指示）：
  - `models.providers.token0` provider 定义：删（实际 edit 时发现已被某次清理移除，present 时再清一次，0 引用）
  - `agents.defaults.models["token0/glm-5.2"]`：删
  - `agents.list[g-career-crawler].models["token0/glm-5.2"]`：删
  - 顺手清掉 `g-career-crawler.models["mydamoxing/glm-5.2-20260613"]`（同位置死引用）
- ✅ 最终状态（实测 2026-07-03 02:45）：
  - `models.providers`：`['nvidia-build','deepseek','glmcode','openai','minimax','zhipu']`
  - `agents.defaults.model`：`{primary: minimax/MiniMax-M3, fallbacks: [deepseek/deepseek-v4-pro, openai/gpt-5.5]}`
  - `g-career-crawler.models`：`[minimax/MiniMax-M3, deepseek/deepseek-v4-pro]`
  - gateway pid 1173763 running, /health 200
- 📁 备份：~/.openclaw/openclaw.json.bak-20260702-102051（最后一次清理前）

## 📌 2026-07-01 部署流水线铁律（H Sing 反馈 → 已固化）
- ❌ 旧判据：`git push origin main` 成功 ≠ URL 可访问  
  - 教训：singclaw-site 推送后，Vercel Git 集成偶发不触发，必须手动 `vercel --prod --yes`  
  - H Sing 反馈 `https://singclaw.xyz/docs/security/` 404（日报文件本身 200，缺目录落地页）  
- ✅ 新判据：每次「Wiki 同步 / 部署」必须 `curl -I` 实测目标 URL 返回 200 才算交付  
- ✅ 落地修复：
  1. docsify 单页 SPA 模式，所有 `docs/<section>/` 必须有 `README.md` 作为目录落地页
  2. Vercel 静态托管不自动解析 README，vercel.json 加 rewrite: `/docs/security` → `/docs/security/README.md`
  3. 侧边栏 `_sidebar.md` 在每段首插入「XX 中心」入口链接
- 🔁 sync-all-wiki.sh 流水线已存在（rsync docs→public/docs + git push + vercel --prod），下一步要把 `curl 200 验证` 集成进 deploy-security-report.sh

## 📌 2026-07-05 Chat 卡"取消"真根因 + Loop 生产就绪
- ✅ **真根因找到了**：不是 chat page 的 bug，是上游 FastAPI Adapter 进程死掉（pm2 没注册 adapter）+ Next.js production build 是 7h 前的 S8 旧版（mvp-proxy stage = `S8-BFF-mvp-proxy`），singclaw-dynamic 仓库 HEAD `09e934c` 根本没跑
- ✅ **修法**：
  1. nohup uvicorn adapter.server:app (pid 2423716, 127.0.0.1:8000)
  2. `pnpm run build` 刷新 .next
  3. `pm2 restart singclaw-dynamic` (新 pid 2426788)
- ✅ **验证**：mvp-proxy stage = `S9.5.2-C-BFF-mvp-proxy` 含 bugfix2 包装；多轮上下文工作（turn2 记住 turn1 名字）；5 轮 HTTP 200 干净 EOF
- ❌ **新发现的盲点**：FastAPI Adapter 不在 pm2 也不在 systemd → 重启 host 会再掉。**建议**挂 pm2：`pm2 start 'uvicorn adapter.server:app --port 8000 --app-dir /root/.openclaw/workspace/SINGCLAW-MVP/adapter' --name singclaw-mvp-adapter`
- ❌ **生产上没跑的真 fix**：源码 commit 09e934c 但 build 没刷新，pm2 进程是 7h 前的旧 build → 部署链路缺验证门（建议加 `post-deploy: curl /api/mvp-proxy | grep -q S9.5.2 || exit 1`）

## 📌 2026-07-02 Sprint log 目录归属铁律（Sprint 185 立约）
- ✅ `memory/ssot-sprint-log/` 由 SSOT sprint cron (`ssot-hourly-sprint-20260617` + 别名 `SSOT·小时级Sprint` / `ssot-hourly-sprint`) 独占使用
- ✅ `scripts/audit_sprint_log.py` 已加 cronId 过滤；其他 cron（如 `Memory Dreaming Promotion` cronId `455bcbd8...`）若复用此目录需迁到子目录
- ❌ 反例：07-02 19:00 UTC `Memory Dreaming Promotion` 直接写 `2026-07-02-19.json`，因 schema 字段不匹配导致 audit_sprint_log exit 1 / perfect-state 95/100
- 🔁 治理：任何新 cron 如要写入 sprint log 体系，要么复用 contract `cronId` 别名（需先在 contract.json 注册），要么迁到独立目录如 `memory/<cron-name>-log/`
