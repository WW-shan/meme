import asyncio
import unittest

from src.trader import bot as bot_module


class BotCleanupTests(unittest.TestCase):
    def test_cleanup_closes_listener_http_providers(self):
        self.assertTrue(
            hasattr(bot_module, "_cleanup_bot_runtime"),
            "bot runtime cleanup helper should be available",
        )

        calls = []

        class FakeListener:
            async def close_log_providers(self):
                calls.append("close_log_providers")

        class FakeBot:
            listener = FakeListener()

            async def sell_all_positions(self, timeout=35):
                calls.append(("sell_all_positions", timeout))

            def _save_state(self):
                calls.append("save_state")

        asyncio.run(bot_module._cleanup_bot_runtime(FakeBot(), ws_manager=None))

        self.assertIn(("sell_all_positions", 35), calls)
        self.assertIn("save_state", calls)
        self.assertIn("close_log_providers", calls)

    def test_cleanup_closes_trade_and_main_http_providers(self):
        calls = []

        class FakeProvider:
            async def disconnect(self):
                calls.append("main_provider_disconnect")

        class FakeW3:
            provider = FakeProvider()

        class FakeExecutor:
            async def close(self):
                calls.append("executor_close")

        class FakeListener:
            async def close_log_providers(self):
                calls.append("close_log_providers")

        class FakeBot:
            listener = FakeListener()
            executor = FakeExecutor()
            w3 = FakeW3()

            async def sell_all_positions(self, timeout=35):
                calls.append(("sell_all_positions", timeout))

            def _save_state(self):
                calls.append("save_state")

        asyncio.run(bot_module._cleanup_bot_runtime(FakeBot(), ws_manager=None))

        self.assertIn("executor_close", calls)
        self.assertIn("main_provider_disconnect", calls)


if __name__ == "__main__":
    unittest.main()
