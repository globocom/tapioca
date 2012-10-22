

class SimpleVisitor(object):

    def visit(self, node):
        class_name = node.__class__.__name__
        visitor_method_name = 'visit_{0}'.format(class_name.lower())
        return getattr(self, visitor_method_name)(node)

    def visit_list(self, node):
        result = []
        for value in node:
            result.append(self.visit(value))
        return result
