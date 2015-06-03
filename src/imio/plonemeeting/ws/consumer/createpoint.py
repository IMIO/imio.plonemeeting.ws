# -*- coding: utf-8 -*-

from collective.zamqp.interfaces import IMessageArrivedEvent
from five import grok
from imio.dataexchange.core import Response
from imio.wsresponse.core import IValidation
from imio.wsresponse.core import ObjectCreation
from imio.wsresponse.core import Request
from imio.wsresponse.core import ResponsePublisher
from imio.wsresponse.core import Validator
from plone import api
from zope.interface import Interface
from zope.schema import ValidationError

import cPickle

from imio.plonemeeting.ws.consumer.interfaces import IResponseCreatePoint


class ResponseConsumer(Request):
    grok.name('ws.request.pm.createpoint')
    queuename = 'PM.CREATEPOINT.{0}'
    marker = IResponseCreatePoint


@grok.subscribe(IResponseCreatePoint, IMessageArrivedEvent)
def consume_requests(message, event):
    request = cPickle.loads(message.body)

    pm_tool = api.portal.get_tool(name='portal_plonemeeting')
    pm_creation = PMPointCreation(request, pm_tool=pm_tool)
    external_uid, url = pm_creation.create()

    publisher = ResponsePublisher()
    publisher.setup_queue(request.uid, request.uid)
    response = Response(
        request.uid,
        external_uid=external_uid,
        url=url,
    )
    publisher.add_message(response)
    publisher.start()
    message.ack()


class IPMPoint(Interface):
    """Marker interface for plone meeting point"""


class PMPointCreation(ObjectCreation):
    grok.implements(IPMPoint)

    @property
    def meeting_config(self):
        return getattr(self.pm_tool, self.meeting_id)

    @property
    def meeting_id(self):
        return self.parameters.get('meeting_id')

    @property
    def user_id(self):
        return self.parameters.get('user_id')

    @property
    def container(self):
        return self.pm_tool.getPloneMeetingFolder(self.meeting_id,
                                                  self.user_id)

    @property
    def portal_type(self):
        return self.meeting_config.getItemTypeName()


class PMOptionalParametersValidator(Validator):
    grok.name('PM.OptionalParametersValidator')
    grok.provides(IValidation)
    grok.context(IPMPoint)

    def validate(self):
        for field in self.context.optional:
            if self._is_activated_optional_field(field) is False:
                raise ValidationError(
                    "The optional field '%s' is not activated in this "
                    "configuration!" % field)

    def _is_activated_optional_field(self, field):
        return (field in self.optional_fields and
                field in self.activated_optional_fields)

    @property
    def optional_fields(self):
        """Return the list of the optional fields"""
        return self.context.meeting_config.listUsedItemAttributes()

    @property
    def activated_optional_fields(self):
        """Return the list of the activated optional fields"""
        return self.context.meeting_config.getUsedItemAttributes()


class PMMemberValidator(Validator):
    grok.name('PM.MemberValidator')
    grok.provides(IValidation)
    grok.context(IPMPoint)

    def validate(self):
        if self.proposingGroup not in self.user_groups:
            raise ValidationError(
                "'%s' can not create items for the '%s' group!" %
                (self.context.user_id, self.proposingGroup))

    @property
    def proposingGroup(self):
        return self.context.data.get('proposingGroup')

    @property
    def user_groups(self):
        groups = self.context.pm_tool.getGroupsForUser(userId=self.context.user_id,
                                                       suffix="creators")
        return [g.getId() for g in groups]
