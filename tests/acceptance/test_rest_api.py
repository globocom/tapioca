#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from json import loads, dumps
from xml.etree import ElementTree
from unittest import TestCase

import tornado.web
from tornado.testing import AsyncHTTPTestCase

from images_api.rest_api import ApiManager, ApiResourceHandler, \
        ResourceDoesNotExist, JsonEncoder

from tests.support import AsyncHTTPClientMixin


FAKE_DATABASE = None


class XmlEncoder(object):
    mimetype = 'text/xml'

    def __init__(self, handler):
        self.handler = handler

    def encode(self, resource):
        data = '%s'
        if type(resource) == list:
            data = '<comments>%s</comments>'
        return data % ('<comment id="%s">%s</comment>' % \
                (resource['id'], resource['text']))

    def decode(self, data):
        doc = ElementTree.fromstring(data)
        new_data = {
            'text': doc.text
        }
        resource_id = doc.get('id', None)
        if not resource_id is None:
            new_data['id'] = resource_id
        return new_data


class AddMoreEncodersMixin:

    def get_encoders(self):
        return ApiResourceHandler.get_encoders(self) + [XmlEncoder]

class ImplementAllRequiredMethodsInApiHandler:

    def _find(self, cid):
        ms = [x for x in FAKE_DATABASE if x['id'] == cid]
        if ms:
            return ms[0]
        else:
            raise ResourceDoesNotExist()

    def create_model(self, model):
        model['id'] = max([int(x['id']) for x in FAKE_DATABASE]) + 1
        FAKE_DATABASE.append(model)
        logging.debug('created %s' % str(model))
        return model

    def get_collection(self, callback):
        callback(FAKE_DATABASE)

    def get_model(self, cid, *args):
        return self._find(int(cid))

    def update_model(self, model, cid, *args):
        model['id'] = int(cid)
        logging.debug('updating %s %s' % (str(cid), str(model)))
        FAKE_DATABASE[FAKE_DATABASE.index(self._find(int(cid)))] = model

    def delete_model(self, cid):
        logging.debug('deleting')
        item = self._find(int(cid))
        FAKE_DATABASE.remove(item)


class FullTestHandler(
        ImplementAllRequiredMethodsInApiHandler,
        AddMoreEncodersMixin,
        ApiResourceHandler):
    pass


class RespondOnlyJsonResourceHandler(
        ImplementAllRequiredMethodsInApiHandler,
        ApiResourceHandler):
    pass


class TestApiManager(TestCase):

    def setUp(self):
        self.api = ApiManager()

    def test_should_be_possible_to_add_a_handler(self):
        self.api.add_resource_handler('api', FullTestHandler)
        assert (r'/api/?', FullTestHandler) in self.api.build_handlers()

    def test_should_generate_a_path_for_access_direcly_an_instance(self):
        self.api.add_resource_handler('comment', FullTestHandler)
        assert (r'/comment/(.+)/?', FullTestHandler) in self.api.build_handlers()


class BaseApiHandlerTestCase(AsyncHTTPTestCase, AsyncHTTPClientMixin):

    def get_app(self):
        api = ApiManager()
        api.add_resource_handler('api', FullTestHandler)
        #, Resource('comment', {
            #'text': dict(name='Text', type=str, default='bla', required=False)
        #}))
        application = tornado.web.Application(api.build_handlers())
        return application

    def setUp(self, *args, **kw):
        super(BaseApiHandlerTestCase, self).setUp(*args, **kw)
        global FAKE_DATABASE
        FAKE_DATABASE = [dict(id=i, text='X' * i) for i in range(10)]

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
        assert 'Location' in response.headers

    def test_put_to_update_an_existing_resource(self):
        response = self.get('/api/1')
        assert response.code == 200, 'the status code should be 200 but it was %d' % response.code
        resource = loads(response.body)
        resource['comment'] = 'wow!'
        response = self.put(self.get_url('/api/1'), dumps(resource))
        assert response.code == 204, 'the status code should be 204 but it was %d' % response.code
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

    def test_return_resource_as_xml(self):
        url = self.get_url('/api/1')
        response = self._fetch(url, 'GET', headers=dict(Accept='text/xml'))
        assert response.code == 200, 'the status code should be 200 but it was %d' % response.code
        assert 'text/xml' in response.headers['Content-Type'], 'the content-type should be text/xml but it was %s' % response.headers['Content-Type']
        assert response.body == '<comment id="1">X</comment>'

    def test_choose_response_type_based_on_the_accept_header(self):
        url = self.get_url('/api/1')
        response = self._fetch(url, 'GET', headers={'Accept':'application/json, text/xml'})
        assert response.code == 200, 'the status code should be 200 but it was %d' % response.code
        assert 'application/json' in response.headers['Content-Type'], 'the content-type should be application/json but it was %s' % response.headers['Content-Type']

    def test_create_new_instance_of_the_resource_with_content_type_text_xml(self):
        a_new_item ='<comment>meu comentario</comment>'
        response = self._fetch(self.get_url('/api'), 'POST', headers={'Content-Type': 'text/xml'}, body=a_new_item)
        assert response.code == 201, 'the status code should be 201 but it was %d' % response.code
        # gets the new instance
        response = self._fetch(response.headers['Location'], 'GET', headers={'Accept': 'text/xml'})
        assert 'text/xml' in response.headers['Content-Type'], 'the content-type should be text/xml but it was %s' % response.headers['Content-Type']
        doc = ElementTree.fromstring(response.body)
        assert doc.tag == 'comment', 'the tag should be "comment" but it was %s' % doc.tag
        assert doc.text == 'meu comentario', 'the comment text should be "meu comentario" but it was %s' % doc.text
        assert doc.get('id') == '10', 'the id should be 11 but it was %s' % doc.get('id')

    def test_get_resource_with_content_type_text_xml(self):
        response = self._fetch(self.get_url('/api/2'), 'GET', headers={'Accept': 'text/xml'})
        assert 'text/xml' in response.headers['Content-Type'], 'the content-type should be text/xml but it was %s' % response.headers['Content-Type']
        doc = ElementTree.fromstring(response.body)
        assert doc.tag == 'comment', 'the tag should be "comment" but it was %s' % doc.tag
        assert doc.text == 'XX', 'the comment text should be "XX" but it was %s' % doc.text

    def test_update_new_instance_of_the_resource_with_content_type_text_xml(self):
        an_updated_item ='<comment id="2">meu comentario</comment>'
        response = self._fetch(self.get_url('/api/2'), 'PUT', headers={'Content-Type': 'text/xml'}, body=an_updated_item)
        assert response.code == 204, 'the status code should be 204 but it was %d' % response.code
        # get the resource to verify if was updated
        response = self._fetch(response.headers['Location'], 'GET', headers={'Accept': 'text/xml'})
        assert 'text/xml' in response.headers['Content-Type'], 'the content-type should be text/xml but it was %s' % response.headers['Content-Type']
        doc = ElementTree.fromstring(response.body)
        assert doc.tag == 'comment', 'the tag should be "comment" but it was %s' % doc.tag
        assert doc.text == 'meu comentario', 'the comment text should be "meu comentario" but it was %s' % doc.text

    def test_jsonp_response_when_accept_textjavascript(self):
        response = self._fetch(
            self.get_url('/api/?callback=my_callback'), 'GET', headers={
                'Accept': 'text/javascript'
            })
        assert response.code == 200, \
                'the status code should be 200 but it was %d' % response.code
        assert response.body.startswith('my_callback(')

    def test_use_the_default_encoder(self):
        response = self._fetch(
            self.get_url('/api/?callback=my_callback'), 'GET', headers={
                'Accept': 'lol/cat'
            })
        assert response.code == 200, \
                'the status code should be 200 but it was %d' % response.code


class ApiResourceHandlerWithoutImplementationTestCase(AsyncHTTPTestCase, AsyncHTTPClientMixin):

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
