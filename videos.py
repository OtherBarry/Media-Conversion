"""Class for analysing and transcoding video files."""

import os
import time
import json
import subprocess


class Video:

    BITRATES = {"tv": 2000000,
                "movie": 4000000,
                "animation": 1000000}

    FILE_EXTENSIONS = ("mkv",
                       "m4v",
                       "avi",
                       "wmv",
                       "mov",
                       "mp4")

    TARGET_EXTENSION = "mp4"

    TARGET_WIDTH = 1920

    def __init__(self, path, type):
        self.path = path
        self.was_target_extension = self.path.endswith("." + Video.TARGET_EXTENSION)
        self.type = type
        self.get_details()
        self.get_params()

    def get_details(self):
        try:
            data = self.get_data()
            self.codec = data["codec_name"]
            self.width = data["width"]
            self.rate = int(data["bit_rate"])
        except Exception:
            self.codec = "FFPROBE ERROR"
            self.width = Video.TARGET_WIDTH
            self.rate = 999999999

    def get_params(self):

        def format_rate(rate):
            return str(int(rate/1000)) + "k"

        rate_modifier = (self.width / Video.TARGET_WIDTH)
        target_rate = int(rate_modifier * Video.BITRATES[self.type])
        params = {"i": '"' + self.path + '"',
                  "c:v": "hevc_nvenc",
                  "c:a": "ac3",
                  "preset": "hq",
                  "2pass": "True",
                  "b:v": format_rate(target_rate)}
        needs_transcoding = True

        if self.rate < (target_rate * 1.05):
            if self.width <= Video.TARGET_WIDTH:
                if self.was_target_extension:
                    needs_transcoding = False
                else:
                    params["c:v"] = "copy"
                    params.pop("preset", None)
                    params.pop("2pass", None)
                    params.pop("b:v", None)
            else:
                params["vf"] = "scale={}:-1".format(Video.TARGET_WIDTH)
                rate = min(self.rate, Video.BITRATES[self.type])
                params["b:v"] = format_rate(rate)
        elif self.width > 1920:
            params["vf"] = "scale=1920:-1"

        self.params = params
        self.needs_transcoding = needs_transcoding

    def transcode(self):
        if not self.needs_transcoding:
            return True

        extension_length = len(Video.TARGET_EXTENSION)
        if self.was_target_extension:
            os.rename(self.path, self.path[:-extension_length])
            self.path = self.path[:-extension_length]
            self.params["i"] = '"' + self.path + '"'
            output = '"{}.{}"'.format(self.path, Video.TARGET_EXTENSION)
        else:
            output = '"{}.{}"'.format(self.path[:-extension_length],
                                      Video.TARGET_EXTENSION)
        args = ""
        for flag, value in self.params.items():
            args += " -" + flag + " " + value
        result = os.system(
            "ffmpeg -hide_banner -y -v fatal -stats {} {}".format(args, output)
        )
        if result == 0:
            while True:
                try:
                    os.remove(self.path)
                    break
                except PermissionError:
                    sys_path = self.path.replace("/", "\\")
                    result = os.system("del /f /q " + sys_path)
                    if result == 0:
                        break
                    log("File in use, waiting 30 seconds...")
                    time.sleep(30)
            self.path = output[1:-1]
            return True
        else:
            return False

    def get_data(self):
        command = 'ffprobe -hide_banner -loglevel fatal -show_entries stream=width,codec_name,bit_rate -of json "{}"'
        raw = subprocess.check_output(command.format(self.path))
        data = json.loads(raw)["streams"][0]
        try:
            rate = data["bit_rate"]
        except KeyError:
            bit_rate = 0
            for stream in json.loads(raw)["streams"]:
                if "bit_rate" in stream.keys():
                    bit_rate -= int(stream["bit_rate"])
            command = 'ffprobe -hide_banner -loglevel fatal -show_format -of json "{}"'
            raw = subprocess.check_output(command.format(self.path))
            bit_rate += int(json.loads(raw)["format"]["bit_rate"])
            data["bit_rate"] = str(bit_rate)
        return data
