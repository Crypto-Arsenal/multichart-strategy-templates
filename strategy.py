class Strategy(StrategyBase):
    def __init__(self):
        self.period = 60
        self.subscribed_books = {}
        self.options = {}
        self.curTotalPosition = None
        self.ORDER_PORTION = 0.1

    def on_tradingview_signal(self, signal, candles):
        exchange, pair, base, quote = CA.get_exchange_pair()

        """
        Calculate New Position
        """
        self.newPosition = None

        signal_action = signal.get('action')
        log = signal.get('log')

        CA.log('multichart log: ' + str(log))

        items = log.split(",")

        if len(items) > 1:
            self.newPosition = items[1]

        if self.newPosition is None:
            CA.log("failed to parse position from log " + log)
            return

        self.newPosition = int(self.newPosition.strip()) * self.ORDER_PORTION

        # start bot only if we have a 0 signal
        if self.curTotalPosition is None and self.newPosition != 0:
            CA.log("current Position is not 0; will start position once at 0")
            return

        """
        Set Current Position
        """
        # will be current position
        self.curTotalPosition = self.get_total_position()

        if self.curTotalPosition == self.newPosition:
            return

        if self.curTotalPosition > self.newPosition:
            if self.newPosition >= 0:
                # 3 -> 2
                amount = self.curTotalPosition - self.newPosition
                CA.log("Amount to close long: " + str(amount))
                CA.close_long(exchange, pair, amount, CA.OrderType.MARKET)
            else:
                # 2 -> -1
                if self.curTotalPosition > 0:
                    # "closeLong/openShort"
                    close_long_amount = self.curTotalPosition
                    open_short_amount = abs(self.newPosition)
                    CA.log("Amount to close long: " + str(close_long_amount))
                    CA.log("Amount to open short: " + str(open_short_amount))
                    CA.place_order(exchange, pair, action='close_long', amount=close_long_amount, conditional_order_type='OTO', child_conditional_orders=[{
                        'action': 'open_short', 'amount': open_short_amount
                    }])
                else:
                    # -3 -> -2 = 1
                    amount = abs(self.newPosition - self.curTotalPosition)
                    CA.log("Amount to open short: " + str(amount))
                    CA.open_short(exchange, pair, amount, CA.OrderType.MARKET)
        else:
            if self.newPosition <= 0:
                #  -3 -> -1
                amount = abs(self.curTotalPosition - self.newPosition)
                CA.log("Amount to close short: " + str(amount))
                CA.close_short(exchange, pair, amount, CA.OrderType.MARKET)
            else:
                if self.curTotalPosition >= 0:
                    # 1 -> 2
                    amount = (self.curTotalPosition - self.newPosition)
                    CA.log("Amount to open long: " + str(amount))
                    CA.open_long(exchange, pair, amount, CA.OrderType.MARKET)
                else:
                    close_short_amount = self.curTotalPosition
                    open_long_amount = abs(self.newPosition) 
                    CA.log("Amount to close short: " + str(close_short_amount))
                    CA.log("Amount to open long: " + str(open_long_amount))
                    CA.place_order(exchange, pair, action='close_short', amount=close_short_amount, conditional_order_type='OTO', child_conditional_orders=[{
                        'action': 'open_long', 'amount': open_long_amount
                    }])

    def on_order_state_change(self,  order):
        if order.status == CA.OrderStatus.FILLED:
            CA.log('LATEST POS: ' + str(self.get_total_position()))

    def trade(self, candles):
        pass

    # return current total position: -n 0, +n  where n is number of contracts
    def get_total_position(self):
        exchange, pair, base, quote = CA.get_exchange_pair()

        curTotalPosition = None
        total_long_position_size = None
        total_short_position_size = None
        long_position = CA.get_position(exchange, pair, CA.PositionSide.LONG)
        if long_position:
            total_long_position_size = long_position.total_size

        short_position = CA.get_position(exchange, pair, CA.PositionSide.SHORT)
        if short_position:
            total_short_position_size = short_position.total_size

        if total_long_position_size is None and total_short_position_size is None:
            curTotalPosition = 0

        if total_long_position_size is not None:
            curTotalPosition = abs(total_long_position_size)

        if total_short_position_size is not None:
            curTotalPosition = -1 * abs(total_short_position_size)

        return curTotalPosition
