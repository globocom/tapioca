import datetime
from unittest import TestCase

from tapioca import JsonEncoder


class JsonEncoderTestCase(TestCase):

    def test_encode_to_keys_to_camelcase(self):
        encoder = JsonEncoder(None)
        result = encoder.encode({'my_name': 1})
        assert 'myName' in result

    def test_encode_deep_dict_to_camelcase(self):
        encoder = JsonEncoder(None)
        result = encoder.encode({'my_dict': {'another_dict': 1}})
        assert 'myDict' in result
        assert 'anotherDict' in result

    def test_decode_dict_keys_from_camelcase(self):
        encoder = JsonEncoder(None)
        result = encoder.decode('{"myAge": 25}')
        assert 'my_age' in result

    def test_decode_deep_keys_from_camelcase(self):
        encoder = JsonEncoder(None)
        result = encoder.decode('{"myAge":{"thisOneIsGood":true}}')
        assert 'my_age' in result
        assert 'this_one_is_good' in result['my_age']
