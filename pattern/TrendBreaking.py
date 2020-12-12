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
from abupy import pd_expanding_max




def TrendBreaking(sample,short=20,mid=60,long=120,level='15min'):
    sample['shigh']=pd_rolling_max(sample.close,window=short)
    expanmax = pd_expanding_max(sample.close)
    sample['shigh'].fillna(value=expanmax, inplace=True)






if __name__ == "__main__":
    pass
    #test = QA.QA_fetch_stock_day_adv('000977', '2019-01-01', '2020-07-03').data
    #radarv2(test)
    #uti.PlotBySe(test, zoom=400, numofax=1)



