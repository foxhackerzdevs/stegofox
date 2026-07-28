"""
Tests for stegofox.py: crypto round-trip, LSB embed/extract round-trip,
and edge cases (capacity, wrong password, corrupted/absent payload).

Regression coverage: embed_lsb used to crash on every call due to a
NumPy 2.x incompatibility (`~1` as a Python int against a uint8 array).
"""
import sys
import os
import shutil
import tempfile
import unittest

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from stegofox.stegofox import (
    derive_key, encrypt_payload, decrypt_payload, embed_lsb, extract_lsb,
)


def make_random_image(path, w=64, h=64):
    arr = (np.random.rand(h, w, 3) * 255).astype(np.uint8)
    Image.fromarray(arr).save(path)


class TestCryptoRoundTrip(unittest.TestCase):
    def test_encrypt_decrypt_round_trip(self):
        data = b"the quick brown fox"
        blob = encrypt_payload(data, "hunter2")
        self.assertEqual(decrypt_payload(blob, "hunter2"), data)

    def test_wrong_password_returns_none(self):
        blob = encrypt_payload(b"secret", "correct")
        self.assertIsNone(decrypt_payload(blob, "wrong"))

    def test_tampered_ciphertext_returns_none(self):
        blob = bytearray(encrypt_payload(b"secret", "pw"))
        blob[-1] ^= 0xFF  # flip a bit in the ciphertext
        self.assertIsNone(decrypt_payload(bytes(blob), "pw"))

    def test_derive_key_is_deterministic_for_same_salt(self):
        salt = b"0" * 16
        self.assertEqual(derive_key("pw", salt), derive_key("pw", salt))

    def test_derive_key_differs_for_different_salt(self):
        self.assertNotEqual(derive_key("pw", b"0" * 16), derive_key("pw", b"1" * 16))


class TestLSBRoundTrip(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.cover = os.path.join(self.tmpdir, "cover.png")
        make_random_image(self.cover, 64, 64)  # 64*64*3 = 12288 bits capacity

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_plaintext_round_trip(self):
        out = os.path.join(self.tmpdir, "out.png")
        secret = b"hello stegofox, this is a secret message!"
        embed_lsb(self.cover, secret, out)
        self.assertTrue(os.path.exists(out))
        self.assertEqual(extract_lsb(out), secret)

    def test_encrypted_round_trip_correct_password(self):
        out = os.path.join(self.tmpdir, "out.png")
        secret = b"top secret payload"
        embed_lsb(self.cover, secret, out, password="correcthorse")
        self.assertEqual(extract_lsb(out, password="correcthorse"), secret)

    def test_encrypted_round_trip_wrong_password(self):
        out = os.path.join(self.tmpdir, "out.png")
        embed_lsb(self.cover, b"top secret", out, password="correct")
        self.assertIsNone(extract_lsb(out, password="wrong"))

    def test_extract_from_clean_image_returns_none(self):
        self.assertIsNone(extract_lsb(self.cover))

    def test_capacity_exceeded_does_not_write_output(self):
        tiny = os.path.join(self.tmpdir, "tiny.png")
        make_random_image(tiny, 4, 4)  # 4*4*3 = 48 bits capacity
        out = os.path.join(self.tmpdir, "out.png")
        embed_lsb(tiny, b"this payload is way too big for a 4x4 image", out)
        self.assertFalse(os.path.exists(out))

    def test_empty_secret_round_trips(self):
        out = os.path.join(self.tmpdir, "out.png")
        embed_lsb(self.cover, b"", out)
        self.assertEqual(extract_lsb(out), b"")

    def test_binary_secret_round_trips(self):
        out = os.path.join(self.tmpdir, "out.png")
        secret = bytes(range(256)) * 4
        embed_lsb(self.cover, secret, out)
        self.assertEqual(extract_lsb(out), secret)

    def test_nonexistent_cover_image_does_not_crash(self):
        out = os.path.join(self.tmpdir, "out.png")
        embed_lsb("/no/such/file.png", b"data", out)
        self.assertFalse(os.path.exists(out))

    def test_nonexistent_stego_image_does_not_crash(self):
        self.assertIsNone(extract_lsb("/no/such/file.png"))


if __name__ == "__main__":
    unittest.main()
