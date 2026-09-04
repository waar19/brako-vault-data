#!/usr/bin/env python3
"""Measure the empirical false positive rate of a Brako Vault Bloom filter.

Usage:
    python tools/leaked-password-filter/measure_fpr.py FILTER [--samples N] [--seed S]

The script parses the `.blf` header (magic BRKBLM01, 84 bytes), verifies the
body SHA-256 checksum, then queries N random candidate passwords (seeded for
reproducibility) that are extremely unlikely to appear in the underlying
corpus. The ratio of `mightContain == true` candidates to the total is the
empirical FPR for the artifact on disk.

The query algorithm mirrors `LeakedPasswordFilter.mightContainSha1` in the
Android client exactly: SHA-256 of the SHA-1 of the password, two 64-bit big
endian lanes combined with the double-hashing scheme (Kirsch-Mitzenmacher).
"""

from __future__ import annotations

import argparse
import hashlib
import random
import struct
import sys
from pathlib import Path

MAGIC = b"BRKBLM01"
HEADER_SIZE = 84
DEFAULT_SAMPLES = 50_000
DEFAULT_SEED = 42


class FilterFormatError(ValueError):
    """Raised when a `.blf` file does not match the expected format."""


def parse_filter(path: Path) -> tuple[bytes, int, int, int, int, int]:
    """Return (body_bytes, item_count, bit_count, hash_count, epoch_day, body_length)."""
    data = path.read_bytes()
    if len(data) < HEADER_SIZE:
        raise FilterFormatError(f"file shorter than header ({len(data)} < {HEADER_SIZE})")

    magic = data[:8]
    if magic != MAGIC:
        raise FilterFormatError(f"unexpected magic {magic!r}")

    version, header_size, item_count, bit_count, hash_count, epoch_day, body_length = struct.unpack(
        ">IIQQIqQ", data[8 : 8 + 44]
    )
    if header_size != HEADER_SIZE:
        raise FilterFormatError(f"unexpected header size {header_size}")

    expected_body_length = (bit_count + 7) // 8
    if body_length != expected_body_length:
        raise FilterFormatError(
            f"body length {body_length} does not match bit count {bit_count}"
        )
    if len(data) - HEADER_SIZE != body_length:
        raise FilterFormatError(
            f"file size {len(data)} does not match header + body {HEADER_SIZE + body_length}"
        )

    body = data[HEADER_SIZE:]
    expected_digest = hashlib.sha256(body).digest()
    if expected_digest != bytes(data[HEADER_SIZE - 32 : HEADER_SIZE]):
        raise FilterFormatError("body SHA-256 checksum mismatch")

    return body, item_count, bit_count, hash_count, epoch_day, body_length


def might_contain(body: bytes, bit_count: int, hash_count: int, password: str) -> bool:
    """Mirror the Kotlin `mightContain`/`mightContainSha1` algorithm exactly."""
    sha1 = hashlib.sha1(password.encode("utf-8")).digest()
    digest = hashlib.sha256(sha1).digest()
    first, second = struct.unpack(">QQ", digest[:16])
    second |= 1
    for index in range(hash_count):
        bit_index = (first + second * index) % bit_count
        if not (body[bit_index >> 3] & (1 << (bit_index & 7))):
            return False
    return True


def measure(
    path: Path, samples: int, seed: int
) -> tuple[int, int, int, int, int, int, float]:
    body, item_count, bit_count, hash_count, epoch_day, body_length = parse_filter(path)

    rng = random.Random(seed)
    positives = 0
    for index in range(samples):
        candidate = f"brako-fpr-probe-{rng.getrandbits(64):016x}-{index}"
        if might_contain(body, bit_count, hash_count, candidate):
            positives += 1

    fpr = positives / samples if samples else 0.0
    return (
        item_count,
        bit_count,
        hash_count,
        epoch_day,
        body_length,
        positives,
        fpr,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("filter", type=Path, help="path to a .blf artifact")
    parser.add_argument("--samples", type=int, default=DEFAULT_SAMPLES)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    try:
        (
            item_count,
            bit_count,
            hash_count,
            epoch_day,
            body_length,
            positives,
            fpr,
        ) = measure(args.filter, args.samples, args.seed)
    except FilterFormatError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    print(
        f"filter={args.filter}\n"
        f"itemCount={item_count} bitCount={bit_count} hashCount={hash_count} "
        f"bodyBytes={body_length} epochDay={epoch_day}\n"
        f"samples={args.samples} seed={args.seed} positives={positives} "
        f"empiricalFpr={fpr:.6f}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
