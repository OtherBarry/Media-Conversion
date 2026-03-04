from pathlib import Path
from typing import TypedDict, NotRequired

import httpx


class _MovieFile(TypedDict):
    path: str


class _GetMovieResponse(TypedDict):
    movieFile: NotRequired[_MovieFile]
    hasFile: bool


class MovieNotDownloadedError(Exception):
    pass


class RadarrClient:
    def __init__(self, base_url: str, api_key: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url, headers={"X-Api-Key": api_key}
        )

    async def get_movie_path(self, movie_id: int) -> Path:
        response = await self._client.get(f"/api/v3/movie/{movie_id}")
        response.raise_for_status()
        data: _GetMovieResponse = response.json()
        if data["hasFile"]:
            movie_file = data.get("movieFile")
            if movie_file is None:
                raise ValueError(
                    "Inconsistent API response: 'hasFile' is True but 'movieFile' is missing."
                )
            return Path(movie_file["path"])
        raise MovieNotDownloadedError(
            f"Movie with ID {movie_id} has not been downloaded."
        )
