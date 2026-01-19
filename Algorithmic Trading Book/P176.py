def close_out(self, bar):
    '''Closing out a long or short position.
    '''
    date, price = self.get_date_price(bar)
    self.amount += self.units * price
    self.units = 0
    self.trades += 1
    if self.verbose:
        print(f'{date} | inventory {self.units} units at {price:2f}')
        print('=' * 55)
    print('Final balance  [$] {:.2f}'.format(self.amount))
    perf = ((self.amount - self.initial_amount)/
            self.initial_amount * 100)
    print(f'Net Performance [%] {pref:.2f}')
    print(f'Trades Executed [#] {self.trades}')
    print('=' * 55)





if __name__ == '__main__':
    bb = BacktestBase('AAPL.O', '2010-1-1', '2019-12-31', 10000)
    print(bb.data.info())
    print(bb.data.tail())
    bb.plot_data()


%run BacktestBase.py