from json import loads

import tornado.web
from schema import Use
from tornado.testing import AsyncHTTPTestCase

from tests.support import AsyncHTTPClientMixin, assert_response_code

from tapioca import TornadoRESTful, ResourceHandler, validate, optional


class ProjectsResource(ResourceHandler):

    @validate(querystring={
        'ck': unicode,
        optional('name'): (unicode, 'The name of the project that do you want to search for'),
        optional('size'): (Use(int), 'The maximum number of projects you want')
    })
    def get_collection(self, callback):
        callback([self.values['querystring']])


class UseOfValidationTestCase(AsyncHTTPTestCase, AsyncHTTPClientMixin):

    def get_app(self):
        api = TornadoRESTful()
        api.add_resource('projects', ProjectsResource)
        application = tornado.web.Application(api.get_url_mapping())
        return application

    def test_should_return_when_called_with_the_correct_values(self):
        response = self.get('/projects.json?ck=1&name=test&size=10')
        assert_response_code(response, 200)

    def test_should_return_ok_if_more_params_than_expected(self):
        response = self.get('/projects.json?ck=1&name=test&foo=bar&size=234')
        assert_response_code(response, 200)

    def test_should_return_an_descriptive_error(self):
        response = self.get('/projects.json?ck=1&name=test&size=foo')
        assert_response_code(response, 400)
        assert loads(response.body)['error'] == \
            'The "size" parameter value is not valid.'

    def test_should_be_able_to_call_without_size(self):
        response = self.get('/projects.json?ck=1&name=foobar')
        assert_response_code(response, 200)

    def test_should_throw_error_when_required_param_is_not_passed(self):
        response = self.get('/projects.json')
        assert_response_code(response, 400)
        assert loads(response.body)['error'] == \
            'The "ck" parameter is required.'


class NoAccessValuesInQuerystring(ResourceHandler):

    @validate(querystring={
        'it_is_int_value': (Use(int), 'The maximum number of projects you want')
    })
    def get_collection(self, callback):
        callback(['its always valid'])


class NoAccessDefinedValuesTestCase(AsyncHTTPTestCase, AsyncHTTPClientMixin):

    def get_app(self):
        api = TornadoRESTful()
        api.add_resource('always_valid', NoAccessValuesInQuerystring)
        application = tornado.web.Application(api.get_url_mapping())
        return application

    def test_should_be_a_valid_using_int(self):
        response = self.get('/always_valid.json?size=1')
        assert_response_code(response, 200)

    def test_should_be_a_valid_request_anyway(self):
        response = self.get('/always_valid.json?size=abc')
        assert_response_code(response, 200)
