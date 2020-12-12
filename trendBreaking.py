import QUANTAXIS as QA
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import abupy
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
alldata = pd.DataFrame(pd.read_csv('./data/528.csv'))


def amountAnalyse(stock):
    """
    @buydata as pdDataFrame
    e.g. buydata = QA.QA_fetch_get_stock_transaction_realtime('pytdx','600797') get current day's transaction
    e.g. data1=QA.QAFetch.QATdx.QA_fetch_get_stock_transaction('600797','2019-01-01','2019-04-11') get transaction among period of time
    buy.sort_values(by="vol" , ascending=False)
    """
    buydata = QA.QA_fetch_get_stock_transaction_realtime('pytdx',stock)
    #buydata = QA.QA_fetch_get_stock_transaction('py')
    sellone = buydata[buydata['buyorsell'] == 1]
    sellone['amount'] = sellone['price'] * sellone['vol']*100
    sellone.sort_values("vol", inplace=True, ascending=False)

    buyone = buydata[buydata['buyorsell'] == 0]
    buyone['amount'] = buyone['price'] * buyone['vol']*100
    buyone.sort_values("vol", inplace=True, ascending=False)
    # print("Top buyer vol")
    # buyone[buyone['vol']>10]
    return buyone, sellone

def historyTransaction(stock, start='2019-04-01', end='2019-05-22'):
    """
    return how many 10G
    :param stock:
    :param start:
    :param end:
    :return:
    """
    buytransaction = QA.QA_fetch_get_stock_transaction('pytdx', stock, start = start, end = end)
    sellone = buytransaction[buytransaction['buyorsell']==1]
    sellone['amount'] = sellone['price'] * sellone['vol'] * 100
    sellone.sort_values("vol", inplace=True, ascending=False)

    buyone = buytransaction[buytransaction['buyorsell']==0]
    buyone['amount'] = buyone['price'] * buyone['vol'] * 100
    buyone.sort_values("vol", inplace=True, ascending=False)
    return (buyone.amount.cumsum().to_list()[-1] - sellone.amount.cumsum().to_list()[-1])/10000


import QUANTAXIS as QA
def getStocklist():
    """
    get all stock as list
    usage as:
    QA.QA_util_log_info('GET STOCK LIST')
    stocks=getStocklist()
    """
    data=QA.QAFetch.QATdx.QA_fetch_get_stock_list('stock')
    stock = data['code'].index
    stocklist = []
    for code in stock:
        stocklist.append(code[0])
    return stocklist


def loadLocalData(stocks, start_date='2017-03-15', end_date='2019-05-07'):
    """
    data() as pdDataFrame
    stocks could be list of all the stock or some. if you pass single one e.g. 000001 it will get one only
    to get dedicated stock, using below method, and notice stockp() will be dataFrame
    stockp = data.select_code(stock)


    """
    QA.QA_util_log_info('load data from local DB')
    data = QA.QA_fetch_stock_day_adv(stocks, start_date, end_date)
    return data


def trendBreak(pdDataFrame):
    from abupy import pd_rolling_max
    from abupy import pd_expanding_max
    # 当天收盘价格超过N1天内最高价格作为买入信号
    N1 = 40
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


def change(a,b):
    return 1 if a>b else 0


def trendSingle(stock):
    """
    calculate the trend of given data length, if you need latest month then you can pass like pdDataFrame[-20:-1]
    """
    from abupy import ABuRegUtil
    return stock, ABuRegUtil.calc_regress_deg(alldata[alldata.code==stock].reset_index(drop=True).close.values, show=False)

def resetData(stock):
    return alldata[alldata.code==stock].reset_index(drop=True)

def getStockPerBlock():
    QA.QAFetch.QATdx.QA_fetch_get_stock_block()
    

if __name__ == "__main__":
    result = []
    stocks = [x for x in alldata.code.values[:3624]]
    #stocks = getStocklist()
    candidate = []
    select = []
    with ThreadPoolExecutor(3) as executor:
        futures = [executor.submit(trendSingle, stock) for stock in stocks]
        for future in as_completed(futures):
            try:
                result.append(future.result())
            except:
                print('wrong')

    for sp,dep in result:
        if(dep>0):
            candidate.append(sp)
    #print (candidate)

    for sp in candidate:
        temp = trendBreak(alldata[alldata.code==sp].reset_index(drop=True))
        if(temp.signal.values[-1] == 1 ):
            select.append(sp)

    if(len(select)>0):
        print (select)
    else:
        print ('nothing proper')

