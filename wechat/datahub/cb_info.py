# -*- coding: UTF-8 -*-
"""
@author:xda
@file:cb_info.py
@time:2020/12/14
"""
# 实时可转债
import datetime
import re
import time
import requests
import pandas as pd
from common.BaseService import HistorySet, BaseService
from configure.settings import DBSelector

NEXT_TIME = 60
max_time = 3

session = requests.Session()

headers = {
    'User-Agent': 'User-Agent:Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest'
}

post_data = {
    'btype': 'C',
    'listed': 'Y',
    'rp': '50',
    'is_search': 'Y'}


def convert_percent(x):
    try:
        ret = float(x) * 100
    except:
        ret = None
    return ret


def remove_percent(x):
    try:
        ret = x.replace(r'%', '')
        ret = float(ret)
    except Exception as e:
        ret = None

    return ret


def convert_float(x):
    try:
        ret_float = float(x)
    except:
        ret_float = None
    return ret_float


def remove_name(x):
    try:
        x = x.replace('转债', '')
    except:
        pass
    return x


def map_rate(x):
    map_dict = {
        'A+': 1,
        'AA-': 1.2,
        'AA': 1.4,
        'AA+': 1.6,
        'AAA': 1.8
    }
    x = x.replace(' ', '')
    return map_dict.get(x, 1)


def convert(df, nums=10):
    df['grade'] = df['评级'].map(lambda x: map_rate(x))
    df['可转债综合价格'] = df['可转债价格'] + df['溢价率'] * df['grade']
    df = df.sort_values(by='可转债综合价格')
    df['剩余规模'] = df['剩余规模'].map(lambda x: round(float(x), 2))
    df = df[df['强赎日期'].isnull()]  # 去除强赎
    df = df[['可转债名称', '可转债价格', '溢价率', '剩余规模']].head(nums)
    df = df.reset_index(drop=True)
    df['可转债名称'] = df['可转债名称'].map(lambda x: x.replace('转债', ''))
    return df


def jsl_fetch():
    timestamp = int(time.time() * 1000)
    url = 'https://www.jisilu.cn/data/cbnew/cb_list/?___jsl=LST___t={}'.format(timestamp)

    retry = 0

    while retry < max_time:

        try:
            r = session.post(
                url=url,
                headers=headers,
                data=post_data,
                timeout=3)

        except Exception as e:
            print(e)
            retry += 1
        else:
            break

    if retry == max_time:
        return None

    if not r:
        return None

    ret = r.json()
    bond_list = ret.get('rows', {})
    cell_list = []
    for item in bond_list:
        cell_list.append(pd.Series(item.get('cell')))
    df = pd.DataFrame(cell_list)
    # print(df)

    df['premium_rt'] = df['premium_rt'].map(lambda x: float(x.replace('%', '')))
    df['price'] = df['price'].astype('float64')
    df['convert_price'] = df['convert_price'].astype('float64')
    df['premium_rt'] = df['premium_rt'].astype('float64')
    df['redeem_price'] = df['redeem_price'].astype('float64')

    df['put_convert_price'] = df['put_convert_price'].map(convert_float)
    df['sprice'] = df['sprice'].map(convert_float)
    df['ration'] = df['ration'].map(convert_percent)
    df['volume'] = df['volume'].map(convert_float)
    df['convert_amt_ratio'] = df['convert_amt_ratio'].map(remove_percent)
    df['ration_rt'] = df['ration_rt'].map(convert_float)
    df['increase_rt'] = df['increase_rt'].map(remove_percent)
    df['sincrease_rt'] = df['sincrease_rt'].map(remove_percent)
    # df['bond_nm'] = df['bond_nm'].map(remove_name)

    return df


filter_columns = ['bond_id', 'bond_nm', 'increase_rt', 'premium_rt', 'sincrease_rt']
rename_dict = {'bond_id': '代码', 'bond_nm': '名称', 'increase_rt': '涨幅', 'premium_rt': '溢价率', 'sincrease_rt': '正股涨幅'}


def formater(df):
    columns = df.columns
    tplt = "{0:^5}\t{1:^5}\t{2:^5}\t{3:^5}\n"
    content = tplt.format(columns[0],columns[1],columns[2],columns[3])

    for idx,row in df.iterrows():
        content+=tplt.format(row['可转债名称'],row['可转债价格'],row['溢价率'],row['剩余规模'])
    return content

last_time = datetime.datetime.now()


# 时间到了
def timesup():
    global last_time
    now = datetime.datetime.now()

    if (now - last_time) > datetime.timedelta(seconds=60) and 8 < now.hour < 14:
        print('需要更新')
        return True
    else:
        print('不需要更新')
        return False


history = {}


def filter_bond(args):
    global last_time
    if timesup() or len(history) == 0:
        # 抓取，更新
        df = jsl_fetch()
        if re.match('\d{6}', args):
            df = df[filter_columns]
            df.rename(columns=rename_dict, inplace=True)

            for idx, row in df.iterrows():
                code = row['代码']
                name = row['名称']
                percent = row['涨幅']
                yjl = row['溢价率']
                zg_percent = row['正股涨幅']

                history[code] = f'代码：{code}\n名称:{name}\n涨幅:{percent}'

        last_time = datetime.datetime.now() + datetime.timedelta(seconds=NEXT_TIME)

    print('返回缓存数据')
    return history[args]


class CBInfo(BaseService):

    def __init__(self):
        super(CBInfo, self).__init__()
        self.db = DBSelector()
        self.conn = self.db.get_mysql_conn('db_stock', 'qq')

    def double_low(self, nums):
        df = jsl_fetch()
        rename_columns = {'bond_id': '可转债代码', 'bond_nm': '可转债名称', 'price': '可转债价格', 'stock_nm': '正股名称',
                          'stock_cd': '正股代码',
                          'sprice': '正股现价',
                          'sincrease_rt': '正股涨跌幅',
                          'convert_price': '最新转股价', 'premium_rt': '溢价率', 'increase_rt': '可转债涨幅',
                          'put_convert_price': '回售触发价', 'convert_dt': '转股起始日',
                          'short_maturity_dt': '到期时间', 'volume': '成交额(万元)',
                          'redeem_price': '强赎价格', 'year_left': '剩余时间',
                          'next_put_dt': '回售起始日', 'rating_cd': '评级',
                          'adjust_tip': '下修提示',
                          'adj_cnt': '下调次数',
                          'convert_amt_ratio': '转债剩余占总市值比',
                          'curr_iss_amt': '剩余规模', 'orig_iss_amt': '发行规模',
                          'ration_rt': '股东配售率',
                          'redeem_flag': '发出强赎公告',
                          'redeem_dt': '强赎日期',
                          }

        df = df.rename(columns=rename_columns)
        df = convert(df, nums)
        print(str(df))
        return df

if __name__ == '__main__':
    # args = '123074'
    # while 1:
    #     print(filter_bond(args))
    #     time.sleep(10)
    app = CBInfo()
    df = app.double_low(2)
    content = formater(df)
    print(content)
