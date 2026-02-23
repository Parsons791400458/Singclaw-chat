"""
Hyperliquid自动化交易机器人 - 主程序
完全自动化执行交易策略
"""

import time
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
import signal
import sys

from hyperliquid_api import HyperliquidAPI
from strategy import TradingStrategy, RiskManager
import pandas as pd

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/.openclaw/workspace/crypto/hyperliquid_bot/trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HyperliquidBot:
    """
    Hyperliquid自动化交易机器人
    
    功能：
    1. 自动获取市场数据
    2. 应用策略生成交易信号
    3. 自动计算仓位和风险管理
    4. 自动执行订单
    5. 自动记录交易日志
    """
    
    def __init__(self, config: Dict):
        """
        初始化交易机器人
        
        Args:
            config: 配置字典，包含：
                - api_key: Hyperliquid API密钥
                - api_secret: Hyperliquid API密钥
                - testnet: 是否使用测试网
                - symbols: 要监控的交易对列表
                - capital: 初始资金
                - strategy_name: 策略名称
        """
        self.config = config
        
        # 初始化API
        api_key = config.get('api_key', '')
        api_secret = config.get('api_secret', '')
        testnet = config.get('testnet', True)
        
        self.api = HyperliquidAPI(api_key, api_secret, testnet=testnet)
        
        # 初始化策略和风险管理
        indicators = None  # 注意：实际使用时需要正确初始化
        self.strategy = TradingStrategy(indicators)
        self.risk_manager = RiskManager(
            total_capital=config.get('capital', 10000),
            max_risk_per_trade=config.get('max_risk_per_trade', 0.02)
        )
        
        # 交易状态
        self.trades = []  # 历史交易记录
        self.current_positions = {}  # 当前持仓
        self.pending_orders = {}  # 挂单
        
        # 配置参数
        self.symbols = config.get('symbols', ['BTCUSDT', 'ETHUSDT'])
        self.check_interval = config.get('check_interval', 60)  # 检查间隔（秒）
        self.min_confidence = config.get('min_confidence', 0.6)  # 最小置信度
        
        # 运行状态
        self.running = False
        self.stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0,
            'start_time': datetime.now()
        }
    
    def start(self):
        """启动交易机器人"""
        logger.info("🚀 启动Hyperliquid自动化交易机器人")
        logger.info(f"配置: {self.config}")
        
        # 检查API连接
        if not self.api.health_check():
            logger.error("❌ API连接失败，请检查配置")
            return False
        
        logger.info("✅ API连接正常")
        
        # 查询账户信息
        account_info = self.api.get_account_info()
        if account_info:
            logger.info(f"账户余额: {account_info.get('balance', 'N/A')}")
        else:
            logger.warning("⚠️ 无法获取账户信息")
        
        # 查询当前持仓
        positions = self.api.get_positions()
        if positions:
            for pos in positions:
                self.current_positions[pos['symbol']] = pos
            logger.info(f"当前持仓: {len(positions)} 个")
        
        self.running = True
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info("🎯 开始监控市场...")
        
        try:
            while self.running:
                self.main_loop()
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("收到停止信号")
        except Exception as e:
            logger.error(f"运行时异常: {e}")
        finally:
            self.shutdown()
        
        return True
    
    def main_loop(self):
        """主循环"""
        try:
            for symbol in self.symbols:
                logger.debug(f"监控 {symbol}...")
                
                # 1. 获取K线数据
                klines = self.api.get_klines(symbol, interval="1h", limit=100)
                if not klines:
                    logger.warning(f"无法获取 {symbol} 的K线数据")
                    continue
                
                # 2. 生成交易信号
                signals = self.strategy.generate_signals(klines)
                
                # 3. 过滤信号
                valid_signals = []
                for signal in signals:
                    if signal['confidence'] >= self.min_confidence:
                        # 检查持仓限制
                        if not self.check_position_limit(symbol):
                            logger.warning(f"{symbol} 已达持仓限制，跳过信号")
                            continue
                        
                        # 计算仓位
                        position_size = self.risk_manager.calculate_position_size(
                            symbol, 
                            signal['price'], 
                            signal['stop_loss']
                        )
                        
                        if position_size <= 0:
                            logger.warning(f"{symbol} 仓位计算为零，跳过")
                            continue
                        
                        signal['position_size'] = position_size
                        valid_signals.append(signal)
                
                # 4. 执行交易
                for signal in valid_signals:
                    self.execute_signal(signal)
                
                # 5. 检查持仓并平仓（止损/止盈）
                self.check_positions_for_exit(symbol)
                
        except Exception as e:
            logger.error(f"主循环异常: {e}", exc_info=True)
    
    def check_position_limit(self, symbol: str) -> bool:
        """检查持仓限制"""
        if symbol in self.current_positions:
            # 已经有持仓，检查是否已满
            # 可根据需要实现更多限制逻辑
            return False
        return True
    
    def execute_signal(self, signal: Dict):
        """执行交易信号"""
        symbol = signal['symbol']
        side = signal['signal']
        price = signal['price']
        position_size = signal['position_size']
        stop_loss = signal['stop_loss']
        take_profit = signal['take_profit']
        confidence = signal['confidence']
        
        logger.info(f"📊 执行信号: {symbol} {side.upper()}")
        logger.info(f"   价格: ${price:.2f}")
        logger.info(f"   仓位: {position_size:.4f}")
        logger.info(f"   止损: ${stop_loss:.2f}")
        logger.info(f"   止盈: ${take_profit:.2f}")
        logger.info(f"   置信度: {confidence:.2f}")
        
        # 风险检查
        allowed, reason = self.risk_manager.is_trade_allowed(
            symbol, price, stop_loss, 0
        )
        if not allowed:
            logger.warning(f"⚠️ 交易被风控拒绝: {reason}")
            return
        
        # 执行下单
        order = self.api.place_order(symbol, side, position_size, price)
        if order:
            logger.info(f"✅ 订单已提交: {order}")
            
            # 记录交易
            trade_record = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'side': side,
                'entry_price': price,
                'position_size': position_size,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'confidence': confidence,
                'strategy': signal.get('strategy', 'unknown'),
                'order_id': order.get('order_id'),
                'status': 'pending'
            }
            
            self.trades.append(trade_record)
            self.current_positions[symbol] = trade_record
            self.stats['total_trades'] += 1
            
            # 保存交易日志
            self.save_trade_log(trade_record)
        else:
            logger.error(f"❌ 下单失败: {signal}")
    
    def check_positions_for_exit(self, symbol: str):
        """检查持仓是否需要平仓"""
        if symbol not in self.current_positions:
            return
        
        position = self.current_positions[symbol]
        
        # 获取当前价格
        current_price = self.api.get_price(symbol)
        if current_price is None:
            return
        
        # 检查止损
        stop_loss = position['stop_loss']
        take_profit = position['take_profit']
        side = position['side']
        
        exit_reason = None
        
        if side == 'buy':
            # 多头持仓
            if current_price <= stop_loss:
                exit_reason = "stop_loss"
            elif current_price >= take_profit:
                exit_reason = "take_profit"
        else:
            # 空头持仓（暂未实现）
            pass
        
        if exit_reason:
            logger.info(f"🎯 触发平仓: {symbol} - {exit_reason}")
            logger.info(f"   当前价格: ${current_price:.2f}")
            
            # 执行平仓
            exit_side = "sell" if side == "buy" else "buy"
            exit_order = self.api.place_order(
                symbol, 
                exit_side, 
                position['position_size'],
                current_price
            )
            
            if exit_order:
                logger.info(f"✅ 平仓成功")
                
                # 更新交易记录
                position['exit_price'] = current_price
                position['exit_time'] = datetime.now().isoformat()
                position['exit_reason'] = exit_reason
                position['status'] = 'closed'
                
                # 计算盈亏
                pnl = 0
                if side == 'buy':
                    pnl = (current_price - position['entry_price']) * position['position_size']
                position['pnl'] = pnl
                
                # 更新统计
                self.stats['total_pnl'] += pnl
                if pnl > 0:
                    self.stats['winning_trades'] += 1
                else:
                    self.stats['losing_trades'] += 1
                
                # 从持仓移除
                del self.current_positions[symbol]
                
                # 保存更新日志
                self.save_trade_log(position)
    
    def signal_handler(self, signum, frame):
        """信号处理"""
        logger.info("收到停止信号，正在安全退出...")
        self.running = False
    
    def shutdown(self):
        """安全关闭"""
        logger.info("正在关闭交易机器人...")
        
        # 保存最新状态
        self.save_stats()
        
        # 检查未平仓持仓
        if self.current_positions:
            logger.warning(f"还有 {len(self.current_positions)} 个持仓未平仓")
            for symbol, pos in self.current_positions.items():
                logger.warning(f"  {symbol}: {pos['position_size']}")
        
        logger.info("交易机器人已关闭")
    
    def save_trade_log(self, trade: Dict):
        """保存交易日志"""
        try:
            log_file = '/root/.openclaw/workspace/crypto/hyperliquid_bot/trades.jsonl'
            with open(log_file, 'a') as f:
                f.write(json.dumps(trade) + '\n')
        except Exception as e:
            logger.error(f"保存交易日志失败: {e}")
    
    def save_stats(self):
        """保存统计数据"""
        stats = {
            'timestamp': datetime.now().isoformat(),
            'stats': self.stats,
            'config': self.config
        }
        try:
            with open('/root/.openclaw/workspace/crypto/hyperliquid_bot/stats.json', 'w') as f:
                json.dump(stats, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"保存统计数据失败: {e}")
    
    def get_stats_report(self) -> str:
        """获取统计报告"""
        uptime = datetime.now() - self.stats['start_time']
        win_rate = (self.stats['winning_trades'] / self.stats['total_trades'] 
                   if self.stats['total_trades'] > 0 else 0)
        
        report = f"""
        ====================
        Hyperliquid交易机器人统计报告
        ====================
        运行时间: {uptime}
        总交易数: {self.stats['total_trades']}
        获利交易: {self.stats['winning_trades']}
        亏损交易: {self.stats['losing_trades']}
        胜率: {win_rate:.2%}
        总盈亏: ${self.stats['total_pnl']:.2f}
        当前持仓: {len(self.current_positions)} 个
        """
        return report


def load_config() -> Dict:
    """加载配置"""
    # TODO: 从配置文件加载
    config = {
        "api_key": "",  # 需要填写
        "api_secret": "",  # 需要填写
        "testnet": True,
        "symbols": ["BTCUSDT", "ETHUSDT"],
        "capital": 10000,
        "max_risk_per_trade": 0.02,
        "check_interval": 60
    }
    return config


def main():
    """主函数"""
    print("""
    ╔═══════════════════════════════════════╗
    ║  Hyperliquid自动化交易机器人        ║
    ║  版本: 1.0.0                         ║
    ║  策略: 综合交易策略                  ║
    ╚═══════════════════════════════════════╝
    """)
    
    # 加载配置
    config = load_config()
    
    # 创建机器人
    bot = HyperliquidBot(config)
    
    try:
        # 启动机器人
        bot.start()
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        logger.error(f"启动失败: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())