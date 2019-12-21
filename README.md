p3k.org’s JSONP Services
========================

For [Google App Engine](https://cloud.google.com/appengine/docs/standard/python3/) Python3 Standard Environment.

```sh
make install && make server
```

Roxy
----

Roxy is a simple HTTP proxy returning the response of an HTTP request as JSON data:

```sh
curl 'http://localhost:8080/roxy?url=https://postman-echo.com/time/now'
```

```json
{
  "headers": {
    "Content-Encoding": "gzip",
    "Content-Type": "text/html; charset=utf-8",
    "Date": "Sat, 21 Dec 2019 15:42:28 GMT",
    "ETag": "W/\"1d-UH6kDbDE38DtobPCNXMLlA/wEg8\"",
    "Server": "nginx",
    "set-cookie": "sails.sid=s%3AUiTdC0Yb8Tf18N8OMI5pAFzRW-exlwTo.QbLryFedr5UI1acbG09jepZUl7wCLiDk8DsEj1AKce4; Path=/; HttpOnly",
    "Vary": "Accept-Encoding",
    "Content-Length": "49",
    "Connection": "Close",
    "X-Roxy-Url": "https://postman-echo.com/time/now",
    "X-Roxy-Status": 200
  },
  "content": "Sat, 21 Dec 2019 15:42:28 GMT"
}
```

```sh
curl 'http://localhost:8080/roxy?url=https://postman-echo.com/status/404'
```

```json
{
  "headers": {
    "X-Roxy-Status": 404,
    "X-Roxy-Error": "Not Found"
  },
  "content": ""
}
```

```sh
curl 'http://localhost:8080/roxy?url=https://unknown.domain'
```

```json
{
  "headers": {
    "X-Roxy-Status": 500,
    "X-Roxy-Error": "<urlopen error [Errno -2] Name or service not known>"
  },
  "content": ""
}
```

### JSONP

```sh
curl 'http://localhost:8080/roxy?url=https://postman-echo.com/time/now&callback=evaluate'
```

```js
evaluate({"headers": {"Date": "Sat, 21 Dec 2019 17:39:51 GMT", "Content-Encoding": "gzip", "Vary": "Accept-Encoding", "Content-Length": "49", "Connection": "Close", "Server": "nginx", "X-Roxy-Status": 200, "ETag": "W/\"1d-4oceoAK5+QVtenK1cnUe78BzhvY\"", "Content-Type":
"text/html; charset=utf-8", "set-cookie": "sails.sid=s%3ABFWOChVuhA6y3jkEL4xdKpqgMwq4_64F.F6qCdcTW5slNikB%2FoGXOrh51iACQOqjy3LuwfrkMEU8; Path=/; HttpOnly", "X-Roxy-Url": "https://postman-echo.com/time/now"}, "content": "Sat, 21 Dec 2019 17:39:51 GMT"})'
```

---

Ferris
------

Ferris is a simple referrer counter incrementing the hits for each registered URL for 24 hours. Each referrer is assigned to a group which eventually can be requested to provide the list of total hits per referrer in descending order. At midnight GMT all records are purged (see `cron.yaml`) and counting starts anew.

```sh
curl -i 'http://localhost:8080/ferris?group=foo&url=https://httpbin.org/status/200'
HTTP/1.0 201 CREATED
Content-Type: text/html; charset=utf-8
Content-Length: 1
Server: Werkzeug/0.16.0 Python/3.6.9
Date: Sat, 21 Dec 2019 17:20:52 GMT

1

curl 'http://localhost:8080/ferris?group=foo&url=https://httpbin.org/get'
1

curl 'http://localhost:8080/ferris?group=foo&url=https://httpbin.org/get'
2

curl 'http://localhost:8080/ferris?group=foo&url=https://httpbin.org/get'
3
```

```sh
curl "http://localhost:8080/ferris?group=foo"
```

```json
[
  {
    "url": "https://httpbin.org/get",
    "hits": 3,
    "date": 1576949054453598
  },
  {
    "url": "https://httpbin.org/status/200",
    "hits": 1,
    "date": 1576948808457560
  }
]
```

### JSONP

```sh
curl "http://localhost:8080/ferris?group=foo&callback=evaluate"
```

```js
evaluate([{"url": "https://httpbin.org/get", "hits": 3, "date": 1576949054453598}, {"url": "https://httpbin.org/status/200", "hits": 1, "date": 1576948808457560}])
```

---

License
-------

JSONP Services by Tobi Schäfer are licensed under a Creative Commons Attribution-ShareAlike 3.0 Austria License. Based on a work at https://github.com/p3k/json3k/.

http://creativecommons.org/licenses/by-sa/3.0/at/deed.en_US

> Copyright (c) 2001—2019 Tobi Schäfer
