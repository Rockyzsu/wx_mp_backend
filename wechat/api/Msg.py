# -*- coding: UTF-8 -*-
"""
@author:xda
@file:Msg.py
@time:2020/12/15
"""
import re

from api import receive
from api import reply
from api.model_process import accessIncrement
from api.config import get_config
from abc import abstractmethod, ABCMeta
from datahub import cb_info
from datahub.cb_info import CBInfo

CONFIG = get_config()
token = CONFIG['token']
MAX_COUNT = CONFIG['access_max']
IGNORE_RESPONSE = CONFIG['ignore']
LIMIT_RESPONSE = CONFIG['limit_response']


class MsgBase:

    def __init__(self, msg):
        self.msg = msg
        self.recMsg = self.parse(self.msg)

    def parse(self, msg):
        return receive.parse_xml(msg)

    @property
    def FromUserName(self):
        return self.recMsg.FromUserName

    @property
    def ToUserName(self):
        return self.recMsg.ToUserName

    @property
    def MsgType(self):
        return self.recMsg.MsgType

    @property
    def Content(self):
        return self.recMsg.Content

    @property
    def MsgId(self):
        return self.recMsg.MsgId

    @property
    def CreateTime(self):
        return self.recMsg.CreateTime


class BaseProcess(metaclass=ABCMeta):

    @abstractmethod
    def response(self):
        pass


def bonds(args):
    result = cb_info.filter_bond(args)
    return result


cb_instance = CBInfo()


def double_low(content):
    nums = re.search('双低\s*(\d+)', content).group(1)
    return cb_instance.double_low(nums)


PATTERN_DICT = {
    '^(11|12)\d{4}': bonds,  # 转债
    '双低\s*(\d+)': double_low,
}


class TextProcess(BaseProcess):
    def __init__(self, content):
        self.content = content

    def pattern(self, content):
        for k, fun in PATTERN_DICT.items():
            match = re.findall(k, content)
            if match:
                result = fun(content)
                return result

    def response(self):
        result = self.pattern(self.content)
        return result


class EventProcess(BaseProcess):
    def __init__(self, msg):
        pass

    def response(self):
        #
        # elif isinstance(recMsg, receive.Msg) and recMsg.MsgType == 'event':
        #     if recMsg.event == 'subscribe':
        #         content = CONFIG['reply']['subscribe']
        #         replyMsg = reply.TextMsg(toUser, fromUser, content)
        #         resp = replyMsg.send()
        #         addUser(toUser)
        #
        #     elif recMsg.event == 'unsubscribe':
        #         content = CONFIG['reply']['unsubscribe']
        #         replyMsg = reply.TextMsg(toUser, fromUser, content)
        #         resp = replyMsg.send()
        #         cancelUser(toUser)
        #
        # else:
        #     resp = 'success'
        pass


class ErrorProcess(BaseProcess):
    '''
    错误回复处理
    '''

    def __init__(self, msg):
        self.msg = msg

    def response(self):
        return IGNORE_RESPONSE


class LimitProcess(BaseProcess):
    '''
    错误回复处理
    '''

    def __init__(self, msg):
        self.msg = msg

    def response(self):
        return LIMIT_RESPONSE


class MsgProcess(MsgBase):

    def __init__(self, msg):
        super(MsgProcess, self).__init__(msg)
        self.processor = None

    def process(self):
        if not isinstance(self.recMsg, receive.Msg):
            self.processor = ErrorProcess(None)

        if self.MsgType == 'text':
            count, is_sponser = accessIncrement(self.MsgId)
            if count > MAX_COUNT:
                self.processor = LimitProcess(None)
            else:
                self.processor = TextProcess(self.Content)

        elif self.MsgType == 'event':
            self.processor = EventProcess()

        return self.processor

    def response(self):
        # 回复内容构造
        result = self.process().response()
        resp = reply.TextMsg(self.ToUserName, self.FromUserName, result)
        return resp.send()
