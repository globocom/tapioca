#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging

import tornado.web
import mimeparse


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

    def encode(self, data):
        return json.dumps(data)

    def decode(self, data):
        return json.loads(data)


class ApiResourceHandler(tornado.web.RequestHandler):

    def get_encoders(self):
        return {
            'application/json': JsonEncoder
        }

    def get_content_type_based_on(self, header_key):
        content_types_by_client = self.request.headers.get(
                header_key, 'application/json')
        if content_types_by_client == 'application/x-www-form-urlencoded':
            content_types_by_client = 'application/json'
        content_type = mimeparse.best_match(
                self.get_encoders().keys(), content_types_by_client)
        return content_type

    def get_encoder_for(self, content_type):
        encoder_class = self.get_encoders()[content_type]
        return encoder_class()

    def respond_with(self, data, force_type=None):
        if force_type is None:
            respond_as = self.get_content_type_based_on('Accept')
        else:
            respond_as = force_type

        self.set_header('Content-Type', respond_as)
        self.write(self.get_encoder_for(respond_as).encode(data))

    def load_data(self):
        content_type = self.get_content_type_based_on('Content-Type')
        data = self.get_encoder_for(content_type).decode(self.request.body)
        return data

    # Generic API HTTP Verbs

    def get(self, *args):
        """ return the collection or a model """
        if self.is_get_collection(*args):
            self.respond_with(self.get_collection(*args))
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

    def get_collection(self, *args):
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
