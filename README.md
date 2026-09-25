# StegoFox Pro 🦊

**High-performance encrypted steganography CLI.**

**More about me / other projects:** [abhrankan.netlify.app](https://abhrankan.netlify.app)

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
# With password protection -- omit the value to be prompted (recommended)
stegofox embed cover.png secret.txt -o output.png --password
# Password:
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
stegofox extract output.png --password
# Password:
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
stegofox extract output.png --password
# Password: (wrong password entered)
```
```
🦊 StegoFox Pro

🔍 Analyzing output.png
🔓 Decrypting...
❌ Decryption failed. Wrong password?
```

`--password <value>` (passing it directly) is also accepted for scripted use, but prints a warning to stderr — the password is visible in shell history and to other local users via `ps`. Prefer the prompted form above for interactive use.

## How it works
Each RGB channel byte of the cover image has its least-significant bit replaced with one bit of the payload. A 4-byte magic signature (`SFOX`) plus a 4-byte length header precede the payload so extraction knows exactly how much data to read back out. Output is always saved as PNG — a lossy format (JPEG, etc.) would destroy the embedded bits on save.

With `--password`, the payload is encrypted with AES-256-GCM (authenticated encryption) before embedding, so a wrong password fails the auth-tag check and returns a clean error rather than garbage bytes.

## Security Notes
- `--password` never touches CLI args when used interactively — omit the value to be prompted via `getpass`. The `--password <value>` form is still accepted for scripts, but leaks the password into shell history and `ps`.
- Encryption is AES-256-GCM (authenticated) — a wrong password or corrupted payload fails the auth-tag check cleanly rather than returning garbage.
- Key derivation is PBKDF2-HMAC-SHA256 at 100,000 iterations, not Argon2id. This is a known tradeoff, not an oversight: **the iteration count isn't stored in the embedded payload**, so changing it (or switching KDFs) would make every already-embedded image undecryptable with a newer version. Strengthening this later requires a self-describing payload format first — noted here rather than silently left undocumented.

## Requirements
Python >= 3.8, `pillow`, `numpy`, `pycryptodome`.

## License
MIT
