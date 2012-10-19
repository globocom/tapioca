#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.ioloop
from tornado.httpserver import HTTPServer

from tapioca import TornadoRESTful, ResourceHandler

from tests.support import ResourceWithDocumentation


if __name__ == '__main__':
    main_loop = tornado.ioloop.IOLoop.instance()

    api = TornadoRESTful(
            version='', base_url='http://127.0.0.1:8000', discovery=True)
    api.add_resource('comments', ResourceWithDocumentation)
    application = tornado.web.Application(api.get_url_mapping())

    server = HTTPServer(application)
    server.bind(8000, '127.0.0.1')
    server.start(1)
    main_loop.start()
