import logging

from app.providers.base import Providers
from app.providers.fakes import FakeStt, FakeTextModel, FakeTts
from app.server import warm_up


class Recorder:
    def __init__(self, fail=False):
        self.calls = 0
        self.fail = fail

    def warm_up(self):
        self.calls += 1
        if self.fail:
            raise RuntimeError("model file missing")


def test_warm_up_calls_the_hook_of_voice_providers():
    stt, tts = Recorder(), Recorder()
    providers = Providers(chat=FakeTextModel(), report=FakeTextModel(), stt=stt, tts=tts)
    warm_up(providers)
    assert (stt.calls, tts.calls) == (1, 1)


def test_warm_up_skips_providers_without_a_hook_and_survives_failures(caplog):
    broken = Recorder(fail=True)
    providers = Providers(chat=FakeTextModel(), report=FakeTextModel(), stt=broken, tts=FakeTts())
    with caplog.at_level(logging.WARNING):
        warm_up(providers)  # FakeTts has no warm_up; the broken one must not raise
    assert broken.calls == 1 and "model file missing" in caplog.text
