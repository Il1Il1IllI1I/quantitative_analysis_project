import backtrader as bt
import quantstats as qs
import yfinance as yf
import pandas as pd
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)

class MovingAverageCrossStrategy(bt.Strategy):
    params = (
        ("fast_ma", 10),
        ("slow_ma", 50),
    )

    def __init__(self):
        self.fast_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.fast_ma)
        self.slow_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.slow_ma)

    def next(self):
        if self.fast_ma > self.slow_ma:
            self.buy()
        elif self.fast_ma < self.slow_ma:
            self.sell()

data_df = yf.download('AAPL', start='2020-01-01', end='2022-01-01')
data_df.to_csv('AAPL.csv')

data = bt.feeds.GenericCSVData(
    dataname='AAPL.csv',
    datetime=0,
    open=1,
    high=2,
    low=3,
    close=4,
    volume=6,
    openinterest=-1,
    dtformat=('%Y-%m-%d')
)

cerebro = bt.Cerebro()
cerebro.adddata(data)
cerebro.addstrategy(MovingAverageCrossStrategy)
cerebro.broker.set_cash(100000)
cerebro.broker.setcommission(commission=0.001)

# TimeReturn Analyzer 추가
cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='returns')

strategies = cerebro.run()
strategy = strategies[0]

# Analyzer로부터 수익률 데이터 얻기
returns = strategy.analyzers.getbyname('returns').get_analysis()
returns_df = pd.DataFrame(list(returns.items()), columns=['date', 'return']).set_index('date')

# QuantStats 라이브러리를 사용하여 수익률 데이터 분석
qs.extend_pandas()
qs.reports.html(returns_df['return'], "AAPL", output='backtest_result.html')
