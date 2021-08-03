# -*- coding: UTF-8 -*-

import pygame
import time


import graph_utils
from display import screen_messages

# RGB colors:
from html_colors import html_color_codes
# from graph_utils import BLACK
# from graph_utils import BLUE
from graph_utils import GREY
# from graph_utils import GAINSBORO

from graph_utils import ANIMATION_STEP_TIME

from graph_utils import CELL_SIZE
from graph_utils import LEFT_MARGIN
from graph_utils import TOP_MARGIN

from utils import CELL_COL, CELL_ROW


from icecream import ic
ic.configureOutput(includeContext=True)


C_OTHER_CELLS = (255, 250, 190)

KEYBOARD_DIGITS = (1, 2, 3, 4, 5, 6, 7, 8, 9)


class AppWindow:
    """ TODO """

    def __init__(self, board, solver_status, inspect):
        if not pygame.get_init():
            pygame.init()
        self.font_type = "FreeSans"
        self.font_clues_size = 47
        self.font_options_size = 17
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
        self.board_cells = graph_utils.set_cell_rectangles()
        self.keypad_frame = graph_utils.set_keypad_frame()
        self.keypad_keys = graph_utils.set_keypad_keys()
        self.buttons = {}
        self.actions = {}

        self.method = graph_utils.set_methods()
        self.peep = inspect if len(inspect) else ''.join(self.method.values())
        self.inspect = self.peep

        self.solver_status = solver_status
        self.wrong_values = set()
        self.options_visible = set()
        self.selected_key = None
        self.selected_cell = None
        self.show_solution_steps = True
        self.show_wrong_values = True
        self.animate = False
        self.board_updated = False
        self.clue_entered = (None, None, None)
        self.show_all_pencil_marks = False
        self.critical_error = None
        self.wait = False
        self.calculate_next_clue = False

        self.time_in = 0
        self.solver_loop = None
        self.solved_board = None

        pygame.display.set_caption('SUDOKU PUZZLE')
        pygame.display.set_icon(pygame.image.load('demon.png'))  # TODO - get a better icon
        self.screen = pygame.display.set_mode(graph_utils.window_size())
        self.screen.fill(html_color_codes["gainsboro"])
        graph_utils.set_buttons(self)

    def critical_error_event(self, board, **kwargs):
        """ Handle 'Critical Error' event """
        if self.buttons[pygame.K_h].is_pressed() or self.buttons[pygame.K_m].is_pressed() or self.buttons[
                pygame.K_s].is_pressed():
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
                    self.solver_status.clues_found.add(kwargs["new_clue"])
                else:
                    self.options_visible.add(kwargs["new_clue"])
            for cell in self.critical_error:
                if cell not in self.solver_status.clues_defined:
                    self.options_visible.add(cell)
            # self.set_current_board(board)         TODO !!!

    def wrong_entry_event(self):
        """ Handle 'Wrong Manual Entry' event """
        graph_utils.set_btn_status(self, False, (pygame.K_h, pygame.K_m, pygame.K_s))
        graph_utils.set_btn_status(self, True, (pygame.K_b,))

    def sudoku_solved_event(self, board):
        """ Handle 'Sudoku Solved' event """
        self.solver_status.board_baseline = board.copy()        # TODO - is it needed?
        self.animate = False
        graph_utils.set_btn_status(self, False, (pygame.K_m, pygame.K_s))
        graph_utils.set_btn_status(self, True, (pygame.K_r,))
        graph_utils.set_btn_state(self, False, (pygame.K_m, pygame.K_s))

    def plain_board_event(self):
        """ Clean current board, not solved yet event  """
        graph_utils.set_btn_status(self, False, (pygame.K_a, pygame.K_b))
        graph_utils.set_btn_status(self, True, (pygame.K_h, pygame.K_m, pygame.K_s))

    # def set_current_board(self, board):         # TODO - move it from here!
        # """ Save copy of the current board (before applying a tool)  """
        # self.solver_status.board_baseline = board.copy()

    def handle_input_events(self, board, **kwargs):
        """ handle input events before entering the display loop  """
        if self.solver_loop == -1:
            self.calculate_next_clue = True
            return True

        solver_tool = kwargs["solver_tool"] if "solver_tool" in kwargs else None        # TODO - fix it !!!
        wrong_entry = bool("conflicted_cells" in kwargs and kwargs["conflicted_cells"] or
                           "wrong_values" in kwargs and kwargs["wrong_values"])
        if not solver_tool:
            pass
        elif self.critical_error:
            self.critical_error_event(board, **kwargs)
        elif wrong_entry:
            self.wrong_entry_event()
        elif kwargs["solver_tool"] == "end_of_game":
            self.sudoku_solved_event(board)
        elif not (self.show_solution_steps and self.method[kwargs["solver_tool"]] in self.inspect):
            return True
        elif solver_tool == "plain_board":
            self.plain_board_event()
        return False

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

    def render_board(self, board, **kwargs):
        """ render board (TODO) """
        active_clue = kwargs["new_clue"] if "new_clue" in kwargs else None
        solver_tool = kwargs["solver_tool"] if "solver_tool" in kwargs else "plain_board"   # None TODO !!!
        # if solver_tool == None:
        #     raise Exception
        removed = kwargs["remove"] if "remove" in kwargs else None
        for row_id in range(9):
            for col_id in range(9):
                cell_id = row_id * 9 + col_id
                cell_pos = (col_id * CELL_SIZE + LEFT_MARGIN, row_id * CELL_SIZE + TOP_MARGIN)
                cell_rect = (cell_pos[0], cell_pos[1], CELL_SIZE + 1, CELL_SIZE + 1)
                pygame.draw.rect(self.screen, graph_utils.cell_color(self, cell_id, **kwargs), cell_rect)

                if board[cell_id] != '.':
                    if (solver_tool is None or cell_id in self.solver_status.clues_defined or
                            cell_id == active_clue and not self.critical_error or
                            cell_id in self.wrong_values and cell_id in self.solver_status.clues_found and
                            not self.critical_error):
                        graph_utils.render_clue(self, board[cell_id], cell_pos, html_color_codes["black"])
                    elif cell_id in self.solver_status.clues_found and len(board[cell_id]) == 1:
                        graph_utils.render_clue(self, board[cell_id], cell_pos, html_color_codes["teal"])
                    elif graph_utils.show_pencil_marks(self, cell_id, **kwargs):
                        if solver_tool != "plain_board":
                            graph_utils.highlight_options(self, cell_id, board[cell_id], cell_pos, **kwargs)
                        graph_utils.render_options(self, board[cell_id], cell_pos)
        if removed:
            for value, cell_id in removed:
                if self.show_all_pencil_marks or cell_id in self.options_visible:
                    cell_pos = (CELL_COL[cell_id] * CELL_SIZE + LEFT_MARGIN, CELL_ROW[cell_id] * CELL_SIZE + TOP_MARGIN)
                    graph_utils.render_options(self, value, cell_pos)

        for i in range(10):
            line_thickness = 5 if i % 3 == 0 else 1
            pygame.draw.line(self.screen, html_color_codes["black"], (LEFT_MARGIN - 2, i * CELL_SIZE + TOP_MARGIN),
                             (LEFT_MARGIN + 9 * CELL_SIZE + 2,
                              i * CELL_SIZE + TOP_MARGIN), line_thickness)
            pygame.draw.line(self.screen, html_color_codes["black"], (i * CELL_SIZE + LEFT_MARGIN, TOP_MARGIN),
                             (i * CELL_SIZE + LEFT_MARGIN,
                              TOP_MARGIN + 9 * CELL_SIZE), line_thickness)
        graph_utils.draw_board_features(self, **kwargs)

        pygame.draw.rect(self.screen, GREY, self.keypad_frame, width=2, border_radius=9)
        for button in self.buttons.values():
            button.draw(self.screen)
        pygame.display.update()

    def draw_board(self, board, **kwargs):
        """ TODO """
        start = time.time()  # TODO - get rid of it!!!
        solver_tool = kwargs["solver_tool"] if "solver_tool" in kwargs else "plain_board"   # TODO - simplify it !!!

        if self.animate and solver_tool == "als_xz":        # TODO - for development & debugging only!
            self.animate = False
            self.wait = True
            self.buttons[pygame.K_m].set_pressed(False)
            graph_utils.set_btn_status(self, True, (pygame.K_a, pygame.K_b))
            graph_utils.set_btn_status(self, False, (pygame.K_m,))
            graph_utils.set_keyboard_status(self, True)

        if self.handle_input_events(board, **kwargs):
            return True
        self.render_board(board, **kwargs)

        if self.critical_error:
            graph_utils.display_info(self, screen_messages["critical_error"])
        elif "conflicted_cells" in kwargs and kwargs["conflicted_cells"]:
            graph_utils.display_info(self, screen_messages["conflicting_values"])
        elif solver_tool == "end_of_game":
            graph_utils.display_info(self, screen_messages[solver_tool])
        elif self.show_wrong_values and self.wrong_values:
            graph_utils.display_info(self, screen_messages["wrong_values"])
        elif solver_tool != "plain_board":
            graph_utils.display_info(self, screen_messages[solver_tool])
        else:
            graph_utils.display_info(self, screen_messages["plain_board"])

        self.board_updated = False
        self.wait = True if solver_tool else False  # TODO - temporary only!!!

        if self.animate:
            self.board_updated = True
            self.calculate_next_clue = True
            time.sleep(ANIMATION_STEP_TIME)
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
                    self.actions[event](self, event, board, **kwargs)
                pygame.display.update()
        # if self.board_updated:
        #     self.input_board = board.copy()
        self.time_in += time.time() - start
        return self.board_updated

    def quit(self):
        """ TODO """
        pygame.quit()
