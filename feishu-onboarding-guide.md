# OpenClaw 飞书（Feishu）使用手册

## 一、快速开始：Bot 授权与配对

### 1. 1 添加 Bot 到工作区
1. 打开飞书管理后台（`https://admin.feishu.cn/`）
2. 进入 **应用** → **开发后台** → **自建应用**
3. 创建新应用或选择现有应用
4. 在 **应用信息** 中复制 `App ID` 和 `App Secret`（如已有，请确保与当前配置一致）：
   - `App ID`: `cli_a90ddd871ab9dbc8`
   - `App Secret`: `i930Lycuthaij7yVQRms8bUHWgBUEp6r`

### 1. 2 权限范围（Scope）配置
在 **权限管理** 页面，为 Bot 添加以下权限（根据需求选择）：
- `chat:bot`（在群组中发送消息）
- `chat:read`（读取群组消息）
- `contact:read`（读取用户信息）
- `wiki:read`、`wiki:write`（读写知识库）
- `drive:read`、`drive:write`（读写云文档）
- `bitable:read`、`bitable:write`（读写多维表格）

保存后 **发布** 应用，使权限生效。

---

## 二、Bot 上线与群组配置

### 2. 1 发布应用到工作区
1. 在管理后台 **应用** 列表中找到你的应用
2. 点击 **发布** → **全员可见** 或指定部门可见
3. 确认发布后，Bot 可在工作区中被搜索到

### 2. 2 邀 Bot入群
1. 在飞书群聊中，点击右上角 **…** → **添加成员**
2. 搜索 Bot 名称（或 App ID）并添加
3. Bot 入群后会自动发送欢迎消息与配对码

### 2. 3 完成配对（Pairing）
首次在群组中使用时，Bot 会返回一个 **配对码**。在 OpenClaw 中执行：

```bash
openclaw pairing approve feishu <pairing_code>
```

配对成功后，Bot 即可响应群组内的 `@Bot` 消息。

---

## 三、常用功能与操作

### 3. 1 发送消息
在你的群组中 `@Bot` 发送指令，例如：
- `@Bot 你好` → Bot 会回复问候
- `@Bot 市场情况` → Bot 会触发对应的技能
- `@Bot 创建文档` → Bot 会在指定位置创建云文档

### 3. 2 知识库（Wiki）操作
Bot 已具备 Wiki 读写权限，你可以：
- 用 `/wiki create` 创建知识库页面
- 用 `/wiki edit <node_token>` 编辑已有页面
- 用 `/wiki list` 列出可用空间

### 3. 3 云文档（Drive）操作
Bot 可创建/读写云文档：
- `/drive create 文档标题` → 创建新文档
- `/drive write <file_token> 内容` → 写入内容
- `/drive read <file_token>` → 读取内容

### 3. 4 多维表格（Bitable）
Bot 可操作表格：
- `/bitable list_tables <app_token>` → 列出表格
- `/bitable add_record <table_id> 字段数据` → 新增记录

---

## 四、实用命令速查

| 场景 | 命令（在群组中@Bot后发送） | 说明 |
|------|-----------------------|------|
| 配对 | 自动收到配对码，随后执行 `openclaw pairing approve feishu <code>` | 一次性 |
| 创建文档 | `/drive create 项目计划` | 在当前空间创建文档 |
| 列出空间 | `/wiki spaces` | 查看可用 Wiki 空间 |
| 列出文件 | `/drive list` | 查看当前目录文件 |
| 写入内容 | `/drive write <file_token> 新的内容` | 需先获取 file_token |

---

## 五、常见问题排查

| 问题 | 可能原因 | 解决 |
|------|----------|------|
| Bot 不响应 @提及 | 未完成配对 / Bot 不在群组 | 确认 Bot 已入群，并检查 `/openclaw pairing list` |
| 权限错误“access denied” | 应用权限范围不足 | 在飞书管理后台添加对应权限后重新发布 |
| 找不到 Wiki 空间 | Bot 未被加入 Wiki 成员 | 在 Wiki 设置 → 成员中添加 Bot |
| 消息发送失败 | `groupPolicy` 限制 | 确保 OpenClaw 配置中 `channels.feishu.groupPolicy = "open"` |

---

## 六、安全与最佳实践

1. **最小权限原则**：仅授予 Bot 完成必需任务的最小权限
2. **定期审计**：检查 `openclaw/plugins/feishu` 的调用日志
3. **敏感信息**：避免在公开群组讨论密钥，重要操作使用私聊
4. **配对管理**：及时清理不再使用的配对（`openclaw pairing list` / `revoke`）

---

## 七、下一步

- 如需定制更多功能（如自动报告、订阅通知），可联系系统管理员扩展技能
- 可将本手册保存到 Wiki 空间（路径：`/wiki/OpenClaw 使用手册`）

祝您使用愉快！如果在配置过程中遇到问题，随时在群组里 @我 获取帮助。

---
*文档版本：1.0 (Last updated: 2025-02-16)*