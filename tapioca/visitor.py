#!/usr/bin/env python
# -*- coding: utf-8 -*-


class SimpleVisitor(object):

    def visit(self, node):
        class_name = node.__class__.__name__
        visitor_method_name = 'visit_%s' % class_name.lower()
        return getattr(self, visitor_method_name)(node)
