from flask import Flask
from flask import g
from flask import Response
from flask import request
from flask import make_response
from flask import current_app

import json
import os
from flask import send_from_directory

# import MySQLdb
from datetime import timedelta
from functools import update_wrapper
from bson import json_util

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from functools import wraps
import requests as reqsts

app = Flask(__name__)

def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    # if not isinstance(origin, basestring):
    #    origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
#                 resp = make_response(f(*args, **kwargs))
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers
            if origin == '*':
                h['Access-Control-Allow-Origin'] = origin
            # h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

def check_auth(username, password):
    print "authentication"
    return True  # login 

@crossdomain(origin='*')
def authenticate():
    return Response(
    'Login Failed', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
    
@app.before_request
def db_connect():
    pass
#     g.conn = MySQLdb.connect(host="127.0.0.1", user="root", passwd="yourpasswordhere", db="test", port=3306)
#     g.cursor = g.conn.cursor()

@app.after_request
def db_disconnect(response):
#     g.cursor.close()
#     g.conn.close()
    response.headers['Access-Control-Allow-Headers'] = "Origin, X-Requested-With,Content-Type, Accept, Authorization"
    return response

def query_db(query, args=(), one=False):
    g.cursor.execute(query, args)
    rv = [dict((g.cursor.description[idx][0], value)
               for idx, value in enumerate(row)) for row in g.cursor.fetchall()]
    return (rv[0] if rv else None) if one else rv

@app.route("/hello", methods=['GET', 'OPTIONS'])
@requires_auth
@crossdomain(origin='*')
def hello():
    return "Message4u"

@app.route("/totalRequests", methods=['GET', 'OPTIONS'])
@crossdomain(origin='*')
def totalRequests():
    result = query_db("SELECT count(*) as total FROM ft_form_30;")
    data = json.dumps(result, default=json_util.default, ensure_ascii=False)
    resp = Response(data, status=200, mimetype='application/json')
    return resp

@app.route("/searchResults", methods=['GET', 'OPTIONS'])
@crossdomain(origin='*')
def searchResults():
    f = open('data/search-results.json', 'r')
    data = f.read()
    # data = json.dumps(result, default=json_util.default, ensure_ascii=False)
    resp = Response(data, status=200, mimetype='application/json')
    return resp


# if __name__ == "__main__":
#     app.run(host= '0.0.0.0')

if __name__ == '__main__':
    http_server = HTTPServer(WSGIContainer(app))
    print "Starting server at 5000"
    http_server.listen(5000)
    IOLoop.instance().start()
