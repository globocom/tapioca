#!/usr/bin/env python
# -*- coding: utf-8 -*-

from json import loads
from unittest import TestCase

from tapioca.spec import SwaggerSpecification, APISpecification, \
        Resource, Path, Method, Param


class SwaggerGenerationTestCase(TestCase):

    def apply_generation(self, api, resource=None):
        result = SwaggerSpecification(api).generate(resource)
        return loads(result)

    def test_general_info(self):
        api = APISpecification(version='v1', base_url='http://api.globo.com')
        result = self.apply_generation(api)
        assert result['apiVersion'] == 'v1'
        assert result['swaggerVersion'] == '1.1'
        assert result['basePath'] == 'http://api.globo.com/v1'
        assert result['apis'] == []
        assert result['models'] == []

    def test_gen_spec_generic_with_resource(self):
        api = APISpecification(version='v1', base_url='http://api.globo.com')
        api.add_resource(
            Resource('comments',
                paths=[
                    Path('/comments', methods=[Method('GET')])
                ]))
        result = self.apply_generation(api)
        assert len(result['apis']) == 1
        assert result['apis'][0]['path'] == '/discovery/comments.swagger'
        assert result['apis'][0]['description'] == ''

    def test_gen_spec_for_a_resource(self):
        api = APISpecification(version='v1', base_url='http://api.globo.com')
        resource_name = 'comments'
        api.add_resource(
            Resource(resource_name,
                paths=[
                    Path('/comments', methods=[Method('GET')])
                ]))
        result = self.apply_generation(api, resource_name)
        assert result['resourcePath'] == '/comments'
        assert len(result['apis']) == 1
        assert result['apis'][0]['path'] == '/comments'
        assert result['apis'][0]['description'] == ''
        assert len(result['apis'][0]['operations']) == 1
        operation = result['apis'][0]['operations'][0]
        assert operation['httpMethod'] == 'GET'
        assert operation['nickname'] == 'get_comments'
        assert operation['parameters'] == []
        assert operation['summary'] == ''
        assert operation['notes'] == ''
        assert operation['errorResponses'] == []

    def test_gen_spec_for_put_method(self):
        api = APISpecification(version='v1', base_url='http://api.globo.com')
        api.add_resource(Resource('dogs',
            paths=[
                Path('/dogs', methods=[
                    Method('PUT')])]))
        api.add_resource(Resource('cats',
            paths=[
                Path('/cats', methods=[
                    Method('PUT')])]))
        result = self.apply_generation(api, 'cats')
        assert result['resourcePath'] == '/cats'
        assert result['apis'][0]['path'] == '/cats'
        operation = result['apis'][0]['operations'][0]
        assert operation['httpMethod'] == 'PUT'
        assert operation['nickname'] == 'put_cats'

    def test_gen_spec_with_params(self):
        api = APISpecification(version='v1', base_url='http://api.globo.com')
        api.add_resource(Resource('dogs', 
            paths=[
                Path('/dogs/{key}',
                    params=[
                        Param('key')
                    ],
                    methods=[
                        Method('GET')
                    ]
                ),
            ])
        )
        result = self.apply_generation(api, 'dogs')
        assert result['apis'][0]['path'] == '/dogs/{key}'
        operation = result['apis'][0]['operations'][0]
        assert len(operation['parameters']) == 1
        assert operation['parameters'][0]['name'] == 'key'
        assert operation['parameters'][0]['paramType'] == 'path'
        assert operation['parameters'][0]['description'] == ''
        assert operation['parameters'][0]['dataType'] == 'String'
        assert operation['parameters'][0]['required'] == True
        assert operation['parameters'][0]['allowMultiple'] == False
