from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views import View
from api.config import get_config
from api.Msg import MsgProcess
from api.model_process import check

# Create your views here.

CONFIG = get_config()
MAX_COUNT = CONFIG['access_max']


class Services(View):

    def get(self, request):

        signature = request.GET.get('signature')
        echostr = request.GET.get('echostr')
        timestamp = request.GET.get('timestamp')
        nonce = request.GET.get('nonce')
        if signature is None:
            return HttpResponse('404', status=404)

        if check(signature, timestamp, nonce):
            return HttpResponse(echostr)
        else:
            ret = 'success'
            return HttpResponse(ret)

    def post(self, request):
        signature = request.POST.get('signature')
        echostr = request.POST.get('echostr')
        timestamp = request.POST.get('timestamp')
        nonce = request.POST.get('nonce')
        openid = request.POST.get('openid')

        body = request.body
        content = None
        print(body)
        msg = body.decode('utf8')
        msg_prcs = MsgProcess(msg)
        processor = msg_prcs.process()
        resp = processor.response()
        return HttpResponse(resp)


# 异常处理

def page_not_found(request, exception):
    print('IP')
    print(request.META['REMOTE_ADDR'])
    return HttpResponse('404', status=404)
