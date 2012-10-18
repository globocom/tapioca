#!/usr/bin/env python
# -*- coding: utf-8 -*-


class SpecItem(object):
    def __init__(self, description=None, *args, **kwargs):
        self.description = description


class NamedItem(SpecItem):
    def __init__(self, name=None, *args, **kwargs):
        super(NamedItem, self).__init__(*args, **kwargs)
        self.name = name


class APISpecification(SpecItem):
    def __init__(self, version=None, base_url=None):
        self.version = version
        self.base_url = base_url
        self.complete_url = '%s/%s' % (self.base_url, self.version)
        self.paths = []

    def add_path(self, path):
        self.paths.append(path)


class Path(NamedItem):
    def __init__(self, name=None, params=None, methods=None, *args, **kwargs):
        super(Path, self).__init__(name, *args, **kwargs)
        self.params = params
        self.methods = methods


class Param(NamedItem):
    def __init__(self, name=None, default_value=None, required=False, 
            options=None, *args, **kwargs):
        super(Param, self).__init__(name, *args, **kwargs)
        self.default_value = default_value
        self.required = required
        self.options = options


class Method(NamedItem):
    def __init__(self, name=None, errors=None, *args, **kwargs):
        super(Method, self).__init__(name, *args, **kwargs)
        self.errors = errors


class APIError(SpecItem):
    def __init__(self, code=None, *args, **kwargs):
        super(APIError, self).__init__(*args, **kwargs)
        self.code = code
