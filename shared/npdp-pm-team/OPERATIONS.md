# NPDP产品经理团队运转手册 v1.0

> 融合 NPDP Stage-Gate + Scrum 敏捷 + Agent Cron 自动化
> 核心原则：**Stage-Gate管方向，Scrum管节奏，数据管决策**

---

## 一、角色与职责矩阵（Scrum视角）

```
┌─────────────────────────────────────────────────────┐
│              NPDP × Scrum 角色映射                    │
├──────────┬──────────────┬──────────────────────────┤
│ Scrum角色 │  NPDP团队成员  │  职责                     │
├──────────┼──────────────┼──────────────────────────┤
│ PO       │  明哥(CPO)    │  Product Backlog优先级     │
│          │              │  Stage-Gate决策            │
│          │              │  验收标准定义               │
├──────────┼──────────────┼──────────────────────────┤
│ SM       │  小迭(敏捷交付) │  Sprint规划/站会/回顾       │
│          │              │  阻塞清除/流程守护           │
│          │              │  Burndown跟踪             │
├──────────┼──────────────┼──────────────────────────┤
│ Dev Team │  小洞/小验/    │  各自专业域内执行            │
│          │  小度/小增     │  交叉Review               │
├──────────┼──────────────┼──────────────────────────┤
│ 利益相关人 │  星哥(CEO)    │  战略方向/最终审批           │
└──────────┴──────────────┴──────────────────────────┘
```

---

## 二、Product Backlog 结构

### 文件位置
`shared/npdp-pm-team/BACKLOG.md`

### Backlog分层（NPDP创新类型 × 优先级）

```
Product Backlog
├── 🔴 P0 — 本Sprint必须完成
├── 🟡 P1 — 下Sprint候选
├── 🟢 P2 — Backlog储备
└── 🧊 Icebox — 暂不考虑
```

### Backlog Item 标准格式

```markdown
### [ID] 标题
- **类型**: Epic / Story / Task / Spike(技术调研)
- **创新类型**: 突破式 / 平台式 / 衍生式
- **Stage-Gate阶段**: Discovery / Scoping / BizCase / Dev / Test / Launch
- **优先级**: P0/P1/P2
- **RICE评分**: R=? I=? C=? E=? → 总分=?
- **负责人**: 小洞/小验/小度/小迭/小增
- **验收标准**: 
  - [ ] AC1
  - [ ] AC2
- **状态**: Inbox / Assigned / In Progress / Review / Done / Failed
```

### RICE评分规则（小迭执行，明哥审核）

| 维度 | 定义 | 评分 |
|------|------|------|
| **R**each | 影响用户数/范围 | 1-10 |
| **I**mpact | 对北极星指标的影响 | 0.25/0.5/1/2/3 |
| **C**onfidence | 数据支撑程度 | 20%/50%/80%/100% |
| **E**ffort | 人·Sprint工作量 | 0.5/1/2/3/5 |

`RICE = (R × I × C) / E`

---

## 三、Sprint 节奏

### Sprint周期：2周

```
Week 1                              Week 2
Mon  Tue  Wed  Thu  Fri    Mon  Tue  Wed  Thu  Fri
 │                          │                   │
 ├─ Sprint Planning          │                   │
 │  (明哥+小迭主持)           │                   │
 │                          │                   │
 ├─ Daily Standup ──────────────────────────────┤
 │  (小迭自动执行,每日)       │                   │
 │                          │                   │
 │                    Wed   │                   │
 │                    Mid-Sprint Review          │
 │                    (小度出数据/小迭检查进度)     │
 │                          │                   │
 │                          │              Fri  │
 │                          │               ├── Sprint Review
 │                          │               │   (明哥验收)
 │                          │               ├── Sprint Retro
 │                          │               │   (小迭主持)
 │                          │               └── Backlog Grooming
 │                          │                   (明哥重排优先级)
```

---

## 四、Scrum仪式 × Agent Cron

### 1. 📋 Daily Standup（小迭 · 每工作日）

**Cron**: `每日 09:00 CST`  
**执行者**: 小迭  
**输出**: `artifacts/sprints/standup-YYYY-MM-DD.md`

**站会模板**：
```markdown
# Daily Standup | YYYY-MM-DD

## 昨日完成
- [Agent] 完成了什么

## 今日计划
- [Agent] 计划做什么

## 阻塞项
- [Agent] 被什么卡住 → 建议解法

## Sprint Burndown
- 总Story Points: X
- 已完成: Y (Z%)
- 剩余: X-Y
- 燃尽预测: 🟢正常 / 🟡有风险 / 🔴超期
```

### 2. 🎯 Sprint Planning（明哥+小迭 · 每2周一）

**Cron**: `每隔两周一 09:00 CST`  
**执行者**: 明哥(选Backlog) → 小迭(拆任务)

**Planning流程**：
```
1. 明哥从BACKLOG.md选取本Sprint项
   - 按RICE排序
   - 考虑团队容量（每人每Sprint可用点数）
   - 标注Stage-Gate阶段要求
   
2. 小迭拆解为Sprint Task
   - Epic → Story → Task
   - 估点（Fibonacci: 1/2/3/5/8/13）
   - 分配到具体Agent
   - 写入 SPRINT.md

3. 团队容量规划
   - 小洞: 8点/Sprint（研究型，耗时长）
   - 小验: 10点/Sprint
   - 小度: 10点/Sprint
   - 小增: 10点/Sprint
   - 总容量: 38点/Sprint
```

### 3. 📊 Mid-Sprint Review（小度+小迭 · Sprint第二周三）

**Cron**: `Sprint中间周三 10:00 CST`  
**执行者**: 小度(数据) + 小迭(进度)

**检查项**：
- Sprint Burndown是否正常
- 是否有Scope Creep
- 数据指标是否偏离预期
- 是否需要调整Sprint范围

### 4. ✅ Sprint Review（明哥 · 每2周五）

**Cron**: `每隔两周五 15:00 CST`  
**执行者**: 明哥

**Review流程**：
```
1. 检查每个Sprint Item的完成状态
2. 验收产出物（对照验收标准逐条勾选）
3. Gate决策：完成的工作是否满足当前Stage-Gate要求
4. 更新Backlog优先级
5. 产出Sprint Review报告 → 推送星哥
```

### 5. 🔄 Sprint Retro（小迭 · 每2周五Review后）

**Cron**: 跟随Sprint Review  
**执行者**: 小迭

**Retro模板**：
```markdown
# Sprint Retro | Sprint #X

## 🟢 继续保持 (Keep)
- 什么做得好？

## 🟡 需要改进 (Improve)
- 什么可以更好？

## 🔴 停止做 (Stop)
- 什么在浪费时间？

## 💡 行动项 (Actions)
- [ ] 具体改进措施 → 负责人 → 截止日
```

---

## 五、Stage-Gate × Sprint 融合机制

### 核心设计：Gate Review嵌入Sprint Review

```
Sprint 1: Discovery阶段
  小洞做用户研究 + 竞品分析
  Sprint Review时 → 明哥做Gate 1决策(Go/Kill)

Sprint 2: Scoping + Business Case
  明哥定范围 + 小度做商业论证
  Sprint Review时 → 明哥做Gate 2+3决策

Sprint 3-4: Development
  小迭管Sprint交付 + 小验写PRD
  Sprint Review时 → 明哥做Gate 4决策

Sprint 5: Testing + Launch
  小验做测试 + 小增做GTM
  Sprint Review时 → 明哥做Gate 5决策 → Launch!
```

### Gate决策记录

每次Gate决策写入 `decisions/gate-YYYY-MM-DD-[产品名].md`：

```markdown
# Gate [N] Decision: [产品/功能名]

**日期**: YYYY-MM-DD
**决策者**: 明哥
**决策**: Go / Kill / Hold / Recycle

## Gate检查清单
- [ ] 用户需求验证（小洞报告）
- [ ] 数据支撑（小度简报）
- [ ] 技术可行性（小迭评估）
- [ ] 商业论证（ROI/NPV）
- [ ] 风险评估

## 决策依据
[为什么Go/Kill/Hold/Recycle]

## 下一阶段要求
[进入下一阶段的交付物清单]
```

---

## 六、交叉Review机制

防止质量漂移，每个角色的产出必须被另一个角色Review：

```
小洞(用户研究) → 小验 Review（需求是否可验证？）
小验(PRD/测试) → 小迭 Review（是否可交付？估点合理？）
小迭(交付物)   → 小度 Review（数据埋点是否覆盖？）
小度(数据报告) → 小洞 Review（数据解读是否偏离用户真实行为？）
小增(GTM策略)  → 明哥 Review（是否对齐产品战略？）
```

**规则**：产出者不能Review自己的产出。每个Review必须在24h内完成。

---

## 七、Cron任务总表

| 任务 | 频率 | 执行者 | 输出路径 |
|------|------|--------|---------|
| Daily Standup | 每日 09:00 | 小迭 | artifacts/sprints/standup-*.md |
| Sprint Planning | 双周一 09:00 | 明哥+小迭 | SPRINT.md |
| Mid-Sprint Review | Sprint中周三 10:00 | 小度+小迭 | artifacts/reports/mid-sprint-*.md |
| Sprint Review | 双周五 15:00 | 明哥 | artifacts/sprints/review-*.md |
| Sprint Retro | 双周五 16:00 | 小迭 | reviews/retros/retro-*.md |
| Backlog Grooming | 双周五 17:00 | 明哥 | BACKLOG.md更新 |
| 数据周报 | 每周一 10:00 | 小度 | artifacts/reports/weekly-*.md |
| 竞品监控 | 每周三 10:00 | 小洞 | specs/competitive/monitor-*.md |
| 增长实验报告 | 每周五 10:00 | 小增 | artifacts/growth-experiments/*.md |

---

## 八、信息流与协作规则

### 共享文件结构（单一真相源）

```
shared/npdp-pm-team/
├── BACKLOG.md              ← Product Backlog（明哥维护）
├── SPRINT.md               ← 当前Sprint看板（小迭维护）
├── OPERATIONS.md           ← 本文件
├── TEAM_PROTOCOL.md        ← 团队架构与角色
├── specs/                  ← 需求侧
│   ├── prd/               ← 小验的PRD
│   ├── user-research/     ← 小洞的研究报告
│   ├── user-stories/      ← 小验的用户故事
│   ├── competitive/       ← 小洞的竞品分析
│   ├── opportunities/     ← 小洞的机会评估
│   ├── personas/          ← 小洞的用户画像
│   ├── gtm/              ← 小增的GTM策略
│   └── roadmap/          ← 明哥的产品路线图
├── artifacts/             ← 产出侧
│   ├── sprints/          ← Sprint计划/站会/Review
│   ├── releases/         ← 版本发布记录
│   ├── dashboards/       ← 小度的数据看板
│   ├── reports/          ← 分析报告
│   ├── prototypes/       ← 原型验证
│   ├── growth-experiments/ ← 增长实验
│   ├── lifecycle/        ← 生命周期评估
│   └── meetings/         ← 会议纪要
├── reviews/              ← 评审侧
│   ├── uat/             ← 验收测试
│   └── retros/          ← 回顾改进
├── decisions/            ← 决策侧
│   ├── gate-*.md        ← Gate决策记录
│   └── data-briefs/     ← 数据决策简报
└── agents/              ← 各Agent身份
    ├── cpo/SOUL.md
    ├── insight/SOUL.md
    ├── validate/SOUL.md
    ├── metrics/SOUL.md
    ├── iterate/SOUL.md
    └── growth/SOUL.md
```

### 沟通规则

1. **异步优先**：所有协作通过共享文件，不依赖实时消息
2. **文档即沟通**：口头讨论不算数，写下来才算
3. **阻塞即上报**：卡住10分钟 → 写comment → 继续其他工作
4. **Review不过夜**：收到Review请求24h内完成
5. **明哥周汇报**：每周五Sprint Review后自动推送星哥

---

## 九、度量体系（小度负责）

### 团队效能指标

| 指标 | 计算方式 | 目标 |
|------|---------|------|
| Sprint完成率 | 完成点数/计划点数 | ≥80% |
| 平均Lead Time | 需求提出→上线天数 | ≤14天 |
| Gate通过率 | Go数/(Go+Kill+Recycle) | 60-80% |
| Review返工率 | Recycle数/总Review数 | ≤20% |
| 阻塞平均解决时间 | 阻塞提出→解决 | ≤4h |

### 产品指标（按产品线定义北极星）

每个产品线进入Development阶段前，小度必须定义：
1. **北极星指标**（1个）
2. **AARRR漏斗指标**（5个）
3. **健康度基线**
4. **告警阈值**

---

## 十、启动清单

### 团队上线步骤

- [ ] 1. 创建初始 BACKLOG.md（明哥）
- [ ] 2. 创建首个 SPRINT.md（小迭）
- [ ] 3. 注册Cron任务（柯维协助）
- [ ] 4. 指定第一个产品线进入Stage-Gate
- [ ] 5. 小洞完成首份用户研究
- [ ] 6. 明哥完成首次Gate 1决策
- [ ] 7. 首个Sprint Planning执行
- [ ] 8. 观察一个Sprint周期，Retro调优

### 星哥需要做的
- 指定第一个要跑Stage-Gate的产品/功能
- 确认Sprint周期（建议2周）
- 确认团队Cron是否立即注册
