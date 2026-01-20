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


#P182↓

for bar in range(SMA, len(self.data)):
    if self.position == 0:
        if(self.data['price'].iloc[bar] <
           self.data['SMA'].iloc[bar] - threshold):
            self.go_long(bar,amount=self.initial_amount)
            self.position = 1
        elif(self.data['price'].iloc[bar] >
             self.data['SMA'].iloc[bar] + threshold):
            self.go_short(bar, amount=self.initial_amount)
            self.position = -1
    elif self.position == 1:
        if self.data['price'].iloc[bar] >= self.data['SMA'].iloc[bar]:
            self.place_sell_order(bar, units=self.units)
            self.position = 0
    elif self.position == -1:
        if self.data['price'].iloc[bar] <= self.data['SMA'].iloc[bar]:
            self.place_buy_order(bar, units=-self.units)
            self.position = 0
self.close_out(bar)