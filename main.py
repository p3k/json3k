from flask import Flask, request, make_response, logging
from logging.config import dictConfig

from roxy import roxy
from ferris import ferris, cleanup as ferris_cleanup


# Source: https://flask.palletsprojects.com/en/1.1.x/logging/#basic-configuration
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'WARN',
        'handlers': ['wsgi']
    }
})

app = Flask(__name__)


# Both services are meant to be called from any page embedding a box, so
# every response needs this – including Flask’s own automatic OPTIONS
# response to a preflight request, which neither roxy() nor ferris() ever
# get to run for (Flask answers it before the view function is called),
# and which a browser sends once a request stops being CORS-simple (e.g.
# past a certain Accept header length). Centralized here, rather than
# set inside each response path, so an easy-to-miss one (like ferris()’s
# own add-a-hit response, which never set this at all) can’t happen again.
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'

    if request.method == 'OPTIONS':
        response.headers['Access-Control-Allow-Headers'] = \
            request.headers.get('Access-Control-Request-Headers', '*')
        response.headers['Access-Control-Allow-Methods'] = 'GET'

    return response


@app.route('/')
def welcome():
    return make_response("JSON3k services ready.")

@app.route('/roxy')
def roxy_service():
    return roxy(request, make_response)


@app.route('/ferris')
def ferris_service():
    return ferris(request, make_response)


@app.route('/tasks/ferris')
def ferris_tasks():
    return ferris_cleanup(request, make_response)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
