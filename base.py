import sys
import re
import threading

from webob import Request, Response, exc

'''
Implementing the 'another do it yourself framework' tutorial found at:
http://docs.webob.org/en/latest/do-it-yourself.html
'''

__version__ = '2.0'


var_regex = re.compile(r'''
    \{          # The exact character "{"
    (\w+)       # The variable name (restricted to a-z, 0-9, _)
    (?::([^}]+))? # The optional :regex part
    \}          # The exact character "}"
    ''', re.VERBOSE)


def template_to_regex(template):
    regex = ''
    last_pos = 0
    for match in var_regex.finditer(template):
        regex += re.escape(template[last_pos:match.start()])
        var_name = match.group(1)
        expr = match.group(2) or '[^/]+'
        expr = '(?P<%s>%s)' % (var_name, expr)
        regex += expr
        last_pos = match.end()
    regex += re.escape(template[last_pos:])
    regex = '^%s$' % regex
    return regex


def load_controller(string):
    module_name, func_name = string.split(':', 1)
    __import__(module_name)
    module = sys.modules[module_name]
    func = getattr(module, func_name)
    return func


class Router(object):

    def __init__(self):
        self.routes = []

    def add_route(self, template, controller, **vars):
        if isinstance(controller, basestring):
            controller = load_controller(controller)
        self.routes.append((re.compile(template_to_regex(template)),
                            controller,
                            vars))

    def __call__(self, environ, start_response):
        req = Request(environ)
        for regex, controller, vars in self.routes:
            match = regex.match(req.path_info)
            if match:
                req.urlvars = match.groupdict()
                req.urlvars.update(vars)
                return controller(environ, start_response)
        return exc.HTTPNotFound()(environ, start_response)


def controller(func):
    def replacement(environ, start_response):
        req = Request(environ)
        try:
            resp = func(req, **req.urlvars)
        except exc.HTTPException, e:
            resp = e
        if isinstance(resp, basestring):
            resp = Response(body=resp)
        return resp(environ, start_response)
    return replacement


def rest_controller(cls):
    def replacement(environ, start_response):
        req = Request(environ)
        try:
            instance = cls(req, **req.urlvars)
            action = req.urlvars.get('action')
            if action:
                action += '_' + req.method.lower()
            else:
                action = req.method.lower()
            try:
                method = getattr(instance, action)
            except AttributeError:
                raise exc.HTTPNotFound("No action %s" % action)
            resp = method()
            if isinstance(resp, basestring):
                resp = Response(body=resp)
        except exc.HTTPException, e:
            resp = e
        return resp(environ, start_response)
    return replacement


class Localized(object):

    def __init__(self):
        self.local = threading.local()

    def register(self, object):
        self.local.object = object

    def unregister(self):
        del self.local.object

    def __call__(self):
        try:
            return self.local.object
        except AttributeError:
            raise TypeError("No object has been registered for this thread")


get_request = Localized()


class RegisterRequest(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        req = Request(environ)
        get_request.register(req)
        try:
            return self.app(environ, start_response)
        finally:
            get_request.unregister()
