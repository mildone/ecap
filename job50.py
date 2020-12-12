import datetime
import re
import smtplib
from email.mime.text import MIMEText
import QUANTAXIS as QA
try:
    assert QA.__version__>='1.1.0'
except AssertionError:
    print('pip install QUANTAXIS >= 1.1.0 请升级QUANTAXIS后再运行此示例')
    import QUANTAXIS as QA 
import pandas as pd
import numpy as np
read_dictionary = np.load('/home/mildone/Project/quanaly/liutong.npy',allow_pickle=True).item()

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


def TrendDetect(sample,short=5,mid=10,long=15):
    sample['short'] = pd.Series.ewm(sample.close, span=short, min_periods=short - 1, adjust=True).mean()
    sample['mid'] = pd.Series.ewm(sample.close, span=mid, min_periods=mid - 1, adjust=True).mean()
    sample['long'] = pd.Series.ewm(sample.close, span=long, min_periods=long - 1, adjust=True).mean()
    sample['CS'] = (sample.close - sample.short) * 100 / sample.short
    sample['SM'] = (sample.short - sample.mid) * 100 / sample.mid
    sample['ML'] = (sample.mid - sample.long) * 100 / sample.long
    return sample


def weektrend(sample):
    #print(sample)
    from functools import reduce
    sample['EMA12']= pd.Series.ewm(sample.close, span=12, min_periods=12 - 1, adjust=True).mean()
    sample['EMA26']= pd.Series.ewm(sample.close, span=26, min_periods=26 - 1, adjust=True).mean()
    sample['EMA13']=pd.Series.ewm(sample.close,span=13,min_periods=13-1,adjust=True).mean()
    sample['MACDQ']= sample['EMA12']-sample['EMA26']
    sample['MACDSIG']=pd.Series.ewm(sample.MACDQ, span=9, min_periods=9 - 1, adjust=True).mean()
    sample['MACDBlock']=sample['MACDQ']-sample['MACDSIG']

    pp_array = [float(close) for close in sample.MACDBlock]
    temp_array = [(price1, price2) for price1, price2 in zip(pp_array[:-1], pp_array[1:])]
    change = list(map(lambda pp: reduce(lambda a, b: round((b - a) / a, 3) if a!=0 else 0, pp), temp_array))
    change.insert(0, 0)
    sample['change'] = change
    '''
    kdj = QA.QA_indicator_KDJ(sample)
    sample['K'] = kdj.KDJ_K
    sample['D'] = kdj.KDJ_D
    sample['J'] = kdj.KDJ_J
    '''

    return sample


def triNetV2detect(codes, start='2019-01-01', freq='15min', short=5, long=10):
    # get today's date in %Y-%m-%d
    cur = datetime.datetime.now()
    mon = str(cur.month)
    day = str(cur.day)
    if (re.match('[0-9]{1}', mon) and len(mon) == 1):
        mon = '0' + mon
    if (re.match('[0-9]{1}', day) and len(day) == 1):
        day = '0' + day

    et = str(cur.year) + '-' + mon + '-' + day

    #wstart = '2018-01-01'
    buyres = ['buy ']
    sellres = ['sell ']
    # now let's get today data from net, those are DataStructure
    daydata = QA.QA_fetch_stock_day_adv(codes, start, et)
    # also min data for analysis
    mindata = QA.QA_fetch_stock_min_adv(codes, start, et, frequence=freq)

    for code in codes:
        print('deal with {}'.format(code))
        sample = daydata.select_code(
            code).data  # this is only the data till today, then contact with daydata ms.select_code('000977').data

        try:
            td = QA.QAFetch.QATdx.QA_fetch_get_stock_day(code,et,et)
            print(td)
        except:
            print('None and try again')
            td = QA.QAFetch.QATdx.QA_fetch_get_stock_day(code,et,et,if_fq='bfq')
        td.set_index(['date','code'],inplace=True)
        td.drop(['date_stamp'], axis=1, inplace=True)
        td.rename(columns={'vol': 'volume'}, inplace=True)
        sample = pd.concat([td, sample], axis=0,sort=True)
        sample.sort_index(inplace=True,level='date')

        # now deal with week status
        # wend = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
        # temp = QA.QA_fetch_stock_day_adv(code, wstart, wend).data
        wd = wds(sample)
        wd = weektrend(wd)
        direction = wd.change.to_list()[-1]  # now we got week trend

        # deal with 15 min status
        # start = sample.index.get_level_values(dayindex)[0].strftime(dayformate)
        # end = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
        md = mindata.select_code(code).data

        m15 = QA.QA_fetch_get_stock_min('tdx', code, et, et, level=freq)
        # convert online data to adv data(basically multi_index setting, drop unused column and contact 2 dataframe as 1)
        # this is network call
        m15.set_index(['datetime', 'code'], inplace=True)
        m15.drop(['date', 'date_stamp', 'time_stamp'], axis=1, inplace=True)

        m15.rename(columns={'vol': 'volume'}, inplace=True)
        ms = pd.concat([m15, md], axis=0,sort=True)
        ms.sort_index(inplace=True, level='datetime')

        ms['short'] = QA.EMA(ms.close, short)
        ms['long'] = QA.EMA(ms.close, long)
        CROSS_5 = QA.CROSS(ms.short, ms.long)
        CROSS_15 = QA.CROSS(ms.long, ms.short)

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
        if (direction > 0 and sig == 1):
            buyres.append(code)
        elif (direction < 0 and sig == 3):
            sellres.append(code)
    return buyres, sellres

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

    #wstart = '2018-01-01'
    if(type=='index'):
        buyres = ['buyetf ']
        sellres = ['selletf ']
    else:
        buyres = ['buystock ']
        sellres = ['sellstock ']
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
            print(td)
        except:
            print('None and try again')
            if(type=='index'):
                td = QA.QAFetch.QATdx.QA_fetch_get_index_day(code, et, et, if_fq='bfq')
            else:
                td = QA.QAFetch.QATdx.QA_fetch_get_stock_day(code,et,et,if_fq='bfq')
        td.set_index(['date','code'],inplace=True)
        td.drop(['date_stamp'], axis=1, inplace=True)
        td.rename(columns={'vol': 'volume'}, inplace=True)
        sample = pd.concat([td, sample], axis=0,sort=True)
        sample.sort_index(inplace=True,level='date')

        # now deal with week status
        # wend = sample.index.get_level_values(dayindex)[-1].strftime(dayformate)
        # temp = QA.QA_fetch_stock_day_adv(code, wstart, wend).data
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

        ms['short'] = QA.EMA(ms.close, short)
        ms['long'] = QA.EMA(ms.close, long)
        CROSS_5 = QA.CROSS(ms.short, ms.long)
        CROSS_15 = QA.CROSS(ms.long, ms.short)

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
        if (direction > 0 and trendv >0 and sig == 1):
            buyres.append(code)
        elif (direction < 0 and sig == 3):
            sellres.append(code)
    return buyres, sellres

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



    
if __name__ == "__main__":
    import warnings
    warnings.filterwarnings('ignore')
    cl = ['000977', '600745', '002889', '600340', '000895', '600019', '600028',
          '601857', '600585', '002415', '002475', '600031', '600276', '600009', '601318',
          '000333', '600031', '002384', '002241']
    etf = ['515880','515050']
    print('>'*100)
    buy,sell = TrendWeekMin(cl)
    eb,es = TrendWeekMin(etf,type='index')




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
    buy.extend(sell)
    buy.extend(eb)
    buy.extend(es)

    #if(len(buy)>4):
        #print(' '.join(buy))

    # codelist1.extend(codelist4)
    #message = list(set(buy))


    print("sending mail")
    if(len(buy)>4 ):
        sendmail(' '.join(buy))



