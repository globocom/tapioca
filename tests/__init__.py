#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
from os.path import abspath, join, dirname

from tornado.ioloop import IOLoop
from tornado.testing import AsyncHTTPTestCase

from images_api.app import ImagesApplication
from images_api.alpha.infrastructure import EsUrls

from tests.support import es_cleanup


class AsyncHTTPClientMixin:
    
    def get(self, path, **querystring):
        url = self.get_url(path)
        if querystring:
            url = "%s?%s" % (url, urllib.urlencode(querystring))
        return self._fetch(url, 'GET')
    
    def post(self, url, data):
        return self._fetch(url, 'POST', body=data)
    
    def put(self, url, data):
        return self._fetch(url, 'PUT', body=data)
    
    def delete(self, url):
        return self._fetch(url, 'DELETE')
    
    def _fetch(self, url, method, **kwargs):
        self.http_client.fetch(url, self.stop, method=method, **kwargs)
        return self.wait()


class BaseImagesAPITestCase(AsyncHTTPTestCase, AsyncHTTPClientMixin):
    
    def setUp(self):
        super(BaseImagesAPITestCase, self).setUp()
        es_cleanup(EsUrls(self._app.config))
    
    def get_app(self):
        return ImagesApplication(conf_file=abspath(join(dirname(__file__), '..', 'images_api.test.conf')))
    
    def get_new_ioloop(self):
        return IOLoop.instance()
