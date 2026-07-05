# INCIDENT Force Push Recovery Runbook
**生成时间**: 2026-07-05 16:00 UTC
**触发事件**: 2026-07-05 R-04 修复 — git filter-branch 清 `crypto/.env` 全历史

---

## ⚠️ 发生了什么

H Sing 2026-07-05 授权: 全权推进安全收口。
我执行了:

```bash
# 1. 在 fresh clone (用 SSH deploy key 验证) 中:
git filter-branch -f --index-filter \
    "git rm --cached --ignore-unmatch crypto/.env" \
    --prune-empty --tag-name-filter cat -- --all

git reflog expire --all --expire=now
git gc --prune=now --aggressive

# 2. force push 到 GitHub private remote:
git push --force --force-with-lease origin main
```

**结果**: GitHub remote main 之前所有 SHA **全部变更**。H Sing 之前在 GitHub 网页上看到的 `a613503` HEAD **已经不存在**。

---

## 🔄 接手者 / H Sing 如何恢复本地视图

### 情况 A: 你本地**未修改**任何东西
```bash
cd /root/.openclaw/workspace
git fetch --all --prune --force
git reset --hard origin/main
```
(注意 `origin` 是 work 仓库，私域用 `private` remote:
```bash
git fetch private --prune --force
git reset --hard private/main
```)

### 情况 B: 你本地有**未推送的修改**
```bash
# 1. 先备份你修改:
cp -r <your_changes_dir> /tmp/my-changes-$(date +%F)/

# 2. fetch 远程:
git fetch private --prune --force

# 3. reset 本地 main 到 remote:
git checkout main
git reset --hard private/main

# 4. 重新应用你的修改 (e.g. cherry-pick or manual re-apply):
git diff HEAD@{1} HEAD -- <your_files>  # 看丢什么
# 手动改回
```

### 情况 C: 你 clone 了 `Parsons791400458/Singclaw-chat` 后做 PR / branch
```bash
# 在 GitHub 网页: 你的 fork/branch 是基于旧 SHA 创建的
# 那些 branch 仍然指向旧 commit, 但旧 commit 现在不可达

# 修复: 在 GitHub 网页删除旧 branch, 重新基于新 main 创建
# 或者: 在本地
git checkout your-branch
git rebase --onto private/main private/main@{1}
# (但这会失败, 因为旧 commit 已经从 remote history 中消失)

# 推荐: 重新创建 branch
git checkout private/main
git checkout -b your-branch-recreated
# 重新 cherry-pick 你要的 commits from old your-branch (如果有)
```

---

## 📌 验证 GitHub remote 已 clean

```bash
# fresh clone 测试
rm -rf /tmp/clone-verify-clean
mkdir /tmp/clone-verify-clean
cd /tmp/clone-verify-clean
git clone git@github.com:Parsons791400458/Singclaw-chat.git

cd Singclaw-chat
git log --all --oneline -- crypto/.env
# 期望: 空 (没有任何 commit 含 crypto/.env)

git ls-tree -r HEAD | grep "crypto/.env"
# 期望: 空 (HEAD tree 不含 .env)

git cat-file -e 6ab394bc143f94d9daa7254a0dcbb807dc5cf8aa
# 期望: exit 1 (blob unreachable / not found)
```

如果上面任意一项 fail → **重新跑 filter-branch + force-push**:
```bash
# 假定你在 workspace 根:
FILTER_BRANCH_SQUELCH_WARNING=1 \
  git filter-branch -f --index-filter \
    "git rm --cached --ignore-unmatch crypto/.env" \
    --prune-empty --tag-name-filter cat -- --all

git reflog expire --all --expire=now
git gc --prune=now --aggressive
git push --force --force-with-lease private main
```

---

## ⚠️ 为什么必须 force push

`git filter-branch` 重写所有 commit SHA — 每个 commit 的 SHA 取决于它**历史 + 内容**。
删一个文件 = 所有依赖它的 commit 的 tree hash 变 = parent hash 变 = 自身 hash 变。
整条链 SHA 变更 → 无法 fast-forward → 必须 force push。

**trade-off**: 
- ✅ 修复: GitHub 上 ETH 私钥 + Telegram token 永远看不到
- ❌ 损失: 所有 commit SHA 变了，H Sing 在 GitHub 网页看到的旧 SHA 不存在

对 **private** repo (只有 H Sing 看) 来说可接受。

---

## 🔧 后续维护

### 如果将来再不小心 commit .env 到 git
```bash
# 1. 立即 untracked:
git rm --cached crypto/.env  # 或 path/of/.env
echo "crypto/.env" >> .gitignore

# 2. 立刻 rotate key (因为 key 已泄漏进 git)
# Telegram: BotFather /revoke
# ETH: transfer + 重生
# LinkedIn: 改密 + 启 2FA
# 等等

# 3. (可选) 清历史 — 按本 runbook 重做 filter-branch
# 注意: 只在 P0 情况下做, 因为它会破坏 SHA 链
```

### 日常预防
1. **永远别** 用 `git add .` (会带 .env* 进 git)
2. **永远别** `git commit -am` (同上)
3. 用 `git status` 每次 commit 前**逐文件**确认
4. Pre-commit hook (e.g. `pre-commit install && pre-commit run`) 自动检测 secrets

— End of Runbook —