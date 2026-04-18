import tempfile
import unittest
from pathlib import Path

from net_bot.config import IPMonitorConfig
from net_bot.ip_monitor import IPMonitor


class StubIPMonitor(IPMonitor):
    def __init__(self, results):
        super().__init__(Path('cfg'), Path('state'), Path('down'))
        self._results = list(results)

    def _tcp_check_once(self, ip: str, port: int, timeout_seconds: int) -> bool:
        return self._results.pop(0)

    def _load_state(self, ips: list[str]) -> dict:
        return {"servers": {ip: {"status": "UNKNOWN"} for ip in ips}}


class IPMonitorTests(unittest.TestCase):
    def make_config(self) -> IPMonitorConfig:
        return IPMonitorConfig(
            ips=['1.1.1.1'],
            target_chat='1',
            bot_api_key='token',
            port=22,
            timezone='Europe/Moscow',
            quiet_start=23,
            quiet_end=8,
            rounds=3,
            interval_seconds=0,
            timeout_seconds=1,
        )

    def test_execute_marks_down_after_all_failures(self):
        monitor = StubIPMonitor([False, False, False])
        result = monitor.execute(self.make_config())
        self.assertEqual(result.state['servers']['1.1.1.1']['status'], 'DOWN')
        self.assertEqual(result.down_now, ['1.1.1.1'])

    def test_execute_marks_up_if_one_round_succeeds(self):
        monitor = StubIPMonitor([False, True, False])
        result = monitor.execute(self.make_config())
        self.assertEqual(result.state['servers']['1.1.1.1']['status'], 'UP')
        self.assertEqual(result.down_now, [])


if __name__ == '__main__':
    unittest.main()
