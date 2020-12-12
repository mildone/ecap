import datetime
import smtplib
from email.mime.text import MIMEText
import pandas as pd
import QUANTAXIS as QA

try:
    assert QA.__version__ >= '1.1.0'
except AssertionError:
    print('pip install QUANTAXIS >= 1.1.0 请升级QUANTAXIS后再运行此示例')
    import QUANTAXIS as QA
import numpy as np


read_dictionary = np.load('../liutong.npy', allow_pickle=True).item()
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtk
import mpl_finance as mpf
import quant.Util as uti
import quant.MACD as mmacd
import quant.weekTrend as wt
import talib as ta
N = 7
M = 7

def mmroc(code):
    cur = datetime.datetime.now()
    if (str(cur.month) != '10' or str(cur.month) != '11' or str(cur.month) != '12'):
        month = '0' + str(cur.month)
    endtime = str(cur.year) + '-' + month + '-' + str(cur.day)
    print(endtime)
    data = QA.QA_fetch_stock_day_adv(code, uti.startday, endtime)
    sample = data.data
    sample['EMA13']=QA.EMA(sample.close,13)
    ROC = []
    SMROC = []
    for i in range(sample.close.shape[0]):
        if(i-N<0):
            ROC.append(0)
        else:
            ROC.append(sample.close[i]/sample.close[i-N])
    for i in range(sample.close.shape[0]):
        if(i-M<0):
            SMROC.append(0)
        else:
            SMROC.append(sample.EMA13[i]/sample.EMA13[i-M])
    sample['ROC']=ROC
    sample['SMROC'] = SMROC

    return sample

def mrocplot(sample,index,formate):
    quotes = mmacd.MINcandlestruct(sample, uti.dayindex, uti.dayformate)
    N = sample.index.get_level_values(index).shape[0]
    ind = np.arange(N)

    def format_date(x, pos=None):
        thisind = np.clip(int(x + 0.5), 0, N - 1)
        return sample.index.get_level_values(index)[thisind].strftime(formate)

    fig = plt.figure()
    fig.set_size_inches(20.5, 12.5)
    ax2 = fig.add_subplot(2, 1, 1)
    ax2.set_title("candlestick", fontsize='xx-large', fontweight='bold')

    # fig,ax=plt.subplots()
    # mpf.candlestick_ochl(ax2,quotes,width=0.2,colorup='r',colordown='g',alpha=1.0)
    # ax2.xaxis_date()
    # plt.setp(plt.gca().get_xticklabels(),rotation=30)
    # ax2.plot(ind,sample.close,'b-',marker='*')
    mpf.candlestick_ochl(ax2, quotes, width=0.6, colorup='r', colordown='g', alpha=1.0)
    ax2.fill_between(ind, 0, sample.close, color='blue', alpha=0.08)
    ax2.text(N / 2, pd.DataFrame.max(sample.EMA13), "EMA13 tells trend",
             fontdict={'size': '16', 'color': 'b'})
    ax2.plot(ind, sample.EMA13)
    ax2.text(ind[-1], sample.high[-1], sample.index.get_level_values('date')[-1].strftime('%Y-%m-%d'),
             fontdict={'size': '12', 'color': 'b'})
    ax2.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    # ax2.set_xticklabels(sample.index.get_level_values(index)[::3])
    ax2.grid(True)
    # t.legend()
    fig.autofmt_xdate()

    ax1 = fig.add_subplot(2,1,2)
    ax1.set_title("Movement ROC ",
                   fontsize='xx-large', fontweight='bold')


    ax1.plot(ind, sample.ROC,'g-')
    ax1.axhline(y=np.mean(sample.ROC), ls="--", c="green")
    ax1.plot(ind,sample.SMROC,'r-')
    ax1.axhline(y=np.mean(sample.SMROC),ls="--",c="red")
    ax1.text(N / 2, max(pd.DataFrame.max(sample.ROC),pd.DataFrame.max(sample.SMROC))
                                     , "Diviation  Red:SMROC,Green:ROC",
             fontdict={'size': '16', 'color': 'b'})


    start = 0
    end = 0
    mv = np.mean(sample.SMROC)
    for i in range(sample.shape[0]):
        if (sample.SMROC[i-1]<mv and sample.SMROC[i]>mv):
            # ax2.axvline(x=i, ls="-", c="red")  # 添加垂直直线
            # ax2.axvline(x=i, ls="-", c="red")
            #            print(str(sample.index.get_level_values(uti.dayindex)[i].strftime('%D')))
            # ax2.text(i, sample.high[i],
            # str(sample.index.get_level_values(index)[i].strftime('%D')),
            # fontdict={'size': '8', 'color': 'b'})

            # ax1.annotate('buy %s' % sample.index.get_level_values('date')[i].strftime('%D'),
            # xy=(i, sample.MACDBlock[i]), xytext=(i, sample.MACDBlock[i] + random.uniform(maxvalue*0.7, maxvalue)),
            # xycoords='data',
            # arrowprops=dict(facecolor='red', shrink=0.05))
            start = i

        elif (sample.SMROC[i-1]>mv and sample.SMROC[i]<mv):
            end = i
            # ax2.axvline(x=i, ls="-", c="green")  # 添加垂直直线
            # ax2.axvline(x=i, ls="-", c="green")
            # ax2.text(i, pd.DataFrame.min(sample.low),
            # sample.index.get_level_values(index)[i].strftime('%D'),
            # fontdict={'size': '8', 'color': 'b'})

            # ax1.annotate('sell %s' % sample.index.get_level_values('date')[i].strftime('%D'),
            # xy=(i, sample.MACDBlock[i]), xytext=(i, sample.MACDBlock[i] + random.uniform(maxvalue*0.25, maxvalue*0.7)),
            # xycoords='data',
            # arrowprops=dict(facecolor='green', shrink=0.05))
        if (start != 0 and end != 0):
            ax2.fill_between(ind[start:end], 0, sample.close[start:end], color='green', alpha=0.38)

            ax2.text(start, sample.close[i]+5,
                     str("before {},after {}".format(sample.close[start],sample.close[end])),
                     fontdict={'size': '12', 'color': 'b'})
            start = 0
            end = 0


    ax1.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    # ax2.set_xticklabels(sample.index.get_level_values(index)[::3])
    ax1.grid(True)
    # t.legend()
    fig.autofmt_xdate()

    plt.show()






if __name__ == "__main__":
    sample=mmroc('000810')
    mrocplot(sample[-90:],uti.dayindex,uti.dayformate)

