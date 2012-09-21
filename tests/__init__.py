#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tornado.testing import AsyncHTTPTestCase

from images_api.app import ImagesApplication


class BaseImagesAPITestCase(AsyncHTTPTestCase):
    def get_app(self):
        return ImagesApplication()

    def get(self, path):
        self.http_client.fetch(self.get_url(path), self.stop)
        return self.wait()
