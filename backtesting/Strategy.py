import backtrader as bt
import math
import statistics
import backtrader.indicators as btind
import numpy as np

class BaseStrategy(bt.Strategy):
    params = (
        ('printlog', False),
    )

    def log(self, txt, dt=None, doprint=False):
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.datetime(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

            # Check if an order has been completed
            # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm

            elif order.issell():
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

            # Write down: no pending order
        self.order = None

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            self.buy_condition()

        else:
            self.sell_condition()

    #if you want to print the result
    # def stop(self):
    #     self.print()

    def buy_condition(self):
        return

    def sell_condition(self):
        return

    def print(self):
        print(self.__class__.__name__, self.broker.getvalue(), self.params.__dict__)

class CrossStrategy(BaseStrategy):
    params = (
        ('ma1_period', 14),
        ('ma2_period', 30),
        ('ma1_type', btind.MovingAverageSimple),
        ('ma2_type', btind.MovingAverageSimple),
        ('printlog', False)
    )

    def __init__(self):
        super().__init__()
        self.ma1 = self.params.ma1_type(self.datas[0] , period = self.params.ma1_period)
        self.ma2 = self.params.ma2_type(self.datas[0] , period = self.params.ma2_period)

    def buy_condition(self):
        if self.ma1 > self.ma2:
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()

    def sell_condition(self):
        if self.ma1 < self.ma2:
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.order = self.sell()

class TripleCrossStrategy(BaseStrategy):
    params = (
        ('ma1_period', 5),
        ('ma2_period', 8),
        ('ma3_period', 11),
        ('ma1_type', btind.MovingAverageSimple),
        ('ma2_type', btind.MovingAverageSimple),
        ('ma3_type', btind.MovingAverageSimple),
        ('printlog', False)
    )

    def __init__(self):
        super().__init__()
        self.ma1 = self.params.ma1_type(self.datas[0], period = self.params.ma1_period)
        self.ma2 = self.params.ma2_type(self.datas[0], period = self.params.ma2_period)
        self.ma3 = self.params.ma3_type(self.datas[0], period= self.params.ma3_period)

    def buy_condition(self):
        if self.ma1 > self.ma2 and self.ma2 > self.ma3:
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()

    def sell_condition(self):
        if self.ma1 < self.ma2 and self.ma2 < self.ma3:
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.order = self.sell()

class SlopeStrategy(BaseStrategy):
    params = (
        ('ma1_period', 14),
        ('ma1_type', btind.MovingAverageSimple),
        ('printlog', False)
    )

    def __init__(self):
        super().__init__()
        self.ma1 = self.params.ma1_type(self.datas[0], period = self.params.ma1_period)

    def buy_condition(self):
        if self.ma1 > self.ma1[-1]:
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()

    def sell_condition(self):
        if self.ma1 < self.ma1[-1]:
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.order = self.sell()

class DirectionalStrategy(BaseStrategy):
    params = (
        ('di_period', 14),
        ('printlog', False)
    )

    def __init__(self):
        super().__init__()
        self.di = btind.DirectionalMovement(self.datas[0], period=self.p.di_period)

    def buy_condition(self):
        if self.di.l.plusDI > self.di.l.minusDI:
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()

    def sell_condition(self):
        if self.di.l.plusDI < self.di.l.minusDI:
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.order = self.sell()

class LaguerreRsiStrategy(BaseStrategy):
    params = (
        ('period', 6),
        ('gamma', 0.5),
        ('overbought', 0.8),
        ('oversold', 0.2),
        ('printlog', False)
    )

    def __init__(self):
        super().__init__()
        self.rsi = btind.LaguerreRSI(period = self.p.period, gamma= self.p.gamma)

    def buy_condition(self):
        if self.rsi > self.rsi[-1] and self.rsi > self.p.oversold:
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()

    def sell_condition(self):
        if self.rsi < self.rsi[-1] and self.rsi < self.p.overbought:
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.order = self.sell()

class AboveBelowStrategy(BaseStrategy):
    params = (
        ('ma1_period', 14),
        ('ma2_period', 30),
        ('ma1_type', btind.MovingAverageSimple),
        ('ma2_type', btind.MovingAverageSimple),
        ('printlog', False)
    )

    def __init__(self):
        super().__init__()
        self.ma1 = self.params.ma1_type(self.datas[0], period = self.params.ma1_period)
        self.ma2 = self.params.ma2_type(self.datas[0], period = self.params.ma2_period)

    def buy_condition(self):
        if self.datas[0].close > self.ma1 and self.datas[0].close > self.ma2:
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()

    def sell_condition(self):
        if self.datas[0].close < self.ma1 and self.datas[0].close < self.ma2:
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.order = self.sell()

class StochCrossStrategy(BaseStrategy):
    params = (
        ('ma1', 14),
        ('ma2', 30),
        ('period', 14),
        ('printlog', False),
    )

    def __init__(self):
        super().__init__()
        self.ma1 = btind.MovingAverageSimple(self.datas[0], period = self.params.ma1)
        self.ma2 = btind.MovingAverageSimple(self.datas[0], period = self.params.ma2)
        self.stoch = btind.Stochastic(self.datas[0], period = self.params.period)

    def buy_condition(self):
        if self.ma1 > self.ma2 and self.stoch < 20:
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()

    def sell_condition(self):
        if self.ma1 < self.ma2 and self.stoch > 80:
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.order = self.sell()

class RsiCrossStrategy(BaseStrategy):
    params = (
        ('ma1', 14),
        ('ma2', 30),
        ('period', 6),
        ('gamma',0.5),
        ('lower_limit', 0.2),
        ('upper_limit', 0.8),
        ('printlog', False),
    )

    def __init__(self):
        super().__init__()
        self.ma1 = btind.MovingAverageSimple(self.datas[0], period = self.params.ma1)
        self.ma2 = btind.MovingAverageSimple(self.datas[0], period = self.params.ma2)
        self.rsi = btind.LaguerreRSI(self.datas[0], period = self.params.period, gamma = self.params.gamma)

    def buy_condition(self):
        if self.ma1 > self.ma2 and self.rsi>self.rsi[-1] and self.rsi > self.params.lower_limit:
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()

    def sell_condition(self):
        if self.ma1 < self.ma2 and self.rsi<self.rsi[-1] and self.rsi < self.params.upper_limit:
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.order = self.sell()

class DoubleCrossStrategy(BaseStrategy):
    params = (
        ('ma1', 14),
        ('ma2', 30),
        ('ma3', 10),
        ('ma4', 20),
        ('printlog', False)
    )

    def __init__(self):
        super().__init__()
        self.ma1 = btind.MovingAverageSimple(self.data, period = self.params.ma1)
        self.ma2 = btind.MovingAverageSimple(self.data, period = self.params.ma2)
        self.ma3 = btind.MovingAverageSimple(self.data1, period = self.params.ma3)
        self.ma4 = btind.MovingAverageSimple(self.data1, period = self.params.ma4)

    def buy_condition(self):
        if self.ma1 > self.ma2 and self.ma3 > self.ma4:
            self.log('BUY CREATE, %.2f %.2f > %.2f & %.2f > %.2f' % (self.dataclose[0], self.ma1[0], self.ma2[0], self.ma3[0], self.ma4[0]))
            self.order = self.buy()

    def sell_condition(self):
        if self.ma1 < self.ma2 and self.ma3 < self.ma4:
            self.log('SELL CREATE, %.2f %.2f < %.2f & %.2f < %.2f' % (self.dataclose[0], self.ma1[0], self.ma2[0], self.ma3[0], self.ma4[0]))
            self.order = self.sell()

class ExtendedCrossStrategy(BaseStrategy):
    params = (
        ('ma1', 5),
        ('ma2', 20),
        ('ma3', 50),
        ('atr', 1),
        ('printlog', False)
    )

    def __init__(self):
        super().__init__()
        self.ma1 = btind.MovingAverageExponential(self.datas[0], period = self.params.ma1)
        self.ma2 = btind.MovingAverageExponential(self.datas[0], period = self.params.ma2)
        self.ma3 = btind.MovingAverageExponential(self.datas[0], period=self.params.ma3)
        self.atr = btind.AverageTrueRange(
            self.datas[0])

    def buy_condition(self):
        if self.ma1 > (self.ma2 + self.params.atr * self.atr) and self.dataclose[0] > self.ma3:
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()

    def sell_condition(self):
        if self.ma1 < (self.ma2 - self.params.atr * self.atr) and self.dataclose[0] < self.ma3:
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.order = self.sell()

class AtrCrossStrategy(CrossStrategy):
    params = (
        ('atr', 1),
        ('period', 14),
    )

    def __init__(self):
        super().__init__()

        self.atr = btind.AverageTrueRange(
            self.datas[0], period=self.params.period)

    def buy_condition(self):
        if self.ma1 > (self.ma2 + self.params.atr * self.atr):
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()

    def sell_condition(self):
        if self.ma1 < (self.ma2 - self.params.atr * self.atr):
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.order = self.sell()

class AboveMA(BaseStrategy):
    params = (
        ('ma1_period', 5),
        ('ma1_type', btind.MovingAverageSimple),
        ('printlog', False)
    )

    def __init__(self):
        super().__init__()
        self.ma1 = self.params.ma1_type(self.datas[0], period = self.params.ma1_period)

    def buy_condition(self):
        if self.dataclose[0] > self.ma1 :
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()

    def sell_condition(self):
        if self.dataclose[0] < self.ma1:
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.order = self.sell()

class AboveZeroStrategy(BaseStrategy):
    params = (
        ('printlog', False),
        ('dummy', False)
    )

    def __init__(self):
        super().__init__()
        self.crossover = btind.CrossOver(self.oss, 0)

    def buy_condition(self):
        if self.crossover > 0:
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()

    def sell_condition(self):
        if self.crossover < 0:
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.order = self.sell()

class SignalStrategy(BaseStrategy):
    params = (
        ('printlog', False),
        ('dummy', False)
    )

    def __init__(self):
        super().__init__()
        self.signal = self.oss.lines.signal
        self.crossover = btind.CrossOver(self.oss, self.signal)

    def buy_condition(self):
        if self.crossover > 0:
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()

    def sell_condition(self):
        if self.crossover < 0:
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.order = self.sell()

    def print(self):
        return

class Default(BaseStrategy):
    params = (
        ("printlog", False),
        ("dummy", 1)
    )


    def __init__(self):
        super().__init__()

    def buy_condition(self):
        self.order = self.buy()

class KnowSureThing(AboveZeroStrategy):
    params = (
        ("rma1", 10),
        ("rma2", 15),
        ("rma3", 20),
        ("rma4", 30),
        ("period", 10)
    )
    def __init__(self):
        self.oss = btind.KnowSureThing(rma1 = self.params.rma1, rma2 = self.params.rma2, rma3 = self.params.rma3, rma4 = self.params.rma4,
                                       rp1 = self.params.period, rp2 = self.params.period, rp3 = self.params.period, rp4 = self.params.period)
        super().__init__()

class Macd(AboveZeroStrategy):
    params = (
        ("period_me1", 12),
        ("period_me2", 26),
        ("period_signal", 9),
    )
    def __init__(self):
        self.oss = btind.MACD(
            self.datas[0], period_me1=self.params.period_me1, period_me2=self.params.period_me2,
            period_signal=self.params.period_signal)
        super().__init__()

class Trix(AboveZeroStrategy):
    params = (
        ("period", 15),
        ("dummy", False)
    )
    def __init__(self):
        self.oss = btind.Trix(
            self.datas[0], period=self.params.period)
        super().__init__()

class Tsi(AboveZeroStrategy):
    params = (
        ("period1", 25),
        ("period2", 13),
        ("pchange", 1),
        ("dummy", False)
    )
    def __init__(self):
        self.oss = btind.TrueStrengthIndicator(
            self.datas[0], period1=self.params.period1, period2=self.params.period2, pchange=self.params.pchange)
        super().__init__()

class Awesome(AboveZeroStrategy):
    params = (
        ('fast', 5),
        ('slow', 34),
    )

    def __init__(self):
        self.oss = btind.AwesomeOscillator(
            self.datas[0], fast=self.params.fast, slow=self.params.slow)
        super().__init__()

class CombinedMACross(BaseStrategy):
    params = (
        ('ma1', 5),
        ('ma2', 20),
        ('printlog', False)
    )

    def __init__(self):
        super().__init__()

        self.atr = btind.AverageTrueRange(
            self.datas[0], period=14)

        self.dma1 = btind.DoubleExponentialMovingAverage(
            self.datas[0], period=self.params.ma1)

        self.dma2 = btind.DoubleExponentialMovingAverage(
            self.datas[0], period=self.params.ma2)

        self.hma1 = btind.HullMovingAverage(
            self.datas[0], period=self.params.ma1)

        self.hma2 = btind.HullMovingAverage(
            self.datas[0], period=self.params.ma2)

        self.zma1 = btind.ZeroLagExponentialMovingAverage(
            self.datas[0], period=self.params.ma1)

        self.zma2 = btind.ZeroLagExponentialMovingAverage(
            self.datas[0], period=self.params.ma2)

    def buy_condition(self):
        # print(self.dma1 > self.dma2)
        # print(self.hma1 > self.hma2)
        # print(self.zma1 > self.zma2)
        # print()
        if self.dma1 > (self.dma2 + self.atr) and self.hma1 > (self.hma2 + self.atr) and self.zma1 > (self.zma2 + self.atr):
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()

    def sell_condition(self):
        if self.dma1 < (self.dma2 - self.atr) and self.hma1 < (self.hma2 - self.atr) and self.zma1 < (self.zma2 - self.atr) :
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.order = self.sell()

class CombinedStrategy(BaseStrategy):
    params = (
        ("kst_rma1", 10),
        ("kst_rma2", 15),
        ("kst_rma3", 20),
        ("kst_rma4", 30),
        ("kst_period", 10),
        ("macd_period_me1", 12),
        ("macd_period_me2", 26),
        ("macd_period_signal", 9),
        ("trix_period", 15),
        ("tsi_period1", 25),
        ("tsi_period2", 13),
        ("tsi_pchange", 1),
        ('ao_fast', 5),
        ('ao_slow', 34),
        ('adx_period', 20),
        ('adx_strength', 20),
        ('buy_limit', 3),
        ('printlog', False)
    )

    def __init__(self):
        super().__init__()

        self.kst = btind.KnowSureThing(self.datas[0], rma1=self.params.kst_rma1, rma2=self.params.kst_rma2, rma3=self.params.kst_rma3,
                                       rma4=self.params.kst_rma4,
                                       rp1=self.params.kst_period, rp2=self.params.kst_period, rp3=self.params.kst_period,
                                       rp4=self.params.kst_period)

        self.macd = btind.MACD(
            self.datas[0], period_me1=self.params.macd_period_me1, period_me2=self.params.macd_period_me2,
            period_signal=self.params.macd_period_signal)

        # self.trix = btind.Trix(
        #     self.datas[0], period=self.params.trix_period)

        # self.tsi = btind.TrueStrengthIndicator(
        #     self.datas[0], period1=self.params.tsi_period1, period2=self.params.tsi_period2, pchange=self.params.tsi_pchange)

        self.ao = btind.AwesomeOscillator(
            self.datas[0], fast=self.params.ao_fast, slow=self.params.ao_slow)

        # self.adx = btind.AverageDirectionalMovementIndex(self.datas[0], period=self.params.adx_period)

        # self.dpo = btind.DetrendedPriceOscillator(self.datas[0])
        #
        self.psar = btind.ParabolicSAR(self.datas[0])

    def buy_condition(self):
        point = 0
        if self.kst > 0:
            point += 1
        if self.macd > 0:
            point += 1
        # if self.trix > 0:
        #     point += 1
        # if self.tsi > 0:
        #     point += 1
        if self.ao > 0 :
            point += 1
        # if self.adx > 20 :
        #     point += 1
        # if self.dpo > 0:
        #     point += 1
        if self.psar < self.dataclose:
            point += 1

        if(point>=self.params.buy_limit):
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()

    def sell_condition(self):
        point = 0
        if self.kst < 0:
            point += 1
        if self.macd < 0:
            point += 1
        # if self.trix < 0:
        #     point += 1
        # if self.tsi < 0:
        #     point += 1
        if self.ao < 0 :
            point += 1
        # if self.adx > 20 :
        #     point += 1
        # if self.dpo < 0:
        #     point += 1
        if self.psar > self.dataclose:
            point += 1

        if(point>=self.params.buy_limit):
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.order = self.sell()

    def print(self):
        print(self.broker.getvalue(), self.params.__dict__)

class AllPosibilitiesStrategy(BaseStrategy):
    params = (
        ('list', []),
        ('ma1', 5),
        ('ma2', 20),
        ('ma', 50),
        ('printlog', False)
    )

    def __init__(self):
        super().__init__()
        self.ma = btind.MovingAverageSimple(self.datas[0], period = self.params.ma)
        self.ma1 = btind.MovingAverageSimple(self.datas[0], period = self.params.ma1)
        self.ma2 = btind.MovingAverageSimple(self.datas[0], period = self.params.ma2)
        self.atr = btind.AverageTrueRange(self.datas[0])

        self.kst = btind.KnowSureThing(self.datas[0])

        self.macd = btind.MACD(self.datas[0])

        self.trix = btind.TrixSignal(self.datas[0])

        self.ao = btind.AwesomeOscillator(self.datas[0])

        self.tsi = btind.TrueStrengthIndicator(self.datas[0])

        self.psar = btind.ParabolicSAR(self.datas[0])

        self.adx = btind.AverageDirectionalMovementIndex(self.datas[0])

        self.dpo = btind.DetrendedPriceOscillator(self.datas[0])

        self.rsi = btind.RSI(self.datas[0])

        self.accdec = btind.AccelerationDecelerationOscillator(self.datas[0])

        self.bbands = btind.BollingerBands(self.datas[0])

        self.cci = btind.CommodityChannelIndex(self.datas[0])

        self.pgood = btind.PrettyGoodOscillator(self.datas[0])

        self.williamsr = btind.WilliamsR(self.datas[0])

        self.uo = btind.UltimateOscillator(self.datas[0])

        self.stoch = btind.Stochastic(self.datas[0])

    def buy_condition(self):
        if self.ma1 > (self.ma2):
            point = 0
            if (1 in self.params.list) and self.kst > 0:
                point += 1
            if (2 in self.params.list) and self.macd > 0:
                point += 1
            if (3 in self.params.list) and self.trix > 0:
                point += 1
            if (4 in self.params.list) and self.tsi > 0:
                point += 1
            if (5 in self.params.list) and self.ao > 0:
                point += 1
            if (6 in self.params.list) and self.psar < self.dataclose:
                point += 1
            # if (7 in self.params.list) and self.adx > 20 :
            #     point += 1
            # if (8 in self.params.list) and self.dpo > 0:
            #     point += 1
            # if (9 in self.params.list) and self.rsi > 50:
            #     point += 1
            # if (10 in self.params.list) and self.accdec > 0:
            #     point += 1
            # if (11 in self.params.list) and self.dataclose > self.bbands.lines.top[0]:
            #     point += 1
            # if (12 in self.params.list) and self.cci > 0:
            #     point += 1
            # if (13 in self.params.list) and self.pgood > 3:
            #     point += 1
            # if (14 in self.params.list) and self.williamsr > -50:
            #     point += 1
            # if (15 in self.params.list) and self.uo > 50:
            #     point += 1
            # if (16 in self.params.list) and self.stoch > 50:
            #     point += 1
            # if (17 in self.params.list) and self.macd > self.macd.lines.signal:
            #     point += 1
            # if (18 in self.params.list) and self.rsi < 30:
            #     point += 1
            # if (19 in self.params.list) and self.cci < -100:
            #     point += 1
            # if (20 in self.params.list) and self.williamsr < -80:
            #     point += 1
            # if (21 in self.params.list) and self.stoch.lines.percK > self.stoch.lines.percD:
            #     point += 1
            # if (22 in self.params.list) and self.trix.lines.trix > self.trix.lines.signal:
            #     point += 1
            # if (23 in self.params.list) and self.kst.lines.kst > self.trix.lines.signal:
            #     point += 1
            if (point >= len(self.params.list)):
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                self.order = self.buy()

    def sell_condition(self):
        if self.ma1 < (self.ma2) :
            point = 0
            if (1 in self.params.list) and self.kst < 0:
                point += 1
            if (2 in self.params.list) and self.macd < 0:
                point += 1
            if (3 in self.params.list) and self.trix < 0:
                point += 1
            if (4 in self.params.list) and self.tsi < 0:
                point += 1
            if (5 in self.params.list) and self.ao < 0:
                point += 1
            if (6 in self.params.list) and self.psar > self.dataclose:
                point += 1
            # if (7 in self.params.list) and self.adx > 20 :
            #     point += 1
            # if (8 in self.params.list) and self.dpo < 0:
            #     point += 1
            # if (9 in self.params.list) and self.rsi < 50:
            #     point += 1
            # if (10 in self.params.list) and self.accdec < 0:
            #     point += 1
            # if (11 in self.params.list) and self.dataclose < self.bbands.lines.bot[0]:
            #     point += 1
            # if (12 in self.params.list) and self.cci < 0:
            #     point += 1
            # if (13 in self.params.list) and self.pgood < 0:
            #     point += 1
            # if (14 in self.params.list) and self.williamsr < -50:
            #     point += 1
            # if (15 in self.params.list) and self.uo < 50:
            #     point += 1
            # if (16 in self.params.list) and self.stoch < 50:
            #     point += 1
            # if (17 in self.params.list) and self.macd < self.macd.lines.signal:
            #     point += 1
            # if (18 in self.params.list) and self.rsi > 70:
            #     point += 1
            # if (19 in self.params.list) and self.cci > 100:
            #     point += 1
            # if (20 in self.params.list) and self.williamsr > -20:
            #     point += 1
            # if (21 in self.params.list) and self.stoch.lines.percK < self.stoch.lines.percD:
            #     point += 1
            # if (22 in self.params.list) and self.trix.lines.trix < self.trix.lines.signal:
            #     point += 1
            # if (23 in self.params.list) and self.kst.lines.kst < self.trix.lines.signal:
            #     point += 1
            if (point >= len(self.params.list)):
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                self.order = self.sell()

class Momentum(AboveZeroStrategy):
    params = (
        ("period", 12),
        ("band", 100),
        ("printlog", True)
    )
    def __init__(self):
        self.oss = btind.MomentumOscillator(
            self.datas[0], period=self.params.period, band = self.params.band)
        super().__init__()

    def print(self):
        print("Momentum Oscillator " + str(self.params.period) + " " +
              str(self.broker.getvalue()))

class AccDec(AboveZeroStrategy):
    params = (
        ('period', 5),
        ('printlog', False)
    )

    def __init__(self):
        self.oss = btind.AccelerationDecelerationOscillator(
            self.datas[0], period=self.params.period)
        super().__init__()

    def print(self):
        print("Acc Dec Oscillator " + str(self.params.period) + " " +
              str(self.broker.getvalue()))

class MacdSignal(SignalStrategy):
    params = (
        ("period_me1", 12),
        ("period_me2", 26),
        ("period_signal", 9),
    )
    def __init__(self):
        self.oss = btind.MACD(
            self.datas[0], period_me1=self.params.period_me1, period_me2=self.params.period_me2,
            period_signal=self.params.period_signal)
        super().__init__()

    def print(self):
        print(str(self.params.period_me1) + " " +
              str(self.params.period_me2) + " " +
              str(self.params.period_signal) + " " +
              str(self.broker.getvalue()))

class TrixSignal(SignalStrategy):
    params = (
        ("period", 15),
        ("dummy", False)
    )
    def __init__(self):
        self.oss = btind.TrixSignal(
            self.datas[0], period=self.params.period)
        super().__init__()

    def print(self):
        print("Trix Signal" + str(self.params.period) + " " +
              str(self.broker.getvalue()))

class VWMA(bt.Indicator):
    lines = ('vwma',)
    params = (
        ('period', 14),
    )

    def __init__(self):
        super().__init__(self)
        ma = btind.MovingAverageSimple(self.data.volume * self.datas[0].close , period = self.params.period) / btind.MovingAverageSimple(self.data.volume, period = self.params.period)
        self.lines.vwma = ma

class VWMAStrategy(CrossStrategy):

    def __init__(self):
        super().__init__()
        self.ma1 = VWMA(
            self.datas[0], period=self.params.ma1_period)

        self.ma2 = VWMA(
            self.datas[0], period=self.params.ma2_period)

class Vix_Fix_Indicator(bt.Indicator):
    params = (
        ("pd", 22),  # LookBack Period Standard Deviation High
        ("bbl", 20),  # Bolinger Band Length
        ("mult", 2),  # Bollinger Band Standard Deviation Up
        ("lb", 50),
        ("ph", 0.85),
        ("pl", 1.01),
        ("hp", False),
        ("sd", False),
    )

    lines = ("wvf", "bbands_top", "bbands_bot", "range_high", "range_low")

    def next(self):
        self.lines.wvf[0] = 0.0
        self.lines.bbands_top[0] = 0.0
        self.lines.bbands_bot[0] = 0.0

        close_list = self.datas[0].close.get(size=self.params.pd).tolist()
        if (len(close_list) == self.params.pd):
            max_close_list = max(close_list)
            self.lines.wvf[0] = ((max_close_list - self.datas[0].low[0]) / max_close_list) * 100

            sdev = self.params.mult * statistics.stdev(self.lines.wvf.get(size=self.params.bbl))
            datasum = math.fsum(self.lines.wvf.get(size=self.params.bbl))
            midline = datasum / self.params.bbl

            self.lines.bbands_top[0] = midline + sdev
            self.lines.bbands_bot[0] = midline - sdev

            range = self.lines.wvf.get(size=self.params.lb).tolist()
            if (len(range) == self.params.lb):
                self.lines.range_high[0] = max(range) * self.params.ph
                self.lines.range_low[0] = min(range) * self.params.pl

            #print(self.lines.max[0], self.lines.wvf[0], self.lines.bbands_top[0], self.lines.bbands_bot[0], self.lines.range_high[0], self.lines.range_low[0])

class Williams_Vix_Fix(BaseStrategy):

    def __init__(self):
        super().__init__()

        self.wvf = Vix_Fix_Indicator()

    def buy_condition(self):
        if self.wvf.lines.wvf > self.wvf.lines.bbands_top or self.wvf.lines.wvf > self.wvf.lines.range_high:
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()

class Laguerre(bt.Indicator):

    params = (
        ('short_gamma', 0.4),
        ('long_gamma', 0.8),
        ('pctile', 90),
        ('wrnpctile', 70),
        ('lkbT',200),
        ('lkbB',200),
    )

    lines = ("pctRankT", "pctRankB", "pctileB", "wrnpctileB", "ppoT", "ppoB")

    lmas_l0, lmas_l1, lmas_l2, lmas_l3 = 0.0, 0.0, 0.0, 0.0
    lmal_l0, lmal_l1, lmal_l2, lmal_l3 = 0.0, 0.0, 0.0, 0.0

    def next(self):

        #lmas
        lmas0_1 = self.lmas_l0  # cache previous intermediate values
        lmas1_1 = self.lmas_l1
        lmas2_1 = self.lmas_l2

        g = self.p.short_gamma  # avoid more lookups
        self.lmas_l0 = l0 = (1.0 - g) * (self.datas[0].high + self.datas[0].low)/2 + g * lmas0_1
        self.lmas_l1 = l1 = -g * l0 + lmas0_1 + g * lmas1_1
        self.lmas_l2 = l2 = -g * l1 + lmas1_1 + g * lmas2_1
        self.lmas_l3 = l3 = -g * l2 + lmas2_1 + g * self.lmas_l3

        self.lmas = lmas = (self.lmas_l0 + 2*self.lmas_l1 + 2*self.lmas_l2 + self.lmas_l3)/6
        
        #lmal
        lmal0_1 = self.lmal_l0  # cache previous intermediate values
        lmal1_1 = self.lmal_l1
        lmal2_1 = self.lmal_l2

        g = self.p.long_gamma  # avoid more lookups
        self.lmal_l0 = l0 = (1.0 - g) * (self.datas[0].high + self.datas[0].low)/2 + g * lmal0_1
        self.lmal_l1 = l1 = -g * l0 + lmal0_1 + g * lmal1_1
        self.lmal_l2 = l2 = -g * l1 + lmal1_1 + g * lmal2_1
        self.lmal_l3 = l3 = -g * l2 + lmal2_1 + g * self.lmal_l3

        lmal = (self.lmal_l0 + 2 * self.lmal_l1 + 2 * self.lmal_l2 + self.lmal_l3) / 6

        self.lines.pctileB[0] = self.params.pctile * -1
        self.lines.wrnpctileB[0] = self.params.wrnpctile * -1

        self.lines.ppoT[0] = (lmas - lmal) / lmal * 100
        self.lines.ppoB[0] = (lmal - lmas) / lmal * 100

        ppoT_list = self.lines.ppoT.get(size=self.params.lkbT).tolist()
        if (len(ppoT_list) == self.params.lkbT):
            self.lines.pctRankT[0] = sum(self.lines.ppoT[0] >= i for i in ppoT_list) / len(ppoT_list) * 100

        ppoB_list = self.lines.ppoB.get(size=self.params.lkbB).tolist()
        if (len(ppoB_list) == self.params.lkbB):
            self.lines.pctRankB[0] = sum(self.lines.ppoB[0] >= i for i in ppoB_list) / len(ppoB_list) * -100

class LaguerrePPO(BaseStrategy):

    params = (
        ('short_gamma', 0.4),
        ('long_gamma', 0.8),
        ('pctile', 90),
        ('wrnpctile', 70),
        ('lkbT',200),
        ('lkbB',200),
        ('printlog', True),

    )

    def __init__(self):
        super().__init__()

        self.lag = Laguerre(self.datas[0])

    def buy_condition(self):
        print(self.lag.lines.ppoT[0], self.lag.lines.ppoB[0], self.lag.lines.pctRankT[0], self.lag.lines.pctRankB[0])
        # if self.lag.lines.pctRankB <= self.lag.lines.pctileB or (self.lag.lines.pctRankB <= self.lag.lines.wrnpctileB and self.lag.lines.pctRankB > self.lag.lines.pctileB):
        if self.lag.lines.pctRankB <= self.lag.lines.pctileB:

            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()

    def sell_condition(self):
        print(self.lag.lines.ppoT[0], self.lag.lines.ppoB[0], self.lag.lines.pctRankT[0], self.lag.lines.pctRankB[0])
        # if self.lag.lines.pctRankT >= self.params.pctile or (self.lag.lines.pctRankT >= self.params.wrnpctile and self.lag.lines.pctRankT < self.params.pctile):
        if self.lag.lines.pctRankT >= self.params.pctile:
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.order = self.sell()

class WaveTrend(BaseStrategy):

    params = (
        ('n1', 10),
        ('n2', 21),
        ('obLevel1', 60),
        ('obLevel2', 53),
        ('osLevel1',-60),
        ('osLevel2',-53),
        ('printlog', True),

    )

    def __init__(self):
        super().__init__()

        ap = (self.datas[0].high + self.datas[0].low + self.datas[0].close)/3
        esa = btind.ExponentialMovingAverage(ap, period = self.params.n1)
        d = btind.ExponentialMovingAverage(abs(ap - esa), period = self.params.n1)
        ci = (ap - esa) / (0.015 * d)
        self.tci = btind.ExponentialMovingAverage(ci, period = self.params.n2)

    def buy_condition(self):
        #print(self.tci)
        # if self.lag.lines.pctRankB <= self.lag.lines.pctileB or (self.lag.lines.pctRankB <= self.lag.lines.wrnpctileB and self.lag.lines.pctRankB > self.lag.lines.pctileB):
        if self.tci <= self.params.osLevel1:

            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()

    def sell_condition(self):
        if self.tci >= self.params.obLevel1:

            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.order = self.sell()

class Laguerre_Williams(BaseStrategy):
    params = (
        ('short_gamma', 0.4),
        ('long_gamma', 0.8),
        ('pctile', 90),
        ('wrnpctile', 70),
        ('lkbT',200),
        ('lkbB',200),
        ('printlog', False),
        ("pd", 22),  # LookBack Period Standard Deviation High
        ("bbl", 20),  # Bolinger Band Length
        ("mult", 2),  # Bollinger Band Standard Deviation Up
        ("lb", 50),
        ("ph", 0.85),
        ("pl", 1.01),
        ("ma1", 10),
        ('ma2', 30),
        ('printlog', False),
        ('n1', 10),
        ('n2', 21),
        ('obLevel1', 60),
        ('obLevel2', 53),
        ('osLevel1', -60),
        ('osLevel2', -53),
        ('printlog', False),
        ('ma1',5),
        ('ma2',13),
        ('printlog', False),
        ('rsi_period', 14),
        ('percent_period', 200),
        ('buy_limit1', 5),
        ('buy_limit2', 20),
        ('sell_limit1', 95),
        ('sell_limit2', 80),

    )

    def __init__(self):
        super().__init__()

        self.lag = Laguerre(self.datas[0],
                            short_gamma = self.params.short_gamma,
                            long_gamma=self.params.long_gamma,
                            pctile=self.params.pctile,
                            wrnpctile=self.params.wrnpctile,
                            lkbT=self.params.lkbT,
                            lkbB=self.params.lkbB,
                            )
        self.wvf = Vix_Fix_Indicator(self.datas[0],
                            pd = self.params.pd,
                            bbl=self.params.bbl,
                            mult=self.params.mult,
                            lb=self.params.lb,
                            ph=self.params.ph,
                            pl=self.params.pl,
                                     )

        ap = (self.datas[0].high + self.datas[0].low + self.datas[0].close)/3
        esa = btind.ExponentialMovingAverage(ap, period = self.params.n1)
        d = btind.ExponentialMovingAverage(abs(ap - esa), period = self.params.n1)
        ci = (ap - esa) / (0.015 * d)
        self.tci = btind.ExponentialMovingAverage(ci, period = self.params.n2)

        self.ma1 = btind.ZeroLagExponentialMovingAverage(self.datas[0], period = self.params.ma1)
        self.ma2 = btind.MovingAverageSimple(self.datas[0], period=self.params.ma2)

        self.rsi = btind.RelativeStrengthIndex(self.datas[0], period = self.params.rsi_period)
        self.prank= btind.PercentRank(self.rsi, period = self.params.percent_period) * 100

        self.pendingBuy = False
        self.pendingSell = False

    def buy_condition(self):
        if (self.wvf.lines.wvf > self.wvf.lines.bbands_top or self.wvf.lines.wvf > self.wvf.lines.range_high) and self.lag.lines.pctRankB <= self.lag.lines.pctileB and self.prank <= self.params.buy_limit1:
            self.log('PENDING BUY, %.2f %.2f %.2f' % (self.dataclose[0], self.lag.lines.pctRankB[0], self.prank[0]))
            self.pendingBuy = True

        elif(self.pendingBuy == True and self.lag.lines.pctRankB >= self.lag.lines.wrnpctileB and self.prank >= self.params.buy_limit2):
            self.pendingBuy = False
            self.log('BUY CREATE, %.2f %.2f %.2f' % (self.dataclose[0], self.lag.lines.pctRankB[0], self.prank[0]))
            self.order = self.buy()


    def sell_condition(self):
        #self.tci >= self.params.obLevel1
        if self.lag.lines.pctRankT >= self.params.pctile and self.prank >= self.params.sell_limit1:
            self.log('PENDING SELL, %.2f %.2f %.2f' % (self.dataclose[0], self.lag.lines.pctRankT[0], self.prank[0]))
            self.pendingSell = True

        elif self.pendingSell == True and self.lag.lines.pctRankT <= self.params.wrnpctile and self.prank <= self.params.sell_limit2:
            self.pendingSell = False
            self.log('SELL CREATE, %.2f %.2f %.2f' % (self.dataclose[0], self.lag.lines.pctRankT[0], self.prank[0]))
            self.order = self.sell()

class PercentRsi(BaseStrategy):
    params =(
        ('rsi_period', 14),
        ('percent_period', 100),
        ('buy_limit1', 1),
        ('buy_limit2', 20),
        ('sell_limit1', 99),
        ('sell_limit2', 80),
    )

    def __init__(self):
        super().__init__()
        self.rsi = btind.RSI(self.datas[0], period = self.params.rsi_period)
        self.prank= btind.PercentRank(self.rsi, period = self.params.percent_period) * 100
        self.pendingBuy = False
        self.pendingSell = False


    def buy_condition(self):
        if self.prank <= self.params.buy_limit1:
            self.pendingBuy = True

        elif self.pendingBuy == True and self.prank >= self.params.buy_limit2:
            self.pendingBuy = False
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()

    def sell_condition(self):
        if self.prank >= self.params.sell_limit1:
            self.pendingSell = True

        elif self.pendingSell == True and self.prank <= self.params.sell_limit2:
            self.pendingSell = False
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.order = self.sell()

class PercentMacdRsi(BaseStrategy):
    params =(
        ('rsi_period', 14),
        ('percent_period', 200),
        ('rsi_limit', 10),
        ('rsi_limit2', 30),
        ('macd_limit', 10),
        ('macd_limit2', 30),
        ('period1',12),
        ('period2', 26),
    )

    def __init__(self):
        super().__init__()
        self.rsi = btind.RelativeStrengthIndex(self.datas[0], period = self.params.rsi_period)
        self.prank_rsi= btind.PercentRank(self.rsi, period = self.params.percent_period) * 100

        self.macd = btind.MACD(self.datas[0], period_me1 = self.params.period1, period_me2 = self.params.period2)
        self.prank_macd = btind.PercentRank(self.macd, period=self.params.percent_period) * 100

        self.buy_limit_rsi = self.params.rsi_limit
        self.sell_limit_rsi = 100 - self.buy_limit_rsi

        self.buy_limit_rsi2 = self.params.rsi_limit2
        self.sell_limit_rsi2 = 100 - self.buy_limit_rsi2

        self.buy_limit_macd = self.params.macd_limit
        self.sell_limit_macd = 100 - self.buy_limit_macd

        self.buy_limit_macd2 = self.params.macd_limit2
        self.sell_limit_macd2 = 100 - self.buy_limit_macd2

        self.pendingBuy = False
        self.pendingSell = False


    def buy_condition(self):
        if self.prank_rsi <= self.buy_limit_rsi and self.prank_macd <= self.buy_limit_macd:
            self.pendingBuy = True

        elif self.pendingBuy == True and self.prank_rsi >= self.buy_limit_rsi2 and self.prank_macd >= self.buy_limit_macd2:
            self.pendingBuy = False
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()

    def sell_condition(self):
        if self.prank_rsi >= self.sell_limit_rsi and self.prank_macd >= self.sell_limit_macd:
            self.pendingSell = True

        elif self.pendingSell == True and self.prank_rsi <= self.sell_limit_rsi2 and self.prank_macd <= self.sell_limit_macd2:
            self.pendingSell = False
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.order = self.sell()

class PercentMA(BaseStrategy):
    params =(
        ('percent_period', 200),
        ('macd_limit', 10),
        ('macd_limit2', 30),
        ('period1',12),
        ('period2',26),
        ('movav', btind.ExponentialMovingAverage)
    )

    def __init__(self):
        super().__init__()
        self.ma1 = self.params.movav(self.datas[0], period = self.params.period1)
        self.ma2 = self.params.movav(self.datas[0], period = self.params.period2)
        self.diff = self.ma1 - self.ma2
        self.prank_diff = btind.PercentRank(self.diff, period=self.params.percent_period) * 100

        self.buy_limit_macd = self.params.macd_limit
        self.sell_limit_macd = 100 - self.buy_limit_macd

        self.buy_limit_macd2 = self.params.macd_limit2
        self.sell_limit_macd2 = 100 - self.buy_limit_macd2

        self.pendingBuy = False
        self.pendingSell = False


    def buy_condition(self):
        if self.prank_diff <= self.buy_limit_macd:
            self.pendingBuy = True

        elif self.pendingBuy == True and self.prank_diff >= self.buy_limit_macd2:
            self.pendingBuy = False
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()

    def sell_condition(self):
        if self.prank_diff >= self.sell_limit_macd:
            self.pendingSell = True

        elif self.pendingSell == True and self.prank_diff <= self.sell_limit_macd2:
            self.pendingSell = False
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.order = self.sell()

class MACD_gradient(BaseStrategy):

    params = (
        ('printlog', True),
        ('period_me1', 12),
        ('period_me2', 26),
    )

    def __init__(self):
        super().__init__()
        self.addminperiod(27)
        self.MACD = btind.MACD(self.datas[0], period_me1 = self.p.period_me1, period_me2 = self.p.period_me2)



    def buy_condition(self):
        if self.MACD[0] > self.MACD[-1] and self.MACD[-1] > self.MACD[-2]:
            self.log('BUY CREATE, %.2f %.2f %.2f %.2f' % (self.dataclose[0], self.MACD[0], self.MACD[-1], self.MACD[-2]))
            self.order = self.buy()

    def sell_condition(self):
        if self.MACD[0] < self.MACD[-1] and self.MACD[-1] < self.MACD[-2]:
            self.log('SELL CREATE, %.2f %.2f %.2f %.2f' % (self.dataclose[0], self.MACD[0], self.MACD[-1], self.MACD[-2]))
            self.order = self.sell()

class RSI(BaseStrategy):
    params = (
        ('rsi_period', 14),
        ('buy_limit',60),
        ('sell_limit', 40),
    )
    def __init__(self):
        super().__init__()
        self.rsi = btind.RSI(self.datas[0], period = self.p.rsi_period)

    def buy_condition(self):
        if(self.rsi > self.p.buy_limit):
            self.log('BUY CREATE, %.2f' % (self.dataclose[0]))
            self.order = self.buy()

    def sell_condition(self):
        if(self.rsi < self.p.sell_limit):
            self.log('SELL CREATE, %.2f' % (self.dataclose[0]))
            self.order = self.sell()

class LimitCrossStrategy(CrossStrategy):
    params = (
        ('atr_mult', 1),
    )

    def __init__(self):
        super().__init__()
        self.atr = btind.AverageTrueRange(self.datas[0])
        self.sellprice = 0

    def buy_condition(self):
        if self.ma1 > self.ma2:
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.sellprice = self.dataclose[0] - (self.p.atr_mult * self.atr[0])
            self.order = self.buy()

    def sell_condition(self):
        if self.ma1 < self.ma2 or self.datas[0].close < self.sellprice:
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.sellprice = 0
            self.order = self.sell()

class DIStrategy(BaseStrategy):
    params = (
        ("buy_plus", 25),
        ("di_period", 14),
        ("band_period", 20),
        ("devfactor", 2.0),
        ("kelch_mult", 1.5),
        ("ma1", 9),
        ("ma2", 20),
        ('printlog', False),

    )
    def __init__(self):
        super().__init__()
        self.di = btind.DirectionalMovement(self.datas[0], period = self.p.di_period)
        self.ma1 = btind.MovingAverageSimple(self.datas[0], period = self.p.ma1)
        self.ma2 = btind.MovingAverageSimple(self.datas[0], period=self.p.ma2)
        self.bbands = btind.BollingerBands(self.datas[0], period = self.p.band_period, devfactor = self.p.devfactor)
        self.ma = btind.MovingAverageSimple(self.datas[0], period=self.p.band_period)
        range = btind.TrueRange(self.datas[0])
        self.rangema = btind.MovingAverageSimple(range, period = self.p.band_period)


    def buy_condition(self):
        upperBB = self.bbands.lines.top[0]
        lowerBB = self.bbands.lines.bot[0]
        upperKC = self.ma + self.rangema * self.p.kelch_mult
        lowerKC = self.ma - self.rangema * self.p.kelch_mult
        self.log(str(upperBB) + " " + str(lowerBB) + " "  + str(upperKC) + " " + str(lowerKC))
        if self.di.lines.plusDI > self.di.lines.minusDI and self.di.lines.plusDI > self.p.buy_plus and upperBB > upperKC and lowerBB < lowerKC :
        # if self.ma1 > self.ma2 and upperBB > upperKC and lowerBB < lowerKC :
        # if self.ma1 > self.ma2 and self.di.lines.plusDI > self.di.lines.minusDI:
            # self.log(str(upperBB) + " " + str(lowerBB) + " " + str(upperKC) + " " + str(lowerKC))
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()

    def sell_condition(self):
        if self.di.lines.plusDI < self.di.lines.minusDI:
        # if self.ma1 < self.ma2 and self.di.lines.plusDI < self.di.lines.minusDI:
        # if self.ma1 < self.ma2:
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.order = self.sell()