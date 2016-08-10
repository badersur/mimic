import mimic


@mimic.wsgi_controller
def hello(req):
    if req.method == 'POST':
        name = req.params['name']
        return 'Hello, %s!' % name
    elif req.method == 'GET':
        return '''<form method="POST">
             Your name: <input type="text" name="name">
             <input type="submit">
             </form>'''


@mimic.wsgi_controller
class Hello(object):

    def __init__(self, req):
        self.request = req

    def get(self):
        return '''Welcome!
            <form method="POST">
            Your name: <input type="text" name="name">
            <input type="submit">
            </form>'''

    def post(self):
        name = self.request.params['name']
        return 'Hello %s!' % name


app1 = mimic.Router()
app1.add_route('/', hello)
app1.add_route('/hello', Hello)
app1 = mimic.RegisterRequest(app1)

if __name__ == '__main__':
    from paste import httpserver
    httpserver.serve(app1, host='127.0.0.1', port=8080)
    # from wsgiref.simple_server import make_server
    # server = make_server('127.0.0.1', 8080, app1)
    # server.serve_forever()
