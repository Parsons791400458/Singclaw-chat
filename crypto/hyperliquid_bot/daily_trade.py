#!/usr/bin/env python3
"""
每日自动交易脚本（Hyperliquid测试网）

功能：
- 每小时执行一次，每日生成至少8笔交易
- 使用Agent钱包签名
- 采用2%单笔风险+2xATR止损+4xATR止盈策略
- 记录所有交易到 logs/trades.jsonl
"""

import os
import time
import json
import logging
from datetime import datetime, date
from pathlib import Path
from eth_account import Account
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils.constants import TESTNET_API_URL

# 配置
MAIN_ADDRESS = os.getenv('HYPERLIQUID_ADDRESS')
PRIVATE_KEY = os.getenv('HYPERLIQUID_PRIVATE_KEY')
API_URL = os.getenv('HYPERLIQUID_API_URL', 'https://api.hyperliquid-testnet.xyz')

assert MAIN_ADDRESS and PRIVATE_KEY, "Missing HYPERLIQUID_ADDRESS or HYPERLIQUID_PRIVATE_KEY"

# 路径
LOG_DIR = Path('/root/.openclaw/workspace/crypto/logs')
DB_FILE = LOG_DIR / 'trades.jsonl'
COUNTER_FILE = LOG_DIR / 'trade_counter.json'
DAILY_TRADE_LOG = LOG_DIR / 'daily_trade.log'

LOG_DIR.mkdir(parents=True, exist_ok=True)

# 日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(DAILY_TRADE_LOG),
        logging.StreamHandler()
    ]
)

# 常量
SYMBOLS = ['BTC', 'ETH', 'SOL']
LEVERAGE = 3
RISK_PERCENT = 0.02
ATR_WINDOW = 14
MIN_ORDER_VALUE_USD = 10.0  # 测试网最小订单价值

class HyperliquidTrader:
    def __init__(self):
        self.account = Account.from_key(PRIVATE_KEY)
        self.exchange = Exchange(wallet=self.account, base_url=API_URL)
        self.info = Info(base_url=API_URL)

        # 读取每日计数器
        self.counter = self.load_counter()
        logging.info(f"初始化完成，今日订单数: {self.counter.get('count', 0)}")

    def load_counter(self):
        """加载今日订单计数器"""
        today = date.today().isoformat()
        if COUNTER_FILE.exists():
            try:
                with open(COUNTER_FILE, 'r') as f:
                    data = json.load(f)
                if data.get('date') == today:
                    return data
            except Exception as e:
                logging.warning(f"加载计数器失败: {e}")
        return {'date': today, 'count': 0}

    def save_counter(self):
        """保存计数器"""
        with open(COUNTER_FILE, 'w') as f:
            json.dump(self.counter, f)

    def can_trade(self):
        """是否还能继续交易（每日最多无硬限制，但可自行添加上限）"""
        # 至少8笔的目标，这里起截至8, 8*...
        return True

    def get_account_value(self):
        """获取主账户净值"""
        try:
            state = self.info.user_state(MAIN_ADDRESS)
            margin = state.get('marginSummary', {})
            value = float(margin.get('accountValue', 0))
            return value
        except Exception as e:
            logging.error(f"获取账户价值失败: {e}")
            return 0

    def fetch_klines(self, symbol: str, n: int = 50, interval: str = '1m'):
        """获取K线数据"""
        try:
            # 计算开始时间（n个1分钟前）
            end = int(time.time() * 1000)
            start = end - n * 60 * 1000
            candles = self.info.candles_snapshot(symbol, interval, start, end)
            return candles
        except Exception as e:
            logging.error(f"获取K线失败 {symbol}: {e}")
            return None

    def compute_atr(self, candles, window=14):
        """计算平均真实波幅（ATR）"""
        if not candles or len(candles) < window + 1:
            return None
        highs = [float(c['h']) for c in candles]
        lows = [float(c['l']) for c in candles]
        closes = [float(c['c']) for c in candles]

        true_ranges = []
        for i in range(1, len(candles)):
            h = highs[i]
            l = lows[i]
            pc = closes[i-1]
            tr = max(h - l, abs(h - pc), abs(l - pc))
            true_ranges.append(tr)

        if len(true_ranges) < window:
            return None
        atr = sum(true_ranges[-window:]) / window
        return atr

    def get_mid_price(self, symbol: str):
        """获取中价"""
        try:
            all_mids = self.info.all_mids()
            coin = symbol.split('-')[0] if '-' in symbol else symbol  # BTC-PERP -> BTC
            price_str = all_mids.get(coin)
            return float(price_str) if price_str else None
        except Exception as e:
            logging.error(f"获取中价失败 {symbol}: {e}")
            return None

    def place_order(self, symbol: str, side: str, size: float, price: float, leverage: int = LEVERAGE, reduce_only: bool = False):
        """下单"""
        try:
            order_type = {"limit": {"tif": "Gtc"}}
            # 确保价格为整数以避免浮点精度问题
            limit_px = int(round(price))

            result = self.exchange.order(
                name=symbol,
                is_buy=(side.lower() == 'buy'),
                sz=size,
                limit_px=limit_px,
                order_type=order_type,
                reduce_only=reduce_only
            )
            return result
        except Exception as e:
            logging.error(f"下单异常 {symbol} {side} {size}@{price}: {e}")
            return None

    def record_trade(self, trade_info: dict):
        """记录交易"""
        trade_info['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        try:
            with open(DB_FILE, 'a') as f:
                f.write(json.dumps(trade_info) + '\n')
            logging.info(f"交易已记录: {trade_info.get('order_id', 'N/A')}")
        except Exception as e:
            logging.error(f"记录交易失败: {e}")

    def run_once(self):
        """执行一轮交易（尝试所有满足条件的币种）"""
        if not self.can_trade():
            logging.info("今日达到目标订单数，停止交易")
            return False

        account_value = self.get_account_value()
        if account_value <= 0:
            logging.warning("账户价值为0或无法获取，跳过本轮")
            return False

        risk_amount = account_value * RISK_PERCENT
        logging.info(f"账户价值: ${account_value:.2f}，单笔风险: ${risk_amount:.2f}")

        for symbol in SYMBOLS:
            # 检查是否已达到订单目标
            if self.counter['count'] >= 8:
                logging.info("已生成至少8笔订单，本日任务完成")
                return False

            # 获取当前价格
            price = self.get_mid_price(symbol)
            if not price:
                logging.warning(f"无法获取{symbol}价格，跳过")
                continue

            # 获取ATR
            candles = self.fetch_klines(symbol, n=ATR_WINDOW + 5)
            atr = self.compute_atr(candles, ATR_WINDOW) if candles else None
            if atr is None:
                logging.warning(f"无法计算{symbol}的ATR，跳过")
                continue

            # 计算止损止盈
            stop_loss = price - 2 * atr
            take_profit = price + 4 * atr
            # 数量基于止损距离
            stop_distance = price - stop_loss
            if stop_distance <= 0:
                logging.warning(f"{symbol}止损距离非正，跳过")
                continue
            size = risk_amount / stop_distance
            # 取合适精度
            size = round(size, 8)

            # 检查最小订单价值
            order_value = size * price
            if order_value < MIN_ORDER_VALUE_USD:
                logging.warning(f"{symbol}订单价值(${order_value:.2f})低于最小要求(${MIN_ORDER_VALUE_USD})，跳过")
                continue

            # 下单：只做多头示例（简化）
            result = self.place_order(symbol, side='buy', size=size, price=price, leverage=LEVERAGE)
            if result and isinstance(result, dict) and result.get('status') == 'ok':
                order_id = result.get('response', {}).get('orderId', 'unknown')
                # 记录
                trade = {
                    'symbol': symbol,
                    'side': 'buy',
                    'size': size,
                    'price': price,
                    'leverage': leverage,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'atr': atr,
                    'order_id': order_id,
                    'order_value': order_value,
                    'risk_amount': risk_amount,
                    'account_value': account_value,
                }
                self.record_trade(trade)
                self.counter['count'] += 1
                self.save_counter()
                logging.info(f"下单成功: {symbol} {size}@{price} (ATR={atr:.2f}, SL={stop_loss:.2f}, TP={take_profit:.2f})")
            else:
                logging.warning(f"下单失败: {result}")

        return True

def main():
    logging.info("="*60)
    logging.info("每日自动化交易脚本启动")
    logging.info(f"主地址: {MAIN_ADDRESS}")
    logging.info(f"测试网: {API_URL}")
    logging.info("="*60)

    trader = HyperliquidTrader()
    try:
        trader.run_once()
    except KeyboardInterrupt:
        logging.info("用户中断")
    except Exception as e:
        logging.error(f"运行异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        logging.info("本次执行结束")

if __name__ == "__main__":
    main()