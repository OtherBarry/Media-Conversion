from flask import Flask, request
from videos import Video
import datetime
import json

app = Flask(__name__)


@app.route('/radarr', methods=['POST'])
def radarr():
    data = json.loads(request.data)
    if data["eventType"] == "Download":
        id = data["movieFile"]["id"]
        relative_path = data["movieFile"]["relativePath"]
        path = data["movieFile"]["path"]
        print("{}. {} ({})".format(id, path, relative_path))
    elif data["eventType"] == "Test":
        print("This is a test")
    return "OK"


@app.route('/sonarr', methods=['POST'])
def sonarr():
    data = json.loads(request.data)
    if data["eventType"] == "Download":
        log("\nDownload received at {}".format(datetime.datetime.now()))
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
            params = vid.params.copy()
            params.pop("i")
            log("\tParams: {}".format(params))
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
    log("Converter Started at {}".format(datetime.datetime.now()))
    app.run()
