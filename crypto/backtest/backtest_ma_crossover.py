#!/usr/bin/env python3
"""
Backtrader MA Crossover backtest for BTC data - with proper position sizing
"""

import backtrader as bt
import pandas as pd
import os

# --- Configuration ---
DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'BTC_historical_data.csv')
OUTPUT_RESULTS = os.path.join(os.path.dirname(__file__), 'backtest_results.txt')
DEBUG_BUY_ON_DAY = 100  # Force buy on day 100 to verify pipeline works

# --- Strategy Definition ---
class MACrossover(bt.Strategy):
    params = (
        ('fast', 20),
        ('slow', 50),
        ('position_size', 0.1),  # Use 10% of portfolio per trade
    )

    def __init__(self):
        # Moving averages
        self.sma_fast = bt.ind.SMA(self.data.close, period=self.params.fast)
        self.sma_slow = bt.ind.SMA(self.data.close, period=self.params.slow)
        self.order = None
        
        # Track trades for analysis
        self.trade_count = 0
        self.total_pnl = 0.0

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                action = 'BUY'
            else:
                action = 'SELL'
            print(f'Order {action} executed: Price={order.executed.price:.2f}, Size={order.executed.size:.4f}, Cost={order.executed.value:.2f}, Comm={order.executed.comm:.2f}')
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            print(f'Order {order.getstatusname()} - Reason: Insufficient funds or other issue')

    def notify_trade(self, trade):
        if trade.isclosed:
            self.trade_count += 1
            self.total_pnl += trade.pnl
            print(f'Trade #{self.trade_count} Closed - PnL: {trade.pnl:.2f}, Net PnL: {self.total_pnl:.2f}')

    def next(self):
        # Debug: Force buy on specific day to verify pipeline works
        if len(self) == DEBUG_BUY_ON_DAY and not self.position:
            # Calculate position size based on available cash
            available_cash = self.broker.getcash()
            position_value = available_cash * self.params.position_size
            size = position_value / self.data.close[0]
            
            self.buy(size=size)
            print(f'[DEBUG] Forced BUY at day {len(self)}, price: {self.data.close[0]:.2f}, size: {size:.4f}')
            return

        # Normal strategy: Golden cross
        if (self.sma_fast[0] > self.sma_slow[0]) and not self.position:
            # Calculate position size based on available cash
            available_cash = self.broker.getcash()
            position_value = available_cash * self.params.position_size
            size = position_value / self.data.close[0]
            
            print(f'[SIGNAL] Golden cross BUY at day {len(self)}, price: {self.data.close[0]:.2f}, size: {size:.4f}')
            self.buy(size=size)
        # Death cross
        elif (self.sma_fast[0] < self.sma_slow[0]) and self.position:
            print(f'[SIGNAL] Death cross SELL at day {len(self)}, price: {self.data.close[0]:.2f}')
            self.sell()

# --- Main Execution ---
def run_backtest():
    # Load data
    print(f'Loading data from: {DATA_PATH}')
    df = pd.read_csv(DATA_PATH, parse_dates=['date'])
    df.set_index('date', inplace=True)
    print(f'Data loaded: {len(df)} rows, date range: {df.index[0]} to {df.index[-1]}')

    # Check SMA values at start
    print(f"\nFirst 60 days SMA status:")
    print(f"{'Day':<6} {'Close':<12} {'SMA20':<12} {'SMA50':<12}")
    for i in range(min(60, len(df))):
        row = df.iloc[i]
        sma20 = row.get('sma_20', 'N/A')
        sma50 = row.get('sma_50', 'N/A')
        print(f"{i+1:<6} {row['close']:<12.2f} {sma20 if pd.isna(sma20) else f'{sma20:.2f}':<12} {sma50 if pd.isna(sma50) else f'{sma50:.2f}':<12}")

    # Create Backtrader data feed
    data_feed = bt.feeds.PandasData(dataname=df)

    # Initialize Cerebro engine
    cerebro = bt.Cerebro()
    cerebro.adddata(data_feed)
    cerebro.addstrategy(MACrossover)

    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analyzer')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')

    # Set initial cash
    cerebro.broker.setcash(10000.0)
    cerebro.broker.setcommission(commission=0.001)  # 0.1% fee

    # Print initial stats
    print('\n=== BACKTEST SETUP ===')
    print(f'Initial Cash: {cerebro.broker.getvalue():.2f}')
    print(f'Position Size: 10% of portfolio per trade')
    print(f'Commission: 0.1%')

    # Run the backtest
    print('\n=== RUNNING BACKTEST ===')
    results = cerebro.run()
    strat = results[0]
    final_value = cerebro.broker.getvalue()
    
    # Get analyzer results
    trade_analyzer = strat.analyzers.trade_analyzer.get_analysis()
    returns_analyzer = strat.analyzers.returns.get_analysis()
    sharpe_analyzer = strat.analyzers.sharpe.get_analysis()
    drawdown_analyzer = strat.analyzers.drawdown.get_analysis()

    # Calculate performance metrics
    total_return = (final_value - cerebro.broker.getcash()) / cerebro.broker.getcash() * 100
    max_drawdown = drawdown_analyzer.get('max', {}).get('drawdown', 0)

    # Save results to file
    with open(OUTPUT_RESULTS, 'w') as f:
        f.write('=== BACKTEST RESULTS ===\n')
        f.write(f'Initial Cash: {cerebro.broker.getvalue():.2f}\n')
        f.write(f'Final Cash: {final_value:.2f}\n')
        f.write(f'Total Return: {total_return:.2f}%\n')
        f.write(f'Sharpe Ratio: {sharpe_analyzer.get("sharperatio", "N/A")}\n')
        f.write(f'Max Drawdown: {max_drawdown:.2f}%\n')
        f.write(f'Total Trades: {trade_analyzer.get("total", {}).get("total", 0)}\n')
        f.write(f'Total PnL: {trade_analyzer.get("pnl", {}).get("net", {}).get("total", 0):.2f}\n')
        
        # Detailed trade information
        trades = trade_analyzer.get('trades', [])
        if trades:
            f.write('\n=== DETAILED TRADES ===\n')
            for i, trade in enumerate(trades):
                f.write(f'Trade {i+1}: Entry={trade["entry"]["price"]:.2f}, Exit={trade["exit"]["price"]:.2f}, PnL={trade["pnl"]:.2f}\n')
        
        # Performance summary
        f.write('\n=== PERFORMANCE SUMMARY ===\n')
        f.write(f'Win Rate: {trade_analyzer.get("won", {}).get("total", 0)}/{trade_analyzer.get("total", {}).get("total", 0)}\n')
        f.write(f'Avg Win: {trade_analyzer.get("won", {}).get("pnl", {}).get("average", 0):.2f}\n')
        f.write(f'Avg Loss: {trade_analyzer.get("lost", {}).get("pnl", {}).get("average", 0):.2f}\n')

    print(f'\nBacktest results saved to {OUTPUT_RESULTS}')
    
    # Print summary
    print('\n=== SUMMARY ===')
    print(f'Initial Cash: {cerebro.broker.getvalue():.2f}')
    print(f'Final Cash: {final_value:.2f}')
    print(f'Total Return: {total_return:.2f}%')
    print(f'Total Trades: {trade_analyzer.get("total", {}).get("total", 0)}')
    print(f'Total PnL: {trade_analyzer.get("pnl", {}).get("net", {}).get("total", 0):.2f}')
    print(f'Max Drawdown: {max_drawdown:.2f}%')
    print(f'Sharpe Ratio: {sharpe_analyzer.get("sharperatio", "N/A")}')

if __name__ == '__main__':
    run_backtest()