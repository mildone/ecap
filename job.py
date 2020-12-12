import datetime
import smtplib
from email.mime.text import MIMEText
import QUANTAXIS as QA
try:
    assert QA.__version__>='1.1.0'
except AssertionError:
    print('pip install QUANTAXIS >= 1.1.0 请升级QUANTAXIS后再运行此示例')
    import QUANTAXIS as QA 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt 
import abupy
from abupy import ABuRegUtil
from concurrent.futures import ThreadPoolExecutor
from functools import reduce
import warnings
read_dictionary = np.load('/home/mildone/Project/quanaly/liutong.npy',allow_pickle=True).item()
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtk
import mpl_finance as mpf
def MACACalculate(sample):
    sample['EMA12']=QA.EMA(sample.close,12)
    sample['EMA26']=QA.EMA(sample.close,26)
    sample['MACDQ']=sample['EMA12']-sample['EMA26']
    sample['MACDSIG']=QA.EMA(sample['MACDQ'],9)
    sample['MACDBlock']=sample['MACDQ']-sample['MACDSIG']
    return sample
def candlestruct(sample):
    import matplotlib.dates as mpd
    quotes=[]
    pydate_array = sample.index.get_level_values('date').to_pydatetime()
    date_only_array = np.vectorize(lambda s: s.strftime('%Y-%m-%d'))(pydate_array )
#date_only_series = pd.Series(date_only_array)
    N=sample.index.get_level_values('date').shape[0]
    ind = np.arange(N)
    for i in range(len(sample)):
        li=[]
    #datet=datetime.datetime.strptime(sample.index.get_level_values('date'),'%Y%m%d')   #字符串日期转换成日期格式
        #datef=mpd.date2num(datetime.datetime.strptime(date_only_array[i],'%Y-%m-%d')) 
        datef=ind[i]#日期转换成float days
        open_p=sample.open[i]
        close_p=sample.close[i]
        high_p=sample.high[i]
        low_p=sample.low[i]
        li=[datef,open_p,close_p,high_p,low_p]
        t=tuple(li)
        quotes.append(t)
    return quotes

def MACDPLOT(sample):
    quotes = candlestruct(sample)
    N=sample.index.get_level_values('date').shape[0]
    ind = np.arange(N)
    def format_date(x, pos=None):
        thisind = np.clip(int(x+0.5), 0, N-1)
        return sample.index.get_level_values('date')[thisind].strftime('%Y-%m-%d')
    fig = plt.figure()
    #fig = plt.gcf()
    fig.set_size_inches(20.5,12.5)
    #plt.xlabel('Trading Day')
    #plt.ylabel('MACD EMA')
    ax2 = fig.add_subplot(3,1,1)
    ax2.set_title("candlestick")
  
    
    #fig,ax=plt.subplots()
    #mpf.candlestick_ochl(ax2,quotes,width=0.2,colorup='r',colordown='g',alpha=1.0)
    #ax2.xaxis_date()
    #plt.setp(plt.gca().get_xticklabels(),rotation=30)
    #ax2.plot(ind,sample.close,'b-',marker='*')
    mpf.candlestick_ochl(ax2,quotes,width=0.6,colorup='r',colordown='g',alpha=1.0)
    ax2.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    ax2.grid(True)
    #t.legend()
    fig.autofmt_xdate()
    
    ax3 = fig.add_subplot(3,1,3,sharex=ax2)
    ax3.set_title("volume")
    #ax1 = ax2.twinx()   #not working like it's 
    ax3.bar(ind,sample.volume)
    ax3.grid(True)
    ax3.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    fig.autofmt_xdate()
    
    #ax1 = ax2.twinx()   #not working like it's 
    ax1 = fig.add_subplot(3,1,2,sharex=ax2)
    ax1.set_title("macd")
    ax1.grid(True)
    ax1.plot(ind,sample.MACDQ,'r-',marker='*')
    ax1.plot(ind,sample.MACDSIG,'o-')
    ax1.bar(ind,sample.MACDBlock)
    ax1.xaxis.set_major_formatter(mtk.FuncFormatter(format_date))
    #ax2.set_yticks(np.linspace(ax2.get_yticks()[0], ax2.get_yticks()[-1], len(ax1.get_yticks())))
    fig.autofmt_xdate()
    plt.legend()
    code = sample.index.get_level_values('code')[0]
    
    plt.savefig('/home/mildone/monitor/'+'Trend'+code+'.png')
    #plt.show()  comment out for hanging with 1 pic 
    plt.close()
def amountAnalyse(buydata):
    """
    @buydata as pdDataFrame
    e.g. buydata = QA.QA_fetch_get_stock_transaction_realtime('pytdx','600797') get current day's transaction
    e.g. data1=QA.QAFetch.QATdx.QA_fetch_get_stock_transaction('600797','2019-01-01','2019-04-11') get transaction among period of time

    """
    sellone = buydata[buydata['buyorsell']==1]
    sellone['amount'] = sellone['price']*sellone['vol']
    sellone.sort_values("vol",inplace=True,ascending=False)

    buyone = buydata[buydata['buyorsell']==0]
    buyone['amount'] = buyone['price']*buyone['vol']
    buyone.sort_values("vol",inplace=True,ascending=False)
    #print("Top buyer vol")
    #buyone[buyone['vol']>10]
    print("Top Seller vol")
    sellone.head(100)
def getStocklist():
    """
    get all stock as list
    usage as:
    QA.QA_util_log_info('GET STOCK LIST')
    stocks=getStocklist()
    """
    data=QA.QAFetch.QATdx.QA_fetch_get_stock_list('stock')
    stock = data['code'].index
    stocklist = []
    for code in stock:
        stocklist.append(code[0])
    return stocklist
def loadLocalData(stocks,start_date ='2018-03-15',end_date = '2019-09-07'):
    """
    data() as pdDataFrame
    stocks could be list of all the stock or some. if you pass single one e.g. 000001 it will get one only
    to get dedicated stock, using below method, and notice stockp() will be dataFrame
    stockp = data.select_code(stock)


    """
    QA.QA_util_log_info('load data from local DB')
    data=QA.QA_fetch_stock_day_adv(stocks,start_date,end_date)
    return data
def loadFromCopy(file):
    """
    loaddata from file copy
    """
    return pd.DataFrame(pd.read_csv(file))

def calAngle(df):
    """
    trend angle based on provided dataframe
    """
    return ABuRegUtil.calc_regress_deg(df.close.values,show=False)

def getData(df, code):
    """
    split data per code from all market data
    """
    return df[df.code==code].reset_index(drop=True)

def trendBreak(pdDataFrame):
    """
    trendBreak based on provdied market data
    """

    from abupy import pd_rolling_max
    from abupy import pd_expanding_max
    # 当天收盘价格超过N1天内最高价格作为买入信号
    N1 = 20
    # 当天收盘价格超过N2天内最低价格作为卖出信号
    N2 = 15
    kl_pd = pdDataFrame
    # 通过rolling_max方法计算最近N1个交易日的最高价
    # kl_pd['n1_high'] = pd.rolling_max(kl_pd['high'], window=N1)
    kl_pd['n1_high'] = pd_rolling_max(kl_pd['high'], window=N1)
    # 表7-4所示

    # expanding_max
    # expan_max = pd.expanding_max(kl_pd['close'])
    expan_max = pd_expanding_max(kl_pd['close'])
    # fillna使用序列对应的expan_max
    kl_pd['n1_high'].fillna(value=expan_max, inplace=True)
    # 表7-5所示
    #print('kl_pd[0:5]:\n', kl_pd[0:5])

    from abupy import pd_rolling_min, pd_expanding_min
    # 通过rolling_min方法计算最近N2个交易日的最低价格
    # rolling_min与rolling_max类似
    # kl_pd['n2_low'] = pd.rolling_min(kl_pd['low'], window=N2)
    kl_pd['n2_low'] = pd_rolling_min(kl_pd['low'], window=N2)
    # expanding_min与expanding_max类似
    # expan_min = pd.expanding_min(kl_pd['close'])
    expan_min = pd_expanding_min(kl_pd['close'])
    # fillna使用序列对应的eexpan_min
    kl_pd['n2_low'].fillna(value=expan_min, inplace=True)

    # 当天收盘价格超过N天内的最高价或最低价, 超过最高价格作为买入信号买入股票持有
    buy_index = kl_pd[kl_pd['close'] > kl_pd['n1_high'].shift(1)].index
    kl_pd.loc[buy_index, 'signal'] = 1

    # 当天收盘价格超过N天内的最高价或最低价, 超过最低价格作为卖出信号
    sell_index = kl_pd[kl_pd['close'] < kl_pd['n2_low'].shift(1)].index
    kl_pd.loc[sell_index, 'signal'] = 0

    #kl_pd.signal.value_counts().plot(kind='pie', figsize=(5, 5))
    #plt.show()

    """
        将信号操作序列移动一个单位，代表第二天再将操作信号执行，转换得到持股状态
        这里不shift(1)也可以，代表信号产生当天执行，但是由于收盘价格是在收盘后
        才确定的，计算突破使用了收盘价格，所以使用shift(1)更接近真实情况
    """
    kl_pd['keep'] = kl_pd['signal'].shift(1)
    kl_pd['keep'].fillna(method='ffill', inplace=True)
    return kl_pd

    # 计算基准收益
    #kl_pd['benchmark_profit'] = np.log(
        #kl_pd['close'] / kl_pd['close'].shift(1))

    # 计算使用趋势突破策略的收益
    #kl_pd['trend_profit'] = kl_pd['keep'] * kl_pd['benchmark_profit']

    # 可视化收益的情况对比
    #kl_pd[['benchmark_profit', 'trend_profit']].cumsum().plot(grid=True,
        #                                                      figsize=(
        #                                                          14, 7))
    #plt.show()
    #kl_pd[['n2_low','n1_high','close']].plot(grid=True,figsize=(14,7))
    #kl_pd.close.plot(grid=True,figsize=(14.7))
    #plt.show()

def execute(stocks,data):
    select=[]
    for stock in stocks:
        try:
            QA.QA_util_log_info('dealting with {}'.format(stock))
            stockp = data.select_code(stock)
            if (trend(stockp[-10:])>0 and trend(stockp[-10:])<10):
                select.append(stock)
        except:
            print('wrong with {}'.format(stock))

    return sorted(select)[-2:]


def executeParallel(stocks,data):
    """
    scan all data and filter out ones doing trendbreak
    """
    alldep=[]
    with ThreadPoolExecutor(5) as executor:
        for stock , dep in zip(stocks,executor.map(trendSingle,alldata)):
            alldep.append((stock,dep))
    print('all done')
    return alldep

def init_change(df):
    #change first (d[i].close-d[i-1].close)/d[i-1].close
    pp_array = [float(close) for close in df.close]
    temp_array = [(price1, price2) for price1,price2 in zip(pp_array[:-1],pp_array[1:])]
    change = list(map(lambda pp: reduce(lambda a, b: round((b - a) / a, 3), pp), temp_array))
    change.insert(0,0)
    df['change'] = change
    #amplitude (d[i].high-d[i].low)/d[i-1].close)
    amp_arry=[float(amp) for amp in (df.high-df.low)]
    amp_temp =  [(price1, price2) for price1,price2 in zip(amp_arry[:-1],pp_array[1:])]
    amplitude = list(map(lambda pp: reduce(lambda a, b: round(a/b, 3), pp), amp_temp))
    amplitude.insert(0,0)
    df['amplitude'] = amplitude
    #sratio = QA.QA_fetch_get_stock_info(df.index.get_level_values('code')[0]).liutongguben[0]
    sratio = read_dictionary[df.index.get_level_values('code')[0]]
    df['SR']=df['volume']/sratio*100


def init_trend(df,period=7):
    """
    period can be set based on situation.
    detect the angle change form negative to positive
    """
    trend=[]
    ratio = []
    for i in range(0,df.shape[0]):
        #print(i)
        if(i<period):
            trend.append(calAngle(df.iloc[:period]))
            ratio.append(df.iloc[i].amount*period/sum(df.iloc[0:period].amount))
        else:
            trend.append(calAngle(df.iloc[i-period+1:i+1]))
            ratio.append(df.iloc[i].amount*5/sum(df.iloc[i-5:i].amount))
    df['trend']=trend
    df['amountRatio'] = ratio
"""

def trendSingle(df):

    buydate=[]
    for i in range(0,df.shape[0]):
        if(df.iloc[i].amountRatio>1 and df.iloc[i].trend>1 and df.iloc[i].amplitude<0.07 and df.iloc[i].change<0.03
          and df.iloc[i].change>0.01):
            buydate.append((i,df.iloc[i].date))
    return buydate
"""

def trendSingle(df,period=7):
    """
    @paramater dataframe
    return True or False
    Justification:
    1. latest 20 days angle >0
    2. change (0.1~0.3)
    3.

    """
    #df['trend']=0
    #df['amountRatio']=0
    #trend=0
    #amountRatio=0
    keep = 5
    init_change(df)
    init_trend(df)
    single=[0,0]
    #temp =[]
    for i in range(1,df.shape[0]):
        """
        if(i<period):
            #trend.append(calAngle(df.iloc[:period]))
            trend=calAngle(df.iloc[:period])
            #print(trend)
            #ratio.append(df.iloc[i].amount*period/sum(df.iloc[0:period].amount))
            amountRatio=df.iloc[i].amount*period/sum(df.iloc[0:period].amount)
        else:
            #trend.append(calAngle(df.iloc[i-period+1:i+1]))
            trend=calAngle(df.iloc[i-period+1:i+1])
            #print(trend)
            #print(calAngle(df.iloc[i-period+1:i+1]))
            #ratio.append(df.iloc[i].amount*5/sum(df.iloc[i-5:i].amount))
            #print(df.iloc[i].amount*5/sum(df.iloc[i-5:i].amount))
            amountRatio=df.iloc[i].amount*5/sum(df.iloc[i-5:i].amount)
        """
        if(1.5>df.iloc[i].amountRatio>1 and df.iloc[i].trend>1 and df.iloc[i].amplitude>0.05
           and 0.01<df.iloc[i].change<0.03 and df.iloc[i].SR <0.05 ):
            single.append(1)
        else:
            single.append(0)
    #single.append(0)
    #single.extend(temp[:-1])
    #print("done here")
    #single.insert(0,0)
    single.pop()
    #print(single)
    size = len(single)
    #for simple purpose, set last (Keep) as 0,simple take 3 days as holding max

    #print("checking operation single")
    for i in range(0, size - 5):
        if single[i] == 1:
            bar = df.iloc[i].open * 1.2
            j = i
            if (df.iloc[j+1].change>0 and df.iloc[j+1].close<bar):
                single[j + 1] = 0
            else:
                single[j + 1] = 3
                continue
            if ((df.iloc[j + 2].change > 0 and df.iloc[j+2].close<bar) or
                (df.iloc[j + 2].change < 0 and df.iloc[j + 2].close > df.iloc[i].open) ):
                single[j + 2] = 0

            else:
                single[j + 2] = 3
                continue
            if ((df.iloc[j + 3].change > 0 and df.iloc[j+3].close<bar)
                or (df.iloc[j + 3].change < 0 and df.iloc[j + 3].close > df.iloc[i].open)):
                single[j + 3] = 0
            else:
                single[j + 3] = 3
                continue
            if ((df.iloc[j + 4].change > 0 and df.iloc[j+4].close<bar)
                or (df.iloc[j + 4].change < 0 and df.iloc[j + 4].close > df.iloc[i].open)):
                single[j + 4] = 0
            else:
                single[j + 4] = 3
                continue
            single[j + 5] = 3

    single[-5:]=[0,0,0,0,0]

    df['single']=single
    #df['single']=df['keep'].shift(1)
    #df['single'].fillna(method='ffill',inplace=True)
    print(df.index.levels[1])
    return df
def ana(df):
    #df = loadLocalData(code,'2014-01-01','2019-09-30')
    #df = df.to_qfq()
    init_change(df)
    init_trend(df)
    if(1.5> df.iloc[-1].amountRatio>1 and df.iloc[-1].trend>1 and df.iloc[-1].amplitude>0.05
       and 0.01<df.iloc[-1].change<0.03 and df.iloc[-1].SR <0.05):
        return True
    else:
        return False


def detect(df):
    init_change(df)
    init_trend(df)
    single=[0,0]
    #temp =[]
    for i in range(1,df.shape[0]):
        """
        if(i<period):
            #trend.append(calAngle(df.iloc[:period]))
            trend=calAngle(df.iloc[:period])
            #print(trend)
            #ratio.append(df.iloc[i].amount*period/sum(df.iloc[0:period].amount))
            amountRatio=df.iloc[i].amount*period/sum(df.iloc[0:period].amount)
        else:
            #trend.append(calAngle(df.iloc[i-period+1:i+1]))
            trend=calAngle(df.iloc[i-period+1:i+1])
            #print(trend)
            #print(calAngle(df.iloc[i-period+1:i+1]))
            #ratio.append(df.iloc[i].amount*5/sum(df.iloc[i-5:i].amount))
            #print(df.iloc[i].amount*5/sum(df.iloc[i-5:i].amount))
            amountRatio=df.iloc[i].amount*5/sum(df.iloc[i-5:i].amount)
        """
        if(1.5>df.iloc[i].amountRatio>1 and df.iloc[i].trend>1 and df.iloc[i].amplitude>0.05
           and 0.01<df.iloc[i].change<0.03 and df.iloc[i].SR <0.05 ):
            single.append(1)
        else:
            single.append(0)
    #single.append(0)
    #single.extend(temp[:-1])
    #print("done here")
    #single.insert(0,0)
    single.pop()
    if(single[-1] == 1):
        return True
    else:
        return False

def sendmail(content):
    msg_from = 'skiping1982@163.com'  # 发送方邮箱
    passwd = 'jyn821014'  # 填入发送方邮箱的授权码(填入自己的授权码，相当于邮箱密码)
    msg_to = ['ynjiang@foxmail.com','skiping1982@163.com']  # 收件人邮箱

    subject = "[INFO]需要跟进项目进度 "+datetime.datetime.now().strftime('%Y-%m-%d')  # 主题
    content = content
# 生成一个MIMEText对象（还有一些其它参数）
# _text_:邮件内容
    msg = MIMEText(content)
# 放入邮件主题
    msg['Subject'] = subject
# 也可以这样传参
# msg['Subject'] = Header(subject, 'utf-8')
# 放入发件人
    msg['From'] = msg_from
# 放入收件人
    msg['To'] = 'ynjiang@foxmail.com'
# msg['To'] = '发给你的邮件啊'
    try:
    # 通过ssl方式发送，服务器地址，端口
        s = smtplib.SMTP_SSL("smtp.163.com", 465)
    # 登录到邮箱
        s.login(msg_from, passwd)
    # 发送邮件：发送方，收件方，要发送的消息
        s.sendmail(msg_from, msg_to, msg.as_string())
        print('success sent')
    except s.SMTPException as e:
        print(e)
    finally:
        s.quit()


def analysis(endtime):
    codelist1 = QA.QA_fetch_stock_block_adv().get_block('华为概念').code[:]
    codelist2 = QA.QA_fetch_stock_block_adv().get_block('5G概念').code[:]
    codelist4 = QA.QA_fetch_stock_block_adv().get_block('国产软件').code[:]
    codelist1.extend(codelist2)
    codelist1.extend(codelist4)
    codelist=list(set(codelist1))
    data = loadLocalData(codelist,'2019-01-01',endtime)
    print('endtime is {}'.format(endtime))
    data=data.to_qfq()
    print('*'*100)
    print('prepare data for back test')
    
    
    select=[]
    for stock in codelist:
        try:
            QA.QA_util_log_info('dealting with {}'.format(stock))
            stockp = data.select_code(stock)
            if (ana(stockp.data)):
                select.append(stock)
        except:
            print()
            print('wrong with {}'.format(stock))
    return select
def generateplot(code):
    import datetime
    cur = datetime.datetime.now()
    endtime = str(cur.year)+'-'+str(cur.month)+'-'+str(cur.day)
    sample = loadLocalData(code,'2019-08-01',endtime)
    sample = sample.to_qfq()
    sampleData = sample.select_code(code)
    MACACalculate(sampleData.data)
    MACDPLOT(sampleData.data)
    
def gitAction(candidate):
    from git import Repo
    r = Repo('/home/mildone/monitor')
    commitfile = [r'/home/mildone/monitor/result.log',r'/home/mildone/monitor/data.csv']
    
    prefix = '/home/mildone/monitor/'
    if(len(candidate)>0):
        for i in range(len(candidate)):          
            generateplot(candidate[i])
            pltfile = prefix+'Trend'+candidate[i]+'.png'
            commitfile.append(pltfile)
    r.index.add(commitfile)
    cur = datetime.datetime.now()
    msg = str(cur.year)+'-'+str(cur.month)+'-'+str(cur.day)+' commit'
    r.index.commit(msg)
    r.remote().push('master')

    
if __name__ == "__main__":
    cur = datetime.datetime.now()
    endtime = str(cur.year)+'-'+str(cur.month)+'-'+str(cur.day)
    #candidate = analysis(endtime)
    candidate=['000021','000034']
    print('>'*100)
    print(candidate)
    with open('/home/mildone/monitor/result.log','w') as f:
        f.write(' '.join(candidate))

    print("commit to Github")
    gitAction(candidate)
    print("sending mail")

    if(len(candidate)>0):
        sendmail(' '.join(candidate))
    


