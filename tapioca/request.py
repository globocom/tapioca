import functools

import tornado.web
from schema import Schema, Optional, SchemaError


class RequestSchema(object):

    def __init__(self, **defs):
        if defs:
            self.__dict__.update(defs)

    @property
    def describe_url(self):
        return self.descriptions('url')

    @property
    def describe_querystring(self):
        return self.descriptions('querystring')

    @property
    def describe_body(self):
        _, description = self.process_body()
        return description

    def validate_url(self, value):
        return self.validate('url', value)

    def validate_querystring(self, value):
        return self.validate('querystring', value)

    def validate_body(self, value):
        pattern, _ = self.process_body()
        return Schema(pattern).validate(value)

    def process_body(self):
        attr = self.get_definition_attr('body')
        pattern = attr
        description = ''
        if isinstance(attr, tuple):
            pattern, description = attr
        return pattern, description

    def descriptions(self, attr_name):
        _, descriptions = self.process_definition(attr_name)
        return descriptions

    def validate(self, attr_name, value):
        patterns, _ = self.process_definition(attr_name)
        return Schema(patterns).validate(value)

    def process_definition(self, attr_name):
        attr = self.get_definition_attr(attr_name)
        if not isinstance(attr, dict):
            raise InvalidSchemaDefinition('Schema definition need to be a dict')
        patterns = {}
        descriptions = {}
        for key, rule in attr.items():
            key_name = key
            if isinstance(key, Optional):
                key_name = key._schema
            descriptions[key_name] = ''
            if isinstance(rule, tuple):
                rule, descriptions[key_name] = rule
            patterns[key] = rule
        return patterns, descriptions

    def get_definition_attr(self, attr_name):
        if not hasattr(self, attr_name):
            raise SchemaNotDefined('Is necessary to define a shema for {}'\
                    .format(attr_name))
        return getattr(self, attr_name)


class SchemaNotDefined(Exception):
    pass


class InvalidSchemaDefinition(Exception):
    pass


def validate(**validation_schema):
    def add_validation(func):
        func.request_schema = RequestSchema(**validation_schema)
        @functools.wraps(func)
        def wrapper(self, *args, **url_params):
            self.values = {}

            try:
                if url_params:
                    self.values['url'] = func.request_schema.validate_url(url_params)

                try:
                    request_values = {}
                    for key in func.request_schema.describe_querystring:
                        value = self.get_argument(key, default=None)
                        if value != None:
                            request_values[key] = self.get_argument(key)
                    self.values['querystring'] = func.request_schema.validate_querystring(request_values)
                except SchemaNotDefined:
                    pass

                if hasattr(func.request_schema, 'body'):
                    self.values['body'] = func.request_schema.validate_body(self.request.body)
            except SchemaError:
                raise tornado.web.HTTPError(400)

            return func(self, *args, **url_params)
        return wrapper
    return add_validation
