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
*版本: 1.0*