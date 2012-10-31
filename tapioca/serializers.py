import re
import json

from tapioca.spec import SwaggerSpecification, WADLSpecification


class Encoder(object):

    def __init__(self, handler):
        self.handler = handler


class JsonEncoder(Encoder):
    mimetype = 'application/json'
    extension = 'json'

    def encode(self, data):
        to_upper = lambda match: match.group(1).upper()
        return json.dumps(self.pass_through_all_values('_(.)', to_upper, data))

    def decode(self, data):
        data = json.loads(data)
        to_lower = lambda match: \
                '{0}_{1}'.format(match.group(1), match.group(2).lower())
        return self.pass_through_all_values('([a-z])([A-Z])', to_lower, data)

    def pass_through_all_values(self, pattern, function, data):
        if isinstance(data, dict):
            new_dict = {}
            for key, value in data.items():
                new_key = re.sub(pattern, function, key)
                new_dict[new_key] = self.pass_through_all_values(
                        pattern, function, value)
            return new_dict
        if isinstance(data, (list, tuple)):
            for i in range(len(data)):
                data[i] = self.pass_through_all_values(
                        pattern, function, data[i])
            return data
        return data


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


class SwaggerEncoder(JsonEncoder):
    extension = 'swagger'

    def encode(self, data):
        return SwaggerSpecification(data['spec']).generate(data['resource'])


class WADLEncoder(Encoder):
    mimetype = 'application/xml'
    extension = 'wadl'

    def encode(self, data):
        return WADLSpecification(data['spec']).generate()
