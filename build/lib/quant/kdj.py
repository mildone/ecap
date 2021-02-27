import datetime
import sys
import os
import smtplib
from email.mime.text import MIMEText
import QUANTAXIS as QA
sys.path.append(os.path.abspath('../'))
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

read_dictionary = np.load('/Users/jiangyongnan/git/ecap/liutong.npy', allow_pickle=True).item()
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtk
import mpl_finance as mpf
import matplotlib.dates as mpd
import quant.Util as uti
import datetime

N = 5
ND = 3
def DROC(sample,N=3):
    quD = []
    size = sample.close.shape[0]
    for i in range(size):
        if(i>N):
            quD.append(((sample.cl[i]+sample.cl[i-1]+sample.cl[i-2])/(sample.hl[i]+sample.hl[i-1]+sample.hl[i-2]))*100)
        else:
            quD.append(None)
    sample['quD']=quD
    return sample

def kdj(sample):

    sample['EMA13'] = QA.EMA(sample.close, 13)
    sample['VolumeEMA'] = QA.EMA(sample.volume, 5)
    kdj = QA.QA_indicator_KDJ(sample)
    sample['K']=kdj.KDJ_K
    sample['D'] = kdj.KDJ_D
    sample['J'] = kdj.KDJ_J
    sample['OBV'] = QA.QA_indicator_OBV(sample).OBV

    return sample



def MINcandlestruct(sample, index, timeFrmate):
    quotes = []
    pydate_array = sample.index.get_level_values(index).to_pydatetime()
    date_only_array = np.vectorize(lambda s: s.strftime(timeFrmate))(pydate_array)
    # date_only_series = pd.Series(date_only_array)
    N = sample.index.get_level_values(index).shape[0]
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
def trendBreak(pdDataFrame):
    from abupy import pd_rolling_max
    from abupy import pd_expanding_max
    # 当天收盘价格超过N1天内最高价格作为买入信号
    N1 = 40
    # 当天收盘价格超过N2天内最低价格作为卖出信号
    N2 = 20
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

    cb = QA.CROSS(kl_pd.close,kl_pd.n1_high)
    cs = QA.CROSS(kl_pd.n2_low,kl_pd.close)
    ss = np.where(cs==1,3,0)
    bs = np.where(cb==1,1,ss)
    sig = [0]+bs[:-1].tolist()
    kl_pd['single'] = sig
    return kl_pd


def kdjPlot(sample, index, formate):
    quotes = MINcandlestruct(sample, index, formate)
    N = sample.index.get_level_values(index).shape[0]
    ind = np.arange(N)

    def format_date(x, pos=None):
        thisind = np.clip(int(x + 0.5), 0, N - 1)
        return sample.index.get_level_values(index)[thisind].strftime(formate)

    fig = plt.figure()
    fig.set_size_inches(20.5, 12.5)
    # plt.xlabel('Trading Day')
    # plt.ylabel('MACD EMA')
    # ax2 = fig.add_subplot(6, 1, 1)
    ax2 = fig.add_subplot(2, 1, 1)
    ax2.set_title("candlestick", fontsize='xx-large', fontweight='bold')

    # fig,ax=plt.subplots()
    # mpf.candlestick_ochl(ax2,quotes,width=0.2,colorup='r',colordown='g',alpha=1.0)
    # ax2.xaxis_date()
    # plt.setp(plt.gca().get_xticklabels(),rotation=30)
    # ax2.plot(ind,sample.close,'b-',marker='*')
    mpf.candlestick_ochl(ax2, quotes, width=0.6, colorup='r', colordown='g', alpha=1.0)
    #va = sorted(list(sample.volume))
    #vmean = np.mean(sample.volume)


    ax2.plot(ind, sample.EMA13, 'r-')
    ax2.plot(ind,sample.n1_high,'blue')
    ax2.plot(ind,sample.n2_low,'blue')
    for i in range(N):
        if(sample.single[i]==1):
            ax2.axvline(x=i,ls='--',color='red')
        if(sample.single[i]==3):
            ax2.axvline(x=i,ls='--',color='green')


    ax2.text(N / 2, pd.DataFrame.max(sample.high), "EMA13 tells the trend",
             fontdict={'size': '12', 'color': 'b'})
    ax2.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    # ax2.set_xticklabels(sample.index.get_level_values(index)[::3])
    ax2.grid(True)
    # t.legend()
    fig.autofmt_xdate()



    ax5 = fig.add_subplot(2, 1, 2, sharex=ax2)
    ax5.set_title('kdj', fontsize='xx-large', fontweight='bold')
    ax5.text(N / 2, pd.DataFrame.max(sample.volume),
             "kdj, quK / quD buy, quk \ quD sell",
             fontdict={'size': '12', 'color': 'b'})
    ax5.grid(True, which='minor')
    #bar_red = np.where(sample.close>sample.open, sample.volume, 0)
    #bar_green = np.where(sample.close<=sample.open, sample.volume,0)
    #ax5.bar(ind, bar_red,color='red')
    #ax5.bar(ind,bar_green,color='green')
    ax5.plot(ind,sample.K,'r-')
    ax5.plot(ind,sample.D,'g-')
    #ax5.plot(ind,sample.J,'y-')
    ax5.axhline(y=80,ls='--',color='red')
    ax5.axhline(y=20,ls='--',color='purple')
    ax5.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    fig.autofmt_xdate()

    plt.show()
    plt.close()





def kdjANA(code):
    cur = datetime.datetime.now()
    if (str(cur.month) != '10' or str(cur.month) != '11' or str(cur.month) != '12'):
        month = '0' + str(cur.month)
    endtime = str(cur.year) + '-' + month + '-' + str(cur.day)
    print(endtime)
    data = QA.QA_fetch_stock_day_adv(code, '2019-01-01', endtime)
    sample = data.data

    kdj(sample)
    trendBreak(sample)
    kdjPlot(sample[-100:],uti.dayindex,uti.dayformate)


if __name__ == "__main__":
    kdjANA('000977')



