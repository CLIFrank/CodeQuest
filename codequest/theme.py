"""Visual constants shared by the CodeQuest interface."""

from __future__ import annotations

from typing import Final

import pygame


WIDTH: Final = 1280
HEIGHT: Final = 760
SIDEBAR_WIDTH: Final = 224

BG = (12, 15, 30)
SURFACE = (22, 26, 46)
SURFACE_2 = (29, 34, 58)
SURFACE_3 = (38, 43, 70)
INK = (241, 244, 255)
MUTED = (145, 153, 184)
FAINT = (84, 92, 123)
PURPLE = (132, 92, 246)
PURPLE_LIGHT = (174, 145, 255)
CYAN = (62, 210, 224)
GREEN = (65, 211, 151)
YELLOW = (255, 201, 92)
RED = (255, 104, 124)
WHITE = (255, 255, 255)
BLACK = (6, 8, 18)


def font(size: int, bold: bool = False, mono: bool = False) -> pygame.font.Font:
    """Return a system font with reliable fallbacks."""
    family = "consolas,couriernew,monospace" if mono else "segoeui,arial,sans"
    return pygame.font.SysFont(family, size, bold=bold)


def rounded_rect(
    target: pygame.Surface,
    rect: pygame.Rect,
    color: tuple[int, int, int],
    radius: int = 14,
    border: tuple[int, int, int] | None = None,
    border_width: int = 1,
) -> None:
    pygame.draw.rect(target, color, rect, border_radius=radius)
    if border:
        pygame.draw.rect(target, border, rect, border_width, border_radius=radius)


def draw_text(
    target: pygame.Surface,
    text: str,
    pos: tuple[int, int],
    size: int = 18,
    color: tuple[int, int, int] = INK,
    bold: bool = False,
    mono: bool = False,
    anchor: str = "topleft",
) -> pygame.Rect:
    rendered = font(size, bold, mono).render(text, True, color)
    rect = rendered.get_rect()
    setattr(rect, anchor, pos)
    target.blit(rendered, rect)
    return rect


def wrap_text(text: str, text_font: pygame.font.Font, max_width: int) -> list[str]:
    """Wrap prose into lines, preserving explicit newlines."""
    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        words = paragraph.split(" ")
        current = ""
        for word in words:
            candidate = word if not current else f"{current} {word}"
            if text_font.size(candidate)[0] <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        lines.append(current)
    return lines
