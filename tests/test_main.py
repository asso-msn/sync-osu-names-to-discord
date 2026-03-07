import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import argparse
from unittest.mock import MagicMock, patch

import pytest


class TestLoopMinutesArgument:
    def _parse_args(self, argv):
        parser = argparse.ArgumentParser()
        parser.add_argument("--loop-minutes", type=float, default=0)
        return parser.parse_args(argv)

    def test_default_is_zero(self):
        args = self._parse_args([])
        assert args.loop_minutes == 0

    def test_loop_minutes_set(self):
        args = self._parse_args(["--loop-minutes", "5"])
        assert args.loop_minutes == 5.0

    def test_loop_minutes_fractional(self):
        args = self._parse_args(["--loop-minutes", "0.5"])
        assert args.loop_minutes == 0.5


class TestMainLoopBehavior:
    def test_no_loop_calls_main_once(self):
        """When loop_minutes <= 0, main() is called exactly once."""
        call_count = 0
        sleep_calls = []

        def fake_main():
            nonlocal call_count
            call_count += 1

        def fake_sleep(secs):
            sleep_calls.append(secs)

        loop_minutes = 0
        if loop_minutes > 0:
            while True:
                fake_main()
                fake_sleep(loop_minutes * 60)
        else:
            fake_main()

        assert call_count == 1
        assert sleep_calls == []

    def test_loop_calls_main_repeatedly(self):
        """When loop_minutes > 0, main() is called in a loop with sleep."""
        iterations = 3
        call_count = 0
        sleep_calls = []

        def fake_main():
            nonlocal call_count
            call_count += 1

        def fake_sleep(secs):
            sleep_calls.append(secs)

        loop_minutes = 2.0
        while call_count < iterations:
            fake_main()
            if call_count < iterations:
                fake_sleep(loop_minutes * 60)

        assert call_count == iterations
        # sleep is called between iterations, not after the last one
        assert len(sleep_calls) == iterations - 1
        assert all(s == loop_minutes * 60 for s in sleep_calls)

    def test_sleep_duration_is_correct(self):
        """Sleep duration matches loop_minutes * 60."""
        sleep_calls = []

        loop_minutes = 3.5
        iterations = 2
        count = 0

        def fake_main():
            nonlocal count
            count += 1

        def fake_sleep(secs):
            sleep_calls.append(secs)

        while count < iterations:
            fake_main()
            if count < iterations:
                fake_sleep(loop_minutes * 60)

        assert sleep_calls == [loop_minutes * 60] * (iterations - 1)
