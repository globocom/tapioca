#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging

import tornado.web
import mimeparse

SIMPLE_POST_MIMETYPE = 'application/x-www-form-urlencoded'


class ApiManager(object):

    def __init__(self):
        self.handlers = []

    def add_resource_handler(self, path, handler, *args, **kw):
        normalized_path = path.rstrip('/').lstrip('/')
        self.handlers.append((r'/%s/?' % normalized_path, handler))
        self.handlers.append((r'/%s/(.+)/?' % normalized_path, handler))

    def build_handlers(self):
        return self.handlers


class ResourceDoesNotExist(Exception):
    pass


class JsonEncoder(object):
    mimetype = 'application/json'

    def __init__(self, handler):
        self.handler = handler

    def encode(self, data):
        return json.dumps(data)

    def decode(self, data):
        return json.loads(data)


class JsonpEncoder(JsonEncoder):
    mimetype = 'text/javascript'

    def encode(self, data):
        data = super(JsonpEncoder, self).encode(data)
        callback_name = self.handler.get_argument('callback', default=None)
        if callback_name:
            data = "%s(%s);" % (callback_name, data)
        return data


class ApiResourceHandler(tornado.web.RequestHandler):
    encoders = (JsonEncoder, JsonpEncoder,)

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
            respond_as = force_type

        self.set_header('Content-Type', respond_as)
        self.write(self.get_encoder_for(respond_as).encode(data))
        self.finish()

    def load_data(self):
        content_type = self.get_content_type_based_on('Content-Type')
        data = self.get_encoder_for(content_type).decode(self.request.body)
        return data

    # Generic API HTTP Verbs

    def get(self, *args):
        """ return the collection or a model """
        if self.is_get_collection(*args):
            self.get_collection(self.respond_with, *args)
        else:
            try:
                model = self.get_model(*args)
                self.respond_with(model)
            except ResourceDoesNotExist:
                raise tornado.web.HTTPError(404)

    def post(self, *args):
        """ create a model """
        resource = self.create_model(self.load_data(), *args)
        self.set_status(201)
        self.set_header('Location', '%s://%s%s/%d' % (self.request.protocol,
            self.request.host, self.request.path, resource['id']))

    def put(self, *args):
        """ update a model """
        try:
            self.update_model(self.load_data(), *args)
            self.set_status(204)
            self.set_header('Location', '%s://%s%s' % (self.request.protocol,
                self.request.host, self.request.path))
        except ResourceDoesNotExist:
            raise tornado.web.HTTPError(404)

    def delete(self, *args):
        """ delete a model """
        try:
            self.delete_model(*args)
        except ResourceDoesNotExist:
            self.set_status(404)

    # Extension points

    def is_get_collection(self, *args):
        """ return true if this get is for a collection """
        return len(args) == 0

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
