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


read_dictionary = np.load('/Users/jiangyongnan/git/ecap/liutong.npy', allow_pickle=True).item()
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtk
import mpl_finance as mpf
import quant.Util as uti
import quant.MACD as mmacd
import quant.weekTrend as wt

def force(sample):
    sample['EMA13'] = QA.EMA(sample.close, 13)
    sample['EMA26'] = QA.EMA(sample.close,26)
    sample['MA64'] = QA.MA(sample.close,64)
    sample['MA256'] = QA.MA(sample.close,256)
    pp_array = [x for x in sample.close]
    forceweight =[]
    force = [0]
    for m,n in zip(pp_array[:-1],pp_array[1:]):
        force.append(n-m)
        #print (n-m)
    #only for online data. is sample.vol, datat
    volumn = [x for x in sample.volume]
    for x,y in zip(force,volumn):
        #print("{0} and {1}".format(x,y))
        forceweight.append(x*y)

    sample['FORCE']=forceweight
    sample['FCEMA2']=QA.EMA(sample.FORCE,2)
    sample['FCEMA13']=QA.EMA(sample.FORCE,13)
    #print(sample)
    return sample
def DayMin(ds, ms):
    '''
    1. Max 256 up, Min 256 up: min64 up through min256, gold speed spot
    2. Max 256 up, min 256 down, min64 up trhough min256, ------ ignore
    3. max 256 up, min256 up, min64 down through min256 ---- ignore
    4. max 256 up, min 256 down, min64 down through min256, dead cross--> buy
    5. max 256 down, min 256 up, min64 up through min256, sell or ignore
    6, max 256 down, min 256 down, min 64 up through min256, sell
    7, max 256 down, min 256 up, min 64 down through 256, buy or ignore
    8, max 256 down, min 256 down, min 64 down through min 256, buy
    '''
    day_start=0
    for i in range(0,ds.shape[0]):
        if(str(ds.index.get_level_values(uti.dayindex)[i]).split(' ')[0]==str(ms.index.get_level_values(uti.index)[0]).split(' ')[0]):
            day_start = i
            break
    quotes = mmacd.MINcandlestruct(ds, uti.dayindex, uti.dayformate)
    N = ds.index.get_level_values(uti.dayindex).shape[0]
    ind = np.arange(N)

    def format_date(x, pos=None):
        thisind = np.clip(int(x + 0.5), 0, N - 1)
        return ds.index.get_level_values(uti.dayindex)[thisind].strftime(uti.dayformate)

    mquotes = mmacd.MINcandlestruct(ms, uti.index, uti.formate)
    M = ms.index.get_level_values(uti.index).shape[0]
    indm = np.arange(M)

    def mformat_date(x, pos=None):
        thisind = np.clip(int(x + 0.5), 0, M - 1)
        return ms.index.get_level_values(uti.index)[thisind].strftime(uti.formate)



    fig = plt.figure()
    fig.set_size_inches(20.5, 12.5)
    ax2 = fig.add_subplot(2, 1, 1)
    obv = QA.QA_indicator_OBV(ds)
    ax2.set_title("Day candlestick", fontsize='xx-large', fontweight='bold')

    # fig,ax=plt.subplots()
    # mpf.candlestick_ochl(ax2,quotes,width=0.2,colorup='r',colordown='g',alpha=1.0)
    # ax2.xaxis_date()
    # plt.setp(plt.gca().get_xticklabels(),rotation=30)
    # ax2.plot(ind,sample.close,'b-',marker='*')
    mpf.candlestick_ochl(ax2, quotes, width=0.6, colorup='r', colordown='g', alpha=1.0)
    #ax2.text(N / 2, pd.DataFrame.max(sample.EMA13), "EMA13 tells trend",
             #fontdict={'size': '16', 'color': 'b'})
    ax2.axvline(x=day_start,ls='--',c='red')
    ax2.plot(ind, ds.MA64, 'red', label='MA64', linestyle='--')
    ax2.plot(ind, ds.EMA26, 'blue', label='MA256', linestyle='--')

    ax2.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))

    ax2.grid(True)
    ax2.legend(loc='best')
    fig.autofmt_xdate()



    ax3 = fig.add_subplot(2, 1, 2)
    ax3.set_title("force", fontsize='xx-large', fontweight='bold')
    mpf.candlestick_ochl(ax3, mquotes, width=0.6, colorup='r', colordown='g', alpha=1.0)
    ax3.plot(indm, ms.MA64, 'red', label='MA64', linestyle='--')
    ax3.plot(indm, ms.EMA26, 'blue', label='MA256', linestyle='--')
    ax3.xaxis.set_major_formatter(mtk.FuncFormatter(mformat_date))
    ax3.grid(True)
    ax3.legend(loc='best')
    fig.autofmt_xdate()

    '''
    ax1 = fig.add_subplot(3, 1, 3, sharex=ax3)
    obv = QA.QA_indicator_OBV(ms)
    ax1.plot(ind, obv.OBV, 'red', label='OBV')

    ax1.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    ax1.grid(True)
    ax1.legend(loc='best')
    fig.autofmt_xdate()
    '''
    plt.show()


def plot(sample,index,format):
    quotes = mmacd.MINcandlestruct(sample, index, format)
    N = sample.index.get_level_values(index).shape[0]
    ind = np.arange(N)

    def format_date(x, pos=None):
        thisind = np.clip(int(x + 0.5), 0, N - 1)
        return sample.index.get_level_values(index)[thisind].strftime(uti.dayformate)

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
    ax2.text(N/2, pd.DataFrame.max(sample.EMA13), "EMA13 tells trend",
             fontdict={'size': '16', 'color': 'b'})
    ax2.plot(ind, sample.MA64,'red',label='MA64',linestyle='--')
    ax2.plot(ind,sample.EMA26,'blue',label='MA256',linestyle='--')
    ax2.text(ind[-1], sample.high[-1], sample.index.get_level_values(index)[-1].strftime('%Y-%m-%d'),
             fontdict={'size': '12', 'color': 'b'})
    ax2.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    # ax2.set_xticklabels(sample.index.get_level_values(index)[::3])
    ax2.grid(True)
    ax2.legend(loc='best')
    fig.autofmt_xdate()

    ax3 = fig.add_subplot(2, 1, 2, sharex=ax2)
    ax3.set_title("force", fontsize='xx-large', fontweight='bold')
    # ax1 = ax2.twinx()   #not working like it's
    #ax3.bar(ind, sample.FORCE)
    ax3.plot(ind, sample.FCEMA2, 'red',label='EMA2') #marker='o'
    ax3.text(N/2, max(pd.DataFrame.max(sample.FCEMA13),pd.DataFrame.max(sample.FCEMA2)),
             "EMA13>0 Optimism, EMA13<0 Pessmist, EMA run around 0 means no trend", fontdict={'size': '16', 'color': 'b'})

    ax3.axhline(y=0, ls="--", c="red")  # 添加水平直线 also dot line as :
    #plt.axvline(x=4, ls="-", c="green")  # 添加垂直直线
    ax3.plot(ind, sample.FCEMA13, 'b-',label='EMA13')
    ax3.grid(True)
    ax3.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    ax3.legend(loc='best')
    fig.autofmt_xdate()

    plt.show()

def forceANA(code):
    cur = datetime.datetime.now()
    endtime = str(cur.year) + '-' + str(cur.month) + '-' + str(cur.day)
    #daydata = QA.QA_fetch_stock_day_adv(code, uti.startday, endtime)
    dd = QA.QA_fetch_stock_day_adv(code,uti.startday,endtime)

    dayd = force(dd.data)
    wt.weekDFANA(code,'2018-01-01',endtime)
    plot(dayd,uti.dayindex,uti.dayformate)
    mind = QA.QA_fetch_stock_min_adv(code,uti.startday,endtime,frequence='30min')
    sample =force(mind.data)
    ms = sample[-256:]
    #print(str(sample.index.get_level_values(uti.index)[-256]).split(' ')[0])
    day_start = 0
    for i in range(0,dayd.shape[0]):
        if(str(dayd.index.get_level_values(uti.dayindex)[i]).split(' ')[0]==str(sample.index.get_level_values(uti.index)[-256]).split(' ')[0]):
            day_start = i
            break
            #print(i)
            #print(dayd.index.get_level_values(uti.dayindex)[i-dayd.shape[0]])
    #ds = dayd[i-dayd.shape[0]:]
    ds = dayd[-256:]
    #print (daydata)
        #if(dayd.index.get_level_values(i)=='2020-04-14'):
            #print(i)
    #plot(sample[-256:],uti.index,uti.formate)
    #weekly df

    DayMin(ds,ms)



if __name__ == "__main__":
    forceANA('600745')
    #wd = QA.QAFetch.QATdx.QA_fetch_get_stock_day('515050','2019-10-18','2020-04-06')
    #print(wd)
    #sample = force(wd)

    #plot(sample)
    #forceANA('002241')