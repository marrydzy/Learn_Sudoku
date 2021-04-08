# -*- coding: UTF-8 -*-

import pygame
import time

import graph_utils
from display import screen_messages

# RGB colors:
from graph_utils import BLACK
from graph_utils import BLUE
from graph_utils import GREY
from graph_utils import GAINSBORO

from graph_utils import ANIMATION_STEP_TIME

from graph_utils import CELL_SIZE
from graph_utils import LEFT_MARGIN
from graph_utils import TOP_MARGIN


C_OTHER_CELLS = (255, 250, 190)

KEYBOARD_DIGITS = (1, 2, 3, 4, 5, 6, 7, 8, 9)


class AppWindow:
    """ TODO """
    def __init__(self, board, inspect):
        if not pygame.get_init():
            pygame.init()
        self.font_type = "FreeSans"
        self.font_clues_size = 47
        self.font_options_size = 15
        self.font_button_size = 20
        self.font_text_size = 22
        self.font_keypad_size = 40
        self.font_clues = pygame.font.SysFont(self.font_type, self.font_clues_size)
        self.font_options = pygame.font.SysFont(self.font_type, self.font_options_size, italic=True)
        self.font_text = pygame.font.SysFont(self.font_type, self.font_text_size, italic=True)
        self.font_buttons = pygame.font.SysFont(self.font_type, self.font_button_size, bold=True)
        self.font_keypad = pygame.font.SysFont(self.font_type, self.font_keypad_size, bold=False)
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
        self.wrong_values = set()
        self.options_visible = set()
        self.remove_from_visible = set()
        self.selected_key = None
        self.selected_cell = None
        self.show_solution_steps = True
        self.show_wrong_values = False
        self.animate = False
        self.board_updated = False
        self.clue_entered = None
        self.entered_conflicted_value = False
        self.show_all_pencil_marks = False
        self.critical_error = None
        self.wait = False
        self.calculate_next_clue = False

        self.time_in = 0
        self.solver_loop = None
        self.solved_board = None

        pygame.display.set_caption('SUDOKU PUZZLE')
        pygame.display.set_icon(pygame.image.load('demon.png'))     # TODO - get a better icon
        self.screen = pygame.display.set_mode(graph_utils.window_size())
        self.screen.fill(GAINSBORO)
        graph_utils.set_buttons(self)

    def critical_error_event(self, board, solver_tool, **kwargs):
        """ Handle 'Critical Error' event """
        # print(f'\n{self.critical_error = }\n')
        # raise Exception
        if self.buttons[pygame.K_h].is_pressed() or self.buttons[pygame.K_m].is_pressed() or self.buttons[pygame.K_s].is_pressed():
            self.show_solution_steps = True
            self.inspect = ''.join(self.method.values())
            self.animate = False
            self.show_wrong_values = True
            graph_utils.set_keyboard_status(self, False)
            graph_utils.set_btn_status(self, False)
            graph_utils.set_btn_status(self, True, (pygame.K_q, pygame.K_r))
            if "new_clue" in kwargs:
                if len(board[kwargs["new_clue"]]) == 1:
                    if kwargs["new_clue"] in self.options_visible:
                        self.options_visible.remove(kwargs["new_clue"])
                    self.clues_found.add(kwargs["new_clue"])
                else:
                    self.options_visible.add(kwargs["new_clue"])
            for cell in self.critical_error:
                self.options_visible.add(cell)
            self.set_current_board(board)

    def sudoku_solved_event(self, board):
        """ Handle 'Sudoku Solved' event """
        self.input_board = board.copy()
        self.animate = False
        graph_utils.set_btn_status(self, False, (pygame.K_m, pygame.K_s))
        graph_utils.set_btn_status(self, True, (pygame.K_r, ))
        graph_utils.set_btn_state(self, False, (pygame.K_m, pygame.K_s))

    def set_current_board(self, board):
        """ Save copy of the current board (before applying a tool)  """
        self.input_board = board.copy()

    def handle_input_events(self):
        """ handle input events before entering the display loop  """
        show_event = False
        if self.entered_conflicted_value:
            graph_utils.set_btn_status(self, False, (pygame.K_m, pygame.K_s))
            graph_utils.set_btn_status(self, True, (pygame.K_b,))
            show_event = True
        return show_event

    def impossible_entry_postproc(self):
        """ Clean up after showing conflicted cells """
        pass
        """
        cell_id = self.impacting_cell[0]
        original_value = self.impacting_cell[1]
        self.input_board[cell_id] = original_value
        self.clues_found.remove(cell_id)
        self.impacting_cell = None
        """

    def wrong_values_removed(self):
        """ TODO """
        self.buttons[pygame.K_h].set_status(True)

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
                    if (solver_tool is None or cell_id in self.clues_defined or
                            cell_id == active_clue and not self.critical_error or
                            cell_id in self.wrong_values and cell_id in self.clues_found and not self.critical_error):
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

        pygame.draw.rect(self.screen, GREY, self.keypad_frame, width=2, border_radius=9)
        for button in self.buttons.values():
            button.draw(self.screen)
        pygame.display.update()

    def draw_board(self, board, solver_tool=None, **kwargs):
        """ TODO """
        if self.solver_loop == -1:
            self.calculate_next_clue = True
            return True

        if not solver_tool:
            self.input_board = board.copy()     # TODO - check if it should be done each time in draw_board
        elif self.critical_error:
            self.critical_error_event(board, solver_tool, **kwargs)
        elif solver_tool == "end_of_game":
            self.sudoku_solved_event(board)
        elif not (self.show_solution_steps and self.method[solver_tool] in self.inspect):
            self.calculate_next_clue = True
            print(f'{self.calculate_next_clue = } out of {solver_tool = }')
            return True

        start = time.time()             # TODO - get rid of it!!!

        self.handle_input_events()
        self.render_board(board, solver_tool, **kwargs)

        if self.critical_error:
            graph_utils.display_info(self, screen_messages["critical_error"])
        elif self.entered_conflicted_value:
            graph_utils.display_info(self, screen_messages["conflicting_values"])       # TODO
            self.entered_conflicted_value = None
        elif solver_tool == "end_of_game":
            graph_utils.display_info(self, screen_messages[solver_tool])
        elif self.show_wrong_values:
            graph_utils.display_info(self, "Inconsistent board data")       # TODO
        elif self.buttons[pygame.K_h].is_pressed():
            graph_utils.display_info(self, screen_messages[solver_tool])
        else:
            graph_utils.display_info(self, screen_messages["plain_board"])

        self.board_updated = False
        self.wait = True if solver_tool else False  # TODO - temporary only!!!

        if self.animate:
            self.board_updated = True
            self.render_board(board, solver_tool, **kwargs)
            pygame.display.update()
            time.sleep(ANIMATION_STEP_TIME)
            self.calculate_next_clue = True
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