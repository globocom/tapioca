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

    def querystring_optionals(self):
        _, _, optionals = self.process_definition('querystring')
        return optionals

    def process_body(self):
        attr = self.get_definition_attr('body')
        pattern = attr
        description = ''
        if isinstance(attr, tuple):
            pattern, description = attr
        return pattern, description

    def descriptions(self, attr_name):
        _, descriptions, _ = self.process_definition(attr_name)
        return descriptions

    def validate(self, attr_name, value):
        patterns, _, _ = self.process_definition(attr_name)
        return Schema(patterns).validate(value)

    def process_definition(self, attr_name):
        attr = self.get_definition_attr(attr_name)
        if not isinstance(attr, dict):
            raise InvalidSchemaDefinition('Schema definition need to be a dict')
        patterns = {}
        descriptions = {}
        optionals = []
        for key, rule in attr.items():
            key_name = key
            if isinstance(key, Optional):
                key_name = key._schema
                optionals.append(key_name)
            descriptions[key_name] = ''
            if isinstance(rule, tuple):
                rule, descriptions[key_name] = rule
            patterns[key] = rule
        return patterns, descriptions, optionals

    def get_definition_attr(self, attr_name):
        if not hasattr(self, attr_name):
            raise SchemaNotDefined('Is necessary to define a shema for {}'\
                    .format(attr_name))
        return getattr(self, attr_name)


class SchemaNotDefined(Exception):
    pass


class InvalidSchemaDefinition(Exception):
    pass


class ValidateDecorator(object):

    def __init__(self, validation_object=None, **validation_schema):
        if validation_object:
            self.request_schema = validation_object()
        else:
            self.request_schema = RequestSchema(**validation_schema)
        self.handler = None

    def __call__(self, func):
        func.request_schema = self.request_schema

        @functools.wraps(func)
        def wrapper(handler, *args, **url_params):
            self.handler = handler
            self.handler.values = {}

            try:
                self.process_params_in_url(url_params)
                self.process_params_in_querystring()
                self.process_body()
            except SchemaError:
                raise tornado.web.HTTPError(400)

            return func(handler, *args, **url_params)
        return wrapper

    def process_params_in_url(self, url_params):
        if url_params:
            parsed_values = self.request_schema.validate_url(url_params)
            self.handler.values['url'] = parsed_values

    def process_params_in_querystring(self):
        if hasattr(self.request_schema, 'querystring'):
            request_values = {}
            for key in self.request_schema.describe_querystring:
                value = self.handler.get_argument(key, default=None)
                if value != None:
                    request_values[key] = value
            parsed_values = self.request_schema.validate_querystring(
                    request_values)
            self.handler.values['querystring'] = parsed_values

    def process_body(self):
        if hasattr(self.request_schema, 'body'):
            parsed_values = self.request_schema.validate_body(
                    self.handler.request.body)
            self.handler.values['body'] = parsed_values


validate = ValidateDecorator
