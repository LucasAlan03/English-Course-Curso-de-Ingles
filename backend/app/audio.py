import re
import uuid
from pathlib import Path

_EXTENSIONS = {"audio/wav": "wav", "audio/x-wav": "wav", "audio/mpeg": "mp3", "audio/mp3": "mp3"}
_MEDIA_TYPES = {"wav": "audio/wav", "mp3": "audio/mpeg"}
_SAFE_NAME = re.compile(r"^[A-Za-z0-9_-]+\.(wav|mp3)$")


def audio_dir(data_dir: str) -> Path:
    path = Path(data_dir) / "audio"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_audio(data_dir: str, audio: bytes, mime: str) -> str:
    name = f"{uuid.uuid4().hex}.{_EXTENSIONS.get(mime, 'wav')}"
    (audio_dir(data_dir) / name).write_bytes(audio)
    return name


def find_audio(data_dir: str, name: str) -> tuple[Path, str] | None:
    """Path and media type of a stored audio file, or None if the name is unsafe or missing."""
    if not _SAFE_NAME.match(name):
        return None
    path = audio_dir(data_dir) / name
    if not path.is_file():
        return None
    return path, _MEDIA_TYPES[name.rsplit(".", 1)[1]]
