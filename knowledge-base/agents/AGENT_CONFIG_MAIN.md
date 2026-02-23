# Agent 配置文档

## 主 Agent (main)

### 基本信息
- **ID**: main
- **描述**: 核心管理与协调
- **工作空间**: /root/.openclaw/workspace/
- **启动命令**: openclaw agent main

### Agent.json 配置
```json
{
  "name": "main",
  "description": "OpenClaw 主 Agent - 负责系统管理、任务调度、消息路由",
  "version": "1.0.0",
  "workspace": "/root/.openclaw/workspace/",
  "skills": ["system", "task", "message", "cron", "memory"],
  "channels": ["telegram", "feishu"],
  "permissions": {
    "read": [
      "workspace/*",
      "memory/*",
      "agents/*"
    ],
    "write": [
      "memory/*",
      "logs/*",
      "reports/*"
    ],
    "exec": [
      "system-commands",
      "file-operations",
      "network-requests"
    ]
  },
  "maxConcurrentTasks": 5,
  "timeout": 300,
  "retryAttempts": 3,
  "logLevel": "info"
}
```

### 技能清单
| 技能 | 描述 | 依赖 |
|------|------|------|
| system | 系统管理 | 内置 |
| task | 任务调度 | 内置 |
| message | 消息处理 | 内置 |
| cron | 定时任务 | 内置 |
| memory | 记忆管理 | 内置 |
| file | 文件操作 | 可选 |

### 任务队列
```json
{
  "queue": {
    "maxSize": 100,
    "priority": ["high", "medium", "low"],
    "retention": "7d"
  }
}
```

### 监控指标
- **CPU 使用率**: < 80%
- **内存使用**: < 90%
- **任务队列**: < 50 tasks
- **响应时间**: < 2s

### 启动脚本
```bash
#!/bin/bash
# 启动主 Agent

# 设置环境
export OPENCLAW_WORKSPACE=/root/.openclaw/workspace/
export OPENCLAW_AGENT=main

# 启动服务
cd /root/.openclaw
openclaw agent start main --daemon

# 检查状态
sleep 2
openclaw agent status main
```

### 日志位置
- **主日志**: /tmp/openclaw/openclaw.log
- **Agent 日志**: /tmp/openclaw/agent-main.log
- **任务日志**: /tmp/openclaw/tasks/main/

### 故障处理
| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 启动失败 | 配置文件错误 | 检查 agent.json 语法 |
| 无响应 | 资源不足 | 检查内存和 CPU |
| 任务失败 | 权限问题 | 验证权限配置 |

---
*最后更新: 2026-02-16*
*版本: 1.0*