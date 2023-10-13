import backtrader as bt
import pandas as pd
import quantstats as qs
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)

# 전략 정의
class MACDStrategy(bt.Strategy):
    params = (
        ("macd1", 12),
        ("macd2", 26),
        ("macdsig", 9),
        ("order_pct", 0.95),
        ("log_file", "macd_strategy.csv")
    )
    
    def __init__(self):
        self.macd = bt.indicators.MACD(self.data.close,
                                       period_me1=self.params.macd1,
                                       period_me2=self.params.macd2,
                                       period_signal=self.params.macdsig)
        self.crossover = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)
        self.log_file = open(self.params.log_file, 'w')
        self.log_file.write("Date,Value\n")
        
    def stop(self):
        self.log_file.close()
        
    def next(self):
        # 적절한 주문 크기 계산
        size = (self.broker.get_cash() * self.params.order_pct) // self.data.close[0]

        # 거래 로직
        if self.crossover > 0:
            self.buy(size=size)
        elif self.crossover < 0:
            self.close()
        
        # 로깅
        self.log_file.write(f"{self.data.datetime.date(0)},{self.broker.getvalue()}\n")


# 백테스팅 엔진 설정
cerebro = bt.Cerebro()
cerebro.broker.set_cash(100000)  # 초기 자본 설정
cerebro.broker.set_slippage_perc(0.001)  # 슬리피지 설정
cerebro.broker.setcommission(commission=0.001)  # 수수료 설정

# 데이터 추가
# (데이터 경로와 형식이 올바른지 확인하세요!)
datafeed = bt.feeds.YahooFinanceCSVData(dataname='../data/aapl.csv', reverse=False)
cerebro.adddata(datafeed)

# 전략 추가
cerebro.addstrategy(MACDStrategy)

# 백테스팅 실행
cerebro.run()

# 결과 분석 및 시각화
portfolio_stats = pd.read_csv("macd_strategy.csv", parse_dates=True, index_col='Date')
portfolio_stats['returns'] = portfolio_stats['Value'].pct_change()
qs.reports.full(portfolio_stats['returns'])
qs.plots.snapshot(portfolio_stats['returns'], title='MACD Strategy Performance')
cerebro.plot(iplot=False)
