#!/usr/bin/python
# _*_ coding: UTF-8 _*_
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
read_dictionary = np.load('../liutong.npy',allow_pickle=True).item()
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtk
import mpl_finance as mpf




class strategy:
    def __init__(self,df):
        self.sample = df
        self.sample['EMA12'] = QA.EMA(df.close, 12)
        self.sample['EMA5'] = QA.EMA(df.close, 5)
        self.sample['MA64'] = QA.MA(df.close, 64)
        self.sample['MA256'] = QA.MA(df.close, 256)
        self.sample['EMA30'] = QA.EMA(df.close, 30)
        self.sample['EMA13'] = QA.EMA(df.close, 13)
        self.sample['optimism'] = self.sample.high - self.sample.EMA13
        self.sample['pessmist'] = self.sample.low - self.sample.EMA13
        quotes = []
        N = self.sample.shape[0]
        ind = np.arange(N)
        for i in range(len(self.sample)):
            li = []
            # datet=datetime.datetime.strptime(sample.index.get_level_values('date'),'%Y%m%d')   #字符串日期转换成日期格式
            # datef=mpd.date2num(datetime.datetime.strptime(date_only_array[i],'%Y-%m-%d'))
            datef = ind[i]  # 日期转换成float days
            open_p = self.sample.open[i]
            close_p = self.sample.close[i]
            high_p = self.sample.high[i]
            low_p = self.sample.low[i]
            li = [datef, open_p, close_p, high_p, low_p]
            t = tuple(li)
            quotes.append(t)
        self.qots = quotes
    def applySingle(self):
        self.sample['single']=[0]*self.sample.shape[0]

    def plot(self,index,formate,period=50):
        tmp = self.sample[0-period:]
        #N = self.sample.shape[0]
        N = tmp.shape[0]
        ind = np.arange(N)

        def format_date(x, pos=None):
            thisind = np.clip(int(x + 0.5), 0, N - 1)
            return self.sample.index.get_level_values(index)[thisind].strftime(formate)

        fig = plt.figure()
        fig.set_size_inches(40.5, 20.5)
        ax2 = fig.add_subplot(3, 1, 1)
        ax2.set_title("candlestick", fontsize='xx-large', fontweight='bold')
        mpf.candlestick_ochl(ax2, self.qots, width=0.6, colorup='r', colordown='g', alpha=1.0)
        ax2.plot(ind, self.sample.MA64, 'r-', label='MA64')
        ax2.plot(ind, self.sample.MA256, 'blue', label='MA256')
        for i in range(N):
            if (self.sample.single[i] == 1):
                ax2.axvline(x=i, ls='--', color='red')
            if (self.sample.single[i] == 3):
                ax2.axvline(x=i, ls='--', color='green')

        ax2.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
        # ax2.set_xticklabels(sample.index.get_level_values(index)[::3])
        ax2.grid(True)
        ax2.legend(loc='best')
        fig.autofmt_xdate()
        #code = self.sample.index.get_level_values('code')[0]
        # plt.savefig('/home/mildone/monitor/'+'Trend'+code+'.png')
        plt.show()
        plt.close()



