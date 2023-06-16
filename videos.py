import datetime
import json
import logging
import os
import subprocess
import time
from logging.handlers import WatchedFileHandler

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


log_handler = WatchedFileHandler("/var/log/transcoder/transcoder.log")
formatter = logging.Formatter(
    "%(asctime)s - [%(levelname)s] %(message)s", "%b %d %H:%M:%S"
)
log_handler.setFormatter(formatter)


class Video:
    BITRATES = {"tv": 2000000, "movie": 4000000, "animation": 1000000}

    TARGET_EXTENSION = "mp4"
    TARGET_WIDTH = 1920

    TEMP_EXTENSION = "tmp"
    TIMEOUT = 20000

    LOG_LEVEL = logging.DEBUG
    LOGGER = logging.getLogger()

    def __init__(self, path: str, media_type: str, indent: str = "") -> None:
        self.path = path
        self.was_target_extension = self.path.endswith("." + Video.TARGET_EXTENSION)
        self.type = media_type
        self.indent = indent

    LOGGER.setLevel(LOG_LEVEL)
    LOGGER.addHandler(log_handler)

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

        params = self._get_params()
        if params is None:
            self._log("No Transcode Required")
            return False
        if drop_subs:
            params.pop("c:s")
        self._log(f"Params: {params}", level=logging.DEBUG)

        base_path, extension = os.path.splitext(self.path)
        if extension_matches(extension, Video.TARGET_EXTENSION):
            temp_path = f"{base_path}.{self.TEMP_EXTENSION}"
            self._log(
                f"Renaming file to {temp_path} as file already has target extension",
                level=logging.DEBUG,
            )
            os.rename(self.path, temp_path)
            self.path = temp_path

        output_path = f"{base_path}.{Video.TARGET_EXTENSION}"
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
            ]
            if not drop_subs:
                args += ["-map", "0:s?"]
            for flag, value in params.items():
                args += ["-" + flag, value]
            args += [output_path]

            result = subprocess.run(args)
            if result.returncode == 0:
                self._log("Successfully Transcoded")
                _delete_old_file(self.path)
                subprocess.run(["chmod", "a+rw", output_path])
            else:
                # TODO: Better exception
                raise Exception(
                    "Transcode Failed with command: ",
                    subprocess.list2cmdline(result.args),
                )
        except BaseException:
            success = False
            self._log("Transcode Failed", level=logging.ERROR)
            if os.path.exists(output_path):
                self._log("Deleting partial output file")
                _delete_old_file(output_path)
            base_path, extension = os.path.splitext(self.path)
            if extension_matches(extension, Video.TEMP_EXTENSION) and os.path.exists(
                self.path
            ):
                new_path = f"{base_path}.{Video.TARGET_EXTENSION}"
                self._log(
                    f"Renaming file from {self.path} to {new_path}",
                    level=logging.DEBUG,
                )
                os.rename(self.path, new_path)
                self.path = new_path
            if not drop_subs:
                self._log("Retrying without subtitles")
                return self.transcode(drop_subs=True)
        finally:
            runtime = datetime.timedelta(seconds=int(round(time.time() - start)))
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
