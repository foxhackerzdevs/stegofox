# StegoFox Pro 🦊

**High-performance encrypted steganography CLI.**

Hide any file inside a PNG image using LSB (least-significant-bit) embedding, optionally encrypted with AES-256-GCM before it ever touches the pixels.

## Features
- LSB steganography — embed arbitrary binary data in a cover image's pixel data
- Optional AES-256-GCM encryption (PBKDF2-HMAC-SHA256, 100k iterations) before embedding
- Lossless PNG output — the embedding survives save/reload exactly
- Wrong-password and corrupted-payload detection fail cleanly (no crash, no garbage output)
- Capacity checking — refuses to embed data too large for the cover image, before touching anything, and prints an estimated capacity upfront

## Install
```bash
pip install stegofox
```

Or from source:
```bash
git clone https://github.com/foxhackerzdevs/stegofox.git
cd stegofox
pip install -e .
```

## Usage

```bash
stegofox embed cover.png secret.txt -o output.png
```

```bash
# With password protection
stegofox embed cover.png secret.txt -o output.png --password hunter2
```
```
🦊 StegoFox Pro

📸 Loading cover image: cover.png
📏 Image capacity: ~2,400 bytes
🔐 Encrypting payload...
🧬 Embedding 712 bits...
✅ Successfully embedded! Saved to output.png
```

```bash
stegofox extract output.png --password hunter2
```
```
🦊 StegoFox Pro

🔍 Analyzing output.png
🔓 Decrypting...
✅ Extracted 33 bytes
checking output messages exactly
```

```bash
# Wrong password fails cleanly, no crash
stegofox extract output.png --password wrongpass
```
```
🦊 StegoFox Pro

🔍 Analyzing output.png
🔓 Decrypting...
❌ Decryption failed. Wrong password?
```

## How it works
Each RGB channel byte of the cover image has its least-significant bit replaced with one bit of the payload. A 4-byte magic signature (`SFOX`) plus a 4-byte length header precede the payload so extraction knows exactly how much data to read back out. Output is always saved as PNG — a lossy format (JPEG, etc.) would destroy the embedded bits on save.

With `--password`, the payload is encrypted with AES-256-GCM (authenticated encryption) before embedding, so a wrong password fails the auth-tag check and returns a clean error rather than garbage bytes.

## Requirements
Python >= 3.8, `pillow`, `numpy`, `pycryptodome`.

## License
MIT
