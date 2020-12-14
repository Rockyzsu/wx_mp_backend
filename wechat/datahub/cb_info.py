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
from common.BaseService import HistorySet

session = requests.Session()
headers = {
    'User-Agent': 'User-Agent:Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest'
}
max_time = 3
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
        x=x.replace('转债','')
    except:
        pass
    return x

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

filter_columns=['bond_id','bond_nm','increase_rt','premium_rt','sincrease_rt']
rename_dict ={'bond_id':'代码','bond_nm':'名称','increase_rt':'涨幅','premium_rt':'溢价率','sincrease_rt':'正股涨幅'}

def formater(df,columns):
    pass

last_time = datetime.datetime.now()

# 时间到了
def timesup():
    now = datetime.datetime.now()

    if (now - last_time)>datetime.timedelta(seconds=60):
        print('需要更新')
        return True
    else:
        print('不需要更新')
        return False

history={}

def filter_bond(args):
    if timesup() or len(history)==0:
        # 抓取，更新
        print('下载jsl')
        df = jsl_fetch()
        if re.match('\d{6}',args):
            df=df[filter_columns]
            # df = df[df['bond_id']==args].iloc[0]
            df.rename(columns=rename_dict,inplace=True)
            # print(df.to_html())
            # print(str(df))
            for idx,row in df.iterrows():
                code = row['代码']
                name=row['名称']
                percent=row['涨幅']
                yjl = row['溢价率']
                zg_percent=row['正股涨幅']

                history[code]=f'代码：{code}\n名称:{name}\n涨幅:{percent}'


    print('返回缓存数据')
    return history[args]





if __name__ == '__main__':
    args='123074'
    while 1:
        print(filter_bond(args))
        time.sleep(10)