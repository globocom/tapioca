import json
import logging

import tornado.web
import mimeparse

from tapioca.serializers import JsonEncoder, JsonpEncoder, HtmlEncoder, \
        SwaggerEncoder, WADLEncoder
from tapioca.metadata import Metadata


SIMPLE_POST_MIMETYPE = 'application/x-www-form-urlencoded'


class TornadoRESTful(object):

    def __init__(self, version=None, base_url=None, discovery=False,
            cross_origin_enabled=False):
        self.metadata = Metadata(version=version, base_url=base_url)
        self.handlers = []
        self.discovery = discovery
        self.cross_origin_enabled = cross_origin_enabled

    def add_resource(self, path, handler, *args, **kw):
        normalized_path = path.rstrip('/').lstrip('/')
        handler.cross_origin_enabled = self.cross_origin_enabled
        self.add_url_mapping(normalized_path, handler)
        self.metadata.add(normalized_path, handler)

    def add_url_mapping(self, normalized_path, handler):
        self.handlers.append(('/{0}/?'.format(normalized_path), handler))
        self.handlers.append(('/{0}\.(?P<force_return_type>\w+)'
                .format(normalized_path), handler))
        self.handlers.append(('/{0}/(?P<key>[^.]+)\.(?P<force_return_type>\w+)'
                .format(normalized_path), handler))
        self.handlers.append(('/{0}/(?P<key>.+)/?'
                .format(normalized_path), handler))

    def get_url_mapping(self):
        url_mapping = self.handlers
        if self.discovery:
            url_mapping = url_mapping + [
            ('/discovery\.(?P<force_return_type>\w+)',
                DiscoveryHandler, {'api_spec': self.metadata.spec}),
            ('/discovery/(?P<resource_name>[\w_/]+)\.(?P<force_return_type>\w+)',
                DiscoveryHandler, {'api_spec': self.metadata.spec})
            ]
        return url_mapping

    def get_spec(self):
        return self.metadata.spec


class ResourceDoesNotExist(Exception):
    pass


def mark_as_original_method(method):
    method.original = True
    return method


class ResourceHandler(tornado.web.RequestHandler):
    encoders = (JsonEncoder, JsonpEncoder, HtmlEncoder,)

    def get_encoders(self):
        return self.encoders

    def get_mimetypes_priority(self):
        encoders_mimetypes = [encoder.mimetype \
                for encoder in self.get_encoders()]
        encoders_mimetypes.reverse()
        return encoders_mimetypes

    def get_content_type_based_on(self, header_key):
        mimetypes = self.get_mimetypes_priority()
        default_encoding = mimetypes[-1]
        content_types_by_client = self.request.headers.get(
                header_key, default_encoding)
        if content_types_by_client == SIMPLE_POST_MIMETYPE:
            content_types_by_client = default_encoding
        content_type = mimeparse.best_match(mimetypes, content_types_by_client)
        return content_type

    def get_encoder_for(self, content_type):
        encoders = self.get_encoders()
        encoder_class = encoders[0]
        for encoder in encoders:
            if content_type == encoder.mimetype:
                encoder_class = encoder
        return encoder_class(self)

    def respond_with(self, data, force_type=None):
        if force_type is None:
            respond_as = self.get_content_type_based_on('Accept')
        else:
            respond_as = self.get_content_type_for_extension(force_type)

        self.set_cross_origin()
        self.set_header('Content-Type', respond_as)
        self.write(self.get_encoder_for(respond_as).encode(data))
        self.finish()

    def set_cross_origin(self):
        if hasattr(self, 'cross_origin_enabled') and self.cross_origin_enabled:
            self.set_header('Access-Control-Allow-Origin', '*')

    def get_content_type_for_extension(self, extension):
        for encoder in self.get_encoders():
            if encoder.extension == extension:
                return encoder.mimetype
        raise tornado.web.HTTPError(404)

    def load_data(self):
        """ load data based on Content-Type request header """
        content_type = self.get_content_type_based_on('Content-Type')
        data_as_string = self.request.body
        data = self.get_encoder_for(content_type).decode(data_as_string)
        return data

    # Generic API HTTP Verbs

    @tornado.web.asynchronous
    def get(self, key=None, force_return_type=None, *args, **kwargs):
        """ return the collection or a model """
        def _callback(data):
            self.respond_with(data, force_return_type)

        if key is None:
            self.get_collection(_callback, *args, **kwargs)
        else:
            try:
                self.get_model(key, _callback, *args, **kwargs)
            except ResourceDoesNotExist:
                raise tornado.web.HTTPError(404)

    @tornado.web.asynchronous
    def post(self, *args, **kwargs):
        """ create a model """
        def _callback(content=None, *args, **kwargs):
            self.set_status(201)
            self.set_cross_origin()
            self.set_header(
                'Location', '{r.protocol}://{r.host}{r.path}/{id:d}'.format(
                    r=self.request, id=content['id']))
            self.finish()

        self.create_model(_callback, *args, **kwargs)

    @tornado.web.asynchronous
    def put(self, key=None, *args, **kwargs):
        """ update a model """
        try:
            self.set_status(204)
            self.set_cross_origin()
            self.set_header('Location', '{r.protocol}://{r.host}{r.path}'
                    .format(r=self.request))
            self.update_model(key, self.finish_callback, *args, **kwargs)
        except ResourceDoesNotExist:
            raise tornado.web.HTTPError(404)

    @tornado.web.asynchronous
    def delete(self, key=None, *args):
        """ delete a model """
        try:
            self.delete_model(key, self.finish_callback, *args)
            self.set_cross_origin()
        except ResourceDoesNotExist:
            raise tornado.web.HTTPError(404)

    def finish_callback(self, *args, **kw):
        self.finish()

    # Extension points
    @mark_as_original_method
    def create_model(self, callback, *args, **kwargs):
        """ create model and return a dictionary of updated attributes """
        raise tornado.web.HTTPError(404)

    @mark_as_original_method
    def get_collection(self, callback, *args, **kwargs):
        """ return the collection """
        raise tornado.web.HTTPError(404)

    @mark_as_original_method
    def get_model(self, oid, callback, *args, **kwargs):
        """ return a model, return None to indicate not found """
        raise tornado.web.HTTPError(404)

    @mark_as_original_method
    def update_model(self, oid, callback, *args, **kwargs):
        """ update a model """
        raise tornado.web.HTTPError(404)

    @mark_as_original_method
    def delete_model(self, oid, callback, *args, **kwargs):
        """ delete a model """
        raise tornado.web.HTTPError(404)


class DiscoveryHandler(ResourceHandler):
    encoders = (SwaggerEncoder, WADLEncoder,)

    def __init__(self, *args, **kwargs):
        self.api_spec = kwargs['api_spec']
        del kwargs['api_spec']
        super(DiscoveryHandler, self).__init__(*args, **kwargs)

    def get_collection(self, callback, resource_name=None, *args):
        self.set_header('Access-Control-Allow-Origin', '*')
        callback({
            'spec': self.api_spec,
            'resource': resource_name
        })
