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
from abupy import pd_rolling_max
from abupy import pd_rolling_min
from abupy import pd_expanding_max
def TrendFinder(day,short=20,mid=60,long=120):
    #20, 30 , 60   5.3/10
    # 20, 60, 120 5.0/10
    #10, 20, 60   6.7/10
    #10, 30, 60   5.7/10

    day['long'] = QA.EMA(day.close, long)
    day['mid'] = QA.EMA(day.close, mid)
    day['short'] = QA.EMA(day.close, short)
    day['BIAS'] = (day.close - day.long) * 100 / day.long
    day['BMA'] = QA.EMA(day.BIAS, short)
    day['CS'] = (day.close - day.short) * 100 / day.short
    day['SM'] = (day.short - day.mid) * 100 / day.mid
    day['ML'] = (day.mid - day.long) * 100 / day.long
    day['threshold'] = pd_rolling_max(day.BIAS,window=2*long)
    day['nthreshold'] = pd_rolling_min(day.BIAS,window=2*long)
    sig = []
    buy = 0
    sell = 0
    for i in range(day.shape[0]):
        if(day.BIAS[i]>=0):
            flag = day.BIAS[i]/day.threshold[i]
        else:
            flag = day.BIAS[i]/day.nthreshold[i]

        if(day.CS[i]>0 and day.SM[i]>0  and buy ==0):
            sig.append(1)
            buy = 1
            sell = 0
        elif(day.CS[i]<0 and day.SM[i]<0  and sell==1):
            sig.append(3)
            sell = 1
            buy = 0
        elif(day.CS[i]<0 and day.BIAS[i] < day.BMA[i] and sell == 0):
            
            sig.append(5)
            buy = 0
            sell = 1

        else:
            sig.append(0)
    day['single'] = sig
   # day['single'] = [0]+sig[:-1]


    return day

def TurnNotice(sample):
    '''
    alerting trend changing based on data
    '''
    return None

def TrendFinM(day,short=20,mid=60,long=120):
    #20, 30 , 60   8/10
    #10, 20, 60   6.7/10
    #10, 30, 60   7.2/10
    day['long'] = QA.MA(day.close, long)
    day['mid'] = QA.MA(day.close, mid)
    day['short'] = QA.MA(day.close, short)
    day['BIAS'] = (day.close - day.long) * 100 / day.long
    day['CS'] = (day.close - day.short) * 100 / day.short
    day['SM'] = (day.short - day.mid) * 100 / day.mid
    day['ML'] = (day.mid - day.long) * 100 / day.long
    sig = []
    buy = 0
    sell = 0
    for i in range(day.shape[0]):
        if(day.CS[i]>0 and day.SM[i]>0 and day.ML[i]>0 and buy ==0):
            sig.append(1)
            buy = 1
            sell = 0
        elif(day.CS[i]<0  and sell==0):
            sig.append(3)
            sell = 1
            buy = 0
        else:
            sig.append(0)
    day['single'] = sig
   # day['single'] = [0]+sig[:-1]


    return day


if __name__ == "__main__":
    test = QA.QA_fetch_stock_day_adv('000977','2019-01-01','2020-07-03').data
    TrendFinder(test)
    uti.PlotBySe(test,zoom = 400,numofax=1)



