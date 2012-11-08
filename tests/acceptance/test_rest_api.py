import re
import logging
from json import loads, dumps
from xml.etree import ElementTree
from unittest import TestCase

import tornado.web
from tornado.testing import AsyncHTTPTestCase

from tapioca import TornadoRESTful, ResourceHandler, \
        ResourceDoesNotExist, JsonEncoder, JsonpEncoder, HtmlEncoder

from tests.support import AsyncHTTPClientMixin, assert_response_code


FAKE_DATABASE = None


class XmlEncoder(object):
    mimetype = 'text/xml'
    extension = 'xml'

    def __init__(self, handler):
        self.handler = handler

    def encode(self, resource):
        data = '{}'
        if type(resource) == list:
            data = '<comments>{}</comments>'
        return data.format('<comment id="{id}">{text}</comment>'
                .format(**resource))

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
    encoders = (JsonEncoder, JsonpEncoder, XmlEncoder, HtmlEncoder,)


class ImplementAllRequiredMethodsInApiHandler:

    def _find(self, cid):
        ms = [x for x in FAKE_DATABASE if x['id'] == cid]
        if ms:
            return ms[0]
        else:
            raise ResourceDoesNotExist()

    def create_model(self, callback):
        model = self.load_data()
        model['id'] = max([int(x['id']) for x in FAKE_DATABASE]) + 1
        FAKE_DATABASE.append(model)
        logging.debug('created {0!s}'.format(model))
        url_to_instance = '{r.protocol}://{r.host}{r.path}/{id:d}'.format(
                        r=self.request, id=model['id'])
        callback(model, url_to_instance)

    def get_collection(self, callback):
        callback(FAKE_DATABASE)

    def get_model(self, cid, callback, *args):
        callback(self._find(int(cid)))

    def update_model(self, cid, callback, *args):
        model = self.load_data()
        model['id'] = int(cid)
        logging.debug('updating {0!s} {1!s}'.format(str(cid), str(model)))
        FAKE_DATABASE[FAKE_DATABASE.index(self._find(int(cid)))] = model
        url_to_instance = '{r.protocol}://{r.host}{r.path}'.format(
                        r=self.request)
        callback(url_to_instance)

    def delete_model(self, cid, callback):
        logging.debug('deleting')
        item = self._find(int(cid))
        FAKE_DATABASE.remove(item)
        callback()


class FullTestHandler(
        ImplementAllRequiredMethodsInApiHandler,
        AddMoreEncodersMixin,
        ResourceHandler):
    pass


class RespondOnlyJsonResourceHandler(
        ImplementAllRequiredMethodsInApiHandler,
        ResourceHandler):
    pass


class BaseApiHandlerTestCase(AsyncHTTPTestCase, AsyncHTTPClientMixin):

    def get_app(self):
        api = TornadoRESTful(version='v1', base_url='http://api.tapioca.com')
        api.add_resource('api', FullTestHandler)
        application = tornado.web.Application(api.get_url_mapping())
        return application

    def setUp(self, *args, **kw):
        super(BaseApiHandlerTestCase, self).setUp(*args, **kw)
        global FAKE_DATABASE
        FAKE_DATABASE = [dict(id=i, text='X' * i) for i in range(10)]

    def test_get_request_to_list_all_resource_instances(self):
        response = self.get('/api')
        assert_response_code(response, 200)
        resources = loads(response.body.decode('utf-8'))
        number_of_items = len(resources)
        assert number_of_items == 10, 'should return 10 resources but returned {0:d}'.format(number_of_items)
        for item in resources:
            assert 'id' in item, 'should have the key \'id\' in the resource instance'
            assert 'text' in item, 'should have the \'text\' in the resource instance'

    def test_get_a_specific_resource_using_get_request(self):
        response = self.get('/api/3')
        assert_response_code(response, 200)
        resource = loads(response.body.decode('utf-8'))
        assert 'id' in resource, 'should have the key \'id\' in the resource instance {0!s}'.format(resource)
        assert 'text' in resource, 'should have the \'text\' in the resource instance {0!s}'.format(resource)

    def test_get_a_resource_that_does_not_exist(self):
        response = self.get('/api/30')
        assert_response_code(response, 404)

    def test_post_to_create_a_new_resource(self):
        a_new_item = {
            'text': 'this is my new item'
        }
        response = self.post(self.get_url('/api'), dumps(a_new_item))
        assert_response_code(response, 201)
        self.assertRegexpMatches(response.headers['Location'], r'http://localhost:\d+/api/\d+')
        assert loads(response.body)['text'] == 'this is my new item'

    def test_put_to_update_an_existing_resource(self):
        response = self.get('/api/1')
        assert_response_code(response, 200)
        resource = loads(response.body.decode('utf-8'))
        resource['comment'] = 'wow!'
        response = self.put(self.get_url('/api/1'), dumps(resource))
        assert_response_code(response, 204)
        response = self.get('/api/1')
        resource = loads(response.body.decode('utf-8'))
        assert 'comment' in resource
        assert resource['comment'] == 'wow!'

    def test_try_to_update_a_resource_that_does_not_exist(self):
        response = self.put(self.get_url('/api/30'), dumps(dict(text='not exist')))
        assert_response_code(response, 404)

    def test_delete_method_to_destroy_a_resource(self):
        response = self.delete(self.get_url('/api/1'))
        assert_response_code(response, 200)
        response = self.delete(self.get_url('/api/1'))
        assert_response_code(response, 404)

    def test_return_resource_as_xml(self):
        url = self.get_url('/api/1')
        response = self._fetch(url, 'GET', headers=dict(Accept='text/xml'))
        assert_response_code(response, 200)
        assert 'text/xml' in response.headers['Content-Type'], 'the content-type should be text/xml but it was {0}'.format(response.headers['Content-Type'])
        assert response.body == b'<comment id="1">X</comment>'

    def test_choose_response_type_based_on_the_accept_header(self):
        url = self.get_url('/api/1')
        response = self._fetch(url, 'GET', headers={'Accept':'application/json, text/xml'})
        assert_response_code(response, 200)
        assert 'application/json' in response.headers['Content-Type'], 'the content-type should be application/json but it was {0}'.format(response.headers['Content-Type'])

    def test_create_new_instance_of_the_resource_with_content_type_text_xml(self):
        a_new_item ='<comment>meu comentario</comment>'
        response = self._fetch(self.get_url('/api'), 'POST', headers={'Content-Type': 'text/xml'}, body=a_new_item)
        assert_response_code(response, 201)
        # gets the new instance
        response = self._fetch(response.headers['Location'], 'GET', headers={'Accept': 'text/xml'})
        assert 'text/xml' in response.headers['Content-Type'], 'the content-type should be text/xml but it was {0}'.format(response.headers['Content-Type'])
        doc = ElementTree.fromstring(response.body)
        assert doc.tag == 'comment', 'the tag should be "comment" but it was {0}'.format(doc.tag)
        assert doc.text == 'meu comentario', 'the comment text should be "meu comentario" but it was {0}'.format(doc.text)
        assert doc.get('id') == '10', 'the id should be 11 but it was {0}'.format(doc.get('id'))

    def test_get_resource_with_content_type_text_xml(self):
        response = self._fetch(self.get_url('/api/2'), 'GET', headers={'Accept': 'text/xml'})
        assert 'text/xml' in response.headers['Content-Type'], 'the content-type should be text/xml but it was {0}'.format(response.headers['Content-Type'])
        doc = ElementTree.fromstring(response.body)
        assert doc.tag == 'comment', 'the tag should be "comment" but it was {0}'.format(doc.tag)
        assert doc.text == 'XX', 'the comment text should be "XX" but it was {0}'.format(doc.text)

    def test_update_new_instance_of_the_resource_with_content_type_text_xml(self):
        an_updated_item ='<comment id="2">meu comentario</comment>'
        response = self._fetch(self.get_url('/api/2'), 'PUT', headers={'Content-Type': 'text/xml'}, body=an_updated_item)
        assert_response_code(response, 204)
        # get the resource to verify if it was updated
        response = self._fetch(response.headers['Location'], 'GET', headers={'Accept': 'text/xml'})
        assert 'text/xml' in response.headers['Content-Type'], 'the content-type should be text/xml but it was {0}'.format(response.headers['Content-Type'])
        doc = ElementTree.fromstring(response.body)
        assert doc.tag == 'comment', 'the tag should be "comment" but it was {0}'.format(doc.tag)
        assert doc.text == 'meu comentario', 'the comment text should be "meu comentario" but it was {0}'.format(doc.text)

    def test_jsonp_response_when_accept_textjavascript(self):
        response = self._fetch(
            self.get_url('/api/?callback=my_callback'), 'GET', headers={
                'Accept': 'text/javascript'
            })
        assert_response_code(response, 200)
        assert response.body.decode('utf-8').startswith('my_callback(')

    def test_use_the_default_encoder(self):
        response = self._fetch(
            self.get_url('/api/?callback=my_callback'), 'GET', headers={
                'Accept': 'lol/cat'
            })
        assert_response_code(response, 200)

    def test_show_content_as_html_when_requested_by_browser(self):
        CHROME_ACCEPT_HEADER = 'text/html,application/xhtml+xml,application/xm'\
                               'l;q=0.9,*/*;q=0.8'
        response = self._fetch(
            self.get_url('/api/'), 'GET', headers={
                'Accept': CHROME_ACCEPT_HEADER
            })
        assert_response_code(response, 200)
        assert '<body>' in response.body.decode('utf-8')

    def test_should_return_type_json_as_specified_in_url(self):
        response = self.get('/api/1.json')
        assert_response_code(response, 200)
        data = loads(response.body.decode('utf-8'))
        assert 'id' in data.decode('utf-8')

    def test_should_return_type_xml_as_specified_in_url(self):
        response = self.get('/api/1.xml')
        assert_response_code(response, 200)
        assert '</comment>' in response.body.decode('utf-8')

    def test_should_raise_404_when_extension_is_not_found(self):
        response = self.get('/api/1.rb')
        assert_response_code(response, 404)

    def test_should_return_type_json_as_specified_in_url(self):
        response = self.get('/api/1.js?callback=myCallbackFooBar')
        assert_response_code(response, 200)
        assert response.body.decode('utf-8').startswith('myCallbackFooBar(')

    def test_should_return_the_default_callback_when_i_not_specify_in_my_request(self):
        response = self.get('/api/1.js')
        assert_response_code(response, 200)
        assert re.match(b'^[\w_]+\(.*', response.body), response.body.decode('utf-8')

    def test_should_return_the_default_callback_when_i_not_specify_in_my_request(self):
        response = self.get('/api/1.js')
        assert_response_code(response, 200)
        assert re.match(b'^defaultCallback\(.*', response.body), response.body.decode('utf-8')


class WithDefaultCallbackHandler(ResourceHandler):
    default_callback_name = 'thePersonalizedCallback'

    def get_model(self, cid, callback, *args):
        callback({})


class JsonEncoderDefineAnDefaultCallbackTestCase(AsyncHTTPTestCase,\
        AsyncHTTPClientMixin):

    def get_app(self):
        api = TornadoRESTful(cross_origin_enabled=True)
        api.add_resource('api', WithDefaultCallbackHandler)
        application = tornado.web.Application(api.get_url_mapping())
        return application

    def test_should_return_the_default_callback_when_i_not_specify_in_my_request(self):
        response = self.get('/api/1.js')
        assert_response_code(response, 200)
        assert re.match(b'^thePersonalizedCallback\(.*', response.body), response.body.decode('utf-8')

    def test_should_return_with_the_callback_name_i_choose(self):
        response = self.get('/api/1.js?callback=fooBar')
        assert_response_code(response, 200)
        assert response.body.decode('utf-8').startswith('fooBar(')

    def test_should_return_cross_origin_header(self):
        response = self.get('/api/1.js?callback=fooBar')
        assert_response_code(response, 200)
        assert 'Access-Control-Allow-Origin' in response.headers
        assert response.headers['Access-Control-Allow-Origin'] == '*'


class ResourceHandlerWithoutImplementationTestCase(AsyncHTTPTestCase,\
        AsyncHTTPClientMixin):

    def get_app(self):
        api = TornadoRESTful()
        api.add_resource('api', ResourceHandler)
        application = tornado.web.Application(api.get_url_mapping())
        return application

    def test_try_to_create_a_resource(self):
        response = self.post(self.get_url('/api'), dumps(dict(text='nice')))
        assert_response_code(response, 404)

    def test_try_to_list_resources(self):
        response = self.get('/api')
        assert_response_code(response, 404)

    def test_try_to_get_instance(self):
        response = self.get('/api/1')
        assert_response_code(response, 404)

    def test_try_to_update_a_resource(self):
        response = self.put(self.get_url('/api/1'), dumps(dict(text='nice')))
        assert_response_code(response, 404)

    def test_try_to_delete_a_resource(self):
        response = self.delete(self.get_url('/api/1'))
        assert_response_code(response, 404)
