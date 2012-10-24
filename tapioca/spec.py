import re

from json import dumps
from tapioca.visitor import SimpleVisitor


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
        self.complete_url = '{s.base_url}/{s.version}'.format(s=self)
        self.resources = []

    def add_resource(self, resource):
        self.resources.append(resource)

class Path(NamedItem):
    def __init__(self, name=None, params=[], methods=[], *args, **kwargs):
        super(Path, self).__init__(name, *args, **kwargs)
        self.params = params
        self.methods = methods


class Resource(NamedItem):
    def __init__(self, name=None, paths=None, *args, **kwargs):
        super(Resource, self).__init__(name, *args, **kwargs)
        if paths:
            self.paths = paths
        else:
            self.paths = []

    def add_path(self, path):
        self.paths.append(path)


class Param(NamedItem):
    def __init__(self, name=None, default_value=None, required=True,
            options=[], *args, **kwargs):
        super(Param, self).__init__(name, *args, **kwargs)
        self.default_value = default_value
        self.required = required
        self.options = options


class Method(NamedItem):
    def __init__(self, name=None, errors=[], *args, **kwargs):
        super(Method, self).__init__(name, *args, **kwargs)
        self.errors = errors


class APIError(SpecItem):
    def __init__(self, code=None, *args, **kwargs):
        super(APIError, self).__init__(*args, **kwargs)
        self.code = code


class DocumentationHelpers(object):

    def slugify_method_with_path(self, method, path):
        normalized = re.sub('[/\.{}]', '_', path)
        return '{0}{1}'.format(method, normalized).lower()


class SwaggerSpecification(SimpleVisitor, DocumentationHelpers):

    def __init__(self, spec):
        self.spec = spec
        self.resource_name = None

    def generate(self, generate_for_resource=None):
        if generate_for_resource:
            self.resource_name = generate_for_resource
        return dumps(self.visit(self.spec))

    def visit_apispecification(self, node):
        root = {
            'apiVersion': node.version,
            'swaggerVersion': '1.1',
            'basePath': node.complete_url,
            'models': []
        }
        if self.resource_name:
            root['resourcePath'] = '/{0}'.format(self.resource_name)
            for resource in node.resources:
                if resource.name == self.resource_name:
                    root['apis'] = self.visit(resource.paths)
        else:
            root['apis'] = self.visit(node.resources)
        return root

    def visit_resource(self, node):
        return {
            'path': '/discovery/{node.name}.swagger'.format(node=node),
            'description': ''
        }

    def visit_path(self, node):
        self.current_path = node.name
        self.current_params = node.params
        return {
            'path': node.name,
            'description': '',
            'operations': self.visit(node.methods)
        }

    def visit_method(self, node):
        return {
            'httpMethod': node.name,
            'nickname': self.slugify_method_with_path(node.name, self.current_path),
            'parameters': self.visit(self.current_params),
            'errorResponses': [],
            'summary': '',
            'notes': '',
        }

    def visit_param(self, node):
        return {
            'paramType': 'path',
            'name': node.name,
            'description': '',
            'dataType': 'String',
            'required': node.required,
            'allowMultiple': False,
        }


class WADLSpecification(SimpleVisitor, DocumentationHelpers):

    def __init__(self, spec):
        self.spec = spec
        self.output = []

    def generate(self):
        self.visit(self.spec)
        return ''.join(self.output)

    def visit_apispecification(self, node):
        self.output.append('<application xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:apigee="http://api.apigee.com/wadl/2010/07/" xmlns="http://wadl.dev.java.net/2009/02" xsi:schemaLocation="http://wadl.dev.java.net/2009/02 http://apigee.com/schemas/wadl-schema.xsd http://api.apigee.com/wadl/2010/07/ http://apigee.com/schemas/apigee-wadl-extensions.xsd">')
        self.output.append('<resources base="{node.complete_url}">'
                .format(node=node))
        self.visit(node.resources)
        self.output.append('</resources>')
        self.output.append('</application>')

    def visit_resource(self, node):
        self.visit(node.paths)

    def visit_path(self, node):
        self.current_resource = node
        self.output.append('<resource path="{node.name}">'.format(node=node))
        self.visit(node.params)
        self.visit(node.methods)
        self.output.append('</resource>')

    def visit_method(self, node):
        self.output.append('<method id="{slug}" name="{node.name}">'.format(node=node, slug=self.slugify_method_with_path(node.name, self.current_resource.name)))
        if node.description:
            self.output.append('<doc><![CDATA[{}]]></doc>'.format(node.description))
        self.output.append('</method>')

    def visit_param(self, node):
        self.output.append('<param name="{node.name}" required="true" type="xsd:string" style="template">'.format(node=node))
        self.output.append('</param>')
