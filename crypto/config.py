
# Crypto Agent 核心配置
# 2026-03-24 更新，修复账户地址错误问题

# 主网API端点
HYPERLIQUID_MAINNET_API = "https://api.hyperliquid.xyz/info"
HYPERLIQUID_MAINNET_EXEC_API = "https://api.hyperliquid.xyz/exchange"

# 交易账户配置
ACCOUNTS = {
    "xiaoxia": {
        "address": "0xD7C04b230f9f28d286Ba27216c103b1CFfC24126",
        "name": "小夏主网账户",
        "network": "mainnet",
        "active": True,
        "risk_limit": 0.08  # 单日最大亏损8%
    },
    "clawfi": {
        "address": "0x7478d07e8ee9a938225224c542f6f4656637bb98",
        "name": "ClawFi主网账户",
        "network": "mainnet",
        "active": True,
        "risk_limit": 0.1  # 单日最大亏损10%
    }
}

# 交易规则配置
TRADING_RULES = {
    "max_position_size": 0.3,  # 单品种最大仓位30%
    "leverage": 5,  # 默认杠杆5倍
    "stop_loss_pct": 0.02,  # 默认止损2%
    "take_profit_pct": 0.05,  # 默认止盈5%
    "allow_shorting": True,
    "allowed_assets": ["BTC", "ETH", "SOL", "ARB", "OP"]
}

# 告警配置
ALERT_CONFIG = {
    "telegram_chat_id": "6509109244",
    "alert_on_open_position": True,
    "alert_on_close_position": True,
    "alert_on_risk_breach": True,
    "alert_on_daily_review": True
}
