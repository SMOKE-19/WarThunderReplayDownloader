from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from http.cookies import SimpleCookie
from pathlib import Path
import time
from typing import Any
from urllib.parse import urlparse

import browser_cookie3
import requests

from .config import ReplayDownloadConfig


@dataclass(slots=True)
class ReplaySearchResult:
    session_id: str
    replay_id: str
    payload: dict[str, Any]


def download_replay(config: ReplayDownloadConfig) -> list[Path]:
    session = build_authenticated_session(config)
    matched_replay = find_replay_by_user_and_session(session, config)
    replay_detail = fetch_replay_detail(session, config, matched_replay.session_id)
    replay_parts = replay_detail.get("replay_parts") or []

    if not replay_parts:
        raise RuntimeError("Replay detail did not include any replay parts.")

    config.download_root.mkdir(parents=True, exist_ok=True)

    download_jobs = [
        (url, config.download_root / replay_filename_from_url(url))
        for url in replay_parts
    ]
    total_jobs = len(download_jobs)
    completed_jobs = 0
    downloaded_files: list[Path] = []

    print(
        f"[{config.session_id}] Starting download of {total_jobs} part(s) "
        f"with {config.max_workers} worker(s)."
    )

    with ThreadPoolExecutor(max_workers=max(1, config.max_workers)) as executor:
        future_to_job = {
            executor.submit(download_file, session, config, url, target_path): (url, target_path)
            for url, target_path in download_jobs
        }

        for future in as_completed(future_to_job):
            _, target_path = future_to_job[future]
            future.result()
            downloaded_files.append(target_path)
            completed_jobs += 1
            print_progress(config.session_id, completed_jobs, total_jobs, target_path.name)

    downloaded_files.sort()
    return downloaded_files


def build_authenticated_session(config: ReplayDownloadConfig) -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": config.user_agent,
            "Referer": config.replay_page_url,
            "Accept": "application/json, text/plain, */*",
        }
    )

    if config.login_cookie:
        apply_cookie_header(session, config.login_cookie)
    elif config.use_edge_cookies:
        session.cookies.update(browser_cookie3.edge(domain_name="warthunder.com"))
    else:
        raise RuntimeError(
            "No login method configured. Enable Edge cookies or set "
            "WARTHUNDER_LOGIN_COOKIE."
        )

    response = session.get(config.replay_page_url, timeout=config.timeout_seconds)
    if "login.gaijin.net" in response.url or "Single Sign On" in response.text:
        raise RuntimeError(
            "Replay page redirected to the Gaijin login page. "
            "Edge cookie auto-login did not work, so set "
            "WARTHUNDER_LOGIN_COOKIE in the process environment."
        )

    return session


def find_replay_by_user_and_session(
    session: requests.Session, config: ReplayDownloadConfig
) -> ReplaySearchResult:
    payload = build_search_payload(config, page=1)
    response = session.post(
        config.replays_api_url,
        json=payload,
        timeout=config.timeout_seconds,
    )
    response.raise_for_status()

    data = response.json()
    match = find_session_match(data.get("items", []), config.session_id)
    if match is not None:
        return match

    sum_pages = ((data.get("pagination") or {}).get("sumPages")) or 1
    max_page = min(sum_pages, config.max_pages)

    for page in range(2, max_page + 1):
        payload = build_search_payload(config, page=page)
        response = session.post(
            config.replays_api_url,
            json=payload,
            timeout=config.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()

        match = find_session_match(data.get("items", []), config.session_id)
        if match is not None:
            return match

    raise RuntimeError(
        f"Could not find SESSION_ID '{config.session_id}' in replay search results "
        f"for USER_ID '{config.user_id}'."
    )


def fetch_replay_detail(
    session: requests.Session,
    config: ReplayDownloadConfig,
    session_id: str,
) -> dict[str, Any]:
    response = session.get(
        f"{config.replays_api_url}/{session_id}",
        timeout=config.timeout_seconds,
    )
    response.raise_for_status()
    data = response.json()

    replay = data.get("replay") or {}
    replay_session_id = str(replay.get("sessionIdHex") or "").lower()
    if replay_session_id != session_id.lower():
        raise RuntimeError(
            "Replay detail response did not match the requested SESSION_ID."
        )

    return data


def build_search_payload(config: ReplayDownloadConfig, page: int) -> dict[str, Any]:
    return {
        "gameMode": list(config.game_modes),
        "gameType": config.game_type,
        "techType": config.tech_type,
        "findMissionValue": "",
        "findUserValue": config.user_id,
        "findUserType": "ID",
        "isUserOwnReplays": False,
        "rankRange": "",
        "timeRangeFrom": "",
        "timeRangeTo": "",
        "timeRangeFromDay": 8,
        "timeRangeFromMonth": 2,
        "timeRangeFromTime": "10:00",
        "timeRangeToDay": 10,
        "timeRangeToMonth": 5,
        "timeRangeToTime": "14:00",
        "limit": config.page_size,
        "page": page,
    }


def find_session_match(
    items: list[dict[str, Any]],
    expected_session_id: str,
) -> ReplaySearchResult | None:
    expected = expected_session_id.lower()
    for item in items:
        session_id = str(item.get("sessionIdHex") or "").lower()
        if session_id != expected:
            continue
        return ReplaySearchResult(
            session_id=session_id,
            replay_id=str(item.get("id") or ""),
            payload=item,
        )
    return None


def apply_cookie_header(session: requests.Session, cookie_header: str) -> None:
    cookie = SimpleCookie()
    cookie.load(cookie_header)
    for morsel in cookie.values():
        session.cookies.set(morsel.key, morsel.value)


def download_file(
    session: requests.Session,
    config: ReplayDownloadConfig,
    url: str,
    target_path: Path,
) -> None:
    if target_path.exists() and target_path.stat().st_size > 0:
        print(f"[{config.session_id}] Skip existing {target_path.name}")
        return

    temp_path = target_path.with_suffix(target_path.suffix + ".part")
    last_error: Exception | None = None

    for attempt in range(1, config.download_retries + 1):
        if temp_path.exists():
            temp_path.unlink()

        try:
            with session.get(url, timeout=config.timeout_seconds, stream=True) as response:
                response.raise_for_status()
                with temp_path.open("wb") as file_handle:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            file_handle.write(chunk)
            temp_path.replace(target_path)
            return
        except requests.RequestException as exc:
            last_error = exc
            if temp_path.exists():
                temp_path.unlink()
            if attempt == config.download_retries:
                break
            print(
                f"[{config.session_id}] Retry {attempt}/{config.download_retries - 1} "
                f"for {target_path.name}: {exc}"
            )
            time.sleep(config.retry_delay_seconds)

    raise RuntimeError(
        f"Failed to download '{target_path.name}' after {config.download_retries} attempts: "
        f"{last_error}"
    )


def replay_filename_from_url(url: str) -> str:
    parsed = urlparse(url)
    name = Path(parsed.path).name
    return name or "replay.wrpl"


def print_progress(session_id: str, completed: int, total: int, filename: str) -> None:
    percent = (completed / total) * 100
    print(f"[{session_id}] Progress {completed}/{total} ({percent:5.1f}%) - {filename}")
