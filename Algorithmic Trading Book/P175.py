def place_buy_order(self, bar, units=None, amount=None):
    '''Place a buy order.
    '''
    date, price = self.get_date_price(bar)
    if units is None:
        units = int(amount / price)
    self.amount -= (units * price) * (1 + self.ptc ) + self.ftc
    self.units += units
    self.trades += 1
    if self.verbose:
        print(f'{date} | selling{units}units at {price:.2f}')
        self.print_balance(bar)
        self.print_net_wealth(bar)





def place_sell_order(self, bar, units=None, amount=None):
    '''Place a sell order.
    '''
    date, price = self.get_date_price(bar)
    if units is None:
        units = int(amount / price)
    self.amount += (units * price) * (1 - self.ptc) - self.ftc
    self.units -= units
    self.trades += 1
    if self.verbose:
        print(f'{date} | selling {units} units at {price:.2f}')
        self.print_balance(bar)
        self.print_net_wealth(bar)
        