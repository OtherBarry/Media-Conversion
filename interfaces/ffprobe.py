from dataclasses import dataclass
from pathlib import Path
import subprocess
import json
from typing import TypedDict, Any, NotRequired

_COMMAND = [
    "ffprobe",
    "-select_streams",
    "v:0",
    "-show_entries",
    "stream=codec_name,width,height,bit_rate",
    "-of",
    "json",
]

_BIT_RATE_COMMAND = [
    "ffprobe",
    "-show_entries",
    "format=bit_rate:stream=codec_type,bit_rate",
    "-of",
    "json",
]


class _FFProbeStream(TypedDict):
    codec_name: str
    width: int
    height: int
    bit_rate: NotRequired[str]


class _FFProbeResponse(TypedDict):
    programs: list[Any]
    streams: list[_FFProbeStream]


class _FFProbeFormat(TypedDict):
    bit_rate: str


class _FFProbeBitRateStream(TypedDict):
    codec_type: str
    bit_rate: str


class _FFProbeBitRateResponse(TypedDict):
    format: _FFProbeFormat
    streams: list[_FFProbeBitRateStream]


def _calculate_bitrate(data: _FFProbeBitRateResponse) -> int:
    total_bit_rate = int(data["format"]["bit_rate"])
    for stream in data["streams"]:
        if (bit_rate := stream.get("bit_rate")) is not None and stream[
            "bit_rate"
        ] != "video":
            total_bit_rate -= int(bit_rate)
    return total_bit_rate


def _execute_command(command: list[str]) -> Any:
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFprobe failed: {e.stderr.strip()}") from e
    return json.loads(result.stdout)


def _execute_ffprobe(path: Path) -> _FFProbeResponse:
    return _execute_command(_COMMAND + [str(path)])


def _execute_bit_rate_ffprobe(path: Path) -> _FFProbeBitRateResponse:
    return _execute_command(_BIT_RATE_COMMAND + [str(path)])


@dataclass
class VideoInfo:
    codec_name: str
    width: int
    height: int
    bit_rate: int


def get_video_info(path: Path) -> VideoInfo:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    ffprobe_data = _execute_ffprobe(path)
    stream = ffprobe_data["streams"][0]
    if "bit_rate" in stream:
        bit_rate = int(stream["bit_rate"])
    else:
        bit_rate_data = _execute_bit_rate_ffprobe(path)
        bit_rate = _calculate_bitrate(bit_rate_data)
    return VideoInfo(
        codec_name=stream["codec_name"],
        width=stream["width"],
        height=stream["height"],
        bit_rate=bit_rate,
    )
