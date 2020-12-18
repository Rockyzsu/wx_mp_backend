# -*-coding=utf-8-*-
# 常用的配置信息
import pymongo
import datetime
import logging
import random
import smtplib
import time
from sqlalchemy import create_engine
import os
import json
import pymysql
import rsa
from email.mime.text import MIMEText
from email.header import Header
from email.utils import parseaddr, formataddr


def get_config_data(config_file='config.json'):
    json_file = os.path.join(os.path.dirname(__file__), config_file)
    with open(json_file, 'r') as f:
        _config = json.load(f)
        return _config

config = get_config_data()

def config_dict(*args):
    result = config
    for arg in args:
        try:
            result = result[arg]
        except:
            print('找不到对应的key')
            return None

    return result

class DBSelector(object):
    '''
    数据库选择类
    '''

    def __init__(self):
        self.json_data = config

    def config(self, db_type='mysql', local='qq'):
        db_dict = self.json_data[db_type][local]
        user = db_dict['user']
        password = db_dict['password']
        host = db_dict['host']
        port = db_dict['port']
        return (user, password, host, port)

    def get_engine(self, db, type_='qq'):

        user, password, host, port = self.config(db_type='mysql', local=type_)
        try:
            engine = create_engine(
                'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8'.format(user, password, host, port, db))
        except Exception as e:
            print(e)
            return None
        return engine

    def get_mysql_conn(self, db, type_='qq'):
        user, password, host, port = self.config(db_type='mysql', local=type_)
        try:
            conn = pymysql.connect(host=host, port=port, user=user, password=password, db=db, charset='utf8')
        except Exception as e:
            print(e)
            return None
        else:
            return conn

    def mongo(self, type='qq'):
        user, password, host, port = self.config('mongo', type)
        connect_uri = f'mongodb://{user}:{password}@{host}:{port}'
        client = pymongo.MongoClient(connect_uri)
        return client

class WechatSend:
    '''
    废弃
    '''

    def __init__(self, name):
        # name为微信要发送的人的微信名称
        self.name = name
        itchat.auto_login(hotReload=True)
        account = itchat.get_friends(self.name)
        self.toName = None
        for i in account:
            if i[u'PYQuanPin'] == self.name:
                self.toName = i['UserName']
        if not self.toName:
            print('please input the right person name')

    def send_price(self, name, real_price, real_percent, types):
        content = name + ' ' + str(real_price) + ' ' + \
                  str(real_percent) + ' percent ' + types
        itchat.send(content, toUserName=self.toName)

    def send_ceiling(self, name, vol):
        current = datetime.datetime.now().strftime('%Y %m %d %H:%M %S')
        content = '{} Warning {} : ceiling volume is {}'.format(current, name, vol)
        itchat.send(content, toUserName=self.toName)

    def send_content(self, content):
        itchat.send(content, toUserName=self.toName)


def llogger(filename):
    # pre_fix = os.path.splitext(filename)[0]
    # 创建一个logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 创建一个handler，用于写入日志文件
    fh = logging.FileHandler(filename)

    # 再创建一个handler，用于输出到控制台
    ch = logging.StreamHandler()

    # # 定义handler的输出格式
    formatter = logging.Formatter(
        '[%(asctime)s][Filename: %(filename)s][line: %(lineno)d][%(levelname)s] :: %(message)s')

    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # 给logger添加handler
    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


def market_status():
    '''
    收盘
    '''
    now = datetime.datetime.now()
    end = datetime.datetime(now.year, now.month, now.day, 15, 2, 5)
    return True if now < end else False


def rsa_encrypt():
    (pubkey, privkey) = rsa.newkeys(1024)
    print('pubkey >>>> {}'.format(pubkey))
    print('privkey >>>> {}'.format(privkey))

    with open('pub.pem', 'w') as f:
        f.write(pubkey.save_pkcs1().decode())

    with open('datasender.pem', 'w') as f:
        f.write(privkey.save_pkcs1().decode())

    message = ''
    print("message encode {}".format(message.encode()))
    crypto = rsa.encrypt(message.encode(), pubkey)  # 加密数据为bytes

    print('密文:\n{}'.format(crypto))

    with open('encrypt.bin', 'wb') as f:
        f.write(crypto)
    # 解密
    e_message = rsa.decrypt(crypto, privkey)  # 解密数据也是为bytes
    print("解密后\n{}".format(e_message.decode()))


def rsa_decrypt():
    with open('encrypt.bin', 'rb') as f:
        content = f.read()

    file = 'priva.pem'
    with open(file, 'r') as f:
        privkey = rsa.PrivateKey.load_pkcs1(f.read().encode())

    e_message = rsa.decrypt(content, privkey)  # 解密数据也是为bytes
    print("解密后\n{}".format(e_message.decode()))


def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))


def send_from_aliyun(title, content, TO_MAIL_=config['mail']['qq']['user'], types='plain'):
    username = config['aliyun']['EMAIL_USER_ALI']  # 阿里云
    password = config['aliyun']['LOGIN_EMAIL_ALYI_PASSWORD']  # 阿里云
    stmp = smtplib.SMTP()

    msg = MIMEText(content, types, 'utf-8')
    subject = title
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = _format_addr('{} <{}>'.format('数据推送', username))
    msg['To'] = TO_MAIL_

    try:
        stmp.connect('smtp.qiye.aliyun.com', 25)
        stmp.login(username, password)
        stmp.sendmail(username, TO_MAIL_, msg.as_string())
    except Exception as e:
        time.sleep(10 + random.randint(1, 5))
        stmp = smtplib.SMTP()
        stmp.connect('smtp.qiye.aliyun.com', 25)
        stmp.login(username, password)
        stmp.sendmail(username, TO_MAIL_, msg.as_string())
    else:
        print('发送完毕')


def send_sms(content):
    from twilio.rest import Client

    client = Client(config.twilio_account_sid, config.twilio_auth_token)
    try:
        message = client.messages.create(
            body=content,
            from_=config.FROM_MOBILE,
            to=config.TO_MOBILE
        )
    except Exception as e:
        print(e)



if __name__ == '__main__':
    # msg=WechatSend(u'wei')
    # msg.send_price('hsdq',12,12,'sell')
    # print(FROM_MAIL)
    # mylogger('test.log','just for test')
    # trading_time()
    # sendmail('content--------', 'subject------')
    # send_aliyun('你是这样的的', '二维翁', 'weigesysu@qq.com')
    # is_holiday()
    pass
