from tapioca.spec import APISpecification, Resource, Path, Method, Param


class Metadata(object):

    def __init__(self, version=None, base_url=None):
        self.spec = APISpecification(version=version, base_url=base_url)

    def add(self, path, handler):
        resource = Resource(path)
        basic_methods = list(self.get_basic_methods(handler))
        if basic_methods:
            resource.add_path(
                    Path('/{0}'.format(path), methods=basic_methods))
            resource.add_path(
                    Path('/{0}.{{type}}'.format(path),
                        params=[Param('type', style='url')],
                        methods=basic_methods))

        instance_methods = list(self.get_instance_methods(handler))
        if instance_methods:
            resource.add_path(
                    Path('/{0}/{{key}}'.format(path),
                        params=[Param('key', style='url')],
                        methods=instance_methods))
            resource.add_path(
                    Path('/{0}/{{key}}.{{type}}'.format(path),
                        params=[
                            Param('key', style='url'),
                            Param('type', style='url')
                        ],
                        methods=instance_methods))
        self.spec.add_resource(resource)

    def get_basic_methods(self, handler):
        return self.introspect_methods(
                GET=handler.get_collection,
                POST=handler.create_model)

    def is_overridden(self, method):
        return not hasattr(method, 'original')

    def get_instance_methods(self, handler):
        return self.introspect_methods(
                GET=handler.get_model,
                PUT=handler.update_model,
                DELETE=handler.delete_model)

    def introspect_methods(self, **mapping):
        for method_type, implementation in mapping.items():
            if self.is_overridden(implementation):
                params = self.introspect_params(implementation)
                yield Method(method_type,
                        params=params, description=implementation.__doc__)

    def introspect_params(self, method):
        params = []
        if hasattr(method, 'request_schema'):
            request_schema = method.request_schema
            if hasattr(request_schema, 'querystring'):
                for param in request_schema.querystring_params():
                    params.append(
                        Param(
                            param.name,
                            required=not param.is_optional,
                            style='querystring',
                            description=param.description
                        )
                    )
        return params
