import json
from unittest import TestCase

from schema import SchemaError, Use, And

from tapioca.request import RequestSchema, \
        InvalidSchemaDefinition, validate, optional


class RequestSchemaTestCase(TestCase):

    def test_url_should_be_a_dict(self):

        class R(RequestSchema):
            url = None

        self.assertRaises(InvalidSchemaDefinition, R)

    def test_params_should_be_a_dict(self):

        class R(RequestSchema):
            querystring = []

        self.assertRaises(InvalidSchemaDefinition, R)

    def test_validate_url_params_with_no_documentation(self):

        class R(RequestSchema):
            url = {
                'key': int
            }

        assert R().validate_url({'key': 1}) == {'key': 1}
        params = R().url_params()
        assert params[0].name == 'key'
        assert params[0].description == ''

    def test_validate_url_params_with_documentation(self):

        class R(RequestSchema):
            url = {
                'key': (int, 'This is an unique key')
            }

        assert R().validate_url({'key': 1}) == {'key': 1}
        params = R().url_params()
        assert params[0].name == 'key'
        assert params[0].description == 'This is an unique key'

    def test_body_schema_without_documentation(self):

        class R(RequestSchema):
            body = int

        assert R().validate_body(1) == 1
        assert R().describe_body == ''

    def test_body_schema_with_documentation(self):

        class R(RequestSchema):
            body = (And(Use(json.loads), {'name': unicode}), 'This is a description')

        assert R().validate_body('{"name": "Rafael Caricio"}') == {
                'name': 'Rafael Caricio'}
        assert R().describe_body == 'This is a description'

    def test_validate_more_than_one_key(self):

        class R(RequestSchema):
            querystring = {
                'name': (And(str, Use(lambda v:v.lower())), 'The name of user'),
                optional('age'): (Use(int), 'The age of user'),
                'year': And(int, lambda v: 1900 < v < 2012)
            }

        assert R().validate_querystring({'name': 'Rafael', 'age': '26', 'year': 2010}) == {
                'name': 'rafael', 'age': 26, 'year': 2010}
        params = R().querystring_params()
        assert len(params) == 3
        for param in params:
            if param.name == 'name':
                assert param.description == 'The name of user'
            elif param.name == 'age':
                assert param.description == 'The age of user'
            elif param.name == 'year':
                assert param.description == ''

    def test_schemas_in_constructor_of_request_schema(self):
        r = RequestSchema(url={'param': Use(int)})
        assert r.validate_url({'param': '123'}) == {'param': 123}
        params = r.url_params()
        assert params[0].name == 'param'
        assert params[0].description == ''

    def test_using_default_value_of_optional_param(self):
        r = RequestSchema(querystring={optional('param', 1): Use(int)})
        assert r.validate_querystring({}) == {'param': 1}

    def test_using_default_value_that_is_falsely_evaluated(self):
        r = RequestSchema(querystring={optional('param', 0): Use(int)})
        assert r.validate_querystring({}) == {'param': 0}

    def test_optional_without_default_value(self):
        r = RequestSchema(querystring={optional('param'): Use(int)})
        assert r.validate_querystring({}) == {}

    def test_default_value_is_the_final_value_to_be_used(self):
        r = RequestSchema(querystring={optional('param', 'blank'): Use(int)})
        assert r.validate_querystring({}) == {'param': 'blank'}


class ValidationDecoratorTestCase(TestCase):

    def test_has_values_attribute(self):

        class FakeHandler(object):

            @validate(url={})
            def get(self, argument):
                return self

        assert FakeHandler().get(None).values == {}

    def test_validate_arguments_in_url(self):

        class FakeHandler(object):

            @validate(url={'key': Use(int)})
            def get(self, key=None):
                return self

        assert FakeHandler().get(key='10').values['url'].get('key') == 10

    def test_validate_querystring_params(self):

        querystring = {
            'name': 'rafael caricio',
            'age': '26',
            'undefined_param': 'hello'
        }

        class FakeHandler(object):

            def get_argument(self, name, default=None):
                return querystring.get(name)

            @validate(querystring={'name': str, 'age': Use(int)})
            def get(self):
                return self

        assert FakeHandler().get().values['querystring'] == {
            'name': 'rafael caricio',
            'age': 26
        }

    def test_validate_body(self):

        class FakeRequest(object):
            body = '{"nome": 1}'

        class FakeHandler(object):

            def __init__(self):
                self.request = FakeRequest()

            @validate(body=And(Use(json.loads), {unicode: Use(int)}))
            def post(self):
                return self

        assert FakeHandler().post().values['body'] == {'nome': 1}

    def test_use_object_in_validate_decorator(self):

        class ParamDefinition(RequestSchema):
            querystring = {
                'name': str
            }

        class FakeHandler(object):

            def get_argument(self, name, **kw):
                return 'foo'

            @validate(ParamDefinition)
            def get(self):
                return self

        assert FakeHandler().get().values['querystring']['name'] == 'foo'
