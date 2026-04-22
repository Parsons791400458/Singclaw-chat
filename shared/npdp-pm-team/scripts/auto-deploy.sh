#!/bin/bash
# NPDP自动部署脚本 v4.0
# 每次Sprint Cron执行后自动调用

WORKSPACE="/root/.openclaw/workspace"
NPDP="$WORKSPACE/shared/npdp-pm-team"
SITE="$WORKSPACE/singclaw-site"

echo "=== NPDP Auto Deploy v4.0 $(date '+%Y-%m-%d %H:%M:%S CST') ==="

# 1. 同步所有文档
echo "[1/4] 同步文档..."
mkdir -p $SITE/docs/{prd,competitive,research,rules,gtm,user-stories,dashboards,backtest,sprints,reports,learning}
cp -r $NPDP/specs/prd/* $SITE/docs/prd/ 2>/dev/null
cp -r $NPDP/specs/competitive/* $SITE/docs/competitive/ 2>/dev/null
cp -r $NPDP/specs/user-research/* $SITE/docs/research/ 2>/dev/null
cp -r $NPDP/specs/rules/* $SITE/docs/rules/ 2>/dev/null
cp -r $NPDP/specs/gtm/* $SITE/docs/gtm/ 2>/dev/null
cp -r $NPDP/specs/user-stories/* $SITE/docs/user-stories/ 2>/dev/null
cp -r $NPDP/artifacts/dashboards/* $SITE/docs/dashboards/ 2>/dev/null
cp -r $NPDP/artifacts/backtest/* $SITE/docs/backtest/ 2>/dev/null
cp -r $NPDP/artifacts/sprints/* $SITE/docs/sprints/ 2>/dev/null
cp -r $NPDP/artifacts/reports/* $SITE/docs/reports/ 2>/dev/null
cp -r $NPDP/artifacts/learning/* $SITE/docs/learning/ 2>/dev/null
cp $NPDP/SPRINT.md $SITE/docs/SPRINT.md 2>/dev/null
cp $NPDP/BACKLOG.md $SITE/docs/BACKLOG.md 2>/dev/null
cp $NPDP/DEPLOY_PIPELINE.md $SITE/docs/DEPLOY_PIPELINE.md 2>/dev/null
cp $NPDP/TEAM_PROTOCOL.md $SITE/docs/TEAM_PROTOCOL.md 2>/dev/null

# 2. 重新生成 Docsify 侧边栏
echo "[2/5] 生成侧边栏..."
cd $SITE/docs
bash gen-sidebar.sh
cp _sidebar.md $SITE/wiki/_sidebar.md

# 3. 构建 Sprint 每日迭代看板
echo "[3/5] 构建 Sprint 看板..."
cd $SITE
node scripts/build-sprint.js 2>&1

# 4. Git commit & push
echo "[4/5] Git push..."
cd $SITE
git add docs/ wiki/ sprint.html
if git diff --cached --quiet; then
  echo "✅ 无变更"
  exit 0
fi
git commit -m "🤖 NPDP自动部署 v4.0 $(date '+%Y-%m-%d %H:%M CST')"
git push origin main 2>&1

# 5. 触发Vercel部署
echo "[5/5] 触发Vercel部署..."
vercel deploy --prod 2>&1 | tail -3

echo "✅ 部署完成: $(git log --oneline -1)"
echo "🌐 文档站点: https://singclaw.xyz/wiki"
