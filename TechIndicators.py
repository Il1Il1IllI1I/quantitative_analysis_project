import yfinance as yf
import pandas as pd
import backtrader as bt

# MFI 구현
class MoneyFlowIndex(bt.Indicator):
    lines = ('mfi',)
    params = (('period', 14),)
    
    def __init__(self):
        # Typical Price
        tp = (self.data.high + self.data.low + self.data.close) / 3.0
        # Raw Money Flow
        rmf = tp * self.data.volume
        # Positive and Negative Money Flow
        pmf = bt.If(self.data.close > self.data.close(-1), rmf, 0)
        nmf = bt.If(self.data.close < self.data.close(-1), rmf, 0)
        # Money Flow Ratio
        mfr = bt.indicators.SmoothedMovingAverage(pmf, period=self.p.period) / \
              bt.indicators.SmoothedMovingAverage(nmf, period=self.p.period)
        # Money Flow Index
        self.lines.mfi = 100.0 - (100.0 / (1.0 + mfr))

indicators = {
    "RSI": bt.indicators.RSI_SMA,
    "MACD": bt.indicators.MACD,
    "Stochastic": bt.indicators.Stochastic,
    "ATR": bt.indicators.ATR,
    "CCI": bt.indicators.CCI,
    "ADX": bt.indicators.ADX,
    "WilliamsR": bt.indicators.WilliamsR,
    "ROC": bt.indicators.ROC,
    "Momentum": bt.indicators.Momentum,
    "MFI": MoneyFlowIndex
}

def fetch_indicators(ticker, start_date, end_date):
    # 데이터 로드
    data = yf.download(ticker, start=start_date, end=end_date)
    data['OpenInterest'] = 0  # backtrader에서 필요한 항목 추가

    # Backtrader 전용 데이터 피드 생성
    k200_data = bt.feeds.PandasData(dataname=data)

    class IndicatorFetcher(bt.Strategy):
        def __init__(self):
            self.indicators = {name: ind(self.data) for name, ind in indicators.items()}

    # 지표 초기화
    cerebro = bt.Cerebro(stdstats=False)  # 기본 통계자료를 포함하지 않음
    cerebro.adddata(k200_data)
    cerebro.addstrategy(IndicatorFetcher)
    
    # 백테스팅 실행
    result = cerebro.run()[0]
    
    # 결과 DataFrame 생성
    df = pd.DataFrame(index=data.index)
    for name in indicators.keys():
        df[name] = result.indicators[name].lines[0].array

    return df.dropna()


def save_to_csv(df, filename="indicators_result.csv"):
    # 소숫점 둘째 자리에서 반올림
    df_rounded = df.round(2)
    # CSV로 저장
    df_rounded.to_csv(filename)
    print(f"Data saved to {filename}")

# 예제 사용
ticker = "^KS11"  # KOSPI 200
start_date = "2011-04-01"
end_date = "2023-06-30"
df = fetch_indicators(ticker, start_date, end_date)
save_to_csv(df)  # 데이터를 CSV로 저장
