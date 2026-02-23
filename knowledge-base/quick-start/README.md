# OpenClaw 快速入门指南

## 1. 系统概述
OpenClaw 是一个 AI 助手系统，用于自动化任务处理、消息管理和知识管理。

## 2. 核心概念
- **Agent**: 智能代理，执行特定任务
- **Workspace**: 工作空间，存储任务相关文件
- **Skill**: 技能，Agent 的能力模块
- **Channel**: 通信渠道（Telegram、飞书等）

## 3. 快速配置
### 3.1 安装依赖
```bash
# 安装 Node.js
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# 安装 OpenClaw
npm install -g openclaw
```

### 3.2 初始化系统
```bash
# 创建工作空间
mkdir -p ~/.openclaw/workspace

# 初始化配置
openclaw init
```

### 3.3 配置 Agent
```bash
# 创建 Agent
openclaw agent create main
openclaw agent create crypto
openclaw agent create ai-news

# 启动 Agent
openclaw agent start main
aopenclaw agent start crypto
openclaw agent start ai-news
```

## 4. 基本操作
### 4.1 消息处理
```bash
# 发送消息到 Telegram
openclaw message send --channel telegram --message "Hello World"

# 处理飞书消息
openclaw message send --channel feishu --message "Hello World"
```

### 4.2 任务管理
```bash
# 创建任务
openclaw task create --agent main --name "test-task" --description "Test task"

# 执行任务
openclaw task run --agent main --name "test-task"
```

## 5. 权限配置
### 5.1 基本权限
```json
{
  "permissions": {
    "read": ["workspace/*"],
    "write": ["memory/*"],
    "exec": ["safe-commands"]
  }
}
```

### 5.2 Agent 权限
```json
{
  "agents": {
    "main": {
      "permissions": {
        "read": ["workspace/*"],
        "write": ["memory/*"],
        "exec": ["system-commands"]
      }
    },
    "crypto": {
      "permissions": {
        "read": ["crypto/*"],
        "write": ["crypto/reports/*"],
        "exec": ["market-data", "strategy-analysis"]
      }
    }
  }
}
```

## 6. 故障排查
### 6.1 常见问题
- **Agent 无法启动**: 检查配置文件和权限
- **消息发送失败**: 检查网络连接和 API 密钥
- **任务执行错误**: 检查任务参数和依赖

### 6.2 日志查看
```bash
# 查看主日志
cat /tmp/openclaw/openclaw.log

# 查看 Agent 日志
cat /tmp/openclaw/agent-{name}.log
```

## 7. 下一步
1. 配置飞书集成
2. 设置 Telegram 群组
3. 创建任务计划
4. 配置监控告警

---
*最后更新: 2026-02-16*
*版本: 1.0*