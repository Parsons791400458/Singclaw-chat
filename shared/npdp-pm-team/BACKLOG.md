# 📋 Product Backlog
> **维护人**: 明哥(CPO) | **上次更新**: 2026-04-20 16:22 CST
> **排序规则**: RICE评分降序 | **容量**: 38点/Sprint
> **流程**: 任务完成后自动更新状态，每次更新标注时间和操作人

---

## Backlog管理流程

| 阶段 | 动作 | 负责人 |
|------|------|--------|
| **新增** | 想法/需求进入Backlog，分配编号和优先级 | 柯维 |
| **排期** | 排入Sprint或标记为Idea（想法团队分析中） | 明哥+柯维 |
| **执行** | 推进任务，更新状态(Inbox→In Progress→Review→Done) | 执行人 |
| **完成** | 完成后更新状态=✅Done，标注完成时间 | 执行人/柯维 |
| **回顾** | Sprint结束时回顾未完成项，决定移入/延期/取消 | 明哥+柯维 |

**规则**:
- ✅ 完成后必须在24h内更新Backlog状态
- ⚠️ 超时48h未更新的任务自动升级P0
- 💡 新想法先进入想法团队分析，再决定是否入Backlog

---

## 产品组合总览（四条产品线 × Stage-Gate定位）

| 产品线 | 创新类型 | 当前Stage-Gate | 北极星指标 |
|--------|---------|---------------|-----------|
| SingClaw | 平台式 | Development→Test | 日活用户(DAU) |
| ShrimpFi | 突破式 | Discovery | NFT铸造数 |
| 加密v6.0 | 衍生式 | Discovery | 月收益率 |
| A股v1.1 | 衍生式 | Testing | 策略胜率 |

---

## 🔴 P0 — Sprint 1（本Sprint必须完成）

### [SC-001] SingClaw用户获取基建三件套
- **类型**: Epic
- **创新类型**: 平台式（衍生）
- **Stage-Gate**: Development
- **RICE**: R=8 I=3 C=100% E=2 → **12.0**
- **负责人**: 小增(GTM) + 小度(埋点)
- **验收标准**:
  - [ ] Google Search Console注册+sitemap提交 ← **需星哥操作(10min)**
  - [ ] Umami统计部署+核心事件埋点定义 ← **需星哥操作(5min)**
  - [ ] 首条社交帖子发布+渠道策略文档 ← **待星哥确认文案**
- **状态**: 🟡 阻塞（等待星哥）
- **Story Points**: 5
- **备注**: 已拖延12天。文案已出三个版本(Twitter/小红书/即刻)，待确认后发布

### [AS-001] A股v1.1止损规则分级升级
- **类型**: Story
- **创新类型**: 衍生式
- **Stage-Gate**: Testing → **✅ Done**
- **RICE**: R=3 I=3 C=80% E=1 → **7.2**
- **负责人**: 小验(规则定义) + 小度(回测数据)
- **验收标准**:
  - [x] AND止损→分级止损规则PRD ✅ 04-17
  - [x] 历史回测验证（≥20个交易日）✅ 04-18, 4假设全部通过
  - [x] v1.2规则文档产出 ✅ 04-20
- **状态**: ✅ Done (04-20) → Review队列(小洞, DDL 04-26)
- **Story Points**: 5
- **下一步**: 04-21实盘首验(M5)

### [CR-001] 加密v6.0 Discovery用户研究
- **类型**: Spike(技术调研)
- **创新类型**: 衍生式
- **Stage-Gate**: Discovery
- **RICE**: R=5 I=2 C=50% E=2 → **2.5**
- **负责人**: 小洞(用户研究)
- **验收标准**:
  - [ ] 策略交易工具竞品矩阵（≥10个产品）
  - [ ] 目标用户画像(Persona)
  - [ ] JTBD分析（用户雇佣交易工具完成什么任务）
  - [ ] 机会评估报告
- **状态**: Inbox
- **Story Points**: 8
- **备注**: v5.3双Key延误两周零实盘，需重新评估产品方向

### [SF-001] ShrimpFi Discovery用户研究+竞品分析
- **类型**: Spike(技术调研)
- **创新类型**: 突破式
- **Stage-Gate**: Discovery
- **RICE**: R=6 I=2 C=50% E=3 → **2.0**
- **负责人**: 小洞(竞品分析)
- **验收标准**:
  - [ ] GameFi赛道竞品矩阵（≥15个项目，含Base链）
  - [ ] 目标用户画像
  - [ ] Kano需求分类（基本/期望/兴奋）
  - [ ] TAM/SAM/SOM估算
- **状态**: Inbox
- **Story Points**: 8

### [SC-002] SingClaw数据度量体系搭建
- **类型**: Story
- **创新类型**: 平台式
- **Stage-Gate**: Development → **✅ Done**
- **RICE**: R=8 I=2 C=80% E=2 → **6.4**
- **负责人**: 小度
- **验收标准**:
  - [x] AARRR漏斗指标定义 ✅
  - [x] 健康度评分体系 ✅
  - [x] 数据看板模板 ✅
  - [x] 告警阈值设定 ✅
- **状态**: ✅ Done (04-20) → Review队列(小增, DDL 04-26)
- **Story Points**: 5
- **产出**: `artifacts/dashboards/sc-002-metrics-framework.md`

---

## 🟡 P1 — Sprint 2候选

### [SC-003] SingClaw内容SEO长尾优化
- **RICE**: R=8 I=1 C=80% E=2 → **3.2**
- **负责人**: 小验(关键词PRD) + 小增(执行)
- **Stage-Gate**: Development
- **Story Points**: 5

### [SF-002] ShrimpFi商业论证(Business Case)
- **RICE**: R=6 I=2 C=50% E=3 → **2.0**
- **负责人**: 小度(财务模型) + 小洞(概念测试)
- **Stage-Gate**: Business Case（需Gate 1通过）
- **Story Points**: 8

### [AS-002] A股v1.1情绪周期完整回测报告
- **RICE**: R=3 I=2 C=80% E=2 → **2.4**
- **负责人**: 小度(回测) + 小验(验证标准)
- **Stage-Gate**: Testing
- **Story Points**: 5

### [CR-002] 加密社交动量引擎Scoping
- **RICE**: R=5 I=2 C=50% E=2 → **2.5**
- **负责人**: 明哥(范围定义)
- **Stage-Gate**: Scoping（需Gate 1通过）
- **Story Points**: 3

---

## 🟢 P2 — Backlog储备

### [SC-004] SingClaw邮箱订阅自动化
- **Stage-Gate**: Development | **Story Points**: 3

### [SF-003] ShrimpFi NFT艺术风格定义
- **Stage-Gate**: Development（需Gate 3通过）| **Story Points**: 5

### [CR-003] 加密v6.0策略回测框架
- **Stage-Gate**: Development（需Gate 3通过）| **Story Points**: 8

### [SC-005] SingClaw多平台内容分发
- **Stage-Gate**: Launch | **Story Points**: 5

---

## 🧊 Icebox

*(暂无)*

---

## 🆕 今日新增（2026-04-20）

### [L-001] 学习材料标准化模板
- **来源**: 学习会话 04-20
- **内容**: 含启发/行动项/Backlog追踪的标准化学习产出模板
- **负责人**: 小迭 | **DDL**: 04-22
- **状态**: 🟡 In Progress

### [L-002] 首次双周学习会
- **来源**: 学习会话 04-20
- **内容**: 主题"AI产品度量体系"，建立定期学习机制
- **负责人**: 小度 | **DDL**: 05-01
- **状态**: 🟡 待启动

### [L-003] AI文章自动扫描+推荐入库
- **来源**: 学习会话 04-20
- **内容**: g-crypto-alpha每日扫描AI领域高价值文章自动入库
- **负责人**: g-crypto-alpha | **DDL**: 04-25
- **状态**: 🟡 待启动

### [PI-001] 原型验证Gate流程
- **来源**: 学习会话 04-20 (Cat Wu文章启发)
- **内容**: Stage-Gate中Spec后增加原型验证步骤，spec→原型→可行→再PRD
- **类型**: 流程改进 | **状态**: 💡 想法分析中 → 待星哥确认是否加入标准流程

### [PI-002] 模型发布自动触发功能复审
- **来源**: 学习会话 04-20 (Cat Wu文章启发)
- **内容**: 新模型发布→自动对比现有PRD能力假设→标记需重评项
- **类型**: 流程改进 | **状态**: 💡 想法分析中 → 待星哥确认

### [PI-003] 脚手架行为监控机制
- **来源**: 学习会话 04-20 (Cat Wu文章启发)
- **内容**: 建立用户脚手架行为追踪表，每周Review发现产品机会
- **类型**: 流程改进 | **状态**: 💡 想法分析中 → 想法团队可扩展

### [IDEA-001] AI能力基准仪表盘
- **来源**: 学习会话 04-20
- **内容**: 定期评测主流模型在各任务上能力，GTM引流
- **状态**: 💡 想法团队分析中 → 详见 `shared/idea-team/analysis/`

### [IDEA-002] Sprint自动化助手
- **来源**: 学习会话 04-20
- **内容**: 任务idle自动分配、Review超时自动Pass
- **状态**: 💡 想法团队分析中

### [IDEA-003] 产品灵感日报
- **来源**: 学习会话 04-20
- **内容**: 每日扫描HN/Product Hunt/Twitter抓产品灵感信号
- **状态**: 💡 想法团队分析中

---

*明哥备注：Sprint 1总点数=31/38容量，留7点buffer给突发。ShrimpFi和加密v6.0的Discovery各占8点，由小洞串行执行（先ShrimpFi后加密，或并行分割时间）。*
