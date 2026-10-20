import unittest

from adapters.personal_voice.nomo_adapter import NomoAdapter
from ports.result import ErrorCode, Failure, Success


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.adapter = object.__new__(NomoAdapter)
        self.adapter._decode = lambda value: value

    def test_invalid_size_never_calls_provider(self):
        def forbidden(_):
            raise AssertionError("provider_called")

        self.assertEqual(
            self.adapter._call(b"", 1, forbidden, lambda v: True), Failure(ErrorCode.INVALID_INPUT)
        )

    def test_provider_exception_is_sanitized(self):
        def provider(_):
            raise RuntimeError("secret tensor and credential")

        result = self.adapter._call(b"0000", 1, provider, lambda v: True)
        self.assertEqual(result, Failure(ErrorCode.INFERENCE_FAILED))
        self.assertNotIn("secret", repr(result))

    def test_invalid_provider_response_and_success(self):
        self.assertEqual(
            self.adapter._call(b"0000", 1, lambda v: float("nan"), lambda v: 0 <= v <= 1),
            Failure(ErrorCode.INVALID_RESPONSE),
        )
        self.assertEqual(self.adapter._call(b"0000", 1, lambda v: 0.8, lambda v: 0 <= v <= 1), Success(0.8))

    def test_programming_error_is_not_hidden(self):
        def broken(_):
            raise AssertionError("bug")

        with self.assertRaises(AssertionError):
            self.adapter._call(b"0000", 1, broken, lambda v: True)
