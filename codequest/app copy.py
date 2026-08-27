"""Main Pygame application and screens."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame

from .curriculum import QUESTS, Quest, output_matches, quest_index
from .progress import Progress, ProgressStore
from .runner import RunResult, run_code
from .theme import (
    BG,
    BLACK,
    CYAN,
    FAINT,
    GREEN,
    HEIGHT,
    INK,
    MUTED,
    PURPLE,
    PURPLE_LIGHT,
    RED,
    SIDEBAR_WIDTH,
    SURFACE,
    SURFACE_2,
    SURFACE_3,
    WHITE,
    WIDTH,
    YELLOW,
    draw_text,
    font,
    rounded_rect,
    wrap_text,
)
from .widgets import Button, CodeEditor, TextInput


@dataclass
class Confetti:
    x: float
    y: float
    vx: float
    vy: float
    color: tuple[int, int, int]
    size: int
    angle: float


class CodeQuestApp:
    def __init__(self, store: ProgressStore | None = None) -> None:
        pygame.init()
        pygame.font.init()
        try:
            pygame.scrap.init()
        except pygame.error:
            pass
        pygame.display.set_caption("CodeQuest — Learn Python by Playing")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.store = store or ProgressStore()
        self.progress: Progress = self.store.load()
        self.view = "dashboard"
        self.running = True
        self.buttons: list[Button] = []
        self.active_quest = self._next_quest()
        initial = self.progress.code.get(self.active_quest.id, self.active_quest.starter)
        self.editor = CodeEditor(pygame.Rect(590, 156, 650, 330), initial)
        self.console_title = "CONSOLE"
        self.console_text = "Ready. Run your code when you want to test it."
        self.console_kind = "idle"
        self.hint_visible = False
        self.success_modal = False
        self.newly_completed = False
        self.task_modal = False
        self.task_input = TextInput(pygame.Rect(0, 0, 380, 46), "e.g. Practise loops for 10 minutes")
        self.confetti: list[Confetti] = []
        self.toast = ""
        self.toast_until = 0

    def _next_quest(self) -> Quest:
        for quest in QUESTS:
            if quest.id not in self.progress.completed and self.progress.is_unlocked(quest.id):
                return quest
        return QUESTS[-1]

    def run(self, max_frames: int | None = None) -> None:
        frame = 0
        while self.running and (max_frames is None or frame < max_frames):
            self._events()
            self._update()
            self._draw()
            pygame.display.flip()
            self.clock.tick(60)
            frame += 1
        self._save_code()
        self.store.save(self.progress)
        pygame.quit()

    def _events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue
            if event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode(
                    (max(1050, event.w), max(680, event.h)), pygame.RESIZABLE
                )
                continue

            if self.success_modal:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    self._close_success()
                else:
                    for button in reversed(self.buttons):
                        if button.handle(event):
                            break
                continue

            if self.task_modal:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.task_modal = False
                    self.task_input.focused = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    self._submit_task()
                else:
                    handled = any(button.handle(event) for button in reversed(self.buttons))
                    if not handled:
                        self.task_input.handle(event)
                continue

            if any(button.handle(event) for button in reversed(self.buttons)):
                continue

            if self.view == "quest":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self._go_dashboard()
                    continue
                if (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_RETURN
                    and bool(event.mod & pygame.KMOD_CTRL)
                ):
                    self._check_solution()
                    continue
                if self.editor.handle(event):
                    self._save_code()

    def _update(self) -> None:
        for particle in self.confetti:
            particle.x += particle.vx
            particle.y += particle.vy
            particle.vy += 0.13
            particle.angle += 0.08
        self.confetti = [p for p in self.confetti if p.y < self.screen.get_height() + 20]

    def _draw(self) -> None:
        self.buttons = []
        self.screen.fill(BG)
        self._draw_background()
        self._draw_sidebar()
        if self.view == "dashboard":
            self._draw_dashboard()
        else:
            self._draw_quest()
        self._draw_confetti()
        self._draw_toast()
        if self.task_modal:
            self._draw_task_modal()
        if self.success_modal:
            self._draw_success_modal()

    def _draw_background(self) -> None:
        width, height = self.screen.get_size()
        glow = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*PURPLE, 18), (width - 80, -20), 260)
        pygame.draw.circle(glow, (*CYAN, 10), (SIDEBAR_WIDTH + 120, height + 40), 220)
        for i in range(22):
            x = (i * 173 + 61) % width
            y = (i * 97 + 33) % height
            pygame.draw.circle(glow, (*WHITE, 28), (x, y), 1)
        self.screen.blit(glow, (0, 0))

    def _draw_sidebar(self) -> None:
        _, height = self.screen.get_size()
        pygame.draw.rect(self.screen, (16, 19, 36), (0, 0, SIDEBAR_WIDTH, height))
        pygame.draw.line(self.screen, (37, 42, 67), (SIDEBAR_WIDTH, 0), (SIDEBAR_WIDTH, height))

        pygame.draw.circle(self.screen, PURPLE, (34, 37), 17)
        draw_text(self.screen, ">_", (34, 37), 13, WHITE, True, mono=True, anchor="center")
        draw_text(self.screen, "CodeQuest", (60, 26), 21, INK, True)
        draw_text(self.screen, "LEARN  •  BUILD  •  PLAY", (24, 66), 10, MUTED, True)

        nav = [
            ("Home base", "home", 112),
            ("Current quest", "quest", 164),
        ]
        for label, destination, y in nav:
            active = (self.view == "dashboard" and destination == "home") or (
                self.view == "quest" and destination == "quest"
            )
            rect = pygame.Rect(14, y, SIDEBAR_WIDTH - 28, 42)
            if active:
                rounded_rect(self.screen, rect, (43, 36, 78), 10)
                pygame.draw.rect(self.screen, PURPLE, (14, y + 9, 3, 24), border_radius=2)
            icon_color = PURPLE_LIGHT if active else MUTED
            if destination == "home":
                pygame.draw.polygon(
                    self.screen,
                    icon_color,
                    [(25, y + 21), (31, y + 15), (37, y + 21)],
                    2,
                )
                pygame.draw.rect(self.screen, icon_color, (27, y + 21, 8, 7), 2)
            else:
                pygame.draw.polygon(
                    self.screen,
                    icon_color,
                    [(31, y + 14), (38, y + 21), (31, y + 28), (24, y + 21)],
                    2,
                )
            draw_text(
                self.screen,
                label,
                (52, y + 21),
                15,
                INK if active else MUTED,
                True,
                anchor="midleft",
            )
            if destination == "home":
                action = self._go_dashboard
            else:
                action = lambda: self._open_quest(self._next_quest())
            self.buttons.append(Button(rect, "", action))

        draw_text(self.screen, "YOUR JOURNEY", (24, 231), 11, FAINT, True)
        completed = len(self.progress.completed)
        draw_text(self.screen, f"{completed}/{len(QUESTS)} quests", (24, 259), 14, MUTED)
        bar = pygame.Rect(24, 286, SIDEBAR_WIDTH - 48, 7)
        pygame.draw.rect(self.screen, SURFACE_3, bar, border_radius=4)
        if completed:
            fill = bar.copy()
            fill.width = int(bar.width * completed / len(QUESTS))
            pygame.draw.rect(self.screen, GREEN, fill, border_radius=4)

        y = height - 80
        pygame.draw.circle(self.screen, (54, 64, 96), (39, y + 23), 22)
        draw_text(self.screen, "PY", (39, y + 23), 12, CYAN, True, mono=True, anchor="center")
        draw_text(self.screen, "Python explorer", (71, y + 13), 14, INK, True)
        draw_text(self.screen, f"Level {self._learner_level()}", (71, y + 34), 12, MUTED)

    def _draw_dashboard(self) -> None:
        width, height = self.screen.get_size()
        left = SIDEBAR_WIDTH + 28
        content_width = width - left - 28

        draw_text(self.screen, "Home base", (left, 25), 26, INK, True)
        draw_text(self.screen, "Pick up where you left off, explorer.", (left, 57), 14, MUTED)
        self._stat_pill(width - 274, 28, f"{self.progress.streak} day streak", YELLOW)
        self._stat_pill(width - 139, 28, f"{self.progress.xp} XP", CYAN)

        hero = pygame.Rect(left, 94, content_width, 148)
        rounded_rect(self.screen, hero, (35, 30, 68), 18, (72, 58, 125))
        pygame.draw.circle(self.screen, (62, 46, 111), (hero.right - 92, hero.centery), 84)
        pygame.draw.circle(self.screen, PURPLE, (hero.right - 92, hero.centery), 49)
        pygame.draw.circle(self.screen, CYAN, (hero.right - 76, hero.centery - 13), 8)
        draw_text(self.screen, "CURRENT MISSION", (hero.x + 24, hero.y + 20), 11, PURPLE_LIGHT, True)
        next_quest = self._next_quest()
        all_done = len(self.progress.completed) == len(QUESTS)
        title = "All missions complete!" if all_done else next_quest.title
        subtitle = (
            "You finished the current expedition. Replay any quest to keep practising."
            if all_done
            else f"World {next_quest.world}  •  {next_quest.concept}  •  +{next_quest.xp} XP"
        )
        draw_text(self.screen, title, (hero.x + 24, hero.y + 48), 26, INK, True)
        draw_text(self.screen, subtitle, (hero.x + 24, hero.y + 84), 14, MUTED)
        continue_rect = pygame.Rect(hero.right - 216, hero.bottom - 48, 180, 38)
        action_quest = next_quest if not all_done else QUESTS[-1]
        self._add_button(continue_rect, "Open mission", lambda: self._open_quest(action_quest), "primary")

        below_y = 270
        gap = 22
        tasks_width = min(318, max(280, int(content_width * 0.3)))
        map_width = content_width - tasks_width - gap
        draw_text(self.screen, "Quest map", (left, below_y), 20, INK, True)
        draw_text(self.screen, "Complete a mission to unlock the next.", (left, below_y + 29), 13, MUTED)
        self._draw_quest_grid(left, below_y + 58, map_width, height - below_y - 78)

        task_x = left + map_width + gap
        draw_text(self.screen, "My tasks", (task_x, below_y), 20, INK, True)
        add_rect = pygame.Rect(task_x + tasks_width - 34, below_y - 4, 34, 34)
        self._add_button(add_rect, "+", self._open_task_modal, "primary")
        self._draw_tasks(task_x, below_y + 58, tasks_width, height - below_y - 78)

    def _stat_pill(self, x: int, y: int, label: str, accent: tuple[int, int, int]) -> None:
        rect = pygame.Rect(x, y, 118, 34)
        rounded_rect(self.screen, rect, SURFACE, 17, (48, 54, 83))
        pygame.draw.circle(self.screen, accent, (x + 17, y + 17), 4)
        draw_text(self.screen, label, (x + 29, y + 17), 12, INK, True, anchor="midleft")

    def _draw_quest_grid(self, x: int, y: int, width: int, height: int) -> None:
        cols = 2
        gap = 12
        card_w = (width - gap) // cols
        card_h = max(70, min(84, (height - 3 * gap) // 4))
        for index, quest in enumerate(QUESTS):
            col, row = index % cols, index // cols
            rect = pygame.Rect(x + col * (card_w + gap), y + row * (card_h + gap), card_w, card_h)
            unlocked = self.progress.is_unlocked(quest.id)
            complete = quest.id in self.progress.completed
            bg = (25, 43, 48) if complete else SURFACE
            border = (45, 113, 89) if complete else (49, 56, 85)
            if not unlocked:
                bg, border = (18, 21, 38), (37, 41, 62)
            hovered = unlocked and rect.collidepoint(pygame.mouse.get_pos())
            if hovered:
                border = PURPLE
            rounded_rect(self.screen, rect, bg, 13, border, 2 if hovered else 1)
            badge_color = GREEN if complete else (PURPLE if unlocked else SURFACE_3)
            pygame.draw.circle(self.screen, badge_color, (rect.x + 27, rect.centery), 17)
            if complete:
                self._draw_check((rect.x + 27, rect.centery), 9, (9, 40, 30), 3)
            else:
                draw_text(
                    self.screen,
                    str(index + 1) if unlocked else "×",
                    (rect.x + 27, rect.centery),
                    14,
                    INK,
                    True,
                    anchor="center",
                )
            draw_text(
                self.screen,
                quest.title,
                (rect.x + 54, rect.y + 16),
                14,
                INK if unlocked else FAINT,
                True,
            )
            draw_text(
                self.screen,
                f"{quest.concept}  •  {quest.xp} XP",
                (rect.x + 54, rect.y + 43),
                11,
                GREEN if complete else MUTED if unlocked else FAINT,
            )
            if unlocked:
                self.buttons.append(Button(rect, "", lambda q=quest: self._open_quest(q)))

    def _draw_tasks(self, x: int, y: int, width: int, height: int) -> None:
        panel = pygame.Rect(x, y, width, height)
        rounded_rect(self.screen, panel, SURFACE, 14, (47, 53, 81))
        if not self.progress.tasks:
            pygame.draw.circle(self.screen, (44, 49, 75), (panel.centerx, y + 66), 31)
            draw_text(self.screen, "+", (panel.centerx, y + 65), 27, PURPLE_LIGHT, anchor="center")
            draw_text(self.screen, "No personal tasks yet", (panel.centerx, y + 111), 14, INK, True, anchor="center")
            draw_text(self.screen, "Add a small goal for today.", (panel.centerx, y + 136), 12, MUTED, anchor="center")
            add = pygame.Rect(x + 28, y + 162, width - 56, 38)
            self._add_button(add, "Create a task", self._open_task_modal, "secondary")
            return

        task_y = y + 16
        for task in self.progress.tasks[-5:]:
            row = pygame.Rect(x + 14, task_y, width - 28, 52)
            hovered = row.collidepoint(pygame.mouse.get_pos())
            if hovered:
                rounded_rect(self.screen, row, SURFACE_2, 9)
            box = pygame.Rect(row.x + 8, row.y + 16, 19, 19)
            rounded_rect(self.screen, box, GREEN if task.done else SURFACE_3, 5, GREEN if task.done else FAINT)
            if task.done:
                self._draw_check(box.center, 7, BLACK, 2)
            label_color = FAINT if task.done else INK
            title = task.title if len(task.title) <= 31 else task.title[:28] + "…"
            draw_text(self.screen, title, (row.x + 39, row.centery), 13, label_color, task.done, anchor="midleft")
            self.buttons.append(Button(row, "", lambda t=task: self._toggle_task(t.id)))
            task_y += 57
        done = sum(task.done for task in self.progress.tasks)
        draw_text(
            self.screen,
            f"{done} of {len(self.progress.tasks)} complete",
            (panel.centerx, panel.bottom - 20),
            11,
            MUTED,
            anchor="center",
        )

    def _draw_quest(self) -> None:
        width, height = self.screen.get_size()
        left = SIDEBAR_WIDTH + 20
        right = width - 22

        back_rect = pygame.Rect(left, 20, 86, 36)
        self._add_button(back_rect, "Back", self._go_dashboard, "secondary")
        draw_text(
            self.screen,
            f"MISSION {quest_index(self.active_quest.id) + 1} OF {len(QUESTS)}",
            (left + 106, 29),
            11,
            PURPLE_LIGHT,
            True,
        )
        draw_text(self.screen, self.active_quest.title, (left + 106, 44), 17, INK, True)

        check_rect = pygame.Rect(right - 126, 20, 126, 40)
        run_rect = pygame.Rect(right - 236, 20, 98, 40)
        self._add_button(run_rect, "Run", self._run_only, "secondary")
        self._add_button(check_rect, "Check", self._check_solution, "success")

        instructions_w = min(318, max(285, int((width - SIDEBAR_WIDTH) * 0.3)))
        panel = pygame.Rect(left, 78, instructions_w, height - 100)
        rounded_rect(self.screen, panel, SURFACE, 15, (48, 55, 84))
        self._draw_instructions(panel)

        work_x = panel.right + 16
        work_w = right - work_x
        draw_text(self.screen, "PYTHON EDITOR", (work_x, 84), 11, MUTED, True)
        reset_rect = pygame.Rect(right - 70, 76, 70, 29)
        self._add_button(reset_rect, "Reset", self._reset_code, "secondary")

        console_h = max(142, int((height - 116) * 0.27))
        editor_y = 113
        editor_h = height - editor_y - console_h - 47
        self.editor.rect = pygame.Rect(work_x, editor_y, work_w, editor_h)
        self.editor.draw(self.screen)

        console_y = editor_y + editor_h + 31
        draw_text(self.screen, self.console_title, (work_x, console_y - 23), 11, MUTED, True)
        self._draw_console(pygame.Rect(work_x, console_y, work_w, console_h))

    def _draw_instructions(self, panel: pygame.Rect) -> None:
        quest = self.active_quest
        inner_x = panel.x + 20
        content_w = panel.width - 40
        chip = pygame.Rect(inner_x, panel.y + 20, min(126, 74 + len(quest.concept) * 4), 26)
        rounded_rect(self.screen, chip, (45, 39, 80), 13)
        draw_text(self.screen, quest.concept, chip.center, 11, PURPLE_LIGHT, True, anchor="center")
        draw_text(self.screen, f"+{quest.xp} XP", (panel.right - 20, panel.y + 33), 12, CYAN, True, anchor="midright")

        draw_text(self.screen, quest.title, (inner_x, panel.y + 66), 23, INK, True)
        body_font = font(14)
        y = panel.y + 105
        for line in wrap_text(quest.story, body_font, content_w):
            draw_text(self.screen, line, (inner_x, y), 14, MUTED)
            y += 21

        y += 18
        draw_text(self.screen, "YOUR TASK", (inner_x, y), 11, GREEN, True)
        y += 26
        for line in wrap_text(quest.objective, body_font, content_w):
            draw_text(self.screen, line, (inner_x, y), 14, INK)
            y += 22

        y += 18
        expected_h = 52 + (quest.expected_output.count("\n") * 18)
        expected = pygame.Rect(inner_x, y, content_w, expected_h)
        rounded_rect(self.screen, expected, (15, 18, 34), 10, (50, 57, 86))
        draw_text(self.screen, "EXPECTED OUTPUT", (expected.x + 12, expected.y + 10), 9, FAINT, True)
        out_y = expected.y + 29
        for line in quest.expected_output.splitlines():
            draw_text(self.screen, line, (expected.x + 12, out_y), 13, CYAN, mono=True)
            out_y += 18
        y = expected.bottom + 18

        if self.hint_visible:
            hint_lines = wrap_text(quest.hint, font(13), content_w - 22)
            hint_h = 34 + len(hint_lines) * 19
            hint = pygame.Rect(inner_x, y, content_w, hint_h)
            rounded_rect(self.screen, hint, (55, 47, 28), 10, (105, 83, 40))
            draw_text(self.screen, "HINT", (hint.x + 11, hint.y + 9), 10, YELLOW, True)
            hint_y = hint.y + 27
            for line in hint_lines:
                draw_text(self.screen, line, (hint.x + 11, hint_y), 13, INK)
                hint_y += 19
        else:
            hint_rect = pygame.Rect(inner_x, y, content_w, 38)
            self._add_button(hint_rect, "Show hint", self._show_hint, "secondary")

        draw_text(
            self.screen,
            "Tip: Ctrl + Enter checks your answer",
            (inner_x, panel.bottom - 25),
            10,
            FAINT,
        )

    def _draw_console(self, rect: pygame.Rect) -> None:
        border = {"success": GREEN, "error": RED}.get(self.console_kind, (49, 57, 87))
        rounded_rect(self.screen, rect, (10, 13, 27), 12, border)
        color = {"success": GREEN, "error": RED}.get(self.console_kind, MUTED)
        icon = {"success": "PASS", "error": "ERROR"}.get(self.console_kind, "OUTPUT")
        chip = pygame.Rect(rect.x + 12, rect.y + 11, 60, 22)
        rounded_rect(self.screen, chip, (*color[:3],), 8)
        draw_text(self.screen, icon, chip.center, 9, BLACK if self.console_kind != "idle" else WHITE, True, anchor="center")

        mono = font(14, mono=True)
        lines: list[str] = []
        for raw in self.console_text.splitlines() or [""]:
            lines.extend(wrap_text(raw, mono, rect.width - 28))
        y = rect.y + 43
        for line in lines[: max(1, (rect.height - 52) // 19)]:
            draw_text(self.screen, line, (rect.x + 14, y), 14, INK if self.console_kind != "error" else RED, mono=True)
            y += 19

    def _draw_task_modal(self) -> None:
        width, height = self.screen.get_size()
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((4, 6, 15, 190))
        self.screen.blit(overlay, (0, 0))
        rect = pygame.Rect(width // 2 - 230, height // 2 - 125, 460, 250)
        rounded_rect(self.screen, rect, SURFACE, 18, (75, 67, 120))
        draw_text(self.screen, "Create a personal task", (rect.x + 28, rect.y + 26), 22, INK, True)
        draw_text(self.screen, "Small goals make steady coders.", (rect.x + 28, rect.y + 58), 13, MUTED)
        self.task_input.rect = pygame.Rect(rect.x + 28, rect.y + 93, rect.width - 56, 46)
        self.task_input.draw(self.screen)
        cancel = pygame.Rect(rect.right - 210, rect.bottom - 56, 82, 36)
        create = pygame.Rect(rect.right - 116, rect.bottom - 56, 88, 36)
        self._add_button(cancel, "Cancel", self._close_task_modal, "secondary")
        self._add_button(create, "Create", self._submit_task, "primary")

    def _draw_success_modal(self) -> None:
        width, height = self.screen.get_size()
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((5, 8, 18, 202))
        self.screen.blit(overlay, (0, 0))
        rect = pygame.Rect(width // 2 - 245, height // 2 - 190, 490, 380)
        rounded_rect(self.screen, rect, SURFACE, 22, (86, 73, 143), 2)
        pygame.draw.circle(self.screen, (35, 91, 71), (rect.centerx, rect.y + 74), 43)
        pygame.draw.circle(self.screen, GREEN, (rect.centerx, rect.y + 74), 31)
        self._draw_check((rect.centerx, rect.y + 74), 15, BLACK, 5)
        draw_text(self.screen, "Mission complete!", (rect.centerx, rect.y + 134), 28, INK, True, anchor="center")
        message = (
            f"You earned {self.active_quest.xp} XP and unlocked a new mission."
            if self.newly_completed and quest_index(self.active_quest.id) < len(QUESTS) - 1
            else "Great work — your solution produces the right output."
        )
        draw_text(self.screen, message, (rect.centerx, rect.y + 175), 14, MUTED, anchor="center")

        xp = pygame.Rect(rect.x + 56, rect.y + 210, 170, 60)
        streak = pygame.Rect(rect.right - 226, rect.y + 210, 170, 60)
        rounded_rect(self.screen, xp, SURFACE_2, 11)
        rounded_rect(self.screen, streak, SURFACE_2, 11)
        draw_text(self.screen, str(self.progress.xp), (xp.centerx, xp.y + 12), 19, CYAN, True, anchor="midtop")
        draw_text(self.screen, "TOTAL XP", (xp.centerx, xp.y + 39), 9, MUTED, True, anchor="midtop")
        draw_text(self.screen, str(len(self.progress.completed)), (streak.centerx, streak.y + 12), 19, GREEN, True, anchor="midtop")
        draw_text(self.screen, "QUESTS DONE", (streak.centerx, streak.y + 39), 9, MUTED, True, anchor="midtop")

        next_exists = quest_index(self.active_quest.id) < len(QUESTS) - 1
        if next_exists:
            button = pygame.Rect(rect.centerx - 91, rect.bottom - 70, 182, 42)
            self._add_button(button, "Next mission", self._open_next_quest, "primary")
        else:
            button = pygame.Rect(rect.centerx - 82, rect.bottom - 70, 164, 42)
            self._add_button(button, "Back to base", self._close_success, "primary")

    def _draw_confetti(self) -> None:
        for particle in self.confetti:
            points = []
            for i in range(4):
                angle = particle.angle + i * math.pi / 2
                points.append(
                    (
                        int(particle.x + math.cos(angle) * particle.size),
                        int(particle.y + math.sin(angle) * particle.size * 0.55),
                    )
                )
            pygame.draw.polygon(self.screen, particle.color, points)

    def _draw_check(
        self,
        center: tuple[int, int],
        size: int,
        color: tuple[int, int, int],
        width: int,
    ) -> None:
        x, y = center
        pygame.draw.lines(
            self.screen,
            color,
            False,
            [(x - size, y), (x - size // 3, y + size // 2), (x + size, y - size)],
            width,
        )

    def _draw_toast(self) -> None:
        if not self.toast or pygame.time.get_ticks() >= self.toast_until:
            return
        width, height = self.screen.get_size()
        toast_w = min(400, max(220, font(13).size(self.toast)[0] + 40))
        rect = pygame.Rect(width // 2 - toast_w // 2, height - 60, toast_w, 38)
        rounded_rect(self.screen, rect, (39, 44, 69), 12, (70, 79, 114))
        draw_text(self.screen, self.toast, rect.center, 13, INK, True, anchor="center")

    def _add_button(
        self,
        rect: pygame.Rect,
        label: str,
        action,
        kind: str = "secondary",
        enabled: bool = True,
    ) -> None:
        button = Button(rect, label, action, kind, enabled=enabled)
        self.buttons.append(button)
        button.draw(self.screen)

    def _go_dashboard(self) -> None:
        self._save_code()
        self.store.save(self.progress)
        self.view = "dashboard"
        self.success_modal = False

    def _open_quest(self, quest: Quest) -> None:
        if not self.progress.is_unlocked(quest.id):
            self._show_toast("Complete the previous mission first.")
            return
        self._save_code()
        self.active_quest = quest
        self.editor.set_text(self.progress.code.get(quest.id, quest.starter))
        self.editor.focused = True
        self.console_title = "CONSOLE"
        self.console_text = "Ready. Run your code when you want to test it."
        self.console_kind = "idle"
        self.hint_visible = False
        self.view = "quest"

    def _save_code(self) -> None:
        if hasattr(self, "active_quest") and hasattr(self, "editor"):
            self.progress.code[self.active_quest.id] = self.editor.get_text()

    def _run(self) -> RunResult:
        self._save_code()
        result = run_code(self.editor.get_text())
        if result.ok:
            self.console_text = result.output if result.output else "Program finished with no output."
            self.console_kind = "success"
        else:
            combined = "\n".join(part for part in (result.output, result.error) if part)
            self.console_text = combined or "The program could not run."
            self.console_kind = "error"
        return result

    def _run_only(self) -> None:
        self.console_title = "CONSOLE • LAST RUN"
        self._run()

    def _check_solution(self) -> None:
        self.console_title = "CONSOLE • CHECKING"
        result = self._run()
        if not result.ok:
            return
        if output_matches(self.active_quest, result.output):
            self.console_title = "CONSOLE • PASSED"
            self.console_text = result.output + "\n\nCorrect output — mission complete!"
            self.console_kind = "success"
            self.newly_completed = self.progress.complete(
                self.active_quest.id, self.active_quest.xp
            )
            self.store.save(self.progress)
            self.success_modal = True
            self._launch_confetti()
        else:
            expected = self.active_quest.expected_output
            actual = result.output.strip() or "(no output)"
            self.console_title = "CONSOLE • NOT YET"
            self.console_text = f"Your output:\n{actual}\n\nExpected:\n{expected}"
            self.console_kind = "error"

    def _reset_code(self) -> None:
        self.editor.set_text(self.active_quest.starter)
        self.editor.focused = True
        self._save_code()
        self.console_title = "CONSOLE"
        self.console_text = "Starter code restored."
        self.console_kind = "idle"

    def _show_hint(self) -> None:
        self.hint_visible = True

    def _launch_confetti(self) -> None:
        width, _ = self.screen.get_size()
        palette = [PURPLE, PURPLE_LIGHT, CYAN, GREEN, YELLOW, RED]
        self.confetti = [
            Confetti(
                random.uniform(width * 0.28, width * 0.82),
                random.uniform(-80, -5),
                random.uniform(-1.5, 1.5),
                random.uniform(1.8, 4.2),
                random.choice(palette),
                random.randint(4, 8),
                random.random() * math.pi,
            )
            for _ in range(90)
        ]

    def _close_success(self) -> None:
        self.success_modal = False
        self._go_dashboard()

    def _open_next_quest(self) -> None:
        current = quest_index(self.active_quest.id)
        self.success_modal = False
        if current + 1 < len(QUESTS):
            self._open_quest(QUESTS[current + 1])
        else:
            self._go_dashboard()

    def _open_task_modal(self) -> None:
        self.task_modal = True
        self.task_input.text = ""
        self.task_input.focused = True

    def _close_task_modal(self) -> None:
        self.task_modal = False
        self.task_input.focused = False

    def _submit_task(self) -> None:
        task = self.progress.add_task(self.task_input.text)
        if task:
            self.store.save(self.progress)
            self._show_toast("Task added to your list.")
        self._close_task_modal()

    def _toggle_task(self, task_id: int) -> None:
        for task in self.progress.tasks:
            if task.id == task_id:
                task.done = not task.done
                break
        self.store.save(self.progress)

    def _show_toast(self, message: str) -> None:
        self.toast = message
        self.toast_until = pygame.time.get_ticks() + 2400

    def _learner_level(self) -> int:
        return 1 + self.progress.xp // 500
