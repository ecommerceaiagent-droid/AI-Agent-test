import struct
import zlib

WIDTH = 2500
HEIGHT = 843

_FONT = {
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
}


def render_sample_menu_png() -> bytes:
    green = bytes((6, 199, 85))
    ink = bytes((18, 50, 38))
    white = bytes((255, 255, 255))
    pixels = bytearray()
    half = WIDTH // 2
    for _y in range(HEIGHT):
        pixels.extend(green * half)
        pixels.extend(ink * (WIDTH - half))

    _draw_page_icon(pixels, 485, 145, white)
    _draw_card_icon(pixels, half + 430, 175, white)
    _draw_text(pixels, "SAMPLE 1", 193, 560, 18, white)
    _draw_text(pixels, "SAMPLE 2", half + 193, 560, 18, white)
    return _png(WIDTH, HEIGHT, pixels)


def _draw_text(pixels: bytearray, text: str, x: int, y: int, scale: int, color: bytes) -> None:
    cursor = x
    for char in text:
        glyph = _FONT[char]
        for row, bits in enumerate(glyph):
            for col, bit in enumerate(bits):
                if bit != "1":
                    continue
                _fill_rect(pixels, cursor + col * scale, y + row * scale, scale - 2, scale - 2, color)
        cursor += 6 * scale


def _draw_page_icon(pixels: bytearray, x: int, y: int, color: bytes) -> None:
    _fill_rect(pixels, x, y, 280, 340, color)
    _fill_rect(pixels, x + 170, y, 110, 90, bytes((4, 122, 54)))
    _fill_rect(pixels, x + 40, y + 130, 200, 18, bytes((18, 50, 38)))
    _fill_rect(pixels, x + 40, y + 180, 200, 18, bytes((18, 50, 38)))
    _fill_rect(pixels, x + 40, y + 230, 130, 18, bytes((18, 50, 38)))


def _draw_card_icon(pixels: bytearray, x: int, y: int, color: bytes) -> None:
    _fill_rect(pixels, x, y, 390, 280, color)
    _fill_rect(pixels, x, y, 390, 70, bytes((6, 199, 85)))
    _fill_rect(pixels, x + 28, y + 110, 150, 130, bytes((6, 199, 85)))


def _fill_rect(pixels: bytearray, x: int, y: int, width: int, height: int, color: bytes) -> None:
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(WIDTH, x + width)
    y1 = min(HEIGHT, y + height)
    for row in range(y0, y1):
        start = (row * WIDTH + x0) * 3
        end = (row * WIDTH + x1) * 3
        pixels[start:end] = color * (x1 - x0)


def _png(width: int, height: int, pixels: bytearray) -> bytes:
    raw = bytearray()
    stride = width * 3
    for row in range(height):
        raw.append(0)
        raw.extend(pixels[row * stride : (row + 1) * stride])

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")
