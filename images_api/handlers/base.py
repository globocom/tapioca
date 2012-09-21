#!/usr/bin/python
# -*- coding: utf-8 -*-

from json import dumps

import tornado.web


class BaseHandler(tornado.web.RequestHandler):
    def _error(self, status, msg=None):
        self.set_status(status)
        self.finish()

    def respond_with(self, data):
        self.add_header('Content-Type', 'application/json')
        self.write(dumps(data))
        self.finish()


