#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from json import loads, dumps

import tornado.web
from tornado.testing import AsyncHTTPTestCase

from images_api.handlers import ApiResourceHandler, ResourceDoesNotExist

from tests.support import AsyncHTTPClientMixin


FAKE_DATABASE = None

class TestHandler(ApiResourceHandler):

    def _find(self, cid):
        ms = [x for x in FAKE_DATABASE if x['id'] == cid]
        if ms:
            return ms[0]
        else:
            raise ResourceDoesNotExist()

    def create_model(self, model):
        model['id'] = str(max([int(x['id']) for x in FAKE_DATABASE]) + 1)
        FAKE_DATABASE.append(model)
        logging.debug('created %s' % str(model))
        return model

    def get_collection(self):
        return FAKE_DATABASE

    def get_model(self, cid):
        return self._find(cid)

    def update_model(self, model, cid):
        logging.debug('updating %s %s' % (str(cid), str(model)))
        FAKE_DATABASE[FAKE_DATABASE.index(self._find(cid))] = model

    def delete_model(self, cid):
        logging.debug('deleting')
        item = self._find(cid)
        FAKE_DATABASE.remove(self._find(cid))


class TestBaseApiHandler(AsyncHTTPTestCase, AsyncHTTPClientMixin):

    def get_app(self):
        application = tornado.web.Application([
                (r"/api", TestHandler),
                (r"/api/(.+)", TestHandler),
            ]
        )
        return application

    def setUp(self, *args, **kw):
        super(TestBaseApiHandler, self).setUp(*args, **kw)
        global FAKE_DATABASE
        FAKE_DATABASE = [dict(id=str(i), text='X' * i) for i in range(10)]

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

    def test_get_a_resource_that_does_not_exist(self):
        response = self.get('/api/30')
        assert response.code == 404, 'the status code should be 404 but it was %d' % response.code

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

    def test_put_to_update_an_existing_resource(self):
        response = self.get('/api/1')
        assert response.code == 200, 'the status code should be 200 but it was %d' % response.code
        resource = loads(response.body)
        resource['comment'] = 'wow!'
        response = self.put(self.get_url('/api/1'), dumps(resource))
        assert response.code == 200, 'the status code should be 200 but it was %d' % response.code
        response = self.get('/api/1')
        resource = loads(response.body)
        assert 'comment' in resource
        assert resource['comment'] == 'wow!'

    def test_try_to_update_a_resource_that_does_not_exist(self):
        response = self.put(self.get_url('/api/30'), dumps(dict(text='not exist')))
        assert response.code == 404, 'the status code should be 404 but it was %d' % response.code

    def test_delete_method_to_destroy_a_resource(self):
        response = self.delete(self.get_url('/api/1'))
        assert response.code == 200, 'the status code should be 200 but it was %d' % response.code
        response = self.delete(self.get_url('/api/1'))
        assert response.code == 404, 'the status code should be 404 but it was %d' % response.code


class TestApiResourceHandlerWithoutImplementation(AsyncHTTPTestCase, AsyncHTTPClientMixin):

    def get_app(self):
        application = tornado.web.Application([
                (r"/api", ApiResourceHandler),
                (r"/api/(.+)", ApiResourceHandler),
            ]
        )
        return application

    def test_try_to_create_a_resource(self):
        response = self.post(self.get_url('/api'), dumps(dict(text='nice')))
        assert response.code == 404, 'the status code should be 404 but it was %d' % response.code

    def test_try_to_list_resources(self):
        response = self.get('/api')
        assert response.code == 404, 'the status code should be 404 but it was %d' % response.code

    def test_try_to_update_a_resource(self):
        response = self.put(self.get_url('/api/1'), dumps(dict(text='nice')))
        assert response.code == 404, 'the status code should be 404 but it was %d' % response.code

    def test_try_to_delete_a_resource(self):
        response = self.delete(self.get_url('/api/1'))
        assert response.code == 404, 'the status code should be 404 but it was %d' % response.code
