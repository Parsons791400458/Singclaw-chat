#!/usr/bin/env python3
"""
Hyperliquid 自动化交易系统 - 主入口
集成策略、风险管理、交易执行
"""

import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
from eth_account import Account

# 导入本地模块
import sys
sys.path.append('/root/.openclaw/workspace/crypto/hyperliquid_bot')
from indicators import TechnicalIndicators

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/.openclaw/workspace/crypto/logs/trading_bot.log'),
        logging.StreamHandler()
    ]
)

class HyperliquidTradingBot:
    """Hyperliquid自动化交易机器人"""
    
    def __init__(self, private_key: str, testnet: bool = True):
        """
        初始化交易机器人
        
        Args:
            private_key: 钱包私钥（0x开头）
            testnet: 是否使用测试网
        """
        self.testnet = testnet
        self.private_key = private_key
        
        # 初始化钱包
        self.account = Account.from_key(private_key)
        self.wallet_address = self.account.address
        
        # 初始化API
        if testnet:
            self.info = Info(constants.TESTNET_API_URL, skip_ws=True)
            self.exchange = Exchange(
                self.account,
                base_url=constants.TESTNET_API_URL
            )
        else:
            self.info = Info(constants.MAINNET_API_URL, skip_ws=True)
            self.exchange = Exchange(
                self.account,
                base_url=constants.MAINNET_API_URL
            )
        
        # 交易参数
        self.symbols = ["0G", "2Z"]  # Hyperliquid交易对（BTC=0G，ETH=2Z）
        self.timeframe = "1h"  # 时间框架
        self.limit = 100  # K线数量
        
        # 风险管理
        self.total_capital = 10000  # 总资金（USDT）
        self.max_risk_per_trade = 0.02  # 单笔最大风险2%
        self.max_position_size = 0.1  # 最大仓位10%
        
        # 状态跟踪
        self.positions = {}
        self.trade_history = []
        
        logging.info(f"🤖 Trading Bot 初始化完成")
        logging.info(f"钱包地址: {self.wallet_address}")
        logging.info(f"环境: {'测试网' if testnet else '主网'}")
    
    def get_klines(self, symbol: str) -> Optional[pd.DataFrame]:
        """获取K线数据"""
        try:
            # 使用Info获取K线数据
            candles = self.info.candles_snapshot(
                name=symbol,
                interval=self.timeframe,
                startTime=int((datetime.now().timestamp() - 3600 * self.limit) * 1000),
                endTime=int(datetime.now().timestamp() * 1000)
            )
            
            if not candles:
                logging.warning(f"未获取到 {symbol} 的K线数据")
                return None
            
            # 转换为DataFrame
            df = pd.DataFrame(candles)
            df['timestamp'] = pd.to_datetime(df['T'], unit='ms')
            df['open'] = pd.to_numeric(df['o'])
            df['high'] = pd.to_numeric(df['h'])
            df['low'] = pd.to_numeric(df['l'])
            df['close'] = pd.to_numeric(df['c'])
            df['volume'] = pd.to_numeric(df['v'])
            
            return df
            
        except Exception as e:
            logging.error(f"获取K线数据失败 {symbol}: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """获取当前价格"""
        try:
            # 获取所有中间价
            all_mids = self.info.all_mids()
            if symbol in all_mids:
                return float(all_mids[symbol])
            else:
                # 尝试不同格式
                symbol_clean = symbol.replace("USDT", "")
                if symbol_clean in all_mids:
                    return float(all_mids[symbol_clean])
            return None
        except Exception as e:
            logging.error(f"获取价格失败 {symbol}: {e}")
            return None
    
    def calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """计算技术指标"""
        if df is None or len(df) < 50:
            return {}
        
        return TechnicalIndicators.calculate_indicators_from_klines(
            df.to_dict('records')
        )
    
    def check_trend_following_signal(self, indicators: Dict, price: float) -> Optional[str]:
        """
        检查趋势跟踪策略信号
        
        条件：
        1. MA20 > MA50 (均线金叉)
        2. RSI > 50
        3. MACD金叉 (DIF > DEA)
        
        Returns:
            "buy" | "sell" | None
        """
        try:
            # 检查是否有力指标
            required = ['sma_20', 'sma_50', 'rsi', 'macd_line', 'signal_line']
            for key in required:
                if key not in indicators:
                    return None
            
            sma20 = indicators['sma_20']
            sma50 = indicators['sma_50']
            rsi = indicators['rsi']
            macd_line = indicators['macd_line']
            signal_line = indicators['signal_line']
            
            # 买入条件
            if (sma20 > sma50 and 
                rsi > 50 and 
                macd_line > signal_line):
                logging.info(f"✅ 买入信号触发: SMA20={sma20:.2f} > SMA50={sma50:.2f}, RSI={rsi:.2f}, MACD={macd_line:.4f} > Signal={signal_line:.4f}")
                return "buy"
            
            # 卖出条件
            elif (sma20 < sma50 and 
                  rsi < 50 and 
                  macd_line < signal_line):
                logging.info(f"✅ 卖出信号触发: SMA20={sma20:.2f} < SMA50={sma50:.2f}, RSI={rsi:.2f}, MACD={macd_line:.4f} < Signal={signal_line:.4f}")
                return "sell"
            
            return None
            
        except Exception as e:
            logging.error(f"信号检查失败: {e}")
            return None
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> Optional[float]:
        """计算ATR"""
        try:
            if len(df) < period + 1:
                return None
            
            atr_series = TechnicalIndicators.calculate_atr(
                df['high'], df['low'], df['close'], period
            )
            return float(atr_series.iloc[-1]) if not pd.isna(atr_series.iloc[-1]) else None
        except Exception as e:
            logging.error(f"ATR计算失败: {e}")
            return None
    
    def calculate_position_size(self, entry_price: float, stop_loss_price: float) -> float:
        """
        计算仓位大小
        
        基于风险控制：单笔风险 = 总资金 * 2%
        """
        risk_amount = self.total_capital * self.max_risk_per_trade
        
        # 计算止损距离
        stop_distance = abs(entry_price - stop_loss_price)
        if stop_distance == 0:
            return 0
        
        # 计算仓位数量
        position_value = risk_amount / (stop_distance / entry_price)
        
        # 限制最大仓位
        max_position_value = self.total_capital * self.max_position_size
        position_value = min(position_value, max_position_value)
        
        return float(position_value)
    
    def calculate_stop_loss(self, entry_price: float, atr: float, side: str) -> float:
        """计算止损价格 (2倍ATR)"""
        if side == "buy":
            return entry_price - (atr * 2)
        else:
            return entry_price + (atr * 2)
    
    def calculate_take_profit(self, entry_price: float, atr: float, side: str) -> float:
        """计算止盈价格 (4倍ATR)"""
        if side == "buy":
            return entry_price + (atr * 4)
        else:
            return entry_price - (atr * 4)
    
    def place_order(self, symbol: str, side: str, size: float, price: float = None,
                   order_type: str = "limit", reduce_only: bool = False):
        """下单"""
        try:
            from hyperliquid.utils import signing

            if order_type == "limit":
                order_type_dict = {"limit": {"tif": "Gtc"}}
            elif order_type == "market":
                order_type_dict = {"limit": {"tif": "Ioc"}}
            else:
                logging.error(f"不支持的订单类型: {order_type}")
                return None

            is_buy = (side == "buy")

            order_response = self.exchange.order(
                name=symbol,
                is_buy=is_buy,
                sz=size,
                limit_px=price,
                order_type=order_type_dict,
                reduce_only=reduce_only
            )

            logging.info(f"📝 订单提交: {symbol} {side} {size} @ {price if price else 'market'}")
            return order_response

        except Exception as e:
            logging.error(f"下单失败: {e}")
            return None
    
    def check_open_positions(self):
        """检查当前持仓"""
        try:
            user_state = self.info.user_state(self.wallet_address)
            if user_state and 'positions' in user_state:
                self.positions = user_state['positions']
                return self.positions
            return []
        except Exception as e:
            logging.error(f"获取持仓失败: {e}")
            return []
    
    def run_strategy(self, symbol: str):
        """执行策略逻辑"""
        logging.info(f"🔍 检查 {symbol} 交易机会...")
        
        # 1. 获取K线数据
        df = self.get_klines(symbol)
        if df is None or len(df) < 50:
            logging.warning(f"数据不足，跳过 {symbol}")
            return
        
        # 2. 计算技术指标
        indicators = self.calculate_indicators(df)
        if not indicators:
            logging.warning(f"指标计算失败，跳过 {symbol}")
            return
        
        # 3. 检查信号
        signal = self.check_trend_following_signal(indicators, df['close'].iloc[-1])
        if signal is None:
            return
        
        # 4. 获取当前价格和ATR
        current_price = self.get_current_price(symbol)
        atr = self.calculate_atr(df)
        
        if current_price is None or atr is None:
            return
        
        # 5. 计算止损止盈
        stop_loss = self.calculate_stop_loss(current_price, atr, signal)
        take_profit = self.calculate_take_profit(current_price, atr, signal)
        
        # 6. 计算仓位大小
        position_size = self.calculate_position_size(current_price, stop_loss)
        if position_size <= 0:
            return
        
        # 7. 检查现有持仓
        existing_positions = self.check_open_positions()
        has_position = any(p.get('coin') == symbol.replace('USDT', '') for p in existing_positions)
        
        # 8. 执行交易
        if signal == "buy" and not has_position:
            logging.info(f"🚀 执行买入: {symbol}")
            logging.info(f"   价格: ${current_price:.2f}")
            logging.info(f"   仓位: ${position_size:.2f}")
            logging.info(f"   止损: ${stop_loss:.2f}")
            logging.info(f"   止盈: ${take_profit:.2f}")
            logging.info(f"   风险回报: 1:{(take_profit - current_price) / (current_price - stop_loss):.1f}")
            
            # 实际下单
            order = self.place_order(symbol, "buy", position_size, current_price, "limit")
            if order:
                self.log_trade(symbol, "buy", current_price, position_size, stop_loss, take_profit)
        
        elif signal == "sell" and has_position:
            logging.info(f"🔻 执行卖出: {symbol}")
            logging.info(f"   价格: ${current_price:.2f}")
            logging.info(f"   平仓全部仓位")
            
            # 平仓
            order = self.place_order(symbol, "sell", position_size, current_price, "limit", reduce_only=True)
            if order:
                self.log_trade(symbol, "sell", current_price, position_size, stop_loss, take_profit)
    
    def log_trade(self, symbol: str, side: str, price: float, size: float, 
                  stop_loss: float, take_profit: float):
        """记录交易"""
        trade = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'side': side,
            'price': price,
            'size': size,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_reward_ratio': (take_profit - price) / (price - stop_loss) if price != stop_loss else 0
        }
        self.trade_history.append(trade)
        
        # 保存到文件
        with open('/root/.openclaw/workspace/crypto/logs/trades.jsonl', 'a') as f:
            f.write(json.dumps(trade) + '\n')
        
        logging.info(f"📊 交易已记录")
    
    def run(self):
        """主循环"""
        logging.info("🚀 开始运行交易系统...")
        
        while True:
            try:
                for symbol in self.symbols:
                    self.run_strategy(symbol)
                
                # 每小时检查一次
                logging.info("⏳ 等待1小时后再次检查...")
                time.sleep(3600)
                
            except KeyboardInterrupt:
                logging.info("⏹️ 收到停止信号，退出...")
                break
            except Exception as e:
                logging.error(f"运行异常: {e}")
                time.sleep(300)  # 出错后等待5分钟再继续


def main():
    """主函数"""
    # ⚠️ 警告：永远不要在生产环境中硬编码私钥！
    # 这里需要你提供你的Agent钱包私钥
    
    # 测试模式：使用示例私钥（仅用于测试，实际需要替换！）
    # 在Hyperliquid测试网创建Agent后，替换成真实的私钥
    TEST_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"  # 示例，需要替换！
    
    # 检查是否为测试私钥
    if TEST_PRIVATE_KEY == "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80":
        logging.warning("⚠️  使用的是示例私钥！请替换为真实的Agent钱包私钥！")
    
    # 初始化机器人
    bot = HyperliquidTradingBot(
        private_key=TEST_PRIVATE_KEY,
        testnet=True  # 使用测试网
    )
    
    # 健康检查 - 使用all_mids接口测试
    try:
        all_mids = bot.info.all_mids()
        if all_mids:
            logging.info(f"✅ API连接正常: 获取中价数据成功")
        else:
            logging.warning("⚠️  获取中价数据失败")
    except Exception as e:
        logging.error(f"❌ API连接异常: {e}")
    
    # 开始运行
    bot.run()


if __name__ == "__main__":
    main()