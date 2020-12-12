import datetime
import smtplib
from email.mime.text import MIMEText
import QUANTAXIS as QA
import dateutil

try:
    assert QA.__version__ >= '1.1.0'
except AssertionError:
    print('pip install QUANTAXIS >= 1.1.0 请升级QUANTAXIS后再运行此示例')
    import QUANTAXIS as QA
from abupy import ABuRegUtil

import re
from matplotlib import gridspec
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtk
import mpl_finance as mpf

index = 'datetime'
formate = '%Y-%m-%dT%H:%M:%S'
dayindex = 'date'
dayformate = '%Y-%m-%d'
startday = '2018-01-01'
wstartday = '2015-01-01'

def percSet(pw, rw, rl):
    pw = 0.47  # backtest win ratio
    rw = 1.15  # sell when got 15% increase
    rl = 0.97  # end if loss 0.03 of holdings
    # kelly rule of holdings
    return (pw / rl) - (1 - pw) / rw

# percSet(pw,rw,rl)


def candlestruct(sample):
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


def getStocklist():
    """
    get all stock as list
    usage as:
    QA.QA_util_log_info('GET STOCK LIST')
    stocks=getStocklist()
    """
    data = QA.QAFetch.QATdx.QA_fetch_get_stock_list('stock')
    stock = data['code'].index
    stocklist = []
    for code in stock:
        stocklist.append(code[0])
    return stocklist


def calAngle(df):
    """
    trend angle based on provided dataframe
    """
    return ABuRegUtil.calc_regress_deg(df.close.values, show=False)

def change_jump(df):
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
def change(dd):
    from functools import reduce
    pp_array = [float(close) for close in dd]
    temp_array = [(price1, price2) for price1, price2 in zip(pp_array[:-1], pp_array[1:])]
    change = list(map(lambda pp: reduce(lambda a, b: round((b - a) / a, 3), pp), temp_array))
    change.insert(0, 0)
    return change


def divergence( day,short = 20, mid = 60, long = 120):
    # change first (d[i].close-d[i-1].close)/d[i-1].close
    """
    supported Indicators
    @change, close(today)-preclose/preclose, up when greater than 0, down when less than 0
    @ MA and EMA of short, mid, long which are configurable
    @ Indicator for monitoring divergence of market invest change by time
    @ CS is (close- shortEMA)/shortEMA
    @ SM is (shortEMA - midEMA)/midEMA
    @ ML is (midEMA-longEMA)/longEMA
    @ BIAS is (close - longEMA)/longEMA
    General Rule of writing indicators:
    * ignore those which can be directly got from QUANTAXIS e.g. MACD, KDJ, .etc.
    * only the one which is used for pattern monitoring and build on top of QUANTAXIS ones
    """

    day['long'] = QA.EMA(day.close, long)
    day['lo'] = QA.MA(day.close, long)
    day['mi'] = QA.MA(day.close, mid)
    day['sh'] = QA.MA(day.close, short)
    day['mid'] = QA.EMA(day.close, mid)
    day['short'] = QA.EMA(day.close, short)
    day['BIAS'] = (day.close - day.long) * 100 / day.long
    day['BMA'] = QA.EMA(day.BIAS,short)
    day['CS'] = (day.close - day.short) * 100 / day.short
    day['CM'] = (day.close - day.mid) * 100 / day.mid
    day['SM'] = (day.short - day.mid) * 100 / day.mid
    day['ML'] = (day.mid - day.long) * 100 / day.long
    #Short MA and Mid MA
    day['SMAcc'] = change(day.SM)
    #Mid and Long MA
    day['MLAcc'] = change(day.ML)
    day['TS'] = (day.close > day.short).astype(int) + (day.close > day.sh).astype(int) + (day.close > day.mid).astype(int)\
                + (day.close > day.mi).astype(int) + (day.sh > day.mi).astype(int)
    day['RTS'] = (day.short > day.close).astype(int) + (day.sh > day.close).astype(int) + (day.mid > day.close).astype(int)\
                 + (day.mi > day.close).astype(int) + (day.mi > day.sh).astype(int)

    return day


def PlotBySe(day, short = 20, mid = 60, long = 120,type='EA',zoom=100,plot='SML',numofax = 3, mark = False,bias = True):
    """
    value of Type:
    * E or A  at least 1, E means EMA, A means MA
    * SML  at least 1, S=short, M=mid, L=long
    e.g. ESM will plot Short EMA, Mid EMA
    ASL will plot short MA, long MA

    """

    divergence(day,short,mid,long)


    if (zoom > day.shape[0]):
        day = day[0:]
    else:
        day = day[0 - zoom:]
    change_jump(day)
    quotes = candlestruct(day)
    # N = sample.index.get_level_values(index).shape[0]
    N = day.shape[0]
    ind = np.arange(N)

    def format_date(x, pos=None):
        thisind = np.clip(int(x + 0.5), 0, N - 1)
        return day.index.get_level_values(dayindex)[thisind]

    if(numofax==1):
        fig = plt.figure()
        gs = gridspec.GridSpec(3, 1)
        fig.set_size_inches(30.5, 20.5)
        ax2 = fig.add_subplot(gs[1:3,0:1])
        ax2.set_title("candlestick", fontsize='xx-large', fontweight='bold')

        mpf.candlestick_ochl(ax2, quotes, width=0.6, colorup='r', colordown='g', alpha=1.0)
        if ('EA' in type):
            # both EMA and MA are required
            if ('S' in plot):
                ax2.plot(ind, day.sh, 'purple', label='MA' + str(short), linewidth=0.7)
                ax2.plot(ind, day.short, 'purple', label='EMA' + str(short), linewidth=0.7, ls='--')
            if ('M' in plot):
                ax2.plot(ind, day.mi, 'blue', label='MA' + str(mid), linewidth=0.7)
                ax2.plot(ind, day.mid, 'blue', label='EMA' + str(mid), linewidth=0.7, ls='--')
            if ('L' in plot):
                ax2.plot(ind, day.lo, 'r-', label='MA' + str(long), linewidth=0.7)
                ax2.plot(ind, day.long, 'r-', label='EMA' + str(long), linewidth=0.7, ls='--')

        else:
            # Only EMA Or MA is required
            if ('S' in plot and 'E' in type):
                ax2.plot(ind, day.short, 'purple', label='EMA' + str(short), linewidth=0.7, ls='--')
            if ('S' in plot and 'A' in type):
                ax2.plot(ind, day.sh, 'purple', label='MA' + str(short), linewidth=0.7)

            if ('M' in plot and 'E' in type):
                ax2.plot(ind, day.mid, 'blue', label='EMA' + str(mid), linewidth=0.7, ls='--')
            if ('M' in plot and 'A' in type):
                ax2.plot(ind, day.mi, 'blue', label='MA' + str(mid), linewidth=0.7)
            if ('L' in plot and 'E' in type):
                ax2.plot(ind, day.long, 'r-', label='EMA' + str(long), linewidth=0.7, ls='--')
            if ('L' in plot and 'A' in type):
                ax2.plot(ind, day.lo, 'r-', label='MA' + str(long), linewidth=0.7)

        # plot SML Position for later simulation
        ratio = day.low.median() * 0.03
        value = np.where(day.RTS > 2, day.close, 0)
        ax2.fill_between(ind, 0, value)
        ax2.text(N - short, day.high[N - short] + ratio,
                 str(day.close[N - short]),
                 fontdict={'size': '12', 'color': 'b'})
        ax2.text(N - mid, day.high[N - mid] + ratio,
                 str(day.close[N - mid]),
                 fontdict={'size': '12', 'color': 'b'})
        ax2.text(N - long, day.high[N - long] + ratio,
                 str(day.close[N - long]),
                 fontdict={'size': '12', 'color': 'b'})
        if(mark):
            ax2.axhline(y=day.close[N-long],ls='--',color='red')
            ax2.axhline(y=day.close[N-mid],ls='--',color='blue')
            ax2.axhline(y=day.close[N - short], ls='--', color='purple')

        ax2.text(N - 1, day.high[-1] + ratio,
                 str(day.close[-1]),
                 fontdict={'size': '8', 'color': 'b'})
        ax2.text(N - 1, day.high[-1] + 3*ratio,
                 str(day.long[-1]),
                 fontdict={'size': '8', 'color': 'b'})
        ax2.plot(N - short, day.low[N - short] - ratio, '^', markersize=4, markeredgewidth=2, markerfacecolor='None',
                 markeredgecolor='purple')
        # ax2.axvline(x=N-short,ls='--',color='purple')
        ax2.plot(N - mid, day.low[N - mid] - ratio, '^', markersize=4, markeredgewidth=2, markerfacecolor='None',
                 markeredgecolor='blue')
        ax2.plot(N - long, day.low[N - long] - ratio, '^', markersize=4, markeredgewidth=2, markerfacecolor='None',
                 markeredgecolor='red')

        # ax2.plot(100, 30, 'go', markersize=12, markeredgewidth=0.5,
        # markerfacecolor='None', markeredgecolor='green')
        # plot jump position
        for i in range(N):
            if (day.jump[i] == 1):
                ax2.plot(i, day.low[i], 'ro', markersize=12, markeredgewidth=2, markerfacecolor='None',
                         markeredgecolor='red')
            if (day.jump[i] == -1):
                ax2.plot(i, day.high[i], 'go', markersize=12, markeredgewidth=2, markerfacecolor='None',
                         markeredgecolor='green')

        if('single' in list(day.columns)):
            for i in range(N):
                if (day.single[i] == 1):
                    ax2.axvline(x=i, ls='--', color='red')
                if (day.single[i] == 3):
                    ax2.axvline(x=i, ls='--', color='green')
                if(day.single[i]==5):
                    ax2.axvline(x=i,ls='--',color='blue')

        ax2.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
        ax2.grid(True)
        ax2.legend(loc='upper left')
        fig.autofmt_xdate()

        ax3 = fig.add_subplot(gs[0:1, 0:1])
        # ax3.set_title("Divergence", fontsize='xx-large', fontweight='bold')
        bar_red = np.where(day.BIAS>0,day.BIAS,0)
        bar_green = np.where(day.BIAS<=0,day.BIAS,0)
        ax3.bar(ind, bar_red, color='red', label='BIAS')
        ax3.bar(ind,bar_green,color='green',label='BIAS')

        ax3.plot(ind,day.BMA, 'black')
        ax3.plot(ind, day.CS, 'blue', label='close/sohrt', linewidth=1)
        ax3.plot(ind, day.SM, 'green', label='short/mid', linewidth=1)
        ax3.grid(True)
        ax3.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
        ax3.legend(loc='upper left')
        fig.autofmt_xdate()

        plt.show()
    elif(numofax==3):
        fig = plt.figure()
        fig.set_size_inches(40.5, 20.5)
        gs = gridspec.GridSpec(7, 1)

        ax3 = fig.add_subplot(gs[0:1, 0:1])
        #ax3.set_title("Divergence", fontsize='xx-large', fontweight='bold')
        bar_red = np.where(day.BIAS > 0, day.BIAS, 0)
        bar_green = np.where(day.BIAS <= 0, day.BIAS, 0)

        #ax3.axhline(y=day.BIAS[-1],color='grey',ls='--')
        ax3.plot(ind, day.CS, 'grey', label='CS', linewidth=1)
        ax3.plot(ind, day.SM, 'blue', label='SM', linewidth=1)
        ax3.plot(ind, day.ML, color='green', label='ML', linewidth=1)
        if(bias):
            #ax3.bar(ind, day.BIAS, color='grey', label='BIAS')
            ax3.bar(ind, bar_red, color='red')
            ax3.bar(ind, bar_green, color='green')
        else:
            ax3.bar(ind, day.CM, color = 'grey', label = 'CLOSE/MID')


        ax3.grid(True)
        ax3.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
        ax3.legend(loc='upper left')
        fig.autofmt_xdate()

        ax1 = fig.add_subplot(gs[6:7, 0:1], sharex=ax3)
        #ax1.set_title("volume", fontsize='xx-large', fontweight='bold')
        bar_red = np.where(day.close > day.open, day.volume, 0)
        bar_green = np.where(day.close < day.open, day.volume, 0)
        ax1.bar(ind, bar_red, color='red')
        ax1.bar(ind, bar_green, color='green')
        # ax3.plot(ind,day.vma,'orange',label='volume EMA20')
        ax1.axhline(y=day.volume.median(), ls='--', color='grey')
        # x3.bar(ind,day.BIAS,color='blue')
        # ax3.axhline(y=0,ls='--',color='yellow')
        ax1.grid(True)
        ax1.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
        ax1.legend(loc='upper left')
        fig.autofmt_xdate()

        ax2 = fig.add_subplot(gs[1:6, 0:1], sharex=ax3)
        #ax2.set_title("candlestick", fontsize='xx-large', fontweight='bold')

        mpf.candlestick_ochl(ax2, quotes, width=0.6, colorup='r', colordown='g', alpha=1.0)
        value = np.where(day.RTS>2,day.close,0)
        win = np.where(day.TS>3,day.close,0)
        danger = np.where(day.TS<3,day.close,0)
        #ax2.fill_between(ind,0,value,color='green',alpha=0.3)
        ax2.fill_between(ind,0,value,color='green',alpha=0.3)
        ax2.fill_between(ind,0,win,color='red',alpha=0.3)
        #v = np.where(day.single>0,day.close,0)
        #ax2.fill_between(ind,0,v,color='red',alpha=0.3)


        if ('EA' in type):
            # both EMA and MA are required
            if ('S' in plot):
                ax2.plot(ind, day.sh, 'purple', label='MA' + str(short), linewidth=0.7)
                ax2.plot(ind, day.short, 'purple', label='EMA' + str(short), linewidth=0.7, ls='--')
            if ('M' in plot):
                ax2.plot(ind, day.mi, 'blue', label='MA' + str(mid), linewidth=0.7)
                ax2.plot(ind, day.mid, 'blue', label='EMA' + str(mid), linewidth=0.7, ls='--')
            if ('L' in plot):
                ax2.plot(ind, day.lo, 'r-', label='MA' + str(long), linewidth=0.7)
                ax2.plot(ind, day.long, 'r-', label='EMA' + str(long), linewidth=0.7, ls='--')

        else:
            # Only EMA Or MA is required
            if ('S' in plot and 'E' in type):
                ax2.plot(ind, day.short, 'purple', label='EMA' + str(short), linewidth=0.7, ls='--')
            if ('S' in plot and 'A' in type):
                ax2.plot(ind, day.sh, 'purple', label='MA' + str(short), linewidth=0.7)

            if ('M' in plot and 'E' in type):
                ax2.plot(ind, day.mid, 'blue', label='EMA' + str(mid), linewidth=0.7, ls='--')
            if ('M' in plot and 'A' in type):
                ax2.plot(ind, day.mi, 'blue', label='MA' + str(mid), linewidth=0.7)
            if ('L' in plot and 'E' in type):
                ax2.plot(ind, day.long, 'r-', label='EMA' + str(long), linewidth=0.7, ls='--')
            if ('L' in plot and 'A' in type):
                ax2.plot(ind, day.lo, 'r-', label='MA' + str(long), linewidth=0.7)

        # plot SML Position for later simulation
        ratio = day.low.median() * 0.03

        ax2.text(N - short, day.high[N - short] + ratio,
                 str(day.close[N - short]),
                 fontdict={'size': '12', 'color': 'b'})
        ax2.text(N - mid, day.high[N - mid] + ratio,
                 str(day.close[N - mid]),
                 fontdict={'size': '12', 'color': 'b'})
        ax2.text(N - long, day.high[N - long] + ratio,
                 str(day.close[N - long]),
                 fontdict={'size': '12', 'color': 'b'})
        ax2.text(N - 1, day.high[-1] + ratio,
                 'cur: '+str(day.close[-1]),
                 fontdict={'size': '8', 'color': 'b'})
        ax2.text(N - 1, day.high[-1] + 3*ratio,
                 '120: '+str(day.long[-1]),
                 fontdict={'size': '8', 'color': 'b'})
        if(mark):
            ax2.axhline(y=day.close[N - long], ls='--', color='red')
            ax2.axhline(y=day.close[N - mid], ls='--', color='blue')
            ax2.axhline(y=day.close[N - short], ls='--', color='purple')

        ax2.plot(N - short, day.low[N - short] - ratio, '^', markersize=4, markeredgewidth=2, markerfacecolor='None',
                 markeredgecolor='purple')
        # ax2.axvline(x=N-short,ls='--',color='purple')
        ax2.plot(N - mid, day.low[N - mid] - ratio, '^', markersize=4, markeredgewidth=2, markerfacecolor='None',
                 markeredgecolor='blue')
        ax2.plot(N - long, day.low[N - long] - ratio, '^', markersize=4, markeredgewidth=2, markerfacecolor='None',
                 markeredgecolor='red')

        # ax2.plot(100, 30, 'go', markersize=12, markeredgewidth=0.5,
        # markerfacecolor='None', markeredgecolor='green')
        # plot jump position
        for i in range(N):
            if (day.jump[i] == 1):
                ax2.plot(i, day.low[i], 'ro', markersize=12, markeredgewidth=2, markerfacecolor='None',
                         markeredgecolor='red')
            if (day.jump[i] == -1):
                ax2.plot(i, day.high[i], 'go', markersize=12, markeredgewidth=2, markerfacecolor='None',
                         markeredgecolor='green')
        if ('single' in list(day.columns)):
            for i in range(N):
                if (day.single[i] == 1):
                    ax2.axvline(x=i, ls='--', color='red')
                if (day.single[i] == 3):
                    ax2.axvline(x=i, ls='--', color='green')
        ax2.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
        ax2.grid(True)
        ax2.legend(loc='upper left')
        fig.autofmt_xdate()

        plt.show()





def getWeekDate(daytime):
    # daytime will be pandas datetime
    # return Timestamp('2020-05-11 00:00:00')
    return daytime + dateutil.relativedelta.relativedelta(days=(6 - daytime.dayofweek))

def prepareData(code,start='2017-01-01',end = 'cur', cg='stock',source='DB',frequence='day'):
    if(end == 'cur'):
        cur = datetime.datetime.now()
        mon = str(cur.month)
        day = str(cur.day)
        if (re.match('[0-9]{1}', mon) and len(mon) == 1):
            mon = '0' + mon
        if (re.match('[0-9]{1}', day) and len(day) == 1):
            day = '0' + day

        et = str(cur.year) + '-' + mon + '-' + day
    else:
        et = end
    #et = '2020-07-01'
    print(et)
    if(cg == 'stock' and frequence=='day'):
        start = '2010-01-01'
        #sample = QA.QA_fetch_stock_day_adv(code, start, et).data

        sample = QA.QA_fetch_stock_day_adv(code, start, et).data
        nstart = (sample.index.get_level_values(dayindex)[-1]+dateutil.relativedelta.relativedelta(days=1)).strftime(dayformate)
        print(nstart)
        if(nstart<=et):
            td = QA.QAFetch.QATdx.QA_fetch_get_stock_day(code,nstart,et,if_fq='bfq')
            td.set_index(['date','code'],inplace=True)
            td.drop(['date_stamp'], axis=1, inplace=True)
            td.rename(columns={'vol': 'volume'}, inplace=True)
            sample = pd.concat([td, sample], axis=0,sort=True)
            sample.sort_index(inplace=True,level='date')
    elif(cg == 'stock' and frequence!='day'):
        start = '2010-01-01'
        #sample = QA.QA_fetch_stock_day_adv(code, start, et).data

        sample = QA.QA_fetch_stock_min_adv(code, start, et,frequence=frequence).data
        nstart = (sample.index.get_level_values(index)[-1]+dateutil.relativedelta.relativedelta(days=1)).strftime(dayformate)
        #nstart = (sample.index.get_level_values(dayindex)[-1]+dateutil.relativedelta.relativedelta(days=1)).strftime(dayformate)
        print(nstart)
        if(nstart<=et):
            m15 = QA.QA_fetch_get_stock_min('tdx', code, et, et, level=frequence)
            # convert online data to adv data(basically multi_index setting, drop unused column and contact 2 dataframe as 1)
            # this is network call
            m15.set_index(['datetime', 'code'], inplace=True)
            m15.drop(['date', 'date_stamp', 'time_stamp'], axis=1, inplace=True)

            m15.rename(columns={'vol': 'volume'}, inplace=True)
            sample = pd.concat([m15, sample], axis=0, sort=True)
            sample.sort_index(inplace=True, level='datetime')


    elif(cg == 'index' and frequence=='day'):
        start = '2019-10-01'
        #sample = QA.QA_fetch_index_day_adv(code, start, et).data

        sample = QA.QA_fetch_index_day_adv(code, start, et).data
        nstart = (sample.index.get_level_values(dayindex)[-1] + dateutil.relativedelta.relativedelta(days=1)).strftime(dayformate)
        if(nstart<=et):
            td = QA.QAFetch.QATdx.QA_fetch_get_index_day(code,nstart,et)
            td.set_index(['date','code'],inplace=True)
            td.drop(['date_stamp'], axis=1, inplace=True)
            td.rename(columns={'vol': 'volume'}, inplace=True)
            sample = pd.concat([td, sample], axis=0,sort=True)
            sample.sort_index(inplace=True,level='date')
    elif(cg == 'index' and frequence !='day'):
        start = '2019-09-01'
        nstart = start
        #sample = QA.QA_fetch_index_min_adv(code, start, et, frequence=frequence).data
        #nstart = (sample.index.get_level_values(index)[-1] + dateutil.relativedelta.relativedelta(days=1)).strftime(dayformate)
        # nstart = (sample.index.get_level_values(dayindex)[-1]+dateutil.relativedelta.relativedelta(days=1)).strftime(dayformate)
        if (nstart <= et):
            m15 = QA.QA_fetch_get_index_min('tdx', code, nstart, et, level=frequence)
            # convert online data to adv data(basically multi_index setting, drop unused column and contact 2 dataframe as 1)
            # this is network call
            m15.set_index(['datetime', 'code'], inplace=True)
            m15.drop(['date', 'date_stamp', 'time_stamp'], axis=1, inplace=True)

            m15.rename(columns={'vol': 'volume'}, inplace=True)
            sample = m15
            sample.sort_index(inplace=True, level='datetime')


    return sample


def forceANA(code,zo=100,ty = 'EA',cg = 'stock', st = 20, mi = 60, ln = 120, pt='SM',nm=3,bias=True):
    dd = prepareData(code,cg=cg)
    #import quant.Util as ut
    #ut.trendWeekMinv3(dd)
    PlotBySe(dd,type = ty,zoom = zo, short = st, mid = mi, long = ln,plot=pt,numofax=nm,bias=bias)



if __name__ == "__main__":

    forceANA('000977',zo=400,ty = 'EA', cg = 'stock', st = 20, mi = 60, ln = 120, pt='SML',nm=3,bias=True)
    #api = QA.QA_TTSBroker()


