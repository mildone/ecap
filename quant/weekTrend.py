import QUANTAXIS as QA
try:
    assert QA.__version__>='1.1.0'
except AssertionError:
    print('pip install QUANTAXIS >= 1.1.0 请升级QUANTAXIS后再运行此示例')
    import QUANTAXIS as QA
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtk
import mpl_finance as mpf
import datetime
import quant.MACD as md
import dateutil as du

def weekDF(df):
    df.reset_index(inplace=True)
    #df.reset_index()

    df.drop(['code'],axis=1,inplace=True)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index("date", inplace=True)
    period = 'W'

    weekly_df = df.resample(period).last()
    weekly_df['open'] = df['open'].resample(period).first()
    weekly_df['high'] = df['high'].resample(period).max()
    weekly_df['low'] = df['low'].resample(period).min()
    weekly_df['close'] = df['close'].resample(period).last()
    weekly_df['volume'] = df['volume'].resample(period).sum()
    weekly_df['amount'] = df['amount'].resample(period).sum()
    weekly_df.reset_index('date',inplace=True)
    return weekly_df

def wds(df,period='W'):
    df['date'] = pd.to_datetime(df.index.get_level_values('date'))
    df.set_index("date", inplace=True)
    #period = 'W'

    weekly_df = df.resample(period).last()
    weekly_df['open'] = df['open'].resample(period).first()
    weekly_df['high'] = df['high'].resample(period).max()
    weekly_df['low'] = df['low'].resample(period).min()
    weekly_df['close'] = df['close'].resample(period).last()
    weekly_df['volume'] = df['volume'].resample(period).sum()
    weekly_df['amount'] = df['amount'].resample(period).sum()
    weekly_df.reset_index('date',inplace=True)
    return weekly_df


def TrendDivergence(wk, short=20, mid=60, long=120):
    wk['long'] = pd.Series.rolling(wk.close, long).mean()
    wk['mid'] = pd.Series.rolling(wk.close, mid).mean()
    wk['short'] = pd.Series.rolling(wk.close, short).mean()

    wk['BIAS'] = (wk.close - wk.long) * 100 / wk.long
    wk['CS'] = (wk.close - wk.short) * 100 / wk.short
    wk['SM'] = (wk.short - wk.mid) * 100 / wk.mid
    wk['ML'] = (wk.mid - wk.long) * 100 / wk.long
    return wk


def TrendDetect(sample,short=5,mid=10,long=15):
    sample['short'] = pd.Series.ewm(sample.close, span=short, min_periods=short - 1, adjust=True).mean()
    sample['mid'] = pd.Series.ewm(sample.close, span=mid, min_periods=mid - 1, adjust=True).mean()
    sample['long'] = pd.Series.ewm(sample.close, span=long, min_periods=long - 1, adjust=True).mean()
    sample['CS'] = (sample.close - sample.short) * 100 / sample.short
    sample['SM'] = (sample.short - sample.mid) * 100 / sample.mid
    sample['ML'] = (sample.mid - sample.long) * 100 / sample.long
    sample['BIAS'] =(sample.close-sample.long) * 100/ sample.long
    return sample



def weektrend(sample):
    #print(sample)
    from functools import reduce
    sample['EMA12']= pd.Series.ewm(sample.close, span=12, min_periods=12 - 1, adjust=True).mean()
    sample['EMA26']= pd.Series.ewm(sample.close, span=26, min_periods=26 - 1, adjust=True).mean()
    sample['EMA5'] = pd.Series.ewm(sample.close, span=5, min_periods=5 - 1, adjust=True).mean()
    sample['EMA10'] = pd.Series.ewm(sample.close, span=10, min_periods=10 - 1, adjust=True).mean()
    sample['EMA13']=pd.Series.ewm(sample.close,span=13,min_periods=13-1,adjust=True).mean()
    sample['MACDQ']= sample['EMA12']-sample['EMA26']
    sample['MACDSIG']=pd.Series.ewm(sample.MACDQ, span=9, min_periods=9 - 1, adjust=True).mean()
    sample['MACDBlock']=sample['MACDQ']-sample['MACDSIG']
    sample['trend']=sample['EMA5']-sample['EMA10']
    sample['CS'] = (sample.close-sample.EMA5)*100/sample.EMA5


    CROSS_5 = QA.CROSS(sample.EMA5, sample.EMA10)
    CROSS_15 = QA.CROSS(sample.EMA10, sample.EMA5)

    C15 = np.where(CROSS_15 == 1, 3, 0)
    m = np.where(CROSS_5 == 1, 1, C15)
    # single = m[:-1].tolist()
    # single.insert(0, 0)
    sample['ws'] = m.tolist()


    pp_array = [float(close) for close in sample.MACDBlock]
    temp_array = [(price1, price2) for price1, price2 in zip(pp_array[:-1], pp_array[1:])]
    change = list(map(lambda pp: reduce(lambda a, b: round((b - a) / a, 3) if a!=0 else 0, pp), temp_array))
    change.insert(0, 0)
    sample['change'] = change
    '''
    kdj = QA.QA_indicator_KDJ(sample)
    sample['K'] = kdj.KDJ_K
    sample['D'] = kdj.KDJ_D
    sample['J'] = kdj.KDJ_J
    '''

    return sample



def weekPlot(sample, short=20, mid=60, long=120):
    quotes = []
    N = sample.shape[0]
    ind = np.arange(N)
    for i in range(len(sample)):
        li = []
        datef = ind[i]  # 日期转换成float days
        open_p = sample.open[i]
        close_p = sample.close[i]
        high_p = sample.high[i]
        low_p = sample.low[i]
        li = [datef, open_p, close_p, high_p, low_p]
        t = tuple(li)
        quotes.append(t)

    def format_date(x, pos=None):
        thisind = np.clip(int(x + 0.5), 0, N - 1)
        return sample.date[thisind].strftime('%Y-%m-%d')

    fig = plt.figure()
    fig.set_size_inches(30.5, 20.5)
    print('call here')
    ax2 = fig.add_subplot(3, 1, 1)
    ax2.set_title("weekly candlestick", fontsize='xx-large', fontweight='bold')

    mpf.candlestick_ochl(ax2, quotes, width=0.6, colorup='r', colordown='g', alpha=1.0)
    ax2.plot(ind,sample.long,'r-',label='MA'+str(long))
    ax2.plot(ind,sample.mid,'blue',label='MA'+str(mid))
    ax2.plot(ind,sample.short,'grey',label='MA'+str(short))
    ax2.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    ax2.grid(True)
    ax2.legend(loc='best')
    fig.autofmt_xdate()

    ax1 = fig.add_subplot(3, 1, 2, sharex=ax2)
    ax1.set_title('weekly macd', fontsize='xx-large', fontweight='bold')
    ax1.grid(True)
    ax1.plot(ind, sample.MACDQ, 'red',label='DIF')
    ax1.plot(ind, sample.MACDSIG, 'blue',label='DEA')
    m_red = np.where(sample.MACDBlock >= 0, sample.MACDBlock, 0)
    m_green = np.where(sample.MACDBlock < 0, sample.MACDBlock, 0)
    ax1.bar(ind, m_red, color='red')
    ax1.bar(ind, m_green, color='green')
    ax1.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    # ax2.set_yticks(np.linspace(ax2.get_yticks()[0], ax2.get_yticks()[-1], len(ax1.get_yticks())))
    ax1.legend(loc='best')
    fig.autofmt_xdate()
    '''
    ax3 = fig.add_subplot(3, 1, 3, sharex=ax2)
    ax3.set_title('weekly kdj', fontsize='xx-large', fontweight='bold')
    ax3.grid(True)
    ax3.plot(ind, sample.K, 'r-')
    ax3.plot(ind,sample.D,'g-')
    ax3.axhline(y=80,ls='--',color='red')
    ax3.axhline(y=20,ls='--',color='purple')
    ax1.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    # ax2.set_yticks(np.linspace(ax2.get_yticks()[0], ax2.get_yticks()[-1], len(ax1.get_yticks())))
    fig.autofmt_xdate()
    '''
    plt.legend()
    #plt.savefig(r'week1.png')
    #plt.close()
    plt.show()





def weekDFANA(code,start='2018-01-01',end='current'):

    cur = datetime.datetime.now()
    endtime = str(cur.year) + '-' + str(cur.month) + '-' + str(cur.day)
    if(end == 'current'):
        et = endtime
    else:
        et = end
    df = QA.QA_fetch_stock_day_adv(code, start, et)
    sda = df.data
    #sda = QA.QAFetch.QATdx.QA_fetch_get_stock_day('515050','2019-10-18','2020-04-06')
    #print(sda)


    wd = wds(sda)
    #print(wd)

    sample = wd
    weektrend(sample)
    TrendDivergence(wd)
    #print(sample)
    weekPlot(sample)






if __name__ == "__main__":
    weekDFANA('000977')