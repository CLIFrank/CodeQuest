"""Reusable Pygame controls for CodeQuest."""

from __future__ import annotations

import io
import keyword
import tokenize
from dataclasses import dataclass
from typing import Callable

import pygame

from .theme import (
    CYAN,
    FAINT,
    GREEN,
    INK,
    MUTED,
    PURPLE,
    PURPLE_LIGHT,
    RED,
    SURFACE_2,
    SURFACE_3,
    WHITE,
    YELLOW,
    draw_text,
    font,
    rounded_rect,
)


@dataclass
class Button:
    rect: pygame.Rect
    label: str
    action: Callable[[], None]
    kind: str = "secondary"
    icon: str = ""
    enabled: bool = True

    def handle(self, event: pygame.event.Event) -> bool:
        if (
            self.enabled
            and event.type == pygame.MOUSEBUTTONUP
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        ):
            self.action()
            return True
        return False

    def draw(self, target: pygame.Surface) -> None:
        hovered = self.enabled and self.rect.collidepoint(pygame.mouse.get_pos())
        if not self.enabled:
            bg, fg, border = SURFACE_2, FAINT, SURFACE_3
        elif self.kind == "primary":
            bg = PURPLE_LIGHT if hovered else PURPLE
            fg, border = WHITE, None
        elif self.kind == "success":
            bg = (82, 226, 166) if hovered else GREEN
            fg, border = (8, 35, 28), None
        elif self.kind == "danger":
            bg = (255, 130, 145) if hovered else RED
            fg, border = WHITE, None
        else:
            bg = SURFACE_3 if hovered else SURFACE_2
            fg, border = INK, (63, 70, 104)
        rounded_rect(target, self.rect, bg, 10, border)
        label = f"{self.icon}  {self.label}" if self.icon else self.label
        draw_text(target, label, self.rect.center, 15, fg, True, anchor="center")


class TextInput:
    def __init__(self, rect: pygame.Rect, placeholder: str, max_length: int = 80) -> None:
        self.rect = rect
        self.placeholder = placeholder
        self.max_length = max_length
        self.text = ""
        self.focused = False

    def handle(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.focused = self.rect.collidepoint(event.pos)
            return self.focused
        if not self.focused:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                return True
            if event.key == pygame.K_RETURN:
                return False
        if event.type == pygame.TEXTINPUT and len(self.text) < self.max_length:
            self.text += event.text.replace("\n", "")[: self.max_length - len(self.text)]
            return True
        return False

    def draw(self, target: pygame.Surface) -> None:
        border = PURPLE if self.focused else (60, 67, 98)
        rounded_rect(target, self.rect, SURFACE_2, 10, border, 2 if self.focused else 1)
        shown = self.text if self.text else self.placeholder
        color = INK if self.text else MUTED
        draw_text(target, shown, (self.rect.x + 14, self.rect.centery), 16, color, anchor="midleft")
        if self.focused and pygame.time.get_ticks() % 1000 < 500:
            fnt = font(16)
            cursor_x = self.rect.x + 14 + fnt.size(self.text)[0]
            pygame.draw.line(
                target,
                INK,
                (cursor_x, self.rect.y + 11),
                (cursor_x, self.rect.bottom - 11),
                2,
            )


class CodeEditor:
    """A compact multiline editor designed for short Python exercises."""

    PADDING_X = 12
    PADDING_Y = 10
    GUTTER = 48
    LINE_HEIGHT = 23

    def __init__(self, rect: pygame.Rect, text: str = "") -> None:
        self.rect = rect
        self.text = text
        self.cursor = len(text)
        self.focused = False
        self.scroll_y = 0
        self._preferred_col: int | None = None
        self._undo: list[tuple[str, int]] = []

    def set_text(self, value: str) -> None:
        self.text = value
        self.cursor = len(value)
        self.scroll_y = 0
        self._undo.clear()

    def get_text(self) -> str:
        return self.text

    def _remember(self) -> None:
        state = (self.text, self.cursor)
        if not self._undo or self._undo[-1] != state:
            self._undo.append(state)
            self._undo = self._undo[-100:]

    def _insert(self, value: str) -> None:
        self._remember()
        self.text = self.text[: self.cursor] + value + self.text[self.cursor :]
        self.cursor += len(value)
        self._preferred_col = None

    def _line_col(self) -> tuple[int, int]:
        before = self.text[: self.cursor]
        line = before.count("\n")
        col = len(before.rsplit("\n", 1)[-1])
        return line, col

    def _line_start(self, position: int | None = None) -> int:
        position = self.cursor if position is None else position
        return self.text.rfind("\n", 0, position) + 1

    def _line_end(self, position: int | None = None) -> int:
        position = self.cursor if position is None else position
        result = self.text.find("\n", position)
        return len(self.text) if result == -1 else result

    def _vertical_move(self, delta: int) -> None:
        line, col = self._line_col()
        lines = self.text.split("\n")
        target_line = max(0, min(len(lines) - 1, line + delta))
        if self._preferred_col is None:
            self._preferred_col = col
        self.cursor = sum(len(item) + 1 for item in lines[:target_line]) + min(
            self._preferred_col, len(lines[target_line])
        )

    def _clipboard_get(self) -> str:
        try:
            value = pygame.scrap.get(pygame.SCRAP_TEXT)
            if not value:
                return ""
            return value.decode("utf-8", errors="ignore").replace("\x00", "")
        except (pygame.error, UnicodeDecodeError):
            return ""

    def handle(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.focused = self.rect.collidepoint(event.pos)
            if self.focused:
                mono = font(16, mono=True)
                char_width = mono.size("M")[0]
                line = max(
                    0,
                    (event.pos[1] - self.rect.y - self.PADDING_Y) // self.LINE_HEIGHT
                    + self.scroll_y,
                )
                lines = self.text.split("\n")
                line = min(line, len(lines) - 1)
                col = max(
                    0,
                    (event.pos[0] - self.rect.x - self.GUTTER - self.PADDING_X + char_width // 2)
                    // char_width,
                )
                self.cursor = sum(len(item) + 1 for item in lines[:line]) + min(
                    col, len(lines[line])
                )
                self._preferred_col = None
            return self.focused
        if event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(pygame.mouse.get_pos()):
            max_scroll = max(0, len(self.text.splitlines()) - self.visible_lines)
            self.scroll_y = max(0, min(max_scroll, self.scroll_y - event.y * 3))
            return True
        if not self.focused:
            return False
        if event.type == pygame.TEXTINPUT:
            self._insert(event.text.replace("\r", ""))
            return True
        if event.type != pygame.KEYDOWN:
            return False

        ctrl = bool(event.mod & pygame.KMOD_CTRL)
        if ctrl and event.key == pygame.K_z:
            if self._undo:
                self.text, self.cursor = self._undo.pop()
            return True
        if ctrl and event.key == pygame.K_v:
            clip = self._clipboard_get()
            if clip:
                self._insert(clip[: max(0, 10_000 - len(self.text))])
            return True
        if ctrl and event.key == pygame.K_c:
            try:
                pygame.scrap.put(pygame.SCRAP_TEXT, self.text.encode("utf-8"))
            except pygame.error:
                pass
            return True
        if event.key == pygame.K_BACKSPACE:
            if self.cursor > 0:
                self._remember()
                if self.text[max(0, self.cursor - 4) : self.cursor] == "    ":
                    remove = 4
                else:
                    remove = 1
                self.text = self.text[: self.cursor - remove] + self.text[self.cursor :]
                self.cursor -= remove
            return True
        if event.key == pygame.K_DELETE:
            if self.cursor < len(self.text):
                self._remember()
                self.text = self.text[: self.cursor] + self.text[self.cursor + 1 :]
            return True
        if event.key == pygame.K_RETURN:
            start = self._line_start()
            current = self.text[start : self.cursor]
            indent = current[: len(current) - len(current.lstrip(" "))]
            if current.rstrip().endswith(":"):
                indent += "    "
            self._insert("\n" + indent)
            return True
        if event.key == pygame.K_TAB:
            self._insert("    ")
            return True
        if event.key == pygame.K_LEFT:
            self.cursor = max(0, self.cursor - 1)
        elif event.key == pygame.K_RIGHT:
            self.cursor = min(len(self.text), self.cursor + 1)
        elif event.key == pygame.K_UP:
            self._vertical_move(-1)
            self._ensure_cursor_visible()
            return True
        elif event.key == pygame.K_DOWN:
            self._vertical_move(1)
            self._ensure_cursor_visible()
            return True
        elif event.key == pygame.K_HOME:
            self.cursor = self._line_start()
        elif event.key == pygame.K_END:
            self.cursor = self._line_end()
        else:
            return False
        self._preferred_col = None
        self._ensure_cursor_visible()
        return True

    @property
    def visible_lines(self) -> int:
        return max(1, (self.rect.height - self.PADDING_Y * 2) // self.LINE_HEIGHT)

    def _ensure_cursor_visible(self) -> None:
        line, _ = self._line_col()
        if line < self.scroll_y:
            self.scroll_y = line
        elif line >= self.scroll_y + self.visible_lines:
            self.scroll_y = line - self.visible_lines + 1

    def _token_colours(self, source: str) -> dict[tuple[int, int], tuple[int, int, int]]:
        colours: dict[tuple[int, int], tuple[int, int, int]] = {}
        token_map = {
            tokenize.STRING: YELLOW,
            tokenize.NUMBER: CYAN,
            tokenize.COMMENT: MUTED,
            tokenize.OP: PURPLE_LIGHT,
        }
        try:
            tokens = tokenize.generate_tokens(io.StringIO(source).readline)
            for token in tokens:
                color = token_map.get(token.type)
                if token.type == tokenize.NAME and keyword.iskeyword(token.string):
                    color = PURPLE_LIGHT
                elif token.type == tokenize.NAME and token.string in {"print", "range", "len"}:
                    color = GREEN
                if color and token.start[0] == token.end[0]:
                    for col in range(token.start[1], token.end[1]):
                        colours[(token.start[0] - 1, col)] = color
        except (tokenize.TokenError, IndentationError):
            pass
        return colours

    def draw(self, target: pygame.Surface) -> None:
        rounded_rect(
            target,
            self.rect,
            (15, 18, 34),
            12,
            PURPLE if self.focused else (50, 57, 88),
            2 if self.focused else 1,
        )
        clip_before = target.get_clip()
        target.set_clip(self.rect)
        pygame.draw.rect(
            target,
            (19, 22, 40),
            (self.rect.x, self.rect.y, self.GUTTER, self.rect.height),
        )

        mono = font(16, mono=True)
        char_width = mono.size("M")[0]
        lines = self.text.split("\n")
        colours = self._token_colours(self.text)
        first, last = self.scroll_y, min(len(lines), self.scroll_y + self.visible_lines + 1)
        for line_index in range(first, last):
            y = self.rect.y + self.PADDING_Y + (line_index - first) * self.LINE_HEIGHT
            draw_text(
                target,
                str(line_index + 1),
                (self.rect.x + self.GUTTER - 10, y + 1),
                14,
                FAINT,
                mono=True,
                anchor="topright",
            )
            x = self.rect.x + self.GUTTER + self.PADDING_X
            line = lines[line_index]
            col = 0
            while col < len(line):
                color = colours.get((line_index, col), INK)
                end = col + 1
                while end < len(line) and colours.get((line_index, end), INK) == color:
                    end += 1
                segment = line[col:end].replace("\t", "    ")
                target.blit(mono.render(segment, True, color), (x + col * char_width, y))
                col = end

        if self.focused and pygame.time.get_ticks() % 1000 < 540:
            line, col = self._line_col()
            if self.scroll_y <= line < self.scroll_y + self.visible_lines:
                cursor_x = self.rect.x + self.GUTTER + self.PADDING_X + col * char_width
                cursor_y = self.rect.y + self.PADDING_Y + (line - self.scroll_y) * self.LINE_HEIGHT
                pygame.draw.rect(target, CYAN, (cursor_x, cursor_y, 2, self.LINE_HEIGHT - 3))

        target.set_clip(clip_before)
