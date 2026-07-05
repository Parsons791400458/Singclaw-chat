# Contact & Escalation
**生成时间**: 2026-07-05 13:08 UTC

---

## 1. 主要联系人

| Role | Name | Contact | Available |
|---|---|---|---|
| **项目发起人 / Sponsor** | H Sing (username `@syberh`) | Telegram DM 6509109244 | 24/7 (Asia/Shanghai 06:00-23:00 preferred) |
| **PMO / 主助手** | Maxink (本助手) | 同 Telegram DM (机器人桥接) | session 持续 |
| **后接手 agent / Codex** | TBD | 通过 H Sing 分配 | 触发制 |

## 2. 通信协议

### 节奏
- **Telegram DM**: H Sing ↔ Maxink (这是当前活跃链路)
- **频率**: H Sing 主动发需求，PMO 主动报状态
- **紧急响应**: < 5 min 在白天，< 30 min 在 H Sing 在线但慢的时段

### 风格
- 结论先行（首句给答案）
- 短句 + 给证据 + 给下一步
- 中文优先；英文仅在 commit/技术术语
- 不用 markdown 表格（除非必要）

## 3. 紧急升级路径

| 严重度 | 触发 | 动作 |
|---|---|---|
| **P0** 生产中断 | 任何 5xx 持续 > 5 min | 立即 @H Sing + 自愈脚本 |
| **P1** 安全事件 | key 泄漏 / 账号入侵 | 立即 @H Sing (含事项 emergency response) |
| **P2** 阻塞 risk | ISS-004~008 还 open | 主动提示 |
| **P3** Polish | docs / refactor | 等 sprint 节奏 |

## 4. H Sing 主动联系

主动联系 H Sing 的触发：
1. 紧急安全事件
2. 阻塞生产超过 30 min
3. 决策需求（不是我能照 single-source-of-truth 走的）
4. 重大里程碑（sprint 交付）
5. 资金 / billing 警告（LLM 配额 / VM 续费）

## 5. 不要打扰 H Sing

- 23:00-07:00 Asia/Shanghai 非紧急（除非 P0）
- 周日尽量避免 (除非紧急)
- 跨 session 自动 follow-up (用 cron, 不用非紧急通知)

## 6. 接手者 / 多机协同

- 跨 session / 跨机器 → 看 [HANDOFF.md](../HANDOFF.md) §6
- 跨 GitHub → clone 仓 + 走 README 流程
- 跨 Telegram chat → H Sing 拉新对话

— End —
