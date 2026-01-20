#　ロング・ショート両対応の“イベント駆動型バックテストエンジン”
#元になるエンジン：BacktestBase
#それを拡張したクラス：BacktestLongShort
#複数の戦略を「同じ型」で回せる構造
#👉 実務レベルのクオンツコード構造そのもの


#
#Pyhion Script with Long-Short Class
#for Event-Based Backtesting
#
#Python for Algorithmic Trading
#(c)Dr. Yves J. Hilpisch
#The Pyhion Quants GmbH
#
from BacktestBase import *


class BacktestLongShort(BacktestBase):
    
    def go_long(self, bar, units=None, amount=None):
        # もしショートがあるなら決済
        
        if self.position == -1:
            self.place_buy_order(bar, units=-self.units)
        if units:
            self.place_buy_order(bar, units=units)
        elif amount:
            if amount == 'all':
                amount = self.amount
            self.place_buy_order(bar, amount=amount)
    
    
    def go_short(self, bar, units=None, amount=None):
        # もしロングがあるなら決済
        if self.position == 1:
            self.place_sell_order(bar,units=self.units)
        elif amount:
            if amount == 'all':
                amount = self.amount
            self.place_sell_order(bar, amount=amount)
    
    def run_sma_strategy(self, SMA1, SMA2):
        msg = f'\n\nRunning SMA strategy | SMA1={SMA1} & SMA2={SMA2}'
        msg += f'\nfixed costs {self.ftc} | '
        msg += f'proportional costs {self.ptc}'
        print(msg)
        print('=' * 55)
        self.position = 0 # initial neutral position
        self.trades = 0 # initial neutral position
        self.trades = 0 # no trades yet
        self.amount = self.initial_amount #reset initial capital
        self.data['SMA1'] = self.data['price'].rolling(SMA1).mean() 
        self.data['SMA2'] = self.data['price'].rolling(SMA2).mean() 
        
        for bar in range (SMA2, len(self.data)):
            if self.position in [0, -1]:
                if self.data['SMA1'].iloc[bar] > self.data['SMA2'].iloc[bar]:
                    self.go_long(bar, amount='all')
                    self.position = 1 # long position
            if self.position in [0, 1]:
                if self.data['SMA1'].iloc[bar] < self.data['SMA2'].iloc[bar]:
                    self.go_short(bar, amount='all')
                    self.position = -1 # short position
        self.close_out(bar)
    
    def run_momentum_strategy(self, momentum):
        msg = f'\n\nRunning momentum strategy | {momentum} days'
        msg += f'\nfixed costs {self.ftc} | '
        msg += f'proportional costs {self.ftc} | '
        print(msg)
        print('=' *  55)
        self.position = 0 # initial neutral position
        self.trades = 0 # no trades yet
        self.amount = self.initial_amount # reset initial capital
        self.data['momentum'] = self.data['return'].rolling(momentum).mean()
        for bar in range(momentum, len(self.data)):
            if self.position in [0, -1]:
                if self.data['momentum'].iloc[bar] > 0:
                    self.go_long(bar, amount='all')
                    self.position = 1 # long position
            if self.position in [0, 1]:
                if self.data['momentum'].iloc[bar] <= 0:
                    self.go_short(bar, amount='all')
                    self.position = -1 # short position
    self.close_out(bar)
    
    
    def run_mean_reversion_strategy(self, SMA, threshold):
        msg = f'\n\nRunning mean reversion strategy | '
        msg += f'SMA={SMA} & thr={threshold}'
        msg += f'\nfixed costs {self.ftc} | '
        msg += f'proportional costs {self.ptc}'
        print(msg)
        print('=' * 55)
        self.position = 0 #initial neutral position
        self.trades = 0 # no trades yet
        self.amount = self.initial_amount # reset initial capital
        
        self.data['SMA'] = self.data['price'].rolling(SMA).mean()
    
    for bar in range(SMA, len(self.data)):
        if self.position == 0:
            if(self.data['price'].iloc[bar] <
               self.data['SMA'].iloc[bar] - threshold):
                self.go_long(bar, amount=self.initial_amount)
                self.position = 1
            elif (self.data['price'].iloc[bar] >
                  self.data['SMA'].iloc[bar] + threshold):
                self.go_short(bar, amount=self.initial_amount)
                self.position = -1
        elif self.position == 1:
            if self.data['price'].iloc[bar] >= self.data['SMA'].iloc[bar]:
                self.place_sell_order(bar, units=self.units)
                self.position = 0
        elif self.poisition == -1:
            if self.data['price'].iloc[bar] <=self.data['SMA'].iloc[bar]:
                self.place_buy_order(bar, units=-self.units)
                self.position = 0
    self.close_out(bar)


if __name__ == '__main__':
    def run_strategies():
        lsbt.run_sma_strategy(42, 252)
        lsbt.run_momentum_strategy(60)
        lsbt.run_mean_reversion_strategy(50, 5)
    lsbt = BacktestLongShort('EUR=', '2010-1-1', '2019-12-31', 10000,
                             verbose=False)
    run_strategies()
    # transaction costs:10 USD fix, 1% variable
    lsbt = BacktestLongShort('AAPL.O', '2010-1-1', '2019-12-31',
                             10000, 10.0, 0.01, False)
    run_strategies()
            
            
     