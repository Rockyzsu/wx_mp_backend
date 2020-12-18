# -*- coding: UTF-8 -*-
"""
@author:xda
@file:model_process.py
@time:2020/12/15
"""
import hashlib
from django.utils import timezone as datetime # 使用django的timezone
from api.models import UserSimple,UserCompleted
from api.config import get_config

CONFIG = get_config()
token = CONFIG['token']

def check(signature, timestamp, nonce):
    list_ = [token, timestamp, nonce]
    list_.sort()
    list_str = ''.join(list_)
    sha1 = hashlib.sha1(list_str.encode('utf8'))
    hashcode = sha1.hexdigest()
    if hashcode == signature:
        return True
    else:
        return False


def addUser(userid):
    try:
        user = UserSimple.objects.get(userid=userid)

    except Exception as e:
        print(e)
        user = UserSimple(userid=userid,
                          access_count=0,
                          canceled=False,
                          follow_time=datetime.now(),
                          last_update_time=datetime.now(),
                          is_sponer=False
                          )

        user.save()

    else:

        user.canceled = False
        user.last_update_time=datetime.now()
        user.save()

def accessIncrement(userid):
    user = UserSimple.objects.get(userid=userid)
    user.access_count=user.access_count+1
    print(user)
    user.save()
    return user.access_count,user.is_sponer

def cancelUser(userid):
    try:
        user = UserSimple.objects.get(userid=userid)

    except:
        pass

    else:
        user.canceled = True
        user.last_update_time=datetime.now()
        user.save()