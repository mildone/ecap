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


def da(sample):
    sample['MA64'] = QA.MA(sample.close, 64)
    sample['MA256'] = QA.MA(sample.close,256)
    sample['k1']=0.618*QA.HHV(sample.high,256)+0.382*QA.LLV(sample.low,256)
    sample['k2']=0.5*QA.HHV(sample.high,256)+0.5*QA.LLV(sample.low,256)
    sample['k3']=0.382*QA.HHV(sample.high,256)+0.618*QA.LLV(sample.low,256)

    return sample

def plot(sample):
    quotes = mmacd.MINcandlestruct(sample, uti.dayindex, uti.dayformate)
    N = sample.index.get_level_values(uti.dayindex).shape[0]
    ind = np.arange(N)

    def format_date(x, pos=None):
        thisind = np.clip(int(x + 0.5), 0, N - 1)
        return sample.index.get_level_values(uti.dayindex)[thisind].strftime(uti.dayformate)

    fig = plt.figure()
    fig.set_size_inches(20.5, 12.5)
    # plt.xlabel('Trading Day')
    # plt.ylabel('MACD EMA')
    ax2 = fig.add_subplot(2, 1, 1)
    ax2.set_title("candlestick", fontsize='xx-large', fontweight='bold')

    # fig,ax=plt.subplots()
    # mpf.candlestick_ochl(ax2,quotes,width=0.2,colorup='r',colordown='g',alpha=1.0)
    # ax2.xaxis_date()
    # plt.setp(plt.gca().get_xticklabels(),rotation=30)
    # ax2.plot(ind,sample.close,'b-',marker='*')
    mpf.candlestick_ochl(ax2, quotes, width=0.6, colorup='r', colordown='g', alpha=1.0)

    ax2.plot(ind, sample.MA64,'red',label='MA64')
    ax2.plot(ind,sample.MA256,'green',label='MA256')
    ax2.plot(ind,sample.k1,'blue',linestyle='--',label='618')
    ax2.plot(ind, sample.k3, 'blue', linestyle='--', label='382')
    ax2.plot(ind,sample.k2,'blue',linestyle='--',label='half')
    ax2.text(ind[-1], sample.high[-1], sample.index.get_level_values('date')[-1].strftime('%Y-%m-%d'),
             fontdict={'size': '12', 'color': 'b'})
    ax2.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    # ax2.set_xticklabels(sample.index.get_level_values(index)[::3])
    ax2.grid(True)
    ax2.legend(loc='best')
    fig.autofmt_xdate()


    plt.show()

def daANA(code):
    cur = datetime.datetime.now()
    endtime = str(cur.year) + '-' + str(cur.month) + '-' + str(cur.day)
    daydata = QA.QA_fetch_stock_day_adv(code, '2005-01-01', endtime)
    sample =da(daydata.data)
    wd = wt.weekDF(sample)
    plot(sample[-100:])
if __name__ == "__main__":
    daANA('000810')