#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging

import tornado.web
import mimeparse


SIMPLE_POST_MIMETYPE = 'application/x-www-form-urlencoded'


class TornadoRESTful(object):

    def __init__(self):
        self.handlers = []

    def add_resource(self, path, handler, *args, **kw):
        normalized_path = path.rstrip('/').lstrip('/')
        self.handlers.append((r'/%s/?' % normalized_path, handler))
        self.handlers.append((r'/%s\.(?P<force_return_type>\w+)'\
                % normalized_path, handler))
        self.handlers.append((r'/%s/(?P<key>[^.]+)\.(?P<force_return_type>\w+)'\
                % normalized_path, handler))
        self.handlers.append((r'/%s/(?P<key>.+)/?' % normalized_path, handler))

    def get_url_mapping(self):
        return self.handlers


class ResourceDoesNotExist(Exception):
    pass


class Encoder(object):

    def __init__(self, handler):
        self.handler = handler


class JsonEncoder(Encoder):
    mimetype = 'application/json'
    extension = 'json'

    def encode(self, data):
        return json.dumps(data)

    def decode(self, data):
        return json.loads(data)


class JsonpEncoder(JsonEncoder):
    mimetype = 'text/javascript'
    extension = 'js'
    default_callback_name = 'defaultCallback'

    def encode(self, data):
        data = super(JsonpEncoder, self).encode(data)
        callback_name = self.get_callback_name()
        return "%s(%s);" % (callback_name, data)

    def get_callback_name(self):
        callback_name = self.default_callback_name
        if hasattr(self.handler, 'default_callback_name'):
            callback_name = self.handler.default_callback_name
        return self.handler.get_argument('callback', default=callback_name)


class HtmlEncoder(Encoder):
    mimetype = 'text/html'
    extension = 'html'

    def encode(self, data):
        pprint_data = json.dumps(data, sort_keys=True, indent=4)
        return self.handler.render_string(
                'templates/tapioca/resource.html',
                    resource_content=pprint_data)


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

        self.set_header('Content-Type', respond_as)
        self.write(self.get_encoder_for(respond_as).encode(data))
        self.finish()

    def get_content_type_for_extension(self, extension):
        for encoder in self.get_encoders():
            if encoder.extension == extension:
                return encoder.mimetype
        raise tornado.web.HTTPError(404)

    def load_data(self):
        content_type = self.get_content_type_based_on('Content-Type')
        data = self.get_encoder_for(content_type).decode(self.request.body)
        return data

    # Generic API HTTP Verbs

    def get(self, key=None, force_return_type=None, *args):
        """ return the collection or a model """
        if key is None:
            def _callback(data):
                self.respond_with(data, force_return_type)
            self.get_collection(_callback, *args)
        else:
            try:
                model = self.get_model(key, *args)
                self.respond_with(model, force_return_type)
            except ResourceDoesNotExist:
                raise tornado.web.HTTPError(404)

    def post(self, *args):
        """ create a model """
        resource = self.create_model(self.load_data(), *args)
        self.set_status(201)
        self.set_header('Location', '%s://%s%s/%d' % (self.request.protocol,
            self.request.host, self.request.path, resource['id']))

    def put(self, key=None, *args):
        """ update a model """
        try:
            self.update_model(self.load_data(), key, *args)
            self.set_status(204)
            self.set_header('Location', '%s://%s%s' % (self.request.protocol,
                self.request.host, self.request.path))
        except ResourceDoesNotExist:
            raise tornado.web.HTTPError(404)

    def delete(self, key=None, *args):
        """ delete a model """
        try:
            self.delete_model(key, *args)
        except ResourceDoesNotExist:
            self.set_status(404)

    # Extension points

    def create_model(self, model, *args):
        """ create model and return a dictionary of updated attributes """
        raise tornado.web.HTTPError(404)

    def get_collection(self, callback, *args):
        """ return the collection """
        raise tornado.web.HTTPError(404)

    def get_model(self, *args):
        """ return a model, return None to indicate not found """
        raise tornado.web.HTTPError(404)

    def update_model(self, model, *args):
        """ update a model """
        raise tornado.web.HTTPError(404)

    def delete_model(self, *args):
        """ delete a model """
        raise tornado.web.HTTPError(404)
