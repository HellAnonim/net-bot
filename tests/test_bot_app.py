import unittest
from pathlib import Path

from net_bot.bot_app import NetBot


class DummyTelegram:
    def __init__(self):
        self.messages = []

    def send_message(self, chat_id, text, reply_markup=None):
        self.messages.append((chat_id, text, reply_markup))


class DummyMonitor:
    def __init__(self):
        self.runs = 0

    def run(self):
        self.runs += 1

    def run_tester(self):
        self.runs += 1


class BotAppTests(unittest.TestCase):
    def make_bot(self):
        bot = NetBot.__new__(NetBot)
        bot.root = Path('/tmp')
        bot.telegram = DummyTelegram()
        bot.ip_monitor = DummyMonitor()
        bot.proxy_monitor = DummyMonitor()
        bot.format_ip_problems = lambda: 'ip problems text'
        bot.format_proxy_problems = lambda: 'proxy problems text'
        return bot

    def test_handle_text_runs_ip_check(self):
        bot = self.make_bot()
        bot.handle_text(1, 'Test IP')
        self.assertEqual(bot.ip_monitor.runs, 1)
        self.assertEqual(bot.telegram.messages[-1][1], 'ip problems text')

    def test_handle_text_runs_proxy_check(self):
        bot = self.make_bot()
        bot.handle_text(1, 'Test Proxy')
        self.assertEqual(bot.proxy_monitor.runs, 1)
        self.assertEqual(bot.telegram.messages[-1][1], 'proxy problems text')

    def test_handle_text_unknown_command(self):
        bot = self.make_bot()
        bot.handle_text(1, 'something else')
        self.assertIn('Нажми кнопку ниже', bot.telegram.messages[-1][1])


if __name__ == '__main__':
    unittest.main()
