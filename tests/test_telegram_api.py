import unittest
from unittest.mock import patch

from net_bot.telegram_api import TelegramAPIError, TelegramClient


class FakeResponse:
    def __init__(self, payload: bytes):
        self.payload = payload

    def read(self):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class TelegramClientTests(unittest.TestCase):
    @patch('urllib.request.urlopen')
    def test_request_ok(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse(b'{"ok": true, "result": {}}')
        client = TelegramClient('token')
        result = client.request('sendMessage', {'chat_id': 1, 'text': 'hi'})
        self.assertTrue(result['ok'])

    @patch('urllib.request.urlopen')
    def test_request_raises_on_api_error(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse(b'{"ok": false, "description": "bad"}')
        client = TelegramClient('token')
        with self.assertRaises(TelegramAPIError):
            client.request('sendMessage', {'chat_id': 1, 'text': 'hi'})


if __name__ == '__main__':
    unittest.main()
