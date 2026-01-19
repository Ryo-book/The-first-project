def__init__(self, symbol, start, ednd, amount,
            ftc=0.0, ptc=0.0, verbose=True):
    self.symbol = symbol
    self.start = start
    self.end = end
    self.initial_amount = amount
    self.amount = amount
    self.ftc = ftc
    self.ptc = ptc
    self.units = 0
    self.position = 0
    self.trades = 0
    self.verbose = verbose
    self.get_data()