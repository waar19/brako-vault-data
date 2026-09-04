import hashlib
import base64
import struct
import tempfile
import unittest
from pathlib import Path

import build_filter
import download_and_build


class BuildFilterTest(unittest.TestCase):
    def test_selects_most_prevalent_hashes(self) -> None:
        records = [
            build_filter.RankedHash(count=count, sha1=hashlib.sha1(name.encode()).digest())
            for name, count in (("low", 1), ("high", 9), ("middle", 5))
        ]

        selected = build_filter.select_most_prevalent(records, 2)

        self.assertEqual([9, 5], [record.count for record in selected])

    def test_generated_header_and_checksum_are_valid(self) -> None:
        records = [
            build_filter.RankedHash(count=7, sha1=hashlib.sha1(b"password").digest()),
            build_filter.RankedHash(count=3, sha1=hashlib.sha1(b"another").digest()),
        ]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "fixture.blf"
            build_filter.write_filter(output, records, corpus_epoch_day=20_000, probability=0.0001)
            content = output.read_bytes()

        self.assertEqual(build_filter.MAGIC, content[:8])
        version, header_size = struct.unpack(">II", content[8:16])
        item_count, bit_count = struct.unpack(">QQ", content[16:32])
        body_length = struct.unpack(">Q", content[44:52])[0]
        body = content[build_filter.HEADER_SIZE:]

        self.assertEqual(build_filter.FORMAT_VERSION, version)
        self.assertEqual(build_filter.HEADER_SIZE, header_size)
        self.assertEqual(2, item_count)
        self.assertEqual((bit_count + 7) // 8, body_length)
        self.assertEqual(hashlib.sha256(body).digest(), content[52:84])

    def test_range_parser_restores_full_hash_and_ignores_padding(self) -> None:
        payload = (
            b"00000000000000000000000000000000000:0\r\n"
            b"11111111111111111111111111111111111:42\r\n"
        )

        records = download_and_build.parse_range("ABCDE", payload)

        self.assertEqual([(42, bytes.fromhex("ABCDE" + "1" * 35))], records)

    def test_content_md5_is_required_and_verified(self) -> None:
        payload = b"range response"
        checksum = base64.b64encode(
            hashlib.md5(payload, usedforsecurity=False).digest()
        ).decode("ascii")

        self.assertTrue(download_and_build.content_md5_matches(payload, checksum))
        self.assertFalse(download_and_build.content_md5_matches(payload + b"x", checksum))
        self.assertFalse(download_and_build.content_md5_matches(payload, None))


if __name__ == "__main__":
    unittest.main()
