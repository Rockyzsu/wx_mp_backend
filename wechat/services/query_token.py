import requests
import datetime
import sqlite3

class Token:
    def __init__(self):
        dbName = 'accessToken'
        self.conn = sqlite3.connect(dbName)
        self.table = 'tb_accessToken'
        self.create_table()

    def create_table(self):
        create_table_sql = f'create table if not exists {self.table} (id int,token varchar(1024),expire_time datetime)'
        cursor = self.conn.cursor()
        cursor.execute(create_table_sql)
        self.conn.commit()


    def update(self,token,expire):
        query = f'select count(*) from {self.table}'
        cursor=  self.conn.cursor()
        cursor.execute(query)
        count = cursor.fetchone()[0]
        if count==0:
            sql = f'insert into {self.table} (id,token,expire_time) values (?,?,?)'
            data=(0,token,expire)
        else:
            sql = f'update {self.table} set token=?,expire_time=? where id=0'
            data=(token,expire)

        cursor.execute(sql,data)
        self.conn.commit()
        print('更新token')
        self.conn.close()

    @property
    def access_token(self):
        appid = 'wxe6e807527c609af1'
        secret = 'bc59aefb6b3454ef2c6f0afef38fb8b0'
        token_url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}'
        try:
            resp = requests.get(token_url)
        except Exception as e:
            print(e)
            return None,None


        resp_json = resp.json()
        access_token = resp_json.get('access_token')
        expires = resp_json.get('expires_in')
        expires_time = datetime.datetime.now()+datetime.timedelta(seconds=expires)
        return access_token,expires_time

    def token_update(self):
        token,expire = self.access_token
        self.update(token,expire)
        return token,expire

    def get(self):
        cursor = self.conn.cursor()
        cursor.execute(f'select token,expire_time from {self.table} where id=0')
        ret = cursor.fetchone()

        if ret is None:
            # 更新
            token,_=self.token_update()
        else:
            token,expired_time=ret
            expired_time=datetime.datetime.strptime(expired_time,'%Y-%m-%d %H:%M:%S.%f')
            if expired_time<datetime.datetime.now():
                token, _ = self.token_update()

        return token


class GetInfo:
    def __init__(self,url,use_token=True):
        token = Token()
        self.__token =token.get()
        if use_token:
            url=url.format(self.__token)
        self.url=url

    def get(self):
        resp = requests.get(self.url)
        return resp.json()

    def post(self,data):
        resp = requests.post(url=self.url,data=data)
        return resp.json()
    
def get_ip():
    # 微信服务器ip
    url='https://api.weixin.qq.com/cgi-bin/get_api_domain_ip?access_token={}'
    app = GetInfo(url)
    resp = app.get()
    print(resp)
    return resp

def get_autoreply():
    # 自动回复内容
    url='https://api.weixin.qq.com/cgi-bin/get_current_autoreply_info?access_token={}'
    app = GetInfo(url)
    resp = app.get()
    print(resp)
    return resp


def get_user_list():
    # 用户列表
    url='https://api.weixin.qq.com/cgi-bin/user/get?access_token={}&next_openid='
    app = GetInfo(url)
    resp = app.get()
    print(resp)
    return resp

def get_user_increment():
    # 用户列表
    url='https://api.weixin.qq.com/datacube/getusercumulate?access_token={}'
    app = GetInfo(url)
    resp = app.get()
    print(resp)
    return resp



def main():
    # get_ip()
    # get_autoreply()
    # get_user_list()
    get_user_increment()

if __name__=='__main__':
    main()