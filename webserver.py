import datetime
import json

import requests
from flask import Flask, request
from redis import Redis
from rq import Queue
from werkzeug.serving import make_server

from videos import transcode_file


class Webserver:
    def __init__(self):
        self._flask_app = Flask("webserver")
        self._add_urls_to_app()
        self._server = make_server("127.0.0.1", 6969, self._flask_app)
        self.queue = Queue(connection=Redis(), default_timeout=3600)
        self._log("Webserver Started at {}".format(datetime.datetime.now()))

    def _add_urls_to_app(self) -> None:
        self._flask_app.add_url_rule(
            rule="/radarr", view_func=self.radarr, methods=["POST"]
        )
        self._flask_app.add_url_rule(
            rule="/sonarr", view_func=self.sonarr, methods=["POST"]
        )

    def start(self) -> None:
        self._server.serve_forever()

    def stop(self) -> None:
        self._server.shutdown()

    def _log(self, line):
        log_file = "logs/{}_webserver.txt".format(datetime.date.today())
        print(line)
        with open(log_file, "a", encoding="utf8") as f:
            f.write(line + "\n")

    def radarr(self):
        data = json.loads(request.data)
        if data["eventType"] == "Download":
            self._log(
                f"\nDownload received from Radarr at {datetime.datetime.now().strftime('%H:%M:%S')}"
            )
            movie_id = data["movie"]["id"]
            data = requests.get(
                "http://192.168.0.10:7878/api/movie/{}".format(movie_id),
                params={"apikey": "26c68f7dfb6d4ad481a33e32a4bf1579"},
            ).json()
            if not data["downloaded"]:
                self._log("\tAPI Error: Movie not labelled 'downloaded'.")
                return "OK"
            path = data["path"] + "/" + data["movieFile"]["relativePath"]
            self._log("\tFile: " + path)
            self.queue.enqueue(transcode_file, path, "movie", job_timeout=3600)
            self._log("\tFile queued for encoding")
        elif data["eventType"] == "Test":
            print("This is a test")
        return "OK"

    def sonarr(self):
        data = json.loads(request.data)
        if data["eventType"] == "Download":
            self._log(
                f"\nDownload received from Sonarr at {datetime.datetime.now().strftime('%H:%M:%S')}"
            )
            folder = data["series"]["path"]
            file = data["episodeFile"]["relativePath"]
            path = folder + "/" + file
            self._log("\tFile: " + path)
            self.queue.enqueue(transcode_file, path)
            self._log("\tFile queued for encoding")
        return "OK"


if __name__ == "__main__":
    webserver = Webserver()
    webserver.start()
