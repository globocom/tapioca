#!/usr/bin/python
# -*- coding: utf-8 -*-

import tornado.web

from images_api.handlers import BaseHandlerMixin


class BaseHandler(tornado.web.RequestHandler, BaseHandlerMixin):

    @property
    def config(self):
        return self.application.config
