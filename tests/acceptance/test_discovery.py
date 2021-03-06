from json import loads

import tornado.web
from tornado.testing import AsyncHTTPTestCase

from tests.support import ResourceWithDocumentation
from tests.support import AsyncHTTPClientMixin

from tapioca import TornadoRESTful, ResourceHandler


class DiscoveryRouteTestCase(AsyncHTTPTestCase, AsyncHTTPClientMixin):

    def get_app(self):
        api = TornadoRESTful(
                version='v1', base_url='http://api.tapioca.com', discovery=True)
        api.add_resource('comments', ResourceWithDocumentation)
        return tornado.web.Application(api.get_url_mapping())

    def test_request_swagger_spec(self):
        response = self.get('/discovery.swagger')
        assert response.code == 200, response.code
        content = loads(response.body.decode('utf-8'))
        response = self.get(content['apis'][0]['path'])
        assert response.code == 200

    def test_request_wadl_spec(self):
        response = self.get('/discovery.wadl')
        assert response.code == 200, response.code
        assert 'application' in response.body.decode('utf-8')
