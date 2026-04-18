import asyncio
import unittest

from net_bot.config import ProxyTarget, ProxyTargetsConfig
from net_bot.proxy_monitor import _validate_mtproto_secret, run_checks


class ProxyMonitorTests(unittest.TestCase):
    def test_validate_mtproto_secret_ok(self):
        ok, msg = _validate_mtproto_secret('00000000000000000000000000000000')
        self.assertTrue(ok)
        self.assertIn('ok', msg)

    def test_validate_mtproto_secret_bad_length(self):
        ok, msg = _validate_mtproto_secret('abcd')
        self.assertFalse(ok)
        self.assertIn('length', msg)

    def test_run_checks_empty_targets(self):
        cfg = ProxyTargetsConfig(
            targets=[],
            timeout_seconds=5,
            rounds=1,
            interval_seconds=1,
            target_chat='1',
            timezone='Europe/Moscow',
        )
        result = asyncio.run(run_checks(cfg))
        self.assertEqual(result['targets'], [])
        self.assertEqual(result['rounds'], 1)

    def test_run_checks_skips_disabled_targets(self):
        cfg = ProxyTargetsConfig(
            targets=[
                ProxyTarget(name='disabled', type='mtproto', host='1.1.1.1', port=443, enabled=False),
            ],
            timeout_seconds=5,
            rounds=1,
            interval_seconds=1,
            target_chat='1',
            timezone='Europe/Moscow',
        )
        result = asyncio.run(run_checks(cfg))
        self.assertEqual(result['targets'], [])


if __name__ == '__main__':
    unittest.main()
