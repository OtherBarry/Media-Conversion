import os
import glob
from videos import Video
import datetime


LOG_NAME = "Daily Log.txt"


def log(line):
    print(line)
    with open(LOG_NAME, "a") as f:
        f.write(line + "\n")


with open(LOG_NAME, "w") as f:
    f.write("Converter Started at {}".format(datetime.datetime.now()) + "\n")

media_libraries = {"tv": "T:/TV Shows/",
                   "movie": "W:/Movies/"}
types = ["**/*." + x for x in Video.FILE_EXTENSIONS]
for media_type, media_dir in media_libraries.items():
    for type in types:
        for file in glob.glob(media_dir + type, recursive=True):
            file = os.path.abspath(file)
            log(file)
            vid = Video(file, media_type)
            log("\tCodec: {}\n\tWidth: {}\n\tBitrate: {}".format(vid.codec,
                                                                 vid.width,
                                                                 vid.rate))
            log("\tParams: {}".format(vid.params))
            if vid.transcode():
                if vid.needs_transcoding:
                    log("\tSuccessfully Transcoded")
                else:
                    log("\tNo Transcode Required")
            else:
                log("\tTranscode Failed")
            log("\n")
