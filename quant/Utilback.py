import datetime
import smtplib
from email.mime.text import MIMEText
import QUANTAXIS as QA
import dateutil

try:
    assert QA.__version__ >= '1.1.0'
except AssertionError:
    print('pip install QUANTAXIS >= 1.1.0 请升级QUANTAXIS后再运行此示例')
    import QUANTAXIS as QA
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import core.Util as util
import abupy
from abupy import ABuRegUtil
from concurrent.futures import ThreadPoolExecutor
from functools import reduce
import warnings
import re

# read_dictionary = np.load('/media/sf_GIT/vest/liutong.npy', allow_pickle=True).item()
read_dictionary = np.load('/Users/jiangyongnan/git/ecap/liutong.npy', allow_pickle=True).item()

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtk
import mpl_finance as mpf

index = 'datetime'
formate = '%Y-%m-%dT%H:%M:%S'
dayindex = 'date'
dayformate = '%Y-%m-%d'
startday = '2018-01-01'

pw = 0.47  # backtest win ratio
rw = 1.15  # sell when got 15% increase
rl = 0.97  # end if loss 0.03 of holdings


def percSet(pw, rw, rl):
    # kelly rule of holdings
    return (pw / rl) - (1 - pw) / rw


# percSet(pw,rw,rl)


def initData(sample):
    sample['EMA13'] = QA.EMA(sample.close, 13)
    # sample['EMA26'] = QA.EMA(sample.close,26)
    sample['MA64'] = QA.MA(sample.close, 64)
    sample['MA256'] = QA.MA(sample.close, 256)
    pp_array = [x for x in sample.close]
    forceweight = []
    force = [0]
    for m, n in zip(pp_array[:-1], pp_array[1:]):
        force.append(n - m)
        # print (n-m)
    # only for online data. is sample.vol, datat
    volumn = [x for x in sample.volume]
    for x, y in zip(force, volumn):
        # print("{0} and {1}".format(x,y))
        forceweight.append(x * y)

    sample['FORCE'] = forceweight
    sample['FCEMA2'] = QA.EMA(sample.FORCE, 2)
    sample['FCEMA13'] = QA.EMA(sample.FORCE, 13)
    # print(sample)
    rate = 0.015
    sample['EMA12'] = QA.EMA(sample.close, 12)
    sample['EMA5'] = QA.EMA(sample.close, 5)
    # sample['MA64']=QA.MA(sample.close,64)
    # sample['MA256']=QA.MA(sample.close,256)
    sample['EMA20'] = QA.EMA(sample.close, 20)
    sample['k1'] = 0.618 * QA.HHV(sample.high, 256) + 0.382 * QA.LLV(sample.low, 256)
    sample['k2'] = 0.5 * QA.HHV(sample.high, 256) + 0.5 * QA.LLV(sample.low, 256)
    sample['k3'] = 0.382 * QA.HHV(sample.high, 256) + 0.618 * QA.LLV(sample.low, 256)
    sample['EMA30'] = QA.EMA(sample.close, 30)
    sample['EMA13'] = QA.EMA(sample.close, 13)
    sample['optimism'] = sample.high - sample.EMA13
    sample['pessmist'] = sample.low - sample.EMA13
    sample['up'] = sample.EMA13 * (1 + rate)
    sample['down'] = sample.EMA13 * (1 - rate)
    sample['EMA26'] = QA.EMA(sample.close, 26)
    sample['MACDQ'] = sample['EMA12'] - sample['EMA26']
    sample['MACDSIG'] = QA.EMA(sample['MACDQ'], 9)
    sample['MACDBlock'] = sample['MACDQ'] - sample['MACDSIG']
    sample['VolumeEMA'] = QA.EMA(sample.volume, 5)
    # sample['VolumeEMA'] = QA.EMA(sample.vol, 5)

    # trend block
    from abupy import pd_rolling_max
    from abupy import pd_expanding_max
    N = 15
    sample['nhigh'] = pd_rolling_max(sample.high, window=N)
    expanmax = pd_expanding_max(sample.close)
    sample['nhigh'].fillna(value=expanmax, inplace=True)

    from abupy import pd_rolling_min, pd_expanding_min
    sample['nlow'] = pd_rolling_min(sample.low, window=N)
    expanmin = pd_expanding_min(sample.close)
    sample['nlow'].fillna(value=expanmin, inplace=True)

    sroc = []
    for i in range(sample.shape[0]):
        if (i - 21 > 0 and sample.iloc[i].EMA13 != None and sample.iloc[i - 21].EMA13 != None):
            # print(sample.iloc[i].EMA13/sample.iloc[i-21].EMA13)
            sroc.append((sample.iloc[i].EMA13 / sample.iloc[i - 21].EMA13) * 100)
        else:
            sroc.append(100)
    sample['SROC'] = sroc
    return sample


def backtest():
    holdingperc = 3
    safeholding = 500
    print('*' * 100)
    print('loading data')
    # stockes = getStocklist()
    # stockes = ['600797','000977']
    # data = loadLocalData(stockes,'2018-03-15',end_date = '2019-09-11')
    print('*' * 100)
    print('init account')
    Account = QA.QA_Account(user_cookie='eric', portfolio_cookie='eric', commission_coeff=0.0002)
    Broker = QA.QA_BacktestBroker()
    Account.reset_assets(60000)
    Account.account_cookie = 'ECAP'
    # codelist=['600797','000977','601068','601069','000977']
    # 云计算，华为，5G概念
    codelist3 = QA.QA_fetch_stock_block_adv().get_block('云计算').code[:]
    codelist1 = QA.QA_fetch_stock_block_adv().get_block('华为概念').code[:]
    codelist2 = QA.QA_fetch_stock_block_adv().get_block('5G概念').code[:]
    # codelist4 = QA.QA_fetch_stock_block_adv().get_block('国产软件').code[:]
    codelist1.extend(codelist2)
    codelist1.extend(codelist3)

    #
    clist3 = QA.QA_fetch_stock_block_adv().get_block('阿里概念').code[:]
    clist1 = QA.QA_fetch_stock_block_adv().get_block('腾讯概念').code[:]
    clist2 = QA.QA_fetch_stock_block_adv().get_block('小米概念').code[:]
    # codelist4 = QA.QA_fetch_stock_block_adv().get_block('国产软件').code[:]
    clist1.extend(clist2)
    clist1.extend(clist3)

    # codelist1.extend(codelist4)
    codelist = list(set(codelist1))

    # QA.QA_fetch_get_stock_info(code)
    cl = ['600745', '000977', '002475', '000987', '300548', '000810']
    cur = datetime.datetime.now()
    mon = str(cur.month)
    day = str(cur.day)

    if (re.match('[0-9]{1}', mon) and len(mon) == 1):
        mon = '0' + mon
    if (re.match('[0-9]{1}', day) and len(day) == 1):
        day = '0' + day
    # endtime = str(cur.year) + '-' + mon + '-' + day

    endtime = '2020-05-11'
    data = loadLocalData(codelist, '2019-01-01', endtime)
    data = data.to_qfq()
    print('*' * 100)
    print('prepare data for back test')
    # trendsingleNew with positive 30%
    ind = data.add_func(trendSingleNew)
    # MACD_JCSC negative
    # ind = data.add_func(MACD_JCSC)
    # doubleAvgMIn 5,15 60min negative
    # ind = data.add_func(doubleAvgmin)

    # ind = data.add_func(ATRStrategy)
    # ind = data.add_func(doubleAvgIndayTrade)
    # c30Day with -10427 profit
    # ind = data.add_func(c30Day)
    # doubleAvgDay with 1028 and 0.30
    # ind = data.add_func(doubleAvgDay)

    # ind = data.add_func(nineTurn)
    # ind=data.add_func(MACACalculate)
    # ind = data.add_func(EMAOP)
    # cur = datetime.datetime.now()
    # endtime = str(cur.year) + '-' + str(cur.month) + '-' + str(cur.day)
    data_forbacktest = data.select_time('2019-01-01', endtime)
    # mind = QA.QA_fetch_stock_min_adv(codelist,'2019-01-01',endtime,frequence='60min')

    for items in data_forbacktest.panel_gen:
        for item in items.security_gen:
            # md = mind.select_code(item.code[0]).data
            daily_ind = ind.loc[item.index]
            if (np.isnan(daily_ind.open.iloc[0]) and np.isnan(daily_ind.close.iloc[0])):
                continue
            else:
                if (daily_ind.single.iloc[0] == 1):

                    if ((Account.cash_available - safeholding) / (holdingperc * item.open[0]) > 0):
                        order = Account.send_order(
                            code=item.code[0],
                            time=item.date[0],
                            amount=int((Account.cash_available - safeholding) / (holdingperc * item.open[0])),
                            # amount = 2000,
                            # amount=2000,
                            towards=QA.ORDER_DIRECTION.BUY,
                            price=item.open[0],
                            # price = md[md.index.get_level_values(index).strftime(dayformate) ==
                            #       (item.date[0]).strftime(dayformate)].open[-1],
                            order_model=QA.ORDER_MODEL.LIMIT,
                            amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
                        )
                    elif ((Account.cash_available - safeholding) / (item.open[0]) > 0):
                        order = Account.send_order(
                            code=item.code[0],
                            time=item.date[0],
                            amount=int((Account.cash_available - safeholding) / item.open[0]),
                            # amount = 2000,
                            # amount=2000,
                            towards=QA.ORDER_DIRECTION.BUY,
                            price=item.open[0],
                            # price=md[md.index.get_level_values(index).strftime(dayformate) ==
                            #        (item.date[0]).strftime(dayformate)].open[-1],
                            order_model=QA.ORDER_MODEL.LIMIT,
                            amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
                        )
                    # print(item.to_json()[0])
                    if order:
                        # print('sending order '+'*'*60)
                        Broker.receive_order(QA.QA_Event(order=order, market_data=item))

                        trade_mes = Broker.query_orders(Account.account_cookie, 'filled')
                        res = trade_mes.loc[order.account_cookie, order.realorder_id]
                        # print(trade_mes)
                        order.trade(res.trade_id, res.trade_price, res.trade_amount, res.trade_time)
                        print('*' * 100)
                        print(str(item.date[0]) + " buy " + item.code[0])
                    # print (res)
                elif (daily_ind.single.iloc[0] == 3):
                    if Account.sell_available.get(item.code[0], 0) > 0:
                        print('>' * 100)
                        print(str(item.date[0]) + " sell " + item.code[0])
                        # print(int(Account.sell_available.get(item.code[0], 0)))
                        order = Account.send_order(
                            code=item.code[0],
                            time=item.date[0],

                            amount=Account.sell_available.get(item.code[0], 0),
                            towards=QA.ORDER_DIRECTION.SELL,
                            # price=(item.close[0]+(item.high[0]-item.close[0])/2),
                            price=item.close[0] * 0.998,
                            order_model=QA.ORDER_MODEL.LIMIT,

                            # amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
                            amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
                        )
                        if order:
                            Broker.receive_order(QA.QA_Event(order=order, market_data=item))

                            trade_mes = Broker.query_orders(Account.account_cookie, 'filled')
                            res = trade_mes.loc[order.account_cookie, order.realorder_id]
                            order.trade(res.trade_id, res.trade_price, res.trade_amount, res.trade_time)
                    # print(res)
        Account.settle()

    print('*' * 100)
    print('analyse account profit')
    Risk = QA.QA_Risk(Account)
    Risk.assets.plot()
    print(Risk.profit_construct)
    print('winning ratio is {}'.format(winRatio(Account)))
    print(Account.history_table)
    print('done')


def MACACalculate(sample):
    rate = 0.015
    sample['EMA12'] = QA.EMA(sample.close, 12)
    sample['EMA13'] = QA.EMA(sample.close, 13)
    sample['optimism'] = sample.high - sample.EMA13
    sample['pessmist'] = sample.low - sample.EMA13
    sample['up'] = sample.EMA13 * (1 + rate)
    sample['down'] = sample.EMA13 * (1 - rate)
    sample['EMA26'] = QA.EMA(sample.close, 26)
    sample['MACDQ'] = sample['EMA12'] - sample['EMA26']
    sample['MACDSIG'] = QA.EMA(sample['MACDQ'], 9)
    sample['MACDBlock'] = sample['MACDQ'] - sample['MACDSIG']
    sample['VolumeEMA'] = QA.EMA(sample.volume, 5)
    sroc = []
    for i in range(sample.shape[0]):
        if (i - 21 > 0 and sample.iloc[i].EMA13 != None and sample.iloc[i - 21].EMA13 != None):
            # print(sample.iloc[i].EMA13/sample.iloc[i-21].EMA13)
            sroc.append((sample.iloc[i].EMA13 / sample.iloc[i - 21].EMA13) * 100)
        else:
            sroc.append(100)
    sample['SROC'] = sroc
    size = sample.shape[0]
    single = [0]
    for i in range(sample.shape[0]):
        if (sample.MACDBlock[i - 1] < 0 and sample.MACDBlock[i] >= 0 and i - 1 >= 0):
            print(sample.index.get_level_values('date')[i])
            single.append(1)
        elif (sample.MACDBlock[i - 1] >= 0 and sample.MACDBlock[i] < 0 and i):
            single.append(3)
        else:
            single.append(0)
    for i in range(sample.shape[0]):
        if (single[i] == 1 and i + 3 < size):
            single[i + 3] = 3
    single.pop()
    sample['single'] = single

    return sample


def candlestruct(sample):
    import matplotlib.dates as mpd
    quotes = []
    pydate_array = sample.index.get_level_values('date').to_pydatetime()
    date_only_array = np.vectorize(lambda s: s.strftime('%Y-%m-%d'))(pydate_array)
    # date_only_series = pd.Series(date_only_array)
    N = sample.index.get_level_values('date').shape[0]
    ind = np.arange(N)
    for i in range(len(sample)):
        li = []
        # datet=datetime.datetime.strptime(sample.index.get_level_values('date'),'%Y%m%d')   #字符串日期转换成日期格式
        # datef=mpd.date2num(datetime.datetime.strptime(date_only_array[i],'%Y-%m-%d'))
        datef = ind[i]  # 日期转换成float days
        open_p = sample.open[i]
        close_p = sample.close[i]
        high_p = sample.high[i]
        low_p = sample.low[i]
        li = [datef, open_p, close_p, high_p, low_p]
        t = tuple(li)
        quotes.append(t)
    return quotes


def MACDPLOT(sample):
    quotes = candlestruct(sample)
    N = sample.index.get_level_values('date').shape[0]
    ind = np.arange(N)

    def format_date(x, pos=None):
        thisind = np.clip(int(x + 0.5), 0, N - 1)
        return sample.index.get_level_values('date')[thisind].strftime('%Y-%m-%d')

    fig = plt.figure()
    fig.set_size_inches(20.5, 12.5)
    # plt.xlabel('Trading Day')
    # plt.ylabel('MACD EMA')
    ax2 = fig.add_subplot(4, 1, 1)
    ax2.set_title("candlestick", fontsize='xx-large', fontweight='bold')

    # fig,ax=plt.subplots()
    # mpf.candlestick_ochl(ax2,quotes,width=0.2,colorup='r',colordown='g',alpha=1.0)
    # ax2.xaxis_date()
    # plt.setp(plt.gca().get_xticklabels(),rotation=30)
    # ax2.plot(ind,sample.close,'b-',marker='*')
    mpf.candlestick_ochl(ax2, quotes, width=0.6, colorup='r', colordown='g', alpha=1.0)
    ax2.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    ax2.plot(ind, sample.up, 'r-')
    ax2.plot(ind, sample.down, 'b-')
    ax2.grid(True)
    # t.legend()
    fig.autofmt_xdate()

    ax4 = fig.add_subplot(4, 1, 2, sharex=ax2)
    ax4.set_title("EMA13/SROC21", fontsize='xx-large', fontweight='bold')
    # ax1 = ax2.twinx()   #not working like it's
    ax4.plot(ind, sample.SROC, 'r-')
    ax4.grid(True)
    ax4.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    fig.autofmt_xdate()

    ax3 = fig.add_subplot(4, 1, 4, sharex=ax2)
    ax3.set_title("volume EMA", fontsize='xx-large', fontweight='bold')
    # ax1 = ax2.twinx()   #not working like it's
    ax3.bar(ind, sample.volume)
    ax3.plot(ind, sample.VolumeEMA, 'r-')
    ax3.grid(True)
    ax3.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    fig.autofmt_xdate()

    ax1 = fig.add_subplot(4, 1, 3, sharex=ax2)
    ax1.set_title('macd', fontsize='xx-large', fontweight='bold')
    ax1.grid(True)
    ax1.plot(ind, sample.MACDQ, 'r-', marker='*')
    ax1.plot(ind, sample.MACDSIG, 'o-')
    ax1.bar(ind, sample.MACDBlock)
    ax1.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    # ax2.set_yticks(np.linspace(ax2.get_yticks()[0], ax2.get_yticks()[-1], len(ax1.get_yticks())))
    fig.autofmt_xdate()
    plt.legend()

    code = sample.index.get_level_values('code')[0]

    plt.savefig('/home/mildone/monitor/' + 'Trend' + code + '.png')
    plt.show()
    plt.close()


def amountAnalyse(buydata):
    """
    @buydata as pdDataFrame
    e.g. buydata = QA.QA_fetch_get_stock_transaction_realtime('pytdx','600797') get current day's transaction
    e.g. data1=QA.QAFetch.QATdx.QA_fetch_get_stock_transaction('600797','2019-01-01','2019-04-11') get transaction among period of time

    """
    sellone = buydata[buydata['buyorsell'] == 1]
    sellone['amount'] = sellone['price'] * sellone['vol']
    sellone.sort_values("vol", inplace=True, ascending=False)

    buyone = buydata[buydata['buyorsell'] == 0]
    buyone['amount'] = buyone['price'] * buyone['vol']
    buyone.sort_values("vol", inplace=True, ascending=False)
    # print("Top buyer vol")
    # buyone[buyone['vol']>10]
    print("Top Seller vol")
    sellone.head(100)


def getStocklist():
    """
    get all stock as list
    usage as:
    QA.QA_util_log_info('GET STOCK LIST')
    stocks=getStocklist()
    """
    data = QA.QAFetch.QATdx.QA_fetch_get_stock_list('stock')
    stock = data['code'].index
    stocklist = []
    for code in stock:
        stocklist.append(code[0])
    return stocklist


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


def loadLocalDataIndex(stocks, start_date='2018-03-15', end_date='2020-08-01'):
    """
    data() as pdDataFrame
    stocks could be list of all the stock or some. if you pass single one e.g. 000001 it will get one only
    to get dedicated stock, using below method, and notice stockp() will be dataFrame
    stockp = data.select_code(stock)


    """
    QA.QA_util_log_info('load data from local DB')
    data = QA.QA_fetch_index_day_adv(stocks, start_date, end_date)
    return data


def loadFromCopy(file):
    """
    loaddata from file copy
    """
    return pd.DataFrame(pd.read_csv(file))


def calAngle(df):
    """
    trend angle based on provided dataframe
    """
    return ABuRegUtil.calc_regress_deg(df.close.values, show=False)


def getData(df, code):
    """
    split data per code from all market data
    """
    return df[df.code == code].reset_index(drop=True)


def trendBreak(pdDataFrame):
    """
    trendBreak based on provdied market data
    """

    from abupy import pd_rolling_max
    from abupy import pd_expanding_max
    # 当天收盘价格超过N1天内最高价格作为买入信号
    N1 = 20
    # 当天收盘价格超过N2天内最低价格作为卖出信号
    N2 = 15
    kl_pd = pdDataFrame
    # 通过rolling_max方法计算最近N1个交易日的最高价
    # kl_pd['n1_high'] = pd.rolling_max(kl_pd['high'], window=N1)
    kl_pd['n1_high'] = pd_rolling_max(kl_pd['high'], window=N1)
    # 表7-4所示

    # expanding_max
    # expan_max = pd.expanding_max(kl_pd['close'])
    expan_max = pd_expanding_max(kl_pd['close'])
    # fillna使用序列对应的expan_max
    kl_pd['n1_high'].fillna(value=expan_max, inplace=True)
    # 表7-5所示
    # print('kl_pd[0:5]:\n', kl_pd[0:5])

    from abupy import pd_rolling_min, pd_expanding_min
    # 通过rolling_min方法计算最近N2个交易日的最低价格
    # rolling_min与rolling_max类似
    # kl_pd['n2_low'] = pd.rolling_min(kl_pd['low'], window=N2)
    kl_pd['n2_low'] = pd_rolling_min(kl_pd['low'], window=N2)
    # expanding_min与expanding_max类似
    # expan_min = pd.expanding_min(kl_pd['close'])
    expan_min = pd_expanding_min(kl_pd['close'])
    # fillna使用序列对应的eexpan_min
    kl_pd['n2_low'].fillna(value=expan_min, inplace=True)

    # 当天收盘价格超过N天内的最高价或最低价, 超过最高价格作为买入信号买入股票持有
    buy_index = kl_pd[kl_pd['close'] > kl_pd['n1_high'].shift(1)].index
    kl_pd.loc[buy_index, 'signal'] = 1

    # 当天收盘价格超过N天内的最高价或最低价, 超过最低价格作为卖出信号
    sell_index = kl_pd[kl_pd['close'] < kl_pd['n2_low'].shift(1)].index
    kl_pd.loc[sell_index, 'signal'] = 0

    # kl_pd.signal.value_counts().plot(kind='pie', figsize=(5, 5))
    # plt.show()

    """
        将信号操作序列移动一个单位，代表第二天再将操作信号执行，转换得到持股状态
        这里不shift(1)也可以，代表信号产生当天执行，但是由于收盘价格是在收盘后
        才确定的，计算突破使用了收盘价格，所以使用shift(1)更接近真实情况
    """
    kl_pd['keep'] = kl_pd['signal'].shift(1)
    kl_pd['keep'].fillna(method='ffill', inplace=True)
    return kl_pd

    # 计算基准收益
    # kl_pd['benchmark_profit'] = np.log(
    # kl_pd['close'] / kl_pd['close'].shift(1))

    # 计算使用趋势突破策略的收益
    # kl_pd['trend_profit'] = kl_pd['keep'] * kl_pd['benchmark_profit']

    # 可视化收益的情况对比
    # kl_pd[['benchmark_profit', 'trend_profit']].cumsum().plot(grid=True,
    #                                                      figsize=(
    #                                                          14, 7))
    # plt.show()
    # kl_pd[['n2_low','n1_high','close']].plot(grid=True,figsize=(14,7))
    # kl_pd.close.plot(grid=True,figsize=(14.7))
    # plt.show()


def init_change(df):
    # change first (d[i].close-d[i-1].close)/d[i-1].close
    pp_array = [float(close) for close in df.close]
    temp_array = [(price1, price2) for price1, price2 in zip(pp_array[:-1], pp_array[1:])]
    change = list(map(lambda pp: reduce(lambda a, b: round((b - a) / a, 3), pp), temp_array))
    change.insert(0, 0)
    df['change'] = change
    # amplitude (d[i].high-d[i].low)/d[i-1].close)
    amp_arry = [float(amp) for amp in (df.high - df.low)]
    amp_temp = [(price1, price2) for price1, price2 in zip(amp_arry[:-1], pp_array[1:])]
    amplitude = list(map(lambda pp: reduce(lambda a, b: round(a / b, 3), pp), amp_temp))
    amplitude.insert(0, 0)
    df['amplitude'] = amplitude
    # sratio = QA.QA_fetch_get_stock_info(df.index.get_level_values('code')[0]).liutongguben[0]
    sratio = read_dictionary[df.index.get_level_values('code')[0]]
    df['SR'] = df['volume'] / sratio * 100
    return df


def init_trend(df, period=5):
    """
    period can be set based on situation.
    detect the angle change form negative to positive
    """
    trend = []
    ratio = []
    for i in range(0, df.shape[0]):
        # print(i)
        if (i < period):
            trend.append(calAngle(df.iloc[:period]))
            ratio.append(df.iloc[i].amount * period / sum(df.iloc[0:period].amount))
        else:
            trend.append(calAngle(df.iloc[i - period + 1:i + 1]))
            ratio.append(df.iloc[i].amount * 5 / sum(df.iloc[i - 5:i].amount))
    df['trend'] = trend
    df['amountRatio'] = ratio
    return df


def init_trendMACD(df, period=7):
    """
    period can be set based on situation.
    detect the angle change form negative to positive
    """
    trend = []
    ratio = []
    for i in range(0, df.shape[0]):
        # print(i)
        if (i < period):
            trend.append(calAngle(df.iloc[:period]))
            ratio.append(df.iloc[i].amount * period / sum(df.iloc[0:period].amount))
        else:
            trend.append(calAngle(df.iloc[i - period + 1:i + 1]))
            ratio.append(df.iloc[i].amount * 5 / sum(df.iloc[i - 5:i].amount))
    df['trend'] = trend
    df['amountRatio'] = ratio
    return df


"""

def trendSingle(df):

    buydate=[]
    for i in range(0,df.shape[0]):
        if(df.iloc[i].amountRatio>1 and df.iloc[i].trend>1 and df.iloc[i].amplitude<0.07 and df.iloc[i].change<0.03 
          and df.iloc[i].change>0.01):
            buydate.append((i,df.iloc[i].date))
    return buydate
"""


def trendSingle(df, period=7):
    """
    @paramater dataframe
    return True or False
    Justification:
    1. latest 20 days angle >0
    2. change (0.1~0.3)
    3.

    """
    # df['trend']=0
    # df['amountRatio']=0
    # trend=0
    # amountRatio=0
    keep = 5
    init_change(df)
    init_trend(df)
    single = [0, 0]
    # temp =[]
    for i in range(1, df.shape[0]):
        """
        if(i<period):
            #trend.append(calAngle(df.iloc[:period]))
            trend=calAngle(df.iloc[:period])
            #print(trend)
            #ratio.append(df.iloc[i].amount*period/sum(df.iloc[0:period].amount))
            amountRatio=df.iloc[i].amount*period/sum(df.iloc[0:period].amount)
        else:
            #trend.append(calAngle(df.iloc[i-period+1:i+1]))
            trend=calAngle(df.iloc[i-period+1:i+1])
            #print(trend)
            #print(calAngle(df.iloc[i-period+1:i+1]))
            #ratio.append(df.iloc[i].amount*5/sum(df.iloc[i-5:i].amount))
            #print(df.iloc[i].amount*5/sum(df.iloc[i-5:i].amount))
            amountRatio=df.iloc[i].amount*5/sum(df.iloc[i-5:i].amount)
        """
        if (1.5 > df.iloc[i].amountRatio > 1 and df.iloc[i].trend > 1 and df.iloc[i].amplitude > 0.05
                and 0.01 < df.iloc[i].change < 0.03 and df.iloc[i].SR < 0.05):
            single.append(1)
        else:
            single.append(0)
    # single.append(0)
    # single.extend(temp[:-1])
    # print("done here")
    # single.insert(0,0)
    single.pop()
    # print(single)
    size = len(single)
    # for simple purpose, set last (Keep) as 0,simple take 3 days as holding max

    # print("checking operation single")
    for i in range(0, size - 5):
        if single[i] == 1:
            bar = df.iloc[i].open * 1.2
            j = i
            if (df.iloc[j + 1].change > 0 and df.iloc[j + 1].close < bar):
                single[j + 1] = 0
            else:
                single[j + 1] = 3
                continue
            if ((df.iloc[j + 2].change > 0 and df.iloc[j + 2].close < bar) or
                    (df.iloc[j + 2].change < 0 and df.iloc[j + 2].close > df.iloc[i].open)):
                single[j + 2] = 0

            else:
                single[j + 2] = 3
                continue
            if ((df.iloc[j + 3].change > 0 and df.iloc[j + 3].close < bar)
                    or (df.iloc[j + 3].change < 0 and df.iloc[j + 3].close > df.iloc[i].open)):
                single[j + 3] = 0
            else:
                single[j + 3] = 3
                continue
            if ((df.iloc[j + 4].change > 0 and df.iloc[j + 4].close < bar)
                    or (df.iloc[j + 4].change < 0 and df.iloc[j + 4].close > df.iloc[i].open)):
                single[j + 4] = 0
            else:
                single[j + 4] = 3
                continue
            single[j + 5] = 3

    single[-5:] = [0, 0, 0, 0, 0]

    df['single'] = single
    # df['single']=df['keep'].shift(1)
    # df['single'].fillna(method='ffill',inplace=True)
    print(df.index.levels[1])
    return df


def nineTurn(sample, period=7):
    sample['highEMAS25'] = QA.EMA(sample.high, 25)
    sample['lowEMAS25'] = QA.EMA(sample.low, 25)
    sample['Stunel'] = sample.highEMAS25 - sample.lowEMAS25
    sample['highEMAL90'] = QA.EMA(sample.high, 90)
    sample['lowEMAL90'] = QA.EMA(sample.low, 90)
    single = [0 for _ in range(13)]
    N = sample.shape[0]
    for i in range(13, N):
        Raise = 1
        Down = 1
        # print('round {}'.format(i))
        for j in range(i - 8, i + 1):
            # print('round {}, index {}'.format(i,j))
            if (sample.close[j] > sample.close[j - 4]):
                Raise = Raise * 1
                Down = Down * 0
            else:
                Raise = Raise * 0
                Down = Down * 1
        # if(Raise and max(sample.close[i],sample.close[i-1])>max(sample.close[i-2],sample.close[i-3])):
        # if (Raise and sample.close[i] > sample.close[i - 2]):
        if (Down and sample.close[i] < sample.lowEMAS25[i]):
            # for n in range(i - 9, i):
            single.append(1)
        else:
            single.append(0)
    for i in range(len(single)):
        if (i + 5 < len(single) and single[i] == 1):
            single[i + 5] = 3
    sample['single'] = single

    return sample


def trendSingleNew(df, period=7):
    # df['trend']=0
    # df['amountRatio']=0
    # trend=0
    # amountRatio=0
    # keep = ３
    init_change(df)
    init_trend(df)
    single = [0, 0]
    # temp =[]
    for i in range(1, df.shape[0]):
        if (1.5 > df.iloc[i].amountRatio > 1 and df.iloc[i].trend > 1 and df.iloc[i].amplitude > 0.05
                and 0.01 < df.iloc[i].change < 0.03 and df.iloc[i].SR < 0.05):
            single.append(1)
        else:
            single.append(0)
    # single.append(0)
    # single.extend(temp[:-1])
    # print("done here")
    # single.insert(0,0)
    single.pop()
    # print(single)
    size = len(single)
    # for simple purpose, set last (Keep) as 0,simple take 3 days as holding max

    # print("checking operation single")
    for i in range(0, size - 3):
        if single[i] == 1:
            bar = df.iloc[i].open * 1.2
            j = i
            if (df.iloc[j + 1].change > 0 and df.iloc[j + 1].close < bar):
                single[j + 1] = 0
            else:
                single[j + 1] = 3
                continue
            if ((df.iloc[j + 2].change > 0 and df.iloc[j + 2].close < bar) or
                    (df.iloc[j + 2].change < 0 and df.iloc[j + 2].close > df.iloc[i].open)):
                single[j + 2] = 0

            else:
                single[j + 2] = 3
                continue

            single[j + 3] = 3

    single[-3:] = [0, 0, 0]

    df['single'] = single
    # df['single']=df['keep'].shift(1)
    # df['single'].fillna(method='ffill',inplace=True)
    print(df.index.levels[1])
    return df


def ana(df):
    # df = loadLocalData(code,'2014-01-01','2019-09-30')
    # df = df.to_qfq()
    init_change(df)
    init_trend(df)
    if (1.5 > df.iloc[-1].amountRatio > 1 and df.iloc[-1].trend > 1 and df.iloc[-1].amplitude > 0.05
            and 0.01 < df.iloc[-1].change < 0.03 and df.iloc[-1].SR < 0.05):
        return True
    else:
        return False


def detect(df):
    init_change(df)
    init_trend(df)
    single = [0, 0]
    # temp =[]
    for i in range(1, df.shape[0]):
        """
        if(i<period):
            #trend.append(calAngle(df.iloc[:period]))
            trend=calAngle(df.iloc[:period])
            #print(trend)
            #ratio.append(df.iloc[i].amount*period/sum(df.iloc[0:period].amount))
            amountRatio=df.iloc[i].amount*period/sum(df.iloc[0:period].amount)
        else:
            #trend.append(calAngle(df.iloc[i-period+1:i+1]))
            trend=calAngle(df.iloc[i-period+1:i+1])
            #print(trend)
            #print(calAngle(df.iloc[i-period+1:i+1]))
            #ratio.append(df.iloc[i].amount*5/sum(df.iloc[i-5:i].amount))
            #print(df.iloc[i].amount*5/sum(df.iloc[i-5:i].amount))
            amountRatio=df.iloc[i].amount*5/sum(df.iloc[i-5:i].amount)
        """
        if (1.5 > df.iloc[i].amountRatio > 1 and df.iloc[i].trend > 1 and df.iloc[i].amplitude > 0.05
                and 0.01 < df.iloc[i].change < 0.03 and df.iloc[i].SR < 0.05):
            single.append(1)
        else:
            single.append(0)
    # single.append(0)
    # single.extend(temp[:-1])
    # print("done here")

    # single.insert(0,0)
    single.pop()
    if (single[-1] == 1):
        return True
    else:
        return False


def generateplot(code):
    import datetime
    cur = datetime.datetime.now()
    endtime = str(cur.year) + '-' + str(cur.month) + '-' + str(cur.day)
    sample = loadLocalData(code, '2019-08-01', endtime)
    sample = sample.to_qfq()
    sampleData = sample.select_code(code)
    MACACalculate(sampleData.data)
    MACDPLOT(sampleData.data)


def gitAction(candidate):
    from git import Repo
    r = Repo('/home/mildone/monitor')
    commitfile = [r'/home/mildone/monitor/result.log', r'/home/mildone/monitor/data.csv']

    prefix = '/home/mildone/monitor/'
    if (len(candidate) > 0):
        for i in range(len(candidate)):
            generateplot(candidate[i])
            pltfile = prefix + 'Trend' + candidate[i] + '.png'
            commitfile.append(pltfile)
    r.index.add(commitfile)
    cur = datetime.datetime.now()
    msg = str(cur.year) + '-' + str(cur.month) + '-' + str(cur.day) + ' commit'
    r.index.commit(msg)
    r.remote().push('master')


def dianostic(code):
    cur = datetime.datetime.now()
    endtime = str(cur.year) + '-' + str(cur.month) + '-' + str(cur.day)
    daydata = QA.QA_fetch_stock_day_adv(code, '2019-04-01', endtime)
    # MINMACACalculate(mindata.data)
    # MINMACDPLOT(mindata.data,index,formate)
    MACACalculate(daydata.data)
    MACDPLOT(daydata.data[:])


def EMAOP(sample):
    period = 5
    sample['EMA13'] = QA.EMA(sample.close, 13)
    sample['optimism'] = sample.high - sample.EMA13
    sample['pessmist'] = sample.low - sample.EMA13
    pp_array = [float(optimism) for optimism in sample.optimism]
    temp_array = [(price1, price2) for price1, price2 in zip(pp_array[:-1], pp_array[1:])]
    change = list(map(lambda pp: reduce(lambda a, b: round((b - a) / a, 3), pp), temp_array))
    change.insert(0, 0)
    trend = []

    for i in range(0, sample.shape[0]):
        # print(i)
        if (i < period):
            trend.append(calAngle(sample.iloc[:period]))
            # ratio.append(df.iloc[i].amount * period / sum(df.iloc[0:period].amount))
        else:
            trend.append(calAngle(sample.iloc[i - period + 1:i + 1]))
            # ratio.append(df.iloc[i].amount * 5 / sum(df.iloc[i - 5:i].amount))
    sample['trend'] = trend

    size = sample.shape[0]
    single = [0]
    for i in range(sample.shape[0]):
        if (sample.pessmist[i - 1] < 0 and sample.pessmist[i] >= 0 and i - 1 >= 0
                and sample.trend[i] > sample.trend[i - 1] and sample.trend[i] > 0):
            # print(sample.index.get_level_values('date')[i])
            single.append(1)
        else:
            single.append(0)
    for i in range(sample.shape[0]):
        if (single[i] == 1 and i + 3 < size):
            single[i + 3] = 3
    single.pop()
    sample['single'] = single

    return sample


def winRatio(Account):
    # input as Account after backtest
    # output is wining ratio of all the trade
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
    return win / (win + loss)


def MACD_JCSC(dataframe, SHORT=12, LONG=26, M=9):
    """
    1.DIF向上突破DEA，买入信号参考。
    2.DIF向下跌破DEA，卖出信号参考。
    """
    CLOSE = dataframe.close
    DIFF = QA.EMA(CLOSE, SHORT) - QA.EMA(CLOSE, LONG)
    DEA = QA.EMA(DIFF, M)
    MACD = 2 * (DIFF - DEA)

    CROSS_JC = QA.CROSS(DIFF, DEA)
    CROSS_SC = QA.CROSS(DEA, DIFF)
    ZERO = 0

    SC = np.where(CROSS_SC == 1, 3, 0)
    m = np.where(CROSS_JC == 1, 1, SC)

    single = [0] + m[:-1].tolist()

    dataframe['single'] = single

    # dataframe['single'] = m.tolist()

    return dataframe


def c30Day(sample, short=30):
    """
    1.DIF向上突破DEA，买入信号参考。
    2.DIF向下跌破DEA，卖出信号参考。
    """
    sample['short'] = QA.EMA(sample.close, short)

    CROSS_5 = QA.CROSS(sample.close, sample.short)
    CROSS_15 = QA.CROSS(sample.short, sample.close)

    C15 = np.where(CROSS_15 == 1, 3, 0)
    m = np.where(CROSS_5 == 1, 1, C15)
    # only can buytomorrow, so shift single
    single = m[:-1].tolist()
    single.insert(0, 0)
    sample['single'] = single
    # sample['single']=m.tolist()

    return sample


def doubleAvgDay(sample, short=5, long=15):
    """
    1.DIF向上突破DEA，买入信号参考。
    2.DIF向下跌破DEA，卖出信号参考。
    """
    init_trend(sample)
    sample['short'] = QA.EMA(sample.close, short)
    sample['long'] = QA.EMA(sample.close, long)
    CROSS_5 = QA.CROSS(sample.short, sample.long)
    CROSS_15 = QA.CROSS(sample.long, sample.short)

    C15 = np.where(CROSS_15 == 1, 3, 0)
    m = np.where(CROSS_5 == 1, 1, C15)
    single = [0] + m[:-1].tolist()
    sample['single'] = single
    # sample['single']=m.tolist()
    for i in range(sample.shape[0]):
        if (sample.trend[i] < 0):
            pass

    return sample


def doubleAvgmin(dd, short=5, long=15, freq='60min'):
    """
    1.DIF向上突破DEA，买入信号参考。
    2.DIF向下跌破DEA，卖出信号参考。
    """
    # init_trend(dd,15)
    # dd['MA60'] = QA.MA(dd.close, 60)
    start = dd.index.get_level_values(dayindex)[0].strftime(dayformate)
    end = dd.index.get_level_values(dayindex)[-1].strftime(dayformate)
    mindata = QA.QA_fetch_stock_min_adv(dd.index.get_level_values('code')[0], start, end, frequence=freq)
    sample = mindata.data
    # print(sample)
    sample['short'] = QA.EMA(sample.close, short)
    sample['MA60'] = QA.MA(sample.close, 60)
    sample['long'] = QA.EMA(sample.close, long)
    CROSS_5 = QA.CROSS(sample.short, sample.long)
    CROSS_15 = QA.CROSS(sample.long, sample.short)

    C15 = np.where(CROSS_15 == 1, 3, 0)
    m = np.where(CROSS_5 == 1, 1, C15)
    # single = m[:-1].tolist()
    # single.insert(0, 0)
    sample['single'] = m.tolist()
    sig = [0]
    for i in range(1, len(dd)):
        temp = sample[sample.index.get_level_values(index).strftime(dayformate) == dd.index.get_level_values(dayindex)[
            i].strftime(dayformate)][:-1]
        # print(temp.shape[0])
        tmp = sample[sample.index.get_level_values(index).strftime(dayformate) == dd.index.get_level_values(dayindex)[
            i - 1].strftime(dayformate)][-1:]
        sing = temp.single.sum() + tmp.single.sum()
        sig.append(sing)

        '''
        if( len(temp.single)>=3 and temp.single[-2]>=4):
            sig.append(3)
        else:
            sig.append(temp.single[-2])
        '''

    try:
        dd['single'] = sig

    except:
        print('error with {}'.format(sample.index.get_level_values('code')[0]))
        dd['single'] = 0

    return dd


def triNetv5(sample, short=5, long=10, freq='15min'):
    SellAnalysis(sample)
    # sample['EMAVolume'] = QA.EMA(sample.volume,5)
    # to get Week and 60 minutes syntony together
    # get week trend
    # 60 76, 30 79, 30 74 more
    # 15 min is the best for now, with 11/10 (5-10 11, 5-15 10 5-20 )

    # with same entry point selection, we chose different exit measure which comes from Bilibili show
    import quant.weekTrend as wt

    # get day level status
    sample['EMA5'] = QA.EMA(sample.close, 5)
    sample['EMA10'] = QA.EMA(sample.close, 10)
    sample['dtrend'] = sample['EMA5'] - sample['EMA10']
    sample.fillna(method='ffill', inplace=True)
    wstart = '2010-01-01'
    code = sample.index.get_level_values('code')[-1]
    wend = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    temp = QA.QA_fetch_stock_day_adv(code, wstart, wend).data
    wd = wt.wds(temp)
    wd = wt.weektrend(wd)

    start = sample.index.get_level_values(dayindex)[0].strftime(dayformate)
    end = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    mindata = QA.QA_fetch_stock_min_adv(sample.index.get_level_values('code')[0], start, end, frequence=freq)
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
    if (freq == '60min'):
        anchor = -2
    elif (freq == '30min'):
        anchor = -4
    elif (freq == '15min'):
        anchor = -8
    for i in range(1, len(sample)):
        graccident = 0
        if (sample.change[i] < 0 and (sample.volume[i] / sample.EMAVolume[i]) > 1.2 and (
                sample.open[i] - sample.close[i]) / (sample.high[i] - sample.low[i]) > 0.8):
            graccident = 1
            # we got a green day

        dtime = sample.index.get_level_values(dayindex)[i]
        wtime = getWeekDate(dtime)
        windex = wd[wd.date == wtime.strftime(dayformate)].index[0]
        # here use index to get value interested, here we take change of MACDBlock to get the short trend in week level
        direction = wd.loc[windex].trend
        temp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[
            i].strftime(dayformate)][:anchor]
        tmp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[
            i - 1].strftime(dayformate)][anchor:]
        sing = temp.single.sum() + tmp.single.sum()
        if (direction > 0 and sample.dtrend[i] > 0 and sing == 1):
            sig.append(1)
        elif ((direction < 0 and sing > 1) or graccident == 1):
            sig.append(3)
        else:
            sig.append(0)

    try:
        # sample['single'] = [0]+sig[:-1]
        sample['single'] = sig

    except:
        print('error with {}'.format(sample.index.get_level_values('code')[0]))
        sample['single'] = 0

    return sample


def triNetv4(sample, short=5, long=10, freq='15min'):
    # to get Week and 60 minutes syntony together
    # get week trend
    # 60 76, 30 79, 30 74 more
    # 15 min is the best for now, with 11/10 (5-10 11, 5-15 10 5-20 )
    import quant.weekTrend as wt
    print('deal with {}'.format(sample.index.get_level_values('code')[-1]))
    print('*' * 100)

    # get day level status
    sample['EMA5'] = QA.EMA(sample.close, 5)
    sample['EMA10'] = QA.EMA(sample.close, 10)
    sample['dtrend'] = sample['EMA5'] - sample['EMA10']

    sample.fillna(method='ffill', inplace=True)
    wstart = '2010-01-01'
    code = sample.index.get_level_values('code')[-1]
    wend = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    temp = QA.QA_fetch_stock_day_adv(code, wstart, wend).data
    wd = wt.wds(temp)
    wd = wt.weektrend(wd)

    start = sample.index.get_level_values(dayindex)[0].strftime(dayformate)
    end = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    mindata = QA.QA_fetch_stock_min_adv(sample.index.get_level_values('code')[0], start, end, frequence=freq)
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
    if (freq == '60min'):
        anchor = -2
    elif (freq == '30min'):
        anchor = -4
    elif (freq == '15min'):
        anchor = -8
    for i in range(1, len(sample)):
        dtime = sample.index.get_level_values(dayindex)[i]
        wtime = getWeekDate(dtime)
        windex = wd[wd.date == wtime.strftime(dayformate)].index[0]
        # here use index to get value interested, here we take change of MACDBlock to get the short trend in week level
        direction = wd.loc[windex].trend
        temp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[
            i].strftime(dayformate)][:anchor]
        tmp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[
            i - 1].strftime(dayformate)][anchor:]
        sing = temp.single.sum() + tmp.single.sum()
        if (direction > 0 and sample.dtrend[i] > 0 and sing == 1):
            sig.append(1)
        elif (direction < 0 and sample.dtrend[i] < 0 and sing > 1):
            sig.append(sing)
        else:
            sig.append(0)

    try:
        # sample['single'] = [0]+sig[:-1]
        sample['single'] = sig

    except:
        print('error with {}'.format(sample.index.get_level_values('code')[0]))
        sample['single'] = 0

    return sample


def SellAnalysis(df, period=5):
    pp_array = [float(close) for close in df.close]
    temp_array = [(price1, price2) for price1, price2 in zip(pp_array[:-1], pp_array[1:])]
    change = list(map(lambda pp: reduce(lambda a, b: round((b - a) / a, 3), pp), temp_array))
    change.insert(0, 0)
    df['change'] = change

    amp_arry = [float(amp) for amp in (df.high - df.low)]
    amp_temp = [(price1, price2) for price1, price2 in zip(amp_arry[:-1], pp_array[1:])]
    amplitude = list(map(lambda pp: reduce(lambda a, b: round(a / b, 3), pp), amp_temp))
    amplitude.insert(0, 0)
    df['amplitude'] = amplitude
    df['EMAVolume'] = QA.EMA(df.volume, period)
    return df
    # df['vr'] = (df.volume - df.EMAVolume)/df.EMAVolume


def EMA_MAV3(sample, period=20):
    sample['MA'] = QA.MA(sample.close, period)
    sample['EMA'] = QA.EMA(sample.close, period)

    CROSS_5 = QA.CROSS(sample.EMA, sample.MA)
    CROSS_15 = QA.CROSS(sample.MA, sample.EMA)

    C15 = np.where(CROSS_15 == 1, 3, 0)
    m = np.where(CROSS_5 == 1, 1, C15)
    single = m[:-1].tolist()
    single.insert(0, 0)
    sample['single'] = single
    return sample


def triNetv6(sample, short=5, long=10, freq='15min'):
    SellAnalysis(sample)
    # sample['EMAVolume'] = QA.EMA(sample.volume,5)
    # to get Week and 60 minutes syntony together
    # get week trend
    # 60 76, 30 79, 30 74 more
    # 15 min is the best for now, with 11/10 (5-10 11, 5-15 10 5-20 )

    # with same entry point selection, we chose different exit measure which comes from Bilibili show
    import quant.weekTrend as wt

    # get day level status
    sample['EMA5'] = QA.EMA(sample.close, 5)
    sample['EMA10'] = QA.EMA(sample.close, 10)
    sample['dtrend'] = sample['EMA5'] - sample['EMA10']
    sample.fillna(method='ffill', inplace=True)
    wstart = '2010-01-01'
    code = sample.index.get_level_values('code')[-1]
    wend = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    temp = QA.QA_fetch_stock_day_adv(code, wstart, wend).data
    wd = wt.wds(temp)
    wd = wt.weektrend(wd)

    start = sample.index.get_level_values(dayindex)[0].strftime(dayformate)
    end = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    mindata = QA.QA_fetch_stock_min_adv(sample.index.get_level_values('code')[0], start, end, frequence=freq)
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
    if (freq == '60min'):
        anchor = -2
    elif (freq == '30min'):
        anchor = -4
    elif (freq == '15min'):
        anchor = -8
    for i in range(1, len(sample)):

        dtime = sample.index.get_level_values(dayindex)[i]
        wtime = getWeekDate(dtime)
        windex = wd[wd.date == wtime.strftime(dayformate)].index[0]
        # here use index to get value interested, here we take change of MACDBlock to get the short trend in week level
        direction = wd.loc[windex].ws
        temp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[
            i].strftime(dayformate)][:anchor]
        tmp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[
            i - 1].strftime(dayformate)][anchor:]
        sing = temp.single.sum() + tmp.single.sum()
        if (direction == 1 and sing == 1):
            sig.append(1)
        elif (direction == 3 and sing == 3):
            sig.append(3)
        else:
            sig.append(0)

    try:
        # sample['single'] = [0]+sig[:-1]
        sample['single'] = sig

    except:
        print('error with {}'.format(sample.index.get_level_values('code')[0]))
        sample['single'] = 0

    return sample


def PlotBySe(day, period=26):
    import quant.MACD as macd
    day['EMA120'] = QA.EMA(day.close, 120)
    day['EMA60'] = QA.EMA(day.close, 60)
    day['EMA20'] = QA.EMA(day.close, 20)
    day['BIAS'] = (day.close - day.EMA120) * 100 / day.EMA120
    print(day)
    quotes = macd.MINcandlestruct(day, dayindex, dayformate)
    # N = sample.index.get_level_values(index).shape[0]
    N = day.shape[0]
    ind = np.arange(N)
    day['EMA'] = QA.EMA(day.close, period)

    def format_date(x, pos=None):
        thisind = np.clip(int(x + 0.5), 0, N - 1)
        return day.index.get_level_values(dayindex)[thisind].strftime(dayformate)

    fig = plt.figure()
    fig.set_size_inches(40.5, 20.5)
    ax2 = fig.add_subplot(2, 1, 1)
    ax2.set_title("candlestick", fontsize='xx-large', fontweight='bold')

    mpf.candlestick_ochl(ax2, quotes, width=0.6, colorup='r', colordown='g', alpha=1.0)
    ax2.plot(ind, day.EMA120, 'r-', label='EMA120')
    ax2.plot(ind, day.EMA60, 'blue', label='EMA60')
    ax2.plot(ind, day.EMA20, 'purple', label='EMA20')
    '''
    for i in range(N):
        if (day.single[i] == 1):
            ax2.axvline(x=i, ls='--', color='red')
        if (day.single[i] == 3):
            ax2.axvline(x=i, ls='--', color='green')
    '''
    ax2.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    ax2.grid(True)
    ax2.legend(loc='best')
    fig.autofmt_xdate()

    ax3 = fig.add_subplot(2, 1, 2, sharex=ax2)
    ax3.bar(ind, day.BIAS, color='blue')
    # ax3.axhline(y=0,ls='--',color='yellow')
    ax3.grid(True)
    ax3.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    fig.autofmt_xdate()

    plt.show()


def TrendFinder(day, short=20, mid=30, long=60):
    # 20, 30 , 60   8/10
    # 10, 20, 60   6.7/10
    # 10, 30, 60   7.2/10
    day['long'] = QA.EMA(day.close, long)
    day['mid'] = QA.EMA(day.close, mid)
    day['short'] = QA.EMA(day.close, short)
    day['BIAS'] = (day.close - day.long) * 100 / day.long
    day['CS'] = (day.close - day.short) * 100 / day.short
    day['SM'] = (day.short - day.mid) * 100 / day.mid
    day['ML'] = (day.mid - day.long) * 100 / day.long
    sig = []
    buy = 0
    sell = 0
    for i in range(day.shape[0]):
        if (day.CS[i] > 0 and day.SM[i] > 0 and day.ML[i] > 0 and buy == 0):
            sig.append(1)
            buy = 1
            sell = 0
        elif (day.CS[i] < 0 and day.SM[i] < 0 and sell == 0):
            sig.append(3)
            sell = 1
            buy = 0
        else:
            sig.append(0)
    day['single'] = sig
    # day['single'] = [0]+sig[:-1]

    return day


def EMA_MA(sample, period=20):
    import quant.weekTrend as wt
    # get day level status
    sample['MA'] = QA.MA(sample.close, period)
    sample['EMA'] = QA.EMA(sample.close, period)
    # sample.fillna(method='ffill',inplace=True)
    # wstart = '2010-01-01'
    code = sample.index.get_level_values('code')[-1]
    wend = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    # temp = QA.QA_fetch_stock_day_adv(code,wstart,wend).data
    # wd = wt.wds(temp)
    # wd = wt.weektrend(wd)

    start = sample.index.get_level_values(dayindex)[0].strftime(dayformate)
    end = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    CROSS_5 = QA.CROSS(sample.EMA, sample.MA)
    CROSS_15 = QA.CROSS(sample.MA, sample.EMA)

    C15 = np.where(CROSS_15 == 1, 3, 0)
    m = np.where(CROSS_5 == 1, 1, C15)
    # single = m[:-1].tolist()
    # single.insert(0, 0)
    # single = m[:-1].tolist()
    # single.insert(0, 0)
    sample['single'] = m.tolist()
    # sample['single']=single
    return sample


def EMA_MAv2(sample, period=20):
    import quant.weekTrend as wt
    # get day level status
    sample['MA'] = QA.MA(sample.close, period)
    sample['EMA'] = QA.EMA(sample.close, period)
    # sample.fillna(method='ffill',inplace=True)
    # wstart = '2010-01-01'
    code = sample.index.get_level_values('code')[-1]
    wend = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    # temp = QA.QA_fetch_stock_day_adv(code,wstart,wend).data
    # wd = wt.wds(temp)
    # wd = wt.weektrend(wd)

    start = sample.index.get_level_values(dayindex)[0].strftime(dayformate)
    end = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    CROSS_5 = QA.CROSS(sample.EMA, sample.MA)
    CROSS_15 = QA.CROSS(sample.MA, sample.EMA)

    C15 = np.where(CROSS_15 == 1, 3, 0)
    m = np.where(CROSS_5 == 1, 1, C15)
    # single = m[:-1].tolist()
    # single.insert(0, 0)
    single = m[:-1].tolist()
    single.insert(0, 0)
    # sample['single'] = m.tolist()
    sample['single'] = single
    return sample


def PlotBySe(day, period=26):
    import quant.MACD as macd
    print(day)
    quotes = macd.MINcandlestruct(day, dayindex, dayformate)
    # N = sample.index.get_level_values(index).shape[0]
    N = day.shape[0]
    ind = np.arange(N)
    day['EMA'] = QA.EMA(day.close, period)

    def format_date(x, pos=None):
        thisind = np.clip(int(x + 0.5), 0, N - 1)
        return day.index.get_level_values(dayindex)[thisind].strftime(dayformate)

    fig = plt.figure()
    fig.set_size_inches(40.5, 20.5)
    ax2 = fig.add_subplot(1, 1, 1)
    ax2.set_title("candlestick", fontsize='xx-large', fontweight='bold')

    mpf.candlestick_ochl(ax2, quotes, width=0.6, colorup='r', colordown='g', alpha=1.0)
    ax2.plot(ind, day.EMA, 'r-', label='EMA')

    for i in range(N):
        if (day.single[i] == 1):
            ax2.axvline(x=i, ls='--', color='red')
        if (day.single[i] == 3):
            ax2.axvline(x=i, ls='--', color='green')
    ax2.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    ax2.grid(True)
    ax2.legend(loc='best')
    fig.autofmt_xdate()
    plt.show()


def ATRStrategy(sample):
    # no good at all

    atr20 = QA.QA_indicator_ATR(sample, 20)
    atr42 = QA.QA_indicator_ATR(sample, 42)
    buy = QA.CROSS(atr20.ATR, atr42.ATR)
    sell = QA.CROSS(atr42.ATR, atr20.ATR)

    C15 = np.where(sell == 1, 3, 0)
    m = np.where(buy == 1, 1, C15)
    single = [0] + m[:-1].tolist()
    sample['single'] = single

    return sample


def getWeekDate(daytime):
    # daytime will be pandas datetime
    # return Timestamp('2020-05-11 00:00:00')
    return daytime + dateutil.relativedelta.relativedelta(days=(6 - daytime.dayofweek))


def triNetv3(sample, short=5, long=10, freq='15min'):
    # to get Week and 60 minutes syntony together
    # get week trend
    # A50 64% 30 5 15 12/10
    #
    # 60 76, 30 79, 30 74 more
    # 15 min is the best for now, with 11/10 (5-10 11, 5-15 10 5-20 )
    import quant.weekTrend as wt
    print('deal with {}'.format(sample.index.get_level_values('code')[-1]))
    print('*' * 100)

    sample.fillna(method='ffill', inplace=True)
    wstart = '2010-01-01'
    code = sample.index.get_level_values('code')[-1]
    wend = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    temp = QA.QA_fetch_stock_day_adv(code, wstart, wend).data
    wd = wt.wds(temp)
    wd = wt.weektrend(wd)

    start = sample.index.get_level_values(dayindex)[0].strftime(dayformate)
    end = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    mindata = QA.QA_fetch_stock_min_adv(sample.index.get_level_values('code')[0], start, end, frequence=freq)
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
    if (freq == '60min'):
        anchor = -2
    elif (freq == '30min'):
        anchor = -4
    elif (freq == '15min'):
        anchor = -8
    for i in range(1, len(sample)):
        dtime = sample.index.get_level_values(dayindex)[i]
        wtime = getWeekDate(dtime)
        windex = wd[wd.date == wtime.strftime(dayformate)].index[0]
        # here use index to get value interested, here we take change of MACDBlock to get the short trend in week level
        direction = wd.loc[windex].trend
        temp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[
            i].strftime(dayformate)][:anchor]
        tmp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[
            i - 1].strftime(dayformate)][anchor:]
        sing = temp.single.sum() + tmp.single.sum()
        if (direction > 0 and sing == 1):
            sig.append(1)
        elif (direction < 0 and sing == 3):
            sig.append(sing)
        else:
            sig.append(0)

    try:
        # sample['single'] = [0]+sig[:-1]
        sample['single'] = sig

    except:
        print('error with {}'.format(sample.index.get_level_values('code')[0]))
        sample['single'] = 0

    return sample


def triNetv2(sample, short=5, long=10, freq='15min'):
    # to get Week and 60 minutes syntony together
    # get week trend
    # A50 64% 30 5 15 12/10
    #
    # 60 76, 30 79, 30 74 more
    # 15 min is the best for now, with 11/10 (5-10 11, 5-15 10 5-20 )
    import quant.weekTrend as wt
    print('deal with {}'.format(sample.index.get_level_values('code')[-1]))
    print('*' * 100)

    sample.fillna(method='ffill', inplace=True)
    wstart = '2010-01-01'
    code = sample.index.get_level_values('code')[-1]
    wend = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    temp = QA.QA_fetch_stock_day_adv(code, wstart, wend).data
    wd = wt.wds(temp)
    wd = wt.weektrend(wd)

    start = sample.index.get_level_values(dayindex)[0].strftime(dayformate)
    end = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    mindata = QA.QA_fetch_stock_min_adv(sample.index.get_level_values('code')[0], start, end, frequence=freq)
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
    if (freq == '60min'):
        anchor = -2
    elif (freq == '30min'):
        anchor = -4
    elif (freq == '15min'):
        anchor = -8
    for i in range(1, len(sample)):
        dtime = sample.index.get_level_values(dayindex)[i]
        wtime = getWeekDate(dtime)
        windex = wd[wd.date == wtime.strftime(dayformate)].index[0]
        # here use index to get value interested, here we take change of MACDBlock to get the short trend in week level
        direction = wd.loc[windex].change
        temp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[
            i].strftime(dayformate)][:anchor]
        tmp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[
            i - 1].strftime(dayformate)][anchor:]
        sing = temp.single.sum() + tmp.single.sum()
        if (direction > 0 and sing == 1):
            sig.append(1)
        elif (direction < 0 and sing == 3):
            sig.append(sing)
        else:
            sig.append(0)

    try:
        # sample['single'] = [0]+sig[:-1]
        sample['single'] = sig

    except:
        print('error with {}'.format(sample.index.get_level_values('code')[0]))
        sample['single'] = 0

    return sample


def trendWeekMin(sample, short=5, long=10, freq='15min'):
    # to get Week and 60 minutes syntony together
    # get week trend
    # A50 64% 30 5 15 12/10
    #
    # 60 76, 30 79, 30 74 more
    # 15 min is the best for now, with 11/10 (5-10 11, 5-15 10 5-20 )
    import quant.weekTrend as wt
    print('deal with {}'.format(sample.index.get_level_values('code')[-1]))
    print('*' * 100)

    sample.fillna(method='ffill', inplace=True)
    wstart = '2010-01-01'
    code = sample.index.get_level_values('code')[-1]
    wend = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    temp = QA.QA_fetch_stock_day_adv(code, wstart, wend).data
    wd = wt.wds(temp)
    wd = wt.weektrend(wd)

    start = sample.index.get_level_values(dayindex)[0].strftime(dayformate)
    end = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    mindata = QA.QA_fetch_stock_min_adv(sample.index.get_level_values('code')[0], start, end, frequence=freq)
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
    if (freq == '60min'):
        anchor = -2
    elif (freq == '30min'):
        anchor = -4
    elif (freq == '15min'):
        anchor = -8
    for i in range(1, len(sample)):
        dtime = sample.index.get_level_values(dayindex)[i]
        wtime = getWeekDate(dtime)
        windex = wd[wd.date == wtime.strftime(dayformate)].index[0]
        # here use index to get value interested, here we take change of MACDBlock to get the short trend in week level
        direction = wd.loc[windex].CS
        temp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[
            i].strftime(dayformate)][:anchor]
        tmp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[
            i - 1].strftime(dayformate)][anchor:]
        sing = temp.single.sum() + tmp.single.sum()
        if (direction > 0 and sing == 1):
            sig.append(1)
        elif (direction < 0 and sing == 3):
            sig.append(sing)
        else:
            sig.append(0)

    try:
        # sample['single'] = [0]+sig[:-1]
        sample['single'] = sig

    except:
        print('error with {}'.format(sample.index.get_level_values('code')[0]))
        sample['single'] = 0

    return sample


def trendWeekMinv2(sample, short=5, long=10, freq='15min'):
    # to get Week and 60 minutes syntony together
    # get week trend
    # A50 64% 30 5 15 12/10
    #
    # 60 76, 30 79, 30 74 more
    # 15 min is the best for now, with 11/10 (5-10 11, 5-15 10 5-20 )
    import quant.weekTrend as wt
    print('deal with {}'.format(sample.index.get_level_values('code')[-1]))
    print('*' * 100)

    sample.fillna(method='ffill', inplace=True)
    wstart = '2010-01-01'
    code = sample.index.get_level_values('code')[-1]
    wend = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    temp = QA.QA_fetch_stock_day_adv(code, wstart, wend).data
    wd = wt.wds(temp)
    wd = wt.TrendDetect(wd)

    start = sample.index.get_level_values(dayindex)[0].strftime(dayformate)
    end = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    mindata = QA.QA_fetch_stock_min_adv(sample.index.get_level_values('code')[0], start, end, frequence=freq)
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
    if (freq == '60min'):
        anchor = -2
    elif (freq == '30min'):
        anchor = -4
    elif (freq == '15min'):
        anchor = -8
    for i in range(1, len(sample)):
        dtime = sample.index.get_level_values(dayindex)[i]
        wtime = getWeekDate(dtime)
        windex = wd[wd.date == wtime.strftime(dayformate)].index[0]
        # here use index to get value interested, here we take change of MACDBlock to get the short trend in week level
        direction = wd.loc[windex].CS
        temp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[
            i].strftime(dayformate)][:anchor]
        tmp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[
            i - 1].strftime(dayformate)][anchor:]
        sing = temp.single.sum() + tmp.single.sum()
        if (direction > 0 and sing == 1):
            sig.append(1)
        elif (direction < 0 and sing == 3):
            sig.append(sing)
        else:
            sig.append(0)

    try:
        # sample['single'] = [0]+sig[:-1]
        sample['single'] = sig

    except:
        print('error with {}'.format(sample.index.get_level_values('code')[0]))
        sample['single'] = 0

    return sample


def DTWM(sample, short=20, long=60, freq='15min'):
    sample['MA'] = QA.MA(sample.close, short)
    sample['EMA'] = QA.EMA(sample.close, short)

    CROSS_5d = QA.CROSS(sample.EMA, sample.MA)
    CROSS_15d = QA.CROSS(sample.MA, sample.EMA)

    C15d = np.where(CROSS_15d == 1, 3, 0)
    md = np.where(CROSS_5d == 1, 1, C15d)
    singled = md[:-1].tolist()
    singled.insert(0, 0)
    sample['ds'] = singled

    import quant.weekTrend as wt
    print('deal with {}'.format(sample.index.get_level_values('code')[-1]))
    print('*' * 100)

    sample.fillna(method='ffill', inplace=True)
    # sample = util.divergence(sample)
    wstart = '2010-01-01'
    code = sample.index.get_level_values('code')[-1]
    wend = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    temp = QA.QA_fetch_stock_day_adv(code, wstart, wend).data
    wd = wt.wds(temp)
    wd = wt.TrendDetect(wd)

    start = sample.index.get_level_values(dayindex)[0].strftime(dayformate)
    end = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    mindata = QA.QA_fetch_stock_min_adv(sample.index.get_level_values('code')[0], start, end, frequence=freq)
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
    if (freq == '60min'):
        anchor = -2
    elif (freq == '30min'):
        anchor = -4
    elif (freq == '15min'):
        anchor = -8
    for i in range(1, len(sample)):
        dtime = sample.index.get_level_values(dayindex)[i]
        wtime = getWeekDate(dtime)
        windex = wd[wd.date == wtime.strftime(dayformate)].index[0]
        # here use index to get value interested, here we take change of MACDBlock to get the short trend in week level
        direction = wd.loc[windex].CS
        trendv = wd.loc[windex].SM
        # dd = sample.CS[i]
        temp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[
            i].strftime(dayformate)][:anchor]
        tmp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[
            i - 1].strftime(dayformate)][anchor:]
        sing = temp.single.sum() + tmp.single.sum()
        if (direction > 0 and trendv > 0 and sing == 1):
            sig.append(1)
        elif (direction < 0 and sing == 3):
            sig.append(sing)
        else:
            sig.append(0)

    try:
        # sample['single'] = [0]+sig[:-1]
        sample['single'] = sig

    except:
        print('error with {}'.format(sample.index.get_level_values('code')[0]))
        sample['single'] = 0

    return sample


def trendWeekMinv3(sample, short=20, long=60, freq='15min'):
    # test summary
    # 5-10 with 21/10
    # 5-15 with 23/10
    # 5-20 with 19/10
    # 20-60 24/10
    # to get Week and 60 minutes syntony together
    # get week trend
    # A50 64% 30 5 15 12/10
    #
    # 60 76, 30 79, 30 74 more
    # 15 min is the best for now, with 11/10 (5-10 11, 5-15 10 5-20 )
    import quant.weekTrend as wt
    print('deal with {}'.format(sample.index.get_level_values('code')[-1]))
    print('*' * 100)

    sample.fillna(method='ffill', inplace=True)
    # sample = util.divergence(sample)

    wstart = '2010-01-01'
    code = sample.index.get_level_values('code')[-1]
    wend = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    if (code == '515880' or code == '515050'):
        temp = QA.QA_fetch_index_day_adv(code, wstart, wend).data
    else:
        temp = QA.QA_fetch_stock_day_adv(code, wstart, wend).data
    wd = wt.wds(temp)
    wd = wt.TrendDetect(wd)
    bechmark = wd.BIAS.max() * 0.97

    start = sample.index.get_level_values(dayindex)[0].strftime(dayformate)
    end = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    if (code == '515880' or code == '515050'):
        mindata = QA.QA_fetch_index_min_adv(sample.index.get_level_values('code')[0], start, end, frequence=freq)
    else:
        mindata = QA.QA_fetch_stock_min_adv(sample.index.get_level_values('code')[0], start, end, frequence=freq)
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
    if (freq == '60min'):
        anchor = -2
    elif (freq == '30min'):
        anchor = -4
    elif (freq == '15min'):
        anchor = -8
    for i in range(1, len(sample)):
        dtime = sample.index.get_level_values(dayindex)[i]
        wtime = getWeekDate(dtime)
        windex = wd[wd.date == wtime.strftime(dayformate)].index[0]
        # here use index to get value interested, here we take change of MACDBlock to get the short trend in week level
        direction = wd.loc[windex].CS
        trendv = wd.loc[windex].SM
        # dd = sample.CS[i]
        temp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[
            i].strftime(dayformate)][:anchor]
        tmp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[
            i - 1].strftime(dayformate)][anchor:]
        sing = temp.single.sum() + tmp.single.sum()
        #
        if (direction > 0 and trendv > 0 and sing == 1 and wd.loc[windex].BIAS < bechmark):
            sig.append(1)
        elif (direction < 0 and sing == 3):
            sig.append(sing)
        else:
            sig.append(0)

    try:
        # sample['single'] = [0]+sig[:-1]
        sample['single'] = sig

    except:
        print('error with {}'.format(sample.index.get_level_values('code')[0]))
        sample['single'] = 0

    return sample


def getMonDate(df, dtime):
    dic = {'2020-20': '2020-20'}
    df['date'] = pd.to_datetime(df.index.get_level_values('date'))
    df.set_index("date", inplace=True)
    period = 'M'
    mdf = df.resample(period).last()
    timelist = list(mdf.index.get_values())
    for i in timelist:
        dic[str(i)[:7]] = str(i)[:10]

    return dic.get(dtime)


def trendMonDay(sample, short=20, long=60):
    # test summary
    # 5-10 with 21/10
    # 5-15 with 23/10
    # 5-20 with 19/10
    # 20-60 24/10
    # to get Week and 60 minutes syntony together
    # get week trend
    # A50 64% 30 5 15 12/10
    #
    # 60 76, 30 79, 30 74 more
    # 15 min is the best for now, with 11/10 (5-10 11, 5-15 10 5-20 )
    import quant.weekTrend as wt
    print('deal with {}'.format(sample.index.get_level_values('code')[-1]))
    print('*' * 100)

    sample.fillna(method='ffill', inplace=True)
    # sample = util.divergence(sample)

    wstart = '2010-01-01'
    code = sample.index.get_level_values('code')[-1]
    wend = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    temp = QA.QA_fetch_stock_day_adv(code, wstart, wend).data
    wd = wt.wds(temp, period='M')
    wd = wt.TrendDetect(wd)
    bechmark = wd.BIAS.max() * 0.97

    # start = sample.index.get_level_values(dayindex)[0].strftime(dayformate)
    # end = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    # mindata = QA.QA_fetch_stock_min_adv(sample.index.get_level_values('code')[0], start, end, frequence= freq)
    # ms = mindata.data
    # print(sample)
    sample['short'] = QA.EMA(sample.close, short)
    sample['long'] = QA.EMA(sample.close, long)
    CROSS_5 = QA.CROSS(sample.short, sample.long)
    CROSS_15 = QA.CROSS(sample.long, sample.short)

    C15 = np.where(CROSS_15 == 1, 3, 0)
    m = np.where(CROSS_5 == 1, 1, C15)
    single = m[:-1].tolist()
    single.insert(0, 0)
    sample['s1'] = m.tolist()
    sig = [0]
    temp = sample.copy(deep=True)
    for i in range(1, len(sample)):
        dtime = sample.index.get_level_values(dayindex)[i].strftime(dayformate)[:7]
        mtime = getMonDate(temp, dtime)
        windex = wd[wd.date == mtime].index[0]
        # print(windex)
        # here use index to get value interested, here we take change of MACDBlock to get the short trend in week level
        direction = wd.loc[windex].CS
        trendv = wd.loc[windex].SM
        sing = sample.s1[i]

        #
        if (direction > 0 and trendv > 0 and sing == 1):
            sig.append(1)
        elif (direction < 0 and sing == 3):
            sig.append(sing)
        else:
            sig.append(0)

    try:
        # sample['single'] = [0]+sig[:-1]
        sample['single'] = sig

    except:
        print('error with {}'.format(sample.index.get_level_values('code')[0]))
        sample['single'] = 0

    return sample


def doubleAvgminv2(dd, short=5, long=15, freq='60min'):
    """
    1.DIF向上突破DEA，买入信号参考。
    2.DIF向下跌破DEA，卖出信号参考。
    """
    # init_trend(dd,15)
    # dd['MA60'] = QA.MA(dd.close, 60)
    init_trend(dd)
    start = dd.index.get_level_values(dayindex)[0].strftime(dayformate)
    end = dd.index.get_level_values(dayindex)[-1].strftime(dayformate)
    mindata = QA.QA_fetch_stock_min_adv(dd.index.get_level_values('code')[0], start, end, frequence=freq)
    sample = mindata.data
    # print(sample)
    sample['short'] = QA.EMA(sample.close, short)
    sample['MA60'] = QA.MA(sample.close, 60)
    sample['long'] = QA.EMA(sample.close, long)
    CROSS_5 = QA.CROSS(sample.short, sample.long)
    CROSS_15 = QA.CROSS(sample.long, sample.short)

    C15 = np.where(CROSS_15 == 1, 3, 0)
    m = np.where(CROSS_5 == 1, 1, C15)
    # single = m[:-1].tolist()
    # single.insert(0, 0)
    sample['single'] = m.tolist()
    sig = [0]
    for i in range(1, len(dd)):
        if (dd.trend[i] < 2):
            sig.append(0)
        else:
            temp = sample[
                       sample.index.get_level_values(index).strftime(dayformate) == dd.index.get_level_values(dayindex)[
                           i].strftime(dayformate)][:]
            # print(temp.shape[0])

            sig.append(temp.single.sum())

        '''
        if( len(temp.single)>=3 and temp.single[-2]>=4):
            sig.append(3)
        else:
            sig.append(temp.single[-2])
        '''

    try:
        dd['single'] = [0] + sig[:-1]

    except:
        print('error with {}'.format(sample.index.get_level_values('code')[0]))
        dd['single'] = 0

    return dd


def bollStrategy(sample):
    boll = QA.QA_indicator_BOLL(sample)
    buy = QA.CROSS(sample.close, boll.LB)
    sell = QA.CROSS(sample.close, boll.UB)

    C15 = np.where(sell == 1, 3, 0)
    m = np.where(buy == 1, 1, C15)
    single = [0] + m[:-1].tolist()
    sample['single'] = single
    return sample


def backtestv2(holdingperc=3):
    # holdingperc = 3
    safeholding = 5000
    print('*' * 100)
    print('loading data')
    # stockes = getStocklist()
    # stockes = ['600797','000977']
    # data = loadLocalData(stockes,'2018-03-15',end_date = '2019-09-11')
    print('*' * 100)
    print('init account')
    Account = QA.QA_Account(user_cookie='eric', portfolio_cookie='eric')
    Broker = QA.QA_BacktestBroker()
    Account.reset_assets(70000)
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
    endtime = '2020-12-15'

    # add trend code
    import monitor.TrendRank as trank
    #res = trank.TrendRank(start='2019-01-01')
    #res = res.sort_values(by=['date', 'CS', 'SM'], axis=0, ascending=[True, True, True])
    # codelist = res[-30:]['code'].to_list()
    #cl = res[-20:].index.get_level_values('code').tolist()
    #print(cl)

    cl = ['000977', '600745','002889','600340','000895','600019',
              '600585','002415','002475','600031','600276','600009','601318',
              '000333','600031','002384','002241','600703','000776','600897','600085']
    codelist2.extend(cl)
    codelist = list(set(codelist2))
    # data = loadLocalData(cl, '2019-01-01', endtime)
    test = []
    # test = ['000977','600745','002241','000333']

    if ('515880' in test or '515050' in test):
        data = loadLocalDataIndex(cl, '2019-01-01', endtime)
    else:
        data = loadLocalData(cl, '2019-01-01', endtime)
    if ('515880' in test or '515050' in test):
        pass
    else:
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
    # triNetV2 a50 10/10
    # ind = data.add_func(triNetv2)

    # 18/10,currently this is job50 taking now
    # ind = data.add_func(trendWeekMinv2)
    # 21/10

    # ind = data.add_func(DTWM)
    ind = data.add_func(trendWeekMinv3)

    # ind = data.add_func(trendMonDay)

    # 7/10
    # ind = data.add_func(EMA_MA)

    # 6/10
    # ind = data.add_func(TrendFinder)

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
                        item.code[0], item.date[0], int((Account.cash_available - safeholding) / (100 * open)) * 100,
                        QA.ORDER_DIRECTION.BUY, open, QA.ORDER_MODEL.LIMIT, QA.AMOUNT_MODEL.BY_AMOUNT))
                    order = Account.send_order(
                        code=item.code[0],
                        time=item.date[0],
                        amount=int((Account.cash_available - safeholding) / (holdingperc * item.open[0] * 100)) * 100,
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
    if ('515880' in test or '515050' in test):
        market_data = QA.QA_fetch_index_day_adv(Account.code,
                                                Account.start_date,
                                                Account.end_date)

        Risk = QA.QA_Risk(Account, market_data=market_data, if_fq=False)
        print(Risk.profit_construct)
    else:
        Risk = QA.QA_Risk(Account)
        # Risk.assets.plot()
        print(Risk.profit_construct)
    print('winning ratio is {}'.format(winRatio(Account)))




def backtestv3(holdingperc=3):
    # holdingperc = 3
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
    endtime = '2020-01-20'
    cl = ['000977', '600745', '002889', '600340', '000895', '600019', '600028',
          '601857', '600585', '002415', '002475', '600031', '600276', '600009', '601318',
          '000333', '600031', '002384', '002241', '600703', '000776', '600897', '600085']
    codelist2.extend(cl)
    codelist = list(set(codelist2))
    # data = loadLocalData(cl, '2019-01-01', endtime)
    data = loadLocalData(cl, '2019-01-01', endtime)
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
    # triNetV2 a50 10/10
    # ind = data.add_func(triNetv2)

    # 18/10,currently this is job50 taking now
    # ind = data.add_func(trendWeekMinv2)
    # 21/10

    ind = data.add_func(DTWM)
    # ind = data.add_func(trendWeekMinv3)

    # 7/10
    # ind = data.add_func(EMA_MA)

    # 6/10
    # ind = data.add_func(TrendFinder)

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
            if (daily_ind.single.iloc[0] == 1 or daily_ind.ds.iloc[0] == 1):
                open = QA.QA_fetch_stock_day_adv(item.code[0], item.date[0], item.date[0]).data.open[0] if np.isnan(
                    item.open[0]) else item.open[0]
                if ((Account.cash_available - safeholding) / (holdingperc * item.close[0]) > 500):
                    print('code {}, time {} amout {}, toward {}, price {} order_model {} amount_model {}'.format(
                        item.code[0], item.date[0], int((Account.cash_available - safeholding) / (100 * open)) * 100,
                        QA.ORDER_DIRECTION.BUY, open, QA.ORDER_MODEL.LIMIT, QA.AMOUNT_MODEL.BY_AMOUNT))
                    order = Account.send_order(
                        code=item.code[0],
                        time=item.date[0],
                        amount=int((Account.cash_available - safeholding) / (holdingperc * item.open[0] * 100)) * 100,
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

            elif (daily_ind.single.iloc[0] == 3 or daily_ind.ds.iloc[0] == 3):
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
    print('winning ratio is {}'.format(winRatio(Account)))


def triNetindexv2(sample, short=5, long=10, freq='15min'):
    # to get Week and 60 minutes syntony together
    # get week trend
    # A50 64% 30 5 15 12/10
    #
    # 60 76, 30 79, 30 74 more
    # 15 min is the best for now, with 11/10 (5-10 11, 5-15 10 5-20 )
    print('*' * 100)
    import quant.weekTrend as wt
    sample.fillna(method='ffill', inplace=True)
    wstart = '2019-01-01'
    code = sample.index.get_level_values('code')[-1]
    wend = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    # temp = QA.QA_fetch_index_day_adv(code,wstart,wend).data
    wd = wt.wds(sample)
    wd = wt.weektrend(wd)

    start = sample.index.get_level_values(dayindex)[0].strftime(dayformate)
    end = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
    # code = sample.index.get_level_values('code')[0]
    code = '515880'
    mindata = QA.QA_fetch_index_min_adv(code, start, end, frequence=freq)
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
    if (freq == '60min'):
        anchor = -2
    elif (freq == '30min'):
        anchor = -4
    elif (freq == '15min'):
        anchor = -8
    for i in range(1, len(sample)):
        dtime = sample.index.get_level_values(dayindex)[i]
        wtime = getWeekDate(dtime)
        windex = wd[wd.date == wtime.strftime(dayformate)].index[0]
        # here use index to get value interested, here we take change of MACDBlock to get the short trend in week level
        direction = wd.loc[windex].change
        temp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[
            i].strftime(dayformate)][:anchor]
        tmp = ms[ms.index.get_level_values(index).strftime(dayformate) == sample.index.get_level_values(dayindex)[
            i - 1].strftime(dayformate)][anchor:]
        sing = temp.single.sum() + tmp.single.sum()
        if (direction > 0 and sing == 1):
            sig.append(1)
        elif (direction < 0 and sing > 1):
            sig.append(sing)
        else:
            sig.append(0)

    try:
        # sample['single'] = [0]+sig[:-1]
        sample['single'] = sig

    except:
        print('error with {}'.format(sample.index.get_level_values('code')[0]))
        sample['single'] = 0

    return sample


def etfverify():
    code = '515880'
    start = '2019-10-01'
    end = '2020-06-15'
    sample = QA.QA_fetch_index_day_adv(code, start, end).data
    triNetindexv2(sample)
    PlotBySe(sample)


def main():
    '''
    for i in range(2,6):
        print('*'*250)
        print('holdingperc with {} '.format(i))
        backtestv21(i)
        print('*'*200)
    '''

    backtestv2()
    # test = QA.QA_fetch_stock_day_adv('000977','2018-01-01','2019-01-01').data
    # test['single']=0
    # triNetv3(test)
    # PlotBySe(test)

    # etfverify()


if __name__ == "__main__":
    main()