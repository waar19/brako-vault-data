#!/usr/bin/env python3
"""Build Brako Vault Bloom filters from Pwned Passwords HASH:COUNT files."""

from __future__ import annotations

import argparse
import hashlib
import heapq
import math
import os
import struct
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import BinaryIO, Iterable, Iterator

MAGIC = b"BRKBLM01"
FORMAT_VERSION = 1
HEADER_SIZE = 84
FALSE_POSITIVE_RATE = 0.0001


@dataclass(frozen=True)
class RankedHash:
    count: int
    sha1: bytes


def iter_sources(path: Path) -> Iterator[Path]:
    if path.is_file():
        yield path
        return
    if not path.is_dir():
        raise ValueError(f"Input does not exist: {path}")
    yield from sorted(candidate for candidate in path.rglob("*.txt") if candidate.is_file())


def prefix_for(path: Path) -> str:
    stem = path.stem.upper()
    return stem if len(stem) == 5 and all(char in "0123456789ABCDEF" for char in stem) else ""


def parse_line(raw_line: bytes, prefix: str, source: Path, line_number: int) -> RankedHash:
    try:
        hash_text, count_text = raw_line.strip().split(b":", 1)
        normalized = hash_text.decode("ascii").upper()
        if len(normalized) == 35 and prefix:
            normalized = prefix + normalized
        if len(normalized) != 40 or any(char not in "0123456789ABCDEF" for char in normalized):
            raise ValueError("expected a 40-character SHA-1")
        count = int(count_text)
        if count < 0:
            raise ValueError("count must be non-negative")
        return RankedHash(count=count, sha1=bytes.fromhex(normalized))
    except (UnicodeDecodeError, ValueError) as error:
        raise ValueError(f"{source}:{line_number}: invalid HASH:COUNT line ({error})") from error


def iter_ranked_hashes(path: Path) -> Iterator[RankedHash]:
    found_source = False
    for source in iter_sources(path):
        found_source = True
        prefix = prefix_for(source)
        with source.open("rb") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                if raw_line.strip():
                    yield parse_line(raw_line, prefix, source, line_number)
    if not found_source:
        raise ValueError(f"No .txt files found under {path}")


def select_most_prevalent(records: Iterable[RankedHash], limit: int) -> list[RankedHash]:
    if limit <= 0:
        raise ValueError("limit must be positive")
    heap: list[tuple[int, bytes]] = []
    for record in records:
        item = (record.count, record.sha1)
        if len(heap) < limit:
            heapq.heappush(heap, item)
        elif item > heap[0]:
            heapq.heapreplace(heap, item)
    if not heap:
        raise ValueError("Input did not contain hashes")
    return [RankedHash(count=count, sha1=sha1) for count, sha1 in sorted(heap, reverse=True)]


def bloom_parameters(item_count: int, probability: float) -> tuple[int, int]:
    if item_count <= 0:
        raise ValueError("item_count must be positive")
    if not 0.0 < probability < 1.0:
        raise ValueError("false positive rate must be between zero and one")
    bit_count = math.ceil(-item_count * math.log(probability) / (math.log(2.0) ** 2))
    hash_count = max(1, round((bit_count / item_count) * math.log(2.0)))
    return bit_count, hash_count


def set_filter_bits(body: bytearray, bit_count: int, hash_count: int, sha1: bytes) -> None:
    digest = hashlib.sha256(sha1).digest()
    first, second = struct.unpack(">QQ", digest[:16])
    second |= 1
    for index in range(hash_count):
        bit_index = ((first + second * index) & 0xFFFFFFFFFFFFFFFF) % bit_count
        body[bit_index >> 3] |= 1 << (bit_index & 7)


def write_filter(
    output: Path,
    records: list[RankedHash],
    corpus_epoch_day: int,
    probability: float,
) -> None:
    bit_count, hash_count = bloom_parameters(len(records), probability)
    body = bytearray((bit_count + 7) // 8)
    for record in records:
        set_filter_bits(body, bit_count, hash_count, record.sha1)

    header = b"".join(
        (
            MAGIC,
            struct.pack(">IIQQIqQ", FORMAT_VERSION, HEADER_SIZE, len(records), bit_count, hash_count,
                        corpus_epoch_day, len(body)),
            hashlib.sha256(body).digest(),
        )
    )
    if len(header) != HEADER_SIZE:
        raise AssertionError(f"Unexpected header size: {len(header)}")

    output.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    try:
        with os.fdopen(file_descriptor, "wb") as handle:
            write_all(handle, header)
            write_all(handle, body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, output)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise

    print(
        f"{output}: items={len(records)} bits={bit_count} hashes={hash_count} "
        f"bytes={HEADER_SIZE + len(body)} sha256={hashlib.sha256(output.read_bytes()).hexdigest()}"
    )


def write_all(handle: BinaryIO, content: bytes | bytearray) -> None:
    written = handle.write(content)
    if written != len(content):
        raise OSError(f"Short write: expected {len(content)}, wrote {written}")


def epoch_day(value: str) -> int:
    parsed = date.fromisoformat(value)
    return (parsed - date(1970, 1, 1)).days


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="HASH:COUNT file or downloader directory")
    parser.add_argument("--corpus-date", required=True, help="UTC date in YYYY-MM-DD format")
    parser.add_argument("--base-output", type=Path, required=True)
    parser.add_argument("--base-limit", type=positive_int, default=1_000_000)
    parser.add_argument("--expansion-output", type=Path)
    parser.add_argument("--expansion-limit", type=positive_int, default=10_000_000)
    parser.add_argument("--false-positive-rate", type=float, default=FALSE_POSITIVE_RATE)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    maximum = args.expansion_limit if args.expansion_output else args.base_limit
    if args.base_limit > maximum:
        raise ValueError("base limit cannot exceed expansion limit")

    selected = select_most_prevalent(iter_ranked_hashes(args.input), maximum)
    available_base = min(args.base_limit, len(selected))
    write_filter(
        args.base_output,
        selected[:available_base],
        epoch_day(args.corpus_date),
        args.false_positive_rate,
    )
    if args.expansion_output:
        write_filter(
            args.expansion_output,
            selected,
            epoch_day(args.corpus_date),
            args.false_positive_rate,
        )


if __name__ == "__main__":
    main()
