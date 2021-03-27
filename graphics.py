# -*- coding: UTF-8 -*-

import pygame
import time

import graph_utils
from display import screen_messages

# RGB colors:
from graph_utils import BLACK
from graph_utils import BLUE
from graph_utils import GAINSBORO

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
        self.option_offsets = graph_utils.set_option_offsets()

        self.screen = None
        self.input_board = None
        self.board_cells = graph_utils.set_cell_rectangles()
        self.keypad_frame = graph_utils.set_keypad_frame()
        self.keypad_keys = graph_utils.set_keypad_keys()
        self.buttons = {}
        self.actions = {}

        self.method = graph_utils.set_methods()
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

    def critical_error_event(self, board, solver_tool, **kwargs):
        """ Handle 'Critical Error' event """
        self.show_solution_steps = True
        self.inspect = ''.join(self.method.values())
        self.animate = False
        graph_utils.set_btn_status(self, False)
        graph_utils.set_keyboard_status(self, False)
        if "new_clue" in kwargs and len(board[kwargs["new_clue"]]) == 1:
            self.clues_found.add(kwargs["new_clue"])
        kwargs["new_clue"] = None
        self.render_board(board, solver_tool, **kwargs)
        graph_utils.display_info(self, "DUPA JAŚ !!!")  # TODO - Fix it !!!

    def sudoku_solved_event(self, board):
        """ Handle 'Sudoku Solved' event """
        self.input_board = board.copy()
        self.animate = False
        graph_utils.set_btn_status(self, False, (pygame.K_m, pygame.K_s))
        graph_utils.set_btn_state(self, False, (pygame.K_m, pygame.K_s))

    def set_current_board(self, board):
        """ Save copy of the current board (before applying a tool)  """
        self.input_board = board.copy()

    def render_board(self, board, solver_tool, **kwargs):
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
                        graph_utils.render_clue(self, board[cell_id], cell_pos, BLACK)
                    elif cell_id in self.clues_found and len(board[cell_id]) == 1:
                        graph_utils.render_clue(self, board[cell_id], cell_pos, BLUE)
                    elif graph_utils.show_pencil_marks(self, cell_id, **kwargs):
                        if solver_tool != "plain_board":
                            graph_utils.highlight_options(self, cell_id, board[cell_id], cell_pos, **kwargs)
                        graph_utils.render_options(self, cell_id, cell_pos)

        for i in range(10):
            line_thickness = 5 if i % 3 == 0 else 1
            pygame.draw.line(self.screen, BLACK, (LEFT_MARGIN- 2, i * CELL_SIZE + TOP_MARGIN),
                             (LEFT_MARGIN+ 9 * CELL_SIZE + 2,
                              i * CELL_SIZE + TOP_MARGIN), line_thickness)
            pygame.draw.line(self.screen, BLACK, (i * CELL_SIZE + LEFT_MARGIN, TOP_MARGIN),
                             (i * CELL_SIZE + LEFT_MARGIN,
                              TOP_MARGIN + 9 * CELL_SIZE), line_thickness)
        graph_utils.draw_board_features(self, **kwargs)
        for button in self.buttons.values():
            button.draw(self.screen)
        graph_utils.display_info(self, screen_messages[solver_tool])
        pygame.display.update()

    def draw_board(self, board, solver_tool=None, **kwargs):
        """ TODO """

        if not solver_tool:
            self.input_board = board.copy()
        elif self.critical_error:
            self.critical_error_event(board, solver_tool, **kwargs)
        elif solver_tool == "end_of_game":
            self.sudoku_solved_event(board)
        elif not (self.show_solution_steps and self.method[solver_tool] in self.inspect):
            return True

        start = time.time()
        if self.previous_cell_value:
            graph_utils.set_btn_status(self, True, (pygame.K_b, ))
            self.input_board[self.previous_cell_value[0]] = self.input_board[self.conflicting_cells[0]]
            self.clues_found.add(self.previous_cell_value[0])
        self.render_board(self.input_board if self.input_board else board, "plain_board" if solver_tool else None,
                           conflicting_cells=self.conflicting_cells, house=self.clue_house)
        if self.previous_cell_value:
            self.input_board[self.previous_cell_value[0]] = self.previous_cell_value[1]
            self.clues_found.remove(self.previous_cell_value[0])
            self.previous_cell_value = None

        if self.conflicting_cells:
            graph_utils.display_info(self, screen_messages["conflicting_values"])
            self.conflicting_cells = None
            self.clue_house = None

        """
        if solver_tool == "end_of_game":
            graph_utils.display_info(self, screen_messages[solver_tool])
        if self.critical_error:
            graph_utils.display_info(self, "DUPA JAŚ !!!")  # TODO - Fix it !!!
        """

        self.board_updated = False
        self.wait = True if solver_tool else False  # TODO - temporary only!!!

        if self.animate:
            self.board_updated = True
            self.render_board(board, solver_tool, **kwargs)
            pygame.display.update()
            time.sleep(ANIMATION_STEP_TIME)
        # if not self.animate:
        else:
            while self.wait:
                event = None
                ev = pygame.event.poll()
                if ev.type == pygame.MOUSEBUTTONDOWN:
                    event = graph_utils.clicked_widget_id(self)
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