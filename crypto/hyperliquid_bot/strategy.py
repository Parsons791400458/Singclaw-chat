"""
交易策略模块 - 实现各种交易策略
"""

import time
from typing import Dict, List, Tuple, Optional
from indicators import TechnicalIndicators
import numpy as np

class TradingStrategy:
    """交易策略基类"""
    
    def __init__(self, indicators: TechnicalIndicators):
        self.indicators = indicators
    
    def generate_signals(self, klines: List[Dict]) -> List[Dict]:
        """
        生成交易信号
        
        Args:
            klines: K线数据
            
        Returns:
            信号列表，每个信号包含:
            - symbol: 交易对
            - signal: "buy"/"sell"/None
            - price: 信号价格
            - stop_loss: 止损价
            - take_profit: 止盈价
            - confidence: 置信度
        """
        signals = []
        
        # 计算技术指标
        indicator_values = TechnicalIndicators.calculate_indicators_from_klines(klines)
        
        # 应用具体策略
        symbol = klines[-1].get('symbol', 'BTCUSDT') if klines else 'BTCUSDT'
        
        # 趋势跟踪策略
        trend_signal = self.trend_following_strategy(indicator_values)
        if trend_signal:
            signals.append(trend_signal)
        
        # 突破策略
        breakout_signal = self.breakout_strategy(indicator_values)
        if breakout_signal:
            signals.append(breakout_signal)
        
        # 均值回归策略
        mean_reversion_signal = self.mean_reversion_strategy(indicator_values)
        if mean_reversion_signal:
            signals.append(mean_reversion_signal)
        
        return signals
    
    def trend_following_strategy(self, indicators: Dict) -> Optional[Dict]:
        """
        趋势跟踪策略
        
        条件：
        - 均线金叉
        - RSI > 50
        - MACD金叉
        """
        # 检查条件
        if (TechnicalIndicators.check_golden_cross(
            indicators.get('sma_20'), indicators.get('sma_50'))
            and indicators.get('rsi', 0) > 50
            and indicators.get('macd_line', 0) > indicators.get('signal_line', 0)
        ):
            # 计算止损和止盈
            atr = indicators.get('atr', 2)
            current_price = indicators.get('close', 0)
            
            stop_loss = current_price - (atr * 2)
            take_profit = current_price + (atr * 4)
            
            return {
                "symbol": "BTCUSDT",
                "signal": "buy",
                "price": current_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "confidence": 0.7,
                "strategy": "trend_following",
                "timestamp": int(time.time())
            }
        return None
    
    def breakout_strategy(self, indicators: Dict) -> Optional[Dict]:
        """
        突破策略
        
        条件：
        - 价格突破布林带上轨
        - 成交量放大
        - RSI < 70（避免超买）
        """
        current_price = indicators.get('close', 0)
        bb_upper = indicators.get('bb_upper', 0)
        volume = indicators.get('volume', 0)
        rsi = indicators.get('rsi', 0)
        
        if (current_price > bb_upper * 1.01  # 突破上轨1%
            and volume > indicators.get('volume', 0) * 1.5  # 成交量放大1.5倍
            and rsi < 70
        ):
            # 计算止损和止盈
            atr = indicators.get('atr', 2)
            stop_loss = current_price - (atr * 2)
            take_profit = current_price + (atr * 3)
            
            return {
                "symbol": "BTCUSDT",
                "signal": "buy",
                "price": current_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "confidence": 0.6,
                "strategy": "breakout",
                "timestamp": int(time.time())
            }
        return None
    
    def mean_reversion_strategy(self, indicators: Dict) -> Optional[Dict]:
        """
        均值回归策略
        
        条件：
        - 价格触及布林带下轨
        - RSI < 30
        - KDJ超卖
        """
        current_price = indicators.get('close', 0)
        bb_lower = indicators.get('bb_lower', 0)
        rsi = indicators.get('rsi', 0)
        k_line = indicators.get('k_line', 0)
        
        if (current_price < bb_lower * 0.99  # 触及下轨
            and rsi < 30
            and k_line < 20
        ):
            # 计算止损和止盈
            atr = indicators.get('atr', 2)
            stop_loss = current_price + (atr * 2)
            take_profit = current_price + (atr * 3)
            
            return {
                "symbol": "BTCUSDT",
                "signal": "buy",
                "price": current_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "confidence": 0.65,
                "strategy": "mean_reversion",
                "timestamp": int(time.time())
            }
        return None
    
    def get_strategy_name(self) -> str:
        """获取当前策略名称"""
        return "综合策略"


class MultiStrategy(TradingStrategy):
    """多策略组合"""
    
    def __init__(self, indicators: TechnicalIndicators):
        super().__init__(indicators)
        self.strategies = [
            self.trend_following_strategy,
            self.breakout_strategy,
            self.mean_reversion_strategy
        ]
    
    def generate_signals(self, klines: List[Dict]) -> List[Dict]:
        """
        生成多策略信号
        
        使用投票机制：
        - 如果多个策略都给出相同信号，置信度提高
        - 如果策略冲突，选择置信度最高的
        """
        signals = []
        symbol = klines[-1].get('symbol', 'BTCUSDT') if klines else 'BTCUSDT'
        
        # 收集所有策略信号
        strategy_signals = []
        for strategy_func in self.strategies:
            signal = strategy_func(TechnicalIndicators.calculate_indicators_from_klines(klines))
            if signal:
                strategy_signals.append(signal)
        
        # 如果没有信号
        if not strategy_signals:
            return []
        
        # 投票机制：相同信号合并
        signal_dict = {}
        for signal in strategy_signals:
            key = (signal['signal'], signal['price'])
            if key not in signal_dict:
                signal_dict[key] = []
            signal_dict[key].append(signal)
        
        # 选择最佳信号
        best_signal = None
        for key, signals in signal_dict.items():
            # 计算平均置信度
            avg_confidence = np.mean([s['confidence'] for s in signals])
            # 计算投票数
            vote_count = len(signals)
            
            # 选择置信度最高且投票数最多的信号
            if (not best_signal or 
                avg_confidence > best_signal['confidence'] or
                (avg_confidence == best_signal['confidence'] and vote_count > best_signal.get('vote_count', 0))):
                best_signal = signals[0].copy()  # 使用第一个信号作为基础
                best_signal['confidence'] = avg_confidence
                best_signal['vote_count'] = vote_count
                best_signal['strategies'] = [s['strategy'] for s in signals]
        
        # 添加时间戳和symbol
        if best_signal:
            best_signal['symbol'] = symbol
            best_signal['timestamp'] = int(time.time())
            signals.append(best_signal)
        
        return signals
    
    def get_strategy_name(self) -> str:
        return "多策略组合"


class RiskManager:
    """风险管理模块"""
    
    def __init__(self, total_capital: float = 10000, max_risk_per_trade: float = 0.02):
        """
        初始化风险管理
        
        Args:
            total_capital: 总资金
            max_risk_per_trade: 单笔最大风险比例（默认2%）
        """
        self.total_capital = total_capital
        self.max_risk_per_trade = max_risk_per_trade
        self.max_position_size = 0.1  # 最大仓位10%
    
    def calculate_position_size(self, symbol: str, price: float, stop_loss: float, 
                               risk_per_trade: float = None) -> float:
        """
        计算仓位大小
        
        Args:
            symbol: 交易对
            price: 当前价格
            stop_loss: 止损价
            risk_per_trade: 单笔风险比例（默认使用配置值）
            
        Returns:
            仓位大小（数量）
        """
        if risk_per_trade is None:
            risk_per_trade = self.max_risk_per_trade
        
        # 计算风险金额
        risk_amount = self.total_capital * risk_per_trade
        
        # 计算止损距离
        stop_loss_distance = abs(price - stop_loss)
        
        if stop_loss_distance <= 0:
            return 0
        
        # 计算仓位大小
        position_size = risk_amount / stop_loss_distance
        
        # 限制最大仓位
        max_position = self.total_capital * self.max_position_size
        position_size = min(position_size, max_position)
        
        # 限制最小仓位（防止过小订单）
        min_position = max_position * 0.01  # 最小仓位的1%
        position_size = max(position_size, min_position)
        
        return position_size
    
    def calculate_risk_reward_ratio(self, entry_price: float, stop_loss: float, take_profit: float) -> float:
        """
        计算风险回报比
        
        Args:
            entry_price: 入场价
            stop_loss: 止损价
            take_profit: 止盈价
            
        Returns:
            风险回报比（>1为好）
        """
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        
        if risk <= 0:
            return float('inf')
        
        return reward / risk
    
    def is_trade_allowed(self, symbol: str, entry_price: float, stop_loss: float, 
                        current_risk: float, max_risk_per_trade: float = None) -> Tuple[bool, str]:
        """
        检查交易是否允许
        
        Args:
            symbol: 交易对
            entry_price: 入场价
            stop_loss: 止损价
            current_risk: 当前风险金额
            max_risk_per_trade: 最大允许风险
            
        Returns:
            (是否允许, 原因)
        """
        if max_risk_per_trade is None:
            max_risk_per_trade = self.max_risk_per_trade
        
        # 检查止损距离
        if abs(entry_price - stop_loss) <= 0:
            return False, "止损距离为零"
        
        # 检查风险金额
        risk_amount = abs(entry_price - stop_loss) * self.calculate_position_size(symbol, entry_price, stop_loss)
        if risk_amount > self.total_capital * max_risk_per_trade:
            return False, f"风险金额超过限制: {risk_amount:.2f} > {self.total_capital * max_risk_per_trade:.2f}"
        
        # 检查最大仓位
        position_size = self.calculate_position_size(symbol, entry_price, stop_loss)
        if position_size > self.total_capital * self.max_position_size:
            return False, f"仓位超过最大限制: {position_size} > {self.total_capital * self.max_position_size}"
        
        return True, "允许交易"
    
    def get_risk_report(self, trades: List[Dict]) -> Dict:
        """
        生成风险报告
        
        Args:
            trades: 交易记录列表
            
        Returns:
            风险报告
        """
        if not trades:
            return {}
        
        total_risk = 0
        total_reward = 0
        winning_trades = 0
        losing_trades = 0
        
        for trade in trades:
            entry_price = trade.get('entry_price', 0)
            stop_loss = trade.get('stop_loss', 0)
            take_profit = trade.get('take_profit', 0)
            outcome = trade.get('outcome', 'unknown')
            
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            
            total_risk += risk
            
            if outcome == 'win':
                total_reward += reward
                winning_trades += 1
            elif outcome == 'loss':
                losing_trades += 1
        
        total_trades = len(trades)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        avg_risk_reward = total_reward / total_risk if total_risk > 0 else 0
        
        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "avg_risk_reward": avg_risk_reward,
            "total_risk": total_risk,
            "total_reward": total_reward
        }


# 测试代码
if __name__ == "__main__":
    print("交易策略测试")
    print("=" * 50)
    
    # 创建策略实例
    indicators = TechnicalIndicators(None)  # 实际使用中需要传入K线数据
    strategy = MultiStrategy(indicators)
    
    # 生成测试K线数据
    np.random.seed(42)
    n = 100
    klines = []
    for i in range(n):
        kline = {
            "symbol": "BTCUSDT",
            "open": 100 + i * 0.1 + np.random.randn(),
            "high": 100 + i * 0.1 + np.random.randn() * 2,
            "low": 100 + i * 0.1 - np.random.randn() * 2,
            "close": 100 + i * 0.1 + np.random.randn(),
            "volume": 1000 + np.random.randn() * 100,
            "timestamp": int(time.time()) - (n - i) * 60
        }
        klines.append(kline)
    
    # 生成信号
    signals = strategy.generate_signals(klines)
    print(f"生成了 {len(signals)} 个交易信号")
    
    for signal in signals:
        print(f"信号: {signal['signal'].upper()} {signal['symbol']}")
        print(f"价格: ${signal['price']:.2f}")
        print(f"止损: ${signal['stop_loss']:.2f}")
        print(f"止盈: ${signal['take_profit']:.2f}")
        print(f"置信度: {signal['confidence']:.2f}")
        print(f"策略: {signal['strategy']}")
        print("-" * 30)
    
    # 风险管理测试
    risk_manager = RiskManager(total_capital=10000)
    position_size = risk_manager.calculate_position_size("BTCUSDT", 50000, 48000)
    print(f"仓位大小: {position_size:.2f}")
    
    risk_reward = risk_manager.calculate_risk_reward_ratio(50000, 48000, 58000)
    print(f"风险回报比: {risk_reward:.2f}")
    
    print("\n✅ 策略测试完成")