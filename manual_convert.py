import glob
import os

from redis import Redis
from rq import Queue

from videos import Video

MEDIA_LIBRARIES = {
    "tv": "/data/media/TV Shows/",
    "movie": "/data/media/Movies/",
    "animation": "/data/media/Animated TV Shows/",
}
TYPES = ["**/*." + x for x in Video.FILE_EXTENSIONS]

Video.LOGGER.info("Starting manual conversion")
q = Queue(connection=Redis(), default_timeout=Video.TIMEOUT)
for file_type in TYPES:
    for media_type, media_dir in MEDIA_LIBRARIES.items():
        for file in glob.glob(media_dir + file_type, recursive=True):
            file = os.path.abspath(file)
            Video.LOGGER.info(f"Queued for transcoding: {file}")
            q.enqueue(
                Video.transcode_from_path, file, media_type, job_timeout=Video.TIMEOUT
            )
