import sys
from pathlib import Path
import shutil

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from warthunder_replay_downloader import ReplayDownloadConfig, download_replay

USER_ID = "0000000"
SESSION_IDS = [
    "0000000000000000",
]
DOWNLOAD_ROOT = Path("/home/smoke/Desktop/warthunder_replays/Downloads")
LOGIN_COOKIE = ""
USE_EDGE_COOKIES = True
DOWNLOAD_RETRIES = 5
RETRY_DELAY_SECONDS = 2.0
MAX_WORKERS = 3
RESET_SESSION_DIR_ON_START = True


def main() -> None:
    session_ids = [session_id.strip() for session_id in SESSION_IDS if session_id.strip()]
    if not session_ids:
        raise SystemExit("Set at least one SESSION_IDS entry at the top of download_replay.py.")

    for session_id in session_ids:
        download_dir = DOWNLOAD_ROOT / session_id
        if RESET_SESSION_DIR_ON_START and download_dir.exists():
            shutil.rmtree(download_dir)

        config = ReplayDownloadConfig(
            user_id=USER_ID,
            session_id=session_id,
            download_root=download_dir,
            login_cookie=LOGIN_COOKIE.strip(),
            use_edge_cookies=USE_EDGE_COOKIES,
            download_retries=DOWNLOAD_RETRIES,
            retry_delay_seconds=RETRY_DELAY_SECONDS,
            max_workers=MAX_WORKERS,
        )
        downloaded_files = download_replay(config)

        print(f"Downloaded {len(downloaded_files)} file(s) into: {download_dir}")
        for path in downloaded_files:
            print(f" - {path}")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, TimeoutError) as exc:
        raise SystemExit(str(exc))
