from xml.etree import ElementTree
from unittest import TestCase

from tapioca.spec import APISpecification, Resource, Path, Param, Method, \
        WADLSpecification


class WADLSpecGeneration(TestCase):

    def gen(self, spec):
        return WADLSpecification(spec).generate()

    def test_generate_basic_spec(self):
        api = APISpecification(version='v1', base_url='http://api.globo.com')
        result = self.gen(api)
        assert '<application xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:apigee="http://api.apigee.com/wadl/2010/07/" xmlns="http://wadl.dev.java.net/2009/02" xsi:schemaLocation="http://wadl.dev.java.net/2009/02 http://apigee.com/schemas/wadl-schema.xsd http://api.apigee.com/wadl/2010/07/ http://apigee.com/schemas/apigee-wadl-extensions.xsd">' in result, result

    def test_generate_with_resource(self):
        api = APISpecification(version='v1', base_url='http://api.globo.com')
        api.add_resource(
            Resource('comments',
                paths=[
                    Path('/comments', methods=[Method('GET')])
                ]))
        result = self.gen(api)
        doc = ElementTree.fromstring(result)
        assert doc.tag.endswith('application')
        resources = doc.getchildren()[0]
        assert resources.tag.endswith('resources')
        assert resources.get('base') == 'http://api.globo.com/v1'
        resource = resources.getchildren()[0]
        assert resource.tag.endswith('resource')
        assert resource.get('path') == '/comments'
        method = resource.getchildren()[0]
        assert method.tag.endswith('method')
        assert method.get('name') == 'GET'

    def test_genetate_with_more_than_one_resource(self):
        api = APISpecification(version='v1', base_url='http://api.globo.com')
        api.add_resource(Resource('dogs',
            paths=[
                Path('/dogs', methods=[
                    Method('PUT')])]))
        api.add_resource(Resource('cats',
            paths=[
                Path('/cats', methods=[
                    Method('PUT')])]))
        result = self.gen(api)
        doc = ElementTree.fromstring(result)
        assert doc.tag.endswith('application')
        resource = doc.getchildren()[0]
        resources = resource.getchildren()
        assert len(resources) == 2
        assert resources[0].tag.endswith('resource')
        assert resources[0].get('path') == '/dogs'
        method = resources[0].getchildren()[0]
        assert method.tag.endswith('method')
        assert method.get('name') == 'PUT'
        assert resources[1].tag.endswith('resource')
        assert resources[1].get('path') == '/cats'
        method = resources[1].getchildren()[0]
        assert method.tag.endswith('method')
        assert method.get('name') == 'PUT'

    def test_generate_with_params(self):
        api = APISpecification(version='v1', base_url='http://api.globo.com')
        api.add_resource(Resource('dogs', 
            paths=[
                Path('/dogs/{key}',
                    params=[
                        Param('key')
                    ],
                    methods=[
                        Method('POST'),
                        Method('GET')
                    ]
                ),
            ])
        )
        result = self.gen(api)
        doc = ElementTree.fromstring(result)
        resources = doc.getchildren()[0]
        resource = resources.getchildren()[0]
        param = resource.getchildren()[0]
        assert param.tag.endswith('param')
        assert param.get('name') == 'key'
        assert param.get('required') == 'true'
        assert param.get('type') == 'xsd:string'
        assert param.get('style') == 'template'
        method_1 = resource.getchildren()[1]
        assert method_1.tag.endswith('method')
        assert method_1.get('name') == 'POST'
        method_2 = resource.getchildren()[2]
        assert method_2.tag.endswith('method')
        assert method_2.get('name') == 'GET'
