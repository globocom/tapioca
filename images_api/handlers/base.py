#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import logging

import tornado.web
import mimeparse

from images_api.handlers import BaseHandlerMixin


class ResourceDoesNotExist(Exception):
    pass


class BaseHandler(tornado.web.RequestHandler, BaseHandlerMixin):

    @property
    def config(self):
        return self.application.config


class JsonEncoder(object):

    def encode(self, data):
        return json.dumps(data)

    def decode(self, data):
        return json.loads(data)


class ApiResourceHandler(BaseHandler):

    def get_encoders(self):
        return {
            'application/json': JsonEncoder
        }

    def respond_with(self, data, force_type=None):
        if force_type is None:
            content_types_accepted_by_client = self.request.headers.get(
                    'Accept', 'application/json')
            respond_as = mimeparse.best_match(
                    self.get_encoders().keys(), content_types_accepted_by_client)
        else:
            respond_as = force_type

        self.set_header('Content-Type', respond_as)
        encoder_class = self.get_encoders()[respond_as]
        self.write(encoder_class().encode(data))

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
        content_types_accepted_by_client = self.request.headers.get('Content-Type', 'application/json')
        if content_types_accepted_by_client == 'application/x-www-form-urlencoded':
            content_types_accepted_by_client = 'application/json'
        content_type = mimeparse.best_match(
                self.get_encoders().keys(), content_types_accepted_by_client)
        encoder_class = self.get_encoders()[content_type]
        data = encoder_class().decode(self.request.body)

        resp = self.create_model(data, *args)
        self.set_status(201)
        self.respond_with(resp, force_type=content_type)

    def put(self, *args):
        """ update a model """
        content_types_accepted_by_client = self.request.headers.get('Content-Type', 'application/json')
        if content_types_accepted_by_client == 'application/x-www-form-urlencoded':
            content_types_accepted_by_client = 'application/json'
        content_type = mimeparse.best_match(
                self.get_encoders().keys(), content_types_accepted_by_client)
        encoder_class = self.get_encoders()[content_type]
        data = encoder_class().decode(self.request.body)

        try:
            self.update_model(data, *args)
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
