# SingClaw MVP — 风险登记册 (Risk Register)
**最后更新**: 2026-07-05 12:30 UTC

## 风险评级标准
| 等级 | Likelihood | Impact |
|---|---|---|
| **P0** | 即将发生 / 已发生 | 业务中断 / 安全 / 不可恢复 |
| **P1** | 30 天内可能 | 业务降级 / 安全漏洞扩大 |
| **P2** | 90 天内可能 | 体验瑕疵 / 性能问题 |
| **P3** | 监控 | 技术债 |

---

## R-01 · Adapter 进程重启后掉
- **等级**: P0 (高可能 + 高影响)
- **来源**: 2026-07-05 真实事件（ISS-001 触发）
- **触发**: host 重启 / 容器调度 / OOM
- **影响**: 整个 `/v1/mvp/*` 流式聊天全瘫；chat page 卡"取消"
- **Mitigation**:
  1. 加 pm2 守护（5 分钟）
  2. 加 systemd unit（备选）
  3. 加 `/v1/mvp/health` 进 `openclaw_gateway_watchdog.py` 自动重启
- **Owner**: 接手者
- **Due**: P0 当天

## R-02 · 源码 HEAD 与 build 脱节
- **等级**: P0
- **来源**: ISS-001 复合根因
- **触发**: 源码 commit 但 `pnpm run build` 未跑或 pm2 未 restart
- **影响**: 部署的功能 ≠ 实际跑的功能，回滚失败用户无感知
- **Mitigation**:
  1. `scripts/deploy-with-verify.sh` 整合 build + restart + curl stage check
  2. ecosystem.config.js 加 post_deploy 校验
  3. 建立 "build id → stage → git commit" 一一映射
- **Detection**: `curl /api/mvp-proxy | grep stage`，如果 stage 不匹配 HEAD 即报警
- **Owner**: 接手者
- **Due**: P0 当天

## R-03 · `/api/mvp-proxy` 公网无鉴权
- **等级**: P0 (安全 + 财务)
- **来源**: 安全巡检 2026-07-05
- **触发**: 公网任何 IP POST
- **影响**:
  1. LLM token 配额消耗（每日可能上百美元）
  2. 聊天历史（turns）被外人污染（DB 写）
  3. 与 H Sing 同 session 命名冲突
- **Mitigation**:
  1. nginx IP allowlist（H Sing 公网 IP + VPN）
  2. 强码（32 位）+ `MVP_DEFAULT_CODE` 留空
  3. Cloudflare Access（一键 5 分钟）
- **Detection**: rate limit 报警 + DB 反常 turn_id 增长
- **Owner**: 接手者 + H Sing（account 操作）
- **Due**: P0 当天

## R-04 · `.env*` 文件 mode 0644
- **等级**: P0 (安全)
- **来源**: 安全巡检
- **触发**: 任何有 shell 的用户都可读
- **影响**: 同 server 多用户场景 key 全泄漏
- **Mitigation**:
  ```bash
  chmod 600 /root/.openclaw/workspace/{crypto,singclaw-dynamic,singclaw-site,worldx-demo,linkedin-agent}/.env*
  ```
- **Detection**: 定期 audit (`find -perm 0644 -name '.env*'`)
- **Owner**: 接手者
- **Due**: 即时（30 秒）

## R-05 · 重要 keys 未 revoke
- **等级**: P0
- **来源**: 安全巡检
- **触发**: key 在 `.env*` 里暴露
- **影响**:
  - Telegram Bot 接管: 任何人在 Telegram 上假冒
  - LinkedIn 接管: 攻击者可代表 H Sing 发 post
  - Vercel token: 接管 site deploy
  - ETH 私钥: 钱包资产清零
- **Mitigation**: H Sing 主账号到对应服务台操作
- **Owner**: H Sing
- **Due**: 本周

## R-06 · git 落后 origin/master 14 commit
- **等级**: P1
- **来源**: `git status -sb` 显示 ahead 14
- **触发**: host 盘坏 / 不可恢复
- **影响**: 新 commit (含 bugfix2) 未推到 remote，灾备缺失
- **Mitigation**: `git push origin main`
- **Detection**: cron 每日 `git fetch && git status -sb | grep ahead`
- **Owner**: 接手者
- **Due**: 本周

## R-07 · `crypto/.env` 已 tracked 进 git
- **等级**: P0 (泄漏历史 + 当前)
- **来源**: `git ls-files crypto/.env`
- **触发**: 仓库历史已含 TELEGRAM_BOT_TOKEN + ETH PRIVATE_KEY
- **影响**:
  - 当前 clone 含明文
  - 已经泄漏到可能抓过仓库的爬虫
- **Mitigation**:
  1. 短期: rm --cached + .gitignore
  2. 中期: revoke 旧 key + git filter-branch / BFG Repo-Cleaner 清历史
  3. 长期: 走 secrets manager
- **Detection**: cron `git ls-files | grep .env*`
- **Owner**: H Sing（revoke 操作）
- **Due**: 本周

## R-08 · fast-path 不支持 tools
- **等级**: P2
- **来源**: 实际观察（多次）
- **触发**: 用户问需实时数据的（BTC 价格 / 新闻）
- **影响**: 模型回"工具暂不可用" + 凭记忆答（不可信）
- **Mitigation**: S9.5.3 真 OpenAI/Anthropic function calling
- **Owner**: 未来接手者
- **Due**: 下个 Sprint

## R-09 · db.sqlite3 单调增长
- **等级**: P2
- **来源**: 当前 74 turns, 增长速率 ~5/小时
- **触发**: 6 个月内
- **影响**: 单文件超过 1 GB 时 SQLite 性能下降
- **Mitigation**:
  1. 加 `/v1/mvp/admin/purge?older_than_days=N` endpoint
  2. 加 cron 每周 vacuum + 90 天前 turn 删
- **Owner**: 接手者
- **Due**: 下个 Sprint

## R-10 · Clerk test publishable key 在 production
- **等级**: P2
- **来源**: 安全巡检
- **影响**: 前端 bundle 暴露 `pk_test_*`，能被解析用户名（major-lacewing-60.clerk.accounts.dev$）
- **Mitigation**: 删 Clerk (单租户不需要) 或换 production key
- **Owner**: 接手者
- **Due**: 后 Sprint

## R-11 · 单点故障: 主电脑 (VM-0-9-opencloudos)
- **等级**: P1
- **来源**: 基础设施层面
- **触发**: 平台维护 / 硬件故障
- **影响**: 整个服务全下线
- **Mitigation**:
  - 短期: 接受（个人 PMO 项目不要求 99.99%）
  - 中期: 多机节点（方案 B - OpenClaw multi-node）
  - 长期: 云容器化 + 自动 failover
- **Owner**: H Sing 决策
- **Due**: 不紧急

## R-12 · 团队单兵风险
- **等级**: P2
- **来源**: 资源
- **触发**: Maxink 不可用 / Codex 不可用
- **影响**: 项目无法推进
- **Mitigation**:
  - HANDOFF.md + 项目文档化
  - 多机 / 多 agent 协同方案
- **Owner**: H Sing 决策

## R-13 · LLM 配额耗尽
- **等级**: P1
- **来源**: 财务
- **触发**: provider 账单超额
- **影响**: 服务降级（fallback 至更便宜的模型）
- **Mitigation**:
  1. 设 budget cap on provider console
  2. 月初审计
- **Owner**: H Sing

## R-14 · 模型降级（miniMax → DeepSeek → OpenAI 链条失效）
- **等级**: P2
- **来源**: 技术
- **触发**: miniMax 接口变更 / DeepSeek rate limit
- **影响**: fallback 全部失败 → 服务 5xx
- **Mitigation**:
  1. healthcheck 三个 provider 都通
  2. 应急预案: 临时切到 claude-3.5-sonnet
- **Owner**: 接手者

## R-15 · 用户行为破坏性
- **等级**: P3
- **来源**: H Sing 测试习惯
- **触发**: H Sing 在 chat 里粘贴大文件 / 触发 OOM
- **影响**: 单 turn 慢 / 失败
- **Mitigation**: max token + length gate in adapter

— End of Risk Register —
