from __future__ import annotations

from io import BytesIO

import pygame
from PIL import Image, ImageDraw, ImageFont


class TextRenderer:
    """Fallback text renderer using Pillow to avoid pygame.font circular import."""

    def __init__(self) -> None:
        """Initialize with a default font."""
        self._font_cache: dict[int, ImageFont.FreeTypeFont] = {}

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Get or create a font at the given size.

        Args:
            size: Font size in points.

        Returns:
            Pillow FreeTypeFont instance.
        """
        if size not in self._font_cache:
            try:
                self._font_cache[size] = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size
                )
            except OSError:
                self._font_cache[size] = ImageFont.load_default()
        return self._font_cache[size]

    def render(self, text: str, size: int, color: tuple[int, int, int]) -> pygame.Surface:
        """Render text to a pygame surface.

        Args:
            text: Text string to render.
            size: Font size in points.
            color: RGB color tuple.

        Returns:
            Pygame surface with the rendered text.
        """
        font = self._get_font(size)
        bbox = font.getbbox(text)
        width = bbox[2] - bbox[0] + 4
        height = bbox[3] - bbox[1] + 4
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((2, 2), text, font=font, fill=(*color, 255))
        with BytesIO() as buf:
            img.save(buf, format="BMP")
            buf.seek(0)
            surf = pygame.image.load(buf)
        return surf.convert_alpha()
