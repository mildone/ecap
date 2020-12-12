import datetime
import re

import QUANTAXIS as QA
import core.Util as uti
import os
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
#import matplotlib.ticker as mtk
import matplotlib.ticker as mtk
import mpl_finance as mpf



def getStocklist():
    """
    get all stock as list
    usage as:
    QA.QA_util_log_info('GET STOCK LIST')
    stocks=getStocklist()
    """
    #data=QA.QAFetch.QATdx.QA_fetch_get_stock_list('stock')
    data = QA.QA_fetch_stock_list()
    stocklist=data.index.get_level_values('code').to_list()
    return stocklist


def loadLocalData(stocks, start_date='2020-01-02', end='cur'):
    """
    data() as pdDataFrame
    stocks could be list of all the stock or some. if you pass single one e.g. 000001 it will get one only
    to get dedicated stock, using below method, and notice stockp() will be dataFrame
    stockp = data.select_code(stock)

    """
    if(end == 'cur'):
        cur = datetime.datetime.now()
        mon = str(cur.month)
        day = str(cur.day)
        if (re.match('[0-9]{1}', mon) and len(mon) == 1):
            mon = '0' + mon
        if (re.match('[0-9]{1}', day) and len(day) == 1):
            day = '0' + day

        et = str(cur.year) + '-' + mon + '-' + day
    else:
        et = end
    print('ok here')
    data = QA.QA_fetch_stock_day_adv(stocks, start_date, et)
    return data

def change(dd,short=20,mid=60,long=120):
    from functools import reduce
    pp_array = [float(close) for close in dd.close]
    temp_array = [(price1, price2) for price1, price2 in zip(pp_array[:-1], pp_array[1:])]
    change = list(map(lambda pp: reduce(lambda a, b: round((b - a) / a, 3), pp), temp_array))
    change.insert(0, 0)
    dd['change']=change
    dd['short']=QA.EMA(dd.close,short)
    dd['CS']=(dd.close-dd.short)*100/dd.short
    return dd


def analysis(df, st='2020-01-01',end='cur'):

    '''
    if(os.path.exists('stock.npy')):
        print('load from file')
        stock = np.load('stock.npy')
    else:
        print('query from net')
        stock = getStocklist()
        np.save('stock.npy',stock)
    '''

    if (end == 'cur'):
        cur = datetime.datetime.now()
        mon = str(cur.month)
        day = str(cur.day)
        if (re.match('[0-9]{1}', mon) and len(mon) == 1):
            mon = '0' + mon
        if (re.match('[0-9]{1}', day) and len(day) == 1):
            day = '0' + day

        et = str(cur.year) + '-' + mon + '-' + day
    else:
        et = end


    stock = getStocklist()

    codelist3 = QA.QA_fetch_stock_block_adv().get_block('云计算').code[:]
    codelist1 = QA.QA_fetch_stock_block_adv().get_block('华为概念').code[:]
    codelist2 = QA.QA_fetch_stock_block_adv().get_block('5G概念').code[:]
    # codelist4 = QA.QA_fetch_stock_block_adv().get_block('国产软件').code[:]
    codelist2.extend(codelist3)
    codelist2.extend(codelist1)

    codelist = list(set(codelist2))
    m = loadLocalData(stock)
    num = 0
    win = 0
    ind = m.add_func(change)
    #st = '2020-01-01'
    data_forbacktest = m.select_time(st, et)

    #start = {'date': [st], 'value': [0]}
    #df = pd.DataFrame(start)
    #df.set_index('date', inplace=True)
    candidate = df.index.get_level_values('date').to_list()
    for items in data_forbacktest.panel_gen:
        num = 0
        win = 0
        for item in items.security_gen:
            daily_ind = ind.loc[item.index]
            num += 1
            # print('{} at {} with {} and {}'.format(item.code[0], item.date[0], item.close[0], daily_ind.change.iloc[0]))
            if (daily_ind.CS.iloc[0] > 0):
                win += 1
        print('{} with {}'.format(item.date[0], win / num))
        if(str(item.date[0])  not in candidate):
            print('adding '+str(item.date[0]))
            df.loc[item.date[0]] = win / num
        else:
            pass
        # print('------' + str(items.date[0]) + '------' + str(win) + '/' + str(num))
    return df
    #df.to_csv('marketwidth.csv')

def contextPlot(df,start='2020-01-01',end='cur'):
    import core.Util as ut
    if (end == 'cur'):
        cur = datetime.datetime.now()
        mon = str(cur.month)
        day = str(cur.day)
        if (re.match('[0-9]{1}', mon) and len(mon) == 1):
            mon = '0' + mon
        if (re.match('[0-9]{1}', day) and len(day) == 1):
            day = '0' + day

        et = str(cur.year) + '-' + mon + '-' + day
    else:
        et = end
    sample = QA.QA_fetch_stock_day_adv('000977',start,et).data
    quots = ut.candlestruct(sample)

    N = df.shape[0]
    ind = np.arange(N)


    def format_date(x, pos=None):
        thisind = np.clip(int(x + 0.5), 0, N - 1)
        return m.index.get_level_values(uti.dayindex)[thisind]


    fig = plt.figure()
    #gs = gridspec.GridSpec(3, 1)
    fig.set_size_inches(30.5, 20.5)



    ax3 = fig.add_subplot(2, 1, 2)
    ax3.set_title("candlestick", fontsize='xx-large', fontweight='bold')

    mpf.candlestick_ochl(ax3, quots, width=0.6, colorup='r', colordown='g', alpha=1.0)

    '''
    for i in range(N):
        if (day.single[i] == 1):
            ax2.axvline(x=i, ls='--', color='red')
        if (day.single[i] == 3):
            ax2.axvline(x=i, ls='--', color='green')
    '''
    ax3.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    ax3.grid(True)
    ax3.legend(loc='best')
    fig.autofmt_xdate()

    ax2 = fig.add_subplot(2, 1, 1,sharex=ax3)
    # ax3.set_title("Divergence", fontsize='xx-large', fontweight='bold')
    ax2.plot(ind, m.value, 'r-', linewidth=1)
    ax2.grid(True)
    ax2.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))

    fig.autofmt_xdate()

    plt.show()

def updateRecord(df):
    df.to_csv('marketwidth.csv')

if __name__ == '__main__':
    #analysis()
    if(os.path.exists('./marketwidth.csv')):
        m = pd.read_csv('./marketwidth.csv')
        m.set_index('date',inplace=True)
    #this is to reload data on top
        stime = m.index.get_level_values('date')[-21]
    else:
        stime = '2020-01-01'
        start = {'date': [stime], 'value': [0]}
        m = pd.DataFrame(start)
        m.set_index('date', inplace=True)
    df = analysis(m,st=stime,end='cur')
    contextPlot(df)
    updateRecord(df)











