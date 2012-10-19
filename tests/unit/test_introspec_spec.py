#!/usr/bin/env python
# -*- coding: utf-8 -*-

from unittest import TestCase

from tapioca import TornadoRESTful, ResourceHandler
from tapioca.spec import *


class ResourceWithDocumentation(ResourceHandler):
    """
    This is my resource
    """

    def create_model(self, model):
        """
        Creates a new instance of the resource
        """
        return {}

    def get_collection(self, callback):
        """
        Gets all instances of the resource
        """
        callback([])

    def get_model(self, cid, *args):
        """
        Gets an instance of the resource
        """
        return {}

    def update_model(self, model, cid, *args):
        """
        Update a specific instance of the resource
        """
        pass

    def delete_model(self, cid):
        """
        Deletes an intance of the resource
        """
        pass


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
        assert len(resource.paths) > 0
        assert resource.paths[0].name == '/comments'
        assert resource.paths[0].methods[0].name == 'GET'
        assert resource.paths[0].methods[1].name == 'POST'
        assert resource.paths[1].name == '/comments.{type}'
        assert len(resource.paths[1].params) == 1
        assert resource.paths[1].params[0].name == 'type'
        assert resource.paths[1].methods[0].name == 'GET'
        assert resource.paths[1].methods[1].name == 'POST'
        assert resource.paths[2].name == '/comments/{key}'
        assert len(resource.paths[2].params) == 1
        assert resource.paths[2].params[0].name == 'key'
        assert resource.paths[2].methods[0].name == 'GET'
        assert resource.paths[2].methods[1].name == 'PUT'
        assert resource.paths[2].methods[2].name == 'DELETE'
        assert resource.paths[3].name == '/comments/{key}.{type}'
        assert len(resource.paths[3].params) == 2
        assert resource.paths[3].params[0].name == 'key'
        assert resource.paths[3].params[1].name == 'type'
        assert resource.paths[3].methods[0].name == 'GET'
        assert resource.paths[3].methods[1].name == 'PUT'
        assert resource.paths[3].methods[2].name == 'DELETE'

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
