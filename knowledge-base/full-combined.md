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
*版本: 1.0*# AI Value Measurement Pyramid

@cryptodaoyi

## Overview
This document summarizes the AI Value Pyramid as depicted in the visual materials shared. It provides a practical framework to quantify and verify value at multiple levels of decision-making in crypto/AI contexts.

## Pyramid Layers
1) Micro — Per Call / Per Transaction
- Focus on granular, verifiable interactions (latency, cost, accuracy per operation).
2) Proof — Quality / Completion Proof
- Evidence that work is complete and meets quality criteria (tests, validation, deliverables).
3) Ledger — Auditable Ledger
- Immutable, auditable records that enable traceability and accountability.
4) Index — Macroeconomic Indicators
- Higher-level indicators that summarize the health of the macro environment (GDP, liquidity, risk appetite).

> Core principle: GDP isn’t everything, but verifiable measurement is essential.

## How to Apply
- Use the pyramid to assess crypto projects and AI-enabled initiatives.
- Start at Micro to ensure each action is traceable and cost-aware.
- Move up to Proof and Ledger to build trust and verifiability.
- Use Index to frame strategic decisions within macro context.

## Practical Scenarios
- Evaluating an investment signal: check micro hit rate, confirm proof, ensure ledger trail, and consult macro indicators.
- Assessing a product launch: verify delivery (Proof), ensure recorded milestones (Ledger), and review macro-market signals (Index).
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
*版本: 1.0*# 系统架构文档

## 1. 系统概览

### 1.1 架构图
```
┌─────────────────────────────────────────────────────────────┐
│                     消息中转层                              │
├──────────────┬──────────────┬──────────────┬───────────────┤
│  Telegram    │   飞书       │   Web API    │   其他        │
└──────────────┴──────────────┴──────────────┴───────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                       OpenClaw 网关                        │
├─────────────────────────────────────────────────────────────┤
│  消息解析  │  路由分发  │  协议转换  │  负载均衡          │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────┬─────────────┬─────────────┬──────────────┐
│             │             │             │              │
▼             ▼             ▼             ▼              ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌─────────┐
│ Agent 1│ │ Agent 2│ │ Agent 3│ │ Agent 4│ │  Agent N│
└────────┘ └────────┘ └────────┘ └────────┘ └─────────┘
```

### 1.2 核心组件
- **Gateway**: 消息网关，负责协议转换和路由
- **Agents**: 智能代理，执行具体任务
- **Workspace**: 工作空间，存储任务相关数据
- **Skills**: 技能模块，提供 Agent 能力
- **Channels**: 通信渠道，连接外部服务

## 2. 网关层设计

### 2.1 网关功能
```go
type Gateway struct {
    // 协议适配器
    adapters map[string]ProtocolAdapter
    
    // 消息路由
    router MessageRouter
    
    // 负载均衡
    loadBalancer LoadBalancer
    
    // 会话管理
    sessionManager SessionManager
    
    // 鉴权中间件
    authMiddleware AuthMiddleware
}
```

### 2.2 协议转换
- **Telemetry**: Telegram Bot API
- **Feishu**: 飞书开放 API
- **Webhook**: HTTP/RESTful API
- **Custom**: 自定义协议适配器

### 2.3 消息路由
```go
type Router struct {
    rules []RoutingRule
    agents map[string]AgentInfo
}

func (r *Router) Route(msg Message) (Agent, error) {
    // 1. 解析消息
    // 2. 匹配路由规则
    // 3. 选择目标 Agent
    // 4. 负载均衡
    // 5. 返回目标 Agent
}
```

## 3. Agent 层设计

### 3.1 Agent 架构
```typescript
interface Agent {
    id: string
    name: string
    description: string
    
    // 技能系统
    skills: Skill[]
    
    // 工作空间
    workspace: Workspace
    
    // 任务引擎
    taskEngine: TaskEngine
    
    // 消息处理器
    messageHandler: MessageHandler
    
    // 状态管理
    state: AgentState
}

interface Skill {
    name: string
    version: string
    dependencies: string[]
    capabilities: Capability[]
}
```

### 3.2 Agent 生命周期
```go
type Lifecycle struct {
    Start() error
    Stop() error
    Pause() error
    Resume() error
    Reload() error
}

// 启动流程
1. 加载配置
2. 初始化工作空间
3. 加载技能
4. 注册消息处理器
5. 启动任务引擎
6. 注册到网关
7. 开始监听消息
```

## 4. 技能系统

### 4.1 技能接口
```typescript
interface Skill {
    // 元数据
    metadata: SkillMetadata
    
    // 能力定义
    capabilities: Capability[]
    
    // 初始化
    initialize(config: SkillConfig): Promise<void>
    
    // 执行能力
    execute(capability: string, params: any): Promise<any>
    
    // 清理资源
    cleanup(): Promise<void>
}

interface Capability {
    name: string
    description: string
    inputSchema: JSONSchema
    outputSchema: JSONSchema
    examples: Example[]
}
```

### 4.2 内置技能
- **system**: 系统管理、文件操作
- **task**: 任务创建、执行、监控
- **message**: 消息发送、接收、过滤
- **memory**: 记忆存储、检索、管理
- **cron**: 定时任务、调度
- **web_search**: 网页搜索、内容抓取
- **data_analysis**: 数据分析、统计
- **api_client**: HTTP 请求、API 调用

### 4.3 自定义技能
```typescript
// 示例: 加密货币价格查询技能
class CryptoSkill implements Skill {
    metadata = {
        name: "crypto",
        version: "1.0.0",
        author: "OpenClaw"
    }
    
    capabilities = [
        {
            name: "get_price",
            inputSchema: { type: "object", properties: {symbol: "string"}},
            outputSchema: {type: "object", properties: {price: "number"}}
        }
    ]
    
    async execute(capability: string, params: any) {
        if (capability === "get_price") {
            return this.getPrice(params.symbol)
        }
    }
}
```

## 5. 数据层设计

### 5.1 数据存储
```
Data Layer:
├── 文件存储 (File Storage)
│   ├── 工作空间文件
│   ├── 配置文件
│   └── 日志文件
├── 数据库 (Database)
│   ├── PostgreSQL (主数据)
│   ├── Redis (缓存)
│   └── SQLite (本地存储)
└── 外部存储 (External Storage)
    ├── 对象存储 (S3/MinIO)
    └── 知识库 (飞书/Notion)
```

### 5.2 数据模型
```sql
-- Agent 表
CREATE TABLE agents (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100),
    workspace_path TEXT,
    config JSONB,
    status VARCHAR(20),
    created_at TIMESTAMP
);

-- 任务表
CREATE TABLE tasks (
    id VARCHAR(50) PRIMARY KEY,
    agent_id VARCHAR(50),
    name VARCHAR(100),
    status VARCHAR(20),
    parameters JSONB,
    result JSONB,
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    finished_at TIMESTAMP
);

-- 消息表
CREATE TABLE messages (
    id BIGSERIAL PRIMARY KEY,
    channel VARCHAR(50),
    sender_id VARCHAR(100),
    content TEXT,
    metadata JSONB,
    created_at TIMESTAMP
);
```

### 5.3 缓存策略
```go
type CacheManager struct {
    redisClient *redis.Client
    memoryCache *sync.Map
    ttl         time.Duration
}

func (cm *CacheManager) Get(key string) (interface{}, error) {
    // 1. 检查内存缓存
    // 2. 检查 Redis 缓存
    // 3. 查询数据库 (如果未命中)
    // 4. 更新缓存
}
```

## 6. 通信协议

### 6.1 内部通信
```protobuf
// Agent 到网关的消息
message AgentMessage {
    string agent_id = 1;
    string type = 2;
    bytes payload = 3;
    string trace_id = 4;
    int64 timestamp = 5;
}

// 网关到 Agent 的消息
message GatewayMessage {
    string message_id = 1;
    string channel = 2;
    string from = 3;
    string to = 4;
    bytes content = 5;
    repeated string tags = 6;
}
```

### 6.2 外部 API
```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "OpenClaw API",
    "version": "1.0.0"
  },
  "paths": {
    "/api/message": {
      "post": {
        "summary": "发送消息",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "channel": {"type": "string"},
                  "message": {"type": "string"},
                  "to": {"type": "string"}
                }
              }
            }
          }
        }
      }
    }
  }
}
```

## 7. 部署架构

### 7.1 单机部署
```
┌─────────────────────────────────┐
│          Host Machine            │
├─────────────────────────────────┤
│  ┌─────────┐  ┌──────────┐     │
│  │ Gateway │  │ Database  │     │
│  └─────────┘  └──────────┘     │
│  ┌─────────┐  ┌──────────┐     │
│  │ Agent1  │  │  Agent2  │     │
│  └─────────┘  └──────────┘     │
│  ┌─────────┐  ┌──────────┐     │
│  │ Agent3  │  │  AgentN  │     │
│  └─────────┘  └──────────┘     │
└─────────────────────────────────┘
```

### 7.2 分布式部署
```
┌────────────┐         ┌────────────┐
│   Load     │────────▶│  Gateway   │
│  Balancer  │         │  Node 1    │
└────────────┘         └────────────┘
      │                       │
      │                       ├─────▶ Database Cluster
      │                       │
      ▼                       │
┌────────────┐         ┌────────────┐
│  Gateway   │────────▶│  Gateway   │
│  Node 2    │         │  Node N    │
└────────────┘         └────────────┘
      │                       │
      └───────────┬───────────┘
                  ▼
         ┌──────────────┐
         │   Agent      │
         │  Cluster     │
         └──────────────┘
```

### 7.3 高可用方案
- **网关集群**: 多节点负载均衡
- **Agent 冗余**: 关键 Agent 多实例
- **数据库主从**: 读写分离
- **缓存集群**: Redis Sentinel/Cluster
- **消息队列**: RabbitMQ/Kafka
- **存储副本**: 对象存储多副本

## 8. 安全架构

### 8.1 安全层
```
┌─────────────────────────────────────────┐
│           Security Layer                │
├─────────────────────────────────────────┤
│  Authentication  │  Authorization     │
│  ┌────────────┐  ┌─────────────────┐ │
│  │  JWT/OAuth │  │  RBAC/ABAC      │ │
│  └────────────┘  └─────────────────┘ │
│  ┌────────────┐  ┌─────────────────┐ │
│  │   TLS/SSL  │  │  Audit Log      │ │
│  └────────────┘  └─────────────────┘ │
│  ┌────────────┐  ┌─────────────────┐ │
│  │ Rate Limit │  │   Encryption    │ │
│  └────────────┘  └─────────────────┘ │
└─────────────────────────────────────────┘
```

### 8.2 鉴权机制
```go
type AuthManager struct {
    jwtSecret []byte
    tokenStore TokenStore
    roles map[string]Role
}

func (am *AuthManager) Authorize(user User, resource Resource, action Action) bool {
    // 1. 检查用户角色
    // 2. 验证角色权限
    // 3. 检查资源 ACL
    // 4. 返回授权结果
}
```

### 8.3 安全审计
```bash
# 审计配置
openclaw security audit \
  --users all \
  --agents all \
  --period "last 30 days" \
  --output audit-report.json

# 检查异常行为
openclaw security detect --anomaly --threshold 0.8

# 生成合规报告
openclaw security compliance --standard gdpr
```

## 9. 监控与日志

### 9.1 指标收集
- **系统指标**: CPU、内存、磁盘、网络
- **Agent 指标**: 运行状态、任务队列、错误率
- **业务指标**: 消息量、响应时间、成功率
- **自定义指标**: 特定业务逻辑指标

### 9.2 日志分类
```go
type LogLevel int32

const (
    LevelDebug LogLevel = iota  // 调试信息
    LevelInfo                   // 一般信息
    LevelWarn                   // 警告信息
    LevelError                  // 错误信息
    LevelFatal                  // 致命错误
)

// 日志字段
type LogEntry struct {
    Timestamp time.Time
    Level     LogLevel
    AgentID   string
    TaskID    string
    Message   string
    Metadata  map[string]interface{}
}
```

### 9.3 告警规则
```yaml
alert_rules:
  - name: "Agent 离线"
    condition: "agent_status != 'running'"
    severity: critical
    notification:
      channels: [telegram, email]
      cooldown: 5m
      
  - name: "任务队列堆积"
    condition: "task_queue_length > 100"
    severity: warning
    notification:
      channels: [telegram]
      cooldown: 10m
```

## 10. 扩展性设计

### 10.1 插件系统
```typescript
interface Plugin {
    name: string
    version: string
    hooks: HookRegistry
    commands: CommandRegistry
}

// 插件生命周期
interface PluginLifecycle {
    onLoad(): Promise<void>
    onUnload(): Promise<void>
    onMessage(msg: Message): Promise<void>
    onTaskEvent(event: TaskEvent): Promise<void>
}
```

### 10.2 微服务化
```yaml
services:
  gateway:
    image: openclaw/gateway:latest
    ports:
      - "18789:18789"
    depends_on:
      - redis
      - postgres
  
  agent.main:
    image: openclaw/agent:latest
    command: ["agent", "main"]
    volumes:
      - ./workspace:/workspace
  
  agent.crypto:
    image: openclaw/agent:latest
    command: ["agent", "crypto"]
    volumes:
      - ./crypto:/workspace
```

### 10.3 API 版本管理
```go
type APIVersioning struct {
    versions map[string]APIHandler
    default  string
}

func (av *APIVersioning) Handle(r *http.Request) {
    version := r.Header.Get("X-API-Version")
    if version == "" {
        version = av.default
    }
    handler, ok := av.versions[version]
    if !ok {
        http.Error(w, "Unsupported API version", http.StatusBadRequest)
        return
    }
    handler.ServeHTTP(w, r)
}
```

---
*最后更新: 2026-02-16*
*版本: 1.0*# Basic Crypto Trading Strategies

- Trend following
- Mean reversion
- Breakouts
- Risk management rules
# OpenClaw 最佳实践指南

## 1. Agent 设计原则

### 1.1 单一职责
每个 Agent 应该只负责一个核心功能：
- **主 Agent**: 系统管理、任务调度、消息路由
- **Crypto Agent**: 加密货币分析、策略制定、市场监控
- **AI News Agent**: AI 新闻收集、分析、报告生成

### 1.2 权限最小化
```json
{
  "permissions": {
    "main": {
      "read": ["workspace/*", "memory/*"],
      "write": ["memory/*"],
      "exec": ["system-commands"]
    },
    "crypto": {
      "read": ["crypto/*"],
      "write": ["crypto/reports/*"],
      "exec": ["market-data"]
    }
  }
}
```

### 1.3 工作空间隔离
```
/root/.openclaw/workspace/
├── main/          # 主 Agent 工作空间
├── crypto/        # Crypto Agent 工作空间
├── ai-news/       # AI News Agent 工作空间
└── shared/        # 共享资源
```

## 2. 任务管理最佳实践

### 2.1 任务规划
**使用 PDCA 循环**:
- **Plan**: 详细的任务计划，包括时间估算
- **Do**: 分步骤执行，记录日志
- **Check**: 验证结果，对比预期
- **Act**: 总结经验，优化流程

### 2.2 任务分解
```json
{
  "task": "crypto-strategy-learning",
  "days": [
    {
      "day": 1,
      "title": "数据收集",
      "tasks": [
        "收集 BTC/ETH/SOL 关键指标",
        "获取历史价格数据",
        "整理市场情绪指标"
      ]
    }
  ]
}
```

### 2.3 任务监控
- 使用 `openclaw task status` 检查进度
- 记录每个子任务的完成时间
- 设置超时和重试机制
- 使用 `--retry` 参数处理失败任务

## 3. 知识库维护

### 3.1 文档结构
```
knowledge-base/
├── quick-start/          # 快速入门
├── agents/              # Agent 配置
├── tasks/               # 任务管理
├── api/                 # API 文档
├── troubleshooting/     # 故障排查
├── best-practices/      # 最佳实践
├── architectures/       # 系统架构
└── logs/               # 运行日志
```

### 3.2 更新规范
- **版本控制**: 每个文档保留版本号
- **更新记录**: 在文档底部添加更新日志
- **时效性**: 过时内容标记为 [DEPRECATED]
- **交叉引用**: 使用链接关联相关文档

### 3.3 内容质量
- 使用清晰的标题层级 (### 三级标题)
- 代码块使用 ``` 标记
- 表格列对齐，包含表头
- 重要信息使用 **加粗** 突出

## 4. 消息处理

### 4.1 消息格式
```bash
# 使用模板化消息
openclaw message send --channel telegram \
  --template "daily-report" \
  --data '{"date":"2025-02-16","agent":"crypto"}'

# 支持 Markdown
openclaw message send --channel telegram \
  --message "**重要通知**: 市场分析完成"
```

### 4.2 消息队列管理
```bash
# 查看队列状态
openclaw message queue status

# 清理失败消息
openclaw message queue cleanup --status failed

# 设置重试策略
openclaw config set message.retryCount 3
openclaw config set message.retryInterval 30
```

### 4.3 错误处理
```bash
# 捕获发送失败
openclaw message send --channel telegram \
  --message "Hello" \
  --on-error retry --max-retries 3

# 记录失败消息
openclaw message log --level error
```

## 5. 安全配置

### 5.1 权限管理
```bash
# 为每个 Agent 创建最小权限
openclaw permission add --agent crypto \
  --resource "crypto/*" \
  --action "read,write"

# 定期审计
openclaw security audit --agents all --report
```

### 5.2 敏感信息保护
- 不在日志中记录 API 密钥
- 使用环境变量存储敏感信息
- 配置文件加密存储
- 定期轮换密钥

### 5.3 网络安全
- 配置防火墙规则
- 使用 HTTPS
- 限制访问 IP
- 启用 DDoS 防护

## 6. 性能优化

### 6.1 Agent 调优
```bash
# 限制并发任务
openclaw config set agent.maxConcurrentTasks 5

# 设置资源限制
openclaw config set agent.memoryLimit 512
openclaw config set agent.cpuLimit 80

# 缓存优化
openclaw config set cache.ttl 3600
openclaw config set cache.maxSize 1024
```

### 6.2 数据库优化
- 定期清理旧数据
- 创建索引
- 优化查询
- 使用连接池

### 6.3 网络优化
- 使用 CDN
- 压缩传输数据
- 批量处理请求
- 设置超时限制

## 7. 监控与告警

### 7.1 关键指标
- Agent 状态（运行/停止）
- 任务队列长度
- 消息发送成功率
- 系统资源使用率
- 错误率统计

### 7.2 告警配置
```bash
# 设置告警阈值
openclaw alert set --metric "queue_length" --threshold 50
openclaw alert set --metric "error_rate" --threshold 0.05

# 配置通知渠道
openclaw alert channel add --type telegram --chat_id "CHAT_ID"
openclaw alert channel add --type email --address "admin@example.com"
```

### 7.3 日志管理
```bash
# 分级日志配置
openclaw config set log.level.info
openclaw config set log.maxFiles 30
openclaw config set log.maxSize 100M

# 日志轮转
openclaw log rotate --daily --compress
```

## 8. 部署规范

### 8.1 环境分离
- **开发环境**: 测试新功能
- **测试环境**: 验证稳定性
- **生产环境**: 正式运行

### 8.2 部署流程
```bash
# 1. 版本打包
openclaw build --version 1.0.0 --output openclaw-v1.0.0.tar.gz

# 2. 上传到服务器
scp openclaw-v1.0.0.tar.gz user@server:/tmp/

# 3. 安装
ssh user@server "openclaw install /tmp/openclaw-v1.0.0.tar.gz"

# 4. 配置
ssh user@server "openclaw config apply /tmp/config.json"

# 5. 启动
ssh user@server "openclaw start"
```

### 8.3 回滚策略
```bash
# 版本列表
openclaw version list

# 回滚到指定版本
openclaw rollback --version 1.0.0

# 验证回滚
openclaw status
openclaw agent status all
```

## 9. 团队协作

### 9.1 文档共享
- 使用飞书知识库集中管理
- 文档变更通过审批流程
- 定期团队培训

### 9.2 变更管理
```bash
# 提交变更申请
openclaw change request create \
  --title "升级 Agent 权限" \
  --description "调整加密权限配置" \
  --agent crypto

# 审批流程
openclaw change request approve --id 123
openclaw change request deploy --id 123
```

### 9.3 代码审查
- 所有配置文件变更需审查
- 重要修改需测试验证
- 保持配置版本一致

## 10. 日常运维

### 10.1 检查清单
```bash
# 每日检查
openclaw daily-check --agents all --channels all

# 每周检查
openclaw weekly-check --performance --security

# 每月检查
openclaw monthly-check --backup --audit
```

### 10.2 备份策略
- **全量备份**: 每周一次
- **增量备份**: 每日一次
- **异地备份**: 每月一次
- **备份验证**: 每次备份后测试恢复

### 10.3 应急预案
- 主备 Agent 自动切换
- 关键服务监控
- 应急联系人清单
- 快速恢复流程

---
*最后更新: 2026-02-16*
*版本: 1.0*# AI Value Measurement Pyramid

@cryptodaoyi

## Overview
This document summarizes the AI Value Pyramid as depicted in the visual materials shared. It provides a practical framework to quantify and verify value at multiple levels of decision-making in crypto/AI contexts.

## Pyramid Layers
1) Micro — Per Call / Per Transaction
- Focus on granular, verifiable interactions (latency, cost, accuracy per operation).
2) Proof — Quality / Completion Proof
- Evidence that work is complete and meets quality criteria (tests, validation, deliverables).
3) Ledger — Auditable Ledger
- Immutable, auditable records that enable traceability and accountability.
4) Index — Macroeconomic Indicators
- Higher-level indicators that summarize the health of the macro environment (GDP, liquidity, risk appetite).

> Core principle: GDP isn’t everything, but verifiable measurement is essential.

## How to Apply
- Use the pyramid to assess crypto projects and AI-enabled initiatives.
- Start at Micro to ensure each action is traceable and cost-aware.
- Move up to Proof and Ledger to build trust and verifiability.
- Use Index to frame strategic decisions within macro context.

## Practical Scenarios
- Evaluating an investment signal: check micro hit rate, confirm proof, ensure ledger trail, and consult macro indicators.
- Assessing a product launch: verify delivery (Proof), ensure recorded milestones (Ledger), and review macro-market signals (Index).
# Basic Crypto Trading Strategies

- Trend following
- Mean reversion
- Breakouts
- Risk management rules
# CRYPTO_INDEX.md

Index of crypto topics and related assets.# Market Overview – Crypto Landscape

A concise overview of the current crypto market, major trends, and notable projects. Updated daily from trusted sources.

- Market size and capitalization snapshots
- Key drivers: liquidity, regulatory clarity, on-chain activity
- Notable projects: Bitcoin, Ethereum, DeFi, Layer-2s
- Risk factors: volatility, regulatory changes, macro shocks
# AI sources list

- Source A
- Source B
- Source C
# Technical Analysis – Crypto & AI

Detailed breakdowns and methodologies for analyzing crypto markets and AI trends.
# 资金流向分析：从主币银行到多资产配置

> @cryptodaoyi | Gemini 2.5 Flash 推理整合

## 资金传导链
```
主币银行 
  ↓ 货币超发 + 利率变化 
  → 多资产分流：现金 → 债 → 股 → 金 → Crypto
```

## Risk-on / Risk-off 双模式
| 模式 | 特征 | 资产表现 | 触发条件 |
|------|------|----------|----------|
| **Risk-on** | 容器溢价上升 | 股/金/Crypto 同涨 | 流动性宽松 + 风险偏好↑ |
| **Risk-off** | 回流现金/短债 | 现金/短债↑，Crypto↓ | 流动性收紧 + 避险情绪↑ |

## 关键决策框架
> **“先看潮汐，再谈浪花”**
- 潮汐 = 宏观流动性周期（美联储政策、M2增速）
- 浪花 = 资产价格波动（具体币种/股票表现）

## 实战应用
1. **仓位动态调整**：
   - Risk-on 期：提高 Crypto 权重（≤10%总仓位）
   - Risk-off 期：切换至现金/短债，保留观察仓

2. **跨市场验证**：
   - 若美股纳指与 BTC 同步上涨 → 真实 Risk-on
   - 若 BTC 独立上涨 → 可能为局部叙事驱动（需警惕）

## 附：资金容器模型
- 现金容器：高流动性，低收益  
- 债容器：中等流动性，收益稳定  
- 股容器：高波动, 长期增长  
- 金容器：抗通胀，避险属性  
- Crypto容器：高波动+高成长+新范式

> 注：所有容器间存在动态再平衡机制# CRYPTO_INDEX.md

Index of crypto topics and related assets.# Token 生命周期底层时间轴分析

> @cryptodaoyi | 基于 Gemini 2.5 Flash 深度推理

## 核心三曲线关系
| 曲线 | 特征 | 关键节点 | 投资启示 |
|------|------|----------|----------|
| **注意力曲线** (Attention) | 高峰前置，衰减缓慢 | TGE → Listing → Peak Attention | 热度≠价格，警惕“FOMO陷阱” |
| **流动性曲线** (Liquidity) | 滞后于注意力，双峰结构 | Listing → Unlock Events | 资金流入滞后，需等待流动性确认 |
| **供给/解锁曲线** (Supply/Unlock) | 锯齿状突增，不可逆 | Token Unlocks（如4月、8月） | 解锁潮是价格波动主因，非项目进展 |

## 关键洞察
- ✅ **认知偏差纠正**：  
  > “你以为在投项目, 实际在投供给曲线”  
  散户关注叙事，机构关注解锁时点与抛压测算

- 📉 **三曲线错位预警信号**：  
  当注意力高峰 > 流动性高峰 > 供给高峰 → **高风险区间**  
  （典型：TGE后1-2个月）

- 🔁 **二次叙事阶段**：  
  供给曲线平台期 + 流动性二次抬升 → 基建层（Chain/Exchanges）率先受益

## 行动清单
- [ ] 建立解锁日历监控（每季度前30天预警）
- [ ] 量化注意力/流动性偏离度指标
- [ ] 将“供给曲线”纳入仓位管理模型# AI Value Measurement Pyramid

@cryptodaoyi

## Overview
This document summarizes the AI Value Pyramid as depicted in the visual materials shared. It provides a practical framework to quantify and verify value at multiple levels of decision-making in crypto/AI contexts.

## Pyramid Layers
1) Micro — Per Call / Per Transaction
- Focus on granular, verifiable interactions (latency, cost, accuracy per operation).
2) Proof — Quality / Completion Proof
- Evidence that work is complete and meets quality criteria (tests, validation, deliverables).
3) Ledger — Auditable Ledger
- Immutable, auditable records that enable traceability and accountability.
4) Index — Macroeconomic Indicators
- Higher-level indicators that summarize the health of the macro environment (GDP, liquidity, risk appetite).

> Core principle: GDP isn’t everything, but verifiable measurement is essential.

## How to Apply
- Use the pyramid to assess crypto projects and AI-enabled initiatives.
- Start at Micro to ensure each action is traceable and cost-aware.
- Move up to Proof and Ledger to build trust and verifiability.
- Use Index to frame strategic decisions within macro context.

## Practical Scenarios
- Evaluating an investment signal: check micro hit rate, confirm proof, ensure ledger trail, and consult macro indicators.
- Assessing a product launch: verify delivery (Proof), ensure recorded milestones (Ledger), and review macro-market signals (Index).
# Basic Crypto Trading Strategies

- Trend following
- Mean reversion
- Breakouts
- Risk management rules
# CRYPTO_INDEX.md

Index of crypto topics and related assets.# Market Overview – Crypto Landscape

A concise overview of the current crypto market, major trends, and notable projects. Updated daily from trusted sources.

- Market size and capitalization snapshots
- Key drivers: liquidity, regulatory clarity, on-chain activity
- Notable projects: Bitcoin, Ethereum, DeFi, Layer-2s
- Risk factors: volatility, regulatory changes, macro shocks
# AI sources list

- Source A
- Source B
- Source C
# Technical Analysis – Crypto & AI

Detailed breakdowns and methodologies for analyzing crypto markets and AI trends.
# OpenClaw 变更日志

## [2026-02-16] - 版本 1.0.0

### 🎉 新增功能
- **知识库系统**: 创建了完整的知识库结构
- **多文档支持**: 将知识库从单一文档拆分为分类文档
- **快速入门**: 添加了详细的安装和配置指南
- **API 文档**: 完整的 API 接口文档
- **故障排查**: 详细的故障排除指南
- **最佳实践**: 系统设计和运维的最佳实践
- **架构文档**: 完整的系统架构设计

### 📚 文档目录
```
knowledge-base/
├── quick-start/          # 快速入门
│   ├── README.md         # 快速指南
│   └── INSTALLATION.md   # 安装指南
├── agents/              # Agent 配置
│   └── AGENT_CONFIG_MAIN.md
├── tasks/               # 任务管理
├── api/                 # API 文档
│   └── API.md           # 完整 API 文档
├── troubleshooting/     # 故障排查
│   └── TROUBLESHOOTING.md
├── best-practices/      # 最佳实践
│   └── BEST_PRACTICES.md
├── architectures/       # 系统架构
│   └── ARCHITECTURE.md
└── logs/               # 运行日志
    └── CHANGELOG.md     # 变更日志
```

### 🔧 系统配置
- **Agent 配置**: 详细的 Agent 配置文档
- **权限管理**: 最小权限原则配置
- **工作空间**: 隔离的工作空间结构
- **启动脚本**: 完整的启动和部署脚本

### 🐛 修复问题
- **文档碎片化**: 将知识库从单一文档优化为结构化分类
- **信息查找困难**: 创建了清晰的目录结构和索引
- **维护困难**: 建立了版本控制和更新机制

### 📈 性能优化
- **文档加载**: 按需加载不同分类文档
- **搜索效率**: 创建了文档索引
- **更新速度**: 优化了文档更新流程

### 🛡️ 安全增强
- **权限控制**: 为每个文档设置适当的访问权限
- **敏感信息**: 保护了配置中的敏感信息
- **审计追踪**: 记录了所有文档变更

---
*最后更新: 2026-02-16*
*版本: 1.0.0*# Market Overview – Crypto Landscape

A concise overview of the current crypto market, major trends, and notable projects. Updated daily from trusted sources.

- Market size and capitalization snapshots
- Key drivers: liquidity, regulatory clarity, on-chain activity
- Notable projects: Bitcoin, Ethereum, DeFi, Layer-2s
- Risk factors: volatility, regulatory changes, macro shocks
# OpenClaw 安装指南

## 1. 系统要求
- **操作系统**: Linux (推荐 Ubuntu 20.04+ / CentOS 8+)
- **Node.js**: 16.0+ (推荐 18.0+)
- **内存**: 2GB+ (推荐 4GB+)
- **磁盘**: 1GB+ 可用空间

## 2. 安装步骤

### 2.1 安装 Node.js
#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y curl
sudo curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs
```

#### CentOS/RHEL
```bash
sudo yum install -y curl
sudo curl -fsSL https://rpm.nodesource.com/setup_lts.x | sudo -E bash -
sudo yum install -y nodejs
```

#### 验证安装
```bash
node --version
npm --version
```

### 2.2 安装 OpenClaw
```bash
# 全局安装
npm install -g openclaw

# 验证安装
openclaw --version
```

### 2.3 创建工作空间
```bash
# 创建目录
mkdir -p ~/.openclaw/workspace

# 设置环境变量
export OPENCLAW_WORKSPACE=~/.openclaw/workspace
```

## 3. 配置环境

### 3.1 系统配置
```bash
# 编辑配置文件
nano ~/.openclaw/openclaw.json
```

### 3.2 权限配置
```bash
# 创建权限目录
mkdir -p ~/.openclaw/permissions

# 设置权限文件
nano ~/.openclaw/permissions/main.json
```

## 4. 启动服务

### 4.1 网关服务
```bash
# 启动网关
sudo systemctl enable openclaw-gateway
sudo systemctl start openclaw-gateway

# 检查状态
sudo systemctl status openclaw-gateway
```

### 4.2 Agent 服务
```bash
# 启动主 Agent
openclaw agent start main

# 启动其他 Agent
openclaw agent start crypto
openclaw agent start ai-news
```

## 5. 验证安装

### 5.1 基础验证
```bash
# 检查版本
openclaw --version

# 检查状态
openclaw status
```

### 5.2 功能验证
```bash
# 测试消息发送
openclaw message send --channel telegram --message "System test"

# 测试任务执行
openclaw task create --agent main --name "test" --description "Test task"
openclaw task run --agent main --name "test"
```

## 6. 常见问题

### 6.1 安装失败
- **问题**: Node.js 安装失败
- **解决**: 检查网络连接，使用国内镜像

### 6.2 权限问题
- **问题**: 权限不足
- **解决**: 检查用户权限，使用 sudo 或 root

### 6.3 依赖问题
- **问题**: 依赖包缺失
- **解决**: 运行 `npm install` 重新安装依赖

## 7. 后续配置

### 7.1 飞书集成
- 创建飞书应用
- 配置 Bot 权限
- 设置 Webhook

### 7.2 Telegram 集成
- 创建 Bot
- 获取 API 密钥
- 配置群组权限

### 7.3 监控配置
- 设置日志级别
- 配置监控告警
- 定期备份数据

---
*最后更新: 2026-02-16*
*版本: 1.0*# OpenClaw 快速入门指南

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
*版本: 1.0*# AI sources list

- Source A
- Source B
- Source C
# Technical Analysis – Crypto & AI

Detailed breakdowns and methodologies for analyzing crypto markets and AI trends.
# 故障排查指南

## 1. Agent 相关问题

### 1.1 Agent 无法启动
**症状**: Agent 启动后立即停止或无响应

**可能原因**:
- 配置文件语法错误
- 权限不足
- 依赖包缺失
- 端口冲突

**解决方案**:
```bash
# 检查配置文件语法
openclaw agent validate main

# 查看日志
cat /tmp/openclaw/agent-main.log

# 检查端口占用
netstat -tulpn | grep 18789

# 重新启动
openclaw agent restart main
```

### 1.2 Agent 运行缓慢
**症状**: Agent 响应时间过长，任务执行缓慢

**可能原因**:
- 资源不足 (CPU/内存)
- 任务队列过长
- 网络延迟
- 代码效率问题

**解决方案**:
```bash
# 检查系统资源
htop
free -h

# 查看任务队列
openclaw agent status main

# 优化配置
nano ~/.openclaw/agents/main/agent.json

# 重启服务
openclaw agent restart main
```

### 1.3 Agent 任务失败
**症状**: 任务执行失败，返回错误信息

**可能原因**:
- 参数错误
- 依赖服务不可用
- 权限不足
- 网络问题

**解决方案**:
```bash
# 查看任务日志
cat /tmp/openclaw/tasks/main/*.log

# 检查任务参数
openclaw task show --name "task-name"

# 重新执行任务
openclaw task run --name "task-name" --retry

# 检查依赖服务
systemctl status openclaw-gateway
```

## 2. 消息处理问题

### 2.1 消息发送失败
**症状**: 消息无法发送到 Telegram 或飞书

**可能原因**:
- API 密钥错误
- 网络连接问题
- 权限不足
- 目标用户/群组不存在

**解决方案**:
```bash
# 检查 API 密钥
cat ~/.openclaw/config/channels/telegram.json
cat ~/.openclaw/config/channels/feishu.json

# 测试网络连接
ping api.telegram.org
ping open.feishu.cn

# 重新授权
openclaw channel reauthorize telegram
openclaw channel reauthorize feishu

# 检查目标
openclaw channel list --channel telegram
openclaw channel list --channel feishu
```

### 2.2 消息接收延迟
**症状**: 消息接收有延迟或丢失

**可能原因**:
- 网络不稳定
- 服务器负载过高
- 消息队列阻塞
- 配置错误

**解决方案**:
```bash
# 检查服务器负载
htop

# 查看消息队列
openclaw message queue

# 优化配置
nano ~/.openclaw/config/agents/main.json

# 重启消息服务
openclaw agent restart main
```

### 2.3 消息格式错误
**症状**: 消息显示异常，格式不正确

**可能原因**:
- Markdown 语法错误
- 字符编码问题
- 平台限制

**解决方案**:
```bash
# 检查消息格式
openclaw message validate --message "your message"

# 使用纯文本
openclaw message send --channel telegram --message "plain text" --format text

# 检查平台限制
openclaw channel limits --channel telegram
```

## 3. 系统服务问题

### 3.1 网关服务无法启动
**症状**: 网关服务启动失败

**可能原因**:
- 端口被占用
- 配置文件错误
- 依赖服务未启动
- 权限问题

**解决方案**:
```bash
# 检查端口
netstat -tulpn | grep 18789

# 查看日志
cat /tmp/openclaw/openclaw.log

# 检查依赖
systemctl status redis
systemctl status nginx

# 重新启动
sudo systemctl restart openclaw-gateway
```

### 3.2 数据库连接问题
**症状**: 数据库连接失败

**可能原因**:
- 数据库服务未启动
- 连接字符串错误
- 认证失败
- 网络问题

**解决方案**:
```bash
# 检查数据库状态
systemctl status postgresql
systemctl status mysql

# 测试连接
psql -h localhost -U openclaw -d openclaw

# 检查配置文件
cat ~/.openclaw/config/database.json

# 重启服务
sudo systemctl restart postgresql
```

### 3.3 文件操作错误
**症状**: 文件读写失败

**可能原因**:
- 权限不足
- 磁盘空间不足
- 文件路径错误
- 文件被锁定

**解决方案**:
```bash
# 检查权限
ls -la /root/.openclaw/workspace/

# 检查磁盘空间
df -h

# 检查文件路径
find /root/.openclaw -name "*.md"

# 修复权限
chmod -R 755 /root/.openclaw
```

## 4. 网络问题

### 4.1 网络连接失败
**症状**: 无法连接到外部服务

**可能原因**:
- 网络配置错误
- 防火墙限制
- DNS 解析问题
- 服务不可用

**解决方案**:
```bash
# 检查网络配置
ip addr
systemctl status NetworkManager

# 测试连接
ping 8.8.8.8
ping google.com

# 检查防火墙
iptables -L
ufw status

# 检查 DNS
cat /etc/resolv.conf
nslookup google.com
```

### 4.2 SSL/TLS 证书问题
**症状**: SSL 证书验证失败

**可能原因**:
- 证书过期
- 证书链不完整
- 系统时间不正确
- 证书信任问题

**解决方案**:
```bash
# 检查系统时间
date

# 更新证书
sudo apt update && sudo apt install ca-certificates

# 检查证书链
openssl s_client -connect api.telegram.org:443 -showcerts

# 信任证书
sudo update-ca-certificates
```

### 4.3 代理配置问题
**症状**: 通过代理连接失败

**可能原因**:
- 代理配置错误
- 代理服务不可用
- 认证失败
- 网络策略限制

**解决方案**:
```bash
# 检查代理配置
env | grep -i proxy
cat ~/.openclaw/config/proxy.json

# 测试代理
curl -x http://proxy.example.com:8080 https://google.com

# 更新代理配置
export http_proxy=http://proxy.example.com:8080
export https_proxy=http://proxy.example.com:8080
```

## 5. 配置问题

### 5.1 配置文件语法错误
**症状**: 配置解析失败

**可能原因**:
- JSON 语法错误
- 缺少必填字段
- 字段值类型错误
- 配置冲突

**解决方案**:
```bash
# 验证 JSON 语法
python -m json.tool ~/.openclaw/config.json

# 检查配置字段
openclaw config validate

# 重置配置
cp ~/.openclaw/config.json.default ~/.openclaw/config.json
```

### 5.2 环境变量问题
**症状**: 环境变量未生效

**可能原因**:
- 环境变量未设置
- 会话未刷新
- 权限问题
- 配置冲突

**解决方案**:
```bash
# 检查环境变量
env | grep OPENCLAW

# 设置环境变量
export OPENCLAW_WORKSPACE=/root/.openclaw/workspace
export OPENCLAW_CONFIG=/root/.openclaw/config.json

# 刷新会话
source ~/.bashrc
source ~/.profile
```

### 5.3 权限配置错误
**症状**: 权限不足，无法执行操作

**可能原因**:
- 权限设置错误
- 用户组配置错误
- 文件所有者错误
- 访问控制列表问题

**解决方案**:
```bash
# 检查权限
ls -la /root/.openclaw/

# 设置权限
chmod -R 755 /root/.openclaw
chown -R openclaw:openclaw /root/.openclaw

# 检查用户组
groups openclaw
```

## 6. 数据问题

### 6.1 数据损坏
**症状**: 数据读取失败或内容异常

**可能原因**:
- 文件损坏
- 磁盘错误
- 数据不一致
- 版本冲突

**解决方案**:
```bash
# 检查文件完整性
md5sum /root/.openclaw/workspace/*.md

# 修复数据
openclaw data repair

# 恢复备份
cp /backup/openclaw/data /root/.openclaw/workspace/
```

### 6.2 数据丢失
**症状**: 数据文件消失或内容为空

**可能原因**:
- 误删除
- 存储空间不足
- 同步问题
- 备份失败

**解决方案**:
```bash
# 检查回收站
ls -la ~/.local/share/Trash/

# 恢复备份
cp /backup/openclaw/data /root/.openclaw/workspace/

# 检查存储空间
df -h

# 配置自动备份
openclaw config set backup.enabled true
```

### 6.3 数据同步问题
**症状**: 多设备数据不同步

**可能原因**:
- 网络连接问题
- 同步服务故障
- 版本冲突
- 配置错误

**解决方案**:
```bash
# 检查同步状态
openclaw sync status

# 强制同步
openclaw sync force

# 检查配置
cat ~/.openclaw/config/sync.json

# 重置同步
openclaw sync reset
```

## 7. 性能问题

### 7.1 系统运行缓慢
**症状**: 整体系统响应缓慢

**可能原因**:
- 资源不足
- 任务过多
- 配置不当
- 代码效率问题

**解决方案**:
```bash
# 检查系统负载
htop
free -h
df -h

# 优化配置
nano ~/.openclaw/config/performance.json

# 清理缓存
openclaw cache clear

# 重启服务
openclaw restart
```

### 7.2 内存泄漏
**症状**: 内存使用持续增加

**可能原因**:
- 代码内存泄漏
- 缓存未清理
- 连接未释放
- 日志文件过大

**解决方案**:
```bash
# 检查内存使用
htop
free -h

# 清理缓存
openclaw cache clear

# 优化代码
openclaw optimize memory

# 重启服务
openclaw restart
```

### 7.3 CPU 使用率过高
**症状**: CPU 使用率持续偏高

**可能原因**:
- 任务过多
- 代码效率问题
- 死循环
- 系统负载过高

**解决方案**:
```bash
# 检查 CPU 使用
htop

# 优化任务
openclaw task optimize

# 限制并发
openclaw config set maxConcurrentTasks 3

# 重启服务
openclaw restart
```

## 8. 安全问题

### 8.1 安全漏洞
**症状**: 系统存在安全风险

**可能原因**:
- 软件版本过旧
- 权限配置不当
- 网络暴露
- 认证机制薄弱

**解决方案**:
```bash
# 更新系统
sudo apt update && sudo apt upgrade

# 检查权限
openclaw security audit

# 配置防火墙
ufw enable
ufw default deny

# 更新密码
openclaw user update-password
```

### 8.2 数据泄露
**症状**: 敏感数据可能泄露

**可能原因**:
- 日志记录敏感信息
- 配置暴露
- 网络传输未加密
- 访问控制不当

**解决方案**:
```bash
# 检查日志
cat /tmp/openclaw/openclaw.log | grep -i password

# 加密配置
openclaw config encrypt

# 配置 HTTPS
openclaw config set https.enabled true

# 审查访问日志
openclaw log review --level error
```

### 8.3 恶意攻击
**症状**: 系统受到攻击

**可能原因**:
- 暴力破解
- DDoS 攻击
- 代码注入
- 恶意文件

**解决方案**:
```bash
# 检查登录失败
cat /var/log/auth.log | grep "Failed password"

# 配置 Fail2Ban
sudo apt install fail2ban
sudo systemctl enable fail2ban

# 扫描恶意文件
clamscan -r /root/.openclaw/
```

## 9. 备份与恢复

### 9.1 备份失败
**症状**: 备份任务无法完成

**可能原因**:
- 存储空间不足
- 网络连接问题
- 配置错误
- 权限不足

**解决方案**:
```bash
# 检查存储空间
df -h

# 测试网络连接
ping backup-server.com

# 检查配置
cat ~/.openclaw/config/backup.json

# 手动备份
openclaw backup manual
```

### 9.2 恢复失败
**症状**: 数据恢复无法完成

**可能原因**:
- 备份文件损坏
- 权限不足
- 版本不兼容
- 存储介质问题

**解决方案**:
```bash
# 检查备份文件
md5sum /backup/openclaw/*.tar.gz

# 验证备份
openclaw backup verify

# 手动恢复
openclaw restore manual --file /backup/openclaw/2023-01-01.tar.gz
```

## 10. 最佳实践

### 10.1 日常维护
```bash
# 每日检查
openclaw daily-check

# 每周优化
openclaw weekly-optimize

# 每月备份
openclaw monthly-backup
```

### 10.2 监控配置
```bash
# 设置监控告警
openclaw config set monitoring.enabled true
openclaw config set monitoring.alerts.email true

# 配置性能指标
openclaw config set performance.maxMemory 80
openclaw config set performance.maxCPU 90
```

### 10.3 安全加固
```bash
# 定期安全审计
openclaw security audit --frequency weekly

# 配置访问控制
openclaw config set security.accessControl true
openclaw config set security.encryption true
```

---
*最后更新: 2026-02-16*
*版本: 1.0*