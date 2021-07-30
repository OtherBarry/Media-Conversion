import datetime
import glob
import os

from videos import Video, transcode_file
from redis import Redis
from rq import Queue


MEDIA_LIBRARIES = {
    "tv": "/data/media/TV Shows/",
    "movie": "/data/media/Movies/",
    "animation": "/data/media/Animated TV Shows/",
}
TYPES = ["**/*." + x for x in Video.FILE_EXTENSIONS]


def log(line):
    log_file = "logs/{}_bulk_transcode.txt".format(datetime.date.today())
    print(line)
    with open(log_file, "a", encoding="utf8") as f:
        f.write(line + "\n")


log("Converter Started at {}".format(datetime.datetime.now().strftime("%H:%M:%S")))
q = Queue(connection=Redis(), default_timeout=3600)
for file_type in TYPES:
    for media_type, media_dir in MEDIA_LIBRARIES.items():
        for file in glob.glob(media_dir + file_type, recursive=True):
            file = os.path.abspath(file)
            log(f"Queued for transcoding: {file}")
            q.enqueue(transcode_file, file, media_type, job_timeout=3600)
