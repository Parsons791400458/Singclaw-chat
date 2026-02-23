import backtrader as bt
import pandas as pd
import datetime
import os

def run_backtest(symbol, data_file, sma_fast=20, sma_slow=50):
    """
    Run a simple moving average crossover strategy backtest
    """
    
    # Create a cerebro entity
    cerebro = bt.Cerebro()
    
    # Add a strategy
    class SmaCrossStrategy(bt.Strategy):
        params = (
            ('sma_fast', sma_fast),
            ('sma_slow', sma_slow),
        )
        
        def __init__(self):
            self.data_close = self.datas[0].close
            self.sma_fast = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.sma_fast)
            self.sma_slow = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.sma_slow)
            self.crossover = bt.indicators.CrossOver(self.sma_fast, self.sma_slow)
            self.order = None
            self.buy_price = None
            self.buy_comm = None
            
        def log(self, txt, dt=None):
            dt = dt or self.datas[0].datetime.date(0)
            print(f'[33m{dt.isoformat()}[0m {txt}')
            
        def notify_order(self, order):
            if order.status in [order.Submitted, order.Accepted]:
                return
                
            if order.status in [order.Completed]:
                if order.isbuy():
                    self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
                    self.buy_price = order.executed.price
                    self.buy_comm = order.executed.comm
                else:
                    self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
                    gross_pnl = order.executed.price - self.buy_price
                    net_pnl = gross_pnl - self.buy_comm
                    self.log(f'PnL: Gross {gross_pnl:.2f}, Net {net_pnl:.2f}')
                    
            elif order.status in [order.Canceled, order.Margin, order.Rejected]:
                self.log('Order Canceled/Margin/Rejected')
                
            self.order = None
            
        def notify_trade(self, trade):
            if not trade.isclosed:
                return
                
            self.log(f'TRADE CLOSED - Gross: {trade.pnl:.2f}, Net: {trade.pnlcomm:.2f}')
            
        def next(self):
            if self.order:
                return
                
            if not self.position:
                if self.crossover > 0:
                    size = int(self.broker.getcash() / self.data_close[0])
                    self.log(f'[32mBUY CREATED, Size: {size}, Price: {self.data_close[0]:.2f}[0m')
                    self.order = self.buy(size=size)
            else:
                if self.crossover < 0:
                    self.log(f'[31mSELL CREATED, Size: {self.position.size}, Price: {self.data_close[0]:.2f}[0m')
                    self.order = self.sell(size=self.position.size)
    
    # Read CSV data
    df = pd.read_csv(data_file)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    # Create a Data Feed
    data = bt.feeds.PandasData(dataname=df)
    
    # Add the Data Feed to Cerebro
    cerebro.adddata(data)
    
    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.PercentSizer, percents=95)
    
    # Set initial cash
    initial_cash = 100000
    cerebro.broker.setcash(initial_cash)
    
    # Set commission
    cerebro.broker.setcommission(commission=0.001)  # 0.1% commission
    
    # Print out the starting conditions
    print('[34m' + '='*60 + '[0m')
    print(f'[34mStarting Backtest for {symbol}[0m')
    print(f'[34mInitial Portfolio Value: ${cerebro.broker.getvalue():.2f}[0m')
    print(f'[34mFast SMA: {sma_fast} periods, Slow SMA: {sma_slow} periods[0m')
    print('[34m' + '='*60 + '[0m')
    
    # Run over everything
    cerebro.run()
    
    # Print out the final result
    final_value = cerebro.broker.getvalue()
    pnl = final_value - initial_cash
    pnl_percentage = (pnl / initial_cash) * 100
    
    print('[34m' + '='*60 + '[0m')
    print(f'[34mFinal Portfolio Value: ${final_value:.2f}[0m')
    print(f'[34mPnL: ${pnl:.2f} ({pnl_percentage:.2f}%)[0m')
    print('[34m' + '='*60 + '[0m')
    
    # Add trade analyzer
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    
    # Run over everything
    strat = cerebro.run()[0]
    
    # Get analyzer results
    trades_analyzer = strat.analyzers.trades
    trade_count = trades_analyzer.get_analysis().get('total', {}).get('closed', 0)
    
    # Print out the final result
    final_value = cerebro.broker.getvalue()
    pnl = final_value - initial_cash
    pnl_percentage = (pnl / initial_cash) * 100
    
    print('[34m' + '='*60 + '[0m')
    print(f'[34mFinal Portfolio Value: ${final_value:.2f}[0m')
    print(f'[34mPnL: ${pnl:.2f} ({pnl_percentage:.2f}%)[0m')
    print(f'[34mTotal Trades: {trade_count}[0m')
    print('[34m' + '='*60 + '[0m')
    
    return {
        'symbol': symbol,
        'initial_cash': initial_cash,
        'final_value': final_value,
        'pnl': pnl,
        'pnl_percentage': pnl_percentage,
        'trades': trade_count,
        'sma_fast': sma_fast,
        'sma_slow': sma_slow
    }

if __name__ == "__main__":
    # Test with BTC data
    btc_data_file = '/root/.openclaw/workspace/crypto/data/BTC_historical_data.csv'
    
    print('[36mStarting BTC MA Crossover Backtest...[0m')
    results = run_backtest('BTC', btc_data_file, sma_fast=20, sma_slow=50)
    
    # Save results to file
    import json
    results_file = f'/root/.openclaw/workspace/crypto/backtest/btc_ma_backtest_results.json'
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f'[32mResults saved to: {results_file}[0m')
    print('[32mBacktest completed successfully![0m')
    print('[36mNext steps: Analyze results and optimize parameters.[0m')