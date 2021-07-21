import os
import glob
from videos import Video
import datetime


def log(line):
    log_file = "logs/{} Log.txt".format(datetime.date.today())
    print(line)
    with open(log_file, "a", encoding="utf8") as f:
        f.write(line + "\n")


log("Converter Started at {}".format(datetime.datetime.now()))
media_libraries = {
    "tv": "M:/TV Shows/",
    "movie": "M:/Movies/",
    "animation": "M:/Animated TV Shows/",
}
types = ["**/*." + x for x in Video.FILE_EXTENSIONS]
for type in types:
    for media_type, media_dir in media_libraries.items():
        for file in glob.glob(media_dir + type, recursive=True):
            file = os.path.abspath(file)
            log(file)
            vid = Video(file, media_type)
            log("\tCodec: {}\n\tWidth: {}\n\tBitrate: {}".format(vid.codec,
                                                                 vid.width,
                                                                 vid.rate))
            if vid.needs_transcoding:
                log("\tParams: {}".format(vid.params))
                if vid.transcode():
                    log("\tSuccessfully Transcoded")
                else:
                    log("\tTranscode Failed")
            else:
                log("\tNo Transcode Required")
            log("\n")
