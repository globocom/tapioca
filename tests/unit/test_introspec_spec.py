from unittest import TestCase

from schema import Optional
from tapioca import TornadoRESTful, ResourceHandler, validate
from tapioca.spec import *

from tests.support import ResourceWithDocumentation


class ExtractInfoFromAPITestCase(TestCase):

    def test_basic_info_about_api(self):
        api = TornadoRESTful(
                version='v1', base_url='http://api.images.globo.com')
        my_api = api.get_spec()
        assert isinstance(my_api, APISpecification)
        assert my_api.version == 'v1'
        assert my_api.base_url == 'http://api.images.globo.com'
        assert my_api.complete_url == 'http://api.images.globo.com/v1'
        assert my_api.resources == []

    def test_complete_resource_mapping(self):
        self.api = TornadoRESTful(
                version='v1', base_url='http://api.images.globo.com')
        self.api.add_resource('comments', ResourceWithDocumentation)
        my_api = self.api.get_spec()
        resource = my_api.resources[0]

        assert resource.name == 'comments'
        assert len(resource.paths) == 4

        path_names = [p.name for p in resource.paths]

        assert '/comments' in path_names
        assert '/comments.{type}' in path_names
        assert '/comments/{key}' in path_names
        assert '/comments/{key}.{type}' in path_names

        method_names = {}
        param_names = {}
        for path in resource.paths:
            method_names[path.name] = [m.name for m in path.methods]
            param_names[path.name] = [p.name for p in path.params]

        assert len(method_names['/comments']) == 2
        assert 'GET' in method_names['/comments']
        assert 'POST' in method_names['/comments']

        assert len(method_names['/comments.{type}']) == 2
        assert 'GET' in method_names['/comments.{type}']
        assert 'POST' in method_names['/comments.{type}']
        assert len(list(param_names['/comments.{type}'])) == 1
        assert 'type' in param_names['/comments.{type}']

        assert len(method_names['/comments/{key}']) == 3
        assert 'GET' in method_names['/comments/{key}']
        assert 'PUT' in method_names['/comments/{key}']
        assert 'DELETE' in method_names['/comments/{key}']
        assert len(list(param_names['/comments/{key}'])) == 1
        assert 'key' in param_names['/comments/{key}']

        assert len(method_names['/comments/{key}.{type}']) == 3
        assert 'GET' in method_names['/comments/{key}.{type}']
        assert 'PUT' in method_names['/comments/{key}.{type}']
        assert 'DELETE' in method_names['/comments/{key}.{type}']
        assert len(list(param_names['/comments/{key}.{type}'])) == 2
        assert 'type' in param_names['/comments/{key}.{type}']
        assert 'key' in param_names['/comments/{key}.{type}']

    def test_spec_that_only_impl_get_collection(self):

        class HalfImplementedResource(ResourceHandler):
            def get_collection(self, callback):
                callback([])

        self.api = TornadoRESTful(
                version='v1', base_url='http://api.images.globo.com')
        self.api.add_resource('comments', HalfImplementedResource)
        my_api = self.api.get_spec()
        resource = my_api.resources[0]
        assert resource.name == 'comments'
        assert len(resource.paths) == 2
        assert resource.paths[0].name == '/comments'
        assert len(resource.paths[0].methods) == 1
        assert resource.paths[0].methods[0].name == 'GET'
        assert resource.paths[1].name == '/comments.{type}'
        assert len(resource.paths[1].methods) == 1
        assert resource.paths[1].methods[0].name == 'GET'

    def test_spec_that_only_impl_create_model(self):

        class HalfImplementedResource(ResourceHandler):
            def create_model(self, *args, **kwargs):
                pass

        self.api = TornadoRESTful(
                version='v1', base_url='http://api.images.globo.com')
        self.api.add_resource('comments', HalfImplementedResource)
        my_api = self.api.get_spec()
        resource = my_api.resources[0]
        assert len(resource.paths) == 2
        assert resource.paths[0].name == '/comments'
        assert len(resource.paths[0].methods) == 1
        assert resource.paths[0].methods[0].name == 'POST'
        assert resource.paths[1].name == '/comments.{type}'
        assert len(resource.paths[1].methods) == 1
        assert resource.paths[1].methods[0].name == 'POST'

    def test_spec_that_only_impl_get_model(self):

        class HalfImplementedResource(ResourceHandler):
            def get_model(self, *args, **kwargs):
                pass

        self.api = TornadoRESTful(
                version='v1', base_url='http://api.images.globo.com')
        self.api.add_resource('comments', HalfImplementedResource)
        my_api = self.api.get_spec()
        resource = my_api.resources[0]
        assert len(resource.paths) == 2
        assert resource.paths[0].name == '/comments/{key}'
        assert len(resource.paths[0].methods) == 1
        assert resource.paths[0].methods[0].name == 'GET'
        assert resource.paths[1].name == '/comments/{key}.{type}'
        assert len(resource.paths[1].methods) == 1
        assert resource.paths[1].methods[0].name == 'GET'

    def test_spec_that_only_impl_update_model(self):

        class HalfImplementedResource(ResourceHandler):
            def update_model(self, *args, **kwargs):
                """Updates the resource."""
                pass

        self.api = TornadoRESTful(
                version='v1', base_url='http://api.images.globo.com')
        self.api.add_resource('comments', HalfImplementedResource)
        my_api = self.api.get_spec()
        resource = my_api.resources[0]
        assert len(resource.paths) == 2
        assert resource.paths[0].name == '/comments/{key}'
        assert len(resource.paths[0].methods) == 1
        assert resource.paths[0].methods[0].name == 'PUT'
        assert resource.paths[0].methods[0].description == 'Updates the resource.'
        assert resource.paths[1].name == '/comments/{key}.{type}'
        assert len(resource.paths[1].methods) == 1
        assert resource.paths[1].methods[0].name == 'PUT'

    def test_spec_that_only_impl_delete_model(self):

        class HalfImplementedResource(ResourceHandler):
            def delete_model(self, *args, **kwargs):
                pass

        self.api = TornadoRESTful(
                version='v1', base_url='http://api.images.globo.com')
        self.api.add_resource('comments', HalfImplementedResource)
        my_api = self.api.get_spec()
        resource = my_api.resources[0]
        assert len(resource.paths) == 2
        assert resource.paths[0].name == '/comments/{key}'
        assert len(resource.paths[0].methods) == 1
        assert resource.paths[0].methods[0].name == 'DELETE'
        assert resource.paths[1].name == '/comments/{key}.{type}'
        assert len(resource.paths[1].methods) == 1
        assert resource.paths[1].methods[0].name == 'DELETE'

    def test_spec_with_params(self):

        class HalfImplementedResource(ResourceHandler):

            @validate(querystring={'host': unicode})
            def get_collection(self, *args, **kwargs):
                pass

        self.api = TornadoRESTful(
                version='v1', base_url='http://api.images.globo.com')
        self.api.add_resource('comments', HalfImplementedResource)
        my_api = self.api.get_spec()
        resource = my_api.resources[0]
        assert resource.paths[0].methods[0].name == 'GET'
        assert len(resource.paths[0].methods[0].params) == 1
        param = resource.paths[0].methods[0].params[0]
        assert isinstance(param, Param)
        assert param.name == 'host'
        assert param.description == ''
        assert param.style == 'querystring'

    def test_spec_with_optional_param(self):

        class HalfImplementedResource(ResourceHandler):

            @validate(querystring={Optional('host'): unicode})
            def get_collection(self, *args, **kwargs):
                pass

        self.api = TornadoRESTful(
                version='v1', base_url='http://api.images.globo.com')
        self.api.add_resource('comments', HalfImplementedResource)
        my_api = self.api.get_spec()
        resource = my_api.resources[0]
        param = resource.paths[0].methods[0].params[0]
        assert param.required == False
