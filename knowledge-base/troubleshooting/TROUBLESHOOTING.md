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