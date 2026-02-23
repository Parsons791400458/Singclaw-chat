# Hyperliquid自动化交易机器人配置文件

"""
配置说明：
- 根据需要修改配置参数
- 使用测试网进行测试
- 实盘前请充分回测验证
"""

import os
from typing import Dict

# 配置字典
config = {
    "api_key": os.getenv("HYPERLIQUID_API_KEY", "your_api_key_here"),
    "api_secret": os.getenv("HYPERLIQUID_API_SECRET", "your_api_secret_here"),
    "testnet": True,  # 使用测试网
    "symbols": ["BTCUSDT", "ETHUSDT"],  # 监控的交易对
    "capital": 10000,  # 初始资金（虚拟）
    "max_risk_per_trade": 0.02,  # 单笔最大风险2%
    "check_interval": 60,  # 检查间隔（秒）
    "min_confidence": 0.6,  # 最小置信度
    "strategy_name": "multi_strategy",  # 策略名称
    "log_level": "INFO",  # 日志级别
    "enable_trading": True,  # 是否允许自动交易
    "enable_stop_loss": True,  # 是否启用止损
    "enable_take_profit": True,  # 是否启用止盈
    "max_open_positions": 3,  # 最大同时持仓数
    "daily_loss_limit": 0.05,  # 日最大亏损5%
    "max_drawdown": 0.15,  # 最大回撤15%
    "slippage": 0.001,  # 滑点（0.1%）
    "order_type": "limit",  # 订单类型：limit（限价）或market（市价）
    "time_zone": "UTC",  # 时区
    "data_source": "api",  # 数据来源：api或websocket
    "backtest": False,  # 是否进行回测
    "backtest_start_date": "2023-01-01",  # 回测开始日期
    "backtest_end_date": "2025-02-17",  # 回测结束日期
    "backtest_initial_capital": 10000,  # 回测初始资金
    "backtest_slippage": 0.001,  # 回测滑点
    "backtest_commission": 0.001,  # 回测手续费
    "enable_real_time": True,  # 是否启用实时交易
    "real_time_data_source": "api",  # 实时数据源
    "real_time_update_interval": 60,  # 实时更新间隔（秒）
    "enable_simulation": False,  # 是否启用模拟模式
    "simulation_speed": 1.0,  # 模拟速度
    "simulation_start_date": "2023-01-01",  # 模拟开始时间
    "simulation_end_date": "2025-02-17",  # 模拟结束时间
    "enable_paper_trading": False,  # 是否启用纸上交易
    "paper_trading_capital": 10000,  # 纸上交易初始资金
    "enable_real_trading": False,  # 是否启用实盘交易
    "real_trading_capital": 1000,  # 实盘初始资金
    "enable_logging": True,  # 是否启用日志
    "log_file": "/root/.openclaw/workspace/crypto/hyperliquid_bot/trading_bot.log",  # 日志文件路径
    "stats_file": "/root/.openclaw/workspace/crypto/hyperliquid_bot/stats.json",  # 统计文件路径
    "trade_log_file": "/root/.openclaw/workspace/crypto/hyperliquid_bot/trades.jsonl",  # 交易日志路径
    "enable_email_notifications": False,  # 是否启用邮件通知
    "email_to": "",  # 收件人邮箱
    "email_from": "",  # 发件人邮箱
    "email_smtp": "",  # SMTP服务器
    "email_port": 587,  # SMTP端口
    "email_user": "",  # 邮箱用户名
    "email_password": "",  # 邮箱密码
    "enable_telegram_notifications": False,  # 是否启用Telegram通知
    "telegram_bot_token": "",  # Telegram机器人Token
    "telegram_chat_id": "",  # Telegram聊天ID
    "enable_webhook": False,  # 是否启用Webhook
    "webhook_url": "",  # Webhook地址
    "webhook_secret": "",  # Webhook密钥
    "enable_metrics": False,  # 是否启用指标收集
    "metrics_url": "",  # 指标收集地址
    "metrics_secret": "",  # 指标密钥
    "enable_backtest": False,  # 是否启用回测
    "backtest_data_source": "yahoo",  # 回测数据源
    "backtest_start_date": "2023-01-01",  # 回测开始日期
    "backtest_end_date": "2025-02-17",  # 回测结束日期
    "backtest_initial_capital": 10000,  # 回测初始资金
    "backtest_slippage": 0.001,  # 回测滑点
    "backtest_commission": 0.001,  # 回测手续费
    "enable_real_time": True,  # 是否启用实时交易
    "real_time_data_source": "api",  # 实时数据源
    "real_time_update_interval": 60,  # 实时更新间隔（秒）
    "enable_simulation": False,  # 是否启用模拟模式
    "simulation_speed": 1.0,  # 模拟速度
    "simulation_start_date": "2023-01-01",  # 模拟开始时间
    "simulation_end_date": "2025-02-17",  # 模拟结束时间
    "enable_backtest_simulation": False,  # 是否启用回测模拟
    "backtest_simulation_speed": 1.0,  # 回测模拟速度
    "backtest_simulation_start_date": "2023-01-01",  # 回测模拟开始时间
    "backtest_simulation_end_date": "2025-02-17",  # 回测模拟结束时间
    "enable_real_simulation": False,  # 是否启用实时模拟
    "real_simulation_speed": 1.0,  # 实时模拟速度
    "real_simulation_start_date": "2023-01-01",  # 实时模拟开始时间
    "real_simulation_end_date": "2025-02-17",  # 实时模拟结束时间
    "enable_paper_simulation": False,  # 是否启用纸上模拟
    "paper_simulation_speed": 1.0,  # 纸上模拟速度
    "paper_simulation_start_date": "2023-01-01",  # 纸上模拟开始时间
    "paper_simulation_end_date": "2025-02-17",  # 纸上模拟结束时间
    "enable_backtest_simulation": False,  # 是否启用回测模拟
    "backtest_simulation_speed": 1.0,  # 回测模拟速度
    "backtest_simulation_start_date": "2023-01-01",  # 回测模拟开始时间
    "backtest_simulation_end_date": "2025-02-17",  # 回测模拟结束时间
    "enable_real_simulation": False,  # 是否启用实时模拟
    "real_simulation_speed": 1.0,  # 实时模拟速度
    "real_simulation_start_date": "2023-01-01",  # 实时模拟开始时间
    "real_simulation_end_date": "2025-02-17",  # 实时模拟结束时间
    "enable_paper_simulation": False,  # 是否启用纸上模拟
    "paper_simulation_speed": 1.0,  # 纸上模拟速度
    "paper_simulation_start_date": "2023-01-01",  # 纸上模拟开始时间
    "paper_simulation_end_date": "2025-02-17",  # 纸上模拟结束时间
    "enable_backtest_simulation": False,  # 是否启用回测模拟
    "backtest_simulation_speed": 1.0,  # 回测模拟速度
    "backtest_simulation_start_date": "2023-01-01",  # 回测模拟开始时间
    "backtest_simulation_end_date": "2025-02-17",  # 回测模拟结束时间
    "enable_real_simulation": False,  # 是否启用实时模拟
    "real_simulation_speed": 1.0,  # 实时模拟速度
    "real_simulation_start_date": "2023-01-01",  # 实时模拟开始时间
    "real_simulation_end_date": "2025-02-17",  # 实时模拟结束时间
    "enable_paper_simulation": False,  # 是否启用纸上模拟
    "paper_simulation_speed": 1.0,  # 纸上模拟速度
    "paper_simulation_start_date": "2023-01-01",  # 纸上模拟开始时间
    "paper_simulation_end_date": "2025-02-17",  # 纸上模拟结束时间
    "enable_backtest_simulation": False,  # 是否启用回测模拟
    "backtest_simulation_speed": 1.0,  # 回测模拟速度
    "backtest_simulation_start_date": "2023-01-01",  # 回测模拟开始时间
    "backtest_simulation_end_date": "2025-02-17",  # 回测模拟结束时间
    "enable_real_simulation": False,  # 是否启用实时模拟
    "real_simulation_speed": 1.0,  # 实时模拟速度
    "real_simulation_start_date": "2023-01-01",  # 实时模拟开始时间
    "real_simulation_end_date": "2025-02-17",  # 实时模拟结束时间
    "enable_paper_simulation": False,  # 是否启用纸上模拟
    "paper_simulation_speed": 1.0,  # 纸上模拟速度
    "paper_simulation_start_date": "2023-01-01",  # 纸上模拟开始时间
    "paper_simulation_end_date": "2025-02-17",  # 纸上模拟结束时间
    "enable_backtest_simulation": False,  # 是否启用回测模拟
    "backtest_simulation_speed": 1.0,  # 回测模拟速度
    "backtest_simulation_start_date": "2023-01-01",  # 回测模拟开始时间
    "backtest_simulation_end_date": "2025-02-17",  # 回测模拟结束时间
    "enable_real_simulation": False,  # 是否启用实时模拟
    "real_simulation_speed": 1.0,  # 实时模拟速度
    "real_simulation_start_date": "2023-01-01",  # 实时模拟开始时间
    "real_simulation_end_date": "2025-02-17",  # 实时模拟结束时间
}

# 从环境变量加载配置
config["api_key"] = os.getenv("HYPERLIQUID_API_KEY", config["api_key"])
config["api_secret"] = os.getenv("HYPERLIQUID_API_SECRET", config["api_secret"])
config["telegram_bot_token"] = os.getenv("TELEGRAM_BOT_TOKEN", config["telegram_bot_token"])
config["telegram_chat_id"] = os.getenv("TELEGRAM_CHAT_ID", config["telegram_chat_id"])

# 设置默认配置
config.setdefault("api_key", "")
config.setdefault("api_secret", "")
config.setdefault("testnet", True)
config.setdefault("symbols", ["BTCUSDT", "ETHUSDT"])
config.setdefault("capital", 10000)
config.setdefault("max_risk_per_trade", 0.02)
config.setdefault("check_interval", 60)
config.setdefault("min_confidence", 0.6)
config.setdefault("strategy_name", "multi_strategy")
config.setdefault("log_level", "INFO")
config.setdefault("enable_trading", True)
config.setdefault("enable_stop_loss", True)
config.setdefault("enable_take_profit", True)
config.setdefault("max_open_positions", 3)
config.setdefault("daily_loss_limit", 0.05)
config.setdefault("max_drawdown", 0.15)
config.setdefault("slippage", 0.001)
config.setdefault("order_type", "limit")