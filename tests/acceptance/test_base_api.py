#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from json import loads, dumps

import tornado.web
from tornado.testing import AsyncHTTPTestCase

from images_api.handlers import ApiResourceHandler

from tests.support import AsyncHTTPClientMixin


class TestHandler(ApiResourceHandler):

    models = [dict(id=str(i), text='X' * i) for i in range(10)]

    def _find(self, cid):
        ms = [x for x in self.models if x['id'] == cid]
        return ms[0] if ms else None

    def create_model(self, model):
        model['id'] = str(max([int(x['id']) for x in self.models]) + 1)
        self.models.append(model)
        logging.debug('created %s' % str(model))
        return model

    def get_collection(self):
        return self.models

    def get_model(self, cid):
        return self._find(cid)

    def update_model(self, model, cid):
        logging.debug('updating %s %s' % (str(cid), str(model)))
        self.models[self.models.index(self._find(cid))] = model

    def delete_model(self, cid):
        logging.debug('deleting')
        self.models.remove(self._find(cid))


application = tornado.web.Application([
        (r"/api", TestHandler),
        (r"/api/(.+)", TestHandler),
    ]
)


class TestBaseApiHandler(AsyncHTTPTestCase, AsyncHTTPClientMixin):

    def get_app(self):
        return application

    def test_get_request_to_list_all_resource_instances(self):
        response = self.get('/api')
        assert response.code == 200, 'the status code should be 200 but it was %d' % response.code
        resources = loads(response.body)
        number_of_items = len(resources)
        assert number_of_items == 10, 'should return 10 resources but returned %d' % number_of_items
        for item in resources:
            assert 'id' in item, 'should have the key \'id\' in the resource instance'
            assert 'text' in item, 'should have the \'text\' in the resource instance'

    def test_get_a_specific_resource_using_get_request(self):
        response = self.get('/api/3')
        assert response.code == 200, 'the status code should be 200 but it was %d' % response.code
        resource = loads(response.body)
        assert 'id' in resource, 'should have the key \'id\' in the resource instance %s' % str(resource)
        assert 'text' in resource, 'should have the \'text\' in the resource instance %s' % str(resource)

    def test_post_to_create_a_new_resource(self):
        a_new_item = {
            'text': 'this is my new item'
        }
        response = self.post(self.get_url('/api'), dumps(a_new_item))
        assert response.code == 201, 'the status code should be 201 but it was %d' % response.code
        resource = loads(response.body)
        assert 'id' in resource, 'should have the key \'id\' in the resource instance %s' % str(resource)
        assert 'text' in resource, 'should have the \'text\' in the resource instance %s' % str(resource)
        assert resource['text'] == a_new_item['text']
