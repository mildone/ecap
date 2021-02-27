import datetime
import re
import smtplib
from email.mime.text import MIMEText
import QUANTAXIS as QA
from retrying import retry
try:
    assert QA.__version__>='1.1.0'
except AssertionError:
    print('pip install QUANTAXIS >= 1.1.0 请升级QUANTAXIS后再运行此示例')
    import QUANTAXIS as QA 
import pandas as pd
import numpy as np
#read_dictionary = np.load('/Users/jiangyongnan/git/ecap/liutong.npy',allow_pickle=True).item()

def wds(df):
    df['date'] = pd.to_datetime(df.index.get_level_values('date'))
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
def divergence( day,short = 20, mid = 60, long = 120):
    # change first (d[i].close-d[i-1].close)/d[i-1].close
    """
    supported Indicators
    @change, close(today)-preclose/preclose, up when greater than 0, down when less than 0
    @ MA and EMA of short, mid, long which are configurable
    @ Indicator for monitoring divergence of market invest change by time
    @ CS is (close- shortEMA)/shortEMA
    @ SM is (shortEMA - midEMA)/midEMA
    @ ML is (midEMA-longEMA)/longEMA
    @ BIAS is (close - longEMA)/longEMA
    General Rule of writing indicators:
    * ignore those which can be directly got from QUANTAXIS e.g. MACD, KDJ, .etc.
    * only the one which is used for pattern monitoring and build on top of QUANTAXIS ones
    """

    day['long'] = QA.EMA(day.close, long)
    day['lo'] = QA.MA(day.close, long)
    day['mi'] = QA.MA(day.close, mid)
    day['sh'] = QA.MA(day.close, short)
    day['mid'] = QA.EMA(day.close, mid)
    day['short'] = QA.EMA(day.close, short)
    day['BIAS'] = (day.close - day.long) * 100 / day.long
    day['BMA'] = QA.EMA(day.BIAS,short)
    day['CS'] = (day.close - day.short) * 100 / day.short
    day['CM'] = (day.close - day.mid) * 100 / day.mid
    day['SM'] = (day.short - day.mid) * 100 / day.mid
    day['ML'] = (day.mid - day.long) * 100 / day.long
    day['TS'] = (day.close > day.short).astype(int) + (day.close > day.sh).astype(int) + (day.close > day.mid).astype(int)\
                + (day.close > day.mi).astype(int) + (day.sh > day.mi).astype(int)
    day['RTS'] = (day.short > day.close).astype(int) + (day.sh > day.close).astype(int) + (day.mid > day.close).astype(int)\
                 + (day.mi > day.close).astype(int) + (day.mi > day.sh).astype(int)

    return day

def TrendDetect(sample,short=5,mid=10,long=15):
    sample['short'] = pd.Series.ewm(sample.close, span=short, min_periods=short - 1, adjust=True).mean()
    sample['mid'] = pd.Series.ewm(sample.close, span=mid, min_periods=mid - 1, adjust=True).mean()
    sample['long'] = pd.Series.ewm(sample.close, span=long, min_periods=long - 1, adjust=True).mean()
    sample['CS'] = (sample.close - sample.short) * 100 / sample.short
    sample['SM'] = (sample.short - sample.mid) * 100 / sample.mid
    sample['ML'] = (sample.mid - sample.long) * 100 / sample.long
    return sample

@retry
def TrendWeekMin(codes, start='2019-01-01', freq='15min', short=20, long=60,type='stock'):
    # get today's date in %Y-%m-%d
    cur = datetime.datetime.now()
    mon = str(cur.month)
    day = str(cur.day)
    if (re.match('[0-9]{1}', mon) and len(mon) == 1):
        mon = '0' + mon
    if (re.match('[0-9]{1}', day) and len(day) == 1):
        day = '0' + day

    et = str(cur.year) + '-' + mon + '-' + day
    #et = '2021-02-25'

    #wstart = '2018-01-01'
    if(type=='index'):
        buyres = ['buyetf ']
    else:
        buyres = ['buystock ']
    sellres = []
    # now let's get today data from net, those are DataStructure
    if(type=='index'):
        daydata = QA.QA_fetch_index_day_adv(codes, start, et)
        # also min data for analysis
        mindata = QA.QA_fetch_index_min_adv(codes, start, et, frequence=freq)
    else:
        daydata = QA.QA_fetch_stock_day_adv(codes, start, et)
    # also min data for analysis
        mindata = QA.QA_fetch_stock_min_adv(codes, start, et, frequence=freq)

    for code in codes:
        print('deal with {}'.format(code))
        sample = daydata.select_code(
            code).data  # this is only the data till today, then contact with daydata ms.select_code('000977').data

        try:
            if(type=='index'):
                td = QA.QAFetch.QATdx.QA_fetch_get_index_day(code, et, et)
            else:
                td = QA.QAFetch.QATdx.QA_fetch_get_stock_day(code,et,et)
            #print(td)
        except:
            print('None and try again')
            if(type=='index'):
                td = QA.QAFetch.QATdx.QA_fetch_get_index_day(code, et, et, if_fq='bfq')
            else:
                td = QA.QAFetch.QATdx.QA_fetch_get_stock_day(code,et,et,if_fq='bfq')
        if(td.empty):
            print('no new data')
        else:
            print(td)
            td.set_index(['date','code'],inplace=True)
            td.drop(['date_stamp'], axis=1, inplace=True)
            td.rename(columns={'vol': 'volume'}, inplace=True)
            sample = pd.concat([td, sample], axis=0,sort=True)
            sample.sort_index(inplace=True,level='date')

        # now deal with week status
        # wend = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
        # temp = QA.QA_fetch_stock_day_adv(code, wstart, wend).data
        sample['atr'] = QA.QA_indicator_ATR(sample, 20).ATR
        wd = wds(sample)
        wd = TrendDetect(wd)
        direction = wd.CS.to_list()[-1]  # now we got week trend
        trendv = wd.SM.to_list()[-1]

        # deal with 15 min status
        # start = sample.index.get_level_values(dayindex)[0].strftime(dayformate)
        # end = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
        md = mindata.select_code(code).data
        if(type=='index'):
            m15 = QA.QA_fetch_get_index_min('tdx', code, et, et, level=freq)
        else:
            m15 = QA.QA_fetch_get_stock_min('tdx', code, et, et, level=freq)
        # convert online data to adv data(basically multi_index setting, drop unused column and contact 2 dataframe as 1)
        # this is network call
        m15.set_index(['datetime', 'code'], inplace=True)
        m15.drop(['date', 'date_stamp', 'time_stamp'], axis=1, inplace=True)

        m15.rename(columns={'vol': 'volume'}, inplace=True)
        ms = pd.concat([m15, md], axis=0,sort=True)
        ms.sort_index(inplace=True, level='datetime')
        divergence(ms)
        #ms['short'] = QA.EMA(ms.close, short)
        #ms['long'] = QA.EMA(ms.close, long)
        ms['short6'] = QA.EMA(ms.close, short)
        ms['long6'] = QA.EMA(ms.close, long)
        CROSS_5 = QA.CROSS(ms.short6, ms.long6)
        CROSS_15 = QA.CROSS(ms.long6, ms.short6)

        #CROSS_5 = QA.CROSS(ms.short, ms.long)
        #CROSS_15 = QA.CROSS(ms.long, ms.short)

        C15 = np.where(CROSS_15 == 1, 3, 0)
        m = np.where(CROSS_5 == 1, 1, C15)
        # single = m[:-1].tolist()
        # single.insert(0, 0)
        ms['single'] = m.tolist()
        sig = [0]
        if (freq == '60min'):
            anchor = -2
        elif (freq == '30min'):
            anchor = -4
        elif (freq == '15min'):
            anchor = -8

        sig = ms[-16:].single.sum()
        rts = ms.RTS[-1]
        if (direction > 0 and trendv >0 and sig == 1):
            print('{} with trend {}'.format(direction,trendv))
            print('got one')
            buyres.append(code+'-atr-'+str(round(sample.atr[-1],2)))
        elif (direction < 0 and rts > 3):
            sellres.append(code)
    sell = list(set(sellres))
    if (type == 'index'):
        sell.insert(0, 'selletf ')
    else:
        sell.insert(0, 'sellstock ')
    return buyres, sell

def sendmail(content):
    msg_from = 'skiping1982@163.com'  # 发送方邮箱
    passwd = 'jyn821014'  # 填入发送方邮箱的授权码(填入自己的授权码，相当于邮箱密码)
    msg_to = ['ynjiang@foxmail.com','skiping1982@163.com','yuanwenbing@sunpower.com.cn']  # 收件人邮箱
    #msg_to = ['skiping1982@163.com']  # 收件人邮箱
    subject = "[INFO_BACK]需要跟进项目进度 "+datetime.datetime.now().strftime('%Y-%m-%d')  # 主题
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



    
if __name__ == "__main__":
    import warnings
    warnings.filterwarnings('ignore')
    cl = ['000977', '600745',
          # '002889',
          '600340', '000895', '600019',
          '600585', '002415', '002475', '600031', '600276', '600009', '601318', '002230', '600875',
          '000333', '600031', '002384', '002241', '600703', '000776', '600897', '600085',
          # '000651','300054','300046','002352',
          # '600438',
          '000651',
          '601318',
          '600036',
          '300059',
          '600887'
          ]
    etf = ['515880','515050']
    print('>'*100)
    buy,sell = TrendWeekMin(cl)
    print(buy)
    eb,es = TrendWeekMin(etf,type='index')
    print()




    if(len(buy)==1):
        buy[0] = 'buy nostock'
    if(len(sell)==1):
        sell[0]='sell nostock'
    if(len(eb)==1):
        eb[0] ='buy noetf'
    if(len(es)==1):
        es[0] = 'sell noetf'
    #buy.insert(0,'buy ')
    #sell.insert(0,'sell ')
    buy.append('\n')
    buy.extend(sell)
    buy.append('\n')
    buy.extend(eb)
    buy.append('\n')
    buy.extend(es)
    buy.append('\n')

    #if(len(buy)>4):
        #print(' '.join(buy))

    # codelist1.extend(codelist4)
    #message = list(set(buy))


    print("sending mail")
    if(len(buy)>8 ):
        sendmail(' '.join(buy))
    else:
        sendmail('another peaceful day')
    


