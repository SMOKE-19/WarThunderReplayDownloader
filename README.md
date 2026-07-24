# WarThunderReplayDownloader

Python tool to download all `.wrpl` parts for a War Thunder server replay.

This version is no longer based on manual URL editing. It works like the replay website:

1. Search replay results by `USER_ID`
2. Find the matching replay by `SESSION_ID`
3. Fetch replay metadata from War Thunder's replay API
4. Download every replay part into a session-specific folder

## Features

- `src/` package layout
- Search by `USER_ID`
- Match exact replay by `SESSION_ID`
- Uses the replay API instead of scraping HTML
- Reads Edge login cookies automatically
- Parallel part downloads
- Retry handling for dropped connections
- Progress output while downloading
- Optional reset of the target session folder before each run

## Requirements

- Python `3.10+`
- Microsoft Edge already logged in to `warthunder.com`

If Edge cookie auto-login does not work, set the `WARTHUNDER_LOGIN_COOKIE`
environment variable for the downloader process.

## Install

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

If you do not want editable install mode:

```bash
pip install .
```

## Configure

Edit [download_replay.py](./download_replay.py) and set:

```python
USER_ID = "0000000"
SESSION_IDS = [
    "0000000000000000",
]
```

Important:

- `USER_ID` is the War Thunder player ID used in replay search
- `SESSION_IDS` is the replay session hex ID list you want to download
- Each session is stored in `Downloads/<session_id>/`

Useful settings in the same file:

- `USE_EDGE_COOKIES = True`
- `MAX_WORKERS = 3`
- `DOWNLOAD_RETRIES = 5`
- `RETRY_DELAY_SECONDS = 2.0`
- `RESET_SESSION_DIR_ON_START = True`

Optional environment variables:

- `WARTHUNDER_REPLAY_DOWNLOAD_ROOT`: output root (defaults to the project's
  `Downloads` directory)
- `WARTHUNDER_LOGIN_COOKIE`: fallback login cookie used only by the downloader
  process

## Run

```bash
source .venv/bin/activate
python download_replay.py
```

## Output

Replay files are saved under:

```text
<download_root>/<session_id>/
```

Example file layout:

```text
Downloads/
  0123456789abcdef/
    0000.wrpl
    0001.wrpl
    0002.wrpl
    ...
```

## Progress Output

During download you will see messages like:

```text
[0123456789abcdef] Starting download of 34 part(s) with 3 worker(s).
[0123456789abcdef] Progress 12/34 ( 35.3%) - 0011.wrpl
```

If a file already exists and folder reset is disabled:

```text
[0123456789abcdef] Skip existing 0011.wrpl
```

## Login Handling

Default behavior:

- The script loads cookies from Microsoft Edge with `browser-cookie3`
- If your Edge session is already logged into `warthunder.com`, no extra login step is needed

Fallback behavior:

- Set `USE_EDGE_COOKIES = False`
- Set `WARTHUNDER_LOGIN_COOKIE` in the downloader process environment

## Notes

- The replay website currently requires an authenticated web session
- High worker counts may cause more connection resets
- `2` to `3` workers is a safer starting point than very high parallelism

## Project Structure

```text
download_replay.py
pyproject.toml
src/warthunder_replay_downloader/
```
