import datetime
import re

import pandas as pd
import QUANTAXIS as QA

try:
    assert QA.__version__ >= '1.1.0'
except AssertionError:
    print('pip install QUANTAXIS >= 1.1.0 请升级QUANTAXIS后再运行此示例')
    import QUANTAXIS as QA
import numpy as np
import quant.Util as uti
import matplotlib.pyplot as plt
import matplotlib.ticker as mtk
import mpl_finance as mpf

def TrendDivergence(day, short=20, mid=60, long=120):
    day['long'] = QA.EMA(day.close, long)
    day['lo'] = QA.MA(day.close,long)
    day['mi'] = QA.MA(day.close,mid)
    day['sh'] = QA.MA(day.close,short)
    day['mid'] = QA.EMA(day.close, mid)
    day['short'] = QA.EMA(day.close, short)
    day['BIAS'] = (day.close - day.long) * 100 / day.long
    day['CS'] = (day.close - day.short) * 100 / day.short
    day['SM'] = (day.short - day.mid) * 100 / day.mid
    day['ML'] = (day.mid - day.long) * 100 / day.long
    return day

def TrendStrength(day):
    day['TS'] = (day.close > day.short).astype(int) + (day.close > day.sh).astype(int) + (day.close > day.mid).astype(int) + \
                (day.close > day.mi).astype(int) + (day.sh > day.mi).astype(int)
    day['RTS'] = (day.short>day.close).astype(int) + (day.sh>day.close).astype(int) + \
                 (day.mid>day.close).astype(int) + (day.mi>day.close).astype(int)+(day.mi>day.sh).astype(int)

    return day


def TrendRank(start = '2015-01-01'):
    codelist3 = QA.QA_fetch_stock_block_adv().get_block('云计算').code[:]
    codelist1 = QA.QA_fetch_stock_block_adv().get_block('华为概念').code[:]
    codelist2 = QA.QA_fetch_stock_block_adv().get_block('5G概念').code[:]
    # codelist4 = QA.QA_fetch_stock_block_adv().get_block('国产软件').code[:]
    codelist2.extend(codelist3)
    codelist2.extend(codelist1)
    codelist = list(set(codelist2))

    cur = datetime.datetime.now()
    mon = str(cur.month)
    day = str(cur.day)
    if (re.match('[0-9]{1}', mon) and len(mon) == 1):
        mon = '0' + mon
    if (re.match('[0-9]{1}', day) and len(day) == 1):
        day = '0' + day

    et = str(cur.year) + '-' + mon + '-' + day
    first = codelist.pop()
    sample = QA.QA_fetch_stock_day_adv(first,start,et).data
    sample = TrendDivergence(sample)[-1:]
    for code in codelist:
        temp = QA.QA_fetch_stock_day_adv(code,start,et).data
        td = TrendDivergence(temp)
        sample = pd.concat([td, sample], axis=0, sort=True)
    return sample

'''
def jump(df):
    jumpratio = df.close.median() * 0.03
    from functools import reduce
    pp_array = [float(close) for close in df.close]
    temp_array = [(price1, price2) for price1, price2 in zip(pp_array[:-1], pp_array[1:])]
    change = list(map(lambda pp: reduce(lambda a, b: round((b - a) / a, 3), pp), temp_array))
    change.insert(0, 0)
    df['change'] = change
    jump = [0]
    for i in range(1,df.shape[0]):
        if(df.change[i]>0 and df.low[i]-df.close[i-1]>jumpratio):
            jump.append(1)
        elif(df.change[i]<0 and df.close[i-1]-df.high[i]>jumpratio):
            jump.append(-1)
        else:
            jump.append(0)
    df['jump'] = jump
    return df


def plot(day, short=20, mid=60, long=120):
    import quant.MACD as macd
    TrendDivergence(day)
    quotes = macd.MINcandlestruct(day, uti.dayindex, uti.dayformate)
    # N = sample.index.get_level_values(index).shape[0]

    N = day.shape[0]
    ind = np.arange(N)

    def format_date(x, pos=None):
        thisind = np.clip(int(x + 0.5), 0, N - 1)
        return day.index.get_level_values(uti.dayindex)[thisind].strftime(uti.dayformate)

    fig = plt.figure()
    fig.set_size_inches(40.5, 20.5)
    ax2 = fig.add_subplot(2, 1, 1)
    ax2.set_title("candlestick", fontsize='xx-large', fontweight='bold')

    mpf.candlestick_ochl(ax2, quotes, width=0.6, colorup='r', colordown='g', alpha=1.0)
    ax2.plot(ind, day.lo, 'r-', label='MA' + str(long),linewidth = 0.7)
    ax2.plot(ind, day.mi, 'blue', label='MA' + str(mid),linewidth =0.7)
    ax2.plot(ind, day.sh, 'purple', label='MA' + str(short),linewidth = 0.7)
    #ax2.plot(100, 30, 'go', markersize=12, markeredgewidth=0.5,
             #markerfacecolor='None', markeredgecolor='green')

    for i in range(N):
        if (day.jump[i] == 1):
            ax2.plot(i, day.low[i], 'ro', markersize=12, markeredgewidth=2, markerfacecolor='None', markeredgecolor='red')
        if (day.jump[i] == -1):
            ax2.plot(i, day.high[i], 'go', markersize=12, markeredgewidth=2, markerfacecolor='None', markeredgecolor='green')

    ax2.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    ax2.grid(True)
    ax2.legend(loc='best')
    fig.autofmt_xdate()

    ax3 = fig.add_subplot(2, 1, 2, sharex=ax2)
    bar_red = np.where(day.close > day.open, day.volume, 0)
    bar_green = np.where(day.close < day.open, day.volume, 0)
    ax3.bar(ind, bar_red, color='red')
    ax3.bar(ind, bar_green, color='green')
    # x3.bar(ind,day.BIAS,color='blue')
    # ax3.axhline(y=0,ls='--',color='yellow')
    ax3.grid(True)
    ax3.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    fig.autofmt_xdate()


    plt.show()

'''




if __name__ == "__main__":
    res = TrendRank(start = '2015-01-01')
    res = res.sort_values(by=['date','CS','SM'],axis=0,ascending=[True,True,True])
    print(res[-20:])





