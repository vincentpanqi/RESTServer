import json
import re
from cgi import parse_header


class Request:
    def __init__(self, environ):
        self.environ = environ

    @property
    def path(self):
        return self.environ.get('PATH_INFO')

    @property
    def method(self):
        return self.environ.get('REQUEST_METHOD')

    @property
    def ip(self):
        return self.environ.get('REMOTE_ADDR')

    @property
    def host(self):
        return self.environ.get('REMOTE_HOST')

    @property
    def query_string(self):
        return self.environ.get('QUERY_STRING')

    @property
    def query(self):
        query = {}
        for i in self.query_string.split('&'):
            key, value = i.split("=")
            query[key] = value
        return query

    @property
    def body(self):
        content_length = int(self.environ.get('CONTENT_LENGTH', 0))
        return self.environ['wsgi.input'].read(content_length).decode('utf-8')

    @property
    def content_type(self):
        return self.environ.get('CONTENT_TYPE', 'application/x-www-form-urlencoded')

    # @property
    # def headers(self):
    #     return self.headers.get('Content-Type', 'application/x-www-form-urlencoded')

    @property
    def data(self):
        content_type, parameters = parse_header(self.content_type)
        if content_type == 'application/x-www-form-urlencoded':
            data = {}
            for i in self.body.split('&'):
                key, value = i.split("=")
                data[key] = value
            return data
        # elif content_type == 'multipart/form-data':
        #     # TODO I need a better form-data parser
        #     parameters['boundary'] = parameters['boundary'].encode('utf-8')
        #     return parse_multipart(self.environ['wsgi.input'], parameters)
        elif content_type == 'application/json':
            return json.loads(self.body)
        elif content_type == 'text/plain':
            return self.body
        else:
            return self.body


class Response:
    def __init__(self):
        self.body = None
        self.headers = {'Content-type': 'text/json'}
        self.status = 200


class Context:
    def __init__(self, environ):
        self.request = Request(environ)
        self.response = Response()


status_code = {
    '100': '100 Continue',
    '101': '101 Switching Protocols',
    '200': '200 OK',
    '204': '204 No Content',
}


class RESTServer:
    def __init__(self):
        self.processors = []
        self.stack = {}

    def __call__(self, environ, start_response):
        ctx = Context(environ)
        # pprint(environ)
        for pattern, methods, fn in self.processors:
            if pattern is not None:
                if ctx.request.method in methods:
                    match = pattern.match(ctx.request.path)
                    if match:
                        ctx.response.body = fn(ctx.request, **match.groupdict())
                        ctx.response.status = ctx.response.status or 200
                        break
            else:
                fn(ctx)

        if isinstance(ctx.response.body, dict):
            body = json.dumps(ctx.response.body)
            ctx.response.headers['Content-type'] = 'text/json'
        else:
            body = str(ctx.response.body)
            ctx.response.headers['Content-type'] = 'text/plain'
        headers = [(key, val) for key, val in ctx.response.headers.items()]
        status = status_code[str(ctx.response.status)]
        start_response(status, headers)
        return [body.encode('utf-8')]

    def plugin(self, fn):
        self.processors.append((None, None, fn))

    def route(self, path, methods=None):
        if methods is None:
            methods = ['GET']

        def decorator(fn):
            pattern = re.compile(
                re.sub(r':(?P<params>[a-z_]+)',
                       lambda m: '(?P<{}>[a-z0-9]+)'.format(m.group('params')),
                       path))
            self.processors.append((pattern, methods, fn))

        return decorator

    def listen(self, port):
        from wsgiref.simple_server import make_server
        server = make_server('0.0.0.0', port, self)
        print('serve on 0.0.0.0:8823')
        server.serve_forever()
