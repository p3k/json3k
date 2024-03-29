# p3k.org’s JSON/P Services

For Python3 / [mod_wsgi](https://modwsgi.readthedocs.io).

```shell
# A virtual Python environment is automatically created in the .venv directory
$ make && make server
# — or —
$ make wgsi && make wsgi-server
```

> 💡 [Integration with Google AppEngine](https://github.com/p3k/json3k/tree/gae) is no longer supported.

## Roxy

Roxy is a simple HTTP proxy returning the response of an HTTP request as JSON data:

```shell
curl -G --data-urlencode 'url=https://postman-echo.com/time/now' \
   'http://localhost:8000/roxy'
```

```json
{
  "content": "Mon, 06 Jan 2020 07:26:58 GMT",
  "headers": {
    "Content-Encoding": "gzip",
     "Content-Type": "text/html; charset=utf-8",
     "Date": "Mon, 06 Jan 2020 07:26:58 GMT",
     "ETag": "W/\"1d\"",
     "Server": "nginx",
     "set-cookie": "sails.sid=s%3AS2fABSVzWnUuBKmQoq5LTwFIf7_QN_NG.xmjFxEuq5w2mVp9DLrknr6tNryVW4JnGO4u5N%2F8dk58; Path=/; HttpOnly",
     "Vary": "Accept-Encoding",
     "Content-Length": "49",
     "Connection": "Close",
     "X-Roxy-Url": "https://postman-echo.com/time/now",
     "X-Roxy-Status": 200
  }
}
```

The additional header `X-Roxy-Url` contains either the final URL, in case the request has been redirected, or the original URL otherwise; `X-Roxy-Status` contains the original HTTP status code which might differ from the one returned by a HTTP server caching Roxy responses (which is recommended).

```shell
curl -Gi --data-urlencode 'url=https://postman-echo.com/status/404' \
  'http://localhost:8000/roxy'
```

```plain
HTTP/1.1 404 NOT FOUND
Date: Sun, 15 Nov 2020 21:08:27 GMT
Server: Apache
Content-Length: 79
Access-Control-Allow-Origin: *
X-Roxy-Status: 404
X-Roxy-Error: Not Found
Expires: Sun, 15 Nov 2020 21:09:27 GMT
Connection: close
Content-Type: application/json

{"content": "", "headers": {"X-Roxy-Status": 404, "X-Roxy-Error": "Not Found"}}
```

In the HTTP headers sent by Roxy (not to be confused with those in the JSON payload) the additional `X-Roxy-*` headers mentioned above are included, too.

Finally, in case of an error `X-Roxy-Error` contains a more or less descriptive error message, depending on the cause (HTTP status code, application issue etc.)

```shell
curl -G --data-urlencode 'url=https://unknown.domain' \
  'http://localhost:8000/roxy'
```

```json
{
  "content": "",
  "headers": {
    "X-Roxy-Status": 500,
    "X-Roxy-Error": "<urlopen error [Errno -2] Name or service not known>"
  }
}
```

### JSONP

```shell
curl -G --data-urlencode 'url=https://postman-echo.com/time/now' \
  'http://localhost:8000/roxy?callback=evaluate'
```

```js
evaluate({"content": "Mon, 06 Jan 2020 07:30:53 GMT", "headers": {"Content-Encoding": "gzip", "Content-Type": "text/html; charset=utf-8", "Date": "Mon, 06 Jan 2020 07:30:53 GMT", "ETag": "W/\"1d\"", "Server": "nginx", "set-cookie": "sails.sid=s%3AsPZWnJe5WvmBOFj4iIydYgPGVcx-zccy.VKP6VA7uRXxkYqk%2FuwCCR9aUnMnb2BfmppSs5sC92es; Path=/; HttpOnly", "Vary": "Accept-Encoding", "Content-Length": "49", "Connection": "Close", "X-Roxy-Url": "https://postman-echo.com/time/now", "X-Roxy-Status": 200}})
```

---

## Ferris

Ferris is a simple referrer counter incrementing the hits for each registered URL. Each referrer is assigned to a group which eventually can be requested to provide the list of total hits per referrer in descending order.

```shell
curl -Gi --data-urlencode 'url=http://host.dom' 'http://localhost:8000/ferris?group=foo'

HTTP/1.0 201 CREATED
Content-Type: text/html; charset=utf-8
Content-Length: 1
Server: Werkzeug/0.16.0 Python/3.6.9
Date: Sat, 21 Dec 2019 17:20:52 GMT

1
```

The response body contains the current hit counter of the referrer URL.

```shell
curl -G --data-urlencode 'url=http://other.server' 'http://localhost:8000/ferris?group=foo'
1

!! # repeat last command
2

!!
3
```

Sending a request without a URL, only with a group (which is required), Ferris returns the list of referrers recorded so far:

```shell
curl 'http://localhost:8000/ferris?group=foo'
```

```json
[
  {
    "url": "http://other.server",
    "hits": 3,
    "date": 1576949054453598,
    "metadata": {}
  },
  {
    "url": "http://host.dom",
    "hits": 1,
    "date": 1576948808457560,
    "metadata": {}
  }
]
```

It is possible to add metadata to a referrer simply by appending it JSON-encoded to the ping URL:

```shell
curl -G --data-urlencode 'metadata={"foo":["bar","baz"]}' --data-urlencode 'url=https://host.dom' 'http://localhost:8000/ferris?group=meta'
1
```

```shell
curl 'http://localhost:8000/ferris?group=meta'
```

```json
[
  {
    "url": "http://host.dom",
    "hits": 1,
    "date": 1578296164821.103,
    "metadata": {
      "foo": ["bar", "baz"]
    }
  }
]
```

### JSONP

```shell
curl 'http://localhost:8000/ferris?group=foo&callback=evaluate'
```

```js
evaluate([{"url": "http://other.server", "hits": 3, "date": 1576949054453598}, {"url": "http://host.dom", "hits": 1, "date": 1576948808457560}])
```

### Cleanup

There is a task URL defined to delete all records of a group to reduce the necessary amount of data storage. This is only allowed from localhost and should be called from a cronjob:

```shell
curl 'http://localhost:8000/tasks/ferris?group=foo'
True
```

## Deployment

Run `make config` to output the corresponding Apache configuration lines:

```shell
$ make config
mod_wsgi-express module-config
LoadModule wsgi_module "/path/to/.venv/json3k/lib/python3.10/site-packages/mod_wsgi/server/mod_wsgi-py310.cpython-310-x86_64-linux-gnu.so"
WSGIPythonHome "/path/to/.venv/json3k"
```

In current Apache installations, the `LoadModule` line goes into `/etc/apache2/mods-enabled/wsgi.load`, and the other one into `/etc/apache2/mods-enabled/wsgi.conf`.

You might also need to modify the `WSGISocketPrefix` setting, so Apache does not complain about [insufficient permission to create the socket](https://modwsgi.readthedocs.io/en/develop/user-guides/configuration-issues.html#location-of-unix-sockets):

```apache2
WSGISocketPrefix /var/run/apache2/wsgi
```

In case of multiple applications are being run, [WSIGʼs “daemon” mode](https://modwsgi.readthedocs.io/en/develop/user-guides/configuration-guidelines.html#defining-process-groups) needs to be used:

```apache2
WSGIDaemonProcess json3k python-home=/path/to/.venv/json3k home=/path/to/json3k
WSGIScriptAlias /json3k /path/to/json3k/wsgi.py process-group=json3k
```

---

## License

JSONP Services by Tobi Schäfer are licensed under a Creative Commons Attribution-ShareAlike 3.0 Austria License. Based on a work at <https://github.com/p3k/json3k>.

<http://creativecommons.org/licenses/by-sa/3.0/at/deed.en_US>
