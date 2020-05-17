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
        return "OK"
    elif data["eventType"] == "Test":
        print("This is a test")
        return "OK"


@app.route('/sonarr', methods=['POST'])
def sonarr():
    data = json.loads(request.data)
    if data["eventType"] == "Download":
        folder = data["series"]["path"]
        file = data["episodeFile"]["relativePath"]
        path = folder + "\\" + file
        log(path)
        vid = Video(path, "tv")
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
        else:
            log("\tNo Transcode Required")
        log("\n")


def log(line):
    log_file = "logs/{} Webserver Log.txt".format(datetime.date.today())
    print(line)
    with open(log_file, "a", encoding="utf8") as f:
        f.write(line + "\n")


if __name__ == '__main__':
    log("Converter Started at {}".format(datetime.datetime.now()))
    app.run()
