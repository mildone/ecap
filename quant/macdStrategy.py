#!/usr/bin/python
# _*_ coding: UTF-8 _*_
from quant.strategy import strategy
import QUANTAXIS as QA
try:
    assert QA.__version__>='1.1.0'
except AssertionError:
    print('pip install QUANTAXIS >= 1.1.0 请升级QUANTAXIS后再运行此示例')
    import QUANTAXIS as QA
import numpy as np
read_dictionary = np.load('/Users/jiangyongnan/git/ecap/liutong.npy',allow_pickle=True).item()
import pandas as pd
import numpy as np
import quant.Util as uti


class macdStrategy(strategy):
    def __init__(self,df):
        super().__init__(df)
    def plotmacd(self,index,formate):
        super().plot(index,formate)

    def applySingle(self,short = 5,long =15,freq='60min'):
        """
         1.DIF向上突破DEA，买入信号参考。
         2.DIF向下跌破DEA，卖出信号参考。
         """
        dd=self.sample
        dayindex = uti.dayindex
        dayformate = uti.dayformate
        start = dd.index.get_level_values(dayindex)[0].strftime(dayformate)
        end = dd.index.get_level_values(dayindex)[-1].strftime(dayformate)
        mindata = QA.QA_fetch_stock_min_adv(dd.index.get_level_values('code')[0], start, end, frequence=freq)
        sample = mindata.data
        # print(sample)
        sample['short'] = QA.EMA(sample.close, short)
        sample['long'] = QA.EMA(sample.close, long)
        CROSS_5 = QA.CROSS(sample.short, sample.long)
        CROSS_15 = QA.CROSS(sample.long, sample.short)

        C15 = np.where(CROSS_15 == 1, 3, 0)
        m = np.where(CROSS_5 == 1, 1, C15)
        # single = m[:-1].tolist()
        # single.insert(0, 0)
        sample['single'] = m.tolist()
        sig = [0]
        for i in range(1, len(dd)):
            if (dd.trend[i] < 3):
                sig.append(0)
            else:

                temp = sample[sample.index.get_level_values(uti.index).strftime(dayformate) ==
                              dd.index.get_level_values(dayindex)[i].strftime(dayformate)][:-1]
                # print(temp.shape[0])
                tmp = sample[sample.index.get_level_values(uti.index).strftime(dayformate) ==
                             dd.index.get_level_values(dayindex)[i - 1].strftime(dayformate)][-1:].single[0]
                temp['sig'] = temp.single.cumsum()
                sig.append(temp.sig[-1] + tmp)

        try:
            self.sample['single'] = sig

        except:
            print('error with {}'.format(sample.index.get_level_values('code')[0]))
            self.sample['single'] = 0


