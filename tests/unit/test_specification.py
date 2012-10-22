from unittest import TestCase

from tapioca.spec import APISpecification, Path, Param, Resource, \
        Method, APIError


class SpecificationTestCase(TestCase):

    def test_create_spec(self):
        spec = APISpecification(version='v1', base_url='http://api.glb.com')
        assert spec.version == 'v1'
        assert spec.base_url == 'http://api.glb.com'
        assert spec.complete_url == 'http://api.glb.com/v1'
        assert spec.resources == []

    def test_create_path(self):
        path = Path('/comments')
        assert path.name == '/comments'
        assert path.params == []
        assert path.methods == []
        assert path.description == None

    def test_create_param(self):
        param = Param('key', default_value='value', required=True, options=[])
        assert param.name == 'key'
        assert param.default_value == 'value'
        assert param.required == True
        assert param.options == []
        assert param.description == None

    def test_create_resource(self):
        resource = Resource('comments', description='')
        assert resource.name == 'comments'
        assert resource.description == ''
        assert resource.paths == []

    def test_create_method(self):
        method = Method('POST', errors=[])
        assert method.name == 'POST'
        assert method.errors == []
        assert method.description == None

    def test_create_api_error(self):
        api_error = APIError(code=404, description='')
        assert api_error.code == 404
        assert api_error.description == ''

    def test_param_defaults(self):
        param = Param('foobar')
        assert param.name == 'foobar'
        assert param.required == True
        assert param.default_value == None
        assert param.options == []
        assert param.description == None

    def test_possible_add_resource(self):
        spec = APISpecification(version='v1', base_url='http://api.glb.com')
        resource = Resource('comments')
        resource.add_path(Path('/comments'))
        spec.add_resource(resource)
        assert len(spec.resources) == 1
        assert len(resource.paths) == 1
        assert resource.name == 'comments'
        assert resource.paths[0].name == '/comments'

    def test_possible_specify_simple_api(self):
        api = APISpecification(version='', base_url='')
        api.add_resource(Resource('comments',
            paths=[
                Path('/comments.{key}',
                    params=[
                        Param('key', default_value='json', required=False,
                            options=[
                                'json',
                                'js',
                                'xml'
                        ]),
                    ],
                    methods=[
                        Method('GET', errors=[
                            APIError(code=301, description=''),
                            APIError(code=404, description='')
                        ]),
                        Method('POST', errors=[
                            APIError(code=301, description=''),
                            APIError(code=404, description='')
                        ]),
                    ]
                ),
            ]
        ))
        resource = api.resources[0]
        assert resource.paths[0].name == '/comments.{key}'
        assert resource.paths[0].params[0].name == 'key'
        assert resource.paths[0].params[0].default_value == 'json'
        assert resource.paths[0].params[0].required == False
        assert resource.paths[0].params[0].options == ['json', 'js', 'xml']
        assert resource.paths[0].methods[0].name == 'GET'
        assert resource.paths[0].methods[1].name == 'POST'
