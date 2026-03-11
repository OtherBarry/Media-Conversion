import datetime
import json
import logging
import os
import subprocess
import time

from opentelemetry import trace

from transcoder.settings import settings

tracer = trace.get_tracer(__name__)

FOLDER_TYPE_MAP = {
    "Animated TV Shows": "animation",
    "Movies": "movie",
    "TV Shows": "tv",
}
FILE_IN_USE_DELAY = 5


def get_video_type(path: str) -> str | None:
    try:
        folder = path.split("/")[3]
        return FOLDER_TYPE_MAP.get(folder)
    except IndexError:
        return None


def format_rate(rate: int) -> str:
    return str(int(rate / 1000)) + "k"


def extension_matches(a: str, b: str) -> bool:
    a, b = a.lower(), b.lower()
    return a == b or ("." + a) == b or a == ("." + b)


def _delete_old_file(path: str, max_attempts: int = 5) -> None:
    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        try:
            os.remove(path)
        except PermissionError:
            result = subprocess.run("rm " + path)
            if result.returncode == 0:
                break
            time.sleep(FILE_IN_USE_DELAY)
        else:
            break


def _move_completed_file(old_path: str, new_path: str, max_attempts: int = 5) -> None:
    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        try:
            os.rename(old_path, new_path)
        except PermissionError:
            time.sleep(FILE_IN_USE_DELAY)
        else:
            break
    subprocess.run(["chown", f"{settings.puid}:{settings.pgid}", new_path], check=True)
    subprocess.run(["chmod", "775", new_path], check=True)


class Video:
    BITRATES = {"tv": 2000000, "movie": 4000000, "animation": 1000000}

    TARGET_EXTENSION = "mp4"
    TARGET_WIDTH = 1920

    TEMP_EXTENSION = "tmp"
    TIMEOUT = 20000

    LOGGER = logging.getLogger(__name__)

    def __init__(self, path: str, media_type: str, indent: str = "") -> None:
        self.path = path
        self.was_target_extension = self.path.endswith("." + Video.TARGET_EXTENSION)
        self.type = media_type
        self.indent = indent

    def _log(self, message: str, level: int = logging.INFO) -> None:
        self.LOGGER.log(level, self.indent + message)

    def _manual_bitrate(self, streams: list[dict[str, str]]) -> int:
        bit_rate = 0
        for stream in streams:
            bit_rate -= int(stream.get("bit_rate", 0))
        args = [
            "ffprobe",
            "-hide_banner",
            "-loglevel",
            "fatal",
            "-show_format",
            "-of",
            "json",
            self.path,
        ]
        raw = subprocess.check_output(args)
        bit_rate += int(json.loads(raw)["format"]["bit_rate"])
        return bit_rate

    def _get_file_info(self) -> dict[str, str]:
        # TODO: Parse json data using pydantic
        args = [
            "ffprobe",
            "-hide_banner",
            "-loglevel",
            "fatal",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,codec_name,bit_rate",
            "-of",
            "json",
            self.path,
        ]
        try:
            raw_data = subprocess.check_output(args)
        except subprocess.CalledProcessError:
            return {}
        streams = json.loads(raw_data)["streams"]
        data = streams[0]
        if "bit_rate" not in data:
            data["bit_rate"] = str(self._manual_bitrate(streams))
        self._log(
            f"Codec: {data.get('codec_name', 'unknown')}"
            + f" | Width: {data.get('width', 'unknown')}"
            + f" | Bitrate: {data.get('bit_rate', 'unknown')}",
            level=logging.DEBUG,
        )
        return data  # type: ignore[no-any-return]

    def _get_params(self) -> dict[str, str] | None:
        file_info = self._get_file_info()
        try:
            width = int(file_info["width"])
            rate = int(file_info["bit_rate"])
        except KeyError:
            raise Exception("Unable to determine file info")  # TODO: Better exception

        rate_modifier = width / Video.TARGET_WIDTH
        target_rate = int(rate_modifier * Video.BITRATES[self.type])
        params = {
            "c:a": "ac3",
            "c:s": "mov_text",  # TODO: Add support for other subtitle types
            "movflags": "+faststart",  # Moves moov atom to start of file
        }

        if rate >= (target_rate * 1.05):
            params["c:v"] = "hevc_nvenc"
            params["preset"] = "slow"
            params["b:v"] = format_rate(target_rate)
        else:
            if self.was_target_extension:
                return None
            else:
                params["c:v"] = "copy"
        return params

    def transcode(self, drop_subs: bool = False) -> bool:
        # TODO: timeout? could do on subprocess.run
        start = time.time()

        with tracer.start_as_current_span("transcode") as span:
            span.set_attribute("transcode.path", self.path)
            span.set_attribute("transcode.media_type", self.type)
            span.set_attribute("transcode.drop_subs", drop_subs)

            params = self._get_params()
            if params is None:
                self._log("No Transcode Required")
                span.set_attribute("transcode.skipped", True)
                return False

            span.set_attribute("transcode.skipped", False)
            if "c:v" in params:
                span.set_attribute("transcode.video_codec", params["c:v"])
            if "b:v" in params:
                span.set_attribute("transcode.target_bitrate", params["b:v"])

            if drop_subs:
                params.pop("c:s")
            self._log(f"Params: {params}", level=logging.DEBUG)

            base_path, extension = os.path.splitext(self.path)
            output_path = f"{base_path}.tmp"
            success = True
            try:
                args = [
                    "ffmpeg",
                    "-hide_banner",
                    "-y",
                    "-v",
                    "error",
                    "-stats",
                    "-i",
                    self.path,
                    "-map",
                    "0:a?",
                    "-map",
                    "0:V",
                    "-f",
                    self.TARGET_EXTENSION,
                ]
                if not drop_subs:
                    args += ["-map", "0:s?"]
                for flag, value in params.items():
                    args += ["-" + flag, value]
                args += [output_path]

                result = subprocess.run(args)
                if result.returncode == 0:
                    self._log("Successfully Transcoded")
                    span.set_attribute("transcode.success", True)
                    _delete_old_file(self.path)
                    _move_completed_file(
                        output_path, f"{base_path}.{Video.TARGET_EXTENSION}"
                    )
                else:
                    # TODO: Better exception
                    raise Exception(
                        "Transcode Failed with command: ",
                        subprocess.list2cmdline(result.args),
                    )
            except BaseException as exc:
                success = False
                span.set_attribute("transcode.success", False)
                span.record_exception(exc)
                span.set_status(trace.StatusCode.ERROR, str(exc))
                self.LOGGER.exception("Transcode Failed")
                if os.path.exists(output_path):
                    self._log("Deleting partial output file")
                    _delete_old_file(output_path)
                if not drop_subs:
                    self._log("Retrying without subtitles")
                    return self.transcode(drop_subs=True)
            finally:
                duration = time.time() - start
                runtime = datetime.timedelta(seconds=int(round(duration)))
                self._log(f"Time taken: {runtime}", level=logging.DEBUG)
            return success

    @classmethod
    def transcode_from_path(cls, path: str, video_type: str | None = None) -> bool:
        if video_type is None:
            video_type = get_video_type(path)
        if video_type is None:
            cls.LOGGER.error(f"Invalid path received: {path}")
            return False
        cls.LOGGER.info(f"Received file {path}")
        video = Video(path, video_type, indent="\t")
        return video.transcode()
