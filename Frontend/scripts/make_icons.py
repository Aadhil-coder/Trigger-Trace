#!/usr/bin/env python3
"""Create the PWA app icons in public/icons/ using only the Python standard library.

Run from the frontend folder:
    python scripts/make_icons.py

Makes:
    public/icons/icon-192.png          (Android home screen)
    public/icons/icon-512.png          (install dialog and splash)
    public/icons/apple-touch-icon.png  (iPhone home screen, 180 px)
"""
import os
import struct
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "..", "public", "icons")
TEAL = (27, 138, 143)   # brand accent, matches the deck
WHITE = (255, 255, 255)


def make_png(size):
    """Draw a teal rounded square with a white cross, a simple health mark."""
    radius = size * 0.22
    cross_w = size * 0.20
    cross_len = size * 0.56
    center = size / 2.0

    def inside_rounded(x, y):
        cx = min(max(x, radius), size - radius)
        cy = min(max(y, radius), size - radius)
        return (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2 or (radius <= x <= size - radius) or (radius <= y <= size - radius)

    def in_cross(x, y):
        vertical = abs(x - center) <= cross_w / 2 and abs(y - center) <= cross_len / 2
        horizontal = abs(y - center) <= cross_w / 2 and abs(x - center) <= cross_len / 2
        return vertical or horizontal

    raw = bytearray()
    for y in range(size):
        raw.append(0)  # filter type: none
        for x in range(size):
            px, py = x + 0.5, y + 0.5
            if not inside_rounded(px, py):
                raw += bytes((0, 0, 0, 0))              # transparent corners
            elif in_cross(px, py):
                raw += bytes(WHITE) + bytes((255,))
            else:
                raw += bytes(TEAL) + bytes((255,))

    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)  # 8-bit RGBA
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    targets = {"icon-192.png": 192, "icon-512.png": 512, "apple-touch-icon.png": 180}
    for name, size in targets.items():
        path = os.path.join(OUT_DIR, name)
        with open(path, "wb") as f:
            f.write(make_png(size))
        print(f"Wrote {path} ({size}x{size})")


if __name__ == "__main__":
    main()
