# -*- coding: UTF-8 -*-

import pygame
import time

import graph_utils
from display import screen_messages

# RGB colors:
from graph_utils import BLACK
from graph_utils import BLUE
from graph_utils import GAINSBORO
from graph_utils import LIGHTGREEN

from graph_utils import ANIMATION_STEP_TIME

from graph_utils import CELL_SIZE
from graph_utils import LEFT_MARGIN
from graph_utils import TOP_MARGIN

# keypad dimensions:
KEYPAD_DIGIT_W = 55
KEYPAD_DIGIT_H = 55
KEYPAD_DIGIT_OFFSET = 10
KEYPAD_LEFT_MARGIN = 80
KEYPAD_TOP_MARGIN = 80

# dimensions of control buttons:
BUTTON_H = 45
BUTTONS_OFFSET = 10

C_OTHER_CELLS = (255, 250, 190)

KEYBOARD_DIGITS = (1, 2, 3, 4, 5, 6, 7, 8, 9)


class AppWindow:
    """ TODO """
    def __init__(self, board, inspect):
        pygame.init()
        self.font_type = "FreeSans"
        self.font_clues_size = 47
        self.font_options_size = 15
        self.font_button_size = 20
        self.font_text_size = 17
        self.font_keypad_size = 22
        self.font_clues = pygame.font.SysFont(self.font_type, self.font_clues_size)
        self.font_options = pygame.font.SysFont(self.font_type, self.font_options_size, italic=True)
        self.font_text = pygame.font.SysFont(self.font_type, self.font_text_size, italic=True)
        self.font_keypad = pygame.font.SysFont(self.font_type, self.font_keypad_size, bold=True)
        self.clue_shift_x = (CELL_SIZE - self.font_clues.size('1')[0]) // 2
        self.clue_shift_y = (CELL_SIZE - self.font_clues.get_ascent()) // 2 - 2
        self.option_shift_x = (CELL_SIZE // 3 - self.font_options.size('1')[0]) // 2
        self.option_shift_y = (CELL_SIZE // 3 - self.font_options.get_ascent()) // 2
        self.option_offsets = graph_utils.get_offsets()

        self.screen = None
        self.input_board = None
        self.board_cells = graph_utils.get_cell_rectangles()
        self.keypad_frame = graph_utils.get_keypad_frame()
        self.keypad_keys = graph_utils.get_keypad_keys()
        self.buttons = {}
        self.actions = {}

        self.method = graph_utils.get_methods()
        self.peep = inspect if len(inspect) else ''.join(self.method.values())
        self.inspect = self.peep

        self.clues_defined = [cell_id for cell_id in range(81) if board[cell_id] != "."]
        self.clues_found = set()
        self.show_options = set()
        self.selected_key = None
        self.selected_cell = None
        self.show_solution_steps = True
        self.animate = False
        self.board_updated = False
        self.clue_entered = None
        self.conflicting_cells = None
        self.clue_house = None
        self.previous_cell_value = None
        self.show_all_pencil_marks = False
        self.critical_error = None
        self.wait = True
        self.time_in = 0

        pygame.display.set_caption('SUDOKU PUZZLE')
        pygame.display.set_icon(pygame.image.load('demon.png'))     # TODO - get a better icon
        self.screen = pygame.display.set_mode(graph_utils.window_size())
        self.screen.fill(GAINSBORO)
        graph_utils.set_buttons(self)

    def set_btn_status(self, state, btn_ids):
        """ TODO """
        for button in btn_ids:
            self.buttons[button].set_status(state)

    def set_keyboard_status(self, status):
        """ TODO """
        for i in range(1, 10):
            self.buttons[i].set_status(status)

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

    def _render_options(self, cell_id, pos):
        """ Render cell_id options (pencil marks) """
        options = self.input_board[cell_id]
        for value in options:
            digit = self.font_options.render(value, True, BLACK)
            self.screen.blit(digit, (pos[0] + self.option_offsets[value][0] + self.option_shift_x,
                                     pos[1] + self.option_offsets[value][1] + self.option_shift_y))

    def set_current_board(self, board):
        """ Save copy of the current board (before applying a tool)  """
        self.input_board = board.copy()

    def _show_pencil_marks(self, cell, **kwargs):
        """ TODO """
        if self.show_all_pencil_marks:
            return True
        if cell not in self.show_options:
            if "impacted_cells" in kwargs and cell in kwargs["impacted_cells"]:
                self.show_options.add(cell)
            if "claims" in kwargs and cell in kwargs["house"]:
                self.show_options.add(cell)
            if "y_wing" in kwargs and kwargs["y_wing"] and cell in kwargs["y_wing"][1:]:
                self.show_options.add(cell)
        return True if cell in self.show_options else False

    def _render_board(self, board, solver_tool, **kwargs):
        """ render board (TODO) """
        active_clue = kwargs["new_clue"] if "new_clue" in kwargs else None
        for row_id in range(9):
            for col_id in range(9):
                cell_id = row_id * 9 + col_id
                cell_pos = (col_id * CELL_SIZE + LEFT_MARGIN, row_id * CELL_SIZE + TOP_MARGIN)
                cell_rect = (cell_pos[0], cell_pos[1], CELL_SIZE + 1, CELL_SIZE + 1)
                pygame.draw.rect(self.screen, graph_utils.cell_color(self, cell_id, **kwargs), cell_rect)

                if board[cell_id] != '.':
                    if solver_tool is None or cell_id in self.clues_defined or cell_id == active_clue:
                        self._render_clue(board[cell_id], cell_pos, BLACK)
                    elif cell_id in self.clues_found and len(board[cell_id]) == 1:
                        self._render_clue(board[cell_id], cell_pos, BLUE)
                    elif self._show_pencil_marks(cell_id, **kwargs):
                        if solver_tool != "plain_board":
                            graph_utils.highlight_options(self, cell_id, board[cell_id], cell_pos, **kwargs)
                        self._render_options(cell_id, cell_pos)

        for i in range(10):
            line_thickness = 5 if i % 3 == 0 else 1
            pygame.draw.line(self.screen, BLACK, (LEFT_MARGIN- 2, i * CELL_SIZE + TOP_MARGIN),
                             (LEFT_MARGIN+ 9 * CELL_SIZE + 2,
                              i * CELL_SIZE + TOP_MARGIN), line_thickness)
            pygame.draw.line(self.screen, BLACK, (i * CELL_SIZE + LEFT_MARGIN, TOP_MARGIN),
                             (i * CELL_SIZE + LEFT_MARGIN,
                              TOP_MARGIN + 9 * CELL_SIZE), line_thickness)
        graph_utils.draw_board_features(self, **kwargs)
        self._draw_buttons()
        graph_utils.display_info(self, screen_messages[solver_tool])

    def _get_cell_id(self, mouse_pos):
        """ TODO """
        for cell_id, cell_rect in self.board_cells.items():
            if cell_rect.collidepoint(mouse_pos):
                return cell_id + 1000
        return None

    def draw_board(self, board, solver_tool=None, **kwargs):
        """ TODO """

        if self.critical_error:
            self.show_solution_steps = True
            self.inspect = ''.join(self.method.values())
            self.animate = False
            self.buttons[pygame.K_m].set_pressed(False)
            self.buttons[pygame.K_s].set_pressed(False)
            self.set_btn_status(False, (pygame.K_c, pygame.K_p, pygame.K_a, pygame.K_h, pygame.K_b,
                                        pygame.K_m, pygame.K_s))
            self.set_keyboard_status(False)
            if "new_clue" in kwargs and len(board[kwargs["new_clue"]]) == 1:
                self.clues_found.add(kwargs["new_clue"])
            kwargs["new_clue"] = None
            self._render_board(board, solver_tool, **kwargs)
            graph_utils.display_info(self, "DUPA JAŚ !!!")  # TODO - Fix it !!!
            pygame.display.update()

        if not solver_tool:
            self.input_board = board.copy()
        elif solver_tool == "end_of_game":
            self.input_board = board.copy()
            self.animate = False
            self.buttons[pygame.K_m].set_pressed(False)
            self.buttons[pygame.K_m].set_status(False)
            self.buttons[pygame.K_s].set_pressed(False)
            self.buttons[pygame.K_s].set_status(False)
            for i in range(81):
                if i not in self.clues_defined and i not in self.clues_found:
                    self.clues_found.add(i)
        elif not (self.show_solution_steps and self.method[solver_tool] in self.inspect):
            return True

        start = time.time()     # TODO
        graph_utils.draw_keypad(self)
        if self.previous_cell_value:
            self.input_board[self.previous_cell_value[0]] = self.input_board[self.conflicting_cells[0]]
            self.clues_found.add(self.previous_cell_value[0])
        self._render_board(self.input_board if self.input_board else board, "plain_board" if solver_tool else None,
                           conflicting_cells=self.conflicting_cells, house=self.clue_house)
        if self.previous_cell_value:
            self.input_board[self.previous_cell_value[0]] = self.previous_cell_value[1]
            self.clues_found.remove(self.previous_cell_value[0])
            self.previous_cell_value = None

        if self.conflicting_cells:
            graph_utils.display_info(self, screen_messages["conflicting_values"])
            self.conflicting_cells = None
            self.clue_house = None
        if solver_tool == "end_of_game":
            graph_utils.display_info(self, screen_messages[solver_tool])
        if self.critical_error:
            graph_utils.display_info(self, "DUPA JAŚ !!!")  # TODO - Fix it !!!

        self.board_updated = False
        self.wait = True if solver_tool else False  # TODO - temporary only!!!

        if self.animate:
            self.board_updated = True
            self._render_board(board, solver_tool, **kwargs)
            pygame.display.update()
            time.sleep(ANIMATION_STEP_TIME)
        # if not self.animate:
        else:
            while self.wait:
                event = None
                ev = pygame.event.poll()
                if ev.type == pygame.MOUSEBUTTONDOWN:
                    event = self._button_pressed()
                    if event is None:
                        event = self._get_cell_id(pygame.mouse.get_pos())
                elif ev.type == pygame.KEYDOWN:
                    if ev.key in self.keypad_keys:
                        event = self.keypad_keys[ev.key]
                    else:
                        event = ev.key
                if event in self.actions:
                    self.actions[event](self, event, board, solver_tool, **kwargs)
                pygame.display.update()

        if self.board_updated:
            self.input_board = board.copy()
        self.time_in += time.time() - start
        return self.board_updated

    def quit(self):
        """ TODO """
        pygame.quit()