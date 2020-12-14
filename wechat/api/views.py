from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import hashlib
import json
# import datetime
import time
from django.utils import timezone as datetime
from api.models import UserSimple,UserCompleted
from api import receive
from api import reply
from api.config import get_config
# Create your views here.

CONFIG = get_config()
token = CONFIG['token']
MAX_COUNT = CONFIG['access_max']

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
        print('取消关注')
        # user=user[0]
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
        print('取消关注')
        # user=user[0]
        user.canceled = True
        user.last_update_time=datetime.now()
        user.save()

def Services(request):

    if request.method == 'GET':

        signature = request.GET.get('signature')
        echostr = request.GET.get('echostr')
        timestamp = request.GET.get('timestamp')
        nonce = request.GET.get('nonce')
        if signature is None:
            return HttpResponse('404',status=404)


        if check(signature, timestamp, nonce):
            return HttpResponse(echostr)
        else:
            ret = 'success'
            return HttpResponse(ret)

    else:
        signature = request.POST.get('signature')
        echostr = request.POST.get('echostr')
        timestamp = request.POST.get('timestamp')
        nonce = request.POST.get('nonce')
        openid = request.POST.get('openid')
        print(openid)
        print(request.POST)
        body = request.body
        content = None
        print(body)
        recMsg = receive.parse_xml(body.decode('utf8'))
        toUser = recMsg.FromUserName
        fromUser = recMsg.ToUserName

        if isinstance(recMsg, receive.Msg) and recMsg.MsgType == 'text':
            count,is_sponser=accessIncrement(toUser)
            if count<MAX_COUNT or is_sponser:
                content = f"访问{count}次"
            else:
                content='访问次数达到上限'

            replyMsg = reply.TextMsg(toUser, fromUser, content)
            resp = replyMsg.send()

        elif isinstance(recMsg, receive.Msg) and recMsg.MsgType == 'event':
            if recMsg.event == 'subscribe':
                content = CONFIG['reply']['subscribe']
                replyMsg = reply.TextMsg(toUser, fromUser, content)
                resp = replyMsg.send()
                addUser(toUser)

            elif recMsg.event == 'unsubscribe':
                content = CONFIG['reply']['unsubscribe']
                replyMsg = reply.TextMsg(toUser, fromUser, content)
                resp = replyMsg.send()
                cancelUser(toUser)

        else:
            resp = 'success'

        print(content)

        return HttpResponse(resp)


def page_not_found(request, exception):
    print('IP')
    print(request.META['REMOTE_ADDR'])
    # return JsonResponse({'error':404})
    return HttpResponse('404',status=404)
