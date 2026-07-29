#!/usr/bin/env python3
"""
StegoFox Pro - High-performance encrypted steganography CLI
"""

import sys
import hashlib
import struct
import argparse
from pathlib import Path
from typing import Optional
import numpy as np

try:
    from PIL import Image
    from Crypto.Cipher import AES
    from Crypto.Random import get_random_bytes
except ImportError:
    print("❌ Error: Missing dependencies. Run: pip install pillow numpy pycryptodome")
    sys.exit(1)

STEGO_SIGNATURE = b"SFOX"

def derive_key(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100_000, dklen=32)

def encrypt_payload(data: bytes, password: str) -> bytes:
    salt = get_random_bytes(16)
    key = derive_key(password, salt)
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    return salt + cipher.nonce + tag + ciphertext

def decrypt_payload(payload: bytes, password: str) -> Optional[bytes]:
    try:
        salt = payload[:16]
        nonce = payload[16:32]
        tag = payload[32:48]
        ciphertext = payload[48:]
        key = derive_key(password, salt)
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag)
    except Exception:
        return None

def get_capacity(image_path: str) -> int:
    """Return approximate capacity in bytes."""
    try:
        img = Image.open(image_path).convert("RGB")
        return np.array(img).size // 8
    except Exception:
        return 0

def embed_lsb(image_path: str, data: bytes, output_path: str, password: Optional[str] = None):
    print(f"📸 Loading cover image: {image_path}")
    try:
        img = Image.open(image_path).convert("RGB")
    except Exception as e:
        print(f"❌ Failed to read image: {e}")
        return

    capacity = get_capacity(image_path)
    print(f"📏 Image capacity: ~{capacity:,} bytes")

    if password:
        print("🔐 Encrypting payload...")
        data = encrypt_payload(data, password)

    full_payload = STEGO_SIGNATURE + struct.pack(">I", len(data)) + data
    payload_bits = np.unpackbits(np.frombuffer(full_payload, dtype=np.uint8))

    img_array = np.array(img).copy()
    orig_shape = img_array.shape
    flat_img = img_array.ravel()
    max_bits = flat_img.size

    if len(payload_bits) > max_bits:
        print(f"❌ Secret too large ({len(payload_bits)} bits > {max_bits} capacity)")
        return

    print(f"🧬 Embedding {len(payload_bits)} bits...")
    flat_img[:len(payload_bits)] = (flat_img[:len(payload_bits)] & np.uint8(0xFE)) | payload_bits

    final_array = flat_img.reshape(orig_shape)
    Image.fromarray(final_array).save(output_path, format="PNG")
    print(f"✅ Successfully embedded! Saved to {output_path}")

def extract_lsb(image_path: str, password: Optional[str] = None) -> Optional[bytes]:
    print(f"🔍 Analyzing {image_path}")
    try:
        img = Image.open(image_path).convert("RGB")
    except Exception as e:
        print(f"❌ Failed to read image: {e}")
        return None

    img_array = np.array(img)
    flat_img = img_array.ravel()

    header_bits = flat_img[:64] & 1
    header_bytes = np.packbits(header_bits).tobytes()

    if not header_bytes.startswith(STEGO_SIGNATURE):
        print("❌ No StegoFox payload detected.")
        return None

    try:
        data_len = struct.unpack(">I", header_bytes[4:8])[0]
        total_bits = (8 + data_len) * 8

        if total_bits > flat_img.size:
            print("❌ Header indicates length out of bounds.")
            return None

        all_bits = flat_img[:total_bits] & 1
        all_bytes = np.packbits(all_bits).tobytes()
        raw_payload = all_bytes[8:8 + data_len]

        if password:
            print("🔓 Decrypting...")
            decrypted = decrypt_payload(raw_payload, password)
            if decrypted is None:
                print("❌ Decryption failed. Wrong password?")
                return None
            return decrypted
        return raw_payload
    except Exception as e:
        print(f"❌ Corrupted payload: {e}")
        return None

def main():
    print("🦊 StegoFox Pro\n")

    parser = argparse.ArgumentParser(description="High-performance encrypted steganography CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    embed_parser = subparsers.add_parser("embed", help="Embed secret into image")
    embed_parser.add_argument("image", type=str, help="Cover image path")
    embed_parser.add_argument("secret", type=str, help="Secret file to hide")
    embed_parser.add_argument("--output", "-o", type=str, default="stegofox_output.png", help="Output image path")
    embed_parser.add_argument("--password", "-p", type=str, default=None, help="Encryption password")

    extract_parser = subparsers.add_parser("extract", help="Extract hidden data")
    extract_parser.add_argument("image", type=str, help="Stego image path")
    extract_parser.add_argument("--password", "-p", type=str, default=None, help="Decryption password")

    args = parser.parse_args()

    if args.command == "embed":
        try:
            with open(args.secret, "rb") as f:
                data = f.read()
            embed_lsb(args.image, data, args.output, args.password)
        except Exception as e:
            print(f"Error during embedding: {e}")

    elif args.command == "extract":
        try:
            data = extract_lsb(args.image, args.password)
            if data is not None:
                print(f"✅ Extracted {len(data)} bytes")
                try:
                    print(data.decode('utf-8')[:500])
                except:
                    print(data[:500])
        except Exception as e:
            print(f"Error during extraction: {e}")

if __name__ == "__main__":
    main()
