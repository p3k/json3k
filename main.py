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
