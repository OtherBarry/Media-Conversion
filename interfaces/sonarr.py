from pathlib import Path
from typing import TypedDict, NotRequired

import httpx


class _EpisodeFile(TypedDict):
    path: str


class _GetEpisodeResponse(TypedDict):
    episodeFile: NotRequired[_EpisodeFile]
    hasFile: bool


class EpisodeNotDownloadedError(Exception):
    pass


class SonarrClient:
    def __init__(self, base_url: str, api_key: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url, headers={"X-Api-Key": api_key}
        )

    async def get_episode_path(self, episode_id: int) -> Path:
        response = await self._client.get(f"/api/v3/episode/{episode_id}")
        response.raise_for_status()
        data: _GetEpisodeResponse = response.json()
        if data["hasFile"]:
            episode_file = data.get("episodeFile")
            if episode_file is None:
                raise ValueError(
                    "Inconsistent API response: 'hasFile' is True but 'episodeFile' is missing."
                )
            return Path(episode_file["path"])
        raise EpisodeNotDownloadedError(
            f"Episode with ID {episode_id} has not been downloaded."
        )
