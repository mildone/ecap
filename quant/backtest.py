#!/usr/bin/python
# _*_ coding: UTF-8 _*_
import datetime
import smtplib
from email.mime.text import MIMEText
import QUANTAXIS as QA
try:
    assert QA.__version__>='1.1.0'
except AssertionError:
    print('pip install QUANTAXIS >= 1.1.0 请升级QUANTAXIS后再运行此示例')
    import QUANTAXIS as QA
import re
import numpy as np
import quant.Util as uti
import matplotlib.pyplot as plt
read_dictionary = np.load('../liutong.npy',allow_pickle=True).item()
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtk
import mpl_finance as mpf
import pattern.TrendFin as tf
import pattern.Radar as ra
import pattern.TriNet as tn
import quant.Util as ut

class backtest(object):
    def __init__(self):
        super()

    def backtest(self):
        holdingperc = 2
        safeholding = 500
        print('*' * 100)
        print('loading data')
        # stockes = getStocklist()
        # stockes = ['600797','000977']
        # data = loadLocalData(stockes,'2018-03-15',end_date = '2019-09-11')
        print('*' * 100)
        print('init account')
        Account = QA.QA_Account(user_cookie='eric', portfolio_cookie='eric')
        Broker = QA.QA_BacktestBroker()
        Account.reset_assets(100000)
        Account.account_cookie = 'ECAP'
        # codelist=['600797','000977','601068','601069','000977']
        # 云计算，华为，5G概念
        codelist3 = QA.QA_fetch_stock_block_adv().get_block('云计算').code[:]
        codelist1 = QA.QA_fetch_stock_block_adv().get_block('华为概念').code[:]
        codelist2 = QA.QA_fetch_stock_block_adv().get_block('5G概念').code[:]
        # codelist4 = QA.QA_fetch_stock_block_adv().get_block('国产软件').code[:]
        codelist2.extend(codelist3)
        codelist2.extend(codelist1)

        #
        clist3 = QA.QA_fetch_stock_block_adv().get_block('阿里概念').code[:]
        clist1 = QA.QA_fetch_stock_block_adv().get_block('腾讯概念').code[:]
        clist2 = QA.QA_fetch_stock_block_adv().get_block('小米概念').code[:]
        # codelist4 = QA.QA_fetch_stock_block_adv().get_block('国产软件').code[:]
        clist3.extend(clist2)
        clist3.extend(clist1)

        # codelist1.extend(codelist4)

        cur = datetime.datetime.now()
        # endtime = str(cur.year) + '-' + str(cur.month) + '-' + str(cur.day)
        # endtime = '2020-06-01'
        endtime = '2019-01-07'
        cl = ['000977', '600745', '002889', '600340', '000895', '600019', '600028',
              '601857', '600585', '002415', '002475', '600031', '600276', '600009', '601318',
              '000333', '600031', '002384', '002241', '600703', '000776', '600897', '600085']
        codelist2.extend(cl)
        codelist = list(set(codelist2))
        data = uti.loadLocalData(cl, '2018-01-01', endtime)
        #data = uti.loadLocalData(codelist, '2019-01-01', endtime)
        data = data.to_qfq()
        print('*' * 100)
        print('prepare data for back test')
        # no qfq, 15/10, with qfq,
        # ind = data.add_func(trendSingleNew)
        # around 1/6
        # ind = data.add_func(trendTurn)
        # 1.7/6
        # ind = data.add_func(doubleAvgDay)
        # wired with sudden draw back
        # ind = data.add_func(trendBreak)
        # with cl only 7/10
        # with codelist
        # ind = data.add_func(doubleAvgminv2)
        # 45/10 with a50, that's -1
        # ind = data.add_func(doubleAvgmin)

        # ind = data.add_func(triNetv3)

        # 7/10
        # ind = data.add_func(EMA_MA)

        # 6/10
        #ind = data.add_func(tf.TrendFinder)
        #ind = data.add_func(ra.radarv2)
        ind = data.add_func(ut.triNetv2)
        #ind = data.add_func(tf.TrendFinM)

        # ind = data.add_func(bollStrategy)
        # ind = data.add_func(nineTurn)
        # ind=data.add_func(MACACalculate)
        # ind = data.add_func(EMAOP)
        # cur = datetime.datetime.now()
        # endtime = str(cur.year) + '-' + str(cur.month) + '-' + str(cur.day)
        data_forbacktest = data.select_time('2019-01-01', endtime)
        deal = {}
        for items in data_forbacktest.panel_gen:
            for item in items.security_gen:

                daily_ind = ind.loc[item.index]
                if (daily_ind.single.iloc[0] == 1):
                    open = QA.QA_fetch_stock_day_adv(item.code[0], item.date[0], item.date[0]).data.open[0] if np.isnan(
                        item.open[0]) else item.open[0]
                    if ((Account.cash_available - safeholding) / (holdingperc * item.close[0]) > 500):
                        print('code {}, time {} amout {}, toward {}, price {} order_model {} amount_model {}'.format(
                            item.code[0], item.date[0],
                            int((Account.cash_available - safeholding) / (100 * open)) * 100,
                            QA.ORDER_DIRECTION.BUY, open, QA.ORDER_MODEL.LIMIT, QA.AMOUNT_MODEL.BY_AMOUNT))
                        order = Account.send_order(
                            code=item.code[0],
                            time=item.date[0],
                            amount=int(
                                (Account.cash_available - safeholding) / (holdingperc * item.open[0] * 100)) * 100,
                            towards=QA.ORDER_DIRECTION.BUY,
                            price=item.close[0],
                            order_model=QA.ORDER_MODEL.LIMIT,
                            amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
                        )
                        # deal[item.code[0]]= int((Account.cash_available - safeholding) / (holdingperc * open*100))*100



                    else:
                        order = None
                    # start to trade
                    if order:
                        # print('sending order '+'*'*60)
                        Broker.receive_order(QA.QA_Event(order=order, market_data=item))
                        # print('got here --------------------')
                        trade_mes = Broker.query_orders(Account.account_cookie, 'filled')
                        # print(trade_mes)
                        # print('got here 2 -------')
                        res = trade_mes.loc[order.account_cookie, order.realorder_id]
                        # print('got here 3 -------- ')
                        order.trade(res.trade_id, res.trade_price, res.trade_amount, res.trade_time)
                        # print('*' * 100)
                        print(str(item.date[0]) + " buy " + item.code[0])

                elif (daily_ind.single.iloc[0] == 3):
                    # close = QA.QA_fetch_stock_day_adv(item.code[0], item.date[0], item.date[0]).data.close[0] if np.isnan(
                    # daily_ind.close.iloc[0]) else item.close[0]
                    if Account.sell_available.get(item.code[0], 0) > 0:
                        print('>' * 100)
                        print(str(item.date[0]) + " sell " + item.code[0])
                        order = Account.send_order(
                            code=item.code[0],
                            time=item.date[0],
                            amount=Account.sell_available.get(item.code[0], 0),
                            # amount = deal.get(item.code[0]),
                            towards=QA.ORDER_DIRECTION.SELL,
                            price=item.close[0],
                            order_model=QA.ORDER_MODEL.LIMIT,
                            amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
                        )
                        if order:
                            Broker.receive_order(QA.QA_Event(order=order, market_data=item))
                            trade_mes = Broker.query_orders(Account.account_cookie, 'filled')
                            res = trade_mes.loc[order.account_cookie, order.realorder_id]
                            order.trade(res.trade_id, res.trade_price, res.trade_amount, res.trade_time)
            Account.settle()

        print('*' * 100)
        print('analyse account profit')
        Risk = QA.QA_Risk(Account)
        Risk.assets.plot()
        print(Risk.profit_construct)
        print('winning ratio is {}'.format(uti.winRatio(Account)))


if __name__=="__main__":
    bt = backtest()
    bt.backtest()