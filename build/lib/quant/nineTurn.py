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


def TrendTunel(sample):
    sample['highEMAS25']=QA.EMA(sample.high,25)
    sample['lowEMAS25'] = QA.EMA(sample.low,25)
    sample['Stunel']=sample.highEMAS25-sample.lowEMAS25
    sample['highEMAL90']=QA.EMA(sample.high,90)
    sample['lowEMAL90']=QA.EMA(sample.low,90)
    sample['EMA13'] = QA.EMA(sample.close, 13)
    size = sample.shape[0]
    hold = []
    for i in range(0,size):
        if(sample.close[i]>sample.highEMAS25[i] and sample.close[i]>sample.highEMAL90[i]):
            hold.append(100)
        elif (sample.close[i] < sample.lowEMAL90[i] and sample.close[i] < sample.lowEMAS25[i]):
            hold.append(0)
        elif(sample.highEMAL90[i]>sample.highEMAS25[i] and sample.close[i]>sample.highEMAS25[i] and sample.close[i]<sample.highEMAL90[i]):
            hold.append(40)
        elif(sample.highEMAL90[i]<sample.highEMAS25[i] and sample.close[i]<sample.highEMAS25[i] and sample.close[i]>sample.highEMAL90[i]):
            hold.append(60)
        else:
            hold.append(0)
    sample['hold']=hold

    sample = uti.init_trendMACD(sample,10)
    return sample

def macdHDeviate(hl):

    import math

    localMax = 0
    hm_index = 0

    peakMax = []

    for i in range(0, len(hl)):

        if (not math.isnan(hl[i]) and hl[i] != 0):

            if (hl[i] > localMax):
                hm_index = i
                localMax = hl[i]
        else:
            if (localMax != 0 and hm_index != 0):
                peakMax.append((hm_index, localMax))
                localMax = 0
                hm_index = 0

    if (localMax != peakMax[-1][1] and hm_index != peakMax[-1][0] and localMax !=0):
        peakMax.append((hm_index, localMax))
    return peakMax

def macdLDeviate(tl):

    import math
    localMin = 0
    localMax = 0
    hm_index = 0
    lm_index = 0
    peakMin = []

    for i in range(0, len(tl)):

        if (not math.isnan(tl[i]) and tl[i] != 0):

            if (tl[i] < localMin):
                lm_index = i
                localMin = tl[i]
        else:
            if (localMin != 0 and lm_index != 0):
                peakMin.append((lm_index, localMin))
                localMin = 0
                lm_index = 0
    if (localMin != peakMin[-1][1] and lm_index != peakMin[-1][0] and localMin!=0):
        peakMin.append((lm_index, localMin))
    return peakMin

def plot(sample):
    quotes = mmacd.MINcandlestruct(sample, uti.dayindex, uti.dayformate)
    N = sample.index.get_level_values(uti.dayindex).shape[0]
    ind = np.arange(N)
    sample = mmacd.MINMACACalculate(sample)
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

    #check high sell or low buy time
    for i in range(13,N):
        Raise =1
        Down = 1
        #print('round {}'.format(i))
        for j in range(i-8,i+1):
            #print('round {}, index {}'.format(i,j))
            if(sample.close[j]>sample.close[j-4]):
                Raise = Raise * 1
                Down = Down * 0
            else:
                Raise = Raise * 0
                Down = Down * 1
        #if(Raise and max(sample.close[i],sample.close[i-1])>max(sample.close[i-2],sample.close[i-3])):
        #if (Raise and sample.close[i] > sample.close[i - 2]):
        if (Raise):
                ax2.scatter(ind[i], sample.high[i] + 1, marker='o', c='blueviolet',s=10)
                #ax2.text(ind[i], sample.high[i]+1, ".",
                    #fontdict={'size': '12', 'color': 'red'})
            #ax2.text(ind[i],sample.high[i]*1.05,'*',
                #fontdict={'size': '12', 'color': 'red'})
                '''
                for m in range(i-8,i+1):
                    ax2.text(ind[m],sample.high[m]+1,".",
                          fontdict={'size': '12', 'color': 'skyblue'})
                '''
        #if (Down and min(sample.close[i], sample.close[i - 1]) < min(sample.close[i - 2], sample.close[i - 3])):
        #if (Down and sample.close[i] < sample.close[i-2]):
        if (Down):
                #for n in range(i - 9, i):
            ax2.scatter(ind[i],sample.low[i]-1, marker = 'o', c='g',s=10)
            #ax2.text(ind[i],sample.low[i]-1,".",fontdict={'size': '12', 'color': 'green'})
            '''
            for n in range(i-8,i+1):
                ax2.text(ind[n],sample.low[n]-1,".",
                          fontdict={'size': '12', 'color': 'green'})
            '''

    #draw Long and Short trend
    # draw Long and Short trend
    bar_redhs = np.where(sample.close > sample.highEMAS25, sample.highEMAS25, 0)
    bar_redls = np.where(sample.close > sample.highEMAS25, sample.lowEMAS25, 0)
    bar_greenhs = np.where(sample.close < sample.lowEMAS25, sample.highEMAS25, 0)
    bar_greenls = np.where(sample.close < sample.lowEMAS25, sample.lowEMAS25, 0)
    for i in range(N):
        pass


    ax2.plot(ind, sample.highEMAS25, 'purple',label='duanduo')
    ax2.plot(ind, sample.lowEMAS25, 'purple',ls='--',label='duankong')
    #ax2.plot(ind, sample.highEMAL90, 'yellow')
    #ax2.plot(ind, sample.lowEMAL90, 'yellow')
    #ax2.plot(ind,sample.EMA13,'red')


    #ax2.fill_between(ind, bar_redls, bar_redhs, facecolor='pink', alpha=0.3)
    #ax2.fill_between(ind, bar_greenls, bar_greenhs, facecolor='blue', alpha=0.3)

    bar_redhl = np.where(sample.close > sample.highEMAL90, sample.highEMAL90, 0)
    bar_redll = np.where(sample.close > sample.highEMAL90, sample.lowEMAL90, 0)

    bar_greenhl = np.where(sample.close < sample.lowEMAL90, sample.highEMAL90, 0)
    bar_greenll = np.where(sample.close < sample.lowEMAL90, sample.lowEMAL90, 0)
    rsi = QA.QA_indicator_RSI(sample)

    #ax2.plot(ind, sample.highEMAS25, 'purple')
    #ax2.plot(ind, sample.lowEMAS25, 'purple')
    ax2.plot(ind, sample.highEMAL90, 'blue',label='changduo')
    ax2.plot(ind, sample.lowEMAL90, 'blue',ls='--',label='changekong')
    #ax2.fill_between(ind, bar_redls, bar_redhs, facecolor='red', alpha=0.3)
    #ax2.fill_between(ind, bar_greenls, bar_greenhs, facecolor='green', alpha=0.3)

    #ax2.fill_between(ind, bar_redll, bar_redhl, facecolor='deeppink', alpha=0.3)
    #ax2.fill_between(ind, bar_greenll, bar_greenhl, facecolor='blue', alpha=0.3)
    hold_red = np.where(sample.hold == 100, 2, 0)
    hold_purple = np.where(sample.hold == 60, 2, 0)
    hold_yellow = np.where(sample.hold == 40, 2, 0)
    hold_green = np.where(sample.hold == 0, 2, 0)

    ax2.bar(ind, hold_red, color='red')
    ax2.bar(ind, hold_purple, color='purple')
    ax2.bar(ind, hold_yellow, color='yellow')
    ax2.bar(ind, hold_green, color='green')
    #    ax2.text(N/2, pd.DataFrame.max(sample.EMA13), "EMA13 tells trend",
         #    fontdict={'size': '16', 'color': 'b'})
#    ax2.plot(ind, sample.EMA13)
    #ax2.text(ind[-1], sample.high[-1], sample.index.get_level_values('date')[-1].strftime('%Y-%m-%d'),
             #fontdict={'size': '12', 'color': 'b'})
    ax2.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    # ax2.set_xticklabels(sample.index.get_level_values(index)[::3])
    ax2.grid(True)
    ax2.legend(['Long Term blue ', 'short Term Purple','1 red ', '0.6 purple', '0.4 yellow','0 green'],
               loc='upper left')
    fig.autofmt_xdate()

    ax1 = fig.add_subplot(2, 1, 2, sharex=ax2)
    ax1.set_title('macd', fontsize='xx-large', fontweight='bold')
    ax1.text(N / 2, pd.DataFrame.max(sample.MACDQ), "MACD Block trend .vs. price trend",
             fontdict={'size': '12', 'color': 'b'})
    ax1.grid(True)
    #ax1.plot(ind, sample.MACDQ, 'r-', marker='.')
    ax1.plot(ind, sample.MACDQ, 'r-')
    ax1.plot(ind, sample.MACDSIG)
    m_red = np.where(sample.MACDBlock >= 0, sample.MACDBlock, 0)
    m_green = np.where(sample.MACDBlock < 0, sample.MACDBlock, 0)
    temp = sample.MACDBlock - m_red
    pm = macdLDeviate(temp.to_list())

    hemp = sample.MACDBlock - m_green
    mm = macdHDeviate(hemp.to_list())
    ax1.bar(ind, m_red, color='red')
    ax1.bar(ind, m_green, color='green')
    #ax1.plot(ind,sample.trend,'purple')
    ax1.plot([pm[-2][0],pm[-1][0]],[pm[-2][1],pm[-1][1]],color='green',linestyle='--')
    if(len(pm)>2):
        ax1.plot([pm[-1][0], pm[-3][0]], [pm[-1][1], pm[-3][1]], color='green',linestyle='--')
    ax1.plot([mm[-2][0], mm[-1][0]], [mm[-2][1], mm[-1][1]], color='red',linestyle='--')
    if(len(mm)>2):
        ax1.plot([mm[-1][0],mm[-3][0]],[mm[-1][1],mm[-3][1]],color='red',linestyle='--')
    ax1.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    ax1.legend(['MACDQ Red','MACDSIG Blue'],loc='upper left')
    # ax2.set_yticks(np.linspace(ax2.get_yticks()[0], ax2.get_yticks()[-1], len(ax1.get_yticks())))
    fig.autofmt_xdate()

    plt.show()


def nineTurnANA(code):

    cur = datetime.datetime.now()
    if (str(cur.month) != '10' or str(cur.month) != '11' or str(cur.month) != '12'):
        month = '0' + str(cur.month)
    endtime = str(cur.year) + '-' + month + '-' + str(cur.day)
    print(endtime)
    data = QA.QA_fetch_stock_day_adv(code, '2019-05-01', endtime)
    sample=data.data
    #sample = QA.QAFetch.QATdx.QA_fetch_get_stock_day('515050','2019-10-18','2020-04-06')

    sample = TrendTunel(sample)
    print(sample)
    plot(sample)




if __name__ == "__main__":
    nineTurnANA('000977')
    
    #forceANA('002241')