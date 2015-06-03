# -*- coding: utf-8 -*-

from imio.wsresponse.core import IResponse


class IResponseCreatePoint(IResponse):
    """Marker interface for request message to create meeting point"""


class IResponseConfig(IResponse):
    """Marker interface for request message to get meeting config"""
