import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import quantstats as qs

class ChandelierStop:
    def __init__(self, symbol: str, length: int = 22, atr_period: int = 22, mult: int = 3):
        self.symbol = symbol
        self.length = length
        self.atr_period = atr_period
        self.mult = mult
        self.df = self._get_data()

    def _get_data(self):
        data = yf.download(self.symbol, start="2022-01-01", end="2023-12-31")
        return data[['Close', 'High', 'Low']]

    def calculate(self):
        df = self.df.copy()
        df['tr'] = df['High'] - df['Low'].shift(1)
        df['atr'] = df['tr'].rolling(window=self.atr_period).mean()
        df['short_stop'] = df['Close'].rolling(window=self.length).min() + self.mult * df['atr']
        df['long_stop'] = df['Close'].rolling(window=self.length).max() - self.mult * df['atr']

        # Initialize shortvs and longvs with short_stop and long_stop
        df['shortvs'] = df['short_stop']
        df['longvs'] = df['long_stop']

        # Use dataframe index for iteration
        indices = df.index
        for i in range(1, len(indices)):
            idx = indices[i]
            prev_idx = indices[i - 1]
            
            if df.at[idx, 'Close'] > df.at[prev_idx, 'shortvs']:
                df.at[idx, 'shortvs'] = df.at[idx, 'short_stop']
            else:
                df.at[idx, 'shortvs'] = min(df.at[idx, 'short_stop'], df.at[prev_idx, 'shortvs'])
            
            if df.at[idx, 'Close'] < df.at[prev_idx, 'longvs']:
                df.at[idx, 'longvs'] = df.at[idx, 'long_stop']
            else:
                df.at[idx, 'longvs'] = max(df.at[idx, 'long_stop'], df.at[prev_idx, 'longvs'])
        
        df['longswitch'] = ((df['Close'] >= df['shortvs'].shift(1)) & (df['Close'].shift(1) < df['shortvs'].shift(1))).astype(int)
        df['shortswitch'] = ((df['Close'] <= df['longvs'].shift(1)) & (df['Close'].shift(1) > df['longvs'].shift(1))).astype(int)
        
        df['direction'] = 0
        df.loc[df['longswitch'] == 1, 'direction'] = 1
        df.loc[df['shortswitch'] == 1, 'direction'] = -1
        df['direction'] = df['direction'].replace(0, method='ffill')
        
        self.df = df

    def plot(self):
        plt.figure(figsize=(12, 6))
        plt.plot(self.df['Close'], label='Close Price', color='black')
        plt.plot(self.df['long_stop'], label='Long Stop', linestyle='--', color='aqua')
        plt.plot(self.df['short_stop'], label='Short Stop', linestyle='--', color='fuchsia')
        plt.title('Chandelier Stop')
        plt.legend()
        plt.show()

    def backtest(self):
        df = self.df.copy()
        
        # Initialize the portfolio with $100,000
        portfolio_value = 100000
        cash = portfolio_value
        position = 0
        
        # Define a new DataFrame to store backtest results
        results = pd.DataFrame(index=df.index, columns=['portfolio_value', 'returns'])
        results.at[df.index[0], 'portfolio_value'] = portfolio_value
        results.at[df.index[0], 'returns'] = 0
        
        # Loop over the DataFrame and execute the strategy
        for i in range(1, len(df)):
            idx = df.index[i]
            prev_idx = df.index[i-1]
            
            # If there is a long signal
            if df.at[idx, 'longswitch'] == 1 and cash > 0:
                position = cash / df.at[idx, 'Close']
                cash = 0
                
            # If there is a short signal
            elif df.at[idx, 'shortswitch'] == 1 and position > 0:
                cash = position * df.at[idx, 'Close']
                position = 0
                
            # Calculate portfolio value and daily returns
            portfolio_value = cash + position * df.at[idx, 'Close']
            daily_return = (portfolio_value / results.at[prev_idx, 'portfolio_value']) - 1 if i > 0 else 0
            
            # Store the results
            results.at[idx, 'portfolio_value'] = portfolio_value
            results.at[idx, 'returns'] = daily_return
            
        self.results = results.dropna()
    
    def plot_results(self):
        plt.figure(figsize=(12, 6))
        plt.plot(self.results.index, self.results['portfolio_value'], label='Portfolio Value', color='blue')
        plt.title('Backtest Results')
        plt.xlabel('Date')
        plt.ylabel('Portfolio Value ($)')
        plt.legend()
        plt.show()
        

# 사용 예제
symbol = "AAPL"
chandelier_stop = ChandelierStop(symbol)
chandelier_stop.calculate()
chandelier_stop.backtest()
chandelier_stop.plot_results()