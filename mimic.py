'''
Implementing the 'another do it yourself framework' tutorial found at:
http://docs.webob.org/en/latest/do-it-yourself.html with some modifications.
'''

import sys
import re
import threading

from types import FunctionType
from webob import Response, exc, Request as webRequest


class Request(webRequest):

    def get(self, param_name, default=''):
        param = self.params.get(param_name)
        return param if param else default


def load_controller(string):
    module_name, func_name = string.split('.', 1)
    __import__(module_name)
    module = sys.modules[module_name]
    func = getattr(module, func_name)
    return func


def function_controller(func):
    def replacement(environ, start_response):
        req = Request(environ)
        try:
            resp = func(req, **req.urlvars)
        except exc.HTTPException as e:
            resp = e
        if isinstance(resp, basestring):
            resp = Response(body=resp)
        return resp(environ, start_response)
    return replacement


def class_controller(cls):
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
        except exc.HTTPException as e:
            resp = e
        return resp(environ, start_response)
    return replacement


def wsgi_controller(arg):
    if isinstance(arg, FunctionType):
        return function_controller(arg)
    return class_controller(arg)


class Router(object):

    def __init__(self):
        self.routes = []

    def add_route(self, template, controller, **variables):
        if isinstance(controller, basestring):
            controller = load_controller(controller)
        regex = re.compile('^%s$' % template)
        self.routes.append((regex, controller, variables))

    def __call__(self, environ, start_response):
        req = Request(environ)
        for regex, controller, variables in self.routes:
            match = regex.match(req.path_info)
            if match:
                req.urlvars = match.groupdict()
                req.urlvars.update(variables)
                return controller(environ, start_response)
        return exc.HTTPNotFound()(environ, start_response)


class Localized(object):

    def __init__(self):
        self.local = threading.local()

    def register(self, obj):
        self.local.obj = obj

    def unregister(self):
        del self.local.obj

    def __call__(self):
        try:
            return self.local.obj
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


class RequestHandler(object):

    def __init__(self, req):
        self.request = req


def wsgi_application(list_of_tuples):
    app = Router()
    for path, controller in list_of_tuples:
        controller = wsgi_controller(controller)
        app.add_route(path, controller)
    return RegisterRequest(app)
