# Hyperliquid自动化交易机器人

## 📊 项目概述

完全自动化的加密货币交易系统，基于Hyperliquid API，实现：
- ✅ 实时市场数据获取
- ✅ 多策略交易信号生成
- ✅ 自动风险管理
- ✅ 自动订单执行
- ✅ 交易日志记录
- ✅ 绩效统计报告

## 🚀 快速开始

### 1. 环境准备

安装Python依赖：
```bash
cd /root/.openclaw/workspace/crypto/hyperliquid_bot
pip install -r requirements.txt
```

### 2. 获取Hyperliquid API密钥

1. 访问 https://hyperliquid.xyz
2. 注册/登录账户
3. 进入API设置页面
4. 创建API Key
5. 记录API Key和Secret

### 3. 配置机器人

编辑 `config.py` 或直接修改代码中的配置：

```python
config = {
    "api_key": "your_api_key_here",
    "api_secret": "your_api_secret_here",
    "testnet": True,  # 使用测试网
    "symbols": ["BTCUSDT", "ETHUSDT"],
    "capital": 10000,  # 初始资金（虚拟）
    "max_risk_per_trade": 0.02,  # 单笔最大风险2%
    "check_interval": 60  # 检查间隔（秒）
}
```

### 4. 运行机器人

```bash
python3 trading_bot.py
```

## 📁 文件结构

```
hyperliquid_bot/
├── hyperliquid_api.py      # API客户端封装
├── indicators.py           # 技术指标计算
├── strategy.py             # 交易策略实现
├── risk_manager.py         # 风险管理模块
├── trading_bot.py          # 主机器人程序
├── config.py               # 配置文件（需创建）
├── requirements.txt        # Python依赖
├── README.md               # 本文档
├── trades.jsonl            # 交易日志（自动生成）
├── stats.json              # 统计信息（自动生成）
└── trading_bot.log         # 运行日志（自动生成）
```

## 🎯 策略说明

### 1. 趋势跟踪策略
**条件：**
- 均线金叉（MA20 > MA50）
- RSI > 50
- MACD金叉

**止损止盈：**
- 止损：2×ATR
- 止盈：4×ATR

### 2. 突破策略
**条件：**
- 价格突破布林带上轨
- 成交量放大1.5倍
- RSI < 70

**止损止盈：**
- 止损：2×ATR
- 止盈：3×ATR

### 3. 均值回归策略
**条件：**
- 价格触及布林带下轨
- RSI < 30
- KDJ超卖

**止损止盈：**
- 止损：2×ATR
- 止盈：3×ATR

### 4. 多策略组合
机器人自动运行多个策略，选择：
- 置信度最高的信号
- 投票机制（多个策略同时给出相同信号时置信度提升）

## ⚠️ 风险管理

### 核心规则：
1. **单笔风险：** ≤2%总资金
2. **最大仓位：** ≤10%总资金
3. **止损设置：** 2×ATR
4. **风险回报比：** ≥1:2

### 风控检查：
- ✅ 止损距离合理性
- ✅ 仓位大小限制
- ✅ 总风险控制
- ✅ 波动率调整

## 📊 输出文件

### 日志文件：
- `trading_bot.log` - 实时运行日志
- `trades.jsonl` - JSON格式交易记录

### 统计文件：
- `stats.json` - 绩效统计数据
  - 总交易数
  - 胜率
  - 平均盈亏比
  - 最大回撤

## 🛠️ 开发说明

### 需要完成的部分：

1. **API签名实现** (`hyperliquid_api.py`)
   - 在 `_sign_request` 方法中实现Hyperliquid的签名算法
   - 参考 https://docs.hyperliquid.xyz 获取签名详情

2. **端点调整** (`hyperliquid_api.py`)
   - 根据真实API文档调整所有端点URL
   - 确保请求参数格式正确

3. **策略参数优化** (`strategy.py`)
   - 根据实际表现调整策略参数
   - 可以添加更多策略

4. **配置管理** (`config.py`)
   - 将硬编码配置移出主程序
   - 支持环境变量和配置文件

## 🔧 待实现功能

### 短期：
- [ ] 实现正确的API签名
- [ ] 获取历史数据回测
- [ ] 实现更完善的错误处理
- [ ] 添加Telegram通知

### 中期：
- [ ] 实现WebSocket实时数据
- [ ] 添加更多技术指标
- [ ] 机器学习信号增强
- [ ] 多时间周期分析

### 长期：
- [ ] 策略自动优化
- [ ] 风险自适应调整
- [ ] 多交易所支持
- [ ] 高级回测系统

## 📈 性能优化

### 监控指标：
- 交易频率
- 信号准确率
- 平均持仓时间
- 滑点控制

### 优化方向：
1. 信号过滤（减少假信号）
2. 仓位动态调整
3. 市场状态识别
4. 策略组合优化

## 🚨 风险提示

⚠️ **重要警告：**
- 本系统仅供学习和测试使用
- 使用测试网进行充分回测
- 实盘前请严格验证策略
- 仅使用可承受损失的资金
- 加密货币交易风险极高

## 📞 支持

遇到问题：
1. 查看日志文件 `trading_bot.log`
2. 检查配置文件是否正确
3. 确认API密钥有效
4. 验证网络连接

---

**项目状态：** 🔴 **待完成API签名**  
**最后更新：** 2025-02-17  
**版本：** 1.0.0

🚀 **开始前请务必完成API文档研究和签名实现！**