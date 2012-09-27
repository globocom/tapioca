#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
from tornado.ioloop import IOLoop
from tornado.testing import AsyncHTTPTestCase

from images_api.app import ImagesApplication


class BaseImagesAPITestCase(AsyncHTTPTestCase):
    
    def get_app(self):
        return ImagesApplication()

    def get(self, path, **querystring):
        url = self.get_url(path)
        if querystring:
            url = "%s?%s" % (url, urllib.urlencode(querystring))
        self.http_client.fetch(url, self.stop)
        return self.wait()

    def get_new_ioloop(self):
        return IOLoop.instance()
