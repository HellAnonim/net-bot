import os
import tempfile
import unittest
from pathlib import Path

from net_bot.config import (
    BotConfig,
    IPMonitorConfig,
    ProxyTargetsConfig,
    load_bot_config,
    load_ip_monitor_config,
    load_proxy_targets_config,
    resolve_config_path,
)


class ConfigTests(unittest.TestCase):
    def test_resolve_config_path_falls_back_to_example(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            example = tmp_path / 'bot.example.json'
            example.write_text('{"allowed_chat_id": 1, "bot_api_key": "x"}', encoding='utf-8')
            resolved = resolve_config_path(tmp_path / 'bot.local.json')
            self.assertEqual(resolved, example)

    def test_load_bot_config_from_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            p = tmp_path / 'bot.example.json'
            p.write_text('{"allowed_chat_id": 123}', encoding='utf-8')
            old = os.environ.get('NET_BOT_TELEGRAM_TOKEN')
            os.environ['NET_BOT_TELEGRAM_TOKEN'] = 'token-from-env'
            try:
                cfg = load_bot_config(tmp_path / 'bot.local.json')
            finally:
                if old is None:
                    os.environ.pop('NET_BOT_TELEGRAM_TOKEN', None)
                else:
                    os.environ['NET_BOT_TELEGRAM_TOKEN'] = old
            self.assertIsInstance(cfg, BotConfig)
            self.assertEqual(cfg.bot_api_key, 'token-from-env')
            self.assertEqual(cfg.allowed_chat_id, 123)

    def test_load_ip_monitor_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            p = tmp_path / 'ip_monitor.example.json'
            p.write_text(
                '{"ips": ["1.1.1.1"], "target_chat": "1", "port": 22, "timezone": "Europe/Moscow", "quiet_start": 23, "quiet_end": 8}',
                encoding='utf-8',
            )
            old = os.environ.get('NET_BOT_TELEGRAM_TOKEN')
            os.environ['NET_BOT_TELEGRAM_TOKEN'] = 'token'
            try:
                cfg = load_ip_monitor_config(tmp_path / 'ip_monitor.local.json')
            finally:
                if old is None:
                    os.environ.pop('NET_BOT_TELEGRAM_TOKEN', None)
                else:
                    os.environ['NET_BOT_TELEGRAM_TOKEN'] = old
            self.assertIsInstance(cfg, IPMonitorConfig)
            self.assertEqual(cfg.ips, ['1.1.1.1'])
            self.assertEqual(cfg.rounds, 5)
            self.assertEqual(cfg.interval_seconds, 60)
            self.assertEqual(cfg.timeout_seconds, 3)

    def test_load_proxy_targets_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            p = tmp_path / 'proxies.example.json'
            p.write_text(
                '{"targets": [{"name": "t1", "type": "mtproto", "host": "1.2.3.4", "port": 443}], "target_chat": "1", "timezone": "Europe/Moscow"}',
                encoding='utf-8',
            )
            cfg = load_proxy_targets_config(tmp_path / 'proxies.local.json')
            self.assertIsInstance(cfg, ProxyTargetsConfig)
            self.assertEqual(len(cfg.targets), 1)
            self.assertEqual(cfg.targets[0].name, 't1')
            self.assertEqual(cfg.targets[0].type, 'mtproto')


if __name__ == '__main__':
    unittest.main()
