#!/usr/bin/python
# -*- coding: utf-8 -*-

import tornado.web


class BaseHandler(tornado.web.RequestHandler):

    @property
    def config(self):
        return self.application.config
