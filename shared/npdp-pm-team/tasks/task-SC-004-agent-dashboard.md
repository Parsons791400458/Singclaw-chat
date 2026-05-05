# [SC-004] Agent Workflow Dashboard

- **来源**: 星哥直接需求 (2026-05-02 10:41 CST)
- **优先级**: 🔴 P0
- **负责人**: 小链（前端开发+部署）
- **DDL**: 2026-05-05
- **Story Points**: 5

## 背景
SingClaw 平台需要新增一个 Agent 工作流 Dashboard 页面，用于可视化展示当前运行的 AI Agent 状态、Cron 任务执行情况、系统健康度等。

## 需求
1. **路由**: `/dashboard/agents`
2. **展示内容**:
   - Agent 列表（名称/角色/状态/最后活跃时间）
   - Cron 任务执行状态（成功率/最近执行时间/下次执行）
   - 系统健康概览（内存/磁盘/在线 Agent 数）
   - 实时刷新（每 30s）
3. **设计要求**: 与 SingClaw 现有暗色主题一致，使用 Tailwind CSS
4. **认证**: 需登录后可见（Clerk 保护）

## 验收标准
- [ ] `/dashboard/agents` 页面可访问
- [ ] 显示所有 20+ Agent 的状态
- [ ] 显示 57+ Cron 任务状态
- [ ] 页面需 Clerk 登录保护
- [ ] 移动端响应式适配
- [ ] PM2 部署到 app.singclaw.xyz 正常

## 数据来源
- Agent 列表: `/root/.openclaw/agents/` 目录扫描
- Cron 状态: `openclaw cron list` 命令输出
- 系统指标: `free -m` / `df -h` / `uptime`

## 技术建议
- 使用 Server Component 获取数据
- 客户端组件负责轮询刷新
- 可参考现有 `/sprint` 页面的风格

---
**创建时间**: 2026-05-02 02:45 UTC
**创建人**: 柯维（Orchestrator）
**状态**: 🟡 Backlog → 待小链执行
