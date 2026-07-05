# Secrets Onboarding — 协作时怎么传递

> 配合 [SECRETS_HANDBOOK.md](./docs/SECRETS_HANDBOOK.md) §7 使用

## 🎯 核心问题
仓库里**没有** `.env*` (filter-branch 清了，避免泄漏)。
新人 / 接手 agent clone 后**必须**拿到 .env 才能跑。

## ✅ 推荐流程（按场景）

### 场景 1: H Sing + 另一台自己的机器（同一台电脑多个 VM / 主机）

**最快: SCP** (内网或 SSH 隧道)
```bash
# H Sing 主电脑:
tar czf /tmp/singclaw-secrets-$(date +%F).tgz \
  singclaw-dynamic/.env.local \
  crypto/.env \
  linkedin-agent/.env \
  worldx-demo/.env

scp /tmp/singclaw-secrets-2026-07-05.tgz user@other-host:/tmp/

# 接手机器:
cd /root/.openclaw/workspace
tar xzf /tmp/singclaw-secrets-2026-07-05.tgz
chmod 600 .env*  singclaw-dynamic/.env.local crypto/.env linkedin-agent/.env worldx-demo/.env
shred -u /tmp/singclaw-secrets-2026-07-05.tgz
```

### 场景 2: 跨网 / 不信任通道 / 公网 (e.g. 接手 agent 在另一家公司)

**Age 加密** (推荐, 公网安全):
```bash
# 前提: 双方装 age (apt install age 或 brew install age)

# === 接手方生成 key pair, 把 pubkey 发给 H Sing ===
# (接手方):
age-keygen -o /tmp/recv-key 2>&1
PUBKEY=$(cat /tmp/recv-key.pub)
echo "把这一行发给 H Sing:"
echo "$PUBKEY"

# === H Sing 端: 用接手方 pubkey 加密 secrets, 发回 .age 文件 ===
# (H Sing):
RECIPIENT="age1..."  # 接手方的 pubkey
cd /root/.openclaw/workspace
tar czf - -C . singclaw-dynamic/.env.local crypto/.env linkedin-agent/.env worldx-demo/.env \
  | age -r "$RECIPIENT" -o /tmp/singclaw-secrets-$(date +%F).age
echo "把 /tmp/singclaw-secrets-2026-07-05.age 发给接手方"

# (H Sing 同时通过 Telegram 把 .age 文件发出去 - 加密体, 不泄漏)

# === 接手方: 解密 ===
# (接手方):
age -d -i /tmp/recv-key /tmp/singclaw-secrets-2026-07-05.age \
  | tar xzf - -C /root/.openclaw/workspace/
chmod 600 /root/.openclaw/workspace/singclaw-dynamic/.env.local \
          /root/.openclaw/workspace/crypto/.env \
          /root/.openclaw/workspace/linkedin-agent/.env \
          /root/.openclaw/workspace/worldx-demo/.env
shred -u /tmp/recv-key
shred -u /tmp/singclaw-secrets-2026-07-05.age
```

### 场景 3: 完全公网 / 临时单次 (用 1Password / Bitwarden)

**1Password Share Link**:
1. H Sing 创 vault entry `SingClaw MVP Secrets` 含全部 .env 内容
2. Settings → Share → 选 "One-time" + "Expires in 24h"
3. 发链接给接手方
4. 接手方 retrieve → 自己写入 .env → 链接自动失效

### 场景 4: 简单拷贝 (开发机, 双方物理可信)

**直接 scp 文件**:
```bash
# H Sing:
scp singclaw-dynamic/.env.local other-host:/root/.openclaw/workspace/singclaw-dynamic/.env.local
scp crypto/.env other-host:/root/.openclaw/workspace/crypto/.env
# ... etc
```

### ❌ 永远不要这样做

| ❌ 错误 | 原因 |
|---|---|
| 把 .env 内容粘到 Telegram / Slack / email | 明文落 history / log |
| `git add .env*` commit 进 git | 即便 private repo，未来导出/截图会泄 |
| 上传 .env 到 Google Drive / Dropbox 公开链接 | link 一旦泄漏 = 永久泄漏 |
| 把 .env 放在 USB / SD 卡（带出公司）| 物理介质丢失 = 永久泄漏 |

## 🛡 一键 onboarding 脚本（接手方跑）

创建文件 `~/.local/bin/secrets-onboard.sh`：
```bash
#!/usr/bin/env bash
set -euo pipefail

if [ -z "${1:-}" ]; then
  echo "Usage: secrets-onboard.sh <encrypted-secrets.age>"
  exit 1
fi

AGE_FILE="$1"
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

# 解密到临时目录
age -d -i ~/.ssh/age-recv.key "$AGE_FILE" | tar xzf - -C "$TMPDIR"

# 移动到 workspace
WORKSPACE="${WORKSPACE:-/root/.openclaw/workspace}"
for f in "$TMPDIR"/*/.env*; do
  src_dir=$(basename "$(dirname "$f")")
  src_file=$(basename "$f")
  dest_dir="$WORKSPACE/$src_dir"
  mkdir -p "$dest_dir"
  cp "$f" "$dest_dir/$src_file"
  chmod 600 "$dest_dir/$src_file"
  echo "✓ $dest_dir/$src_file"
done

echo ""
echo "✅ Secrets 落地完成. 验证:"
ls -la "$WORKSPACE"/singclaw-dynamic/.env.local 2>&1
ls -la "$WORKSPACE"/crypto/.env 2>&1
echo ""
echo "下一步:"
echo "  cd $WORKSPACE/singclaw-dynamic"
echo "  pnpm install && pnpm run build"
echo "  pm2 start ecosystem.config.js"
```

## 📋 给接手方的清单

接手方应在收到 `Singclaw-chat` clone 后**立刻**做：
- [ ] 看 [README.md](./README.md)
- [ ] 看 [QUICK_START.md](./QUICK_START.md) §1 (clone + 工具)
- [ ] 联系 H Sing 拿 secrets (用本 doc 推荐流程)
- [ ] 跑 `secrets-onboard.sh <file.age>`
- [ ] 跑 `QUICK_START.md` §3-5 (build + 起 + verify)

如果**某一步卡了** — H Sing 不是 24/7 在, 请看：
- [CONTACT_ESCALATION.md](./docs/CONTACT_ESCALATION.md)
- 紧急 issue → Telegram DM H Sing

— End of Secrets Onboarding —