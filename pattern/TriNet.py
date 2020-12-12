import QUANTAXIS as QA
import core.Util as ut
import numpy as np
def triNetv5(sample,short=20, long=60, freq='15min'):


    start = sample.index.get_level_values(ut.dayindex)[0].strftime(ut.dayformate)
    end = sample.index.get_level_values(ut.dayindex)[-1].strftime(ut.dayformate)
    mindata = QA.QA_fetch_stock_min_adv(sample.index.get_level_values('code')[0], start, end, frequence= freq)
    ms = mindata.data
    # print(sample)
    ms['short'] = QA.MA(ms.close, short)
    ms['long'] = QA.MA(ms.close, long)
    CROSS_5 = QA.CROSS(ms.short, ms.long)
    CROSS_15 = QA.CROSS(ms.long, ms.short)

    C15 = np.where(CROSS_15 == 1, 3, 0)
    m = np.where(CROSS_5 == 1, 1, C15)
    # single = m[:-1].tolist()
    # single.insert(0, 0)
    ms['single'] = m.tolist()
    #sig = [0]

    #single = m[:-1].tolist()
    #single.insert(0, 0)
    # sample['single'] = m.tolist()
    #ms['single'] = single

    if(freq=='60min'):
        anchor = -2
    elif(freq=='30min'):
        anchor = -4
    elif(freq=='15min'):
        anchor = -8
    sig = [0]
    for i in range(1, len(sample)):


        #dtime = sample.index.get_level_values(ut.dayindex)[i]
        temp = ms[ms.index.get_level_values(ut.index).strftime(ut.dayformate) == sample.index.get_level_values(ut.dayindex)[i].strftime(ut.dayformate)][:anchor]
        tmp = ms[ms.index.get_level_values(ut.index).strftime(ut.dayformate) == sample.index.get_level_values(ut.dayindex)[i-1].strftime(ut.dayformate)][anchor:]
        sing = temp.single.sum()+tmp.single.sum()
        if(sing==1):
            sig.append(1)
        elif(sing==3):
            sig.append(3)
        else:
            sig.append(0)

    try:
        #sample['single'] = [0]+sig[:-1]
        sample['single']=sig

    except:
        print('error with {}'.format(sample.index.get_level_values('code')[0]))
        sample['single'] = 0
    return sample