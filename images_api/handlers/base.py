#!/usr/bin/python
# -*- coding: utf-8 -*-

import tornado.web

from images_api.handlers import ExtractArgumentsMixin


class BaseHandler(tornado.web.RequestHandler, ExtractArgumentsMixin):

    @property
    def config(self):
        return self.application.config
