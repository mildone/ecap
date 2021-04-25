# -*- coding: utf-8 -*-
from jqdatasdk import get_trade_days, get_index_stocks, get_industry, auth
from jqdatasdk.technical_analysis import *
import pandas as pd
from tqdm import tqdm  # 用于显示进度的库
import matplotlib.pyplot as plt
import matplotlib


auth('15608006621', 'JyNN20120606jyn')  # 账号是申请时所填写的手机号；密码为聚宽官网登录密码，新申请用户默认为手机号后6位
font = {
    'family': 'SimHei',
    'weight': 'bold',
    'size': 12
}
matplotlib.rc("font", **font)
from datetime import datetime
import seaborn as sns

# 指数
index_code = '000906.XSHG'
# 行业分类标准
industry_type = 'sw_l1'

# 宽度日期
market_breadth_days = 30

# 获取每个行业 以及 获取每个行业包含中证800的成分股的个数
zz800 = get_index_stocks('000906.XSHG')

zz800_industry = get_industry(zz800, date=datetime.strftime(datetime.today(), '%Y-%m-%d'))
zz800_industry = pd.DataFrame(zz800_industry).T[[industry_type]]
zz800_industry[industry_type] = zz800_industry[industry_type].apply(lambda x: x['industry_name'])

industries = zz800_industry[industry_type]
industries = list(set(industries))
industries.sort()

# 创建表格  列是日期，行是行业，最后需要转置
market_breadth = pd.DataFrame(index=(['zz800'] + industries))

# 根据交易日来计算宽度
# 最近80天交易日
# 然后倒序[::-1]
# 最后取出80天[:80]
trade_days = get_trade_days(start_date='2015-01-01', end_date=None)[::-1][:market_breadth_days]

for day in tqdm(trade_days):
    # BIAS:(CLOSE-MA(CLOSE,N))/MA(CLOSE,N)*100
    # 负的说明 当前收盘价在MAN日线之下
    BIAS1, BIAS2, BIAS3 = BIAS(zz800, check_date=day, N1=20, N2=60, N3=120)  # 乖离率

    zz800_industry['BIAS20'] = pd.Series(BIAS1)

    day_market_breadth1 = pd.DataFrame()

    # 统计zz800中站在20日线上的有多少占比
    day_market_breadth1.loc['zz800', 'BIAS20'] = round(
        (len(zz800_industry[zz800_industry['BIAS20'] > 0]) / len(zz800_industry)) * 100)

    # 统计每个行业有多少只股票站在20日线上
    day_market_breadth2 = zz800_industry[zz800_industry["BIAS20"] > 0].groupby('sw_l1').count()

    # 将两个拼接成完整的一天市场宽度
    day_market_breadth = pd.concat([day_market_breadth1, day_market_breadth2], axis=0)

    market_breadth[day] = day_market_breadth['BIAS20']

# 将行业名称和中证800每个行业包含的股票个数拼接在一起
x = zz800_industry.groupby(industry_type).groups
industries = ['CSI800']
for k, v in x.items():
    industries.append(k + '(' + str(len(v)) + ')')

market_breadth.index = industries
# 将值为空的填为0
market_breadth.fillna(0, inplace=True)

# 转置
market_breadth = market_breadth.T

# 把每个int64的值换位int32的
for col in market_breadth.columns:
    market_breadth[col] = market_breadth[col].astype('int32')

# 总和列
market_breadth['sum'] = market_breadth[industries[1:]].sum(axis=1)

# 画图
fig = plt.figure(figsize=(45, 50))

grid = plt.GridSpec(market_breadth_days, len(industries) + 1)  # 80x30  其中29列给行业和zz800  1列给sum
# GridSpec: https://blog.csdn.net/weixin_43055882/article/details/86518052
# https://www.jianshu.com/p/445a027c9f8c

cmap = sns.diverging_palette(130, 15, n=10)  # 0-359  红白绿的色带
# diverging_palette：https://blog.csdn.net/flowingfog/article/details/102541748
# https://www.cntofu.com/book/172/docs/60.md
# https://zhuanlan.zhihu.com/p/53467339

# 市场宽度
for i in range(30):
    if (i != 0 and i != 29):
        htmap = fig.add_subplot(grid[:, i])
        htmap.xaxis.set_ticks_position('top')
        # test.columns[1] 交通运输I(40)  40从 -3:-1  有一些可能是个位数 如休闲服务I(5)
        v_max = market_breadth.columns[i]
        # 想法：用字符串的find函数，找到 '(' ')' 的索引号，然后获取 它们之间的数字即可
        beg = v_max.find('(')
        end = v_max.find(')')
        v_max = int(v_max[beg + 1:end])

        sns.heatmap(market_breadth[[market_breadth.columns[i]]], vmin=0, vmax=v_max, annot=True, cmap=cmap, fmt='d',
                    annot_kws={'size': 16}, cbar=False)
        plt.xticks(size=13)
        plt.yticks([])

    if (i == 29):
        htmap = fig.add_subplot(grid[:, -1])
        htmap.xaxis.set_ticks_position('top')
        sns.heatmap(market_breadth[[market_breadth.columns[i]]], vmin=0, vmax=800, annot=True, cmap=cmap, fmt='d',
                    annot_kws={'size': 16}, cbar=False)
        plt.xticks([])
        plt.yticks([])

    if (i == 0):
        htmap = fig.add_subplot(grid[:, i])
        htmap.xaxis.set_ticks_position('top')
        sns.heatmap(market_breadth[[market_breadth.columns[i]]], vmin=0, vmax=100, annot=True, cmap=cmap, fmt='d',
                    annot_kws={'size': 16}, cbar=False)
        plt.xticks(size=15)
        plt.yticks(size=15)

plt.savefig("my_market_width.png", dpi=225)
#plt.show()

# 导出excel文件
#market_breadth.to_excel('market_breadth.xlsx')