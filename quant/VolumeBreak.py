import datetime
import smtplib
from email.mime.text import MIMEText
import QUANTAXIS as QA

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

read_dictionary = np.load('../liutong.npy', allow_pickle=True).item()
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtk
import mpl_finance as mpf
import matplotlib.dates as mpd
import quant.Util as uti
import datetime


def volBreak(sample):

    sample['EMA13'] = QA.EMA(sample.close, 13)
    sample['VolumeEMA'] = QA.EMA(sample.volume, 5)

    # trend block
    pp_array = [float(volume) for volume in sample.volume]
    temp_array = [(price1, price2) for price1, price2 in zip(pp_array[:-1], pp_array[1:])]
    change = list(map(lambda pp: reduce(lambda a, b: round((b - a) / a, 3), pp), temp_array))
    change.insert(0, 0)
    sample['vchange'] = change

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


def volBreakPlot(sample, index, formate):
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
    va = sorted(list(sample.volume))
    vmean = np.mean(sample.volume)
    for i in range(N):
        if(sample.volume[i]>vmean and sample.vchange[i]>1):
            ax2.axhline(y=sample.close[i],ls='--',color='green')
            ax2.text(N / 2,sample.close[i] ,
            str(sample.close[i]),
            fontdict={'size': '12', 'color': 'b'})


    ax2.plot(ind, sample.EMA13, 'r-')
    #temp = sample
    #ax2.axhline(y=sample.close[np.argmax(sample.volume[-180:])[0]][0], ls='--', color='red')
    #ax2.text(N / 2,sample.close[np.argmax(sample.volume[-180:])[0]][0] ,
            # "180 days press",
            # fontdict={'size': '12', 'color': 'b'})
    #for i in range(4):
        #temp.drop(index=np.argmax(temp.volume)[0])
        #ax2.axhline(y=sample.close[np.argmax(temp.volume)[0]][0],ls='--',color='red')
    # ax2.plot(ind,sample.EMA5,'yellow')
    # ax2.plot(ind,sample.EMA20,'green')
    # ax2.plot(ind,sample.EMA30,'purple')
    # ax2.plot(ind,sample.nhigh)
    # ax2.plot(ind,sample.nlow)
    # ax2.fill_between(ind,sample.EMA13,color='blue',alpha=0.08)

    ax2.text(N / 2, pd.DataFrame.max(sample.high), "EMA13 tells the trend",
             fontdict={'size': '12', 'color': 'b'})
    ax2.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    # ax2.set_xticklabels(sample.index.get_level_values(index)[::3])
    ax2.grid(True)
    # t.legend()
    fig.autofmt_xdate()



    ax5 = fig.add_subplot(2, 1, 2, sharex=ax2)
    ax5.set_title('volumeBreak block', fontsize='xx-large', fontweight='bold')
    ax5.text(N / 2, pd.DataFrame.max(sample.volume),
             "largest volumn with price as block peak",
             fontdict={'size': '12', 'color': 'b'})
    ax5.grid(True, which='minor')
    bar_red = np.where(sample.close>sample.open, sample.volume, 0)
    bar_green = np.where(sample.close<=sample.open, sample.volume,0)
    ax5.bar(ind, bar_red,color='red')
    ax5.bar(ind,bar_green,color='green')
    ax5.plot(ind,sample.VolumeEMA,'r-')
    ax5.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    fig.autofmt_xdate()

    plt.show()
    plt.close()





def volBreakANA(code):
    cur = datetime.datetime.now()
    if (str(cur.month) != '10' or str(cur.month) != '11' or str(cur.month) != '12'):
        month = '0' + str(cur.month)
    endtime = str(cur.year) + '-' + month + '-' + str(cur.day)
    print(endtime)
    data = QA.QA_fetch_stock_day_adv(code, '2019-12-01', endtime)
    sample = data.data

    volBreak(sample)
    volBreakPlot(sample,uti.dayindex,uti.dayformate)


if __name__ == "__main__":
    volBreakANA('000977')



