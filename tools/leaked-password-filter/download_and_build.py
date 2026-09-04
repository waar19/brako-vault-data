#!/usr/bin/env python3
"""Stream Pwned Passwords ranges and build Brako Vault filters without a full corpus file."""

from __future__ import annotations

import argparse
import base64
import hashlib
import heapq
import hmac
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import build_filter

PREFIX_COUNT = 16**5
API_URL = "https://api.pwnedpasswords.com/range/{prefix}"
USER_AGENT = "Brako-Vault-offline-filter-builder/1"


def parse_range(prefix: str, payload: bytes) -> list[tuple[int, bytes]]:
    records: list[tuple[int, bytes]] = []
    for line_number, raw_line in enumerate(payload.splitlines(), start=1):
        if not raw_line:
            continue
        try:
            suffix_text, count_text = raw_line.split(b":", 1)
            suffix = suffix_text.decode("ascii").upper()
            if len(suffix) != 35 or any(char not in "0123456789ABCDEF" for char in suffix):
                raise ValueError("invalid SHA-1 suffix")
            count = int(count_text)
            if count < 0:
                raise ValueError("negative count")
            if count > 0:
                records.append((count, bytes.fromhex(prefix + suffix)))
        except (UnicodeDecodeError, ValueError) as error:
            raise ValueError(f"Prefix {prefix}, line {line_number}: {error}") from error
    return records


def content_md5_matches(payload: bytes, expected_base64: str | None) -> bool:
    if not expected_base64:
        return False
    actual = hashlib.md5(payload, usedforsecurity=False).digest()
    try:
        expected = base64.b64decode(expected_base64, validate=True)
    except ValueError:
        return False
    return hmac.compare_digest(actual, expected)


def fetch_range(prefix_number: int, retries: int) -> list[tuple[int, bytes]]:
    prefix = f"{prefix_number:05X}"
    request = urllib.request.Request(
        API_URL.format(prefix=prefix),
        headers={"User-Agent": USER_AGENT},
    )
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = response.read()
                expected_md5 = response.headers.get("Content-MD5")
            if not content_md5_matches(payload, expected_md5):
                raise OSError(f"Content-MD5 verification failed for {prefix}")
            return parse_range(prefix, payload)
        except Exception as error:
            last_error = error
            if attempt == retries:
                break
            time.sleep(min(2**attempt, 10))
    raise RuntimeError(f"Could not download prefix {prefix}") from last_error


def update_top(heap: list[tuple[int, bytes]], records: list[tuple[int, bytes]], limit: int) -> None:
    for item in records:
        if len(heap) < limit:
            heapq.heappush(heap, item)
        elif item > heap[0]:
            heapq.heapreplace(heap, item)


def download_top(limit: int, workers: int, retries: int) -> list[build_filter.RankedHash]:
    top: list[tuple[int, bytes]] = []
    batch_size = workers * 8
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for batch_start in range(0, PREFIX_COUNT, batch_size):
            batch_end = min(batch_start + batch_size, PREFIX_COUNT)
            futures = [
                executor.submit(fetch_range, prefix_number, retries)
                for prefix_number in range(batch_start, batch_end)
            ]
            for future in as_completed(futures):
                update_top(top, future.result(), limit)
            if batch_end % 4096 == 0 or batch_end == PREFIX_COUNT:
                print(
                    f"downloaded={batch_end}/{PREFIX_COUNT} selected={len(top)}/{limit}",
                    flush=True,
                )
    return [
        build_filter.RankedHash(count=count, sha1=sha1)
        for count, sha1 in sorted(top, reverse=True)
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-date", required=True)
    parser.add_argument("--base-output", type=Path, required=True)
    parser.add_argument("--base-limit", type=build_filter.positive_int, default=1_000_000)
    parser.add_argument("--expansion-output", type=Path, required=True)
    parser.add_argument("--expansion-limit", type=build_filter.positive_int, default=10_000_000)
    parser.add_argument("--workers", type=build_filter.positive_int, default=64)
    parser.add_argument("--retries", type=int, default=5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.base_limit > args.expansion_limit:
        raise ValueError("base limit cannot exceed expansion limit")
    if args.workers > 128:
        raise ValueError("workers cannot exceed 128")
    if args.retries < 0:
        raise ValueError("retries cannot be negative")

    selected = download_top(args.expansion_limit, args.workers, args.retries)
    if len(selected) < args.base_limit:
        raise ValueError(
            f"Corpus returned only {len(selected)} hashes; base requires {args.base_limit}"
        )
    build_filter.write_filter(
        args.base_output,
        selected[: args.base_limit],
        build_filter.epoch_day(args.corpus_date),
        build_filter.FALSE_POSITIVE_RATE,
    )
    build_filter.write_filter(
        args.expansion_output,
        selected,
        build_filter.epoch_day(args.corpus_date),
        build_filter.FALSE_POSITIVE_RATE,
    )


if __name__ == "__main__":
    main()
