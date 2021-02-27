import sys
import os
import QUANTAXIS as QA

sys.path.append(os.path.abspath('../'))
try:
    assert QA.__version__ >= '1.1.0'
except AssertionError:
    print('pip install QUANTAXIS >= 1.1.0 请升级QUANTAXIS后再运行此示例')
    import QUANTAXIS as QA
import core.Util as uti



def radar(sample,short=20,mid=60,long=120,level='15min'):
    code = sample.index.get_level_values('code')[-1]
    wend = sample.index.get_level_values(uti.dayindex)[-1].strftime(uti.dayformate)
    wstart = sample.index.get_level_values(uti.dayindex)[0].strftime(uti.dayformate)
    test = QA.QA_fetch_stock_min_adv(code,wstart,wend,frequence=level).data
    uti.divergence(test)

    t6 = QA.QA_fetch_stock_min_adv(code, wstart, wend, frequence='60min').data
    uti.divergence(t6)
    mins = []
    buy = 0
    sell = 0
    for i in range(test.shape[0]):
        if(test.CS[i]>0 and test.SM[i]>0 and test.ML[i]>0 and buy ==0):
            mins.append(1)
            buy = 1
            sell = 0
        elif(test.CS[i]<0 and test.SM[i]<0 and test.ML[i]<0 and sell == 0):
            mins.append(3)
            buy = 0
            sell = 1
        else:
            mins.append(0)
    test['single'] = mins


    sample['single'] = 0
    for i in range(test.shape[0]):
        if(test.single[i]==1):
            dat = test.index.get_level_values(uti.index)[i].strftime(uti.dayformate)
            sample.loc[sample[sample.index.get_level_values(uti.dayindex) == dat].index, ['single']] = 1
        elif(test.single[i]==3):
            dat = test.index.get_level_values(uti.index)[i].strftime(uti.dayformate)
            sample.loc[sample[sample.index.get_level_values(uti.dayindex) == dat].index, ['single']] = 3
    return sample



def radarv2(sample,short=20,mid=60,long=120,level='15min'):
    code = sample.index.get_level_values('code')[-1]
    wend = sample.index.get_level_values(uti.dayindex)[-1].strftime(uti.dayformate)
    wstart = sample.index.get_level_values(uti.dayindex)[0].strftime(uti.dayformate)
    test = QA.QA_fetch_stock_min_adv(code,wstart,wend,frequence=level).data
    uti.divergence(test)

    t6 = QA.QA_fetch_stock_min_adv(code, wstart, wend, frequence='60min').data
    uti.divergence(t6)
    mins = []
    buy = 0
    sell = 0
    for i in range(test.shape[0]):
        if(test.CS[i]>0 and test.SM[i]>0 and test.ML[i]>0 and buy ==0):
            mins.append(1)
            buy = 1
            sell = 0
        elif(test.CS[i]<0 and test.SM[i]<0 and test.ML[i]<0 and sell == 0):
            mins.append(3)
            buy = 0
            sell = 1
        else:
            mins.append(0)
    test['single'] = mins

    buy = 0
    sell = 0
    m6s = []
    for i in range(t6.shape[0]):
        if (t6.CS[i] > 0 and t6.SM[i] > 0 and t6.ML[i] > 0 and buy == 0):
            m6s.append(1)
            buy = 1
            sell = 0
        elif (t6.CS[i] < 0 and t6.SM[i] < 0 and t6.ML[i]<0 and sell == 0):
            m6s.append(3)
            buy = 0
            sell = 1
        else:
            m6s.append(0)
    t6['single'] = m6s


    sample['single'] = 0
    for i in range(test.shape[0]):
        if(test.single[i]==1):
            dat = test.index.get_level_values(uti.index)[i].strftime(uti.dayformate)
            sample.loc[sample[sample.index.get_level_values(uti.dayindex) == dat].index, ['single']] = 1
        '''
        elif(test.single[i]==3):
            dat = test.index.get_level_values(uti.index)[i].strftime(uti.dayformate)
            sample.loc[sample[sample.index.get_level_values(uti.dayindex) == dat].index, ['single']] = 3
        '''

    for i in range(t6.shape[0]):
        if(t6.single[i]==3):
            dat = t6.index.get_level_values(uti.index)[i].strftime(uti.dayformate)
            sample.loc[sample[sample.index.get_level_values(uti.dayindex) == dat].index, ['single']] = 3

    return sample


if __name__ == "__main__":
    test = QA.QA_fetch_stock_day_adv('000977', '2019-01-01', '2020-07-03').data
    radarv2(test)
    uti.PlotBySe(test, zoom=400, numofax=1)



