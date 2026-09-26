# p3k.org’s JSON/P Services

For Python3 / [mod_wsgi](https://modwsgi.readthedocs.io).

```shell
# A virtual Python environment is automatically created in the .venv directory
$ make && make server
# – or –
$ make wsgi && make wsgi-server
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

In the HTTP headers sent by Roxy (not to be confused with those in the JSON payload) the additional `X-Roxy-*` headers mentioned above are included, too. Of the headers of the proxied response only `ETag` and `Last-Modified` are passed on in addition, since the others – `Set-Cookie` above all – would take effect on the origin of Roxy; the JSON payload still lists all of them. In the same spirit, the cookies sent by a client to Roxy are not forwarded to the requested server.

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

### Restrictions

Roxy only fetches `http` and `https` URLs; any other scheme (e.g. `file` or `ftp`) is refused with status `400`. Requests to addresses that are not publicly routable – loopback addresses like `localhost`, private networks, link-local addresses like `169.254.169.254` and so on – are refused with status `403`. Both checks apply to every redirect, too.

```shell
curl -G --data-urlencode 'url=http://localhost:8000/' 'http://localhost:8000/roxy'
```

```json
{
  "content": "",
  "headers": {
    "X-Roxy-Status": 403,
    "X-Roxy-Error": "Requests to non-public addresses are not allowed"
  }
}
```

To allow such requests, e.g. for feeds in your intranet or when developing against a local server, create the optional file `local.py` next to `roxy.py` (it is ignored by Git):

```python
allow_private_hosts = True
```

The setting is read when the server starts, so restart it after changing the file. Other URL schemes remain refused.

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

A group name may only consist of letters, digits, hyphens and underscores (up to 64 characters), since it is used as the name of the file the records are stored in. Requests with any other group name – as well as ones with metadata that is not valid JSON – are refused with status `400`.

```shell
curl -G --data-urlencode 'url=http://other.server' 'http://localhost:8000/ferris?group=foo'
1

!! # repeat last command
2

!!
3
```

Sending a request without a URL, only with a group (which is required), Ferris returns the referrers seen recently, most hits first:

```shell
curl 'http://localhost:8000/ferris?group=foo'
```

```json
[
  {
    "url": "http://other.server",
    "hits": 3,
    "metadata": {}
  },
  {
    "url": "http://host.dom",
    "hits": 1,
    "metadata": {}
  }
]
```

"Recently" defaults to the last 7 days, regardless of hit count – a single hit yesterday is still shown. An optional `days` query param overrides that window, up to a maximum of 90 (matching how long entries are retained at all – see below); anything outside `1`–`90`, or non-numeric, is refused with status `400`.

```shell
curl -G --data-urlencode 'days=30' 'http://localhost:8000/ferris?group=foo'
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
evaluate([{"url": "http://other.server", "hits": 3, "metadata": {}}, {"url": "http://host.dom", "hits": 1, "metadata": {}}])
```

### Retention

Entries not seen in 90 days are pruned automatically – permanently deleted from disk – the next time the group is requested; there’s no separate cleanup step to run. This is what actually keeps Entrecote’s per-group JSON files bounded in size, since `add()` on its own never removes anything.

For a full, immediate wipe of a group instead of waiting on that 90-day window, there’s still a task URL, allowed only from localhost (e.g. from a cronjob):

```shell
curl 'http://localhost:8000/tasks/ferris?group=foo'
True
```

## Deployment

The actual push of this code to a server – rsync plus the swap-in/reload sequence – is handled by [p3k/rss-box](https://github.com/p3k/rss-box)'s deploy tooling (`deploy.sh`'s `deploy-services` case, run via `npm run deploy:services` or the `Deploy (Stage)` workflow), since that’s where the app embedding this service actually lives. What follows here is purely the Apache/WSGI side: how the deployed `wsgi.py` gets served at all.

```apache
WSGIRestrictEmbedded On
WSGISocketPrefix /var/run/apache2/wsgi

WSGIDaemonProcess json3k python-home=/path/to/.venv home=/path/to/json3k

WSGIScriptAlias /json3k /path/to/json3k/wsgi.py process-group=json3k

<Location /json3k>
   WSGIApplicationGroup %{GLOBAL}
   Require all granted
</Location>
```

`python-home` just needs a venv whose Python matches whatever `LoadModule wsgi_module` below was built against – it doesn’t need `mod-wsgi-standalone` installed itself (`make install` deliberately excludes it; only `make wsgi`/`make wsgi-server` do).

### `LoadModule`

Prefer your distro’s own mod_wsgi package (e.g. `apt install libapache2-mod-wsgi-py3` on Debian/Ubuntu) over a venv-bundled `.so`:

```apache
LoadModule wsgi_module /usr/lib/apache2/modules/mod_wsgi.so
```

A distro package is built by the same pipeline as the distro’s own Apache and Python, so it’s guaranteed to match both – a venv-installed one has no such guarantee and has to be tracked by hand as the system’s Python version changes over time. Confirm the actual installed path first (`dpkg -L libapache2-mod-wsgi-py3 | grep '\.so$'`) rather than assuming the one above.

If you do need a venv-bundled build instead (e.g. a non-package-managed system, or a Python version the distro doesn’t ship), `make wsgi-config` prints the corresponding lines for whatever’s in `.venv`:

```shell
$ make wsgi-config
mod_wsgi-express module-config
LoadModule wsgi_module "/path/to/.venv/lib/python3.10/site-packages/mod_wsgi/server/mod_wsgi-py310.cpython-310-x86_64-linux-gnu.so"
WSGIPythonHome "/path/to/.venv"
```

In current Apache installations, the `LoadModule` line goes into `/etc/apache2/mods-enabled/wsgi.load`.

You might also need to modify the `WSGISocketPrefix` setting, so Apache does not complain about [insufficient permission to create the socket](https://modwsgi.readthedocs.io/en/develop/user-guides/configuration-issues.html#location-of-unix-sockets).

### Permissions

`.entrecote/` (Ferris’s referrer database – see above) is the one path this app writes to at runtime, both the JSON files themselves and the lock file `filelock`/PupDB creates to guard concurrent access. Whatever user Apache’s WSGI daemon process runs as needs write access there specifically, on top of read access to everything else.

---

## License

JSONP Services by Tobi Schäfer are licensed under a Creative Commons Attribution-ShareAlike 3.0 Austria License. Based on a work at <https://github.com/p3k/json3k>.

<http://creativecommons.org/licenses/by-sa/3.0/at/deed.en_US>
