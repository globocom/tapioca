# Tapioca [![build status](https://secure.travis-ci.org/globocom/tapioca.png)](http://travis-ci.org/globocom/tapioca)

Tapioca is a small and flexible micro-framework on top of Tornado.
It provides a simpler way to create RESTful API's.

## Why Tapioca?

Create APIs using Tornado is easy, but Tapioca makes it even easier.
Tapioca provides common behaviour to manage resources as close as possible
to the definition of your RESTful API. 

Tapioca also provides many different encoders enabling your resource 
to be easily serialized in different formats. 

It´s incredibly easy to respond in a format that your API clients can understand. 

Doesn't matter if they are a machine or a human being. 

Tapioca gives you an automatic console interface to your API. This way it can be used
as both the documentation and testing interface by your API clients.

## Usage

Here is a "Hello, world!" example API written using Tapioca:

```python

import tornado.ioloop
import tornado.web

from tapioca import TornadoRESTful, ResourceHandler

class HelloResource(ResourceHandler):

    def get_collection(self, callback):
        callback("Hello, world!")

api = TornadoRESTful(discovery=True)
api.add_resource('hello', HelloResource)
application = tornado.web.Application(
    api.get_url_mapping()
)

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()

```

This is the simplest usege of Tapioca. That provide the very basic features which is available to you.

### Handing content types

With the code above you running you can access the hello route of your
application.

```bash
$ curl -XGET -v -H "Accept: application/json" http://127.0.0.1:8888/hello
$ curl -XGET -v -H "Accept: text/javascript" http://127.0.0.1:8888/hello
$ curl -XGET -v -H "Accept: text/html" http://127.0.0.1:8888/hello
```

Or you can use extensions to force different content types.

```bash
$ curl -XGET -v http://127.0.0.1:8888/hello.json
$ curl -XGET -v http://127.0.0.1:8888/hello.js
$ curl -XGET -v http://127.0.0.1:8888/hello.html
```

Those are the default content types which Tapioca gives you.

### Parameters

All API's need to define parameters which users can query data or send 
other informations to the server. Tapioca provides a simple way to define 
and validate the data sent by your users. Those definitions will also be used later to
introspect your API. The definition of which parameters do you expect in a specific route 
should be defined as follow:

```python
...

from tapioca import validate

class HelloResource(ResourceHandler):

    @validate(querystring={'name': unicode})
    def get_collection(self, callback):
        name = self.values.querystring['name']
        callback("Hello, {}!".format(name))

...
```

As you can see in the code above, it's clear that the route expect to receive a parameter
'name' which is a ```unicode``` value. It expect an unicode value because all parameters sent 
to Tornado in a query string is a unicode value.

For parameter definition and validation Tapioca uses [Schema](https://github.com/halst/schema) 
a pythonic library to define what values are accepted by your API. An example of an interger parameter
would be ```{ 'parameter_name': Use(int) }``` this way the value of ```parameter_name``` will be converted
in an integer value. If it fails, an error will be raised and your API will return an error response.
You can also need that some parameters to be optional or maybe have default value when the parameter is not sent by
the users. Tapioca provide to you a way to declare it using the ```optional``` function as follow:

```python
...

from schema import Use
from tapioca import validate, optional

class HelloResource(ResourceHandler):

    @validate(querystring={
        'name': unicode,
        optional('page', default_value=1): Use(int)
    })
    def get_collection(self, callback):
        name = self.values.querystring['name']
        page = self.values.querystring['page']
        callback("Hello, {}! It's page {!s}.".format(name, page))

...
```

The example above shows how to define a parameter named ```page``` with the default value ```1``` if
it is not present in the query string of the user request. If it's present the value will be used to 
call the function ```int``` as declared in the definition. We used the ```int``` built-in function, but 
you can use any callable object. We recommend you to read the [Schema documentation](https://github.com/halst/schema#how-schema-validates-data) for details.

To be make the code more readable Tapioca accepts as parameter in the ```validate``` decorator an
class that defines the attribute ```querystring``` as you can see below. The only requirement is that
class should inherits from ```RequestSchema```.

```python
...

from schema import Use
from tapioca import validate, optional, RequestSchema

class SayHelloRequest(RequestSchema):
    querystring = {
        'name': unicode,
        optional('page', 1): Use(int)
    }

class HelloResource(ResourceHandler):

    @validate(SayHelloRequest)
    def get_collection(self, callback):
        name = self.values.querystring['name']
        page = self.values.querystring['page']
        callback("Hello, {}! It's page {!s}.".format(name, page))

...
```



### Extending

You can easily make your API speak a new "language". 

Implementing your own encoder can be achieved in a few steps:

* Create a python class that inherits from `tapioca.Encoder`;
* Override both `encode` and `decode` methods;
* Provide some metadata about your new encoder by specifying its `mimetype` and `extension`. 

Below is a example of an encoder that enables responses as yaml data.

```python

import yaml

from tapioca import Encoder

class YamlEncoder(Encoder):
    mimetype = 'text/yaml'
    extension = 'yaml'

    def encode(self, data):
        return yaml.dump(data)

    def decode(self, data):
        return yaml.load(data)

```

Using this encoder in your resources is as easy as including it in the
`encoders` attribute in the respective `ResourceHandler`s.


```python

from tapioca import ResourceHandler

class CommentsResource(ResourceHandler):
    encoders = ResourceHandler.encoders + (YamlEncoder,)

    # ...

```

Now you can access your route and see it working:

    $ curl -X GET http://localhost:8000/comments.yaml


## Contributing

To contribute with the Tapioca you can just [fork the project](https://github.com/globocom/tapioca/fork_select), 
implement all the changes you need and then send us a pull request. 
It's important to make consistents pull request's. This means that every new feature should be in a separated 
pull request, in order to give us the possibility to review them separately (comments and feedback as well).
We are open to suggestions and to discuss all your ideas.


## License

Tapioca is licensed under the MIT License:

The MIT License

Copyright (c) 2012 globo.com lambda@corp.globo.com

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
