from flask import Flask, request
from videos import Video
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
        id = data["episodeFile"]["id"]
        path = data["series"]["path"] + "\\" + data["episodeFile"]["relativePath"]
        vid = Video(path, "tv")
        print("\tCodec: {}\n\tWidth: {}\n\tBitrate: {}".format(vid.codec,
                                                               vid.width,
                                                                vid.rate))
        print("\tParams: {}".format(vid.params))
        if vid.transcode():
            if vid.needs_transcoding:
                print("\tSuccessfully Transcoded")
            else:
                print("\tNo Transcode Required")
        else:
            print("\tTranscode Failed")
        print("\n")
        return "OK"
    elif data["eventType"] == "Test":
        print("This is a test")
        return "OK"



if __name__ == '__main__':
    app.run()


# {
#     "movieFile": {
#         "id": 2,
#         "relativePath": "Finding Nemo (2003) DVD.mkv",
#         "path": "Z:\\Finding.Nemo.2003.iNTERNAL.DVDRip.x264-REGRET\\regret-nemo.mkv",
#     },
# }
#
#
#
# # RADARR things to update from GET
# {
#   "sizeOnDisk": 0,
#   "year": 2016,
#   "path": "/path/to/Assassin's Creed (2016)",
#   "profileId": 6,
#   "qualityProfileId": 6,
# }
