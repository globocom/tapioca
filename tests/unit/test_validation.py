import json
from unittest import TestCase

from schema import SchemaError, Use, And

from tapioca.request import RequestSchema, SchemaNotDefined, \
        InvalidSchemaDefinition, validate, optional


class RequestSchemaTestCase(TestCase):

    def test_should_not_be_possible_to_validate_url(self):
        r = RequestSchema()
        self.assertRaises(SchemaNotDefined, r.validate_url, '')

    def test_should_not_be_possible_to_validate_querystring(self):
        r = RequestSchema()
        self.assertRaises(SchemaNotDefined, r.validate_querystring, '')

    def test_should_not_be_possible_to_validate_body(self):
        r = RequestSchema()
        self.assertRaises(SchemaNotDefined, r.validate_body, '')

    def test_url_should_be_a_dict(self):

        class R(RequestSchema):
            url = None

        self.assertRaises(InvalidSchemaDefinition, R().validate_url, '')

    def test_params_should_be_a_dict(self):

        class R(RequestSchema):
            querystring = []

        self.assertRaises(InvalidSchemaDefinition, R().validate_querystring, '')

    def test_validate_url_params_with_no_documentation(self):

        class R(RequestSchema):
            url = {
                'key': int
            }

        assert R().validate_url({'key': 1}) == {'key': 1}
        assert R().describe_url['key'] == ''

    def test_validate_url_params_with_documentation(self):

        class R(RequestSchema):
            url = {
                'key': (int, 'This is an unique key')
            }

        assert R().validate_url({'key': 1}) == {'key': 1}
        assert R().describe_url['key'] == 'This is an unique key'

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
        assert R().describe_querystring['name'] == 'The name of user'
        assert R().describe_querystring['age'] == 'The age of user'
        assert R().describe_querystring['year'] == ''

    def test_schemas_in_constructor_of_request_schema(self):
        r = RequestSchema(url={'param': Use(int)})
        assert r.validate_url({'param': '123'}) == {'param': 123}
        assert r.describe_url['param'] == ''

    def test_using_default_value_of_optional_param(self):
        r = RequestSchema(url={optional('param', 1): Use(int)})
        assert r.validate_url({}) == {'param': 1}

    def test_optional_without_default_value(self):
        r = RequestSchema(url={optional('param'): Use(int)})
        assert r.validate_url({}) == {}


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
