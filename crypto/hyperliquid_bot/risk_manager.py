"""
风险管理模块 - 负责仓位管理、止损、风险评估
"""

from typing import Dict, List, Tuple
import numpy as np

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
        self.max_daily_loss = 0.05    # 日最大亏损5%
        self.max_drawdown = 0.15      # 最大回撤15%
    
    def calculate_position_size(self, symbol: str, price: float, stop_loss: float, 
                               risk_per_trade: float = None) -> float:
        """
        计算仓位大小
        
        Args:
            symbol: 交易对
            price: 当前价格
            stop_loss: 止损价
            risk_per_trade: 单笔风险比例
            
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
            current_risk: 当前已用风险
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
        position_size = self.calculate_position_size(symbol, entry_price, stop_loss)
        risk_amount = abs(entry_price - stop_loss) * position_size
        
        if risk_amount > self.total_capital * max_risk_per_trade:
            return False, f"风险金额超过限制: {risk_amount:.2f} > {self.total_capital * max_risk_per_trade:.2f}"
        
        # 检查最大仓位
        max_position = self.total_capital * self.max_position_size
        if position_size > max_position:
            return False, f"仓位超过最大限制: {position_size} > {max_position}"
        
        # 检查总风险
        total_risk_after = current_risk + risk_amount
        if total_risk_after > self.total_capital * max_risk_per_trade:
            return False, f"总风险超过限制: {total_risk_after:.2f} > {self.total_capital * max_risk_per_trade:.2f}"
        
        return True, "允许交易"
    
    def validate_stop_loss(self, entry_price: float, stop_loss: float, atr: float = None) -> Tuple[bool, str]:
        """
        验证止损合理性
        
        Args:
            entry_price: 入场价
            stop_loss: 止损价
            atr: ATR值（可选）
            
        Returns:
            (是否合理, 原因)
        """
        # 止损距离
        stop_distance = abs(entry_price - stop_loss)
        
        # 检查止损距离是否过大
        stop_percentage = stop_distance / entry_price
        if stop_percentage > 0.10:  # 止损超过10%
            return False, f"止损距离过大: {stop_percentage:.2%} > 10%"
        
        # 如果提供了ATR，检查是否符合ATR标准
        if atr:
            atr_multiple = stop_distance / atr
            if atr_multiple < 1.5:
                return False, f"ATR倍数太小: {atr_multiple:.2f}x"
            if atr_multiple > 3:
                return False, f"ATR倍数太大: {atr_multiple:.2f}x"
        
        return True, "止损合理"
    
    def get_position_size_by_risk(self, symbol: str, entry_price: float, stop_loss: float, 
                                 desired_risk: float) -> float:
        """
        根据期望风险计算仓位大小
        
        Args:
            symbol: 交易对
            entry_price: 入场价
            stop_loss: 止损价
            desired_risk: 期望风险（美元）
            
        Returns:
            仓位大小
        """
        stop_loss_distance = abs(entry_price - stop_loss)
        if stop_loss_distance <= 0:
            return 0
        
        return desired_risk / stop_loss_distance
    
    def calculate_dynamic_position(self, symbol: str, price: float, stop_loss: float, 
                                  account_balance: float, volatility: float = None) -> float:
        """
        动态计算仓位大小
        
        Args:
            symbol: 交易对
            price: 价格
            stop_loss: 止损价
            account_balance: 账户余额
            volatility: 波动率指标（可选，用于调整仓位）
            
        Returns:
            最优仓位大小
        """
        # 基础仓位
        base_position = self.calculate_position_size(symbol, price, stop_loss)
        
        # 如果有波动率信息，进行动态调整
        if volatility:
            # 波动率高时减小仓位
            if volatility > 0.05:  # 5%波动率
                base_position *= 0.8
            elif volatility < 0.02:  # 2%波动率
                base_position *= 1.2
        
        # 确保不超过账户余额
        max_affordable = account_balance * 0.95 / price
        return min(base_position, max_affordable)
    
    def get_risk_summary(self, trades: List[Dict]) -> Dict:
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
        total_trades = len(trades)
        
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
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        avg_risk_reward = total_reward / total_risk if total_risk > 0 else 0
        avg_win = total_reward / winning_trades if winning_trades > 0 else 0
        avg_loss = total_risk / losing_trades if losing_trades > 0 else 0
        
        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": round(win_rate, 4),
            "avg_risk_reward": round(avg_risk_reward, 4),
            "avg_win": round(avg_win, 4),
            "avg_loss": round(avg_loss, 4),
            "total_risk": round(total_risk, 4),
            "total_reward": round(total_reward, 4),
            "profit_factor": round(total_reward / total_risk, 4) if total_risk > 0 else 0
        }


# 测试代码
if __name__ == "__main__":
    print("风险管理测试")
    print("=" * 50)
    
    risk_manager = RiskManager(total_capital=10000, max_risk_per_trade=0.02)
    
    # 计算仓位大小
    entry_price = 50000
    stop_loss = 48000
    position = risk_manager.calculate_position_size("BTCUSDT", entry_price, stop_loss)
    print(f"仓位大小: {position:.2f}")
    print(f"风险金额: {abs(entry_price - stop_loss) * position:.2f}")
    
    # 计算风险回报比
    take_profit = 58000
    rr = risk_manager.calculate_risk_reward_ratio(entry_price, stop_loss, take_profit)
    print(f"风险回报比: {rr:.2f}")
    
    # 验证交易
    allowed, reason = risk_manager.is_trade_allowed("BTCUSDT", entry_price, stop_loss, 200)
    print(f"交易是否允许: {allowed} - {reason}")
    
    # 模拟交易记录
    trades = [
        {"entry_price": 50000, "stop_loss": 48000, "take_profit": 58000, "outcome": "win"},
        {"entry_price": 52000, "stop_loss": 50000, "take_profit": 60000, "outcome": "win"},
        {"entry_price": 51000, "stop_loss": 49000, "take_profit": 59000, "outcome": "loss"},
    ]
    
    summary = risk_manager.get_risk_summary(trades)
    print("\n风险报告:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\n✅ 风险管理测试完成")