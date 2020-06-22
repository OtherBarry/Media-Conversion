from flask import Flask, request
from videos import Video
import datetime
import requests
import json
import os

app = Flask(__name__)


@app.route('/radarr', methods=['POST'])
def radarr():
    data = json.loads(request.data)
    if data["eventType"] == "Download":
        log("\nDownload received from Radarr at {}".format(datetime.datetime.now()))
        id = data["movie"]["id"]
        data = requests.get("http://192.168.0.10:7878/api/movie/{}".format(id),
                            params={"apikey": "26c68f7dfb6d4ad481a33e32a4bf1579"}).json()
        if not data["downloaded"]:
            log("\tAPI Error: Movie not labelled 'downloaded'.")
            return "OK"
        path = data["path"] + "/" + data["movieFile"]["relativePath"]
        path = path.replace("/data/media/", "M:/")
        log("\tFile: " + path)
        vid = Video(path, "movie")
        log("\tCodec: {}\n\tWidth: {}\n\tBitrate: {}".format(vid.codec,
                                                             vid.width,
                                                             vid.rate))
        if vid.needs_transcoding:
            log("\tParams: {}".format(vid.params))
            if vid.transcode():
                log("\tSuccessfully Transcoded")
            else:
                log("\tTranscode Failed")
            log("\tTranscode ended at {}".format(datetime.datetime.now()))
        else:
            log("\tNo Transcode Required")
    elif data["eventType"] == "Test":
        print("This is a test")
    return "OK"


@app.route('/sonarr', methods=['POST'])
def sonarr():
    data = json.loads(request.data)
    if data["eventType"] == "Download":
        log("\nDownload received from Sonarr at {}".format(datetime.datetime.now()))
        folder = data["series"]["path"]
        file = data["episodeFile"]["relativePath"]
        path = folder + "/" + file
        path = path.replace("/data/media/", "M:/")
        if path.startswith("M:/Animated TV Shows/"):
            type = "animation"
        else:
            type = "tv"
        log("\tFile: " + path)
        vid = Video(path, type)
        log("\tCodec: {}\n\tWidth: {}\n\tBitrate: {}".format(vid.codec,
                                                             vid.width,
                                                             vid.rate))
        if vid.needs_transcoding:
            log("\tParams: {}".format(vid.params))
            if vid.transcode():
                log("\tSuccessfully Transcoded")
            else:
                log("\tTranscode Failed")
            log("\tTranscode ended at {}".format(datetime.datetime.now()))
        else:
            log("\tNo Transcode Required")
    return "OK"


def log(line):
    log_file = "logs/{} Webserver Log.txt".format(datetime.date.today())
    print(line)
    with open(log_file, "a", encoding="utf8") as f:
        f.write(line + "\n")


if __name__ == '__main__':
    log("Webserver Started at {}".format(datetime.datetime.now()))
    app.run()
