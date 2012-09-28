#!/usr/bin/python
# -*- coding: utf-8 -*-

from json import dumps

import tornado.web


class BaseHandler(tornado.web.RequestHandler):

    def _error(self, status, msg=None):
        self.set_status(status)
        self.finish()

    def respond_with(self, data):
        self.set_header('Content-Type', 'application/json')
        data = dumps(data)
        callback_name = self.get_argument('callback', default=None)
        if callback_name:
            data = "%s(%s)" % (callback_name, data)
        self.write(data)
        self.finish()

    @property
    def config(self):
        return self.application.config
