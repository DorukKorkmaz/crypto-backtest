from datetime import datetime
import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicators as btind
import numpy as np
from backtesting import Strategy


#list of coins
coins = ['ETHBTC', 'LTCBTC', 'BNBBTC', 'NEOBTC', 'BCCBTC', 'GASBTC', 'HSRBTC', 'MCOBTC', 'WTCBTC', 'LRCBTC',
         'QTUMBTC', 'YOYOBTC', 'OMGBTC', 'ZRXBTC', 'STRATBTC', 'SNGLSBTC', 'BQXBTC', 'KNCBTC', 'FUNBTC', 'SNMBTC',
         'IOTABTC', 'LINKBTC', 'XVGBTC', 'CTRBTC', 'SALTBTC', 'MDABTC', 'MTLBTC', 'SUBBTC', 'EOSBTC', 'SNTBTC',
         'ETCBTC', 'MTHBTC', 'ENGBTC', 'DNTBTC', 'ZECBTC', 'BNTBTC', 'ASTBTC', 'DASHBTC', 'OAXBTC', 'ICNBTC',
         'BTGBTC', 'XRPBTC', 'EVXBTC', 'REQBTC', 'VIBBTC', 'TRXBTC', 'POWRBTC', 'ARKBTC']

max = 0

for ma1 in range(5,25,2):
    for ma2 in range(8,50,3):
        for atr in [x * 0.1 for x in range(0,11,5)]:
                if(ma1 < ma2):
                    default_value = 0
                    strategy_value = 0
                    for coin in coins:
                        data = btfeeds.GenericCSVData(
                            dataname="/Users/dorukkorkmaz/Documents/GitHub/coinbot/market_data/" + coin + "/" +"1h?09-01-2017?01-01-2018.txt",
                            datetime=0,
                            open=1,
                            high=2,
                            low=3,
                            close=4,
                            volume=5,
                            openinterest=-1,
                            dtformat='%Y-%m-%d %H:%M:%S',
                            timeframe=bt.TimeFrame.Ticks,
                            nullvalue=0.0
                        )
                        # print(data.params.dataname)
                        #
                        # default_cerebro = bt.Cerebro()
                        # default_cerebro.addstrategy(Strategy.Default)
                        # default_cerebro.broker.setcash(1000000.0)
                        # default_cerebro.adddata(data)
                        # default_cerebro.addsizer(bt.sizers.PercentSizer, percents=99)
                        # default_cerebro.broker.setcommission(commission=0.002)
                        # default_cerebro.run()
                        # default_value += default_cerebro.broker.getvalue()

                        cerebro = bt.Cerebro()
                        cerebro.addstrategy(
                            Strategy.AtrCrossStrategy,
                            ma1_period = ma1,
                            ma2_period = ma2,
                            ma1_type = btind.SmoothedMovingAverage,
                            ma2_type = btind.MovingAverageSimple,
                            atr = atr
                        )

                        cerebro.broker.setcash(1000000.0)
                        cerebro.adddata(data)
                        cerebro.addsizer(bt.sizers.PercentSizer, percents=99)
                        cerebro.broker.setcommission(commission=0.001)
                        value = cerebro.run()
                        strategy_value += cerebro.broker.getvalue()

                    if strategy_value > max:
                        max = strategy_value
                        print(default_value)
                        print(ma1, ma2, atr, "Simple Moving Average Crossover", strategy_value)
                        print(ma1, strategy_value)

