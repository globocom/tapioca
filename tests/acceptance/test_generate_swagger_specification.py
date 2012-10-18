#!/usr/bin/env python
# -*- coding: utf-8 -*-

from json import loads
from unittest import TestCase

from tapioca.spec import SwaggerSpecification, APISpecification, \
        Path, Method, Param


class SwaggerGenerationTestCase(TestCase):

    def apply_generation(self, api):
        result = SwaggerSpecification(api).generate()
        return loads(result)

    def test_general_info(self):
        api = APISpecification(version='v1', base_url='http://api.globo.com')
        result = self.apply_generation(api)
        assert result['apiVersion'] == 'v1'
        assert result['swaggerVersion'] == '1.1'
        assert result['basePath'] == 'http://api.globo.com/v1'
        assert result['apis'] == []
        assert result['models'] == []

    def test_gen_spec_for_a_resource(self):
        api = APISpecification(version='v1', base_url='http://api.globo.com')
        api.add_path(Path('/comments', methods=[Method('GET')]))
        result = self.apply_generation(api)
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
        api.add_path(Path('/dogs', methods=[Method('PUT')]))
        result = self.apply_generation(api)
        assert result['apis'][0]['path'] == '/dogs'
        operation = result['apis'][0]['operations'][0]
        assert operation['httpMethod'] == 'PUT'
        assert operation['nickname'] == 'put_dogs'

    def test_gen_spec_with_params(self):
        api = APISpecification(version='v1', base_url='http://api.globo.com')
        api.add_path(Path('/dogs.{format}',
            params=[
                Param('format')
            ],
            methods=[
                Method('GET')
            ]
        ))
        result = self.apply_generation(api)
        assert result['apis'][0]['path'] == '/dogs.{format}'
        operation = result['apis'][0]['operations'][0]
        assert len(operation['parameters']) == 1
        assert operation['parameters'][0]['name'] == 'format'
        assert operation['parameters'][0]['paramType'] == 'path'
        assert operation['parameters'][0]['description'] == ''
        assert operation['parameters'][0]['dataType'] == 'String'
        assert operation['parameters'][0]['required'] == True
        assert operation['parameters'][0]['allowMultiple'] == False
