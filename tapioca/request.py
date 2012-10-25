from schema import Schema


class RequestSchema(object):

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
            descriptions[key] = ''
            if isinstance(rule, tuple):
                rule, descriptions[key] = rule
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

