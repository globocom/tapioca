
from .async_http_client_mixin import AsyncHTTPClientMixin
from .resources import ResourceWithDocumentation


def assert_response_code(response, expected_status_code):
    assert response.code == expected_status_code, \
            'the status code should be {0:d} but it was {1:d}'.format(
                    expected_status_code, response.code)
