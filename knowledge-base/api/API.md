# API 文档

## 1. 消息处理 API

### 1.1 发送消息
```bash
# 发送到 Telegram
curl -X POST "http://localhost:18789/api/message" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "telegram",
    "message": "Hello World",
    "to": "chat_id"
  }'

# 发送到飞书
curl -X POST "http://localhost:18789/api/message" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "feishu",
    "message": "Hello World",
    "to": "user_id"
  }'
```

### 1.2 获取消息
```bash
curl -X GET "http://localhost:18789/api/messages?channel=telegram"
```

### 1.3 删除消息
```bash
curl -X DELETE "http://localhost:18789/api/message?message_id=12345"
```

## 2. Agent 管理 API

### 2.1 创建 Agent
```bash
curl -X POST "http://localhost:18789/api/agent" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "crypto",
    "description": "加密货币分析师",
    "skills": ["web_search", "clawhub"]
  }'
```

### 2.2 启动 Agent
```bash
curl -X POST "http://localhost:18789/api/agent/start?name=crypto"
```

### 2.3 停止 Agent
```bash
curl -X POST "http://localhost:18789/api/agent/stop?name=crypto"
```

### 2.4 获取 Agent 状态
```bash
curl -X GET "http://localhost:18789/api/agent/status?name=crypto"
```

## 3. 任务管理 API

### 3.1 创建任务
```bash
curl -X POST "http://localhost:18789/api/task" \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "main",
    "name": "test-task",
    "description": "Test task",
    "parameters": {
      "param1": "value1"
    }
  }'
```

### 3.2 执行任务
```bash
curl -X POST "http://localhost:18789/api/task/run?name=test-task"
```

### 3.3 获取任务状态
```bash
curl -X GET "http://localhost:18789/api/task/status?name=test-task"
```

### 3.4 取消任务
```bash
curl -X POST "http://localhost:18789/api/task/cancel?name=test-task"
```

## 4. 文件管理 API

### 4.1 上传文件
```bash
curl -X POST "http://localhost:18789/api/file/upload" \
  -F "file=@/path/to/file.txt" \
  -F "path=/workspace/file.txt"
```

### 4.2 下载文件
```bash
curl -X GET "http://localhost:18789/api/file/download?path=/workspace/file.txt"
```

### 4.3 删除文件
```bash
curl -X DELETE "http://localhost:18789/api/file/delete?path=/workspace/file.txt"
```

## 5. 系统管理 API

### 5.1 系统状态
```bash
curl -X GET "http://localhost:18789/api/system/status"
```

### 5.2 重启服务
```bash
curl -X POST "http://localhost:18789/api/system/restart"
```

### 5.3 关闭服务
```bash
curl -X POST "http://localhost:18789/api/system/shutdown"
```

## 6. 权限管理 API

### 6.1 创建权限
```bash
curl -X POST "http://localhost:18789/api/permission" \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "main",
    "resource": "workspace/*",
    "action": "read"
  }'
```

### 6.2 检查权限
```bash
curl -X GET "http://localhost:18789/api/permission/check?agent=main&resource=workspace/*&action=read"
```

## 7. 监控 API

### 7.1 获取指标
```bash
curl -X GET "http://localhost:18789/api/metrics"
```

### 7.2 获取日志
```bash
curl -X GET "http://localhost:18789/api/logs?level=error&limit=100"
```

## 8. Webhook API

### 8.1 配置 Webhook
```bash
curl -X POST "http://localhost:18789/api/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "message",
    "url": "https://your-webhook-url.com",
    "secret": "your-secret"
  }'
```

### 8.2 触发 Webhook
```bash
curl -X POST "http://localhost:18789/api/webhook/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "message",
    "data": {
      "message": "Hello World"
    }
  }'
```

## 9. 错误码

### 9.1 通用错误
| 状态码 | 含义 | 描述 |
|--------|------|------|
| 200 | OK | 请求成功 |
| 400 | Bad Request | 请求格式错误 |
| 401 | Unauthorized | 未授权 |
| 403 | Forbidden | 禁止访问 |
| 404 | Not Found | 资源不存在 |
| 500 | Internal Server Error | 服务器错误 |

### 9.2 Agent 错误
| 错误码 | 含义 | 描述 |
|--------|------|------|
| 1001 | Agent Not Found | Agent 不存在 |
| 1002 | Agent Already Running | Agent 正在运行 |
| 1003 | Agent Configuration Error | Agent 配置错误 |

### 9.3 任务错误
| 错误码 | 含义 | 描述 |
|--------|------|------|
| 2001 | Task Not Found | 任务不存在 |
| 2002 | Task Already Running | 任务正在运行 |
| 2003 | Task Timeout | 任务超时 |

---
*最后更新: 2026-02-16*
*版本: 1.0*