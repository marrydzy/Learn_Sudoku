# -*- coding: UTF-8 -*-

import pygame
import sys
import time

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (160, 160, 160)
MAGENTA = (255, 0, 255)
LIME = (0, 255, 0)
CYAN = (0, 255, 255)
SILVER = (192, 192, 192)
LIGHTGREEN = (190, 255, 190)
LIGHTPINK = (255, 182, 193)
GAINSBORO = (230, 230, 230)

C_HOUSE = (255, 255, 225)
C_OTHER_CELLS = (255, 250, 190)
Y_WING_ROOT = (255, 153, 51)
Y_WING_LEAF = (255, 153, 51)  # (153, 255, 255)    (255, 229, 204)


class AppWindow:
    """ TBD """
    def __init__(self, inspect):
        pygame.init()

        self.cell_size = 66
        self.left_margin = 25
        self.top_margin = 60
        self.bottom_margin = 90
        self.btn_w = 140
        self.btn_h = 40
        self.btn_margin = 20

        self.dark_grey = (150, 150, 150)        # TODO - remove it from here!

        self.font_type = "FreeSans"
        self.font_clues_size = 47
        self.font_options_size = 15
        self.font_button_size = 20
        self.font_text_size = 17
        self.font_clues = pygame.font.SysFont(self.font_type, self.font_clues_size)
        self.font_options = pygame.font.SysFont(self.font_type, self.font_options_size, italic=True)
        self.font_button = pygame.font.SysFont(self.font_type, self.font_button_size, bold=True)
        self.font_text = pygame.font.SysFont(self.font_type, self.font_text_size, italic=True)
        self.clue_shift_x = (self.cell_size - self.font_clues.size('1')[0]) // 2
        self.clue_shift_y = (self.cell_size - self.font_clues.get_ascent()) // 2 - 2    # TODO
        self.option_shift_x = (self.cell_size // 3 - self.font_options.size('1')[0]) // 2
        self.option_shift_y = (self.cell_size // 3 - self.font_options.get_ascent()) // 2
        self.offsets = {'1': (0, 0),
                        '2': (self.cell_size // 3, 0),
                        '3': (2 * self.cell_size // 3, 0),
                        '4': (0, self.cell_size // 3),
                        '5': (self.cell_size // 3, self.cell_size // 3),
                        '6': (2 * self.cell_size // 3, self.cell_size // 3),
                        '7': (0, 2 * self.cell_size // 3),
                        '8': (self.cell_size // 3, 2 * self.cell_size // 3),
                        '9': (2 * self.cell_size // 3, 2 * self.cell_size // 3),
                        }

        self.show_solution_steps = True
        self.inspect = inspect
        self.method = {
            "manual_solution": "m",
            "scrub_pencil_marks": "e",
            "unique_values": "u",
            "hidden_pairs": "h",
            "naked_twins": "p",
            "omissions": "o",
            "y_wings": "y",
            "hidden_triplets": "i",
            "hidden_quads": "j",
            "naked_triplets": "t",
            "naked_quads": "q",
            "unique_rectangles": "r",
            "x_wings": "x",
            "swordfish": "s",
            "iterate": "z",
        }
        self.time_in = 0

        display_width = 2 * self.left_margin + 9 * self.cell_size
        display_height = self.top_margin + 9 * self.cell_size + self.bottom_margin
        self.screen = pygame.display.set_mode((display_width, display_height))
        self.screen.fill(GAINSBORO)
        pygame.display.set_caption('SUDOKU PUZZLE')
        pygame.display.set_icon(pygame.image.load('demon.png'))     # TODO - fix it!

        self.input_board = None

    def _draw_button(self, step):
        """ TODO """
        btn_w, btn_h = 140, 40
        displ = pygame.display.get_window_size()
        btn_x = (displ[0] - btn_w) // 2
        offset_y = self.top_margin + 9 * self.cell_size
        btn_y = offset_y + (displ[1] - offset_y - btn_h) // 2
        btn_rect = pygame.Rect((btn_x, btn_y, btn_w, btn_h))
        pygame.draw.rect(self.screen, self.dark_grey, btn_rect)
        pygame.draw.rect(self.screen, WHITE, btn_rect.inflate(-4, -4))
        btn_name = "Solve" if step else "Quit"                    # TODO - fix it!
        btn_txt = self.font_button.render(btn_name, True, BLACK)
        txt_x = btn_x + (self.btn_w - self.font_button.size(btn_name)[0]) // 2
        txt_y = btn_y + (self.btn_h - self.font_button.get_ascent()) // 2
        self.screen.blit(btn_txt, (txt_x, txt_y))
        return btn_rect

    def _render_clue(self, clue, pos):
        """ Render board clues """
        digit = self.font_clues.render(clue, True, BLACK)
        self.screen.blit(digit, (pos[0] + self.clue_shift_x, pos[1] + self.clue_shift_y))

    def _higlight_clue(self, cell_id, pos, **kwargs):
        """ Highlight clue cell, as applicable """

        new_singles = kwargs["singles"] if "singles" in kwargs else []
        active_clue = kwargs["new_clue"] if "new_clue" in kwargs else None

        if new_singles and cell_id in new_singles and len(self.input_board[cell_id]) == 1:
            pygame.draw.rect(
                self.screen, LIGHTGREEN,
                (pos[0], pos[1], self.cell_size + 1, self.cell_size + 1))

        if cell_id == active_clue:
            cell_center = (pos[0] + (self.cell_size + 1) // 2,
                           pos[1] + (self.cell_size + 1) // 2)
            pygame.draw.rect(self.screen, LIGHTGREEN,
                             (pos[0], pos[1], self.cell_size + 1, self.cell_size + 1))
            pygame.draw.circle(self.screen, (255, 99, 71), cell_center, (self.cell_size - 1) // 2, 5)

    def _highlight_options(self, cell_id, new_value, pos, **kwargs):
        """ Highlight pencil marks, as applicable """

        remove = kwargs["remove"] if "remove" in kwargs else None
        subset = kwargs["subset"] if "subset" in kwargs else None
        claims = kwargs["claims"] if "claims" in kwargs else None
        iterate = kwargs["iterate"] if "iterate" in kwargs else None
        y_wing = kwargs["y_wing"] if "y_wing" in kwargs else None
        corners = kwargs["rectangle"] if "rectangle" in kwargs else None
        x_wing = kwargs["x_wing"] if "x_wing" in kwargs else None
        sword = kwargs["sword"] if "sword" in kwargs else None

        if iterate is not None and cell_id == iterate:
            pygame.draw.rect(
                self.screen, LIGHTPINK,
                (pos[0], pos[1], self.cell_size + 1, self.cell_size + 1))
        if y_wing is not None and cell_id == y_wing[1]:
            pygame.draw.rect(
                self.screen, Y_WING_ROOT,
                (pos[0], pos[1], self.cell_size + 1, self.cell_size + 1))
        if y_wing is not None and (cell_id == y_wing[2] or cell_id == y_wing[3]):
            pygame.draw.rect(
                self.screen, Y_WING_LEAF,
                (pos[0], pos[1], self.cell_size + 1, self.cell_size + 1))
        if corners and cell_id in corners or x_wing and cell_id in x_wing[1:]:
            pygame.draw.rect(
                self.screen, Y_WING_LEAF,       # TODO
                (pos[0], pos[1], self.cell_size + 1, self.cell_size + 1))
        if sword and cell_id in sword[1:]:
            pygame.draw.rect(
                self.screen, Y_WING_LEAF,       # TODO
                (pos[0], pos[1], self.cell_size + 1, self.cell_size + 1))

        for value in self.input_board[cell_id]:
            if remove and (value, cell_id) in remove:
                pygame.draw.rect(self.screen, GREY,
                                 (pos[0] + self.offsets[value][0],
                                  pos[1] + self.offsets[value][1],
                                  self.cell_size // 3, self.cell_size // 3))
            if value == new_value:
                pygame.draw.rect(self.screen, LIME,
                                 (pos[0] + self.offsets[value][0],
                                  pos[1] + self.offsets[value][1],
                                  self.cell_size // 3, self.cell_size // 3))
            if subset and value in new_value and cell_id in subset:
                pygame.draw.rect(self.screen, CYAN,
                                 (pos[0] + self.offsets[value][0],
                                  pos[1] + self.offsets[value][1],
                                  self.cell_size // 3, self.cell_size // 3))
            if claims and (value, cell_id) in claims:
                pygame.draw.rect(self.screen, CYAN,
                                 (pos[0] + self.offsets[value][0],
                                  pos[1] + self.offsets[value][1],
                                  self.cell_size // 3, self.cell_size // 3))
            if x_wing and value == x_wing[0] and cell_id in x_wing[1:]:
                pygame.draw.rect(self.screen, CYAN,
                                 (pos[0] + self.offsets[value][0],
                                  pos[1] + self.offsets[value][1],
                                  self.cell_size // 3, self.cell_size // 3))
            if y_wing and value == y_wing[0] and cell_id in (y_wing[2], y_wing[3]):
                pygame.draw.rect(self.screen, CYAN,
                                 (pos[0] + self.offsets[value][0],
                                  pos[1] + self.offsets[value][1],
                                  self.cell_size // 3, self.cell_size // 3))
            if sword and value == sword[0] and cell_id in sword[1:]:
                pygame.draw.rect(self.screen, CYAN,
                                 (pos[0] + self.offsets[value][0],
                                  pos[1] + self.offsets[value][1],
                                  self.cell_size // 3, self.cell_size // 3))

    def _draw_board_features(self, **kwargs):
        """ TBD """

        rectangle = kwargs["rectangle"] if "rectangle" in kwargs else None
        y_wing = kwargs["y_wing"] if "y_wing" in kwargs else None
        x_wing = kwargs["x_wing"] if "x_wing" in kwargs else None

        if rectangle:
            left = (rectangle[0] % 9 + 0.5) * self.cell_size + self.left_margin
            top = (rectangle[0] // 9 + 0.5) * self.cell_size + self.top_margin
            right = (rectangle[1] % 9 + 0.5) * self.cell_size + self.left_margin
            bottom = (rectangle[2] // 9 + 0.5) * self.cell_size + self.top_margin
            rect = pygame.Rect(left, top, right - left, bottom - top)
            pygame.draw.rect(self.screen, MAGENTA, rect, width=4)

        if x_wing:
            color = MAGENTA
            x_wing = sorted(x_wing[1:])
            x1 = (x_wing[0] % 9 + 0.5) * self.cell_size + self.left_margin
            y1 = (x_wing[0] // 9 + 0.5) * self.cell_size + self.top_margin
            x2 = (x_wing[3] % 9 + 0.5) * self.cell_size + self.left_margin
            y2 = (x_wing[3] // 9 + 0.5) * self.cell_size + self.top_margin
            pygame.draw.line(self.screen, color, (x1, y1), (x2, y2), width=5)
            x1 = (x_wing[1] % 9 + 0.5) * self.cell_size + self.left_margin
            y1 = (x_wing[1] // 9 + 0.5) * self.cell_size + self.top_margin
            x2 = (x_wing[2] % 9 + 0.5) * self.cell_size + self.left_margin
            y2 = (x_wing[2] // 9 + 0.5) * self.cell_size + self.top_margin
            pygame.draw.line(self.screen, color, (x1, y1), (x2, y2), width=5)

        if y_wing:
            x1 = (y_wing[1] % 9 + 0.5) * self.cell_size + self.left_margin
            y1 = (y_wing[1] // 9 + 0.5) * self.cell_size + self.top_margin
            root = (x1, y1)
            x2 = (y_wing[2] % 9 + 0.5) * self.cell_size + self.left_margin
            y2 = (y_wing[2] // 9 + 0.5) * self.cell_size + self.top_margin
            leaf = (x2, y2)
            width = 4 if x1 == x2 or y1 == y2 else 5
            pygame.draw.line(self.screen, MAGENTA, root, leaf, width=width)
            x2 = (y_wing[3] % 9 + 0.5) * self.cell_size + self.left_margin
            y2 = (y_wing[3] // 9 + 0.5) * self.cell_size + self.top_margin
            leaf = (x2, y2)
            width = 4 if x1 == x2 or y1 == y2 else 5
            pygame.draw.line(self.screen, MAGENTA, root, leaf, width=width)

    def _render_options(self, cell_id, pos):
        """ Render cell_id options (pencil marks) """
        options = self.input_board[cell_id]
        for value in options:
            digit = self.font_options.render(value, True, BLACK)
            self.screen.blit(digit, (pos[0] + self.offsets[value][0] + self.option_shift_x,
                                     pos[1] + self.offsets[value][1] + self.option_shift_y))

    def set_current_board(self, board):
        """ Save copy of the current board (before applying a tool)  """
        self.input_board = board.copy()

    def display_info(self, text):
        """ Display info 'text' starting at the left top corner of the window """
        msg = self.font_text.render(text, True, BLACK)
        top_margin = (self.top_margin - self.font_text.get_ascent()) // 2
        info_rect = pygame.Rect((self.left_margin, top_margin, 9 * self.cell_size, self.font_text_size+1))
        pygame.draw.rect(self.screen, GAINSBORO, info_rect)
        self.screen.set_clip(info_rect)
        self.screen.blit(msg, (self.left_margin, top_margin))
        self.screen.set_clip(None)

    def draw_board(self, board, solver_tool=None, **kwargs):
        """ TODO """

        if solver_tool and not (self.show_solution_steps and self.method[solver_tool] in self.inspect):
            return

        # TODO
        if solver_tool == "naked_twins":
            self.display_info("'Naked Pairs' technique")

        start = time.time()     # TODO
        house = kwargs["house"] if "house" in kwargs else None
        greyed_out = kwargs["greyed_out"] if "greyed_out" in kwargs else None
        other_cells = kwargs["other_cells"] if "other_cells" in kwargs else None
        naked_singles = kwargs["naked_singles"] if "naked_singles" in kwargs else []

        for row_id in range(9):
            for col_id in range(9):
                cell_id = row_id * 9 + col_id
                cell_pos = (col_id * self.cell_size + self.left_margin,
                            row_id * self.cell_size + self.top_margin)
                pygame.draw.rect(self.screen, WHITE,
                                 (cell_pos[0], cell_pos[1], self.cell_size + 1, self.cell_size + 1))
                if house and cell_id in house:
                    pygame.draw.rect(
                        self.screen, C_HOUSE,   # TODO
                        (cell_pos[0], cell_pos[1], self.cell_size + 1, self.cell_size + 1))
                if greyed_out and cell_id in greyed_out:
                    pygame.draw.rect(
                        self.screen, SILVER,
                        (cell_pos[0], cell_pos[1], self.cell_size + 1, self.cell_size + 1))

                if board[cell_id] != '.':
                    if other_cells and cell_id in other_cells:
                        pygame.draw.rect(
                            self.screen, C_OTHER_CELLS,   # TODO
                            (cell_pos[0], cell_pos[1], self.cell_size + 1, self.cell_size + 1))

                    if solver_tool is None: # and len(board[cell_id]) == 1:      TODO - fix it
                        # self._higlight_clue(cell_id, cell_pos, **kwargs)
                        self._render_clue(board[cell_id], cell_pos)
                    elif solver_tool == "manual_solution":
                        if board[cell_id] != ".":
                            self._higlight_clue(cell_id, cell_pos, **kwargs)
                            self._render_clue(board[cell_id], cell_pos)
                    else:
                        if len(self.input_board[cell_id]) == 1 and cell_id not in naked_singles:
                            self._higlight_clue(cell_id, cell_pos, **kwargs)
                            self._render_clue(self.input_board[cell_id], cell_pos)
                        else:
                            self._highlight_options(cell_id, board[cell_id], cell_pos, **kwargs)
                            self._render_options(cell_id, cell_pos)

        for i in range(10):
            line_thickness = 5 if i % 3 == 0 else 1
            pygame.draw.line(self.screen, BLACK, (self.left_margin- 2, i * self.cell_size + self.top_margin),
                             (self.left_margin+ 9 * self.cell_size + 2,
                              i * self.cell_size + self.top_margin), line_thickness)
            pygame.draw.line(self.screen, BLACK, (i * self.cell_size + self.left_margin, self.top_margin),
                             (i * self.cell_size + self.left_margin,
                              self.top_margin + 9 * self.cell_size), line_thickness)
        self._draw_board_features(**kwargs)
        btn_rect = self._draw_button(solver_tool)

        wait = True
        # start = time.time()
        while wait:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                if ev.type == pygame.MOUSEBUTTONDOWN and btn_rect.collidepoint(pygame.mouse.get_pos()):
                    self.show_solution_steps = False
                    wait = False
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_RETURN:
                        self.show_solution_steps = False
                        wait = False
                    if ev.key == pygame.K_RIGHT:
                        wait = False
                    if ev.key == pygame.K_DOWN:
                        wait = False
                    if ev.key == pygame.K_q:
                        pygame.quit()
                        sys.exit(0)
            pygame.display.update()

        self.input_board = board.copy()
        self.time_in += time.time() - start

    def quit(self):
        """ TODO """
        pygame.quit()

