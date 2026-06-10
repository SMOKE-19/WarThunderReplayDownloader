from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ReplayDownloadConfig:
    user_id: str
    session_id: str
    download_root: Path
    login_cookie: str = ""
    language: str = "en"
    use_edge_cookies: bool = True
    timeout_seconds: int = 30
    download_retries: int = 5
    retry_delay_seconds: float = 2.0
    max_workers: int = 3
    max_pages: int = 10
    page_size: int = 20
    game_modes: tuple[str, ...] = ("arcade", "realistic", "simulation")
    game_type: str = "randomBattle"
    tech_type: str = "all"
    user_agent: str = (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    )

    @property
    def replay_page_url(self) -> str:
        return f"https://warthunder.com/{self.language}/tournament/replay/"

    @property
    def replays_api_url(self) -> str:
        return f"https://warthunder.com/{self.language}/api/replay"
