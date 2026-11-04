from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class Msg:
    role: Literal["user", "assistant"]
    content: str


@dataclass(frozen=True)
class Usage:
    provider: str
    model: str
    kind: str  # "text" | "stt" | "tts"
    input_units: int  # tokens (text), seconds (stt), characters (tts)
    output_units: int


@dataclass(frozen=True)
class TextResult:
    text: str
    usage: Usage


@dataclass(frozen=True)
class SttResult:
    text: str
    usage: Usage


@dataclass(frozen=True)
class TtsResult:
    audio: bytes
    mime: str
    usage: Usage


class TextModel(Protocol):
    is_paid: bool

    def generate(self, system: str, messages: list[Msg], json_mode: bool = False) -> TextResult: ...


class SpeechToText(Protocol):
    is_paid: bool

    def transcribe(self, audio: bytes, mime: str) -> SttResult: ...


class TextToSpeech(Protocol):
    is_paid: bool

    def synthesize(self, text: str) -> TtsResult: ...


@dataclass
class Providers:
    chat: TextModel
    report: TextModel
    stt: SpeechToText
    tts: TextToSpeech
