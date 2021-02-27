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


read_dictionary = np.load('/Users/jiangyongnan/git/ecap/liutong.npy', allow_pickle=True).item()
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtk
import mpl_finance as mpf
import quant.Util as uti
import quant.MACD as mmacd
import quant.weekTrend as wt
import quant.kdj as kdj


def zoom(code):
    wt.weekDFANA(code)
    kdj.kdjANA(code)

    mmacd.macdANA(code)
    mmacd.minMACDANA(code)


if __name__ == "__main__":
    zoom('600189')