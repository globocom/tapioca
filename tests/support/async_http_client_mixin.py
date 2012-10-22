import urllib


class AsyncHTTPClientMixin(object):

    def get(self, path, **querystring):
        url = self.get_url(path)
        if querystring:
            url = "{0}?{1}".format(url, urllib.urlencode(querystring))
        return self._fetch(url, 'GET')

    def post(self, url, data):
        return self._fetch(url, 'POST', body=data)

    def put(self, url, data):
        return self._fetch(url, 'PUT', body=data)

    def delete(self, url):
        return self._fetch(url, 'DELETE')

    def _fetch(self, url, method, **kwargs):
        self.http_client.fetch(url, self.stop, method=method, **kwargs)
        return self.wait()
