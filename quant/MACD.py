import datetime
import smtplib
from email.mime.text import MIMEText
import QUANTAXIS as QA
try:
    assert QA.__version__>='1.1.0'
except AssertionError:
    print('pip install QUANTAXIS >= 1.1.0 请升级QUANTAXIS后再运行此示例')
    import QUANTAXIS as QA
import re
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
import matplotlib.dates as mpd
import quant.Util as uti
import datetime

def MINMACACalculate(sample):
    rate = 0.015
    sample['EMA12'] = QA.EMA(sample.close, 12)
    sample['EMA5']=QA.EMA(sample.close,5)
    sample['MA64']=QA.MA(sample.close,64)
    sample['MA256']=QA.MA(sample.close,256)
    sample['EMA20']=QA.EMA(sample.close,20)
    sample['k1'] = 0.618 * QA.HHV(sample.high, 256) + 0.382 * QA.LLV(sample.low, 256)
    sample['k2'] = 0.5 * QA.HHV(sample.high, 256) + 0.5 * QA.LLV(sample.low, 256)
    sample['k3'] = 0.382 * QA.HHV(sample.high, 256) + 0.618 * QA.LLV(sample.low, 256)
    sample['EMA30']=QA.EMA(sample.close,30)
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
    #sample['VolumeEMA'] = QA.EMA(sample.vol, 5)

    #trend block
    from abupy import pd_rolling_max
    from abupy import pd_expanding_max
    N = 15
    sample['nhigh']=pd_rolling_max(sample.high,window=N)
    expanmax = pd_expanding_max(sample.close)
    sample['nhigh'].fillna(value=expanmax,inplace=True)

    from abupy import pd_rolling_min, pd_expanding_min
    sample['nlow']=pd_rolling_min(sample.low,window=N)
    expanmin = pd_expanding_min(sample.close)
    sample['nlow'].fillna(value=expanmin,inplace = True)



    sroc = []
    for i in range(sample.shape[0]):
        if (i - 21 > 0 and sample.iloc[i].EMA13 != None and sample.iloc[i - 21].EMA13 != None):
            # print(sample.iloc[i].EMA13/sample.iloc[i-21].EMA13)
            sroc.append((sample.iloc[i].EMA13 / sample.iloc[i - 21].EMA13) * 100)
        else:
            sroc.append(100)
    sample['SROC'] = sroc


    return sample


def MINcandlestruct(sample, index, timeFrmate):

    quotes = []
    #pydate_array = sample.index.get_level_values(index).to_pydatetime()
    #date_only_array = np.vectorize(lambda s: s.strftime(timeFrmate))(pydate_array)
    # date_only_series = pd.Series(date_only_array)
    #N = sample.index.get_level_values(index).shape[0]
    N = sample.shape[0]
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


def MINMACDPLOT(sample, index, formate):
    quotes = MINcandlestruct(sample, index, formate)
    #N = sample.index.get_level_values(index).shape[0]
    N = sample.shape[0]
    ind = np.arange(N)

    def format_date(x, pos=None):
        thisind = np.clip(int(x + 0.5), 0, N - 1)
        return sample.index.get_level_values(index)[thisind].strftime(formate)

    fig = plt.figure()
    fig.set_size_inches(40.5, 20.5)
    # plt.xlabel('Trading Day')
    # plt.ylabel('MACD EMA')
    #ax2 = fig.add_subplot(6, 1, 1)
    ax2 = fig.add_subplot(3,1,1)
    ax2.set_title("candlestick", fontsize='xx-large', fontweight='bold')

    # fig,ax=plt.subplots()
    # mpf.candlestick_ochl(ax2,quotes,width=0.2,colorup='r',colordown='g',alpha=1.0)
    # ax2.xaxis_date()
    # plt.setp(plt.gca().get_xticklabels(),rotation=30)
    # ax2.plot(ind,sample.close,'b-',marker='*')
    mpf.candlestick_ochl(ax2, quotes, width=0.6, colorup='r', colordown='g', alpha=1.0)
    ax2.plot(ind,sample.MA64,'r-',label='MA64')
    ax2.plot(ind,sample.MA256,'blue',label='MA256')
    for i in range(N):
        if(sample.single[i]==1):
            ax2.axvline(x=i,ls='--',color='red')
        if(sample.single[i]==3):
            ax2.axvline(x=i,ls='--',color='green')
    #ax2.plot(ind,sample.EMA20,'green')
    #ax2.plot(ind,sample.EMA30,'purple')
    #ax2.plot(ind,sample.nhigh)
    #ax2.plot(ind,sample.nlow)
   # ax2.fill_between(ind,sample.EMA13,color='blue',alpha=0.08)

    #ax2.text(N / 2, pd.DataFrame.max(sample.high), "EMA13 tells the trend",
    #         fontdict={'size': '12', 'color': 'b'})
    ax2.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    # ax2.set_xticklabels(sample.index.get_level_values(index)[::3])
    ax2.grid(True)
    ax2.legend(loc='best')
    fig.autofmt_xdate()



    #ax1 = fig.add_subplot(6, 1, 2, sharex=ax2)
    ax1 = fig.add_subplot(3,1,2,sharex=ax2)
    ax1.set_title('macd', fontsize='xx-large', fontweight='bold')
    ax1.text(N / 2, pd.DataFrame.max(sample.MACDQ), "MACD Block trend .vs. price trend",
             fontdict={'size': '12', 'color': 'b'})
    ax1.grid(True)
    ax1.plot(ind, sample.MACDQ, 'r-',label='quick')
    ax1.plot(ind, sample.MACDSIG,'blue',label='sig')
    m_red = np.where(sample.MACDBlock>=0,sample.MACDBlock,0)
    m_green = np.where(sample.MACDBlock<0,sample.MACDBlock,0)
    ax1.bar(ind, m_red,color='red')
    ax1.bar(ind,m_green,color='green')

    ax1.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    # ax2.set_yticks(np.linspace(ax2.get_yticks()[0], ax2.get_yticks()[-1], len(ax1.get_yticks())))
    ax2.legend(loc='best')
    fig.autofmt_xdate()




    ax3 = fig.add_subplot(3, 1, 3, sharex=ax2)
    ax3.set_title("volume", fontsize='xx-large', fontweight='bold')
    # ax1 = ax2.twinx()   #not working like it's
    bar_red = np.where(sample.close>sample.open,sample.volume,0)
    ax3.bar(ind,bar_red,color='red')
    bar_green = np.where(sample.close<sample.open,sample.volume,0)
    ax3.bar(ind,bar_green,color='green')
    #ax3.bar(ind, sample.volume)
    ax3.plot(ind, sample.VolumeEMA, 'r-')
    ax3.grid(True)
    ax3.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    fig.autofmt_xdate()

    '''
    ax4 = fig.add_subplot(6, 1, 4, sharex=ax2)
    ax4.set_title("OPTIMISM", fontsize='xx-large', fontweight='bold')
    # ax1 = ax2.twinx()   #not working like it's
    ax4.text(N / 2, pd.DataFrame.max(sample.optimism), "pay attention to up & down trend, if op less than 0 means super sell",
             fontdict={'size': '12', 'color': 'b'})
    ax4.bar(ind, sample.optimism)
    ax4.grid(True, which='minor')
    ax4.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    fig.autofmt_xdate()

    ax5 = fig.add_subplot(6, 1, 5, sharex=ax2)
    ax5.set_title('PESSMIST', fontsize='xx-large', fontweight='bold')
    ax5.text(N / 2, pd.DataFrame.max(sample.pessmist),
             "pay attention to up & down trend, if pessmist larger than 0 means super buy",
             fontdict={'size': '12', 'color': 'b'})
    ax5.grid(True, which='minor')
    ax5.bar(ind, sample.pessmist)
    ax5.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    fig.autofmt_xdate()
    
    ax6 = fig.add_subplot(6, 1, 6, sharex=ax2)
    ax6.set_title("EMA13/SROC21", fontsize='xx-large', fontweight='bold')
    ax6.text(N / 2, pd.DataFrame.max(sample.SROC),
             "Pay attention to turn around of trend",
             fontdict={'size': '12', 'color': 'b'})
    # ax1 = ax2.twinx()   #not working like it's
    ax6.plot(ind, sample.SROC, 'r-')
    ax6.axhline(y=np.mean(sample.SROC),ls='--',c='red')
    ax6.grid(True)
    ax6.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    fig.autofmt_xdate()
    '''

    '''
    import random
    maxvalue = pd.DataFrame.max(sample.MACDBlock)
    minv =pd.DataFrame.min(sample.MACDBlock)
    for i in range(sample.shape[0]):
        if (sample.MACDBlock[i - 1] < 0 and sample.MACDBlock[i] >= 0):
            ax1.axvline(x=i, ls="-", c="red")  # 添加垂直直线
            ax2.axvline(x=i,ls="-",c="red")
#            print(str(sample.index.get_level_values(uti.dayindex)[i].strftime('%D')))
            ax2.text(i, sample.high[i],
                     str(sample.index.get_level_values(index)[i].strftime('%D')),
                     fontdict={'size': '8', 'color': 'b'})
            
            #ax1.annotate('buy %s' % sample.index.get_level_values('date')[i].strftime('%D'),
                         #xy=(i, sample.MACDBlock[i]), xytext=(i, sample.MACDBlock[i] + random.uniform(maxvalue*0.7, maxvalue)),
                         #xycoords='data',
                         #arrowprops=dict(facecolor='red', shrink=0.05))
            
        elif (sample.MACDBlock[i - 1] >= 0 and sample.MACDBlock[i] < 0):
            ax1.axvline(x=i, ls="-", c="green")  # 添加垂直直线
            ax2.axvline(x=i,ls="-",c="green")
            ax2.text(i, pd.DataFrame.min(sample.low),
                     sample.index.get_level_values(index)[i].strftime('%D'),
                     fontdict={'size': '8', 'color': 'b'})
            
            #ax1.annotate('sell %s' % sample.index.get_level_values('date')[i].strftime('%D'),
                         #xy=(i, sample.MACDBlock[i]), xytext=(i, sample.MACDBlock[i] + random.uniform(maxvalue*0.25, maxvalue*0.7)),
                         #xycoords='data',
                         #arrowprops=dict(facecolor='green', shrink=0.05))
    '''
    #plt.legend()

    code = sample.index.get_level_values('code')[0]

    # plt.savefig('/home/mildone/monitor/'+'Trend'+code+'.png')
    plt.show()
    plt.close()


def MINMACDPLOT_Candlestick(sample, index, formate):
    quotes = MINcandlestruct(sample, index, formate)
    #N = sample.index.get_level_values(index).shape[0]
    N = sample.shape[0]
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
    start = 0
    end = 0



    # fig,ax=plt.subplots()
    # mpf.candlestick_ochl(ax2,quotes,width=0.2,colorup='r',colordown='g',alpha=1.0)
    # ax2.xaxis_date()
    # plt.setp(plt.gca().get_xticklabels(),rotation=30)
    # ax2.plot(ind,sample.close,'b-',marker='*')
    mpf.candlestick_ochl(ax2, quotes, width=0.6, colorup='r', colordown='g', alpha=1.0)
    ax2.fill_between(ind,0,sample.close,color='blue',alpha=0.08)
    for i in range(sample.shape[0]):
        if (sample.MACDBlock[i - 1] < 0 and sample.MACDBlock[i] >= 0):
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

        elif (sample.MACDBlock[i - 1] >= 0 and sample.MACDBlock[i] < 0):
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
            start = 0
            end = 0
    ax2.set_ylim(np.min(sample.close)-5,np.max(sample.close+5))
    ax2.plot(ind, sample.EMA13,'red')
    ax2.plot(ind, sample.EMA5,'yellow')
    ax2.plot(ind, sample.EMA30,'blue')

    #ax2.plot([ind[-10],ind[-20]],[sample.close[-10],sample.close[-20]],'o-',color='red')

    # ax2.fill_between(ind,sample.EMA13,color='blue',alpha=0.08)

    ax2.text(N / 2, pd.DataFrame.max(sample.high), "EMA13 tells the trend, 5 yellow,13 red, 30 blue",
             fontdict={'size': '12', 'color': 'b'})

    ax2.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    # ax2.set_xticklabels(sample.index.get_level_values(index)[::3])
    ax2.grid(True)
    # t.legend()
    fig.autofmt_xdate()

    # ax1 = fig.add_subplot(6, 1, 2, sharex=ax2)

    ax1 = fig.add_subplot(2, 1, 2, sharex=ax2)
    ax1.set_title('macd', fontsize='xx-large', fontweight='bold')
    ax1.text(N / 2, pd.DataFrame.max(sample.MACDQ), "MACD Block trend .vs. price trend",
             fontdict={'size': '12', 'color': 'b'})
    ax1.grid(True)
    ax1.plot(ind, sample.MACDQ, 'r-', marker='*')
    ax1.plot(ind, sample.MACDSIG)
    m_red = np.where(sample.MACDBlock >= 0, sample.MACDBlock, 0)
    m_green = np.where(sample.MACDBlock < 0, sample.MACDBlock, 0)
    ax1.bar(ind, m_red, color='red')
    ax1.bar(ind, m_green, color='green')
    #print(sample.index.get_level_values('date')[-1])

    # ax1.annotate('buy %s' % sample.index.get_level_values('date')[i].strftime('%D'),
    # xy=(i, sample.MACDBlock[i]), xytext=(i, sample.MACDBlock[i] + random.uniform(maxvalue*0.7, maxvalue)),
    # xycoords='data',
    # arrowprops=dict(facecolor='red', shrink=0.05
    #print(sample.index.get_level_values('date')[-1].strftime('%D'))

    ax2.text(ind[-1], sample.high[-1], sample.index.get_level_values(index)[-1].strftime('%Y-%m-%d'),
             fontdict={'size': '12', 'color': 'b'})

    ax1.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    # ax2.set_yticks(np.linspace(ax2.get_yticks()[0], ax2.get_yticks()[-1], len(ax1.get_yticks())))
    fig.autofmt_xdate()
    ax2.legend(['20EMA','5EMA','30EMA'],loc='best')
    ax1.legend(['MACDQ','MACDSIG','MACDBlock'],loc='best')
    plt.show()


def macdANA(code,start='2019-01-01'):
    cur = datetime.datetime.now()
    endtime = str(cur.year) + '-' + str(cur.month) + '-' + str(cur.day)
    print(endtime)
    mindata = QA.QA_fetch_stock_day_adv(code, start, endtime)
    index = 'datetime'
    formate = '%Y-%m-%dT%H:%M:%S'
    dayindex = 'date'
    dayformate = '%Y-%m-%d'
    daydata = QA.QA_fetch_stock_day_adv(code, start, endtime)

    # MINMACACalculate(mindata.data)
    # MINMACDPLOT(mindata.data,index,formate)
    MINMACACalculate(daydata.data)
    uti.trendBreak(daydata.data)
    print(daydata.data)
    MINMACDPLOT(daydata.data[-80:], dayindex, dayformate)

    MINMACDPLOT_Candlestick(daydata.data[-80:],dayindex,dayformate)


def minMACDANA(code, start='2019-01-01',period=512,frequence='15min'):
    cur = datetime.datetime.now()
    day = str(cur.day)
    if(str(cur.month)!='10' or str(cur.month)!='11' or str(cur.month)!='12'):
        month='0'+str(cur.month)
    if (re.match('[0-9]{1}',day) and len(day)==1):
        day = '0' + str(cur.day)
    endtime = str(cur.year) + '-' + month + '-' +day
    print(endtime)
    mindata = QA.QA_fetch_stock_min_adv(code, '2019-01-01', endtime, frequence)


    # MINMACACalculate(mindata.data)
    # MINMACDPLOT(mindata.data,index,formate)
    print(mindata.data)
    MINMACACalculate(mindata.data)
    MINMACDPLOT(mindata.data[0-period:], uti.index, uti.formate)

if __name__ == "__main__":
    #macdANA('002241')
    minMACDANA('000810','15min')


