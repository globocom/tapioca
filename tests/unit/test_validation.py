import json
from unittest import TestCase

from schema import SchemaError, Use, And

from tapioca.request import RequestSchema, SchemaNotDefined, \
        InvalidSchemaDefinition


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
                'age': (Use(int), 'The age of user'),
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
