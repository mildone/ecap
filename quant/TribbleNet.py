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
import re

read_dictionary = np.load('/Users/jiangyongnan/git/ecap/liutong.npy', allow_pickle=True).item()
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtk
import mpl_finance as mpf
import quant.Util as uti
import quant.MACD as mmacd
import quant.weekTrend as wt
def plot(sample,index,format,type='Day'):
    #this works for day and min level
    quotes = mmacd.MINcandlestruct(sample, index, format)
    N = sample.index.get_level_values(index).shape[0]
    ind = np.arange(N)
    def format_date(x, pos=None):
        thisind = np.clip(int(x + 0.5), 0, N - 1)
        return sample.index.get_level_values(index)[thisind].strftime(format)

    fig = plt.figure()
    fig.set_size_inches(40.5, 32.5)
    # plt.xlabel('Trading Day')
    # plt.ylabel('MACD EMA')
    ax2 = fig.add_subplot(3, 1, 1)
    ax2.set_title("candlestick for "+type, fontsize='xx-large', fontweight='bold')

    # fig,ax=plt.subplots()
    # mpf.candlestick_ochl(ax2,quotes,width=0.2,colorup='r',colordown='g',alpha=1.0)
    # ax2.xaxis_date()
    # plt.setp(plt.gca().get_xticklabels(),rotation=30)
    # ax2.plot(ind,sample.close,'b-',marker='*')
    mpf.candlestick_ochl(ax2, quotes, width=0.6, colorup='r', colordown='g', alpha=1.0)
    ax2.text(N/2, pd.DataFrame.max(sample.EMA13), "EMA13 tells trend",
             fontdict={'size': '16', 'color': 'b'})
    ax2.plot(ind, sample.MA64,'red',label='MA64',linestyle='--')
    ax2.plot(ind,sample.MA256,'blue',label='MA256',linestyle='--')
    ax2.text(ind[-1], sample.high[-1], sample.index.get_level_values(index)[-1].strftime('%Y-%m-%d'),
             fontdict={'size': '12', 'color': 'b'})
    ax2.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    # ax2.set_xticklabels(sample.index.get_level_values(index)[::3])
    ax2.grid(True)
    ax2.legend(loc='best')
    fig.autofmt_xdate()

    ax3 = fig.add_subplot(3, 1, 2, sharex=ax2)
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

    ax1 = fig.add_subplot(3, 1, 3, sharex=ax2)
    ax1.set_title("MACD", fontsize='xx-large', fontweight='bold')
    ax1.plot(ind, sample.MACDQ, 'r-', label='quick/DIF')
    ax1.plot(ind, sample.MACDSIG, 'blue', label='sig/DEA')
    m_red = np.where(sample.MACDBlock >= 0, sample.MACDBlock, 0)
    m_green = np.where(sample.MACDBlock < 0, sample.MACDBlock, 0)
    ax1.bar(ind, m_red, color='red')
    ax1.bar(ind, m_green, color='green')

    ax1.grid(True)
    ax1.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    ax1.legend(loc='best')
    fig.autofmt_xdate()


    #plt.show()
    #pic = type+'.png'
    print('call plot')
    plt.savefig(r'./%s.png'%type)
    plt.close()

def TNANA(code):
    cur = datetime.datetime.now()
    mon = str(cur.month)
    day = str(cur.day)
    if(re.match('[0-9]{1}',mon) and len(mon)==1):
        mon ='0'+mon
    if (re.match('[0-9]{1}', day) and len(day) == 1):
        day = '0' + day


    endtime = str(cur.year) + '-' + mon + '-' + day

    dd = QA.QA_fetch_stock_day_adv(code,uti.startday,endtime)

    dayd = uti.initData(dd.data)
    #NET 1, WEEK
    wt.weekDFANA(code,'2018-01-01',endtime)
    print('done week')
    #NET 2, DAY
    plot(dayd,uti.dayindex,uti.dayformate)

    #NET 3, 30 MIN & 60 MIN
    mind = QA.QA_fetch_stock_min_adv(code,uti.startday,endtime,frequence='30min')
    sample =uti.initData(mind.data)
    ms = sample[-128:]
    #print(str(sample.index.get_level_values(uti.index)[-256]).split(' ')[0])
    day_start = 0
    for i in range(0,dayd.shape[0]):
        if(str(dayd.index.get_level_values(uti.dayindex)[i]).split(' ')[0]==str(sample.index.get_level_values(uti.index)[-256]).split(' ')[0]):
            day_start = i
            break
            #print(i)
            #print(dayd.index.get_level_values(uti.dayindex)[i-dayd.shape[0]])
    #ds = dayd[i-dayd.shape[0]:]
    ds = dayd[-128:]
    #print (daydata)
        #if(dayd.index.get_level_values(i)=='2020-04-14'):
            #print(i)
    #plot(sample[-256:],uti.index,uti.formate)
    #weekly df
    plot(ms,uti.index,uti.formate,'30MIN')
    #DayMin(ds,ms)

    mind6 = QA.QA_fetch_stock_min_adv(code, uti.startday, endtime, frequence='60min')
    sample6 = uti.initData(mind6.data)
    ms6 = sample6[-128:]
    plot(ms6, uti.index, uti.formate,'60MIN')
    print('done tribbleNet')



if __name__ == "__main__":
    TNANA('600745')
