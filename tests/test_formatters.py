import json
import tempfile
import unittest
from pathlib import Path

from net_bot.formatters import format_ip_problems_from_state, format_proxy_problems_from_report


class FormatterTests(unittest.TestCase):
    def test_format_ip_problems_no_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'state.json'
            self.assertIn('данные не найдены', format_ip_problems_from_state(path))

    def test_format_ip_problems_with_down_server(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'state.json'
            path.write_text(json.dumps({
                'servers': {
                    '1.1.1.1': {'status': 'DOWN', 'last_check': '2026-04-18T08:00:00+03:00'},
                    '2.2.2.2': {'status': 'UP', 'last_check': '2026-04-18T08:00:00+03:00'},
                }
            }), encoding='utf-8')
            text = format_ip_problems_from_state(path)
            self.assertIn('1.1.1.1', text)

    def test_format_proxy_problems_no_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'report.json'
            self.assertIn('данные не найдены', format_proxy_problems_from_report(path))

    def test_format_proxy_problems_with_down_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'report.json'
            path.write_text(json.dumps({
                'checked_at': 1713416400,
                'targets': [
                    {'status': 'DOWN', 'type': 'socks5', 'host': '1.2.3.4', 'port': 1080},
                ]
            }), encoding='utf-8')
            text = format_proxy_problems_from_report(path)
            self.assertIn('1.2.3.4:1080', text)


if __name__ == '__main__':
    unittest.main()
