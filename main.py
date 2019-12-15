from flask import Flask, request, make_response

from roxy import roxy
from ferris import ferris, cleanup as ferris_cleanup

app = Flask(__name__)


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
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
