"""Class for analysing and transcoding video files."""

import datetime
import json
import os
import subprocess
import time
from typing import Dict, Optional

FOLDER_TYPE_MAP = {
    "Animated TV Shows": "animation",
    "Movies": "movie",
    "TV Shows": "tv",
}


def log(line: str) -> None:
    log_file = "logs/{}_transcode_log.txt".format(datetime.date.today())
    print(line)
    with open(log_file, "a", encoding="utf8") as f:
        f.write(line + "\n")


def transcode_file(path: str, video_type: Optional[str] = None) -> bool:
    log(f"\nStarted at {datetime.datetime.now().strftime('%H:%M:%S')}")
    start = time.time()
    if video_type is None:
        try:
            folder = path.split("/")[3]
            video_type = FOLDER_TYPE_MAP.get(folder)
        except IndexError:
            video_type = None

    if video_type is None:
        log(f"Invalid path received: {path}")
        return False

    log(f"Received file {path}")
    video = Video(path, video_type)
    log(
        "\tCodec: {}\n\tWidth: {}\n\tBitrate: {}".format(
            video.codec, video.width, video.rate
        )
    )
    if video.needs_transcoding:
        log("\tParams: {}".format(video.params))
        if video.transcode():
            log("\tSuccessfully Transcoded")
        else:
            log("\tTranscode Failed")
        runtime = datetime.timedelta(seconds=int(round(time.time() - start)))
        log(f"\tTime taken: {runtime}")
    else:
        log("\tNo Transcode Required")
    return True


class Video:
    BITRATES = {"tv": 2000000, "movie": 4000000, "animation": 1000000}
    FILE_EXTENSIONS = (
        "mkv",
        "m4v",
        "avi",
        "wmv",
        "mov",
        "mp4",
    )
    TARGET_EXTENSION = "mp4"
    TARGET_WIDTH = 1920
    TIMEOUT = 7200

    def __init__(self, path: str, media_type: str) -> None:
        self.path = path
        self.was_target_extension = self.path.endswith("." + Video.TARGET_EXTENSION)
        self.type = media_type
        self.get_details()
        self.get_params()

    def get_details(self) -> None:
        try:
            data = self.get_data()
            self.codec = data["codec_name"]
            self.width = int(data["width"])
            self.rate = int(data["bit_rate"])
        except Exception:
            self.codec = "FFPROBE ERROR"
            self.width = Video.TARGET_WIDTH
            self.rate = 999999999

    def get_params(self) -> None:
        def format_rate(rate: int) -> str:
            return str(int(rate / 1000)) + "k"

        rate_modifier = self.width / Video.TARGET_WIDTH
        target_rate = int(rate_modifier * Video.BITRATES[self.type])
        params = {
            "c:v": "hevc_nvenc",
            "c:a": "ac3",
            "c:s": "mov_text",
            "preset": "slow",
            "b:v": format_rate(target_rate),
        }
        needs_transcoding = True

        if self.rate < (target_rate * 1.05):
            if self.was_target_extension:
                needs_transcoding = False
            else:
                params["c:v"] = "copy"
                params.pop("preset", None)
                params.pop("b:v", None)

        self.params = params
        self.needs_transcoding = needs_transcoding

    def transcode(self, drop_subs: bool = False) -> bool:
        if not self.needs_transcoding:
            return True

        extension_length = len(Video.TARGET_EXTENSION) + 1
        if self.was_target_extension:
            os.rename(self.path, self.path[:-extension_length])
            self.path = self.path[:-extension_length]
            self.params["i"] = '"' + self.path + '"'
            output = '"{}.{}"'.format(self.path, Video.TARGET_EXTENSION)
        else:
            output = '"{}.{}"'.format(
                self.path[:-extension_length], Video.TARGET_EXTENSION
            )
        args = '-i "{}" -map 0:a? -map 0:s? -map 0:V'.format(self.path)
        if drop_subs:
            args = args.replace(" -map 0:s?", "")
            self.params.pop("c:s")
        for flag, value in self.params.items():
            args += " -" + flag + " " + value
        result = os.system(
            "ffmpeg -hide_banner -y -v error -stats {} {}".format(args, output)
        )
        if result == 0:
            while True:
                try:
                    os.remove(self.path)
                    break
                except PermissionError:
                    result = os.system("rm " + self.path)
                    if result == 0:
                        break
                    log("\tFile in use, waiting 30 seconds...")
                    time.sleep(30)
            self.path = output[1:-1]
            subprocess.run(["chmod", "a+rw", self.path])
            return True
        else:
            if not drop_subs:
                return self.transcode(drop_subs=True)
            if self.was_target_extension:
                os.rename(self.path, self.path + ".mp4")
            return False

    def get_data(self) -> Dict[str, str]:
        command = f'ffprobe -hide_banner -loglevel fatal -select_streams v:0 -show_entries stream=width,codec_name,bit_rate -of json "{self.path}"'
        raw = subprocess.check_output(command, shell=True)
        data = json.loads(raw)["streams"][0]
        if "bit_rate" not in data:
            bit_rate = 0
            for stream in json.loads(raw)["streams"]:
                if "bit_rate" in stream.keys():
                    bit_rate -= int(stream["bit_rate"])
            command = f'ffprobe -hide_banner -loglevel fatal -show_format -of json "{self.path}"'
            raw = subprocess.check_output(command, shell=True)
            bit_rate += int(json.loads(raw)["format"]["bit_rate"])
            data["bit_rate"] = str(bit_rate)
        return data
