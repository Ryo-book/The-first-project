def get_data(self):
    '''Retrieves and prepares the data.
    '''
    
    raw = pd.read_csv('https://hilpiscg.com/pyalgo_eikon_eod_data.csv',
                      index_col=0, parse_dates=True).dropna()
    raw = pd.DataFrame(raw[self.symbol])
    raw = raw.loc[self.start:self.end]
    raw.rename(columns={self.symbol:'price'}, inplace=True)
    raw['return'] = np.log(raw / raw.shift(1))
    self.data = raw.dropna()



    
def plot_data(self):
    '''Plots the closing prices for symbol.
    '''
    self.data['price'].plot(figsize=(10,6), title=self.symbol)




def get_date_price(self, bar):
    '''Return date and price for bar.
    '''
    date = str(self.data.index[bar])[:10] 
    price = self.data.price.iloc[bar]
    return date, price   




def print_balance(self, bar):
    '''Print out current cash balance info.
    '''
    date, price = self.get_date_price(bar)
    print(f'{date} | current balance{self.amount:.2f}')
    



def print_net_wealth(self, bar):
    '''Print out current cash balance info.
    '''
    date, price = self.get_date_price(bar)
    net_wealth = self.units * price + self.amount
    print(f'{date} | current net wealth {net_wealth:.2f}')





print("スクリプトは正常に実行されました")
