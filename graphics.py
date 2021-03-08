# -*- coding: UTF-8 -*-

import pygame
import sys
import time

from display import screen_messages

# dimensions of sudoku board:
CELL_SIZE = 66
LEFT_MARGIN = 25
TOP_MARGIN = 60
BOTTOM_MARGIN = 90

# keypad dimensions:
KEYPAD_DIGIT_W = 55
KEYPAD_DIGIT_H = 55
KEYPAD_DIGIT_OFFSET = 10
KEYPAD_LEFT_MARGIN = 80
KEYPAD_TOP_MARGIN = 80

# dimensions of control buttons:
BUTTON_H = 45
BUTTONS_OFFSET = 10

# RGB colors:
BLACK = (0, 0, 0)
BLUE = (51, 102, 153)
WHITE = (255, 255, 255)
GREY = (160, 160, 160)
MAGENTA = (255, 0, 255)
LIME = (0, 255, 0)
CYAN = (0, 255, 255)
SILVER = (192, 192, 192)
LIGHTGREEN = (190, 255, 190)
LIENGHTPINK = (255, 182, 193)
GAINSBORO = (230, 230, 230)
DARKGREY = (150, 150, 150)
LIGHTGREY = (200, 200, 200)

C_HOUSE = (255, 255, 225)
C_OTHER_CELLS = (255, 250, 190)
Y_WING_ROOT = (255, 153, 51)
Y_WING_LEAF = (255, 153, 51)  

ANIMATION_STEP_TIME = 0.2


class Button:
    """ TODO """
    def __init__(self, rect, text,
                 border_color=DARKGREY, face_color=WHITE, font_color=BLACK,
                 disable_border_color=LIGHTGREY, disable_face_color=WHITE, disable_font_color=LIGHTGREY,
                 pressed_border_color=DARKGREY, pressed_face_color=WHITE, pressed_font_color=BLACK,
                 call_back_function=None):
        self.rect = rect
        self.text = text
        self.border_color = border_color
        self.face_color = face_color
        self.font_color = font_color
        self.disable_border_color = disable_border_color
        self.disable_face_color = disable_face_color
        self.disable_font_color = disable_font_color
        self.pressed_border_color = pressed_border_color
        self.pressed_face_color = pressed_face_color
        self.pressed_font_color = pressed_font_color
        self.call_back_function = call_back_function
        self.font_button = pygame.font.SysFont("FreeSans", 20, bold=True)
        self.txt_x = rect[0] + (rect[2] - self.font_button.size(self.text)[0]) // 2
        self.txt_y = rect[1] + (rect[3] - self.font_button.get_ascent()) // 2
        self.active = True
        self.pressed = False

    def draw(self, screen):
        """ TODO """
        if self.active and not self.pressed:
            pygame.draw.rect(screen, self.face_color, self.rect, border_radius=9)
            pygame.draw.rect(screen, self.border_color, self.rect, width=2, border_radius=9)
            btn_txt = self.font_button.render(self.text, True, self.font_color)
            screen.blit(btn_txt, (self.txt_x, self.txt_y))
        elif not self.active:
            pygame.draw.rect(screen, self.face_color, self.rect, border_radius=9)
            pygame.draw.rect(screen, self.disable_border_color, self.rect, width=2, border_radius=9)
            btn_txt = self.font_button.render(self.text, True, self.disable_font_color)
            screen.blit(btn_txt, (self.txt_x, self.txt_y))
        elif self.pressed:
            pygame.draw.rect(screen, self.pressed_face_color, self.rect, border_radius=9)
            pygame.draw.rect(screen, self.pressed_border_color, self.rect, width=2, border_radius=9)
            btn_txt = self.font_button.render(self.text, True, self.pressed_font_color)
            screen.blit(btn_txt, (self.txt_x, self.txt_y))

    def being_pressed(self, wait_to_release=False):
        """ TODO """
        if self.active and not wait_to_release and self.rect.collidepoint(pygame.mouse.get_pos()):
            if self.call_back_function:
                self.call_back_function()
            return True
        return False

    def set_status(self, enable):
        """ TODO """
        self.active = enable

    def is_active(self):
        """ TODO """
        return self.active

    def set_pressed(self, pressed):
        """ TODO """
        self.pressed = pressed

    def is_pressed(self):
        """ TODO """
        return self.pressed


class AppWindow:
    """ TODO """
    def __init__(self, board, inspect):
        pygame.init()

        self.dark_grey = (150, 150, 150)        # TODO - remove it from here!

        self.font_type = "FreeSans"
        self.font_clues_size = 47
        self.font_options_size = 15
        self.font_button_size = 20
        self.font_text_size = 17
        self.font_keypad_size = 22
        self.font_clues = pygame.font.SysFont(self.font_type, self.font_clues_size)
        self.font_options = pygame.font.SysFont(self.font_type, self.font_options_size, italic=True)
        # self.font_button = pygame.font.SysFont(self.font_type, self.font_button_size, bold=True)
        self.font_text = pygame.font.SysFont(self.font_type, self.font_text_size, italic=True)
        self.font_keypad = pygame.font.SysFont(self.font_type, self.font_keypad_size, bold=True)
        self.clue_shift_x = (CELL_SIZE - self.font_clues.size('1')[0]) // 2
        self.clue_shift_y = (CELL_SIZE - self.font_clues.get_ascent()) // 2 - 2    # TODO
        self.option_shift_x = (CELL_SIZE // 3 - self.font_options.size('1')[0]) // 2
        self.option_shift_y = (CELL_SIZE // 3 - self.font_options.get_ascent()) // 2
        self.offsets = {'1': (0, 0),
                        '2': (CELL_SIZE // 3, 0),
                        '3': (2 * CELL_SIZE // 3, 0),
                        '4': (0, CELL_SIZE // 3),
                        '5': (CELL_SIZE // 3, CELL_SIZE // 3),
                        '6': (2 * CELL_SIZE // 3, CELL_SIZE // 3),
                        '7': (0, 2 * CELL_SIZE // 3),
                        '8': (CELL_SIZE // 3, 2 * CELL_SIZE // 3),
                        '9': (2 * CELL_SIZE // 3, 2 * CELL_SIZE // 3),
                        }

        self.show_solution_steps = True
        self.inspect = inspect
        self.method = {
            # "manual_solution": "m",     # TODO - fix it (remove manual solution)
            "open_singles": "g",
            "visual_elimination": "v",
            "naked_singles": "n",
            "hidden_singles": "u",
            "scrub_pencil_marks": "e",  # TODO - fix it!
            "unique_values": "u",       # TODO - fix it!
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

        display_width = LEFT_MARGIN + 9 * CELL_SIZE + 2 * KEYPAD_LEFT_MARGIN + \
            3 * KEYPAD_DIGIT_W + 2 * KEYPAD_DIGIT_OFFSET
        display_height = TOP_MARGIN + 9 * CELL_SIZE + BOTTOM_MARGIN
        self.screen = pygame.display.set_mode((display_width, display_height))
        self.screen.fill(GAINSBORO)
        pygame.display.set_caption('SUDOKU PUZZLE')
        pygame.display.set_icon(pygame.image.load('demon.png'))     # TODO - fix it!

        self.input_board = None
        self.clues_found = []
        self.clues_defined = []
        self.board_cells = {}
        self.keypad = {}
        self.buttons = {}
        self.actions = {}
        self.animate = False
        self.board_updated = False

        for i in range(81):
            if board[i] != '.':
                self.clues_defined.append(i)

        for row_id in range(9):
            for col_id in range(9):
                cell_rect = pygame.Rect((col_id * CELL_SIZE + LEFT_MARGIN,
                                         row_id * CELL_SIZE + TOP_MARGIN,
                                         CELL_SIZE, CELL_SIZE))
                self.board_cells[row_id * 9 + col_id] = cell_rect

        x_offset = LEFT_MARGIN + 9 * CELL_SIZE + KEYPAD_LEFT_MARGIN
        for row in range(3):
            for col in range(3):
                digit = 3 * row + col + 1
                btn_x = x_offset + col * (KEYPAD_DIGIT_W + KEYPAD_DIGIT_OFFSET)
                btn_y = KEYPAD_TOP_MARGIN + row * (KEYPAD_DIGIT_H + KEYPAD_DIGIT_OFFSET)
                btn_rect = pygame.Rect((btn_x, btn_y, KEYPAD_DIGIT_W, KEYPAD_DIGIT_H))
                self.keypad[digit] = btn_rect

        x_offset -= 20
        y_offset = KEYPAD_TOP_MARGIN - 20
        keyboard_w = 3 * (KEYPAD_DIGIT_W + KEYPAD_DIGIT_OFFSET) - KEYPAD_DIGIT_OFFSET + 40
        keyboard_h = 3 * (KEYPAD_DIGIT_H + KEYPAD_DIGIT_OFFSET) - KEYPAD_DIGIT_OFFSET + 40
        self.keypad_frame = pygame.Rect((x_offset, y_offset, keyboard_w, keyboard_h))

        self._set_buttons()
        self.wait = True
        self.dupa_counter = 0

    def clue_pressed(self, *args, **kwargs):
        """ TODO """
        if self.buttons[pygame.K_c].is_active() and not self.buttons[pygame.K_c].is_pressed():
            self.buttons[pygame.K_c].set_pressed(True)
            self.buttons[pygame.K_c].draw(self.screen)
            self.buttons[pygame.K_p].set_pressed(False)
            self.buttons[pygame.K_p].draw(self.screen)

    def pencil_mark_pressed(self, *args, **kwargs):
        """ TODO """
        if self.buttons[pygame.K_p].is_active() and not self.buttons[pygame.K_p].is_pressed():
            self.buttons[pygame.K_p].set_pressed(True)
            self.buttons[pygame.K_p].draw(self.screen)
            self.buttons[pygame.K_c].set_pressed(False)
            self.buttons[pygame.K_c].draw(self.screen)

    def accept_pressed(self, *args, **kwargs):
        """ TODO """
        if self.buttons[pygame.K_a].is_active():
            self.buttons[pygame.K_b].set_status(False)
            self.buttons[pygame.K_a].set_status(False)
            self.buttons[pygame.K_c].set_status(True)
            self.buttons[pygame.K_p].set_status(True)
            self.board_updated = True
            self.wait = False

    def hint_pressed(self, board, solver_tool, **kwargs):
        """ TODO """
        if self.buttons[pygame.K_h].is_active():
            self.buttons[pygame.K_a].set_status(True)
            self.buttons[pygame.K_b].set_status(True)
            self.buttons[pygame.K_c].set_status(False)
            self.buttons[pygame.K_p].set_status(False)
            self._render_board(board, solver_tool, **kwargs)

    def solve_pressed(self):
        """ TODO """
        self.show_solution_steps = False
        self.wait = False

    def back_pressed(self, board, solver_tool, **kwargs):
        """ TODO """
        self.buttons[pygame.K_a].set_status(False)
        self.buttons[pygame.K_b].set_status(False)
        self.buttons[pygame.K_c].set_status(True)
        self.buttons[pygame.K_p].set_status(True)
        self._render_board(self.input_board, "plain_board", options_set=kwargs["options_set"])

    def animate_pressed(self, board, solver_tool, **kwargs):
        """ TODO """
        self.buttons[pygame.K_c].set_status(False)
        self.buttons[pygame.K_p].set_status(False)
        self.buttons[pygame.K_m].set_pressed(True)
        self.buttons[pygame.K_h].set_status(False)
        self.buttons[pygame.K_b].set_status(False)
        self.buttons["solve"].set_status(False)
        self.animate = True
        self.wait = False
        self.board_updated = True
        self._render_board(board, solver_tool, **kwargs)
        pygame.display.update()
        time.sleep(ANIMATION_STEP_TIME)

    def _set_buttons(self):
        """ TODO """
        btn_x = self.keypad_frame[0]
        btn_y = self.keypad_frame[1] + self.keypad_frame[3] + 30

        btn_rect = pygame.Rect((btn_x, btn_y, self.keypad_frame[3], BUTTON_H))
        self.buttons[pygame.K_c] = Button(btn_rect, "Clue",
                                          pressed_border_color=BLUE,
                                          pressed_face_color=BLUE,
                                          pressed_font_color=WHITE)
        self.buttons[pygame.K_c].set_pressed(True)
        self.actions[pygame.K_c] = self.clue_pressed

        btn_y += BUTTON_H + BUTTONS_OFFSET
        btn_rect = pygame.Rect((btn_x, btn_y, self.keypad_frame[3], BUTTON_H))
        self.buttons[pygame.K_p] = Button(btn_rect, "Pencil Mark",
                                          pressed_border_color=BLUE,
                                          pressed_face_color=BLUE,
                                          pressed_font_color=WHITE)
        self.actions[pygame.K_p] = self.pencil_mark_pressed

        btn_y += BUTTON_H + BUTTONS_OFFSET
        btn_rect = pygame.Rect((btn_x, btn_y, self.keypad_frame[3], BUTTON_H))
        self.buttons[pygame.K_a] = Button(btn_rect, "Accept")
        self.buttons[pygame.K_a].set_status(False)
        self.actions[pygame.K_a] = self.accept_pressed

        btn_y += BUTTON_H + BUTTONS_OFFSET + 20
        btn_w = (self.keypad_frame[3] - BUTTONS_OFFSET) // 2
        btn_rect = pygame.Rect((btn_x, btn_y, btn_w, BUTTON_H))
        self.buttons[pygame.K_h] = Button(btn_rect, "Hint")
        self.actions[pygame.K_h] = self.hint_pressed

        btn_rect = pygame.Rect((btn_x + btn_w + BUTTONS_OFFSET, btn_y, btn_w, BUTTON_H))
        self.buttons[pygame.K_b] = Button(btn_rect, "Back")
        self.buttons[pygame.K_b].set_status(False)
        self.actions[pygame.K_b] = self.back_pressed

        btn_y += BUTTON_H + BUTTONS_OFFSET
        btn_rect = pygame.Rect((btn_x, btn_y, self.keypad_frame[3], BUTTON_H))
        self.buttons[pygame.K_m] = Button(btn_rect, "Animate",
                                          pressed_border_color=BLUE,
                                          pressed_face_color=BLUE,
                                          pressed_font_color=WHITE)
        self.actions[pygame.K_m] = self.animate_pressed

        btn_y += BUTTON_H + BUTTONS_OFFSET
        btn_rect = pygame.Rect((btn_x, btn_y, self.keypad_frame[3], BUTTON_H))
        self.buttons["solve"] = Button(btn_rect, "Auto Solve", call_back_function=self.solve_pressed)

    def _draw_buttons(self):
        """ TODO """
        for button in self.buttons.values():
            button.draw(self.screen)

    def _button_pressed(self):
        """ TODO """
        for key, button in self.buttons.items():
            if button.being_pressed():
                return key
        return None

    def _draw_keypad_button(self, btn_rect, digit):
        """ TODO """
        pygame.draw.rect(self.screen, self.dark_grey, btn_rect, border_radius=9)
        button_text = self.font_keypad.render(str(digit), True, BLACK)
        txt_x = btn_rect[0] + (KEYPAD_DIGIT_W - self.font_keypad.size(str(digit))[0]) // 2
        txt_y = btn_rect[1] + (KEYPAD_DIGIT_H - self.font_keypad.get_ascent()) // 2
        self.screen.blit(button_text, (txt_x, txt_y))

    def _draw_keypad(self):
        """ TODO """
        pygame.draw.rect(self.screen, self.dark_grey, self.keypad_frame, width=1, border_radius=9)
        for i in range(1, 10):
            self._draw_keypad_button(self.keypad[i], i)

    def _render_clue(self, clue, pos, color):
        """ Render board clues """
        digit = self.font_clues.render(clue, True, color)
        self.screen.blit(digit, (pos[0] + self.clue_shift_x, pos[1] + self.clue_shift_y))

    def _highlight_clue(self, cell_id, pos, **kwargs):
        """ Highlight clue cell, as applicable """

        active_clue = kwargs["new_clue"] if "new_clue" in kwargs else None

        if cell_id == active_clue:
            pygame.draw.rect(
                self.screen, LIGHTGREEN,
                (pos[0], pos[1], CELL_SIZE + 1, CELL_SIZE + 1))

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
                self.screen, LIENGHTPINK,
                (pos[0], pos[1], CELL_SIZE + 1, CELL_SIZE + 1))
        if y_wing is not None and cell_id == y_wing[1]:
            pygame.draw.rect(
                self.screen, Y_WING_ROOT,
                (pos[0], pos[1], CELL_SIZE + 1, CELL_SIZE + 1))
        if y_wing is not None and (cell_id == y_wing[2] or cell_id == y_wing[3]):
            pygame.draw.rect(
                self.screen, Y_WING_LEAF,
                (pos[0], pos[1], CELL_SIZE + 1, CELL_SIZE + 1))
        if corners and cell_id in corners or x_wing and cell_id in x_wing[1:]:
            pygame.draw.rect(
                self.screen, Y_WING_LEAF,       # TODO
                (pos[0], pos[1], CELL_SIZE + 1, CELL_SIZE + 1))
        if sword and cell_id in sword[1:]:
            pygame.draw.rect(
                self.screen, Y_WING_LEAF,       # TODO
                (pos[0], pos[1], CELL_SIZE + 1, CELL_SIZE + 1))

        for value in self.input_board[cell_id]:
            if remove and (value, cell_id) in remove:
                pygame.draw.rect(self.screen, GREY,
                                 (pos[0] + self.offsets[value][0],
                                  pos[1] + self.offsets[value][1],
                                  CELL_SIZE // 3, CELL_SIZE // 3))

            if subset and value in new_value and cell_id in subset:
                pygame.draw.rect(self.screen, CYAN,
                                 (pos[0] + self.offsets[value][0],
                                  pos[1] + self.offsets[value][1],
                                  CELL_SIZE // 3, CELL_SIZE // 3))
            if claims and (value, cell_id) in claims:
                pygame.draw.rect(self.screen, CYAN,
                                 (pos[0] + self.offsets[value][0],
                                  pos[1] + self.offsets[value][1],
                                  CELL_SIZE // 3, CELL_SIZE // 3))
            if x_wing and value == x_wing[0] and cell_id in x_wing[1:]:
                pygame.draw.rect(self.screen, CYAN,
                                 (pos[0] + self.offsets[value][0],
                                  pos[1] + self.offsets[value][1],
                                  CELL_SIZE // 3, CELL_SIZE // 3))
            if y_wing and value == y_wing[0] and cell_id in (y_wing[2], y_wing[3]):
                pygame.draw.rect(self.screen, CYAN,
                                 (pos[0] + self.offsets[value][0],
                                  pos[1] + self.offsets[value][1],
                                  CELL_SIZE // 3, CELL_SIZE // 3))
            if sword and value == sword[0] and cell_id in sword[1:]:
                pygame.draw.rect(self.screen, CYAN,
                                 (pos[0] + self.offsets[value][0],
                                  pos[1] + self.offsets[value][1],
                                  CELL_SIZE // 3, CELL_SIZE // 3))

    def _draw_board_features(self, **kwargs):
        """ TBD """

        rectangle = kwargs["rectangle"] if "rectangle" in kwargs else None
        y_wing = kwargs["y_wing"] if "y_wing" in kwargs else None
        x_wing = kwargs["x_wing"] if "x_wing" in kwargs else None

        if rectangle:
            left = (rectangle[0] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
            top = (rectangle[0] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
            right = (rectangle[1] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
            bottom = (rectangle[2] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
            rect = pygame.Rect(left, top, right - left, bottom - top)
            pygame.draw.rect(self.screen, MAGENTA, rect, width=4)

        if x_wing:
            color = MAGENTA
            x_wing = sorted(x_wing[1:])
            x1 = (x_wing[0] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
            y1 = (x_wing[0] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
            x2 = (x_wing[3] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
            y2 = (x_wing[3] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
            pygame.draw.line(self.screen, color, (x1, y1), (x2, y2), width=5)
            x1 = (x_wing[1] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
            y1 = (x_wing[1] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
            x2 = (x_wing[2] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
            y2 = (x_wing[2] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
            pygame.draw.line(self.screen, color, (x1, y1), (x2, y2), width=5)

        if y_wing:
            x1 = (y_wing[1] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
            y1 = (y_wing[1] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
            root = (x1, y1)
            x2 = (y_wing[2] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
            y2 = (y_wing[2] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
            leaf = (x2, y2)
            width = 4 if x1 == x2 or y1 == y2 else 5
            pygame.draw.line(self.screen, MAGENTA, root, leaf, width=width)
            x2 = (y_wing[3] % 9 + 0.5) * CELL_SIZE + LEFT_MARGIN
            y2 = (y_wing[3] // 9 + 0.5) * CELL_SIZE + TOP_MARGIN
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
        if text:
            msg = self.font_text.render(text, True, BLACK)
            top_margin = (TOP_MARGIN - self.font_text.get_ascent()) // 2
            info_rect = pygame.Rect((LEFT_MARGIN, top_margin, 9 * CELL_SIZE, self.font_text_size+1))
            pygame.draw.rect(self.screen, GAINSBORO, info_rect)
            self.screen.set_clip(info_rect)
            self.screen.blit(msg, (LEFT_MARGIN, top_margin))
            self.screen.set_clip(None)

    def _render_board(self, board, solver_tool, **kwargs):
        """ render board (TODO) """
        options_set = kwargs["options_set"] if "options_set" in kwargs else True
        house = kwargs["house"] if "house" in kwargs else None
        greyed_out = kwargs["greyed_out"] if "greyed_out" in kwargs else None
        other_cells = kwargs["other_cells"] if "other_cells" in kwargs else None
        active_clue = kwargs["new_clue"] if "new_clue" in kwargs else None

        self.display_info(screen_messages[solver_tool])

        for row_id in range(9):
            for col_id in range(9):
                cell_id = row_id * 9 + col_id
                cell_pos = (col_id * CELL_SIZE + LEFT_MARGIN,
                            row_id * CELL_SIZE + TOP_MARGIN)
                pygame.draw.rect(self.screen, WHITE,
                                 (cell_pos[0], cell_pos[1], CELL_SIZE + 1, CELL_SIZE + 1))
                if house and cell_id in house:
                    pygame.draw.rect(
                        self.screen, C_HOUSE,   # TODO
                        (cell_pos[0], cell_pos[1], CELL_SIZE + 1, CELL_SIZE + 1))
                if greyed_out and cell_id in greyed_out:
                    pygame.draw.rect(
                        self.screen, SILVER,
                        (cell_pos[0], cell_pos[1], CELL_SIZE + 1, CELL_SIZE + 1))

                if board[cell_id] != '.':
                    self._highlight_clue(cell_id, cell_pos, **kwargs)
                    if other_cells and cell_id in other_cells:
                        pygame.draw.rect(
                            self.screen, C_OTHER_CELLS,   # TODO
                            (cell_pos[0], cell_pos[1], CELL_SIZE + 1, CELL_SIZE + 1))

                    if solver_tool is None or cell_id in self.clues_defined or (active_clue and active_clue == cell_id):
                        self._render_clue(board[cell_id], cell_pos, BLACK)
                    elif not options_set:
                        self._render_clue(board[cell_id], cell_pos, BLUE)
                    else:
                        # print(f'{self.input_board = }')
                        if len(self.input_board[cell_id]) == 1 and cell_id in self.clues_found:
                            self._highlight_clue(cell_id, cell_pos, **kwargs)
                            self._render_clue(self.input_board[cell_id], cell_pos,
                                              BLUE if cell_id in self.clues_found else BLACK)
                        else:
                            if solver_tool != "plain_board":
                                self._highlight_options(cell_id, board[cell_id], cell_pos, **kwargs)
                            self._render_options(cell_id, cell_pos)

        for i in range(10):
            line_thickness = 5 if i % 3 == 0 else 1
            pygame.draw.line(self.screen, BLACK, (LEFT_MARGIN- 2, i * CELL_SIZE + TOP_MARGIN),
                             (LEFT_MARGIN+ 9 * CELL_SIZE + 2,
                              i * CELL_SIZE + TOP_MARGIN), line_thickness)
            pygame.draw.line(self.screen, BLACK, (i * CELL_SIZE + LEFT_MARGIN, TOP_MARGIN),
                             (i * CELL_SIZE + LEFT_MARGIN,
                              TOP_MARGIN + 9 * CELL_SIZE), line_thickness)
        self._draw_board_features(**kwargs)
        self._draw_buttons()
        return None

    def _get_cell_id(self, mouse_pos):
        """ TODO """

        for cell_id, cell_rect in self.board_cells.items():
            if cell_rect.collidepoint(mouse_pos):
                return cell_id
        return None

    def draw_board(self, board, solver_tool=None, **kwargs):
        """ TODO """

        if not solver_tool:
            self.input_board = board.copy()
        elif solver_tool == "end_of_game":
            self.input_board = board.copy()
            self.animate = False
            self.buttons[pygame.K_m].set_pressed(False)
            self.buttons[pygame.K_m].set_status(False)
            for i in range(81):
                if i not in self.clues_defined and i not in self.clues_found:
                    self.clues_found.append(i)
        elif not (self.show_solution_steps and self.method[solver_tool] in self.inspect):
            return

        start = time.time()     # TODO
        options_set = kwargs["options_set"] if "options_set" in kwargs else False
        self._draw_keypad()
        self._render_board(self.input_board if self.input_board else board, "plain_board" if solver_tool else None,
                           ptions_set=options_set)
        if solver_tool == "end_of_game":
            self.display_info(screen_messages[solver_tool])

        self.board_updated = False
        self.wait = True if solver_tool else False

        if self.animate:
            self.board_updated = True
            self._render_board(board, solver_tool, **kwargs)
            pygame.display.update()
            time.sleep(ANIMATION_STEP_TIME)
        else:
            while self.wait:
                event = None
                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT:
                        event = "quit"
                    elif ev.type == pygame.MOUSEBUTTONDOWN:
                        event = self._button_pressed()
                    elif ev.type == pygame.KEYDOWN:
                        event = ev.key

                    if event in ("solve", pygame.K_s):
                        pass
                    elif event in ("quit", pygame.K_q):
                        pygame.quit()
                        sys.exit(0)
                    elif event in self.actions:
                        self.actions[event](board, solver_tool, **kwargs)

                    """
                        elif not accept:
                            cell_id = self._get_cell_id(pygame.mouse.get_pos())
                            if cell_id is not None:
                                self._render_board(self.input_board if self.input_board else board,
                                                   "plain_board", options_set=options_set)
                                cell_selected = cell_id if cell_selected != cell_id else None
                                if cell_selected is not None:
                                    self.input_board[cell_id] = '5'   # TODO
                                    self._render_board(self.input_board if self.input_board else board,
                                                       "plain_board", options_set=options_set, new_clue=cell_id)
                    """
                pygame.display.update()

        if self.board_updated:
            self.input_board = board.copy()
        elif solver_tool:
            for i in range(81):
                board[i] = self.input_board[i]
        self.time_in += time.time() - start

        return self.board_updated

    def quit(self):
        """ TODO """
        pygame.quit()

