# 🚀 NPDP自动部署管线

> 2026-04-20 星哥指令：产出即发布，Review异步化

## 核心原则
1. Agent产出文档 → 自动同步到singclaw-site → git push → Vercel自动部署
2. Review不阻塞部署，先上线后审核
3. 每次Sprint Cron执行后自动触发部署

## 仓库配置
- **singclaw-site**: `github.com/Parsons791400458/singclaw-site`
- **Token**: ✅ 已配置 (x-access-token)
- **Vercel**: ✅ vercel.json存在，push到main自动触发

## 同步映射

| 源目录 | → 目标目录 |
|--------|-----------|
| specs/prd/ | singclaw-site/docs/prd/ |
| specs/competitive/ | singclaw-site/docs/competitive/ |
| specs/user-research/ | singclaw-site/docs/research/ |
| specs/rules/ | singclaw-site/docs/rules/ |
| specs/gtm/ | singclaw-site/docs/gtm/ |
| specs/user-stories/ | singclaw-site/docs/user-stories/ |
| artifacts/dashboards/ | singclaw-site/docs/dashboards/ |
| artifacts/backtest/ | singclaw-site/docs/backtest/ |
| artifacts/sprints/ | singclaw-site/docs/sprints/ |
| artifacts/reports/ | singclaw-site/docs/reports/ |
| artifacts/learning/ | singclaw-site/docs/learning/ |
| SPRINT.md | singclaw-site/docs/SPRINT.md |
| BACKLOG.md | singclaw-site/docs/BACKLOG.md |

## 自动部署脚本

路径：`shared/npdp-pm-team/scripts/auto-deploy.sh`

每次Sprint Cron执行后自动调用。

## 部署日志

| 时间 | 变更 | 状态 |
|------|------|------|
| 2026-04-20 11:21 | 首次全量同步（68个文件） | ✅ 已push到GitHub |
