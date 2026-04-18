import json
import os
import tempfile
import unittest
from pathlib import Path

from net_bot.proxy_monitor import ProxyMonitor


class ProxyNotifyTests(unittest.TestCase):
    def make_monitor(self, base: Path) -> ProxyMonitor:
        return ProxyMonitor(
            targets_config=base / 'proxies.local.json',
            notify_config=base / 'proxies.local.json',
            report_path=base / 'proxy-report.json',
            prev_report_path=base / 'proxy-report.prev.json',
            down_log_path=base / 'proxy-down.log',
        )

    def write_notify_config(self, base: Path):
        (base / 'proxies.example.json').write_text(json.dumps({
            'targets': [],
            'target_chat': '1',
            'timezone': 'Europe/Moscow',
        }), encoding='utf-8')

    def test_build_message_returns_empty_if_no_down(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            self.write_notify_config(base)
            (base / 'proxy-report.json').write_text(json.dumps({'targets': []}), encoding='utf-8')
            old = os.environ.get('NET_BOT_TELEGRAM_TOKEN')
            os.environ['NET_BOT_TELEGRAM_TOKEN'] = 'token'
            try:
                monitor = self.make_monitor(base)
                text = monitor.build_message()
            finally:
                if old is None:
                    os.environ.pop('NET_BOT_TELEGRAM_TOKEN', None)
                else:
                    os.environ['NET_BOT_TELEGRAM_TOKEN'] = old
            self.assertEqual(text, '')

    def test_build_message_reports_new_down_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            self.write_notify_config(base)
            (base / 'proxy-report.json').write_text(json.dumps({
                'targets': [
                    {'name': 'p1', 'type': 'socks5', 'host': '1.2.3.4', 'port': 1080, 'status': 'DOWN'}
                ]
            }), encoding='utf-8')
            old = os.environ.get('NET_BOT_TELEGRAM_TOKEN')
            os.environ['NET_BOT_TELEGRAM_TOKEN'] = 'token'
            try:
                monitor = self.make_monitor(base)
                text = monitor.build_message()
            finally:
                if old is None:
                    os.environ.pop('NET_BOT_TELEGRAM_TOKEN', None)
                else:
                    os.environ['NET_BOT_TELEGRAM_TOKEN'] = old
            self.assertIn('не работают 1 прокси', text)
            self.assertIn('1.2.3.4:1080', text)

    def test_build_message_skips_already_down_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            self.write_notify_config(base)
            current = {
                'targets': [
                    {'name': 'p1', 'type': 'socks5', 'host': '1.2.3.4', 'port': 1080, 'status': 'DOWN'}
                ]
            }
            previous = {
                'targets': [
                    {'name': 'p1', 'status': 'DOWN'}
                ]
            }
            (base / 'proxy-report.json').write_text(json.dumps(current), encoding='utf-8')
            (base / 'proxy-report.prev.json').write_text(json.dumps(previous), encoding='utf-8')
            old = os.environ.get('NET_BOT_TELEGRAM_TOKEN')
            os.environ['NET_BOT_TELEGRAM_TOKEN'] = 'token'
            try:
                monitor = self.make_monitor(base)
                text = monitor.build_message()
            finally:
                if old is None:
                    os.environ.pop('NET_BOT_TELEGRAM_TOKEN', None)
                else:
                    os.environ['NET_BOT_TELEGRAM_TOKEN'] = old
            self.assertEqual(text, '')


if __name__ == '__main__':
    unittest.main()
