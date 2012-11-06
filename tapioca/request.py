import functools

import tornado.web
from schema import Schema, Optional, SchemaError


class RequestSchema(object):

    def __init__(self, **defs):
        if defs:
            self.__dict__.update(defs)

        self.querystring_processor = None
        if hasattr(self, 'querystring'):
            self.querystring_processor = QuerystringSchemaProcessor(
                    self.querystring)

        self.url_processor = None
        if hasattr(self, 'url'):
            self.url_processor = UrlSchemaProcessor(self.url)

    def validate_url(self, values):
        return self.url_processor.validate(values)

    def url_params(self):
        return self.url_processor.params

    def validate_querystring(self, values):
        return self.querystring_processor.validate(values)

    def querystring_params(self):
        return self.querystring_processor.params

    @property
    def describe_body(self):
        _, description = self.process_body()
        return description

    def validate_body(self, value):
        pattern, _ = self.process_body()
        return Schema(pattern).validate(value)

    def process_body(self):
        pattern = self.body
        description = ''
        if isinstance(self.body, tuple):
            pattern, description = self.body
        return pattern, description


class ParamSchema(object):
    def __init__(self, name, pattern, description, is_optional, default_value):
        self.name = name
        self.pattern = pattern
        self.description = description
        self.is_optional = is_optional
        self.default_value = default_value

    def validate(self, values):
        if not self.name in values:
            if self.is_optional:
                if self.default_value:
                    return self.default_value
            else:
                raise ParamRequiredError(self.name)
        else:
            value = values[self.name]
            try:
                return Schema(self.pattern).validate(value)
            except SchemaError:
                raise InvalidParamError(self.name)


class ParamSchemaProcessor(object):
    def __init__(self, definition):
        self.params = []
        self.definition = definition
        self.process_definition()

    def process_definition(self):
        if not isinstance(self.definition, dict):
            raise InvalidSchemaDefinition('Schema definition need to be a dict')
        for key, rule in self.definition.items():
            default_value = None
            is_optional = False
            key_name = key
            if isinstance(key, OptionalParameter):
                key_name = key._schema
                is_optional = True
                default_value = key.default_value
            description = ''
            if isinstance(rule, tuple):
                rule, description = rule
            self.params.append(ParamSchema(key_name, rule, description,
                is_optional, default_value))

    def validate(self, real_values):
        final_values = {}
        for param in self.params:
            result = param.validate(real_values)
            if result:
                final_values[param.name] = result
        return final_values


class QuerystringSchemaProcessor(ParamSchemaProcessor):
    pass


class UrlSchemaProcessor(ParamSchemaProcessor):
    pass


class InvalidSchemaDefinition(Exception):
    pass


class ParamError(Exception):
    def __init__(self, param):
        Exception.__init__(self)
        self.param = param


class ParamRequiredError(ParamError):
    def __init__(self, param):
        ParamError.__init__(self, param)
        self.message = 'The "{}" parameter is required.'.format(self.param)


class InvalidParamError(ParamError):
    def __init__(self, param):
        ParamError.__init__(self, param)
        self.message = 'The "{}" parameter value is not valid.'.format(
                self.param)


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
            except SchemaError as error:
                raise tornado.web.HTTPError(400)
            except ParamError as error:
                handler.set_status(400)
                handler.respond_with(self.format_error(error))
                return

            return func(handler, *args, **url_params)
        return wrapper

    def process_params_in_url(self, url_params):
        if url_params:
            parsed_values = self.request_schema.validate_url(url_params)
            self.handler.values['url'] = parsed_values

    def process_params_in_querystring(self):
        if hasattr(self.request_schema, 'querystring'):
            request_values = {}
            for param in self.request_schema.querystring_params():
                value = self.handler.get_argument(param.name, default=None)
                if value != None:
                    request_values[param.name] = value
            parsed_values = self.request_schema.validate_querystring(
                    request_values)
            self.handler.values['querystring'] = parsed_values

    def process_body(self):
        if hasattr(self.request_schema, 'body'):
            parsed_values = self.request_schema.validate_body(
                    self.handler.request.body)
            self.handler.values['body'] = parsed_values

    def format_error(self, error):
        return {'error': error.message}


class OptionalParameter(Optional):
    def __init__(self, name, default_value=None):
        Optional.__init__(self, name)
        self.default_value = default_value


validate = ValidateDecorator
optional = OptionalParameter
