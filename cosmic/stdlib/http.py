"""Cosmic Standard Library — http module."""
from __future__ import annotations
import urllib.request
import urllib.parse
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Response:
    status: int
    headers: dict[str, str]
    body: bytes
    url: str = ''

    @property
    def text(self) -> str:
        return self.body.decode('utf-8')

    @property
    def json(self) -> Any:
        return json.loads(self.body)

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300

    def __repr__(self) -> str:
        return f"Response(status={self.status}, url={self.url!r})"


@dataclass
class Session:
    headers: dict[str, str] = field(default_factory=dict)
    cookies: dict[str, str] = field(default_factory=dict)
    base_url: str = ''

    def request(self, method: str, url: str, data: Any = None,
                headers: dict[str, str] | None = None, json_body: Any = None) -> Response:
        full_url = self.base_url + url if self.base_url else url
        req_headers = {**self.headers}
        if headers:
            req_headers.update(headers)
        body = None
        if json_body is not None:
            body = json.dumps(json_body).encode('utf-8')
            req_headers['Content-Type'] = 'application/json'
        elif data is not None:
            if isinstance(data, str):
                body = data.encode('utf-8')
            elif isinstance(data, bytes):
                body = data
            elif isinstance(data, dict):
                body = urllib.parse.urlencode(data).encode('utf-8')
                req_headers['Content-Type'] = 'application/x-www-form-urlencoded'
        req = urllib.request.Request(full_url, data=body, headers=req_headers, method=method)
        if self.cookies:
            cookie_str = '; '.join(f'{k}={v}' for k, v in self.cookies.items())
            req.add_header('Cookie', cookie_str)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_body = resp.read()
                resp_headers = dict(resp.headers)
                resp_cookies = resp.headers.get_all('Set-Cookie') or []
                for cookie in resp_cookies:
                    name, _, value = cookie.partition('=')
                    self.cookies[name.strip()] = value.split(';')[0].strip()
                return Response(status=resp.status, headers=resp_headers,
                              body=resp_body, url=full_url)
        except urllib.error.HTTPError as e:
            return Response(status=e.code, headers=dict(e.headers),
                          body=e.read(), url=full_url)

    def get(self, url: str, **kwargs: Any) -> Response:
        return self.request('GET', url, **kwargs)

    def post(self, url: str, data: Any = None, json_body: Any = None, **kwargs: Any) -> Response:
        return self.request('POST', url, data=data, json_body=json_body, **kwargs)

    def put(self, url: str, data: Any = None, json_body: Any = None, **kwargs: Any) -> Response:
        return self.request('PUT', url, data=data, json_body=json_body, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> Response:
        return self.request('DELETE', url, **kwargs)

    def patch(self, url: str, data: Any = None, json_body: Any = None, **kwargs: Any) -> Response:
        return self.request('PATCH', url, data=data, json_body=json_body, **kwargs)

    def head(self, url: str, **kwargs: Any) -> Response:
        return self.request('HEAD', url, **kwargs)

    def options(self, url: str, **kwargs: Any) -> Response:
        return self.request('OPTIONS', url, **kwargs)


def get(url: str, headers: dict[str, str] | None = None, **kwargs: Any) -> Response:
    return Session(headers=headers or {}).get(url, **kwargs)


def post(url: str, data: Any = None, json_body: Any = None,
         headers: dict[str, str] | None = None, **kwargs: Any) -> Response:
    return Session(headers=headers or {}).post(url, data=data, json_body=json_body, **kwargs)


def put(url: str, data: Any = None, json_body: Any = None,
        headers: dict[str, str] | None = None, **kwargs: Any) -> Response:
    return Session(headers=headers or {}).put(url, data=data, json_body=json_body, **kwargs)


def delete(url: str, headers: dict[str, str] | None = None, **kwargs: Any) -> Response:
    return Session(headers=headers or {}).delete(url, **kwargs)


def patch(url: str, data: Any = None, json_body: Any = None,
          headers: dict[str, str] | None = None, **kwargs: Any) -> Response:
    return Session(headers=headers or {}).patch(url, data=data, json_body=json_body, **kwargs)


def head(url: str, headers: dict[str, str] | None = None, **kwargs: Any) -> Response:
    return Session(headers=headers or {}).head(url, **kwargs)


def options(url: str, headers: dict[str, str] | None = None, **kwargs: Any) -> Response:
    return Session(headers=headers or {}).options(url, **kwargs)


def request(method: str, url: str, **kwargs: Any) -> Response:
    return Session().request(method, url, **kwargs)


def download(url: str, path: str) -> str:
    resp = get(url)
    with open(path, 'wb') as f:
        f.write(resp.body)
    return path


def upload(url: str, path: str, field: str = 'file') -> Response:
    import mimetypes
    boundary = '----CosmicBoundary'
    filename = path.split('/')[-1]
    content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    with open(path, 'rb') as f:
        file_data = f.read()
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'
        f'Content-Type: {content_type}\r\n\r\n'
    ).encode() + file_data + f'\r\n--{boundary}--\r\n'.encode()
    return request('POST', url, data=body,
                   headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})


def encode_params(params: dict[str, Any]) -> str:
    return urllib.parse.urlencode(params)


def decode_params(query: str) -> dict[str, str]:
    return dict(urllib.parse.parse_qsl(query))


def url_join(base: str, path: str) -> str:
    return urllib.parse.urljoin(base, path)
