# -*- coding: utf-8 -*-

from collective.zamqp.interfaces import IMessageArrivedEvent
from five import grok
from imio.dataexchange.core import Response
from imio.wsresponse.core import IResponse
from imio.wsresponse.core import Request
from imio.wsresponse.core import ResponsePublisher
from plone import api

import cPickle


class ResponseConsumer(Request):
    grok.name('ws.request.pm.config')
    queuename = 'PM.CONFIG.{0}'


@grok.subscribe(IResponse, IMessageArrivedEvent)
def consume_requests(message, event):
    content = cPickle.loads(message.body)
    publisher = ResponsePublisher()
    publisher.setup_queue(content.uid, content.uid)

    response = Response(
        content.uid,
        config={
            'meeting': get_meetings(),
            'users': get_users(),
            'services': get_services(),
        }
    )
    publisher.add_message(response)
    publisher.start()

    message.ack()


def get_meetings():
    pm_config = api.portal.get_tool(name='portal_plonemeeting')
    return {id: obj.title for id, obj in pm_config.items()
            if obj.portal_type == 'MeetingConfig'}


def get_users():
    return [u.id for u in api.user.get_users()]


def get_services():
    pm_config = api.portal.get_tool(name='portal_plonemeeting')
    return {id: obj.title for id, obj in pm_config.items()
            if obj.portal_type == 'MeetingGroup'}
