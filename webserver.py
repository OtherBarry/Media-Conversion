import json
import logging

import requests
import rq_dashboard
from flask import Flask, request, redirect, jsonify
from redis import Redis
from rq import Queue
from werkzeug.serving import make_server
from werkzeug.wrappers.response import Response

from videos import LOGGER as logger
from videos import transcode_file, Video


class Webserver:
    def __init__(self):
        self._flask_app = Flask("webserver")
        self._flask_app.config.from_object(rq_dashboard.default_settings)
        self._flask_app.register_blueprint(rq_dashboard.blueprint, url_prefix="/rq")
        self._add_urls_to_app()
        self._server = make_server("0.0.0.0", 6969, self._flask_app)
        self.queue = Queue(connection=Redis(), default_timeout=Video.TIMEOUT)
        self._flask_app.logger.disabled = True
        log = logging.getLogger('werkzeug')
        log.disabled = True
        logger.info("Started webserver")

    def _add_urls_to_app(self) -> None:
        self._flask_app.add_url_rule(
            rule="/radarr", view_func=self.radarr, methods=["POST"]
        )
        self._flask_app.add_url_rule(
            rule="/sonarr", view_func=self.sonarr, methods=["POST"]
        )
        self._flask_app.add_url_rule(
            rule="/", view_func=self.redirect_home, methods=["GET"]
        )

    def start(self) -> None:
        self._server.serve_forever()

    def stop(self) -> None:
        self._server.shutdown()

    def redirect_home(self) -> Response:
        return redirect("/rq")

    def radarr(self) -> Response:
        data = json.loads(request.data)
        if data["eventType"] == "Download":
            logger.info("Download received from Radarr")
            movie_id = data["movie"]["id"]
            data = requests.get(
                "http://192.168.0.10:7878/api/movie/{}".format(movie_id),
                params={"apikey": "26c68f7dfb6d4ad481a33e32a4bf1579"},
            ).json()
            if not data["downloaded"]:
                logger.error("\tAPI Error: Movie not labelled 'downloaded'.")
                return jsonify({"result": "success"})
            path = data["path"] + "/" + data["movieFile"]["relativePath"]
            logger.info("\tFile: " + path)
            self.queue.enqueue(transcode_file, path, "movie", job_timeout=Video.TIMEOUT)
            logger.info("\tFile queued for encoding")
        elif data["eventType"] == "Test":
            print("This is a test")
        return jsonify({"result": "success"})

    def sonarr(self) -> Response:
        data = json.loads(request.data)
        if data["eventType"] == "Download":
            logger.info("Download received from Sonarr")
            folder = data["series"]["path"]
            file = data["episodeFile"]["relativePath"]
            path = folder + "/" + file
            logger.info("\tFile: " + path)
            self.queue.enqueue(transcode_file, path, job_timeout=Video.TIMEOUT)
            logger.info("\tFile queued for encoding")
        return jsonify({"result": "success"})


if __name__ == "__main__":
    webserver = Webserver()
    webserver.start()
