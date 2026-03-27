"""Render the SVG app icon into a multi-size Windows ICO file."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, Qt
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_SVG = PROJECT_ROOT / "src" / "dorkvault" / "assets" / "icons" / "app_icon.svg"
OUTPUT_ICO = PROJECT_ROOT / "src" / "dorkvault" / "assets" / "icons" / "app_icon.ico"
ROOT_OUTPUT_ICO = PROJECT_ROOT / "app_icon.ico"


def main() -> int:
    app = QGuiApplication.instance() or QGuiApplication([])
    renderer = QSvgRenderer(str(SOURCE_SVG))
    if not renderer.isValid():
        print(f"Unable to load SVG icon source: {SOURCE_SVG}", file=sys.stderr)
        return 1

    png_frames = [(size, _render_png_bytes(renderer, size)) for size in ICON_SIZES]
    ico_bytes = _build_ico(png_frames)
    OUTPUT_ICO.write_bytes(ico_bytes)
    ROOT_OUTPUT_ICO.write_bytes(ico_bytes)
    print(f"Wrote {OUTPUT_ICO}")
    print(f"Wrote {ROOT_OUTPUT_ICO}")
    app.quit()
    return 0


def _render_png_bytes(renderer: QSvgRenderer, size: int) -> bytes:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    _add_background_padding(image)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    renderer.render(painter)
    painter.end()

    buffer_bytes = QByteArray()
    buffer = QBuffer(buffer_bytes)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    buffer.close()
    return bytes(buffer_bytes)


def _add_background_padding(image: QImage) -> None:
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    color = QColor("#17212b")
    color.setAlpha(14)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    inset = max(1, image.width() // 32)
    radius = max(2, image.width() // 6)
    painter.drawRoundedRect(inset, inset, image.width() - (inset * 2), image.height() - (inset * 2), radius, radius)
    painter.end()


def _build_ico(png_frames: list[tuple[int, bytes]]) -> bytes:
    header = struct.pack("<HHH", 0, 1, len(png_frames))
    directory_entries: list[bytes] = []
    image_payloads: list[bytes] = []
    offset = 6 + (16 * len(png_frames))

    for size, png_bytes in png_frames:
        width = 0 if size >= 256 else size
        height = 0 if size >= 256 else size
        directory_entries.append(
            struct.pack(
                "<BBBBHHII",
                width,
                height,
                0,
                0,
                1,
                32,
                len(png_bytes),
                offset,
            )
        )
        image_payloads.append(png_bytes)
        offset += len(png_bytes)

    return header + b"".join(directory_entries) + b"".join(image_payloads)


if __name__ == "__main__":
    raise SystemExit(main())
