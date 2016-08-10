import mimic


def hello(req):
    if req.method == 'POST':
        name = req.params['name']
        return 'Hello, %s!' % name
    elif req.method == 'GET':
        return '''<form method="POST">
             Your name: <input type="text" name="name">
             <input type="submit">
             </form>'''


class Hello(mimic.RequestHandler):

    def get(self):
        user = self.request.get('user', 'visitor')
        return '''Welcome %s!
            <form method="POST">
            Your name: <input type="text" name="name">
            <input type="submit">
            </form>''' % user

    def post(self):
        name = self.request.get('name')
        return 'Hello %s!' % name


app = mimic.wsgi_application([
    ('/', hello),
    ('/hello', Hello),
])

if __name__ == '__main__':
    from paste import httpserver
    httpserver.serve(app, host='127.0.0.1', port=8080)
    # from wsgiref.simple_server import make_server
    # server = make_server('127.0.0.1', 8080, app1)
    # server.serve_forever()
