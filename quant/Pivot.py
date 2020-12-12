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


read_dictionary = np.load('../liutong.npy', allow_pickle=True).item()
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtk
import mpl_finance as mpf
import quant.Util as uti
import quant.MACD as mmacd
import quant.weekTrend as wt

def pivotIndicator(data, index, formate):
    # prepare data
    sample = uti.MACACalculate(data)[-90:]
    # candlestick prepare
    quotes = mmacd.MINcandlestruct(sample, index, formate)

    N = sample.index.get_level_values(index).shape[0]

    # formate timeindex
    ind = np.arange(N)

    def format_date(x, pos=None):
        thisind = np.clip(int(x + 0.5), 0, N - 1)
        return sample.index.get_level_values(index)[thisind].strftime(formate)

    fig = plt.figure()
    fig.set_size_inches(20.5, 12.5)
    # plt.xlabel('Trading Day')
    # plt.ylabel('MACD EMA')
    ax2 = fig.add_subplot(3, 1, 1)
    ax2.set_title("candlestick with EMA13")
    ax2.plot(ind, sample.EMA13)
    mpf.candlestick_ochl(ax2, quotes, width=0.6, colorup='r', colordown='g', alpha=1.0)
    ax2.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))

    ax2.grid(True, which='minor')
    # t.legend()
    fig.autofmt_xdate()

    ax3 = fig.add_subplot(3, 1, 2, sharex=ax2)
    ax3.set_title("OPTIMISM")
    # ax1 = ax2.twinx()   #not working like it's
    baro_red = np.where(sample.optimism>0,sample.optimism,0)
    baro_purple = np.where(sample.optimism<0,sample.optimism,0)
    ax3.bar(ind, baro_red,color='red')
    ax3.bar(ind,baro_purple,color='purple')
    ax3.grid(True, which='minor')
    ax3.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    fig.autofmt_xdate()

    ax1 = fig.add_subplot(3, 1, 3, sharex=ax2)
    ax1.set_title('PESSMIST')
    ax1.grid(True, which='minor')
    bar_green = np.where(sample.pessmist<0,sample.pessmist,0)
    bar_yellow = np.where(sample.pessmist >0, sample.pessmist,0)
    ax1.bar(ind, bar_green,color='green')
    ax1.bar(ind,bar_yellow,color='yellow')
    ax1.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    fig.autofmt_xdate()
    plt.legend()

    # code = sample.index.get_level_values('code')[0]

    # plt.savefig('/home/mildone/monitor/'+'Trend'+code+'.png')
    plt.show()
    plt.close()




def strategyWP(code):
    '''
    check first the week trend by comparing MACD peak with price
    optimisim and pessmist compare,

    :param code: stock number
    :return: plot view

    '''
    cur = datetime.datetime.now()
    endtime = str(cur.year) + '-' + str(cur.month) + '-' + str(cur.day)
    #df = QA.QA_fetch_stock_day_adv(code, '2018-01-01',endtime)
    #df = QA.QA_fetch_stock_day_adv(code, uti.startday, endtime)

    #sda = df.data
    #wd = wt.weekDF(sda)
    #sample = wd
    #wt.weektrend(sample)
    #wt.weekPlot(sample)
    wt.weekDFANA(code)


    testdata =QA.QA_fetch_stock_day_adv(code, uti.startday, endtime)
    pivotIndicator(testdata.data, uti.dayindex, uti.dayformate)
    test = testdata.data
    mmacd.MINMACACalculate(test)
    mmacd.MINMACDPLOT(test,uti.dayindex,uti.dayformate)



if __name__ == "__main__":
    #strategyWP('600745')
    strategyWP('002384')