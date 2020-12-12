import datetime
import smtplib
from email.mime.text import MIMEText
import QUANTAXIS as QA
import dateutil
import sys

try:
    assert QA.__version__ >= '1.1.0'
except AssertionError:
    print('pip install QUANTAXIS >= 1.1.0 请升级QUANTAXIS后再运行此示例')
    import QUANTAXIS as QA
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import abupy
from abupy import ABuRegUtil
from concurrent.futures import ThreadPoolExecutor
from functools import reduce
import warnings
import re

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtk
import mpl_finance as mpf
index = 'datetime'
formate = '%Y-%m-%dT%H:%M:%S'
dayindex = 'date'
dayformate = '%Y-%m-%d'
startday='2018-01-01'

pw=0.47  #backtest win ratio
rw=1.15 #sell when got 15% increase
rl=0.97 #end if loss 0.03 of holdings

def loadLocalData(stocks, start_date='2018-03-15', end_date='2019-09-07'):
    """
    data() as pdDataFrame
    stocks could be list of all the stock or some. if you pass single one e.g. 000001 it will get one only
    to get dedicated stock, using below method, and notice stockp() will be dataFrame
    stockp = data.select_code(stock)


    """
    QA.QA_util_log_info('load data from local DB')
    data = QA.QA_fetch_stock_day_adv(stocks, start_date, end_date)
    return data

def getWeekDate(daytime):
    #daytime will be pandas datetime
    #return Timestamp('2020-05-11 00:00:00')
    return daytime+dateutil.relativedelta.relativedelta(days=(6-daytime.dayofweek))


def winRatio(Account):
    #input as Account after backtest
    #output is wining ratio of all the trade
    his = Account.history_table
    vest = {}
    win = 0
    loss = 0
    for i in range(his.shape[0]):
        if his.code[i] in vest:
            if (his.price[i] > vest[his.code[i]]):
                win += 1
            elif (his.price[i] < vest[his.code[i]]):
                loss += 1
            del vest[his.code[i]]
        else:
            vest[his.code[i]] = his.price[i]
    print('win {}, loss {}'.format(win, loss))
    return win/(win + loss)

def trendWeekMinv152060(sample,short=20, long=60, freq='15min'):
    #test summary
    #5-10 with 21/10
    #5-15 with 23/10
    #5-20 with 19/10
    #20-60 24/10
    #to get Week and 60 minutes syntony together
    #get week trend
    #A50 64% 30 5 15 12/10
    #
    #60 76, 30 79, 30 74 more
    #15 min is the best for now, with 11/10 (5-10 11, 5-15 10 5-20 )
    import quant.weekTrend as wt
    print('{} deal with {}'.format(sys._getframe().f_code.co_name, sample.index.get_level_values('code')[-1]))
    print('*'*100)

    sample.fillna(method='ffill',inplace=True)
    wstart = '2010-01-01'
    code = sample.index.get_level_values('code')[-1]
    wend = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    temp = QA.QA_fetch_stock_day_adv(code,wstart,wend).data
    wd = wt.wds(temp)
    wd = wt.TrendDetect(wd)

    start = sample.index.get_level_values(dayindex)[0].strftime(dayformate)
    end = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    mindata = QA.QA_fetch_stock_min_adv(sample.index.get_level_values('code')[0], start, end, frequence= freq)
    ms = mindata.data
    # print(sample)
    ms['short'] = QA.EMA(ms.close, short)
    ms['long'] = QA.EMA(ms.close, long)
    CROSS_5 = QA.CROSS(ms.short, ms.long)
    CROSS_15 = QA.CROSS(ms.long, ms.short)

    C15 = np.where(CROSS_15 == 1, 3, 0)
    m = np.where(CROSS_5 == 1, 1, C15)
    # single = m[:-1].tolist()
    # single.insert(0, 0)
    ms['single'] = m.tolist()
    sig = [0]
    if(freq=='60min'):
        anchor = -2
    elif(freq=='30min'):
        anchor = -4
    elif(freq=='15min'):
        anchor = -8
    for i in range(1, len(sample)):
        dtime = sample.index.get_level_values(dayindex)[i]
        wtime = getWeekDate(dtime)
        windex = wd[wd.date == wtime.strftime(dayformate)].index[0]
        # here use index to get value interested, here we take change of MACDBlock to get the short trend in week level
        direction = wd.loc[windex].CS
        trendv = wd.loc[windex].SM
        temp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[i].strftime(dayformate)][:anchor]
        tmp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[i-1].strftime(dayformate)][anchor:]
        sing = temp.single.sum()+tmp.single.sum()
        if(direction>0 and trendv >0 and sing==1):
            sig.append(1)
        elif(direction<0 and sing==3):
            sig.append(sing)
        else:
            sig.append(0)

    try:
        #sample['single'] = [0]+sig[:-1]
        sample['single']=sig

    except:
        print('error with {}'.format(sample.index.get_level_values('code')[0]))
        sample['single'] = 0


    return sample

def backtest152060( holdingperc = 3):
    #holdingperc = 3
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
    #endtime = '2020-06-01'
    endtime = '2020-07-15'
    cl = ['000977', '600745','002889','600340','000895','600019','600028',
          '601857','600585','002415','002475','600031','600276','600009','601318',
          '000333','600031','002384','002241','600703','000776','600897','600085']
    c1 = ['000977', '600745']
    codelist2.extend(cl)
    codelist = list(set(codelist2))
    # data = loadLocalData(codelist, '2018-01-01', endtime)
    data = loadLocalData(cl, '2019-01-01', endtime)
    data = data.to_qfq()
    print('*' * 100)
    print('prepare data for back test')
    #no qfq, 15/10, with qfq,
    #ind = data.add_func(trendSingleNew)
    # around 1/6
    #ind = data.add_func(trendTurn)
    # 1.7/6
    #ind = data.add_func(doubleAvgDay)
    # wired with sudden draw back
    #ind = data.add_func(trendBreak)
    #with cl only 7/10
    #with codelist
    #ind = data.add_func(doubleAvgminv2)
    #45/10 with a50, that's -1
    #ind = data.add_func(doubleAvgmin)
    #triNetV2 a50 10/10
    #ind = data.add_func(triNetv2)

    #18/10,currently this is job50 taking now
    #ind = data.add_func(trendWeekMinv2)
    #21/10
    ind = data.add_func(trendWeekMinv152060)

    #7/10
    #ind = data.add_func(EMA_MA)


    #6/10
    #ind = data.add_func(TrendFinder)

    #ind = data.add_func(bollStrategy)
    # ind = data.add_func(nineTurn)
    #ind=data.add_func(MACACalculate)
    #ind = data.add_func(EMAOP)
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
                        item.code[0], item.date[0], int((Account.cash_available - safeholding) / (100 * open)) * 100,
                        QA.ORDER_DIRECTION.BUY, open, QA.ORDER_MODEL.LIMIT, QA.AMOUNT_MODEL.BY_AMOUNT))
                    order = Account.send_order(
                        code=item.code[0],
                        time=item.date[0],
                        amount=int((Account.cash_available - safeholding) / (holdingperc * item.open[0] *100))*100,
                        towards=QA.ORDER_DIRECTION.BUY,
                        price=item.close[0],
                        order_model=QA.ORDER_MODEL.LIMIT,
                        amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
                    )
                    #deal[item.code[0]]= int((Account.cash_available - safeholding) / (holdingperc * open*100))*100



                else:
                    order = None
                #start to trade
                if order:
                    # print('sending order '+'*'*60)
                    Broker.receive_order(QA.QA_Event(order=order, market_data=item))
                    #print('got here --------------------')
                    trade_mes = Broker.query_orders(Account.account_cookie, 'filled')
                    #print(trade_mes)
                   # print('got here 2 -------')
                    res = trade_mes.loc[order.account_cookie, order.realorder_id]
                    #print('got here 3 -------- ')
                    order.trade(res.trade_id, res.trade_price, res.trade_amount, res.trade_time)
                   #print('*' * 100)
                    print(str(item.date[0]) + " buy " + item.code[0])

            elif (daily_ind.single.iloc[0] == 3):
                #close = QA.QA_fetch_stock_day_adv(item.code[0], item.date[0], item.date[0]).data.close[0] if np.isnan(
                    #daily_ind.close.iloc[0]) else item.close[0]
                if Account.sell_available.get(item.code[0], 0) > 0:
                    print('>' * 100)
                    print(str(item.date[0]) + " sell " + item.code[0])
                    order = Account.send_order(
                        code=item.code[0],
                        time=item.date[0],
                        amount=Account.sell_available.get(item.code[0], 0),
                        #amount = deal.get(item.code[0]),
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
    print('analyse account profit for ' +sys._getframe().f_code.co_name)
    Risk = QA.QA_Risk(Account)
    Risk.assets.plot()
    print('{} with risk {} '.format( sys._getframe().f_code.co_name,Risk.profit_construct))
    print(' 152060 winning ratio is {}'.format( winRatio(Account)))




def trendWeekMinv15515(sample,short=5, long=15, freq='15min'):
    #test summary
    #5-10 with 21/10
    #5-15 with 23/10
    #5-20 with 19/10
    #20-60 24/10
    #to get Week and 60 minutes syntony together
    #get week trend
    #A50 64% 30 5 15 12/10
    #
    #60 76, 30 79, 30 74 more
    #15 min is the best for now, with 11/10 (5-10 11, 5-15 10 5-20 )
    import quant.weekTrend as wt
    print('{} deal with {}'.format(sys._getframe().f_code.co_name,sample.index.get_level_values('code')[-1]))
    print('*'*100)

    sample.fillna(method='ffill',inplace=True)
    wstart = '2010-01-01'
    code = sample.index.get_level_values('code')[-1]
    wend = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    temp = QA.QA_fetch_stock_day_adv(code,wstart,wend).data
    wd = wt.wds(temp)
    wd = wt.TrendDetect(wd)

    start = sample.index.get_level_values(dayindex)[0].strftime(dayformate)
    end = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    mindata = QA.QA_fetch_stock_min_adv(sample.index.get_level_values('code')[0], start, end, frequence= freq)
    ms = mindata.data
    # print(sample)
    ms['short'] = QA.EMA(ms.close, short)
    ms['long'] = QA.EMA(ms.close, long)
    CROSS_5 = QA.CROSS(ms.short, ms.long)
    CROSS_15 = QA.CROSS(ms.long, ms.short)

    C15 = np.where(CROSS_15 == 1, 3, 0)
    m = np.where(CROSS_5 == 1, 1, C15)
    # single = m[:-1].tolist()
    # single.insert(0, 0)
    ms['single'] = m.tolist()
    sig = [0]
    if(freq=='60min'):
        anchor = -2
    elif(freq=='30min'):
        anchor = -4
    elif(freq=='15min'):
        anchor = -8
    for i in range(1, len(sample)):
        dtime = sample.index.get_level_values(dayindex)[i]
        wtime = getWeekDate(dtime)
        windex = wd[wd.date == wtime.strftime(dayformate)].index[0]
        # here use index to get value interested, here we take change of MACDBlock to get the short trend in week level
        direction = wd.loc[windex].CS
        trendv = wd.loc[windex].SM
        temp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[i].strftime(dayformate)][:anchor]
        tmp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[i-1].strftime(dayformate)][anchor:]
        sing = temp.single.sum()+tmp.single.sum()
        if(direction>0 and trendv >0 and sing==1):
            sig.append(1)
        elif(direction<0 and sing==3):
            sig.append(sing)
        else:
            sig.append(0)

    try:
        #sample['single'] = [0]+sig[:-1]
        sample['single']=sig

    except:
        print('error with {}'.format(sample.index.get_level_values('code')[0]))
        sample['single'] = 0


    return sample

def backtest15515(holdingperc = 3):
    #holdingperc = 3
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
    #codelist2.extend(codelist3)
    #codelist2.extend(codelist1)

    #
    clist3 = QA.QA_fetch_stock_block_adv().get_block('阿里概念').code[:]
    clist1 = QA.QA_fetch_stock_block_adv().get_block('腾讯概念').code[:]
    clist2 = QA.QA_fetch_stock_block_adv().get_block('小米概念').code[:]
    # codelist4 = QA.QA_fetch_stock_block_adv().get_block('国产软件').code[:]
    #clist3.extend(clist2)
    #clist3.extend(clist1)

    # codelist1.extend(codelist4)



    cur = datetime.datetime.now()
    # endtime = str(cur.year) + '-' + str(cur.month) + '-' + str(cur.day)
    #endtime = '2020-06-01'
    endtime = '2020-07-15'
    cl = ['000977', '600745','002889','600340','000895','600019','600028',
          '601857','600585','002415','002475','600031','600276','600009','601318',
          '000333','600031','002384','002241','600703','000776','600897','600085']
    c1 = ['000977','600745']
    codelist3.extend(cl)
    codelist = list(set(codelist3))
    # data = loadLocalData(codelist, '2018-01-01', endtime)
    data = loadLocalData(cl, '2019-01-01', endtime)
    data = data.to_qfq()
    print('*' * 100)
    print('prepare data for back test')
    #no qfq, 15/10, with qfq,
    #ind = data.add_func(trendSingleNew)
    # around 1/6
    #ind = data.add_func(trendTurn)
    # 1.7/6
    #ind = data.add_func(doubleAvgDay)
    # wired with sudden draw back
    #ind = data.add_func(trendBreak)
    #with cl only 7/10
    #with codelist
    #ind = data.add_func(doubleAvgminv2)
    #45/10 with a50, that's -1
    #ind = data.add_func(doubleAvgmin)
    #triNetV2 a50 10/10
    #ind = data.add_func(triNetv2)

    #18/10,currently this is job50 taking now
    #ind = data.add_func(trendWeekMinv2)
    #21/10
    ind = data.add_func(trendWeekMinv15515)

    #7/10
    #ind = data.add_func(EMA_MA)


    #6/10
    #ind = data.add_func(TrendFinder)

    #ind = data.add_func(bollStrategy)
    # ind = data.add_func(nineTurn)
    #ind=data.add_func(MACACalculate)
    #ind = data.add_func(EMAOP)
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
                        item.code[0], item.date[0], int((Account.cash_available - safeholding) / (100 * open)) * 100,
                        QA.ORDER_DIRECTION.BUY, open, QA.ORDER_MODEL.LIMIT, QA.AMOUNT_MODEL.BY_AMOUNT))
                    order = Account.send_order(
                        code=item.code[0],
                        time=item.date[0],
                        amount=int((Account.cash_available - safeholding) / (holdingperc * item.open[0] *100))*100,
                        towards=QA.ORDER_DIRECTION.BUY,
                        price=item.close[0],
                        order_model=QA.ORDER_MODEL.LIMIT,
                        amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
                    )
                    #deal[item.code[0]]= int((Account.cash_available - safeholding) / (holdingperc * open*100))*100



                else:
                    order = None
                #start to trade
                if order:
                    # print('sending order '+'*'*60)
                    Broker.receive_order(QA.QA_Event(order=order, market_data=item))
                    #print('got here --------------------')
                    trade_mes = Broker.query_orders(Account.account_cookie, 'filled')
                    #print(trade_mes)
                   # print('got here 2 -------')
                    res = trade_mes.loc[order.account_cookie, order.realorder_id]
                    #print('got here 3 -------- ')
                    order.trade(res.trade_id, res.trade_price, res.trade_amount, res.trade_time)
                   #print('*' * 100)
                    print(str(item.date[0]) + " buy " + item.code[0])

            elif (daily_ind.single.iloc[0] == 3):
                #close = QA.QA_fetch_stock_day_adv(item.code[0], item.date[0], item.date[0]).data.close[0] if np.isnan(
                    #daily_ind.close.iloc[0]) else item.close[0]
                if Account.sell_available.get(item.code[0], 0) > 0:
                    print('>' * 100)
                    print(str(item.date[0]) + " sell " + item.code[0])
                    order = Account.send_order(
                        code=item.code[0],
                        time=item.date[0],
                        amount=Account.sell_available.get(item.code[0], 0),
                        #amount = deal.get(item.code[0]),
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
    print('analyse account profit for ' +sys._getframe().f_code.co_name)
    Risk = QA.QA_Risk(Account)
    Risk.assets.plot()
    print('{} with risk {} '.format( sys._getframe().f_code.co_name,Risk.profit_construct))
    print('{} winning ratio is {}'.format(sys._getframe().f_code.co_name,winRatio(Account)))


def trendWeekMinv15510(sample,short=5, long=10, freq='15min'):
    #test summary
    #5-10 with 21/10
    #5-15 with 23/10
    #5-20 with 19/10
    #20-60 24/10
    #to get Week and 60 minutes syntony together
    #get week trend
    #A50 64% 30 5 15 12/10
    #
    #60 76, 30 79, 30 74 more
    #15 min is the best for now, with 11/10 (5-10 11, 5-15 10 5-20 )
    import quant.weekTrend as wt
    print('{} deal with {}'.format(sys._getframe().f_code.co_name,sample.index.get_level_values('code')[-1]))
    print('*'*100)

    sample.fillna(method='ffill',inplace=True)
    wstart = '2010-01-01'
    code = sample.index.get_level_values('code')[-1]
    wend = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    temp = QA.QA_fetch_stock_day_adv(code,wstart,wend).data
    wd = wt.wds(temp)
    wd = wt.TrendDetect(wd)

    start = sample.index.get_level_values(dayindex)[0].strftime(dayformate)
    end = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    mindata = QA.QA_fetch_stock_min_adv(sample.index.get_level_values('code')[0], start, end, frequence= freq)
    ms = mindata.data
    # print(sample)
    ms['short'] = QA.EMA(ms.close, short)
    ms['long'] = QA.EMA(ms.close, long)
    CROSS_5 = QA.CROSS(ms.short, ms.long)
    CROSS_15 = QA.CROSS(ms.long, ms.short)

    C15 = np.where(CROSS_15 == 1, 3, 0)
    m = np.where(CROSS_5 == 1, 1, C15)
    # single = m[:-1].tolist()
    # single.insert(0, 0)
    ms['single'] = m.tolist()
    sig = [0]
    if(freq=='60min'):
        anchor = -2
    elif(freq=='30min'):
        anchor = -4
    elif(freq=='15min'):
        anchor = -8
    for i in range(1, len(sample)):
        dtime = sample.index.get_level_values(dayindex)[i]
        wtime = getWeekDate(dtime)
        windex = wd[wd.date == wtime.strftime(dayformate)].index[0]
        # here use index to get value interested, here we take change of MACDBlock to get the short trend in week level
        direction = wd.loc[windex].CS
        trendv = wd.loc[windex].SM
        temp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[i].strftime(dayformate)][:anchor]
        tmp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[i-1].strftime(dayformate)][anchor:]
        sing = temp.single.sum()+tmp.single.sum()
        if(direction>0 and trendv >0 and sing==1):
            sig.append(1)
        elif(direction<0 and sing==3):
            sig.append(sing)
        else:
            sig.append(0)

    try:
        #sample['single'] = [0]+sig[:-1]
        sample['single']=sig

    except:
        print('error with {}'.format(sample.index.get_level_values('code')[0]))
        sample['single'] = 0


    return sample

def backtest15510(holdingperc = 3):
    #holdingperc = 3
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
    #endtime = '2020-06-01'
    endtime = '2020-07-15'
    cl = ['000977', '600745','002889','600340','000895','600019','600028',
          '601857','600585','002415','002475','600031','600276','600009','601318',
          '000333','600031','002384','002241','600703','000776','600897','600085']
    codelist2.extend(cl)
    codelist = list(set(codelist2))
    # data = loadLocalData(cl, '2018-01-01', endtime)
    data = loadLocalData(cl, '2018-01-01', endtime)
    data = data.to_qfq()
    print('*' * 100)
    print('prepare data for back test')
    #no qfq, 15/10, with qfq,
    #ind = data.add_func(trendSingleNew)
    # around 1/6
    #ind = data.add_func(trendTurn)
    # 1.7/6
    #ind = data.add_func(doubleAvgDay)
    # wired with sudden draw back
    #ind = data.add_func(trendBreak)
    #with cl only 7/10
    #with codelist
    #ind = data.add_func(doubleAvgminv2)
    #45/10 with a50, that's -1
    #ind = data.add_func(doubleAvgmin)
    #triNetV2 a50 10/10
    #ind = data.add_func(triNetv2)

    #18/10,currently this is job50 taking now
    #ind = data.add_func(trendWeekMinv2)
    #21/10
    ind = data.add_func(trendWeekMinv15510)

    #7/10
    #ind = data.add_func(EMA_MA)


    #6/10
    #ind = data.add_func(TrendFinder)

    #ind = data.add_func(bollStrategy)
    # ind = data.add_func(nineTurn)
    #ind=data.add_func(MACACalculate)
    #ind = data.add_func(EMAOP)
    # cur = datetime.datetime.now()
    # endtime = str(cur.year) + '-' + str(cur.month) + '-' + str(cur.day)
    data_forbacktest = data.select_time('2018-01-01', endtime)
    deal = {}
    for items in data_forbacktest.panel_gen:
        for item in items.security_gen:

            daily_ind = ind.loc[item.index]
            if (daily_ind.single.iloc[0] == 1):
                open = QA.QA_fetch_stock_day_adv(item.code[0], item.date[0], item.date[0]).data.open[0] if np.isnan(
                    item.open[0]) else item.open[0]
                if ((Account.cash_available - safeholding) / (holdingperc * item.close[0]) > 500):
                    print('code {}, time {} amout {}, toward {}, price {} order_model {} amount_model {}'.format(
                        item.code[0], item.date[0], int((Account.cash_available - safeholding) / (100 * open)) * 100,
                        QA.ORDER_DIRECTION.BUY, open, QA.ORDER_MODEL.LIMIT, QA.AMOUNT_MODEL.BY_AMOUNT))
                    order = Account.send_order(
                        code=item.code[0],
                        time=item.date[0],
                        amount=int((Account.cash_available - safeholding) / (holdingperc * item.open[0] *100))*100,
                        towards=QA.ORDER_DIRECTION.BUY,
                        price=item.close[0],
                        order_model=QA.ORDER_MODEL.LIMIT,
                        amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
                    )
                    #deal[item.code[0]]= int((Account.cash_available - safeholding) / (holdingperc * open*100))*100



                else:
                    order = None
                #start to trade
                if order:
                    # print('sending order '+'*'*60)
                    Broker.receive_order(QA.QA_Event(order=order, market_data=item))
                    #print('got here --------------------')
                    trade_mes = Broker.query_orders(Account.account_cookie, 'filled')
                    #print(trade_mes)
                   # print('got here 2 -------')
                    res = trade_mes.loc[order.account_cookie, order.realorder_id]
                    #print('got here 3 -------- ')
                    order.trade(res.trade_id, res.trade_price, res.trade_amount, res.trade_time)
                   #print('*' * 100)
                    print(str(item.date[0]) + " buy " + item.code[0])

            elif (daily_ind.single.iloc[0] == 3):
                #close = QA.QA_fetch_stock_day_adv(item.code[0], item.date[0], item.date[0]).data.close[0] if np.isnan(
                    #daily_ind.close.iloc[0]) else item.close[0]
                if Account.sell_available.get(item.code[0], 0) > 0:
                    print('>' * 100)
                    print(str(item.date[0]) + " sell " + item.code[0])
                    order = Account.send_order(
                        code=item.code[0],
                        time=item.date[0],
                        amount=Account.sell_available.get(item.code[0], 0),
                        #amount = deal.get(item.code[0]),
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
    print('analyse account profit for ' +sys._getframe().f_code.co_name)
    Risk = QA.QA_Risk(Account)
    Risk.assets.plot()
    print('{} with risk {} '.format(sys._getframe().f_code.co_name,Risk.profit_construct))
    print('winning ratio is {}'.format(winRatio(Account)))




def trendWeekMinv15520(sample,short=5, long=20, freq='15min'):
    #test summary
    #5-10 with 21/10
    #5-15 with 23/10
    #5-20 with 19/10
    #20-60 24/10
    #to get Week and 60 minutes syntony together
    #get week trend
    #A50 64% 30 5 15 12/10
    #
    #60 76, 30 79, 30 74 more
    #15 min is the best for now, with 11/10 (5-10 11, 5-15 10 5-20 )
    import quant.weekTrend as wt
    print('{} deal with {}'.format(sys._getframe().f_code.co_name,sample.index.get_level_values('code')[-1]))
    print('*'*100)

    sample.fillna(method='ffill',inplace=True)
    wstart = '2010-01-01'
    code = sample.index.get_level_values('code')[-1]
    wend = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    temp = QA.QA_fetch_stock_day_adv(code,wstart,wend).data
    wd = wt.wds(temp)
    wd = wt.TrendDetect(wd)

    start = sample.index.get_level_values(dayindex)[0].strftime(dayformate)
    end = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    mindata = QA.QA_fetch_stock_min_adv(sample.index.get_level_values('code')[0], start, end, frequence= freq)
    ms = mindata.data
    # print(sample)
    ms['short'] = QA.EMA(ms.close, short)
    ms['long'] = QA.EMA(ms.close, long)
    CROSS_5 = QA.CROSS(ms.short, ms.long)
    CROSS_15 = QA.CROSS(ms.long, ms.short)

    C15 = np.where(CROSS_15 == 1, 3, 0)
    m = np.where(CROSS_5 == 1, 1, C15)
    # single = m[:-1].tolist()
    # single.insert(0, 0)
    ms['single'] = m.tolist()
    sig = [0]
    if(freq=='60min'):
        anchor = -2
    elif(freq=='30min'):
        anchor = -4
    elif(freq=='15min'):
        anchor = -8
    for i in range(1, len(sample)):
        dtime = sample.index.get_level_values(dayindex)[i]
        wtime = getWeekDate(dtime)
        windex = wd[wd.date == wtime.strftime(dayformate)].index[0]
        # here use index to get value interested, here we take change of MACDBlock to get the short trend in week level
        direction = wd.loc[windex].CS
        trendv = wd.loc[windex].SM
        temp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[i].strftime(dayformate)][:anchor]
        tmp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[i-1].strftime(dayformate)][anchor:]
        sing = temp.single.sum()+tmp.single.sum()
        if(direction>0 and trendv >0 and sing==1):
            sig.append(1)
        elif(direction<0 and sing==3):
            sig.append(sing)
        else:
            sig.append(0)

    try:
        #sample['single'] = [0]+sig[:-1]
        sample['single']=sig

    except:
        print('error with {}'.format(sample.index.get_level_values('code')[0]))
        sample['single'] = 0


    return sample

def backtest15520(holdingperc = 3):
    #holdingperc = 3
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
    #endtime = '2020-06-01'
    endtime = '2020-07-15'
    cl = ['000977', '600745','002889','600340','000895','600019','600028',
          '601857','600585','002415','002475','600031','600276','600009','601318',
          '000333','600031','002384','002241','600703','000776','600897','600085']
    codelist2.extend(cl)
    codelist = list(set(codelist2))
    # data = loadLocalData(cl, '2018-01-01', endtime)
    data = loadLocalData(cl, '2019-01-01', endtime)
    data = data.to_qfq()
    print('*' * 100)
    print('prepare data for back test')
    #no qfq, 15/10, with qfq,
    #ind = data.add_func(trendSingleNew)
    # around 1/6
    #ind = data.add_func(trendTurn)
    # 1.7/6
    #ind = data.add_func(doubleAvgDay)
    # wired with sudden draw back
    #ind = data.add_func(trendBreak)
    #with cl only 7/10
    #with codelist
    #ind = data.add_func(doubleAvgminv2)
    #45/10 with a50, that's -1
    #ind = data.add_func(doubleAvgmin)
    #triNetV2 a50 10/10
    #ind = data.add_func(triNetv2)

    #18/10,currently this is job50 taking now
    #ind = data.add_func(trendWeekMinv2)
    #21/10
    ind = data.add_func(trendWeekMinv15520)

    #7/10
    #ind = data.add_func(EMA_MA)


    #6/10
    #ind = data.add_func(TrendFinder)

    #ind = data.add_func(bollStrategy)
    # ind = data.add_func(nineTurn)
    #ind=data.add_func(MACACalculate)
    #ind = data.add_func(EMAOP)
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
                        item.code[0], item.date[0], int((Account.cash_available - safeholding) / (100 * open)) * 100,
                        QA.ORDER_DIRECTION.BUY, open, QA.ORDER_MODEL.LIMIT, QA.AMOUNT_MODEL.BY_AMOUNT))
                    order = Account.send_order(
                        code=item.code[0],
                        time=item.date[0],
                        amount=int((Account.cash_available - safeholding) / (holdingperc * item.open[0] *100))*100,
                        towards=QA.ORDER_DIRECTION.BUY,
                        price=item.close[0],
                        order_model=QA.ORDER_MODEL.LIMIT,
                        amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
                    )
                    #deal[item.code[0]]= int((Account.cash_available - safeholding) / (holdingperc * open*100))*100



                else:
                    order = None
                #start to trade
                if order:
                    # print('sending order '+'*'*60)
                    Broker.receive_order(QA.QA_Event(order=order, market_data=item))
                    #print('got here --------------------')
                    trade_mes = Broker.query_orders(Account.account_cookie, 'filled')
                    #print(trade_mes)
                   # print('got here 2 -------')
                    res = trade_mes.loc[order.account_cookie, order.realorder_id]
                    #print('got here 3 -------- ')
                    order.trade(res.trade_id, res.trade_price, res.trade_amount, res.trade_time)
                   #print('*' * 100)
                    print(str(item.date[0]) + " buy " + item.code[0])

            elif (daily_ind.single.iloc[0] == 3):
                #close = QA.QA_fetch_stock_day_adv(item.code[0], item.date[0], item.date[0]).data.close[0] if np.isnan(
                    #daily_ind.close.iloc[0]) else item.close[0]
                if Account.sell_available.get(item.code[0], 0) > 0:
                    print('>' * 100)
                    print(str(item.date[0]) + " sell " + item.code[0])
                    order = Account.send_order(
                        code=item.code[0],
                        time=item.date[0],
                        amount=Account.sell_available.get(item.code[0], 0),
                        #amount = deal.get(item.code[0]),
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
    print('analyse account profit for ' +sys._getframe().f_code.co_name)
    Risk = QA.QA_Risk(Account)
    Risk.assets.plot()
    print('{} with risk {} '.format( sys._getframe().f_code.co_name,Risk.profit_construct))
    print('winning ratio is {}'.format(winRatio(Account)))










def trendWeekMinv60510(sample,short=5, long=10, freq='60min'):
    #test summary
    #5-10 with 21/10
    #5-15 with 23/10
    #5-20 with 19/10
    #20-60 24/10
    #to get Week and 60 minutes syntony together
    #get week trend
    #A50 64% 30 5 15 12/10
    #
    #60 76, 30 79, 30 74 more
    #15 min is the best for now, with 11/10 (5-10 11, 5-15 10 5-20 )
    import quant.weekTrend as wt
    print('{} deal with {}'.format(sys._getframe().f_code.co_name,sample.index.get_level_values('code')[-1]))
    print('*'*100)

    sample.fillna(method='ffill',inplace=True)
    wstart = '2010-01-01'
    code = sample.index.get_level_values('code')[-1]
    wend = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    temp = QA.QA_fetch_stock_day_adv(code,wstart,wend).data
    wd = wt.wds(temp)
    wd = wt.TrendDetect(wd)

    start = sample.index.get_level_values(dayindex)[0].strftime(dayformate)
    end = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    mindata = QA.QA_fetch_stock_min_adv(sample.index.get_level_values('code')[0], start, end, frequence= freq)
    ms = mindata.data
    # print(sample)
    ms['short'] = QA.EMA(ms.close, short)
    ms['long'] = QA.EMA(ms.close, long)
    CROSS_5 = QA.CROSS(ms.short, ms.long)
    CROSS_15 = QA.CROSS(ms.long, ms.short)

    C15 = np.where(CROSS_15 == 1, 3, 0)
    m = np.where(CROSS_5 == 1, 1, C15)
    # single = m[:-1].tolist()
    # single.insert(0, 0)
    ms['single'] = m.tolist()
    sig = [0]
    if(freq=='60min'):
        anchor = -2
    elif(freq=='30min'):
        anchor = -4
    elif(freq=='15min'):
        anchor = -8
    for i in range(1, len(sample)):
        dtime = sample.index.get_level_values(dayindex)[i]
        wtime = getWeekDate(dtime)
        windex = wd[wd.date == wtime.strftime(dayformate)].index[0]
        # here use index to get value interested, here we take change of MACDBlock to get the short trend in week level
        direction = wd.loc[windex].CS
        trendv = wd.loc[windex].SM
        temp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[i].strftime(dayformate)][:anchor]
        tmp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[i-1].strftime(dayformate)][anchor:]
        sing = temp.single.sum()+tmp.single.sum()
        if(direction>0 and trendv >0 and sing==1):
            sig.append(1)
        elif(direction<0 and sing==3):
            sig.append(sing)
        else:
            sig.append(0)

    try:
        #sample['single'] = [0]+sig[:-1]
        sample['single']=sig

    except:
        print('error with {}'.format(sample.index.get_level_values('code')[0]))
        sample['single'] = 0


    return sample

def backtest60510(holdingperc = 3):
    #holdingperc = 3
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
    #endtime = '2020-06-01'
    endtime = '2020-07-15'
    cl = ['000977', '600745','002889','600340','000895','600019','600028',
          '601857','600585','002415','002475','600031','600276','600009','601318',
          '000333','600031','002384','002241','600703','000776','600897','600085']
    codelist2.extend(cl)
    codelist = list(set(codelist2))
    # data = loadLocalData(cl, '2018-01-01', endtime)
    data = loadLocalData(cl, '2018-01-01', endtime)
    data = data.to_qfq()
    print('*' * 100)
    print('prepare data for back test')
    #no qfq, 15/10, with qfq,
    #ind = data.add_func(trendSingleNew)
    # around 1/6
    #ind = data.add_func(trendTurn)
    # 1.7/6
    #ind = data.add_func(doubleAvgDay)
    # wired with sudden draw back
    #ind = data.add_func(trendBreak)
    #with cl only 7/10
    #with codelist
    #ind = data.add_func(doubleAvgminv2)
    #45/10 with a50, that's -1
    #ind = data.add_func(doubleAvgmin)
    #triNetV2 a50 10/10
    #ind = data.add_func(triNetv2)

    #18/10,currently this is job50 taking now
    #ind = data.add_func(trendWeekMinv2)
    #21/10
    ind = data.add_func(trendWeekMinv60510)

    #7/10
    #ind = data.add_func(EMA_MA)


    #6/10
    #ind = data.add_func(TrendFinder)

    #ind = data.add_func(bollStrategy)
    # ind = data.add_func(nineTurn)
    #ind=data.add_func(MACACalculate)
    #ind = data.add_func(EMAOP)
    # cur = datetime.datetime.now()
    # endtime = str(cur.year) + '-' + str(cur.month) + '-' + str(cur.day)
    data_forbacktest = data.select_time('2018-01-01', endtime)
    deal = {}
    for items in data_forbacktest.panel_gen:
        for item in items.security_gen:

            daily_ind = ind.loc[item.index]
            if (daily_ind.single.iloc[0] == 1):
                open = QA.QA_fetch_stock_day_adv(item.code[0], item.date[0], item.date[0]).data.open[0] if np.isnan(
                    item.open[0]) else item.open[0]
                if ((Account.cash_available - safeholding) / (holdingperc * item.close[0]) > 500):
                    print('code {}, time {} amout {}, toward {}, price {} order_model {} amount_model {}'.format(
                        item.code[0], item.date[0], int((Account.cash_available - safeholding) / (100 * open)) * 100,
                        QA.ORDER_DIRECTION.BUY, open, QA.ORDER_MODEL.LIMIT, QA.AMOUNT_MODEL.BY_AMOUNT))
                    order = Account.send_order(
                        code=item.code[0],
                        time=item.date[0],
                        amount=int((Account.cash_available - safeholding) / (holdingperc * item.open[0] *100))*100,
                        towards=QA.ORDER_DIRECTION.BUY,
                        price=item.close[0],
                        order_model=QA.ORDER_MODEL.LIMIT,
                        amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
                    )
                    #deal[item.code[0]]= int((Account.cash_available - safeholding) / (holdingperc * open*100))*100



                else:
                    order = None
                #start to trade
                if order:
                    # print('sending order '+'*'*60)
                    Broker.receive_order(QA.QA_Event(order=order, market_data=item))
                    #print('got here --------------------')
                    trade_mes = Broker.query_orders(Account.account_cookie, 'filled')
                    #print(trade_mes)
                   # print('got here 2 -------')
                    res = trade_mes.loc[order.account_cookie, order.realorder_id]
                    #print('got here 3 -------- ')
                    order.trade(res.trade_id, res.trade_price, res.trade_amount, res.trade_time)
                   #print('*' * 100)
                    print(str(item.date[0]) + " buy " + item.code[0])

            elif (daily_ind.single.iloc[0] == 3):
                #close = QA.QA_fetch_stock_day_adv(item.code[0], item.date[0], item.date[0]).data.close[0] if np.isnan(
                    #daily_ind.close.iloc[0]) else item.close[0]
                if Account.sell_available.get(item.code[0], 0) > 0:
                    print('>' * 100)
                    print(str(item.date[0]) + " sell " + item.code[0])
                    order = Account.send_order(
                        code=item.code[0],
                        time=item.date[0],
                        amount=Account.sell_available.get(item.code[0], 0),
                        #amount = deal.get(item.code[0]),
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
    print('analyse account profit for ' +sys._getframe().f_code.co_name)
    Risk = QA.QA_Risk(Account)
    Risk.assets.plot()
    print('{} with risk {} '.format( sys._getframe().f_code.co_name,Risk.profit_construct))
    print('winning ratio is {}'.format(winRatio(Account)))


def trendWeekMinv60515(sample,short=5, long=15, freq='60min'):
    #test summary
    #5-10 with 21/10
    #5-15 with 23/10
    #5-20 with 19/10
    #20-60 24/10
    #to get Week and 60 minutes syntony together
    #get week trend
    #A50 64% 30 5 15 12/10
    #
    #60 76, 30 79, 30 74 more
    #15 min is the best for now, with 11/10 (5-10 11, 5-15 10 5-20 )
    import quant.weekTrend as wt
    print('{} deal with {}'.format(sys._getframe().f_code.co_name,sample.index.get_level_values('code')[-1]))
    print('*'*100)

    sample.fillna(method='ffill',inplace=True)
    wstart = '2010-01-01'
    code = sample.index.get_level_values('code')[-1]
    wend = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    temp = QA.QA_fetch_stock_day_adv(code,wstart,wend).data
    wd = wt.wds(temp)
    wd = wt.TrendDetect(wd)

    start = sample.index.get_level_values(dayindex)[0].strftime(dayformate)
    end = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    mindata = QA.QA_fetch_stock_min_adv(sample.index.get_level_values('code')[0], start, end, frequence= freq)
    ms = mindata.data
    # print(sample)
    ms['short'] = QA.EMA(ms.close, short)
    ms['long'] = QA.EMA(ms.close, long)
    CROSS_5 = QA.CROSS(ms.short, ms.long)
    CROSS_15 = QA.CROSS(ms.long, ms.short)

    C15 = np.where(CROSS_15 == 1, 3, 0)
    m = np.where(CROSS_5 == 1, 1, C15)
    # single = m[:-1].tolist()
    # single.insert(0, 0)
    ms['single'] = m.tolist()
    sig = [0]
    if(freq=='60min'):
        anchor = -2
    elif(freq=='30min'):
        anchor = -4
    elif(freq=='15min'):
        anchor = -8
    for i in range(1, len(sample)):
        dtime = sample.index.get_level_values(dayindex)[i]
        wtime = getWeekDate(dtime)
        windex = wd[wd.date == wtime.strftime(dayformate)].index[0]
        # here use index to get value interested, here we take change of MACDBlock to get the short trend in week level
        direction = wd.loc[windex].CS
        trendv = wd.loc[windex].SM
        temp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[i].strftime(dayformate)][:anchor]
        tmp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[i-1].strftime(dayformate)][anchor:]
        sing = temp.single.sum()+tmp.single.sum()
        if(direction>0 and trendv >0 and sing==1):
            sig.append(1)
        elif(direction<0 and sing==3):
            sig.append(sing)
        else:
            sig.append(0)

    try:
        #sample['single'] = [0]+sig[:-1]
        sample['single']=sig

    except:
        print('error with {}'.format(sample.index.get_level_values('code')[0]))
        sample['single'] = 0


    return sample

def backtest60515(holdingperc = 3):
    #holdingperc = 3
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
    #endtime = '2020-06-01'
    endtime = '2020-07-15'
    cl = ['000977', '600745','002889','600340','000895','600019','600028',
          '601857','600585','002415','002475','600031','600276','600009','601318',
          '000333','600031','002384','002241','600703','000776','600897','600085']
    codelist2.extend(cl)
    codelist = list(set(codelist2))
    # data = loadLocalData(cl, '2018-01-01', endtime)
    data = loadLocalData(cl, '2018-01-01', endtime)
    data = data.to_qfq()
    print('*' * 100)
    print('prepare data for back test')
    #no qfq, 15/10, with qfq,
    #ind = data.add_func(trendSingleNew)
    # around 1/6
    #ind = data.add_func(trendTurn)
    # 1.7/6
    #ind = data.add_func(doubleAvgDay)
    # wired with sudden draw back
    #ind = data.add_func(trendBreak)
    #with cl only 7/10
    #with codelist
    #ind = data.add_func(doubleAvgminv2)
    #45/10 with a50, that's -1
    #ind = data.add_func(doubleAvgmin)
    #triNetV2 a50 10/10
    #ind = data.add_func(triNetv2)

    #18/10,currently this is job50 taking now
    #ind = data.add_func(trendWeekMinv2)
    #21/10
    ind = data.add_func(trendWeekMinv60515)

    #7/10
    #ind = data.add_func(EMA_MA)


    #6/10
    #ind = data.add_func(TrendFinder)

    #ind = data.add_func(bollStrategy)
    # ind = data.add_func(nineTurn)
    #ind=data.add_func(MACACalculate)
    #ind = data.add_func(EMAOP)
    # cur = datetime.datetime.now()
    # endtime = str(cur.year) + '-' + str(cur.month) + '-' + str(cur.day)
    data_forbacktest = data.select_time('2018-01-01', endtime)
    deal = {}
    for items in data_forbacktest.panel_gen:
        for item in items.security_gen:

            daily_ind = ind.loc[item.index]
            if (daily_ind.single.iloc[0] == 1):
                open = QA.QA_fetch_stock_day_adv(item.code[0], item.date[0], item.date[0]).data.open[0] if np.isnan(
                    item.open[0]) else item.open[0]
                if ((Account.cash_available - safeholding) / (holdingperc * item.close[0]) > 500):
                    print('code {}, time {} amout {}, toward {}, price {} order_model {} amount_model {}'.format(
                        item.code[0], item.date[0], int((Account.cash_available - safeholding) / (100 * open)) * 100,
                        QA.ORDER_DIRECTION.BUY, open, QA.ORDER_MODEL.LIMIT, QA.AMOUNT_MODEL.BY_AMOUNT))
                    order = Account.send_order(
                        code=item.code[0],
                        time=item.date[0],
                        amount=int((Account.cash_available - safeholding) / (holdingperc * item.open[0] *100))*100,
                        towards=QA.ORDER_DIRECTION.BUY,
                        price=item.close[0],
                        order_model=QA.ORDER_MODEL.LIMIT,
                        amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
                    )
                    #deal[item.code[0]]= int((Account.cash_available - safeholding) / (holdingperc * open*100))*100



                else:
                    order = None
                #start to trade
                if order:
                    # print('sending order '+'*'*60)
                    Broker.receive_order(QA.QA_Event(order=order, market_data=item))
                    #print('got here --------------------')
                    trade_mes = Broker.query_orders(Account.account_cookie, 'filled')
                    #print(trade_mes)
                   # print('got here 2 -------')
                    res = trade_mes.loc[order.account_cookie, order.realorder_id]
                    #print('got here 3 -------- ')
                    order.trade(res.trade_id, res.trade_price, res.trade_amount, res.trade_time)
                   #print('*' * 100)
                    print(str(item.date[0]) + " buy " + item.code[0])

            elif (daily_ind.single.iloc[0] == 3):
                #close = QA.QA_fetch_stock_day_adv(item.code[0], item.date[0], item.date[0]).data.close[0] if np.isnan(
                    #daily_ind.close.iloc[0]) else item.close[0]
                if Account.sell_available.get(item.code[0], 0) > 0:
                    print('>' * 100)
                    print(str(item.date[0]) + " sell " + item.code[0])
                    order = Account.send_order(
                        code=item.code[0],
                        time=item.date[0],
                        amount=Account.sell_available.get(item.code[0], 0),
                        #amount = deal.get(item.code[0]),
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
    print('analyse account profit for ' +sys._getframe().f_code.co_name)
    Risk = QA.QA_Risk(Account)
    Risk.assets.plot()
    print('{} with risk {} '.format( sys._getframe().f_code.co_name,Risk.profit_construct))
    print('winning ratio is {}'.format(winRatio(Account)))

def trendWeekMinv602060(sample,short=20, long=60, freq='60min'):
    #test summary
    #5-10 with 21/10
    #5-15 with 23/10
    #5-20 with 19/10
    #20-60 24/10
    #to get Week and 60 minutes syntony together
    #get week trend
    #A50 64% 30 5 15 12/10
    #
    #60 76, 30 79, 30 74 more
    #15 min is the best for now, with 11/10 (5-10 11, 5-15 10 5-20 )
    import quant.weekTrend as wt
    print('{} deal with {}'.format(sys._getframe().f_code.co_name,sample.index.get_level_values('code')[-1]))
    print('*'*100)

    sample.fillna(method='ffill',inplace=True)
    wstart = '2010-01-01'
    code = sample.index.get_level_values('code')[-1]
    wend = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    temp = QA.QA_fetch_stock_day_adv(code,wstart,wend).data
    wd = wt.wds(temp)
    wd = wt.TrendDetect(wd)

    start = sample.index.get_level_values(dayindex)[0].strftime(dayformate)
    end = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    mindata = QA.QA_fetch_stock_min_adv(sample.index.get_level_values('code')[0], start, end, frequence= freq)
    ms = mindata.data
    # print(sample)
    ms['short'] = QA.EMA(ms.close, short)
    ms['long'] = QA.EMA(ms.close, long)
    CROSS_5 = QA.CROSS(ms.short, ms.long)
    CROSS_15 = QA.CROSS(ms.long, ms.short)

    C15 = np.where(CROSS_15 == 1, 3, 0)
    m = np.where(CROSS_5 == 1, 1, C15)
    # single = m[:-1].tolist()
    # single.insert(0, 0)
    ms['single'] = m.tolist()
    sig = [0]
    if(freq=='60min'):
        anchor = -2
    elif(freq=='30min'):
        anchor = -4
    elif(freq=='15min'):
        anchor = -8
    for i in range(1, len(sample)):
        dtime = sample.index.get_level_values(dayindex)[i]
        wtime = getWeekDate(dtime)
        windex = wd[wd.date == wtime.strftime(dayformate)].index[0]
        # here use index to get value interested, here we take change of MACDBlock to get the short trend in week level
        direction = wd.loc[windex].CS
        trendv = wd.loc[windex].SM
        temp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[i].strftime(dayformate)][:anchor]
        tmp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[i-1].strftime(dayformate)][anchor:]
        sing = temp.single.sum()+tmp.single.sum()
        if(direction>0 and trendv >0 and sing==1):
            sig.append(1)
        elif(direction<0 and sing==3):
            sig.append(sing)
        else:
            sig.append(0)

    try:
        #sample['single'] = [0]+sig[:-1]
        sample['single']=sig

    except:
        print('error with {}'.format(sample.index.get_level_values('code')[0]))
        sample['single'] = 0


    return sample

def backtest602060(holdingperc = 3):
    #holdingperc = 3
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
    #endtime = '2020-06-01'
    endtime = '2020-07-15'
    cl = ['000977', '600745','002889','600340','000895','600019','600028',
          '601857','600585','002415','002475','600031','600276','600009','601318',
          '000333','600031','002384','002241','600703','000776','600897','600085']
    codelist2.extend(cl)
    codelist = list(set(codelist2))
    # data = loadLocalData(cl, '2018-01-01', endtime)
    data = loadLocalData(cl, '2018-01-01', endtime)
    data = data.to_qfq()
    print('*' * 100)
    print('prepare data for back test')
    #no qfq, 15/10, with qfq,
    #ind = data.add_func(trendSingleNew)
    # around 1/6
    #ind = data.add_func(trendTurn)
    # 1.7/6
    #ind = data.add_func(doubleAvgDay)
    # wired with sudden draw back
    #ind = data.add_func(trendBreak)
    #with cl only 7/10
    #with codelist
    #ind = data.add_func(doubleAvgminv2)
    #45/10 with a50, that's -1
    #ind = data.add_func(doubleAvgmin)
    #triNetV2 a50 10/10
    #ind = data.add_func(triNetv2)

    #18/10,currently this is job50 taking now
    #ind = data.add_func(trendWeekMinv2)
    #21/10
    ind = data.add_func(trendWeekMinv602060)

    #7/10
    #ind = data.add_func(EMA_MA)


    #6/10
    #ind = data.add_func(TrendFinder)

    #ind = data.add_func(bollStrategy)
    # ind = data.add_func(nineTurn)
    #ind=data.add_func(MACACalculate)
    #ind = data.add_func(EMAOP)
    # cur = datetime.datetime.now()
    # endtime = str(cur.year) + '-' + str(cur.month) + '-' + str(cur.day)
    data_forbacktest = data.select_time('2018-01-01', endtime)
    deal = {}
    for items in data_forbacktest.panel_gen:
        for item in items.security_gen:

            daily_ind = ind.loc[item.index]
            if (daily_ind.single.iloc[0] == 1):
                open = QA.QA_fetch_stock_day_adv(item.code[0], item.date[0], item.date[0]).data.open[0] if np.isnan(
                    item.open[0]) else item.open[0]
                if ((Account.cash_available - safeholding) / (holdingperc * item.close[0]) > 500):
                    print('code {}, time {} amout {}, toward {}, price {} order_model {} amount_model {}'.format(
                        item.code[0], item.date[0], int((Account.cash_available - safeholding) / (100 * open)) * 100,
                        QA.ORDER_DIRECTION.BUY, open, QA.ORDER_MODEL.LIMIT, QA.AMOUNT_MODEL.BY_AMOUNT))
                    order = Account.send_order(
                        code=item.code[0],
                        time=item.date[0],
                        amount=int((Account.cash_available - safeholding) / (holdingperc * item.open[0] *100))*100,
                        towards=QA.ORDER_DIRECTION.BUY,
                        price=item.close[0],
                        order_model=QA.ORDER_MODEL.LIMIT,
                        amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
                    )
                    #deal[item.code[0]]= int((Account.cash_available - safeholding) / (holdingperc * open*100))*100



                else:
                    order = None
                #start to trade
                if order:
                    # print('sending order '+'*'*60)
                    Broker.receive_order(QA.QA_Event(order=order, market_data=item))
                    #print('got here --------------------')
                    trade_mes = Broker.query_orders(Account.account_cookie, 'filled')
                    #print(trade_mes)
                   # print('got here 2 -------')
                    res = trade_mes.loc[order.account_cookie, order.realorder_id]
                    #print('got here 3 -------- ')
                    order.trade(res.trade_id, res.trade_price, res.trade_amount, res.trade_time)
                   #print('*' * 100)
                    print(str(item.date[0]) + " buy " + item.code[0])

            elif (daily_ind.single.iloc[0] == 3):
                #close = QA.QA_fetch_stock_day_adv(item.code[0], item.date[0], item.date[0]).data.close[0] if np.isnan(
                    #daily_ind.close.iloc[0]) else item.close[0]
                if Account.sell_available.get(item.code[0], 0) > 0:
                    print('>' * 100)
                    print(str(item.date[0]) + " sell " + item.code[0])
                    order = Account.send_order(
                        code=item.code[0],
                        time=item.date[0],
                        amount=Account.sell_available.get(item.code[0], 0),
                        #amount = deal.get(item.code[0]),
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
    print('analyse account profit for ' +sys._getframe().f_code.co_name)
    Risk = QA.QA_Risk(Account)
    Risk.assets.plot()
    print('{} with risk {} '.format( sys._getframe().f_code.co_name,Risk.profit_construct))
    print('winning ratio is {}'.format(winRatio(Account)))


def main():
    '''
    print('*'*300)
    print('15510')
    backtest15510()
    '''
    import multiprocessing
    processList=[]
    tmp1 = multiprocessing.Process(target=backtest15515,args=())
    processList.append(tmp1)

    tmp2 = multiprocessing.Process(target=backtest152060,args=())
    processList.append(tmp2)

    tmp3 = multiprocessing.Process(target=backtest15510, args=())
    processList.append(tmp3)

    tmp4 = multiprocessing.Process(target=backtest60510, args=())
    processList.append(tmp4)

    tmp5 = multiprocessing.Process(target=backtest60515, args=())
    processList.append(tmp5)

    tmp6 = multiprocessing.Process(target=backtest602060, args=())
    processList.append(tmp6)


    for process in processList:
        process.start()
    for process in processList:
        process.join()

    '''
    print('*'*300)
    print('15515')
    backtest15515()
    
    print('*' * 300)
    print('15520')
    backtest15520()

    
    print('*'*300)
    print('152060')
    backtest152060()

    print('*' * 300)
    print('60510')
    backtest60510()
    print('*' * 300)
    print('60515')
    backtest60515()
    print('*' * 300)
    print('602060')
    backtest602060()
    '''

if __name__=="__main__":
    import warnings
    warnings.filterwarnings('ignore')
    main()