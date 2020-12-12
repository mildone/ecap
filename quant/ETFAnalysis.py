import datetime
import smtplib
from email.mime.text import MIMEText
import QUANTAXIS as QA
try:
    assert QA.__version__>='1.1.0'
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
read_dictionary = np.load('../liutong.npy',allow_pickle=True).item()
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtk
import mpl_finance as mpf



def force(sample):
    sample['EMA13'] = QA.EMA(sample.close, 13)
    sample['MA20']=QA.MA(sample.close,20)
    sample['optimism'] = sample.high - sample.EMA13
    sample['pessmist'] = sample.low - sample.EMA13
    pp_array = [x for x in sample.close]
    forceweight =[]
    force = [0]
    for m,n in zip(pp_array[:-1],pp_array[1:]):
        force.append(n-m)
        #print (n-m)
    #only for online data. is sample.vol, datat
    volumn = [x for x in sample.vol]
    for x,y in zip(force,volumn):
        #print("{0} and {1}".format(x,y))
        forceweight.append(x*y)

    sample['FORCE']=forceweight
    sample['FCEMA2']=QA.EMA(sample.FORCE,2)
    sample['FCEMA13']=QA.EMA(sample.FORCE,13)
    #print(sample)
    return sample

def plot(wd,rsi):
    sample = wd
    quotes = []
    # pydate_array = sample.index.get_level_values(index).to_pydatetime()
    # date_only_array = np.vectorize(lambda s: s.strftime(timeFrmate))(pydate_array)
    # date_only_series = pd.Series(date_only_array)
    # N = sample.index.get_level_values(index).shape[0]
    N = wd.shape[0]
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
    N = sample.shape[0]
    ind = np.arange(N)
    # macd = QA.QA_indicator_MACD(sample,short=5,long=34,mid=9)
    macd = QA.QA_indicator_MACD(sample)
    sample['MA5'] = QA.MA(sample.close, 5)
    sample['MA10'] = QA.MA(sample.close, 10)
    boll = QA.QA_indicator_BOLL(sample)

    def format_date(x, pos=None):
        if x < 0 or x > N - 1:
            return ''

        return sample.date[int(x)]

    fig = plt.figure()
    fig.set_size_inches(50.5, 34.5)
    # plt.xlabel('Trading Day')
    # plt.ylabel('MACD EMA')
    # ax2 = fig.add_subplot(3, 1, 1)
    ax2 = fig.add_subplot(5, 1, 1)
    ax2.set_title("candlestick", fontsize='xx-large', fontweight='bold')

    # fig,ax=plt.subplots()
    # mpf.candlestick_ochl(ax2,quotes,width=0.2,colorup='r',colordown='g',alpha=1.0)
    # ax2.xaxis_date()
    # plt.setp(plt.gca().get_xticklabels(),rotation=30)
    # ax2.plot(ind,sample.close,'b-',marker='*')
    mpf.candlestick_ochl(ax2, quotes, width=0.6, colorup='r', colordown='g', alpha=1.0)
    ax2.plot(ind, sample.MA5, 'r-', label='MA5')
    ax2.plot(ind, sample.MA10, 'blue', label='MA10')
    # ax2.plot(ind,sample.MA20,'blue',label='MA20')
    # ax2.plot(ind,sample.close,'blue')

    ax2.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    # ax2.set_xticklabels(sample.index.get_level_values(index)[::3])
    ax2.grid(True)
    ax2.legend(loc='best', fontsize='x-large')
    # t.legend()
    fig.autofmt_xdate()

    ax4 = fig.add_subplot(5, 1, 2, sharex=ax2)
    ax4.set_title("RSI", fontsize='xx-large', fontweight='bold')
    mpf.candlestick_ochl(ax4, quotes, width=0.6, colorup='r', colordown='g', alpha=1.0)
    ax4.plot(ind, rsi.RSI1, 'purple', linestyle='--', label='12day')
    ax4.plot(ind, rsi.RSI2, 'red', linestyle='--', label='26day')
    ax4.plot(ind, rsi.RSI3, 'blue', linestyle='--', label='9day')
    ax4.axhline(y=80, ls='--')
    ax4.axhline(y=20, ls='--')
    ax4.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    # ax2.set_xticklabels(sample.index.get_level_values(index)[::3])
    ax4.grid(True)
    ax4.legend(loc='best')
    fig.autofmt_xdate()

    ax3 = fig.add_subplot(5, 1, 3, sharex=ax2)
    ax3.set_title("Force with price and amount", fontsize='xx-large', fontweight='bold')
    ax3.plot(ind, wd.FCEMA13, 'blue', label='13 days force')
    ax3.plot(ind, wd.FCEMA2, 'red', label='2 days force')
    ax3.axhline(y=0, ls="--", c="red")
    ax3.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    # ax2.set_xticklabels(sample.index.get_level_values(index)[::3])
    ax3.grid(True)
    ax3.legend(loc='best', fontsize='x-large')
    ax3.legend(loc='best')
    fig.autofmt_xdate()

    ax5 = fig.add_subplot(5, 1, 5, sharex=ax2)
    ax5.set_title("Daily Volume", fontsize='xx-large', fontweight='bold')
    vol5 = QA.MA(wd.vol, 5)
    bar_red = np.where(wd.close > wd.open, wd.vol, 0)
    bar_green = np.where(wd.close <= wd.open, wd.vol, 0)
    ax5.plot(ind, vol5, 'red')
    ax5.bar(ind, bar_red, color='red')
    ax5.bar(ind, bar_green, color='green')
    ax5.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    # ax2.set_xticklabels(sample.index.get_level_values(index)[::3])
    ax5.grid(True)
    # t.legend()
    fig.autofmt_xdate()

    ax1 = fig.add_subplot(5, 1, 4, sharex=ax2)
    ax1.set_title("MACD,DIF,DEA", fontsize='xx-large', fontweight='bold')
    ax1.plot(ind, macd.DIF, 'r-', label='DIF quick')
    ax1.plot(ind, macd.DEA, 'blue', label='DEA slow')
    ax1.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    # ax2.set_xticklabels(sample.index.get_level_values(index)[::3])
    ax1.grid(True)
    ax1.legend(loc='best', fontsize='x-large')
    # t.legend()
    bar_red = np.where(macd.MACD >= 0, macd.MACD, 0)
    bar_green = np.where(macd.MACD < 0, macd.MACD, 0)
    ax1.bar(ind, bar_red, color='red')
    ax1.bar(ind, bar_green, color='green')
    fig.autofmt_xdate()

    plt.show()


if __name__ == "__main__":
    #macdANA('002241')
    codetx = '515880'
    code5g = '515050'
    wd = QA.QAFetch.QATdx.QA_fetch_get_stock_day(codetx, '2019-01-18', '2020-06-13')
    #print(wd)

    rsi = QA.QA_indicator_RSI(wd)
    force(wd)
    plot(wd,rsi)

